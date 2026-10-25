# Incident: controls and gates never shown to fire (2026-10-24 to 2026-10-25)

**Class:** CONTROL NEVER SHOWN TO FIRE -> GREEN THAT IS INDISTINGUISHABLE FROM A WORKING GUARD.
A gate, or a control inside a gate, was green because it could not go red. Found three times, once in
each of S5, S6 and S7, and each time the cure was a mutation drill plus a control that proves the drill
itself can fail.

## Symptom

- S5: the resolver audit counted disagreements only when the resolver found a receipt through the stem
  convention, so it could not count a declared receipt found elsewhere. The audit was vacuous (read from
  the diff of 755a757a: the old predicate required the resolver source to be the stem path while also
  requiring the path to differ from the stem path; that is inferred from the diff, not replayed).
- S6: every gate passed on its first run. That says nothing about their ability to fail (STATE.md line 53).
- S7: controls that did not fire on the first run (STATE.md line 80):
  - the first calibration matrix counted absent gates as red, because the calibrate edit had not applied;
  - the readonly group crashed on every re-run in one temp tree (`mkdir` on an existing probe directory),
    which made its gates absent and falsely red in every drill;
  - M-CENSUS-DIFF-ZERO was an equivalent mutant (the pin count made 0 equal the expected difference);
  - M-PROBE-BLIND crashed on a missing attribute of the blinded probe;
  - M-PIN-READS-SHORT and M-REPORT-EMPTY-COMMAND only made whole groups crash, so no gate went red by
    its own check.

## Timeline (local time, CEST)

| when | what | instrument |
|---|---|---|
| 2026-10-24 20:59:46 | S5 resolver audit fixed: positive case plus control plus mutant, 44/44 (755a757a) | git log date, diff of tools/mission_reconcile.py |
| 2026-10-24 (S6 build) | 34 mutation drills and the no-op control added (f1ef65fb) | commit body: `S6_PASS=72/72` |
| 2026-10-25 (S7 build) | 78 drills, no-op control, real-file-untouched, MUTANT_FOR map (70f5a2dd) | commit subject |
| 2026-10-25 this phase | suites rerun: S5 11 mutant gates, S6 34 drill gates, S7 78 drill gates, all PASS | counts of `PASS V-S5-MUTANT-`, `PASS V-S6-DRILL-M-`, `PASS V-S7-DRILL-M-` lines in /tmp/s9-evidence |

## Root cause

A control proves only what it is shown to do. Each of these was written, observed green and trusted. The
S5 audit's predicate could never be true on the input it was meant to judge. The S7 drills asked "is the
mapped gate red under the mutant", which is also true when the gate is absent, crashed or was never
applied; a mutant equivalent to the original makes the answer "not red" for the wrong reason.

## Why the existing rule did not prevent it

Each slice required "every gate has a control that fires". The wording was satisfied by writing a control.
Nothing demanded the observation that it fires, nor a control for the control (a no-op mutant that must
leave every mapped gate green, which proves a drill would read a real failure as one).

## Earliest discoverable point

The first run of each gate set, read line by line: a suite that is all green on its first run, or a
matrix that counts absent gates, is the signal. For S5 it is the first time the audit was asked to count
a case it should have counted.

## Repair

- S5: 755a757a, positive control, stem-present control and mutant M-AUDIT-NEVER-COUNTS.
- S6: f1ef65fb, 34 mutation drills, each mapped gate green on baseline and red under its mutant, plus
  V-S6-DRILL-CONTROL-NOOP-FIRES (all 34 drills fail when the mutants are replaced by no-ops) and
  V-S6-MUTANT-MAP.
- S7: 70f5a2dd, 78 drills, V-S7-DRILL-CONTROL-NOOP-FIRES (a no-op substitution leaves 81 of 81 mapped gates
  green, so every drill would read it as a failure), V-S7-DRILL-REAL-FILE-UNTOUCHED (flow_replay.py hash
  identical across 78 mutated copies) and V-S7-MUTANT-MAP (every gate mapped or listed UNMUTATED with a
  reason; this phase measured two: V-S7-HELD-RESTORED and V-S7-READONLY-COPY-IDENTICAL).

## Test

- commit: 755a757a
- commit: f1ef65fb
- commit: 70f5a2dd
- gate: V-S5-RESOLVER-AUDIT-COUNTS-DECLARED-ONLY in tools/test_s5_reconcile.py
- gate: V-S5-RECEIPT-INVENTORY-CONTROL in tools/test_s5_reconcile.py
- gate: V-S6-DRILL-CONTROL-NOOP-FIRES in tools/test_s6_blockers.py
- gate: V-S6-MUTANT-MAP in tools/test_s6_blockers.py
- gate: V-S7-DRILL-CONTROL-NOOP-FIRES in tools/test_s7_replay.py
- gate: V-S7-DRILL-REAL-FILE-UNTOUCHED in tools/test_s7_replay.py
- gate: V-S7-MUTANT-MAP in tools/test_s7_replay.py

## Pattern

A gate that is green on its first run needs a mutation drill, and the drill needs a no-op control that
proves it can read a failure; "absent" and "crashed" are never counted as "red".

## Open debt

- Two S7 gates stay UNMUTATED by design and with a stated reason (V-S7-HELD-RESTORED,
  V-S7-READONLY-COPY-IDENTICAL); their in-gate controls carry the proof. Not repaired.
- Phases 1 to 4 suites were not audited for this class in this phase; whether each carries a
  no-op drill control is UNMEASURED here.
