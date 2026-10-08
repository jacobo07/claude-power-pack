# WU-1C -- goal roots: refuse an overlapping declare, add goal-unroot (WU-1 step 5)

Plan: vault/plans/ce-lifecycle-WU-1R-recovery-plan-2026-10-08.md (APPROVED, Owner A). Cites amendment A1.
Goal ce-lifecycle-v2. Worktree = your cwd (branch ce/lifecycle-v2). Detailed step text: WU-1.md step 5 and the
ROOT-OVERLAP / UNROOT parts of step 7.
Precondition: WU-1B-receipt.md exists and says WU-1B done. If it says BLOCKED, stop and repeat its blocker.

Budget discipline (measured: context rent is the cost driver, ~18K floor + ~2.4K per call):
- Hard cap 12 model calls. Batch work into few, large PowerShell calls that write logs to files under _logs/wu1c/.
- Read only the goal-declare code path in tools/mission_spend.py, never the whole file.
- If context passes ~50K: commit what is green, append to WU-1C-receipt.md, end with HANDOFF NOTE.

Steps:
1. In tools/mission_spend.py `goal-declare`: refuse a --root already held by another goal whose remaining > 0.
   Exit non-zero and name the holding goal. A goal with remaining <= 0 or state superseded does not block.
2. Add `goal-unroot --goal G --root R`. It removes R from G only when G has remaining <= 0 or is superseded. It removes
   authority and never adds it, so no --owner flag. On a live goal it refuses and exits non-zero.
3. Tests in tools/test_process_lifecycle.py, hermetic temp state dir:
   - V-LIFE-ROOT-OVERLAP: declaring a second goal on a root held by a live goal is refused.
   - V-LIFE-UNROOT: unroot on a live goal is refused; on an exhausted goal it removes the root.
   - For each, a mutant on an isolated copy (tools/mutation_drill.py) that must go red.
4. Run test_process_lifecycle.py and test_goal_budget_admission.py. Record each PASS line. A new failure blocks the commit.
5. Commit by pathspec with -F msgfile and verify `git log -1 --format=%s`. Never push, reset, stash or check out.
6. Write WU-1C-receipt.md (<= 40 lines): gates, mutants, commit, calls used, deploy recipe for mission_spend.py
   (files + sha256; do NOT deploy, HR-001). Commit it.
7. Arm WU-1D only if WU-1D.md and route-WU-1D.json exist here. Recipe (python =
   C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe, tool =
   C:\Users\User\.claude\skills\claude-power-pack\tools\gsd_mission.py):
   `arm --cwd <this worktree> --command /gsd-autonomous --no-launch --rollover-protocol capsule-v2 --max-cycles 3 --parallel-unit lc-WU-1D`
   then `envelope --mission <id> --wu-packet <abs WU-1D.md> --token-estimate 550000`
   then `admit --mission <id> --route <abs route-WU-1D.json>`.
   If they are absent, say so in the receipt.

Do not touch: the live checkout under ~/.claude, ctx-rent (Apps\pp-ctx-rent), the ce-lifecycle-v worktree.

End your final message with: HANDOFF NOTE: WU-1C done
