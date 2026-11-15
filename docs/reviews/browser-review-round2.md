# Independent browser review — round 2

**Verdict: PASS for original attainable browser/data-artifact scope and B1.** B1 is resolved on all seven final panels. No remaining browser Fix finding. Genuine live/full-history sentiment remains externally blocked, independently of this UI PASS; this is not whole-goal acceptance or approval of R1/R2 acquisition implementation.

Reviewed prior [round1 review](browser-review-round1.md), [correction evidence](../fix-evidence-round1.md), README, goal ledger and actual chart layout. No production, README, ledger or acquisition edits; no commits; no live-provider failure rerun.

Final actual `report.html` SHA256: `9545c8e93a44a83489b2db018ee071cacf7957019f9033d8b20124be294698c0`.

## B1 — PASS on every actual surface

At desktop viewport 1440×1100, independently inspected all seven complete panel screenshots. Each shows its blue index-line swatch/local Chinese index label and orange open-diamond swatch with the complete **文档示例 documentation example, not live/full history** label. Both labels are readable, unclipped, and separate from each other, chart title, plot, navigation buttons, slider and date footer. The global warning is not needed to identify samples when scrolled down.

| Panel | Actual surface | Drag-zoom surface |
|---|---|---|
| 上证指数 sh000001 | [initial](browser-evidence-round2/panel-1-initial.png) | [drag](browser-evidence-round2/panel-1-drag.png) |
| 上证50 sh000016 | [initial](browser-evidence-round2/panel-2-initial.png) | [drag](browser-evidence-round2/panel-2-drag.png) |
| 沪深300 sh000300 | [initial](browser-evidence-round2/panel-3-initial.png) | [drag](browser-evidence-round2/panel-3-drag.png) |
| 创业板指 sz399006 | [initial](browser-evidence-round2/panel-4-initial.png) | [drag](browser-evidence-round2/panel-4-drag.png) |
| 创业板50 sz399673 | [initial](browser-evidence-round2/panel-5-initial.png) | [drag](browser-evidence-round2/panel-5-drag.png) |
| 科创综指 sh000680 | [initial](browser-evidence-round2/panel-6-initial.png) | [drag](browser-evidence-round2/panel-6-drag.png) |
| 科创50 sh000688 | [initial](browser-evidence-round2/panel-7-initial.png) | [drag](browser-evidence-round2/panel-7-drag.png) |

[Raw observations](browser-evidence-round2/observations.json) retain legend text/obstacle rectangles for every panel: two 12px labels, both within the graph; no text overlap with title, selector, plot or slider. First panel: title bottom543.59px, index-label top550.81px, documentation-label top569.81px/bottom583.81px, selector top611.59px, plot top639.59px. Visible glyphs/swatch locations and screenshots, not only layout configuration, establish readability.

## Warning, identity, dates and axes — PASS

[Actual top warning](browser-evidence-round2/01-warning.png) retains `transport_failure`, attempt time `2026-11-15T20:37:32.340823+00:00`, current provider unavailable, genuine coverage unknown (not zero), no successful snapshot, only ten historical documentation points, not live/full history, missing year not connected, and remaining231 rows not recovered. Page title explicitly says partial comparison, not complete real-time dual series.

Ran `.venv/bin/python -m app.verify --input data --report report.html`, exit0: [output](browser-evidence-round2/offline-verify.txt). Raw bodies/hashes replay, immutable documentation sources, normalized CSV and seven embedded arrays agree. Index counts6509/5552/6030/3995/3017/1663/1663; all actual index relative-gap counts0. This is not proof against common omissions in the non-independent calendar.

Browser independently compares every plotted x/y/mode/yaxis array with embedded JSON: all equal. Every panel has exactly two traces: index line and ten documentation-only points; no genuine-provider sentiment overlay. All ten main-subplot marker elements exist per panel; marker-only mode creates no connecting documentation line. Full-history marker clusters can overlap adjacent daily symbols without omitting rows or inventing intervening data.

All Chinese chart names/codes, left index and right sentiment titles are visible. Each right axis overlays `y` on side `right`, independently scaled. Full index ranges differ by panel (e.g. sh000001 `[729.2457777777777,6374.310222222222]`, sh000688 `[556.1073888888889,2294.799611111111]`), while sample sentiment spans `[0.9843222184757011,1.020552781524299]`. Matching right ranges reflect identical sample data, not shared index scaling. Exact titles/scales retained in JSON.

## Actual mouse interactions on EACH final panel — PASS

No Plotly API was used to manipulate the real report. Each panel received mouse-down/move/up rectangular drag zoom, actual reset-button click, actual 1年/5年/全部 clicks, actual slider mouse drag, then reset again. Each rectangle narrowed the date range and left every other panel unchanged. Both resets and 全部 exactly restored original date strings. Every 1年 result was `2025-11-13 → 2026-11-13`; every5年 result `2021-11-13 → 2026-11-13`.

