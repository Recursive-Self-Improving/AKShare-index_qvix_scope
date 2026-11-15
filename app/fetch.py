"""Sequential AKShare calls in bounded subprocesses, capture before application decoding."""
import argparse
import importlib.metadata
import json
import subprocess
import sys
import uuid
from datetime import date
from pathlib import Path

from app.core import (
    INDICES, PUBLICATION, atomic, csv_bytes, decode, dump, now, selected, selected_history, sha,
)
from app.identities import IDENTITIES


def worker(feed, directory, start, end):
    import akshare as ak
    import requests
    from akshare.utils import http

    directory = Path(directory)
    captures = []
    attempted = now()
    versions = {k: importlib.metadata.version(k) for k in ("akshare", "requests", "pandas", "mini-racer")}

    def capture(response, *args, **kwargs):
        body = response.content  # HTTP-decompressed, before JSON/JS decoding; not wire bytes.
        index = len(captures)
        path = directory / f"response-{index}.body"
        path.write_bytes(body)
        meta = {"body": str(path), "sha256": sha(body), "url": response.url,
                "requested_url": response.request.url, "status": response.status_code,
                "headers": dict(response.headers), "encoding": response.encoding or "utf-8",
                "retrieved_at": now(), "http_decompressed": True}
        captures.append(meta)
        dump(directory / "transport.json", captures)
        return response

    def get(url, **kwargs):
        return requests.get(url, **kwargs, timeout=(5, 12), hooks={"response": capture})

    original = http.get
    result = {"feed": feed, "attempted_at": attempted, "versions": versions,
              "window": [start, end], "invocation": "index_news_sentiment_scope()" if feed == "sentiment"
              else f"index_zh_daily_sina(symbol={feed!r})", "request_timeout_seconds": [5, 12]}
    try:
        http.get = get
        if feed == "sentiment":
            try:
                ak.index_news_sentiment_scope()  # Actual pinned invocation, not a direct-request substitute.
            except KeyError as error:
                # 1.20.53 projects missing columns on its empty DataFrame. Accept only
                # that frame/state, plus an independently validated HTTP200 [] below.
                tb = error.__traceback__
                while tb and tb.tb_frame.f_code is not ak.index_news_sentiment_scope.__code__:
                    tb = tb.tb_next
                empty_projection = (
                    tb is not None and tb.tb_next is not None
                    and tb.tb_next.tb_frame.f_globals.get("__name__") == "pandas.core.frame"
                    and tb.tb_next.tb_frame.f_code.co_name == "__getitem__"
                    and tb.tb_next.tb_frame.f_locals.get("key") == ["日期", "市场情绪指数", "沪深300指数"]
                    and tb.tb_frame.f_locals.get("data_json") == []
                    and tb.tb_frame.f_locals.get("temp_df") is not None
                    and tb.tb_frame.f_locals["temp_df"].shape == (0, 0)
                )
                if not (empty_projection and captures and captures[-1]["status"] == 200
                        and decode(feed, Path(captures[-1]["body"]).read_bytes(),
                                   captures[-1]["encoding"]) == []):
                    raise
                result["wrapper_empty_projection"] = "AKShare 1.20.53 empty DataFrame column KeyError"
        else:
            ak.index_zh_daily_sina(symbol=feed)
        if not captures or captures[-1]["status"] != 200:
            raise ValueError("no successful captured body")
        raw = captures[-1]
        rows = decode(feed, Path(raw["body"]).read_bytes(), raw["encoding"])
        rows = selected(rows, start, end)
        fields = ["sentiment", "market_close"] if feed == "sentiment" else ["close", "pre_release", "pre_base"]
        body = csv_bytes(rows, fields)
        path = directory / "observations.csv"
        path.write_bytes(body)
        result.update(status="success", csv=str(path), csv_sha256=sha(body), raw=raw,
                      count=len(rows), range=[rows[0]["date"], rows[-1]["date"]] if rows else None,
                      successful_at=now(), publication_date=PUBLICATION.get(feed),
                      retrospective_count=sum(r["date"] < PUBLICATION[feed] for r in rows)
                      if feed in PUBLICATION else None,
                      identity=IDENTITIES.get(feed))
    except Exception as error:
        transport_error = isinstance(error, requests.RequestException) and not isinstance(error, ValueError)
        result.update(status="transport_failure" if transport_error else "validation_failure",
                      error=f"{type(error).__name__}: {error}")
    finally:
        http.get = original
        result["finished_at"] = now()
        result["captures"] = captures
        dump(directory / "result.json", result)


