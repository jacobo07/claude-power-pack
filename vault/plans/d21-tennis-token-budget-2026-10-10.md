# D21 Wii Sports Tennis -- token budget to completion (handoff, 2026-10-10)

Backlog entry: `vault/plans/deferred-backlog.md` D21 (was D11 on this branch). Unit: processed tokens (input + cache
read + cache write + output, deduplicated by message.id), the unit every goal ledger in PP uses. M = measured (source
next to it). H = hypothesis (assumption stated). D = derived here by arithmetic.

## 0. The one-line answer

The number that decides the budget, **tokens per reconstructed function, has never been measured**. The factory has
produced 4 model MATCHes in its whole life (recon STATE.md:86), and the instrument built to measure it, CP50 C2b,
returned `STALE_INPUT "environment"` on all 50 units (C2b-receipt.md:8). Every figure below the gate in section 5 is
therefore a hypothesis band, not a forecast.

| Scope | LOWER | P50 | HIGH (~P90) |
|---|---:|---:|---:|
| **A. Motion closure + relink + WMOS (D21's recommended scope)** | **~47M** | **~215M** | **~755M** |
| B. Full Tennis matching (all Tennis code as source) | ~434M | ~1,927M | ~4,640M |
| C. Whole SportsPackEP.dol | not budgeted (18,820 functions; ~10x B) | | |

Spend now, before any Tennis work: **section 5 gate, ~2-6M**, which converts the bands into a measured forecast.

## 1. What is measured (inputs)

| Fact | Value | Source |
|---|---|---|
| Wii Sports executable | `files/EU/sys/sports/SportsPackEP.dol`, 4,343,616 B, no RELs | M, d11-tennis-step0.md:8 |
| DTK functions in the DOL | 14,885 (probe convention 18,820) | M, step0:14-15 |
| Tennis candidate (6 DTK objects) | 1,797 functions, 100,947 instructions (upper bound) | M, step0:20 |
| Exact Resort shape inside Tennis | 408 (23%); loose 574 (32%) | M, step0:27 |
| Novel closure inside Tennis units | 1,323 functions | M, step1:30 |
| KPAD read path | 3 game functions; Tennis reads controller state by DATA | M, step1:33-39 |
| Direct motion consumers in Tennis | 50 getter callers, 20 read controller fields (floors) | M, step3:22-23 |
| Resort factory: model MATCHes ever | 4 (Sonnet), plus 289 donor MATCHes | M, recon STATE.md:86 |
| Worker cost per call (C1) | 731,961 / 6 calls = ~122k | M, RECON-FACTORY-HANDOFF:75 |
| Fresh context floor per call | 115-150k | M, economic-engine-repair plan:14, CDC plan:62 |
| Resort P2 oracle parity (phase cost) | ~40.8M (P2a 2.40 + main 10.81 + P2b 27.60) | M, RECON-FACTORY-HANDOFF:139 |
| Resort P3 promotion (phase cost) | ~7.0M (P3a 2.35 + P3b-1 1.79 + misattr. 1.32 + P3b-2 1.49) | M, same |
| Resort P5 census | 1.02M (+1.41M failed lease) | M, recon STATE.md:7 |
| Resort phases 1/01.1/4 (pre-economy) | ~1,180M lineage | M, recon STATE.md:46 (not comparable: old regime) |
| C2b | 1 of 4 Phase-7 GEX44 jobs spent, 0 verdicts | M, C2b-receipt.md:8-11 |

**Unmeasured and decisive:** tokens per attempted function (c), success fraction per attempt (s), the donor discount for
Resort-shape functions (d), and the true size of the motion closure (N_A).

## 2. Cost model

```
TOTAL = G (measurement gate)
      + P (probes)
      + O (onboarding the Wii Sports DOL into the factory)
      + N_novel * c / s  +  N_shared * c * d / s      (reconstruction)
      + R (relink / build pipeline)
      + W (Wii Motion OS integration)
      + V (validation: Dolphin on GEX44, hardware prep)
      + 25% x subtotal  (coordination <= 10% + repair reserve 15%)
```

Parameter bands (H unless marked):

| Param | LOWER | P50 | HIGH | Basis |
|---|---:|---:|---:|---|
| c, tokens per attempted function | 0.25M | 1.0M | 2.0M | H: calls/fn x cost/call. LOWER = 4 calls x ~60k (cohort worker, slim floor, cache hits); P50 = 8 x ~120k (C1's measured per-call); HIGH = ~13 x ~150k (hard functions, repair loops) |
| s, verified fraction per attempt | 0.9 | 0.7 | 0.5 | H; failed attempts are paid too, so c/s is cost per VERIFIED function |
| d, donor discount (shape match in Resort) | 0.1 | 0.3 | 0.6 | H; a shape match is a donor, not a MATCH (step0:30), and only helps if the Resort side is solved, which today it mostly is not |
| N_A, motion closure size (scope A) | 50 | 120 | 250 | H from M floors: 50 getter callers (step3); step 4 argument propagation expected to widen 1-5x |

Note on c/s: the table in section 3 folds s into c's band ends (LOWER uses c=0.25, s~=1; P50 uses c=1.0, s~=1;
HIGH uses c=2.0, s~=1) to avoid double-stretching the tails. Treat the result as a band, not a distribution.

## 3. Scope A -- motion closure + relink + WMOS (recommended)

| # | Line | LOWER | P50 | HIGH | Notes / done check |
|---|---|---:|---:|---:|---|
| A0 | Section 5 gate (C2b fix + rerun + C3) | 2.0 | 3.5 | 6.0 | Done = per-function cost table for draw 1-5 |
| A1 | Step 4 probe (argument propagation, subtract Resort overlap) | 0.2 | 0.3 | 0.5 | Zero-model script; one bounded Sonnet subagent like step 3 (138,532 M) |
| A2 | Onboarding, closure-scoped (split certification + oracle parity for the target units only, not a full census) | 10 | 20 | 40 | Anchored on Resort P2 ~40.8M (full title) and P5 1.0M; GEX44 jobs needed (job budget is an Owner decision) |
| A3 | Reconstruct N_A functions to MATCH (both oracles) | 12.5 | 120 | 500 | N_A x c: 50x0.25 / 120x1.0 / 250x2.0 |
| A4 | Relink pipeline for SportsPackEP (`relink.py` / `lcf2ld.py` exist; retail objects for everything else) | 5 | 10 | 20 | Done = relinked DOL byte-identical outside the closure, boots in Dolphin |
| A5 | WMOS integration at source (U1 not on this path) | 5 | 12 | 25 | Spec: KSR `t3-wii-motion-os-compendium.md`; adapter at V0A |
| A6 | Validation: Dolphin on GEX44, then hardware prep | 3 | 6 | 12 | Hardware boot is the Owner's step |
| | Subtotal | 37.7 | 171.8 | 603.5 | D |
| | +25% coordination + repair reserve | 9.4 | 43.0 | 150.9 | D |
| | **Total scope A** | **~47M** | **~215M** | **~755M** | D |

What dominates: A3 is 33% of LOWER, 70% of P50 and 83% of HIGH. The budget is a bet on c; everything else is small.

## 4. Scope B -- full Tennis matching

N_novel = 1,323 (M); N_shared = 1,797 - 1,323 = 474 (M, upper bound because the candidate is an upper bound).

| # | Line | LOWER | P50 | HIGH |
|---|---|---:|---:|---:|
| B0 | Section 5 gate | 2.0 | 3.5 | 6.0 |
| B1 | Onboarding, full title | 20 | 45 | 80 |
| B2 | Novel functions: N_novel x c (LOWER uses 1,200) | 300 | 1,323 | 3,000 (1,500 x 2.0) |
| B3 | Shared functions: 474 x c x d | 11.9 (474 x 0.25 x 0.1) | 142.2 (474 x 1.0 x 0.3) | 568.8 (474 x 2.0 x 0.6) |
| B4 | Relink + WMOS + validation (A4+A5+A6) | 13 | 28 | 57 |
| | Subtotal | 346.9 | 1,541.7 | 3,711.8 |
| | +25% | 86.7 | 385.4 | 928.0 |
| | **Total scope B** | **~434M** | **~1,927M** | **~4,640M** |

For scale: the Resort lineage spent ~1,180M on phases 1, 01.1 and 4 under the pre-economy regime (STATE.md:46).

## 5. The gate that turns this into a forecast (do first)

1. **Diagnose C2b's STALE_INPUT "environment"** on all 50 units (pins / environment hash between the built job and the
   judge; C2b-receipt.md:13). Zero-model where possible. ~0.3-1M.
