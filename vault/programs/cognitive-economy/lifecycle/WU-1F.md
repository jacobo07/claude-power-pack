# WU-1F -- name and classify the 53/54 in test_goal_budget_admission.py (BLOCKER for WU-1B)

Plan: vault/plans/ce-lifecycle-WU-1R-recovery-plan-2026-10-08.md (APPROVED). Cites amendment A1.
Goal ce-lifecycle-v2. Worktree = your cwd (branch ce/lifecycle-v2, HEAD e71f3a0b + the plan commit).
Code state = step 1 extraction (9bc030c9). The salvage patch is NOT applied; do not apply it in this unit.

Budget discipline (measured: context rent is the cost driver):
- Hard cap 12 model calls. Batch work into few, large PowerShell calls that write logs to files.
- Never read whole large files. Read only the failing test and the code it names.
- If context passes ~50K: commit what is green, append to the receipt, end with HANDOFF NOTE.

Steps:
1. One PowerShell call: run `tools/test_goal_budget_admission.py` 8 times from this worktree. Redirect each run to
   `_logs/wu1f/run-N.txt`. Then print only the `^FAIL` lines and the `GOAL_PASS=` lines across all runs.
2. If any FAIL appears, read that test's function and the code path it exercises. Classify with evidence:
   - REGRESSION: caused by the 9bc030c9 extraction. Compare with `git show 578f701e:<path>`; never check out.
   - PREEXISTING_FLAKY: the same failure exists at 578f701e. Prove it by running the old guard text from a temp copy
     under _logs, not by switching branches.
   - INTERFERENCE: depends on live ~/.claude state or a concurrent writer.
   - NONDETERMINISM: timing, ordering or randomness inside the test.
   Fix only REGRESSION, or NONDETERMINISM in the test itself. Fixing means: minimal edit, 8 more runs, all 54/54.
3. If 0 FAIL in 8 runs: run 8 more in one call. If still 0, the verdict is UNREPRODUCED in 16 runs. Record it and do
   not block on it.
4. Commit the fix if any, by pathspec with `git commit -F <msgfile>`, then verify `git log -1`. Never push, reset,
   stash or check out.
5. Write `vault/programs/cognitive-economy/lifecycle/WU-1F-receipt.md` (<= 40 lines): runs, failing test name or
   UNREPRODUCED, classification and evidence, fix commit, calls used. Commit it.
6. Arm WU-1B only if WU-1B.md and route-WU-1B.json exist in this directory. The coordinator writes them; do not
   author them yourself. Recipe (python = C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe, tool =
   C:\Users\User\.claude\skills\claude-power-pack\tools\gsd_mission.py):
   `arm --cwd <this worktree> --command /gsd-autonomous --no-launch --rollover-protocol capsule-v2 --max-cycles 3 --parallel-unit lc-WU-1B`
   then `envelope --mission <id> --wu-packet <abs WU-1B.md> --token-estimate 1100000`
   then `admit --mission <id> --route <abs route-WU-1B.json>`.
   If they are absent, say so in the receipt.

End your final message with: HANDOFF NOTE: WU-1F done (<verdict>)
