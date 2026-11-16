# Daily refresh whole-change review — round 2

## Verdict: PASS

Independent final whole-change REVIEW-LOOP against `f16be449c1`, controlled by active AC17–21, P-D1/P-D2 and D19/D20 in `docs/goals/sentiment-index-history.md`. **D-R1, S1 and S2 close. No new or reopened actionable Fix/Replan findings; no Discards or newly accepted risks.** This is repository implementation/review convergence, not certification of hosted execution or the parent's final-tree gates/ledger closure.

## Scope and method

Read the original correctness and security round-1 reports, original plan review and plan-delta review before assessing the corrections. Inspected the entire owned scope, including untracked files that `git diff f16be449c1` alone omits:

- `.github/workflows/daily-refresh.yml`
- `app/daily.py`
- `app/daily_transfer.py`
- `tests/test_daily.py`
- `README.md` and `AGENTS.md` changes
- `docs/daily-refresh-implementation-evidence.md`

Also followed actual acquisition/cached-worker completion and promotion in `app/fetch.py`, and immutable/shared identity, time, raw/CSV/quality replay and report verification in `app/verify.py`. Requested LSP references for `app/daily.py:36` (`eligibility`); server returned `Unknown request: textDocument/references`, so source inspection supplied the unavailable-server fallback. No implementation or ledger edits, commits, live providers, real remote pushes, deployment, browser or subdelegation. Only this report was authored. Disposable test repositories and temporary outputs were removed.

## Prior findings

### D-R1 — closed: actual cached acquisition interval

`app/daily.py:57–62` retains member attempt ≤ success ≤ finish inside the enclosing manifest, itself inside the measured invocation. QVIX acquisition is now bounded by manifest begin and each member's successful completion; index acquisition retains its own attempt/finish bounds. The independent verifier still binds the immutable native result, invocation/config/group, shared response acquisition time, transport and hashes. No worker timestamps or immutable evidence were rewritten to pretend seven downloads occurred.

Independently ran the real preparation fixture directly, outside pytest collection, with its advancing microsecond acquisition clock, eight actual index workers, seven actual cached QVIX wrappers, real rendering and separate-process baseline/candidate verifier. Retained Sina bodies and an all-blank QVIX revision supplied HTTP; no live source access. Observed:

```text
eligible: True quality: partial fetch exit: 1 cutoff: 2026-11-15
qvix_50index attempt: 00:05:02.000034 shared: 00:05:02.000035 success: 00:05:02.000036
qvix_50etf   attempt: 00:05:02.000038 shared: 00:05:02.000035 success: 00:05:02.000039
qvix_100etf  attempt: 00:05:02.000041 shared: 00:05:02.000035 success: 00:05:02.000042
qvix_300index attempt: 00:05:02.000044 shared: 00:05:02.000035 success: 00:05:02.000045
qvix_300etf  attempt: 00:05:02.000047 shared: 00:05:02.000035 success: 00:05:02.000048
qvix_cyb     attempt: 00:05:02.000050 shared: 00:05:02.000035 success: 00:05:02.000051
qvix_kcb     attempt: 00:05:02.000053 shared: 00:05:02.000035 success: 00:05:02.000054
```

All times above are on 2026-11-16 UTC. Later six members genuinely start after the shared acquisition and now remain eligible. Each QVIX snapshot was fresh partial with 2848 selected rows, null prices and retained common raw dates. The integration tests additionally assert the current-day raw observation is retained but excluded from selected traces, old history survives, observed dates end Friday November 13 without weekend fabrication, and the frozen cutoff survives finishing across midnight. Old/future acquisition, completion-bound and member-order refusal cases passed for index and QVIX.

Extended the direct preparation probe through a complete local publication: committed the actual retained baseline `data/`, `index.html` and lock into a disposable Git repository, rebound only the fixture receipt's test invocation identity/hash to that local base, published the real prepared payload, checked every remote payload blob against its receipt size/hash and required the complete parent list `[base]`. Cloned the published remote and ran the actual independent verifier against that clone's full data/page, not just the preparation directory:

