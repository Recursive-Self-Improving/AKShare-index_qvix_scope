import copy
import csv
import io
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from app.core import (
    INDICES, MAPPINGS, OHLC, QVIX_FEEDS, SCHEMA, artifact_ref, atomic, compact_quality,
    csv_bytes, dump, histories, load_manifest, qvix_artifacts, raw_qvix, read_csv,
    replay_qvix, sha, validate,
)
from app.fetch import fetch, group_worker, promote, recover_group, state_after
from app.verify import Embedded, independent_qvix, validate_manifest, verify

WINDOW = ["2000-01-01", "2026-11-16"]
FEED = "qvix_50etf"
ROOT = Path(__file__).resolve().parents[1]


def source(records, overrides=None):
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["", *map(str, range(2, 88))])
    for ordinal, (day, values) in enumerate(records):
        row = [day, *([""] * 86)]
        for feed, definition in QVIX_FEEDS.items():
            chosen = (overrides or {}).get(feed, {}).get(ordinal, values)
            for column, value in zip(definition["columns"][1:], chosen, strict=True):
                row[column] = value
        writer.writerow(row)
    return out.getvalue().encode("gbk")


def derive(records, calendar=None, window=WINDOW, feed=FEED, stale=False):
    body = source(records)
    wrapper = replay_qvix(body, feed)
    comparator = {"stale_reuse": stale} if calendar is not None else None
    result = qvix_artifacts(body, wrapper, window, calendar, comparator, feed)
    assert result == independent_qvix(body, wrapper, window, calendar, comparator, feed)
    return result


def test_f2_exact_sets_nulls_and_zero_without_comparator():
    records = [(f"2024/1/{d}", v) for d, v in [
        (1, [""] * 4), (2, [1, 2, 0, 1]), (3, [""] * 4),
        (4, [1, 2, 0, "#NUM!"]), (5, [0, 0, 0, 0]), (6, [""] * 4)]]
    calendar = {"2024-01-02", "2024-01-04", "2024-01-05"}
    window = ["2024-01-03", "2024-01-06"]
    rows, q, status = derive(records, calendar, window)
    assert status == "partial"
    assert [(r["date"], r["close"]) for r in rows] == [
        ("2024-01-03", None), ("2024-01-04", None), ("2024-01-05", 0), ("2024-01-06", None)]
    assert q["full"]["range"] == q["full"]["close_range"] == ["2024-01-02", "2024-01-05"]
    assert q["sets"]["blank_prefix"] == ["2024-01-01"]
    assert q["sets"]["blank_internal"] == ["2024-01-03"]
    assert q["sets"]["blank_tail"] == ["2024-01-06"]
    assert q["sets"]["invalid_close"] == q["sets"]["holes"] == ["2024-01-04"]
    assert q["sets"]["blank_source_only"] == ["2024-01-01", "2024-01-03", "2024-01-06"]
    assert q["selected"]["holes"] == 1
    unknown, uq, _ = derive(records, None, window)
    assert unknown == rows and uq["full"]["holes"] is None


@pytest.mark.parametrize("prior", [False, True])
@pytest.mark.parametrize("records,source_bounds", [
    ([("2024/1/2", [""] * 4)], None),
    ([("2024/1/2", ["#VALUE!"] * 4)], ["2024-01-02"] * 2),
    ([("2024/1/2", [1, 2, 0, 1]), ("2024/1/2", [2, 2, 0, 1])], ["2024-01-02"] * 2),
])
def test_fresh_no_close_replaces_prices_with_evidence(prior, records, source_bounds):
    rows, q, status = derive(records, {"2024-01-02"})
    assert status == "partial" and all(r["close"] is None for r in rows)
    assert q["full"]["range"] == source_bounds and q["full"]["close_range"] is None
    old = state_after({}, {"status": "success", "csv": "old-prices"}) if prior else {}
    fresh = state_after(old, {"status": status, "accounting": compact_quality(q), "rows": rows})
    assert fresh["snapshot"]["rows"] == rows and not fresh["stale_reuse"]
    failed = state_after(fresh, {"status": "failure"})
    assert failed["snapshot"] == fresh["snapshot"] and failed["stale_reuse"]
    assert state_after({}, {"status": "failure"})["snapshot"] is None


def test_full_history_with_empty_selection_keeps_status_and_full_holes():
    records = [("2024/1/2", [1, 2, 0, 1]), ("2024/1/4", [1, 2, 0, 1])]
    rows, q, status = derive(records, {"2024-01-02", "2024-01-03", "2024-01-04"},
                             ["2024-01-03", "2024-01-03"])
    assert status == "partial" and [(r["date"], r["close"]) for r in rows] == [("2024-01-03", None)]
    assert q["selected"]["range"] is None and q["selected"]["close_range"] is None
    assert q["selected"]["holes"] == q["full"]["holes"] == 1
    rows, q, status = derive(records, {"2024-01-02", "2024-01-04"}, ["2025-01-01", "2025-01-02"])
    assert status == "success" and rows == [] and q["full"]["close_range"] == ["2024-01-02", "2024-01-04"]


