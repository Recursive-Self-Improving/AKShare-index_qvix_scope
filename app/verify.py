"""Independent offline raw-to-artifacts accounting and actual embedded trace checks."""
import argparse
import csv
import io
import json
import math
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

from app.core import (
    INDICES, OHLC, QVIX, SCHEMA, compact_quality, compact_snapshot, comparator_history,
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

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section":
            require(not any(k in attrs for k in ("hidden", "style")), "hidden panel")
            self.section = attrs.get("id")
        if tag == "p" and attrs.get("id", "").startswith(("index-status-", "qvix-status-")):
            self.disclosure = attrs["id"]
            require(self.disclosure not in self.disclosures, "duplicate visible disclosure")
            require(not any(k in attrs for k in ("hidden", "style")) and
                    attrs.get("class", "") in ("index-status", "quality"), "hidden disclosure")
            self.disclosures[self.disclosure] = ""
            self.disclosure_sections[self.disclosure] = self.section
        if tag == "script":
            self.script = True
            self.in_data = attrs.get("id") == "report-data"
            if "src" in attrs:
                self.external.append(attrs["src"])
        if tag in ("link", "img", "iframe"):
            self.external.append(attrs)

    def handle_endtag(self, tag):
        if tag == "section":
            self.section = None
        if tag == "p":
            self.disclosure = None
        if tag == "script":
            self.in_data = False
            self.script = False

    def handle_data(self, value):
        if self.in_data:
            self.payload += value
        elif not self.script:
            self.visible.append(value)
            if self.disclosure:
                self.disclosures[self.disclosure] += value


def independent_qvix(body, wrapper, window, calendar, comparator):
    """Separate raw parser/grouping, not renderer/normalizer expected helpers."""
    table = list(csv.reader(io.StringIO(body.decode("gbk")), strict=True))
    require(table and table[0][:5] == ["", "2", "3", "4", "5"], "raw schema")
    groups = {}
    order = []
    wr = list(csv.DictReader(io.StringIO(wrapper.decode())))
    require(len(wr) == len(table) - 1 and wr, "wrapper row count")
    for ordinal, (row, decoded) in enumerate(zip(table[1:], wr, strict=True), 1):
        require(len(row) == len(table[0]) and
                re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}", row[0]), "raw row/date")
        day = date(*map(int, row[0].split("/"))).isoformat()
        raw_values = list(map(float, row[1:5]))
        values = [float(decoded[k]) for k in OHLC]
        require(decoded["date"] == day and all(math.isfinite(v) and math.isfinite(r)
                and math.isclose(v, r, rel_tol=1e-14, abs_tol=0)
                for v, r in zip(values, raw_values, strict=True)), "raw/wrapper values")
        o, h, lo, c = values
        groups.setdefault(day, []).append({"ordinal": ordinal, "ohlc": values,
                                           "envelope_anomaly": h < max(o, c, lo) or lo > min(o, c, h)})
        order.append(day)
    details = {}
    rows = []
    for day, occurrences in sorted(groups.items()):
        distinct = len(set(tuple(v["ohlc"]) for v in occurrences))
        anomaly = any(v["envelope_anomaly"] for v in occurrences)
        details[day] = {"occurrences": occurrences, "distinct_candidates": distinct,
                        "conflict": distinct > 1, "envelope_anomaly": anomaly,
                        "source_only": day not in calendar if comparator else None}
        values = [None] * 4 if distinct > 1 else occurrences[0]["ohlc"]
        rows.append(dict(date=day, **dict(zip(OHLC, values)),
                         quality="conflict" if distinct > 1 else "envelope_anomaly" if anomaly else "ok"))

    bounds = min(groups), max(groups)
    missing = sorted(d for d in calendar if bounds[0] <= d <= bounds[1] and d not in groups)

    def count(days, selected=False):
        days = sorted(days)
        return {"source_rows": sum(len(groups[d]) for d in days), "dates": len(days),
                "distinct_candidates": sum(details[d]["distinct_candidates"] for d in days),
                "exact_duplicates": sum(len(groups[d]) - details[d]["distinct_candidates"] for d in days),
                "conflicts": sum(details[d]["conflict"] for d in days),
                "envelope_rows": sum(v["envelope_anomaly"] for d in days for v in groups[d]),
                "source_only": sorted(set(days) - calendar) if comparator else None,
                "missing": [d for d in missing if not selected or window[0] <= d <= window[1]]
                           if comparator else None,
                "range": [days[0], days[-1]] if days else None}

    chosen = [r for r in rows if window[0] <= r["date"] <= window[1]]
    quality = {"algorithm": SCHEMA, "comparator": comparator, "dates": details,
               "ordered": order == sorted(order), "full": count(groups),
               "selected": count((r["date"] for r in chosen), selected=True)}
    c = quality["full"]
    partial = (not comparator or comparator["stale_reuse"] or c["conflicts"] or c["envelope_rows"]
               or c["source_only"] or c["missing"])
    return chosen, quality, "partial" if partial else "success"


def validate_manifest(root, manifest):
    root = Path(root)
    require(manifest.get("schema") == SCHEMA and set(manifest["feeds"]) == {*INDICES, QVIX},
            "incompatible active schema")
    verified = {}
    if manifest.get("previous"):
        reference = manifest["previous"]
        require(sha((root / reference["path"]).read_bytes()) == reference["sha256"],
                "previous immutable manifest hash")
    cache = {}

    def check(snap, feed):
        key = (feed, json.dumps(snap, sort_keys=True))
        if key in cache:
            return cache[key]
        require(snap["feed"] == feed and snap["status"] in ("success", "partial"), "snapshot identity")
        require("origin" in snap and "transport" in snap and "transport_sha256" in snap,
                "mandatory transport/origin provenance")
        origin_path = (Path(snap["csv"]).parent.parent / "manifest.json"
                       if snap["origin"]["kind"] == "manifest"
                       else Path(snap["csv"]).parent / "result.json")
        require(snap["origin"]["path"] == str(origin_path), "immutable origin membership")
        original, origin_manifest = origin_snapshot(root, snap["origin"], feed)
        expected = compact_snapshot(original)
        actual = {k: v for k, v in snap.items() if k not in ("origin", "derivation")}
        if "derivation" in snap:
            require(feed == QVIX and snap["origin"]["kind"] == "manifest" and
                    origin_manifest["schema"] == "qvix-comparison-v2" and
                    snap["derivation"] == {"operation": "quality-format-migration",
                                           "source_schema": "qvix-comparison-v2"},
                    "invalid derived acquisition")
            expected["schema"] = SCHEMA
            expected["accounting"] = actual["accounting"]
        require(actual == expected, "immutable revision identity/time")
        raw = snap["raw"]
        body = (root / raw["body"]).read_bytes()
        require(sha(body) == raw["sha256"] and raw["status"] == 200, "raw hash/status")
        transport = (root / snap["transport"]).read_bytes()
        require(sha(transport) == snap["transport_sha256"], "transport hash")
        captures = json.loads(transport)
        require(len(captures) == 1 and
                {k: v for k, v in captures[0].items() if k != "body"} ==
                {k: v for k, v in raw.items() if k != "body"}, "consumed transport identity")
        if feed == QVIX:
            require(snap["schema"] == SCHEMA, "QVIX schema")
            wrapper = (root / snap["wrapper"]).read_bytes()
            require(sha(wrapper) == snap["wrapper_sha256"] and replay_qvix(body) == wrapper,
                    "wrapper hash/replay")
            comparator = snap["accounting"]["comparator"]
            if "derivation" in snap:
                origin_calendar = origin_manifest["feeds"]["sh000001"]
                original_snap = origin_calendar["snapshot"]
                require(comparator is not None and original_snap is not None,
                        "migration comparator unavailable")
                require({k: comparator[k] for k in ("csv", "csv_sha256", "successful_at")} ==
                        {k: original_snap[k] for k in ("csv", "csv_sha256", "successful_at")} and
                        comparator["stale_reuse"] == origin_calendar["stale_reuse"],
                        "comparator origin/stale provenance")
                require(comparator["origin"] == snap["origin"], "migration comparator origin")
            calendar = set()
            if comparator:
                index_original, _ = origin_snapshot(root, comparator["origin"], "sh000001")
                index_snap = compact_snapshot(index_original) | {"origin": comparator["origin"]}
                check(index_snap, "sh000001")
                require(all(comparator[k] == index_snap[k]
                            for k in ("csv", "csv_sha256", "successful_at")), "comparator identity")
                calendar = comparator_history(root, comparator)
            rows, quality, status = independent_qvix(body, wrapper, snap["window"], calendar, comparator)
            sidecar = (root / snap["quality"]).read_bytes()
            require(sha(sidecar) == snap["quality_sha256"], "quality hash")
            if "derivation" in snap:
                # Original sidecar remains immutable. Recheck its complete candidate evidence;
                # corrected calendar accounting lives only in the derived compact view.
                stored = json.loads(sidecar)
                require(set(stored["dates"]) == set(quality["dates"]), "quality dates")
                for day, detail in quality["dates"].items():
                    require({k: v for k, v in stored["dates"][day].items() if k != "source_only"} ==
                            {k: v for k, v in detail.items() if k != "source_only"}, "quality candidates")
            else:
                canonical = (json.dumps(quality, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
                require(sidecar == canonical, "quality sidecar")
            require(snap["accounting"] == compact_quality(quality), "quality accounting")
            require(status == snap["status"] and snap["source_range"] == quality["full"]["range"],
                    "quality outcome/source range")
            fields = [*OHLC, "quality"]
        else:
            require(snap["identity"] == IDENTITIES[feed], "index identity")
            rows = [r for r in decode(feed, body, raw["encoding"])
                    if snap["window"][0] <= r["date"] <= snap["window"][1]]
            require(sum(r["pre_release"] for r in rows) == snap["retrospective_count"], "retrospective count")
            fields = ["close", "pre_release", "pre_base"]
        content = (root / snap["csv"]).read_bytes()
        require(sha(content) == snap["csv_sha256"] and csv_bytes(rows, fields) == content, "CSV hash/replay")
        require(snap["count"] == len(rows) and snap["range"] ==
                ([rows[0]["date"], rows[-1]["date"]] if rows else None), "count/range")
        cache[key] = rows
        return rows

    for feed, state in manifest["feeds"].items():
        require(set(state) == {"attempt", "snapshot", "stale_reuse"}, "compact whole snapshot state")
        for capture in state["attempt"].get("captures", []):
            path = root / manifest["run"] / feed / Path(capture["body"]).name
            require(sha(path.read_bytes()) == capture["sha256"], "attempt capture hash")
        snap = state["snapshot"]
        usable = state["attempt"]["status"] in ("success", "partial")
        require(state["stale_reuse"] == (not usable and bool(snap)), "stale policy")
        if usable:
            require(state["attempt"] == snap, "fresh attempt identity")
        verified[feed] = check(snap, feed) if snap else []
    # A stale QVIX retains its own comparator, but every common trace must use that exact calendar.
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
    require(payload["qvix_status"] == manifest["feeds"][QVIX], "HTML QVIX status")
    require([p["code"] for p in payload["panels"]] == list(INDICES), "seven panels")
    qstate = manifest["feeds"][QVIX]
    qsnap = qstate["snapshot"]
    comparator = qsnap["accounting"]["comparator"] if qsnap else None
    calendar = comparator_history(root, comparator)
    qbounds = ([max(qsnap["window"][0], qsnap["source_range"][0]),
                min(qsnap["window"][1], qsnap["source_range"][1])] if qsnap else None)

    def compare(trace, rows, sessions, bounds=None):
        values = {r["date"]: r["close"] for r in rows}
        if bounds is None:
            bounds = [min(values), max(values)] if values else None
        days = sorted(set(values) | {d for d in sessions if bounds and bounds[0] <= d <= bounds[1]})
        require(trace["x"] == days and trace["y"] == [values.get(d) for d in days], "embedded trace arrays")
        require(trace["connectgaps"] is False, "connected null")

    for panel in payload["panels"]:
        code = panel["code"]
        state = manifest["feeds"][code]
        snap = state["snapshot"]
        require(panel["name"] == INDICES[code] and len(panel["data"]) == 2, "panel identity/trace count")
        compare(panel["data"][0], data[code], {r["date"] for r in data["sh000001"]})
        compare(panel["data"][1], data[QVIX], calendar, qbounds)
        require(panel["data"][0]["yaxis"] == "y" and panel["data"][1]["yaxis"] == "y2", "trace axes")
        require(panel["data"][1]["name"] == "50ETF QVIX 收盘（%）" and
                panel["layout"]["yaxis2"]["side"] == "right" and
                panel["layout"]["yaxis2"]["overlaying"] == "y", "QVIX right axis")
        status = panel["status"]
        expected = {"attempt": state["attempt"]["status"], "attempted_at": state["attempt"]["attempted_at"],
                    "stale_reuse": state["stale_reuse"], "range": snap["range"] if snap else None,
                    "snapshot_status": snap["status"] if snap else "unavailable",
                    "rows": len(data[code]), "successful_at": snap["successful_at"] if snap else None,
                    "publication_date": IDENTITIES[code]["release_date"],
                    "base_date": IDENTITIES[code]["base_date"], "official_name": IDENTITIES[code]["official_name"],
                    "citation": IDENTITIES[code]["citation"],
                    "relative_gaps": [d for d in sorted({r["date"] for r in data["sh000001"]})
                                      if data[code] and data[code][0]["date"] <= d <= data[code][-1]["date"]
                                      and d not in {r["date"] for r in data[code]}],
                    "calendar_stale": manifest["feeds"]["sh000001"]["stale_reuse"],
                    "retrospective_rows": snap["retrospective_count"] if snap else None}
        require(status == expected, "panel status")
        disclosure_id = "index-status-" + code
        require(parser.disclosure_sections.get(disclosure_id) == "panel-section-" + code,
                "missing visible index disclosure")
        try:
            disclosed = json.loads(parser.disclosures[disclosure_id])
        except (KeyError, json.JSONDecodeError) as error:
            raise ValueError("invalid visible index disclosure") from error
        require(disclosed == expected, "visible index disclosure")
        qid = "qvix-status-" + code
        require(parser.disclosure_sections.get(qid) == "panel-section-" + code,
                "missing visible QVIX disclosure")
        text = parser.disclosures[qid]
        prefix = (f"QVIX 尝试 {qstate['attempt']['status']} @ {qstate['attempt']['attempted_at']}；"
                  f"请求 {manifest['window']}；")
        if qsnap:
            q = qsnap["accounting"]
            c = q["selected"]
            expected_quality = (
                prefix + f"快照 {qsnap['status']} / {'stale 陈旧' if qstate['stale_reuse'] else 'fresh 新鲜'} "
                f"@ {qsnap['successful_at']}；源范围 {q['full']['range']}；选中 {c['range']} / {c['dates']}日期；"
                f"缺失源日期 {len(c['missing']) if c['missing'] is not None else 'unknown'}（无源行，以null断线）；"
                f"冲突日期 {c['conflicts']}（全部OHLC为null，不选任一候选）；"
                f"源外日期 {len(c['source_only']) if c['source_only'] is not None else 'unknown'}；"
                f"包络异常源行 {c['envelope_rows']}；精确重复 {c['exact_duplicates']}；"
                f"源有序 {q['ordered']}；全响应质量计数 {q['full']}；"
                f"比较日历身份 {q['comparator']}（非官方独立日历；陈旧/未知不能声称完整）。")
        else:
            expected_quality = prefix + "unavailable 无可用快照，范围未知，非零值。"
        require(text == expected_quality, "visible QVIX disclosure")
        print(code, len(data[code]), status["range"], state["attempt"]["status"])
    visible = "".join(parser.visible)
    require(visible.count("QVIX 尝试 " + qstate["attempt"]["status"]) == 8, "visible per-panel QVIX status")
    if qsnap:
        c = qsnap["accounting"]["selected"]
        require(visible.count(f"冲突日期 {c['conflicts']}") == 8, "visible conflict count")
        require(visible.count("缺失源日期 " + str(len(c["missing"]) if c["missing"] is not None else "unknown"))
                == 8, "visible missing count")
    print("Offline verification passed: raw/wrapper/artifacts/accounting and seven actual embedded trace pairs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data")
    parser.add_argument("--report", default="report.html")
    args = parser.parse_args()
    verify(args.input, args.report)


if __name__ == "__main__":
    main()
