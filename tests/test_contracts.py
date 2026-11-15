import copy
import json

import pytest

from app.core import csv_bytes, decode, latest_by_date, read_csv, sha, trace_points, validate
from app.fetch import promote


def snapshot(root, value=1.0, name="first"):
    raw = [{"tradeDate": "2024-10-31", "maIndex1": value, "marketClose": 3891.0396}]
    body = json.dumps(raw).encode()
    rows = decode("sentiment", body)
    (root / f"{name}.body").write_bytes(body)
    csv = csv_bytes(rows, ["sentiment", "market_close"])
    (root / f"{name}.csv").write_bytes(csv)
    return {"feed": "sentiment", "status": "success", "successful_at": name,
            "window": ["2000-01-01", "2026-11-15"], "csv": f"{name}.csv", "csv_sha256": sha(csv),
            "raw": {"body": f"{name}.body", "sha256": sha(body), "encoding": "utf-8"}}


def manifest(snap, name="first"):
    return {"manifest_path": f"{name}.json", "feeds": {"sentiment": {
        "snapshot": snap, "revisions": [snap], "attempt": {"status": "success"}, "stale_reuse": False}}}


@pytest.mark.parametrize("body", [
    b"<html>upstream maintenance</html>", b"{bad", b'[{"tradeDate":"not-date","maIndex1":1,"marketClose":2}]',
    b'[{"tradeDate":"2024-10-31","maIndex1":NaN,"marketClose":2}]',
    b'[{"tradeDate":"2024-10-31","maIndex1":Infinity,"marketClose":2}]',
    b'[{"tradeDate":"2024-10-31","maIndex1":"oops","marketClose":2}]',
    b'[{"tradeDate":"2024-10-31","maIndex1":1,"marketClose":2},'
    b'{"tradeDate":"2024-10-31","maIndex1":2,"marketClose":2}]',
    b'[{"tradeDate":"2024-10-31","maIndex1":1,"marketClose":2},'
    b'{"tradeDate":"2024-10-30","maIndex1":2,"marketClose":2}]',
])
def test_invalid_refresh_preserves_success(tmp_path, body):
    good = snapshot(tmp_path)
    promote(tmp_path, manifest(good))
    before = (tmp_path / "latest.json").read_bytes()
    bad = copy.deepcopy(good)
    bad["raw"] = {"body": "bad.body", "sha256": sha(body), "encoding": "utf-8"}
    (tmp_path / "bad.body").write_bytes(body)
    with pytest.raises((ValueError, KeyError, TypeError)):
        promote(tmp_path, manifest(bad, "bad"))
    assert (tmp_path / "latest.json").read_bytes() == before
    assert read_csv(tmp_path / good["csv"])[0]["sentiment"] == 1


def test_interrupted_atomic_promotion_preserves_success(tmp_path, monkeypatch):
    good = snapshot(tmp_path)
    promote(tmp_path, manifest(good))
    before = (tmp_path / "latest.json").read_bytes()
    revised = snapshot(tmp_path, 1.2, "second")

    def interrupted(*args):
        raise OSError("interrupted before atomic replacement")

    monkeypatch.setattr("app.core.os.replace", interrupted)
    with pytest.raises(OSError):
        promote(tmp_path, manifest(revised, "second"))
    assert (tmp_path / "latest.json").read_bytes() == before
    assert read_csv(tmp_path / good["csv"])[0]["sentiment"] == 1


def test_stale_reuse_retains_success_identity_and_attempt(tmp_path):
    good = snapshot(tmp_path)
    run = manifest(good)
    state = run["feeds"]["sentiment"]
    state.update(attempt={"status": "transport_failure", "attempted_at": "second"}, stale_reuse=True)
    promote(tmp_path, run)
    saved = json.loads((tmp_path / "latest.json").read_text())["feeds"]["sentiment"]
    assert saved["snapshot"]["successful_at"] == "first"
    assert saved["attempt"]["status"] == "transport_failure"
    assert saved["stale_reuse"] is True
    saved["snapshot"] = dict(saved["snapshot"], successful_at="second")
    with pytest.raises(ValueError, match="identity"):
        promote(tmp_path, {"manifest_path": "bad.json", "feeds": {"sentiment": saved}})


def test_wrong_source_identity_rejected(tmp_path):
    good = snapshot(tmp_path)
    good["feed"] = "sh000001"
    with pytest.raises(ValueError, match="source identity"):
        promote(tmp_path, manifest(good))


def test_revisions_latest_by_date_preserves_older_unrevised_date(tmp_path):
    first = [{"date": "2024-10-30", "sentiment": 0.9}, {"date": "2024-10-31", "sentiment": 1.0}]
    second = [{"date": "2024-10-31", "sentiment": 1.1}]
    assert latest_by_date([first, second]) == [first[0], second[0]]
    old = snapshot(tmp_path, 1.0)
    old_bytes = (tmp_path / old["raw"]["body"]).read_bytes()
    new = snapshot(tmp_path, 1.1, "second")
    run = manifest(new, "second")
    run["feeds"]["sentiment"]["revisions"] = [old, new]
    promote(tmp_path, run)
    saved = json.loads((tmp_path / "latest.json").read_text())["feeds"]["sentiment"]
    merged = latest_by_date([read_csv(tmp_path / s["csv"]) for s in saved["revisions"]])
    assert merged[0]["sentiment"] == 1.1
    assert (tmp_path / old["raw"]["body"]).read_bytes() == old_bytes
    assert read_csv(tmp_path / old["csv"])[0]["sentiment"] == 1.0


