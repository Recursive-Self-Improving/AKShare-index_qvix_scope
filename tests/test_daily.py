"""Network-free automation boundary proofs; only disposable local remotes."""
import copy
import csv
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from app import daily
from app.core import INDICES, QVIX_FEEDS, dump, load_manifest, sha
from app.daily_transfer import digest, git, inventory, publish, validate_bundle

ROOT = Path(__file__).resolve().parents[1]
FIXED = datetime(2026, 11, 16, 11, 15, tzinfo=timezone.utc)


def repo_pair(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "--initial-branch=main", str(remote)], check=True, capture_output=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", str(remote), str(repo)], check=True, capture_output=True)
    (repo / "README").write_text("baseline\n")
    git(repo, "add", "README")
    git(repo, "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-m", "baseline")
    git(repo, "push", "origin", "HEAD:main")
    identity = {"repository": "test/local", "branch": "main", "base_sha": git(repo, "rev-parse", "HEAD").stdout.strip(),
                "run_id": "123", "run_attempt": "1"}
    return repo, remote, identity


def small_bundle(tmp_path, identity, quality="success"):
    bundle = tmp_path / "bundle"
    payload = bundle / "payload"
    (payload / "data/runs/new").mkdir(parents=True)
    (payload / "data/runs/new/manifest.json").write_text('{"run":"runs/new"}\n')
    (payload / "data/latest.json").write_text('{"run":"runs/new"}\n')
    (payload / "index.html").write_text("verified page\n")
    receipt = {"identity": identity, "run": "runs/new", "quality": quality, "files": inventory(payload)}
    dump(bundle / "receipt.json", receipt)
    return bundle, sha((bundle / "receipt.json").read_bytes())


def test_exact_atomic_tree_and_replay_refusal(tmp_path):
    repo, remote, identity = repo_pair(tmp_path)
    bundle, receipt_hash = small_bundle(tmp_path, identity, "partial")
    commit = publish(repo, bundle, receipt_hash, identity)
    assert git(remote, "rev-parse", "main").stdout.strip() == commit
    for path, facts in inventory(bundle / "payload").items():
        body = subprocess.run(["git", "--git-dir", str(remote), "show", f"main:{path}"],
                              check=True, capture_output=True).stdout
        assert digest(body) == facts["sha256"]
    assert git(remote, "rev-parse", "main^").stdout.strip() == identity["base_sha"]
    with pytest.raises(ValueError, match="checkout base"):
        publish(repo, bundle, receipt_hash, identity)
    assert git(remote, "rev-parse", "main").stdout.strip() == commit


@pytest.mark.parametrize("attack", ["hash", "extra", "symlink", "executable", "identity", "traversal", "missing"])
def test_transfer_rejections_preserve_remote(tmp_path, attack):
    repo, remote, identity = repo_pair(tmp_path)
    bundle, receipt_hash = small_bundle(tmp_path, identity)
    receipt = json.loads((bundle / "receipt.json").read_text())
    if attack == "hash":
        (bundle / "payload/index.html").write_text("forged")
    elif attack == "extra":
        (bundle / "payload/evil.py").write_text("bad")
        receipt["files"] = inventory(bundle / "payload")
    elif attack == "symlink":
        (bundle / "payload/index.html").unlink()
        (bundle / "payload/index.html").symlink_to(repo / "README")
    elif attack == "executable":
        (bundle / "payload/index.html").chmod(0o755)
    elif attack == "identity":
        receipt["identity"]["run_attempt"] = "2"
    elif attack == "traversal":
        receipt["files"]["../evil"] = {"size": 0, "sha256": digest(b"")}
    else:
        (bundle / "payload/data/runs/new/manifest.json").unlink()
    if attack in ("identity", "traversal", "extra"):
        dump(bundle / "receipt.json", receipt)
        receipt_hash = digest((bundle / "receipt.json").read_bytes())
    with pytest.raises(ValueError):
        publish(repo, bundle, receipt_hash, identity)
    assert git(remote, "rev-parse", "main").stdout.strip() == identity["base_sha"]
    assert not (repo / "index.html").exists()


