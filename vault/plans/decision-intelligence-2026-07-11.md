# Decision Review Kernel — Reality Scan Report + STOP #1 Plan

> **Proposal audited:** "Claude Power Pack Decision Intelligence Authority" (a new corpus that
> decides whether a decision is correct / necessary / proportional / reversible / sustainable
> before the stack acts).
> **Reality Scan date:** 2026-07-11 · **Author:** Claude Code (Opus 4.8) · **Gate:** STOP #1 (blocking).
> **Backup of:** the inline STOP #1 emission of this session. Nothing is built until Owner approval.

---

## 0. Mode verdict — **PLAN** (not ULTRA-PLAN)

The ROI detector fires **ULTRA-PLAN** only when the authority "altera gobernanza, criterio
institucional o contratos de decisión **sin equivalente existente**." That condition **fails**:

- **SDD-OS Parte V — DECISION OS & Engineering Governance Layer** (`vault/knowledge_base/sdd_os/sdd_os_05_decision_os_engineering_governance_layer.md`, sealed, 769 lines) already IS the decision-governance doctrine, at institutional depth. It defines the Decision Object, Decision Registry, reversibility classification, blast radius, confidence score, governance tiering, adversarial review, decision debt, fitness functions and the Engineering Governance Pipeline (`Requirement → Spec → Contracts → Invariants → Decision Review → Decision Approval → …`).
- The epistemics / evidence surface is owned by **ACIS** (founded 2026-07-11, same day). Duplication handling by **D2A**. Cost/routing by **CO-00…12**. Runtime compilation by **FIOS**. Precedent-collision by the **arch-decision** skill.

