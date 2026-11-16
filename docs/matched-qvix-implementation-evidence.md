# Matched-QVIX implementation evidence

Implementation slice against requested baseline `a18afebada`; no ledger edit, commit, push, delegation, scheduler or browser launch. Binding contract: `docs/research/matched-qvix-plan.md`, including F1–F3, and `docs/reviews/matched-qvix-plan-review-round2.md`. Implementation acceptance below is not independent review or economic/source-quality certification.

## Preservation and cutover

Before the first production edit, inventoried **213** existing files under `data/runs`, `data/derived`, `data/documentation-example`, `docs/research` and `docs/reviews`:

- Inventory: `docs/matched-qvix-pre-edit.sha256`.
- SHA-256: `43b51cde41546bf404599266064b5e8a250715ce8f9f55878f9f79c0f3b720c7`.
- Final `sha256sum -c docs/matched-qvix-pre-edit.sha256`: exit **0**, **213** `OK` lines. Output retained during implementation at `/tmp/matched-qvix-immutable-check.log`.
- No old acquisition, derived sidecar/manifest, research or review was changed. The goal ledger was not edited.

Explicit offline v4 migration created `data/derived/matched-qvix-v4/`. Its manifest declares `operation=format-migration`, retains original acquisition run/times, and records a separate `derived_at`. Seven verified original index snapshots retain their origin references. Only original 50ETF has a rederived v4 snapshot: new quality/CSV/result and a shared evidence reference, original raw/transport/wrapper, original `successful_at=2026-11-15T21:47:48.027025+00:00`. Original sidecars remain unchanged. Other new feeds have no fabricated prior. Migration was independently validated before promotion; the deterministic migration regression also passes. Active runtime rejects v3; no implicit old single-feed decoder path remains.

## One actual bounded production acquisition

Command, executed once:

```sh
uv run python -m app.fetch --start 2000-01-01 --end 2026-11-16
```

Observed exit **1**, intentionally honest source partial. Console output:

```text
sh000001 success 6509
sh000016 success 5552
sz399330 success 5053
sh000300 success 6030
sz399006 success 3995
sz399673 success 3017
sh000680 success 1663
sh000688 success 1663
qvix_50index partial 939
qvix_50etf partial 2861
qvix_100etf partial 954
qvix_300index partial 1674
qvix_300etf partial 1674
qvix_cyb partial 1009
qvix_kcb partial 839
FETCH_EXIT=1
```

Production run: `data/runs/2026-11-16T01-33-45.220298+00-00-55dc38c0/`.
Manifest attempt/finish: `2026-11-16T01:33:45.220358+00:00` / `2026-11-16T01:34:09.167519+00:00`. Entire shell command observed **26.49 seconds**, including independent validation/promotion. Manifest and active pointer both SHA-256 `9543f1a4a656edcdda397c6f845e97507b889d29ab76158fd87c891ad67a1bbd`.

Eight sequential index subprocesses, then one QVIX group subprocess; each subprocess has a 45-second wall deadline, finite 5/12-second connect/read timeout, no retries or endpoint substitutions. Actual versions: AKShare 1.20.53, pandas 3.1.1, requests 2.34.2, mini-racer 0.14.1. Scratch research was not counted as production.

### Index rows and selected genuine coverage

All end at **2026-11-13**, requested lower bound 2000-01-01; no early history fabricated.

| Index | Rows | First selected observation | Pre-release rows |
|---|---:|---|---:|
| sh000001 | 6509 | 2000-01-04 | 0 |
| sh000016 | 5552 | 2004-01-02 | 0 |
| sz399330 | 5053 | 2006-01-24 | 0 |
| sh000300 | 6030 | 2002-01-04 | 782 |
| sz399006 | 3995 | 2010-06-01 | 0 |
| sz399673 | 3017 | 2014-06-18 | 0 |
| sh000680 | 1663 | 2020-01-02 | 1224 |
| sh000688 | 1663 | 2020-01-02 | 133 |

Each CSV preserves independent `pre_release` and `pre_base` flags. 399330 identity uses the retained compiler factsheet excerpt: base **2002-12-31**, release **2006-01-24**, not 399004 and not a family anniversary date. Its first observation is not inferred inception. Original full raw index history, rather than selected CSV, supplies comparator calendars.

### Shared QVIX response and actual member times

All seven **actual pinned wrapper calls were invoked**, using one real `__get_optbbs_daily` cache load and one captured HTTP200 response. One group-level body and transport, not seven copies:

- URL: `http://1.optbbs.com/d/csv/d/k.csv`.
- Acquired: `2026-11-16T01:34:04.446448+00:00`.
- Body: **928727 bytes**, SHA-256 `2e0f2edc8a6bd80cc4ec71fec22d01d933cc29af7de7b2337c406b0fea436071`.
- HTTP-decompressed `Response.content`, not wire bytes; GBK parser independent of HTTP header encoding.
- Body byte equality with older research does not authenticate HTTP or independently resolve source errors.
- `qvix-group/group.json` binds body/transport/config/hash/group identity and acquisition time. Each `invocation.json` and atomically published `result.json` records actual invoked status, callable, columns and original times.

