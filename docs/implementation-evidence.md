# Implementation evidence

Implementation slice only; no goal-ledger edits or commits. No independent acceptance/self-certification claim. Browser/UI interaction review remains with the independent reviewer.

## Reproducible environment and commands

Python 3.14.4 in this environment; `pyproject.toml` supports 3.14 and `uv.lock` freezes all resolved packages. Direct pins: AKShare 1.20.53, requests 2.34.2, Plotly 7.1.0, Ruff 0.14.5, pytest 9.0.2. Decoder distribution is mini-racer 0.14.1; pandas 3.1.1.

Observed initial commands:

```sh
uv lock && uv sync --frozen
uv run python -m compileall -q app && uv run ruff check . && uv run pytest -q
uv run python -m app.fetch --start 2000-01-01 --end 2026-11-15
uv run python -m app.sample
uv run python -m app.chart --input data --output report.html
uv run python -m app.verify --input data --report report.html
```

- Environment resolution/install: exit0, 35 resolved packages, 33 installed.
- Initial compileall/Ruff/pytest: exit0, `All checks passed!`, 14 tests passed in 0.48s. Two upstream mini-racer ctypes layout deprecation warnings for eventual Python3.19, not suppressed.
- Real acquisition: exactly one eight-source run, **exit1**, 22.11s including offline validation/promotion. Seven real index successes and one real sentiment transport failure. Not a passing acquisition gate.
- Documentation import: first attempt rejected an incorrectly bounded empty excerpt before writing any sample data; corrected extraction then exit0, `MIT source retained; ten documentation-only rows transcribed`. This was not a provider retry or genuine sentiment success.
- Initial chart and offline verify: exit0; seven panel arrays agreed with real normalized CSV and raw-body replay; all relative index gaps zero. This is data verification, not visual proof.

## Real run

Run: `data/runs/2026-11-15T20-37-20.565654+00-00-3d8f6463/manifest.json`; `data/latest.json` points to the same immutable run content. Requested window 2000-01-01 through 2026-11-15. Raw capture before application decoding retained all fetched source history, not just the filtered CSV window.

| Canonical index | Symbol | Rows in window | First observation | Last observation | Pre-release rows | Relative gaps |
|---|---|---:|---|---|---:|---:|
| 上证指数 | sh000001 | 6509 | 2000-01-04 | 2026-11-13 | 0 | 0 |
| 上证50 | sh000016 | 5552 | 2004-01-02 | 2026-11-13 | 0 | 0 |
| 沪深300 | sh000300 | 6030 | 2002-01-04 | 2026-11-13 | 782 | 0 |
| 创业板指 | sz399006 | 3995 | 2010-06-01 | 2026-11-13 | 0 | 0 |
| 创业板50 | sz399673 | 3017 | 2014-06-18 | 2026-11-13 | 0 | 0 |
| 科创综指 | sh000680 | 1663 | 2020-01-02 | 2026-11-13 | 1224 | 0 |
| 科创50 | sh000688 | 1663 | 2020-01-02 | 2026-11-13 | 133 | 0 |

The comparator is observed 上证指数 from this run, **non-independent**, not an official exchange calendar; common omissions remain unknown. Counts do not establish perfect history or contemporaneous availability. Per-index CSV includes numeric `pre_release`/`pre_base` flags. Identity/base/release metadata and authoritative links come from `docs/research/index-identities.md`; metadata persisted in each success and `data/identities.json`. 沪深300 observations before its official base are not described as contemporaneous or as a proven reconstruction method. 科创综指 includes dividends, distinct from 科创50 price index. Earlier unavailable intervals are not guessed pre-inception dates.

## Actual sentiment invocation and external blocker

`index_news_sentiment_scope()` actually invoked in pinned AKShare1.20.53 at `2026-11-15T20:37:32.340823+00:00`. Request: `https://www.chinascope.com/inews/senti/index?period=YEAR`. Captured HTTP301 to `https://www.chinascope.com.cn`, then authenticated TLS failed:

```text
SSLError: HTTPSConnectionPool(host='www.chinascope.com.cn', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1081)')))
```

