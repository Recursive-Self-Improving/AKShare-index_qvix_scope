# Matched-QVIX independent implementation review — round 1

## Disposition: FINDINGS — two Fix items

Reviewed the whole delivered implementation against baseline `a18afebada`, active AC13–16, the complete approved `docs/research/matched-qvix-plan.md` including F1–F3, and `matched-qvix-plan-review-round2.md`. No economic-methodology certification. Source partial quality is intentional, disclosed and not itself a finding. Browser acceptance belongs to the separate surface reviewer.

### M-R1 — P2 / Fix: incomplete native completion timestamps pass recovery and promotion

**Locations:** `app/verify.py:277–305,324–345`, `app/fetch.py:191–220,224–233`.

Native v4 snapshot validation compares the snapshot with its own immutable `result.json`, but does not require `successful_at` or `finished_at`. Invocation equality binds the invocation fields only; the invocation does not contain these completion fields. Thus a completion record missing both fields still passes independent recovery as fresh partial and passes `promote`, replacing the active pointer. Rendering then raises `KeyError: 'successful_at'`. Hash equality with the incomplete origin is not validation of its required fields.

**Offline reproduction:** the retained probe runs the real pinned seven wrappers with injected one-row HTTP evidence, deletes only those two fields from the disposable 50ETF `result.json`, then calls `recover_group`, builds a manifest from those recovered results and calls `promote` and `build`. Observed:

```text
missing_times_recovery: partial {'attempted_at': True, 'successful_at': False, 'finished_at': False}
missing_times_promotion: ACCEPTED
missing_times_chart: KeyError 'successful_at'
```

**Risk:** violates mandatory original times and F3 rejection of incomplete completion records; an invalid completed member can destroy chart availability after otherwise successful promotion. This is a validator acceptance defect, not evidence that the delivered production timestamps are currently missing.

**Required correction:** validate mandatory native completion fields and usable timestamp values before treating the result as complete; retain original identity/time checks. Incomplete records must become feed-local failure/own-prior stale during recovery, and direct promotion must reject them. Add a regression at the immutable native result boundary, not just mutation of a manifest against an unchanged origin. Exercise required times for native snapshots and preserve the stricter original-time checks on the derived-v3 lineage path.

### M-R2 — P2 / Fix: hidden ancestor defeats visible per-feed disclosure verification

**Location:** `app/verify.py:37–48,57–72,395–398`.

`Embedded` rejects `hidden`/`style` directly on a disclosure paragraph or section, but does not track hidden ancestors. Wrapping the entire unmodified 300股指 paragraph in `<div hidden>…</div>` hides that feed's material warning while preserving the expected text, IDs, arrays and JSON. `verify` still reports success.

**Offline reproduction:** the retained probe modifies only the disposable report copy around `qvix-status-sh000300-qvix_300index`. Observed:

```text
Offline verification passed: eight panels, seven raw/wrapper/artifact/quality replays
hidden_ancestor_verification: ACCEPTED
```

**Risk:** one feed's warning can disappear while its sibling remains visible, and the independent acceptance gate falsely certifies visible disclosure. This contradicts the explicit hidden-disclosure/per-feed tamper contract. No browser is needed to establish the standard HTML `hidden` ancestor behavior.

**Required correction:** bind disclosure visibility to its ancestor context, conservatively rejecting hidden/style-bearing or otherwise disallowed containers on the disclosure path. Cover hidden ancestor wrappers as well as direct paragraph hiding, removal and text contradictions. Do not weaken per-feed exact text/section binding.

## Whole-change coverage and positive evidence

- Inspected `core`, `fetch`, `chart`, `verify`, identities, README, regression implementation and relevant baseline changes. Exact registry/order/mappings match AC14; panels 1, 2 and 4 have three traces. The new active report independently replays all eight index histories and seven QVIX artifacts/quality/arrays. Observed index counts: 6509/5552/5053/6030/3995/3017/1663/1663; latest observation 2026-11-13. No invented early history identified.
- All **213** pre-edit inventory entries passed `sha256sum -c docs/matched-qvix-pre-edit.sha256` (exit 0). Ledger changes relative to the baseline were treated as orchestrator-owned, not attributed to the sole implementer. No historical evidence was rewritten by this review.
- Native v4: inspected shared body/transport/config/member/origin membership, actual invocation and cache boundary, global versus feed-local failure handling, durable sibling commit ordering, timeout/crash recovery, fresh partial/no-close replacement and own-feed fatal stale semantics. Separate offline native transition probe ran populated partial → shared failure/own prior stale → fresh blank/no-close replacement → corrected fresh partial for all seven feeds. No comparator in that synthetic probe intentionally means partial rather than clean success.
- Derived v3 lineage: inspected the explicit v4 migration manifest, migrated 50ETF result/shared evidence and original source reference; its original acquisition times/body/transport/wrapper remain bound separately from derivation time. The selected migration regression independently ran `validate_manifest` on the actual derived view and checked original times/artifact preservation. Active v3 rejection remains explicit; no runtime single-feed compatibility path was found.
- Accounting: inspected the independent raw implementation and production algorithm for full-raw versus selected calendars, the F2 oracle, absent/blank/conflict/invalid-close/missing-close partition, source-only nulls, all-blank/no-source bounds, invalid-token identity, zero preservation, full-tuple/equal-close conflicts and blank collisions. Focused deterministic regressions passed; no additional arithmetic defect established.
- README distinguishes proxies and methodology/timing/HTTP/licensing limits, partial versus fatal, shared 45-second deadline, immutable migrations and offline replay. Static layout inspection shows existing cards/CSS/navigation/Plotly controls retained with extended traces/disclosures and a legend-position adjustment. This is not visual or interaction acceptance.

## Verification actually run

1. Immutable inventory check: exit 0, 213 `OK` lines.
2. `.venv/bin/python -m app.verify --input data --report report.html`: exit 0; actual delivered eight panels and all seven raw/wrapper/artifact/quality replays passed.
3. Focused existing contracts:

```sh
.venv/bin/python -m pytest -q tests/test_contracts.py -k 'f2_exact or fresh_no_close or full_history or hole_partition or invalid_nonclose or duplicates_full or shared_loader or wrapper_local or completed_sibling or global_failure or member_nonfinite or recovery_rejects or mandatory_provenance or stale_comparator or durable_no_close or member_commit or explicit_derived or fetch_narrow or durable_artifact'
```

Observed **40 passed, 21 deselected**, two upstream mini-racer deprecation warnings, exit 0. These cover plausible value/state/consumer-visible regressions, but timestamp mutations against unchanged origin hashes do not cover M-R1; direct paragraph hiding does not cover M-R2. A full 61-test gate was claimed by implementation, not rerun or independently claimed here.

4. `PYTHONPATH=. .venv/bin/python docs/reviews/matched-qvix-implementation-evidence-round1/probe.py`: exit 0; findings and native transitions reproduced. Retained `probe-output.txt` records exact output. Generated data/report copies were removed; only the minimal reproduction script and output are retained. A final script-only cleanup addition removes its generated evidence after future runs.
5. LSP references were attempted for `validate_snapshot`; server returned `Unknown request: textDocument/references`. Review continued by direct source inspection; no production refactor was performed.

Only this review and its disjoint minimal evidence directory were written. No endpoint calls, browser, production/data/report/ledger edits, commit or subdelegation. **Not PASS: M-R1 and M-R2 require correction and independent re-review.**
