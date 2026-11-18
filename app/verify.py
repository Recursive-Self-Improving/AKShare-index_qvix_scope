"""Independent offline raw-to-artifacts accounting and actual embedded trace checks."""
import argparse
import csv
import io
import json
import math
import re
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path

from app.core import (
    INDICES, MAPPINGS, OHLC, QVIX_FEEDS, SCHEMA, compact_quality, compact_snapshot,
    csv_bytes, decode, load_manifest, origin_snapshot, replay_qvix, sha,
)
from app.identities import IDENTITIES


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Embedded(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_data = False
        self.payload = ""
        self.external = []
        self.visible = []
        self.script = False
        self.disclosures = {}
        self.disclosure = None
        self.section = None
        self.disclosure_sections = {}
        self.disclosure_classes = {}
        self.regions = {}
        self.region = None
        self.region_depth = None
        self.ancestors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        require(self.disclosure is None, "disallowed disclosure content container")
        if tag not in ("area", "base", "br", "col", "embed", "hr", "img", "input",
                       "link", "meta", "param", "source", "track", "wbr"):
            self.ancestors.append((tag, attrs))
        if self.region is not None:
            self.regions[self.region].append([tag, attrs, ""])
        elif attrs.get("id") in REGIONS:
            self.enter_region(tag, attrs)
        if tag == "section":
            require(not any(k in attrs for k in ("hidden", "style")), "hidden panel")
            self.section = attrs.get("id")
        if tag == "p" and attrs.get("id", "").startswith(("index-status-", "qvix-status-")):
            self.disclosure = attrs["id"]
            require(self.disclosure not in self.disclosures, "duplicate visible disclosure")
            classes = ("index-status ok", "index-status warn") if self.disclosure.startswith("index-") else ("quality ok", "quality warn")
            require(not any(k in attrs for k in ("hidden", "style")) and attrs.get("class", "") in classes,
                    "hidden disclosure")
            self.disclosure_classes[self.disclosure] = attrs["class"]
            # Accept only the renderer's visible path, not arbitrary HTML containers
            # (details, template, extra wrappers/classes or inline CSS can hide text).
            require([t for t, _ in self.ancestors] ==
                    ["html", "body", "main", "section", "div", "p"],
                    "disallowed disclosure containers")
            allowed = ({"lang"}, set(), set(), {"class", "id"}, {"class"}, {"class", "id"})
            require(all(set(a) <= keys for (_, a), keys in zip(self.ancestors, allowed, strict=True)) and
                    self.ancestors[3][1].get("class") == "panel" and
                    self.ancestors[4][1].get("class") == "status",
                    "hidden/style-bearing disclosure containers")
            self.disclosures[self.disclosure] = ""
            self.disclosure_sections[self.disclosure] = self.section
        if tag == "script":
            self.script = True
            self.in_data = attrs.get("id") == "report-data"
            if "src" in attrs:
                self.external.append(attrs["src"])
        if tag in ("link", "img", "iframe"):
            self.external.append(attrs)

    def enter_region(self, tag, attrs):
        """Summary/quality table: fixed visible path, exact attributes, captured cell by cell."""
        rid = attrs["id"]
        path, parents, own = REGIONS[rid]
        require(rid not in self.regions, "duplicate visible region disclosure")
        require([t for t, _ in self.ancestors] == path and
                [a for _, a in self.ancestors[:-1]] == parents and attrs == own,
                "hidden/disallowed visible region disclosure")
        self.region, self.region_depth, self.regions[rid] = rid, len(self.ancestors), []

    def handle_endtag(self, tag):
        require(bool(self.ancestors) and self.ancestors[-1][0] == tag,
                "invalid disclosure container nesting")
        self.ancestors.pop()
        if self.region is not None and len(self.ancestors) < self.region_depth:
            self.region = None
        if tag == "section":
            self.section = None
        if tag == "p":
            self.disclosure = None
        if tag == "script":
            self.in_data = False
            self.script = False

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.ancestors and self.ancestors[-1][0] == tag:
            self.handle_endtag(tag)

    def handle_data(self, value):
        if self.in_data:
            self.payload += value
        elif not self.script:
            self.visible.append(value)
            if self.region is not None:
                cells = self.regions[self.region]
                if cells:
                    cells[-1][2] += value
                else:
                    cells.append(["#text", {}, value])
            if self.disclosure:
                self.disclosures[self.disclosure] += value


_WORD = {"success": "成功", "partial": "部分成功", "failure": "失败"}
_TOP = [{"lang": "zh-CN"}, {}, {}]
REGIONS = {"summary": (["html", "body", "main", "div"], _TOP, {"class": "stats", "id": "summary"}),
           "quality-table": (["html", "body", "main", "div", "table"], _TOP + [{"class": "scroll"}],
                             {"class": "grid", "id": "quality-table"})}


def _utc(value):
    return value[:16].replace("T", " ") + " UTC" if value else "未知"


def _span(pair):
    return f"{pair[0]} → {pair[1]}" if pair else "范围未知"


def _stale(status, when):
    return f"陈旧：本次获取{_WORD.get(status, status)}，沿用 {_utc(when)} 快照"


def visible_index(s):
    """Independently expected compact index disclosure (deviations only)."""
    if s["snapshot_status"] == "unavailable":
        out = [f"无可用快照（本次获取{_WORD.get(s['attempt'], s['attempt'])} @ {_utc(s['attempted_at'])}）"]
    else:
        out = [f"新浪收盘 {_span(s['range'])}", f"{s['rows']} 行"]
        if s["snapshot_status"] != "success":
            out.append("快照" + _WORD.get(s["snapshot_status"], s["snapshot_status"]))
        if s["stale_reuse"]:
            out.append(_stale(s["attempt"], s["successful_at"]))
        if len(s["relative_gaps"]) > 0:
            out.append(f"较上证缺 {len(s['relative_gaps'])} 日")
    retro = s["retrospective_rows"]
    out += ["发布前回溯行数未知"] if retro is None else [f"发布前回溯 {retro} 行"] if retro != 0 else []
    out += ["上证日历陈旧"] if s["calendar_stale"] else []
    return " · ".join(out)


_ISSUES = (("缺口", "holes"), ("冲突", "conflict"), ("无效字段", "invalid_fields"),
           ("零值行", "zero_rows"), ("源外", "source_only"), ("包络异常", "envelope_rows"),
           ("内部空白", "blank_internal"), ("尾部空白", "blank_tail"))


def _qvix_calm(state):
    snap = state["snapshot"]
    return (bool(snap) and snap["status"] == "success" and not state["stale_reuse"] and
            snap["accounting"]["comparator"] is not None and
            not snap["accounting"]["comparator"]["stale_reuse"] and
            all(snap["accounting"][part][k] == 0 for _, k in _ISSUES for part in ("full", "selected")))


def visible_summary(manifest):
    """Independently expected header stat cards as [tag, attrs, text] cells."""
    index_states = [manifest["feeds"][c] for c in INDICES]
    feed_states = [manifest["feeds"][f] for f in QVIX_FEEDS]
    good = len([s for s in index_states if s["snapshot"] and not s["stale_reuse"]
                and s["snapshot"]["status"] == "success"])
    calm = len([s for s in feed_states if _qvix_calm(s)])
    ends = [s["snapshot"]["range"][1] for s in index_states if s["snapshot"] and s["snapshot"]["range"]]
    times = [s["attempt"]["attempted_at"] for s in index_states + feed_states if s["attempt"].get("attempted_at")]
    cards = [("指数", f"{good} / 8", "本次获取成功", good != 8),
             ("QVIX 质量", f"{7 - calm} / 7", "条需留意，见各图下方", calm != 7),
             ("数据截至", max(ends) if ends else "未知", "最新观察日", False),
             ("获取时间", _utc(max(times) if times else None)[:16], "UTC", False)]
    cells = []
    for label, value, note, warn in cards:
        cells += [["div", {"class": "stat warn" if warn else "stat"}, ""], ["span", {}, label],
                  ["b", {}, value], ["small", {}, note]]
    return cells


def visible_quality_table(manifest):
    """Independently expected bottom QVIX table, including snapshot ID and comparator staleness."""
    cells = [["thead", {}, ""], ["tr", {}, ""]] + [
        ["th", {}, h] for h in ["QVIX", "状态", "收盘范围", *[label for label, _ in _ISSUES], "比较指数", "快照 ID"]]
    cells.append(["tbody", {}, ""])
    for feed in QVIX_FEEDS:
        state, name = manifest["feeds"][feed], QVIX_FEEDS[feed]["label"].removesuffix(" 收盘（%）")
        snap = state["snapshot"]
        cells += [["tr", {}, ""], ["th", {"scope": "row"}, name]]
        if snap is None:
            status = state["attempt"]["status"]
            cells.append(["td", {"colspan": str(len(_ISSUES) + 4)}, "无可用快照 · 本次获取" + _WORD.get(status, status)])
            continue
        full, comp = snap["accounting"]["full"], snap["accounting"]["comparator"]
        cells += [["td", {}, _WORD.get(snap["status"], snap["status"]) + ("（陈旧）" if state["stale_reuse"] else "")],
                  ["td", {}, _span(full["close_range"])]]
        cells += [["td", {"class": "num" if full[k] == 0 else "num warn"}, "未知" if full[k] is None else str(full[k])]
                  for _, k in _ISSUES]
        cells += [["td", {"class": "mono"}, "未知" if comp is None else comp["feed"] + ("（陈旧）" if comp["stale_reuse"] else "")],
                  ["td", {"class": "mono"}, snap["origin"]["sha256"][:12]]]
    return cells


def visible_qvix(feed, state):
    """Independent expected visible feed-local material disclosures."""
    snap = state["snapshot"]
    name = QVIX_FEEDS[feed]["label"].removesuffix(" 收盘（%）")
    if snap is None:
        a = state["attempt"]
        return f"{name} · 无可用快照（本次获取{_WORD.get(a['status'], a['status'])} @ {_utc(a['attempted_at'])}）"
    q = snap["accounting"]
    c, full, comp = q["selected"], q["full"], q["comparator"]
    flagged = [k for _, k in _ISSUES if full[k] is None or full[k] != 0 or c[k] != 0]
    out = [name, "有质量异常" if snap["status"] != "success" else "需留意" if flagged else "无质量异常"]
    out += [] if full["range"] == full["close_range"] else ["源 " + _span(full["range"])]
    out.append("收盘 " + _span(full["close_range"]))
    if c["range"] != full["range"] or c["close_range"] != full["close_range"]:
        out.append("窗口内收盘 " + _span(c["close_range"]))
    if state["stale_reuse"]:
        out.append(_stale(state["attempt"]["status"], snap["successful_at"]))
    for label, key in _ISSUES:
        if full[key] is None:
            out.append(label + " 未知")
        elif full[key] != 0 or c[key] != 0:
            out.append(f"{label} {full[key]}" + ("" if c[key] == full[key] else f"（窗口内 {c[key]}）"))
    if comp is None:
        out.append("比较日历未知")
    elif comp["stale_reuse"]:
        out.append(f"比较日历 {comp['feed']} 陈旧")
    return " · ".join(out)


def independent_qvix(body, wrapper, window, calendar, comparator, feed):
    """Separate full raw interpretation; no production parser, normalizer or renderer."""
    table = list(csv.reader(io.StringIO(body.decode("gbk")), strict=True))
    require(len(table) > 1 and table[0][:5] == ["", "2", "3", "4", "5"], "raw schema")
    positions = QVIX_FEEDS[feed]["columns"][1:]
    require(max(positions) < len(table[0]), "member positional schema")
    decoded = list(csv.DictReader(io.StringIO(wrapper.decode())))
    require(decoded and list(decoded[0]) == ["date", *OHLC] and len(decoded) == len(table) - 1,
            "wrapper schema/count")
    source, grouped, blank = [], {}, {}
    for ordinal, (record, wr) in enumerate(zip(table[1:], decoded, strict=True), 1):
        require(len(record) == len(table[0]) and
                re.fullmatch(r"\d{4}/(?:[1-9]|1[0-2])/(?:[1-9]|[12]\d|3[01])", record[0]),
                "raw width/date")
        day = date(*map(int, record[0].split("/"))).isoformat()
        values, errors, missing = [], {}, []
        for field, position in zip(OHLC, positions, strict=True):
            token = record[position]
            if token == "":
                missing.append(field)
                value = None
            else:
                try:
                    value = float(token)
                except ValueError:
                    errors[field] = token
                    value = None
                else:
                    require(math.isfinite(value), "nonfinite numeric")
            values.append(value)
            require((wr[field] == "" if value is None else bool(wr[field]) and
                     math.isfinite(float(wr[field])) and
                     math.isclose(float(wr[field]), value, rel_tol=1e-14, abs_tol=0)), "raw/wrapper values")
        require(wr["date"] == day, "raw/wrapper date")
        item = {"date": day, "ordinal": ordinal, "ohlc": values, "invalid": errors, "blank_fields": missing}
        source.append(item)
        if len(missing) == 4:
            blank.setdefault(day, []).append(ordinal)
        else:
            o, h, lo, c = values
            item["envelope_anomaly"] = (None not in values and (h < max(o, c, lo) or lo > min(o, c, h)))
            grouped.setdefault(day, []).append(item)
    nonblank, all_dates = set(grouped), {r["date"] for r in source}
    blank_only = set(blank) - nonblank
    def extent(values):
        return [min(values), max(values)] if values else None
    source_bounds = extent(nonblank)
    def bucket(d):
        if source_bounds is None:
            return "no_source"
        if d < source_bounds[0]:
            return "prefix"
        return "tail" if d > source_bounds[1] else "internal"
    sets = {f"blank_{k}": {d for d in blank_only if bucket(d) == k}
            for k in ("prefix", "internal", "tail", "no_source")}
    sets.update(nonblank=nonblank, usable_close=set(), conflict=set(),
                invalid_close_dates=set(), missing_close_dates=set(), blank_collision=set(blank) & nonblank)
    details, values_by_day = {}, {}
    for day in sorted(all_dates):
        candidates = grouped.get(day, [])
        identities = {(tuple(r["ohlc"]), tuple(sorted(r["invalid"].items())), tuple(r["blank_fields"]))
                      for r in candidates}
        conflict = len(identities) > 1
        details[day] = {"occurrences": candidates, "distinct_candidates": len(identities),
                        "conflict": conflict, "blank_ordinals": blank.get(day, [])}
        if not candidates:
            continue
        if conflict:
            sets["conflict"].add(day)
            v = [None] * 4
            flag = "conflict"
        else:
            first = candidates[0]
            v = first["ohlc"]
            category = ("usable_close" if v[3] is not None else
                        "invalid_close_dates" if "close" in first["invalid"] else "missing_close_dates")
            sets[category].add(day)
            flag = ("partial" if first["invalid"] or first["blank_fields"] else
                    "envelope_anomaly" if first["envelope_anomaly"] else "ok")
        values_by_day[day] = dict(date=day, **dict(zip(OHLC, v)), quality=flag)
    comparator_keys = ("absent", "blank", "conflict_holes", "invalid_close", "missing_close",
                       "holes", "source_only", "blank_source_only")
    if calendar is None:
        sets.update(dict.fromkeys(comparator_keys))
    else:
        inside = {d for d in calendar if source_bounds and source_bounds[0] <= d <= source_bounds[1]}
        sets.update(absent=inside - all_dates, blank=inside & blank_only,
                    conflict_holes=inside & sets["conflict"],
                    invalid_close=inside & sets["invalid_close_dates"],
                    missing_close=inside & sets["missing_close_dates"],
                    holes=inside - sets["usable_close"], source_only=nonblank - calendar,
                    blank_source_only=blank_only - calendar)
        categories = [sets[k] for k in comparator_keys[:5]]
        require(sum(map(len, categories)) == len(set.union(*categories)) and
                set.union(*categories) == sets["holes"], "hole partition")
    trace_days = (nonblank | sets["blank_internal"] | sets["blank_tail"] | sets["blank_no_source"]
                  | (sets["holes"] or set()))
    rows = [values_by_day.get(d, dict(date=d, **dict.fromkeys(OHLC), quality="blank_or_absent"))
            for d in sorted(trace_days) if window[0] <= d <= window[1]]
    def summary(start=None, end=None):
        def take(d):
            return start is None or start <= d <= end
        rr = [r for r in source if take(r["date"])]
        nn = {d for d in nonblank if take(d)}
        vv = {d for d in sets["usable_close"] if take(d)}
        result = {"common_range": extent({r["date"] for r in rr}), "range": extent(nn),
                  "close_range": extent(vv), "source_rows": len(rr), "dates": len(nn),
                  "incomplete_rows": sum(0 < len(r["blank_fields"]) < 4 for r in rr),
                  "finite_close_dates": len(vv),
                  "all_cells_nonblank": sum(len(r["blank_fields"]) == 0 for r in rr),
                  "finite_complete_rows": sum(None not in r["ohlc"] for r in rr),
                  "invalid_fields": sum(len(r["invalid"]) for r in rr),
                  "invalid_dates": len({r["date"] for r in rr if r["invalid"]}),
                  "zero_rows": sum(any(v == 0 for v in r["ohlc"]) for r in rr),
                  "zero_close_rows": sum(r["ohlc"][3] == 0 for r in rr),
                  "envelope_rows": sum(r.get("envelope_anomaly", False) for r in rr),
                  "distinct_candidates": sum(details[d]["distinct_candidates"] for d in nn),
                  "exact_duplicates": sum(len(grouped[d]) - details[d]["distinct_candidates"] for d in nn),
                  "blank_collision_rows": sum(len(blank[d]) for d in set(blank) & nonblank if take(d))}
        for kind in ("prefix", "internal", "tail", "no_source"):
            result[f"blank_{kind}_rows"] = sum(len(v) for d, v in blank.items() if take(d) and bucket(d) == kind)
        result.update({k: None if v is None else len({d for d in v if take(d)}) for k, v in sets.items()})
        return result
    quality = {"algorithm": SCHEMA, "feed": feed, "comparator": comparator, "dates": details,
               "sets": {k: None if v is None else sorted(v) for k, v in sets.items()},
               "ordered": [r["date"] for r in source] == sorted(r["date"] for r in source),
               "full": summary(), "selected": summary(*window)}
    counts = quality["full"]
    defect = (comparator is None or comparator["stale_reuse"] or not sets["usable_close"] or
              any(counts[k] for k in ("conflict", "invalid_fields", "envelope_rows", "source_only",
                                     "holes", "incomplete_rows", "blank_internal", "blank_tail")))
    return rows, quality, "partial" if defect else "success"


def read_ref(root, ref):
    content = (Path(root) / ref["path"]).read_bytes()
    require(sha(content) == ref["sha256"], "artifact reference hash")
    return json.loads(content)


def check_transport(root, evidence):
    raw = evidence["raw"]
    body = (root / raw["body"]).read_bytes()
    require(sha(body) == raw["sha256"] and raw["status"] == 200, "raw hash/status")
    transport = (root / evidence["transport"]).read_bytes()
    require(sha(transport) == evidence["transport_sha256"], "transport hash")
    _require_time(raw.get("retrieved_at"), "raw.retrieved_at")
    captures = json.loads(transport)
    require(len(captures) == 1 and
            {k: v for k, v in captures[0].items() if k != "body"} ==
            {k: v for k, v in raw.items() if k != "body"}, "consumed transport identity")
    return body


def _require_time(value, label):
    require(isinstance(value, str) and
            re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)", value),
            "missing/unusable timestamp: " + label)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("unusable timestamp: " + label) from error
    require(parsed.utcoffset() == timedelta(0), "non-UTC timestamp: " + label)


