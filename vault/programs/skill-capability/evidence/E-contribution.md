# [E] contribution + result consumption -- D-SESSIONS measurement

Planes: sessions host `laptop` (derived: every row's `metrics.transcript` starts with `C:\Users\User\`); derivation host-independent (this file is rendered from committed rows by `tools/test_contribution_verdict.py`, nothing typed in). Sessions consumed by this phase: 0.

Frozen pillar E rule (ledger `frozen.pillars[E].rule`):

> contribution is claimed only from a paired benchmark inside the <= 10 new-session budget (D-SESSIONS); otherwise the measurement records why the budget cannot separate the arms

## Rows (authoritative grade = regrade row when one exists, else stored grade)

| run_id | arm | rep | valid | stored grade | regrade grade | authoritative | source |
|---|---|---|---|---|---|---|---|
| D-cwst-N0-r1 | N0 | 1 | True | FAIL-SWALLOW | FAIL-SWALLOW | FAIL-SWALLOW | regrade |
| D-cwst-N0-r2 | N0 | 2 | True | FAIL-SWALLOW | FAIL-SWALLOW | FAIL-SWALLOW | regrade |
| D-cwst-P-r1 | P | 1 | True | PASS | FAIL-SWALLOW-REPAIRED | FAIL-SWALLOW-REPAIRED | regrade |
| D-cwst-P-r2 | P | 2 | True | FAIL-SWALLOW | FAIL-SWALLOW | FAIL-SWALLOW | regrade |
| D-cwst-R-r1 | R | 1 | True | FAIL-SWALLOW | FAIL-SWALLOW | FAIL-SWALLOW | regrade |
| D-cwst-R-r2 | R | 2 | True | FAIL-SWALLOW | FAIL-SWALLOW | FAIL-SWALLOW | regrade |
| D-cwst-C-r1 | C | 1 | True | FAIL-SWALLOW | - | FAIL-SWALLOW | stored |
| D-cwst-C-r2 | C | 2 | True | FAIL-SWALLOW | - | FAIL-SWALLOW | stored |

## Arms (passes = exact `PASS`)

| arm | measured n | passes (authoritative) | passes (stored) |
|---|---|---|---|
| N0 | 2 | 0 of 2 | 0 of 2 |
| R | 2 | 0 of 2 | 0 of 2 |
| P | 2 | 0 of 2 | 1 of 2 |
| C | 2 | 0 of 2 | 0 of 2 |

## Pairs against N0 (authoritative grades, two-sided Fisher exact)

| arm | effect | points | p | p (4 dp) |
|---|---|---|---|---|
| R | 0 | 0 | 1 | 1.0000 |
| P | 0 | 0 | 1 | 1.0000 |
| C | 0 | 0 | 1 | 1.0000 |

## Separation bound (alpha 1/20, budget 10 sessions)

Equal allocation (k sessions per arm):

| k | floor | points | attaining tables (a/k vs b/k, p) |
|---|---|---|---|
| 1 | none | none | no table separates |
| 2 | none | none | no table separates |
| 3 | none | none | no table separates |
| 4 | 1 | 100 | 0/4 vs 4/4 p=1/35; 4/4 vs 0/4 p=1/35 |
| 5 | 4/5 | 80 | 0/5 vs 4/5 p=1/21; 1/5 vs 5/5 p=1/21; 4/5 vs 0/5 p=1/21; 5/5 vs 1/5 p=1/21 |

All allocations n1 + n2 <= 10 (n1, n2 >= 1): 45 allocations, 23 separate nothing; those that separate:

| n1 | n2 | floor | points | attaining tables (a/n1 vs b/n2, p) |
|---|---|---|---|---|
| 2 | 5 | 1 | 100 | 0/2 vs 5/5 p=1/21; 2/2 vs 0/5 p=1/21 |
| 2 | 6 | 1 | 100 | 0/2 vs 6/6 p=1/28; 2/2 vs 0/6 p=1/28 |
| 2 | 7 | 1 | 100 | 0/2 vs 7/7 p=1/36; 2/2 vs 0/7 p=1/36 |
| 2 | 8 | 1 | 100 | 0/2 vs 8/8 p=1/45; 2/2 vs 0/8 p=1/45 |
| 3 | 4 | 1 | 100 | 0/3 vs 4/4 p=1/35; 3/3 vs 0/4 p=1/35 |
| 3 | 5 | 1 | 100 | 0/3 vs 5/5 p=1/56; 3/3 vs 0/5 p=1/56 |
| 3 | 6 | 5/6 | 250/3 | 0/3 vs 5/6 p=1/21; 3/3 vs 1/6 p=1/21 |
| 3 | 7 | 6/7 | 600/7 | 0/3 vs 6/7 p=1/30; 3/3 vs 1/7 p=1/30 |
| 4 | 3 | 1 | 100 | 0/4 vs 3/3 p=1/35; 4/4 vs 0/3 p=1/35 |
| 4 | 4 | 1 | 100 | 0/4 vs 4/4 p=1/35; 4/4 vs 0/4 p=1/35 |
| 4 | 5 | 3/4 | 75 | 1/4 vs 5/5 p=1/21; 3/4 vs 0/5 p=1/21 |
| 4 | 6 | 3/4 | 75 | 1/4 vs 6/6 p=1/30; 3/4 vs 0/6 p=1/30 |
| 5 | 2 | 1 | 100 | 0/5 vs 2/2 p=1/21; 5/5 vs 0/2 p=1/21 |
| 5 | 3 | 1 | 100 | 0/5 vs 3/3 p=1/56; 5/5 vs 0/3 p=1/56 |
| 5 | 4 | 3/4 | 75 | 0/5 vs 3/4 p=1/21; 5/5 vs 1/4 p=1/21 |
| 5 | 5 | 4/5 | 80 | 0/5 vs 4/5 p=1/21; 1/5 vs 5/5 p=1/21; 4/5 vs 0/5 p=1/21; 5/5 vs 1/5 p=1/21 |
| 6 | 2 | 1 | 100 | 0/6 vs 2/2 p=1/28; 6/6 vs 0/2 p=1/28 |
| 6 | 3 | 5/6 | 250/3 | 1/6 vs 3/3 p=1/21; 5/6 vs 0/3 p=1/21 |
| 6 | 4 | 3/4 | 75 | 0/6 vs 3/4 p=1/30; 6/6 vs 1/4 p=1/30 |
| 7 | 2 | 1 | 100 | 0/7 vs 2/2 p=1/36; 7/7 vs 0/2 p=1/36 |
| 7 | 3 | 6/7 | 600/7 | 1/7 vs 3/3 p=1/30; 6/7 vs 0/3 p=1/30 |
| 8 | 2 | 1 | 100 | 0/8 vs 2/2 p=1/45; 8/8 vs 0/2 p=1/45 |

Floor: 3/4 (75 points), first attained at (4,5), (4,6), (5,4), (6,4); equal-allocation floor 4/5 (80 points).

verdict: NOT_SEPARABLE (largest committed effect 0, floor 3/4)

## Commands

command: python .planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py run --arm N0 --reps 2
command: python .planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py run --arm R --reps 2
command: python .planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py run --arm P --reps 2
command: python .planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py run --arm C --reps 2

(host laptop; shape from the `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py` docstring line 6; per-run settings such as arm C's `--settings` card attachment are not recorded in the rows)

command: python3 tools/test_contribution_verdict.py
command: python3 tools/test_contribution_verdict.py --write-evidence

(`python` on the laptop, `python3` on gex44; the first renders nothing, it checks)
