---
status: APPROVED 2026-11-06 (Owner "y 60M" to the S16 plan, lane C1, session 177efe77; plan vault/programs/ascension/S16-PLAN-PROPOSAL.md)
covers: [mission-close, close-cli, terminal-close, owner-close]
owner: tools/gsd_mission.py close_mission
---

# `close`: settle a mission terminal on the Owner's word

## Problem (measured 2026-11-06, Solver Ascension coordinator 177efe77)
The mission controller had no verb that ends a mission. To close 12 missions that were RUNNING with no progress
(S9..S15, recon-general, m-088f20232c3c, m-34bc2fe24e53, m-5b1d5ae8d356), the coordinator called
`gm.transition(event="hold_settled", state=HALTED)` by hand from Python on GEX44 (Owner "go ahead", 11:50:30Z).
That path:
- borrowed the sweep's own event name, so the ledger cannot tell an Owner closure from a sweep settlement;
- recorded no Owner authority and no reason of the Owner's;
- did not stop a live worker (all 12 had none, by luck of the moment);
- relied on a pre-existing `owner_hold` to keep renewal refused.
`--supersedes` is not a substitute: it needs a workstream goal key and only applies at `arm`.

## Decision
`gsd_mission.py close --mission <id> --reason <text> --owner-turn <session>:<timestamp> [--outcome HALTED|COMPLETED]`
calls `close_mission`. Default outcome HALTED.

1. **Authority.** `--owner-turn` is required and is resolved by `verify_owner_turn` to exactly one Owner message in
   that session's transcript (the `authority` verb's rule, T1 F2). A free-text authority is never accepted. One Owner
   turn may close several missions (one "go ahead" closed 12).
2. **Refusals, record unchanged:** unknown mission; a TERMINAL mission (nothing to close); empty reason; outcome not
   HALTED/COMPLETED; owner turn unverifiable.
3. **Worker stop.** The worker is proven gone when there is no owner, or the hold recorded its own stop
   (`worker_stopped_at`). Otherwise the host is asked (`host_sessions`):
   - host unavailable (None) -> REFUSE, record unchanged. `stop_owner` answers "not listed by host" = ok for a None
     list, so it cannot be the judge here; an unanswered host is UNKNOWN, and UNKNOWN never closes.
   - host answered -> the mission is parked with an `owner_stop` hold BEFORE the stop (if it holds nothing yet), so
     no sweep pass can launch a successor during the stop's wait (review F1, 2026-11-06).
   - `stop_owner` (host `claude stop` + wait for the pid) fails -> the park stands, the ledger gets
     `mission_close_stop_failed`, and the close is NOT applied (`closed: False`, exit 1). A retry after the worker
     dies closes it.
   - ok -> the stopped worker's spend is booked (`settle_stopped_worker`, best effort, as `_stop_for_wait`).
   - the record is re-read; if its epoch or owner differ from the ones read before the stop, the stopped worker is
     not the current one: CasConflict, nothing closed.
4. **Terminal write.** One `transition()` with compare-and-swap on epoch, state AND `seq` (re-read after the stop):
   `event="mission_closed"`, `state=<outcome>`, `pending=None`, `closed={at, outcome, reason, owner_turn, prior_state,
   stop}`, and `owner_hold={kind: "closed", reason, set_at, prior: <old hold or None>}`. The hold is what
   `renewal_refusal` reads, so a closed mission is never renewed whatever its halt reason says. The ledger row carries
   `outcome`, `prior_state`, `owner_turn` (uuid) and `stop`.
5. **Budget guard.** After the write, `hold_guard_budget` writes the stop=1 session guard for every session the
   mission spent through (best effort), so an interactive owner left running cannot keep spending under the mission.
6. `release` refuses a hold of kind `closed`: a closed mission is reopened only by arming a new one.

## Acceptance (tools/test_mission_close.py, V-CLOSE-*)
- No owner, PREPARED: closes HALTED; record carries `closed` and the `closed` hold; ledger has `mission_closed`.
- RUNNING with a background worker the host stops: `claude stop` invoked, pid waited, closes; `closed.stop` names it.
- RUNNING, host unavailable: refuses; record byte-identical (no hold, no state change).
- RUNNING, stop fails (pid survives): `closed: False`; an `owner_stop` hold stands; state not terminal;
  `mission_close_stop_failed` ledgered.
- Held with `worker_stopped_at`: closes without asking the host.
- TERMINAL, empty reason, bad outcome, unverifiable owner turn: each refuses, record unchanged.
- `--outcome COMPLETED` lands COMPLETED.
- After close: `renewal_refusal` refuses even with a `budget:` halt reason; `plan_next` answers none; `release` refuses.
- A record moved between the stop and the write (seq bumped) raises CasConflict and the mission is not closed.
- CLI: missing `--owner-turn` exits 2 with nothing written.
- Mutation drills: dropping the host-None refusal, the `expect_seq`, the closed hold, or the release refusal each
  turns its gate red.

## Accepted, not changed
- `mission_steward` counts any mission with an `owner_hold` as covering its goal, before the terminal check, so a
  goal whose missions were all closed is not reported as forgotten. A close is a deliberate Owner decision; the
  hand-closed missions of 2026-11-06 already behaved this way (review F3).

## Never
- Never close on a self-reported authority string.
- Never write a terminal state while a background worker is not proven stopped.
- Never reuse the sweep's `hold_settled` event for an Owner closure.

## Rollback
Remove `close_mission`, the `close` sub-parser and dispatch, the `closed` check in `release_owner_hold`, and the test
file. Records already closed stay terminal; their `closed` field is read by nothing else.
