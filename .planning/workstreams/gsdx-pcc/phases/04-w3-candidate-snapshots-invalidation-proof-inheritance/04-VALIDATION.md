# Phase 4 Validation

| Requirement | Gate(s) | Suite | Plan |
|---|---|---|---|
| R12 unknown tree equality | V-INV-R12-CLOSURE, -NEEDS-GATE, -CONTROL | invalidation | 04-01 |
| D23/R02 candidate on git objects | V-CAND-SNAPSHOT-OID, -NO-SIDE-EFFECT, -UNKNOWN-ON-DOUBT, -STABLE, -DRIFT | invalidation | 04-01 |
| candidate.promoted landed | V-INV-PROMOTED-PROJECTION, V-PCC-VOCAB | invalidation, semantics | 04-01 |
| D12/D13/D10 certificate, moved under verification | V-CERT-* (6) | certificate | 04-02 |
| D01/D14/D45 inheritance, RED list | V-INV-FALSE-REUSE, -UNKNOWN-NOT-CLEAN, -FRESH-REQUIRED-NEVER, -OMITTED-WITHOUT-EVENT, -EVENT-DISAGREES, -INHERIT-OK, -SWITCH-OFF | invalidation | 04-03 |
| D11 algebra (PARTIAL), D20, D39, D24 substrate | V-INV-ALGEBRA-TRUTH, -NONAND-RUNS-FULL, -VSET-*, -FRESH-ISLANDS, -DRIFT-SUBSTRATE | invalidation | 04-04 |
| Mutation kill | drills d1-d6, each KILLED with a valid control | mutation_drill | 04-05 |

Regression (must not move): `GSDX_PCC_REPLAY_PASS=28/28`, `GSDX_PCC_SEMANTICS_PASS` (Phase 2 count, may grow only
by the vocab gate edit), `GSDX_FRONTIER_PASS=40/40`; `judge.py` diff empty; liveness exit 0.
Planes: laptop unless a drill is UNRUN, then "Linux plane" by the coordinator. Every gate has a red state recorded
before its green. UNKNOWN is never PASS.
