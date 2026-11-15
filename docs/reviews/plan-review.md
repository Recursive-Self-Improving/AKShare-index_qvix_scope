# Independent plan review

## Verdict: Fix before implementation; no architectural replan required

Review baseline: commit `4989b47969`, using `docs/goals/sentiment-index-history.md` and `docs/research/endpoint-feasibility.md`. Static PLAN-REVIEW only: no endpoint calls, implementation, ledger edits, browser, or commits. Runtime observations below are attributed to the feasibility report, not independently reproduced.

The bounded sequential Python + seven Sina histories + one offline Plotly HTML design is feasible and appropriate. Approve that architecture, but incorporate F1–F5 into the firm plan before implementation. No substitute sentiment, scheduler, web server, new data vendor, or strategy/backtest engine is required. Genuine ChinaScope recovery remains a separate research dependency; a changed source contract needs re-review.

A failed real AKShare invocation proves an acquisition attempt, not successful sentiment acquisition or the provider's historical limits. A seven-index artifact with a missing-sentiment warning is useful partial delivery, **not** a successful sentiment overlay. AC1 and AC3 cannot be marked fully done without real sentiment. They may reach an explicitly recorded external-blocked state under the ledger's final-gate rules after bounded recovery research concludes. This review does not close that research.

## AC coverage

| AC | Coverage and required acceptance evidence |
| --- | --- |
| 1 | Old-version actual invocation is reported; no real sentiment response yet. Persist the production attempt/version, original request and redirect outcome, UTC times, failure class and history-limit evidence. Successful acquisition must capture real response and observed dates; failure leaves range unknown, not empty or zero. Research outcome controls the external blocker. |
| 2 | Seven reported real histories support feasibility. Persist their exact raw responses, validated normalized closes, canonical source mappings, observed ranges and bounded gap classifications. Independently establish publication/base dates where possible; do not equate first returned row with inception. |
| 3 | Bundled Plotly can provide seven labelled dual-scale panels with drag zoom/reset. Requires actual offline behavioral proof. Without sentiment, seven index-only panels remain partial AC3, irrespective of successful zoom. |
| 4 | Proposed commands are not runnable yet. Deliver refresh/backfill/chart commands, pinned reproducible environment, raw/normalized schemas and provenance, explicit revision/missingness and look-ahead caveats. Full-history Sina fetch plus local date filtering is valid backfill; do not promise unsupported sentiment pagination. |
| 5 | Still prospective. Independent whole-change review, actual acquisition/artifact checks, gated browser proof and final-tree project gates must converge. A valid sentiment blocker does not excuse checks for reachable index/chart work. |

## Findings

### F1 — Fix: define the missing/stale sentiment contract and process result

The plan correctly rejects fabricated values but leaves machine-readable status and stale-snapshot behavior unspecified. Make these acceptance requirements:

- Each run manifest distinguishes acquisition success, transport/provider failure, validation failure, and reuse of a prior valid snapshot. Record attempted retrieval separately from the last successful snapshot retrieval.
- Missing sentiment is represented by explicit status and no synthetic observations, not a zero-valued trace or an apparently valid empty historical dataset. A successful response containing no observations is a distinct observed outcome; preserve it without claiming all history is absent.
- A preserved older snapshot remains identifiable as stale; never relabel it with the latest failed-attempt timestamp. An old successful run must not conceal today's error.
- HTML prominently states sentiment availability, observation range if known, snapshot retrieval time, and partial-overlay status. If genuine sentiment exists only over a short range, do not imply coverage back to 2000.
- Document exit behavior. Recommended: acquisition returns nonzero when a required feed fails while retaining its run manifest and any valid acquired data; chart generation may successfully render that explicitly partial run. No blanket swallowing of acquisition failure to obtain a green gate.

### F2 — Fix: make bounded, raw-preserving acquisition executable as a contract

Requests connect/read timeouts alone are not a total deadline: a trickling response can continue indefinitely. Use finite request timeouts plus a finite command/worker wall-clock deadline, with no unbounded retry. Seven requests remain sequential; any throttling is explicit and finite.

Capture the response consumed by the decoder/AKShare wrapper, not an unrelated second successful request. A scoped transport hook or worker can preserve the consumed response and restore global state afterward. The sentiment requirement still includes actually invoking `index_news_sentiment_scope()`; a direct endpoint request alone does not meet it.

Define “raw bytes” precisely: preserve the HTTP response-body bytes before application-level Sina decoding or JSON parsing, with headers/content encoding and whether HTTP decompression occurred. Do not claim socket-level wire fidelity for `requests.Response.content`. Hash the exact persisted bytes, and decode those bytes. Record requested URL/query, final URL/redirects, HTTP status/content type, source, pinned AKShare/decoder and dependency versions, UTC retrieval, requested window and observed range. Preserve full fetched history even when normalized output is filtered since 2000.

Promote only validated artifacts through a manifest referencing immutable snapshot paths/hashes; a failed or interrupted refresh must not expose mismatched raw/CSV/metadata or destroy the last valid snapshot. Reject HTML/provider error pages, malformed dates, duplicate keys, nonfinite/non-numeric closes and invalid date ordering before promotion. Keep this small; no database or general ingestion framework is needed.

### F3 — Fix: specify date gaps and offline chart interaction precisely

`connectgaps=False` alone does not preserve missing observations when absent dates simply never appear in a sparse trace. Explicit null separators are needed across known missing trading observations. Do not fill weekends/holidays as observations or silently interpolate. Unavailable sentiment outside its observed range must remain absent. A relative comparison against 上证指数 detects only relative gaps; label common omissions and an unverified calendar as unknown, not complete official coverage.

