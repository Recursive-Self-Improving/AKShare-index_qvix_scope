"""Small immutable snapshot contract; no network in validation or rendering."""
import csv
import hashlib
import io
import json
import math
import os
from datetime import date, datetime, timezone
from pathlib import Path

from app.identities import IDENTITIES

INDICES = {
    "sh000001": "上证指数", "sh000016": "上证50", "sh000300": "沪深300",
    "sz399006": "创业板指", "sz399673": "创业板50", "sh000680": "科创综指",
    "sh000688": "科创50",
}
PUBLICATION = {code: identity["release_date"] for code, identity in IDENTITIES.items()}
SCHEMA = "qvix-comparison-v3"
QVIX = "qvix_50etf"
OHLC = ["open", "high", "low", "close"]


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(body):
    return hashlib.sha256(body).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def atomic(path, value):
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    dump(tmp, value)
    with tmp.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def validate(rows, fields, allow_empty=False):
    previous = None
    for row in rows:
        day = row["date"]
        if date.fromisoformat(day).isoformat() != day or (previous is not None and day <= previous):
            raise ValueError("invalid, duplicate or unordered date")
        previous = day
        for field in fields:
            value = row[field]
            if value is None and field != "close":
                continue
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
                raise ValueError(f"invalid {field}: {value}")
    if not rows and not allow_empty:
        raise ValueError("empty index history")
    return rows


def csv_bytes(rows, fields):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=["date", *fields], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def read_csv(path):
    with Path(path).open(newline="") as handle:
        return [{k: (v if k in ("date", "quality") else float(v) if v else None)
                 for k, v in row.items()} for row in csv.DictReader(handle)]


def decode(feed, body, encoding="utf-8"):
    import akshare as ak
    from akshare.utils import http
    import requests

    text = body.decode(encoding)
    if "<html" in text.lower() or "<!doctype" in text.lower():
        raise ValueError("HTML is not data")
    import re
    if not re.match(r"\s*var\s+KLC_KL_" + re.escape(feed) + r"\s*=", text):
        raise ValueError("Sina response instrument identity mismatch")
    response = requests.Response()
    response.status_code = 200
    response._content = body
    response.encoding = encoding
    original = http.get
    try:
        http.get = lambda *args, **kwargs: response
        frame = ak.index_zh_daily_sina(symbol=feed)
    finally:
        http.get = original
    identity = IDENTITIES[feed]
    rows = [{"date": r.date.isoformat(), "close": float(r.close),
             "pre_release": int(r.date.isoformat() < identity["release_date"]),
             "pre_base": int(r.date.isoformat() < identity["base_date"])} for r in frame.itertuples()]
    return validate(rows, ["close", "pre_release", "pre_base"])


def selected(rows, start, end):
    return [r for r in rows if start <= r["date"] <= end]




def trace_points(rows, field, calendar, bounds=None):
    """Insert nulls only on observed comparator sessions, within observed coverage."""
    if bounds is None:
        bounds = [rows[0]["date"], rows[-1]["date"]] if rows else None
    values = {r["date"]: r[field] for r in rows}
    dates = sorted(set(values) | {d for d in calendar if bounds and bounds[0] <= d <= bounds[1]})
    return dates, [values.get(d) for d in dates]


def load_manifest(root):
    manifest = json.loads((Path(root) / "latest.json").read_text())
    if manifest.get("schema") != SCHEMA or set(manifest.get("feeds", {})) != {*INDICES, QVIX}:
        raise ValueError("incompatible active schema; run a new eight-source fetch")
    return manifest


def histories(root, manifest):
    root = Path(root)
    return {
        feed: read_csv(root / state["snapshot"]["csv"])
        for feed, state in manifest["feeds"].items() if state.get("snapshot")
    }


def compact_quality(quality):
    return {k: v for k, v in quality.items() if k != "dates"}


def artifact_ref(root, path):
    return {"path": path, "sha256": sha((Path(root) / path).read_bytes())}


def origin_snapshot(root, origin, feed):
    """Resolve an immutable acquisition, never infer provenance from missing fields."""
    content = (Path(root) / origin["path"]).read_bytes()
    if sha(content) != origin["sha256"]:
        raise ValueError("immutable origin hash")
    value = json.loads(content)
    if origin["kind"] == "manifest":
        return value["feeds"][feed]["snapshot"], value
    if origin["kind"] == "result":
        return value, None
    raise ValueError("unknown acquisition origin")


def compact_snapshot(snapshot):
    result = {k: v for k, v in snapshot.items() if k not in ("captures", "accounting")}
    if "accounting" in snapshot:
        result["accounting"] = compact_quality(snapshot["accounting"])
    return result


def comparator_history(root, comparator):
    if not comparator:
        return set()
    snapshot, _ = origin_snapshot(root, comparator["origin"], "sh000001")
    raw = snapshot["raw"]
    body = (Path(root) / raw["body"]).read_bytes()
    if sha(body) != raw["sha256"]:
        raise ValueError("comparator raw hash")
    return {r["date"] for r in decode("sh000001", body, raw["encoding"])}



