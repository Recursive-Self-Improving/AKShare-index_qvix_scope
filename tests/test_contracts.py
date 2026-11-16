import copy
import csv
import io
import json
from pathlib import Path

import pytest

from app.core import (
    INDICES, OHLC, QVIX, SCHEMA, artifact_ref, compact_quality, comparator_history,
    csv_bytes, dump, histories, load_manifest, qvix_artifacts, raw_qvix,
    read_csv, replay_qvix, sha, trace_points, validate,
)
from app.fetch import promote, state_after, worker
from app.verify import independent_qvix, validate_manifest

EVIDENCE = Path(__file__).resolve().parents[1] / "docs/research/qvix-evidence"
WINDOW = ["2000-01-01", "2026-11-15"]


@pytest.fixture(scope="module")
def observed():
    body = (EVIDENCE / "response-0.body").read_bytes()
    wrapper = (EVIDENCE / "normalized.csv").read_bytes()
    coverage = json.loads((EVIDENCE / "coverage.json").read_text())
    # Historical pinned comparator identity is part of the real evidence.
    root = Path(__file__).resolve().parents[1] / "data"
    calendar_path = next((root / "runs").glob("2026-11-15T20-37*/sh000001/observations.csv"))
    calendar = {r["date"] for r in read_csv(calendar_path)}
    comparator = {"csv": str(calendar_path.relative_to(root)), "csv_sha256": sha(calendar_path.read_bytes()),
                  "successful_at": "historical", "stale_reuse": False}
    return body, wrapper, calendar, comparator, coverage


def test_real_candidates_nulls_counts_and_independent_replay(observed):
    body, wrapper, calendar, comparator, _ = observed
    assert replay_qvix(body) == wrapper
    rows, quality, status = qvix_artifacts(body, wrapper, WINDOW, calendar, comparator)
    assert (rows, quality, status) == independent_qvix(body, wrapper, WINDOW, calendar, comparator)
    assert status == "partial"
    assert len(rows) == 2848
    assert sum(r["close"] is not None for r in rows) == 2847
    conflict = next(r for r in rows if r["date"] == "2026-11-02")
    assert [conflict[k] for k in OHLC] == [None] * 4
    assert quality["dates"]["2026-11-02"]["occurrences"] == [
        {"ordinal": 2841, "ohlc": [16.21, 17.48, 15.82, 15.92], "envelope_anomaly": False},
        {"ordinal": 2843, "ohlc": [16.71, 16.86, 15.81, 15.9], "envelope_anomaly": False}]
    c = quality["full"]
    assert (c["source_rows"], c["dates"], c["distinct_candidates"], c["conflicts"],
            c["envelope_rows"], len(c["source_only"]), len(c["missing"])) == (2849, 2848, 2849, 1, 8, 4, 13)
    assert quality["ordered"] is False
    x, y = trace_points(rows, "close", calendar)
    assert sum(v is None for v in y) == 14
    assert set(c["source_only"]) <= set(x)
    assert x[0] == "2015-02-09" and x[-1] == "2026-11-13"


def source(records):
    return (",2,3,4,5\n" + "\n".join(",".join(map(str, r)) for r in records) + "\n").encode()


def derive(records, calendar=None, window=WINDOW):
    body = source(records)
    raw_qvix(body)
    return qvix_artifacts(body, replay_qvix(body), window, calendar or set(),
                          {"stale_reuse": False} if calendar is not None else None)


def test_exact_duplicates_order_zero_and_equal_close_conflict():
    records = [("2024/1/3", 0, 2, 0, 1), ("2024/1/2", 1, 2, 0, 1),
               ("2024/1/3", -0.0, 2.0, 0, 1)]
    rows, q, status = derive(records, {"2024-01-02", "2024-01-03"})
    assert status == "success" and q["full"]["exact_duplicates"] == 1 and not q["ordered"]
    assert [r["date"] for r in rows] == ["2024-01-02", "2024-01-03"]
    assert rows[1]["open"] == 0 and rows[1]["close"] == 1
    records.append(("2024/1/3", 1, 2, 0, 1))
    rows, q, status = derive(records, {"2024-01-02", "2024-01-03"})
    assert status == "partial" and rows[1]["quality"] == "conflict"
    assert all(rows[1][k] is None for k in OHLC)
    assert len(q["dates"]["2024-01-03"]["occurrences"]) == 3


