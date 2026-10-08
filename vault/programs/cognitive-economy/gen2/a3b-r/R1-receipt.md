# R1 + R1b receipt -- canonical goal-state authorization + scoped Owner grants (goal ce-a3b-r)

decision: finish R1 in R1b. R1 (m-f81fab63562c) stopped on its call breaker after the RED tests (a317f5c2, 61/67,
6 red by design; 19240f98 cherry-picked as 5ecd559b). R1b (this unit) wrote the implementation: d0d0eb2b.

effect:
- hooks/session_budget_guard.js: file-tool targets (file_path / path / notebook_path) are canonicalized (cwd-resolved,
  realpath of the deepest existing ancestor so junctions and 8.3 names resolve, lowercase on win32, no trailing
  separator) and denied only inside the goal state dir or as a state/session-budget-* file. A spec merely NAMED like
  the state is admitted. Shell: verb deny now goal-(declare|renew|spawn|grant|revoke) (grant-use is not denied), plus
  best-effort path-token check; trust-boundary comment states only the file tools are canonical.
- A protected READ is admitted only through `goal-grant-use` (mission_spend.py); `CPP_GOAL_GRANTS=0` skips it.
- tools/mission_spend.py: goal_grant / goal_revoke / goal_grant_use; CLI goal-grant (--owner TTY proof),
  goal-revoke, goal-grant-use. Rows grant / revoke / grant_use go through the ledger `_append` under its lock; the
  operation key is `access` (`op` is the row type). A grant on the journal or lock file is refused (self-voiding).
- tools/test_goal_budget_admission.py: the `relative` alias in V-GOAL-CANON-STATE-DENIED ran with cwd=state dir, under
  no goal root, hence an UNBOUND session that is out of scope by design; the loop now binds with CPP_GOAL=gc.

proof: test_goal_budget_admission.py GOAL_PASS=67/67 exit 0; test_session_budget_guard.py SBG_PASS=16/16 (one
earlier run read V-SBG-LATENCY 544 ms under host load; rerun 47.8 ms, borderline against the 50 ms bar -- unbound
path, my change does not execute there). Mutation drill (tools/mutation_drill.py, isolated copy, control passed):
canonical check reverted to the old substring regex -> MUTANT KILLED, V-GOAL-CANON-SPEC-READABLE red, STATE-DENIED
also red (8.3-short, junction admitted-by-lexical-miss). 65/67.

unknowns: the live guard is the main checkout under ~/.claude and still has the old regex; going live is R3/the
Owner (HR-001). The LATENCY gate is flaky at 50 ms on this host. The path-token shell check can false-positive on
a token that merely resolves into the state dir.

refs: R1.md, R1b.md, vault/plans/ce-a3b-recovery-2026-10-08.md sections 4, 10; commits a317f5c2, 5ecd559b, d0d0eb2b.

actual vs forecast 1.6M (R1b): about 38 tool calls in one pane; the ledger-measured spend is not read here
(UNKNOWN; R1b's own transcript total is the authority). R1 + R1b together vs the 2.0M R1 forecast: not separately
metered.
