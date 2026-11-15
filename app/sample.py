"""One bounded, explicit import of the ten historical documentation example rows."""
import re
from pathlib import Path

import requests

from app.core import csv_bytes, dump, now, sha, validate

COMMIT = "8fc02741a1807a2fa111d5baf119b19c5718ae79"
BASE = f"https://raw.githubusercontent.com/akfamily/akshare/{COMMIT}/"
DOC_HASH = "3e8d086441ec1d252d556050d5b5a1112bc2199112d90daddf267d3228c89785"
ROOT = Path("data/documentation-example")


def transcribe(excerpt):
    matches = re.findall(r"^\d+\s+(\d{4}-\d{2}-\d{2})\s+([\d.]+)\s+([\d.]+)\s*$", excerpt, re.M)
    rows = [{"date": d, "sentiment": float(s), "market_close": float(m)} for d, s, m in matches]
    if len(rows) != 10:
        raise ValueError("documentation transcription must contain exactly ten explicit rows")
    return validate(rows, ["sentiment", "market_close"])


def main():
    if ROOT.exists():
        raise SystemExit("immutable documentation source already exists; use verify, not overwrite")
    responses = {}
    for name, path in (("source.md", "docs/data/index/index.md"), ("LICENSE", "LICENSE")):
        response = requests.get(BASE + path, timeout=(5, 12))
        response.raise_for_status()
        responses[name] = response
    source = responses["source.md"].content
    license_body = responses["LICENSE"].content
    if sha(source) != DOC_HASH:
        raise ValueError("immutable documentation source hash differs from research evidence")
    license_text = license_body.decode()
    if "MIT License" not in license_text or "Permission is hereby granted, free of charge" not in license_text:
        raise ValueError("MIT permission not established; no redistribution")
    text = source.decode()
    match = re.search(r"\(index_news_sentiment_scope\)=.*?\[241 rows x 3 columns\]\n```", text, re.S)
    if match is None:
        raise ValueError("documented example section not found")
    excerpt = match.group(0)
    rows = transcribe(excerpt)
    ROOT.mkdir(parents=True)
    for name, response in responses.items():
        (ROOT / name).write_bytes(response.content)
    (ROOT / "excerpt.txt").write_text(excerpt)
    body = csv_bytes(rows, ["sentiment", "market_close"])
    (ROOT / "documentation-example.csv").write_bytes(body)
    dump(ROOT / "provenance.json", {
        "classification": "AKShare documentation example, not live/full history or provider response",
        "source_commit": COMMIT, "retrieved_at": now(), "license": "MIT",
        "permission_basis": "Repository MIT license at same immutable commit; copyright and permission retained",
        "source_url": BASE + "docs/data/index/index.md", "license_url": BASE + "LICENSE",
        "source_sha256": sha(source), "license_sha256": sha(license_body),
        "excerpt_sha256": sha(excerpt.encode()), "csv_sha256": sha(body),
        "original_capture_at": None, "published_at": None, "revision_at": None,
        "count": len(rows), "range": [rows[0]["date"], rows[-1]["date"]],
        "http": {n: {"url": r.url, "status": r.status_code, "headers": dict(r.headers),
                        "body_semantics": "HTTP-decompressed response body"} for n, r in responses.items()},
        "omitted_rows": "231 not recovered; ellipsis is not data; no interpolation"})
    print("MIT source retained; ten documentation-only rows transcribed")


if __name__ == "__main__":
    main()
