# WU-S5d -- the steward settles every terminal worker; a PARTIAL receipt is read wherever its status is written

Goal ce-lifecycle-v3. cwd = this worktree. Work class: REPAIR (two small fixes, measured live).

Measured live after the L3 install (37a5f3c0):
- D1: the steward never settled a single sid of this chain. The coordinator settled them by hand with a script.
  Cause: tools/mission_steward.py:292 skips any mission whose state is not HALTED/BLOCKED, or that has no `goal`
  field. Sweep-armed records carry no goal, and COMPLETED missions are excluded. The open leases of
  INST2 (m-52f5b06b4c28) and ADV2a (m-86c2f1a9f3b0), 750K each, stayed held.
- D2: WU-ADV2a wrote `# WU-ADV2a receipt -- Status: PARTIAL` on its title line. gsd_mission._receipt_present reads the
  status only at the start of a line, so the PARTIAL unit was marked COMPLETED and halt_continue did not continue it.

Read ONLY:
- tools/mission_steward.py 280-306;
- `grep -n "def spend_goal_for" tools/mission_steward.py` (+15);
- `grep -n "def _receipt_present" tools/gsd_mission.py` (+25).

Budget: about 12 physical calls. Commit when the gates are green.

Steps:
1. D1: the R1 selection is a terminal state (COMPLETED, HALTED or BLOCKED) with a wu_packet. The goal comes from
   m.get("goal"), else spend_goal_for(m["cwd"], index). Each sid is settled once: keep the steward's own done marker.
   Gates in tools/test_mission_steward.py:
   - V-STEWARD-SETTLES-COMPLETED: a COMPLETED sweep-armed mission with no goal field, bound by cwd, has its open
     lease closed;
   - V-STEWARD-SETTLE-ONCE, the control: a second pass appends nothing.
   Mutant: COMPLETED excluded again.
2. D2: _receipt_present treats `Status: PARTIAL|IN PROGRESS|stub` anywhere in the first 3 lines as absent.
   Gate in tools/test_halt_continues.py: V-LIFE-RECEIPT-STATUS-IN-TITLE, with a DONE-in-title control.
   Mutant: line-start-only match.
3. Suites: steward, halt, ADM 43/43, advance 4/0, MC baseline (224/225). Commit by pathspec with -F.
   WU-S5d-receipt.md (<= 12 lines), Status: DONE as its own line. Commit.
4. Arm WU-ADV2b with LIVE gsd_mission.py arm-chain (--parallel-unit lc3-WU-ADV2b, packet WU-ADV2b.md, route
   route-WU-ADV2b.json, token-estimate 720000) if goal-status remaining - open >= 720,000. Else write
   WAITING_FOR_AUTHORITY.

NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-S5d done


## Residual
Proposed by the steward for stopped mission m-3bf354f42adc (PROPOSAL ONLY: arming it needs the Owner/coordinator).
- Partial receipt: C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\programs\cognitive-economy\lifecycle\WU-S5d.md.partial.json
- RESUMPTION_FILE: C:\Users\User\Apps\pp-ce-lifecycle-v3\RESUMPTION_FILE.md
- Salvage: C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\specs\salvage\m-3bf354f42adc
