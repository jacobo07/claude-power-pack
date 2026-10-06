# Requirements: autonomous-optimization (IC gen2)

Source: the Owner's /cpp-gsd-long brief (2026-10-05), master done-gate items 1-33, mapped to phases.

| id | requirement | phase |
|---|---|---|
| AO-01 | ownership reconciled; no parallel OS/runtime/DB/ratchet (gate 1-2) | 0 |
| AO-02 | executable optimization contract + gen2 ledger (gate 3, 6) | 0, 4 |
| AO-03 | cheap always-on observation during normal execution (gate 4, 24) | 1, 3 |
| AO-04 | generic detector discovers a candidate without instruction (gate 5, 19, 20) | 3, 5 |
| AO-05 | owner search before building (gate 7) | 4 |
| AO-06 | autonomy envelope (gate 8) | 4 |
| AO-07 | champion/challenger, shadow/canary/certify/deopt (gate 9-10) | 2, 5 |
| AO-08 | realized dividend measured; regressions detected; retirement semantics (gate 11-13, 26) | 4, 6 |
| AO-09 | KME-L measured, challenger by extension, equal-or-stronger, no unrelated-project raw reads (gate 14-18) | 1, 2 |
| AO-10 | certified path inherited by a fresh worker (gate 21, 33) | 6 |
| AO-11 | Production Reality producer -> consumer -> effect (gate 22) | 6 |
| AO-12 | negative controls reject bad / low-ROI optimizations (gate 23) | 3, 4 |
| AO-13 | meta-optimization stop rules (gate 25) | 4 |
| AO-14 | CBR promotion scoped to evidence (gate 27-28) | 6 |
| AO-15 | Vault + UKDL disposition for every bug (gate 29) | 7 |
| AO-16 | vMAX-NULL-ERROR clean; tests, mutants, benchmarks, PRG green (gate 30-31) | 7 |
| AO-17 | survives a fresh worker without transcript archaeology (gate 32) | 7 |

## Traceability (IC-gen2 pillars, read by the bound X2 clause of tools/ic_gen2.py)

| Req | Pillar | Status |
|---|---|---|
| AOP-M | optimizer lifecycle (reopened) | Pending |
| AOP-O | usage_index v5 substrate | Complete |
| AOP-P | KME-L challenger | Pending |
| AOP-Q | generic opportunity detectors | Pending |
| AOP-R | second workload taken by the loop | Pending |
