# WU-1B -- land prospective binding (WU-1 steps 2-4, salvage verified)

Plan: vault/plans/ce-lifecycle-WU-1R-recovery-plan-2026-10-08.md (APPROVED). Cites amendment A1.
Detailed step text: WU-1.md steps 2, 3, 4 and the matching parts of step 7.
Precondition: WU-1F-receipt.md exists. If its verdict is REGRESSION and it is unfixed, stop and say so.

Budget discipline (context rent is the measured cost driver; WU-1 overran at 52K mean context/call):
- 13 model calls per epoch, at most 2 epochs. Large batched PowerShell calls, logs to files, grep only what you need.
- If context passes ~50K or the epoch's calls are used: commit what is green, append to WU-1B-receipt.md, and end
  with HANDOFF NOTE. The capsule-v2 successor continues from the receipt.

Steps:
1. Apply `salvage/WU-1-steps2-4-SALVAGE_PENDING_VERIFICATION.patch` with `git apply --check`, then `git apply`.
   Run `node --check` on both files. Record any hunk that does not apply as SALVAGE_REJECTED with its reason.
2. Add to tools/mission_spend.py:
   - the `prebind` journal op `{op:"prebind", sid, measured, goal}`, counted as PRE_BINDING_PROGRAM_CAPEX and never as
     goal spend;
   - the `goal-prebind` CLI the salvaged guard already calls;
   - `resolve_binding`, the Python twin of hooks/lib/goal_binding.js. Its precedence and record format must match.
   - Keep the kill switch: CPP_PROSPECTIVE_BIND=0 restores the old behaviour.
3. Tests in tools/test_process_lifecycle.py:
   - V-LIFE-BIND-RETRO: a session with 6M of pre-binding history, bound by cwd, is charged only after its binding.
   - V-LIFE-BIND-CONTROL: with the kill switch set, the old retroactive charge reappears.
   - V-LIFE-OBSERVER: a read-only call in a goal root writes no binding record.
   - For each, a mutant that must go red. Use tools/mutation_drill.py or isolated copies, never the live file.
4. Run test_process_lifecycle.py, test_goal_budget_admission.py, test_hook_boundary.py and test_gsd_mission.py.
   Record each PASS line; any new failure blocks the commit.
5. Commit by pathspec with -F msgfile and verify git log -1. Never push, reset, stash or check out.
6. Write WU-1B-receipt.md (<= 50 lines). Include the deploy recipe for hooks/lib/goal_binding.js,
   hooks/session_budget_guard.js and tools/mission_spend.py into the live checkout. Do NOT deploy (HR-001).
7. Arm WU-1C only if WU-1C.md and route-WU-1C.json exist here. Use the same recipe as WU-1F step 6 with
   lc-WU-1C and --token-estimate 500000. Otherwise say they are absent.

End your final message with: HANDOFF NOTE: WU-1B done