The requests exception's phrase “Max retries exceeded” is urllib3 wording, not an application retry loop. The application makes one invocation per source, no retries, normal certificate validation. Connect/read5/12s and independent per-worker wall deadline45s. Preserved redirect body SHA256 `9e17cb15dd75bbbd5dbb984eda674863c3b10ab72613cf8a39a00c3e11a8492a`; no fictitious final TLS response body. Exact timestamps, response headers/encoding/URLs and error in `sentiment/transport.json` and `result.json`, also the run manifest. Range/count are unknown, no last successful provider snapshot; not zero observations and not proof no history exists.

Full genuine sentiment refresh/backfill and seven genuine full-history overlays remain externally blocked pending restored authenticated provider/API access or authentic authorized retained history. Existing same-provider recovery evidence in `docs/research/sentiment-recovery.md` remains applicable. No substitute metric, disabled TLS or invented observations.

## Licensed documentation-only sample

Actual immutable GitHub source and LICENSE both HTTP200, retrieved `2026-11-15T20:38:45.592784+00:00`; commit `8fc02741a1807a2fa111d5baf119b19c5718ae79`. MIT license permission language checked before sample redistribution; full original copyright and permission retained at `data/documentation-example/LICENSE`. Full source, excerpt, retrieval metadata and hashes retained there:

- source: `3e8d086441ec1d252d556050d5b5a1112bc2199112d90daddf267d3228c89785`
- license: `90540e7266c3e3297439796078aa745fa6754561c1b6d021be6f680e690b39b3`
- excerpt: `beeeb33d160a98d02756e4bc16c29b0254a12383999036a8f3bf3ce1c0b6ef36`
- CSV: `b86689540e50295e2ded0c7e76789c95a8e95647d5962c93cf84643884ea658e`

Exactly ten explicitly printed dated rows, five2023-10-31–2023-11-06 and five2024-10-25–2024-10-31. Ellipsis/other231 rows not imported. Separate `documentation-example.csv`, never a provider snapshot or successful timestamp. Original sample capture/publication/revision times unknown. `market_close` stays separate from independently acquired 沪深300 closes. All seven panels include isolated sample-axis markers, with English/Chinese documentation-only classification and prominent partial/live-missing warning. No line across the missing year.

## Verification scope and resource policy

`app.verify` uses no network: every captured transport body hash; all successful raw hashes, decoder replay and CSV byte comparisons; latest/immutable manifest identity; source/license/excerpt/transcription hashes; actual HTML JSON arrays compared independently with CSV, known comparator null gaps, axes and sample classification. It does not call the chart builder to generate its expected arrays. Deterministic tests cover invalid/HTML/duplicates/nonfinite rejection preserving success, interrupted atomic replacement, stale/wrong identities, immutable revisions, sparse gaps and null versus zero.

No browser, Electron, emulator or command expected above2GiB launched. Therefore no heavy-gate launch/status/free command was required or invoked; no uncapped heavy launch or bypass. Exact browser/heavy gate commands/results: **none**. Browser visual/offline zoom/reset/navigation verification is explicitly unperformed by this implementation slice, per handoff instruction; the independent reviewer must run it under the shared heavy-gate policy.

`data/` total at initial replay: 1,704,320 bytes, including real bodies, CSV, manifests and immutable MIT documentation source. No downloaded environment/cache is included in delivery; `.venv`, Python/test/Ruff caches are ignored. `report.html` is regenerated with embedded Plotly once and embedded data. No scheduling or ingestion framework.

## Final reachable gate run

After the last code/test changes, ran exactly:

```sh
uv sync --frozen && uv run python -m compileall -q app && uv run ruff check . && uv run pytest -q && uv run python -m app.chart --input data --output report.html && uv run python -m app.verify --input data --report report.html
```

Observed exit0, 9.71s. Frozen sync checked33 packages; compileall exit0; Ruff `All checks passed!`; pytest **19 passed, 2 upstream deprecation warnings in0.49s**. Rebuilt actual report then offline replay again reported all seven exact counts/ranges above and zero relative index gaps: `Offline verification: raw bodies/hashes replay, immutable sources, CSV and seven embedded arrays agree`. No second provider acquisition was made. This does not turn the earlier fetch exit1 into success and does not certify browser interaction.
