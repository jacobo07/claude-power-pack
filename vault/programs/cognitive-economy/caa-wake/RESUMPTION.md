# RESUMPTION -- caa-wake (dependency wake + Cheap Architecture Admission continuation)

Identity:
- Worktrees: `C:\Users\User\Apps\pp-caa-wake` (ce/caa-wake, goal caa-wake) and, from W1R-2 on,
  `C:\Users\User\Apps\pp-caa-wake-t2` (ce/caa-wake-t2, goal caa-wake-t2, cap 3,200,000).
- Plans: `vault/plans/event-driven-wake-caa-2026-10-08.md` and its Amendment R
  (`caa-wake-amendment-R-recovery-2026-10-08.md`, Owner "y" 2026-10-08).
- Thesis: the sweep, not a pane, advances the chain; CAA waits zero-hot and is woken by a machine predicate.

Sealed:
- 78813b21 Amendment R.
- 35d88fd5 Step 0:
  - W1 fault receipt;
  - reconcile caa-wake open 1,320,938 -> 0, remaining 1,165,904;
  - salvage patch;
  - W1R-1/W1R-2/W2/W4 packets with slim-t2 routes.
- W1 m-0fdcdcadd6f5 is under an Owner hold. Never release it.

Chain:
1. W1R-1 m-f2cd327f40f3: armed --no-launch, envelope 800K sonnet, route admitted; the sweep launches it.
2. W1R-1 creates pp-caa-wake-t2 and arms W1R-2.
3. W1R-2 writes W1-receipt (DONE) and arms W2.
4. W2: live install of the sweep `wait` stage, canaries, then declares wait `caa-t3-binding`.
5. The sweep wakes W4 when lifecycle WU-1 SUCCESS + goal_binding.js are live.
6. W4 arms W5, or writes AUTHORITY_REQUEST.md.

Decisions:
- Every arm is `arm --no-launch` + `envelope --token-estimate` + `admit`. Never an auto envelope.
- Coordinators never cd into a goal root.
- Settle holds at autopsy BOUND totals, not with plain goal-reconcile, which overcharges panes that left the root.

Known gaps (owned elsewhere, do not rebuild):
- A unit that HALTS without its receipt still parks the chain until lifecycle WU-1H is live.
- Route admit prints `remaining=None` (WU-4).

Next 3 actions (for a control pane, read-only first):
1. `gsd_mission.py status`, then read the newest `*-receipt.md` here.
2. If a unit is HALTED or BLOCKED with no receipt: write its fault receipt, reconcile, re-arm the residual by the
   recipe.
3. Otherwise do nothing; the chain is self-driving.

Start: read only this file, then action 1.