def test_competing_writer_and_default_branch_change(tmp_path):
    first, remote, identity = repo_pair(tmp_path)
    second = tmp_path / "second"
    subprocess.run(["git", "clone", str(remote), str(second)], check=True, capture_output=True)
    bundle, receipt_hash = small_bundle(tmp_path, identity)
    winner = publish(first, bundle, receipt_hash, identity)
    with pytest.raises(ValueError, match="remote base"):
        publish(second, bundle, receipt_hash, identity)
    assert git(remote, "rev-parse", "main").stdout.strip() == winner
    git(remote, "symbolic-ref", "HEAD", "refs/heads/other")
    with pytest.raises(ValueError, match="default branch"):
        publish(second, bundle, receipt_hash, identity)


def test_push_race_preserves_human_commit(tmp_path, monkeypatch):
    repo, remote, identity = repo_pair(tmp_path)
    human = tmp_path / "human"
    subprocess.run(["git", "clone", str(remote), str(human)], check=True, capture_output=True)
    (human / "README").write_text("human update")
    git(human, "add", "README")
    git(human, "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-m", "human")
    human_sha = git(human, "rev-parse", "HEAD").stdout.strip()
    bundle, receipt_hash = small_bundle(tmp_path, identity)
    original = git
    def racing(root, *args, **kwargs):
        if args[0] == "push":
            original(human, "push", "origin", "HEAD:main")
        return original(root, *args, **kwargs)
    monkeypatch.setattr("app.daily_transfer.git", racing)
    with pytest.raises(RuntimeError, match="unknown/rejected"):
        publish(repo, bundle, receipt_hash, identity)
    assert git(remote, "rev-parse", "main").stdout.strip() == human_sha
    assert not git(remote, "ls-tree", "main", "index.html").stdout


def test_push_rollback_race_preserves_ancestor(tmp_path, monkeypatch):
    repo, remote, identity = repo_pair(tmp_path)
    ancestor = identity["base_sha"]
    (repo / "README").write_text("second baseline\n")
    git(repo, "add", "README")
    git(repo, "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-m", "second")
    git(repo, "push", "origin", "HEAD:main")
    identity["base_sha"] = git(repo, "rev-parse", "HEAD").stdout.strip()
    bundle, receipt_hash = small_bundle(tmp_path, identity)
    pushes = []
    def racing(root, *args, **kwargs):
        if args[0] == "push":
            pushes.append(args)
            git(remote, "update-ref", "refs/heads/main", ancestor, identity["base_sha"])
        return git(root, *args, **kwargs)
    monkeypatch.setattr("app.daily_transfer.git", racing)
    with pytest.raises(RuntimeError, match="unknown/rejected"):
        publish(repo, bundle, receipt_hash, identity)
    assert len(pushes) == 1
    assert pushes[0][1] == "--force-with-lease=refs/heads/main:" + identity["base_sha"]
    assert git(remote, "rev-parse", "main").stdout.strip() == ancestor
    assert git(remote, "show", "main:README").stdout == "baseline\n"
    assert not git(remote, "ls-tree", "main", "index.html").stdout


@pytest.mark.parametrize("parents", ["wrong", "multiple"])
def test_publication_refuses_non_exact_parent_list(tmp_path, monkeypatch, parents):
    import os
    repo, remote, identity = repo_pair(tmp_path)
    bundle, receipt_hash = small_bundle(tmp_path, identity)
    base = identity["base_sha"]
    env = os.environ | {"GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
                        "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid"}
    tree = git(repo, "rev-parse", "HEAD^{tree}").stdout.strip()
    wrong = git(repo, "commit-tree", tree, "-m", "unrelated root", env=env).stdout.strip()
    def altered_commit(root, *args, **kwargs):
        result = git(root, *args, **kwargs)
        if "commit" in args:
            tree = git(root, "rev-parse", "HEAD^{tree}").stdout.strip()
            parent_args = ["-p", wrong] if parents == "wrong" else ["-p", base, "-p", wrong]
            altered = git(root, "commit-tree", tree, *parent_args, "-m", "altered", env=env).stdout.strip()
            git(root, "update-ref", "HEAD", altered)
        assert args[0] != "push"
        return result
    monkeypatch.setattr("app.daily_transfer.git", altered_commit)
    with pytest.raises(ValueError, match="parents must equal receipt base"):
        publish(repo, bundle, receipt_hash, identity)
    assert git(remote, "rev-parse", "main").stdout.strip() == base
    assert not git(remote, "ls-tree", "main", "index.html").stdout


