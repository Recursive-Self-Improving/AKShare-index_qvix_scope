# Independent matched-QVIX browser review — round 1

## FIX — F-B1: hover toolbar overlaps the QVIX legend

Reviewed actual root `report.html`, SHA-256 **`218d623efde86f040b9896348f78d2cb16950c55b9725c2c02a1c6eb135931a0`**, unchanged before every browser attempt and after the final run. Scope: browser portions of active AC13–16, approved matched-QVIX plan and existing `9cb3397` layout. No production/data/report/ledger changes, endpoint calls, delegates or commits.

### F-B1 — Medium / Fix: reserve separate space for the hover modebar and legend

The rightmost QVIX legend occupies the same area as the Plotly hover modebar on **all eight panels**. Hovering the graph reveals toolbar icons over the label; the center of the first panel's 50ETF legend cannot be clicked normally because `.modebar-group` intercepts pointer events. The original center-click harness timed out on that real interception. The legends are individually toggleable at exposed line-sample coordinates, but that does not satisfy the requested readable/no-overlap controls contract.

Concrete final-run viewport geometry, panel 1:

- Rightmost legend hit rectangle: x **1031.72–1204.25**, y **259.00–278.00**.
- Modebar groups: x **1053–1269**, y **243.58–268.97**.
- Vertical overlap approximately **9.97 px**; toolbar covers the upper half of much of the legend.
- Reproduce: navigate to 上证指数, bring graph into view, hover its upper-right legend/toolbar region, then try clicking the center of `50ETF QVIX 收盘（%）`.

Evidence: [gap-conflict.png](matched-qvix-browser-evidence-round1/gap-conflict.png), [gap-error.png](matched-qvix-browser-evidence-round1/gap-error.png), [zero-kcb.png](matched-qvix-browser-evidence-round1/zero-kcb.png), original intercepted-click log in `attempt1-output.txt`, and all-panel DOM intersections in `legend-modebar-overlap.json`. The overlap is visibly captured, not inferred from source. Move the legend or toolbar into non-overlapping space without removing existing controls; then recheck ordinary legend-text clicks and hover screenshots. No production fix was made by this review.

## Successful final harness execution, not unconditional acceptance

Final complete corrected harness: **exit 0**, `status=PASS`, `failures=[]`, **8 panels**, **3 genuine gap views**, labelled zero hover. Its geometry assertion covers legends, range selector, slider and axis titles, **not the modebar**. F-B1 is a separately observed review finding; automated PASS does not override it.

Execution:

```sh
~/.omp/bin/heavy-gate -n 1 -m 6G -- node /tmp/sentiment-browser-round1/matched-review.cjs
```

Exact shell wrappers, commands, corrections, hashes and resource evidence: [matched-qvix-browser-evidence-round1/](matched-qvix-browser-evidence-round1/), particularly `commands-errors.txt`, `harness-output.txt`, `harness-exit.txt`, `scratch.sha256`, `report.sha256` and `observations.json`.

**Launch accounting deviation:** three serial gated launches, not the requested one total. Each used exactly one Chrome/browser/context/reused page; no parallel browser workers. Attempt 1 exposed center-click interception and incomplete harness handling. Attempt 2 completed all panel/gap checks, then failed because SVG `.hoverlayer` does not support Playwright `innerText()`. Final run used `textContent()` and completed every stage. Both failed attempts are retained; no explanation-only pass or partial run is presented as the final success. All launches used `async:true, timeout:0`, no outer timeout, one-slot/6G isolation and `finally` browser close. Preflight ran before each launch; both gate slots were free afterward. Initial available memory 8869 MiB; final 8638 MiB; no swap.

Actual offline `file://` report, 1440×1100 viewport, Playwright-core/Google Chrome, blocked service workers, offline context and abort-on-external routing. Final run made exactly two report-file requests (light load and dark reload), **zero external requests, zero blocked dependencies, zero console messages and zero page errors**. DBus accessibility startup messages in shell output are not page-console errors.

## Eight actual panels and arrays

All exact ordered mappings passed; panels 1, 2 and 4 have **three** traces, the others two. Index is left `y`; every named QVIX is right `y2`, percent, `mode=lines`, `connectgaps=false`. Dual QVIX feeds use distinct orange solid/purple dashed styling. Every rendered `g.data` equals its embedded panel data.

| Panel | Index rows | QVIX feeds: trace rows / nulls / finite zero closes |
|---|---:|---|
| 上证指数 sh000001 | 6509 | 50index 939/186/33; 50etf 2861/14/0 |
| 上证50 sh000016 | 5552 | 50index 939/186/33; 50etf 2861/14/0 |
| 深证100 sz399330 | 5053 | 100etf 954/14/0 |
| 沪深300 sh000300 | 6030 | 300index 1674/192/42; 300etf 1674/15/0 |
| 创业板指 sz399006 | 3995 | cyb 1009/14/0 |
| 创业板50 sz399673 | 3017 | cyb 1009/14/0 |
| 科创综指 sh000680 | 1663 | kcb 839/14/1 |
| 科创50 sh000688 | 1663 | kcb 839/14/1 |

