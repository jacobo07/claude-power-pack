# ce-lifecycle L1 - STOPPED by the goal guard (budget_spent)

State at stop (derived from git log c21200e0 and the tree):
- Step 1 DONE, committed c21200e0: tools/test_process_lifecycle.py gates V-LIFE-PREMODEL-TRANSPORT (+CONTROL), exit 0.
  Finding: hooks/hook-dispatcher.js does NOT swallow a UserPromptSubmit block. mergeOutputs maps block->deny,
  sanitizeForSchema maps deny->block, `reason` is copied. No dispatcher fix needed. "Red" is still owed: the
  mutant (dispatcher drops decision) must be run in step 4.
- Baseline at HEAD: test_goal_budget_admission 52/54 (exit 1) on one run, 54/54 on the next (flaky, not mine);
  test_hook_boundary 7/7 (exit 0).
- Step 2 NOT done: hooks/lib/goal_binding.js was not written; session_budget_guard.js untouched.
  Source to move: goalBinding/normPath/under (session_budget_guard.js:183-206), stateDir() honours GSD_LONG_RUN_STATE_DIR.
- Steps 3-8 NOT done.

Blocker: ce-lifecycle used 8,669,531 of cap 8,000,000 (guard: after one final reply per live pane, 0 left, less than
one call of 62,816). A crossed cap is never raised; the Owner must declare a new goal id (or approve a raise) before
L1 can resume. Not circumvented.

Note for the resumer: a chain step has a 3,000 ms UserPromptSubmit deadline (dispatcher line ~821), so the 4 s
goal-status timeout in the packet exceeds it; use <= 2 s in premodel_gate.js.
Also: Bash/Write commands whose text contains the goal state-path string are denied by the guard; use Edit/Write tools.