def policy_fixture():
    previous = {"run": "runs/old", "manifest_path": "runs/old/manifest.json",
                "window": [daily.START, "2026-11-16"], "feeds": {}}
    candidate = {"run": "runs/new", "manifest_path": "runs/new/manifest.json", "operation": "acquisition",
                 "window": [daily.START, "2026-11-15"], "attempted_at": FIXED.isoformat(),
                 "finished_at": (FIXED + timedelta(seconds=10)).isoformat(), "feeds": {}}
    for feed in [*INDICES, *QVIX_FEEDS]:
        snap = {"status": "success", "origin": {"kind": "result", "path": f"runs/new/{feed}/result.json"},
                "window": candidate["window"], "csv": feed, "range": ["2024-01-02", "2024-01-04"],
                "raw": {"retrieved_at": (FIXED + timedelta(seconds=2)).isoformat()},
                "attempted_at": (FIXED + timedelta(seconds=1)).isoformat(),
                "successful_at": (FIXED + timedelta(seconds=3)).isoformat(),
                "finished_at": (FIXED + timedelta(seconds=4)).isoformat()}
        candidate["feeds"][feed] = {"attempt": snap, "snapshot": snap, "stale_reuse": False}
        previous["feeds"][feed] = {"snapshot": copy.deepcopy(snap) | {"origin": {"path": "old"}}}
    return previous, candidate


@pytest.mark.parametrize("feed", ["sh000001", "qvix_50etf"])
@pytest.mark.parametrize("attack", ["old", "future", "completion-bound", "member-order"])
def test_acquisition_temporal_boundaries(tmp_path, monkeypatch, feed, attack):
    previous, candidate = policy_fixture()
    candidate["previous"] = "previous-hash"
    monkeypatch.setattr("app.core.artifact_ref", lambda *args: "previous-hash")
    monkeypatch.setattr("app.core.read_csv", lambda *args: [{"date": "2024-01-03"}])
    monkeypatch.setattr(daily, "source_dates", lambda *args: {"2024-01-03"})
    snap = candidate["feeds"][feed]["snapshot"]
    if attack == "member-order":
        snap["successful_at"] = (FIXED + timedelta(seconds=5)).isoformat()
    else:
        seconds = {"old": -1, "future": 11, "completion-bound": 3.5 if feed in QVIX_FEEDS else 0}[attack]
        snap["acquired_at"] = (FIXED + timedelta(seconds=seconds)).isoformat()
    with pytest.raises(ValueError, match="member time|acquisition time"):
        daily.eligibility(tmp_path, previous, candidate, 0, FIXED,
                          FIXED + timedelta(seconds=11), "2026-11-15")


@pytest.mark.parametrize("feed", ["sh000001", "qvix_100etf"])
@pytest.mark.parametrize("lost", ["2024-01-02", "2024-01-03", "2024-01-04"])
def test_date_loss_equal_count_endpoints_and_null_retention(tmp_path, monkeypatch, feed, lost):
    previous, candidate = policy_fixture()
    days = {"2024-01-02", "2024-01-03", "2024-01-04"}
    monkeypatch.setattr("app.core.artifact_ref", lambda *args: "previous-hash")
    candidate["previous"] = "previous-hash"
    monkeypatch.setattr("app.core.read_csv", lambda *args: [{"date": "2024-01-03", "close": None}])
    def dates(root, snap, code):
        return days if snap["origin"]["path"] == "old" or code != feed else days - {lost} | {"2024-01-01"}
    monkeypatch.setattr(daily, "source_dates", dates)
    with pytest.raises(ValueError, match=f"source dates lost {feed}.*{lost}"):
        daily.eligibility(tmp_path, previous, candidate, 0, FIXED, FIXED + timedelta(seconds=11), "2026-11-15")
    monkeypatch.setattr(daily, "source_dates", lambda *args: days)
    candidate["feeds"]["qvix_100etf"]["snapshot"]["status"] = "partial"
    quality, _ = daily.eligibility(tmp_path, previous, candidate, 1, FIXED, FIXED + timedelta(seconds=11), "2026-11-15")
    assert quality == "partial"  # Nulls do not create source date loss.