@pytest.mark.parametrize("bad", [
    ("1999/2/29", 1, 2, 0, 1), ("1999-01-01", 1, 2, 0, 1),
    ("1999/1/1oops", 1, 2, 0, 1), ("1999/1/1", "nan", 2, 0, 1),
    ("1999/1/1", 1, "inf", 0, 1), ("1999/1/1", 1, 2, "", 1),
])
def test_full_raw_validation_before_window_or_coercion(bad):
    with pytest.raises(ValueError):
        derive([bad, ("2024/1/2", 1, 2, 0, 1)], {"2024-01-02"}, ["2024-01-01", "2024-12-31"])


@pytest.mark.parametrize("body", [b"", b"<html>error</html>", b",2,3,4,6\n2024/1/2,1,2,0,1\n",
                                 b",2,3,4,5\n2024/1/2,1,2,0\n"])
def test_raw_schema_failure(body):
    with pytest.raises(ValueError):
        raw_qvix(body)


def test_full_vs_selected_and_unknown_stale_comparator():
    rows, q, status = derive([("2024/1/2", 1, 2, 0, 1), ("2024/1/3", 1, 2, 0, 1),
                             ("2024/1/3", 2, 2, 0, 1)], {"2024-01-02", "2024-01-03"},
                            ["2024-01-02", "2024-01-02"])
    assert status == "partial" and q["full"]["conflicts"] == 1 and q["selected"]["conflicts"] == 0
    assert len(rows) == 1
    _, q, status = derive([("2024/1/2", 1, 2, 0, 1)])
    assert status == "partial" and q["full"]["missing"] is None


def test_whole_snapshot_transition_no_revision_fill():
    old = state_after({}, {"status": "success", "successful_at": "first", "csv": "clean"})
    partial = state_after(old, {"status": "partial", "successful_at": "second", "csv": "conflict"})
    assert partial["snapshot"]["csv"] == "conflict" and not partial["stale_reuse"]
    failed = state_after(partial, {"status": "failure", "attempted_at": "third"})
    assert failed["snapshot"] == partial["snapshot"] and failed["stale_reuse"]
    corrected = state_after(failed, {"status": "success", "successful_at": "fourth", "csv": "corrected"})
    assert corrected["snapshot"]["csv"] == "corrected"
    assert state_after({}, {"status": "failure"})["snapshot"] is None


@pytest.mark.parametrize("body,status", [(b"<html>error</html>", 200), (b"[]", 200),
                                       (source([("2024/1/2", 1, 2, 0, 1)]), 503)])
def test_actual_worker_capture_failure(tmp_path, monkeypatch, body, status):
    import requests

    def get(url, **kwargs):
        response = requests.Response()
        response.status_code = status
        response.url = url
        response.request = requests.Request("GET", url).prepare()
        response._content = body
        kwargs["hooks"]["response"](response)
        return response

    monkeypatch.setattr(requests, "get", get)
    worker(QVIX, tmp_path, *WINDOW)
    result = json.loads((tmp_path / "result.json").read_text())
    assert result["status"] == "failure"
    assert (tmp_path / "response-0.body").read_bytes() == body
    assert result["captures"][0]["sha256"] == sha(body)


def test_cache_isolation_between_replays():
    a = replay_qvix(source([("2024/1/2", 1, 2, 0, 1)]))
    b = replay_qvix(source([("2024/1/2", 1, 3, 0, 2)]))
    assert list(csv.DictReader(io.StringIO(a.decode())))[0]["close"] == "1"
    assert list(csv.DictReader(io.StringIO(b.decode())))[0]["close"] == "2"


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), "3.5"])
def test_invalid_index_close(value):
    with pytest.raises(ValueError):
        validate([{"date": "2024-01-02", "close": value}], ["close"])


