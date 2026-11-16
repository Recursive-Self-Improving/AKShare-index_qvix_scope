# Daily refresh implementation evidence

Implementation slice for reviewed P-D1/P-D2, D19 and approved D20 delta; no goal-ledger edits or commits. Existing v4 financial schema, dependencies, panel mappings/layout and immutable production bytes are not changed. Independent whole-change review belongs to the parent, not this implementation report.

## Boundaries delivered

- `.github/workflows/daily-refresh.yml`: UTC `5 0 * * *` / manual default-branch-only; empty default permissions; workflow-level fixed concurrency without cancellation; separate read-only prepare, contents-write persistence, opt-in Pages, and always-running final quality conclusion. Job limits 30/5/10/2 minutes; preparation has a 25-minute driver alarm. Python 3.14.4, uv 0.13.6, frozen no-dev runtime lock; all top-level actions pinned to verified upstream commit SHAs.
- `app/daily.py`: verify baseline before acquisition, ordinary-copy private staging, explicit frozen full window, actual acquisition invocation identity/time/previous/member/exit checks, selected cutoff, overlapping index raw/QVIX common-raw date retention, actual chart and independent verifier, immutable inventory protection, exact hashed candidate and bounded diagnostics. No acquisition retry, rolling merger, stale publication or null-price resurrection.
- `app/daily_transfer.py`: standard-library-only executable boundary. Trusted same-run/attempt/base identity and receipt hash; allowlisted file/size/hash inventory; no links/executable modes/extra/missing files; exact clean base and current remote/default branch. Complete new-commit parent list must equal `[receipt base]`; one push of that exact commit with explicit `--force-with-lease=refs/heads/<branch>:<base>`, no generic force/retry/rebase/fallback. Accepted transition is a strict fast-forward, not history rewriting; ordinary non-force push was superseded by D20. Exact read-back required to prove persistence, including a lost push response. Pages packages only exact verified HTML after checking persisted target; never treats Git persistence as deployment.
- `tests/test_daily.py`: deterministic policy, real preparation/render/verifier, transfer and disposable-local-Git scenarios. No provider/real remote requests or hosted deployment. Writer CLI additionally runs with `python -I -S`, excluding site-packages.
- README documents permission/setup, cutoff/whole-history choice, red partial/fatal withholding, Pages opt-in boundary, races, storage/retention, recovery/notifications and external limits. AGENTS adds the reusable publication-boundary lesson.

## Tools and upstream action identity

LSP attempted with `{"action":"symbols","file":"app/fetch.py"}` via `xd://lsp`; returned `LSP error -32601: Unknown request: textDocument/documentSymbol`. Source inspection used the unavailable-server fallback; no existing exported code symbols changed.

Executed `uv --version` → `uv 0.13.6 (x86_64-unknown-linux-gnu)` and `.venv/bin/python --version` → `Python 3.14.4`.

Executed these exact read-only commands (each exit0):

```sh
git ls-remote https://github.com/actions/checkout.git refs/tags/v4.2.2
git ls-remote https://github.com/actions/setup-python.git refs/tags/v5.6.0
git ls-remote https://github.com/astral-sh/setup-uv.git refs/tags/v6.4.3
git ls-remote https://github.com/actions/upload-artifact.git refs/tags/v4.6.2
git ls-remote https://github.com/actions/download-artifact.git refs/tags/v4.3.0
git ls-remote https://github.com/actions/upload-pages-artifact.git refs/tags/v3.0.1
git ls-remote https://github.com/actions/deploy-pages.git refs/tags/v4.0.5
```

| Upstream tag | Observed SHA |
|---|---|
| actions/checkout v4.2.2 | `11bd71901bbe5b1630ceea73d27597364c9af683` |
| actions/setup-python v5.6.0 | `a26af69be951a213d495a4c3e4e4022e16d87065` |
| astral-sh/setup-uv v6.4.3 | `e92bafb6253dcd438e0484186d7669ea7a8ca1cc` |
| actions/upload-artifact v4.6.2 | `ea165f8d65b6e75b540449e92b4886f43607fa02` |
| actions/download-artifact v4.3.0 | `d3f86a106a0bac45b974a628896c90dbdf5c8093` |
| actions/upload-pages-artifact v3.0.1 | `56afc609e74202658d3ffba0e8f6dda462b719fa` |
| actions/deploy-pages v4.0.5 | `d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e` |

This establishes observed top-level upstream tag identity, not transitive locking or upstream-code safety. No action-lock expansion adopted under D19.

## Narrow verification runs

