# WU-1D -- arm --goal with a launcher binding record; close WU-1 (WU-1 steps 6-9)

Plan: vault/plans/ce-lifecycle-WU-1R-recovery-plan-2026-10-08.md (APPROVED, Owner A). Cites amendment A1.
Goal ce-lifecycle-v2. Worktree = your cwd (branch ce/lifecycle-v2). Detailed step text: WU-1.md steps 6, 8 and 9 and
the LAUNCHER-WINS / ARM-GOAL parts of step 7.
Precondition: WU-1C-receipt.md exists and says WU-1C done. If it says BLOCKED, stop and repeat its blocker.

Budget discipline: hard cap 13 model calls; batch into large PowerShell calls with logs under _logs/wu1d/; read only
the arm and launch_worker paths of tools/gsd_mission.py. Past ~50K context: commit what is green, append to the
receipt, end with HANDOFF NOTE.

Steps:
1. `gsd_mission.py arm --goal G`: store the goal in the record. At launch, where the worker sid is known, the
   supervisor writes state/goal-binding/<sid>.json {goal, since_ts, source: "launcher", pid} with the same 'wx'
   immutable write as hooks/lib/goal_binding.js, so the worker never binds by cwd. Reuse resolve_binding / the record
   writer WU-1B added; do not write a third copy.
2. Tests in tools/test_process_lifecycle.py, hermetic temp state dir:
   - V-LIFE-LAUNCHER-WINS: a launcher record beats a cwd under another goal's root.
   - V-LIFE-ARM-GOAL: arm --goal persists and the launch writes the launcher record.
   - Mutant on an isolated copy: let cwd override the launcher record -> LAUNCHER-WINS goes red.
3. Run the four suites: test_process_lifecycle.py, test_goal_budget_admission.py, test_hook_boundary.py,
   test_gsd_mission.py. Record exit codes and PASS lines. Pre-existing reds are recorded against HEAD, not fixed.
4. Commit by pathspec with -F msgfile and verify `git log -1 --format=%s`. Never push, reset, stash or check out.
5. Write WU-1-receipt.md (<= 40 lines) closing WU-1 across WU-1A/1F/1B/1C/1D: commits, gates + exit codes, mutants,
   ONE consolidated deploy recipe for every file WU-1 changed that the live checkout runs (hooks/lib/goal_binding.js,
   hooks/session_budget_guard.js, tools/mission_spend.py, tools/gsd_mission.py, modules/provider_routing/ledger.py):
   files + sha256 + base sha in the live checkout + rollback. Do NOT deploy (HR-001). Spend, reforecast, UNKNOWNs.
6. Write WU-2.md + route-WU-2.json from the vertical-slice plan (vault/plans/ce-lifecycle-vertical-slice-plan-2026-10-08.md)
   and amendment A1, same shape as this file. Use the measured estimator (~34K per call at the 50K rotation rule),
   not the plan's nominal lease. Do NOT arm WU-2.
7. Commit the receipt and the WU-2 packet.
8. Arm WU-1H only if WU-1H.md and route-WU-1H.json exist here. Recipe (python =
   C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe, tool =
   C:\Users\User\.claude\skills\claude-power-pack\tools\gsd_mission.py):
   `arm --cwd <this worktree> --command /gsd-autonomous --no-launch --rollover-protocol capsule-v2 --max-cycles 3 --parallel-unit lc-WU-1H`
   then `envelope --mission <id> --wu-packet <abs WU-1H.md> --token-estimate 550000`
   then `admit --mission <id> --route <abs route-WU-1H.json>`.

Do not touch: the live checkout under ~/.claude, ctx-rent, the ce-lifecycle-v worktree.

End your final message with: HANDOFF NOTE: WU-1D done
