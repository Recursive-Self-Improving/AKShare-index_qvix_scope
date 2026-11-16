# Matched-QVIX independent PLAN-REVIEW

## Disposition: Fix before implementation

Reviewed active AC13–16, P-M1–3 and D13–14 in `docs/goals/sentiment-index-history.md`, the complete `docs/research/matched-qvix-plan.md`, its linked local evidence, installed AKShare 1.20.53 wrappers, current v3 acquisition/normalization/provenance/verifier code, existing regression scenarios, and the layout introduced by `9cb3397`.

The architecture and substantive invalid-cell policy are defensible. The plan is **not yet complete enough to approve**: resolve F1–F4 below. No Replan or Ask finding; no unavailable economic methodology is being demanded as a code gate. These are plan/evidence corrections, not authorization to change production during this review.

Only this review document was written. No production, ledger, data or report edits; no commit, subdelegation, browser or network calls. Offline investigation commands exited successfully; no production test suite or browser acceptance is claimed.

## Independent evidence replay

Executed `.venv/bin/python` heredoc checks using the retained bodies, Python CSV parsing, full raw Sina comparator replay and actual installed AKShare calls. Network was blocked during wrapper/decoder execution by patching Requests session requests and socket connection creation to raise. The replay supplied the captured bytes through AKShare's buffer/response interfaces; it was not a new acquisition.

Verified:

- AKShare version `1.20.53`; common body **928727 bytes**, SHA-256 `2e0f2edc8a6bd80cc4ec71fec22d01d933cc29af7de7b2337c406b0fea436071`.
- Common raw CSV: **2849 source rows, 87 columns**, consistent widths and valid source dates across the entire response.
- Archive SHA-256 `45e1e5761bd5ec8e5fec185590cc92ca9f037a6b6f64f56e7ce7ebea7cc57a77`.
- All seven actual pinned wrappers returned byte-identical CSVs to their archived outputs and matched their recorded hashes. A cleared shared cache required **exactly one** `get_buffer` load across all seven calls, not seven separately supplied responses.
- Installed positional selections exactly match the proposed date/O/H/L/C mapping: 50index `[0,79,80,81,82]`; 50etf `[0,1,2,3,4]`; 100etf `[0,75,76,77,78]`; 300index `[0,17,18,19,20]`; 300etf `[0,9,10,11,12]`; cyb `[0,71,72,73,74]`; kcb `[0,83,84,85,86]`.
- Independently classified every selected raw cell as empty, finite numeric or invalid nonempty token; compared every wrapper date/field in source order. Finite values agreed within the existing numeric tolerance; raw empty/invalid cells corresponded to empty wrapper CSV fields. Wrapper emptiness alone cannot distinguish their provenance.
- Independently reproduced complete-finite row/date counts, complete-case ranges, every recorded conflict tuple and ordinal, envelope counts, invalid-token frequency maps, and every complete-case missing/extra date list.
- Calendar replay used complete retained raw Sina bodies, not filtered normalized CSVs. Verified the retained origin manifest hash `c99274d7755b8b3a0e3ca9dc55e312fd771bcb7eb8333eabc994e0cfebb55d66` and raw hashes before replay for sh000001, sh000300, sz399006 and sh000688. The 100etf comparator used the separately replayed scratch sz399330 body.
- sz399330 body SHA-256 `f717c0e02f2712784c98c00a21aab40f612746e1ec3cc6d97b35d261db4ed6a6`; actual offline Sina wrapper replay reproduced the archived CSV byte-for-byte and its hash `cc797110c2effcbf1eb2b27cb1cff8659b6d9435e6d640d0863c877f11fa80ca`: **5053 rows, 2006-01-24–2026-11-13**. This verifies vendor observations, not official inception or official-calendar completeness.

### Arithmetic cross-check

“Finite close rows” includes source duplicates and zero. “Unambiguous close dates” below applies the proposed full-tuple policy to all nonblank candidates, including invalid-token identity, then counts dates retaining a finite close. It is review-derived arithmetic, not a v4 artifact or a clean-quality claim.

