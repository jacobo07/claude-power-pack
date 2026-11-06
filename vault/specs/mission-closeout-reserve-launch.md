---
status: DRAFT 2026-11-06 (coordinator lane (b) of the S14 plan the Owner approved with "y"; implementation follows mission-gate-carried-spend)
covers: [closeout-reserve-launch, authority-trip-closeout]
owner: tools/gsd_mission.py supervise (cost-hold stop branch) · hooks/lib/mission_gate.js holdDecision
---

# A mission-authority trip must spend its closeout reserve on an actual closeout

## Incident (measured, m-84f2641865dd, S13, 2026-11-05)
16:12:38Z `cost_breaker_tripped` with reason "only closeout may run". 16:12:39Z `cost_hold_worker_stopped` (zero grace for
an authority hold, gsd_mission.py supervise cost-hold branch). Nothing launched afterwards: no closeout turn ran and
`evidence/ascension/s13/closeout.md` did not exist until the Owner raised the authority 2 h later.

Root cause (RCA 2026-11-06): the reserve is accounting only. It moves the trip line (`mission_spend.judge`), the
renewal and `set_authority` checks, and AMR's lease pricing, but no code path launches a closeout-only worker. On the trip,
`holdDecision` denies every tool call with no carve-out, the sweep stops the worker with zero grace, AMR prices no lease
(room < 0) and `_dead_worker_authority_guard` marks the mission CAPITAL_EXHAUSTED, "not replaced". The hold and the missing
closeout are designed behaviour, not a race.

## States the controller must distinguish (S14 brief XVII)
IMPLEMENTATION_STOPPED -> BUDGET_EXHAUSTED -> CLOSEOUT_AUTHORIZED -> CLOSEOUT_LAUNCHED -> CLOSEOUT_COMPLETED (checkpoint
persisted by the closeout worker) -> mission parked. A stopped worker plus a hold is BUDGET_EXHAUSTED, never "complete".

## Change (extends the breaker and the relay; no second breaker, no new loop)
1. After `cost_hold_worker_stopped` for an AUTHORITY hold, if the reserve is > 0 and the record has no `closeout_lease`,
   the sweep writes `closeout_lease={granted_at, tokens: reserve, base_spend: spent, sid: null}` (CLOSEOUT_AUTHORIZED) and
   launches ONE fresh worker through the existing launch path with a closeout prompt: read the brief's closeout section,
   write the closeout file from committed evidence, commit it, declare CHECKPOINT_COMPLETE (or a residual). Ledger
   `closeout_launched` with the session id (CLOSEOUT_LAUNCHED).
2. `holdDecision` admits that session only (`closeout_lease.sid`), only while its own usage + next call stays under the
   lease tokens; every other session stays denied. Past the lease -> deny, as today.
3. A checkpoint declared by the closeout session -> `closeout_done` (CLOSEOUT_COMPLETED). A closeout worker that ends
   without one -> `closeout_failed` ledgered, surfaced, never relaunched (one lease per trip; a second trip needs a new
   Owner authority).
4. Kill switch `CPP_MISSION_CLOSEOUT_LAUNCH=off` keeps today's behaviour.

## Acceptance (tools/test_gsd_mission_cost_hold.py, new V-COST-CLOSEOUT-*)
- Authority 30M, spend 29.4M, authority hold, worker stopped -> exactly one `closeout_launched`, lease tokens = reserve;
  a second sweep pass launches nothing.
- Reserve 0 (`closeout_tokens=0`) -> no launch, today's CAPITAL_EXHAUSTED.
- Gate: the lease session is admitted under the lease, denied past it; any other session of the mission stays denied.
- Closeout session ends with a checkpoint -> `closeout_done`; ends without -> `closeout_failed`, no relaunch.
- Mutation: removing the once-only check gives a second launch (red).

## Never
- Never launch a closeout for a non-authority hold (Owner park, stall) or with no reserve.
- Never let the closeout session do productive work: the prompt is closeout-only, and its spend is capped by the lease.

## Rollback
`CPP_MISSION_CLOSEOUT_LAUNCH=off`, or revert the commit; `closeout_lease` is read by nothing else.
