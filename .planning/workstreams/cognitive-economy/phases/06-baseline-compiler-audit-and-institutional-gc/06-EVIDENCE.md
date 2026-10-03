# Phase 6 Evidence: Baseline compiler audit and institutional GC

Full evidence: `vault/programs/cognitive-economy/handoffs/S.md`, `vault/programs/cognitive-economy/measure/s_demo/`,
`vault/programs/cognitive-economy/evidence/B-T-floor-and-gc.md`.

| Pillar | Terminal | Key evidence |
|---|---|---|
| S | MERGED_INTO_EXISTING_OWNER | derivation lives in `gsd_x_mission derive`, demonstrated on a real README with a negative control |
| T | AUTHORIZATION_BOUND | 490 modules swept; 14 DORMANT_TESTED to declare or wire; RETIRE_CANDIDATE 0 |

Verifier (epoch 4 re-run): `CEP_PILLAR_S=PASS`, `CEP_PILLAR_T=PASS`.

## Product Delta

- `measure/t_sweep.py`: a module-reachability sweep with PACKAGE_INTERNAL and from-package import handling, each
  matcher fix pinned by a control.

## Intelligence Delta

- The "universal baseline compiler" already exists in a different owner than the plan named; the right extension
  point is `gsd_x_mission derive`, not `baseline_ledger.py`.
- A naive orphan sweep proposed 3 deletions that were all live via relative sibling imports. Run on its own, the
  instrument would have recommended removing working code.