def test_hole_partition_collisions_source_only_errors_and_error_tail():
    records = [
        ("2024/1/1", [""] * 4), ("2024/1/2", [1, 2, 0, 1]), ("2024/1/2", [""] * 4),
        ("2024/1/4", [""] * 4), ("2024/1/5", [1, 2, 0, "#N/A"]),
        ("2024/1/6", [1, 2, 0, ""]), ("2024/1/7", [1, 2, 0, 1]),
        ("2024/1/7", [2, 2, 0, 1]), ("2024/1/8", ["#NAME?"] * 4),
        ("2024/1/9", [1, 2, 0, 1]), ("2024/1/10", ["#NUM!"] * 4)]
    calendar = {f"2024-01-{d:02}" for d in range(2, 10)}
    calendar.remove("2024-01-08")
    rows, q, _ = derive(records, calendar)
    sets = q["sets"]
    expected = {"absent": ["2024-01-03"], "blank": ["2024-01-04"],
                "invalid_close": ["2024-01-05"], "missing_close": ["2024-01-06"],
                "conflict_holes": ["2024-01-07"]}
    for key, values in expected.items():
        assert sets[key] == values
    assert sets["holes"] == [f"2024-01-{d:02}" for d in range(3, 8)]
    assert sets["source_only"] == ["2024-01-08", "2024-01-10"]
    assert q["full"]["range"][-1] == "2024-01-10" and q["full"]["close_range"][-1] == "2024-01-09"
    assert q["full"]["blank_collision_rows"] == 1 and sets["blank_collision"] == ["2024-01-02"]
    assert q["dates"]["2024-01-02"]["blank_ordinals"] == [3]
    assert next(r for r in rows if r["date"] == "2024-01-02")["close"] == 1
    assert rows[-1]["close"] is None


def test_invalid_nonclose_retains_close_exact_token_and_ordinal():
    rows, q, status = derive([("2024/1/2", ["22。27", "#VALUE!", 0, 1])], {"2024-01-02"})
    assert status == "partial" and rows[0]["close"] == 1 and rows[0]["open"] is None
    candidate = q["dates"]["2024-01-02"]["occurrences"][0]
    assert candidate["invalid"] == {"open": "22。27", "high": "#VALUE!"} and candidate["ordinal"] == 1
    assert q["full"]["invalid_fields"] == 2 and q["full"]["holes"] == 0


def test_duplicates_full_tuple_missing_invalid_and_zero_notice():
    rows, q, status = derive([("2024/1/2", [0, 2, 0, 1]), ("2024/1/2", [-0.0, 2.0, 0, 1])],
                             {"2024-01-02"})
    assert status == "success" and q["full"]["exact_duplicates"] == 1 and q["full"]["zero_rows"] == 2
    for a, b in [([1, 2, 0, 1], [2, 2, 0, 1]), (["", 2, 0, 1], ["#N/A", 2, 0, 1])]:
        rows, q, status = derive([("2024/1/2", a), ("2024/1/2", b)], {"2024-01-02"})
        assert status == "partial" and all(rows[0][k] is None for k in OHLC)
        assert q["full"]["conflict"] == 1


@pytest.mark.parametrize("bad", ["nan", "NaN", "inf", "-inf", "1e9999"])
def test_numeric_nonfinite_fatal_even_outside_window(bad):
    body = source([("1999/1/1", [bad, 2, 0, 1]), ("2024/1/2", [1, 2, 0, 1])])
    with pytest.raises(ValueError, match="nonfinite"):
        qvix_artifacts(body, replay_qvix(body, FEED), ["2024-01-01", "2024-12-31"],
                       None, None, FEED)


@pytest.mark.parametrize("bad", ["1999/2/29", "1999-01-01", "1999/01/1", "1999/1/1oops"])
def test_dates_fatal_outside_window(bad):
    with pytest.raises(ValueError):
        raw_qvix(source([(bad, [1, 2, 0, 1])]), FEED)


def test_cache_isolation_member_columns_and_wrapper_substitution():
    body = source([("2024/1/2", [1, 2, 0, 1])], {"qvix_50index": {0: [10, 20, 0, 10]}})
    for feed in QVIX_FEEDS:
        wrapper = replay_qvix(body, feed)
        rows, _, _ = qvix_artifacts(body, wrapper, WINDOW, None, None, feed)
        assert rows[0]["close"] == (10 if feed == "qvix_50index" else 1)
    with pytest.raises(ValueError, match="raw/wrapper"):
        qvix_artifacts(body, replay_qvix(body, "qvix_50index"), WINDOW, None, None, FEED)
    alternate = source([("2024/1/2", [1, 3, 0, 2])])
    assert list(csv.DictReader(io.StringIO(replay_qvix(alternate, FEED).decode())))[0]["close"] == "2"


def install_http(monkeypatch, body=None, status=200, failure=False):
    import requests
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        if failure:
            raise requests.ConnectionError("fixture shared load failure")
        response = requests.Response()
        response.status_code = status
        response.url = url
        response.request = requests.Request("GET", url).prepare()
        response._content = body
        kwargs["hooks"]["response"](response)
        return response
    monkeypatch.setattr(requests, "get", get)
    return calls


