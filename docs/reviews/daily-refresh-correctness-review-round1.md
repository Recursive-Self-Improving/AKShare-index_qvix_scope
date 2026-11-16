# Daily refresh correctness review — round 1

## Verdict: FIX

Independent implementation review against `f16be449c1`, AC17–21, P-D1/P-D2, D19 and `daily-refresh-plan-review.md`. One high-priority correctness finding; no PASS or green-checkpoint certification. No production code, ledger, live provider, real remote, deployment, browser, delegation or commit changes performed. This report is the only review-authored repository change.

## D-R1 — High / Fix: shared QVIX acquisition predates later member attempts

**Location:** `app/daily.py:57–60`; coverage defect at `tests/test_daily.py:256–260` (the fixture's constant `app.fetch.now`).

`eligibility` requires each snapshot's acquisition timestamp to fall between that member's `attempted_at` and `finished_at`. That is correct for independently acquired index responses, but wrong for the cached QVIX group. `app/fetch.py:122–141` captures the shared response once; `:144–163` starts each successive wrapper attempt and assigns the same earlier `group['acquired_at']` to every successful member. The second through seventh members normally begin **after** the shared acquisition. They are valid fresh run-local results, not stale data.

Consequently a normal otherwise eligible daily acquisition is rejected at `acquisition time qvix_50etf`, after real rendering and independent verification pass. Prepare exits unsuccessfully, persist/Pages never run. This breaks AC17/19 and P-D2 end to end, including the permitted partial-publication path. It is not an external GitHub/provider limitation.

### Independently observed evidence

Ran `uv run --frozen pytest -q tests/test_daily.py`: **40 passed**, two existing mini-racer deprecation warnings, **57.12s**. Ran `actionlint .github/workflows/daily-refresh.yml`: exit0.

Then reran the real preparation fixture with its actual eight index workers, shared seven QVIX wrappers, renderer and separate-process verifier, changing **only** its frozen acquisition clock to an increasing microsecond clock. All response bodies remained the fixture's retained/synthetic HTTP; no provider request or publication occurred. Observed:

```text
sh000001 success 6509
sh000016 success 5552
sz399330 success 5053
sh000300 success 6030
sz399006 success 3995
sz399673 success 3017
sh000680 success 1663
sh000688 success 1663
qvix_50index partial 2848
qvix_50etf partial 2848
qvix_100etf partial 2848
qvix_300index partial 2848
qvix_300etf partial 2848
qvix_cyb partial 2848
qvix_kcb partial 2848
INDEPENDENT PROBE: ValueError acquisition time qvix_50etf
eligible: False phase: candidate verification
candidate verification last line: Offline verification passed: eight panels, seven raw/wrapper/artifact/quality replays
qvix_50index attempted: 2026-11-16T00:05:02.000034+00:00 acquired: 2026-11-16T00:05:02.000035+00:00
qvix_50etf attempted: 2026-11-16T00:05:02.000038+00:00 acquired: 2026-11-16T00:05:02.000035+00:00
qvix_100etf attempted: 2026-11-16T00:05:02.000041+00:00 acquired: 2026-11-16T00:05:02.000035+00:00
qvix_300index attempted: 2026-11-16T00:05:02.000044+00:00 acquired: 2026-11-16T00:05:02.000035+00:00
qvix_300etf attempted: 2026-11-16T00:05:02.000047+00:00 acquired: 2026-11-16T00:05:02.000035+00:00
qvix_cyb attempted: 2026-11-16T00:05:02.000050+00:00 acquired: 2026-11-16T00:05:02.000035+00:00
qvix_kcb attempted: 2026-11-16T00:05:02.000053+00:00 acquired: 2026-11-16T00:05:02.000035+00:00
```

Reproduction (stdin script leaves no permanent fixture/scripts):

```sh
uv run --frozen python - <<'PY'
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import timedelta
import pytest
spec = importlib.util.spec_from_file_location('review_daily_tests', 'tests/test_daily.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
original = pytest.MonkeyPatch.setattr
counter = iter(range(1000))
def patched(self, target, *args, **kwargs):
    if target == 'app.fetch.now':
        args = (lambda: (m.FIXED + timedelta(seconds=2, microseconds=next(counter))).isoformat(),)
    return original(self, target, *args, **kwargs)
with TemporaryDirectory() as temp, pytest.MonkeyPatch.context() as patch:
    class Factory:
        def mktemp(self, name):
            p = Path(temp) / name
            p.mkdir()
            return p
    patch.setattr(pytest.MonkeyPatch, 'setattr', patched)
    try:
        m.real_prepared.__wrapped__(Factory())
    except Exception as e:
        print('INDEPENDENT PROBE:', type(e).__name__, str(e))
        work = Path(temp) / 'daily-real/work'
        outcome = json.loads((work / 'diagnostics/outcome.json').read_text())
        print('eligible:', outcome['eligible'], 'phase:', outcome['phase'])
        print('candidate verification last line:', (work / 'diagnostics/candidate.log').read_text().splitlines()[-1])
        manifest = json.loads((work / 'stage/data/latest.json').read_text())
        for feed in m.QVIX_FEEDS:
            s = manifest['feeds'][feed]['snapshot']
            print(feed, 'attempted:', s['attempted_at'], 'acquired:', s['acquired_at'])
    else:
        raise AssertionError('Expected independently reproduced acquisition time rejection')
PY
```

### Required correction / acceptance

Use the correct acquisition boundary for shared QVIX: the authenticated/bound shared acquisition must be within the measured current invocation and enclosing manifest, and no later than the relevant successful completion; it need not follow each cached member's attempt. Retain member attempted/success/finish ordering, exact run/shared identity checks and rejection of genuinely old/out-of-invocation acquisitions. Do not alter immutable provider evidence or change worker timestamps to pretend each member fetched independently.

Make the real integration fixture use advancing timestamps and prove eligible fresh partial preparation, exact publication and red conclusion with cached later members; also retain deterministic rejection coverage for old/future shared acquisitions. The existing constant-clock fixture cannot prove this real temporal contract.

## Full-scope assessment

Inspected all seven owned files in full, including untracked implementation additions (plain `git diff f16be449c1` alone omits them), the active ledger and approved plan review; followed actual fetch/state/recovery, source-date decoding, verifier and chart trace contracts. The tracked diff also contains parent-authored ledger accounting; it was not edited by this reviewer.

- **Cutoff/full history (AC18/P-D1):** actual preparation-start UTC-yesterday is frozen once; fetch explicitly uses start2000, not a rolling 30-day selector. Selection is independently replayed before eligibility, and chart arrays are independently bound to selected CSV rows. Full raw evidence can legitimately contain current-day observations. Tests exercise leap/year boundaries, timezone independence, cross-midnight finish, Friday/weekend coverage and preservation of pre-30-day history.
- **Source loss/null semantics (AC18/19/D19):** decoded index raw dates and shared QVIX common raw dates are compared within overlapping windows, rather than counts, endpoints or finite-close sets. Blank common dates survive; fresh nulls replace prices, with no stitching. Beginning/middle/end/equal-count replacement tests and actual all-blank revision/render/verifier tests pass. No additional defect found here.
- **Identity/immutability (AC19/P-D2):** baseline verification precedes ordinary copying and acquisition; candidate independent verification precedes eligibility; new operation/run, previous hash, windows, registry, fresh member origins and exit/status agreement are enforced. All prior data files, including unreferenced historical evidence, must remain identical except latest.json; new files are limited to the new run. Crash/hidden disclosure/immutable mutation/fatal candidate tests exercise actual verification and preserve baseline bytes. The acquisition-time check is the blocking exception described above.
- **Persistence/partial/fatal (AC17/19):** exact-base clean stdlib publisher, hashed same-identity payload, staged byte checks, one commit and non-force push, branch/default checks and exact readback are implemented. Disposable local remotes exercise atomic payload bytes, replay refusal, competing/human writers and lost response/timeout. Fatal/stale rejects the whole candidate; permitted partial is designed to persist before the final red quality result. Actual concluding workflow shell is exercised, not merely asserted as YAML text. These tests pass, but D-R1 prevents the real preparation-to-persistence route.
- **Pages/operations (AC17/20):** optional explicit Pages job uses the exact bundle HTML and rechecks persisted target, independently of Git persistence. Default-branch schedule/manual guards, concurrency, pinned actions/tools and job bounds are present. README covers delayed/dropped schedules, current-day exclusion, full refresh, retention, permissions, Pages setup, notifications, recovery and service/race limits. Hosted operation and redistribution rights are honestly external, not locally established. No UI change/browser acceptance claimed.
- **Evidence/ledger (AC21):** implementation's recorded 156-test/full-gate results are its evidence, not an independent pass by this reviewer. This reviewer independently ran the 40 daily cases and actionlint above and reproduced D-R1 with real acquisition/render/verifier code. W23/W24 remain active and the active ledger does not yet claim daily final acceptance; that is appropriate. Do not close AC17/19/21 or certify convergence until D-R1 is corrected and independently re-reviewed, followed by the required final-tree gates. No dropped/superseded obligation or new product decision is proposed.

Security/workflow review is separate; this report does not substitute for that review. No further correctness finding identified in the inspected scope.
