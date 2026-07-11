# Decision Review Kernel — Master Index (DRK)

> Where **CO-00…12** governs a session's *cost*, **ACIS** the *epistemic status* of a claim,
> **D2A** what happens when the stack is asked to build something that *already exists*, **FIOS**
> the *execution* of a frontier session, and **SDD-OS** the *specification* a build obeys — the
> **Decision Review Kernel (DRK)** governs one thing none of them operationalizes: **whether a
> proposed decision is correct, necessary, proportional, reversible, and evidenced *before* the
> stack acts on it — and whether, in hindsight, the reasoning that produced it was actually sound.**
>
> **Root law (`DRK-00`):** *A decision is an engineering asset, not a side effect. No decision of
> consequence is acted on unauthenticated (unrecorded, unclassified for reversibility, unpriced for
> blast radius, unmatched against precedent) and no decision is judged by its outcome alone —
> reasoning quality and outcome quality are separate ledgers.*
>
> **Mode verdict (STOP #1, Reality Scan, 2026-07-11):** PLAN, then **Owner-overridden to a fuller
> corpus** (register: `vault/plans/decision-intelligence-2026-07-11.md` §9). DRK alters no
> foundational architecture; it **DEEPENs** the shallow SDD-OS Parte V decision enumeration into an
> operating discipline and ships the executable that Parte V never had. Backup + full coverage
> matrix + override reconciliation: the plan file above.

---

## The honest position of this family (why it is a DEEPEN, not a duplication)

SDD-OS **Parte V (Decision OS)** already *names* the decision-governance concepts — Decision Object,
reversibility Tipo A/B/C, blast radius, confidence score, governance tiering, adversarial review,
decision debt, fitness functions. It names them in **1–3 line declaratives with no mechanism, no
canonical object schema, no failure modes, and no executable.** DRK does three things Parte V does
not: (1) it gives each concept a **mechanism** at reference density; (2) it ships the **runtime**
that instantiates and records a decision; (3) it adds the **one genuinely-absent concept** —
prediction accountability and causal attribution of decision quality — as **SDD-OS Parte VI**.

Every covered surface is **cross-referenced, never re-narrated** (GK-00 "one system, no parallels"):
evidence levels → **ACIS** epistemic ladder; capability-placement of a "should we build X" →
**D2A** engine; cost/model routing → **CO-03**; runtime prompt compilation → **FIOS**
`session_compiler`; escalation queue → **owner_queue**; task-tier → **spec_gate** `classify_tier`;
precedent-collision → the **arch-decision** skill. DRK composes these; it forks none.

## Family tree (what ships)

```
SDD-OS Parte V (enumeration) + ACIS + D2A + CO + FIOS + one_shot + owner_queue + arch-decision   ← PARENT SUBSTRATE (DEEPENed / composed, never re-narrated)
│
└── DRK — Decision Review Kernel (the Decision axis)
    │
    ├── FOUNDATIONS
    │   └── DRK-00  Foundations & Canonical Objects      the Decision Object/Record · taxonomy · verdict ontology · evidence/confidence/risk models · review-tier L0–Ln
    │
    ├── THE KERNEL
    │   └── DRK-01  Review Kernel & Verdict Engine        review pipeline · composition contracts · adversarial pass · authority block-gate
    │
    ├── THE MODELS (DEEPEN of Parte V clusters)
    │   ├── DRK-02  Reversibility · Blast Radius · Entropy   Tipo A/B/C mechanism · DBR compute · 2nd/3rd-order · architectural entropy
    │   ├── DRK-03  Evidence Burden & Confidence            burden-by-reversibility · calibration (cross-ref ACIS ladder)
    │   ├── DRK-04  Counterfactual Simulation & Horizons    simulate 1mo–3yr by decision type · opportunity cost · strategic ROI
    │   ├── DRK-05  Institutional Debt & Decision Memory     multi-axis decision debt · precedent registry · genome · institutional memory
    │   └── DRK-06  Tensions & Quality-Type Separation       irreducible tensions · decision/spec/impl/operational/outcome/learning quality
    │
    ├── ACCOUNTABILITY (Owner-chosen home = the SDD-OS family)
    │   └── SDD-OS Parte VI  Decision Accountability & Attribution   prediction→outcome scoring · reasoning vs execution vs luck vs context
    │
    └── GOVERNANCE OF THE AUTHORITY
        └── DRK-07  Governance · Evolution · Authority Limits   override protocol · anti-capture · 3-bias calibration · self-evolution
```

## Coverage cross-reference (the 22 proposed capabilities → home)

| Home | Capabilities absorbed |
|---|---|
| **DRK-00** | Decision Review Kernel object surface · risk-based review router (L0–Ln) · verdict ontology |
| **DRK-01** | Decision Review Kernel pipeline · adversarial review · decision quality evaluator (reasoning side) |
| **DRK-02** | reversibility classifier · architectural consequence/entropy · blast radius |
| **DRK-03** | evidence burden model · confidence (cross-ref ACIS falsification/evidence) |
| **DRK-04** | counterfactual simulator · adaptive temporal horizons · opportunity cost |
| **DRK-05** | institutional debt ledger (multi-axis) · precedent registry & memory · negative knowledge (decision anti-patterns) |
| **DRK-06** | irreducible tensions · quality-type separation |
| **SDD-OS VI** | prediction accountability · attribution model |
| **DRK-07** | governance & escalation (cross-ref one_shot/owner_queue) · self-evolution (cross-ref FIOS evolution_engine) · authority limits |
| **Reference (DO_NOT_BUILD)** | falsification/evidence → ACIS · capability placement → D2A · runtime compiler → FIOS · precedent-collision → arch-decision · unknown-unknown → FIOS II-1/FD-02 |

## Executable (the delta Parte V never had)

| Module | Contract |
|---|---|
| `modules/decision_review/decision_record.py` | canonical `DecisionObject` / `DecisionRecord` + append-only Registry writer (fail-open) |
| `modules/decision_review/decision_kernel.py` | `review_decision(obj) → Verdict` — composes arch_check · one_shot.compiler · spec_gate.classify_tier · d2a_engine · acis.epistemic_ladder · cost_collapse.route · owner_queue; computes reversibility-tier + DCS + DBR; **blocks only when Tipo-C irreversible AND ACIS < E3**; recommends otherwise; fail-open (pathological → DEFER) |
| `modules/decision_review/accountability.py` | records the decision's prediction, scores it against the realized outcome; separates reasoning-error from execution-error/luck/context-change; feeds CO-12 |

## Verdict ontology (composes SDD-OS approval pipeline + explicit set)

`REJECT · REFRAME · REQUEST-EVIDENCE · RUN-EXPERIMENT · DEFER · KEEP-LOCAL · CONSOLIDATE · REMOVE ·
APPROVE-WITH-CONDITIONS · APPROVE`. The authority **blocks** only on `Tipo-C irreversible ∧ evidence <
E3`; everywhere else it **recommends**. Every block or approval writes a DecisionRecord; every Owner
override is recorded (`PR-DECISION-AUTHORITY-LIMITS-001`).

## V-gates (FASE 4 done-gate) — planned scorecard

`tools/test_decision_review.py`, hermetic ×3:
`V-DRK-REALITY-SCAN` (declares COVERED set + real parents) · `V-DRK-RECORD-CANONICAL` (every review
writes a schema-valid DecisionRecord) · `V-DRK-REVERSIBILITY` (Tipo A/B/C assigned + rigor scales) ·
`V-DRK-BLOCK-GATE` (blocks iff Tipo-C ∧ <E3; never otherwise) · `V-DRK-VERDICT-ONTOLOGY` (all 10
verdicts reachable) · `V-DRK-ACCOUNTABILITY` (prediction recorded + scored vs outcome) ·
`V-DRK-ATTRIBUTION` (reasoning/execution/luck/context separated) · `V-DRK-3-BIAS` (never-reject /
always-reject / always-platform each caught by a scenario) · `V-DRK-DEPTH` (≥2500 real words/Part) ·
`V-DRK-NO-CODE-IN-DOCTRINE` · `V-DRK-CROSS-REF-NOT-RENARRATE` (each covered surface is linked, not
re-explained) · `V-DRK-FAILOPEN` (pathological input → DEFER) · `V-DRK-BASELINE` (ACIS/D2A/FIOS/FD/CO
suites still green).

## Build ledger (updated after every sealed unit — coherence anchor)

| Unit | Status | Words / evidence |
|---|---|---|
| DRK_INDEX.md | ✅ written | this file |
| DRK-00 Foundations | ✅ written | ~2800w · 3 Parts · 0 code fences · canonical objects fixed |
| DRK-01 Review Kernel | ✅ written | ~2600w · 3 Parts · 9-stage sieve · 7 composition contracts · block-gate |
| DRK-02 Reversibility/Blast/Entropy | ✅ written | 4186w · Tipo A/B/C classifier · DBR · entropy ledger · verified (0 fence/0 contam) |
| DRK-03 Evidence/Confidence | ✅ written | 3447w · burden-by-reversibility · DCS derivation · verified (0 fence/0 contam) |
| DRK-04 Counterfactual/Horizons | ✅ written | 4147w · adaptive horizons · 3-trajectory counterfactual · verified (0 fence/0 contam) |
| DRK-05 Debt/Memory | ✅ written | 4405w · 6-axis decision debt · genome · precedent-reversal · verified (0 fence/0 contam) |
| DRK-06 Tensions/Quality | ✅ written | ~2500w · 8-tension catalog · 6-way quality separation (I author) |
| SDD-OS Parte VI Accountability | ✅ written | ~2500w · two-ledger · 4-source attribution · calibration (I author) |
| DRK-07 Governance/Evolution | ✅ written | ~2600w · block-narrow constitution · 3-bias · propose-never-apply (I author) |
| decision_record.py | ✅ built | canonical objects + append-only fail-open Registry |
| decision_kernel.py | ✅ built | 9-stage sieve · reversibility/DBR/DCS · verdict precedence · block-gate · `live=True` resolves real providers |
| accountability.py | ✅ built | prediction scoring · 4-source attribution · 3-bias calibration |
| providers.py | ✅ **wired live** | 6 adapters (arch-decision · d2a_engine · epistemic_ladder · spec_gate · cost_collapse · owner_queue), each fail-open + budgeted. Signatures verified at source first (HR-PREMISE-001); **3 asserted premises were false** |
| proactive_scanner.py | ✅ **live** | 4 evidence-mandatory detectors (D1 liveness · D3 recall-ROI · D4 residuals · unrecorded decisions); daily task `PP-DRKScan`; output → `vault/audits/drk_proactive_*.md` + OWNER_QUEUE |
| tools/register_drk_scan.ps1 | ✅ shipped | idempotent per-user Scheduled Task (Owner runs once) |
| tools/test_decision_review.py | ✅ green | **18/18 hermetic ×3** · V-BASELINE (strategic-gaps 21/21, D2A 22/22, FIOS 48/48, FD 12/12) green |
| D1 Liveness ledger | ✅ LIVE | `drk-kernel` + `drk-proactive` rows added; both probe **LIVE** (earned: a real Decision Record + a real audit report exist) |
| UKDL (4 rules) | ✅ sealed | PR-DECISION-AUTHORITY-LIMITS-001 · T-DECISION-AUTHORITY-CAPTURE-001 · T-DRK-PROACTIVE-NOISE-001 · T-DRK-PRECEDENT-LENGTH-BIAS-001 |
| `DEC-0001` | ✅ recorded | the wiring decision, reviewed by the kernel itself: APPROVE-WITH-CONDITIONS · Tipo-B · L3 · DCS 92 |

## The self-review that found the bug

The wiring decision was submitted to the kernel as its first real input. It returned **REJECT**
(`precedent-collision-on-veto`). The collision was false: `arch_check`'s score rises with input
LENGTH, and 86% of its index is veto-class, so feeding it a long statement+problem+rationale blob
made every substantial decision "collide with a Hard Rule". That is the always-reject bias of
`T-DECISION-AUTHORITY-CAPTURE-001` arriving through an adapter rather than a doctrine. Fixed
(statement-only input; `on_veto` mirrors arch_check's own COLLISION condition), gated
(`V-DRK-NO-LENGTH-BIAS`), sealed (`T-DRK-PRECEDENT-LENGTH-BIAS-001`). The corrected review returns
APPROVE-WITH-CONDITIONS with the precedent cited as a WARNING — surfaced, not vetoing. **A decision
authority that cannot survive its own review is not an authority.**

## The fundamental property

> **Authenticate the decision, then judge the reasoning — not just the result.** A decision of
> consequence is recorded, classified for reversibility, priced for blast radius, matched against
> precedent, and held to an evidence burden proportional to its irreversibility — before the stack
> acts. Afterward, its predicted consequences are scored against reality, and a good outcome from
> bad reasoning is not counted as a win. The authority blocks only what is irreversible and
> under-evidenced; everywhere else it recommends and the Owner decides, every override recorded. It
> composes the sealed families and forks none; it is files on disk and a function that reads them —
> no new brain, no parallel accountant, no magic promised.