def replay_qvix(body):
    """Pinned decoder, isolated cache and disabled network, full source-order CSV."""
    import akshare as ak
    import akshare.index.index_option_qvix as module
    import requests
    import socket
    from unittest.mock import patch
    from akshare.utils import http

    cache = getattr(module, "__get_optbbs_daily")
    cache.cache_clear()
    try:
        with patch.object(http, "get_buffer", lambda *a, **k: io.BytesIO(body)), \
                patch.object(requests.sessions.Session, "request", side_effect=ValueError("offline replay")), \
                patch.object(socket, "create_connection", side_effect=ValueError("offline replay")):
            return ak.index_option_50etf_qvix().to_csv(index=False).encode()
    finally:
        cache.cache_clear()


def raw_qvix(body):
    """Validate required raw fields before pandas coercion; ignore unrelated series."""
    import re
    records = list(csv.reader(io.StringIO(body.decode("gbk")), strict=True))
    if not records or records[0][:5] != ["", "2", "3", "4", "5"]:
        raise ValueError("QVIX raw schema")
    rows = []
    for ordinal, record in enumerate(records[1:], 1):
        if len(record) != len(records[0]):
            raise ValueError("QVIX CSV width")
        day = record[0]
        if not re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}", day):
            raise ValueError("QVIX raw date")
        year, month, daynum = map(int, day.split("/"))
        day = date(year, month, daynum).isoformat()
        values = [float(v) for v in record[1:5]]
        if not all(math.isfinite(v) for v in values):
            raise ValueError("QVIX nonfinite OHLC")
        rows.append({"date": day, "ordinal": ordinal, "ohlc": values})
    if not rows:
        raise ValueError("empty QVIX")
    return rows


def qvix_artifacts(body, wrapper, window, calendar, comparator):
    raw = raw_qvix(body)
    decoded = list(csv.DictReader(io.StringIO(wrapper.decode())))
    if list(decoded[0]) != ["date", *OHLC] or len(decoded) != len(raw):
        raise ValueError("QVIX wrapper schema/count")
    groups = {}
    for source, row in zip(raw, decoded, strict=True):
        values = [float(row[k]) for k in OHLC]
        if row["date"] != source["date"] or any(
                not math.isfinite(v) or not math.isclose(v, r, rel_tol=1e-14, abs_tol=0)
                for v, r in zip(values, source["ohlc"], strict=True)):
            raise ValueError("raw/wrapper values")
        o, h, lo, c = values
        candidate = {"ordinal": source["ordinal"], "ohlc": values,
                     "envelope_anomaly": h < max(o, c, lo) or lo > min(o, c, h)}
        groups.setdefault(row["date"], []).append(candidate)
    dates = sorted(groups)
    details = {}
    normalized = []
    for day in dates:
        occurrences = groups[day]
        distinct = {tuple(r["ohlc"]) for r in occurrences}
        conflict = len(distinct) > 1
        anomaly = any(r["envelope_anomaly"] for r in occurrences)
        quality = "conflict" if conflict else "envelope_anomaly" if anomaly else "ok"
        details[day] = {"occurrences": occurrences, "distinct_candidates": len(distinct),
                        "conflict": conflict, "envelope_anomaly": anomaly,
                        "source_only": day not in calendar if comparator else None}
        values = [None] * 4 if conflict else occurrences[0]["ohlc"]
        normalized.append(dict(date=day, **dict(zip(OHLC, values)), quality=quality))

    full_missing = sorted(d for d in calendar if dates[0] <= d <= dates[-1] and d not in groups)

    def accounting(days, bounds=None):
        days = sorted(days)
        missing = [d for d in full_missing if bounds is None or bounds[0] <= d <= bounds[1]]
        return {"source_rows": sum(len(groups[d]) for d in days), "dates": len(days),
                "distinct_candidates": sum(details[d]["distinct_candidates"] for d in days),
                "exact_duplicates": sum(len(groups[d]) - details[d]["distinct_candidates"] for d in days),
                "conflicts": sum(details[d]["conflict"] for d in days),
                "envelope_rows": sum(r["envelope_anomaly"] for d in days for r in groups[d]),
                "source_only": [d for d in days if d not in calendar] if comparator else None,
                "missing": missing if comparator else None,
                "range": [days[0], days[-1]] if days else None}

    chosen = selected(normalized, *window)
    quality = {"algorithm": SCHEMA, "comparator": comparator, "dates": details,
               "ordered": [r["date"] for r in raw] == sorted(r["date"] for r in raw),
               "full": accounting(dates), "selected": accounting((r["date"] for r in chosen), window)}
    counts = quality["full"]
    partial = (not comparator or comparator["stale_reuse"] or counts["conflicts"]
               or counts["envelope_rows"] or counts["source_only"] or counts["missing"])
    return chosen, quality, "partial" if partial else "success"
