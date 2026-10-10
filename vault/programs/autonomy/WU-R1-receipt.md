# R1 receipt
Status: DONE

- `auto_continue` in `decide` (pure, `progress` injected) + `auto_continue()` effect in `tick`: packet cN, chain insert with successor re-pointed, halted receipt DONE + AUTO-CONTINUED line. No git run by the chain.
- PROVEN: test_gsdx_chain 20/20 (7 new V-CHAIN-AUTOCONT-*: insert, repoint, idempotent, no-progress, cap 3, BLOCKED_HUMAN, default-no-evidence); test_chain_registry 8/8.
- PROVEN: mutation drill (progress gate forced on, isolated copy) -> 6 gates red.
- NOT_PROVEN: live tick against a real HALTED mission (`created_at` format handled as epoch or ISO; unobserved live).
- Next: landing via tools/land_worktree.py (see commit log).
