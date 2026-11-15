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
        return [{k: (v if k == "date" else float(v) if v else None) for k, v in row.items()}
                for row in csv.DictReader(handle)]


def decode(feed, body, encoding="utf-8"):
    import akshare as ak
    from akshare.utils import http
    import requests

    text = body.decode(encoding)
    if "<html" in text.lower() or "<!doctype" in text.lower():
        raise ValueError("HTML is not data")
    if feed == "sentiment":
        payload = json.loads(text)
        if not isinstance(payload, list):
            raise ValueError("expected JSON array")
        rows = [{"date": r["tradeDate"], "sentiment": r["maIndex1"],
                 "market_close": r["marketClose"]} for r in payload]
        return validate(rows, ["sentiment", "market_close"], allow_empty=True)
    # Reject a response belonging to another instrument, before invoking the pinned decoder.
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


def latest_by_date(snapshots):
    merged = {}
    for rows in snapshots:
        for row in rows:
            merged[row["date"]] = row
    return [merged[d] for d in sorted(merged)]


def trace_points(rows, field, calendar):
    """Insert nulls only on observed comparator sessions, within observed coverage."""
    if not rows:
        return [], []
    values = {r["date"]: r[field] for r in rows}
    dates = sorted(set(values) | {d for d in calendar if rows[0]["date"] <= d <= rows[-1]["date"]})
    return dates, [values.get(d) for d in dates]


def load_manifest(root):
    return json.loads((Path(root) / "latest.json").read_text())


def histories(root, manifest):
    root = Path(root)
    return {
        feed: latest_by_date([read_csv(root / s["csv"]) for s in state["revisions"]])
        if feed == "sentiment" else read_csv(root / state["snapshot"]["csv"])
        for feed, state in manifest["feeds"].items() if state.get("snapshot")
    }


def selected_history(root, manifest):
    """Derived coverage of exactly the selected/plotted observations, not the last response."""
    data = histories(root, manifest)
    calendar_snapshot = manifest["feeds"]["sh000001"]["snapshot"]
    calendar = {r["date"] for r in data.get("sh000001", [])}
    result = {}
    for feed, state in manifest["feeds"].items():
        dates = {r["date"] for r in data.get(feed, [])}
        bounds = [min(dates), max(dates)] if dates else None
        result[feed] = {
            "count": len(dates) if state.get("snapshot") else None,
            "range": bounds,
            "relative_gaps": sorted(d for d in calendar if bounds and bounds[0] <= d <= bounds[1]
                                    and d not in dates),
            "relative_extra_dates": sorted(dates - calendar) if calendar else None,
            "calendar_snapshot": calendar_snapshot["csv"] if calendar_snapshot else None,
        }
    return result