2. **Rerun C2b** with Phase-7 job 2 of 4 (Owner: job budget). ~1.5M class (P3b-2 measured 1.49M).
   Done = `arm_a.py records --first 1 --last 5` with best verdict, compiles and wall_s per function.
3. **C3**: p50/p95 of c from 5 functions. Then re-run this file's section 3 with c MEASURED. ~0.2M.
4. Re-budget Tennis from the measured c. With N_A = 120 and the other P50 lines unchanged: c = 0.5M gives scope A
   (51.8 + 60) x 1.25 = ~140M; c = 2.0M gives (51.8 + 240) x 1.25 = ~365M, and scope B is then not economic without a
   learning curve.

Gate cost: **~2-6M** (goal cp50-c2 has 11.2M left, so no new goal is needed for it).

Second gate (D21's own activation criterion): CP50 reports the learning curve (does c fall as donors and procedures
accumulate?). Without it, scope B is a flat extrapolation and should not be funded.

## 6. Funding shape (how to spend it without a coordinator overrun)

- One goal per stage, never one monolithic goal: `tennis-a1` (probe), `tennis-a2` (onboarding), `tennis-a3-tN`
  (reconstruction tranches of ~25 functions each), `tennis-a4`, `tennis-a5`, `tennis-a6`.
- Tranche rule for A3: fund 25 functions, measure c, re-forecast, then fund the next 25. Stop if c drifts > 2x the gate's
  p50 for two tranches (Regla 12 economics: pivot, not retry).