@pytest.mark.parametrize("attack", ["old", "window", "origin", "stale", "failure", "time", "current", "exit"])
def test_invocation_and_cutoff_refusals(tmp_path, monkeypatch, attack):
    previous, candidate = policy_fixture()
    candidate["previous"] = "previous-hash"
    monkeypatch.setattr("app.core.artifact_ref", lambda *args: "previous-hash")
    monkeypatch.setattr("app.core.read_csv", lambda *args: [{"date": "2026-11-16" if attack == "current" else "2024-01-03"}])
    monkeypatch.setattr(daily, "source_dates", lambda *args: {"2024-01-03"})
    snap = candidate["feeds"]["sh000001"]["snapshot"]
    if attack == "old":
        candidate["run"] = previous["run"]
    elif attack == "window":
        candidate["window"] = ["2026-10-15", "2026-11-15"]
    elif attack == "origin":
        snap["origin"]["path"] = "runs/old/result.json"
    elif attack == "stale":
        candidate["feeds"]["sh000001"]["stale_reuse"] = True
    elif attack == "failure":
        snap["status"] = "failure"
    elif attack == "time":
        snap["finished_at"] = "2026-11-15T00:00:00+00:00"
    with pytest.raises(ValueError):
        daily.eligibility(tmp_path, previous, candidate, 1 if attack == "exit" else 0,
                          FIXED, FIXED + timedelta(seconds=11), "2026-11-15")


@pytest.mark.parametrize("start,expected", [
    ("2026-11-16T11:15:00+00:00", "2026-11-16"),
    ("2026-11-14T11:15:00+00:00", "2026-11-14"),
    ("2024-02-29T23:59:59+00:00", "2024-02-29"),
    ("2026-12-31T23:59:59+00:00", "2026-12-31"),
    ("2027-01-01T01:00:00+08:00", "2026-12-31"),
])
def test_frozen_utc_cutoff_without_local_timezone(tmp_path, start, expected, monkeypatch):
    monkeypatch.setenv("TZ", "Pacific/Honolulu")
    root = tmp_path / "root"
    (root / "data").mkdir(parents=True)
    (root / "uv.lock").write_text("lock")
    ticks = iter([datetime.fromisoformat(start), datetime.fromisoformat(start) + timedelta(days=1)])
    def reject(command, log):
        log.write_text("baseline deliberately invalid")
        return 1
    with pytest.raises(ValueError, match="baseline verification"):
        daily.prepare(root, tmp_path / "work", {}, clock=lambda: next(ticks), runner=reject)
    outcome = json.loads((tmp_path / "work/diagnostics/outcome.json").read_text())
    assert outcome["window"] == ["2000-01-01", expected] and not outcome["eligible"]


