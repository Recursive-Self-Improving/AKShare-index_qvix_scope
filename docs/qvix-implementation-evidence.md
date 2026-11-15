# QVIX implementation evidence

Implementation slice only; no ledger edit, commit, push, scheduler, browser launch or browser-verification claim. Baseline requested: `c9943caf13`. Active contract: AC9–12, P-Q1–3, D9–11, full qvix-quality-plan.md and qvix-plan-review.md residual obligations. Earlier strict duplicate rejection proposal is superseded.

## Commands and observed proof

- `uv sync --frozen && uv run python -m compileall -q app && uv run ruff check .`: exit0 before acquisition; 33 locked packages checked, Ruff passed.
- `uv run python -m app.fetch --start 2000-01-01 --end 2026-11-15`: actual new sequential eight-source run, **exit1**. No source retry or second real fetch. All seven index workers success; QVIX partial. This nonzero is the required quality policy, not a clean fetch.
- `uv run pytest -q -k 'not offline_real_active'`: 25 passed, one deselected, two upstream mini-racer ctypes deprecation warnings.
- `uv run python -m app.chart --input data --output report.html && uv run python -m app.verify --input data --report report.html && uv run pytest -q`: exit0; actual seven embedded trace pairs/raw replay verified; initial full suite 26 passed, two upstream warnings.
- `uv run pytest -q -k 'promoted_clean or fatal_nonzero'`: one transition test passed; one newly added test fixture failed because its subprocess argument slice read the start date as directory. Corrected fixture from `[5:7]` to `[4:6]`; production subprocess command was correct. No network rerun.
- Artifact inventory/hash and run metadata inspection used `find ... -type f | sort`, `sha256sum .../{response-0.body,wrapper.csv,observations.csv,quality.json,transport.json}`, and a read-only Python JSON print. No Git validation or commit commands.
- LSP references were attempted for `app/core.py:60 csv_bytes`; server returned `-32601 Unknown request: textDocument/references`. An earlier request at line1 correctly returned symbol-not-found. Reference support unavailable; callers were inspected directly. No subdelegates.

Final union checks after the completed source/docs/test edits are recorded below when run. No separate build/typecheck framework exists; compileall is the adopted syntax gate. Offline proof does not satisfy the still-required independent visual/interaction review.

## New real acquisition

Run: `data/runs/2026-11-15T21-47-32.121889+00-00-3b7821e3/`.
Run attempted `2026-11-15T21:47:32.121955+00:00`, finished `2026-11-15T21:47:48.384835+00:00`.
QVIX attempted `2026-11-15T21:47:41.624102+00:00`; captured retrieval `2026-11-15T21:47:47.907836+00:00`; wrapper success timestamp `2026-11-15T21:47:48.027025+00:00` retained on the fresh partial snapshot.
Versions: AKShare1.20.53, requests2.34.2, pandas3.1.1, mini-racer0.14.1.

| Feed | Selected dates | Range | Attempt |
| --- | ---: | --- | --- |
| sh000001 | 6509 | 2000-01-04–2026-11-13 | success |
| sh000016 | 5552 | 2004-01-02–2026-11-13 | success |
| sh000300 | 6030 | 2002-01-04–2026-11-13 | success |
| sz399006 | 3995 | 2010-06-01–2026-11-13 | success |
| sz399673 | 3017 | 2014-06-18–2026-11-13 | success |
| sh000680 | 1663 | 2020-01-02–2026-11-13 | success |
| sh000688 | 1663 | 2020-01-02–2026-11-13 | success |
| qvix_50etf | 2848 | 2015-02-09–2026-11-13 | partial |

Actual pinned wrapper URL and consumed URL are both `http://1.optbbs.com/d/csv/d/k.csv`, HTTP200, one response/no redirect, 928727 HTTP-decompressed bytes. No HTTPS override. The new real response happens to match the retained research spike byte-for-byte; it was acquired anew, not migrated from research. Later research HTTPS matching does not authenticate this HTTP transfer. Provider Last-Modified is not a demonstrated publication time.

