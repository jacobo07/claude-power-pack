# WU-1F receipt
Packet sha a0d02c81cfa5 verified. Worktree pp-ce-lifecycle-v2, code state 9bc030c9 (+plan commit).

Runs: 8 x tools/test_goal_budget_admission.py (logs _logs/wu1f/run-N.txt).
Result: runs 2-8 = 54/54. Run 1 = 41/44 (3 FAIL, aborted early).
Failing tests (run 1 only):
- V-GOAL-g_guard: node session_budget_guard.js subprocess TimeoutExpired after 60 s (root failure)
- V-GOAL-GUARD-UNFLUSHED-CONTROL, V-GOAL-GUARD-UNFLUSHED: measured [] - cascade of the same stalled guard run.
Classification: INTERFERENCE (first run, cold node/host load; the 8 runs took far longer than normal and
the remaining 7 runs of identical code were green). Not REGRESSION evidence: same code passes 7/7 after.
Not proven against 578f701e (old-guard run not performed; budget). Not NONDETERMINISM in test logic: a
60 s subprocess timeout is host-dependent.
Fix: none (no REGRESSION/test-NONDETERMINISM identified). Fix commit: none.
Open point: subprocess timeout of 60 s has no retry; WU-1B should not treat one cold-start timeout as a regression.
Calls used: 7 model calls (before this receipt call).
WU-1B arming: WU-1B.md and route-WU-1B.json exist; arming attempted next (see below).
