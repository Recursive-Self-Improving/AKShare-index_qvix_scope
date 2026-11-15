# Independent whole-change implementation review — round 2

## Verdict: PASS — implementation/data review converged

No remaining implementation/data **Fix** or **Replan** finding. R1 and R2 are resolved against their original contracts; neither is discarded, downgraded or accepted as a risk. B1's static correction is present, but its actual visibility/non-overlap must be certified by the parallel browser reviewer. This PASS does **not** certify final browser behavior, final union gates, genuine live/full sentiment availability, or whole-goal completion.

Reviewed the uncommitted implementation and actual data/report, the original ledger AC1–5 and F1–F5, original plan review and round-two approval, sample approval, both round-one implementation findings, browser B1, correction evidence, acquisition/identity/recovery research, README, all application modules and contract tests, and dependency configuration. No production, acquisition, ledger or existing evidence edits; no commits, browser launches, repeated live sentiment failure, full-suite/install/lint reruns or delegated work. This file is the only deliverable written by this review.

## Original finding disposition

### R1 — resolved: strict observed-empty worker path

`app/fetch.py:worker` still invokes the actual pinned `ak.index_news_sentiment_scope()` and captures the consumed response before application decoding. Inspected the installed wrapper: HTTP GET with `period=YEAR`, JSON decoding, DataFrame construction/rename, then projection of the three Chinese columns. Empty `[]` reaches precisely the documented empty-frame KeyError.

The correction catches only KeyError around that invocation. Acceptance requires the wrapper's code-object traceback frame, its `data_json == []`, an empty `(0, 0)` DataFrame, the immediately following pandas DataFrame `__getitem__` frame with the exact three-column projection, the captured HTTP200, and independent strict decoding of those saved bytes to `[]`. Other exception recording remains failure recording, not exception-to-success fallback. The normal CSV/snapshot/promotion path handles the accepted empty response; a successful snapshot with count0/range null remains distinct from no successful snapshot and from numeric zero/null observations.

Independent selected regressions passed for actual pinned invocation with HTTP200 `[]`, zero, explicit null, HTTP503 `[]` and malformed JSON; arbitrary KeyError/ValueError after exact empty capture remain validation failures, and missing-body transport failure remains transport failure. Successful worker outputs also exercise actual promotion/replay. The pinned wrapper-specific compatibility clause is explicit, documented and fails closed rather than broadening acceptance when unrelated wrapper behavior changes.

### R2 — resolved: selected merged history is accounted separately

`app/core.py:histories` consistently selects latest successful index snapshots and latest-successful-by-date merged sentiment revisions. `selected_history` derives count/range, relative gaps/extra dates and comparator snapshot identity from exactly those selected rows. The chart consumes that policy, embeds selected-history metadata, and distinguishes latest-response range/count/success time from selected merged-history coverage in the warning. No successful snapshot means count null; observed empty selected history means count0. Source `market_close` is not substituted for any independently acquired index.

`app.verify:verify_accounting` independently reconstructs coverage from replayed rows rather than invoking the renderer's coverage helper. It checks all feeds, report metadata, new manifest fields, and the old manifest's original latest-response gap semantics. Snapshot count/range are separately checked against that individual response. The two-revision regression passes actual report generation and offline verification: selected October25/31 observations remain `[0.9, null, null, null, 1.1]` on October25/28/29/30/31 in every genuine trace, while the latest response remains count1/range October31. Deliberately incorrect range/count/gaps/extra dates/comparator identity are rejected for both new manifest and embedded report accounting.

An additional temporary, deterministic migration probe supplied an older two-date success followed by a genuinely empty latest revision. Legacy response-level gaps remained empty; selected merged count remained2, range October25–31, and relative gap October28. `verify_accounting` accepted these distinct meanings. Removing the older revision produced observed-empty count0/range null; removing the successful snapshot produced unknown count null/range null. No fixture was published or presented as acquired observations.

### Immutable evidence/migration — preserved

Independently observed identical SHA256 for `data/latest.json` and its retained immutable run manifest:

```text
333e7fa27f98d8b71bb8dbb928807328914f5794ab8622480fb79f79d85f8b63
```

This matches correction evidence and preserves the original run `runs/2026-11-15T20-37-20.565654+00-00-3d8f6463`. Existing v1 response-level metadata is validated under its original meaning, not rewritten to manufacture a new acquisition or success timestamp. Fresh report accounting is derived; the next genuine fetch writes the new per-feed selected-history fields. README accurately describes this clean evidence-preserving migration.

Actual sentiment state remains `transport_failure`, attempted `2026-11-15T20:37:32.340823+00:00`, zero successful revisions and no successful snapshot. The original HTTP301 body remains captured before the authenticated TLS failure; no nonexistent final TLS body is invented. Offline verification checks the captured transport hashes and all successful raw/CSV replay.

### B1 — static correction present; visual disposition reserved

