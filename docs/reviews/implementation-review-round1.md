# Independent whole-change implementation review — round 1

## Verdict: Fix; original scope has not converged

Baseline: `0e67402c2f` plus the supplied uncommitted implementation, data, report and documentation. Reviewed the durable goal ledger, original F1–F5, round-two approval, sample-plan approval, research, all application modules and contract tests, dependencies, persisted acquisition accounting and actual embedded artifact. No production/ledger edits, commits, live endpoint calls or browser launches. Browser/offline interaction review belongs to the other reviewer; final union gates belong to the orchestrator.

Two in-scope correctness findings remain. Neither requires an architectural replan. Genuine sentiment unavailability is an independently documented external blocker, **not** one of these defects and not a successful overlay.

## Findings

### R1 — Fix (medium): observed empty sentiment is classified as validation failure

- **Location:** `app/fetch.py:49–56,68–71`; contrasting contract at `app/core.py:82–88` and test at `tests/test_contracts.py:113–118`.
- **Evidence:** A network-free invocation of the real `worker`, with only `requests.get` replaced by a response-hook-compatible HTTP200 response containing exactly `[]`, persisted the exact body but produced:

  ```text
  EMPTY: validation_failure KeyError: "None of [Index(['日期', '市场情绪指数', '沪深300指数'], dtype='str')] are in the [columns]" capture= b'[]'
  ```

  Inspected installed AKShare1.20.53: its actual function builds an empty DataFrame and selects three missing columns before returning. Consequently the worker never reaches its own strict decoder, which explicitly accepts this genuine empty JSON-array outcome. Existing coverage exercises `decode`, not this worker path.
- **Consumer impact:** An observed empty successful response is reported as malformed/provider failure; a prior snapshot would be marked stale and the required-feed exit would be nonzero. README's distinction between a successful zero-row response and unknown/failed acquisition is not implemented end to end. This violates approved F1, even though the currently delivered live attempt was a different, validly reported TLS failure.
- **Required fix:** Preserve the actual pinned invocation and raw capture while explicitly supporting the valid observed-empty outcome through acquisition/promotion. Do not turn arbitrary wrapper exceptions, malformed JSON, non200 responses or transport failures into success. Add a deterministic worker-level regression proving empty success remains distinct from failure and from numeric zero.
- **Triage rationale:** **Fix**, not Replan or Discard: the approved contract already requires this distinction; it is reachable without provider access. No substitute source or broader ingestion framework is needed.

### R2 — Fix (medium): displayed sentiment coverage describes only the last revision, not the plotted merged history

- **Location:** `app/chart.py:15–17,23,31–34,72–76`; related acquisition coverage accounting at `app/fetch.py:138–146`.
- **Evidence:** A temporary, network-free two-revision fixture retained 2023-10-31 and 2024-10-31 in its first successful CSV and only a revised 2024-10-31 in its second. Using the actual `sentiment_rows` and `panels` functions gave:

  ```text
  MERGED: ['2023-10-31', '2024-10-31'] DISPLAYED_RANGE: ['2024-10-31', '2024-10-31']
  PANEL_GENUINE: 2023-10-31 2024-10-31
  ```

  The displayed range expression reads `snapshot['range']`, whereas the plotted trace merges every successful revision. Manifest sentiment `relative_gaps` and extra dates likewise use only `snapshot['csv']`, not the selected merged history. Thus first-to-last plotted coverage and retained historical observations can disagree with the human/machine-readable coverage accounting. The HTML trace comparison currently validates merged arrays but cannot detect this metadata mismatch.
- **Consumer impact:** After normal rolling-window refresh/backfill, the warning claims a shorter sentiment coverage than it actually plots, and the supplied gap accounting does not describe that plotted series. Users comparing dates or assessing missingness cannot distinguish latest-response coverage from accumulated selected coverage. This violates F1/F4's visible actual ranges and deterministic revision-policy accounting.
- **Required fix:** Keep latest-response range/time and immutable revision identities, but explicitly distinguish them from the selected latest-successful-by-date history's range/count and relative gaps. Use the same documented selection policy for rendered and machine-readable coverage; retain the non-independent calendar caveat. Add a focused two-revision regression covering an older date omitted by a newer successful response.
- **Triage rationale:** **Fix**, not Replan or Discard: accumulation is already the approved policy; this is inconsistent accounting, not a request for a point-in-time database. The delivered no-success sentiment state is unaffected, but refresh/backfill correctness remains in original scope.

