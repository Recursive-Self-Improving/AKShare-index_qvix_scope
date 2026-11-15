# Independent UI/data artifact review — round 1

**Verdict: Fix — B1 (panel-local legends not readable).** Data identity, seven independent dual axes, offline loading, drag zoom, reset, navigation, and sparse-gap rendering pass the observations below. This is not acceptance of unavailable genuine full sentiment history.

Read goal ledger, README, implementation evidence, actual `app/chart.py`, and relevant offline verifier/gap helper. No production, README, ledger or acquisition edits; no commits. No repeat live provider request.

## B1 — Fix: legend is not readable on the actual panel surface

Location: `app/chart.py:42-54` (`height=520`, bottom margin 110, horizontal legend `y=-0.27`), actual `report.html`.

At 1440×1100 all seven complete panel screenshots show blue index lines and orange documentation markers, but **neither trace legend is readable anywhere in the panel**. The visible range slider and date-axis title leave no readable local label for the orange diamonds. This matters when scrolled to a later panel: the global documentation-only warning is out of view and the right axis merely says sentiment. The claim of differently classified legends is not delivered visibly.

Evidence: [panel 1](browser-evidence/panel-1-initial.png), [panel 4](browser-evidence/panel-4-initial.png), [panel 7](browser-evidence/panel-7-initial.png); identical issue on other panel screenshots. The deliberately synthetic [gap fixture](browser-evidence/synthetic-gap-fixture.png) also shows legend text intersecting/being obscured by the slider. **[INFERENCE]** The legend/slider/footer layout competes for the same space; exact corrective positioning is implementer's choice.

Required fix: reserve nonoverlapping visible space for both trace labels on every panel, with documentation-only/not-live classification readable next to the samples. Rebuild report and have a new independent browser review check the actual surface. Do not remove or weaken the top failure warning.

## Browser/resource evidence

Exactly **one** real Chrome browser, one context, one reused page; no preview tools/server. Loaded actual report with `file://`, context `offline:true`, service workers blocked, non-file/data routes aborted. Browser launched only through:

```sh
~/.omp/bin/heavy-gate -n 1 -m 6G -- node /tmp/sentiment-browser-round1/review.cjs
```

Finite bash `async:true, timeout:0`. Initial `free -m`: 7741 MiB available; both gate slots free. Browser closed in `finally`; both slots free afterward. [Exact resource outputs](browser-evidence/resource-guard.txt).

Report SHA256 at review: `69597295f96a086dafef1ebc3464e443b2847070eb4becad9163c9361fa79b4d`.

[Raw browser observations](browser-evidence/observations.json) retain exact ranges, actual axes, data comparisons, requests and errors. Console messages: `[]`; page errors: `[]`; blocked network attempts: `[]`. Only observed requests: actual report file and scratch fixture file. Thus actual offline render/interactions needed no external resource, rather than merely having no configured CDN.

## Actual data and honest state — PASS

Ran `.venv/bin/python -m app.verify --input data --report report.html`, exit 0. [Exact output](browser-evidence/offline-verify.txt). Raw body/hash replay, CSV/manifest identity and actual seven embedded arrays agreed. Index row counts: 6509 / 5552 / 6030 / 3995 / 3017 / 1663 / 1663; all real relative index gap counts zero.

Browser additionally compared each live Plotly graph's plotted x/y/mode/yaxis arrays with the embedded JSON: all seven equal, exactly two traces per panel, second trace exactly ten documentation examples. No genuine provider sentiment trace exists. Orange open-diamond points render in two historical clusters without a connecting year-long line. Some adjacent daily markers overlap at full-history scale; this does not invent or omit rows.

[Top warning screenshot](browser-evidence/01-warning.png) visibly states `transport_failure`, current provider unavailable, genuine coverage unknown, no last successful snapshot, only ten documentation examples, not live/full history, remaining 231 rows not recovered. No completed genuine sentiment history is represented. These observations do not change the existing external full-history blocker.

All seven screenshot surfaces have legible Chinese names/codes and Chinese left index/right sentiment titles, separate numeric scales. Example full left axes: sh000001 `[729.2457777777778, 6374.310222222222]`, sh000688 `[556.1073888888889, 2294.799611111111]`; independent right sentiment range `[0.9842923081614549, 1.0205826918385452]` on every panel. Equal right ranges are expected from identical ten-point samples, not shared index scaling. Exact remaining axes in JSON. The raw `visible_markers:0` field is an invalid DOM selector measurement, not absence of plotted markers; screenshots show the markers and live arrays retain all ten.

## Every panel's real mouse interactions — PASS

Each panel was scrolled into view and captured, then mouse-down/move/up rectangle-dragged from 20%/20% to 75%/80% of its actual plot area. Every drag narrowed x-range; all six other panels' x-ranges stayed exactly unchanged. Clicked actual `重置本图`, `1年`, `5年`, `全部`; mouse-dragged the actual bottom slider; clicked reset again. No Plotly API was used for these real-report interactions.

