---
status: APPROVED 2026-11-06 (Owner "y" on the S14 plan, coordinator lane (b): breaker overshoot)
covers: [mission-gate-carried-spend, breaker-overshoot, next-call-exposure]
owner: hooks/lib/mission_gate.js decide (Env 0) · tools/gsd_mission.py _reconciled_breaker
---

# The pre-call mission gate must see the whole mission's spend, not one session's

## Incident (measured, m-84f2641865dd, S13, 2026-11-05)
Authority 30,000,000 processed, closeout reserve 1,000,000 (trip line 29,000,000). Ledger: 16:07:08Z `cost_mark` at
28,725,068 (progress_frontier); 16:12:38Z `cost_breaker_tripped` spent=33,405,167. The worker (epoch 5) burned ~4.7M in
the 5-minute sweep window and passed the line by 4.4M.

The pre-call gate (`mission_gate.js` decide, step 4 "next-call exposure") existed and ran on every call. It did not deny
because (RCA in scratchpad breaker_rca.md, 2026-11-06):
1. `used` = this session's main transcript + `record.spend_carried`. Nothing in the repo writes `spend_carried`, so the
   ~23M of epochs 1-4 were invisible: the epoch-5 worker looked like a ~5-10M mission.
2. Its subagents (`<sid>/subagents/agent-*.jsonl`, counted by the sweep's meter) were not in `used`.
3. `hardCap` used the raw authority (30M), not authority minus the closeout reserve the breaker trips at.

## Change (extends the existing gate and breaker; no second breaker)
- **Floor.** The gate reads a measured floor `{tokens, at}`: the freshest of `record.cost_mark` and a new
  `record.spend_stamp`. Mission spend is then at least `floor.tokens + (session + its subagents' usage dated after
  floor.at)`. `used` = max(that, session + subagents + spend_carried). Both are lower bounds, so a deny stays positive
  evidence. A row with no readable timestamp counts as after the floor only when the floor is absent (never silently
  dropped from the session total).
- **Subagents.** `used` includes `<transcript dir>/subagents/agent-*.jsonl` of the current session.
- **Reserve.** The authority cap is `authority - closeout_reserve` with the same rule as `mission_spend.closeout_reserve`
  (`closeout_tokens`, else min(1M, authority/20)). Label "authority minus closeout reserve".
- **Stamp.** `_reconciled_breaker`, on a pass that does not trip, writes `spend_stamp={tokens, at}` when the measured
  spend moved >= 1,000,000 since the last stamp (bounded writes: at most one per 1M processed).

## Residual (stated, not hidden)
Metering is post-hoc: the gate admits a call whose cost is only known after it returns, so a mission can still pass its
line by about one call's context (~1M for a serial worker) plus, with N parallel subagents, N calls. Zero overshoot is not
claimed.

## Acceptance (tools/test_mission_gate.py, V-MG-*)
- V-MG-CARRIED-FLOOR-DENIES: authority 30M, cost_mark 28.7M at T, the session has 0.4M dated after T and a last call of
  0.3M -> deny (28.7+0.4+0.3 > 29.0). Control: same with cost_mark 20M -> admitted.
- V-MG-SUBAGENTS-COUNT: authority 30M, main 20M, subagents 8.5M, last 1M, no floor -> deny. Control without the subagent
  file -> admitted.
- V-MG-RESERVE-CAP: the existing near-cap case now names "authority minus closeout reserve"; a case between 29M and 30M
  denies only because of the reserve.
- V-MG-STAMP (in tools/test_mission_continuity.py or the breaker suite): a non-trip pass with +1M writes spend_stamp;
  +0.5M does not.
- Mutation: dropping the floor turns V-MG-CARRIED-FLOOR-DENIES red; dropping subagents turns V-MG-SUBAGENTS-COUNT red.
- Existing suites stay green: test_mission_gate, test_mission_spend, test_mission_authority, test_gsd_mission_cost_hold,
  test_mission_continuity, test_gsd_mission.

## Amendment A (2026-11-06): the gate was not running on GEX44 at all
Measured on GEX44 after landing the change there: `~/.claude/settings.json` registers only
`~/agora/mission-hooks/mission_hold_gate.js` (matcher "*", hold-only) for missions; session_budget_guard has no
dispatcher lane (V-SBG-WIRED 0/3 lanes there), so decide's step 4 never ran for any GEX44 worker. Fix: step 4 is now
`exposureDecision` (side-effect free, like holdDecision) and the standalone hold gate runs it after the hold check.
Deploy: the agora copy (hook + lib) is replaced from the PP after a backup. Gates V-MG-HOLDGATE-DENIES-EXPOSURE and its
under-cap control, driven through the hook's stdin entrypoint; the mutant without the call goes red.

## Never
- Never deny on an unmeasured number (no transcript -> no exposure deny, as today).
- Never let the gate write the record.

## Rollback
Revert the commit. `spend_stamp` is read by nothing else; old records without it behave as today plus the reserve.