## Independent evidence and boundaries

1. Ran `uv run python -m app.verify --input data --report report.html` once; exit0. Actual persisted raw-body hashes/replay, immutable/latest manifest identity, normalized CSV, documentation hashes/transcription and seven actual embedded panel arrays agreed. Observed index counts: 6509, 5552, 6030, 3995, 3017, 1663, 1663; all seven relative index gaps zero. This comparator is non-independent and does not establish complete exchange-calendar history.
2. Inspected installed pinned AKShare function bodies after LSP definition lookup returned `Unknown request: textDocument/definition`. Sentiment actually calls `http.get` with `period=YEAR`; Sina uses the pinned JavaScript decoder. No provider invocation was repeated during review.
3. Inspected current manifest/attempts: seven real successes, one `transport_failure`, actual invocation `index_news_sentiment_scope()`, pinned AKShare1.20.53 and decoder mini-racer0.14.1, no stale reuse and no successful sentiment revision. The preserved HTTP301 body/hash precedes the recorded authenticated TLS failure. No nonexistent final TLS body or successful sentiment range is claimed.
4. Inspected immutable documentation source reference, exact excerpt, CSV/provenance and retained MIT copyright/permission. Ten explicit dated values only; the other231 rows are not imported. Samples stay separate from provider snapshots and source `marketClose` remains separate from independent index closes. Plot traces use isolated, explicitly documentation-only markers, not a line across the missing year. Permission basis is the retained AKShare documentation license, not a claim of licensed complete ChinaScope history.
5. The two investigations above ran in temporary directories, using local deterministic responses/CSVs. No permanent test or fixture files were added and no production data was changed. These are contract probes, not acquired observations.
6. Did not rerun full lint/tests/install, a live endpoint failure, or browser gates. Implementation evidence reports its own19-test union run; that report is not independent final-tree certification. No browser/heavy launch was needed.

## Whole-scope accounting

| Acceptance criterion | Review disposition |
| --- | --- |
| AC1 — actual invocation, genuine sentiment and historical limits | Actual pinned invocation and authentic failure evidence retained. Bounded recovery research supports the explicit environment-specific external blocker; genuine live/full backfill remains blocked, range unknown. Documentation points do not complete this criterion. R1 and R2 are separately reachable implementation fixes. |
| AC2 — seven genuine canonical index histories | Offline replay passed for all seven source symbols. Authoritative base/release identities, citations, numeric pre-release/pre-base flags and unknown early availability are retained. Vendor pre-base沪深300 and pre-release科创综指 observations are not presented as contemporaneously public history. No additional defect found in this review. |
| AC3 — seven readable dual-scale interactive overlays | Actual embedded index arrays and isolated sample arrays match CSV; named independent axes and local Plotly/data are present. Genuine full overlays remain externally blocked. Actual offline rendering/zoom/reset/navigation is not certified here; other review owns that gate. R2 concerns eventual genuine merged-history accounting, not browser behavior. |
| AC4 — runnable commands, raw/normalized provenance, backtesting limits | Existing offline artifact is runnable and replayable. Sequential subprocess wall deadlines, scoped response capture, immutable run paths, atomic latest replacement and retained revisions are implemented. Missingness/null-versus-zero and relative-calendar caveats are explicit. Date alignment, revisions and retrospective indices are expressly not point-in-time/causal/safe-lag evidence. R1/R2 prevent unconditional acceptance of refresh/state/coverage contracts. |
| AC5 — independent convergence and final gates | Not yet converged: R1/R2 are Fix. Independent browser result and orchestrator's final-tree union gates are also still required. No final success can be inferred from this review's offline verification alone. |

## Design/security and convergence

The bounded sequential acquisition and one self-contained report remain appropriate; no scheduler, TLS bypass, fake sentiment, alternative metric, or unnecessary framework was introduced. Captured `.content` is correctly described as HTTP-decompressed application-input bytes, not socket wire bytes. Validation/replay precede atomic latest publication, and failures retain prior success identity. JSON embedded in HTML escapes `<`; visible metadata is HTML-escaped. No additional evidenced security defect found in the reviewed paths.

**Original-scope convergence verdict:** not converged until R1/R2 are fixed and independently checked, browser review returns its evidence, and final union gates pass on the final tree. Keep genuine sentiment live/full-history and full-overlay portions explicitly external-blocked under D4, rather than marking them done. No AC needs weakening, discarding or architectural replan.
