# Incident: gate fixtures written from memory of the reader (2026-10-24 to 2026-10-25)

**Class:** FIXTURE FROM MEMORY OF THE READER -> A GATE THAT CANNOT SEE THE DEFECT IT NAMES.
Four times in phases 5 to 7 a test input was written from what the author believed the reader
accepts, not from the reader. Each produced a red or a vacuous gate on the first run, and each was
found only because the run was read.

## Symptom

- S5, first hand-off: 37 of 42 gates green, 5 red (commit 4b21336a). The divergence fixture wrote the
  sidecar key `measured`, the reader (`receipt_judge`) reads `values`, so a DIVERGENT receipt looked DONE
  in two gates. The test also set `CPP_HALT_CONTINUE=off`, which switches off the missing-receipt halt
  as well, so two gates could not see the halt they were written for (STATE.md line 41).
- S6, first run of V-S6-HOLD-PARKS-TYPED: the gate read the ledger event `recovery_owner_boundary`; the
  typed row is the transition event `recovery_boundary`; the separate `recovery_owner_boundary` row carries
  no blocker fields (STATE.md line 52).
- S7: the spend-within-authority seed set `token_estimate` 100000, which tripped the estimate cap, so the
  control read as a hold instead of a spend inside authority (STATE.md line 79).

## Timeline (local time, CEST)

| when | what | instrument |
|---|---|---|
| 2026-10-24 (S5 build) | S5 suite 37/42, 5 red (4b21336a) | the suite's own summary line in the commit subject |
| 2026-10-24 | fixtures changed: sidecar key `values`, halt switch left on with the relaunch stubbed, breaker rows allowed in the no-spend gate (37333b56, 42/42) | git diff of tools/test_s5_reconcile.py: `measured` -> `values`, `CPP_HALT_CONTINUE=off` line removed |
| 2026-10-24 (S6 build) | first V-S6-HOLD-PARKS-TYPED run red; read `recovery_boundary` instead (b6a30be4) | git log -S on the event name |
| 2026-10-25 (S7 build) | seed estimate 100000 trips the cap; raised to 600000 and checked against the real judge (95080159) | tools/flow_replay.py seed table, line with `token_estimate` 600000 |
| 2026-10-25 | this phase reran all three suites: S5 44/44, S6 72/72, S7 164/164 | /tmp/s9-evidence/*.out summary lines |

## Root cause

Each fixture encoded the author's memory of a contract: the sidecar key name, which switch gates which
halt, which ledger event carries the typed row, how large an estimate stays under a cap. The reader was
not consulted when the fixture was written. A negative control built this way is wrong in a way the suite
cannot show: it passes or fails for a reason unrelated to the behaviour it names.

## Why the existing rule did not prevent it

Gates were written with positive and negative cases, which is the rule. The rule did not say the
negative case has to be observed firing against the real reader before the gate counts. A fixture that
never reaches the reader gives a green that looks identical to a guard that works.

## Earliest discoverable point

The first red or suspicious run of each suite. For S5 that is the first full run (5 red). For S6 and S7
it is the first read of the gate's own output: the observed value in the detail string disagreed with
the expected one. A fixture whose control never fires proves nothing.

## Repair

S5: 37333b56 (sidecar key and switch fixture). S6: b6a30be4 (event name). S7: 95080159 (seed value, checked
against the real judge). Prevention: every negative control is run against the real reader and its firing
is read before any gate that depends on it is trusted.

## Test

- commit: 37333b56
- commit: b6a30be4
- commit: 95080159
- gate: V-S5-TRACER-MISSING-HALTS in tools/test_s5_reconcile.py
- gate: V-S5-NO-FALSE-DONE-MATRIX in tools/test_s5_reconcile.py
- gate: V-S6-HOLD-PARKS-TYPED in tools/test_s6_blockers.py
- gate: V-S7-NEGCONTROL-SEEDED-FC06 in tools/test_s7_replay.py

## Pattern

A fixture is built from the reader's code, and its negative control is shown to fire against that reader
before the gate it supports is trusted.

## Open debt

- No static check forbids a fixture literal that the reader does not parse; the guard is the habit of
  reading the first run. Not repaired in this mission.
