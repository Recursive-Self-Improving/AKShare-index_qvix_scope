# Daily refresh proposal B

Research/design only, 2026-11-16. Scope: active AC17–21 in
[`../goals/sentiment-index-history.md`](../goals/sentiment-index-history.md).
Proposal A was not read. No implementation, ledger, acquisition, push, deployment,
browser, delegation, or commit was performed for this proposal.

## 1. Recommendation

1. Schedule `5 0 * * *` in UTC and support `workflow_dispatch`, using the same
   full-history acquisition and publication policy for both.
2. Fetch **whole source revisions**, selecting `2000-01-01` through yesterday
   relative to one frozen **actual execution-start UTC date**. Do not use a rolling
   `--start` and do not splice old and new CSV rows.
3. Prepare an isolated candidate, independently verify its data and root
   `index.html`, then persist both in **one commit and one fast-forward push**.
   Production `data/latest.json` must never advance independently of the HTML.
4. Distinguish a verified fresh QVIX `partial` from a provider `failure`, an
   interrupted invocation, and a failed integrity check. Permit the first;
   withhold publication for the others. Preserve the real fetch exit code and
   finish **nonzero even when a valid partial candidate was persisted**.
5. Separate a read-only preparation job from a minimal write-capable persistence
   job. Do not give AKShare, package installation, or provider-processing commands
   a repository-write token.
6. Treat Git persistence and GitHub Pages deployment as different outcomes.
   `GITHUB_TOKEN` pushes do **not** trigger branch-based Pages builds. If automatic
   Pages publication is wanted, recommend a separately permissioned deployment
   job in this same workflow and an owner-managed switch to Pages “GitHub Actions”.
   No PAT is needed for that design.

These are proposed implementation decisions, not evidence that hosted automation
or publication already works.

## 2. Repository evidence and the overlap decision

### Current boundaries

- [`../../pyproject.toml`](../../pyproject.toml) requires Python `>=3.14,<3.15` and
  pins AKShare `1.20.53`, requests `2.34.2`, Plotly `7.1.0`; the existing `uv.lock`
  is the dependency authority. Do not upgrade AKShare as part of scheduling.
- [`../../README.md`](../../README.md) specifies `uv sync --frozen`, fetch, chart,
  and independent offline verification. It documents root `index.html` and
  branch-based Pages from `master`/root. That is documentation, not proof of the
  actual hosted default branch, Pages mode, or branch rules.
- [`app.fetch.worker`](../../app/fetch.py) calls
  `ak.index_zh_daily_sina(symbol=feed)` without a date argument, captures the full
  response, then applies `selected(..., start, end)` locally. `group_worker`
  invokes seven argument-free QVIX wrappers sharing one captured source load;
  `qvix_artifacts` interprets full raw history before selecting its output window.
  **The existing acquisition path does not request a reduced upstream window.**
- `app.fetch.state_after` replaces the entire snapshot for `success`/`partial`;
  only `failure` reuses that feed's prior snapshot. `fetch` returns 1 whenever any
  required attempt is not `success`. Exit 1 therefore cannot distinguish expected
  QVIX quality defects from a genuine acquisition failure.
- `app.fetch.promote` validates before replacing `latest.json`, but this is
  data-only atomicity: it does not build or verify `index.html` in the same
  transaction. It also cannot protect the checkout from an interrupted chart
  build or a later Git conflict.
- [`app.core.histories`](../../app/core.py) reads each selected snapshot CSV;
  [`app.chart.panels`](../../app/chart.py) renders those rows, not a union of
  historical runs. Setting `--start` to 30 days ago therefore truncates the chart
  even though complete source bodies remain on disk.
- [`app.verify.verify`](../../app/verify.py) binds immutable origins, raw and
  artifact hashes, wrapper replay, independent quality accounting, actual HTML
  arrays and visible disclosures. It can correctly verify a stale candidate or a
  narrow window; automation must additionally establish **this invocation's
  identity, required full window, and publication eligibility**.
- The retained active manifest observed for this proposal is v4, window
  `2000-01-01`–`2026-11-16`, with eight fresh index successes and seven fresh QVIX
  partials. This observation is not a new provider call or a replay test.

### Compare exactly 30 calendar days with full replacement

Let `D` be execution-start UTC date and `E = D - 1 day`. A 30-calendar-day repair
window ending at `E` is `[E - 29 days, E]`, equivalently `[D - 30 days, D - 1 day]`.
It is not 30 trading sessions.

