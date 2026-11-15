# Independent whole-change QVIX REVIEW-LOOP — round 1

## Decision: Fix — not converged

Baseline `c9943caf13` plus the uncommitted QVIX implementation and new real run. Four in-scope Fix findings below; no Replan request. Provider accuracy/methodology/publication/redistribution remain disclosed external limits, not repository failures and not grounds to manufacture clean success. Browser proof and final union gates belong to the other workers/orchestrator.

Reviewed AC9–12, applicable AC2/4/5, D9–11, the complete approved quality plan and plan review, implementation evidence, all four active implementation modules, removal of `sample.py`, all contract tests, README/Lessons, active schema/latest/immutable new manifest and raw/derived artifacts, and the embedded report. No production, README, ledger, acquisition/evidence edit, endpoint call, browser, subdelegate or commit. Only this review document is written.

## Findings

### Q-R1 — Fix / P1: deleting transport metadata bypasses immutable revision identity

**Locations:** `app/verify.py:119–137`, especially both `if "transport" in snap` guards.

The new-schema provenance obligations are optional according to the verifier. Removing `transport` and `transport_sha256` from a QVIX revision skips both transport verification and membership in its immutable origin manifest. This is not merely an undetected header change: a stale revision can acquire a fabricated original successful timestamp while its genuine origin manifest remains untouched.

**Observed offline probes against the real active artifacts:**

1. Deep-copy the manifest and remove those two fields from the QVIX attempt/snapshot/revision copies. `validate_manifest(data, altered)` returns successfully (`PROBE_TRANSPORT_REMOVAL_ACCEPTED`).
2. Simulate a later failed refresh in memory, preserve original artifact paths, remove the two fields from the retained QVIX snapshot/revision, change its `successful_at` to `2099-01-01T00:00:00+00:00`, and mark all attempts failed/stale. Validation again succeeds (`PROBE_FORGED_STALE_QVIX_TIME_ACCEPTED`). No disk artifact or original manifest was changed.

**Impact:** independent verification and prepublication validation do not enforce the promised original revision identity/time or mandatory new QVIX transport provenance. Tests currently allow transport-free current-schema fixture revisions, which masks this boundary.

**Required correction:** require complete transport provenance for QVIX and other newly acquired current-schema revisions; enforce origin membership regardless of which optional fields a candidate happens to contain. Any necessary handling of genuinely historical index snapshots must be identified by their verified origin contract, not by absence of a field. Reject missing provenance and forged stale timestamps in deterministic consumer-visible regression cases.

### Q-R2 — Fix / P2: calendar accounting conflates full history with the selected window and loses boundary gaps

**Locations:** `app/fetch.py:66,122–130`; `app/core.py:205–229`; duplicated derivation in `app/verify.py:78–103`.

The index comparator CSV has already been filtered to the request window, but QVIX full-response accounting compares every raw date to that selected calendar. Narrowing `--start`/`--end` therefore fabricates full-response source-only dates for ordinary earlier/later sessions and forces partial status. Full structural validation outside the window is correct; treating unexamined calendar coverage as proven source-only is not.

**Observed deterministic pinned-wrapper probe:** raw QVIX contains ordinary 2024-01-02 and 2024-01-03 observations; window is Jan 3 only; comparator contains Jan 3, exactly as the index worker's selected CSV would. Result is `partial`, `full.source_only=['2024-01-02']`, `selected.source_only=[]`. This is not a provider defect.

There is a second boundary error in the same accounting: selected gaps are bounded by the first/last *retained source row*, rather than by the requested window intersected with known full-response coverage. With source rows Jan 2/Jan 4, comparator Jan 2/Jan 3/Jan 4, and requested Jan 3–Jan 4, the full missing list correctly contains Jan 3 but the selected missing list is empty. The report consequently says zero missing source dates for a requested window containing that known hole. Both normalizer and independent verifier share this mistake, so agreement does not establish correct accounting.

**Required correction:** bind full-response calendar accounting to verifiable comparator coverage capable of supporting it; distinguish unknown/out-of-coverage from source-only. Derive selected missing dates by filtering the full in-observed-bounds gap set to the request window, including windows with no retained QVIX rows. Preserve full-response defects/nonzero policy, comparator identity/staleness, and no extrapolation. Add narrow-window and boundary-only missing-session cases; do not merely duplicate the current calculation in expected results.

### Q-R3 — Fix / P2: offline verification accepts removal of every visible index-status disclosure

**Locations:** `app/verify.py:233–253`; rendered status paragraphs at `app/chart.py:93–96`.

The verifier checks each index's status only inside the inert JSON payload. Visible HTML checking covers only three QVIX phrases/counts; it does not bind index failure/stale/unavailable state or original timestamps/ranges to the displayed per-panel disclosure.

**Observed:** baseline `verify(data, report.html)` passes. In a temporary HTML copy, remove all seven `<p>{&quot;attempt&quot;: ...}</p>` index status paragraphs while leaving JSON and QVIX summaries intact. `verify` still passes (`PROBE_VISIBLE_INDEX_STATUS_REMOVAL_ACCEPTED 7`). The same unchecked surface is the only index attempt/snapshot/stale disclosure in a failed-refresh report.

