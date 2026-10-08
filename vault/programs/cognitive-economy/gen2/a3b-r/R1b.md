# R1b -- finish R1: canonical goal-state authorization + scoped grants (goal ce-a3b-r)

Worktree C:\Users\User\Apps\pp-ce-a3b-r, branch ce/a3b-r. Never push. NEVER edit anything under C:\Users\User\.claude\
(the main checkout there IS the live guard). Do NOT read vault/specs/goal-budget-admission.md (its path trips the
live regex). R1 (m-f81fab63562c) stopped on its call breaker after committing the RED tests: a317f5c2 (GOAL_PASS=61/67,
6 red by design), with 19240f98 cherry-picked as 5ecd559b. Read R1.md for the full contract, then do ONLY:

1. `hooks/session_budget_guard.js` `touchesGoalState`:
   - Canonicalize file-tool targets (path.resolve against event.cwd, fs.realpathSync.native when it exists,
     lowercase on win32, no trailing separator). Deny only inside `state/goal-budget` or `state/session-budget-*`.
   - Keep the shell verb deny, extended to goal-(declare|renew|spawn|grant|revoke). Add the best-effort path-token
     check with a trust-boundary comment.
   - Admit a protected Read only through a `goal-grant-use` call to mission_spend.py, skipped when
     CPP_GOAL_GRANTS=0.
2. `tools/mission_spend.py`:
   - Add `goal_grant` (params owner, now) and `goal_revoke`.
   - Add the CLI verbs goal-grant (`--owner` TTY proof, like rebind), goal-revoke and goal-grant-use.
   - Append grant / revoke / grant_use rows to the goal journal via the ledger's `_append` under its lock. The read
     operation's key is `access`, because `op` is the row type.
   - A grant names a stable file (a grant on spend.journal.jsonl would void itself: its sha256 changes per row).
3. `python tools/test_goal_budget_admission.py` (takes over 2 min: run it with a 6-min timeout, foreground, nothing
   else in that turn) and `python tools/test_session_budget_guard.py`. Both must exit 0, with all 67 GOAL gates green.
   Commit (pathspec, guard + mission_spend.py).
4. Mutation drill on an isolated copy (tools/mutation_drill.py if it applies, else a copy): revert the canonical
   check to the old substring regex -> V-GOAL-CANON-SPEC-READABLE must go red. Record it in the receipt.

## Progress contract
First durable progress = a commit of the guard change, by 40% of the envelope. Commit after each numbered step.
Two failed attempts of the same shape = stop and write the receipt.

## Close
Write `gen2/a3b-r/R1-receipt.md` (decision / effect / proof / unknowns / refs / actual vs forecast 1.6M; note R1 + R1b
together). Write R2.md + route-R2.json from plan section 4 row R2. Cost them from YOUR measured calls (tool calls
~30-40 per code unit, ~115k per model call). Arm R2:
`python C:\Users\User\.claude\skills\claude-power-pack\tools\gsd_mission.py arm --cwd C:\Users\User\Apps\pp-ce-a3b-r
--command /gsd-autonomous --no-launch --rollover-protocol capsule-v2 --parallel-unit a3b-r-R2`, then `envelope --mission
<id> --wu-packet <abs R2.md> --token-estimate <M> --autocompact 600k`, then `admit --mission <id> --route <abs
route-R2.json>`. Context lifecycle is capsule-v2 rotation (Owner 2026-10-08). Pass autocompact 600k explicitly: the
laptop resolver otherwise fills 250k, which makes provider compaction primary. If arming is refused, record that in the
receipt and stop.
