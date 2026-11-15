# Independent final QVIX browser REVIEW-LOOP round2

## PASS — complete corrected harness, exit 0

No material browser-surface Fix/Replan findings. Scope: active AC10 and browser/disclosure portions of AC12, including final compact-v3 metadata corrections. Not a static/data-acquisition review, full-gate result, ledger acceptance, or clean-provider-quality certification.

Reviewed final `report.html` SHA256: `384c57b2e79c95b0ca66727e7867b4c1230b3e04a03c6b22be29fdc95ee26544`.
Read round1 browser review, corrective evidence, README and active ledger AC9–12. The active view is `qvix-comparison-v3`, `operation=format-migration`; active feeds equal the derived manifest feeds. Browser status remains the genuine original acquisition **fresh partial**, not a new fetch or migration-time observation.

## Execution and evidence

Exactly **one** heavy-gated Chrome launch, one context, one reused page, workers=1 equivalent serial execution. Shared resource preflight ran first: available8328 MiB, both slots free, no swap. Command:

```sh
~/.omp/bin/heavy-gate -n 1 -m 6G -- node /tmp/sentiment-browser-round1/qvix-review-round2.cjs
```

Finite bash used `async:true, timeout:0`; gate isolation succeeded. Real `file://report.html`, viewport1440×1100, offline context, service workers blocked, external network routes aborted. Only the report file request occurred; no external dependency, blocked request, console message or page error. Browser closed in `finally`. Final `observations.json` has `status=PASS`, `failures=[]`, seven completed panels and both gap assertions; `harness-exit.txt` is **0**. No separate-selector waiver or explanation-only pass.

Evidence: [qvix-browser-evidence-round2/](qvix-browser-evidence-round2/), containing report hash, exact commands/errors, resource before/after, complete harness output, scratch hash, `observations.json`, exact `ranges.json`, `main-trace-gaps.json`, seven initial/seven drag screenshots, report provenance screenshot and two actual gap screenshots. Automation remains outside the repository; no new Python archive script.

## All seven panels

- Visually inspected every initial panel screenshot, report provenance and both actual gap screenshots. Chinese index labels/codes, two legends, independent left/right titles, date footer, reset,1年/5年/全部 and rangeslider readable. Geometry assertions found no graph-label/control collisions or containment failures; status paragraphs wrap without clipping. The dense disclosure remains readable text, not inert metadata. Panel2 screenshot includes a transient standard Plotly zoom-tip overlay; no persistent layout defect.
- Each actual `g.data` equals its embedded panel data. Independently read current seven index CSVs; declared CSV hashes and exact date/value arrays match, retaining6509/5552/6030/3995/3017/1663/1663 observations.
- Independently construct expected QVIX arrays from actual QVIX CSV plus the compact snapshot-bound comparator CSV calendar within observed bounds. CSV/quality/comparator declared hashes match. Every panel has the identical **2847 nonnull closes +14 explicit nulls**:13 missing source dates and2026-11-02 conflict. Right axis is `50ETF QVIX 收盘（%）`, overlays left `y`, trace uses `y2`, lines and `connectgaps=false`. Index remains on the left. Exactly two traces; no old sentiment/documentation-example trace or obsolete warning.
- Independently compute source-only membership against that comparator:2026-08-22,2026-09-12,2026-09-13,2026-11-01; all four retain exact CSV values in every panel.
- Actual visible `.index-status` JSON matches each current index attempt status/time, snapshot status/time, fresh reuse flag, count and range. QVIX per-panel visible text shows attempt partial at `2026-11-15T21:47:41.624102+00:00`, snapshot partial/fresh at `2026-11-15T21:47:48.027025+00:00`, request2000-01-01–2026-11-15, source/selected2015-02-09–2026-11-13,2848 dates,13 missing,1 conflict,4 source-only,8 envelope rows,0 exact duplicates and unordered source. Missing means no source row; conflict means no candidate selected/all OHLC null. Both explanations visible without null hover.
- Provenance visibly identifies Sina, optbbs and pinned-wrapper API; volatility is not news sentiment;50ETF is not the other six underlyings. First observation is not inception. Unknown horizon/annualization/close/publication/revision/reconstruction, retrospective/non-point-in-time history, relative-calendar/common-omission limits, HTTP versus HTTPS/hash limits and unconfirmed redistribution permission remain explicit.

## Real mouse interaction on EACH panel

Every panel passed actual mouse down/move/up main-plot zoom: range narrowed and the other six remained exactly unchanged. Reset restored the exact original range. Real button clicks selected1年 and5年, then全部 restored the original. Actual rangeslider drag narrowed the range; final reset restored all seven ranges exactly. No scripted relayout substitutes for these seven interaction checks. Full timestamp precision and each intermediate range are in `ranges.json`.

| Index | Original start (end2026-11-13) | Mouse zoom dates |
| --- | --- | --- |
| 上证指数 sh000001 |2000-01-04|2005-05-15–2020-02-21|
| 上证50 sh000016 |2004-01-02|2008-07-26–2021-02-20|
| 沪深300 sh000300 |2002-01-04|2006-12-21–2020-08-22|
| 创业板指 sz399006 |2010-06-01|2013-09-12–2022-09-30|
| 创业板50 sz399673 |2014-06-18|2016-12-08–2023-10-05|
| 科创综指 sh000680 |2015-02-09|2017-06-15–2023-12-03|
| 科创50 sh000688 |2015-02-09|2017-06-15–2023-12-03|

The last two shared plot ranges begin with real QVIX data, not invented index history; their index CSVs begin2020-01-02.

## Actual disconnected gap views

After completing every mouse/navigation check, targeted inspection used Plotly range changes on panel0:2024-05-15–2024-06-07 and2026-10-26–2026-11-13. Both screenshots show orange QVIX disconnection while blue index history continues. November retains the source-only2026-11-01 value before conflict/missing dates.

The complete harness selects QVIX using actual `_fullData[1].uid` (`f14585`) and excludes **ALL** `.rangeslider-container` descendants. Each targeted view selects exactly one main QVIX trace with six disconnected SVG line paths and excludes its one slider copy. Relevant null dates: May22/23/24/27/29/30/31; November2/3/4/5. Exact SVG paths and ranges recorded. No synthetic fixture, old selector or weakened assertion.

## Boundaries

Only new round2 review/evidence paths written. No production/README/ledger/data/historical evidence edits, commits, provider retries or subdelegates. Static review and final full project gates remain separate. PASS certifies observed browser behavior and disclosures, **not** resolution of source conflicts/gaps or provider methodology/license unknowns.