def test_sparse_calendar_gap_no_weekend_fill_or_extrapolation():
    rows = [{"date": "2024-11-01", "sentiment": 0}, {"date": "2024-11-05", "sentiment": 1.1}]
    dates, values = trace_points(rows, "sentiment", ["2024-10-31", "2024-11-01", "2024-11-04",
                                                   "2024-11-05", "2024-11-06"])
    assert dates == ["2024-11-01", "2024-11-04", "2024-11-05"]
    assert values == [0, None, 1.1]


def test_observed_null_and_zero_are_not_empty_or_missing_feed():
    body = b'[{"tradeDate":"2024-10-30","maIndex1":null,"marketClose":null},'
    body += b'{"tradeDate":"2024-10-31","maIndex1":0,"marketClose":0}]'
    rows = decode("sentiment", body)
    assert [r["sentiment"] for r in rows] == [None, 0]
    assert decode("sentiment", b"[]") == []
    with pytest.raises(ValueError):
        decode("sh000001", b"var KLC_KL_sh000300=\"other instrument\";")


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), "3.5"])
def test_invalid_index_closes_are_rejected(value):
    with pytest.raises(ValueError):
        validate([{"date": "2024-10-31", "close": value}], ["close"])


def test_provider_html_is_validation_failure_with_exact_capture(tmp_path, monkeypatch):
    import requests
    from app.fetch import worker

    body = b"<html>provider error, not observations</html>"

    def get(url, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response.url = url
        response.request = requests.Request("GET", url, params=kwargs.get("params")).prepare()
        response._content = body
        response.encoding = "utf-8"
        kwargs["hooks"]["response"](response)
        return response

    monkeypatch.setattr(requests, "get", get)
    worker("sentiment", tmp_path, "2000-01-01", "2026-11-15")
    result = json.loads((tmp_path / "result.json").read_text())
    assert result["status"] == "validation_failure"
    assert (tmp_path / "response-0.body").read_bytes() == body
    assert result["captures"][0]["sha256"] == sha(body)
    assert not (tmp_path / "observations.csv").exists()


@pytest.mark.parametrize(("body", "status", "outcome", "values"), [
    (b"[]", 200, "success", []),
    (b'[{"tradeDate":"2024-10-31","maIndex1":0,"marketClose":0}]', 200, "success", [0]),
    (b'[{"tradeDate":"2024-10-31","maIndex1":null,"marketClose":null}]', 200, "success", [None]),
    (b"[]", 503, "validation_failure", None),
    (b"{bad", 200, "validation_failure", None),
])
def test_worker_observed_empty_zero_null_and_failed_responses(tmp_path, monkeypatch, body, status,
                                                            outcome, values):
    import requests
    from app.fetch import worker

    def get(url, **kwargs):
        response = requests.Response()
        response.status_code = status
        response.url = url
        response.request = requests.Request("GET", url, params=kwargs.get("params")).prepare()
        response._content = body
        response.encoding = "utf-8"
        kwargs["hooks"]["response"](response)
        return response

    monkeypatch.setattr(requests, "get", get)  # Leave the actual pinned AKShare invocation intact.
    worker("sentiment", tmp_path, "2000-01-01", "2026-11-15")
    result = json.loads((tmp_path / "result.json").read_text())
    assert result["status"] == outcome
    assert (tmp_path / "response-0.body").read_bytes() == body
    assert result["captures"][0]["sha256"] == sha(body)
    if values is None:
        assert "successful_at" not in result
        assert not (tmp_path / "observations.csv").exists()
    else:
        assert [r["sentiment"] for r in read_csv(tmp_path / "observations.csv")] == values
        assert result["count"] == len(values)
        assert result["range"] == (["2024-10-31", "2024-10-31"] if values else None)
        snap = copy.deepcopy(result)
        snap["csv"] = "observations.csv"
        snap["raw"]["body"] = "response-0.body"
        promote(tmp_path, manifest(snap))
        saved = json.loads((tmp_path / "latest.json").read_text())["feeds"]["sentiment"]
        assert saved["snapshot"]["count"] == len(values)
        assert saved["stale_reuse"] is False


@pytest.mark.parametrize("error", [KeyError("unrelated wrapper bug"), ValueError("unrelated wrapper bug")])
def test_worker_does_not_accept_arbitrary_wrapper_error_after_empty_capture(tmp_path, monkeypatch, error):
    import akshare as ak
    import requests
    from akshare.utils import http
    from app.fetch import worker

    def get(url, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response.url = url
        response.request = requests.Request("GET", url).prepare()
        response._content = b"[]"
        response.encoding = "utf-8"
        kwargs["hooks"]["response"](response)
        return response

    def broken_wrapper():
        http.get("https://example.invalid")
        raise error

    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(ak, "index_news_sentiment_scope", broken_wrapper)
    worker("sentiment", tmp_path, "2000-01-01", "2026-11-15")
    result = json.loads((tmp_path / "result.json").read_text())
    assert result["status"] == "validation_failure"
    assert (tmp_path / "response-0.body").read_bytes() == b"[]"
    assert "successful_at" not in result
    assert not (tmp_path / "observations.csv").exists()


def test_worker_transport_failure_is_not_observed_empty(tmp_path, monkeypatch):
    import requests
    from app.fetch import worker

    def get(*args, **kwargs):
        raise requests.ConnectionError("deterministic transport failure")

    monkeypatch.setattr(requests, "get", get)
    worker("sentiment", tmp_path, "2000-01-01", "2026-11-15")
    result = json.loads((tmp_path / "result.json").read_text())
    assert result["status"] == "transport_failure"
    assert result["captures"] == []
    assert "successful_at" not in result
    assert not (tmp_path / "observations.csv").exists()


def test_two_revision_selected_history_matches_plot_and_independent_accounting(tmp_path):
    import shutil
    from pathlib import Path

    from app.chart import build
    from app.core import dump, histories, load_manifest, selected_history
    from app.verify import Embedded, verify, verify_accounting

    # Copy retained evidence only; this fixture never invokes transport or changes real data.
    root = tmp_path / "data"
    shutil.copytree(Path(__file__).resolve().parents[1] / "data", root)
    run = load_manifest(root)
    revisions = []
    for name, records in [
        ("old", [("2024-10-25", 0.9), ("2024-10-31", 1.0)]),
        ("new", [("2024-10-31", 1.1)]),
    ]:
        raw = [{"tradeDate": day, "maIndex1": value, "marketClose": 2} for day, value in records]
        body = json.dumps(raw).encode()
        (root / f"{name}.body").write_bytes(body)
        rows = decode("sentiment", body)
        csv = csv_bytes(rows, ["sentiment", "market_close"])
        (root / f"{name}.csv").write_bytes(csv)
        revisions.append({
            "feed": "sentiment", "status": "success", "successful_at": name,
            "window": ["2000-01-01", "2026-11-15"], "csv": f"{name}.csv", "csv_sha256": sha(csv),
            "count": len(rows), "range": [rows[0]["date"], rows[-1]["date"]],
            "raw": {"body": f"{name}.body", "sha256": sha(body), "encoding": "utf-8"},
        })
    run["feeds"]["sentiment"] = {
        "snapshot": revisions[-1], "revisions": revisions,
        "attempt": {"status": "success", "attempted_at": "new"}, "stale_reuse": False,
    }
    coverage = selected_history(root, run)
    selected = coverage["sentiment"]
    assert selected["range"] == ["2024-10-25", "2024-10-31"]
    assert selected["count"] == 2
    assert selected["relative_gaps"] == ["2024-10-28", "2024-10-29", "2024-10-30"]
    assert selected["relative_extra_dates"] == []
    assert selected["calendar_snapshot"] == run["feeds"]["sh000001"]["snapshot"]["csv"]
    run["feeds"]["sentiment"]["selected_history"] = selected
    dump(root / "latest.json", run)
    dump(root / run["manifest_path"], run)
    old_bytes = (root / "old.body").read_bytes()
    report = tmp_path / "fixture.html"
    build(root, report)
    verify(root, report)
    parser = Embedded()
    parser.feed(report.read_text())
    payload = json.loads(parser.payload)
    assert payload["sentiment_status"]["snapshot"]["range"] == ["2024-10-31", "2024-10-31"]
    assert payload["sentiment_status"]["snapshot"]["count"] == 1
    assert payload["sentiment_status"]["snapshot"]["successful_at"] == "new"
    assert payload["selected_history"]["sentiment"] == selected
    for panel in payload["panels"]:
        trace = panel["data"][1]
        assert trace["x"] == ["2024-10-25", "2024-10-28", "2024-10-29", "2024-10-30", "2024-10-31"]
        assert trace["y"] == [0.9, None, None, None, 1.1]
    assert (root / "old.body").read_bytes() == old_bytes
    data = histories(root, run)
    latest = dict(data, sentiment=read_csv(root / "new.csv"))
    for field, wrong in [("range", ["2024-10-31", "2024-10-31"]), ("count", 1),
                         ("relative_gaps", []), ("relative_extra_dates", ["2024-10-25"]),
                         ("calendar_snapshot", "wrong.csv")]:
        broken = copy.deepcopy(payload)
        broken["selected_history"]["sentiment"][field] = wrong
        with pytest.raises(ValueError, match="HTML selected-history accounting"):
            verify_accounting(run, data, latest, broken)
        broken_run = copy.deepcopy(run)
        broken_run["feeds"]["sentiment"]["selected_history"][field] = wrong
        with pytest.raises(ValueError, match="sentiment selected-history metadata"):
            verify_accounting(broken_run, data, latest, payload)