@pytest.fixture(scope="module")
def real_prepared(tmp_path_factory):
    """Real fetch workers, renderer and independent verifier; retained HTTP only."""
    from app.chart import build
    from app.fetch import fetch, group_worker, worker
    import requests
    temporary = tmp_path_factory.mktemp("daily-real")
    root = temporary / "root"
    root.mkdir()
    shutil.copytree(ROOT / "data", root / "data")
    shutil.copyfile(ROOT / "index.html", root / "index.html")
    shutil.copyfile(ROOT / "uv.lock", root / "uv.lock")
    baseline = load_manifest(root / "data")
    original_inventory = inventory(root / "data", bounded=False)
    q = baseline["feeds"]["qvix_50etf"]["snapshot"]
    shared = json.loads((root / "data" / q["shared"]["path"]).read_text())
    records = list(csv.reader(io.StringIO((root / "data" / shared["raw"]["body"]).read_bytes().decode("gbk"))))
    for row in records[1:]:
        for definition in QVIX_FEEDS.values():
            for column in definition["columns"][1:]:
                row[column] = ""
    records.append(["2026/11/16", *records[-1][1:]])
    records.append(["2026/11/17", *records[-1][1:]])
    stream = io.StringIO(newline="")
    csv.writer(stream, lineterminator="\n").writerows(records)
    blank_body = stream.getvalue().encode("gbk")
    def retained_get(url, **kwargs):
        if "optbbs" in url:
            body, encoding = blank_body, "gbk"
        else:
            feed = next(feed for feed in INDICES if feed in url)
            snap = baseline["feeds"][feed]["snapshot"]
            body, encoding = (root / "data" / snap["raw"]["body"]).read_bytes(), snap["raw"]["encoding"]
        response = requests.Response()
        response.status_code, response.url, response.encoding = 200, url, encoding
        response.request = requests.Request("GET", url).prepare()
        response._content = body
        kwargs["hooks"]["response"](response)
        return response
    def local_worker(command, **kwargs):
        if command[3] == "--group-worker":
            group_worker(Path(command[4]))
        else:
            worker(*command[4:])
        return subprocess.CompletedProcess(command, 0)
    def runner(command, log):
        if "app.fetch" in command:
            with pytest.MonkeyPatch.context() as patch:
                patch.setattr("requests.get", retained_get)
                patch.setattr("app.fetch.subprocess.run", local_worker)
                ticks = iter(range(1000))
                patch.setattr("app.fetch.now",
                              lambda: (FIXED + timedelta(seconds=2, microseconds=next(ticks))).isoformat())
                code = fetch(command[command.index("--output") + 1],
                             command[command.index("--start") + 1], command[command.index("--end") + 1])
            log.write_text(f"actual fetch exit={code}; retained HTTP fixture\n")
            return code
        if "app.chart" in command:
            build(command[command.index("--input") + 1], command[command.index("--output") + 1])
            log.write_text("actual renderer completed\n")
            return 0
        return daily.execute(command, log)  # Real separate-process independent verifier.
    ticks = iter([FIXED, FIXED + timedelta(seconds=1), FIXED + timedelta(seconds=3),
                  FIXED + timedelta(days=1)])
    identity = {"repository": "test/local", "branch": "main", "base_sha": "a" * 40,
                "run_id": "123", "run_attempt": "1"}
    work = temporary / "work"
    outcome = daily.prepare(root, work, identity, clock=lambda: next(ticks), runner=runner)
    assert inventory(root / "data", bounded=False) == original_inventory
    return root, work, outcome, identity


def test_real_orchestration_blank_partial_and_independent_verifier(real_prepared):
    root, work, outcome, identity = real_prepared
    assert outcome["eligible"] and outcome["quality"] == "partial" and outcome["fetch_exit"] == 1
    assert outcome["window"] == [daily.START, "2026-11-16"]
    assert outcome["finished_at"].startswith("2026-11-17")  # Cutoff survives midnight.
    validate_bundle(work / "bundle", outcome["receipt_hash"], identity)
    candidate = load_manifest(work / "stage/data")
    from app.core import read_csv
    for feed in QVIX_FEEDS:
        snap = candidate["feeds"][feed]["snapshot"]
        assert not candidate["feeds"][feed]["stale_reuse"]
        assert snap["acquired_at"] <= snap["successful_at"] <= snap["finished_at"]
        if feed != next(iter(QVIX_FEEDS)):
            assert snap["acquired_at"] < snap["attempted_at"]
        assert all(row["close"] is None for row in read_csv(work / "stage/data" / snap["csv"]))
        days = {row["date"] for row in read_csv(work / "stage/data" / snap["csv"])}
        assert days and max(days) == "2026-11-16" and min(days) < "2026-10-01"
        assert "2026-11-17" not in days
        assert "2026-11-17" in daily.source_dates(work / "stage/data", snap, feed)
    for log in ("baseline.log", "candidate.log"):
        assert "Offline verification passed: eight panels" in (work / "diagnostics" / log).read_text()
    assert not (root / "data" / candidate["run"]).exists()


def test_real_verified_payload_commits_exactly_together(real_prepared, tmp_path):
    _, work, outcome, identity = real_prepared
    repo, remote, local_identity = repo_pair(tmp_path)
    bundle = tmp_path / "bundle"
    shutil.copytree(work / "bundle", bundle)
    receipt = json.loads((bundle / "receipt.json").read_text())
    receipt["identity"] = local_identity
    dump(bundle / "receipt.json", receipt)
    receipt_hash = digest((bundle / "receipt.json").read_bytes())
    commit = publish(repo, bundle, receipt_hash, local_identity)
    assert git(remote, "rev-parse", "main").stdout.strip() == commit
    assert git(remote, "show", "main:data/latest.json").stdout == (bundle / "payload/data/latest.json").read_text()
    committed_html = subprocess.run(["git", "--git-dir", str(remote), "show", "main:index.html"],
                                    check=True, capture_output=True).stdout
    assert digest(committed_html) == receipt["files"]["index.html"]["sha256"]
    assert outcome["quality"] == "partial"
    test_actual_workflow_conclusion(tmp_path, outcome["quality"], "false", "skipped", 0, "::warning::")


