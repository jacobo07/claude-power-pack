# WU-S7 -- Autonomy Convergence unit S7

Read `vault/programs/autonomy/PROGRAMME.md` first (session loop, continuation units, constraints).
Your scope: Plan section 3 rows 'Waiting', 'Reflexes', '8 invariants'.

## Do
Deterministic V-gates for the 8 invariants (duration, goal count, history, capability, test estate, observability, wait, control), each with a mutation drill. Reflex coverage counter over steward / linger-kill / reapers / chain refusals (known failure classes handled with zero model, as a number). Record the compiled patterns: manual re-arm -> chain, manual landing -> land_worktree.

Receipt: `vault/programs/autonomy/WU-S7-receipt.md`.

## Added 2026-10-10 (from the S5 halts, observed by the bootstrap pane)
- Reflex: a unit HALTED by the call breaker that left a handoff (residual / progress file) must not stall the chain as
  `stopped_without_done`. Compile the known recovery: the chain (or steward) inserts the continuation unit from the
  handoff deterministically, or the breaker reserves its last N calls for closeout writes (receipt, chain.json). Test it.
- Bug: `programme_status.py` prints spend UNKNOWN for goal autonomy-convergence while `mission_spend goal-status` reports
  settled 5,996,557. Fix the projection's spend source; add a gate that compares both.

## Added 2026-10-11 (bootstrap pane)
- Reflex: `gsd_mission release` of a held mission drops its admission, so the sweep logs `work unit not admitted (verdict none)` on every pass and never launches it (L1 sat 2.7 h). On release, re-admit from the recorded route when packet + route sha are intact (same rule as A3 readmit_for_relay). Test it.
- Attribution: an interactive pane whose cwd enters a goal root is charged to that goal (pane b3fb1dd2: 6.0M into autonomy-convergence). Charge it with role=control/interactive and show it apart in programme-spend and programme_status.
