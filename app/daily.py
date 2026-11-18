"""Read-only preparation: real acquisition in a fresh, private stage."""
import argparse
from datetime import date, datetime, timedelta, timezone
import filecmp
from itertools import chain
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys

from app.daily_transfer import (
    MAX_BYTES, MAX_FILES, auth_env, digest, identity_from_env, payload_inventory, remote_head, require,
)


START = "2000-01-01"


def utc_now():
    return datetime.now(timezone.utc)


def instant(value):
    result = datetime.fromisoformat(value)
    require(result.tzinfo is not None and result.utcoffset() == timedelta(0), "non-UTC invocation time")
    return result


def source_dates(root, snap, feed):
    from app.core import QVIX_FEEDS, common_qvix, decode
    if feed in QVIX_FEEDS:
        group = json.loads((root / snap["shared"]["path"]).read_text())
        records = common_qvix((root / group["raw"]["body"]).read_bytes())
        return {date(*map(int, row[0].split("/"))).isoformat() for row in records[1:]}
    return {r["date"] for r in decode(feed, (root / snap["raw"]["body"]).read_bytes(),
                                     snap["raw"]["encoding"])}


def eligibility(baseline_root, candidate_root, previous, candidate, code, started, finished, cutoff):
    from app.core import INDICES, QVIX_FEEDS, read_csv
    require(candidate["operation"] == "acquisition" and
            instant(candidate["attempted_at"]) != instant(previous["attempted_at"]), "no new acquisition")
    require(candidate["window"] == [START, cutoff], "incorrect full window")
    require(set(candidate["feeds"]) == {*INDICES, *QVIX_FEEDS}, "incomplete registry")
    begin, end = instant(candidate["attempted_at"]), instant(candidate["finished_at"])
    require(started <= begin <= end <= finished, "manifest outside invocation")
    partial = False
    details = {}
    for feed, state in candidate["feeds"].items():
        snap = state["snapshot"]
        require(snap and not state["stale_reuse"] and state["attempt"] == snap, f"fatal/stale {feed}")
        require(snap["status"] in (("success",) if feed in INDICES else ("success", "partial")),
                f"ineligible status {feed}")
        partial |= snap["status"] == "partial"
        require(snap["window"] == [START, cutoff], f"snapshot window {feed}")
        require(snap["feed"] == feed, f"member identity {feed}")
        directory = f"current/qvix-group/{feed}" if feed in QVIX_FEEDS else f"current/{feed}"
        require(snap["origin"]["kind"] == "result" and snap["origin"]["path"] == f"{directory}/result.json" and
                snap["csv"] == f"{directory}/observations.csv", f"snapshot paths {feed}")
        if feed in QVIX_FEEDS:
            require(snap["shared"]["path"] == "current/qvix-group/group.json" and
                    snap["wrapper"] == f"{directory}/wrapper.csv" and snap["quality"] == f"{directory}/quality.json",
                    f"QVIX paths {feed}")
        times = [instant(snap[k]) for k in ("attempted_at", "successful_at", "finished_at")]
        require(begin <= times[0] <= times[1] <= times[2] <= end, f"member time {feed}")
        acquired = snap.get("acquired_at", snap.get("raw", {}).get("retrieved_at"))
        # Cached QVIX siblings share one earlier response; the verifier binds its identity.
        lower, upper = (begin, times[1]) if feed in QVIX_FEEDS else (times[0], times[2])
        require(lower <= instant(acquired) <= upper, f"acquisition time {feed}")
        require(all(START <= row["date"] <= cutoff for row in read_csv(candidate_root / snap["csv"])),
                f"selected cutoff {feed}")
        prior = previous["feeds"][feed]["snapshot"]
        require(prior is not None, f"missing baseline {feed}")
        low = max(START, previous["window"][0], prior["window"][0])
        high = min(cutoff, previous["window"][1], prior["window"][1])
        old = {d for d in source_dates(baseline_root, prior, feed) if low <= d <= high}
        new = source_dates(candidate_root, snap, feed)
        lost = sorted(old - new)
        require(not lost, f"source dates lost {feed}: {lost}; prior={prior['origin']}; new={snap['origin']}")
        details[feed] = {"status": snap["status"], "origin": snap["origin"],
                         "range": snap["range"], "overlap": [low, high], "retained_dates": len(old)}
    require(code == int(partial), "fetch exit/status mismatch")
    return "partial" if partial else "success", details


