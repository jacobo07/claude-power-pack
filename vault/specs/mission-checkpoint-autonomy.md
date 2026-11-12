---
status: SPECIFIED 2026-11-12 (Owner, session 423c9c50: "recarga y si no sale cambia de estrategia, eso deberia pasar de forma 100% autonoma"; "hazlo ambas cosas" = code + GEX44 deploy)
tier: T2
covers: [checkpoint-complete-pivot, arm-pivot-default, gex44-topup-stage, mission-checkpoint-autonomy]
owner: tools/gsd_mission.py (pivot_decision, arm), tools/gsd_sweep_pass.py (STAGES)
---

# A wave that closes with the Goal open continues on its own, and a pre-authorised top-up is granted on GEX44 too

## Incident (measured 2026-11-12, GEX44, S30T m-2e14179c5b6a)
The worker declared `CHECKPOINT_COMPLETE` (P1 REFUTED, 0 certificates) at ~01:16Z with `owner_required: false`. The mission
then sat for 10.8 h (`waited_s=38947`) until the Owner asked. Three causes:
1. S30T was armed without `pivot-autonomy --on` (off by default).
2. `pivot_decision` only pivots `METHOD_PIVOT_REQUIRED` / `NEXT_PLAN_REQUIRED`; `CHECKPOINT_COMPLETE` always parks, although
   the worker card itself defines it as "the wave's obligations are closed and the Goal is not".
3. The arm granted "20M + 2x4M top-ups" as text. A typed, progress-gated auto top-up already exists
   (`tools/mission_topup.py`, spec `mission-auto-topup`, 2026-10-23), but S30T had no policy recorded, and the GEX44 sweep
   (`gsd_sweep_pass.py --stages mission`) has no `topup` stage at all: only the laptop's `gsd_long_run_sweep.ps1` runs it.

Correction recorded: the first cut of this spec added a second top-up mechanism inside gsd_mission.py and overwrote
`tools/test_mission_topup.py` (the existing module's gates). Both were reverted in the same session; C2 below replaces it.

## Change
**C1 (checkpoint-complete-pivot).** On an opted-in mission, `CHECKPOINT_COMPLETE` is a pivot state like
`NEXT_PLAN_REQUIRED`. The residual falls back to the checkpoint's `--evidence` when `--residual` is absent. Every existing
guard stays and runs first: the authority net (typed receipt objects + `mission_policy.gate_question` over the reason),
the streak cap, Gen2 early stop / hard cap, the kill switch `CPP_PIVOT_AUTONOMY=off`. No residual and no evidence = park.

**C2 (gex44-topup-stage).** `gsd_sweep_pass.py` gains the `topup` stage (`mission_topup.py sweep`, 120 s deadline,
`CPP_SWEEP_TOPUP_TIMEOUT_S`), parity with the .ps1 order mission -> topup -> v2, and the default `--stages` becomes
`mission,topup,v2`. The GEX44 unit `agora-mission-sweep` is changed to `--stages mission,topup`. The top-up rules are the
existing module's, unchanged (authority trip only, progress since the last grant, max N, kill switch
`CPP_MISSION_AUTO_TOPUP=off`). S30T's remaining 4M is recorded as a policy with `mission_topup.py budget`.

**C3 (arm-pivot-default).** `arm` turns pivot autonomy on before the first launch (so the first worker's card carries the
typed-checkpoint instructions); `--no-pivot` keeps the old park-for-Owner behaviour.

Out of scope: lifting a tripped authority hold outside mission_topup; raising any ceiling the Owner did not pre-authorise.

## Acceptance
- tools/test_mission_pivot.py: V-PIV-CC-PIVOTS, V-PIV-CC-NO-RESIDUAL (neg), V-PIV-CC-OWNER (neg), V-PIV-CC-OPTOUT (neg),
  V-ARM-PIVOT-DEFAULT, V-ARM-NO-PIVOT; drills D16-D18 red their gates.
- tools/test_gsd_sweep_pass_py.py: V-SWEEPPY-MISSION-FIRST-AND-OK (order mission, topup, v2), V-SWEEPPY-TOPUP-STAGE-RUNS.
- tools/test_mission_topup.py unchanged and green.
- Field (GEX44): after the unit change, one sweep heartbeat lists a `topup` stage with rc 0.

## Rollback
`CPP_PIVOT_AUTONOMY=off` / `CPP_MISSION_AUTO_TOPUP=off` in the sweep env, `--stages mission` back in the unit, or revert.
