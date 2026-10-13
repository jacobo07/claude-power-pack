# RESUMPTION -- dgl W4 residual (worktree C:\Users\User\Apps\pp-dgl, branch dgl/durable-goal-lease)

Session budget breaker tripped (31 calls > 1.5 x 20) mid mutation drill. Continue with a fresh session.

## Sealed (committed, gates green)
- 7a3a34ed crash matrix fault points + goal_chain dead evidence: test_goal_crash_matrix GOALCRASH 11/11
- 6c8ec84c goal_autopsy: test_goal_autopsy 10/10, test_goal_lease_autopsy 5/5 (includes migration canary)
- 24349cc3 predictive DRAIN (hooks/session_budget_guard.js) + hooks/goal_session_end.js: test_goal_drain 6/6
  (fix that made it green: fixture rows needed a timestamp, else the guard measured 0)
- Mutation drill specs are in C:\Users\User\.claude\jobs\3eb8e620\tmp\m1..m4.json (copy_dirs tools/modules/hooks)
  - m1 drain threshold ignored: KILLED by V-DRAIN-DENIES-SPAWN-AT-EDGE
  - m4 fault point after_close removed: KILLED by V-CRASH-AFTER-CLOSE
  - m2 autopsy appends a row: SURVIVED V-GOAL-AUTOPSY-READONLY (mutant wrote gs.JOURNAL; gate's `jr` is another file)
  - m3 session_end settles: SURVIVED V-SESSION-END-WAKE-ROW-ONLY (mutant wrote journal.jsonl; gate checks spend.journal.jsonl)

## Next 3 actions
1. Retarget m2/m3 mutants at the file each gate compares (grep `jr` in tools/test_goal_autopsy.py; spend.journal.jsonl for m3),
   or widen the gates to assert every file in the goal dir is byte-identical. Rerun until KILLED. Commit.
2. Regression, before = detached worktree at 550cd247^ (remove after): test_goal_lease, test_workspace_lease,
   test_goal_succession, test_goal_budget_admission, test_session_budget_admission, test_tranche_driver, test_hook_boundary.
3. Write vault/programs/dgl/W4-receipt.md (Status DONE; commits above; ~45 calls used across both sessions) and
   packets/W5.md + route-W5.json per CHAIN.md (DEPLOY: read hardrule_compile.py --class DEPLOY first). Commit.

Untracked noise to leave alone: .pp-capabilities, packets/*.partial.json, *.residual.md, vault/specs/salvage/.
Do not run the debug scripts dbg*.py again; they live only in the job tmp dir.
