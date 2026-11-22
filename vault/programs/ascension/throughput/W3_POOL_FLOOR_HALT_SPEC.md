---
covers: [W3, pool-adequacy, POOL_FLOOR, count-first, INSTRUMENT_FAIL class A]
tier: T2
owner_ruling: "AskUserQuestion 2026-11-22 15:3xZ, pane a52cc240: (b) Count-first P1 (Recommended)"
---
# W3: halt below the declared floor at the freeze (spec)

## Problem (measured)
- O6 census: 21 to 23 INSTRUMENT_FAIL generations of class A (a pool below its own declared floor), 97.2M measured
  spend in 11 days. W3 step 0: 4 of 5 sampled checkpoints confirm class A.
- In all 4 true A cases the generation wrote its own counting tool, so no command exists for the autopilot to run
  before arming.
- 153 of 314 historical packets declare a floor. In 149 of them, Phase 1 already freezes the pool (P1 cap p50 1.5M,
  p80 2.5M), and 112 name the floor in Phase 1 itself.
- So the count-first slice already exists. What is missing is the halt: the worker counts below the floor and keeps
  spending (S134K reached Phase 3 before failing; S31T spent 8.4M).

## Change (PRD)
1. Worker command (`autopilot.command_text`): the phase that freezes a population with a declared floor writes the
   machine line `POOL_FLOOR: <name> count <N> floor <F>` into its evidence. When N < F it stops the generation there,
   with no further phase. It commits an INSTRUMENT_FAIL (population) checkpoint carrying `CHECKPOINT_FINAL: true` and
   runs `gsd_mission.py checkpoint`.
2. Planner prompt (`planner_prompt.md`): a plan whose instrument declares a population/pool/cohort floor freezes and
   counts that population in the earliest phase it can, and that phase line says "stop below floor".
3. Measurement (`autopilot.pool_floor_halt`): when a checkpoint is judged, a `POOL_FLOOR` line with N < F books
   ledger `pool_floor_halt` {lane, gen, name, count, floor, tokens 0}. There is no behaviour change, and the judge runs
   as before.

Not changed, by design:
- No skipped judge. Skipping it would save about 0.4M but bypass the judge's protected-identity and gate checks.
- No autopilot kill of a running worker. That is a new effect class.
- No certification predicate. A halted generation would have produced INSTRUMENT_FAIL anyway.

## Architecture
- `POOL_FLOOR_RE` and `pool_floor_line(checkpoint, product) -> dict | None` sit next to `declared_not_final`, with
  the same path resolution and an OSError meaning None.
- In `judge()`, before the model call, a below-floor line books the ledger row once per checkpoint. The key is
  (lane, checkpoint), held in `ls["pool_floor_for"]`.
- The text changes are in `command_text` and the live `planner_prompt.md`, which is mirrored at
  `vault/programs/ascension/autopilot/planner_prompt.md`.

## Acceptance
- AC1: `command_text` contains `POOL_FLOOR:` and "stop", and the policy still admits the neutral plan, since
  `policy_check` does not judge command_text.
- AC2: the parser reads `POOL_FLOOR: ctl count 4 floor 24` as below, and `count 30 floor 24` as not below. A missing
  line or a missing file gives None. Prose such as "the pool floor is 24" gives None.
- AC3: a judged checkpoint with a below-floor line books exactly one `pool_floor_halt`, also when the same checkpoint
  is judged twice. With no line, nothing is booked. A planted mutant (the row never booked) turns the gate red.
- AC4: GEX44 gate `test_autopilot.py` PASS with every mutant killed. Control: the live autopilot with the new test is
  red on exactly the new checks.
- AC5 (effect, measured after deploy): `pool_floor_halt` rows appear, and the class-A INSTRUMENT_FAIL spend per
  generation falls from its baseline (97.2M / 21 = about 4.6M) toward the P1 cap (about 1.5M). Read after 3 days.

## Rollback
Restore `autopilot.py.bak-a52c-w3-*` and `planner_prompt.md.bak-a52c-w3-*` under cron.lock. Ledger rows are
additive (kind `pool_floor_halt`), and nothing reads them.
