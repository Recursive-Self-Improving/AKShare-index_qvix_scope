"""Single-snapshot data contract; no network in validation or rendering."""
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
    "sh000001": "上证指数", "sh000016": "上证50", "sz399330": "深证100", "sh000300": "沪深300",
    "sz399006": "创业板指", "sz399673": "创业板50", "sh000680": "科创综指",
    "sh000688": "科创50",
}
PUBLICATION = {code: identity["release_date"] for code, identity in IDENTITIES.items()}
SCHEMA = "qvix-comparison-v4"
QVIX_FEEDS = {
    "qvix_" + code: {"wrapper": f"index_option_{code}_qvix", "columns": [0, *range(pos, pos + 4)],
                    "label": label + " QVIX 收盘（%）", "comparator": comp,
                    "url": "http://1.optbbs.com/d/csv/d/k.csv"}
    for code, pos, label, comp in [
        ("50index", 79, "50股指", "sh000001"), ("50etf", 1, "50ETF", "sh000001"),
        ("100etf", 75, "深证100ETF", "sz399330"), ("300index", 17, "300股指", "sh000300"),
        ("300etf", 9, "300ETF", "sh000300"), ("cyb", 71, "创业板", "sz399006"),
        ("kcb", 83, "科创板", "sh000688")]}
MAPPINGS = {
    "sh000001": ["qvix_50index", "qvix_50etf"], "sh000016": ["qvix_50index", "qvix_50etf"],
    "sz399330": ["qvix_100etf"], "sh000300": ["qvix_300index", "qvix_300etf"],
    "sz399006": ["qvix_cyb"], "sz399673": ["qvix_cyb"],
    "sh000680": ["qvix_kcb"], "sh000688": ["qvix_kcb"]}
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


    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
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


def read_csv(path, *, expected_sha=None):
    if expected_sha is None:
        source = Path(path).open(newline="")
    else:
        # The stable path may have been replaced since the chart read its manifest.
        body = Path(path).read_bytes()
        if sha(body) != expected_sha:
            raise ValueError(f"observations do not match the loaded manifest: {path}")
        source = io.StringIO(body.decode(), newline="")
    with source as handle:
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
    manifest = json.loads((Path(root) / "current" / "manifest.json").read_bytes())
    if manifest.get("schema") != SCHEMA or set(manifest.get("feeds", {})) != {*INDICES, *QVIX_FEEDS}:
        raise ValueError("incompatible active schema")
    return manifest


def histories(root, manifest):
    root = Path(root)
    return {
        feed: read_csv(root / state["snapshot"]["csv"], expected_sha=state["snapshot"]["csv_sha256"])
        for feed, state in manifest["feeds"].items() if state.get("snapshot")
    }


def compact_quality(quality):
    return {k: v for k, v in quality.items() if k not in ("dates", "sets")}


def artifact_ref(root, path):
    return {"path": path, "sha256": sha((Path(root) / path).read_bytes())}


def origin_snapshot(root, origin, feed):
    directory = f"current/qvix-group/{feed}" if feed in QVIX_FEEDS else f"current/{feed}"
    if origin.get("kind") != "result" or origin["path"] != f"{directory}/result.json":
        raise ValueError("invalid acquisition origin")
    content = (Path(root) / origin["path"]).read_bytes()
    if sha(content) != origin["sha256"]:
        raise ValueError("acquisition result hash")
    return json.loads(content)


def comparator_history(root, comparator):
    if not comparator:
        return None
    feed = comparator["feed"]
    snapshot = origin_snapshot(root, comparator["origin"], feed)
    raw = snapshot["raw"]
    body = (Path(root) / raw["body"]).read_bytes()
    if sha(body) != raw["sha256"]:
        raise ValueError("comparator raw hash")
    return {r["date"] for r in decode(feed, body, raw["encoding"])}


def replay_qvix(body, feed):
    """Run the actual pinned wrapper against retained bytes without network."""
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
            return getattr(ak, QVIX_FEEDS[feed]["wrapper"])().to_csv(index=False).encode()
    finally:
        cache.cache_clear()


