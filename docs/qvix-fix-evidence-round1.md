# QVIX corrective implementation evidence — round 1

Implementation evidence, not independent review or convergence. Addresses Q-R1–Q-R4 from `docs/reviews/qvix-implementation-review-round1.md`. No endpoint repeat, browser, subdelegate, ledger edit or commit in this corrective slice.

## Changed paths and contracts

- `app/core.py`: v3 active schema; compact quality/snapshot projection and ordinary path/hash acquisition references; full retained Sina comparator replay; selected holes are full in-observed-bounds holes filtered to the request, including windows with no retained source rows; explicit trace bounds preserve boundary nulls.
- `app/fetch.py`: whole-current state without cumulative revision bodies; previous immutable manifest reference; compact accounting only in result/state; full candidate tables only in the quality sidecar. New acquisitions bind the canonical immutable result file by path/hash. Publication refuses an unequal existing manifest.
- `app/verify.py`: mandatory origin and transport fields for every usable active index/QVIX snapshot, exact immutable origin membership and original metadata/times; raw/transport/wrapper/CSV/sidecar replay; independent full-calendar grouping/accounting; per-panel actual HTML disclosure parsing and comparison independent of inert JSON status. Missing/contradictory index and QVIX state/time/range/quality fails verification.
- `app/chart.py`: current-only status/provenance payload, full verified comparator calendar, requested/source intersection bounds, explicit visible snapshot status including unavailable, per-panel labelled disclosure elements.
- `tests/test_contracts.py`: immutable-origin metadata deletion and forged stale time; narrow-window fetch with a one-row comparator CSV but full raw replay; selected boundary and no-selected-source holes including actual embedded null arrays; visible index/QVIX deletion and contradiction under fresh/stale/unavailable; clean→partial→fatal stale→correction with current-only display and auditable previous-manifest/sidecar references.
- `README.md`, repository `AGENTS.md`: corrected active schema, migration, calendar, provenance, history and verification semantics.
- `data/derived/qvix-v3-round1/manifest.json`, `data/latest.json`, `report.html`: derived compact active view and rebuilt report only. No acquisition artifact is rewritten.

## Exact immutable-preserving migration

Original acquisition: `runs/2026-11-15T21-47-32.121889+00-00-3b7821e3/manifest.json`. A one-time `/tmp/qvix-migrate.py` read that manifest and retained raw artifacts, replayed the full comparator history and QVIX grouping, validated the derived view, wrote a **new** `data/derived/qvix-v3-round1/manifest.json`, then atomically replaced `data/latest.json`. It made no network call and created no acquisition run. The throwaway script is not a maintained compatibility CLI.

The view's `operation=format-migration`, `derived_at` and explicit prose identify the operation. Its run/attempted_at/finished_at and every snapshot's original attempted_at/successful_at remain acquisition times, not migration time. `previous` and each snapshot `origin` reference the original manifest and SHA256. Index projections remove only duplicated captures; QVIX also replaces full candidate accounting with a recomputed compact summary and declares `derivation={operation: quality-format-migration, source_schema: qvix-comparison-v2}`. Raw/transport/wrapper/observations/quality paths and hashes remain original. Verification checks original candidate evidence from the original immutable sidecar, with corrected compact calendar accounting independently recomputed from raw. No extra candidate sidecar is created by the migration.

Old v2 manifests retain their historical duplicated candidate tables as immutable evidence. New state has only attempt/snapshot/stale_reuse; new manifests link previous manifests instead of accumulating revision bodies. The report contains current display arrays/status/compact references only. The verifier validates current snapshots and the exact bound comparator, not every historical version; archived evidence remains reachable and unmodified. No sentiment decoder or date-fill compatibility path exists.

## Verification record

Commands (no real fetch):

```sh
PYTHONPATH=. .venv/bin/python /tmp/qvix-migrate.py
uv sync --frozen
uv run python -m compileall -q app
uv run ruff check .
uv run pytest -q
uv run python -m app.chart --input data --output report.html
uv run python -m app.verify --input data --report report.html
rm /tmp/qvix-migrate.py
```

Migration validation exited 0 and wrote the 66,715-byte derived manifest; throwaway script removed. The initial union run passed frozen sync/compileall/Ruff, then reported 41 passed / 4 failed. Those four deletion probes changed only snapshot while leaving a distinct fresh attempt copy, so they stopped at `fresh attempt identity` instead of the expected mandatory-provenance boundary. The fixture now binds both fresh copies before deleting metadata; it does not relax the expected provenance rejection. The final union runs after that fixture correction and the origin-path membership enforcement.

Final union command (the six `uv` commands above joined with `&&`) exited **0** after the last production/test change:

