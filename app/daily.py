"""Read-only preparation: real acquisition in a private, ordinary-copy stage."""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

from app.daily_transfer import MAX_BYTES, MAX_FILES, auth_env, digest, identity_from_env, inventory, remote_head, require


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


def eligibility(root, previous, candidate, code, started, finished, cutoff):
    from app.core import INDICES, QVIX_FEEDS, artifact_ref, read_csv
    require(candidate["run"] != previous["run"] and candidate["operation"] == "acquisition",
            "no new acquisition")
    require(candidate["window"] == [START, cutoff], "incorrect full window")
    require(candidate["previous"] == artifact_ref(root, previous["manifest_path"]), "previous binding")
    require(candidate["manifest_path"] == candidate["run"] + "/manifest.json", "manifest membership")
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
        require(snap["origin"]["kind"] == "result" and
                snap["origin"]["path"].startswith(candidate["run"] + "/"), f"old origin {feed}")
        times = [instant(snap[k]) for k in ("attempted_at", "successful_at", "finished_at")]
        require(begin <= times[0] <= times[1] <= times[2] <= end, f"member time {feed}")
        acquired = snap.get("acquired_at", snap.get("raw", {}).get("retrieved_at"))
        # Cached QVIX siblings share one earlier response; the verifier binds its identity.
        lower, upper = (begin, times[1]) if feed in QVIX_FEEDS else (times[0], times[2])
        require(lower <= instant(acquired) <= upper, f"acquisition time {feed}")
        require(all(START <= row["date"] <= cutoff for row in read_csv(root / snap["csv"])),
                f"selected cutoff {feed}")
        prior = previous["feeds"][feed]["snapshot"]
        require(prior is not None, f"missing baseline {feed}")
        low = max(START, previous["window"][0], prior["window"][0])
        high = min(cutoff, previous["window"][1], prior["window"][1])
        old = {d for d in source_dates(root, prior, feed) if low <= d <= high}
        new = source_dates(root, snap, feed)
        lost = sorted(old - new)
        require(not lost, f"source dates lost {feed}: {lost}; prior={prior['origin']}; new={snap['origin']}")
        details[feed] = {"status": snap["status"], "origin": snap["origin"],
                         "range": snap["range"], "overlap": [low, high], "retained_dates": len(old)}
    require(code == int(partial), "fetch exit/status mismatch")
    return "partial" if partial else "success", details


def execute(command, log):
    try:
        with log.open("w") as handle:
            return subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, timeout=1200).returncode
    finally:
        if log.exists() and log.stat().st_size > 4 * 1024 * 1024:
            with log.open("r+b") as handle:
                handle.truncate(4 * 1024 * 1024)
            raise ValueError("command diagnostic exceeded 4 MiB; truncated")


