# Independent QVIX PLAN-REVIEW

## Decision: PASS

Approve P-Q1–P-Q3 for implementation under the complete `qvix-quality-plan.md` contract and D9–D11. No material Fix/Replan finding. This is scope/plan approval, not implementation success, full-quality acquisition, exchange-calendar completeness, or final AC9–12 acceptance.

Review basis: requested checkpoint `042d9b9ada`, active AC9–12/P-Q1–P-Q3/D9–D11 in `docs/goals/sentiment-index-history.md`, current feasibility and quality plans, retained QVIX evidence, and current fetch/core/verifier publication boundaries. The quality plan explicitly supersedes the feasibility document's earlier duplicate/order rejection proposal; that earlier proposal is not an additional implementation requirement.

**Yes: the plan permits honest usable partial delivery without fabricating values or weakening the active acceptance criteria.** AC9 validation means strict structural validation with explicit unresolved quality under D11, not certification of every provider value. Genuine retained source rows satisfy the attainable history requirement; 2000–2015 values, one disputed daily observation, and clean-data success are not manufactured. Full-quality acquisition remains unproved. Final acceptance still requires actual new acquisition, independent artifact verification, seven-panel browser proof, whole-change review, and final gates.

## Independently checked evidence

One narrow offline probe ran with `.venv/bin/python`; no network request, browser, production edit, ledger edit, or full test run. It parsed the GBK raw CSV separately, checked finite first-five-column OHLC and date groups, recomputed gaps/extras against the named retained comparator, and replayed the pinned wrapper with its cache cleared and `http.get_buffer` supplied from retained bytes. Requests and socket connection creation were disabled during replay.

Observed:

- Raw body: 928,727 bytes; SHA-256 `2e0f2edc8a6bd80cc4ec71fec22d01d933cc29af7de7b2337c406b0fea436071`; first five headers `['', '2', '3', '4', '5']`.
- 2,849 source rows, 2,848 dates, 2015-02-09–2026-11-13, unordered; 2,847 dates have one unambiguous OHLC tuple.
- Conflict on 2026-11-02: one-based data-row ordinals 2841 and 2843; tuples `(16.21,17.48,15.82,15.92)` and `(16.71,16.86,15.81,15.90)`.
- Eight source-row envelope violations; 13 relative gaps and four source-only dates exactly match `coverage.json`.
- Comparator CSV SHA-256 `e72c43dbd2b3bf97736d8be6b4d09ce4ff2ebac6432a507f0d70ff861b02d52c` for the snapshot named in `coverage.json`.
- Pinned wrapper replay matched the entire retained source-order CSV byte-for-byte: SHA-256 `31261ded64485ebbdf3620a13f8d718c25aec472d1e57536a6105480b3b6f63f`.

These observations establish reproducibility of the retained response, not economic correctness, transit authentication of the HTTP acquisition, or future availability. `result.json`'s historical `status=success` describes wrapper execution; it must not become the new snapshot's clean-quality status.

## Approval rationale

### User coverage and maintainability

The named `index_option_50etf_qvix` feed becomes one common daily-close comparison, not seven substitute feeds. Seven genuine index histories/identities remain; all panels receive identical QVIX date/value/null arrays on independent percent right axes. Local index ranges and zoom/reset/navigation remain requirements. Volatility/news-sentiment and 50ETF/other-underlying distinctions are explicit.

The clean cutover is preferable to retaining parallel sentiment/sample conventions: remove active sentiment invocation, empty-projection workaround, revision merging, sample runtime and obsolete tests; migrate fetch/chart/verify/schema/README together. Preserve historical acquisitions, evidence and archive scripts without rewriting them or adding runtime shims. Document historical-checkout reproduction. A new real eight-source run, not renamed sentiment observations, establishes the new schema. A versioned artifact contract and ordinary deterministic grouping are sufficient; no new framework is justified.

### Source quality and publication

Sorting changes order, not evidence. Grouping by full finite decoded OHLC tuple, retaining every occurrence/ordinal, and nulling all OHLC for distinct candidates avoids arbitrary first/last selection, including equal-close/different-open conflicts. Exact duplicates can collapse with notice; envelope anomalies and source-only dates retain their observed values with flags. Missing comparator sessions and conflicts become explicit disconnected nulls, never interpolation or older-revision fill.

