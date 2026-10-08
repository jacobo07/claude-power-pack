# R5 receipt -- goal-autopsy + Fault Capsule (goal ce-a3b-r)

decision: goal-autopsy is deterministic, read-only, exempt from goal charging like goal-status. A bound session's terminal refusal or SessionEnd writes a Fault Capsule through mission_capsule (fault_capsule), no new format.

effect: tools/mission_spend.py `goal-autopsy --goal G` and `goal-fault --goal G --session S --cwd C --reason R`; mission_capsule.fault_capsule; repo hooks/session_budget_guard.js exempts goal-autopsy. goal-fault is wired into the guard terminal-refusal path in R4 (nothing calls goal_fault_capsule yet).

proof: RED 88d37fe9 (1/10); GREEN 6902264d test_goal_autopsy.py 10/10. test_session_budget_guard.py SBG_PASS=16/16 exit 0. test_goal_budget_admission.py GOAL_PASS=72/72 exit 0. Mutation drill (isolated copy, control passed; autopsy appends a row): KILLED, V-GOAL-AUTOPSY-READONLY red (AUTOPSY_PASS=9/10).

unknowns: R5 halted on its call breaker (1.57M vs 1.5M stop) before verification; handoff note was blocked. Regression suites unrun since the session_budget_guard.js regex edit.

refs: R5.md, R5c.md, commits 88d37fe9, 6902264d; report ~/.claude/state/slim-jobs/m-e518415e2749.

actual vs forecast: actual 1.73M for 30 calls vs forecast 1.2M.

