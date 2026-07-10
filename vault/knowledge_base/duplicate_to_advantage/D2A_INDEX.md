# Duplicate-to-Advantage Engine — Master Index (D2A)

> The immune-and-evolution system of the Claude Power Pack. Where **CO** governs a
> session's *cost*, **PM** the *coordination* of panes, **GK** *how knowledge is located*,
> **FD** *converting a frontier delta into advantage*, and **FIOS** *executes* that
> doctrine — the **D2A Engine** governs what happens when the ecosystem is asked to build
> something that **already partly exists.**
>
> **Root law (`PR-DUPLICATE-TO-ADVANTAGE-001`):** *Ninguna duplicidad termina en rechazo.
> Toda duplicidad se convierte en búsqueda estructurada de la mejor capacidad adyacente
> que aún no existe.*
>
> **Scope approved by Owner 2026-07-10 (STOP #1):** the Reality Scan found **0 of 6
> components are pure-NEW prose datasets** — all are EXTEND compositions of sealed
> families, unified by one genuinely-new *prospective-intake* delta. Following the FIOS
> precedent (SCS C84: 17 systems → 3 engines + 1 doctrine), and applying the D2A
> anti-inflation contract **to D2A itself**, the honest build is **1 doctrine dataset +
> 1 code engine + 2 UKDL rules**, not 6 prose datasets. Sealed as **SCS C85**.

---

## What ships (the Hybrid, Option C)

```
CO-00..12 + PM-01..05 + GK-00..12 + FD-00..07 + FIOS   ← PARENT SUBSTRATE (composed, never rebuilt)
│
└── D2A Engine                                          ← this build
    ├── vault/knowledge_base/duplicate_to_advantage/
    │     ├── d2a_00_duplicate_to_advantage_doctrine.md   (the paradigm + 6 components, 3 Parts >2500w)
    │     └── D2A_INDEX.md                                 (this file)
    ├── modules/duplicate_to_advantage/d2a_engine.py       (the 6-stage prospective intake pipeline)
    └── tools/test_duplicate_to_advantage.py               (V-D2A-* gates, hermetic ×3)
```

## The 6 components (architecture) and their parents

| Component | Stage | Verdict | Composes (parent, never rebuilt) |
|---|---|---|---|
| **D2A-1** Duplicate Detection Core | detect | EXTEND (prospective delta) | FD-01 classifier · `evolution_engine.merge` (Jaccard) · PM-03 Redundancy Tax · PM-02 collision |
| **D2A-2** Capability Gap Mapper | map | EXTEND | CO-12 Gap Radar · GK-09 coverage/blind-spot |
| **D2A-3** Vertical Reinforcement Gen | generate ↓ | EXTEND `evolution_engine` | `reinforce`/`specialize`/`abstract` (prospective) |
| **D2A-4** Horizontal Reinforcement Gen | generate → | EXTEND `evolution_engine`+GK-04 | `merge`/`abstract` · typed cross-family edges · FD-06 |
| **D2A-5** Portfolio Optimizer | score | EXTEND | `token_irr` reuse/compound · PM-04 auction · CO-01 WU/MTok · FD-04 |
| **D2A-6** Build Governor | govern | EXTEND FD-03 | FD-03 8-home taxonomy · one_shot · spec_gate |

## Dependency graph (consumer → provider)

- **D2A-1** consumes the sealed FAMILY_REGISTRY (CO/PM/GK/FD/FIOS/CDIO responsibilities) +
  `evolution_engine._tokens`; provides the DUPE VERDICT to D2A-2 and the whole pipeline.
- **D2A-2** consumes the DUPE VERDICT + a per-family covers table; provides the 14-dim GAP
  MAP (absent/partial/covered) to D2A-3/4.
- **D2A-3/4** consume the GAP MAP; provide ≥3 vertical + ≥3 horizontal candidates to D2A-5.
- **D2A-5** consumes the candidate pool; provides the ratio-ranked portfolio + winner to D2A-6.
- **D2A-6** consumes the winner + DUPE VERDICT + GAP MAP; provides the minimal BUILD CONTRACT
  under the 10-rule anti-inflation gate. Propose-never-build, Owner-gated.

## The vocabulary — 15 operations

`DEEPEN · CONNECT · GENERALIZE · SPECIALIZE · AUTOMATE · DETERMINIZE · EVALUATE · HARDEN ·
COMPRESS · PORT · COMPOSE · MUTATE · REPLACE · RETIRE · DO_NOT_BUILD.` Each recommendation
uses exactly one. `DO_NOT_BUILD` is always in scope — it is what the engine recommended to
its own proposal.

## The structured output

`DUPE VERDICT` (parent · coverage% · 3-axis overlap) → `REINFORCEMENT MAP` (14 dims
absent/partial/covered) → `CANDIDATE PORTFOLIO` (vertical + horizontal, 16 numeric scores,
ranked by ratio) → `RECOMMENDED ACTION` (1 operation) → `BUILD CONTRACT` (artifact · lives_in
· reinforces · not-dup · retires · eval · 10-rule anti-inflation ledger).

## Canonical worked example — "Token Budget Planner" (reproducible)

| Stage | Result |
|---|---|
| D2A-1 detects | **FD-05** at **95 %** coverage (sem 56 / func 33 / arch 100); secondaries **CO-01 + FIOS-IRR**; `is_duplicate=True` |
| D2A-2 maps | 3 covered / 4 partial / **7 absent** of 14; key gap = *budget adaptation mid-session on real novelty* |
| D2A-3 vertical | **Frontier Budget Adaptation Engine** (DEEPEN — re-price budget in real time) |
| D2A-4 horizontal | **Cross-Session Budget Learning Loop** (CONNECT FD-05×FD-07 — budget compounds across sessions) |
| D2A-5 scores | **Counterfactual Frontier Spend Simulator** wins on ratio (highest novelty + compound + frontier-savings, low complexity) |
| D2A-6 decides | **new Part in FD-05** — *not* a new dataset (coverage 95 % → deep parent → Part) |
| BUILD CONTRACT | extend FD-05 Part III with counterfactual Opus-cost simulation · operation DETERMINIZE · anti-inflation **10/10** |

Reproduce: `python -m modules.duplicate_to_advantage.d2a_engine "route the model budget,
price frontier token cost as capital, plan reuse and deterministic conversion, adapt the
session budget" --name "Token Budget Planner"`.

## V-gates (done-gate) — scorecard

`tools/test_duplicate_to_advantage.py`, hermetic ×3:

| Gate | Checks |
|---|---|
| `V-D2A-DETECTION-SEMANTIC` | duplicate proposal detected > 80 % |
| `V-D2A-GAP-MAPPED` | ≥ 8 of 14 capability dimensions mapped |
| `V-D2A-VERTICAL-GENERATED` | ≥ 3 vertical candidates, numeric scores |
| `V-D2A-HORIZONTAL-GENERATED` | ≥ 3 horizontal candidates, numeric scores |
| `V-D2A-PORTFOLIO-SCORED` | every candidate carries all 16 dimension scores |
| `V-D2A-CONTRACT-MINIMAL` | Build Governor picks Part over dataset when coverage warrants |
| `V-D2A-ANTIINFLATION` | all 10 anti-inflation rules recorded on every contract |
| `V-D2A-NO-DUPLICATE` | registry references real families; doctrine declares non-duplication |
| `V-D2A-DEPTH` | each doctrine Part > 2500 real words |
| `V-D2A-NUMERIC-BENCHMARKS` | zero adjectives-without-numbers in scoring |
| `V-D2A-FAILOPEN` | pathological input → DEFER, never a raise |
| `V-D2A-BASELINE` | FD (12/12) + FIOS (13/13) suites still green |

## UKDL sealed

- **`PR-DUPLICATE-TO-ADVANTAGE-001`** — no proposal ends in bare rejection for duplication;
  every detection activates the D2A search → gap map → scored candidates → minimal BUILD
  CONTRACT. Duplication is a search signal, not a block.
- **`T-D2A-ANTIINFLATION-VIOLATION-001`** — recommending a full dataset where a Part, rule,
  or eval would suffice is a contract violation; every new dataset must beat *a new Part, a
  new UKDL rule, a new eval, and not-building.*

## The fundamental property

> **No duplication ends in rejection.** A detected duplicate is a coordinate: it marks the
> exact edge of the non-redundant capability space. The engine stands at that edge, maps the
> gap, generates the vertical and horizontal reinforcements, scores them by value-per-cost,
> and reduces the winner to the smallest correct artifact — a Part before a dataset, a rule
> before a Part, and *do-not-build* always on the table. It proposes; the Owner promotes. It
> costs zero frontier tokens. And it obeys its own contract — which is why the D2A family is
> one doctrine and one engine, not six datasets.
