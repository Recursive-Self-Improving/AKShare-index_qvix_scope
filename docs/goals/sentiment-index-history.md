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
- Research and feasibility [firm; unreviewed]: runtime evidence and proposed plan in [endpoint feasibility](../research/endpoint-feasibility.md); targeted same-source recovery research remains before accepting the sentiment blocker.
- Acquisition and visualization [firm; unreviewed]: sequential bounded Python acquisition, AKShare 1.20.53 for actual sentiment invocation and Sina decoder; retain exactly fetched raw bytes, normalized CSV and provenance/gap metadata. Build one offline Plotly HTML with seven dual-axis charts, drag zoom, reset/navigation, no fabricated sentiment. Missing sentiment must be prominently marked as externally blocked, not successful overlay completion. Preserve prior successful snapshots on errors. Detailed proposal: endpoint-feasibility.md §Bounded implementation plan.
- Verification and delivery [firm; unreviewed]: independent PLAN-REVIEW; implement bounded acquisition+HTML slice; independent whole-change review with gated real-browser zoom/offline proof; full project gates after final code change. Targeted same-source recovery research may improve the source plan; a changed source contract requires re-review.

## Work items
- W1 research/spike; AC1,2,4; done — observed actual AKShare invocation failure and seven real index histories; persisted docs/research/endpoint-feasibility.md.
- W2 review; AC1–5; active — independent PLAN-REVIEW of evidence and firm proposal.
- W3 impl; AC1–4; todo — acquire genuine history and build reproducible seven-chart artifact.
- W4 review; AC1–5; todo — independent whole-change review and visual verification.
- W5 fix; AC5; todo — resolve findings, run final gates, commit final ledger.
- W6 research; AC1,3; active — targeted independent same-provider recovery/archive investigation before treating sentiment as externally blocked.

## Decision log
- D1: No existing ledger, code or commits found (`ls -la`, `git status`, `git log`, 2026-11-15). Choose a new ledger here rather than competing artifacts. Use T3 delegates rather than unavailable in-process workers. Preserve original goal, including partial-history fallback and explicit exclusion of scheduling.
- D2: Runtime spike fires unknown-until trigger. Evidence: docs/research/endpoint-feasibility.md. All seven Sina symbols work; sentiment was removed in AKShare 1.20.54 and old invocation fails after provider redirect/certificate error. Choose bounded raw-preserving acquisition and self-contained Plotly over CDN or a server; do not substitute a different sentiment metric. Plan diff replaces unknown acquisition section with firm proposal; no owned production code exists to remove/rewrite/keep. W3 covers all original acquisition/visualization scope; W6 tests whether the external sentiment failure is recoverable. AC1/3 are not weakened: absent sentiment remains an explicit external blocker, not a completed overlay.

## Findings and open questions
- Q1: Sentiment wrapper has no dates/pagination; actual history unknown because provider is inaccessible. Triage research, open, W6; evidence endpoint-feasibility.md §Sentiment.
- Q2: Canonical identifiers resolved and seven histories observed; triage research, closed, W1. Pre-publication history requires explicit retrospective flags, not pre-inception labels.
- Q3: Choose offline Plotly bundled once; triage design, closed by D2, subject to W2 review.

## Iteration log
- I1: Choose scratch runtime research + plan before implementation; reject guessing API history or using fabricated historical sentiment. Replan when endpoint capability is observed.
- I2: Evaluate W1 and replan on runtime evidence; choose independent plan review plus focused same-source recovery investigation. Reject declaring all sentiment history impossible from a short timeout alone. A genuine same-source response changes the acquisition plan; otherwise finish all index/chart work with an explicit external blocker.