def test_legacy_active_schema_rejected(tmp_path):
    dump(tmp_path / "latest.json", {"feeds": {"sentiment": {}}})
    with pytest.raises(ValueError, match="incompatible"):
        load_manifest(tmp_path)


def empty_manifest():
    return {"schema": SCHEMA, "manifest_path": "manifest.json", "feeds": {
        f: state_after({}, {"status": "failure", "attempted_at": "now"}) for f in [*INDICES, QVIX]}}


def test_atomic_and_validation_failure_preserve_pointer(tmp_path, monkeypatch):
    manifest = empty_manifest()
    promote(tmp_path, manifest)
    before = (tmp_path / "latest.json").read_bytes()
    broken = copy.deepcopy(manifest)
    broken["feeds"][QVIX]["stale_reuse"] = True
    with pytest.raises(ValueError):
        promote(tmp_path, broken)
    assert (tmp_path / "latest.json").read_bytes() == before

    def interrupt(*args):
        raise OSError("interrupted")

    monkeypatch.setattr("app.core.os.replace", interrupt)
    with pytest.raises(OSError):
        promote(tmp_path, manifest)
    assert (tmp_path / "latest.json").read_bytes() == before


def test_nullable_csv_does_not_become_zero(tmp_path):
    body = csv_bytes([{"date": "2024-01-02", **dict.fromkeys(OHLC), "quality": "conflict"}],
                     [*OHLC, "quality"])
    (tmp_path / "conflict.csv").write_bytes(body)
    assert read_csv(tmp_path / "conflict.csv")[0]["close"] is None


def test_offline_real_active_artifacts_and_tampering(tmp_path):
    # Current-schema immutable acquisition is the integration fixture; old evidence is never decoded as sentiment.
    import shutil
    from app.chart import build
    from app.verify import Embedded, verify

    origin = Path(__file__).resolve().parents[1] / "data"
    manifest = load_manifest(origin)
    shutil.copytree(origin, tmp_path / "data")
    dump(tmp_path / "data/latest.json", manifest)
    root = tmp_path / "data"
    report = tmp_path / "report.html"
    build(root, report)
    verify(root, report)
    data = histories(root, manifest)
    assert len(data[QVIX]) == manifest["feeds"][QVIX]["snapshot"]["count"]
    parser = Embedded()
    parser.feed(report.read_text())
    payload = json.loads(parser.payload)
    common = [p["data"][1] for p in payload["panels"]]
    assert all(t == common[0] for t in common)
    snap = manifest["feeds"][QVIX]["snapshot"]
    for field in ("csv", "wrapper", "quality"):
        path = root / snap[field]
        before = path.read_bytes()
        path.write_bytes(before + b"\n")
        with pytest.raises(ValueError):
            validate_manifest(root, manifest)
        path.write_bytes(before)
    raw_path = root / snap["raw"]["body"]
    before = raw_path.read_bytes()
    raw_path.write_bytes(before + b"\n")
    with pytest.raises(ValueError, match="capture hash|raw hash"):
        validate_manifest(root, manifest)
    raw_path.write_bytes(before)
    for field in ("count", "accounting"):
        broken = copy.deepcopy(manifest)
        target = broken["feeds"][QVIX]
        altered = copy.deepcopy(target["snapshot"])
        altered[field] = -1 if field == "count" else {}
        target["snapshot"] = target["attempt"] = altered
        with pytest.raises((ValueError, KeyError)):
            validate_manifest(root, broken)
    text = report.read_text()
    payload["panels"][3]["data"][1]["y"][0] += 1
    start = text.index('>', text.index('<script id="report-data"')) + 1
    end = text.index("</script>", start)
    report.write_text(text[:start] + json.dumps(payload) + text[end:])
    with pytest.raises(ValueError, match="trace arrays"):
        verify(root, report)