| Feed | Complete finite rows / dates | Envelope rows | Complete-case relative holes / extras | Finite close rows | Zero close rows | Unambiguous close dates |
|---|---:|---:|---:|---:|---:|---:|
| 50index | 722 / 722 | 13 | 100 / 0 | 753 | 33 | 753 |
| 50etf | 2849 / 2848 | 8 | 13 / 4 | 2849 | 0 | 2847 |
| 100etf | 938 / 937 | 4 | 17 / 4 | 942 | 0 | 940 |
| 300index | 1447 / 1447 | 24 | 110 / 0 | 1482 | 42 | 1482 |
| 300etf | 1658 / 1657 | 13 | 17 / 4 | 1661 | 0 | 1659 |
| cyb | 997 / 996 | 2 | 13 / 4 | 997 | 0 | 995 |
| kcb | 824 / 823 | 6 | 16 / 4 | 827 | 1 | 825 |

The research's complete-case table is correct **under its stated definition**; its gap counts must not become v4 daily-close gap counts. `sparse-summary.json` uses a different `complete` category (all selected cells populated, including invalid tokens), e.g. 927 for 50index versus 722 finite-complete rows. Define/rename that category in active accounting rather than copy its label as finite-valid.

Verified invalid tokens: 50index `#VALUE!`33, `#DIV/0!`24, `#NUM!`2, `#NAME?`728; 300index `#VALUE!`63, `#N/A`8, `#DIV/0!`26, `#NAME?`722; 100etf `#NUM!`8; 300etf `#VALUE!`4, `#NUM!`4 and `22。27`1; kcb `#NUM!`6. 50etf/cyb have none. These are field-token counts, not affected-date counts.

The five finite-complete duplicate conflicts are all 2026-11-02 at raw ordinals 2841/2843. All four normalized fields must remain null, including any equal-close/different-other-field future case. For 50index/300index there are respectively **174/179 nonblank rows without a finite close**. Their final raw 2026-11-13 tuples are `[#NAME?, #NAME?, #NAME?, 0]`: zero is a raw finite close, not evidence of economic validity. All seven feeds' nonempty bounds extend to 2026-11-13; the two index feeds' last complete tuple on 2026-05-29 is not their source end. This evidence materially supports D14's policy rather than blanket all-feed rejection.

## Accepted design and goal coverage

- **AC13:** real sz399330 raw/CSV replay and earliest returned coverage are established. The compiler factsheet citation distinguishes 399330 from 399004; primary-document inspection remains limited as described in F4. No interpolation/backfill to 2000 or to the 2002 base is permitted. Production acquisition must request 2000-to-current/retain earliest genuinely returned history and preserve independent pre-base/pre-release flags.
- **AC14:** exact eight-panel order and mappings are correct: 上证指数→50index+50etf; 上证50→50index+50etf; 深证100→100etf; 沪深300→300index+300etf; 创业板指→cyb; 创业板50→cyb; 科创综指→kcb; 科创50→kcb. The first, second and fourth panels require **three traces**, not two replacement QVIX-only traces. One left-axis index and two distinguishable, separately toggleable right-axis percent traces is feasible with current Plotly controls. Sharing a feed means identical arrays across its panels, not recomputation against the local index calendar.
- **AC15:** seven actual pinned wrappers and one shared body/cache are established. Preserve full raw response and per-feed selected columns, wrapper bytes, invalid spellings/ordinals, source-only dates, full and selected accounting, and honest nonzero partial/failure. The distinct fixed comparator registry is coherent; relative gaps are not official-calendar completeness.
- **AC16:** clean v4 cutover is feasible. `app/core.py` currently hardcodes the lone feed and sh000001 comparator; `app/fetch.py` assumes eight sequential sources and one result per worker; `app/chart.py` assumes one QVIX badge/card/trace; `app/verify.py` binds one QVIX origin and one comparator. These must migrate together, not gain runtime compatibility branches.
- Current immutable-origin/time verification and full-raw comparator checks are valuable contracts to retain, not obstacles to the new registry. A derived v4 view may reference original verified v3/v2 acquisition lineage and rederive new artifacts without changing any original acquisition time or pretending its derivation is a fetch. A fresh v4 failure should still be able to retain the prior 50etf snapshot if explicit migration has made it available; new feeds have no fabricated prior success.
- `9cb3397`'s card layout, dark/light CSS, navigation, metadata, reset, slider/range controls and offline Plotly bundle should remain. Labels, trace-specific disclosures and summary contents necessarily change. Extend the current layout rather than replace it. Three-item legends and multiple local warnings need final real-browser proof; static review cannot certify overlap or interaction behavior.
- Body/transport once per group, one per-feed quality sidecar, compact state and hashed previous reference avoid the prior candidate/history multiplication. Do not embed all raw candidates or recursively expanded previous manifests in eight-panel payloads. Repeating trace arrays for panels sharing a feed is a rendering requirement, not justification to duplicate immutable raw bodies.

