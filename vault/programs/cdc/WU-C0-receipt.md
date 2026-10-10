# C0 receipt
Status: DONE

- Worktree `C:\Users\User\Apps\pp-cdc`, branch feat/cdc, base live b0d72dda (the approved plan commit). PROVEN (git log).
- Programme files: PROGRAMME.md, WU-C1..C12 packets, route.json (slim-t2, 30 calls, target 7M), chain.json (goal cdc,
  envelope 80M), chain_tick.ps1, evidence/ql_old_claims.json (old 50-claim graph, for C12 comparison only). PROVEN.
- Deviation from plan section 4, recorded: CDC units are NOT appended inside the Autonomy chain.json (that would spend
  Autonomy's 90M envelope and bind its root pp-ucda-wt). They run in a sibling chain on the same zero-model tool
  (live gsdx_chain.py) with goal `cdc`; C1 `wait`s on `pp-ucda-wt\vault\programs\autonomy\WU-S9-receipt.md`, which gives
  the approved order (after Autonomy S9) with one writer at a time. `requires` support was NOT needed: gsdx_chain
  already has `wait`.
- Dry-run tick: `{"action":"wait_event","unit":"C1","missing":[...WU-S9-receipt.md],"goal":"cdc","used":0}`. PROVEN.
- Goal `cdc` declared: cap 80,000,000, root pp-cdc, source plan@b0d72dda (goal-status ok, used 0). PROVEN.
- Scheduled task PP-CdcChain-Tick: every 10 min, 15 min limit, IgnoreNew, hidden launch; log
  `~/.claude/state/cdc-chain-tick.log`. Kill: CPP_GSDX_CHAIN=off or disable the task. PROVEN (registered, Ready).
- If S9 ends BLOCKED its receipt still exists, so C1 starts anyway: S10 is read-only, so the one-writer rule holds.
Calls used: ~10 (inside the planning pane). Next unit (C1) must read PROGRAMME.md first.
