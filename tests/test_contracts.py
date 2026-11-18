import csv
import io
import json
import re
import subprocess
from pathlib import Path

import pytest

from app.core import (
    INDICES, MAPPINGS, OHLC, QVIX_FEEDS, artifact_ref, atomic,
    csv_bytes, dump, histories, load_manifest, qvix_artifacts, raw_qvix, read_csv,
    replay_qvix, sha, validate,
)
from app.fetch import acquire, completed, fetch, group_worker, main, recover_group, worker
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


@pytest.mark.parametrize("records,source_bounds", [
    ([("2024/1/2", [""] * 4)], None),
    ([("2024/1/2", ["#VALUE!"] * 4)], ["2024-01-02"] * 2),
    ([("2024/1/2", [1, 2, 0, 1]), ("2024/1/2", [2, 2, 0, 1])], ["2024-01-02"] * 2),
])
def test_fresh_no_close_is_partial_with_evidence(records, source_bounds):
    rows, q, status = derive(records, {"2024-01-02"})
    assert status == "partial" and all(r["close"] is None for r in rows)
    assert q["full"]["range"] == source_bounds and q["full"]["close_range"] is None


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
    directory = tmp_path / "current/qvix-group"
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


def test_completed_sibling_survives_termination(tmp_path, monkeypatch):
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
    assert results[FEED]["termination"] == results["qvix_100etf"]["termination"] == "wall deadline 45"


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


@pytest.mark.parametrize("field", ["attempted_at", "successful_at", "finished_at", "acquired_at"])
@pytest.mark.parametrize("bad", ["missing", None, "", "2024-02-30T12:00:00Z", "2024-01-02T12:00:00"])
def test_native_completion_times_fail_locally(tmp_path, monkeypatch, field, bad):
    from app.verify import validate_snapshot
    directory = group_fixture(tmp_path)
    install_http(monkeypatch, source([("2024/1/2", [1, 2, 0, 1])]))
    group_worker(directory)
    path = directory / FEED / "result.json"
    result = json.loads(path.read_text())
    if bad == "missing":
        del result[field]
    else:
        result[field] = bad
    dump(path, result)
    with pytest.raises(ValueError, match="timestamp"):
        validate_snapshot(tmp_path, completed(tmp_path, path), FEED)
    recovered = recover_group(tmp_path, directory)
    assert recovered[FEED]["status"] == "failure" and "timestamp" in recovered[FEED]["error"]
    assert all(r["status"] == "partial" for f, r in recovered.items() if f != FEED)


@pytest.mark.parametrize("field", ["acquired_at", "retrieved_at"])
@pytest.mark.parametrize("bad", [None, "not-a-time"])
def test_native_shared_original_times_rejected(tmp_path, monkeypatch, field, bad):
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


def test_acquire_sequential_workers_and_timeout_evidence(tmp_path, monkeypatch, capsys):
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
    monkeypatch.setattr("sys.argv", ["fetch", "--candidate", "--output", str(tmp_path),
                                     "--start", WINDOW[0], "--end", WINDOW[1]])
    assert main() == 1
    assert calls == ["--worker"] * 8 + ["--group-worker"]
    manifest = load_manifest(tmp_path)
    assert manifest["worker_wall_seconds"] == 45 and manifest["qvix_group_wall_seconds"] == 300
    assert all(manifest["feeds"][f]["attempt"]["request_timeout_seconds"] == [5, 300] for f in QVIX_FEEDS)
    assert all(manifest["feeds"][f]["attempt"]["captures"] for f in INDICES)
    assert all(s["snapshot"] is None for s in manifest["feeds"].values())
    assert all(not s["stale_reuse"] for s in manifest["feeds"].values())
    assert "worker exceeded 45s wall deadline" in capsys.readouterr().out
    with pytest.raises(FileExistsError, match="must be empty"):
        acquire(tmp_path, *WINDOW)


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), "3.5"])
def test_invalid_index_close(value):
    with pytest.raises(ValueError):
        validate([{"date": "2024-01-02", "close": value}], ["close"])


def test_nullable_csv_and_legacy_schema_rejection(tmp_path):
    path = tmp_path / "null.csv"
    path.write_bytes(csv_bytes([dict(date="2024-01-02", **dict.fromkeys(OHLC), quality="conflict")],
                               [*OHLC, "quality"]))
    assert read_csv(path)[0]["close"] is None
    path = tmp_path / "current/manifest.json"
    path.parent.mkdir()
    dump(path, {"schema": "qvix-comparison-v3"})
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


