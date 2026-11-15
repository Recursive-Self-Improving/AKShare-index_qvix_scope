# 情绪与七指数历史对照

## Control summary
- Mode: proactive; orchestrator chooses the next move from evidence, delegates implementation/research/review, and maintains this single ledger.
- Scope is the AC below; never silently weaken or drop it. Persist evidence and append decisions.
- Implementation and review use different workers; implement only firm, independently reviewed plan sections.
- Commit every green checkpoint with Conventional Commits; protect unrelated changes; never push.
- Final gate: Reread the ledger. The gate passes only when every AC has verified evidence or a valid recorded blocker or deferral; every dropped, weakened, superseded, or invalidated AC or work item cites its decision-log entry; no decision is open; no finding is open with triage Fix or Replan; no plan section is still unknown-until unless its trigger is recorded as blocked; a final whole-change REVIEW-LOOP has converged; and you have rerun the full project gates (build/typecheck, tests, lint as applicable) on the final tree after the last change, and they pass. If any item is still doable now, continue the loop instead.
- At completion quote every non-done item with its status/reason; only external missing tools/access/services or external-system changes justify pause.

## Acceptance criteria
1. Actually invoke AKShare `index_news_sentiment_scope`; persist real response, source/version, retrieval timestamp, available range, and evidence of history/backfill limits. Seek daily observations from 2000-01-01 through retrieval date; if unavailable, backfill all genuinely obtainable observations, recording gaps without synthesis.
2. Fetch and persist daily histories since 2000-01-01 (or earliest genuine available date) for 上证指数、上证50、沪深300、创业板指、创业板50、科创综指、科创50. Resolve canonical identifiers; include dates and close values, provenance/ranges/gaps; distinguish pre-inception and unavailable data.
3. Deliver one HTML with seven clearly labelled charts, each overlaying the corresponding daily index and sentiment on readable separate scales, preserving real dates/missingness. Mouse drag/selection must zoom the time range; provide usable reset/navigation.
4. Provide runnable refresh/backfill/chart commands, machine-readable raw/normalized data and documentation sufficient for comparison/backtesting; clearly state publication/look-ahead limitations and do not imply causality. No scheduled task in this goal.
5. Independent review converges; actual data and chart behavior are verified; all applicable project checks pass on final tree.

## Plan
- Research and feasibility [firm; unreviewed]: delegate a runtime spike in scratch space and a proposed implementation plan; persist evidence under docs/research/. Empty repository has no prior artifacts.
- Acquisition and visualization [unknown-until(runtime spike); unreviewed]: choose dependencies, sources, history limits and chart delivery based on observed endpoint behavior.
- Verification and delivery [tentative; unreviewed]: independent plan review before implementation; independent whole-change review and gated visual browser verification; final full checks.

## Work items
- W1 research/spike; AC1,2,4; active — probe endpoints and propose feasible plan with persisted evidence.
- W2 review; AC1–5; todo — independent PLAN-REVIEW.
- W3 impl; AC1–4; todo — acquire genuine history and build reproducible seven-chart artifact.
- W4 review; AC1–5; todo — independent whole-change review and visual verification.
- W5 fix; AC5; todo — resolve findings, run final gates, commit final ledger.

## Decision log
- D1: No existing ledger, code or commits found (`ls -la`, `git status`, `git log`, 2026-11-15). Choose a new ledger here rather than competing artifacts. Use T3 delegates rather than unavailable in-process workers. Preserve original goal, including partial-history fallback and explicit exclusion of scheduling.

## Findings and open questions
- Q1: Actual sentiment history depth and historical query support unknown; triage research, open, W1.
- Q2: Canonical 科创综指 and 创业板50 identifiers/source history need evidence; triage research, open, W1.
- Q3: Browser/chart packaging and offline portability depend on runtime findings; triage design, open, W1/W2.

## Iteration log
- I1: Choose scratch runtime research + plan before implementation; reject guessing API history or using fabricated historical sentiment. Replan when endpoint capability is observed.