| Panel | Initial / both resets / 全部 | Observed drag x-range |
|---|---|---|
| 上证指数 sh000001 | 2000-01-04 → 2026-11-13 | 2005-05-15 17:39:02.0965 → 2020-02-21 10:03:47.6206 |
| 上证50 sh000016 | 2004-01-02 → 2026-11-13 | 2008-07-26 10:06:11.381 → 2021-02-20 18:37:44.2263 |
| 沪深300 sh000300 | 2002-01-04 → 2026-11-13 | 2006-12-21 18:41:19.8669 → 2020-08-22 11:21:39.8336 |
| 创业板指 sz399006 | 2010-06-01 → 2026-11-13 | 2013-09-12 19:12:28.7521 → 2022-09-30 06:00:35.9401 |
| 创业板50 sz399673 | 2014-06-18 → 2026-11-13 | 2016-12-08 16:36:44.3261 → 2023-10-05 08:45:55.4077 |
| 科创综指 sh000680 | 2020-01-02 → 2026-11-13 | 2021-05-16 13:34:38.5358 → 2025-02-23 04:58:18.1697 |
| 科创50 sh000688 | 2020-01-02 → 2026-11-13 | 2021-05-16 13:34:38.5358 → 2025-02-23 04:58:18.1697 |

Every panel's 1年 range exactly `[2025-11-13, 2026-11-13]`; every 5年 range exactly `[2021-11-13, 2026-11-13]`. Every 全部 and both resets exactly restored that panel's original date strings, including after slider navigation.

| Panel | Slider start (end always 2026-11-13) | Initial / drag screenshots |
|---|---|---|
| sh000001 | 2010-10-03 15:10:28.9517 | [initial](browser-evidence/panel-1-initial.png) / [drag](browser-evidence/panel-1-drag.png) |
| sh000016 | 2013-02-24 18:56:54.3095 | [initial](browser-evidence/panel-2-initial.png) / [drag](browser-evidence/panel-2-drag.png) |
| sh000300 | 2011-12-16 02:39:20.0666 | [initial](browser-evidence/panel-3-initial.png) / [drag](browser-evidence/panel-3-drag.png) |
| sz399006 | 2016-12-30 14:23:45.624 | [initial](browser-evidence/panel-4-initial.png) / [drag](browser-evidence/panel-4-drag.png) |
| sz399673 | 2019-06-05 03:41:37.8369 | [initial](browser-evidence/panel-5-initial.png) / [drag](browser-evidence/panel-5-drag.png) |
| sh000680 | 2022-10-01 05:12:40.7321 | [initial](browser-evidence/panel-6-initial.png) / [drag](browser-evidence/panel-6-drag.png) |
| sh000688 | 2022-10-01 05:12:40.7321 | [initial](browser-evidence/panel-7-initial.png) / [drag](browser-evidence/panel-7-drag.png) |

## Sparse-gap fixture — PASS by actual surface and captured paths

Real datasets have no comparator gaps. A scratch data copy outside the repo was fed through actual `app.chart.build`; never replaced/published real report or data. Synthetic sh000016 observations span 2024-10-21–31: missing comparator session Oct23, explicit null Oct28, genuine numeric zero Oct29. Expected/observed plotted arrays:

```text
x = [21,22,23,24,25,28,29,30,31] (all October 2024)
y = [10,11,null,13,14,null,0,12,14]
```

No weekend Oct26/27 samples inserted. Browser calcdata preserves missing/null as unavailable and Oct29 as numeric zero. `connectgaps=false`; [actual synthetic screenshot](browser-evidence/synthetic-gap-fixture.png), prominently red-labelled NOT REAL DATA, shows three separated blue segments, not a line spanning either missing/null date. Scratch fixture only was zoomed by `Plotly.relayout` to Oct20–Nov1 to make gaps visible.

Harness caveat, preserved rather than hidden: the browser command exited 1 at its final fixture assertion `svg_line_paths.length===3`, yielding raw JSON `status:Fix`, `failure:gap rendered as connected`. That assertion accidentally selected **both** main-plot and rangeslider SVG paths: captured six paths comprise three main paths then three miniature slider paths. First three main paths exactly:

```text
M100.17,75.25L200.33,59.5
M400.67,28L500.83,12.25
M901.5,232.75L1001.67,43.75L1101.83,12.25
```

They explicitly encode three disconnected segments; screenshot independently confirms. This is an instrumentation failure, not a product gap bug. No second browser or artificial passing rerun was used. All seven real-panel assertions completed successfully before this final harness assertion. The review's actual Fix is B1 above, not that misleading raw harness failure text.

## Boundary

Desktop viewport only; no mobile or double-click/wheel-specific acceptance claim. Static implementation review belongs to the other reviewer. No independent whole-goal PASS while B1 or genuine provider/full-history external blockers remain.