@pytest.mark.parametrize("condition", ["fresh", "unavailable"])
def test_visible_per_feed_and_index_disclosure_tampering(tmp_path, condition, offline_feeds):
    from app.chart import build
    root = tmp_path / "data"
    if condition == "fresh":
        offline_feeds["qvix"] = source([("2024/1/2", ["#VALUE!"] * 4)])
    else:
        offline_feeds["failed"].update([*INDICES, "qvix"])
    assert acquire(root, *WINDOW) == 1
    report = tmp_path / "report.html"
    build(root, report)
    verify(root, report)
    original = report.read_text()
    stamp = json.dumps(load_manifest(root)["attempted_at"])
    original_binding = f'"attempted_at": {stamp}'
    assert original_binding in original
    report.write_text(original.replace(original_binding, '"attempted_at": "2000-01-01T00:00:00Z"', 1))
    with pytest.raises(ValueError, match="HTML acquisition identity"):
        verify(root, report)
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
@pytest.mark.parametrize("attack", ["origin", "foreign_path", "time", "transport"])
def test_mandatory_provenance_and_original_time(tmp_path, offline_feeds, feed, attack):
    assert acquire(tmp_path, *WINDOW) == 0
    manifest = load_manifest(tmp_path)
    snap = manifest["feeds"][feed]["snapshot"]
    if attack == "origin":
        snap.pop("origin")
    elif attack == "foreign_path":
        completion = tmp_path / snap["origin"]["path"]
        other = completion.with_name("copy.json")
        other.write_bytes(completion.read_bytes())
        snap["origin"] = artifact_ref(tmp_path, str(other.relative_to(tmp_path))) | {"kind": "result"}
    elif attack == "time":
        snap["successful_at"] = "2099-01-01"
    elif feed in QVIX_FEEDS:
        snap.pop("shared")
    else:
        snap.pop("transport")
    manifest["feeds"][feed]["attempt"] = snap
    error = {"origin": "mandatory origin provenance", "foreign_path": "invalid acquisition origin"}.get(
        attack, "immutable revision identity/time")
    with pytest.raises(ValueError, match=error):
        validate_manifest(tmp_path, manifest)


def test_stale_comparator_is_partial_without_mutating_calendar():
    records = [("2024/1/2", [1, 2, 0, 1])]
    _, q, status = derive(records, {"2024-01-02"}, stale=True)
    assert status == "partial" and q["full"]["holes"] == 0 and q["comparator"]["stale_reuse"]


@pytest.mark.parametrize("records", [
    [("2024/1/2", [""] * 4)],
    [("2024/1/2", ["#VALUE!"] * 4)],
    [("2024/1/2", [1, 2, 0, 1]), ("2024/1/2", [2, 2, 0, 1])],
])
def test_durable_no_close_snapshot_survives_parent_and_renders_null(tmp_path, offline_feeds, records):
    from app.chart import build
    offline_feeds["qvix"] = source(records)
    assert fetch(tmp_path, *WINDOW) == 1
    manifest = load_manifest(tmp_path)
    state = manifest["feeds"][FEED]
    assert state["attempt"] == state["snapshot"] and not state["stale_reuse"]
    assert state["snapshot"]["accounting"]["full"]["close_range"] is None
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
def offline_feeds(monkeypatch):
    """Keep real worker logic and verification; replace subprocess and HTTP boundaries."""
    import akshare as ak
    import pandas as pd
    import requests
    from akshare.index.cons import zh_sina_index_stock_hist_url
    from akshare.utils import http

    feeds = {"qvix": source([(f"2024/1/{d}", [1, 2, 0, 1]) for d in (2, 3, 4)]),
             "failed": set(), "index_close": 10}
    urls = {zh_sina_index_stock_hist_url.format(f): f for f in INDICES}
    def sina(symbol):
        text = http.get(zh_sina_index_stock_hist_url.format(symbol)).text
        data = json.loads(text.split("=", 1)[1])
        return pd.DataFrame({"date": pd.to_datetime(list(data)).date, "close": list(data.values())})
    def get(url, **kwargs):
        feed = urls.get(url, "qvix")
        if feed in feeds["failed"]:
            raise requests.ConnectionError(f"offline failure: {feed}")
        if feed == "qvix":
            assert url == QVIX_FEEDS[FEED]["url"]
            body = feeds["qvix"]
        else:
            data = {f"2024-01-0{d}": feeds["index_close"] for d in (2, 3, 4)}
            body = f"var KLC_KL_{feed}={json.dumps(data)}".encode()
        response = requests.Response()
        response.status_code = 200
        response.url = url
        response.request = requests.Request("GET", url).prepare()
        response._content = body
        kwargs["hooks"]["response"](response)
        return response
    def run(command, **kwargs):
        if command[3] == "--group-worker":
            group_worker(command[4])
        else:
            assert command[3] == "--worker"
            worker(*command[4:])
    monkeypatch.setattr(ak, "index_zh_daily_sina", sina)
    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr("app.fetch.subprocess.run", run)
    return feeds