```text
published clone: Offline verification passed: eight panels, seven raw/wrapper/artifact/quality replays
real conclusion: exit1 after exact partial publication; all payload bytes and sole parent verified
```

Executed the workflow's actual conclusion shell with this partial outcome: persistence precedes the expected red exit1. Direct preparation/publication/clone-verification probe exited0 in 25.94s.

### S1 — closed: exact expected-base transaction, sole parent

`app/daily_transfer.py:117–124` requires the full parent output exactly `[commit, receipt base]`, then makes one push of that exact commit with explicit `--force-with-lease=refs/heads/<branch>:<base>`. It uses neither an inferred tracking-ref lease nor generic force. Prechecks and exact read-back remain; no retry/rebase/fallback. Accepted transition is therefore base→child, preserving history while atomically requiring the expected ref value.

Daily regressions independently passed: successful exact-base publication/replay refusal; divergent human race; rollback-to-ancestor after the final precheck; wrong and multiple parent rejection before push; accepted push with a lost response or timeout proved solely by exact read-back.

Additional independently chosen disposable-remote probes exercised edges beyond the regression set:

1. Delete target ref immediately before the one push: rejected; target remained absent, not recreated; exactly one receipt-base lease push.
2. Roll back the target **inside the bare remote's pre-receive hook**, after push advertisement rather than before `git push`: rejected by receive-side old-value checking; competing ancestor and its original README remained intact. Exactly one receipt-base lease push.

Observed receive-side output:

```text
remote: INJECTED-ROLLBACK
! [remote rejected] ... -> main (incorrect old value provided)
RuntimeError persistence unknown/rejected for ...; push exit 1
rollback-in-receive: rejected; competing ancestor preserved; one lease push
```

Probe method: create two baseline commits with `repo_pair`, build `small_bundle`, install this temporary pre-receive hook, instrument only the publisher's Git wrapper to count actual push calls, call the real `publish`, then inspect the bare remote directly:

```sh
#!/bin/sh
cat >/dev/null
unset GIT_QUARANTINE_PATH
git update-ref refs/heads/main "$ancestor" "$base" || exit 1
echo INJECTED-ROLLBACK >&2
```

The script writes the concrete test ancestor/base into the hook. Initial hook setup without clearing the quarantine environment did not establish the injected rollback and failed the probe's fixture assertion; it was not a product finding. Corrected hook emitted the marker and the transaction rejection above. No implementation was changed for either probe.

D20's disclosed ABA limitation remains accurately stated: ref equality does not detect base→other→base, nor lock later writers. This is the already-reviewed external concurrency boundary, not a new waiver.

### S2 — closed: explicit external exact-byte recovery

`README.md:97–116` now says no deploy-only command/dispatch exists. It explicitly rejects failed-job reruns because the attempt changes, and all-job reruns after persistence because the event base is obsolete. A new default-branch dispatch is a new refresh, not exact-byte deployment recovery. No receipt/hash/attempt relaxation was added.

The documented authorized external/manual procedure binds original run/attempt, repository/default branch/event base, persisted commit, trusted receipt hash and HTML hash; reads committed HTML without rerender/fetch; requires current remote-target and deployment authorization/environment checks; and verifies the deployed bytes. This matches the plan delta's expressly selected external operational boundary, without implying a supplied recovery implementation.

Independently executed the actual `python -I -S app/daily_transfer.py` CLI on a disposable accepted publication with the same run and attempt2: `pages` exited1 with `invocation identity mismatch`, created no site directory; `check` against the old event base exited1 with `remote base changed`. The documentation now describes those enforced outcomes accurately. Existing stdlib CLI/one-file exact Pages-package regression passed too.

## Whole original scope assessment

