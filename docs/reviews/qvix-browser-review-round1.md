# Independent QVIX browser REVIEW-LOOP round1

## Decision: PASS — actual offline browser surface and interactions

No material production Fix/Replan finding. Scope: AC10/browser portion of AC12 and approved quality-plan graph/visible-partial obligations. This is **not** clean-source-quality certification, raw-wrapper replay, whole-change review, final gates, or ledger acceptance.

Reviewed report SHA256: `97885ead3795f8986a85c6a1b4e148c62b08cab2e8e104e7a80465ce9b346c1f`.
Read README, implementation evidence, active AC9–12/D9–11, approved quality plan and plan-review residual obligations.

## Actual proof

Google Chrome156.0.8078.79 with playwright-core1.65.1,1440×1100, real `file://` report, browser context offline, network dependencies denied. Every launch ran through shared heavy-gate `-n 1 -m 6G`; sequential single-browser/context/reused-page runs; browsers closed in `finally`. Report requested only its own file URL; no external requests, blocked dependencies, console errors or page errors.

- Visually inspected all seven saved initial panel screenshots, report warning and actual 2024/2026 gap screenshots. Index labels, both trace legends, left/right titles, date footer, reset,1年/5年/全部 and rangeslider readable. Visible legend text does not overlap title/buttons/slider; DOM text/control bounds contained and collision-free in all seven. Dense status paragraphs wrap rather than clip.
- Each rendered `g.data` exactly matched its embedded panel data. Index plotted values matched the original current snapshot CSV with all nonnull rows retained:6509/5552/6030/3995/3017/1663/1663. Current manifest feeds equal active feeds; every current index CSV digest matched its declared snapshot hash.
- All seven identical QVIX arrays matched an independently constructed union of QVIX CSV dates and the snapshot-bound comparator CSV dates inside QVIX source bounds. CSV/quality/comparator hashes matched declarations. Each array has **2847 nonnull closes and14 explicit nulls**, not zero-filled gaps:13 missing source dates plus the2026-11-02 conflict. Independent right axis `50ETF QVIX 收盘（%）`, overlaying left axis; two line traces only; `connectgaps=false`. No old sentiment/example trace or obsolete failure/example warnings.
- Four source-only dates retain source values in every panel:2026-08-22,2026-09-12,2026-09-13,2026-11-01. Expected arrays are computed from retained artifacts; evidence-count assertions in scratch do not introduce production constants.
- Report and each panel visibly show attempt `partial` at2026-11-15T21:47:41.624102+00:00 and snapshot `partial / fresh` at2026-11-15T21:47:48.027025+00:00, requested2000–2026 window, actual2015-02-09–2026-11-13 range,2848 source dates,13 missing,1 conflict,4 source-only,8 envelope anomalies,0 exact duplicates and unordered source. Missing-source versus conflicting-candidate explanations remain visible without requiring null hover.
- Visible provenance distinguishes volatility from news sentiment and50ETF from the other six underlyings. optbbs/AKShare attribution, first observation versus inception, unknown horizon/annualization/close/publication/revision/reconstruction, non-point-in-time history, HTTP/TLS/hash limits, relative-calendar limits and unconfirmed raw/derived/embedded-HTML redistribution permission are explicit. No source-clean claim.

## Seven actual mouse/navigation checks

For **each panel**, real mouse down/move/up on the main drag surface narrowed its range; the other six ranges were unchanged. Reset restored the exact original range. Real clicks selected1年=`2025-11-13–2026-11-13`,5年=`2021-11-13–2026-11-13`, then全部 restored original. Real rangeslider drag narrowed the range; final reset restored all seven original ranges. Full timestamp precision and every intermediate range are in `observations.json`.

| Panel | Original range start; end2026-11-13 | Mouse-zoom range, date portion |
| --- | --- | --- |
| 上证指数 sh000001 |2000-01-04|2005-05-15–2020-02-21|
| 上证50 sh000016 |2004-01-02|2008-07-26–2021-02-20|
| 沪深300 sh000300 |2002-01-04|2006-12-21–2020-08-22|
| 创业板指 sz399006 |2010-06-01|2013-09-12–2022-09-30|
| 创业板50 sz399673 |2014-06-18|2016-12-08–2023-10-05|
| 科创综指 sh000680 |2015-02-09|2017-06-15–2023-12-03|
| 科创50 sh000688 |2015-02-09|2017-06-15–2023-12-03|

The last two common x-ranges begin with genuine QVIX history; their original index traces still begin2020-01-02. This is not invented earlier index history.

## Real gaps, not a synthetic replacement

Zoomed actual panel0 to2024-05-15–2024-06-07 and2026-10-26–2026-11-13 using Plotly range changes for targeted inspection. Screenshots show the orange main QVIX line disconnected across missing May sessions and the November conflict/missing cluster. The2026-11-01 source-only observation remains immediately before the latter gap.

Final gap probe identifies the rendered QVIX trace by `_fullData[1].uid` and excludes **all** `.rangeslider-container` descendants. Exactly one main QVIX trace, with six disconnected SVG paths, is selected in both views; the separate rangeslider copy is excluded. Null dates in each targeted range are recorded alongside exact SVG path coordinates in `main-trace-gaps.json`. No synthetic fixture was needed.

## Evidence and harness corrections

Directory: [qvix-browser-evidence-round1](qvix-browser-evidence-round1/).

- `00-report-status.png`; `panel-1-initial.png` through `panel-7-initial.png`; matching seven `*-drag.png` screenshots.
- `gap-2024-05-15.png`, `gap-2026-10-26.png`; final main-trace assertion `main-trace-gaps.json` **PASS**.
- `observations.json`: actual arrays/status/geometry/range proof; its top-level `FIX` records two subsequently corrected **harness selectors**, not production findings. All seven non-gap assertions passed. Do not interpret that label as a clean full-script pass.
- `harness-attempt1.json`: preserved initial selector/background-box false positives. Visible legend glyphs, not transparent legend-background padding, are the correct readability collision target. Overlay trace groups are not children of `.subplot.xy2`; select by actual trace UID and exclude rangeslider instead.
- `commands-errors.txt`: commands, resource preflight, versions, scratch script hashes, exact harness-error accounting and manifest/index hash observations. One read-only probe exited1 after incorrectly expecting a nonexistent `manifest_sha256` field; active/manifest feed equality and all seven declared CSV hashes had passed. No production defect inferred from that scratch mistake.

Scratch JavaScript stayed outside the repository; no new Python evidence, production/README/ledger/data edits, provider retry, commits or subdelegates. Whole-change/static review and full gates remain the orchestrator's separate work.
