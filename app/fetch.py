"""Eight sequential bounded actual AKShare invocations and atomic whole snapshots."""
import argparse
import importlib.metadata
import json
import subprocess
import sys
import uuid
from datetime import date
from pathlib import Path

from app.core import (
    INDICES, OHLC, QVIX, SCHEMA, artifact_ref, atomic, compact_quality, comparator_history,
    csv_bytes, decode, dump, now, qvix_artifacts, raw_qvix, replay_qvix, selected, sha,
)
from app.identities import IDENTITIES


def worker(feed, directory, start, end):
    import akshare as ak
    import requests
    from akshare.utils import http

    directory = Path(directory)
    captures = []
    result = {"feed": feed, "attempted_at": now(), "window": [start, end],
              "versions": {k: importlib.metadata.version(k)
                           for k in ("akshare", "requests", "pandas", "mini-racer")},
              "invocation": "index_option_50etf_qvix()" if feed == QVIX
              else f"index_zh_daily_sina(symbol={feed!r})", "request_timeout_seconds": [5, 12]}

    def capture(response, *args, **kwargs):
        body = response.content
        path = directory / f"response-{len(captures)}.body"
        path.write_bytes(body)
        captures.append({"body": str(path), "sha256": sha(body), "url": response.url,
                         "requested_url": response.request.url, "status": response.status_code,
                         "headers": dict(response.headers), "encoding": response.encoding or "utf-8",
                         "retrieved_at": now(), "http_decompressed": True})
        dump(directory / "transport.json", captures)
        if feed == QVIX and response.status_code == 200:
            raw_qvix(body)  # Before the wrapper's coercive conversion.
        return response

    def get(url, **kwargs):
        return requests.get(url, **kwargs, timeout=(5, 12), hooks={"response": capture})

    original = http.get
    try:
        http.get = get
        if feed == QVIX:
            import akshare.index.index_option_qvix as module
            getattr(module, "__get_optbbs_daily").cache_clear()
            wrapper = ak.index_option_50etf_qvix().to_csv(index=False).encode()
            (directory / "wrapper.csv").write_bytes(wrapper)
        else:
            ak.index_zh_daily_sina(symbol=feed)
        if len(captures) != 1 or captures[0]["status"] != 200:
            raise ValueError("expected one HTTP200 response; redirects are not accepted")
        raw = captures[0]
        body = Path(raw["body"]).read_bytes()
        if feed == QVIX:
            if replay_qvix(body) != wrapper:
                raise ValueError("captured body/wrapper replay mismatch")
            result.update(wrapper=str(directory / "wrapper.csv"), wrapper_sha256=sha(wrapper))
        else:
            rows = selected(decode(feed, body, raw["encoding"]), start, end)
            content = csv_bytes(rows, ["close", "pre_release", "pre_base"])
            (directory / "observations.csv").write_bytes(content)
            result.update(csv=str(directory / "observations.csv"), csv_sha256=sha(content),
                          count=len(rows), range=[rows[0]["date"], rows[-1]["date"]] if rows else None,
                          identity=IDENTITIES[feed],
                          retrospective_count=sum(r["pre_release"] for r in rows))
        result.update(status="success", raw=raw, successful_at=now())
    except Exception as error:
        result.update(status="failure", error=f"{type(error).__name__}: {error}")
    finally:
        http.get = original
        result.update(finished_at=now(), captures=captures)
        dump(directory / "result.json", result)


def state_after(old, result):
    usable = result["status"] in ("success", "partial")
    snapshot = result if usable else old.get("snapshot")
    return {"attempt": result, "snapshot": snapshot,
            "stale_reuse": not usable and bool(snapshot)}


def promote(root, manifest):
    from app.verify import validate_manifest
    validate_manifest(root, manifest)
    path = root / manifest["manifest_path"]
    if path.exists():
        if json.loads(path.read_text()) != manifest:
            raise ValueError("refusing immutable manifest overwrite")
    else:
        dump(path, manifest)
    atomic(root / "latest.json", manifest)