def test_clean_eligibility_and_changed_old_values(tmp_path, monkeypatch):
    previous, candidate = policy_fixture()
    candidate["previous"] = "previous-hash"
    monkeypatch.setattr("app.core.artifact_ref", lambda *args: "previous-hash")
    monkeypatch.setattr("app.core.read_csv", lambda *args: [{"date": "2001-01-02", "close": 9876}])
    monkeypatch.setattr(daily, "source_dates", lambda *args: {"2001-01-02", "2026-11-16"})
    quality, details = daily.eligibility(tmp_path, previous, candidate, 0, FIXED,
                                         FIXED + timedelta(seconds=11), "2026-11-15")
    assert quality == "success" and details["sh000001"]["retained_dates"] == 1


@pytest.mark.parametrize("timeout", [False, True])
def test_accepted_push_with_lost_response_is_proven_by_readback(tmp_path, monkeypatch, timeout):
    repo, remote, identity = repo_pair(tmp_path)
    bundle, receipt_hash = small_bundle(tmp_path, identity)
    original = git
    def lost_response(root, *args, **kwargs):
        result = original(root, *args, **kwargs)
        if args[0] == "push":
            if timeout:
                raise subprocess.TimeoutExpired("git push", 60)
            result.returncode = 1
        return result
    monkeypatch.setattr("app.daily_transfer.git", lost_response)
    commit = publish(repo, bundle, receipt_hash, identity)
    assert git(remote, "rev-parse", "main").stdout.strip() == commit


