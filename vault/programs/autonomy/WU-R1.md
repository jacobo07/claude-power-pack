# WU-R1 -- reflex: a breaker-halted unit continues itself (zero model)

Read `vault/programs/autonomy/PROGRAMME.md` first. Owner asked (2026-10-10): "no puedes automatizar ese desbloqueo?".
Measured incident: S5 HALTED twice by the session call breaker before closeout (m-1ebf9abcd5ea, m-05ab467c0a81); the
chain logged `stopped_without_done` every tick for 6 h until a model in a pane wrote the receipt and inserted S5b by
hand (commit d0059f42 shows exactly the transaction to compile).

## Do (tests first, in tools/gsdx_chain.py on feat/ucda; keep `decide` pure)
1. New action `auto_continue` in `decide`, taken instead of `stopped_without_done` only when ALL hold:
   - every mission of the unit is terminal and the latest one is HALTED/COMPLETED without a DONE receipt;
   - it made progress: commits on the root's branch since that mission's `created_at`, or a handoff file newer than it
     (`<packet>.residual.md` written by the steward, or `vault/plans/WU-<id>-progress.md`);
   - fewer than 3 auto-continuations already exist for this unit's lineage (ids `<id>c1`, `<id>c2`, `<id>c3`).
   No progress, or the cap reached, keeps `stopped_without_done` (a human/residual owns it). BLOCKED_HUMAN never continues.
2. The effect (in `tick`, not in `decide`), one transaction:
   - write the packet `WU-<id>cN.md` beside the original: original packet path, the handoff paths, the commit list
     since the mission started, "do only the remaining steps; close by call 22";
   - insert the unit into chain.json right after the halted unit, and re-point `after` of its successor;
   - write the halted unit's receipt `Status: DONE` + `AUTO-CONTINUED in <id>cN (breaker halt, progress: ...)`;
   - log one row. Leave the commit to the next worker (the chain never runs git); the next tick arms `<id>cN`.
3. Tests: halted with progress -> auto_continue; halted without progress -> stopped; cap 3 -> stopped; BLOCKED_HUMAN ->
   stopped; successor re-pointed; idempotent (a second tick does not insert twice). Mutation drill: progress check off
   -> the no-progress gate goes red. Existing test_gsdx_chain and test_chain_registry stay green.
4. Land it to live PP with `tools/land_worktree.py` (the active tick runs the LIVE gsdx_chain.py). Close by call 22.
Receipt: `vault/programs/autonomy/WU-R1-receipt.md`.