QVIX hashes:

| Artifact | SHA256 |
| --- | --- |
| response-0.body | `2e0f2edc8a6bd80cc4ec71fec22d01d933cc29af7de7b2337c406b0fea436071` |
| wrapper.csv | `31261ded64485ebbdf3620a13f8d718c25aec472d1e57536a6105480b3b6f63f` |
| observations.csv | `0ad3d7206585721f30fcd5905fb2074ff3f613577ea3c5897f7b610666ae9849` |
| quality.json | `9d4ac0b2aa5e46516011438fc1055b4fefbcad50955ed245702c8b47ec7e3a85` |
| transport.json | `42a112f7cad45b5be59657ae577c3f5fd3384c1f7393824aaa656fed8be8a263` |

Full response and selected window both contain 2849 source rows, 2848 dates, 2849 distinct date/OHLC candidates, 2847 unambiguous dates, zero exact duplicates, one conflict, eight source-row envelope anomalies. Source is unordered. Conflict 2026-11-02 has source data-row ordinals2841/2843: `(16.21,17.48,15.82,15.92)` and `(16.71,16.86,15.81,15.90)`. All four selected OHLC fields are null. Every original occurrence remains in quality.json; all other observed values remain, including source-only dates.

Relative missing dates: 2024-05-22, 05-23, 05-24, 05-27, 05-29, 05-30, 05-31; 2025-11-10; 2026-09-10, 09-11, 11-03, 11-04, 11-05 (13). Source-only: 2026-08-22, 09-12, 09-13, 11-01 (4). Common QVIX arrays contain14 explicit nulls:13 absent dates plus one conflict, not fabricated OHLC or old-revision fill. Production derives these categories, never hardcodes dates/counts.

Comparator: the **new run's** sh000001/observations.csv, SHA256 `e72c43dbd2b3bf97736d8be6b4d09ce4ff2ebac6432a507f0d70ff861b02d52c`, fresh, original successful time retained in sidecar. Seven QVIX traces use this same snapshot/hash/calendar, including when QVIX is later stale. It is not an independent exchange calendar; common omissions unknown. Source observations begin2015, not2000.

## Implementation and verification boundaries

- New explicit `qvix-comparison-v2` active schema; only seven original index IDs plus `qvix_50etf`. Legacy active input rejected. Actual wrapper, cache clear, response-hook pre-coercion raw validation, request bounds and per-worker45s subprocess wall bound retained.
- Sorted whole-snapshot OHLC grouping uses complete finite decoded tuples. Exact duplicates collapse with notices; equal-close/different-OHLC is still conflict. Envelope anomalies/source-only dates retain values. Full-versus-selected accounting is independent. Unknown/stale comparator cannot yield clean quality.
- Structurally valid partial snapshots replace older clean snapshots and return nonzero. Fatal snapshots never replace prior usable whole snapshots; stale identity/time/quality retained. Initial fatal remains unavailable. Later corrections never merge dates. Validator runs before atomic latest publication; failed validation/replacement leaves prior pointer untouched.
- Renderer: seven independent right axes, daily close in percent, identical common QVIX trace; visible per-panel attempt/snapshot times/ranges/status/quality and separate missing/conflict explanation (null cannot normally hover). Existing legends/top margin, zoom/reset/buttons/slider retained. One bundled Plotly JS and JSON payload, no external data/script/styles.
- Independent verifier does not import chart or qvix_artifacts. It independently parses raw GBK fields, groups all occurrences, reconstructs exact CSV/sidecar/accounting, validates comparator identity/hash and original staleness, replays the pinned wrapper with cleared cache/network disabled, checks every referenced revision and actual seven index/QVIX trace pairs/statuses. It does not decode archived sentiment.
- Contract tests use real retained conflict arithmetic plus deterministic edge fixtures, temporary copies only: duplicates/order/zero/equal-close conflicts; full-response malformed date/nonfinite/schema failures; replay cache isolation/capture/non200/HTML; nullable CSV; raw/wrapper/CSV/sidecar/count/array tampering; atomicity; initial unavailable; clean→partial→fatal stale→correction without merge; sequential eight-feed failure/nonzero and wall-timeout captured evidence. Real acquisition's partial process exit is separately preserved above.
- No claim about exact provider horizon/annualization/close cutoff/publication schedule, safe trading lag, causality, point-in-time access, economic correctness, or unrestricted redistribution. optbbs attribution and unknown raw/derived/embedded-HTML redistribution permission remain visible; local noncommercial experiment only.

