# RESUMPTION -- Context Rent Extinction (goal ctx-rent)

Identity: worktree C:\Users\User\Apps\pp-ctx-rent, branch ctx/rent (off 86ad6f16). Spec
vault/specs/context-rent-extinction.md (Owner "y+floor" 2026-10-08). Goal ctx-rent cap 6,000,000
incl. the coordinator pane. Thesis: rotation already works but fires at ~450k; move it to economics.

State: S0 DONE (goal declared, spec + this file). Next: S1 rent meter.

Decisions: extend rollover.py / rollover_wall.js / rollover_econ.py / rollover_replay.py / kresume.md only.
A4 owns mission/worker side -- do not duplicate. 45 % wall stays (Owner band 40-50 %).

Next 3 actions:
1. S1: deterministic baseline from ~/.claude/state/rollover/rollover-ledger.jsonl + transcripts; write
   vault/audits/ctx-rent/baseline-2026-10-08.md (MEASURED/ESTIMATED labels).
2. S2: measure what a successor reads before first mutation; cut /kresume to an obligation-scoped projection.
3. S4: replace MIN_GROWTH_TOKENS with a derived minimum; state-conditioned prior.

Start: read the spec, then do action 1. Work only inside this worktree. Commit per unit (pathspec).