def install_qvix(root, manifest, name, records, window=WINDOW):
    """Persist genuine decoder-derived fixture artifacts; no production data touched."""
    manifest = copy.deepcopy(manifest)
    manifest["previous"] = artifact_ref(root, manifest["manifest_path"])
    manifest.update(run=f"runs/{name}", manifest_path=f"runs/{name}/manifest.json")
    directory = root / manifest["run"] / QVIX
    directory.mkdir(parents=True)
    for code in INDICES:
        if name != "clean":
            manifest["feeds"][code] = state_after(manifest["feeds"][code],
                                                  {"status": "failure", "attempted_at": name})
    body = source(records)
    wrapper = replay_qvix(body)
    cs = manifest["feeds"]["sh000001"]
    s = cs["snapshot"]
    comparator = {"csv": s["csv"], "csv_sha256": s["csv_sha256"],
                  "successful_at": s["successful_at"], "stale_reuse": cs["stale_reuse"],
                  "origin": s["origin"]}
    calendar = comparator_history(root, comparator)
    rows, quality, status = qvix_artifacts(body, wrapper, window, calendar, comparator)
    (directory / "response-0.body").write_bytes(body)
    (directory / "wrapper.csv").write_bytes(wrapper)
    content = csv_bytes(rows, [*OHLC, "quality"])
    (directory / "observations.csv").write_bytes(content)
    dump(directory / "quality.json", quality)
    snap = {"feed": QVIX, "schema": SCHEMA, "status": status,
            "successful_at": name, "attempted_at": name, "window": window,
            "csv": str((directory / "observations.csv").relative_to(root)), "csv_sha256": sha(content),
            "wrapper": str((directory / "wrapper.csv").relative_to(root)), "wrapper_sha256": sha(wrapper),
            "quality": str((directory / "quality.json").relative_to(root)),
            "quality_sha256": sha((directory / "quality.json").read_bytes()),
            "raw": {"body": str((directory / "response-0.body").relative_to(root)),
                    "sha256": sha(body), "status": 200, "encoding": "gbk"},
            "accounting": compact_quality(quality), "source_range": quality["full"]["range"],
            "count": len(rows), "range": quality["selected"]["range"]}
    dump(directory / "transport.json", [snap["raw"]])
    snap["transport"] = str((directory / "transport.json").relative_to(root))
    snap["transport_sha256"] = sha((directory / "transport.json").read_bytes())
    dump(directory / "result.json", snap)
    snap["origin"] = artifact_ref(root, str((directory / "result.json").relative_to(root))) | {"kind": "result"}
    manifest["feeds"][QVIX] = state_after(manifest["feeds"][QVIX], snap)
    promote(root, manifest)
    return manifest


