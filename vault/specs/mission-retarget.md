---
status: APPROVED 2026-11-03 (Owner "y" to the S11 K unit (d), session 95e69b3d)
covers: [mission-retarget, retarget-cli, launch-prompt-change]
owner: tools/gsd_mission.py retarget_mission
---

# `retarget`: change a parked mission's launch prompt without re-arming

## Problem (measured 2026-11-03, Solver Ascension S11H)
A mission's launch prompt (`resume_command`) is fixed at `arm`. A new generation of the same programme needed a new
prompt, and the only route was to arm a second mission (m-fc7047a29f01 after m-f0b595fd509f). That loses the record's
directives, decisions, workset, pivot history and authority lineage, or makes the coordinator rebuild them by hand
(incident S11-13 in `vault/programs/ascension/S11-INCIDENTS.md`).

Part of the same gap was the cycle-cap halt (S11-12). It was NOT a missing renewal path: the sweep refused renewal
because GSD answered NO_PHASES (`gsd-long-run-sweep.log`, 2026-11-03T11:48:40Z). That half is owned by
`vault/specs/gsd-x-universal-mission.md` (arm scaffolds a milestone), and this spec does not touch it.

## Decision
`gsd_mission.py retarget --mission <id> --command-file <path> --reason <text> [--expect-cwd <dir>]`
replaces `resume_command` through `transition()`. The compare-and-swap covers epoch, state AND `seq`: a hold released
or a checkpoint cleared between the read and the write moves only `seq`. The ledger event is `mission_retargeted`,
with the sha256 of the old and new commands, never the text.

It is allowed only while no worker can be following the old prompt:
- state PREPARED (nothing launched yet), or
- an `owner_hold` is set AND the owner is positively gone: there is no owner, the hold recorded its own stop
  (`worker_stopped_at`), or `liveness()` on the real host rows says DEAD. A hold alone is not enough. A checkpoint
  lets a busy worker finish its turn, and a plain hold does not stop the worker. An unanswered host is UNKNOWN, and
  UNKNOWN refuses.

It refuses, naming why:
- a TERMINAL mission (renewal carries the command forward; retarget the successor);
- LAUNCHING / RUNNING / HANDOFF / BLOCKED with no hold (a live worker is executing the old prompt; hold first);
- held with an owner that is not proven gone (pause it first: `hold --stop`, or wait for the turn to end);
- a mission with a `wu_packet` (the packet's launch prompt is sent instead of `resume_command`, so the change would
  have no effect);
- a change of route class: `/gsd-` to prose, or prose to `/gsd-`. Arm admission judged the old class, so that change
  is a re-arm;
- a `/gsd-` command whose `--ws`/`--workstream` differs from the record's workstream. `create` derives the workstream
  from that flag, and the goal key and GSD status follow it, so the change is a different Goal: re-arm;
- an empty command, or a reason that is empty.

The record keeps `retargets: [{at, from_sha256, to_sha256, reason}]`. `bind_workstream` is re-applied to the new
command.

## Acceptance (tools/test_mission_retarget.py, V-RETARGET-*; review pp-code-reviewer 2026-11-03 WARNING, all four findings fixed)
- PREPARED: retarget applies; the record and the next launch prompt (`launch_prompt`) carry the new text.
- Unheld RUNNING: refuses. Held with the host listing the owner running: refuses. Host unavailable: refuses. Held with
  the host listing it `done`: applies. Held with `worker_stopped_at`: applies.
- TERMINAL, wu_packet, route-class change, workstream change, empty command, empty reason: each refuses, and the
  record is unchanged.
- A hold released between the read and the write raises CasConflict, and the command stays the old one.
- The retarget's ledger row carries both hashes and not the command text.
- Mutation drills (6): removing the hold, liveness, workstream or route-class check, dropping `expect_seq`, or putting
  the text in the row each turns its gate red.

## Never
- Never retarget a live worker's mission, held or not.
- The retarget's own ledger row never carries the command text. The next launch's `armed` row records the command as
  every launch does (`_arm_worker_marker`); that is outside this verb.

## Rollback
Remove `retarget_mission`, the `retarget` sub-parser and its dispatch, and the test file. No other code reads
`retargets`.
