"""Sequential bounded index workers and one durable shared-cache QVIX worker."""
import argparse
import importlib.metadata
import json
import os
import subprocess
import sys
import uuid
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from app.core import (
    INDICES, OHLC, QVIX_FEEDS, SCHEMA, artifact_ref, atomic, bounds, common_qvix,
    compact_quality, comparator_history, csv_bytes, decode, now, qvix_artifacts, selected, sha,
)
from app.identities import IDENTITIES


INDEX_HTTP_TIMEOUT = (5, 12)
QVIX_GROUP_SECONDS = 5 * 60
QVIX_HTTP_TIMEOUT = (5, QVIX_GROUP_SECONDS)


def durable_mkdir(path):
    path = Path(path)
    if path.exists():
        return
    durable_mkdir(path.parent)
    path.mkdir()
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def durable_bytes(path, content):
    with Path(path).open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


@contextmanager
def capture_http(root, directory, timeout):
    import requests
    from akshare.utils import http
    captures = []
    def capture(response, *args, **kwargs):
        body = response.content
        path = directory / f"response-{len(captures)}.body"
        durable_bytes(path, body)
        captures.append({"body": str(path.relative_to(root)), "sha256": sha(body),
                         "url": response.url, "requested_url": response.request.url,
                         "status": response.status_code, "headers": dict(response.headers),
                         "encoding": response.encoding or "utf-8", "retrieved_at": now(),
                         "http_decompressed": True})
        atomic(directory / "transport.json", captures)
        return response
    def get(url, **kwargs):
        return requests.get(url, **kwargs, timeout=timeout, hooks={"response": capture})
    original = http.get
    http.get = get
    try:
        yield captures
    finally:
        http.get = original


def attempt(feed, window):
    return {"feed": feed, "attempted_at": now(), "window": window,
            "versions": {k: importlib.metadata.version(k)
                         for k in ("akshare", "requests", "pandas", "mini-racer")},
            "request_timeout_seconds": list(QVIX_HTTP_TIMEOUT if feed in QVIX_FEEDS else INDEX_HTTP_TIMEOUT)}


def transport(root, directory, captures):
    if len(captures) != 1 or captures[0]["status"] != 200:
        raise ValueError("expected one HTTP200 response; redirects rejected")
    raw = captures[0]
    return {"raw": raw, "transport": str((directory / "transport.json").relative_to(root)),
            "transport_sha256": sha((directory / "transport.json").read_bytes())}


def worker(feed, directory, start, end):
    import akshare as ak
    directory = Path(directory)
    root = directory.parents[2]
    result = attempt(feed, [start, end])
    result["invocation"] = f"index_zh_daily_sina(symbol={feed!r})"
    with capture_http(root, directory, INDEX_HTTP_TIMEOUT) as captures:
        try:
            ak.index_zh_daily_sina(symbol=feed)
            result.update(transport(root, directory, captures))
            raw = result["raw"]
            rows = selected(decode(feed, (root / raw["body"]).read_bytes(), raw["encoding"]), start, end)
            content = csv_bytes(rows, ["close", "pre_release", "pre_base"])
            durable_bytes(directory / "observations.csv", content)
            result.update(status="success", csv=str((directory / "observations.csv").relative_to(root)),
                          csv_sha256=sha(content), count=len(rows), range=bounds({r["date"] for r in rows}),
                          identity=IDENTITIES[feed], retrospective_count=sum(r["pre_release"] for r in rows),
                          successful_at=now())
        except Exception as error:
            result.update(status="failure", error=f"{type(error).__name__}: {error}", captures=captures)
    result["finished_at"] = now()
    atomic(directory / "result.json", result)


def bind_comparator(feed, states):
    code = QVIX_FEEDS[feed]["comparator"]
    state = states[code]
    snap = state["snapshot"]
    if not snap:
        return None
    return {k: snap[k] for k in ("origin", "csv", "csv_sha256", "successful_at")} | {
        "feed": code, "raw_sha256": snap["raw"]["sha256"], "stale_reuse": state["stale_reuse"]}