An equivalent exists for **every** conceptual capability the proposal lists. The only genuine
gap is **executable**: SDD-OS Parte V is prose with no runtime. Per the sibling precedent
(ACIS STOP #1: *"PLAN — not ULTRA-PLAN … it formalizes the promotion chain the substrate already
implements"*; FIOS STOP #1: *"FD is the doctrine, FIOS is the executable that runs it"*), this is
**PLAN**: a code execution layer + one thin Part + rules + benchmarks. Not a new prose family.

**Identity (Reality-Scan-renamed):** drop "Authority" (anti-grandiosity ban). Ship the
**Decision Review Kernel (DRK)** — the executable **Decision axis** of SDD-OS. No new narrative
identity, no acronym theatre, zero CommonWealth terminology.

---

## 1. Coverage Matrix (full — 22 proposed capabilities)

Columns: Capability · Existing System (evidence) · Coverage · Overlap · Gap · Action (D2A verb) · Verdict · Confidence.

| # | Proposed capability | Existing system (evidence) | Coverage | Gap (genuine delta) | Action | Verdict | Conf |
|---|---|---|---|---|---|---|---|
| 1 | Decision Review Kernel | arch-decision `arch_check.py` (precedent COLLISION/WARNING/CLEAR) + one_shot `compiler.py` (contract) + spec_gate `classify_tier` | PARTIAL | no unified entrypoint that instantiates a Decision Object, routes review depth, runs adversarial review, writes a record | COMPOSE+AUTOMATE | **CREATE (code)** | High |
| 2 | Falsification & Evidence System | ACIS epistemic ladder E0–E7 + `epistemic_ladder.py`; code_review Proof Triad; CO-12 (metric,source,value) | COVERED | — | DO_NOT_BUILD | Reference | High |
| 3 | Capability Placement & Boundary | D2A `d2a_engine.py` (detect→gap→govern, 15 ops, System Admission analog) | COVERED | — | DO_NOT_BUILD | Reference | High |
| 4 | Architectural Consequence / Entropy | SDD-OS Parte V (2nd/3rd-order effects, blast radius) + arch-decision | COVERED (doctrine) | scoring is prose-only, no runtime | AUTOMATE | fold → DRK engine | Med |
| 5 | Institutional Debt Ledger (multi-axis) | Cognitive Leak Taxonomy C70 (cognitive debt); SDD-OS Parte V "Decision Debt"; CO-02 violation registry; vault backlog | COVERED (doctrine) | no live decision-debt accrual | DEEPEN | fold → DRK + Part VI | Med |
| 6 | Decision Reversibility Classifier | SDD-OS Parte V Tipo A/B/C; HR-CASCADE irreversibility triggers; core.md Blast Radius | PARTIAL | no classifier function; doctrine only | DETERMINIZE | **CREATE (fn in engine)** | High |
| 7 | Evidence Burden Model | ACIS falsifier discipline; code_review Proof Triad; CO-12 Telemetry-Before-Claims | COVERED | — | DO_NOT_BUILD | Reference | High |
| 8 | Counterfactual Decision Simulator | SDD-OS Parte V "Decision Simulation Engine" (1mo–3yr); D2A "Counterfactual Frontier Spend Simulator"; FIOS `token_irr` | COVERED (doctrine) | no executable simulate() | AUTOMATE | fold → DRK engine | Med |
| 9 | Decision Precedent Registry & Memory | UKDL append-only; arch-decision `index.json`; SDD-OS "Institutional Memory Layer"; vault | COVERED | no first-class Decision Registry on disk | COMPOSE | fold → DRK registry writer | High |
| 10 | Prediction Accountability System | fd_04_prover (`portability_proven`); liveness D1; CO-12 calibration; SDD-OS "consecuencias previstas vs no previstas" (FIELDS only) | **ABSENT** | no engine scores a decision's prediction vs realized outcome | EVALUATE | **CREATE (Part VI + prover)** | High |
| 11 | Attribution model (reasoning vs execution vs luck vs context) | ACIS causal effect-separation (for claims, not decisions) | **ABSENT** | genuinely new for decisions | GENERALIZE | **CREATE (Part VI section)** | High |
| 12 | Decision Quality Evaluator | code_review severity/verdict; output_contracts OQS; UQF | COVERED | decision-quality-vs-outcome-quality separation absent | DEEPEN | fold → Part VI | Med |
| 13 | Risk-Based Review Router (L0–Ln) | SDD-OS Parte V Governance Tiering A–E + Tier 0–3; cost_collapse `route`; spec_gate `classify_tier`; CO-03; core.md Blast Radius | COVERED | no decision-review-depth router (vs task-tier router) | SPECIALIZE | fold → DRK router | High |
| 14 | Governance & Escalation Layer | one_shot `escalation.py` (HR-ONESHOT-003, OD7); owner_queue; HR framework | COVERED | — | DO_NOT_BUILD | Reference | High |
| 15 | Runtime Prompt Compiler | FIOS `session_compiler.py`; jit_skill_loader; GK-06 minimal-context pack | COVERED | DRK invocation is one caller of it | DO_NOT_BUILD | Reference | High |
| 16 | Self-Evolution System | FIOS `evolution_engine.py`; FD-07 flywheel; FD-06 writeback | COVERED | — | DO_NOT_BUILD | Reference | High |
| 17 | Quality-type separation (decision/spec/impl/operational/outcome/learning) | scattered across code_review/spec_gate/output_contracts/liveness | PARTIAL | never formalized as one model | GENERALIZE | **CREATE (Part VI section)** | Med |
| 18 | Irreducible tensions (optionality↔simplicity, reuse↔coupling, …) | E10 Elixir-first tradeoffs; scattered | PARTIAL | no formal tension catalog | DEEPEN | fold → Part VI section | Med |
| 19 | Adaptive temporal horizons | SDD-OS Parte V Simulation (1mo–3yr) | COVERED (doctrine) | not horizon-by-decision-type | SPECIALIZE | fold → DRK engine field | Low |
| 20 | Negative Knowledge Engine | FD DISCARD; UKDL Traps (T-*); Leak Taxonomy; SDD-OS "Anti-Pattern Registry"; ACIS retired-doctrine | COVERED | — | DO_NOT_BUILD | Reference | High |
| 21 | Unknown-Unknown Generator | FIOS II-1 (thin-extend); FD-02 | COVERED | — | DO_NOT_BUILD | Reference | Med |
| 22 | Benchmarks / adversarial arena | fd_04_prover; test suites; CDIO scorer | PARTIAL (framework) | no decision-scenario suite | EVALUATE | **CREATE (V-gates)** | High |

**Tally:** 10 COVERED (DO_NOT_BUILD/Reference) · 8 fold-into-engine-or-Part (EXTEND) · **4 genuine CREATE** (the DRK engine #1/#6/#9 mechanics, Prediction-Accountability+Attribution #10/#11/#17, review-router #13, benchmarks #22). **~80 % already covered or thin-extension** — identical ratio to FD (81 %), D2A (0/6 pure-new), FIOS (5/17 covered), CO (7/9 covered).

---

## 2. System Admission Test — applied to each candidate "system"

Only **one** organism passes as new independent code; everything else is a Part, a field, or a reference.

| Candidate | Unique problem? | Can't live in existing dataset? | Verdict |
|---|---|---|---|
| **Decision Review Kernel (`decision_kernel.py`)** | Yes — no executable runs SDD-OS Parte V | Correct: doctrine ≠ runtime (FIOS precedent) | **ADMIT (code engine)** |
| **Prediction Accountability + Attribution** | Yes — nothing scores decision predictions vs outcomes | Best home = a new **SDD-OS Parte VI** (extends the sealed family) | **ADMIT (1 Part, Owner picks Part vs section)** |
| Decision doctrine corpus (the proposed "Authority") | No — SDD-OS Parte V is it | Would duplicate a sealed dataset → `T-D2A-ANTIINFLATION-VIOLATION-001` | **REJECT (DO_NOT_BUILD)** |
| Evidence/Falsification, Placement, Router, Escalation, Compiler, Evolution, Negative-Knowledge, Unknown-Unknown | No | Owned by ACIS / D2A / cost_collapse / one_shot / FIOS / FD | **REJECT (Reference)** |

---

## 3. Approved minimal architecture (what actually ships)

Mirrors D2A ("1 doctrine + 1 engine + 2 UKDL") and FIOS ("code where the delta is code, one thin doctrine, zero new prose families").

```
SDD-OS Parte V (Decision OS doctrine)  +  ACIS + D2A + CO + FIOS + one_shot + spec_gate + arch-decision + owner_queue   ← PARENT SUBSTRATE (composed, never rebuilt)
│
└── Decision Review Kernel (DRK)                                    ← this build (the executable Decision axis)
    ├── modules/decision_review/decision_kernel.py                 review_decision(DecisionObject) → Verdict + DecisionRecord
    │     composes: arch_check (precedent) · one_shot.compiler (contract) · spec_gate.classify_tier (tier)
    │     · d2a_engine (build/placement) · acis.epistemic_ladder (evidence level) · cost_collapse.route (review depth)
    │     · reversibility classifier (Tipo A/B/C) · DCS + DBR compute · adversarial pass · owner_queue (escalate)
    ├── modules/decision_review/decision_record.py                 canonical DecisionObject/DecisionRecord + Registry writer
    ├── modules/decision_review/accountability.py                  records prediction, scores vs outcome (rides fd_04_prover + liveness)
    ├── vault/knowledge_base/sdd_os/sdd_os_06_decision_accountability_attribution.md   Parte VI (the ONE new Part: #10/#11/#17)
    ├── vault/knowledge_base/decision_review/DRK_INDEX.md          doctrine index (pointer, not a re-narration of Parte V)
    └── tools/test_decision_review.py                              V-DRK-* gates + FASE-5 decision scenarios, hermetic ×3
```

**Verdict ontology (composes SDD-OS approval pipeline + explicit set):** `REJECT · REFRAME ·
REQUEST-EVIDENCE · RUN-EXPERIMENT · DEFER · KEEP-LOCAL · CONSOLIDATE · REMOVE ·
APPROVE-WITH-CONDITIONS · APPROVE`. Authority: **block only when irreversible (Tipo C) AND
evidence insufficient (ACIS < E3)**; recommend in every other case; Owner override always
registered (`PR-DECISION-AUTHORITY-LIMITS-001`). Fail-open (pathological input → DEFER, never raise).

---

## 4. Build order · micro-commits · gates

1. `decision_record.py` (DecisionObject + Registry writer) → commit `feat(drk): canonical decision record + registry`
2. reversibility classifier + DCS/DBR compute (in `decision_kernel.py`) → commit
3. `decision_kernel.py` composition wiring (arch/one_shot/spec_gate/d2a/acis/cost_collapse/owner_queue) → commit
4. `accountability.py` (prediction→outcome scoring) → commit
5. SDD-OS **Parte VI** doctrine (`sdd_os_06_…`) + `DRK_INDEX.md` → commit
6. `tools/test_decision_review.py` V-gates + FASE-5 scenarios → commit
7. UKDL append (2 rules) → commit ; wire spec_gate/skill_router trigger → commit

**Per-phase gates:** each step ends with `python tools/test_decision_review.py` PASS ×3 hermetic +
`V-BASELINE` (FD 12/12, FIOS 13/13, D2A, CO suites still green). Pathspec-scoped commits only.
`NEVER git add -A`. Push at close → `REMOTE_DELTA = 0 0`.

**FASE-5 mandatory scenarios (benchmarks):** best-answer-is-build-nothing · request-evidence ·
platform-correct · platform-incorrect · temporary-duplication-acceptable · long-term→over-arch ·
short-term→destroys-optionality · ambiguous-incomplete-info · adversarial-abstain ·
precedent-reversal · Big-Tech-is-a-bad-reference. Calibration: record predictions, measure error,
separate judgment-error from execution-error, test the three biases (never-reject / always-reject /
always-platform).

---

## 5. Contamination Audit plan (CommonWealth quarantine)

Continuous grep-gate before/during/after: reject any name-collision, imported taxonomy, commercial
metaphor (ecommerce/store/brand/growth), or renamed-concept from CW Ops. The reference is studied
only for **abstract** quality attributes (depth/density/interconnection), never content. "Decision
Review Kernel", "Decision Object", "DCS", "DBR", "Governance Tier" are all pre-existing PP/SDD-OS
terms — native, not imported. No CW string appears in any artifact.

---

## 6. Completion criteria

DRK engine runs + writes a DecisionRecord · reversibility+DCS+DBR computed · verdict ontology live ·
review-depth routed by Governance Tier · adversarial pass fires · Parte VI depth ≥2500 words/Part at
reference density · Prediction Accountability records+scores · benchmarks green (all 11 scenarios) ·
3-bias calibration present · authority limits + override registered · Contamination Audit clean ·
Residual Capability Audit emitted · V-BASELINE green · REMOTE_DELTA 0 0.

## 7. Residual Capability Audit (capabilities NOT built — pre-classified)

- **duplicate (10):** Falsification/Evidence, Capability-Placement, Evidence-Burden, Governance/
  Escalation, Runtime-Compiler, Self-Evolution, Negative-Knowledge, Unknown-Unknown, Precedent-
  Registry-store, Decision-Quality-Evaluator → owned by ACIS/D2A/CO/one_shot/FIOS/FD/UKDL.
- **folded (8):** consequence/entropy, debt-ledger, counterfactual-sim, horizons, tensions, quality-
  type-separation, review-router, decision-quality → Parts/fields/sections of DRK engine or Parte VI.
- **future extension:** Decision Court multi-role simulation as a live agent panel (SDD-OS Parte V
  §15 doctrine exists; a runtime panel is a later EXTEND, gated on demand).

## 8. UKDL to append at close

- `PR-DECISION-AUTHORITY-LIMITS-001` — DRK blocks only on irreversible + insufficient-evidence;
  recommends otherwise; Owner override always registered; DRK audits its own errors as rigorously
  as others'.
- `T-DECISION-AUTHORITY-CAPTURE-001` — never-reject = theatre; always-reject = a block;
  always-platform = complexity bias. Calibrating against all three is part of the done-gate.

---

## 9. OWNER OVERRIDE REGISTER (STOP #1 decision, 2026-07-11)

**Recommendation issued:** minimal (DRK engine + 1 Part + rules + benchmarks; DO_NOT_BUILD a prose corpus).
**Owner decision:** **Build fuller corpus** · Prediction-Accountability home = **SDD-OS Parte VI**.
**Override status:** REGISTERED (per `PR-DECISION-AUTHORITY-LIMITS-001` — Owner may override; recorded, not silently executed).

**Reconciliation (how the fuller build stays honest, not an anti-inflation violation):**
SDD-OS Parte V is a **shallow enumeration** — it *names* 30 decision concepts in 1–3 line
declaratives (e.g. "Decision Blast Radius. ¿Qué podría afectar? Código. Usuarios. …") with **no
mechanism, no contract, no ontology, no failure modes, no adversarial cases, no executable**. The
fuller corpus is therefore admissible as a genuine **DEEPEN** (D2A verb): each dataset takes one
Parte-V concept-cluster to full reference density (≥2500 real words/Part, mechanism + object +
invariants + failure modes + adversarial cases + integration), **cross-references** ACIS/D2A/CO/FIOS
for the surfaces they own (never re-narrates them), and is backed by the executable kernel. This
converts the enumeration into an operating discipline — the DEEPEN operation, not duplication.
**Binding constraint:** any Part that merely restates Parte V or an ACIS/D2A/CO/FIOS dataset without
adding mechanism is a `T-D2A-ANTIINFLATION-VIOLATION-001` and is dropped at the done-gate.

## 10. APPROVED FULLER ARCHITECTURE — the DRK corpus (Decision axis)

```
SDD-OS Parte V (shallow decision enumeration) + ACIS + D2A + CO + FIOS + one_shot + owner_queue   ← PARENT SUBSTRATE (DEEPENed / cross-ref'd, never re-narrated)
│
└── DRK — Decision Review Kernel corpus (the executable + deep Decision axis)
    ├── DOCTRINE (vault/knowledge_base/decision_review/)
    │   ├── DRK_INDEX.md                         master index + family tree + coverage cross-ref
    │   ├── drk_00_foundations_canonical_objects.md   ontology · Decision Object/Record · taxonomy · verdict ontology · evidence/confidence/risk models · review-tier L0–Ln
    │   ├── drk_01_review_kernel_verdict_engine.md     review pipeline · composition contracts · adversarial pass · authority limits (block-gate)
    │   ├── drk_02_reversibility_blast_radius_entropy.md   Tipo A/B/C mechanism · DBR compute · 2nd/3rd-order · architectural entropy
    │   ├── drk_03_evidence_burden_confidence.md       burden-by-reversibility · confidence calibration (cross-ref ACIS ladder, not re-narrate)
    │   ├── drk_04_counterfactual_simulation_horizons.md   simulate 1mo–3yr by decision type · opportunity cost · strategic ROI
    │   ├── drk_05_institutional_debt_memory.md        multi-axis decision debt · precedent registry · decision genome · institutional memory (cross-ref Leak Taxonomy C70)
    │   ├── drk_06_tensions_quality_separation.md      irreducible tensions · decision/spec/impl/operational/outcome/learning quality separation
    │   └── drk_07_governance_evolution_authority.md   authority limits · override protocol · anti-capture · 3-bias calibration · self-evolution/recalibration
    │
    ├── SDD-OS Parte VI (Owner-chosen home for the ONE genuinely-new concept)
    │   └── vault/knowledge_base/sdd_os/sdd_os_06_decision_accountability_attribution.md   prediction→outcome scoring · reasoning vs execution vs luck vs context
    │
    ├── EXECUTABLE (modules/decision_review/)
    │   ├── decision_record.py     canonical DecisionObject/DecisionRecord + Registry writer
    │   ├── decision_kernel.py      review_decision() — composes arch_check·one_shot·spec_gate·d2a·acis·cost_collapse·owner_queue; reversibility+DCS+DBR; verdict ontology; fail-open
    │   └── accountability.py       records prediction, scores vs outcome (rides fd_04_prover + liveness + CO-12)
    │
    └── EVALUATION (tools/test_decision_review.py)   V-DRK-* gates · 11 FASE-5 scenarios · 3-bias calibration · V-BASELINE · hermetic ×3
```

**Build order (dependency):** DRK-00 (foundations) → decision_record.py → drk_01 + decision_kernel.py
→ drk_02/03/04 → drk_05/06 → Parte VI + accountability.py → drk_07 (governance) → benchmarks → UKDL → wire.
**Continuity:** `RESUMPTION_FILE.md` at repo root updated after every sealed unit; DRK_INDEX is the coherence anchor (dataset count must match). Depth gate `V-DRK-DEPTH` ≥2500 real words/Part.
**Delegation (per [[feedback_dataset_family_build_delegate_wordfloor]]):** I author DRK-00 + DRK-01 as depth exemplars; DRK-02..07 delegated to subagents (Agent SOLO, ≤2 parallel on Windows, overshoot+self-verify word-floor), each verified + pathspec-committed in batches.