def group_fixture(tmp_path):
    directory = tmp_path / "runs/fixture/qvix-group"
    directory.mkdir(parents=True)
    atomic(directory / "config.json", {"group_id": "fixture", "window": WINDOW,
                                      "comparators": dict.fromkeys(QVIX_FEEDS)})
    return directory


def test_shared_loader_failure_invokes_once(tmp_path, monkeypatch):
    directory = group_fixture(tmp_path)
    calls = install_http(monkeypatch, failure=True)
    group_worker(directory)
    results = recover_group(tmp_path, directory)
    assert len(calls) == 1
    assert [r["invoked"] for r in results.values()] == [True, *([False] * 6)]
    assert all(r["status"] == "failure" for r in results.values())


def test_wrapper_local_failure_does_not_stop_or_reload_siblings(tmp_path, monkeypatch):
    import akshare as ak
    directory = group_fixture(tmp_path)
    calls = install_http(monkeypatch, source([("2024/1/2", [1, 2, 0, 1])]))
    def local():
        raise ValueError("local wrapper failure before loader")
    monkeypatch.setattr(ak, "index_option_50index_qvix", local)
    group_worker(directory)
    results = recover_group(tmp_path, directory)
    assert len(calls) == 1 and results["qvix_50index"]["status"] == "failure"
    assert all(r["invoked"] and r["status"] == "partial" for f, r in results.items() if f != "qvix_50index")


def test_completed_sibling_survives_termination_unfinished_only_own_prior(tmp_path, monkeypatch):
    import akshare as ak
    directory = group_fixture(tmp_path)
    calls = install_http(monkeypatch, source([("2024/1/2", [1, 2, 0, 1])]))
    def killed():
        raise SystemExit("terminated after completed sibling")
    monkeypatch.setattr(ak, "index_option_50etf_qvix", killed)
    with pytest.raises(SystemExit):
        group_worker(directory)
    results = recover_group(tmp_path, directory, "wall deadline 45")
    assert len(calls) == 1 and results["qvix_50index"]["status"] == "partial"
    assert results[FEED]["invoked"] and results[FEED]["status"] == "failure"
    assert not results["qvix_100etf"]["invoked"]
    old = {"snapshot": {"feed": FEED, "status": "success", "csv": "own-prior"}}
    state = state_after(old, results[FEED])
    assert state["stale_reuse"] and state["snapshot"] == old["snapshot"]
    assert not state_after({}, results["qvix_50index"])["stale_reuse"]


@pytest.mark.parametrize("attack", ["width", "date", "status"])
def test_global_failure_no_completed_feed(tmp_path, monkeypatch, attack):
    directory = group_fixture(tmp_path)
    body = source([("2024/1/2", [1, 2, 0, 1])])
    if attack == "width":
        body = body.rstrip(b"\n") + b",oops\n"
    if attack == "date":
        body = body.replace(b"2024/1/2", b"2024/2/30")
    calls = install_http(monkeypatch, body, 503 if attack == "status" else 200)
    group_worker(directory)
    results = recover_group(tmp_path, directory)
    assert len(calls) == 1 and all(r["status"] == "failure" for r in results.values())
    assert sum(r["invoked"] for r in results.values()) == 1


def test_member_nonfinite_isolated_after_shared_validation(tmp_path, monkeypatch):
    directory = group_fixture(tmp_path)
    body = source([("2024/1/2", [1, 2, 0, 1])], {"qvix_50index": {0: ["inf", 2, 0, 1]}})
    calls = install_http(monkeypatch, body)
    group_worker(directory)
    results = recover_group(tmp_path, directory)
    assert len(calls) == 1 and results["qvix_50index"]["status"] == "failure"
    assert results[FEED]["status"] == "partial"


@pytest.mark.parametrize("attack", ["incomplete", "crossfeed", "body", "time", "columns", "origin"])
def test_recovery_rejects_member_substitution_and_incomplete_commit(tmp_path, monkeypatch, attack):
    directory = group_fixture(tmp_path)
    install_http(monkeypatch, source([("2024/1/2", [1, 2, 0, 1])]))
    group_worker(directory)
    path = directory / FEED / "result.json"
    result = json.loads(path.read_text())
    if attack == "incomplete":
        path.write_text('{"status":')
    elif attack == "body":
        (directory / "response-0.body").write_bytes(b"forged")
    else:
        if attack == "crossfeed":
            result["feed"] = "qvix_50index"
        elif attack == "time":
            result["acquired_at"] = "2099-01-01"
        elif attack == "columns":
            result["columns"] = QVIX_FEEDS["qvix_50index"]["columns"]
        elif attack == "origin":
            result["csv"] = str((directory / "qvix_50index/observations.csv").relative_to(tmp_path))
        dump(path, result)
    recovered = recover_group(tmp_path, directory)
    assert recovered[FEED]["status"] == "failure"
    assert recovered["qvix_100etf"]["status"] == ("failure" if attack == "body" else "partial")