| Panel | Initial / both resets / 全部 | Actual rectangle drag | Slider start (end2026-11-13) |
|---|---|---|---|
| sh000001 | 2000-01-04 → 2026-11-13 | 2005-05-15 17:39:02.0965 → 2020-02-21 10:03:47.6206 | 2010-10-03 15:10:28.9517 |
| sh000016 | 2004-01-02 → 2026-11-13 | 2008-07-26 10:06:11.381 → 2021-02-20 18:37:44.2263 | 2013-02-24 18:56:54.3095 |
| sh000300 | 2002-01-04 → 2026-11-13 | 2006-12-21 18:41:19.8669 → 2020-08-22 11:21:39.8336 | 2011-12-16 02:39:20.0666 |
| sz399006 | 2010-06-01 → 2026-11-13 | 2013-09-12 19:12:28.7521 → 2022-09-30 06:00:35.9401 | 2016-12-30 14:23:45.624 |
| sz399673 | 2014-06-18 → 2026-11-13 | 2016-12-08 16:36:44.3261 → 2023-10-05 08:45:55.4077 | 2019-06-05 03:41:37.8369 |
| sh000680 | 2020-01-02 → 2026-11-13 | 2021-05-16 13:34:38.5358 → 2025-02-23 04:58:18.1697 | 2022-10-01 05:12:40.7321 |
| sh000688 | 2020-01-02 → 2026-11-13 | 2021-05-16 13:34:38.5358 → 2025-02-23 04:58:18.1697 | 2022-10-01 05:12:40.7321 |

## Sparse scratch fixture — PASS, successful harness exit

Created a scratch-only copy of data outside repository, fed through current `app.chart.build`. Never published/replaced real data/report. [Builder](browser-evidence-round2/fixture.py), [build output](browser-evidence-round2/fixture-build.txt), [actual prominently synthetic-labelled surface](browser-evidence-round2/synthetic-gap-fixture.png).

Synthetic sh000016: Oct23 missing comparator session; Oct28 explicit null; Oct29 numeric zero. Actual x dates are Oct21,22,23,24,25,28,29,30,31 (2024); y is `[10,11,null,13,14,null,0,12,14]`. No weekend dates inserted; `connectgaps=false`; calcdata retains zero at Oct29 and unavailable entries at both gaps. Scratch-only API zoom to Oct20–Nov1 makes gaps visible.

Corrected selector accepts **main `.subplot.xy` ancestry only and excludes `.rangeslider-container`**. Exactly three disconnected main SVG paths:

```text
M100.17,78.01L200.33,61.69
M400.67,29.03L500.83,12.7
M901.5,241.3L1001.67,45.36L1101.83,12.7
```

The screenshot visibly shows three separated blue segments and the third starting at numeric zero, not a line spanning either unavailable date. Final complete browser harness returned **exit0, status PASS**, including gap-count, null/zero and weekend assertions. No explanation-only waiver of the round1 fixture failure.

## Offline/resource execution and harness transparency

First commands were `free -m` (6741MiB available) and `~/.omp/bin/heavy-gate --status` (both slots free). Every browser launch was gated, finite bash `async:true, timeout:0`, no timeout wrapper:

```sh
~/.omp/bin/heavy-gate -n 1 -m 6G -- node /tmp/sentiment-browser-round1/review-round2.cjs
```

Final run uses **one browser, one context, one reused page**, serial seven-panel loop, `file://`, context offline, service workers blocked, non-file/data routing aborted. Only two observed requests: actual report file and scratch fixture file. Blocked network attempts, browser console and page errors all `[]`. Browser closes in `finally`; [post-run resource output](browser-evidence-round2/resource-after.txt) shows both slots free. No server or eval browser launcher.

Two earlier serial, gated harness-development attempts exited1 before any real interaction loop: first overstrict legend-background/title rectangle intersection (~0.96px of empty legend padding, not glyph overlap), second invalid direct-child marker selector. Both browsers closed before the next attempt. Their exact observations/output are retained as `attempt1-*` and `attempt2-*` under the evidence directory; no product change occurred. Final measurements use visible text geometry with actual screenshot inspection and main-subplot ancestry for markers/paths. **The final run completed every assertion successfully**, rather than reclassifying a failed harness as passing.

[Commands/hash/attempt record](browser-evidence-round2/commands.txt), [final harness](browser-evidence-round2/review.cjs), [final output](browser-evidence-round2/harness-output.txt), [exit0](browser-evidence-round2/harness-exit.txt), [full exact ranges/data](browser-evidence-round2/observations.json), [pre-run resources](browser-evidence-round2/resource-before.txt).

Boundary: desktop only; no mobile/wheel/double-click-specific claim. R1/R2 whole-change static/acquisition acceptance belongs to its independent reviewer. External genuine live/full-history sentiment blocker remains unchanged; no fabricated full overlay, no whole-goal PASS.
