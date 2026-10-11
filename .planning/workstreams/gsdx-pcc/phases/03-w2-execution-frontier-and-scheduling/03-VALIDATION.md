# Phase 3 Validation Strategy

Phase goal: `decide()` is the first action of a compiled execution frontier; WAIT only when the frontier is empty; the sweep dispatches N independent gate epochs under a declared bound; legacy behaviour is byte-equal when the switch is off or posture is default.

## Requirement -> plan -> gate

| Req | Plan | Gates |
|---|---|---|
| D04 | 03-01, 03-03 | V-FRONTIER-FRONTIERS, V-FRONTIER-GLOBAL-WAIT, V-FRONTIER-WAIT-ONLY-EMPTY |
| D05 | 03-01 | V-FRONTIER-GRAPH |
| D06 | 03-03, 03-04 | V-FRONTIER-LEGACY-EQUAL, V-FRONTIER-SWEEP-N, V-FRONTIER-BEGIN-REFUSES |
| D07 | 03-01, 03-04 | V-FRONTIER-UNIT-DERIVE, V-FRONTIER-UNDECLARED, V-FRONTIER-INDEP, V-FRONTIER-RESOURCE, V-FRONTIER-UNSAFE-WRITES |
| D08 | 03-02 | V-FRONTIER-PRIOR, V-FRONTIER-CRITICAL-PATH |
| D09 | 03-02, 03-04 | V-FRONTIER-POSTURE, V-FRONTIER-SWEEP-BOUND |
| D25 | 03-05 | V-FRONTIER-SPEC-ADMIT, V-FRONTIER-SPEC-REFUSE, V-FRONTIER-REPORTED-NOT-EXECUTED |
| D26 | 03-05 | V-FRONTIER-RACE-ADMIT, V-FRONTIER-YIELD (execution deferred to Phase 4) |
| D27 | 03-02 | V-FRONTIER-CLASSES |
| D28 | 03-02 | V-FRONTIER-ORDER, V-FRONTIER-CRITICAL-PATH |
| D33 | 03-02 | V-FRONTIER-INFOGAIN |
| D34 | 03-02 | V-FRONTIER-FAILURE-FIRST |

## RED list (each driven red, then green, then mutation-killed)
1. global WAIT with independent work -> V-FRONTIER-GLOBAL-WAIT, drill m1/m8
2. unsafe parallel writes -> V-FRONTIER-UNSAFE-WRITES, drill m2/m3
3. resource collision admitted as independent -> V-FRONTIER-RESOURCE, drill m4

## Instrument honesty (could the gate have said otherwise?)
Every refusal gate has a paired admit control. Legacy-equality gate prints the count of contexts compared and fails on zero. Sweep gates run the real `sweep_goal` against a real temp git repo and real subprocess gates, awaiting every dispatched run (harvest) before assertions. Mutation drills run in an isolated copy with a control run.

## Suites that must not regress
`GSDX_PCC_REPLAY_PASS=28/28`, `GSDX_PCC_SEMANTICS_PASS=48/48`, all existing `tools/test_gsd_x_goal_*.py` at Phase 2 baseline counts, liveness exit 0.

## Budget note
Part B plans run inline in PowerShell; one commit per plan by pathspec; a SUMMARY per plan.