def prepare(root, work, identity, clock=utc_now, runner=execute):
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
    before = None
    try:
        before = inventory(root / "data", bounded=False)
        require(runner([sys.executable, "-m", "app.verify", "--input", str(root / "data"),
                        "--report", str(root / "index.html")], diagnostics / "baseline.log") == 0,
                "baseline verification failed")
        previous = load_manifest(root / "data")
        stage.mkdir()
        shutil.copytree(root / "data", stage / "data")
        outcome["phase"] = "acquisition"
        invoked = clock()
        code = runner([sys.executable, "-m", "app.fetch", "--output", str(stage / "data"),
                       "--start", START, "--end", cutoff], diagnostics / "fetch.log")
        finished = clock()
        outcome.update(fetch_exit=code, invocation_start=invoked.isoformat(), invocation_finish=finished.isoformat())
        candidate = load_manifest(stage / "data")
        outcome["run"] = candidate["run"]
        outcome["feeds"] = {f: {"attempt": s["attempt"]["status"], "stale": s["stale_reuse"],
                                  "origin": s["snapshot"].get("origin") if s["snapshot"] else None}
                            for f, s in candidate["feeds"].items()}
        require(code in (0, 1), "unexpected fetch exit")
        outcome["phase"] = "candidate verification"
        require(runner([sys.executable, "-m", "app.chart", "--input", str(stage / "data"),
                        "--output", str(stage / "index.html")], diagnostics / "chart.log") == 0,
                "chart failed")
        require(runner([sys.executable, "-m", "app.verify", "--input", str(stage / "data"),
                        "--report", str(stage / "index.html")], diagnostics / "candidate.log") == 0,
                "candidate verification failed")
        quality, details = eligibility(stage / "data", previous, candidate, code, invoked, finished, cutoff)
        outcome.update(quality=quality, retention=details)
        after = inventory(stage / "data", bounded=False)
        require(all(path in after and (path == "latest.json" or facts == after[path])
                    for path, facts in before.items()), "old immutable data changed/deleted")
        additions = set(after) - set(before)
        require(additions and all(p.startswith(candidate["run"] + "/") for p in additions),
                "unexpected additions")
        require(not any(p.startswith(candidate["run"] + "/") for p in before), "run already exists")
        bundle = work / "bundle"
        payload = bundle / "payload"
        payload.mkdir(parents=True)
        for path in sorted(additions | {"latest.json"}):
            target = payload / "data" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(stage / "data" / path, target)
        shutil.copyfile(stage / "index.html", payload / "index.html")
        receipt = {"identity": identity, "run": candidate["run"], "window": [START, cutoff],
                   "started_at": started.isoformat(), "fetch_exit": code, "quality": quality,
                   "verified": True, "files": inventory(payload)}
        body = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
        (bundle / "receipt.json").write_bytes(body)
        outcome.update(eligible=True, receipt_hash=digest(body), phase="eligible")
        return outcome
    except Exception as error:
        outcome["error"] = f"{type(error).__name__}: {error}"[:32768]
        raise
    finally:
        outcome["finished_at"] = clock().isoformat()
        (diagnostics / "outcome.json").write_text(json.dumps(outcome, indent=2) + "\n")
        # Only new evidence, never the baseline, enters expiring failure diagnostics.
        if stage.exists() and before is not None:
            evidence = diagnostics / "new-evidence"
            copied_bytes = copied_files = 0
            for path in (stage / "data").rglob("*"):
                if path.is_file() and not path.is_symlink() and path.relative_to(stage / "data").as_posix() not in before:
                    copied_files += 1
                    copied_bytes += path.stat().st_size
                    if copied_files > MAX_FILES or copied_bytes > MAX_BYTES:
                        (diagnostics / "TRUNCATED").write_text("New evidence exceeds 512 files / 256 MiB\n")
                        break
                    target = evidence / path.relative_to(stage / "data")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
            if (stage / "index.html").is_file() and (stage / "index.html").stat().st_size <= MAX_BYTES:
                shutil.copyfile(stage / "index.html", diagnostics / "candidate.html")


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
        result = prepare(Path.cwd(), args.work, identity)
    finally:
        signal.alarm(0)
        outcome_path = Path(args.work) / "diagnostics/outcome.json"
        if outcome_path.is_file() and os.environ.get("GITHUB_STEP_SUMMARY"):
            outcome = json.loads(outcome_path.read_text())
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
                summary.write(f"UTC window: {outcome['window']}; eligible: {outcome['eligible']}; "
                              f"phase: {outcome['phase']}; fetch exit: {outcome.get('fetch_exit', 'not reached')}\n\n")
                summary.write("| Feed | Attempt | Stale |\n|---|---|---|\n")
                for feed, state in outcome.get("feeds", {}).items():
                    summary.write(f"| {feed} | {state['attempt']} | {state['stale']} |\n")
    with open(os.environ["GITHUB_OUTPUT"], "a") as handle:
        handle.write(f"eligible=true\nquality={result['quality']}\nreceipt_hash={result['receipt_hash']}\n")


if __name__ == "__main__":
    main()