Times below are UTC on 2026-11-16; exact full ISO values are retained in each result.

| Feed | Attempt | Validated snapshot | Finished |
|---|---|---|---|
| 50index | 01:33:56.900872 | 01:34:04.773011 | 01:34:04.774235 |
| 50etf | 01:34:04.776925 | 01:34:05.022409 | 01:34:05.024589 |
| 100etf | 01:34:05.030321 | 01:34:05.258808 | 01:34:05.260024 |
| 300index | 01:34:05.264802 | 01:34:05.455175 | 01:34:05.457026 |
| 300etf | 01:34:05.461133 | 01:34:05.665042 | 01:34:05.666456 |
| cyb | 01:34:05.675153 | 01:34:05.858962 | 01:34:05.860046 |
| kcb | 01:34:05.863046 | 01:34:06.002817 | 01:34:06.003917 |

Global encoding/shape/date validation precedes accepting members. Member files are fsynced before atomic completion; directory entries and pointer replacements are also fsynced. A shared loader exception stops subsequent calls; a local wrapper failure before loading does not imply a shared failure. Parent timeout/crash recovery independently validates completed member bindings/artifacts, preserves those fresh and fails unfinished members with their own prior only.

### Full-response quality

Common body: **2849 raw rows**, **2848 distinct common dates**, **2015-02-09–2026-11-13**. Every feed is fresh **partial**, not stale; no fatal acquisition occurred. All full nonblank-source and usable-close ranges end 2026-11-13 in this response. Earliest source/close observations:

| Feed | First source/close | Nonblank dates | Finite unambiguous close dates | Trace rows | Nulls |
|---|---|---:|---:|---:|---:|
| 50index | 2023-01-03 | 926 | 753 | 939 | 186 |
| 50etf | 2015-02-09 | 2848 | 2847 | 2861 | 14 |
| 100etf | 2022-12-12 | 941 | 940 | 954 | 14 |
| 300index | 2019-12-23 | 1660 | 1482 | 1674 | 192 |
| 300etf | 2019-12-23 | 1661 | 1659 | 1674 | 15 |
| cyb | 2022-09-19 | 996 | 995 | 1009 | 14 |
| kcb | 2023-06-05 | 826 | 825 | 839 | 14 |

Trace null counts are trace rows minus finite unambiguous close dates. Source-only invalid closes can make trace null count exceed comparator-hole count. Finite close beside invalid non-close fields is retained with partial quality; finite-complete OHLC is not the same count as usable close.

| Feed | Conflicts | Invalid fields | Zero rows / zero-close rows | Relative holes | Source-only dates | Envelope rows |
|---|---:|---:|---|---:|---:|---:|
| 50index | 0 | 787 | 34 / 33 | 182 | 4 | 13 |
| 50etf | 1 | 0 | 0 / 0 | 14 | 4 | 8 |
| 100etf | 1 | 8 | 0 / 0 | 14 | 4 | 4 |
| 300index | 0 | 819 | 45 / 42 | 188 | 4 | 24 |
| 300etf | 1 | 9 | 0 / 0 | 15 | 4 | 13 |
| cyb | 1 | 0 | 0 / 0 | 14 | 4 | 2 |
| kcb | 1 | 6 | 1 / 1 | 14 | 4 | 6 |

All have 13 absent comparator dates. Additional disjoint hole categories: 50index 169 invalid-close; 50etf/100etf/cyb/kcb one conflict each; 300index one blank and 174 invalid-close; 300etf one conflict and one invalid-close. No missing-close comparator holes. Error-close dates outside the comparator remain source-only nulls, not dropped. Counts describe retained sources, not official-calendar completeness or economic validity. Quality labels such as invalid, zero, source-only and envelope may overlap.

## Regression and final gates

Final command sequence (one shell chain, exit **0**):

```sh
uv sync --frozen
uv run python -m compileall -q app
uv run ruff check .
uv run pytest -q
uv run python -m app.chart --input data --output report.html
uv run python -m app.verify --input data --report report.html
```

Observed output:

```text
Checked 33 packages in 0.43ms
All checks passed!
.............................................................            [100%]
61 passed, 2 warnings in 60.23s (0:01:00)
Wrote report.html: eight panels; seven independently disclosed QVIX feeds
sh000001 6509 ['2000-01-04', '2026-11-13'] success
sh000016 5552 ['2004-01-02', '2026-11-13'] success
sz399330 5053 ['2006-01-24', '2026-11-13'] success
sh000300 6030 ['2002-01-04', '2026-11-13'] success
sz399006 3995 ['2010-06-01', '2026-11-13'] success
sz399673 3017 ['2014-06-18', '2026-11-13'] success
sh000680 1663 ['2020-01-02', '2026-11-13'] success
sh000688 1663 ['2020-01-02', '2026-11-13'] success
Offline verification passed: eight panels, seven raw/wrapper/artifact/quality replays
```