@pytest.mark.parametrize("prior", [False, True])
@pytest.mark.parametrize("field", ["attempted_at", "successful_at", "finished_at", "acquired_at"])
@pytest.mark.parametrize("bad", ["missing", None, "", "2024-02-30T12:00:00Z", "2024-01-02T12:00:00"])
def test_native_completion_times_fail_locally_preserve_pointer_and_chart(
        tmp_path, monkeypatch, prior, field, bad):
    from app.chart import build
    from app.fetch import completed
    directory = group_fixture(tmp_path)
    install_http(monkeypatch, source([("2024/1/2", [1, 2, 0, 1])]))
    group_worker(directory)
    good = recover_group(tmp_path, directory)
    baseline = empty_manifest()
    if prior:
        for feed, result in good.items():
            baseline["feeds"][feed] = state_after({}, result)
    promote(tmp_path, baseline)
    pointer = (tmp_path / "latest.json").read_bytes()
    # A new native attempt, not a manifest mutation against an unchanged origin.
    current = tmp_path / "runs/current/qvix-group"
    current.mkdir(parents=True)
    dump(current / "config.json", json.loads((directory / "config.json").read_text()))
    group_worker(current)
    path = current / FEED / "result.json"
    result = json.loads(path.read_text())
    if bad == "missing":
        del result[field]
    else:
        result[field] = bad
    dump(path, result)
    direct = copy.deepcopy(baseline)
    direct["feeds"][FEED] = state_after({}, completed(tmp_path, path))
    with pytest.raises(ValueError, match="timestamp"):
        promote(tmp_path, direct)
    assert (tmp_path / "latest.json").read_bytes() == pointer
    recovered = recover_group(tmp_path, current)
    assert recovered[FEED]["status"] == "failure" and "timestamp" in recovered[FEED]["error"]
    assert all(r["status"] == "partial" for f, r in recovered.items() if f != FEED)
    manifest = copy.deepcopy(baseline)
    manifest["manifest_path"] = "recovered.json"
    for feed, value in recovered.items():
        manifest["feeds"][feed] = state_after(baseline["feeds"][feed], value)
    state = manifest["feeds"][FEED]
    assert state["stale_reuse"] == prior
    assert state["snapshot"] == (good[FEED] if prior else None)
    promote(tmp_path, manifest)
    report = tmp_path / "recovered.html"
    build(tmp_path, report)
    verify(tmp_path, report)
    parser = Embedded()
    parser.feed(report.read_text())
    panel = json.loads(parser.payload)["panels"][0]
    assert panel["data"][2]["y"] == ([1.0] if prior else [])


@pytest.mark.parametrize("field", ["acquired_at", "retrieved_at"])
@pytest.mark.parametrize("bad", [None, "not-a-time"])
def test_native_shared_original_times_rejected(tmp_path, monkeypatch, field, bad):
    from app.core import artifact_ref
    directory = group_fixture(tmp_path)
    install_http(monkeypatch, source([("2024/1/2", [1, 2, 0, 1])]))
    group_worker(directory)
    group = json.loads((directory / "group.json").read_text())
    target = group if field == "acquired_at" else group["raw"]
    if bad is None:
        del target[field]
    else:
        target[field] = bad
    dump(directory / "group.json", group)
    # Bind to the mutated immutable shared origin, not its old hash.
    for feed in QVIX_FEEDS:
        path = directory / feed / "result.json"
        result = json.loads(path.read_text())
        result["shared"] = artifact_ref(tmp_path, str((directory / "group.json").relative_to(tmp_path)))
        dump(path, result)
    recovered = recover_group(tmp_path, directory)
    assert all(r["status"] == "failure" and "timestamp" in r["error"] for r in recovered.values())


def empty_manifest():
    return {"schema": SCHEMA, "run": "runs/empty", "window": WINDOW,
            "manifest_path": "manifest.json", "feeds": {
                f: state_after({}, {"status": "failure", "attempted_at": "fixture"})
                for f in [*INDICES, *QVIX_FEEDS]}}


def test_atomic_validation_and_rename_failure_preserve_pointer(tmp_path, monkeypatch):
    manifest = empty_manifest()
    promote(tmp_path, manifest)
    before = (tmp_path / "latest.json").read_bytes()
    broken = copy.deepcopy(manifest)
    broken["feeds"][FEED]["stale_reuse"] = True
    with pytest.raises(ValueError):
        promote(tmp_path, broken)
    assert (tmp_path / "latest.json").read_bytes() == before
    def interrupt(*args):
        raise OSError("interrupted atomic rename")
    monkeypatch.setattr("app.core.os.replace", interrupt)
    with pytest.raises(OSError):
        promote(tmp_path, manifest)
    assert (tmp_path / "latest.json").read_bytes() == before