def validate_snapshot(root, snap, feed, cache=None):
    root = Path(root)
    cache = {} if cache is None else cache
    key = (feed, json.dumps(snap, sort_keys=True))
    if key in cache:
        return cache[key]
    require(snap["feed"] == feed and snap["status"] in ("success", "partial"), "snapshot identity")
    require("origin" in snap, "mandatory origin provenance")
    original, _ = origin_snapshot(root, snap["origin"], feed)
    for key in ("attempted_at", "successful_at", "finished_at"):
        _require_time(original.get(key), key)
    actual = {k: v for k, v in snap.items() if k != "origin"}
    require(actual == compact_snapshot(original), "immutable revision identity/time")
    require(snap["origin"]["path"] == (str(Path(snap["csv"]).parent / "result.json")
            if snap["origin"]["kind"] == "result" else
            str(Path(snap["csv"]).parent.parent / "manifest.json")), "immutable origin membership")
    if feed in QVIX_FEEDS:
        require(snap["schema"] == SCHEMA and snap["columns"] == QVIX_FEEDS[feed]["columns"] and
                snap["invocation"] == QVIX_FEEDS[feed]["wrapper"] + "()" and snap["invoked"],
                "member callable/columns")
        group = read_ref(root, snap["shared"])
        _require_time(original.get("acquired_at"), "acquired_at")
        _require_time(group.get("acquired_at"), "shared.acquired_at")
        body = check_transport(root, group)
        require(group["group_id"] == snap["group_id"] and group["global_validated"] is True and
                group["acquired_at"] == group["raw"]["retrieved_at"] == snap["acquired_at"],
                "shared identity/time")
        require(group["raw"]["url"] == group["raw"]["requested_url"] == QVIX_FEEDS[feed]["url"],
                "shared endpoint identity")
        if "migration" not in snap:
            directory = Path(snap["shared"]["path"]).parent
            require(Path(snap["csv"]).parent == directory / feed, "cross-feed/body membership")
            config = read_ref(root, group["config"])
            invocation = json.loads((root / directory / feed / "invocation.json").read_text())
            require(config["group_id"] == snap["group_id"] and snap["window"] == config["window"] and
                    all(invocation[k] == snap[k] for k in invocation), "invocation identity/time")
            require(snap["accounting"]["comparator"] == config["comparators"][feed], "bound comparator")
            require(Path(group["raw"]["body"]).parent == directory and
                    group["transport"] == str(directory / "transport.json"), "shared body membership")
        else:
            old, _ = origin_snapshot(root, snap["migration"], feed)
            require(feed == "qvix_50etf" and all(snap[k] == old[k] for k in
                    ("attempted_at", "successful_at", "finished_at", "window", "wrapper_sha256")) and
                    group["raw"] == old["raw"] and group["transport"] == old["transport"] and
                    group["transport_sha256"] == old["transport_sha256"], "migration origin/time")
        comparator = snap["accounting"]["comparator"]
        calendar = None
        if comparator:
            code = QVIX_FEEDS[feed]["comparator"]
            require(comparator["feed"] == code, "fixed comparator identity")
            origin, _ = origin_snapshot(root, comparator["origin"], code)
            csnap = compact_snapshot(origin) | {"origin": comparator["origin"]}
            validate_snapshot(root, csnap, code, cache)
            require(all(comparator[k] == csnap[k] for k in ("csv", "csv_sha256", "successful_at")) and
                    comparator["raw_sha256"] == csnap["raw"]["sha256"], "comparator origin/time/hash")
            calendar = {r["date"] for r in decode(code, (root / csnap["raw"]["body"]).read_bytes(),
                                                 csnap["raw"]["encoding"])}
        wrapper = (root / snap["wrapper"]).read_bytes()
        require(sha(wrapper) == snap["wrapper_sha256"] and replay_qvix(body, feed) == wrapper,
                "wrapper hash/replay")
        rows, quality, status = independent_qvix(body, wrapper, snap["window"], calendar, comparator, feed)
        sidecar = (root / snap["quality"]).read_bytes()
        require(sha(sidecar) == snap["quality_sha256"] and json.loads(sidecar) == quality, "quality sidecar")
        require(snap["accounting"] == compact_quality(quality) and status == snap["status"] and
                snap["source_range"] == quality["full"]["range"], "quality accounting/outcome")
        fields = [*OHLC, "quality"]
    else:
        require("transport" in snap and "transport_sha256" in snap, "mandatory transport provenance")
        body = check_transport(root, snap)
        require(snap["identity"] == IDENTITIES[feed], "index identity")
        rows = [r for r in decode(feed, body, snap["raw"]["encoding"])
                if snap["window"][0] <= r["date"] <= snap["window"][1]]
        require(sum(r["pre_release"] for r in rows) == snap["retrospective_count"], "retrospective count")
        fields = ["close", "pre_release", "pre_base"]
    content = (root / snap["csv"]).read_bytes()
    require(sha(content) == snap["csv_sha256"] and csv_bytes(rows, fields) == content, "CSV hash/replay")
    require(snap["count"] == len(rows) and snap["range"] ==
            ([rows[0]["date"], rows[-1]["date"]] if rows else None), "count/range")
    cache[key] = rows
    return rows


