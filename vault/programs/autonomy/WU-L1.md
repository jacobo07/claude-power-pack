# WU-L1 -- reconcile feat/ucda with live PP and land (S1..S5 + R1)

Read `vault/programs/autonomy/PROGRAMME.md` first. Evidence: `WU-R1-land.json` (land_worktree REFUSED REBASE_CONFLICT at
6cfde80b S2 vs live d74c385e). Live PP moved (econ-contain WS-F 999984d1 touched mission_spend accounting roles; trf
programme commits) and live `tools/gsdx_chain.py` is dirty from ANOTHER writer (never touch it).

## Do
1. Rebase feat/ucda onto the current live HEAD in this worktree. Resolve each conflict by keeping BOTH semantics
   (live's econ-contain roles/recovery reserve + this programme's S2 programme-spend/ledger_goal, S5 EVC changes).
   Run every test file the touched tools have (mission_spend, gsd_mission, goal_*, gsdx_chain, chain_registry,
   programme_spend, cost_to_completion, reforecast, hold_guard_budget, land_worktree) before and after.
2. Land with `tools/land_worktree.py`. If it refuses ONLY for overlap with another writer's uncommitted live file
   (expected: tools/gsdx_chain.py), land is impossible as one ff: record it, and write receipt DONE with
   `LANDING_PENDING_OVERLAP: <files>` (the branch stays rebased; a later unit retries). Never edit, stash or commit
   another writer's live files.
3. A conflict whose right resolution you cannot decide from code + tests is a cognitive question, not BLOCKED_HUMAN:
   write it down precisely in the receipt and choose the conservative side (live's behaviour wins).
Close by call 22. Receipt: `vault/programs/autonomy/WU-L1-receipt.md`.