def test_fetch_sequential_workers_and_timeout_evidence(tmp_path, monkeypatch):
    calls = []
    def deadline(command, **kwargs):
        calls.append(command[3])
        if command[3] == "--group-worker":
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        directory = Path(command[5])
        body = b"received before timeout"
        (directory / "response-0.body").write_bytes(body)
        dump(directory / "transport.json", [{"body": str((directory / "response-0.body").relative_to(tmp_path)),
                                            "sha256": sha(body)}])
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])
    monkeypatch.setattr("app.fetch.subprocess.run", deadline)
    assert fetch(tmp_path, *WINDOW) == 1
    assert calls == ["--worker"] * 8 + ["--group-worker"]
    manifest = load_manifest(tmp_path)
    assert manifest["worker_wall_seconds"] == 45 and manifest["qvix_group_wall_seconds"] == 300
    assert all(manifest["feeds"][f]["attempt"]["request_timeout_seconds"] == [5, 300] for f in QVIX_FEEDS)
    assert all(manifest["feeds"][f]["attempt"]["captures"] for f in INDICES)
    assert all(s["snapshot"] is None for s in manifest["feeds"].values())


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), "3.5"])
def test_invalid_index_close(value):
    with pytest.raises(ValueError):
        validate([{"date": "2024-01-02", "close": value}], ["close"])


def test_nullable_csv_and_legacy_schema_rejection(tmp_path):
    path = tmp_path / "null.csv"
    path.write_bytes(csv_bytes([dict(date="2024-01-02", **dict.fromkeys(OHLC), quality="conflict")],
                               [*OHLC, "quality"]))
    assert read_csv(path)[0]["close"] is None
    dump(tmp_path / "latest.json", {"schema": "qvix-comparison-v3"})
    with pytest.raises(ValueError, match="incompatible"):
        load_manifest(tmp_path)


@pytest.fixture(scope="module")
def active():
    return load_manifest(ROOT / "data")


def test_actual_active_artifacts_mapping_and_shared_trace_identity(active, tmp_path):
    from app.chart import build
    report = tmp_path / "report.html"
    build(ROOT / "data", report)
    verify(ROOT / "data", report)
    parser = Embedded()
    parser.feed(report.read_text())
    panels = json.loads(parser.payload)["panels"]
    assert [len(p["data"]) for p in panels] == [3, 3, 2, 3, 2, 2, 2, 2]
    seen = {}
    for panel in panels:
        for feed, trace in zip(MAPPINGS[panel["code"]], panel["data"][1:], strict=True):
            assert (trace["x"], trace["y"]) == seen.setdefault(feed, (trace["x"], trace["y"]))
    assert len(histories(ROOT / "data", active)["sz399330"]) >= 5053


@pytest.mark.parametrize("condition", ["fresh", "stale", "unavailable"])
def test_visible_per_feed_and_index_disclosure_tampering(active, tmp_path, condition):
    from app.chart import build
    root = tmp_path / "data"
    shutil.copytree(ROOT / "data", root)
    manifest = copy.deepcopy(active)
    if condition != "fresh":
        manifest["previous"] = artifact_ref(root, active["manifest_path"])
        manifest["manifest_path"] = "tamper-manifest.json"
        for feed, state in manifest["feeds"].items():
            manifest["feeds"][feed] = state_after(
                state if condition == "stale" else {}, {"status": "failure", "attempted_at": "later"})
        promote(root, manifest)
    report = tmp_path / "report.html"
    build(root, report)
    verify(root, report)
    original = report.read_text()
    ids = ["index-status-sh000300", "qvix-status-sh000300-qvix_300index",
           "qvix-status-sh000300-qvix_300etf"]
    for identity in ids:
        match = re.search(rf'<p class="[^"]+" id="{identity}">.*?</p>', original)
        assert match
        contradiction = re.sub(r" · [^·<]*</p>$", "</p>", match[0])
        assert contradiction != match[0]
        for replacement in ("", contradiction, match[0].replace("</p>", " · 已修复</p>"),
                            match[0].replace('<p ', '<p hidden '),
                            match[0].replace('<p ', '<p style="display:none" '),
                            '<div hidden>' + match[0] + '</div>',
                            '<div style="display:none">' + match[0] + '</div>',
                            '<details>' + match[0] + '</details>',
                            '<template>' + match[0] + '</template>',
                            match[0].replace('>', '><span hidden>', 1).replace('</p>', '</span></p>')):
            report.write_text(original[:match.start()] + replacement + original[match.end():])
            with pytest.raises(ValueError, match="disclosure"):
                verify(root, report)
    for old, new in [
        ('<div class="status">', '<div class="status" hidden>'),
        ('<div class="status">', '<div class="status" style="display:none">'),
        ('<div class="status">', '<div class="status" class="notes">'),
        ('class="quality warn"', 'class="quality ok"'),
        ('<div class="scroll">', '<div class="scroll" hidden>'),
        ('<table class="grid" id="quality-table">', '<table class="grid" id="quality-table" style="display:none">'),
        ('<div class="stats" id="summary">', '<div class="stats" id="summary" hidden>'),
        ('<div class="stats" id="summary">', '<details><div class="stats" id="summary">'),
        ('<td class="mono">', '<td class="mono"><span hidden>'),
        ('<span>指数</span>', '<span>指数（已修复）</span>'),
        ('<tbody><tr>', '<tbody><tr hidden>'),
        ('<b>', '<b style="display:none">'),
        ('class="index-status ' + ("ok" if condition == "fresh" else "warn") + '"',
         'class="index-status ' + ("warn" if condition == "fresh" else "ok") + '"'),
        ('<body>', '<body hidden>'),
        ('<main>', '<main style="display:none">'),
    ]:
        if old not in original:
            assert condition == "unavailable" and "mono" in old
            continue
        report.write_text(original.replace(old, new, 1))
        with pytest.raises(ValueError, match="disclosure"):
            verify(root, report)
    hashes = re.findall(r'<td class="mono">([0-9a-f]{12})</td>', original)
    assert len(hashes) == (0 if condition == "unavailable" else 7)
    for value in hashes[:1]:
        report.write_text(original.replace(value, "0" * 12, 1))
        with pytest.raises(ValueError, match="quality table disclosure"):
            verify(root, report)


