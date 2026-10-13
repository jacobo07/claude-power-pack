# W2 receipt
Status: DONE
COMMITS: db9c2153 (tests RED) · 47aa4d77 (workspace_registry.py + resolve_binding) · 31f9b5f4 (goal_binding.js + session_budget_guard.js, hook gates) · receipt + W3 packet in the next commit
Red -> green: tools/test_workspace_lease.py WS_LEASE_PASS import-fail (module absent) -> 8/10 impl (hook gates not yet written) -> 10/10. Gates: CLAIM-CAS, STALE-GEN-REFUSED, IDEMPOTENT, DOUBLE-CLAIM-RACE (2 spawned processes), CWD-OBSERVE-ONLY, ZOMBIE-FENCED, CLOSED-LEASE-FENCED, PRECEDENCE, HOOK-BINDING, HOOK-CLOSED-LEASE-FENCED (node subprocess).
Mutation kills (tools/mutation_drill.py, isolated copy, copy_dirs=["hooks"], all KILLED): drop gen CAS -> V-WS-STALE-GEN-REFUSED; cwd entry binds -> V-WS-CWD-OBSERVE-ONLY; fenced settle booked as 0 -> V-WS-ZOMBIE-FENCED; ignore closed lease -> V-WS-CLOSED-LEASE-FENCED. (First run was CONTROL_INVALID: the copy lacked hooks/.)
Regression exit codes, base b0e5d871 (detached worktree, removed) vs now, all 0/0: test_goal_lease 10/10, test_goal_budget_admission 54/54, test_session_budget_admission 12/12, test_tranche_driver 27/27, test_hook_boundary 7/7.
Measured spend: NOT MEASURED (packet forbids transcript and ~/.claude/state reads). About 40 tool calls (envelope 45); W3 is sized on that.

## What landed
- modules/provider_routing/workspace_registry.py: WorkspaceRegistry(root): claim (CAS on gen, idempotent), holder, holder_for_cwd (read-only), authority, settle (fenced => journal `fenced` row + ledger.settle_stopped at the measured value).
- tools/mission_spend.py resolve_binding and hooks/lib/goal_binding.js: registry holder > goal roots. Guard: a registry-bound session whose lease is closed/unknown in goal-lineage is denied FENCED.
## Decisions that differ from or extend the packet
- Journal lives in the goal-budget ROOT (`goal-budget/workspace.journal.jsonl`), not a goal dir: one-holder-per-workspace needs one journal all goals contend on.
- "cwd entry is OBSERVE only" is conditional: once the registry journal exists, a root match never writes a binding. With no journal the pre-W2 behaviour is kept (54/54 admission gates pin it). W5/W6 must create the first claim to turn it on.
## Not done / traps
- No CLI yet for claim/holder (module API only); W6 needs one (`goal-workspace-claim`). Not added: mission_spend.py is not frozen but the packet scoped W2 to the registry + wiring.
- The guard fences on closed lease only. A zombie sid is fenced through registry.settle(gen=...); the guard does not carry a per-sid gen.
- Nothing copied to ~/.claude/hooks (W5).
HANDOFF NOTE: W2 done