Independently read all eight index and seven QVIX CSVs and checked declared hashes; checked seven quality-file hashes and quality accounting against manifest snapshots; active feeds equal retained acquisition-manifest feeds. Constructed expected feed dates from quality nonblank/internal-blank/tail-blank/hole sets, selected by request window, and values from CSV closes with explicit nulls. Exact browser-array equality passes for every panel, so repeated feeds are identical across mapped panels. This is CSV/manifest/quality-to-browser verification, not an independent raw-normalization audit; the separate static/data reviewer owns that deeper replay.

Different coverage remains obvious: 50ETF begins 2015-02-09 versus 50股指 2023-01-03; 100ETF 2022-12-12; 300 feeds 2019-12-23; 创业板 2022-09-19; 科创板 2023-06-05. No invented early QVIX prices. 深证100 shows base 2002-12-31, release/first retained observation 2006-01-24 and 5053 rows, without presenting vendor first observation as inception.

## Real mouse interaction on every panel

All **19 traces** were independently hidden and restored using actual mouse clicks on exposed legend hit regions; sibling visibility stayed unchanged. No forced clicks, event dispatch, toolbar removal or scripted restyle substitute. Every panel passed actual main-plot mouse down/move/up drag zoom, its reset button, 1年/5年/全部 clicks, an actual rangeslider mouse drag and final reset. Other panels retained exact original ranges; range buttons were also checked for independence. Zoom proof uses real mouse events, not `Plotly.relayout`.

| Panel | Initial start (all end 2026-11-13) | Actual mouse zoom, date portion |
|---|---|---|
| 上证指数 | 2000-01-04 | 2005-05-10–2020-02-20 |
| 上证50 | 2004-01-02 | 2008-07-22–2021-02-19 |
| 深证100 | 2006-01-24 | 2010-03-17–2021-08-27 |
| 沪深300 | 2002-01-04 | 2006-12-17–2020-08-21 |
| 创业板指 | 2010-06-01 | 2013-09-09–2022-09-29 |
| 创业板50 | 2014-06-18 | 2016-12-06–2023-10-04 |
| 科创综指 | 2020-01-02 | 2021-05-15–2025-02-22 |
| 科创50 | 2020-01-02 | 2021-05-15–2025-02-22 |

Full timestamps and all intermediate reset/year/all/slider ranges are in `ranges.json`; eight initial and eight mouse-drag screenshots retained.

## Genuine nulls and labelled zero

Targeted view setup used explicit Plotly range changes only **after** all real-mouse control tests:

- **Invalid/error:** panel 1, 50股指, 2024-05-13–2024-06-07; 2024-05-20 invalid close is null, alongside absent May source dates. Orange main line visibly disconnects while blue index continues.
- **Conflict:** panel 1, 50ETF, 2026-10-26–2026-11-13; 2026-11-02 conflict is null with November 3–5 absent dates. Purple main line visibly disconnects; no candidate is selected.
- **Blank:** panel 4, 300股指, 2026-09-07–2026-09-22; 2026-09-14 internal blank is explicit null, within a broader actual error/null run. Orange line is absent through that run and resumes September 16. This is not an isolated blank between two adjacent finite closes; no synthetic isolation is claimed.

Each query selects exactly **one main** QVIX trace by its actual `_fullData[trace].uid` and excludes **all `.rangeslider-container` descendants**; a separate slider copy was found and excluded in each case. Main paths: 23/6/31 respectively; these are retained SVG path counts, not counts of only currently visible in-range segments. Category membership and null values checked against retained quality sets. Exact UIDs, paths, null dates and ranges: `main-trace-gaps.json`. Screenshots establish the actual visible discontinuity.

Real 科创板 2026-11-09 close **0** survives CSV→embedded→rendered data. Targeted November 6–13 view shows the orange line reaching zero and exact hover **`科创板 QVIX 收盘（%）(Nov 9, 2026, 0)`**. Reading notes explicitly say zero is retained without guaranteeing economic validity; not silently treated as a missing sentinel.

## Preserved layout and honest source disclosure

Entire page CSS equals `9cb3397` CSS byte-for-byte. Ordered navigation links were clicked; cards, reset, range controls and sliders remain. Visually inspected all eight initial light panels, header, quality-detail samples, three gap views, labelled zero, reading notes and first dark dual-feed panel/header; all eight dark screenshots retained. Dark body/card/plot ink values are verified. Apart from F-B1's hover modebar overlap, graph title/legend/range-selector/slider geometry is contained and non-overlapping; disclosure paragraphs wrap without horizontal clipping.

Each mapped feed's own visible paragraph passed name, attempt partial/time, snapshot partial/fresh/time, original identity hash, own source/close ranges, holes, conflicts, invalid fields, zero rows and comparator identity checks. All seven detail summaries visibly say **partial**, not clean success. Expanded cards show distinct own counts, shared source reference, quality hash and comparator provenance; no sibling's clean badge conceals defects. Reading notes disclose proxy mappings, unknown exact ETF contracts, invalid/blank/conflict gaps, null OHLC on conflicts, no repair/interpolation/extrapolation, finite zero, non-point-in-time retrospective timing, 科创综指 dividends, HTTP source and unconfirmed redistribution permission.

No certification of provider correctness, official-calendar completeness, contract methodology, timing or licensing. No fresh fatal/stale/unavailable state was fabricated into this real fresh-partial report. Final acceptance remains **FIX for F-B1**, despite successful complete harness execution and the other passing surface checks.
