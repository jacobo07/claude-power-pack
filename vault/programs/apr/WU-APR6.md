# WU-APR6 -- Judge the canary, capture knowledge, hand off (Production Reality, part 2)

Common brief: `PROGRAMME.md`. Read `WU-APR5-receipt.md` and `vault/programs/apr-canary/EXPECTED.md` first.
Route S. cwd `C:\Users\User\Apps\wt_apr`. This unit arms only after the canary's C3 receipt exists and no canary
mission is live (the chain's `wait` + one-writer rule), so the canary ran with nobody watching.

Steps:
1. Evidence, read-only: canary rows in `~/.claude/state/gsdx-chain.jsonl` (goal apr, canary units), the mission
   records/ledger rows for each canary mission, the seal/refusal files, `tools/gsdx_chain.py status --chain
   vault/programs/apr-canary/chain.json`. Compare to EXPECTED.md row by row: C1 sealed by the finalizer with no
   renewal; C2 refused -> residual -> sealed; C3 armed with trigger event; no duplicate arm; no human_gate; wall time
   inside the window; and the coordinator pane sent nothing (no mission or row was created by an interactive
   session -- cite the launch causes). Write `vault/programs/apr/PRODUCTION-REALITY.md` with every row quoted.
   A mismatch is a finding, not a failure to hide: record it in KNOWLEDGE.md, fix it if internal (new commit + test,
   install like APR-4 step 3), otherwise say exactly what remains.
2. Disable `PP-AprCanary-Tick` (Disable-ScheduledTask; do not delete it) once the canary is complete.
3. Knowledge: finish `vault/programs/apr/KNOWLEDGE.md` (every bug this programme found). Append UKDL CANDIDATES (not
   promoted) to `vault/knowledge_base/ukdl-universal.md` for: receipt syntax as truth (trap); one parser per fact
   (process rule); machine-critical lifecycle state must not rest on model-authored text alone (hard-rule candidate);
   an active programme needs progress, an explicit wait, recovery, or a terminal state (hard-rule candidate);
   human-as-watchdog (trap). Each with evidence ids and the UCR-CIF stage reached (expected: OBSERVED + LOCAL SUCCESS
   + REGRESSION + PRODUCTION REALITY in one repo; cross-project NOT earned). Extend EWC K5 with a pointer.
4. `vault/programs/apr/REPORT.md`: the handoff contract (root cause, unit-state authority, receipt role, residual
   model, auto-recovery, event loop, watchdog, bounded silence, fencing, attribution, route estimation, no-user proof,
   EWC status E1-E6, commits in causal order, change impact, UNPROVEN list, next task). Measured numbers only, each
   with its source command.
Receipt: PRODUCTION-REALITY verdict per expected row; files written; UNPROVEN list.