@pytest.mark.parametrize("feed", [FEED, "sh000001"])
@pytest.mark.parametrize("attack", ["origin", "time", "transport"])
def test_mandatory_provenance_and_original_time(active, feed, attack):
    root = ROOT / "data"
    manifest = copy.deepcopy(active)
    manifest["previous"] = artifact_ref(root, active["manifest_path"])
    snap = manifest["feeds"][feed]["snapshot"]
    if attack == "origin":
        snap.pop("origin")
    elif attack == "time":
        snap["successful_at"] = "2099-01-01"
    elif feed in QVIX_FEEDS:
        snap.pop("shared")
    else:
        snap.pop("transport")
    manifest["feeds"][feed]["attempt"] = snap
    error = "mandatory origin provenance" if attack == "origin" else "immutable revision identity/time"
    with pytest.raises(ValueError, match=error):
        validate_manifest(root, manifest)


def test_stale_comparator_is_partial_without_mutating_calendar():
    records = [("2024/1/2", [1, 2, 0, 1])]
    _, q, status = derive(records, {"2024-01-02"}, stale=True)
    assert status == "partial" and q["full"]["holes"] == 0 and q["comparator"]["stale_reuse"]


@pytest.mark.parametrize("records", [
    [("2024/1/2", [""] * 4)],
    [("2024/1/2", ["#VALUE!"] * 4)],
    [("2024/1/2", [1, 2, 0, 1]), ("2024/1/2", [2, 2, 0, 1])],
])
def test_durable_no_close_snapshot_survives_parent_and_renders_null(tmp_path, monkeypatch, records):
    from app.chart import build
    directory = group_fixture(tmp_path)
    install_http(monkeypatch, source(records))
    group_worker(directory)
    recovered = recover_group(tmp_path, directory)
    manifest = empty_manifest()
    for feed, result in recovered.items():
        manifest["feeds"][feed] = state_after({"snapshot": {"csv": "obsolete-prices"}}, result)
        assert result["status"] == "partial" and not manifest["feeds"][feed]["stale_reuse"]
        assert result["accounting"]["full"]["close_range"] is None
    promote(tmp_path, manifest)
    report = tmp_path / "no-close.html"
    build(tmp_path, report)
    verify(tmp_path, report)
    parser = Embedded()
    parser.feed(report.read_text())
    payload = json.loads(parser.payload)
    assert all(v is None for p in payload["panels"] for t in p["data"][1:] for v in t["y"])


def test_member_commit_atomic_failure_does_not_publish_incomplete_prices(tmp_path, monkeypatch):
    directory = group_fixture(tmp_path)
    install_http(monkeypatch, source([("2024/1/2", [1, 2, 0, 1])]))
    real_atomic = atomic
    def interrupted(path, value):
        if Path(path).name == "result.json":
            raise OSError("power loss before completion rename")
        real_atomic(path, value)
    monkeypatch.setattr("app.fetch.atomic", interrupted)
    with pytest.raises(OSError):
        group_worker(directory)
    assert (directory / "qvix_50index/wrapper.csv").exists()
    results = recover_group(tmp_path, directory, "crash")
    assert all(r["status"] == "failure" for r in results.values())
    assert results["qvix_50index"]["invoked"] and not results[FEED]["invoked"]


