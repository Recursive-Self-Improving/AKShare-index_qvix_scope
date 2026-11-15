# Independent sample-plan delta review

## Verdict: PASS

Review baseline: `4dcb9246a8` (task-supplied). Scope: only the ledger Plan “Documented historical samples” and D4, checked against AC1–5, the existing acquisition/visualization contracts, `plan-review-round2.md`, `sentiment-recovery.md`, and the exact historical-documentation excerpt. Static review; no implementation, endpoint calls, browser work, ledger edits, or commits.

**Honest partial inclusion is acceptable.** The delta adds separately identified evidence, not a replacement sentiment feed or a relaxation of acceptance criteria. No Fix or Replan finding.

## Evidence and compatibility

- The excerpt explicitly prints ten dates and sentiment values: five observations spanning 2023-10-31–2023-11-06 and five spanning 2024-10-25–2024-10-31. Its ellipsis and `[241 rows x 3 columns]` do not recover the other 231 rows or prove historical completeness. The proposed import correctly excludes them.
- The source is an AKShare documentation example attributed to ChinaScope, not retained provider JSON or an independently authenticated original capture. Separate CSV naming, manifest provenance, and visible HTML labels preserve that distinction. An immutable source reference and exact-source/excerpt hashes establish reproducible transcription, not provider authenticity.
- Isolated sentiment-axis markers, explicitly labelled **“documentation example, not live/full history”**, preserve the reported dates without interpolation, connecting lines, extrapolation, or invented observations. Unobserved dates remain unknown, not zero or proven provider omissions. The original independent index histories and seven-panel interaction requirements remain unchanged.
- Unknown original capture, publication, and revision times remain explicit. These examples cannot establish point-in-time availability, a safe trading lag, causality, or backtest-ready sentiment history. Any retained documentation 沪深300 values remain source-example fields, separate from independently acquired 沪深300 closes under the existing contract.
- Documentation import cannot promote a provider acquisition to success, replace its response capture, suppress the required nonzero live-fetch failure, or update its success timestamp. The existing acquisition contract and the delta's separate manifest/HTML live-failure status require this separation.
- D4's blocker is supported as an environment-specific outcome of bounded recovery attempts, not proof that no archive or service exists. Research explicitly distinguishes archive timeouts from negative results. Provider restoration/access to authentic history remains the unblock condition; the documentation samples do not resolve it.

## Approval boundary

The license check is a prerequisite to sample redistribution, not a completed finding. Before publishing the CSV or embedded chart samples, record the applicable license/terms and permission basis, plus immutable source identity, retrieval provenance and exact-source/excerpt hashes. If permission is not established, do not redistribute the samples; retain an explicit blocked disposition rather than silently substituting or declaring completion.

Implementation must still pass the already-approved raw/hash replay and embedded-trace comparison gates, including exact transcription of these ten rows and their documentation-only labelling, followed by the existing interaction and final review gates. This review does not claim those checks have run or that the recorded upstream hash has been independently verified.

AC1/AC3 remain incomplete/external-blocked for genuine live/full sentiment history and successful provider overlays. All reachable acquisition, chart, provenance, command and verification work remains required. PASS approves this bounded plan addition only; it does not approve final delivery or weaken the original acceptance criteria.