@pytest.mark.parametrize("quality,pages,deploy,expected,notice", [
    ("success", "false", "skipped", 0, "Pages: disabled"),
    ("success", "true", "success", 0, "Pages: success"),
    ("partial", "false", "skipped", 0, "::warning::"),
    ("partial", "true", "success", 0, "::warning::"),
    ("partial", "true", "failure", 1, "::error::"),
    ("partial", "true", "skipped", 1, "::error::"),
    ("", "true", "success", 1, "::error::"),
    ("success", "true", "failure", 1, "no rollback"),
])
def test_actual_workflow_conclusion(tmp_path, quality, pages, deploy, expected, notice):
    import os
    import textwrap
    # Execute the workflow's real concluding shell, not an assertion about its source.
    shell = (ROOT / ".github/workflows/daily-refresh.yml").read_text().rsplit("        run: |\n", 1)[1]
    env = os.environ | {"PREPARE": "success", "PERSIST": "success", "DEPLOY": deploy,
                        "PAGES_ENABLED": pages, "QUALITY": quality, "DATA_COMMIT": "verified-commit",
                        "EVENT_SHA": "event-code", "GITHUB_STEP_SUMMARY": str(tmp_path / "summary")}
    result = subprocess.run(["bash", "-e", "-c", textwrap.dedent(shell)], env=env,
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == expected and notice in result.stdout
    assert "Data commit: verified-commit" in (tmp_path / "summary").read_text()


@pytest.mark.parametrize("attack,reason", [
    ("crash", "no new acquisition"),
    ("immutable", "old immutable data changed"),
    ("hidden", "candidate verification failed"),
    ("fatal", "fatal/stale"),
])
def test_real_preparation_withholds_invalid_candidates(real_prepared, tmp_path, attack, reason):
    from app.chart import build
    from app.fetch import promote, state_after
    root, accepted, _, identity = real_prepared
    original_inventory = inventory(root / "data", bounded=False)
    original_html = digest((root / "index.html").read_bytes())
    baseline = load_manifest(root / "data")
    candidate = load_manifest(accepted / "stage/data")
    def runner(command, log):
        if "app.fetch" in command:
            destination = Path(command[command.index("--output") + 1])
            if attack != "crash":
                shutil.copytree(accepted / "stage/data" / candidate["run"], destination / candidate["run"])
                fresh = copy.deepcopy(candidate)
                if attack == "fatal":
                    feed = "sh000001"
                    failed = {"status": "failure", "feed": feed, "attempted_at": FIXED.isoformat(),
                              "finished_at": FIXED.isoformat(), "error": "deterministic provider outage"}
                    fresh["feeds"][feed] = state_after(baseline["feeds"][feed], failed)
                    # Retain the real stale contract; the independent verifier accepts it.
                    (destination / fresh["manifest_path"]).unlink()
                dump(destination / "latest.json", fresh)
                if attack == "fatal":
                    promote(destination, fresh)
                if attack == "immutable":
                    # Unreferenced historical evidence still must never be rewritten.
                    (destination / "documentation-example/UNREFERENCED").write_text("unexpected addition")
                    historical = next((destination / "documentation-example").glob("*.csv"))
                    historical.write_bytes(historical.read_bytes() + b"\n")
            log.write_text("retained completed acquisition, or deliberate crash without promotion\n")
            return 1
        if "app.chart" in command:
            output = Path(command[command.index("--output") + 1])
            build(command[command.index("--input") + 1], output)
            if attack == "hidden":
                output.write_text(output.read_text().replace('<div class="status">', '<div class="status" hidden>', 1))
            log.write_text("actual chart built\n")
            return 0
        return daily.execute(command, log)
    ticks = iter([FIXED, FIXED + timedelta(seconds=1), FIXED + timedelta(seconds=3),
                  FIXED + timedelta(seconds=4)])
    work = tmp_path / "rejected"
    with pytest.raises(ValueError, match=reason):
        daily.prepare(root, work, identity, clock=lambda: next(ticks), runner=runner)
    outcome = json.loads((work / "diagnostics/outcome.json").read_text())
    assert not outcome["eligible"] and reason in outcome["error"]
    assert not (work / "bundle").exists()
    assert inventory(root / "data", bounded=False) == original_inventory
    assert digest((root / "index.html").read_bytes()) == original_html


def test_stdlib_only_cli_and_exact_pages_package(tmp_path):
    import os
    import sys
    repo, remote, identity = repo_pair(tmp_path)
    bundle, receipt_hash = small_bundle(tmp_path, identity, "partial")
    output = tmp_path / "outputs"
    env = os.environ.copy()
    env.pop("GH_TOKEN", None)
    env.update(DEFAULT_BRANCH="main", GITHUB_REF="refs/heads/main", GITHUB_EVENT_NAME="workflow_dispatch",
               GITHUB_REPOSITORY=identity["repository"], GITHUB_SHA=identity["base_sha"],
               GITHUB_RUN_ID=identity["run_id"], GITHUB_RUN_ATTEMPT=identity["run_attempt"],
               GITHUB_OUTPUT=str(output))
    # -S excludes site-packages: application dependencies cannot be imported here.
    command = [sys.executable, "-I", "-S", str(ROOT / "app/daily_transfer.py")]
    result = subprocess.run([*command, "publish", "--bundle", str(bundle), "--receipt-hash", receipt_hash],
                            cwd=repo, env=env, check=True, capture_output=True, text=True, timeout=30)
    commit = git(remote, "rev-parse", "main").stdout.strip()
    assert f"Persisted {commit}; quality=partial" in result.stdout
    assert output.read_text() == f"commit={commit}\nquality=partial\n"
    site = tmp_path / "site"
    subprocess.run([*command, "pages", "--bundle", str(bundle), "--receipt-hash", receipt_hash,
                    "--commit", commit, "--site", str(site)], cwd=repo, env=env, check=True,
                   capture_output=True, timeout=30)
    assert list(site.iterdir()) == [site / "index.html"]
    assert (site / "index.html").read_bytes() == (bundle / "payload/index.html").read_bytes()
    # Other-branch manual dispatch is rejected even with a valid same-run receipt.
    env["GITHUB_REF"] = "refs/heads/feature"
    refused = subprocess.run([*command, "check"], cwd=repo, env=env, capture_output=True, timeout=30)
    assert refused.returncode != 0 and b"not default branch" in refused.stderr
    assert git(remote, "rev-parse", "main").stdout.strip() == commit
