---
phase: 3
workstream: gsdx-pcc
status: passed
verified: 2026-10-12
head_at_verification: edc5f0c8
---

# Phase 3 Verification -- W2 Execution frontier and scheduling

Every check below was run by the worker. Plane is stated per line: **Windows plane** = the laptop, **Linux plane** = GEX44 (reported by the coordinator, log `03-06-drill-gex44.log`).

## Gates

| Gate | Result | Plane | Source |
|---|---|---|---|
| `GSDX_FRONTIER_PASS=40/40  threshold=40/40` (HEAD 298ba2c6, 9 runs: 3 sequential, 6 parallel, all rc=0) | PASS | Linux | 03-06-drill-gex44.log |
| `GSDX_FRONTIER_PASS=39/39  threshold=39/39` (8e2f6ce8, before the fixture fix) | PASS | Windows | 03-05-green.log |
| Frontier suite at 298ba2c6 on the laptop | NOT RUN to completion (two runs killed by the harness for low memory, not restarted) | Windows | stated, not hidden |
| `GSDX_PCC_SEMANTICS_PASS=48/48  threshold=48/48` (incl. V-PCC-ADDITIVE-ONLY, Phase 2 git range, no hash re-pinned) | PASS | Windows | 03-06-semantics.log, HEAD edc5f0c8 |
| `GSDX_PCC_REPLAY_PASS=28/28` | PASS | Windows | 03-06-regress.log |
| `GSDX_GOAL_MUTATIONS_CAUGHT=58/58` | PASS | Windows | 03-06-regress.log |
| `GSDX_RECONCILE_PASS=22/22` `GSDX_GOAL_SWEEP_PASS=14/14` `GSDX_SWEEP_ALL_PASS=11/11` `GSDX_GOAL_EPOCH_PASS=19/19` `GSDX_ENGINE_ID_PASS=14/14` | PASS | Windows | 03-06-regress.log |
| the other 12 pre-existing goal suites at baseline (bind_mission 10, chaos 15, claude_providers 20, cli 25, codex_provider 18, convergence 29, gate_class 11, gate_provider 18, judge 11, long_run_provider 16, mutation_safety 8) | PASS | Windows | 03-06-regress.log |
| `python modules/liveness/reachability.py` | exit 0 | Windows | run at HEAD edc5f0c8 |

The fixture fix (298ba2c6) changed only the test file. No engine file changed after the Windows regression run, so the Windows suites above still describe the engine. Cause of the one earlier 38/39 read: the old sweep fixture gate could finish before the pass decided again, so the pass harvested and stopped at 1 (`sweep.py` further-dispatch loop breaks on any non-NEXT_EPOCH decision). The new gate `V-FRONTIER-SWEEP-EARLY-FINISH` reads, on the Linux plane, old fixture under a slow pass dispatched=1 and blocking fixture dispatched=3.

## Mutation drills (frontier suite, `tools/mutation_drill.py`)

| Drill | Gate | Verdict | Plane |
|---|---|---|---|
| m1 | V-FRONTIER-GLOBAL-WAIT | KILLED | Windows (03-06-drill.log) and Linux |
| m2 | V-FRONTIER-UNSAFE-WRITES | KILLED | Windows and Linux |
| m3 | V-FRONTIER-UNDECLARED | KILLED | Linux (03-06-drill-gex44.log) |
| m4 | V-FRONTIER-RESOURCE | KILLED | Linux |
| m5 | V-FRONTIER-POSTURE | KILLED | Linux |
| m6 | V-FRONTIER-ORDER | KILLED | Linux |
| m7 | V-FRONTIER-SWITCH | KILLED | Linux |
| m8 | V-FRONTIER-HARVEST-NOT-HIDDEN | KILLED | Linux |

The Linux drills ran with valid controls on a clone of 20c0f56f (before the test-only fixture fix). The Windows m3 attempt was CONTROL_INVALID (control 38/39) and is not counted.

## Requirements

| Req | Evidence (gate, plane) | Verdict |
|---|---|---|
| D04 four frontiers | V-FRONTIER-FRONTIERS, -GLOBAL-WAIT, -WAIT-ONLY-EMPTY (Linux 40/40; m1 killed) | met |
| D05 convergence graph | V-FRONTIER-GRAPH (Linux 40/40) | met |
| D06 no global WAIT | V-FRONTIER-LEGACY-EQUAL, -SWEEP-N, -BEGIN-REFUSES (Linux 40/40) | met |
| D07 unit properties | V-FRONTIER-UNIT-DERIVE, -UNDECLARED, -INDEP, -RESOURCE, -UNSAFE-WRITES (Linux; m2 m3 m4 killed) | met |
| D08 critical path | V-FRONTIER-PRIOR, -CRITICAL-PATH (Linux 40/40) | met |
| D09 postures | V-FRONTIER-POSTURE, -SWEEP-BOUND (Linux 40/40; m5 killed) | met |
| D25 speculative execution | policy + report only: V-FRONTIER-SPEC-ADMIT, -SPEC-REFUSE, -REPORTED-NOT-EXECUTED, -YIELD. Nothing speculative executes | PARTIAL by design: executed speculation is open for Phase 4 |
| D26 racing candidates | policy + ledger only: V-FRONTIER-RACE-ADMIT, -YIELD. Nothing races | PARTIAL by design: executed racing is open for Phase 4 |
| D27 resource-aware | V-FRONTIER-CLASSES (Linux 40/40) | met |
| D28 worker classes | V-FRONTIER-ORDER, -CRITICAL-PATH (Linux; m6 killed) | met |
| D33 information gain | V-FRONTIER-INFOGAIN (Linux 40/40) | met |
| D34 failure first | V-FRONTIER-FAILURE-FIRST (Linux 40/40) | met |

## Human-verification checks, run myself

1. Phase 2 suites green: replay 28/28 and semantics 48/48 (rows above). Done.
2. Every `03-0N-SUMMARY.md` present (01..06): checked in the phase dir listing. Done.
3. Liveness exit 0 with `frontier` declared PLANNED: run. Done.
4. Nothing pushed; `git status --short` clean except `vault/progress.md`: checked after the last commit. Done.
5. Kill switches (`GSDX_FRONTIER`, `FRONTIER.off`) -- V-FRONTIER-SWITCH green (Linux), m7 killed.

## Honest limits

- The frontier suite at 298ba2c6 was not completed on the laptop; its 40/40 is Linux-plane only.
- Phase 3 edits `epoch.py`, `reconcile.py`, `sweep.py` and adds `frontier.py`; `V-PCC-ADDITIVE-ONLY` is scoped to the Phase 2 range by Owner decision (option b).
- Engine identity term changed to `engine:b650bc5355d1...` (new `.py` under `goal/`); the before-value was not captured.
- D25/D26 are only partly met; do not report them as executed capabilities.