def _feed_content(root, feed, snap):
    """Publication inputs of an independently replayed snapshot, not its acquisition ID."""
    from app.core import QVIX_FEEDS
    if feed in QVIX_FEEDS:
        raw = json.loads((root / snap["shared"]["path"]).read_bytes())["raw"]
        quality = snap["accounting"]
        comp = quality["comparator"]
        # A fresh comparator has new paths/timestamps even when its history is identical.
        binding = comp and {k: comp[k] for k in ("feed", "raw_sha256", "csv_sha256", "stale_reuse")}
        derived = (snap["wrapper_sha256"], quality | {"comparator": binding})
    else:
        raw = snap["raw"]
        derived = snap["identity"]
    return (snap["status"], snap["versions"], snap["invocation"], snap["csv_sha256"], derived,
            tuple(raw[k] for k in ("requested_url", "url", "encoding", "sha256")))


def _same_data(baseline_root, candidate_root, previous, candidate):
    # A later cutoff alone is not a revision. Selected CSVs *and* windowed quality
    # still change if a previously out-of-window row becomes material.
    return (previous.get("operation") == "acquisition" and previous["window"][0] == START and
            previous["window"][1] <= candidate["window"][1] and
            all(not old["stale_reuse"] and old["snapshot"]["window"] == previous["window"] and
                _feed_content(baseline_root, feed, old["snapshot"]) ==
                _feed_content(candidate_root, feed, candidate["feeds"][feed]["snapshot"])
                for feed, old in previous["feeds"].items()))


def execute(command, log):
    try:
        with log.open("w") as handle:
            return subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, timeout=1200).returncode
    finally:
        if log.exists() and log.stat().st_size > 4 * 1024 * 1024:
            with log.open("r+b") as handle:
                handle.truncate(4 * 1024 * 1024)
            raise ValueError("command diagnostic exceeded 4 MiB; truncated")