def fetch(root, start, end):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    previous = json.loads((root / "latest.json").read_text()) if (root / "latest.json").exists() else {}
    if previous and previous.get("schema") != SCHEMA:
        raise ValueError("incompatible active schema; explicit derived migration required")
    run = "runs/" + now().replace(":", "-") + "-" + uuid.uuid4().hex[:8]
    manifest = {"schema": SCHEMA, "run": run, "attempted_at": now(), "window": [start, end],
                "feeds": {}, "manifest_path": run + "/manifest.json", "worker_wall_seconds": 45,
                "revision_policy": "latest usable whole snapshot; never merge dates; not point-in-time"}
    manifest["operation"] = "acquisition"
    if previous:
        manifest["previous"] = artifact_ref(root, previous["manifest_path"])
    for feed in [*INDICES, QVIX]:
        directory = root / run / feed
        directory.mkdir(parents=True)
        try:
            subprocess.run([sys.executable, "-m", "app.fetch", "--worker", feed, str(directory), start, end],
                           timeout=45, check=True)
            result = json.loads((directory / "result.json").read_text())
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
            result = {"feed": feed, "status": "failure", "attempted_at": manifest["attempted_at"],
                      "error": str(error), "finished_at": now()}
            transport = directory / "transport.json"
            result["captures"] = json.loads(transport.read_text()) if transport.exists() else []
        if result["status"] == "success" and feed == QVIX:
            try:
                comparator_state = manifest["feeds"]["sh000001"]
                comparator_snap = comparator_state["snapshot"]
                comparator = ({"csv": comparator_snap["csv"], "csv_sha256": comparator_snap["csv_sha256"],
                               "successful_at": comparator_snap["successful_at"],
                               "origin": comparator_snap["origin"],
                               "stale_reuse": comparator_state["stale_reuse"]} if comparator_snap else None)
                calendar = comparator_history(root, comparator)
                rows, quality, status = qvix_artifacts(
                    Path(result["raw"]["body"]).read_bytes(), Path(result["wrapper"]).read_bytes(),
                    [start, end], calendar, comparator)
                dump(directory / "quality.json", quality)
                content = csv_bytes(rows, [*OHLC, "quality"])
                (directory / "observations.csv").write_bytes(content)
                result.update(status=status, csv=str(directory / "observations.csv"), csv_sha256=sha(content),
                              quality=str(directory / "quality.json"),
                              quality_sha256=sha((directory / "quality.json").read_bytes()),
                              count=len(rows), range=quality["selected"]["range"],
                              source_range=quality["full"]["range"], accounting=compact_quality(quality),
                              schema=SCHEMA)
            except Exception as error:
                result.update(status="failure", error=f"{type(error).__name__}: {error}")
        snapshot = json.loads(json.dumps(result))
        if snapshot["status"] in ("success", "partial"):
            for key in ("csv", "wrapper", "quality"):
                if key in snapshot:
                    snapshot[key] = str(Path(snapshot[key]).relative_to(root))
            snapshot["raw"]["body"] = str(Path(snapshot["raw"]["body"]).relative_to(root))
            snapshot["transport"] = str((directory / "transport.json").relative_to(root))
            snapshot["transport_sha256"] = sha((directory / "transport.json").read_bytes())
            snapshot.pop("captures", None)
        # Persist the actual result once; future active snapshots bind its immutable hash.
        dump(directory / "result.json", snapshot)
        if snapshot["status"] in ("success", "partial"):
            snapshot["origin"] = artifact_ref(root, str((directory / "result.json").relative_to(root)))
            snapshot["origin"]["kind"] = "result"
        old = previous.get("feeds", {}).get(feed, {})
        if previous.get("schema") != SCHEMA:
            old = {}
        manifest["feeds"][feed] = state_after(old, snapshot)
        print(feed, result["status"], result.get("count", "unknown"), flush=True)
    manifest["finished_at"] = now()
    promote(root, manifest)
    return int(any(s["attempt"]["status"] != "success" for s in manifest["feeds"].values()))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker(*sys.argv[2:])
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