- Coordinator per stage <= 1.0M (D23 cost rule: a long laptop pane coordinated 25.36M against a 2.0M forecast).
- Workers: slim packet workers, Sonnet by default (HR-COST-003), escalate only on failed verification (tier routing).
- Never Set-Location into a goal root (32.8M and 1.32M misattribution incidents).
- GEX44 jobs are a second budget next to tokens: A2 + A3 need an Owner-ratified job count (Resort used P2 2 / P3 2 / P7 4).

## 7. Risks that move the number

| Risk | Effect | Mitigation |
|---|---|---|
| c unmeasured | dominates every band | section 5 gate |
| Motion closure larger than 250 (vtable / argument flow) | A3 grows linearly | step 4 probe before funding A3 |
| Resort donors unsolved | d tends to 1 for scope B | scope A first; B only after CP50's learning curve |
| SportsPackEP onboarding hits Resort-P2-class trouble (P2b alone was 27.6M) | A2 at HIGH | closure-scoped parity only |
| Non-matching code needed for WMOS changes | MATCH oracle no longer applies after integration | match first, then integrate on a branch; behavioural check in Dolphin |
| Weekly provider limit | time, not tokens (a 429 already stopped a worker on 10-10) | tranches sized below the weekly quota |

## 8. Next 3 actions

1. Diagnose C2b STALE_INPUT (section 5.1), in a fresh pane, goal cp50-c2, no Set-Location into wt_cp50_c2.
2. Owner: authorize Phase-7 job 2 of 4 for the C2b rerun; run it; write C3.
3. Run D21 step 4 (zero-model probe) in parallel, since it does not depend on c; then recompute section 3 with measured c
   and N_A and replace every H in it.
