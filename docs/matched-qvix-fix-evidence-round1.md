# Matched-QVIX implementation fixes — round 1

Implementation evidence for M-R1/M-R2 from `docs/reviews/matched-qvix-implementation-review-round1.md`, plus F-B1 added from `docs/reviews/matched-qvix-browser-review-round1.md`. Active AC13–16 and the approved matched-QVIX plan remain controlling. This is not independent acceptance or a browser re-review.

## Changed paths in this corrective slice

- `app/verify.py`: validate required original timestamps before accepting an immutable snapshot; track HTML ancestor context and restrict disclosure containers.
- `tests/test_contracts.py`: native immutable-result mutations, local recovery/stale/unavailable outcomes, pointer/chart availability, shared original times, derived-v3 original-time rejection, and disclosure ancestor/content tampering.
- `app/chart.py`: left-anchor the horizontal legend at its existing height instead of right-anchoring it. No controls removed or CSS redesigned.
- `report.html`: regenerated exactly once after F-B1; only eight embedded legend anchors changed.
- `README.md`: permanent completion-time, disclosure-container and legend-position contracts; separate browser acceptance remains explicit.
- `AGENTS.md`: reusable immutable-completion/ancestor-visibility lesson.
- `docs/matched-qvix-fix-evidence-round1.md`: this evidence.

No `app/fetch.py` change was needed: recovery already converts independent validation exceptions into feed-local failure, `state_after` already selects only that feed's prior snapshot, and promotion already validates before replacing the pointer. No ledger, production data, historical evidence/review, dependency or lock changes; no endpoint calls, browser launches, subdelegation, commit or push.

## M-R1 — original timestamp boundary

`validate_snapshot` reads and hash-verifies the immutable origin, then requires original `attempted_at`, `successful_at`, and `finished_at` values. QVIX also requires original member/shared `acquired_at`; transport requires original `raw.retrieved_at`. Values must be strings with full ISO date/time through seconds, optional fractional seconds, and UTC `Z` or `+00:00`; calendar validity is checked by `datetime.fromisoformat`. Missing, empty, null, malformed, impossible-date and timezone-less values cannot become a completed snapshot. Existing immutable snapshot equality, invocation identity/time, shared acquisition identity, comparator provenance and derived-v3 original-time equality checks remain in force.

The new 40-case native regression creates a valid prior group and a distinct current group using the real pinned wrappers with injected offline HTTP bytes. It mutates the current immutable `result.json` itself, then obtains its new origin hash. Each of attempted/successful/finished/acquired times is tested missing, null, empty, impossible date and timezone-less, both with and without a prior snapshot. Direct promotion rejects without changing `latest.json`; recovery fails only the attacked feed while siblings remain fresh partial; recovered promotion and actual chart build/offline verification succeed. Own prior closes survive only as stale, or the feed has an empty unavailable trace without prior. The invalid current result remains invalid throughout; no origin restoration masks the recovery test.

Four additional shared-origin cases mutate missing/unusable shared acquisition or raw retrieval timestamps, rebinding member shared hashes to the mutated immutable evidence. Three derived-v3 cases mutate the derived immutable result's otherwise valid attempt/success/finish times and rebind its origin: independent validation still rejects disagreement with the original v3 lineage. Existing explicit migration and original-provenance tests also pass.

## M-R2 — visible disclosure context

`Embedded` tracks non-void ancestors and matching closures. A disclosure is accepted only on the existing `html/body/main/section/div/div/p` path, with the existing card/panel-head classes and conservative attribute allowlists. Hidden/style-bearing ancestors, arbitrary wrappers, `details`, `template`, extra classes/attributes, and nested disclosure content tags are rejected. The independent exact paragraph text and per-feed/per-panel section bindings are unchanged; JSON is not a visibility substitute.

The existing fresh/stale/unavailable tamper regression now also covers hidden and styled ancestor wrappers, hidden/styled existing panel-head/body/main ancestors, disallowed containers and hidden nested content, alongside direct hidden/style attributes, paragraph removal and contradictory text. Real report parsing and all independent raw/array checks pass.

## F-B1 — legend versus hover modebar

Changed only legend `x: 1 → 0` and `xanchor: right → left`; `y=1.17`, bottom anchor, horizontal orientation, chart height/margins, range selector, slider, axes, reset and Plotly configuration remain unchanged. This moves the legend toward the left, away from the upper-right hover toolbar. Actual non-overlap and ordinary center-clickability remain for the separate final browser reviewer; no browser acceptance is claimed here.

A post-build throwaway inline Python comparison parsed old/new report payloads, changed only those eight expected legend fields in the old payload, and asserted full payload equality. It also asserted identical CSS, disclosure text, and complete report text outside the report-data script. Thus all arrays, status, controls, surrounding HTML and configured panel geometry are unchanged.

## Checks actually run

Targeted commands (exit 0):

```sh
.venv/bin/python -m pytest -q tests/test_contracts.py -k 'native_completion_times or visible_per_feed or explicit_derived or mandatory_provenance'
# 50 passed, 51 deselected; 2 upstream mini-racer deprecation warnings; 193.75s
.venv/bin/python -m pytest -q tests/test_contracts.py -k 'native_shared_original_times or derived_completion_cannot'
# 7 passed, 101 deselected; same 2 warnings; 3.63s
```

Final union, after all code/test/README/lesson edits (exit 0, 252.92s):

```sh
uv sync --frozen
uv run python -m compileall -q app
uv run ruff check .
uv run pytest -q
uv run python -m app.chart --input data --output report.html
uv run python -m app.verify --input data --report report.html
```

Observed: frozen sync checked 33 packages; compileall succeeded; root Ruff `All checks passed!` including retained review probe scripts, no unrelated lint failures or fixes; **108 passed**, 2 upstream mini-racer deprecation warnings, pytest 245.61s. Chart wrote eight panels/seven disclosed QVIX feeds. Independent verification replayed all eight index histories and seven raw/wrapper/artifact/quality chains. Index row counts: 6509/5552/5053/6030/3995/3017/1663/1663; latest date 2026-11-13. Full shell output retained in `/tmp/matched-qvix-fix-union.log` for this run.

## Preservation and report identity

Before edits, hashed every production `data/` file and root report into `/tmp/matched-qvix-fix-production.sha256`. Final `sha256sum -c` against its data-only entries passed for **all 152 files**, including active pointer, identities, current and historical native/derived artifacts. All **213** historical inventory entries passed `sha256sum -c docs/matched-qvix-pre-edit.sha256` before and after the fixes. Nothing in either inventory was rewritten. Check output retained under `/tmp/matched-qvix-fix-{production,historical}-check.txt`.

- Before report SHA-256: `218d623efde86f040b9896348f78d2cb16950c55b9725c2c02a1c6eb135931a0`.
- Final report SHA-256: **`84d5570f1551e6e193310fec3e769ad356fa95187e9e3ec8ce725bf112da5d58`**.
- Verifier-only fixes required no report regeneration. The sole regeneration was authorized for F-B1; the payload/HTML comparison above proves its narrow delta.

No independent acceptance, provider/economic certification, final browser non-overlap or center-click claim. Final independent review must hover and normally center-click all 19 legend labels on this final report hash.
