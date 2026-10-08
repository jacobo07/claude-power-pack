# WU-1C2 -- goal roots: refuse an overlapping declare, add goal-unroot (WU-1 step 5)

Plan: vault/plans/ce-lifecycle-WU-1R-recovery-plan-2026-10-08.md (APPROVED, Owner A), row WU-1C, renamed WU-1C2 by
ce-a3 Amendment C (the WU-1C slot now carries WU-1H). Cites amendment A1. Goal ce-lifecycle-v2. Worktree = your cwd.
Detailed step text: WU-1.md step 5 and the ROOT-OVERLAP / UNROOT parts of step 7.
Precondition: WU-1C-receipt.md exists and says WU-1C (WU-1H) done. If it says BLOCKED, stop and repeat its blocker.

Budget discipline (measured: ~18K floor + ~2.4K per call): hard cap 13 model calls; large batched PowerShell calls,
logs under _logs/wu1c2/; read only the goal-declare path of tools/mission_spend.py. Past ~50K context: commit what
is green, append to WU-1C2-receipt.md, end with HANDOFF NOTE. CHECKPOINT FIRST: commit a stub receipt before step 1.

Steps:
1. In tools/mission_spend.py `goal-declare`: refuse a --root already held by another goal whose remaining > 0.
   Exit non-zero and name the holding goal. A goal with remaining <= 0 or state superseded does not block.
2. Add `goal-unroot --goal G --root R`: removes R from G only when G has remaining <= 0 or is superseded. It removes
   authority and never adds it, so no --owner flag. On a live goal it refuses and exits non-zero.
3. Tests in tools/test_process_lifecycle.py, hermetic temp state dir: V-LIFE-ROOT-OVERLAP (declare on a live goal's
   root refused) and V-LIFE-UNROOT (refused on a live goal, removes on an exhausted one). For each, a mutant on an
   isolated copy (tools/mutation_drill.py) that must go red.
4. Run test_process_lifecycle.py and test_goal_budget_admission.py. Record each PASS line. A new failure blocks.
5. Commit by pathspec with -F msgfile and verify `git log -1 --format=%s`. Never push, reset, stash or check out.
6. Finish WU-1C2-receipt.md (<= 40 lines): gates, mutants, commit, calls used, deploy recipe for mission_spend.py as a
   MERGE note, not a copy (see RESUMPTION "Install hazard"). Do NOT deploy (HR-001). Commit it.
7. Arm WU-1D if WU-1D.md and route-WU-1D.json exist on disk AND `mission_spend.py goal-status --goal ce-lifecycle-v2`
   shows remaining - open >= 850,000. Use `gsd_mission.py arm-chain` if it exists (WU-1C added it), else
   (python = C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe, tool =
   C:\Users\User\.claude\skills\claude-power-pack\tools\gsd_mission.py):
   `arm --cwd <this worktree> --command /gsd-autonomous --no-launch --rollover-protocol capsule-v2 --max-cycles 3 --parallel-unit lc-WU-1D`
   then `envelope --mission <id> --wu-packet <abs WU-1D.md> --token-estimate 550000`
   then `admit --mission <id> --route <abs route-WU-1D.json>`.
   If authority is short, write WAITING_FOR_AUTHORITY with the numbers. Never hand the arm to "a fresh pane": arm it
   yourself or record ARM_FAILED + the error.

Do not touch: the live checkout under ~/.claude, ctx-rent, the ce-lifecycle-v worktree.

End your final message with: HANDOFF NOTE: WU-1C2 done