| Concern | Thirty-day overlap/merge | Full historical replacement — recommended |
|---|---|---|
| Provider requests | No reduction through these call sites; full responses still arrive | Same eight index calls plus one shared QVIX source load |
| Validation cost | Full-response validation and QVIX grouping still required | Reuses the current full-response contract |
| Chart history | Passing only the narrow window truncates it; a new merger is required | Fixed start preserves the requested historical window |
| Corrections older than 30 days | Missed by a rolling repair, despite already having the raw response | Captured by the next accepted full revision |
| Conflict/blank corrections | A merge can incorrectly resurrect previous prices or hide a new null | Fresh evidence replaces old prices, including legitimate nulls |
| Provenance | Requires per-date revision selection, withdrawal rules, comparator/calendar policy, new verification and likely schema work | Existing whole-snapshot origins and comparator bindings remain valid |
| Failure recovery | Requires rules for partially repaired windows and disjoint revision dates | Existing fatal/stale semantics remain intact inside the staged run |
| Long schedule outage | Can leave unrepaired holes older than the overlap | Next successful full refresh covers the outage and older corrections |
| Immutable storage | Still retains full raw evidence; overlap is not a demonstrated storage solution | Explicitly retains complete new evidence; growth must be budgeted |

Do not implement an overlap mode merely to offer two knobs. Revisit it only if a
supported source actually provides bounded incremental revisions and a separately
reviewed per-date provenance/withdrawal contract makes merging worthwhile. That
would be a data-contract change, not a cron optimization.

### What “preserve history” means

Keep every pre-existing immutable data artifact byte-for-byte. Preserve full
requested chart coverage, not the previous numeric answer at every date: fresh
QVIX blank/error/conflict evidence must still replace old prices with nulls under
the current contract. Do not stitch earlier revisions into those nulls.

Add a **publication safety check**, not a normalizer change, for unexplained
source-history contraction. Compare prior and candidate raw **date sets** within
`[2000-01-01, min(prior window end, E)]`: index decoded dates and QVIX shared common
dates, not finite-close sets or nonblank per-feed bounds. A previously retained
source date disappearing from the new full response blocks automatic publication
and is listed in diagnostics for review. All-blank/all-conflict QVIX rows with the
same common dates still pass this guard and remain fresh partials. Value
corrections, resolved duplicate ordinals, later dates, and changed quality counts
are allowed. Dates later than `E` in a prior manual snapshot are not demanded.

Tradeoff: a legitimate provider withdrawal can require human review before the
new whole snapshot is published. This is safer than silently reducing an index
to a short, structurally valid response. The failed publication keeps the old
entry points and new evidence artifact; it does not falsify the candidate's
underlying source status or invent missing data. No percentage-loss threshold,
per-date fallback, or unattended bypass is recommended.

## 3. Schedule, execution date, branch, and bounds

Required trigger/concurrency shape, deliberately not a complete workflow:

```yaml
on:
  schedule:
    - cron: '5 0 * * *'
  workflow_dispatch:
permissions: {}
concurrency:
  group: daily-refresh-persistence
  cancel-in-progress: false
```

- Omit a timezone override: GitHub's default is UTC. `00:05` is a scheduled
  eligibility time, not a promise that work or publication completes then.
  GitHub documents delays and possible dropped scheduled runs, especially near
  hourly load peaks. Schedules run only from the default branch; the workflow
  must exist there. Public-repository inactivity can disable them after 60 days.
  Manual dispatch also requires the workflow on the default branch.[G1]
- Freeze `started_at = datetime.now(timezone.utc)` once before preparation;
  derive `D` and `E` from it and persist both in the outcome. Always pass explicit
  `--start 2000-01-01 --end E`. Current `app.fetch.main` uses local `date.today()`
  by default; do not rely on runner timezone or that default.
- A scheduled run delayed into another UTC day uses that **actual** day's
  yesterday. It does not reconstruct a missing nominal cron timestamp. If a run
  crosses midnight after start, keep the frozen `E`. This remains conservative
  and reproducible. A rerun is a new actual attempt, not a historical fetch at
  the old run's nominal time.
- `E` is a maximum observation date, not an assertion that data exists for `E`.
  Do not skip weekends or Chinese holidays by guessing a calendar. Observe the
  providers' dated history and existing null/gap accounting. For example,
  Monday's run can legitimately end its actual observations on Friday.
- Raw response bodies, full quality sets and wrapper evidence may contain `D`
  or later source dates: retain and validate them. **Selected CSV rows and every
  plotted date must be no later than `E`**. Disclosures may describe the separate
  full-source bounds. Acquisition timestamps naturally occur on execution day.
- Resolve the target from the repository's default branch, not an assumed
  `main` or a hardcoded `master`. Require the event ref to equal that branch;
  reject manual dispatch on a tag or other branch before any live acquisition.
  No arbitrary ref/date inputs are needed for the first version.
- Check out the event SHA, record it as `base_sha`, and refuse a stale event if
  the target already points elsewhere. Repeat that check at publication. This
  avoids running new repository code under an old workflow definition or
  publishing an old rerun over new work. Recovery is a **new manual dispatch**,
  not repeated “re-run all jobs” on a stale event SHA.