### D14 policy judgment

**Honest if implemented as proposed, with F1/F2 made deterministic.** Raw blanks, explicit error strings and finite values remain different evidence classes. Preserving an independently finite close beside an invalid open/high/low does not certify the OHLC tuple: it retains a source value with explicit partial quality. It neither silently coerces an error to clean missingness nor repairs `22。27`. Raw spelling/field/ordinal, row-by-row wrapper comparison and full-response validation prevent pandas coercion from becoming the definition of truth. Numeric NaN/infinity remain fatal; malformed nonempty nonnumeric strings remain explicit source-invalid cells. Conflict comparison must preserve missing-versus-invalid and invalid-token identity and still null the entire distinct tuple. Zero must remain visibly flagged, not silently treated as a sentinel.

This is a substantive declared quality-policy change, not proof of correct economic methodology. No exact contract selection, tenor, annualization, publication/revision timing, transport authentication or redistribution permission has been established. Existing proxy, HTTP, retrospective-history and licensing limitations are correctly explicit. None requires inventing an alternative feed or blocking mechanical verification on unavailable provider methodology.

## Findings

### F1 — Fix: deterministic no-close state transitions are missing

**Location:** proposed contract §4 “unavailable/partial as appropriate” and §5 “optional whole usable immutable snapshot”.

Those phrases do not determine whether a newly acquired all-error or all-blank feed replaces an old usable snapshot, becomes a fatal/stale attempt, or is retained only as evidence. They also do not separate globally no finite close, no unambiguous close after conflicts, and a selected window with no closes despite usable full history. Different implementations would pass the prose while displaying different dates and different stale values.

**Required plan correction:** specify a state table for all-blank full feed; nonblank all-error/all-conflict full feed; usable full history but empty/all-null selected window; and ordinary partial-with-close. State attempt status, retained snapshot/evidence, stale flag, visible availability/ranges and process exit in each case, with and without prior success. Recommended safe contract: structurally valid fresh evidence is nonfatal; persist its whole partial snapshot even when the close trace is unavailable, do not silently reuse prior prices, and reserve stale fallback for fatal acquisition/validation failures. No-close selected windows must not erase full-history bounds or masquerade as acquisition failures. An all-blank required feed must not become a clean successful acquisition merely because no quality group exists. Explicitly distinguish snapshot availability from close availability.

**Acceptance:** deterministic fixtures exercising these rows and previous-success replacement; verify actual normalized rows, stale state, null/empty traces and visible full/selected ranges. Do not merely assert the state helper echoes a supplied status.

### F2 — Fix: blank-tail and close-gap accounting still lack exact bounds/trace rules

**Location:** proposed contract §4 and the acceptance bullet listing all-empty prefix/internal/tail.

Bounds from nonempty selected raw fields are appropriate for observed source bounds and prevent treating error tails as absent history. But “pre-history all-empty fields alone are not defects” plus “internal empty observation” leaves an all-empty suffix unspecified: it falls outside those bounds and can disappear from missing-date counts and the plot. Known blank source-only dates can also disappear if null insertion uses only comparator sessions. Likewise an all-error/nonfinite-close observation is present in the group map but absent as a usable close; “relative gaps” alone does not specify which category counts it. The seven real feeds have no all-empty suffix after their last nonempty date, so successful real replay will not expose this ambiguity.

**Required plan correction:** separately define common-response date bounds, nonempty-feed source bounds, usable-close bounds, leading/internal/trailing blank rows/dates, absent comparator sessions, and observed blank/invalid/conflict close dates. State exact full/selected formulas and overlap rules. Count/disclose trailing blanks without claiming they are observed closes or automatically extending source coverage to the request end. No extrapolation or inferred post-history official-calendar holes. Preserve explicit null separators for known internal blank/error dates, including source-only dates and absent/stale-comparator cases; do not rely solely on the comparator union. Explain trailing close unavailability even if bounds exclude it. Keep all-error tail dates and finite zero closes distinct. Selected holes must be the full, appropriately bounded set filtered to the window, including windows with no source candidates.

**Acceptance:** independent expected arrays/counts for blank suffix, internal blank non-session date, no comparator, error-only tail, allblank/no-close feed and an all-null selected window. A test-name list without these definitions does not settle the contract.

