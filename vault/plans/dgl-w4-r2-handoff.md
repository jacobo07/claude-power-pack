# dgl W4 residual 2 -- handoff (session breaker tripped at 22 calls > 1.5 x 14)

Worktree C:\Users\User\Apps\pp-dgl, branch dgl/durable-goal-lease. HEAD 65dfdfd2 (W4 steps 2a-2c sealed: 7a3a34ed, 6c8ec84c, 24349cc3).

## Done this session (UNCOMMITTED edits, both gates re-run green)
- tools/test_goal_autopsy.py g_autopsy: READONLY gate now snapshots every file in the goal dir (AUTOPSY 10/10).
- tools/test_goal_drain.py V-SESSION-END-WAKE-ROW-ONLY: asserts no new file besides ended.jsonl and all pre-existing files byte-identical (GOALDRAIN 6/6).
- Mutant m3 (session_end settles) now KILLED by V-SESSION-END-WAKE-ROW-ONLY (rc=0).

## Finding on m2
tools/test_goal_autopsy.py exercises the OLD mission_spend.goal_autopsy, NOT tools/goal_autopsy.py, so m2 can never be killed there.
The gate for the new module is V-AUTOPSY-APPENDS-NOTHING in tools/test_goal_lease_autopsy.py (snapshots whole state dir).
Spec to run (not yet written because the breaker blocked the write): copy m2.json from C:\Users\User\.claude\jobs\3eb8e620\tmp with
"test": "tools/test_goal_lease_autopsy.py", "gate": "V-AUTOPSY-APPENDS-NOTHING"; run
`python tools/mutation_drill.py --spec <spec>` from the worktree. Expect MUTANT KILLED.

## Next 3 actions
1. Commit the two test edits (msg via temp file), write m2b spec, run drill -> KILLED. (m1, m3, m4 already KILLED.)
2. Regression vs detached worktree at 550cd247^ (remove after): test_goal_lease, test_workspace_lease, test_goal_succession,
   test_goal_budget_admission, test_session_budget_admission, test_tranche_driver, test_hook_boundary.
3. vault/programs/dgl/W4-receipt.md (Status DONE, <=25 lines) + packets/W5.md + route-W5.json (read
   `hardrule_compile.py --class DEPLOY` first). Commit.
