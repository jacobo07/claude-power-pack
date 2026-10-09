# WU-ADV progress -- epoch 1 stopped by the session budget breaker (833K > stop 800K)

Status: PARTIAL. Nothing committed except checkpoint 014f1edb (stub WU-ADV-receipt.md).

## Written to the working tree, UNCOMMITTED, NOT YET RUN
- modules/provider_routing/ledger.py: `GoalLedger.declare_cap(..., approval_id=None)` -- consume-once: a journal `cap` op whose
  source contains `approval:<id>` makes a second call append nothing (reason "already consumed").
- _logs/wuadv/block.py: the advance stage source (parse_plan, receipt_complete, goal_headroom, apply_approval, advance_unit
  with explicit `unit not in plan["units"]` check, singleflight key file opened "x" before arm_chain, advance_pass,
  `supervise` wrapper that calls `_supervise_core` then `advance_pass`; CPP_SWEEP_ADVANCE=off).
- _logs/wuadv/patch1.py: applies block.py to tools/gsd_mission.py (renames supervise -> _supervise_core), makes admit_route
  goal-aware (goal_rem = goal_headroom(rec.goal.ce_goal or CPP_CE_GOAL); remaining = min(...); admission.goal_remaining),
  and arm_chain accepts ce_goal. The patch was NOT applied (the breaker denied the run). Apply:
  `python -I _logs\wuadv\patch1.py` from the worktree root, then `python -c "import sys;sys.path.insert(0,'tools');import gsd_mission"`.

## Next exact actions (fresh pane / next epoch)
1. Apply patch1.py; import-check; run tools/test_halt_continues.py (expect 10/0) to prove the supervise wrapper is safe.
2. Write tools/test_advance.py (hermetic: GSD_LONG_RUN_STATE_DIR temp, temp git repo, temp plan with frontmatter
   status/units/packet_dir, approvals/<id>.json with repo, plan_path, goal, estimates, optional cap_delta; inject
   `headroom=lambda g: N` and `arm_fn=counting stub`): V-LIFE-ADV-ARMS-NEXT, -ONCE, -NOT-LISTED (call advance_unit with an
   unlisted unit), -NO-AUTHORITY, V-LIFE-APPROVAL-ONCE (GoalLedger in a temp root: apply_approval twice -> one cap op),
   V-LIFE-ADMIT-GOAL (admit_route with a goal ledger whose remaining < need -> DEFER/refused; goal-less -> unchanged) + controls.
3. Mutants through tools/mutation_drill.py: drop the singleflight FileExistsError branch (ADV-ONCE), drop the
   `unit not in plan["units"]` check (NOT-LISTED), drop the `tok in str(r.get("source"))` check in ledger.py (APPROVAL-ONCE).
4. Write the approval record for Extension #1 in `<state>/approvals/` (approval_id amendment-D-ext1, goal ce-lifecycle-v2,
   cap_delta 5600000, `consumed: {"seq": 26}`), and prove apply_approval refuses it.
5. Suites: test_gsd_mission.py (baseline 224/225, the one pre-existing FAIL), test_process_lifecycle.py (baseline 5/1),
   test_goal_budget_admission.py, test_hook_boundary.py. Commit by pathspec with -F; fill WU-ADV-receipt.md (<=50 lines).
6. Step 8: arm WU-1C via the atomic arm (--parallel-unit lc-WU-1C --token-estimate 500000) only if remaining - open >= 800,000.
   Currently UNMEASURED this epoch: WAITING_FOR_AUTHORITY.

HANDOFF NOTE: WU-ADV partial -- see this file