def test_promoted_clean_partial_stale_correction_and_common_calendar(tmp_path):
    import shutil
    from app.chart import build
    from app.verify import verify

    root = tmp_path / "data"
    origin = Path(__file__).resolve().parents[1] / "data"
    shutil.copytree(origin, root)
    manifest = load_manifest(root)
    manifest["feeds"][QVIX] = state_after({}, {"status": "failure", "attempted_at": "initial"})
    clean = install_qvix(root, manifest, "clean", [("2024/1/2", 1, 2, 0, 1), ("2024/1/3", 1, 2, 0, 1)])
    assert clean["feeds"][QVIX]["snapshot"]["status"] == "success"
    # The comparator was fresh for clean; reused indices now disclose stale on later attempts.
    partial = install_qvix(root, clean, "partial", [
        ("2024/1/2", 1, 2, 0, 1), ("2024/1/2", 2, 2, 0, 1), ("2024/1/3", 1, 2, 0, 1)])
    assert partial["feeds"][QVIX]["snapshot"]["status"] == "partial"
    assert histories(root, partial)[QVIX][0]["close"] is None
    before = copy.deepcopy(partial["feeds"][QVIX]["snapshot"])
    failed = copy.deepcopy(partial)
    failed.update(run="runs/fatal", manifest_path="runs/fatal/manifest.json")
    failed["previous"] = artifact_ref(root, partial["manifest_path"])
    (root / failed["run"]).mkdir()
    failed["feeds"][QVIX] = state_after(failed["feeds"][QVIX],
                                       {"status": "failure", "attempted_at": "fatal"})
    promote(root, failed)
    assert load_manifest(root)["feeds"][QVIX]["snapshot"] == before
    assert failed["feeds"][QVIX]["stale_reuse"]
    report = tmp_path / "stale.html"
    build(root, report)
    verify(root, report)
    corrected = install_qvix(root, failed, "corrected", [("2024/1/3", 1, 2, 0, 1)])
    assert [r["date"] for r in histories(root, corrected)[QVIX]] == ["2024-01-03"]
    assert corrected["previous"] == artifact_ref(root, failed["manifest_path"])
    archived = json.loads((root / failed["manifest_path"]).read_text())
    assert archived["feeds"][QVIX]["snapshot"] == before
    assert read_csv(root / before["csv"])[0]["close"] is None
    assert "revisions" not in corrected["feeds"][QVIX]
    assert "dates" not in corrected["feeds"][QVIX]["snapshot"]["accounting"]
    old_quality = json.loads((root / before["quality"]).read_text())
    assert len(old_quality["dates"]["2024-01-02"]["occurrences"]) == 2
    build(root, report)
    from app.verify import Embedded
    parser = Embedded()
    parser.feed(report.read_text())
    payload = json.loads(parser.payload)
    assert payload["qvix_status"] == corrected["feeds"][QVIX]
    assert payload["panels"][0]["data"][1]["x"] == ["2024-01-03"]
    assert before["quality"] not in parser.payload
    verify(root, report)


def test_fetch_fatal_nonzero_and_sequential_eight_sources(tmp_path, monkeypatch):
    from app.fetch import fetch
    calls = []

    def fail_worker(command, **kwargs):
        feed, directory = command[4:6]
        calls.append(feed)
        dump(Path(directory) / "result.json",
             {"feed": feed, "status": "failure", "attempted_at": "fixture", "error": "offline"})

    monkeypatch.setattr("app.fetch.subprocess.run", fail_worker)
    assert fetch(tmp_path, *WINDOW) == 1
    assert calls == [*INDICES, QVIX]
    assert all(s["snapshot"] is None and not s["stale_reuse"]
               for s in load_manifest(tmp_path)["feeds"].values())


def test_wall_deadline_retains_received_capture(tmp_path, monkeypatch):
    import subprocess
    from app.fetch import fetch

    def deadline(command, **kwargs):
        feed, directory = command[4:6]
        directory = Path(directory)
        body = b"received before timeout"
        (directory / "response-0.body").write_bytes(body)
        dump(directory / "transport.json",
             [{"body": str(directory / "response-0.body"), "sha256": sha(body)}])
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr("app.fetch.subprocess.run", deadline)
    assert fetch(tmp_path, *WINDOW) == 1
    manifest = load_manifest(tmp_path)
    for state in manifest["feeds"].values():
        assert len(state["attempt"]["captures"]) == 1
        assert state["snapshot"] is None


@pytest.mark.parametrize("feed", [QVIX, "sh000001"])
@pytest.mark.parametrize("attack", ["delete_transport", "forged_time", "delete_and_forge", "delete_origin"])
def test_mandatory_provenance_and_original_time(feed, attack):
    root = Path(__file__).resolve().parents[1] / "data"
    manifest = copy.deepcopy(load_manifest(root))
    state = manifest["feeds"][feed]
    snap = state["snapshot"]
    state["attempt"] = snap
    if attack in ("delete_transport", "delete_and_forge"):
        snap.pop("transport")
        snap.pop("transport_sha256")
    if attack in ("forged_time", "delete_and_forge"):
        snap["successful_at"] = "2099-01-01T00:00:00+00:00"
        state["attempt"] = {"status": "failure", "attempted_at": "later"}
        state["stale_reuse"] = True
    if attack == "delete_origin":
        snap.pop("origin")
    with pytest.raises(ValueError, match="provenance|identity/time"):
        validate_manifest(root, manifest)


