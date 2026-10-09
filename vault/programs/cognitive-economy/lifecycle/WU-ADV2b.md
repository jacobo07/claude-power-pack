# WU-ADV2b -- advance stage: approval record -> goal authority -> armed next unit, by the sweep (OB-APPROVAL-TO-ARM)

Goal ce-lifecycle-v3. cwd = this worktree. Work class: IMPLEMENTATION (control plane).

Obligation (Owner, plan ec7f78a0): an Owner approval must become a durable decision record that the sweep turns into
goal-declare plus an armed mission (packet + envelope + gate), with no hand-opened pane.
Today every next unit is armed either by the previous worker's last step or by the coordinator pane.

Design input: salvage/WU-ADV-block.py has the epoch-1 design: parse_plan, receipt_complete, goal_headroom,
apply_approval, advance_unit, the singleflight key file, advance_pass, and a supervise wrapper with
CPP_SWEEP_ADVANCE=off. Read it once. Re-fit it to the CURRENT gsd_mission.py rather than applying patch1.py blindly
(supervise has changed since).

Read ONLY: salvage/WU-ADV-block.py; `grep -n "def supervise\|def arm_chain\|def _supervise" tools/gsd_mission.py`
plus 30 lines around each hit.

Budget: about 16 physical calls. Commit as soon as the gates are green.

Contract:
- A plan file with front matter {status: APPROVED, units: [ordered ids], packet_dir} plus <state>/approvals/<id>.json
  {approval_id, plan_path, goal, cap_delta?} is the decision record.
- advance_pass, run by the sweep after supervise:
  - for an APPROVED plan whose last unit has a complete receipt (Status: DONE, not a stub), arm the next listed unit
    with arm_chain, if its packet and route exist and goal headroom covers its token estimate;
  - apply the approval's cap_delta once through the consume-once declare_cap (WU-ADV2a);
  - singleflight per (plan, unit); never a unit that is not listed;
  - write WAITING_FOR_AUTHORITY or WAITING_FOR_PACKET to the plan's status file when it cannot arm.
Gates (tools/test_advance.py, hermetic: temp state dir, temp git repo, injected headroom and arm_fn):
- V-LIFE-ADV-ARMS-NEXT, -ONCE, -NOT-LISTED, -NO-AUTHORITY, -STUB-RECEIPT-NO-ARM.
- Mutants: drop singleflight; drop the listed check.
Then:
- Wire it into the sweep path behind CPP_SWEEP_ADVANCE (default on). Suites as in ADV2a.
- Commit. WU-ADV2b-receipt.md (<= 15 lines). Commit.
- Arm WU-INST3 if its packet exists (else WAITING_FOR_PACKET in the receipt).

NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-ADV2b done
