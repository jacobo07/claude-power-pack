---
status: APPROVED 2026-11-06 (coordinator obligation from the S16 arm, session 177efe77 handoff item 2; extends
  vault/specs/gsd-x-universal-mission.md, Owner 2026-11-03 "si no tiene el milestone, debe crearse autónomamente")
covers: [arm-no-launch-milestone, milestone-from, arm-preflight-no-launch]
owner: tools/gsd_mission.py arm
---

# `arm --no-launch` runs the GSD milestone check

## Problem (measured 2026-11-06, GEX44)
S16 (m-29dd612ed825) was armed `--no-launch` so that the sweep would launch it. The GEX44 ledger has NO
`arm-preflight` row for it: `arm()` ran the milestone scaffold and the preflight only when `launch=True`. The cwd's
S15 milestone had been archived, so the first worker would have started with no GSD milestone. The coordinator ran
`gsd_milestone_scaffold.py ensure --command <prose>` by hand. With no packet, `phases_from_packet` fell back to ONE
phase named after the command. The right input was the phases file (`S16-PHASES.md`, 8 phases), and `arm` had no way
to pass it. (The handoff guessed "unmeasured GSD state passes arm". That was not the cause: a STATE.md without
ROADMAP.md already reads NO_PHASES via `absent_roadmap`, measured on GEX44 the same day.)

## Decision
- `arm()` runs `ensure_gsd_milestone` + `arm_preflight` on EVERY arm. Memory admission stays launch-only, as before.
- `arm --milestone-from <file>` is the phase source for the scaffold. It is never stored as `wu_packet` (a packet
  replaces the launch prompt; this file only names phases).
- At `--no-launch`, a NO_PHASES/ALL_COMPLETE that survives the scaffold is a ledgered **warn**, not a refusal.
  Workers arm sub-missions `--no-launch` (`worker_arm_launch_refused`), and 4 suites arm `--no-launch` in
  milestone-less fixtures. Refusing there is a wider change than this gap needs. A launching arm still refuses,
  as before.
- `arm_chain` already runs the scaffold and preflight itself; it calls `arm(preflighted=True)` so they run once.

## Acceptance (tools/test_arm_no_launch_milestone.py, V-ANL-*)
- `--no-launch` with `--milestone-from`: ROADMAP.md is scaffolded with the file's 3 phases; an `arm_preflight` row is
  ledgered; the record has no `wu_packet`.
- Scaffold off, no milestone: `--no-launch` arms with a `gsd_status` warn; `launch=True` refuses on NO_PHASES.
- `preflighted=True` runs neither the scaffold nor the preflight.
- CLI `--milestone-from` reaches the scaffold.
- Drills (4): skipping at no-launch, dropping the phases file, refusing at no-launch, ignoring `preflighted` each turn
  their gate red.
- Fixture isolation: `test_gsd_mission_capsule_v2` armed `--no-launch` in its shared REPO, and the scaffold now
  rewrote REPO/.planning, which the later L1 backoff sections fingerprint (bisected: the `arm()` hunk alone moved it
  78/79 -> 76/79). That one call now sets `CPP_GSD_X_AUTOSCAFFOLD=off`; back to 78/79 (the remaining red is
  pre-existing).

## Review 2026-11-06 (pp-code-reviewer: APPROVE, one MEDIUM, one LOW)
- MEDIUM, fixed: a mission worker (`worker_arm_refusal` names it) arming a sub-mission `--no-launch` in a repo whose
  milestone reached ALL_COMPLETE would have its own `.planning` archived and replaced mid-run. The scaffold is skipped
  for a worker caller; the GSD check still runs and warns. Gate `V-ANL-WORKER-PLANNING-UNTOUCHED`, with a drill.
  Consequence: the worker's LAUNCH refusal (A4-P5) now runs first in `arm()`, before scaffold and preflight. With the
  scaffold skipped, NO_PHASES had pre-empted it and `V-ARM-WORKER-RED` lost the mission id in its message. Now a
  refused worker launch also writes nothing to `.planning`.
- LOW, accepted: the scaffold runs before goal/supersedes/governor refusals, so a refused arm can leave a scaffolded
  milestone. That already held for launching arms; the prior files are archived, never deleted.

## Kill switches
`CPP_GSD_X_AUTOSCAFFOLD=off` (no scaffold), `CPP_ARM_PREFLIGHT=off` (no preflight), `CPP_GSD_X_OPTOUT=<reason>`.

## Rollback
Restore `if launch:` around the scaffold + preflight in `arm()`, drop `milestone_from`/`preflighted`/`gsd_refuse` and
the CLI flag, delete the test file and the capsule_v2 isolation block.
