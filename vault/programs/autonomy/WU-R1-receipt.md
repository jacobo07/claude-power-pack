# R1 receipt
Status: BLOCKED_HUMAN

- `auto_continue` in `decide` (pure, `progress` injected) + `auto_continue()` effect in `tick`: packet cN, chain insert with successor re-pointed, halted receipt DONE + AUTO-CONTINUED line. No git run by the chain.
- PROVEN: test_gsdx_chain 20/20 (7 new V-CHAIN-AUTOCONT-*: insert, repoint, idempotent, no-progress, cap 3, BLOCKED_HUMAN, default-no-evidence); test_chain_registry 8/8.
- PROVEN: mutation drill (progress gate forced on, isolated copy) -> 6 gates red.
- NOT_PROVEN: live tick against a real HALTED mission (`created_at` format handled as epoch or ISO; unobserved live).
- BLOCKED_HUMAN: land_worktree REFUSED REBASE_CONFLICT at 6cfde80b (S2) vs live d74c385e; branch restored at 39a92181, nothing landed. R1 is NOT live until feat/ucda (S1-S5 + R1) is reconciled with live tools/{gsd_mission,mission_spend,gsdx_chain}.py. Receipt: WU-R1-land.json.