`app/chart.py` reserves a top legend band with vertical legend, paper y1.18/bottom anchor, top margin200, panel height660 and bottom margin125. Index, optional genuine sentiment and full documentation-only sample labels remain distinct; no top warning, trace classification, reset, navigation, slider or drag-zoom contract was removed. The actual regenerated report was included in offline verification.

These facts establish the intended static contract, **not** readable final pixels. This review neither closes B1 visually nor accepts its former unreadability. The independent browser worker must supply the final actual-surface result, including the corrected main-plot-only sparse-gap selector.

## Whole original scope, design and security

| Original scope | Round-two review disposition |
| --- | --- |
| AC1 — actual invocation, genuine sentiment and history limits | Actual pinned invocation and authentic failure evidence retained; empty success now works without admitting arbitrary failures. Bounded recovery remains an environment-specific external blocker, not proof that history does not exist. Ten documentation rows are not live/full provider acquisition. |
| AC2 — seven daily canonical index histories | Actual saved raw/normalized histories replay successfully for all seven requested symbols. Counts are6509/5552/6030/3995/3017/1663/1663; latest observation2026-11-13. Official identity/base/release citations and pre-release/pre-base flags remain consistent with the researched contract. First vendor observation is not called inception; early unavailable intervals and reconstruction method remain unknown. |
| AC3 — seven readable dual-scale interactive charts | Actual seven embedded index/sample arrays agree with retained data; genuine trace policy and merged sparse null separators pass deterministic fixture verification. Independent per-panel ranges/axes, drag zoom, reset, selector and slider remain configured, with bundled Plotly/data and no external script/style dependency. Actual final visibility/interactions belong to the parallel browser gate. Genuine full overlays remain external-blocked. |
| AC4 — runnable acquisition/chart/provenance/backtesting interfaces | README commands match the actual CLI interfaces and pinned environment. Serial subprocess acquisition retains request and wall deadlines, current errors versus stale success identity, nonzero required-feed failure, immutable revisions and validation before atomic latest publication. Latest-response and selected-history semantics now agree across acquisition/report/verifier/docs without rewriting old evidence. Observation dates, unknown publication/revision times, retrospective indices and latest-revised histories are expressly not point-in-time tradability, safe-lag or causal evidence. |
| AC5 — independent convergence and final checks | This independent implementation/data loop converges with no new Fix/Replan. B1 final browser disposition and orchestrator's full final-tree gates remain required; this review's narrow checks do not replace them. |

The small bounded acquisition/offline-report architecture remains appropriate for six-month maintenance. Shared selection is centralized without a second merge convention; verification remains independently computed. No scheduler, replacement metric, database/framework, production TLS bypass, fabricated response or synthetic missing-data values were introduced. Requests `.content` is accurately documented as HTTP-decompressed bytes, not socket wire bytes. Exact response hashes/replay, source-symbol checks, ordered unique dates and finite numeric validation protect the published data path. The report HTML-escapes visible metadata and escapes `<` in embedded JSON. No additional evidenced security/design defect found in the reviewed interfaces.

Documentation-only samples remain separate from provider revisions: exact ten-row transcription, immutable commit/source/excerpt hashes, retained MIT copyright/permission, unknown original capture/publication/revision times and isolated markers. The ellipsis does not become231 recovered observations; source-example market closes do not replace independent 沪深300 closes. Non-independent comparator limitations and possible common omissions remain explicit, not silently accepted as complete calendar coverage.

## Independent commands and observed evidence

Executed once:

```sh
uv run pytest -q tests/test_contracts.py -k 'worker_observed_empty or arbitrary_wrapper_error or worker_transport_failure or two_revision_selected'
uv run python -m app.verify --input data --report report.html
```

Both exit0. Selected tests: **9 passed,19 deselected,2 warnings in70.63s**; warnings are the two upstream mini-racer ctypes layout deprecations, not suppressed. Actual artifact verification: all retained transport hashes, successful raw/CSV replay, immutable documentation/source transcription, response/selected-history accounting and seven embedded arrays agree. All seven relative index gap counts are0; this is not independent exchange-calendar completeness proof.

A separate read-only Python heredoc inspected installed wrapper source, retained run/attempt identities, manifest/report SHA256 and the temporary legacy/empty/unknown accounting cases described above. It made no network requests and left no script or fixture file. LSP references were attempted and returned `Unknown request: textDocument/references`; direct source/installed-wrapper inspection supplied the unavailable service's evidence.

Reviewed actual report SHA256:

```text
9545c8e93a44a83489b2db018ee071cacf7957019f9033d8b20124be294698c0
```

## Original-scope convergence conclusion

**PASS for this independent whole-change implementation/data round. R1/R2 closed; no remaining static/data Fix or Replan, no discarded finding and no accepted-risk substitute.** Overall final acceptance is not yet certified here: the parallel browser result must resolve B1 on the actual final surface, and the orchestrator must run its final union gates. Genuine live/full sentiment backfill and seven full genuine overlays remain explicitly external-blocked under D4 pending authenticated provider restoration or access to authentic authorized history. They are not successful or silently weakened acceptance criteria.