def validate_manifest(root, manifest):
    root = Path(root)
    require(manifest.get("schema") == SCHEMA and set(manifest["feeds"]) == {*INDICES, *QVIX_FEEDS},
            "incompatible active schema")
    if manifest.get("previous"):
        try:
            read_ref(root, manifest["previous"])
        except FileNotFoundError:
            # An operator can cut history immediately before one exact, immutable
            # acquisition. No other missing parent or corrupt artifact is excused.
            marker = root / "history-root.json"
            if not marker.is_file():
                raise
            anchor = json.loads(marker.read_bytes())
            require(manifest.get("operation") == "acquisition" and
                    anchor["path"] == manifest["manifest_path"] == manifest["run"] + "/manifest.json" and
                    read_ref(root, anchor) == manifest, "missing predecessor outside retained history root")
    verified, cache = {}, {}
    for feed, state in manifest["feeds"].items():
        require(set(state) == {"attempt", "snapshot", "stale_reuse"}, "compact whole snapshot state")
        for capture in state["attempt"].get("captures", []):
            require(sha((root / capture["body"]).read_bytes()) == capture["sha256"], "attempt capture hash")
        snap = state["snapshot"]
        usable = state["attempt"]["status"] in ("success", "partial")
        require(state["stale_reuse"] == (not usable and bool(snap)), "stale policy")
        if usable:
            require(state["attempt"] == snap, "fresh attempt identity")
        verified[feed] = validate_snapshot(root, snap, feed, cache) if snap else []
    return verified