@pytest.mark.parametrize("window,expected_dates,expected_y", [
    (["2024-01-03", "2024-01-04"], ["2024-01-03", "2024-01-04"], [None, 1]),
    (["2024-01-03", "2024-01-03"], ["2024-01-03"], [None]),
    (["2024-01-01", "2024-01-02"], ["2024-01-02"], [1]),
])
def test_boundary_gaps_and_empty_selected_source(tmp_path, window, expected_dates, expected_y):
    import shutil
    from app.chart import build
    from app.verify import Embedded, verify
    root = tmp_path / "data"
    shutil.copytree(Path(__file__).resolve().parents[1] / "data", root)
    manifest = install_qvix(root, load_manifest(root), "boundary",
                           [("2024/1/2", 1, 2, 0, 1), ("2024/1/4", 1, 2, 0, 1)], window)
    snap = manifest["feeds"][QVIX]["snapshot"]
    expected_missing = ["2024-01-03"] if window[0] == "2024-01-03" else []
    assert snap["accounting"]["full"]["missing"] == ["2024-01-03"]
    assert snap["accounting"]["selected"]["missing"] == expected_missing
    assert snap["accounting"]["full"]["source_only"] == []
    report = tmp_path / "boundary.html"
    build(root, report)
    verify(root, report)
    parser = Embedded()
    parser.feed(report.read_text())
    trace = json.loads(parser.payload)["panels"][0]["data"][1]
    assert (trace["x"], trace["y"]) == (expected_dates, expected_y)


def test_narrow_window_does_not_invent_full_history_extras():
    body = source([("2024/1/2", 1, 2, 0, 1), ("2024/1/3", 1, 2, 0, 1)])
    calendar = {"2024-01-02", "2024-01-03"}
    window = ["2024-01-03", "2024-01-03"]
    comparator = {"stale_reuse": False}
    for derive_quality in (qvix_artifacts, independent_qvix):
        rows, quality, status = derive_quality(body, replay_qvix(body), window, calendar, comparator)
        assert status == "success"
        assert quality["full"]["source_only"] == quality["full"]["missing"] == []
        assert [r["date"] for r in rows] == ["2024-01-03"]


@pytest.mark.parametrize("condition", ["fresh", "stale", "unavailable"])
def test_visible_disclosure_removal_and_contradiction(tmp_path, condition):
    import html
    import re
    import shutil
    from app.chart import build
    from app.verify import verify
    root = tmp_path / "data"
    shutil.copytree(Path(__file__).resolve().parents[1] / "data", root)
    manifest = load_manifest(root)
    if condition != "fresh":
        manifest = copy.deepcopy(manifest)
        manifest.update(manifest_path=f"derived/{condition}/manifest.json")
        (root / manifest["manifest_path"]).parent.mkdir()
        for feed, state in manifest["feeds"].items():
            manifest["feeds"][feed] = state_after(
                state if condition == "stale" else {}, {"status": "failure", "attempted_at": "later"})
        promote(root, manifest)
    report = tmp_path / "report.html"
    build(root, report)
    verify(root, report)
    original = report.read_text()
    for kind in ("index", "qvix"):
        pattern = rf'<p class="[^"]+" id="{kind}-status-sh000300">.*?</p>'
        match = re.search(pattern, original)
        assert match
        for replacement in ("", match[0].replace("failure" if condition != "fresh" else
                                                "success" if kind == "index" else "partial", "forged", 1)):
            report.write_text(original[:match.start()] + replacement + original[match.end():])
            with pytest.raises(ValueError, match="visible .* disclosure"):
                verify(root, report)
        if kind == "index":
            snap = manifest["feeds"]["sh000300"]["snapshot"]
            swaps = [("本次尝试", "隐藏尝试"), ("发布前回溯", "隐藏回溯")]
            if condition != "unavailable":
                swaps += [("新鲜" if condition == "fresh" else "陈旧（沿用旧快照）", "无可用快照"),
                          (snap["range"][0], "1900-01-01"), (snap["successful_at"][:10], "2099-01-01"),
                          ("快照 success", "快照 partial")]
        elif condition != "unavailable":
            swaps = [("新鲜" if condition == "fresh" else "陈旧", "unavailable"),
                     ("快照 partial", "快照 success"), ("冲突 1", "冲突 0"), ("缺失 13", "缺失 0"),
                     ("2015-02-09", "2016-01-01")]
        else:
            swaps = [("无可用快照", "快照 success")]
        for old, new in swaps:
            assert old in html.unescape(match[0]), old
            replacement = match[0].replace(html.escape(old), html.escape(new), 1)
            report.write_text(original[:match.start()] + replacement + original[match.end():])
            with pytest.raises(ValueError, match="visible .* disclosure"):
                verify(root, report)


