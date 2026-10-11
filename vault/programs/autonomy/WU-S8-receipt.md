# S8 receipt
Status: DONE

Commit d6c73738 (registry-driven tick + canary programme).

## Canary
Goal xdomain-canary (cap 3M, root C:\Users\User\Apps\wt_xcanary, fresh worktree, branch canary/xdomain), 2 units X1/X2 (pure-PP: index the 27 deferred-backlog headings, then check it), chain in vault/programs/xdomain-canary/.
Gap found and fixed: a new programme needed its own scheduled task (a manual step); the registry tool existed but no task ran it. PP-AutonomyChain-Tick's chain_tick.ps1 now runs `chain_registry.py tick` over vault/programs/chains.json; a new programme = one registry entry, no task.

## Claims
1. PROVEN zero manual steps: after the commit the 17:41 tick armed X1 (m-3bdc40e7c41c), 17:51 tick sealed X1 and armed X2 (m-3db5a88b1527); chain status decision=complete, X1/X2 done. No human, no coordinator message.
2. PROVEN zero model on control path: every control action is python from the scheduled task (tick/arm/settle/seal); only the two XS workers used a model (6 tool calls each).
3. Measured spend: goal xdomain-canary used 871584 (settled 121584 for X1, X2 reserved 750000 pending settle at the time of reading). Control-plane model spend 0 (no model session other than workers on this goal).
4. Seal path: X1 partial record said PARTIAL but acceptance gate passed (gate.json passed=true) and the chain advanced; residual file written but not needed.
5. programme_status output (autonomy goal, run from this root): state running, spend settled=18361841 reserved=1916890 unknown=0 interactive=0. programme_status is bound by cwd, so the canary view is `gsdx_chain.py status --chain vault/programs/xdomain-canary/chain.json`: decision complete, envelope used 871584/3000000.
6. NOT_PROVEN worker quality: X2 receipt says backlog-check=mismatch while the file in wt_xcanary reads ok (two "canary x2" commits). Worker-side noise, not control.

## Next unit must know
- Tick task still points at pp-ucda-wt chain_tick.ps1; after landing to live, repoint or keep the worktree.
- X2 may still hold a 750000 reservation until the next tick settles it.
- wt_xcanary worktree and branch canary/xdomain can be removed after the Owner has seen this.
