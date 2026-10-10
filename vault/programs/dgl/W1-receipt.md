# W1 receipt
Status: PARTIAL
Blocker: session budget guard tripped at 20 tool calls (estimate 13) after reading only. No code, test, OWNERSHIP.md or W2 packet was written. Nothing implemented.
First-call floor: ~112K tokens at the first call (15,000,000 -> 14,888,256 left, includes the standing prefix).
COMMITS: this receipt only.
Red -> green: not run (tools/test_goal_lease.py not written). Mutation kills: not run. Regression exit codes (goal_budget_admission, session_budget_admission, tranche_driver): not run.
Measured spend: about 150K tokens (15,000,000 -> 14,850,676 left).

## State at stop (verified)
- dgl goal status: cap 17,000,000, used 1,369,500, open 725,545, settled 643,955. Not crossed.
- Branch dgl/durable-goal-lease, tree clean apart from untracked .pp-capabilities.
- Read: ledger.py in full, mission_spend.py 380-580 and 800-918, plan sections 1-3.

## Findings the next worker should reuse (cite file:line)
- GoalLedger._gfold ledger.py:189-222 is the only fold. declare_cap :256, renew :293, spawn :363, settle_stopped :335, status :382 (status sweeps leaks, so it APPENDS rows; goal-lineage must use a lock-free _gfold(_read()) instead).
- mission_spend goal_declare :489, resolve_binding :646, _main :802 (goal-* dispatch :861-898), state_dir :194 (GSD_LONG_RUN_STATE_DIR).
- Owner-ness: goal_declare treats `owner and not inside_agent()` as the Owner; reuse that rule for programme ops.
- gsd_mission.renew_mission :2188; mission_steward settle_stopped call :157. tools/gsdx_chain.py is NOT in this worktree: the tick wrapper points at Apps\pp-gsdx-factory-2\tools\gsdx_chain.py. goal_binding.js is hooks/lib/goal_binding.js (goalBinding :99).

## Design decided (not yet written)
- programme / lease_open / lease_close / authority_required rows in the goal's own journal. Fold keeps goal cap/used unchanged when no programme or lease row exists.
- lease_open: idempotent by succession_id; CAS prev_lease == latest lease id (loser gets a refusal naming the winner); the row closes the predecessor; need = cap + reserves, executable = programme - settled - open (RESERVED+LEAKED) - reserves of other open leases; short -> one authority_required row per succession id, status AUTHORITY_REQUIRED.
- A cap row for a closed lease is refused in declare_cap and ignored by the fold. Per-lease used = settle watermark deltas booked while it was current + holds opened under it.
- Add goal-lease-open, goal-lineage and programme-status (read-only, no rows) plus an Owner-TTY goal-programme.

## Open points
1. GUARD BLOCK: a PowerShell call naming the live goal-budget directory was denied as "touches goal-budget state from a bound session". V-LEASE-LEGACY-FOLD on byte copies of the rf-p3b and canary-20261007 journals cannot be fed from this bound session. Make the test take copies via an env var and have the Owner or an unbound session supply them. Do not route around the guard.
2. The next call budget needs about 3x the W1 estimate: 13 calls cannot hold step 2 through step 8 once reading is done.
HANDOFF: W1 PARTIAL. Next action is to write tools/test_goal_lease.py (RED), then the ledger and CLI changes.