**Required correction:** independently validate the actual per-panel rendered index status disclosures and the material QVIX fresh/stale/unavailable, snapshot status/time/range and quality disclosures, not just payload status and global phrase counts. Deterministic removal/contradiction tests should fail. This finding is about the offline verification contract, not a claim that the unchanged current page is visually defective; the independent browser worker remains responsible for visual/interaction proof.

### Q-R4 — Fix / P2: full candidate provenance is needlessly multiplied into cumulative manifests and the browser

**Locations:** `app/fetch.py:82–89,131–143`; `app/chart.py:86–92`; `app/verify.py:115,162,207`.

`quality.json` correctly retains every original candidate/ordinal. The same entire per-date occurrence table is also put into `snapshot.accounting`, repeated in attempt/snapshot/revisions, retained in every later cumulative manifest, and embedded with *all historical QVIX revisions* into every report. Plotting and visible summaries use only current counts/ranges/comparator, not archived candidate tables.

**Observed current sizes:** quality sidecar about 1.1 MiB; immutable new manifest/latest about 4.5 MiB each; report about 7.5 MiB. Compact JSON measurement gives 605,808 bytes for one accounting object and 1,825,359 bytes for the current QVIX state, already containing three copies at the first revision. These measurements exclude whitespace inflation. Existing revisions are copied into each subsequent immutable run manifest, so retained metadata storage grows quadratically with refresh count; report metadata and full replay work grow with all historical revisions. This is a practical six-month refresh/browser cost, not necessary provenance.

**Required correction:** retain full candidate evidence once in each immutable sidecar, with hashes/identity references and compact accounting summaries in state; avoid serializing historical candidate tables/revision bodies into report payloads. Preserve all immutable historical evidence and independent raw-derived verification. Use the ordinary artifact-reference convention already present rather than a new persistence framework. Do not delete legitimate raw/wrapper/normalized/sidecar evidence to reduce size. Existing published historical manifests must remain untouched; adapt active representation cleanly if needed.

## Verified strengths and scope accounting

- Real active raw/wrapper/normalized/sidecar and all seven embedded arrays/status payloads pass the independent verifier. This is a replay/integrity observation, not a clean-source or historical authenticity claim.
- Targeted deterministic command: `.venv/bin/pytest -q tests/test_contracts.py -k 'real_candidates or promoted_clean_partial or atomic_and_validation or fetch_fatal_nonzero or wall_deadline'` — **5 passed, 24 deselected**, two upstream mini-racer deprecation warnings. No full suite or endpoint rerun.
- Real-data regression independently exercises 2849 raw rows/2848 dates, 2847 unambiguous dates, exact conflict ordinals2841/2843 and both complete OHLC candidates, all-four-null conflict, 13 relative gaps, four source-only dates, eight envelope rows and 14 trace nulls. These are retained-response observations, not production constants.
- Full raw parsing precedes coercive wrapper conversion/windowing; all required OHLC fields and dates are inspected across the full response. Header/row-width checks, finite numeric checks, actual wrapper/cache isolation, exact full wrapper replay, scoped response capture and bounded subprocess/request behavior are implemented. Equal-close/different-OHLC conflicts, equal duplicates, signed zero, order normalization, nullable CSV and full-versus-selected intrinsic defect counts have focused cases.
- Whole-snapshot clean→partial→fatal stale→correction semantics and no date merge, initial unavailable/nonzero, sequential eight-feed processing, captured timeout evidence and failed validation/atomic replacement preserving latest are exercised by the targeted cases. A structurally valid partial remains usable and nonzero; no requirement to retry known provider defects.
- Common QVIX arrays are bound to the original verified comparator identity/hash/staleness, including stale QVIX reuse. Seven index identities, pre-base/pre-release flags, independent right axes, source-only values and explicit disconnected conflict/missing nulls remain represented.
- Active sentiment decoder/invocation/empty workaround, revision merging and documentation-example runtime are removed; `app/sample.py` is deleted. README clearly separates historical-checkout evidence, current partial exit semantics, HTTP/TLS/hash limits, volatility versus sentiment, target mismatch, timing/look-ahead and redistribution uncertainty. No compatibility sentiment path or sample fallback was found.
- Baseline diff inspection shows no tracked modifications to earlier acquisition runs, documentation examples, research or prior reviews. The new run is separate; the ledger's observed I22 addition is orchestrator context, not an edit by this reviewer. Lessons additions are consistent with the approved contract.
- Source/JSON string escaping in chart generation avoids inserting provider-controlled text as executable markup; bundled Plotly/payload do not require external resources in the checked current report. No browser or broader security certification is asserted.

## Convergence disposition

Whole-scope implementation review is **not converged** until Q-R1–Q-R4 are corrected and independently rechecked. The real partial source observations and provider limitations are accepted as honest evidence; do not recover sentiment, choose a conflict winner, rerun known-failing endpoints, or rewrite immutable history to address these findings. Final browser interaction evidence and final applicable union gates remain separate acceptance obligations.
