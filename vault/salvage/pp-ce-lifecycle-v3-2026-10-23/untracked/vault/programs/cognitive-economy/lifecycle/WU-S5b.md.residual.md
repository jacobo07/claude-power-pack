# WU-S5b -- residual of WU-S5: finish the steward adoption, prove it, commit (coordinator-compiled residual)

Goal ce-lifecycle-v3. cwd = this worktree. Work class: INTEGRATION closeout.
WU-S5 (m-b2fefaf352e1) tripped at 893K. halt_continue wrote fault-capsules/m-b2fefaf352e1-e1.json but did not renew
it, with no reason recorded (a defect, logged for S5c). This residual was compiled by the coordinator from that capsule.

ALREADY DONE in the working tree (do not redo, do not re-read the snapshot):
- tools/mission_steward.py and tools/test_mission_steward.py copied in.
- modules/provider_routing/ledger.py: steward patch applied (staged).
- tools/mission_spend.py: two conflicts resolved, keeping both sides (goal-prebind and goal-settle/goal-correct) (staged).
- tools/gsd_mission.py: partially merged (unstaged). Check it first with `git diff -- tools/gsd_mission.py` and
  `python -m py_compile tools/gsd_mission.py`.

Budget: about 15 physical calls. Commit as soon as step 2 is green.

Steps:
1. Finish tools/gsd_mission.py only if it is incomplete: compare the diff with
   salvage/gsdx-S1-steward/steward-core.patch hunks for that file. Then py_compile all three .py files.
2. One PowerShell call, each test in a child process via Start-Process -WorkingDirectory (never cd), logs to
   _logs/wus5b/:
   - test_mission_steward.py (expect 18/18);
   - test_halt_continues.py (16/0);
   - test_gsd_mission.py (226/227: the one FAIL is pre-existing);
   - test_gsd_mission_admission.py (43/43);
   - test_session_budget_guard.py (20/20).
   Print the summary lines only.
3. Commit by pathspec with -F msgfile: ledger.py, mission_spend.py, gsd_mission.py, mission_steward.py,
   test_mission_steward.py, this packet. Do NOT commit RESUMPTION_FILE.md (not ours).
4. WU-S5b-receipt.md (<= 15 lines), Status: DONE or PARTIAL plus the exact next step. Commit it.

Out of scope here (it goes to WU-S5c): F1, F3, the capsule DONE-list scope, the live dry run and the install patch.
NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-S5b done


## Residual
Proposed by the steward for stopped mission m-b205bb55bdac (PROPOSAL ONLY: arming it needs the Owner/coordinator).
- Partial receipt: C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\programs\cognitive-economy\lifecycle\WU-S5b.md.partial.json
- RESUMPTION_FILE: C:\Users\User\Apps\pp-ce-lifecycle-v3\RESUMPTION_FILE.md
- Salvage: C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\specs\salvage\m-b205bb55bdac
