# Daily refresh security review — round 1

## Verdict: Fix

Independent whole-change publication/security review against `f16be449c1`, active AC17–21, P-D1/P-D2, D19 and `daily-refresh-plan-review.md`. Reviewed the new untracked workflow, `app/daily.py`, `app/daily_transfer.py`, `tests/test_daily.py`, implementation evidence and README/AGENTS changes; the tracked diff alone does not include the new implementation. No implementation, ledger or commit changes made. Data accounting has a separate reviewer.

## S1 — Fix, P2: pre-push check is not an atomic expected-base guard

**Location:** `app/daily_transfer.py:116–128` (`remote_head`, then ordinary `git push`).

The normal divergent-human-commit race is handled, but a branch rollback between the final check and push is accepted. An ordinary non-force push checks fast-forward ancestry, not equality with the event base. If another authorized writer resets the branch to an ancestor, this publication is still a fast-forward from that ancestor and silently reinstates the reverted baseline. This violates P-D2's rejection of branch races and README's “HEAD变化即拒绝” promise. Concurrency cannot serialize external writers.

**Observed:** on a disposable local bare remote with two baseline commits, changed the remote ref to the first commit immediately before the publisher's push. `publish` succeeded, returned the new commit and reinstated the second baseline's README. No provider, GitHub push or deployment was involved.

**Required correction:** enforce expected-ref equality at the push transaction, not only with preceding/read-back inspection. One Git-native option is an explicit `--force-with-lease=refs/heads/<branch>:<base>` together with proof that the sole new commit has exactly the expected base parent; that preserves the no-history-rewrite invariant while adding compare-and-swap. Reconcile the literal “non-force” wording with the reviewed safety invariant rather than silently weakening it. Alternatively use another genuinely atomic expected-base mechanism. Do not rebase/retry. Add a rollback-to-ancestor race regression that proves the remote remains at the competing rollback, alongside the existing divergent-commit race test.

An ABA change away from and back to the exact base cannot be detected by ref equality alone; avoid claiming detection of every historical ref movement.

## S2 — Fix, P3: Pages-only recovery instructions omit an enforced rerun rejection

**Location:** `README.md:94–96`, workflow Pages job and `app/daily_transfer.py:63,142–148`.

The README instructs operators to retry only deployment of the exact committed HTML after a Pages-only failure. The supplied workflow has no deploy-only dispatch. GitHub's failed-job rerun increments `github.run_attempt` while reusing the completed preparation's artifact/output. That artifact's receipt contains the previous attempt identity, so both Pages package checks reject it before deployment. Re-running all jobs is also refused after persistence because the event SHA is now obsolete. Rejecting stale/cross-attempt receipts is consistent with the approved trust boundary; the problem is the undocumented recovery dead end, not a request to remove that check.

**Observed:** executed the actual stdlib Pages CLI with an accepted attempt-1 receipt, exact current published commit, same run ID and attempt 2. Exit 1: `ValueError: invocation identity mismatch`.

**Required correction:** state explicitly that failed-job/all-job reruns cannot recover this case. Document a concrete supported way to deploy the already-persisted exact HTML, with authorization and identity checks, or explicitly identify deploy-only recovery as an external/manual operational step absent from this workflow. Do not suggest merely replacing the receipt hash/attempt or rerunning acquisition as equivalent exact-byte recovery. A new default-branch dispatch is valid for a new refresh, not a deployment-only retry.

## Boundaries that passed this review

- Empty workflow permissions; read-only preparation; fresh contents-write runner executes only checked-out stdlib transfer code/Git, not payload application code. Checkout credentials are not persisted. Pages alone has Pages/OIDC rights. Checkout uses the event SHA, not artifact-provided code.
- Receipt hash comes through the preparation job output, not from the downloaded receipt itself. Receipt identity checks repository, branch, event base, run and attempt. Artifact download selects the exact output ID, without a name fallback; download's default current-run scope is relied upon. This authenticates the selected preparation result, not independent resistance to a compromised preparation job.
- Payload validation checks exact path/size/hash inventory and required entrypoints; restricts writes to the new run subtree, pointer and HTML; rejects traversal, symlinks, executable files and extras. Destination ancestor symlinks are checked. Staged blobs/modes are independently read back before one commit. Existing source/Git configuration is trusted, not supplied by the artifact. Hardlink count and every POSIX permission bit are not checked; copied target files are normalized to `0644`, and GitHub artifact transfer does not preserve original POSIX modes. Do not describe this as a general archive/hardlink validator.
- Clean checkout/base checks, remote default-branch checks, divergent-writer rejection, and ambiguous-push exact read-back are exercised. No force/retry/rebase exists in the reviewed implementation; S1 is the remaining expected-base gap.
- Preparation checks baseline/candidate through separate verifier commands, freezes UTC yesterday, copies staging without hardlinks, compares immutable inventories and refuses fatal/stale publication. This is evidence consistency, not source authenticity or HTML-script security. Redirect hardening and financial normalization are outside this review's change scope.
- Pages copies only the receipt-bound `index.html` into a new one-file directory after persistence; rechecks the remote target immediately before deploy. The Pages action packages that directory. Its `build_version`/event SHA is not evidence that the new data commit was checked out; the supplied artifact carries the new bytes. Git and Pages remain non-atomic and a race after the last check remains disclosed.
- The actual conclusion shell passed clean/partial/disabled/deploy-failure scenarios: partial can persist/deploy before the final red job; disabled Pages is explicit; deployment failure does not roll back Git. Default success gating prevents persistence after preparation/upload failure; `always()` conclusion exposes failure/skips. Cancellation may preclude final diagnostics/conclusion and is documented.
- Top-level actions have full SHA pins consistent with the implementation's retained upstream tag evidence. Inspected the exact pinned [upload-pages-artifact action](https://raw.githubusercontent.com/actions/upload-pages-artifact/56afc609e74202658d3ffba0e8f6dda462b719fa/action.yml): it creates the tar from the site directory and invokes `actions/upload-artifact@v4` internally. Thus top-level pins are not transitive locks, as README correctly states; D19 explicitly does not require action-lock expansion. Hosted runner image and downloaded Python/uv distributions are separate supply-chain trust.
- Git authentication uses an environment-only Git extraheader; the workflow does not interpolate a token into shell source, command arguments or URLs. Application subprocesses lose `GH_TOKEN` before acquisition. Preparation's read-only job token still belongs to the preparation trust domain; hashes do not sandbox its dependencies.