1. `uv run --frozen pytest -q tests/test_daily.py` → exit0, 28 passed / 2 upstream mini-racer deprecation warnings, 19.37s (initial slice).
2. `actionlint .github/workflows/daily-refresh.yml; uv run --frozen ruff check app/daily.py app/daily_transfer.py tests/test_daily.py` → actionlint passed; Ruff found one unused `os` import in the new test; removed it.
3. `uv run --frozen pytest -q tests/test_daily.py` → exit0, 38 passed / same 2 warnings, 52.91s (expanded refusal/conclusion cases).
4. `actionlint .github/workflows/daily-refresh.yml && uv run --frozen ruff check app/daily.py app/daily_transfer.py tests/test_daily.py && uv run --frozen pytest -q tests/test_daily.py` → exit0, lint passed, 40 passed / same 2 warnings, 54.52s.

The last narrow run includes:

- Actual `fetch` orchestration and all eight real index workers replay retained Sina responses; seven real cached wrappers process synthetic all-blank revisions preserving original common dates plus a current-day raw row. Baseline and candidate use the real separate-process independent verifier and actual renderer. Frozen Nov16 UTC start selects through Nov15, retains history before October, shows fresh nulls rather than old prices, excludes Nov16 from selected traces, ends on observed Friday Nov13 without inventing weekend rows, and preserves the cutoff when finish crosses midnight.
- Real baseline/candidate verification rejects unchanged old acquisition after a simulated crash, a newly edited unreferenced historical CSV, hidden HTML disclosure, and a valid stale/fatal candidate; checkout pointer/page/evidence remain unchanged and no bundle is emitted. Fatal's independent data contract remains valid: it is the stricter publication policy that refuses it.
- Index and per-feed QVIX guard scenarios reject missing beginning/middle/end dates, including equal-count replacements with retained endpoints; policy allows all-blank/null retention and changed old values. Time, origin, full-window, cutoff, stale/status and exit-code mismatch cases refuse eligibility.
- Exact verified partial payload persists pointer, report and new evidence in one commit against disposable local bare remotes; replay refuses a duplicate acquisition. Hash/identity/extra-path/link/executable/missing/traversal attacks preserve the remote. The original run covered competing/divergent writers but not rollback; its ordinary non-force push mechanism is superseded by the D20 correction below. Accepted push with lost error response or timeout is proved only by exact read-back.
- Actual concluding workflow shell is executed for clean/partial/disabled-Pages/deployed-partial/deploy-failure outcomes: partial is red after persistence, Pages failure says no rollback, disabled is explicit. Stdlib-only publisher CLI and exact single-file Pages package run without application dependencies; other-branch manual execution refuses.

## Final applicable gates

Final union invocation follows. No separate build/typecheck framework exists. Chart output is temporary: the existing public `index.html` is never overwritten by verification.

```sh
set -e
uv sync --frozen
uv run --frozen python -m compileall -q app
uv run --frozen ruff check .
actionlint --version
actionlint .github/workflows/daily-refresh.yml
uv run --frozen pytest -q
check_dir=$(mktemp -d)
trap 'rm -rf "$check_dir"' EXIT
uv run --frozen python -m app.chart --input data --output "$check_dir/index.html"
uv run --frozen python -m app.verify --input data --report "$check_dir/index.html"
cmp index.html "$check_dir/index.html"
uv run --frozen python - <<'PY'
from pathlib import Path
from app.daily_transfer import inventory, digest
import json
files = inventory(Path('data'), bounded=False)
print('Retained data:', len(files), 'files;', sum(v['size'] for v in files.values()), 'bytes')
print('Data inventory SHA256:', digest(json.dumps(files, sort_keys=True).encode()))
print('Public index.html SHA256:', digest(Path('index.html').read_bytes()))
PY
```

Result: **exit0**, wall 364.01s. Frozen sync checked33 packages; compileall passed; root Ruff passed; actionlint1.7.12 passed (built with go1.27.3). Full pytest **156 passed**, two known upstream mini-racer deprecation warnings, 358.69s. Temporary chart rendered8 panels and independent verifier passed all7 raw/wrapper/artifact/quality replays. `cmp` exit0 establishes byte-identical regenerated/public HTML; no page/layout mutation.

Observed retained data: **152 files / 22,488,124 bytes**. Inventory SHA256 (sorted JSON of path/size/SHA256): `232bfb24e1b0fa8306072d05ef6c3251c1582d669f1d3b38f67905c27e22890d`. Public `index.html` SHA256: `572e90ba08ec928f5692b48e82cc685bd21ccb0f42ee8e7885f799eb39df8ce8`.

