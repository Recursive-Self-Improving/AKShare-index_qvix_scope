# Round-one correction evidence — R1, R2, B1

Implementation correction slice only; no ledger edits, commits, new provider requests, browser launches, or fabricated acquisition. Read the ledger, README, original F1–F5 review, round-two approval, sample approval, implementation review and subsequent browser review in full. Independent re-review owns acceptance and final visual proof.

## R1 — observed-empty worker success

`app/fetch.py` still invokes the actual pinned `ak.index_news_sentiment_scope()` and captures the exact response through the existing requests hook. AKShare 1.20.53 constructs an empty DataFrame from `[]`, then raises a pandas KeyError projecting the three renamed columns. The correction catches only KeyError around that invocation, requiring the wrapper's own traceback frame, its empty decoded array and `(0, 0)` DataFrame, and the immediate pandas DataFrame `__getitem__` frame with precisely those three columns. It also requires captured HTTP200 and independent strict decoding of the exact saved body to an empty array. The normal strict decode/window/CSV/snapshot/promotion path then handles zero rows. A recorded `wrapper_empty_projection` annotation identifies this compatibility outcome; no response bytes are changed or substituted.

Other wrapper exceptions, non200, malformed payloads and transport failures remain failures. No general exception-to-empty fallback was added. Existing broad failure recording still records errors rather than treating them as successful acquisitions.

Deterministic worker-level tests leave the actual pinned invocation intact and replace only requests transport for HTTP200 `[]`, numeric zero, explicit null, HTTP503 `[]`, and malformed JSON. Successful outputs pass actual `promote` replay; empty success has count0/range null and an identifiable successful snapshot, while numeric zero/null each retain one dated observation. Separate worker tests reject arbitrary KeyError/ValueError after an exact empty capture and preserve missing-body transport failure without a CSV or successful timestamp. Existing HTML/error and decode validation tests remain in force.

## R2 — selected history versus latest response

`app/core.py:histories` is now the shared selected-row policy: indices use the latest successful snapshot; sentiment merges all successful revisions by date, newer success winning only dates it actually contains. The obsolete chart-only merge helper was removed.

`selected_history` derives range, count, relative gaps, extra dates and comparator CSV identity from those selected rows. A missing successful snapshot has count null; observed empty selected history has count0. Future fetch manifests store this under each feed's `selected_history`; immutable snapshot range/count/success time continue to describe only the latest successful response. The report embeds a top-level per-feed `selected_history`, and its visible sentiment warning distinguishes the latest successful response's time/range/count from the merged selected history's range/count/relative-gap count. The non-independent calendar caveat remains explicit.

The independent offline verifier recomputes these fields from raw-replayed records without calling the renderer's coverage helper. It checks all feeds, including sentiment; checks each response snapshot range/count; compares report accounting; and checks new manifest accounting where present. Tampering with selected range, count, gaps, extra dates or comparator identity is rejected for both the embedded report and manifest metadata.

The focused two-revision regression uses a temporary copy of retained evidence, never production transport: first success includes 2024-10-25=0.9 and 2024-10-31=1.0; newer success includes only 2024-10-31=1.1. The built report and full independent verifier retain the older date and revised latest value, selected count2/range 2024-10-25–31, and comparator gaps October28/29/30. Every panel contains `[0.9, null, null, null, 1.1]` at the five matching dates. Latest response remains count1/range October31/success identity `new`; old raw bytes remain intact. Both valid metadata and deliberate mismatches are exercised.

### Evidence-preserving schema migration

No existing acquisition manifest, latest entry, raw response, CSV, transport/result record, snapshot identity, retrieval time or error was rewritten. Existing v1 manifests retain their original latest-response `relative_gaps`, `relative_extra_dates` and `calendar_snapshot`; the verifier checks that legacy meaning against the latest revision's actual rows. New reports derive selected-history accounting from the existing revisions without creating a new run. Only the next genuine fetch writes the new per-feed `selected_history` schema instead of the old standalone gap fields. README documents both meanings and this non-destructive migration.