For every panel, require readable title/name/code, date x-axis, named index-close and sentiment axes, actual independent y-scales, and visible missing-sentiment status when relevant. Specify whether the seven time ranges are linked or independent; either is acceptable if reset/navigation is usable and documented. Select drag mode `zoom` explicitly, retain modebar reset and date navigation, and verify the chosen implementation on actual panels. Chinese labels must remain legible.

Keep one self-contained HTML with Plotly JS once and embedded data; no CDN, local companion file or runtime fetch. The absence of a real sentiment series must not prevent verifying seven index panels, offline operation and zoom, but it prevents calling the result seven real overlays.

### F4 — Fix: complete provenance and point-in-time limitations

The report's source/code mappings and 科创综指 launch evidence are a good start, not provenance for all seven inception dates. Persist authoritative name/code and available base/public-release evidence per index, with citations and explicit unknowns. Mark known pre-release rows as retrospective; do not label them pre-inception simply because public launch came later. Avoid asserting all unmatched early intervals are unavailable market history.

Store sentiment `tradeDate` as an observation date, not publication timestamp. Preserve source `marketClose` separately from independently fetched 沪深300 close; do not use it to fill, reconcile or silently replace index data. If snapshots revise an existing sentiment date, retain both source versions and choose an explicit deterministic chart policy; a merged latest-revised series is not point-in-time backtest data.

Documentation must say that index back-calculation, unknown sentiment publication times, revisions, and retrieval-time availability prevent a verified historical tradability claim. Date alignment does not prove same-day availability, predictive value or causality. Any example lag must be labelled an assumption, not an established safe one. This task need not reconstruct publication timestamps or implement a backtest.

### F5 — Fix: turn verification intentions into concrete gates

No application or project gate configuration exists in the reviewed tree. Establish the following narrow gates alongside implementation; the module names below follow the proposed interface, not existing runnable commands. Freeze the actual commands in README/ledger before declaring a green checkpoint.

1. **Environment/static gate:** commit dependency pins/lock and a supported Python version; install from that lock (for uv, `uv sync --frozen`), then `uv run python -m compileall -q app` and `uv run ruff check .` with pinned Ruff/config. Add a typecheck command only if the implemented project adopts one; do not report a nonexistent typecheck/build as passed.
2. **Contract/regression gate:** `uv run pytest -q` for the implemented project. Keep tests deterministic and network-free. Cover plausible consumer-visible failures: malformed/provider-HTML response rejected without replacing prior success, interrupted promotion, duplicate/nonfinite records, explicit missing sentiment versus zero, stale snapshot identity, revision conflict policy, and sparse-date gaps. Test only contracts actually implemented; no source-text, wiring-only or wording assertions. Add tests for uncertain edges rather than broad speculative suites.
3. **Real-data acceptance:** run the documented refresh/backfill command from `2000-01-01` through the actual retrieval date once with real transport. Persist seven successes or specific errors plus the real old-AKShare sentiment invocation result. Verify hashes, raw-to-normalized replay without network, requested versus observed ranges/counts, unique ordered dates, finite closes and canonical symbols. Distinguish dates before publication, unavailable intervals and the non-independent calendar limitation. Do not freeze the spike's latest row/count as a future exact expectation. If required sentiment fails, retain the nonzero result and explicit blocker rather than redefining full acquisition as passing.
4. **Artifact acceptance:** run the documented chart command against that run's manifest. Independently compare all seven embedded index traces and any real sentiment trace to normalized records, including dates/nulls and their respective axes. This checks actual artifact data, not just HTML string counts. Missing-feed state must survive a fresh chart build and be readable in the file.
5. **Behavioral/offline gate:** a single gated browser, one worker, opens the generated `file://` HTML with network blocked. Assert seven rendered labelled panels and readable axes, no external resource dependency, drag-zoom narrowing the x range on each panel (or proving the documented linked behavior), navigation and reset restoring the original range. Check sparse-gap behavior using a throwaway fixture if real data has no gap; never present that fixture as acquired data. Capture the observed ranges/screenshots or equivalent review evidence. This proves interaction, not genuine overlays when sentiment is absent.
6. **Final gate:** independent whole-change review resolves every Fix/Replan finding; rerun applicable static/tests and actual final-artifact/browser gates after the last relevant change on the final tree. Ledger separately records completed ACs and exact external-blocked portions of AC1/AC3, research conclusion, decisions and evidence. Do not declare full-overlay success merely because all code checks pass.

For browser/heavy verification: first `free -m` and `~/.omp/bin/heavy-gate --status`; launch through `~/.omp/bin/heavy-gate [-n N] [-m 6G] -- command`, with finite gated bash calls `async:true, timeout:0` and no timeout wrapper. Use at most one browser/worker, close it in `finally`, and stop if isolation is unavailable. Eval browser attachment must use explicit `app.cdp_url` for that owned gated browser or `app.relay:true` for an existing user browser, with `app` first. No browser was needed for this review.

## Replan triggers and handoff

- Recovery worker finds genuine same-source data or a supported archive: re-review acquisition, authenticity, date coverage, revisions and raw-capture contract before adopting it. Do not infer `ALL`/`MAX` support from attempted URLs.
- A proposed replacement sentiment metric, disabled TLS verification, or a claimed full completion with index-only panels requires replan; none is approved here.
- If recovery yields no accessible genuine response, record bounded attempts and the external dependency precisely. “Provider unavailable from this environment; range unknown” is valid; “no history exists” is not supported. Finish all reachable index, documentation and partial-artifact work.

**Handoff:** safe to implement the bounded architecture once F1–F5 are incorporated into the firm plan. Sentiment recovery remains open; this is not PASS for the current underspecified plan or for final AC completion.