@pytest.fixture
def migrated_v4(tmp_path, active):
    from app.core import decode
    from app.fetch import bind_comparator, completed

    # Model the old standalone 50ETF acquisition and its manifest-based comparator.
    root = tmp_path
    legacy_dir = root / "runs/legacy"
    legacy_member = legacy_dir / FEED
    legacy_member.mkdir(parents=True)
    code = QVIX_FEEDS[FEED]["comparator"]
    index = active["feeds"][code]["snapshot"].copy()
    index.pop("origin")
    index_dir = legacy_dir / code
    index_dir.mkdir()
    csv_path = index_dir / "observations.csv"
    shutil.copyfile(ROOT / "data" / index["csv"], csv_path)
    raw_path = index_dir / "response-0.body"
    shutil.copyfile(ROOT / "data" / index["raw"]["body"], raw_path)
    index["raw"] = index["raw"] | {"body": str(raw_path.relative_to(root))}
    transport = index_dir / "transport.json"
    dump(transport, [index["raw"]])
    index.update(csv=str(csv_path.relative_to(root)), transport=str(transport.relative_to(root)),
                 transport_sha256=sha(transport.read_bytes()))
    calendar = {r["date"] for r in decode(code, raw_path.read_bytes(), index["raw"]["encoding"])}

    window = ["2024-01-02", "2024-01-04"]
    body = source([("2024/1/2", [1, 2, 1, 2]), ("2024/1/4", [2, 3, 1, 3])])
    wrapper = replay_qvix(body, FEED)
    raw_path = legacy_member / "response-0.body"
    raw_path.write_bytes(body)
    url = QVIX_FEEDS[FEED]["url"]
    acquired = "2024-01-05T00:00:01Z"
    raw = {"body": str(raw_path.relative_to(root)), "sha256": sha(body), "status": 200,
           "url": url, "requested_url": url, "encoding": "gbk", "retrieved_at": acquired}
    transport = legacy_member / "transport.json"
    dump(transport, [raw])
    evidence = {"raw": raw, "transport": str(transport.relative_to(root)),
                "transport_sha256": sha(transport.read_bytes())}
    fields = [*OHLC, "quality"]
    legacy_rows, _, legacy_status = qvix_artifacts(body, wrapper, window, None, None, FEED)
    wrapper_path = legacy_member / "wrapper.csv"
    wrapper_path.write_bytes(wrapper)
    legacy_csv = legacy_member / "observations.csv"
    legacy_csv.write_bytes(csv_bytes(legacy_rows, fields))
    original = {
        "feed": FEED, "schema": "qvix-comparison-v2", "status": legacy_status, "window": window,
        "attempted_at": "2024-01-05T00:00:00Z", "successful_at": "2024-01-05T00:00:02Z",
        "finished_at": "2024-01-05T00:00:03Z", "wrapper": str(wrapper_path.relative_to(root)),
        "wrapper_sha256": sha(wrapper), "csv": str(legacy_csv.relative_to(root)),
        "csv_sha256": sha(legacy_csv.read_bytes()), **evidence,
    }
    legacy_manifest = legacy_dir / "manifest.json"
    dump(legacy_manifest, {"schema": original["schema"], "feeds": {
        FEED: state_after({}, original), code: state_after({}, index)}})
    origin = artifact_ref(root, str(legacy_manifest.relative_to(root))) | {"kind": "manifest"}
    index_state = state_after({}, index | {"origin": origin})
    comparator = bind_comparator(FEED, {code: index_state})

    # A derived completion binds the old acquisition and reaccounts against its calendar.
    directory = root / "derived/v4"
    member = directory / FEED
    member.mkdir(parents=True)
    group = directory / "group.json"
    group_id = "derived-v4-fixture"
    dump(group, evidence | {"group_id": group_id, "global_validated": True, "acquired_at": acquired})
    rows, quality, status = qvix_artifacts(body, wrapper, window, calendar, comparator, FEED)
    csv_path, quality_path = member / "observations.csv", member / "quality.json"
    csv_path.write_bytes(csv_bytes(rows, fields))
    dump(quality_path, quality)
    result_path = member / "result.json"
    result = {k: original[k] for k in (
        "feed", "window", "attempted_at", "successful_at", "finished_at", "wrapper", "wrapper_sha256")}
    dump(result_path, result | {
        "schema": SCHEMA, "status": status, "migration": origin, "invoked": True,
        "columns": QVIX_FEEDS[FEED]["columns"], "invocation": QVIX_FEEDS[FEED]["wrapper"] + "()",
        "shared": artifact_ref(root, str(group.relative_to(root))),
        "group_id": group_id, "acquired_at": acquired, "accounting": compact_quality(quality),
        "count": len(rows), "range": window, "source_range": window,
        "csv": str(csv_path.relative_to(root)), "csv_sha256": sha(csv_path.read_bytes()),
        "quality": str(quality_path.relative_to(root)), "quality_sha256": sha(quality_path.read_bytes()),
    })
    manifest = empty_manifest() | {"window": window, "operation": "format-migration"}
    manifest["feeds"][code] = index_state
    manifest["feeds"][FEED] = state_after({}, completed(root, result_path))
    return root, manifest


def test_explicit_derived_v4_migration_preserves_original_times_and_artifacts(migrated_v4):
    root, manifest = migrated_v4
    verified = validate_manifest(root, manifest)
    snap = manifest["feeds"][FEED]["snapshot"]
    source_manifest = json.loads((root / snap["migration"]["path"]).read_text())
    original = source_manifest["feeds"][FEED]["snapshot"]
    assert all(snap[k] == original[k] for k in ("attempted_at", "successful_at", "finished_at"))
    assert snap["wrapper"] == original["wrapper"] and snap["csv"] != original["csv"]
    assert snap["csv_sha256"] != original["csv_sha256"]
    assert snap["accounting"]["comparator"]["origin"] == snap["migration"]
    assert snap["accounting"]["full"]["holes"] == snap["accounting"]["selected"]["holes"] == 1
    assert [(row["date"], row["close"]) for row in verified[FEED]] == [
        ("2024-01-02", 2.0), ("2024-01-03", None), ("2024-01-04", 3.0)]
    assert all(manifest["feeds"][f]["snapshot"] is None for f in QVIX_FEEDS if f != FEED)


