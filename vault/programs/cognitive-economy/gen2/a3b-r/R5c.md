# R5c -- close R5: verify, receipt, arm R4 (goal ce-a3b-r)

Worktree C:\Users\User\Apps\pp-ce-a3b-r, branch ce/a3b-r. Never push. NEVER edit anything under C:\Users\User\.claude\.
R5 (m-e518415e2749) committed 88d37fe9 (RED) + 6902264d (GREEN, test_goal_autopsy.py 10/10) and halted on its call
breaker before verification and Close. Its report: ~/.claude/state/slim-jobs/m-e518415e2749/*.out.json (read only
the `result` field). No new feature work in this unit.

## Steps, in this order (CHECKPOINT FIRST)
1. Write R5-receipt.md now, with proof marked PENDING (decision / effect / proof / unknowns / refs / actual 1.73M vs
   forecast 1.2M). Write R4.md (plan card section 4 row R4, PLUS: wire `goal-fault` into the terminal-refusal path
   of the repo copy of hooks/session_budget_guard.js -- nothing calls goal_fault_capsule yet) and route-R4.json
   (shape of route-R5.json; target from measured R5 = 1.73M for 30 calls, scale to R4's calls). Copy this file's
   Close and the CHECKPOINT FIRST rule into R4.md. Commit with a pathspec.
2. `python tools/test_session_budget_guard.py`, then `python tools/test_goal_budget_admission.py` (foreground,
   6-min timeout, alone in its turn). Both exit 0, or record the failure.
3. Mutation drill (tools/mutation_drill.py, isolated copy): autopsy appends a row -> V-GOAL-AUTOPSY-READONLY red.
4. Update R5-receipt.md proof lines with the measured results. Commit.

## Budget
Envelope 0.6M, about 14 calls. Two failed attempts of the same shape = stop. If a breaker warns, skip to Close.

## Close (AUTOCHAIN, amendment B1)
`python C:\Users\User\Apps\pp-ce-a3b-r\tools\mission_spend.py goal-status --goal ce-a3b-r`.
- If remaining - 800000 >= the R4 envelope target: arm R4 with absolute paths:
  `python C:\Users\User\.claude\skills\claude-power-pack\tools\gsd_mission.py arm --cwd C:\Users\User\Apps\pp-ce-a3b-r
  --command /gsd-autonomous --no-launch --rollover-protocol capsule-v2 --parallel-unit a3b-r-R4`, then
  `envelope --mission <id> --wu-packet <abs R4.md> --token-estimate <target>`, then
  `admit --mission <id> --route <abs route-R4.json>`. Record the id in R5-receipt.md.
- Otherwise do NOT arm. Append ONE line to vault/OWNER_QUEUE.md and to R5-receipt.md:
  `AUTHORITY_REQUEST ce-a3b-r: up to <X> to run R4 (+R3 later); excludes everything else; YES -> re-run R5c Close`.
If arming is refused, write that in the receipt and stop. Do not work around it.