- Use GitHub-hosted ephemeral runners, one preparation lane, no browser/matrix.
  Suggested job bounds: prepare 30 minutes with a 25-minute driver deadline
  leaving diagnostics time; persist 5 minutes; optional Pages 10 minutes; final
  conclusion 2 minutes. Keep the existing eight independent 45-second index
  workers and one 45-second QVIX group, with no provider retry loop. Queue delays
  are outside these execution bounds.

Concurrency uses one fixed group for every schedule/manual writer, spanning the
whole workflow; do not put the same group on its child jobs and deadlock it.
`cancel-in-progress: false` prevents a newer run intentionally killing a running
publication. With default queue behavior, a newer pending run can replace the
previous pending run; execution order is not a reliable dispatch order.[G2]
Full refresh makes lost pending repair windows harmless, but this is **not an
exactly-once daily scheduler**. The group does not lock human pushes or workflows
using other groups. All automated writers of this dataset must share the group.

## 4. Staged transaction and status protocol

### A. Read-only preparation

1. Pin the checkout to `base_sha`; use `persist-credentials: false`. Install an
   explicitly selected Python 3.14 patch and uv version, then
   `uv sync --frozen --no-dev`. Execute with that environment without an implicit
   re-sync. No lock update, dependency upgrade, provider credentials, or write
   token. Dev dependencies remain for implementation gates, not daily fetching.
2. Verify the existing `data/` plus root `index.html` baseline offline. If it is
   inconsistent, stop before fetching: automation must not build on a corrupt
   pointer or silently repair unrelated edits.
3. Create a private staging directory under `RUNNER_TEMP` and copy `data/` using
   ordinary copies, not hardlinks. Inventory/hash existing files; keep diagnostics
   outside the candidate data tree. Do not copy `.git`, credentials or the virtual
   environment. Existing immutable paths, identities, and derived evidence are
   read-only inputs to this transaction.
4. Invoke the real fetch once with `--output STAGE/data` and the fixed window.
   Record its exit code without shell `&&` suppressing later diagnostics. A
   subprocess result is preferable to a pipeline whose `tee` exit code can mask
   the fetch. Do not use blanket `|| true` or job-wide `continue-on-error`.
5. Require a **new acquisition** manifest, not the unchanged baseline after a
   crash: new run directory, `operation=acquisition`, correct window and complete
   feed registry, current-run origins, valid completion times and previous
   manifest reference to the checked baseline. Bind these facts to this
   invocation and its measured start/finish; an independently valid old manifest
   is not evidence of today's successful attempt.
6. Independently validate staged data, run the status/retention policy below,
   build `STAGE/index.html`, then execute the existing `app.verify` against that
   exact pair. Check every selected/embedded date against `E`. Do not rebuild,
   reformat or otherwise mutate accepted bytes afterward.
7. Compare the stage against the baseline inventory. Only `data/latest.json`
   may change in old data; additions must be in **this run's new**
   `data/runs/<run-id>/` subtree. No deletion, historical rewrite, derived-format
   migration or identity change is permitted by this scheduler. Include all new
   raw bodies, transport, results, group/config, CSV, quality and immutable
   manifest artifacts, not only files currently pointed to by `latest.json`.
8. Produce a candidate containing just the allowed new files, replacement
   `data/latest.json`, and replacement root `index.html`, plus an external
   inventory/receipt. The receipt records repository, base SHA, workflow run ID
   and attempt, frozen cutoff, acquisition run, fetch result, verification result,
   and path/size/SHA256 for every payload file. Expose its hash and the exact
   uploaded artifact ID as job outputs. No files in this bundle are executable
   inputs for the writer.

The stage is not production. `fetch` may atomically promote its *staged* latest
pointer and still return 1; that is expected. Only the outer transaction decides
whether the checkout/published branch should move.

### B. Classify before permitting persistence

| Observed outcome | Eligible to persist data + HTML? | Final workflow result |
|---|---|---|
| Fetch 0; all 15 attempts fresh success; verification and safety checks pass | Yes | Success if persistence and enabled deployment also succeed |
| Fetch 1; all 8 index attempts fresh success; each QVIX fresh success/partial; at least one partial; verification and safety checks pass | Yes, with unchanged partial flags/nulls/disclosures | **Nonzero: validated partial persisted** |
| Fetch 1 with any feed `failure`, stale reuse, or missing snapshot | No | **Nonzero: acquisition failure; production unchanged** |
| Fetch 1 but no new completed acquisition, all-success manifest, or other exit/status mismatch | No | **Nonzero: orchestration/invocation failure** |
| Other exit code, signal, driver deadline, malformed/incomplete manifest | No | **Nonzero: execution failure** |
| Raw/sidecar/time/comparator/HTML verification fails; current-day rows; old evidence changes; source date-set contraction | No | **Nonzero: candidate rejected** |
| Valid candidate, but upload/receipt/branch/push check fails | No new publication by this run | **Nonzero: persistence failure/conflict** |
| Push succeeds, enabled Pages deployment fails | Git candidate remains persisted; prior site may remain | **Nonzero: deployment failed, not data rollback** |

