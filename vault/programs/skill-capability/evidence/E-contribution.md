# [E] contribution + result consumption -- D-SESSIONS measurement

Planes: sessions host `laptop` (derived: every row's `metrics.transcript` starts with `C:\Users\User\`); derivation host-independent (this file is rendered from committed rows by `tools/test_contribution_verdict.py`, nothing typed in). Sessions consumed by this phase: 0.

Frozen pillar E rule (ledger `frozen.pillars[E].rule`):

> contribution is claimed only from a paired benchmark inside the <= 10 new-session budget (D-SESSIONS); otherwise the measurement records why the budget cannot separate the arms

## Sources

- rows: `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/results-delivery.jsonl`, the run_id set of its blob at 123c96cc (the commit that brought it to 8 rows), LF sha256 `90f3e94810d6883ca0f2fb3fca9c6a1b2dfafe7d8f98eb720ad620b64c1a021d`
- regrade: `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/results-delivery-regrade.jsonl`, blob at its add commit 713b02a7 (6 rows), LF sha256 `07792b9862814703a7e9d57269bebb9ed48257b01ac70395fa0997b84ee78620`
- Rows outside the pinned set (not used by the verdict): none

## Grade authority (why the regrade row wins)

- commit 713b02a7 added the regrade file; subject: "test(r2): CWST delivery runs -- 6/6 swallow across N0/R/P; residency and judged paging both fail, commit card earned (C3, C7)"; body: "P-r1's amend hid a swallow from the history grader -> reflog-aware grader"
- `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py` at 713b02a7 carries `FAIL-SWALLOW-REPAIRED` on lines 147, 307, 308
- `vault/audits/cwst-representation-verdict-2026-10-03.md` line 19: "r1 stored PASS = swallow + `--amend`, regrades FAIL-SWALLOW-REPAIRED"
- `vault/plans/skill-residency-program-2026-10-03.md` line 92: "P-r1 stored PASS = amended shape, regrades FAIL-SWALLOW-REPAIRED"

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

Largest effect against N0: authoritative 0 (0 points), stored 1/2 (50 points).

## Pairs against N0 (authoritative grades, two-sided Fisher exact)

| arm | effect | points | p | p (4 dp) |
|---|---|---|---|---|
| R | 0 | 0 | 1 | 1.0000 |
| P | 0 | 0 | 1 | 1.0000 |
| C | 0 | 0 | 1 | 1.0000 |

## Sessions (D-SESSIONS)

- frozen D-SESSIONS: new_benchmark_cap 10; listing family remaining 8 of 12
- phase 1: not stated
- phase 2: 0 (.planning/workstreams/skill-capability/phases/02-listing-floor/02-02-SUMMARY.md:47; vault/programs/skill-capability/evidence/B-listing-floor.md:3; vault/programs/skill-capability/evidence/B-listing-floor.md:52)
- phase 3: 0 (vault/programs/skill-capability/evidence/C-delivery.md:84)
- phase 4: not stated
- phase 5: 0 (vault/programs/skill-capability/evidence/F-representation.md:50)
- phase 6: not stated
- consumed_stated 0; remaining 10 (the budget of the bound below)
- this phase (7): 0 sessions; this script runs no session. `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_runner.py` at HEAD sets line 29 `RUNS = Path(r"C:\Users\User\Apps\p3-runs")`; line 32 `CLAUDE = r"C:\Users\User\.local\bin\claude.exe"`, so the benchmark cannot run on a POSIX host as committed.
- Unstated phases can only lower the true remaining budget, and a lower budget never lowers the floor (checked below), so NOT_SEPARABLE at the stated budget implies NOT_SEPARABLE at the true one.

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

Floor: 3/4 (75 points), attained at (4,5), (4,6), (5,4), (6,4); equal-allocation floor 4/5 (80 points).

Floor per budget (non-increasing in the budget, checked): 2: none, 3: none, 4: none, 5: none, 6: none, 7: 1, 8: 1, 9: 3/4, 10: 3/4

verdict: NOT_SEPARABLE (largest committed effect 0, floor 3/4; under the stored grades 1/2, also NOT_SEPARABLE)

## Result consumption (from the rows' `delivery` and `card_rows` fields)

| arm | n | listing | skill invoked | skill before the protected commit | card_rows |
|---|---|---|---|---|---|
| N0 | 2 | absent 2 | 0 of 2 | 0 of 2 | - |
| R | 2 | absent 2 | 0 of 2 | 0 of 2 | - |
| P | 2 | bare 2 | 0 of 2 | 0 of 2 | - |
| C | 2 | bare 2 | 0 of 2 | 0 of 2 | unknown 2 |

The delivered capability's output was consumed (a Skill invocation, or a card deny reaching the agent) in 0 of 8 measured rows; 0 rows UNMEASURED for consumption.

n < 5 per arm: no rate estimated, only counts.

## Figures not derivable from the committed rows (cited, not used by the verdict)

- C card fixed, deny mode: frozen `D-CARD.arm_c` = "2/2 PASS (123c96cc)"; `vault/audits/cwst-representation-verdict-2026-10-03.md` line 21: "| **C card, fixed (123c96cc), deny mode** | 2 | **2/2 PASS**, 1 commit each |" -- no committed row holds it (the 8 pinned rows hold only the pre-fix C arm); not used by the verdict.
  - judged by the verdict rule used for the committed rows: 2/2 PASS against N0 0/2 is an effect of 1 (100 points), floor 3/4, so SEPARABLE: the budget could separate an effect of this size (smallest total 7 sessions (2 vs 5 or 3 vs 4 or 4 vs 3 or 5 vs 2); equal allocation 4 per arm (8 sessions), against new_benchmark_cap 10). Rows like these, judged as committed rows, would give the verdict SEPARABLE.
  - fisher_two_sided(2, 2, 0, 2) = 1/3: whether these few rows are significant on their own, which is not what pillar E asks (it asks whether the budget can separate an effect of this size).
- "10/40 sessions used" (`vault/plans/skill-residency-program-2026-10-03.md` line 93): the skill-residency program's own budget, not D-SESSIONS; not used by the verdict.
- "R loaded the full body (proven by a body-only sentence)" (commit 713b02a7 message): no row field records it; not used by the verdict.

## What a separating benchmark would need (necessary condition, not a power calculation)

- authoritative effect 0: no n separates a zero effect.
- stored-grade effect 1/2: smallest total 15 sessions (6 vs 9 or 9 vs 6); equal allocation 10 per arm (20 sessions), against new_benchmark_cap 10.
- The smallest total is taken over every allocation n1 + n2 (the same most-favourable-design rule as the floor); the equal allocation is shown beside it.
- This is only the smallest design in which such a table could separate at all; a powered design (a stated chance of separating when the effect is real) needs more sessions than this.

## Commands

command: python .planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py run --arm N0 --reps 2
command: python .planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py run --arm R --reps 2
command: python .planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py run --arm P --reps 2
command: python .planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py run --arm C --reps 2

(host laptop; shape from the `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py` docstring line 6; per-run settings such as arm C's `--settings` card attachment are not recorded in the rows)

command: python3 tools/test_contribution_verdict.py
command: python3 tools/test_contribution_verdict.py --write-evidence

(`python` on the laptop, `python3` on gex44; the first renders nothing, it checks)