Retained real run: `runs/2026-11-15T20-37-20.565654+00-00-3d8f6463`. Both `data/latest.json` and that run's `manifest.json` SHA256: `333e7fa27f98d8b71bb8dbb928807328914f5794ab8622480fb79f79d85f8b63`.

Actual sentiment attempt remains `2026-11-15T20:37:32.340823+00:00`, pinned AKShare1.20.53 / pandas3.1.1 / requests2.34.2 / mini-racer0.14.1, `transport_failure` caused by certificate verification failure after the provider redirect. The sole captured HTTP301 body hash remains `9e17cb15dd75bbbd5dbb984eda674863c3b10ab72613cf8a39a00c3e11a8492a`. There are zero successful sentiment revisions and no successful sentiment snapshot; no final TLS response body is invented. The correction does not establish live sentiment availability or full overlays.

## B1 — reserve panel-local legend space

`app/chart.py` moves the legend from the slider/footer area into an explicitly reserved upper band: vertical orientation, left anchor, paper y1.18 with bottom anchor, font12; panel height660, top margin200 and bottom margin125. This allocates room for the two current trace labels and an eventual third genuine trace separately from the plot, range selector and lower slider/date title. Documentation diamond markers retain the full `文档示例 documentation example, not live/full history` label; no warning, trace classification or interaction control was removed.

The final report was rebuilt. This slice did not launch a browser, so actual final legend visibility/non-overlap is not claimed verified here. The independent final browser reviewer must check the rebuilt surface, including the previously reported legend defect. The prior browser review's range-slider path selector error is instrumentation, not a product gap defect; no product change was made for it.

## Commands and observed results

Executed once as a single chained gate (all exit0):

```sh
uv sync --frozen && uv run python -m compileall -q app && uv run ruff check . && uv run pytest -q && uv run python -m app.chart --input data --output report.html && uv run python -m app.verify --input data --report report.html
```

- Frozen sync: `Checked 33 packages in 0.32ms`.
- Compileall: exit0, no output.
- Ruff: `All checks passed!`.
- Pytest: `28 passed, 2 warnings in 70.23s (0:01:10)`; both existing upstream mini-racer ctypes `_pack_` deprecation warnings, not suppressed.
- Chart: seven panels; existing `transport_failure`, original attempt time, genuine coverage unknown, no last successful snapshot remain visible in the generated warning.
- Verify: raw bodies/hashes replay, immutable documentation sources, CSV and seven embedded arrays agree; selected-history accounting also checked. Index counts/ranges: sh000001 6509 (2000-01-04–2026-11-13), sh000016 5552 (2004-01-02–2026-11-13), sh000300 6030 (2002-01-04–2026-11-13), sz399006 3995 (2010-06-01–2026-11-13), sz399673 3017 (2014-06-18–2026-11-13), sh000680/sh000688 each1663 (2020-01-02–2026-11-13). All seven relative gap counts0, not proof of an independent complete exchange calendar.

Identity evidence commands (read-only, exit0):

```sh
sha256sum data/latest.json data/runs/*/manifest.json
uv run python -c 'import json; from pathlib import Path; m=json.loads(Path("data/latest.json").read_text()); s=m["feeds"]["sentiment"]; print(json.dumps({"run":m["run"],"manifest_path":m["manifest_path"],"sentiment_attempt":s["attempt"],"snapshot":s["snapshot"],"revision_count":len(s["revisions"])},ensure_ascii=False,indent=2))'
sha256sum report.html
```

Rebuilt report SHA256: `9545c8e93a44a83489b2db018ee071cacf7957019f9033d8b20124be294698c0`.

Changed paths: `app/fetch.py`, `app/core.py`, `app/chart.py`, `app/verify.py`, `tests/test_contracts.py`, `README.md`, repository `AGENTS.md`, `report.html`, and this evidence file. README changes document the corrected accounting schema/migration; the repo lesson records the verified wrapper pitfall. No acquisition files or ledger were edited. LSP reference requests returned `Unknown request: textDocument/references`; available source/callers were inspected directly. No git status/diff audit or commit was performed; independent re-review handles shared-checkout accounting.