Do not whitelist today's defect counts, error messages, or a particular QVIX
feed. `partial` is acceptable only because the normal independent verifier proves
that exact snapshot's declared quality under the current contract. New blank,
error and conflict evidence remains partial even when it has no finite close.

**Deliberate stricter publication policy:** the acquisition layer can validly
recover siblings and produce a verified stale/failure report; daily automation
still withholds the entire public update after any fatal feed attempt. Keep that
candidate and its actual stale status in failure diagnostics. This sacrifices
availability of new successful siblings until a later run, but prevents a failed
feed silently becoming an ordinary published refresh. Do not change `state_after`
or claim that a verified stale report is corrupt. The public page remains the
last accepted report, not a live status view of the latest failed attempt.

### C. Persistence on a separate runner

- The writer depends on successful preparation plus explicit `eligible=true`;
  missing/malformed outputs mean refusal. Its fresh checkout is exactly
  `base_sha`. It downloads only the same run/attempt's identified candidate, not
  the latest artifact by a reusable name and not artifacts from other workflows.
- Check the receipt against trusted preparation outputs and rehash every file.
  GitHub artifact download digest mismatch is documented as a **warning**, so
  implement an explicit fatal payload-hash check rather than assuming the action
  fails closed.[G8] Reject extra files, absolute/traversal paths, symlinks,
  executable file modes and `.git`/workflow/code paths. Do not execute a downloaded
  shell script or load Python modules from the candidate.
- Run only reviewed repository-owned standard-library persistence code and
  reviewed Git/Actions tooling in this write-capable job. Do not install/import
  AKShare or re-run fetch/renderer dependencies here. Unchanged baseline plus
  exact verified candidate bytes is the verification argument for the final tree;
  a candidate cannot change between validation and commit.
- Apply just the receipt's allowlisted paths. Commit one tree containing the
  pointer, all referenced new evidence and root `index.html`; never commit just
  HTML or stage the entire checkout with `git add .`. The receipt is diagnostics,
  not an extra mutable pointer in `data/`.
- Recheck the current default branch name and target head against `base_sha`.
  Push only `HEAD:refs/heads/<target>`, without force, force-with-lease, pull,
  rebase, merge, cherry-pick or retry. A human push after the check makes the
  fast-forward push fail safely. Even an unrelated README change invalidates
  this attempt's base; conservative retry requires a new manual dispatch.
- Record both the input SHA and resulting data commit SHA. Recheck remote
  publication outcome before claiming it persisted. A lost network response can
  make push outcome ambiguous; a read-only ref/ancestry check may establish that
  this exact commit was accepted. If it cannot, report **unknown**, do not
  fabricate success or force/retry the push.
- A real attempt normally creates new immutable identity/times even if weekend
  prices do not change, so a new audit commit is legitimate. Do not compare only
  price CSVs and discard provenance. Repeating the writer with the identical
  receipt must recognize its already-persisted commit or refuse, never create a
  duplicate acquisition claim.

Branch protection, required PRs/checks/signatures, rulesets and token policy can
reject a push despite `contents: write`.[G7] Do not weaken them or silently switch
to a broad PAT. If direct bot updates are prohibited, the owner must choose a
reviewed PR/merge or separate data-branch design; that changes this proposal's
persistence boundary. A red daily quality job should not be installed as a
required code-integration check: expected provider partials are not code defects.

### D. Nonzero observability after useful work

Use separate `prepare`, `persist`, optional `deploy-pages`, and `quality-status`
jobs. The prepare job succeeds for an **eligible partial** because it completed
its preparation contract; its structured output still records `fetch_exit=1`.
Persist/deploy depend on eligibility, not on reinterpreting that code as clean
source data. The concluding job runs with `if: always()` after those jobs and
exits nonzero for partial, any failure, missing required output, or unknown push
outcome. Emit an explicit error annotation such as “verified QVIX partial;
data persisted at <commit>; deployment <state>”.

This avoids both failure modes: early `set -e` preventing valid partial updates,
and `continue-on-error` turning every source failure green. A Pages job must not
depend on the deliberately red concluding job. Cancellation/hard runner failure
can prevent even `always()` cleanup; GitHub's canceled/failed run is the remaining
signal, not a guaranteed uploaded artifact.

## 5. Permissions and workflow supply chain