| Contract | Independent assessment |
|---|---|
| AC17 — workflow and least privilege | UTC cron/manual default-branch guards, fixed non-cancelling concurrency, explicit job/driver deadlines and empty default permissions are present. Preparation is read-only and credentials are not persisted; acquisition subprocesses lose `GH_TOKEN`. Fresh contents-write job executes trusted checked-out stdlib transfer/Git, not payload code. Only Pages has Pages/OIDC rights. Top-level actions are SHA-pinned; upstream identity evidence is not misrepresented as transitive supply-chain assurance. `actionlint` passed. |
| AC18 / P-D1 — full history and cutoff | One actual-start UTC-yesterday cutoff, explicit start2000, no rolling merge. Real render/verifier path and leap/year/timezone/cross-midnight tests passed. Selected values and independently reconstructed trace dates are cutoff-bound; full raw may contain current-day rows. Source-loss protection compares overlapping raw date sets, including QVIX blank common dates, not close counts/endpoints. Beginning/middle/end and equal-count replacement refusal, fresh null retention and old-value revision cases passed. |
| AC19 / P-D2 — verification and immutability | Actual baseline verification precedes copying/acquisition; actual candidate chart/independent verifier precede eligibility. New run/current member origin, exact previous/window/registry/time/exit agreement and fresh statuses are required. Old immutable inventories include unreferenced evidence; additions are confined to a new run. Crash/no promotion, immutable historical mutation, hidden disclosure and valid-but-fatal/stale candidates refuse a bundle and preserve public baseline bytes in executed regressions. |
| AC19 / D20 — handoff and persistence | Receipt hash is a trusted preparation output; workflow selects the exact current-run artifact ID, without a name fallback. Identity includes repository/branch/base/run/attempt. Allowlist/inventory rejects extra/missing/hash/path/link/executable/identity attacks. Fresh clean exact-base checkout, destination checks and actual staged blob/mode verification precede commit. One exact-parent/lease push and exact read-back pass successful, competing, rollback, deletion and ambiguous-response probes. Hashes establish consistency, not provider authenticity or a sandbox against a compromised preparation job. |
| AC17/19 — quality and Pages | Fresh success/partial can publish; fatal/stale never does. Actual partial preparation→publication→red shell path passes, as do clean/disabled/deployed-partial/deploy-failure conclusion cases. Pages receives only receipt-bound HTML after persistence and rechecks target immediately before deployment. Disabled is explicit; failure does not roll back Git. No new HTML/browser behavior is claimed. |
| AC20 — operations | README covers full refresh, cutoff, dropped/delayed/inactive scheduling, pending replacement, permissions/setup, optional Pages, red partial/fatal policy, diagnostics/retention/storage growth, alerts and missing-run limits, supported recovery distinction and source/publication/license limitations. S2's former misleading recovery route is removed. |
| AC21 — evidence/accounting | Implementation evidence distinguishes earlier results from corrective results and external execution limits. AGENTS lessons match corrected contracts. Active ledger still marks the implementation/review work and three findings open pending independent acceptance; it does not prematurely claim daily completion. This report supplies closure evidence; the parent must reconcile that ledger and run its required final union gates. No untriaged omission or weakened/silently superseded obligation found. |

## Verification record

Ran once for this review:

```sh
uv run --frozen pytest -q tests/test_daily.py && actionlint .github/workflows/daily-refresh.yml
```

**Exit0: 51 passed, two known upstream mini-racer deprecation warnings, pytest57.36s / command58.56s.** This includes actual preparation/render/verifier, withholding, local publication/races, stdlib CLI/Pages package and real conclusion-shell cases, not only YAML/source assertions.

Additionally executed temporary stdin Python probes as described above: deleted-ref race; corrected receive-hook rollback race; same-attempt/base recovery rejection CLI; and actual advancing-time preparation through complete baseline-backed publication, fresh clone verification and red partial conclusion. All corrected probes passed. No full-suite rerun or hosted verification claimed; parent's final-tree union remains its responsibility.

## External boundaries

No new risk is accepted to obtain PASS. Existing documented external hosted setup/execution remains unproved locally: scheduler delivery, artifact service, credentials/branch rules, runner/network/provider behavior, notifications, Pages/environment approvals and redistribution permission. ABA and Git-versus-Pages non-atomicity remain explicit under the approved plan. This review does not certify economic source correctness, HTTP authenticity or unchanged browser behavior. No actionable repository finding remains in the reviewed daily-owned scope.