def verify(root, report):
    root = Path(root)
    manifest = load_manifest(root)
    require(manifest == json.loads((root / manifest["manifest_path"]).read_text()), "immutable manifest")
    data = validate_manifest(root, manifest)
    parser = Embedded()
    parser.feed(Path(report).read_text())
    require(not parser.external, "external HTML resources")
    payload = json.loads(parser.payload)
    require(payload["run"] == manifest["run"] and payload["window"] == manifest["window"], "HTML run")
    require(payload["qvix_status"] == {f: manifest["feeds"][f] for f in QVIX_FEEDS}, "HTML QVIX status")
    require([p["code"] for p in payload["panels"]] == list(INDICES), "eight ordered panels")
    require(parser.regions.get("summary") == visible_summary(manifest), "visible summary disclosure")
    require(parser.regions.get("quality-table") == visible_quality_table(manifest),
            "visible quality table disclosure")
    calendar = {r["date"] for r in data["sh000001"]}
    for panel in payload["panels"]:
        code = panel["code"]
        state = manifest["feeds"][code]
        snap = state["snapshot"]
        require(panel["name"] == INDICES[code] and len(panel["data"]) == 1 + len(MAPPINGS[code]),
                "panel identity/trace count")
        values = {r["date"]: r["close"] for r in data[code]}
        limits = (min(values), max(values)) if values else None
        days = sorted(set(values) | {d for d in calendar if limits and limits[0] <= d <= limits[1]})
        traces = [(panel["data"][0], days, [values.get(d) for d in days], "y", INDICES[code] + " 收盘")]
        for trace, feed in zip(panel["data"][1:], MAPPINGS[code], strict=True):
            traces.append((trace, [r["date"] for r in data[feed]], [r["close"] for r in data[feed]],
                           "y2", QVIX_FEEDS[feed]["label"]))
            qid = f"qvix-status-{code}-{feed}"
            require(parser.disclosure_sections.get(qid) == "panel-section-" + code and
                    parser.disclosures.get(qid) == visible_qvix(feed, manifest["feeds"][feed]),
                    "visible QVIX disclosure")
            qstate = manifest["feeds"][feed]
            require(parser.disclosure_classes.get(qid) == ("quality ok" if _qvix_calm(qstate) else "quality warn"),
                    "visible QVIX disclosure tone")
        for trace, x, y, axis, label in traces:
            require(trace["x"] == x and trace["y"] == y, "embedded trace arrays")
            require(trace["connectgaps"] is False and trace["yaxis"] == axis and trace["name"] == label,
                    "trace identity/axes/nulls")
        require(panel["layout"]["yaxis2"]["side"] == "right" and
                panel["layout"]["yaxis2"]["overlaying"] == "y", "QVIX right axis")
        expected = {"attempt": state["attempt"]["status"], "attempted_at": state["attempt"]["attempted_at"],
                    "stale_reuse": state["stale_reuse"], "range": snap["range"] if snap else None,
                    "snapshot_status": snap["status"] if snap else "unavailable",
                    "rows": len(data[code]), "successful_at": snap["successful_at"] if snap else None,
                    "publication_date": IDENTITIES[code]["release_date"],
                    "base_date": IDENTITIES[code]["base_date"], "official_name": IDENTITIES[code]["official_name"],
                    "citation": IDENTITIES[code]["citation"],
                    "relative_gaps": [d for d in sorted(calendar) if limits and limits[0] <= d <= limits[1]
                                      and d not in values],
                    "calendar_stale": manifest["feeds"]["sh000001"]["stale_reuse"],
                    "retrospective_rows": snap["retrospective_count"] if snap else None}
        require(panel["status"] == expected, "panel status")
        disclosure_id = "index-status-" + code
        require(parser.disclosure_sections.get(disclosure_id) == "panel-section-" + code and
                parser.disclosures.get(disclosure_id) == visible_index(expected), "visible index disclosure")
        calm = (expected["snapshot_status"] == "success" and not expected["stale_reuse"] and
                not expected["calendar_stale"] and not expected["relative_gaps"] and
                expected["retrospective_rows"] is not None)
        require(parser.disclosure_classes.get(disclosure_id) == ("index-status ok" if calm else "index-status warn"),
                "visible index disclosure tone")
        print(code, len(data[code]), expected["range"], state["attempt"]["status"])
    print("Offline verification passed: eight panels, seven raw/wrapper/artifact/quality replays")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data")
    parser.add_argument("--report", default="index.html")
    args = parser.parse_args()
    verify(args.input, args.report)


if __name__ == "__main__":
    main()
