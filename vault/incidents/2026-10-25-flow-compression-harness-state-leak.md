# Incident: replay harness state leaks between runs (2026-10-25, phase 7)

**Class:** HARNESS STATE LEAK -> A TEST OR REPLAY ANSWERS DIFFERENTLY BECAUSE OF WHAT A PREVIOUS RUN LEFT BEHIND.
Three leaks of one family in the S7 harness: raw temp paths stored in seeded inputs, a probe that assumed
a clean directory, and a pin helper that builds its pin over a copy with no mission records.

## Symptom

- Two replays of the seeded cases differed. The seeded FC-06 inputs held raw temp paths, which change on
  every run, so the replay was not deterministic (STATE.md line 78).
- The readonly probe's `mkdir` on an already existing directory crashed every re-run in one temp tree,
  which made its gates absent and falsely red in every drill (STATE.md line 80, item 2).
- Under test_s7_replay the replay sees 215 incidents and the CLI sees 266, a 51-incident gap. This phase
  re-measured the first number: the suite prints `REPLAY ... incidents=215` in
  /tmp/s9-evidence/test_s7_replay.out (STATE.md line 82 for the second).

## Timeline (local time)

| when | what | instrument |
|---|---|---|
| 2026-10-25 (07-02 build) | first seeded run: two replays not byte-identical | V-S7-DETERMINISTIC |
| 2026-10-25 | `_scrub` keeps basenames only in the seeded FC-06 inputs (95080159) | git log -S `_scrub` |
| 2026-10-25 | probe made re-runnable, drills trusted only after the fix (70f5a2dd) | the drill matrix reading baseline green |
| 2026-10-25 07:07:24 | cause of 215 versus 266 corrected: the pin helper builds its pin over a copy with no records (c1d17703) | 07-VERIFICATION W3 |
| 2026-10-25 this phase | S7 suite 164 of 164; two replays byte-identical | V-S7-DETERMINISTIC line in the evidence file |

## Root cause

Harness state outlived the run that created it. Paths, directories and a pin were taken from the ambient
environment of the previous call. A replay is only a measurement if its inputs are the same bytes on the
second call.

## Why the existing rule did not prevent it

The replay was specified as read-only and deterministic; the gate for determinism existed (and caught the
first leak). The probe and the pin helper had no equivalent: a leak that persists after its first
occurrence cannot be seen by a gate that only compares two calls.

## Earliest discoverable point

V-S7-DETERMINISTIC on the first seeded run for the paths; the first re-run in the same temp tree for the
probe; the first comparison of the suite count with the CLI count for the pin helper.

## Repair

95080159 (`_scrub`), 70f5a2dd (probe rerun). The pin-helper difference is benign scaffolding and is not
repaired: the committed report comes from the CLI, the test only needs a pin that verifies. Scope is
guarded by V-S7-SCOPE-RESTORED, V-S7-MUTANT-SCOPE-RESTORED and V-S7-NO-REDEFINE-AFTER-MUTANTS; read-only
by V-S7-READONLY-PROBE-FIRES.

## Test

- commit: 95080159
- commit: 70f5a2dd
- commit: c1d17703
- gate: V-S7-DETERMINISTIC in tools/test_s7_replay.py
- gate: V-S7-SCOPE-RESTORED in tools/test_s7_replay.py
- gate: V-S7-MUTANT-SCOPE-RESTORED in tools/test_s7_replay.py
- gate: V-S7-NO-REDEFINE-AFTER-MUTANTS in tools/test_s7_replay.py
- gate: V-S7-READONLY-PROBE-FIRES in tools/test_s7_replay.py

## Pattern

A harness run takes nothing from the previous run: inputs are scrubbed of ambient paths, directories are
created idempotently, and every patched name is shown restored.

## Open debt

- Not repaired, benign: `gate_pin` builds its own pin over a copy with no mission records, so the test
  sees 215 incidents and the CLI sees 266. No verdict is affected; the committed report is from the CLI.
- V-S7-HELD-RESTORED cannot see a leak made by an earlier call (a leak persists after its first
  occurrence); V-S7-SCOPE-RESTORED is the gate that goes red under M-HELD-LEAKS. Stated, not repaired.