| Job | `GITHUB_TOKEN` permissions | Reason |
|---|---|---|
| Workflow default / quality conclusion | `{}` | No API write or repository content access needed for conclusion |
| Prepare | `contents: read` | Checkout trusted default-branch code/data |
| Persist | `contents: write` only | Checkout plus one repository ref update |
| Optional Pages deploy | `pages: write`, `id-token: write`; `contents: read` for explicit ref/hash checking | Pages/OIDC deployment, no repository writes |

Unspecified permissions stay unavailable. Artifact transfer within the same run
uses Actions' artifact mechanisms; do not add `actions: write`, `issues: write`,
`pull-requests: write`, `checks: write`, or `write-all` for logging or ordinary
persistence. GitHub documents that actions can access `github.token` even when
not explicitly passed, so merely hiding the token environment variable is not
privilege isolation.[G3]

- No write token in the preparation runner, fetch subprocess, package installer,
  diagnostic bundle or HTML. Use `persist-credentials: false` for checkout; make
  the write token available only to the final trusted Git authentication step,
  never as a token-bearing remote URL or shell command text. Clear temporary auth
  in cleanup. Do not archive all of `RUNNER_TEMP`: newer checkout versions can
  store persisted credentials there.[G10]
- Do not dump environment variables, the entire GitHub context, `.git/config`,
  request authorization headers, or `set -x` output. Pass any GitHub-derived
  branch/value through a validated environment variable and quoted arguments,
  not inline expression interpolation into executable shell. No `eval`.[G4]
- Use only schedule/manual triggers for this privileged workflow. Do not add
  `pull_request_target` or consume untrusted PR artifacts through `workflow_run`.
  Manual other-branch execution must be blocked before checkout/execution of
  code that could use publication permissions.
- Lock workflow dependencies. Current primary GitHub documentation recommends
  generated `.github/workflows/actions.lock`, including transitive actions and
  source repository identity, over only top-level SHA pinning.[G11] For GitHub.com,
  recommend onboarding this workflow with `gh actions-lock`, review the generated
  file and workflow rewrites, and never run lock regeneration/`--accept-moved`
  unattended in the daily job. Reusable workflows require their own full-SHA
  pinning/dependency review; none is needed here.
- If the target platform cannot support workflow lockfiles, the explicitly
  reviewed compatibility alternative is **full 40-character upstream commit
  SHAs for every `uses`**, with human-readable version comments and a transitive
  action audit. No mutable `@main`, floating `@vN`, or invented SHA. The
  implementation must resolve actual supported versions and verify upstream
  ownership; this proposal has not selected or fetched action executables.
- Pin uv and the Python 3.14 patch explicitly; choose a named supported runner
  image rather than claiming `ubuntu-latest` is reproducible. A named hosted image
  still changes. Keep `uv.lock` frozen and verify packages through its hashes.
  Neither dependency hashes nor action locks prove upstream code is safe, nor
  authenticate the providers' HTTP market data. Avoid curl-to-shell bootstrap and
  caches of credentials or mutable `data/`.
- The repository already records a security advisory affecting pinned pytest
  9.0.2. `--no-dev` keeps that unnecessary package out of the daily runtime; it is
  not a remediation claim for development gates. Any dependency change requires
  its own review rather than a hidden lock update in this scheduling task.

## 6. GitHub Pages: explicit boundary, no token-trigger assumption

README currently says pushing `index.html` to `master`/root publishes Pages.
GitHub explicitly documents the exception: commits pushed by a workflow using
`GITHUB_TOKEN` do **not** trigger a branch-based Pages build.[G5] Also, a normal
`on: push` deployment workflow will not run just because this token pushed a
commit.[G6] Adding `.nojekyll` does not change either trigger rule.

Recommended automatic-site option:

1. Repository owner switches Settings → Pages → Source to **GitHub Actions** and
   configures the `github-pages` environment to admit only the intended default
   branch. Redistribution approval is a separate prerequisite.
2. An explicit repository variable, for example `PUBLISH_PAGES=true`, enables the
   workflow's Pages job after that setup. With it disabled, the workflow promises
   repository persistence only and reports `deployment=disabled`, not “site
   updated”. If automatic Pages is part of the selected delivery scope, that
   disabled state remains an **external setup blocker**, not a completed feature.
3. After successful persistence, package only the **exact verified** root
   `index.html` as the site artifact. Do not upload `.`: raw data, retained
   failures, diagnostic logs, repository metadata and unrelated research are not
   necessary for this self-contained page. Use the official locked
   `upload-pages-artifact`/`deploy-pages` actions.[G9]
4. Check that the target still identifies the just-persisted data commit before
   deployment; otherwise abort rather than overwrite a newer site with an older
   artifact. Keep all site writers on the same workflow-level concurrency group.
   Git push and Pages deployment are not a cross-service atomic transaction.
