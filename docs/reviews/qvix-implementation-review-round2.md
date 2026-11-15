# Independent whole-scope QVIX REVIEW-LOOP — round 2

## Decision: PASS

Whole-scope implementation/data/offline-contract review converges. Q-R1–Q-R4 are closed by the evidence below; no new or reopened Fix/Replan finding, accepted risk, or discarded finding. This is not final browser acceptance or an assertion that the provider delivered clean data. Final surface review and orchestrator final-tree gates remain separate obligations.

Reviewed the active AC9–12 and applicable AC2/4/5, P-Q1–3, D9–11, the complete approved quality plan and independent plan review, round1 findings, corrective evidence, current uncommitted core/fetch/chart/verifier/tests/README, active v3 derived manifest and original acquisition references, retained raw/quality evidence and report contracts. No production, ledger, acquisition, README or other evidence edits, commits, browser, endpoint requests, full-suite rerun or subdelegation. This review is the only file written.

## Q-R1 — closed: mandatory provenance and original identity/time

`app/verify.py:144–175` requires origin, transport path and transport hash for every usable snapshot, including seven indices, fresh acquisitions and stale reuse. Origin membership is tied to the observation artifact's immutable run manifest or feed result path, then its hash is checked. Exact compact original metadata equality binds the original window, status, source/version metadata and attempted/successful/finished times; transport deletion cannot disable that comparison. Transport content must match consumed-response metadata, and raw bytes/status are independently checked.

The only quality migration exception is explicit, QVIX-only and restricted to an original v2 manifest. It cannot replace source artifacts or original times. Its compact accounting is independently recomputed, not trusted through the exception. Original comparator identity/time/staleness are bound to the same original acquisition manifest. The focused regressions reject missing transport/origin and forged stale times for both QVIX and an index.

Fresh v3 result origins were additionally exercised through the actual `worker`, not only migrated v2 fixtures: see the four-refresh probe below. Every resulting usable QVIX snapshot had `origin.kind=result`, without a migration derivation.

## Q-R2 — closed: full raw comparator and selected boundary holes

`app/core.py:163–171`, `app/fetch.py:128–137` and `app/verify.py:181–200` use the exact bound comparator's retained Sina raw history. Verification checks that comparator's origin, transport, raw, selected CSV and metadata before full-history calendar replay. A later comparator refresh does not change a retained stale QVIX snapshot's calendar.

Both independent quality derivation and production normalization first derive the full in-observed-bounds hole set, then filter it by the requested window. Chart/verifier trace bounds use request intersected with full QVIX source bounds, not selected source endpoints. Focused regressions prove a one-row selected comparator CSV does not fabricate full-history extras; Jan 3–4 boundary holes and a Jan 3-only window with no retained QVIX row produce the expected explicit nulls. No extrapolation, source-only deletion or official-calendar claim was introduced. Missing comparator coverage remains unknown/partial, and stale comparator coverage remains partial.

## Q-R3 — closed: actual per-panel disclosure validation

`app/verify.py:24–72,284–326` parses the actual labelled HTML paragraphs within their matching panel sections. Index disclosures are compared independently with verified attempt/stale/snapshot status, original time, range, row/gap/retrospective accounting and identity metadata. QVIX disclosures independently bind attempt/time/request, snapshot quality/freshness/time, source and selected ranges, missing/conflict/source-only/envelope/duplicate counts and comparator identity. They are not accepted merely because inert JSON contains correct status. Duplicate, missing and directly hidden disclosure elements are rejected.

Focused fresh/stale/unavailable cases remove or contradict real paragraphs without changing payloads and are rejected. Range/time/status and material QVIX quality substitutions are covered. This proves the offline disclosure contract; it does not substitute for the separate final browser worker's visibility and interaction checks.

## Q-R4 — closed: compact current state and preserved historical audit

Full candidate/ordinal occurrences remain in the immutable quality sidecar; new result/state accounting excludes the per-date table. Active state has exactly attempt/snapshot/stale_reuse, with no cumulative revision bodies. New acquisitions link the previous immutable manifest by ordinary path/hash. Report status is current-only; historical candidates are not embedded again. Bounded repeated current artifact checks are independent of the number of archived revisions; no new history persistence framework or deletion of legitimate evidence was introduced.

The promotion/correction regression proves that correction display contains only the correction's dates while prior conflict candidates remain reachable through the archived manifest and original sidecar. Existing v2 duplicated payloads remain untouched historical evidence, not newly multiplied state.

Current observed sizes: active manifest 66,715 bytes; report 5,958,135 bytes. These are observations, not pinned behavioral requirements or claims that the bundled Plotly/trace payload is tiny.

## Migration and immutable-history proof

Independently enumerated all existing data files excluding mutable `latest.json` and the new derived directory: **73 files**. SHA256 of the sorted compact JSON path-to-SHA256 inventory is:

