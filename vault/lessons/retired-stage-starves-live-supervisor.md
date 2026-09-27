# A retired stage that still runs can starve the live stage behind it

**Date:** 2026-09-27 · **Fix:** `9f750fa` · **Gate:** `tools/test_sweep_ralph_markers.py` (V-SWEEP-RALPH-*)
**Epistemic status:** mechanism CONFIRMED (code read + marker census + live recovery after the fix);
the exact second at which the pile-up began is INFERRED from the log gap (last line 19:58).

## Symptom
Seven `gsd_long_run.py sweep` processes piled up from 20:01; the sweep log was silent after 19:58;
mission `m-8ab6628b7acd` stayed RUNNING for 46 h against a 24 h budget and never relayed. The
scheduled task reported "Running" the whole time, so nothing looked broken.

## Root cause
The sweep has two stages in series: the retired v2 compact-and-resume marker stage, then the
live Ralph mission supervisor. The v2 stage walked every `gsd-autorun-*.json` marker and asked
`gsd-tools query init.manager` about each. Ralph workers write markers of the SAME name
(`mode: ralph`), and no one deleted them when their mission ended: 403 markers, 399 of terminal
missions. At ~500 MB free one query took > 45 s, so one pass outlived the 5-minute schedule.

## Why the defences failed
- **"Retired" meant "cannot arm", not "does not run".** The v2 path refuses to arm a live run, but
  its sweep stage kept executing on every pass, over files the live path produces.
- **A shared filename, two owners.** The marker format was reused by Ralph so the watchdog would
  read the wall; nothing gave the v2 stage a way to tell the files apart, so it treated them as its own.
- **Leak with no reaper.** Mission termination stopped workers but left their markers; the v2
  reaper only fires after 48 h idle, and an ended worker's transcript is recent.
- **The task time limit ends wscript, not the python grandchild** (known family:
  `feedback_timeout_without_reaping_is_the_leak_engine`), so `MultipleInstances IgnoreNew`
  did not prevent overlap. Each overlapping pass added load and slowed every query further.
- **Healthy-looking death.** The live stage never ran, so no mission produced an error; the
  budget it enforces simply stopped existing.

## Fix
A Ralph marker is never asked about by the v2 stage. It is retired when its mission record states
a terminal state; kept, with its owner named in `--explain`, otherwise; an absent or unreadable
record is UNKNOWN and keeps it. Proven: red 4/10 before (5 gsd calls for 5 markers), 10/10 after,
mutation "absent record read as HALTED" caught. Live: markers 403 -> 4 in one pass; supervise
resumed (23:05, 23:09, 23:17); `m-8ab6628b7acd` HALTED on budget and its worker reaped.

## Still open
Single-instance lease + tree reap on timeout so a slow pass can never overlap the next
(mission-continuity T7, owned by the `claude-power-pack-e9` pane).

## Transferable lesson
When a path is retired, retire its **execution**, not only its **entry point** -- and check every
file format it shares with its successor. A retired stage that still runs, in series in front of a
live one, is a liveness defect in the live one.
