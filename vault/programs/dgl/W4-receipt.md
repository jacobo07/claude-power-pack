# W4 receipt
Status: DONE
COMMITS: 550cd247 (gates RED) · 7a3a34ed (fault points + matrix, GOALCRASH 11/11) · 6c8ec84c (goal_autopsy, AUTOPSY 10/10, GOALAUTOPSY 5/5) · 24349cc3 (predictive DRAIN + goal_session_end, GOALDRAIN 6/6) · 80e2cee4 (autopsy/drain gate hardening) · receipt + W5 packet + budget-admission gate fix in the next commit
Red -> green: step 1 gates RED (tools/goal_autopsy.py, hooks/goal_session_end.js and fault points absent) -> GOALCRASH 11/11, AUTOPSY 10/10, GOALAUTOPSY 5/5, GOALDRAIN 6/6.
Mutation kills (tools/mutation_drill.py, copy_dirs tools/modules/hooks, all KILLED): drain threshold ignored (m1); autopsy appends a row -> V-AUTOPSY-APPENDS-NOTHING in tools/test_goal_lease_autopsy.py (m2; tools/test_goal_autopsy.py exercises the OLD mission_spend.goal_autopsy and cannot kill it); session_end settles -> V-SESSION-END-WAKE-ROW-ONLY (m3); a fault point removed from the matrix path (m4).
Regression exit codes, before = detached worktree at 550cd247^ (removed) vs now: test_goal_lease 0/0 (10/10), test_workspace_lease 0/0 (10/10), test_goal_succession 0/0 (9/9), test_session_budget_admission 0/0 (12/12), test_tranche_driver 0/0 (27/27), test_hook_boundary 0/0 (7/7), test_goal_budget_admission 0 -> 1 (53/54) -> 0 (54/54) after the fix below.
Calls: NOT MEASURED in total (4 sessions: r1, r2 22, r3 about 14); packet planned 40, so W5 is sized 28.

## Decision that differs from the packet
- DRAIN now precedes goal-spawn in the guard (it must, goal-spawn reserves a hold and a denial after it would leak one). That made V-GOAL-GUARD-AGENT-REFUSED in tools/test_goal_budget_admission.py deny with DRAIN wording instead of "child refused". The gate now runs that case with CPP_DRAIN=off (it pins the goal-spawn refusal), DRAIN's own denial is pinned by GOALDRAIN. Regression was real and is fixed, not waived.
## Not done / traps
- CLAIM_LOST residue (lease open, workspace unclaimed) is pinned in the crash matrix; nothing claims in live state, no succession-plan.json exists. hooks/goal_session_end.js is not registered (W5, Owner-side).
HANDOFF NOTE: W4 done
