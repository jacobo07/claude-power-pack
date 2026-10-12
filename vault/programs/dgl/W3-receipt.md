# W3 receipt
Status: DONE
COMMITS: 52db5918 (gates RED) · 04ba8fff (tools/goal_succession.py, 8/8) · 5ebf782c (tools/goal_chain.py + tick hook + V-SUCC-CHAIN-HOOK, 9/9) · receipt + W4 packet in the next commit
Red -> green: tools/test_goal_succession.py ModuleNotFoundError (module absent) -> 8/8 -> 9/9 (SUCCESSION_PASS=9/9). Gates: TERMINAL-SETTLED, UNKNOWN-RESERVED-HOLDS, TTL-SWEEP-MEASURED-ONLY, IDEMPOTENT, RESUME-AFTER-CRASH (subprocess killed with os._exit between close and open), DOUBLE-SUCCESSOR-RACE (2 spawned processes), AUTHORITY-REQUIRED-NO-HALF, CLI, CHAIN-HOOK.
Mutation kills (tools/mutation_drill.py, copy_dirs tools/modules/hooks, all KILLED): unknown treated as terminal -> V-SUCC-UNKNOWN-RESERVED-HOLDS; drop succession-id idempotence (done lookup) -> V-SUCC-IDEMPOTENT; claim before close/open -> V-SUCC-AUTHORITY-REQUIRED-NO-HALF; drop the measured-only TTL guard -> V-SUCC-TTL-SWEEP-MEASURED-ONLY.
Regression exit codes, before = detached worktree at 52db5918^ (removed) vs now, all 0/0: test_goal_lease, test_workspace_lease, test_goal_budget_admission, test_session_budget_admission, test_tranche_driver, test_hook_boundary.
Measured spend: NOT MEASURED (packet forbids transcript and ~/.claude/state reads). About 30 tool calls (envelope 45); W4 is sized on that.

## What landed
- tools/goal_succession.py: reconcile (TERMINAL_PROVEN only with dead=True AND an int measured; else UNKNOWN_RESERVED, hold kept, first-seen journalled), sweep_unknown (past TTL 1800 s converts only by a measured value), succeed (STEPS settle, close, open, claim; refusals returned: UNKNOWN_RESERVED, AUTHORITY_REQUIRED, CAS_LOST, CLAIM_LOST), CLI succeed/reconcile (rc 0 ok, 3 refused). Per-succession journal goal-budget/<goal>/succession.journal.jsonl, deduped by (op,key).
- tools/goal_chain.py react: acts only on `stopped_without_done` / `refuse_envelope`, and only when vault/programs/dgl/succession-plan.json exists. dgl_chain_tick.ps1 calls it; gsdx_chain.py (driver, live checkout) is untouched, so no copy-free hook point was needed.
## Decisions that differ from the packet
- Sibling module, not the ledger: the ledger stays a pure spend fold; the cross-journal order lives in goal_succession.py.
- succeed() takes old_sid/dead/measured (evidence) and root/now/ttl keyword args beyond the packet's signature.
- The envelope is pre-checked BEFORE lease_close (lease_open's own formula, latest lease's reserves added back), so an AUTHORITY_REQUIRED succession leaves the old lease open and the old holder with its workspace. A refusal is journalled once by lease_open.
## Not done / traps
- CLAIM_LOST after a won lease_open leaves the lease open and unclaimed; W4's crash matrix must pin the outcome.
- Nothing claims in live state; no succession-plan.json exists, so the tick hook is inert. Nothing copied to ~/.claude/hooks (W5).
HANDOFF NOTE: W3 done