def group_worker(directory):
    import akshare as ak
    import akshare.index.index_option_qvix as module
    directory = Path(directory)
    root = directory.parents[2]
    config = json.loads((directory / "config.json").read_text())
    cache = getattr(module, "__get_optbbs_daily")
    cache.cache_clear()
    group = None
    shared_error = None
    try:
        with capture_http(root, directory, QVIX_HTTP_TIMEOUT) as captures:
            def loader():
                nonlocal group, shared_error
                if shared_error:
                    raise ValueError(shared_error)
                try:
                    frame = cache()
                    if group is None:
                        evidence = transport(root, directory, captures)
                        common_qvix((root / evidence["raw"]["body"]).read_bytes())
                        group = evidence | {"group_id": config["group_id"],
                                            "acquired_at": evidence["raw"]["retrieved_at"],
                                            "global_validated": True,
                                            "config": artifact_ref(root, str((directory / "config.json").relative_to(root)))}
                        atomic(directory / "group.json", group)
                    return frame
                except Exception as error:
                    shared_error = f"{type(error).__name__}: {error}"
                    raise
            setattr(module, "__get_optbbs_daily", loader)
            for feed, definition in QVIX_FEEDS.items():
                member = directory / feed
                durable_mkdir(member)
                result = attempt(feed, config["window"]) | {
                    "group_id": config["group_id"], "invocation": definition["wrapper"] + "()",
                    "invoked": shared_error is None, "columns": definition["columns"]}
                atomic(member / "invocation.json", result)
                if shared_error:
                    result.update(status="failure", error="shared load/global failure: " + shared_error)
                else:
                    try:
                        wrapper = getattr(ak, definition["wrapper"])().to_csv(index=False).encode()
                        durable_bytes(member / "wrapper.csv", wrapper)
                        comparator = config["comparators"][feed]
                        rows, quality, status = qvix_artifacts(
                            (root / group["raw"]["body"]).read_bytes(), wrapper, config["window"],
                            comparator_history(root, comparator), comparator, feed)
                        durable_bytes(member / "observations.csv", csv_bytes(rows, [*OHLC, "quality"]))
                        atomic(member / "quality.json", quality)
                        result.update(status=status, schema=SCHEMA, successful_at=now(),
                                      acquired_at=group["acquired_at"],
                                      shared=artifact_ref(root, str((directory / "group.json").relative_to(root))),
                                      accounting=compact_quality(quality), count=len(rows),
                                      range=bounds({r["date"] for r in rows}),
                                      source_range=quality["full"]["range"])
                        for key, filename in (("csv", "observations.csv"), ("quality", "quality.json"),
                                              ("wrapper", "wrapper.csv")):
                            ref = artifact_ref(root, str((member / filename).relative_to(root)))
                            result[key], result[key + "_sha256"] = ref["path"], ref["sha256"]
                    except Exception as error:
                        result.update(status="failure", error=f"{type(error).__name__}: {error}")
                result["finished_at"] = now()
                # This is the commit record: all artifacts fsynced before its atomic rename.
                atomic(member / "result.json", result)
    finally:
        setattr(module, "__get_optbbs_daily", cache)
        cache.cache_clear()


def state_after(old, result):
    usable = result["status"] in ("success", "partial")
    snapshot = result if usable else old.get("snapshot")
    return {"attempt": result, "snapshot": snapshot, "stale_reuse": not usable and bool(snapshot)}


def completed(root, path):
    result = json.loads(path.read_text())
    if result["status"] in ("success", "partial"):
        result["origin"] = artifact_ref(root, str(path.relative_to(root))) | {"kind": "result"}
    return result