def preserve_evidence(stage, diagnostics):
    data, html = stage / "data", stage / "index.html"
    paths = data.rglob("*") if data.is_dir() and not data.is_symlink() else ()
    sources = ((p, diagnostics / "new-evidence" / p.relative_to(data)) for p in paths)
    copied_bytes = copied_files = 0
    for path, target in chain(sources, ((html, diagnostics / "candidate.html"),) if html.exists() else ()):
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            continue
        copied_files += 1
        copied_bytes += info.st_size
        if copied_files > MAX_FILES or copied_bytes > MAX_BYTES:
            (diagnostics / "TRUNCATED").write_text("Evidence exceeds 512 files / 256 MiB\n")
            break
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def prepare(root, work, identity, clock=utc_now, runner=execute, *, publish_unchanged=False):
    from app.core import load_manifest
    root, work = Path(root), Path(work)
    started = clock()
    cutoff = started.astimezone(timezone.utc).date().isoformat()
    work.mkdir(parents=True, exist_ok=False)
    diagnostics = work / "diagnostics"
    diagnostics.mkdir()
    outcome = {"identity": identity, "started_at": started.isoformat(), "window": [START, cutoff],
               "eligible": False, "phase": "baseline", "lock_sha256": digest((root / "uv.lock").read_bytes())}
    stage = work / "stage"
    baseline_root, candidate_root = root / "data", stage / "data"
    try:
        require(runner([sys.executable, "-m", "app.verify", "--input", str(baseline_root),
                        "--report", str(root / "index.html")], diagnostics / "baseline.log") == 0,
                "baseline verification failed")
        previous = load_manifest(baseline_root)
        stage.mkdir()
        outcome["phase"] = "acquisition"
        invoked = clock()
        code = runner([sys.executable, "-m", "app.fetch", "--candidate", "--output", str(candidate_root),
                       "--start", START, "--end", cutoff], diagnostics / "fetch.log")
        finished = clock()
        outcome.update(fetch_exit=code, invocation_start=invoked.isoformat(), invocation_finish=finished.isoformat())
        require(code in (0, 1), "unexpected fetch exit")
        require((candidate_root / "current/manifest.json").is_file(), "no new acquisition")
        candidate = load_manifest(candidate_root)
        outcome["attempted_at"] = candidate["attempted_at"]
        outcome["feeds"] = {f: {"attempt": s["attempt"]["status"], "stale": s["stale_reuse"],
                                  "origin": s["snapshot"].get("origin") if s["snapshot"] else None}
                            for f, s in candidate["feeds"].items()}
        outcome["phase"] = "candidate verification"
        require(runner([sys.executable, "-m", "app.chart", "--input", str(candidate_root),
                        "--output", str(stage / "index.html")], diagnostics / "chart.log") == 0,
                "chart failed")
        require(runner([sys.executable, "-m", "app.verify", "--input", str(candidate_root),
                        "--report", str(stage / "index.html")], diagnostics / "candidate.log") == 0,
                "candidate verification failed")
        quality, details = eligibility(baseline_root, candidate_root, previous, candidate, code, invoked, finished, cutoff)
        outcome.update(quality=quality, retention=details)
        files, attempted_at = payload_inventory(stage)
        require(attempted_at == candidate["attempted_at"], "candidate acquisition identity changed")
        if not publish_unchanged and _same_data(baseline_root, candidate_root, previous, candidate):
            # Compare at the same acquisition ID: a renderer-only change must still ship.
            rebuilt = work / "baseline.html"
            require(runner([sys.executable, "-m", "app.chart", "--input", str(baseline_root),
                            "--output", str(rebuilt)], diagnostics / "baseline-chart.log") == 0,
                    "baseline chart rebuild failed")
            if filecmp.cmp(rebuilt, root / "index.html", shallow=False):
                outcome.update(eligible=True, phase="unchanged", retained_attempted_at=previous["attempted_at"])
                return outcome
        bundle = work / "bundle"
        payload = bundle / "payload"
        shutil.copytree(stage, payload)
        copied, _ = payload_inventory(payload)
        require(copied == files, "candidate bytes changed during transfer")
        receipt = {"identity": identity, "attempted_at": attempted_at, "window": [START, cutoff],
                   "started_at": started.isoformat(), "fetch_exit": code, "quality": quality,
                   "verified": True, "files": files}
        body = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
        (bundle / "receipt.json").write_bytes(body)
        outcome.update(eligible=True, receipt_hash=digest(body), phase="publish")
        return outcome
    except Exception as error:
        outcome["error"] = f"{type(error).__name__}: {error}"[:32768]
        raise
    finally:
        outcome["finished_at"] = clock().isoformat()
        (diagnostics / "outcome.json").write_text(json.dumps(outcome, indent=2) + "\n")
        if not outcome["eligible"] and stage.exists():
            preserve_evidence(stage, diagnostics)


def main():
    import os
    import signal
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", required=True)
    args = parser.parse_args()
    identity = identity_from_env()
    env = auth_env()
    os.environ.pop("GH_TOKEN", None)
    remote_head(Path.cwd(), identity["branch"], identity["base_sha"], env)
    def deadline(signum, frame):
        raise TimeoutError("25-minute preparation deadline")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(25 * 60)
    try:
        result = prepare(Path.cwd(), args.work, identity,
                         publish_unchanged=os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch")
    finally:
        signal.alarm(0)
        outcome_path = Path(args.work) / "diagnostics/outcome.json"
        if outcome_path.is_file() and os.environ.get("GITHUB_STEP_SUMMARY"):
            outcome = json.loads(outcome_path.read_text())
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
                summary.write(f"UTC window: {outcome['window']}; eligible: {outcome['eligible']}; "
                              f"phase: {outcome['phase']}; fetch exit: {outcome.get('fetch_exit', 'not reached')}\n\n")
                if outcome.get("retained_attempted_at"):
                    summary.write(f"Verified unchanged against `{outcome['retained_attempted_at']}`; "
                                  "no new snapshot or deployment requested.\n\n")
                if "receipt_hash" in outcome:
                    summary.write(f"Candidate receipt SHA256: `{outcome['receipt_hash']}`\n\n")
                summary.write("| Feed | Attempt | Stale |\n|---|---|---|\n")
                for feed, state in outcome.get("feeds", {}).items():
                    summary.write(f"| {feed} | {state['attempt']} | {state['stale']} |\n")
    with open(os.environ["GITHUB_OUTPUT"], "a") as handle:
        handle.write(f"publication={result['phase']}\nquality={result['quality']}\n")
        if result["phase"] == "publish":
            handle.write(f"receipt_hash={result['receipt_hash']}\n")


if __name__ == "__main__":
    main()
