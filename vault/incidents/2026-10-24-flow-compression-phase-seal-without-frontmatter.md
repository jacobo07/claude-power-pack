# Incident: phase seal without GSD frontmatter (2026-10-24 18:31 to 20:20 CEST)

**Class:** PHASE SEAL WITHOUT GSD FRONTMATTER -> COMPLETION INVISIBLE TO THE SCHEDULER.
Phases 1-4 of the flow-compression mission were sealed and closed twice by hand while GSD still
listed the workstream as 0/8 complete. The code and every suite were healthy; the only thing
missing was the field GSD reads to decide a phase is done.

## Symptom

- The unit was sealed and closed twice, and GSD still listed it: 0/8 phases complete, phase 1 re-queued
  as the next command to run.
- The mission parked at an AMR Owner boundary for about 1.5 h (carried from STATE.md lines 30-37; the
  duration was written by the session that observed it, not re-measured here).
- After the repair GSD reported 4/8 (commit message of 89fa5527); this phase measured 7/8 with the
  command in the Timeline.

## Timeline (local time, CEST)

| when | what | instrument |
|---|---|---|
| 2026-10-24 18:31:45 | phase 1 closed by hand (6943ee56) | git commit date |
| 2026-10-24 18:34 to 18:40 | S2, S3 and S4 sealed by hand (da0580e8, dc7428d3, 54dd9e21); no VERIFICATION frontmatter written | git commit dates |
| 2026-10-24 18:40 to 20:20 | GSD reports 0/8 complete and re-queues phase 1; mission parks at the AMR Owner boundary (about 1.5 h, carried) | STATE.md lines 30-37 |
| 2026-10-24 20:20:15 | frontmatter (phase, verified, status, score) added to the eight phase 1-4 VERIFICATION and SUMMARY files (89fa5527) | git diff --stat: 8 files, 56 insertions |
| 2026-10-24 20:20:38 | incident recorded in STATE.md (b9ff692d) | git commit date |
| 2026-10-24 later | `gsd_long_run.gsd_status` found not to be a CLI subcommand; status read with `init.progress` instead | STATE.md line 43 |
| 2026-10-25 11:23:04Z | `node ~/.claude/gsd-core/bin/gsd-tools.cjs query init.progress --ws flow-compression --raw` at this phase: **completed_count 7**, phases 01-07 phase_complete true, phase 08 false | the command itself, output captured in /tmp/s9-initprogress.json |

## Root cause

The phase artifacts (VERIFICATION and SUMMARY) were written by hand as prose without the GSD
frontmatter keys. GSD completion is `verification.status === passed`, read from that frontmatter, so a
phase whose VERIFICATION has no frontmatter is incomplete as far as GSD is concerned, however green
its suite is. The seal step and the scheduler had no shared definition of "closed".

## Why the existing rule did not prevent it

The seal step already required a passing suite and a written VERIFICATION. Both were true. Nothing
in the seal step asked the scheduler. The check that matters is not "I wrote the artifact" but "the
reader of the artifact now reports one more phase complete".

## Earliest discoverable point

The phase-close step: right after sealing each phase, ask GSD for the status and compare it with the
count before the seal. At 18:31:45 on 2026-10-24 that comparison would have shown 0 -> 0 and stopped
the close, instead of surfacing about 1.5 h later as a parked mission.

## Repair

Frontmatter added to the eight phase 1-4 files (89fa5527), the incident recorded (b9ff692d). Phases
5 to 8 artifacts are produced by the GSD planner and verifier workflows, not by hand.
Prevention instrument (D-12): after every phase seal, run
`node ~/.claude/gsd-core/bin/gsd-tools.cjs query init.progress --ws flow-compression --raw` and
require `completed_count` to have advanced. If it did not, the seal is not closed.
`gsd_long_run.gsd_status` is a Python function, not a CLI subcommand, so it cannot be the shell
instrument; `init.progress` is.

## Test

gate and commit lines below are parsed by `tools/s9_kv_check.py`; the check line runs the instrument.

- commit: 89fa5527
- commit: b9ff692d
- check: init-progress

## Pattern

A seal is closed only when the scheduler that decides what runs next agrees it is closed: assert the
reader's count advanced, never that the writer's artifact exists.

## Open debt

- The duration of the parked interval (about 1.5 h) is carried from STATE.md, not re-measured; the
  AMR boundary log of that interval was not re-read in this phase.
- Phase 8 closure is asserted by plan 08-03 (`init.progress` completed_count 8); until then this
  incident's prevention has been executed for 7 of 8 phases only.