5. Give only the deployment job `pages: write` and `id-token: write`, and set
   `environment: github-pages`. A validated partial remains deployable before the
   final quality job turns the overall run red. Fatal/rejected/unpersisted
   candidates never reach this job.
6. Record source/event SHA, data commit SHA, artifact/HTML hashes and returned site
   URL separately. The workflow event SHA is the input code revision, not
   automatically the data commit created later in the job; do not mislabel the
   deployment's associated revision. A subsequent Pages failure must not revert
   a valid Git commit or cause another provider fetch merely to retry deployment.

Keeping branch-based Pages instead requires an explicit alternate triggering
identity such as a least-privilege GitHub App installation token, or a later
human publication action. A PAT/App adds secret custody, rotation, permissions,
branch-rule interaction and potentially recursive `push` workflows; it is not the
recommended default. GitHub's documented `workflow_dispatch`/`repository_dispatch`
exceptions can trigger another workflow with `GITHUB_TOKEN`, but add API rights
and orchestration without benefit over a deployment job in this same run.[G6]

No repository file can prove or silently change hosted Pages mode, environment
approval rules, branch permissions or data-redistribution authorization.

## 7. Diagnostics, retention, and recovery

Create a structured outcome before the first risky command and update it at
phase boundaries. Include:

- Event name/cron, actual UTC start/finish, frozen requested window, repository,
  default branch, input SHA, workflow run ID/attempt and link.
- Fetch exit/signal/deadline; new acquisition identity or an explicit absence;
  each of 15 feed attempt statuses, snapshot status, stale reuse, snapshot origin,
  observed ranges, full/selected quality counts and comparator state.
- Separate baseline/data/HTML verification results and their stdout/stderr;
  rejected paths/date contractions; stage and HTML hashes; selected maximum date.
- `eligible`, `persisted`, `data_commit`, remote outcome, Pages enabled/result/URL,
  and final conclusion. Missing values mean unknown/not reached, not success.
- Python/uv/dependency versions, lock hash and runner identity sufficient to
  reproduce offline checks. Do not claim hashes authenticate source economics.

Upload uniquely named artifacts containing the current attempt's new run subtree,
command logs, outcome, receipt, and candidate HTML if available. On failure, retain
incomplete bodies/results too; without them a promotion error cannot be diagnosed.
Do not repeatedly upload all old immutable history. Use `if: always()` for
best-effort diagnostics with an explicit **14-day** retention request (subject to
repository/org limits), and fail an expected diagnostic/candidate upload that
silently produced no files. Artifacts expire or can be deleted; they are not a
permanent historical data store.[G8]

Accepted raw/normalized/provenance evidence is permanently retained in the Git
candidate. Rejected/fatal new evidence is retained in the run artifact only;
operators needing it beyond retention must download it before expiration. No
“failure-only commit” is recommended: it adds another mutation path to a failed
transaction. The last accepted root page can therefore lag the latest failed
attempt; use the workflow outcome to diagnose freshness.

Write a concise job summary with per-feed status, acquisition versus integrity
versus persistence outcome, data commit and Pages state. Preserve nonzero quality
as described above. GitHub notifications depend on user settings; scheduled
notifications go to the creator/cron editor, or the user who re-enabled a disabled
schedule, not necessarily every maintainer.[G12] Expected daily partials can cause
alert fatigue; use explicit job/summary labels, not a green workflow that hides
them. An external “no run happened” freshness alert is not provided by this cron:
a dropped/disabled schedule may produce no failed job and no notification.

Recovery:

- Provider outage, missed days, or conflict: inspect the artifact, resolve the
  external issue if necessary, then dispatch a new full refresh on current default
  HEAD. Do not retry within the same run to obtain cleaner source data.
- Integrity failure: preserve the old Git entry points, diagnose/review the code
  or data defect, then run the ordinary full window. Do not weaken verification.
- Pages-only failure after persistence: retry only the deployment for the exact
  committed HTML after checking current branch/artifact identity. If the artifact
  expired, retrieve that committed HTML, not a newly fetched approximation.
- Intentional historical analysis can still use the existing local `--end`
  command in a separate output directory; publishing an older cutoff through
  scheduled/manual automation is not part of this design.

Observed size: retained `data/` contains 152 files / 22,488,124 bytes; its current
acquisition run contains 72 files / 9,916,501 bytes; root `index.html` is 6,037,507
bytes. **[INFERENCE]** One similar immutable run per day adds approximately
3.62 GB/year of uncompressed files before Git compression and future source growth;
this is not a measured repository-pack forecast. Full-source acquisition makes
that growth explicit, and 30-day local selection does not remove the raw-evidence
cost. Budget clone/staging disk, Git size and Actions artifact storage before
turning it on; no automatic pruning, LFS migration, or audit-history deletion is
included. A future archival/content-addressing design requires independent review
of every retained reference.