### F3 — Fix: one shared worker needs explicit cached-failure/deadline persistence semantics

**Location:** proposed contract §2 versus current `app/fetch.py:118–125` subprocess failure handling.

Successful caching is proven. Failure caching is not: `lru_cache` does not cache loader exceptions. Blindly continuing to invoke all wrappers after an initial transport/cache-load failure can refetch the same endpoint, contrary to “one captured response”, “no retries” and AC15. Current timeout recovery retrieves transport only and synthesizes a failed worker result; moved unchanged to one seven-feed worker, it cannot preserve completed sibling outputs when a later wrapper hangs. The plan requires sibling isolation but does not define this terminal group case.

**Required plan correction:** define a group result protocol with durable per-feed completion and shared transport identity. A shared load/transport failure must stop further loader calls; record remaining feeds as failed due to that shared failure, with honest invoked/not-invoked/error metadata, not seven claimed wrapper executions. Distinguish globally fatal encoding/CSV width/date failures from feed-local positional schema/conversion/wrapper failures. Flush completed per-feed results before the next call. Specify recovery after group wall timeout/nonzero process exit: retain independently validated completed sibling artifacts, fail unfinished feeds and use only their own prior snapshots. Alternatively explicitly replan the isolation boundary; do not silently lose successful siblings. Promotion remains one validated atomic active-pointer change, and a failed promotion leaves the prior pointer intact while retaining immutable attempted evidence.

**Acceptance:** one loader-call count on shared failure, wrapper-local exception with later successful sibling, and timeout after at least one completed sibling, plus provenance rejection for cross-bound member/body substitution. Use deterministic injection; do not perform repeat real fetches for these tests.

### F4 — Fix: primary identity assertion is linked but not independently inspectable offline

**Location:** identity paragraph and linked `matched-qvix-evidence/` contents.

The plan cites the compiler's [399330 factsheet](https://www.cnindex.com.cn/html2pdf/preview/jj_399330.pdf) for base 2002-12-31, release 2006-01-24, base 1000 and the distinct 399004 return index. The retained evidence set contains wrapper/transport/quality artifacts, but no factsheet body or source excerpt. A bounded local search also found no cached matching PDF. Under this review's explicit no-network constraint I can verify the cited primary URL and vendor history, **not independently verify the primary document's contents**. The matching vendor first date is not independent authority for release/base dates. This is not a finding that those dates are wrong.

**Required evidence correction:** retain an inspectable compiler-source document or exact primary excerpt with source URL, relevant page/text and retrieval identity/hash; then independently verify code/name, base/release and the 399004 distinction. If the source capture cannot be obtained, record that specific external evidence limit rather than mark independently verified identity. Do not infer 399330 release from the family anniversary or require unavailable methodology. No new product decision is needed.

## Implementation verification obligations after fixes

The existing test file already covers whole-snapshot replacement, exact duplicates/equal-close conflicts, fatal capture, cache isolation, atomic validation/pointer failure, immutable origin/time tampering, narrow windows/full comparator replay and visible disclosure removal/contradiction. Preserve their consumer contracts, replacing obsolete single-QVIX assumptions rather than freezing old implementation wording. LSP document-symbol lookup was unavailable (`textDocument/documentSymbol` unsupported); test scenario declarations were inspected directly. No language-server refactor or production edit was attempted.

New uncertainty is concentrated in seven-column selection and one-cache group failure/deadline behavior, raw blank/invalid classification and tuple identity, no-close/blank-tail rules, original v3 lineage into v4, and mixed per-feed stale/fresh/unavailable panels. Use small network-free raw fixtures and actual pinned wrapper replay with independently computed expected values, not `chart` or normalization output as the verifier's oracle. Revalidate visible disclosure tampering per feed so a clean sibling cannot conceal another feed's partial or stale state. Include malformed schema/date/width/nonfinite values outside the requested window as fatal cases and clean→partial→fatal/stale→corrected whole-feed transitions.

After plan corrections: sole implementation writer; one bounded real acquisition (not seeking cleaner data); independent raw/artifact/HTML review; one gated offline eight-panel browser stage exercising three-trace legend toggles, all panel zoom/reset/slider/range interactions, per-feed disclosures and gaps; final applicable gates after final evidence files; preserve all historical artifacts and original times. This review supplies evidence and concrete fixes, not implementation acceptance or a ledger update.
