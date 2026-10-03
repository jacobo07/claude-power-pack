---
phase: 06-baseline-compiler-audit-and-institutional-gc
status: passed
score: 3/3
verified: 2026-10-03
---

# Phase 6 Verification

Re-verified by epoch 4 from a fresh process: `--pillar S` -> PASS, `--pillar T` -> PASS, `--final` ->
`CEP_VERDICT=PASS failures=0`.

| # | Success criterion | Result | Evidence |
|---|---|---|---|
| 1 | S: owners and their tests read and run; trait->obligation derivation demonstrated on a real project or the gap named | PASS | Gap named: neither owner derives obligations (`handoffs/S.md:11`); derivation demonstrated with `gsd_x_mission.py derive` on a real README, negative control 0 facts (`measure/s_demo/derive_stdout.txt`). Owner tests run by epoch 4 (see below) |
| 2 | T: liveness sweep run; never-invoked skills and orphan modules listed; retirements needing settings/deletion to the Owner bundle | PASS | `evidence/B-T-floor-and-gc.md:29-45` (490 modules, 14 DORMANT_TESTED, 3 PACKAGE_INTERNAL, RETIRE_CANDIDATE 0); Owner item `[T]` |
| 3 | Each pillar passes --pillar | PASS | epoch 4 re-run above |

## Owner tests run (epoch 4, 2026-10-03) -- named owner debt, not campaign-caused

| suite | campaign branch | main checkout | reading |
|---|---|---|---|
| `tools/test_baseline_generations.py` | 15/16, rc 1 | 15/16, rc 1 | `V-BGEN-REAL-B0-CITATIONS-HOLD`: 9 of 62 B0 citations `QUOTE_MISSING` (persistent_state destructive / monetary rules and one wii_homebrew rule). Red on both trees: pre-existing; the quoted rule bodies moved out of `~/.claude/rules` into skills |
| `tools/test_tower_ratchet.py` | 20/21, rc 1 | 21/21, rc 0 | `V-TRAT-REAL-CHAINS`: `web_surface` generation 1 `tampered` on the branch only. The branch diff since its fork (8b62b6ce) touches only campaign paths plus the verifier, and main has no committed tower/baseline change since then, so the difference comes from main's uncommitted tree; not campaign-caused |

Neither red is in the trait->obligation derivation that S judged. Both belong to the baseline owners.