def recover_group(root, directory, termination=None):
    from app.verify import validate_snapshot
    config = json.loads((directory / "config.json").read_text())
    results = {}
    for feed in QVIX_FEEDS:
        member = directory / feed
        record = member / "result.json"
        try:
            if not record.exists():
                raise ValueError("unfinished member")
            result = completed(root, record)
            if result["status"] in ("success", "partial"):
                validate_snapshot(root, result, feed)
                if result["group_id"] != config["group_id"]:
                    raise ValueError("group attempt identity")
        except Exception as error:
            invoked = member / "invocation.json"
            result = (json.loads(invoked.read_text()) if invoked.exists() else
                      attempt(feed, config["window"]) | {"invoked": False, "group_id": config["group_id"]})
            result.update(status="failure", error=f"recovery: {error}", finished_at=now())
        if termination:
            result = result if result["status"] in ("success", "partial") else result | {"termination": termination}
        results[feed] = result
    return results


def promote(root, manifest):
    from app.verify import validate_manifest
    validate_manifest(root, manifest)
    path = root / manifest["manifest_path"]
    if path.exists():
        if json.loads(path.read_text()) != manifest:
            raise ValueError("refusing immutable manifest overwrite")
    else:
        atomic(path, manifest)
    atomic(root / "latest.json", manifest)


def fetch(root, start, end):
    root = Path(root).resolve()
    durable_mkdir(root)
    previous = json.loads((root / "latest.json").read_text()) if (root / "latest.json").exists() else {}
    if previous and previous.get("schema") != SCHEMA:
        raise ValueError("incompatible active schema; explicit derived migration required")
    run = "runs/" + now().replace(":", "-") + "-" + uuid.uuid4().hex[:8]
    manifest = {"schema": SCHEMA, "run": run, "attempted_at": now(), "window": [start, end],
                "feeds": {}, "manifest_path": run + "/manifest.json", "worker_wall_seconds": 45,
                "qvix_group_wall_seconds": QVIX_GROUP_SECONDS,
                "operation": "acquisition",
                "revision_policy": "whole snapshots only; not point-in-time"}
    if previous:
        manifest["previous"] = artifact_ref(root, previous["manifest_path"])
    for feed in INDICES:
        directory = root / run / feed
        durable_mkdir(directory)
        try:
            subprocess.run([sys.executable, "-m", "app.fetch", "--worker", feed, str(directory), start, end],
                           timeout=manifest["worker_wall_seconds"], check=True)
            result = completed(root, directory / "result.json")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
            result = attempt(feed, [start, end]) | {"status": "failure", "error": str(error),
                                                   "finished_at": now()}
            if (directory / "transport.json").exists():
                result["captures"] = json.loads((directory / "transport.json").read_text())
            atomic(directory / "terminated.json", result)
        manifest["feeds"][feed] = state_after(previous.get("feeds", {}).get(feed, {}), result)
        print(feed, result["status"], result.get("count", "unknown"), flush=True)
    directory = root / run / "qvix-group"
    durable_mkdir(directory)
    atomic(directory / "config.json", {"group_id": uuid.uuid4().hex, "window": [start, end],
                                      "comparators": {f: bind_comparator(f, manifest["feeds"]) for f in QVIX_FEEDS}})
    termination = None
    try:
        subprocess.run([sys.executable, "-m", "app.fetch", "--group-worker", str(directory)],
                       timeout=manifest["qvix_group_wall_seconds"], check=True)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
        termination = str(error)
        atomic(directory / "termination.json", {"error": termination, "finished_at": now()})
    for feed, result in recover_group(root, directory, termination).items():
        manifest["feeds"][feed] = state_after(previous.get("feeds", {}).get(feed, {}), result)
        print(feed, result["status"], result.get("count", "unknown"), flush=True)
    manifest["finished_at"] = now()
    promote(root, manifest)
    return int(any(s["attempt"]["status"] != "success" for s in manifest["feeds"].values()))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker(*sys.argv[2:])
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "--group-worker":
        group_worker(sys.argv[2])
        return 0
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data")
    parser.add_argument("--start", default="2000-01-01")
    parser.add_argument("--end", default=date.today().isoformat())
    args = parser.parse_args()
    if date.fromisoformat(args.start) > date.fromisoformat(args.end):
        parser.error("start must precede end")
    return fetch(args.output, args.start, args.end)


if __name__ == "__main__":
    sys.exit(main())
