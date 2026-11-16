# Independent matched-QVIX final browser review — round 2

## PASS — F-B1 resolved; complete browser acceptance converged

Reviewed actual root `report.html`, SHA-256 **`84d5570f1551e6e193310fec3e769ad356fa95187e9e3ec8ce725bf112da5d58`**, checked before and at the end of the complete harness. Scope: browser obligations of active AC13–16, approved matched-QVIX plan, original round-one findings and `9cb3397` layout preservation. No open/new/reopened browser Fix, Replan or Ask; no failed assertion waived.

Only this review and [round-two evidence](matched-qvix-browser-evidence-round2/) were written in the repository. No production/data/report/ledger edits, commits, provider endpoint calls or subdelegation. Read the complete round-one review/harness, retained failures and final evidence, corrective evidence, active requirements and approved plan before execution.

## Complete successful execution

**One gated launch, one browser/context/reused page, exit 0, `status=PASS`, `failures=[]`, eight completed panels, three genuine null-gap views and labelled finite zero.** Playwright-core/Google Chrome; actual offline `file://` report; 1440×1100 viewport; light then dark reload; service workers blocked and external requests aborted. Exactly two report-file requests, **zero external requests, zero blocked dependencies, zero page errors and zero console messages**. Shell DBus accessibility startup messages are not page-console errors.

```sh
~/.omp/bin/heavy-gate -n 1 -m 6G -- bash -c \
  'node --check /tmp/sentiment-browser-round2/matched-review.cjs && node /tmp/sentiment-browser-round2/matched-review.cjs'
```

Finite launch used `async:true, timeout:0`, no outer timeout, one reserved slot and 6G scoped cap; browser closed in `finally`. Initial preliminary resource check found one unrelated occupied slot and 6928 MiB available. Immediately before the actual launch, both slots were free and `free -m` showed 6732 MiB available (gate status 6726 MiB); afterward both slots were free and 7013 MiB available (gate status 7019 MiB). One owned browser maximum; machine-wide width remained within two.

Retained [commands/errors](matched-qvix-browser-evidence-round2/commands-errors.txt), [exact harness source](matched-qvix-browser-evidence-round2/harness-source.txt), [output](matched-qvix-browser-evidence-round2/harness-output.txt), [exit](matched-qvix-browser-evidence-round2/harness-exit.txt), source/report hashes, resource snapshots and [complete observations](matched-qvix-browser-evidence-round2/observations.json). Runnable scratch automation remains outside the repository.

## F-B1: actual hover and ordinary label-center clicks

On **every panel**, real mouse hover exposes the existing modebar. Actual DOM `.legendtext` **and** `.legendtoggle` rectangles are disjoint from all `.modebar-group` rectangles, in **both light and dark**: 16 panel/theme measurements, zero intersections; modebar group opacity 1 and visibility `visible`. All eight legends have `x=0`, `xanchor=left`, unchanged `y=1.17`.

All **19 legend labels**, including each index, were hidden and restored with ordinary `page.mouse.click` at the exact geometric **center of the label text**, following actual hover. At every click center `elementFromPoint` belonged to that legend entry and the modebar remained exposed. Each clicked trace alone became `legendonly`; every sibling stayed visible; restoring returned every trace to visible. No exposed-line-sample workaround, alternate-point scan, forced click, event dispatch, modebar removal or scripted restyle.

Panel 1 concrete geometry: rightmost QVIX hit rectangle x **529.72–702.25**, y **259.00–278.00**; modebar x **1053–1269**, y **243.58–268.97**. Horizontal separation **350.75 px**. Actual 50ETF label center **(634.73, 269.18)** successfully hides/restores only that trace. This resolves the real interception documented in round one, rather than bypassing it.

Evidence: [all centers, visibility states and modebar geometry](matched-qvix-browser-evidence-round2/legend-center-and-modebar.json); `panel-1-initial.png` through `panel-8-initial.png` and `panel-1-dark.png` through `panel-8-dark.png`. Visually inspected all 16 full-panel screenshots: labels readable, hover controls present and separate, neither control strip nor plot/axis/slider clipped.

Round-one instrument errors were corrected **before this launch**: removed the exposed-line workaround; retained 1000ms click separation and SVG `textContent()` instead of unsupported `innerText()`; included actual modebar geometry and computed group opacity. One scratch edit-anchor request was rejected and corrected before launch. This round had no failed browser attempt or explanation-only acceptance.

## Whole eight-panel acceptance

Exact ordered panel mappings and trace counts passed:

| Panel | Index rows | QVIX feeds: trace rows / nulls / finite zero dates |
|---|---:|---|
| 上证指数 sh000001 | 6509 | 50index 939/186/33; 50etf 2861/14/0 |
| 上证50 sh000016 | 5552 | 50index 939/186/33; 50etf 2861/14/0 |
| 深证100 sz399330 | 5053 | 100etf 954/14/0 |
| 沪深300 sh000300 | 6030 | 300index 1674/192/42; 300etf 1674/15/0 |
| 创业板指 sz399006 | 3995 | cyb 1009/14/0 |
| 创业板50 sz399673 | 3017 | cyb 1009/14/0 |
| 科创综指 sh000680 | 1663 | kcb 839/14/1 |
| 科创50 sh000688 | 1663 | kcb 839/14/1 |