- Frozen sync: `Checked 33 packages`.
- Compileall: exit 0.
- Ruff: `All checks passed!`.
- Pytest: **45 passed, 2 warnings in 245.14s**. Both warnings are upstream mini-racer ctypes `_pack_` deprecations, not suppressed.
- Chart: seven panels, QVIX fresh partial with original `2026-11-15T21:47:48.027025+00:00` snapshot time; 2848 selected dates, 13 missing, one conflict, four source-only, eight envelope rows.
- Verify: seven index counts `6509/5552/6030/3995/3017/1663/1663`, each latest `2026-11-13`; `Offline verification passed: raw/wrapper/artifacts/accounting and seven actual embedded trace pairs`.

The final post-gate path→SHA256 comparison again reported **73 unchanged; changed=[]** and confirmed the throwaway script absent. Both latest and derived manifest: 66,715 bytes / SHA256 `c3f54a0fc5ec00620040aa8deb8f1f0454e73984a6d2797a26315e4bbeeb07dc`. Final report: 5,958,135 bytes / SHA256 `384c57b2e79c95b0ca66727e7867b4c1230b3e04a03c6b22be29fdc95ee26544`.

Consumer-visible regression proof includes a new offline eight-source fetch path whose selected comparator CSV contains only Jan 3 while full raw replay includes Jan 2: QVIX stays success with no invented full-history extras. Requested Jan 3–4 and Jan 3-only windows with source Jan 2/Jan 4 preserve the known Jan 3 gap, including an actual null-only trace when no QVIX source row is selected. Fresh/stale/unavailable reports reject removed or contradicted per-panel disclosures without changing their JSON payload. Correction snapshots display only the correction's dates; previous conflict candidates remain accessible through the archived manifest and original sidecar, not copied into active/report candidate tables.

A passing offline check does not establish browser interaction correctness, authentic historical availability, clean source quality or redistribution permission.

## Remaining limits

The real source remains fresh **partial**: one unresolved conflicting date, 13 relative gaps, four source-only dates, eight envelope-anomaly rows. No conflict winner, fill, remap, official/external calendar assumption or source repair. Provider methodology/publication/reconstruction/redistribution and original HTTP authentication limits remain unchanged. Independent whole-change and final browser reviews remain the orchestrator's acceptance gates; this document makes no self-clean claim.

## Pre-edit immutable hashes

Before any production edit, all 73 pre-existing files below `data/` other than the mutable `latest.json` were SHA256-inventoried in `/tmp/qvix-before.json`. Comparing every inventoried path after migration reported `PREEXISTING_IMMUTABLE_FILES 73 CHANGED []`. SHA256 of the sorted compact JSON path→hash inventory: `4846aa155b73679259832be23064a314042fe22aa86db8344f5e02a194266106`.

Original acquisition run prefix below: `data/runs/2026-11-15T21-47-32.121889+00-00-3b7821e3/`.

| Original immutable artifact | SHA256 before and after |
| --- | --- |
| prior `20-37-20.565654+00-00-3d8f6463/manifest.json` | `333e7fa27f98d8b71bb8dbb928807328914f5794ab8622480fb79f79d85f8b63` |
| `manifest.json` | `c99274d7755b8b3a0e3ca9dc55e312fd771bcb7eb8333eabc994e0cfebb55d66` |
| `qvix_50etf/response-0.body` | `2e0f2edc8a6bd80cc4ec71fec22d01d933cc29af7de7b2337c406b0fea436071` |
| `qvix_50etf/transport.json` | `42a112f7cad45b5be59657ae577c3f5fd3384c1f7393824aaa656fed8be8a263` |
| `qvix_50etf/wrapper.csv` | `31261ded64485ebbdf3620a13f8d718c25aec472d1e57536a6105480b3b6f63f` |
| `qvix_50etf/observations.csv` | `0ad3d7206585721f30fcd5905fb2074ff3f613577ea3c5897f7b610666ae9849` |
| `qvix_50etf/quality.json` | `9d4ac0b2aa5e46516011438fc1055b4fefbcad50955ed245702c8b47ec7e3a85` |
| `sh000001/response-0.body` | `8652957f0248b9637a5ed6715028ceea8af2eccf57e9fbd6e78972da41e25eb8` |
| `sh000001/transport.json` | `bcdeefb37de1fc608a2ec6720e1bef7df7dba17ec6e7019dc9bffe65499fe7b6` |
| `sh000001/observations.csv` | `e72c43dbd2b3bf97736d8be6b4d09ce4ff2ebac6432a507f0d70ff861b02d52c` |

Derived view SHA256: `c3f54a0fc5ec00620040aa8deb8f1f0454e73984a6d2797a26315e4bbeeb07dc`; 66,715 bytes. Original top-level attempt/finish times remain `2026-11-15T21:47:32.121955+00:00` / `2026-11-15T21:47:48.384835+00:00`; QVIX successful snapshot time remains `2026-11-15T21:47:48.027025+00:00`. Size is an observation, not the regression contract: tests assert current-only whole-snapshot display and preserved historical sidecar accessibility.