def test_fetch_narrow_window_replays_full_raw_comparator(tmp_path, monkeypatch):
    from app.core import decode, selected
    from app.fetch import fetch
    origin = Path(__file__).resolve().parents[1] / "data"
    retained = load_manifest(origin)["feeds"]["sh000001"]["snapshot"]

    def offline_worker(command, **kwargs):
        feed, directory, start, end = command[4:]
        directory = Path(directory)
        if feed not in ("sh000001", QVIX):
            dump(directory / "result.json", {"feed": feed, "status": "failure", "attempted_at": "offline"})
            return
        body = ((origin / retained["raw"]["body"]).read_bytes() if feed == "sh000001" else
                source([("2024/1/2", 1, 2, 0, 1), ("2024/1/3", 1, 2, 0, 1)]))
        raw = {"body": str(directory / "response-0.body"), "sha256": sha(body), "status": 200,
               "encoding": retained["raw"]["encoding"] if feed == "sh000001" else "gbk"}
        (directory / "response-0.body").write_bytes(body)
        dump(directory / "transport.json", [raw])
        result = {"feed": feed, "status": "success", "attempted_at": "offline",
                  "successful_at": "original-offline-time", "window": [start, end], "raw": raw}
        if feed == "sh000001":
            rows = selected(decode(feed, body, raw["encoding"]), start, end)
            content = csv_bytes(rows, ["close", "pre_release", "pre_base"])
            (directory / "observations.csv").write_bytes(content)
            result.update(csv=str(directory / "observations.csv"), csv_sha256=sha(content),
                          count=len(rows), range=[rows[0]["date"], rows[-1]["date"]],
                          identity=retained["identity"], retrospective_count=0)
        else:
            wrapper = replay_qvix(body)
            (directory / "wrapper.csv").write_bytes(wrapper)
            result.update(wrapper=str(directory / "wrapper.csv"), wrapper_sha256=sha(wrapper))
        dump(directory / "result.json", result)

    monkeypatch.setattr("app.fetch.subprocess.run", offline_worker)
    assert fetch(tmp_path, "2024-01-03", "2024-01-03") == 1  # Other indices intentionally unavailable.
    manifest = load_manifest(tmp_path)
    assert [r["date"] for r in histories(tmp_path, manifest)["sh000001"]] == ["2024-01-03"]
    snap = manifest["feeds"][QVIX]["snapshot"]
    assert snap["status"] == "success"
    assert snap["accounting"]["full"]["source_only"] == []
    assert snap["accounting"]["selected"]["dates"] == 1
    assert "2024-01-02" in comparator_history(tmp_path, snap["accounting"]["comparator"])
    validate_manifest(tmp_path, manifest)