Panels **1, 2 and 4 have three traces**, not two: index left `y`, two separately named QVIX closes on right `y2`, percent. Other panels have two traces. QVIX traces are lines with `connectgaps=false`; dual feeds use distinct orange-solid/purple-dashed styles.

Independently read/hash-checked eight index CSVs, seven QVIX CSVs and seven quality sidecars; active feeds equal retained manifest feeds. Rebuilt expected date unions from nonblank/internal-blank/tail-blank/hole sets, selected by the requested window, and closes/nulls from CSVs. Every rendered array exactly equals embedded panel data and these independent expectations; shared feeds therefore retain identical arrays across panels. This is browser/CSV/quality/manifest binding, **not a replacement for the separate full raw-normalization review**.

Different coverage remains visible: 50ETF starts 2015-02-09 versus 50股指 2023-01-03; 100ETF 2022-12-12; 300 feeds 2019-12-23; 创业板 2022-09-19; 科创板 2023-06-05. No fabricated earlier prices. 深证100 visibly identifies base 2002-12-31, release 2006-01-24 and 5053 retained rows from 2006-01-24, not a vendor-first-row inception claim.

**All eight panels** passed real mouse down/move/up main-plot drag zoom, reset, **1年/5年/全部**, actual rangeslider drag and final reset. Other panels retained their original ranges; navigation clicks also preserved every range. No scripted relayout substitutes for these control tests. Exact intermediate ranges: [ranges.json](matched-qvix-browser-evidence-round2/ranges.json); eight `panel-*-drag.png` captures retained.

## Real source nulls and labelled zero

Only after all real-mouse control tests, targeted range setup used Plotly relayout for these real source views:

- **Invalid/error:** 50股指, 2024-05-13–2024-06-07, actual invalid close **2024-05-20 = null**; orange main line disconnects while the index continues.
- **Conflict:** 50ETF, 2026-10-26–2026-11-13, actual **2026-11-02 = null**, alongside November 3–5 absent dates; purple main line disconnects, no candidate selected.
- **Blank:** 300股指, 2026-09-07–2026-09-22, actual internal blank **2026-09-14 = null** within a broader real null/error run; orange line resumes September 16. Not a synthetic isolated blank between adjacent finite closes.

Each query binds the actual main trace `_fullData[trace].uid`, excludes **all** `.rangeslider-container` descendants and finds exactly one main trace plus one explicitly excluded slider copy. Retained main paths: **23/6/31**; these are full retained main-trace path counts, not only in-range visible segment counts. Null/category assertions and visual gap screenshots both pass. [Main-trace evidence](matched-qvix-browser-evidence-round2/main-trace-gaps.json), `gap-error.png`, `gap-conflict.png`, `gap-blank.png`.

Real 科创板 **2026-11-09 close 0** survives CSV→embedded→rendered arrays and reaches the axis in the targeted view. Exact labelled hover: **`科创板 QVIX 收盘（%）(Nov 9, 2026, 0)`**; [zero screenshot](matched-qvix-browser-evidence-round2/zero-kcb.png). Hover setup uses `Plotly.Fx.hover`, not a claim of real-mouse zero discovery. Reading notes explicitly retain zero without certifying economic validity.

## Disclosure and preserved layout

Entire page CSS equals retained `9cb3397` CSS byte-for-byte. Actual navigation/card/reset/range-selector/slider layout and light/dark surfaces remain intact; all non-modebar label geometry is contained/disjoint and paragraphs wrap without horizontal clipping. Visually inspected final header, all light/dark panels, three gap views, zero hover, source-detail sample and reading notes.

Every mapped feed has its **own visible** name, partial attempt/time, partial fresh snapshot/time, original identity hash, source/close coverage, holes, conflicts, invalid fields, zero-row counts and comparator identity; seven quality summaries explicitly say **partial**. Index success/fresh/range/row disclosures also pass. Different feed warnings are not concealed by siblings. Source detail preserves distinct own counts, shared acquisition reference, quality identity and comparator provenance. No fresh fatal/stale/unavailable state was fabricated into this actual fresh-partial report.

Reading notes visibly disclose proxy mappings/unknown exact ETF contracts, blank/error/conflict gaps, conflicts nulling all OHLC, no repair/interpolation/extrapolation, zero retention, retrospective non-point-in-time timing, 科创综指 dividends versus 科创50 price index, HTTP acquisition and unconfirmed redistribution permission.

**Final browser disposition: PASS. F-B1 closed by direct surface proof; complete browser acceptance converged on the final hash.** Provider correctness, official-calendar completeness, economic methodology, publication timing and licensing remain external limitations, not certified by this review. Independent code/data review and orchestrator project-gate/ledger decisions remain separate responsibilities.