Compileall was silent and exited zero. Two warnings are upstream mini-racer `DeprecationWarning`s at `_dll.py:42` (`_RawValue`) and `_objects.py:195` (`_ArrayBufferByte`): implicit MSVC layout from `_pack_`, deprecated toward Python 3.19. Final shell wall time **64.85s**. Exact full gate output was retained at `/tmp/matched-qvix-gates.log`; fetch output at `/tmp/matched-qvix-production-fetch.log`.

Earlier development checks exposed two lint issues (ambiguous invalid-close set name and unused import), then eight recovery fixture failures caused by an incorrect group-directory root. These were fixed before the passing final gates; deterministic pre-integration run was 42 passed, 10 deselected. No provider retry was used to make tests green.

Regressions cover the exact F2 oracle with/without comparator; fresh blank/error/conflict no-close with/without prior; real durable no-close snapshots through chart/verification; source-empty windows and full-raw calendar accounting; overlapping quality/disjoint hole categories; blank collision ordinals, internal/tail/source-only nulls; finite zero; invalid-token identity with finite close; equal-close/full-tuple conflicts and missing-versus-invalid; numeric nonfinite/date errors outside window; per-wrapper positional/cache isolation and substitution; shared-load once/not-invoked outcomes; local wrapper and nonfinite isolation; termination after completed sibling; incomplete/atomic completion failures; cross-feed/body/time/column/origin substitutions; per-member artifact hashes; atomic pointer failure; sequential worker deadlines retaining captured bytes; native v4 source-window fetch; explicit v4 migration; mandatory origin/time/transport and fresh/stale/unavailable visible per-feed/index removal/contradiction/hidden-paragraph rejection.

`verify` independently parses raw fields/groups/date sets and reconstructs expected CSV/quality/actual embedded arrays and actual labelled visible disclosure text. It does not call the production normalizer or renderer as its oracle. Each panel has one left index and one/two named distinct right QVIX traces, with `connectgaps=false`; shared feeds retain identical arrays. Existing card/light-dark/navigation/controls remain; legend row is separated vertically from the range buttons. Static HTML/data proof is not visual or interaction proof.

## Delivered identity and remaining acceptance

- `report.html`: **6066722 bytes**.
- Final report SHA-256: **`218d623efde86f040b9896348f78d2cb16950c55b9725c2c02a1c6eb135931a0`**.
- Latest manifest: **148877 bytes**, compact counters/references, no candidate payload/history accumulation. Full candidate evidence exists once per member sidecar and shared body once per acquisition group.
- No browser, Electron, emulator or expected >2-GiB command was required or launched; no heavy-gate reservation was taken. No browser verification is claimed. Independent whole-change/data and gated eight-panel browser review remain the orchestrator's acceptance stage, not implementation blockers.
- Source partial remains material: malformed/spreadsheet cells, conflicts, anomalous envelopes and relative gaps/extras unresolved. No source correction, exact option-contract proof, tenor/annualization/publication/revision/reconstruction timing, HTTP authenticity or redistribution permission was fabricated.

## Complete changed-path specification

Existing files changed:

```text
AGENTS.md
README.md
app/core.py
app/fetch.py
app/chart.py
app/verify.py
app/identities.py
tests/test_contracts.py
data/latest.json
data/identities.json
report.html
```

New evidence:

```text
docs/matched-qvix-pre-edit.sha256
docs/matched-qvix-implementation-evidence.md
```

New immutable derived artifacts (five files):

```text
data/derived/matched-qvix-v4/group.json
data/derived/matched-qvix-v4/manifest.json
data/derived/matched-qvix-v4/qvix_50etf/observations.csv
data/derived/matched-qvix-v4/qvix_50etf/quality.json
data/derived/matched-qvix-v4/qvix_50etf/result.json
```

New immutable production artifacts are exactly the following finite Cartesian expansion, **72 files**. Prefix `R = data/runs/2026-11-16T01-33-45.220298+00-00-55dc38c0/`:

1. `R/manifest.json`.
2. For each of `sh000001`, `sh000016`, `sz399330`, `sh000300`, `sz399006`, `sz399673`, `sh000680`, `sh000688`: `R/<index>/observations.csv`, `response-0.body`, `result.json`, `transport.json` (32 files).
3. `R/qvix-group/config.json`, `group.json`, `response-0.body`, `transport.json` (four files).
4. For each of `qvix_50index`, `qvix_50etf`, `qvix_100etf`, `qvix_300index`, `qvix_300etf`, `qvix_cyb`, `qvix_kcb`: `R/qvix-group/<feed>/invocation.json`, `observations.csv`, `quality.json`, `result.json`, `wrapper.csv` (35 files).

No other production/evidence path was written by this slice. Cache/bytecode files produced by standard gates are not deliverable changes.