def common_qvix(body):
    """Validate the shared structure before accepting any member."""
    import re
    records = list(csv.reader(io.StringIO(body.decode("gbk")), strict=True))
    if not records or records[0][:5] != ["", "2", "3", "4", "5"] or len(records) < 2:
        raise ValueError("QVIX raw schema/empty response")
    for row in records[1:]:
        if len(row) != len(records[0]):
            raise ValueError("QVIX CSV width")
        if not re.fullmatch(r"\d{4}/(?:[1-9]|1[0-2])/(?:[1-9]|[12]\d|3[01])", row[0]):
            raise ValueError("QVIX raw date")
        date(*map(int, row[0].split("/")))
    return records


def raw_qvix(body, feed):
    records = common_qvix(body)
    columns = QVIX_FEEDS[feed]["columns"]
    if max(columns) >= len(records[0]):
        raise ValueError("QVIX member positional schema")
    rows = []
    for ordinal, record in enumerate(records[1:], 1):
        tokens = [record[p] for p in columns[1:]]
        values, invalid = [], {}
        for field, token in zip(OHLC, tokens, strict=True):
            if token == "":
                values.append(None)
                continue
            try:
                value = float(token)
            except ValueError:
                invalid[field] = token
                values.append(None)
            else:
                if not math.isfinite(value):
                    raise ValueError("QVIX nonfinite numeric")
                values.append(value)
        rows.append({"date": date(*map(int, record[0].split("/"))).isoformat(),
                     "ordinal": ordinal, "ohlc": values, "invalid": invalid,
                     "blank_fields": [f for f, t in zip(OHLC, tokens, strict=True) if t == ""]})
    return rows


def bounds(days):
    return [min(days), max(days)] if days else None


