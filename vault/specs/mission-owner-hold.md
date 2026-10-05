---
covers: [mission-owner-hold, owner_hold, gsd-mission-park, renewal-refusal-owner-hold]
status: LIVE once the commit carrying this spec, gsd_mission.py and tools/test_gsd_mission_owner_hold.py lands
parent: vault/specs/mission-continuity.md (v3); TOK-18 gen2 S0 (Owner approval 2026-10-05)
---

# Mission Owner hold -- park a mission without killing its identity

## Why
A non-terminal mission has no Owner-controlled park. The supervisor halts a BLOCKED mission once its budget
is spent, and a budget halt with GSD work remaining is renewed (up to 3 times per lineage) into a fresh
mission whose worker resumes the roadmap. Measured 2026-10-05: `m-4df3ebcb89ff` (BLOCKED + budget) was
renewed as `m-608c8d8d761f`, itself BLOCKED, due to hit its budget at 19:56Z and renew again. The Owner
ordered that roadmap NOT to resume under the old execution architecture. The existing holds do not cover
this: the provider hold is quota-only, `gsd_hold` is the supervisor's own GSD verdict, and
`CPP_MISSION_RENEW=off` is estate-wide.

## Contract
* `owner_hold` on a mission record = `{reason, set_at}`. Set and cleared ONLY by the Owner-facing CLI
  (`gsd_mission.py hold --mission ID --reason TEXT` / `release --mission ID`), through the same
  compare-and-swap `transition` as every other change (ledger rows `owner_hold_set` / `owner_hold_released`).
  An empty reason is refused. A terminal mission cannot be held (nothing to park).
* While held, `plan_next` answers `none` for every non-terminal state BEFORE any budget, launch, replace,
  relay or unblock decision: nothing is launched, stopped, halted or renewed, and the record keeps its
  identity, epoch and state. Holding is not halting.
* `renewal_refusal` refuses a held mission (second guard: a halt reached by any other path still does not
  renew while the hold stands).
* Release returns the mission to normal supervision; the budget clock is NOT reset (a release is not a
  fresh budget -- a spent budget halts on the next pass, and renewal then judges it normally).

## Acceptance (each can go red)
1. Held + budget spent + owner dead -> `plan_next` = none (control: the same record unheld -> halt).
2. Held BLOCKED, held RUNNING, held LAUNCHING, held PREPARED -> none.
3. `renewal_refusal` on a held budget halt -> refused naming the hold (control: unheld -> None).
4. hold with empty reason refused; hold on a terminal mission refused; release clears it.
5. Mutation drill: remove the `plan_next` check -> test 1 red; remove the renewal guard -> test 3 red.

## Rollback
Release the hold (`release`), or revert the commit; a record carrying `owner_hold` under old code is ignored.
