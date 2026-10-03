---
phase: 03-opportunity-and-delivery-measurement
verified: 2026-10-03T19:40:00Z
status: passed
score: 3/3 roadmap success criteria + 6/6 frozen-rule checks verified (SC-C)
behavior_unverified: 0
verifier: orchestrator (the gsd-verifier subagent stopped at a context wall before running any check; every line below was re-observed by the orchestrator on host gex44 at HEAD a3a58716)
---

# Phase 3: Opportunity and delivery measurement - Verification

**Goal:** One gate computes opportunity, delivery, recall and precision over a named transcript window.
**Requirement:** SC-C. Host: gex44.

## Success criteria

| # | Criterion | Command | Observed | Verdict |
|---|-----------|---------|----------|---------|
| 1 | The gate is driven red once | temp copy of `vault/programs/skill-capability/delivery_fixture.json` with the first `deny-card` row flipped to `no_opportunity`, expected block unchanged; `python3 tools/test_skill_delivery.py --fixture <copy>` | rc=1, `SD_PASS=1/7`, FAIL V-SD-OPPORTUNITY (measured 7, expected 8), V-SD-DELIVERY, V-SD-UNMEASURED-NOT-ZERO, V-SD-RECALL (`3/5 = 0.600 (n=5)` vs `4/6`), V-SD-PRECISION, V-SD-SMALL-N | PASS |
| 2 | n is reported per rate | `grep -nE "recall\|precision" vault/programs/skill-capability/evidence/C-delivery.md` | F: `recall: 4/6 = 0.667 (n=6)`, `precision: n=4 (< 5, not estimated)`; L: `recall: 6/6 = 1.000 (n=6) -- selection-bound`, `precision (card channel): 0/5 = 0.000 (n=5)`; G: `recall and precision: UNMEASURED (no opportunity source on this plane)` | PASS |
| 3 | `--pillar C` PASS | `python3 tools/test_skill_capability_program.py --pillar C` | `CEP_PILLAR_C=PASS` | PASS |

## Frozen rule and run constraints

- **No ratio below n=5:** `grep -nE "\(n=[0-4]\)" evidence/C-delivery.md` -> no match; window F precision (n=4) prints no ratio.
- **UNMEASURED is never 0:** F prints `delivery UNMEASURED: 2 (outside the recall n)`; G prints opportunity UNMEASURED; L prints `population recall: UNMEASURED on host gex44`.
- **Gate reads only committed files** (the CE verifier re-runs it on the laptop at `--final`): `HOME=<empty temp dir> python3 tools/test_skill_delivery.py` -> `SD_PASS=36/36`, identical to the default run.
- **Fixture and evidence agree:** fixture `expected` = opportunities 8, delivery_measured 6, unmeasured 2, delivered 4, recall 4/6, precision 1/4 (n=4), matching the rendered evidence (the plan's "7 / 1" was superseded by orchestrator amendment A-1, recorded in 03-01-SUMMARY).
- **Owner baseline not worsened:** `python3 tools/test_skill_invocations.py` -> `SKINV_PASS=11/12`, only FAIL `V-SKINV-REAL-TYPED: positive-control transcript not found` (laptop-only control, pre-existing).
- **Ledger frozen untouched:** `frozen` equals the copy at FROZEN_AT `217d72b5` -> True.
- **Earlier pillars:** `--pillar A` -> `CEP_PILLAR_A=PASS`, `--pillar B` -> `CEP_PILLAR_B=PASS`.
- **No placeholders:** `grep -nE "TBD|FIXME|XXX" tools/test_skill_delivery.py tools/skill_invocations.py` -> none.

## Laptop plane (not a phase gap)

The population run over the laptop's full card ledger and transcripts is the `[C]` owner-bundle line.

## Addendum (orchestrator, after review fixes 8b0137aa)

Review WR-01 (`pass-unrecordable` now an opportunity, `other_decision` counter), WR-02 (ts-less deny-card keeps card
delivery), WR-03 (each provenance clause has its own red mutant), IN-01 (naive ts unparseable) changed window F:
opportunities 9, measured 7, `[F] recall: 4/7 = 0.571 (n=7)`, `[F] precision: n=4 (< 5, not estimated)`; evidence and
fixture sha re-pinned in state.C. Re-observed on gex44 at 8b0137aa: `SD_PASS=53/53`; the same red drive (first deny-card
row flipped, expected unchanged) -> rc=1, `SD_PASS=1/7`; `--pillar A/B/C` PASS. Status stays passed.