def test_fetch_narrow_window_uses_full_retained_comparator(tmp_path, monkeypatch, active):
    from app.core import decode, selected
    def offline(command, **kwargs):
        if command[3] == "--group-worker":
            group_worker(Path(command[4]))
            return
        feed, directory, start, end = command[4:]
        directory = Path(directory)
        original = active["feeds"][feed]["snapshot"]
        body = (ROOT / "data" / original["raw"]["body"]).read_bytes()
        raw = original["raw"] | {"body": str((directory / "response-0.body").relative_to(tmp_path))}
        (directory / "response-0.body").write_bytes(body)
        dump(directory / "transport.json", [raw])
        rows = selected(decode(feed, body, raw["encoding"]), start, end)
        content = csv_bytes(rows, ["close", "pre_release", "pre_base"])
        (directory / "observations.csv").write_bytes(content)
        result = {k: original[k] for k in ("feed", "identity", "attempted_at", "successful_at", "finished_at")}
        result.update(status="success", window=[start, end], raw=raw, count=len(rows),
                      range=[rows[0]["date"], rows[-1]["date"]] if rows else None,
                      retrospective_count=sum(r["pre_release"] for r in rows),
                      csv=str((directory / "observations.csv").relative_to(tmp_path)),
                      csv_sha256=sha(content), transport=str((directory / "transport.json").relative_to(tmp_path)),
                      transport_sha256=sha((directory / "transport.json").read_bytes()))
        dump(directory / "result.json", result)
    monkeypatch.setattr("app.fetch.subprocess.run", offline)
    install_http(monkeypatch, source([("2024/1/2", [1, 2, 0, 1]), ("2024/1/4", [1, 2, 0, 1])]))
    assert fetch(tmp_path, "2024-01-03", "2024-01-03") == 1
    manifest = load_manifest(tmp_path)
    q = manifest["feeds"][FEED]["snapshot"]["accounting"]
    assert q["full"]["holes"] == q["selected"]["holes"] == 1
    assert q["full"]["source_only"] == 0
    assert q["selected"]["range"] is None
    data = histories(tmp_path, manifest)
    assert data["sh000001"] == [{"date": "2024-01-03", "close": data["sh000001"][0]["close"],
                                 "pre_release": 0, "pre_base": 0}]
    assert [(r["date"], r["close"]) for r in data[FEED]] == [("2024-01-03", None)]


@pytest.mark.parametrize("artifact", ["wrapper.csv", "observations.csv", "quality.json"])
def test_durable_artifact_hash_failure_is_member_local(tmp_path, monkeypatch, artifact):
    directory = group_fixture(tmp_path)
    install_http(monkeypatch, source([("2024/1/2", [1, 2, 0, 1])]))
    group_worker(directory)
    path = directory / FEED / artifact
    path.write_bytes(path.read_bytes() + b"\n")
    results = recover_group(tmp_path, directory)
    assert results[FEED]["status"] == "failure"
    assert results["qvix_100etf"]["status"] == "partial"


@pytest.mark.parametrize("field", ["attempted_at", "successful_at", "finished_at"])
def test_derived_completion_cannot_replace_original_times(migrated_v4, field):
    from app.fetch import completed
    root, manifest = migrated_v4
    snap = manifest["feeds"][FEED]["snapshot"]
    path = root / snap["origin"]["path"]
    result = json.loads(path.read_text())
    result[field] = "2099-01-01T00:00:00Z"
    dump(path, result)
    manifest["feeds"][FEED] = state_after({}, completed(root, path))
    with pytest.raises(ValueError, match="migration origin/time"):
        validate_manifest(root, manifest)


@pytest.mark.parametrize("edit", ["clean", "zero_success", "no_comparator", "stale_comparator",
                                  "unknown", "window", "stale", "missing"])
def test_visible_qvix_edge_states_match_and_never_look_clean(active, edit):
    from app.chart import qvix_clean, qvix_line
    from app.verify import visible_qvix
    state = copy.deepcopy(active["feeds"]["qvix_50etf"])
    snap = state["snapshot"]
    q = snap["accounting"]
    for part in ("full", "selected"):
        q[part].update({k: 0 for k in ("holes", "conflict", "invalid_fields", "zero_rows", "source_only",
                                       "envelope_rows", "blank_internal", "blank_tail")})
    snap["status"] = "success"
    if edit == "zero_success":
        q["full"]["zero_rows"] = q["selected"]["zero_rows"] = 2
    elif edit == "no_comparator":
        q["comparator"] = None
    elif edit == "stale_comparator":
        q["comparator"]["stale_reuse"] = True
    elif edit == "unknown":
        q["full"]["holes"] = q["selected"]["holes"] = None
    elif edit == "window":
        q["selected"]["close_range"] = ["2020-01-02", "2026-11-13"]
        q["full"]["holes"] = 3
    elif edit == "stale":
        state.update(stale_reuse=True, attempt={"status": "failure", "attempted_at": "2026-11-17T00:00:00+00:00"})
    elif edit == "missing":
        state["snapshot"] = None
    text = qvix_line("qvix_50etf", state)
    assert text == visible_qvix("qvix_50etf", state)
    assert qvix_clean(state) == (edit == "clean")
    assert ("无质量异常" in text) == (edit in ("clean", "no_comparator", "stale_comparator", "stale"))
    if edit == "window":
        assert "窗口内收盘 2020-01-02" in text and "缺口 3（窗口内 0）" in text
