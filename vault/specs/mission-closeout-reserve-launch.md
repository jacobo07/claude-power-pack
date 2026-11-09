---
status: IMPLEMENTED 2026-11-06 (S14 coordinator lane (b), Owner "y"; S15 brief XXVIII). See "As built" at the end.
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

## As built (2026-11-06) -- deviations from the draft, each for a measured reason
- **Owner:** `gsd_mission.closeout_gate` runs as a sweep step before `_dead_worker_authority_guard`, not inside the stop
  branch. It fires once the authority hold has `worker_stopped_at` (or the owner is DEAD), which is one pass after the
  stop.
- **Lease size:** `tokens = min(reserve, authority - spent)`, not the bare reserve. S13 overshot the line by 4.4M, so a
  bare-reserve lease would have spent past the Owner's authority. Under 100k of room, the lease is recorded
  `CLOSEOUT_FAILED unfunded` and no worker is launched.
- **Launch:** `launch_worker(prompt_override=closeout_prompt)` takes the existing claim -> launch -> ack path. The
  deterministic and done-gate closes are skipped, and the prompt is closeout-only, with the checkpoint command in it.
- **Completion:** `set_checkpoint` under an authority hold with a launched lease of the current epoch marks
  `CLOSEOUT_COMPLETED` and keeps the hold. `_closeout_follow` stops the idle worker.
  - A closeout worker that ends its turn without a checkpoint is `CLOSEOUT_FAILED`.
  - So is one that ends on a question (WAITING_HUMAN). A closeout needs no human, and S14 sat 7.5 h on such a question.
  - So is one never acked before the start deadline.
  - None of these is relaunched.
- **Supervisor:** `plan_next` returns `none` while the lease is AUTHORIZED or LAUNCHED, so recovery, settle and relay
  cannot touch the closeout worker.
- **Gate:** `mission_gate.js closeoutLease`. `holdDecision` admits only the record's owner at the lease epoch.
  `exposureDecision` caps that session's own usage (main + subagents) at the lease. `mission_wall.js` already stays
  silent once `worker_stopped_at` is set.
- **Review fixes** (pp-code-reviewer verdict WARNING: one HIGH and two MEDIUM, all fixed):
  - **H1.** A lease left `CLOSEOUT_AUTHORIZED` by a lost final write is now resolved. When the record reached
    claim_epoch + 1 it becomes LAUNCHED; past the start deadline it becomes FAILED. The final write is retried on
    CasConflict.
  - **M1.** The AUTHORIZED write is a CAS on `seq`. A launcher that loses the claim writes nothing.
  - **M2.** A finished lease is history only under a NEW Owner authority, so a new trip gets its own closeout. A
    LAUNCHED lease whose record moved epoch is retired as `superseded`.
- **Gates:** test_gsd_mission_cost_hold V-COST-CLOSEOUT-* (24 checks; suite 59/59). Five mutation drills were run, and
  each turned its target red:
  - once-only lease check removed: 3 checks red;
  - the gate's lease admission removed: 2 red;
  - `expect_seq` dropped: CONCURRENT-SWEEP red;
  - the history rule dropped: NEW-AUTHORITY red;
  - the AUTHORIZED branch dropped: 2 red.
- **Residual:** metering is post-hoc, so the lease can be passed by about one call. With no transcript path the lease
  session is admitted unmetered (the same rule as the exposure check).

## Amendment 2026-11-09 -- unlisted background owner (S22 m-4a5a719551ae)
- **Defect (measured):** the authority trip at 14:01:38Z found worker f271b7bd already gone and no longer listed by the
  host. `liveness` returns UNKNOWN for an unlisted background owner (the host owns its restarts), the sweep's stop
  branch stops LIVE owners only, so `worker_stopped_at` was never set and `closeout_gate` (DEAD or stopped only)
  never leased the 400k reserve. Observed 2.5 h with `closeout_lease: null`.
- **Rule:** on an authority hold, a background owner absent from a host list that WAS read is settled through
  `stop_owner` (the same host path `close` uses) and recorded as the hold's `worker_stopped_at`; the gate then
  proceeds. `sessions is None` (host not asked) settles nothing. A listed owner is untouched (LIVE stays excluded).
- **Gates:** V-COST-CLOSEOUT-UNLISTED-BACKGROUND-LAUNCHES (red before the fix, green after),
  V-COST-CLOSEOUT-CONTROL-HOST-LIST-UNAVAILABLE, V-COST-CLOSEOUT-CONTROL-LIVE-WORKER unchanged. COST_HOLD 61/61, MC 242/242.
- **Residual:** an unlisted owner the host later revives would overlap the closeout worker; the same exposure `close`
  already accepts.