`4846aa155b73679259832be23064a314042fe22aa86db8344f5e02a194266106`

This exactly matches the corrective worker's documented pre-edit inventory digest. The temporary inventory file itself was no longer present; this comparison uses the persisted pre-edit digest, not a claim to have inspected that deleted file. Additionally compared all **38 tracked immutable data files** directly against HEAD bytes: **changed=[]**. The inventory digest covers the additional original QVIX acquisition artifacts as well.

The active view explicitly declares `operation=format-migration` and `derived_at`; its `previous` points to the original `21-47-32` acquisition manifest/hash. Independently compared run/window/top-level attempted_at/finished_at with that original: all equal. Every active snapshot origin names that original manifest, and offline replay checks exact source membership/times. QVIX declares only the quality-format migration; its original quality sidecar, raw/wrapper/normalized artifacts and hashes stay unchanged. Corrected calendar accounting is derived from the original retained evidence, not a new acquisition or invented historical observation.

## Whole original scope

- Actual retained pinned-wrapper response is independently replayed. The real-candidate regression checks 2849 source rows, 2848 dates, 2847 unambiguous closes; both original OHLC candidates/ordinals at the conflict; all-four-null conflict; eight envelope rows, four source-only dates, 13 relative holes and 14 trace nulls. These remain evidence observations, not production constants or clean-quality certification.
- Full GBK raw structural parsing precedes wrapper coercion/window filtering. Required date/schema/width/finite OHLC validation covers out-of-window rows; complete source-order wrapper byte replay is isolated from cache and network. Grouping uses full decoded OHLC, including equal-close/different-open conflicts and signed-zero/equal duplicates. Nullable values are not converted to zero; source-only/anomalous observed values are preserved.
- Snapshot transitions remain whole-response replacement, not date merge: clean → fresh partial → fatal stale original partial → corrected fresh whole snapshot. First failure is unavailable. Partial and failed required feeds remain nonzero. Per-source subprocess/request bounds, captured failure evidence, prepublication validation, immutable-manifest overwrite refusal and atomic active replacement remain intact. The atomic failure regression preserves the previous pointer.
- Seven genuine index histories and canonical identity/pre-base/pre-release semantics remain. Every panel uses the same QVIX union/null arrays and independent percent right axis. Source-only points and disconnected missing/conflict dates remain represented; chart interactions and offline bundled rendering remain assigned to the final browser reviewer.
- Active schema/commands are a clean QVIX cutover. No active sentiment decoder, empty-projection workaround, sample import/fallback or revision merge remains; archived evidence and historical-checkout reproduction are separated. README accurately documents commands/nonzero flow, v3 provenance, derived migration, partial/stale behavior and raw-versus-selected calendar accounting.
- Provider-controlled report strings are HTML escaped; JSON escapes `<`; no provider text is interpolated as executable code. The current chart embeds Plotly/data rather than external resource URLs. No broader adversarial security certification is asserted.
- Source accuracy, original HTTP authentication, methodology/horizon/annualization, publication/closing/revision timing, retrospective availability and redistribution authorization remain explicitly unknown/disclosed. They are external limits, not excuses for repository bugs and not evidence of clean source quality.

## Independent verification run

Narrow deterministic selection, not the orchestrator's full final suite:

```sh
.venv/bin/pytest -q tests/test_contracts.py -k 'mandatory_provenance or boundary_gaps or narrow_window or visible_disclosure or promoted_clean_partial or atomic_and_validation or actual_worker_capture_failure or real_candidates'
```

**22 passed, 23 deselected, 2 warnings in 228.18s**. Both warnings are upstream mini-racer ctypes layout deprecations. The selection includes actual retained raw/wrapper replay and real-artifact fresh/stale/unavailable report verification, in addition to correction regressions.

Additional throwaway inline probe used a temporary data root, actual `app.fetch.worker`, pinned AKShare wrappers and capture hooks. Only HTTP delivery/subprocess dispatch were replaced with deterministic retained Sina bodies and a four-date QVIX CSV; no network. It ran four complete eight-source `fetch` operations and independent `validate_manifest` after each:

| Phase | Fetch exit | QVIX attempt | Usable snapshot | Stale |
| --- | --- | --- | --- | --- |
| clean | 0 | success | success | false |
| new conflict | 1 | partial | partial | false |
| HTTP503 | 1 | failure | exact previous partial | true |
| correction | 0 | success | success | false |

The new conflict differed in open with equal close; its selected close was null. All usable origins were native v3 result references. Correction cleared stale state and replaced the whole snapshot. Temporary probe artifacts were automatically removed; no maintained test or production fixture was added.

## Convergence disposition

**Implementation/data/offline review PASS across the original full QVIX scope and all four corrective findings.** No outstanding Fix/Replan from this review. Final seven-panel surface proof and final applicable union-gate evidence must be supplied by their assigned workers before the orchestrator closes AC12; this report does not pre-claim those results.