## 8. Concrete implementation boundaries

Proposed files, not files created by this research:

- `.github/workflows/daily-refresh.yml`: triggers, fixed concurrency group,
  permission-separated jobs, explicit runtime/tool versions, bounded runtime,
  artifact handoff, optional Pages deployment and concluding nonzero status.
- `.github/workflows/actions.lock`: generated/reviewed action dependency closure
  for the workflow on supported GitHub; otherwise documented full-SHA compatibility
  choice. Do not introduce both as competing hand-maintained conventions.
- `app/daily.py`: small argparse/std-library orchestration module with explicit
  preparation and persistence boundaries, injectable clock for deterministic
  checks, JSON outcome/receipt, path/hash checks and safe Git ref update. In the
  writer mode it must not import provider/renderer dependencies. Reuse the real
  fetch/chart/verify CLIs and their authoritative registries/validation in prepare;
  do not duplicate a financial normalizer or teach YAML to interpret manifests.
- `tests/test_daily.py`: focused transaction/date/outcome/conflict regressions.
  Preserve existing v4 data semantics and existing `tests/test_contracts.py`.
- `README.md`: actual schedule/date semantics, full-refresh decision, partial
  publication plus red status, exact commands, Git/Pages setup separation,
  permissions, retention/storage/notification limits and recovery instructions.

No required changes to `app.fetch` exit semantics, v4 normalization, immutable
manifests, panel mappings, chart surface, or independent verifier. If a needed
invariant cannot be enforced by the orchestration layer, stop for plan review
rather than quietly weakening it. A new overlap merger, schema migration, source
retry service, issue bot, trading-calendar dependency or self-hosted runner is
outside this slice.

## 9. Deterministic acceptance scenarios

These are proposed acceptance checks, **not tests executed for this proposal**.
Use fixed UTC clocks, temporary copies of retained evidence, real offline
rendering/verification, and disposable local bare Git remotes for transaction
races. No live market request, real GitHub push, browser, or deployment is needed
for these local scenarios. Exercise observable output/branch state, not YAML text
or mocked success returns. Existing contract tests already cover QVIX grouping,
shared-worker recovery, timestamp validity, stale behavior and visible tampering;
new tests should cover the automation boundary rather than duplicate those tests.

| Scenario | Required observable result | AC |
|---|---|---|
| UTC midnight, year boundary, leap day, and non-UTC process timezone | One frozen `E = UTC-start-date - 1`; inclusive full window; no local-date dependence | 17,18 |
| Cron intended Monday but starts Tuesday; run crosses another midnight | Cutoff is Monday and stays frozen; nominal cron timestamp is not fabricated | 18,20 |
| Weekend/holiday response ends Friday | Friday remains last observed date; no Saturday/Sunday rows or fabricated fill | 18 |
| Source has a row on execution day and a malformed row outside selection | Valid current-day row retained raw but absent from selected CSV/HTML; malformed full response still rejected | 18,19 |
| Correction older than 30 days | Full-refresh candidate contains corrected old value with new whole-snapshot provenance; old evidence unchanged | 18,19 |
| Accidentally narrow candidate window, or a previously observed raw date disappears | Reject automatic persistence; old pointer/page/remote remain unchanged; diagnostics name lost window/dates | 18,19 |
| Fresh QVIX blank/error/conflict revision keeps the common dates | New nulls replace prior prices, no stitching/stale flag; partial candidate may persist, final status 1 | 18,19 |
| Clean all-feed success, code 0 | Exact verified files reach one commit; both pointer and root page refer to same run; final status 0 | 17,19 |
| Eight index successes, seven fresh QVIX partials, code 1 | All independent checks pass; candidate persists/deploys if enabled; quality job remains nonzero and labels partial | 17,19,20 |
| One fatal index/QVIX with valid prior; another case without prior | Candidate truthfully contains stale/unavailable state; no public update; old Git tree unchanged; failure evidence retained | 19 |
| Process raises/terminates leaving yesterday's valid `latest.json`; exit 1 with all-success data; exit 0 with partial state | None is mistaken for eligible partial; require this invocation's completed identity and exit/status agreement | 19 |
| Native completion has missing times, incomplete member, altered raw/quality/comparator, or a hidden/contradictory HTML warning | Existing verifier rejects; transaction cannot push even if child fetch returned an expected code | 19 |
| Disk/write failure during stage, chart, receipt, or candidate upload | No Git publication; prior data/page remain paired; available diagnostics explain the reached phase | 19 |
| Old immutable file edited/deleted, extra workflow/code file, symlink, traversal path or candidate hash mismatch | Reject at inventory/transfer boundary before Git stage; no executable artifact is run | 17,19 |
| Human changes target before preparation, before commit, or between final check and push | Early stale-base refusal or non-fast-forward failure; human commit preserved; no rebase/force/retry | 17,19 |
| Manual dispatch on another branch/tag; default branch changes; rerun of obsolete SHA | Refuse publication and, when detectable early, refuse acquisition; new dispatch required | 17,20 |
| Two simultaneous writers from the same base against a local remote | At most one succeeds; rejected writer leaves winner intact. Hosted concurrency queue semantics remain a separate external check | 17,21 |
| Same receipt reused after successful persistence | No duplicate acquisition/commit or overwrite; report exact already-persisted identity or refuse | 19 |
| Push accepted but client response lost; later remote lookup unavailable | Distinguish persisted when provable from unknown; no invented success and no force rollback | 19,20 |
| Pages disabled, Pages enabled with valid partial, Pages failure after Git success | Report disabled/partial-deployed/deploy-failed distinctly; never gate eligible partial on final green status; never revert valid data | 17,20 |
| Diagnostic upload fails or process is canceled before cleanup | Nonzero/canceled run, no promised artifact; successful earlier push is not relabeled unpersisted | 19,20 |
| Writer runner has no application dependencies or provider credentials | Can only validate receipt/apply allowed bytes/push; acquisition packages are unnecessary in the privileged job | 17,19 |