## Exact verification commands and observations

Initial scope inventory (read-only; `ls docs/evidence` reported absent and exit 2, not a project failure):

```sh
git diff --stat f16be449c1
git diff --name-only f16be449c1
ls docs/reviews
git status --short
ls app
ls .github/workflows
ls tests
ls docs/evidence
```

Requested `xd://lsp` with `{"action":"symbols","file":"app/daily_transfer.py"}`; server returned `Unknown request: textDocument/documentSymbol`. Used source inspection because code intelligence was unavailable.

Narrow existing executable security/publication coverage, run once:

```sh
uv run --frozen pytest -q tests/test_daily.py -k 'transfer_rejections or exact_atomic or competing_writer or push_race or accepted_push or actual_workflow_conclusion or stdlib_only'
```

Result: **17 passed, 23 deselected**, 1.49s. These tests use disposable local remotes, including exact atomic tree/pointer/page, hash/path/identity/link/mode rejection, competing/default-branch/divergent races, ambiguous push read-back, real conclusion shell and stdlib Pages CLI. Passing tests do not cover the rollback race below.

Independent S1/S2 reproduction, run once:

```sh
uv run --frozen python - <<'PY'
import json, os, runpy, subprocess, sys, tempfile
from pathlib import Path
from unittest.mock import patch
import app.daily_transfer as t
h = runpy.run_path('tests/test_daily.py')
with tempfile.TemporaryDirectory(prefix='daily-security-') as d:
    root = Path(d)
    repo, remote, identity = h['repo_pair'](root)
    ancestor = identity['base_sha']
    (repo / 'README').write_text('new baseline\n')
    t.git(repo, 'add', 'README')
    t.git(repo, '-c', 'user.name=test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'new baseline')
    t.git(repo, 'push', 'origin', 'HEAD:main')
    identity['base_sha'] = t.git(repo, 'rev-parse', 'HEAD').stdout.strip()
    bundle, receipt_hash = h['small_bundle'](root, identity)
    original = t.git
    def rollback(root, *args, **kwargs):
        if args[0] == 'push':
            original(remote, 'update-ref', 'refs/heads/main', ancestor, identity['base_sha'])
            print('RACE: remote rolled back after final pre-push check')
        return original(root, *args, **kwargs)
    with patch.object(t, 'git', rollback):
        commit = t.publish(repo, bundle, receipt_hash, identity)
    print('RESULT: publisher accepted competing rollback:', original(remote, 'rev-parse', 'main').stdout.strip() == commit)
    print('RESULT: rolled-back baseline restored:', original(remote, 'show', 'main:README').stdout.strip())
    env = os.environ.copy()
    env.pop('GH_TOKEN', None)
    env.update(DEFAULT_BRANCH='main', GITHUB_REF='refs/heads/main', GITHUB_EVENT_NAME='workflow_dispatch', GITHUB_REPOSITORY=identity['repository'], GITHUB_SHA=identity['base_sha'], GITHUB_RUN_ID=identity['run_id'], GITHUB_RUN_ATTEMPT='2')
    result = subprocess.run([sys.executable, '-I', '-S', str(Path('app/daily_transfer.py').resolve()), 'pages', '--bundle', str(bundle), '--receipt-hash', receipt_hash, '--commit', commit, '--site', str(root/'site')], cwd=repo, env=env, capture_output=True, text=True)
    print('RESULT: Pages-only failed-job rerun:', result.returncode, result.stderr.splitlines()[-1])
PY
```

Observed output, exit 0 for the investigation script:

```text
RACE: remote rolled back after final pre-push check
RESULT: publisher accepted competing rollback: True
RESULT: rolled-back baseline restored: new baseline
RESULT: Pages-only failed-job rerun: 1 ValueError: invocation identity mismatch
```

No permanent regression tests or runtime changes added; no real provider calls, real remote push, API write, deployment, browser, heavy workload, subdelegation or commit. Temporary repositories were automatically removed. No full-suite rerun: the parent owns the final union gates. Actual GitHub artifact extraction/service authorization, scheduler delivery, branch rules, environment approvals, installed hosted versions and deployment execution remain externally unproved, not claimed verified by local tests. **S1 and S2 remain open Fix findings.**