## Changed paths and preserved archives

Modified: `AGENTS.md`, `README.md`, `app/core.py`, `app/fetch.py`, `app/chart.py`, `app/verify.py`, `tests/test_contracts.py`, `data/latest.json`, `report.html`.
New: `docs/qvix-implementation-evidence.md` and the following exact run-relative paths under `data/runs/2026-11-15T21-47-32.121889+00-00-3b7821e3/`:

```text
manifest.json
qvix_50etf/response-0.body
qvix_50etf/transport.json
qvix_50etf/result.json
qvix_50etf/wrapper.csv
qvix_50etf/observations.csv
qvix_50etf/quality.json
sh000001/response-0.body
sh000001/transport.json
sh000001/result.json
sh000001/observations.csv
sh000016/response-0.body
sh000016/transport.json
sh000016/result.json
sh000016/observations.csv
sh000300/response-0.body
sh000300/transport.json
sh000300/result.json
sh000300/observations.csv
sz399006/response-0.body
sz399006/transport.json
sz399006/result.json
sz399006/observations.csv
sz399673/response-0.body
sz399673/transport.json
sz399673/result.json
sz399673/observations.csv
sh000680/response-0.body
sh000680/transport.json
sh000680/result.json
sh000680/observations.csv
sh000688/response-0.body
sh000688/transport.json
sh000688/result.json
sh000688/observations.csv
```

Removed runtime file: `app/sample.py`. Removed active sentiment invocation/empty-projection workaround/decoder/by-date merge; documentation-example CLI/import/trace/reverification; obsolete sentiment/sample tests. No compatibility shims.
Kept unchanged: all earlier `data/runs/2026-11-15T20-37-20.565654+00-00-3d8f6463/` artifacts/manifests, `data/documentation-example/` source/excerpt/CSV/LICENSE/provenance, `data/identities.json`, all old research/reviews and scripts. The archived browser fixture and related old scripts require a separate historical checkout at `c9943caf13` with its lock/data; they are not supported by the new active runtime. README documents this; archived evidence not rewritten. Goal ledger untouched.

## Final union result

Executed after the completed production/test/README/Lessons edits and this evidence file was created:

```sh
uv sync --frozen &&
uv run python -m compileall -q app &&
uv run ruff check . &&
uv run pytest -q &&
uv run python -m app.chart --input data --output report.html &&
uv run python -m app.verify --input data --report report.html &&
sha256sum report.html
```

Exit0. Frozen sync checked33 packages; compileall passed; Ruff `All checks passed!`;
pytest **29 passed**, two upstream mini-racer ctypes deprecation warnings,34.04s.
Chart rebuilt; independent verifier passed raw/wrapper/artifacts/accounting and all seven actual embedded index/QVIX trace pairs.
Final `report.html` SHA256:
`97885ead3795f8986a85c6a1b4e148c62b08cab2e8e104e7a80465ce9b346c1f`.
Real fetch remains **exit1/fresh partial**, not relabelled by these green offline checks.
Only this result-recording prose was appended after the union command. No production/test/data edits followed it.
Independent browser/whole-change review and orchestrator final acceptance remain outside this implementation slice.