For implementation acceptance, run the existing documented full gates on the final
union tree: frozen sync, compileall, root Ruff, pytest including new deterministic
scenarios, chart build and independent data/HTML verification. A syntax check is
not a typecheck; this repository has no separate typecheck/build framework.
Workflow schema/action-lock validation is additional. Local Git races and static
workflow review do not prove GitHub scheduler delivery, permission enforcement,
notifications, hosted pushes or Pages availability. Independent plan and final
whole-change review must assess the selected policy and these remaining limits.

## 10. External setup and evidence limits

Before enabling unattended publication, an owner must establish:

- Workflow merged to the actual default branch; Actions and chosen locked actions
  permitted by repository/organization policy; available runner minutes/storage.
- A permitted GitHub Actions write-token/direct-update path compatible with branch
  protections and rulesets. No assumptions about bypass or automatic PR approval.
- If publishing Pages: Pages Actions mode, environment/branch rules and any
  approvals, compatible plan/site settings, and approved redistribution of raw,
  normalized and HTML-embedded provider values. The existing local-experiment
  disclaimer is not a distribution license.
- Notification ownership/settings, schedule re-enable procedure, and acceptance
  that an absent/delayed run is not detected by this workflow alone.
- Actual connectivity from GitHub-hosted runners and source behavior. Static
  source inspection and retained data do not establish new live availability,
  HTTPS authenticity for the pinned HTTP QVIX source, or economic correctness.

This research read README, pyproject, active AC17–21, relevant acquisition/core/
renderer/verifier code and existing test declarations; inspected retained manifest
states and file sizes; and read primary GitHub documentation below. No tests,
provider fetch, browser, remote push, deployment, or action executable was run.
The only requested persistent deliverable is this proposal. Hosted acceptance
must be recorded later as actual evidence, not inferred from local file creation.

## Primary GitHub references

- **[G1]** [Events: schedule and workflow_dispatch](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) — UTC default, delay/drop, default-branch and inactivity behavior; [manual dispatch](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch).
- **[G2]** [Control workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) — running/pending semantics, pending replacement and ordering limits.
- **[G3]** [Use GITHUB_TOKEN for authentication](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token) — job permissions and implicit action token access.
- **[G4]** [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use) — least privilege, script injection, untrusted workflow/artifact risks and action supply chain.
- **[G5]** [Configure a Pages publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#troubleshooting-publishing-from-a-branch) — explicit GITHUB_TOKEN branch-build exception and Pages Actions mode.
- **[G6]** [Trigger a workflow from a workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow#triggering-a-workflow-from-a-workflow) — token-created push suppression and dispatch exceptions.
- **[G7]** [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) — PR/check/signature/push restrictions.
- **[G8]** [Store and share workflow artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data) — retention limits, artifact identity and digest-mismatch warning behavior.
- **[G9]** [Custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) — site artifact, deployment dependencies, environment and minimum Pages/OIDC permissions.
- **[G10]** [actions/checkout upstream README](https://github.com/actions/checkout) — credential persistence opt-out and version-dependent storage location.
- **[G11]** [Workflow dependency lockfiles](https://docs.github.com/en/actions/concepts/security/workflow-dependency-lockfiles) and [onboarding](https://docs.github.com/en/actions/how-tos/secure-your-work/lock-workflow-dependencies) — generated actions.lock, transitive pins, repository identity, reviewed updates and compatibility limits.
- **[G12]** [Notifications for workflow runs](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs) — user preferences and scheduled-notification ownership/re-enabling.
