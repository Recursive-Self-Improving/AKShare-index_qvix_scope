# Daily refresh plan delta review

## Verdict: PASS — plan only

Independent review of only D20 and revised P-D2 in `docs/goals/sentiment-index-history.md` against S1/S2 in `daily-refresh-security-review-round1.md`. No implementation certification: the existing owned implementation remains red and uncommitted; S1/S2 stay open until correction and independent verification. No new plan-level Fix/Replan findings.

## S1: expected-base transaction

The selected mechanism closes the reported gap without weakening the approved no-history-rewrite invariant:

- Let B be the receipt/event-bound exact base, C the sole new publication commit, and R the target branch ref. Require C's complete parent list to be exactly `[B]`, not merely its first parent or an ancestry relationship. Preserve the existing allowlisted tree/blob/mode verification.
- Push only C to `refs/heads/<branch>`, once, with explicit `--force-with-lease=refs/heads/<branch>:<base>`. The expected value is B, not a remote-tracking ref or a newly fetched value. No generic force, rebase, retry, or replacement base.
- The explicit lease checks the advertised target against B; Git's receive-side ref transaction also checks its old value while updating the ref. Thus a divergent commit or rollback to an ancestor that is still current at the transaction cannot be overwritten. This closes the precheck/push TOCTOU gap: the protection is not another client-side observation.
- When accepted, the transition is B→C and C has exactly B as its sole parent. The lease option permits conditional force in general, but this independently enforced parent constraint makes this particular accepted update a strict fast-forward. No existing target history is removed by the publisher.
- Concurrent deletion or another non-B value likewise cannot be treated as permission to publish. Server branch protections may reject this command; rejection is fail-closed, not grounds for a fallback push.

**ABA limitation:** equality cannot detect B→X→B before the checked update. The plan guarantees rejection of a competing non-B current ref, not detection of every historical movement. A different authorized writer can also move the ref after publication; this mechanism is not a durable branch lock or an atomic Git-plus-Pages transaction.

The corrective implementation must prove both divergent and rollback-to-ancestor races leave the competing ref untouched, preserve the successful exact-base path, and reject a commit whose full parent list is not exactly `[B]`. Preserve existing ambiguous-push exact read-back handling without making a second push; read-back is observation, not a retry or a substitute for the lease.

## S2: recovery boundary

D20 correctly chooses documentation correction rather than relaxing same-attempt receipts or adding a deployment subsystem:

- Failed-job Pages-only reruns and all-job reruns after persistence are explicitly unsupported for recovery of this case under the existing identity/base checks.
- Exact-byte recovery is an external/manual operational step, absent from this workflow: an authorized operator must identify the accepted persisted commit and verify the deployed `index.html` bytes against that committed artifact. Existing authorization/environment requirements still apply; do not mutate the old receipt's attempt/hash to bypass checks.
- A new default-branch dispatch is a new refresh, not a deployment-only retry and not a promise of the same bytes.

This matches S2's expressly permitted external/manual disposition. README correction must make these limitations explicit rather than imply a supplied deploy-only command exists.

## Preserved safety and review boundary

The delta retains baseline/candidate verification, immutable inventory and payload allowlist, receipt identity/hash binding, separate permissioned publisher, exact verified Pages bytes after persistence, partial/fatal policy, bounded diagnostics, and no provider retry. It supersedes only the literal ordinary/non-force push mechanism and misleading recovery instructions; it does not authorize broad force, historical rewriting, new permissions, receipt relaxation, or a new recovery service.

Verification performed: static comparison of the two named documents and reasoning about the specified Git ref transaction. No code review, tests, live requests, push, deployment, browser, heavy work, subdelegation, commit, implementation edits, or ledger edits performed. The parent's corrective implementer and subsequent independent review own executable proof and closure of S1/S2.