def promote(root, manifest):
    """Only publish after all referenced immutable artifacts validate."""
    for feed, state in manifest["feeds"].items():
        revisions = state.get("revisions", [])
        if state.get("snapshot") != (revisions[-1] if revisions else None):
            raise ValueError("stale snapshot identity differs from latest successful revision")
        for snapshot in revisions:
            if snapshot["feed"] != feed or snapshot["status"] != "success":
                raise ValueError("snapshot source identity mismatch")
            for key, hashkey in (("csv", "csv_sha256"),):
                if sha((root / snapshot[key]).read_bytes()) != snapshot[hashkey]:
                    raise ValueError("snapshot hash mismatch")
            raw = snapshot["raw"]
            if sha((root / raw["body"]).read_bytes()) != raw["sha256"]:
                raise ValueError("raw hash mismatch")
            rows = selected(decode(feed, (root / raw["body"]).read_bytes(), raw["encoding"]),
                            *snapshot["window"])
            fields = ["sentiment", "market_close"] if feed == "sentiment" else ["close", "pre_release", "pre_base"]
            if csv_bytes(rows, fields) != (root / snapshot["csv"]).read_bytes():
                raise ValueError("raw/CSV replay mismatch")
    dump(root / manifest["manifest_path"], manifest)
    atomic(root / "latest.json", manifest)


def fetch(root, start, end):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    previous = json.loads((root / "latest.json").read_text()) if (root / "latest.json").exists() else {}
    run = "runs/" + now().replace(":", "-") + "-" + uuid.uuid4().hex[:8]
    manifest = {"run": run, "attempted_at": now(), "window": [start, end], "feeds": {},
                "manifest_path": run + "/manifest.json", "worker_wall_seconds": 45,
                "revision_policy": "latest successful snapshot observation by date; not point-in-time",
                "calendar": "sh000001 relative comparator, non-independent; common omissions unknown"}
    for feed in [*INDICES, "sentiment"]:
        directory = root / run / feed
        directory.mkdir(parents=True)
        try:
            subprocess.run([sys.executable, "-m", "app.fetch", "--worker", feed, str(directory), start, end],
                           timeout=45, check=True)
            result = json.loads((directory / "result.json").read_text())
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
            result = {"feed": feed, "status": "wall_deadline_failure", "attempted_at": manifest["attempted_at"],
                      "error": str(error), "finished_at": now()}
            dump(directory / "result.json", result)
        old = previous.get("feeds", {}).get(feed, {})
        revisions = list(old.get("revisions", []))
        if result["status"] == "success":
            # Stored references are root-relative; worker evidence remains immutable too.
            snapshot = dict(result)
            snapshot["csv"] = str(Path(result["csv"]).relative_to(root))
            snapshot["raw"] = dict(result["raw"])
            snapshot["raw"]["body"] = str(Path(result["raw"]["body"]).relative_to(root))
            revisions.append(snapshot)
        manifest["feeds"][feed] = {"attempt": result, "revisions": revisions,
                                   "snapshot": revisions[-1] if revisions else None,
                                   "stale_reuse": result["status"] != "success" and bool(revisions)}
        print(feed, result["status"], result.get("count", "unknown"), flush=True)
    manifest["finished_at"] = now()
    dump(root / "identities.json", IDENTITIES)
    coverage = selected_history(root, manifest)
    for feed, state in manifest["feeds"].items():
        state["selected_history"] = coverage[feed]
        state["early_interval"] = "Before first vendor observation: availability unknown, not inferred pre-inception"
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
