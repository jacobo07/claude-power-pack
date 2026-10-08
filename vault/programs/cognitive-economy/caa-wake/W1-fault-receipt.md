# caa-wake W1 -- FAULT receipt (partial; NOT a success receipt)

Written by the control plane (unbound pane 3bd3b9be, main checkout cwd, git -C / absolute paths only) under
Amendment R (`vault/plans/caa-wake-amendment-R-recovery-2026-10-08.md`, Owner "y" 2026-10-08). No worker wrote this.

## Process
- Mission m-0fdcdcadd6f5, epoch 1, BLOCKED. Worker 12820fd5, pid 38012, dead. Owner hold set by the control plane.
- Normal receipt: ABSENT. Commit: none past 480f0241. Tests: none.
- Block reason (host): the worker asked for "a new goal id caa-wake-b ~1.5M" -- a worker requesting authority in prose.

## Economics (MEASURED: `mission_spend.py goal-autopsy` from ce/a3b-r, read-only)
| sid | role | calls | processed | bound to caa-wake |
|---|---|---|---|---|
| 12820fd5 | W1 worker | 21 | 3,390,276 | 3,390,276 |
| 41f83b39 | coordinator pane | 34 | 6,707,162 | 443,820 (pre-bind 6,263,342, not charged) |

- The reported figure of "45" was tool calls; there were 21 model calls (MEASURED). Average 161K processed per call.
- Root causes:
  - Envelope `token_estimate` 5,381,919, `src: auto` (MEASURED, mission record). The packet's 1.3M + 0.3M lease
    was prose, so the cost breaker judged a number that was 3.4x the packet's.
  - Launched as a top-level `--bg` worker. Its first-call floor is about 110,835, against 13,507 for slim-t2
    (vault/config/route-floors.json). So about 21 x 110K, roughly 2.3M, was floor rent (ESTIMATED).
  - The packet ordered "build all, then tests, then commit". No checkpoint commit.
  - Progress-free spend: 3.39M with zero commits. The notes file was the only durable output (MEASURED).

## Reservation reconciliation (MEASURED, ledger journal settle ops, reason `reconcile-bound`)
- Before: used 4,955,858 | settled 3,634,920 | open 1,320,938 | remaining 44,142.
- Each sid was settled at its autopsy BOUND total, and its open holds were closed:
  - 12820fd5 at 3,390,276, closing final hold `:10` (209,848);
  - 41f83b39 at 443,820, closing lease `:1` (1,111,090). Owner-approved release.
- After: used 3,834,096 | settled 3,834,096 | open 0 | remaining 1,165,904.
- Why not plain `goal-reconcile`: it settles a sid at its transcript total since the bind time. 41f83b39 kept
  working OUTSIDE the root until 17:02, so that would have charged caa-wake for out-of-root work. The defect is
  recorded for ce-a3b-r R2.

## Salvage: SALVAGE_PENDING_VERIFICATION
- Patch: `W1-SALVAGE_PENDING_VERIFICATION.patch`. sha256 prefix 27E2AEE5C8910271. It reverse-applies cleanly on
  the tree it was cut from. mission_wait.py sha256 prefix C39B92287BC0751D.
- `py_compile` passes for mission_wait.py and wake_check.py.

| packet req | state | evidence |
|---|---|---|
| 1 wait record + GoalLog states + seq-CAS | PRESENT, UNVERIFIED | validate/REQUIRED/open_log/derive/ALLOWED/cas/declare/supersede |
| 2 evaluator, level-triggered, cat-file, model refusal, UNKNOWN->REFUSED | PARTIAL | in mission_wait (`_git_leaf` uses cat-file -e; Unknown -> REFUSED); **wake_check has no `--waits/--delta/--declare` wiring** (D1 not done) |
| 3 wake admission | PRESENT, UNVERIFIED | admit(): goal-status, gsd_mission._scan, route_admission, RAM |
| 4 delta | PRESENT, UNVERIFIED | delta() |
| 5 cycle check | PRESENT, UNVERIFIED | find_cycles() |
| 6 kill switch | PRESENT, UNVERIFIED | disabled() reads CPP_MISSION_WAIT |
| proof | ABSENT | no test_mission_wait.py, no mutants |

- New defect (MEASURED): `wake_check.py --help` is not parsed. It RUNS the default gate and writes a live
  WAKE_FLAG.json (control pane, 15:53:46Z). The control plane removed that flag after verifying its content.
  An unknown argument must be refused, not executed.

## Next lifecycle state
W1R-1 (slim-t2, goal caa-wake, about 0.8M): tests, the wiring, and the argv fix to green, with a checkpoint commit.
Then W1R-2 (goal caa-wake-t2, worktree pp-caa-wake-t2): mutants, W1 receipt, arm W2.
