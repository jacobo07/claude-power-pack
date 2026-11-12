---
status: SPECIFIED 2026-11-12 (Owner, session 423c9c50: "recarga y si no sale cambia de estrategia, eso deberia pasar de forma 100% autonoma"; "hazlo ambas cosas" = code + GEX44 deploy)
tier: T2
covers: [checkpoint-complete-pivot, preauthorized-topup, arm-pivot-default, mission-checkpoint-autonomy]
owner: tools/gsd_mission.py (pivot_decision, topup_pass, set_authority, arm)
---

# A wave that closes with the Goal open continues on its own, and a top-up the Owner pre-authorized is spent without asking again

## Incident (measured 2026-11-12, GEX44, S30T m-2e14179c5b6a)
The worker declared `CHECKPOINT_COMPLETE` (P1 REFUTED, 0 certificates) at ~01:16Z with `owner_required: false`. The mission
then sat for 10.8 h (`waited_s=38947`) until the Owner asked. Three causes, each in code:
1. S30T was armed without `pivot-autonomy --on` (off by default).
2. `pivot_decision` only pivots `METHOD_PIVOT_REQUIRED` / `NEXT_PLAN_REQUIRED`; `CHECKPOINT_COMPLETE` always parks, although
   the worker card itself defines it as "the wave's obligations are closed and the Goal is not".
3. The arm granted "20M + 2x4M top-ups", but the top-ups existed only as text: nothing could spend them, so room 1.35M
   after the reserve would have parked the next wave for the Owner again.

## Change
**C1 (checkpoint-complete-pivot).** On an opted-in mission, `CHECKPOINT_COMPLETE` is a pivot state like
`NEXT_PLAN_REQUIRED`. The residual falls back to the checkpoint's `--evidence` when `--residual` is absent. Every existing
guard stays and runs first: the authority net (typed receipt objects + `mission_policy.gate_question` over the reason),
the streak cap, Gen2 early stop / hard cap, the kill switch `CPP_PIVOT_AUTONOMY=off`. No residual and no evidence = park.

**C2 (preauthorized-topup).** `authority --topups N --topup-size S` records, under a verified `--owner-turn`, N top-ups of
S tokens each (`topups = {left, size, owner_turn}`). `topup_pass` (one more step of `supervise`, never in a dry run) spends
ONE when a live mission's room after the closeout reserve is below `TOPUP_TRIGGER_TOKENS` (3M, one measured epoch):
- only when the mission is not terminal and holds no hold, or only a checkpoint/resource hold (never an Owner, cost or
  authority hold: an already-tripped breaker stays the existing Owner path);
- `authority_tokens += size`, `left -= 1`, a receipt in `authority_receipts` naming the stored owner turn and
  `actor: sweep:topup`; ledger `topup_applied`; `mission_remedies.notify_incident` once (key `topup:<mission>:<n>`);
- an unmeasurable spend never spends a top-up (absent is not zero); `left == 0` does nothing.
Kill switch `CPP_MISSION_TOPUP=off`.

**C3 (arm-pivot-default).** `arm` turns pivot autonomy on before the first launch (so the first worker's card carries the
typed-checkpoint instructions); `--no-pivot` keeps the old park-for-Owner behaviour.

Out of scope: lifting a tripped authority hold; raising any ceiling the Owner did not pre-authorize; certification rules.

## Acceptance (tools/test_mission_pivot.py, tools/test_mission_topup.py)
- V-PIV-CC-PIVOTS: opted-in, CHECKPOINT_COMPLETE with evidence only -> action pivot, directive names the evidence.
- V-PIV-CC-NO-RESIDUAL (neg): CHECKPOINT_COMPLETE, no residual, no evidence -> park.
- V-PIV-CC-OWNER (neg): CHECKPOINT_COMPLETE whose receipt carries CERTIFICATION_RULE -> owner.
- V-PIV-CC-OPTOUT (neg): pivot_autonomy off -> pivot_gate leaves it parked.
- V-TOPUP-APPLIES: room 1.3M < 3M, left 2 -> authority +4M, left 1, receipt with owner turn, ledger topup_applied.
- V-TOPUP-ROOM (neg): room 5M -> nothing. V-TOPUP-NONE-LEFT (neg): left 0 -> nothing.
- V-TOPUP-UNMEASURED (neg): spend unmeasurable -> nothing. V-TOPUP-OWNER-HOLD (neg): owner/cost hold -> nothing.
- V-TOPUP-ONCE: two passes with room still low after the first -> only when the new room is again < trigger.
- V-TOPUP-SET-NEEDS-TURN (neg): `--topups` without `--owner-turn` refused.
- V-TOPUP-REPLAY-NOOP (review HIGH): re-running the same Owner turn after a top-up was spent is a no-op with the
  same figures and refused with others; it never resets `left`.
- V-TOPUP-OFF: kill switch -> nothing. V-ARM-PIVOT-DEFAULT / V-ARM-NO-PIVOT.

## Rollback
`CPP_PIVOT_AUTONOMY=off` and `CPP_MISSION_TOPUP=off` in the sweep env, or revert the commit. State added: `topups` on the
record, ledger rows.