def current_bytes(root):
    return {path.relative_to(root): path.read_bytes() for path in (root / "current").rglob("*")
            if path.is_file()}


def test_fetch_overwrites_twice_then_preserves_dataset_on_fatal(tmp_path, offline_feeds, capsys):
    sibling = tmp_path / "static.json"
    sibling.write_text("not payload")
    assert fetch(tmp_path, *WINDOW) == 0
    obsolete = tmp_path / "current/obsolete"
    obsolete.touch()
    prior = load_manifest(tmp_path)

    offline_feeds["index_close"] = 20
    assert fetch(tmp_path, *WINDOW) == 0
    fresh = load_manifest(tmp_path)
    assert not obsolete.exists()
    assert fresh["attempted_at"] != prior["attempted_at"]
    assert histories(tmp_path, fresh)["sh000001"][0]["close"] == 20
    with pytest.raises(ValueError, match="observations do not match the loaded manifest"):
        histories(tmp_path, prior)  # A reader spanning replacement must not render mixed data.

    offline_feeds["index_close"] = 30
    offline_feeds["qvix"] = source([("2024/1/2", ["#VALUE!"] * 4)])
    assert fetch(tmp_path, *WINDOW) == 1
    partial = load_manifest(tmp_path)
    assert partial["attempted_at"] != fresh["attempted_at"]
    assert histories(tmp_path, partial)["sh000001"][0]["close"] == 30
    assert all(partial["feeds"][f]["snapshot"]["status"] == "partial" for f in QVIX_FEEDS)
    assert all(not state["stale_reuse"] for state in partial["feeds"].values())
    assert set(partial).isdisjoint({"run", "manifest_path", "previous"})
    before = current_bytes(tmp_path)
    offline_feeds["index_close"] = 40
    for failed in ("sh000001", "qvix"):
        offline_feeds["failed"] = {failed}
        assert fetch(tmp_path, *WINDOW) == 1
        assert current_bytes(tmp_path) == before
    assert "offline failure: sh000001" in capsys.readouterr().out
    assert {p.name for p in tmp_path.iterdir()} == {"current", sibling.name}
    assert sibling.read_text() == "not payload"


def test_fetch_does_not_replace_an_unrelated_current_directory(tmp_path, offline_feeds):
    local = tmp_path / "current" / "notes.txt"
    local.parent.mkdir()
    local.write_text("user data")
    with pytest.raises(FileExistsError, match="unmanaged directory"):
        fetch(tmp_path, *WINDOW)
    assert local.read_text() == "user data"


def test_fatal_first_fetch_has_no_live_payload(tmp_path, offline_feeds):
    offline_feeds["failed"].add("qvix")
    assert fetch(tmp_path, *WINDOW) == 1
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("failure", ["validation", "install"])
def test_fetch_validation_or_install_failure_preserves_live(tmp_path, monkeypatch, offline_feeds, failure):
    assert fetch(tmp_path, *WINDOW) == 0
    before = current_bytes(tmp_path)
    offline_feeds["index_close"] = 20

    def interrupt(*args):
        raise OSError(f"interrupted {failure}")
    symbol = "app.verify.validate_manifest" if failure == "validation" else "app.fetch._install_current"
    monkeypatch.setattr(symbol, interrupt)
    with pytest.raises(OSError, match=f"interrupted {failure}"):
        fetch(tmp_path, *WINDOW)
    assert current_bytes(tmp_path) == before
    assert {p.name for p in tmp_path.iterdir()} == {"current"}


def test_fetch_narrow_window_uses_full_retained_comparator(tmp_path, offline_feeds):
    offline_feeds["qvix"] = source([("2024/1/2", [1, 2, 0, 1]), ("2024/1/4", [1, 2, 0, 1])])
    assert fetch(tmp_path, "2024-01-03", "2024-01-03") == 1
    manifest = load_manifest(tmp_path)
    q = manifest["feeds"][FEED]["snapshot"]["accounting"]
    assert q["full"]["holes"] == q["selected"]["holes"] == 1
    assert q["full"]["source_only"] == 0
    assert q["selected"]["range"] is None
    data = histories(tmp_path, manifest)
    assert data["sh000001"] == [{"date": "2024-01-03", "close": 10, "pre_release": 0, "pre_base": 0}]
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


@pytest.mark.parametrize("edit", ["clean", "zero_success", "no_comparator", "stale_comparator",
                                  "unknown", "window", "stale", "missing"])
def test_visible_qvix_edge_states_match_and_never_look_clean(tmp_path, offline_feeds, edit):
    from app.chart import qvix_clean, qvix_line
    from app.verify import visible_qvix
    assert acquire(tmp_path, *WINDOW) == 0
    state = load_manifest(tmp_path)["feeds"][FEED]
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
