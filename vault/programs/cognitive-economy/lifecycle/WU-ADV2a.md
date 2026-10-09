# WU-ADV2a -- consume-once approval in the goal ledger + goal-aware route admission (WU-ADV residual, part 1)

Goal ce-lifecycle-v3. cwd = this worktree. Work class: IMPLEMENTATION (small).

Facts (measured, do not re-derive):
- Every `gsd_mission.py admit` in this program printed `remaining=None`: route admission never reads goal authority.
  Units have only been safe because the coordinator checked goal-status by hand.
- WU-ADV epoch 1 wrote, untested, a consume-once `approval_id` for GoalLedger.declare_cap. It is saved as
  salvage/WU-ADV-ledger-approval-id-UNVERIFIED.patch. Its design is in vault/plans/ce-lifecycle-WU-ADV-progress-2026-10-08.md
  (read only that file's section "Written to the working tree").

Read ONLY: that progress-note section; the salvage patch; `grep -n "def admit_route\|remaining" tools/gsd_mission.py`
plus 20 lines around each hit; modules/provider_routing/ledger.py lines 250-270 (declare_cap).

Budget: about 14 physical calls. Commit when each part's gates are green.

Part 1, the approval:
- Apply the salvage patch with `git apply --3way`, or re-implement it in declare_cap: a `cap` op whose source carries
  `approval:<id>` means a second call with the same approval_id appends nothing (reason "already consumed").
- Gates in tools/test_halt_continues.py or a new tools/test_advance.py:
  - V-LIFE-APPROVAL-ONCE, with a control that a different id is applied;
  - mutant: the consumed check is dropped.
Part 2, goal-aware admission:
- admit_route resolves the mission's spend goal (the steward's spend_goal_for, or gsd_mission's spend_goal), reads
  GoalLedger status and passes remaining - open to route_admission.admit(remaining=...).
- A missing goal keeps today's behaviour.
- Gates:
  - V-LIFE-ADMIT-GOAL-DEFER: remaining below need gives DEFER;
  - V-LIFE-ADMIT-NO-GOAL-UNCHANGED, the control.
  - Mutant: remaining is not passed.
Then:
- Suites: halt, ADM 43/43, MC baseline, steward 18/18.
- Commit by pathspec with -F. WU-ADV2a-receipt.md (<= 15 lines). Commit.
- Arm WU-ADV2b with LIVE gsd_mission.py arm-chain (--parallel-unit lc3-WU-ADV2b, packet WU-ADV2b.md, route
  route-WU-ADV2b.json, token-estimate 700000) if remaining - open >= 700,000.

NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-ADV2a done
