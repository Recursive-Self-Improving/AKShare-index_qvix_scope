"""Offline raw/hash replay and comparison of the actual HTML arrays against CSV."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path

from app.core import INDICES, csv_bytes, decode, latest_by_date, load_manifest, read_csv, selected, sha
from app.identities import IDENTITIES
from app.sample import DOC_HASH, transcribe


class Embedded(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_data = False
        self.payload = ""
        self.external = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script":
            self.in_data = attrs.get("id") == "report-data"
            if "src" in attrs:
                self.external.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.external.append(attrs.get("href"))

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_data = False

    def handle_data(self, value):
        if self.in_data:
            self.payload += value


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_accounting(manifest, data, latest, payload):
    """Recompute from independently replayed rows; never trust renderer coverage."""
    calendar_state = manifest["feeds"]["sh000001"]["snapshot"]
    calendar = {r["date"] for r in data["sh000001"]}
    expected = {}
    for feed, state in manifest["feeds"].items():
        dates = {r["date"] for r in data[feed]}
        bounds = [min(dates), max(dates)] if dates else None
        expected[feed] = {
            "count": len(dates) if state["snapshot"] else None,
            "range": bounds,
            "relative_gaps": sorted((calendar - dates) & {
                d for d in calendar if bounds and bounds[0] <= d <= bounds[1]}),
            "relative_extra_dates": sorted(dates - calendar) if calendar else None,
            "calendar_snapshot": calendar_state["csv"] if calendar_state else None,
        }
        if "selected_history" in state:
            require(state["selected_history"] == expected[feed], f"{feed} selected-history metadata")
        else:
            # Immutable v1 evidence used latest-response gaps. Check that contract,
            # but independently require merged-history accounting in the new report.
            last_dates = {r["date"] for r in latest[feed]}
            legacy_gaps = sorted(d for d in calendar if last_dates
                                 and min(last_dates) <= d <= max(last_dates) and d not in last_dates)
            require(state["relative_gaps"] == legacy_gaps, f"{feed} legacy relative gaps")
            require(state["relative_extra_dates"] == (sorted(last_dates - calendar) if calendar else None),
                    f"{feed} legacy extra dates")
            require(state["calendar_snapshot"] == expected[feed]["calendar_snapshot"],
                    f"{feed} legacy calendar identity")
    require(payload["selected_history"] == expected, "HTML selected-history accounting")


def verify(root, report):
    root = Path(root)
    manifest = load_manifest(root)
    immutable = json.loads((root / manifest["manifest_path"]).read_text())
    require(manifest == immutable, "latest does not match immutable run manifest")
    for transport in (root / "runs").glob("*/*/transport.json"):
        for response in json.loads(transport.read_text()):
            body = (transport.parent / Path(response["body"]).name).read_bytes()
            require(sha(body) == response["sha256"], f"transport hash: {transport}")
    data = {}
    latest = {}
    for feed, state in manifest["feeds"].items():
        revisions = state["revisions"]
        require(state["snapshot"] == (revisions[-1] if revisions else None), "stale snapshot identity")
        decoded = []
        for snap in revisions:
            require(snap["feed"] == feed and snap["status"] == "success", "snapshot source identity")
            body = (root / snap["raw"]["body"]).read_bytes()
            require(sha(body) == snap["raw"]["sha256"], "raw hash")
            rows = selected(decode(feed, body, snap["raw"]["encoding"]), *snap["window"])
            fields = ["sentiment", "market_close"] if feed == "sentiment" else ["close", "pre_release", "pre_base"]
            csv = (root / snap["csv"]).read_bytes()
            require(sha(csv) == snap["csv_sha256"], "CSV hash")
            require(csv_bytes(rows, fields) == csv, "actual raw replay differs from CSV")
            require(len(rows) == snap["count"], "snapshot count")
            require(snap["range"] == ([rows[0]["date"], rows[-1]["date"]] if rows else None),
                    "snapshot range")
            decoded.append(read_csv(root / snap["csv"]))
        data[feed] = latest_by_date(decoded) if feed == "sentiment" else decoded[-1] if decoded else []
        latest[feed] = decoded[-1] if decoded else []
    docs = root / "documentation-example"
    provenance = json.loads((docs / "provenance.json").read_text())
    for name, key in (("source.md", "source_sha256"), ("LICENSE", "license_sha256"),
                      ("excerpt.txt", "excerpt_sha256"), ("documentation-example.csv", "csv_sha256")):
        require(sha((docs / name).read_bytes()) == provenance[key], f"documentation {name} hash")
    source = (docs / "source.md").read_text()
    excerpt = (docs / "excerpt.txt").read_text()
    require(provenance["source_sha256"] == DOC_HASH and excerpt in source, "immutable source/excerpt")
    samples = transcribe(excerpt)
    require(samples == read_csv(docs / "documentation-example.csv"), "documentation transcription")
    parser = Embedded()
    parser.feed(Path(report).read_text())
    require(not parser.external, "HTML requires external script/style")
    payload = json.loads(parser.payload)
    require(payload["run"] == manifest["run"], "HTML run identity")
    require(payload["sentiment_status"] == manifest["feeds"]["sentiment"], "HTML hides acquisition status")
    require([p["code"] for p in payload["panels"]] == list(INDICES), "seven canonical panels")
    calendar = {r["date"] for r in data["sh000001"]}
    verify_accounting(manifest, data, latest, payload)

    def compare(trace, rows, field, gaps):
        values = {r["date"]: r[field] for r in rows}
        dates = set(values)
        if rows and gaps:
            dates |= {d for d in calendar if rows[0]["date"] <= d <= rows[-1]["date"]}
        days = sorted(dates)
        require(trace["x"] == days and trace["y"] == [values.get(d) for d in days], "HTML/CSV arrays differ")
        require(trace["connectgaps"] is False, "HTML connects missing observations")

    for panel in payload["panels"]:
        code = panel["code"]
        traces = panel["data"]
        require(panel["name"] == INDICES[code], "panel name")
        require(panel["status"]["citation"] == IDENTITIES[code]["citation"], "identity provenance")
        require(traces[0]["yaxis"] == "y", "index axis")
        compare(traces[0], data[code], "close", True)
        require(traces[-1]["yaxis"] == "y2" and traces[-1]["mode"] == "markers", "isolated sample axis")
        compare(traces[-1], samples, "sentiment", False)
        require("not live/full history" in traces[-1]["name"], "sample misclassification")
        if data["sentiment"]:
            require(len(traces) == 3 and traces[1]["yaxis"] == "y2", "genuine sentiment axis")
            compare(traces[1], data["sentiment"], "sentiment", True)
        else:
            require(len(traces) == 2, "invented genuine sentiment trace")
        gaps = payload["selected_history"][code]["relative_gaps"]
        print(code, len(data[code]), data[code][0]["date"] if data[code] else "unknown",
              data[code][-1]["date"] if data[code] else "unknown", "relative gaps", len(gaps))
    print("Offline verification: raw bodies/hashes replay, immutable sources, CSV and seven embedded arrays agree")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data")
    parser.add_argument("--report", default="report.html")
    args = parser.parse_args()
    verify(args.input, args.report)


if __name__ == "__main__":
    main()