Freshness, quality and attempt outcome are separate. The specified transitions are coherent:

| Attempt | Active usable QVIX snapshot | Refresh exit |
| --- | --- | --- |
| Structurally valid, no declared quality defects | New whole snapshot, fresh/success | Zero only if every required feed succeeds |
| Structurally valid with declared defects | New whole snapshot, fresh/partial, even after an older clean snapshot | Nonzero |
| Fatal acquisition/validation failure with prior usable snapshot | Prior whole snapshot, stale, original identity/time/quality | Nonzero |
| Fatal failure with no prior usable snapshot | Null; visibly unavailable | Nonzero |
| Manifest validation or atomic promotion failure | Prior active pointer untouched | Nonzero |

Promoting a manifest that records a failed attempt is not promoting malformed source data. A later corrected response replaces the whole snapshot; immutable earlier candidates remain evidence. The 13 gaps are relative to a named comparator, not proof of the official trading calendar; four extras must not be silently deleted as holidays. No exact methodology, publication cutoff, annualization, point-in-time availability or safe trading lag is established.

### Independent verifiability

The plan requires raw-to-wrapper byte replay plus separate raw-field derivation of grouped observations, candidate ordinals, quality sidecar, counts, ranges and calendar differences. That is stronger than comparing a renderer with its own output. Artifact hashes, immutable manifest identity, active references and embedded chart arrays/status must agree before publication. All seven traces share the same calendar union; panel-specific calendars must not silently change the common comparison series. Full-response and selected-window accounting stay separate; narrowing a view cannot clear a full-response defect.

## Residual findings and implementation acceptance checks

These are existing contract obligations or disclosed limits, not additional pre-implementation blockers:

1. **Atomic status/schema boundary.** Exercise initial failure, stale prior partial, new partial after clean, later correction, and failed promotion. Preserve original reused index identities too. Version the new schema and reject incompatible active inputs clearly rather than silently interpreting old sentiment fields. A nonzero partial refresh must still leave runnable chart/replay commands against the promoted usable run; documentation must not imply that a shell `&&` chain will continue after that exit.
2. **Calendar provenance.** Bind quality accounting to an actual verified comparator snapshot/hash and disclose stale comparator reuse. Missing/unverifiable comparator evidence cannot justify a clean completeness claim. Do not infer gaps outside observed QVIX bounds or discard source-only rows. Recompute counts rather than pinning this response's dates or totals in production.
3. **Strict parsing without source loss.** Validate the whole raw response before windowing and before coercive wrapper conversion can hide malformed rows. Accept the documented source date spelling through explicit calendar parsing, not an assumption that raw dates already are ISO. Preserve source-order raw/wrapper artifacts separately from unique-date observations; count source-row anomalies separately from conflict dates and distinct candidates. Nullable quality fields must never enter the old generic numeric reader as zero.
4. **Visible partial delivery.** Browser review must verify readable per-report/per-panel status, source/attempt timestamps, issue counts and missing-versus-conflict explanation, as well as real gaps, source-only observations, percent axes and interactions. Null points need a visible explanation even where ordinary line hover cannot target a missing point. Offline verifier success is not evidence of a clean provider response.
5. **Transport/provenance limits.** The original wrapper capture used HTTP. Recorded HTTPS byte identity and the provider's chart script are same-provider corroboration, not independent accuracy evidence or retroactive TLS. A future HTTPS override requires explicit reviewed transport provenance, as the plan states. Hash checks establish retained-byte identity only.
6. **License/distribution limits.** The [provider page](https://1.optbbs.com/s/vix.shtml?50ETF) and [same-provider evidence notes](../research/qvix-quality-evidence.txt) do not establish unconditional redistribution rights. Keep provider attribution and unknown raw/derived-data redistribution permission explicit, including for an HTML report embedding values. This does not block the requested local noncommercial experiment or require commercial authorization as a prerequisite. Do not claim public redistribution is licensed; assess actual terms before distributing artifacts.

External correction, exact methodology/timing and redistribution permission remain unresolved disclosures, not excuses to fabricate values or blockers to implementing the approved local partial-quality contract. No implementation or final gate result is claimed by this review.