Independent verifier printed index row counts **6509/5552/5053/6030/3995/3017/1663/1663**, all ending2026-11-13, all index attempts success. This offline pass does not change the seven retained QVIX fresh-partial states.

Changed files in this implementation slice: `.github/workflows/daily-refresh.yml`, `app/daily.py`, `app/daily_transfer.py`, `tests/test_daily.py`, `README.md`, `AGENTS.md`, and this evidence file. No production `data/`, public HTML, lockfile, financial schema or goal-ledger edits.

## External limits

No live provider fetch, real remote push, GitHub API write, Pages deployment, browser, dependency/schema change, goal-ledger edit or commit was performed. All push tests use newly created disposable filesystem bare remotes. Existing HTML/UI was not changed, so no new browser acceptance is claimed or required for this slice.

Hosted scheduling delivery/delays/inactivity, token and branch-rule enforcement, network/provider availability, notifications, actual artifact-service behavior, Pages source/environment/approvals and redistribution authorization remain external setup/verification limits. Pages is explicitly disabled unless repository variable `PUBLISH_PAGES=true` and hosted setup authorize it. Git and Pages are not atomic; a human can race after a deployment ref check. Current partial provider quality and unauthenticated HTTP source are not fixed by hashing or automation. No automatic absent-run alert, retention pruning or reviewed-history-loss bypass is provided.

## Round-1 corrective slice (D-R1, S1, S2)

- S1: preserve staged path/blob/mode checks and ambiguous push read-back; require the complete parent list exactly `[receipt base]`, then issue exactly one explicit receipt-base lease push of the verified commit. Regression races inject both a divergent human update and rollback to an ancestor after the final precheck; the competing remote must remain untouched. Wrong-parent and multi-parent commits must refuse before any push. Ref equality cannot detect ABA and does not lock future writers; server refusal remains fail-closed.
- D-R1: retain member attempted/successful/finished ordering and independent verifier's immutable result/shared/config/group identity checks. QVIX acquisition must fall within the current invocation/enclosing manifest and no later than that member's successful completion, not after each cached wrapper starts. Index acquisition retains its per-attempt interval. No worker or immutable evidence timestamps changed. The real preparation fixture now advances the acquisition clock; later members explicitly have acquisition before attempt. Actual fetch/render/separate-process verifier, exact local publication and actual red partial conclusion are exercised together. Deterministic old/future/completion/order refusals cover the temporal edges.
- S2: README explicitly states no deploy-only command exists, failed-job reruns mismatch attempt, and all-job reruns use an obsolete event base after persistence. Exact-byte recovery is authorized external/manual deployment of committed HTML with original identity/receipt hash/HTML hash, remote-target and Pages permissions/settings/approval checks; new dispatch is a new refresh. No receipt relaxation or new deployment subsystem.
- Corrective LSP references request at `app/daily_transfer.py:88` returned `Unknown request: textDocument/references`; source inspection used unavailable-server fallback.

Corrective commands executed:

```sh
uv run --frozen pytest -q tests/test_daily.py
uv sync --frozen && uv run --frozen python -m compileall -q app && uv run --frozen ruff check . && actionlint .github/workflows/daily-refresh.yml
```

Results: daily regressions **51 passed**, two known upstream mini-racer deprecation warnings, 56.90s; static chain exit0, frozen sync checked33 packages, compileall/root Ruff/actionlint passed. Includes disposable-remote rollback/divergent preservation, wrong/multiple parent refusal, ambiguous-response read-back, temporal old/future/completion/order refusal, advancing-clock real preparation/render/verifier and exact partial persistence followed by the actual red conclusion shell.

Final corrective integration command:

```sh
set -e
uv run --frozen pytest -q
check_dir=$(mktemp -d)
trap 'rm -rf "$check_dir"' EXIT
uv run --frozen python -m app.chart --input data --output "$check_dir/index.html"
uv run --frozen python -m app.verify --input data --report "$check_dir/index.html"
cmp index.html "$check_dir/index.html"
```

Result: **exit0**, wall387.21s; full suite **167 passed**, two known upstream mini-racer warnings, 381.97s. Temporary chart rendered eight panels; independent verifier passed seven raw/wrapper/artifact/quality replays; `cmp` passed, proving regenerated/public HTML byte identity. Temporary output removed by trap. No public HTML/data, worker evidence, historical research/reviews, workflow, ledger or commit changes in this corrective slice.

Exact corrective changed paths: `app/daily.py`, `app/daily_transfer.py`, `tests/test_daily.py`, `README.md`, `AGENTS.md`, `docs/daily-refresh-implementation-evidence.md`. No live providers, real push/deploy, browser or subdelegation; hosted operation and independent review remain outside this local proof.