def qvix_artifacts(body, wrapper, window, calendar, comparator, feed):
    raw = raw_qvix(body, feed)
    decoded = list(csv.DictReader(io.StringIO(wrapper.decode())))
    if not decoded or list(decoded[0]) != ["date", *OHLC] or len(decoded) != len(raw):
        raise ValueError("QVIX wrapper schema/count")
    groups, blanks = {}, {}
    for source, row in zip(raw, decoded, strict=True):
        if row["date"] != source["date"]:
            raise ValueError("raw/wrapper date")
        for field, value in zip(OHLC, source["ohlc"], strict=True):
            token = row[field]
            if value is None:
                if token != "":
                    raise ValueError("raw/wrapper missing value")
            elif not token or not math.isfinite(float(token)) or not math.isclose(
                    float(token), value, rel_tol=1e-14, abs_tol=0):
                raise ValueError("raw/wrapper values")
        if len(source["blank_fields"]) == 4:
            blanks.setdefault(source["date"], []).append(source["ordinal"])
            continue
        o, h, lo, c = source["ohlc"]
        source["envelope_anomaly"] = (all(v is not None for v in source["ohlc"]) and
                                      (h < max(o, c, lo) or lo > min(o, c, h)))
        groups.setdefault(source["date"], []).append(source)
    D, N, B = {r["date"] for r in raw}, set(groups), set(blanks)
    B0, V, K, invalid_close_dates, M = B - N, set(), set(), set(), set()
    details, normalized = {}, {}
    for day, occurrences in sorted(groups.items()):
        distinct = {(tuple(r["ohlc"]), tuple(sorted(r["invalid"].items())), tuple(r["blank_fields"]))
                    for r in occurrences}
        conflict = len(distinct) > 1
        if conflict:
            K.add(day)
        elif occurrences[0]["ohlc"][3] is not None:
            V.add(day)
        elif "close" in occurrences[0]["invalid"]:
            invalid_close_dates.add(day)
        else:
            M.add(day)
        partial = any(r["invalid"] or r["blank_fields"] for r in occurrences)
        anomaly = any(r["envelope_anomaly"] for r in occurrences)
        values = [None] * 4 if conflict else occurrences[0]["ohlc"]
        normalized[day] = dict(date=day, **dict(zip(OHLC, values)),
                               quality="conflict" if conflict else "partial" if partial else
                               "envelope_anomaly" if anomaly else "ok")
        details[day] = {"occurrences": occurrences, "distinct_candidates": len(distinct),
                        "conflict": conflict, "blank_ordinals": blanks.get(day, [])}
    for day in B - N:
        details[day] = {"occurrences": [], "distinct_candidates": 0, "conflict": False,
                        "blank_ordinals": blanks[day]}
    S = bounds(N)
    regions = {name: set() for name in ("prefix", "internal", "tail", "no_source")}
    def region(day):
        return "no_source" if not S else "prefix" if day < S[0] else "tail" if day > S[1] else "internal"
    for day in B0:
        regions[region(day)].add(day)
    sets = {"nonblank": N, "usable_close": V, "conflict": K, "invalid_close_dates": invalid_close_dates,
            "missing_close_dates": M, "blank_collision": B & N,
            **{"blank_" + k: v for k, v in regions.items()}}
    if calendar is not None:
        Cs = {d for d in calendar if S and S[0] <= d <= S[1]}
        sets.update(absent=Cs - D, blank=Cs & B0, conflict_holes=Cs & K,
                    invalid_close=Cs & invalid_close_dates, missing_close=Cs & M, holes=Cs - V,
                    source_only=N - calendar, blank_source_only=B0 - calendar)
    else:
        sets.update(dict.fromkeys(("absent", "blank", "conflict_holes", "invalid_close",
                                   "missing_close", "holes", "source_only", "blank_source_only")))
    trace = N | regions["internal"] | regions["tail"] | regions["no_source"] | (sets["holes"] or set())
    rows = [normalized.get(d, dict(date=d, **dict.fromkeys(OHLC), quality="blank_or_absent"))
            for d in sorted(trace) if window[0] <= d <= window[1]]

    def accounting(chosen):
        rr = [r for r in raw if chosen(r["date"])]
        nn, vv = {d for d in N if chosen(d)}, {d for d in V if chosen(d)}
        result = {"common_range": bounds({d for d in D if chosen(d)}), "range": bounds(nn),
                  "close_range": bounds(vv), "source_rows": len(rr), "dates": len(nn),
                  "finite_close_dates": len(vv),
                  "all_cells_nonblank": sum(not r["blank_fields"] for r in rr),
                  "finite_complete_rows": sum(all(v is not None for v in r["ohlc"]) for r in rr),
                  "invalid_fields": sum(len(r["invalid"]) for r in rr),
                  "invalid_dates": len({r["date"] for r in rr if r["invalid"]}),
                  "incomplete_rows": sum(0 < len(r["blank_fields"]) < 4 for r in rr),
                  "zero_rows": sum(0 in r["ohlc"] for r in rr),
                  "zero_close_rows": sum(r["ohlc"][3] == 0 for r in rr),
                  "envelope_rows": sum(r.get("envelope_anomaly", False) for r in rr),
                  "distinct_candidates": sum(details[d]["distinct_candidates"] for d in nn),
                  "exact_duplicates": sum(len(groups[d]) - details[d]["distinct_candidates"] for d in nn),
                  "blank_collision_rows": sum(len(blanks[d]) for d in B & N if chosen(d))}
        for name in regions:
            result["blank_" + name + "_rows"] = sum(len(blanks[d]) for d in B if chosen(d) and region(d) == name)
        for name, values in sets.items():
            result[name] = None if values is None else sum(chosen(d) for d in values)
        return result
    quality = {"algorithm": SCHEMA, "feed": feed, "comparator": comparator,
               "dates": details, "sets": {k: sorted(v) if v is not None else None for k, v in sets.items()},
               "ordered": [r["date"] for r in raw] == sorted(r["date"] for r in raw),
               "full": accounting(lambda d: True),
               "selected": accounting(lambda d: window[0] <= d <= window[1])}
    c = quality["full"]
    partial = (not comparator or comparator["stale_reuse"] or not V or c["conflict"] or c["invalid_fields"]
               or c["envelope_rows"] or c["source_only"] or c["holes"]
               or c["incomplete_rows"]
               or c["blank_internal"] or c["blank_tail"])
    return rows, quality, "partial" if partial else "success"
