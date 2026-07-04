# CO-NextGen (CO-11 / CO-12) — NEXTGEN REALITY SCAN REPORT

**Mode:** ULTRA-PLAN · FASE -1 Reality Scan · STOP #1 (blocking) · 2026-07-04
**Goal framing:** 2x/3x/4x savings in *reasoning* (dup elimination + minimum context +
economic model routing + loop compression + repo brain), token savings as consequence.
**Hard constraint:** CO-09/CO-10 are TAKEN (SCS C61/C62). New datasets take the next free CO IDs.

---

## Slot inventory (verified)

Highest sealed = **C73** (Activate-Before-Build, sealed 2026-07-03). C71/C72 = Graphify.
**Next free SCS slot = C74.** CO family = CO-00..CO-10 (11 datasets, sealed C61/C62) →
**next free CO IDs = CO-11, CO-12.** Never CO-09/CO-10.

## Per-system verdict (the doc's CO-09..CO-15 proposals)

| Proposed system | PP equivalent | Verdict | Note |
|---|---|---|---|
| Model Economics Router | **CO-03** Dynamic Cognitive Router (Vault→asset→deterministic→Haiku→Sonnet→Opus) + `router.py` | **COVERED** | live cascade |
| Context VM / Context Compiler | **CO-04** Context Virtual Memory (Hot/Warm/Cold/External) + **GK-06** Route Compiler + Minimal Context Pack | **COVERED** | two layers |
| Zero-Token / Asset Factory | **CO-05** Zero Token Layer + Asset Registry + **GK-08** Knowledge Writeback | **COVERED** | session→asset live |
| Reasoning Deduplication Engine | **PM-03** Findings Bus + Redundancy Tax (activated + proven yesterday, SCS C73) | **COVERED** | consume-before-reason gate |
| Repo Shared Brain / Repo Intelligence | **PM-01** Repo Shared Brain | **COVERED** | generated once, consumed by all |
| Model Economics / Budget Auction | **PM-04** Parallel Budget Auction + Opus Singleton | **COVERED** | cross-pane model axis |
| Loop Compression Engine | **CO-09** Loop & Subagent Economics | **COVERED** | see below |
| **Output Budget Governor** | CO-01 (cost model) / CO-08 (sessions) / `output_contracts` (quality only) | **GAP-REAL** | see below |
| **2x/3x/4x Readiness Telemetry** | C68/C69/C70 (past-tense) / CO-01 WU/MTok / GK-09 (graph-only) | **GAP-REAL** | see below |

### Loop Compression → COVERED by CO-09 (do NOT build)
CO-09's 7-part loop budget already mandates: max-iterations (hard cap), **checkpoint plan**,
**stop gates** (success / no-progress / loop-until-dry convergence), **kill switch** (auto forcible
termination, cost>2×budget / ceiling breach / 2-consecutive-failures, no bypass), resume plan.
Anti-patterns forbid uncapped loops and no-convergence spins. The only conceivable sliver —
"detect a loop iteration that re-derives an earlier iteration's *conclusion* and short-circuit it" —
is **PM-03 (Findings Bus)** applied across iterations, not a new engine. **Not a dataset.**

### GAP-REAL 1 — Output Budget Governor (→ CO-11)
Evidence of absence: `grep "output budget"` across the whole repo = **0 matches**.
`output_contracts/validator.py` is **quality-only** (OQS slop-token detection, exists/test-passed,
threshold 70) — it never bounds output *length or economy per turn*. CO-01 prices cost as an input;
CO-08 caps *sessions*; CO-09 caps *loops*. **No dataset owns the per-turn output contract.**
Evidence of need (measured): C69 P1 agent self-correction = **370k output tokens**; P4 plan→exec
divergence = **249k** — output waste with no per-turn budget. Genuinely new; ~40% synthesis
(extends `output_contracts` with an economy dimension + CO-01 output pricing).

### GAP-REAL 2 — Cognitive Readiness Telemetry (→ CO-12)
The audit family measures what **happened**: C68 volume, C69 behavior, C70 infra. CO-01 measures
WU/MTok (efficiency). GK-09 measures graph coverage (graph-only). **None measures adoption-rate of
the cognitive machinery** — the leading indicator of whether 2x/3x/4x is actually being realized:
bus-consult-before-reason %, brain-reuse (repo-scan-skipped-when-Brain-valid) %, model-demotion
count, **Opus-avoided** count, cognitive-compression ratio. Without these, any savings claim is
speculation (the doc's "Telemetry Before Claims" is exactly right). Genuinely new; extends the
C68/C69/C70 audit family + CO-01 WU/MTok + the GK-09 observatory pattern.

## Requested contracts — status

| Contract | Status |
|---|---|
| **Output Budget Contract** | **NEW** → lands in CO-11 (binary criteria for when long output is justified) |
| **Telemetry Before Claims Contract** | **PARTIAL→formalize** — the discipline already lives in C68/C69/C70 ("si un patrón no tiene ROI medible → ignorar"; fix only at freq≥5). Naming it a cross-cutting contract is a thin add → lands in CO-12 |
| **Extend Existing Parent Contract** | **ALREADY DOCTRINE** — SCS C73 (Activate-Before-Build) + HR-PREMISE-001 (verify premises) + V-REALITY-SCAN gate already enforce it. Re-formalizing is redundant; cite, don't create |

## Telemetry: existing vs requested

| Requested metric | Exists? | Source |
|---|---|---|
| cognitive compression ratio | **NO** | — (CO-12) |
| 2x/3x/4x readiness score | **NO** | — (CO-12) |
| cost per useful decision | PARTIAL | CO-01 WU/MTok (per-op, not per-decision) |
| model demotions count | **NO** | — (CO-12; CO-03 routes but does not count demotions) |
| Opus avoided count | **NO** | — (CO-12) |

## Recommendation (STOP #1)

Unlike yesterday's Scope A (all-already-built), here there ARE **two genuine gaps**: CO-11 + CO-12.
Both are honest ~40% synthesis but own material nothing else does (per-turn output contract;
adoption-rate telemetry). **Drop Loop Compression (CO-09 covers it).** SCS seal = **C74**.

Honest ROI caveat: the single biggest *practical* lever is still **activating the inert** — the
CO-08 wrapper routing remains Owner-side-pending from yesterday. CO-12 is the instrument that makes
that activation *measurable* (it proves whether the machinery is used), so CO-12 has the higher ROI
of the two and directly serves the "Telemetry Before Claims" mandate.

**Options:** A = build CO-11 + CO-12 (both gaps). B = CO-12 only (telemetry first — measure before
more building). C = drop both, activate-the-inert only (CO-08 wrapper) — highest immediate ROI,
zero new datasets. **Recommended: B or A.**
