# DFP — Canonical Ontology

> **Binding.** Read before authoring any DFP Part or writing any `modules/dataset_first/` code.
> Every term below has exactly one meaning inside this family. A Part that redefines a term
> here, or invents a synonym for it, is rejected and rewritten.
>
> Founded 2026-07-12. Architecture approved at STOP #1:
> `vault/plans/dataset-first-protocol-2026-07-12.md`.

---

## 0. What this family is, and what it refuses to be

### 0.1 The thesis

> **Never build permanent infrastructure when the institutional science that must govern it
> does not yet exist.**

The Dataset First Protocol governs one question no other Power Pack system answers:
**when must a body of knowledge be built *before* an implementation, and when is demanding
that knowledge pure bureaucracy?**

Both halves of that sentence are load-bearing. A protocol that always demands a corpus is as
destructive as one that never does — it becomes a tax the Owner routes around, and a rule
routed around is not a rule. The discipline earns its authority only by being *calibrated*
(DFP-05), never by being *asserted*.

### 0.2 The parent substrate — composed, never re-narrated

DFP is a **thin family over a thick substrate**. It owns three things and cross-references
everything else. This table is the non-duplication contract; it is enforced by
`V-DFP-CROSS-REF-NOT-RENARRATE` and by the D2A verdicts in `DFP_D2A_VERDICTS.md`.

| Capability | Owner (never forked by DFP) |
|---|---|
| Is a proposed decision sound, reversible, evidenced, proportional? | **DRK** (`modules/decision_review`) |
| What is the epistemic level of a claim (E0–E7)? | **ACIS** (`epistemic_ladder`) |
| Does this task need a spec/PRD before coding? Tier 0–3. | **`modules/spec_gate`** — sealed as **HR-SPEC-001** |
| Is this proposal a duplicate of something already built? | **D2A** (`modules/duplicate_to_advantage`) |
| Where does knowledge live, and how is it navigated? | **graphify** (GK-00…12) |
| How does a frontier delta become a portable asset? | **FD-00…07** |
| What does a session cost, and how is it routed? | **CO-00…12** |
| Is the executable reality actually verified? | **SQI** |
| What must never happen again? | **`modules/hard_rules`** |

**DFP owns exactly three things:**

1. **The corpus-versus-spec distinction** (DFP-00). `spec_gate` already forbids executing a
   Tier ≥ 2 task without a PRD. DFP asks the question one level up: *when is a spec itself
   insufficient, and a governing **corpus** required?*
2. **The Knowledge Infrastructure lifecycle** (DFP-02). The Power Pack has shipped ten-plus
   dataset families with no governing discipline for **how** a corpus is built, reviewed,
   certified, or frozen. Each family re-invents its own rubric and lands an order of
   magnitude apart in density. That hole is real, evidenced, and unowned.
3. **The calibration science** (DFP-05). Nothing in the repo measures whether
   knowledge-first *paid off* against direct implementation. Without that measurement, this
   family is dogma.

### 0.3 The refusals (what DFP will not build)

- **No second court.** DRK-01 is already a review kernel with an adversarial pass, a
  ten-verdict ontology, and a block-gate authority. A "Dataset Necessity Court" is a parallel
  authority, forbidden by `T-DECISION-AUTHORITY-CAPTURE-001`.
- **No second detector.** `spec_gate.classify_tier` already classifies a free-text task and
  is already reachable from the `UserPromptSubmit` JIT loader. DFP extends it; it does not
  build a rival.
- **No second duplicate-detector.** D2A owns that surface.
- **No second knowledge graph.** graphify owns that surface.

---

## 1. Canonical objects

Six objects. Each has exactly one producer and at least one consumer. An object defined here
with no producer is **dead by starvation** and must be deleted, not documented.

### 1.1 `ProjectClassification`

The output of classifying a *proposed unit of work* — the question "what kind of thing is
this, before we decide how to start it".

| field | type | meaning |
|---|---|---|
| `project_class` | `ProjectClass` | one of the four values in §2.1 |
| `tier` | `int` 0–3 | delegated verbatim to `spec_gate.classify_tier` — never re-derived |
| `signals` | `list[Signal]` | the evidence that produced the class (§3) |
| `rationale` | `str` | why this class, in one sentence, naming the deciding signal |
| `confidence` | `int` 0–100 | how strongly the signals separate this class from the runner-up |

Producer: `modules/dataset_first/classifier.py`. Consumer: the DRK kernel (as a provider),
the `spec_gate` extension, and `DatasetNecessityRecord`.

### 1.2 `KnowledgeSufficiencyVerdict`

The output of asking "is the knowledge we already hold sufficient to *govern* this build".
This is the family's central judgment.

| field | type | meaning |
|---|---|---|
| `sufficient` | `bool` | whether existing knowledge can govern the implementation |
| `score` | `int` 0–100 | the aggregate sufficiency score |
| `dimensions` | `dict[str, int]` | the ten dimensions of §4, each scored 0–10 |
| `missing` | `list[KnowledgeType]` | which *kinds* of knowledge (§2.2) are absent |
| `existing_assets` | `list[str]` | the corpora/specs already found that count toward sufficiency |
| `acis_ceiling` | `int` | the highest ACIS level (E0–E7) the existing assets reach — **read from ACIS, never assigned here** |
| `verdict` | `ProjectClass` | the recommended class (§2.1) |

Producer: `modules/dataset_first/knowledge_sufficiency.py`. Consumer: DRK (provider),
`DatasetNecessityRecord`, `ProtocolCalibrationRecord`.

**Invariant:** `acis_ceiling` is *always* obtained by calling ACIS. DFP never assigns an
epistemic level itself. A DFP that grades its own evidence is the No-Autopromotion violation
ACIS exists to prevent.

### 1.3 `DatasetNecessityRecord`

The append-only, immutable record of a single necessity decision. This is the raw material
of the calibration science — without it, DFP-05 has nothing to measure and the family is
dogma by construction.

| field | type | meaning |
|---|---|---|
| `id` | `str` | `DFP-NNNN`, monotonic |
| `subject` | `str` | what was proposed |
| `classification` | `ProjectClassification` | §1.1 |
| `sufficiency` | `KnowledgeSufficiencyVerdict` | §1.2 |
| `decided` | `ProjectClass` | what was actually done — **may differ from the verdict** |
| `override` | `Override \| None` | if `decided != verdict.verdict`: who, why, when |
| `prediction` | `Prediction` | what the protocol predicts will happen (§1.6) — recorded **before** the outcome is known |
| `outcome` | `Outcome \| None` | filled in later, by measurement, never by recollection |

Producer: `modules/dataset_first/necessity_record.py` (append-only, fail-open).
Consumer: DFP-05's calibrator.

**Invariant (the falsifiability contract):** a record without a `prediction` is inadmissible
as calibration evidence. A protocol that only records its decisions, and not what it expected
those decisions to produce, cannot be proven wrong — and a discipline that cannot be proven
wrong is a belief, not a science.

### 1.4 `KnowledgeInfrastructureManifest`

The declaration a corpus makes about itself when Knowledge Infrastructure Mode is active
(DFP-02). It is what turns "we are writing datasets" into a governed lifecycle with a
terminating condition.

| field | type | meaning |
|---|---|---|
| `family` | `str` | the family id (e.g. `DFP`, `SQI`, `DRK`) |
| `stage` | `KnowledgeStage` | one of the eight stages in §2.3 |
| `parts_planned` | `int` | declared up front; a moving denominator is a gaming signal |
| `parts_sealed` | `int` | Parts that passed the quality rubric |
| `fabrication_standard` | `FabricationStandard` | words/Part band, Parts/dataset band, the rejection criteria |
| `certification` | `Certification \| None` | set only at stage `CERTIFIED` |
| `frozen_at` | `str \| None` | ISO timestamp; a frozen corpus is immutable except by amendment |
| `siblings` | `list[str]` | the families this one composes — the non-duplication declaration |

Producer: `modules/dataset_first/manifest.py`. Consumer: the DFP-02 gates, the D1 Liveness
Ledger, and `CompoundEffect`.

### 1.5 `CompoundEffect`

The measured (never asserted) statement that a family made its siblings more valuable.

| field | type | meaning |
|---|---|---|
| `family` | `str` | the subject |
| `parents_composed` | `list[str]` | what it reused instead of rebuilding |
| `capabilities_enabled` | `list[str]` | what became possible that was not before |
| `duplication_avoided` | `int` | count of D2A `DO_NOT_BUILD` / `dataset_part` verdicts it honored |
| `reuse_events` | `int` | measured times a sibling read this corpus — **measured, from the graph, not claimed** |

Producer: `modules/dataset_first/compound.py`, reading graphify edges and D2A verdicts.
Consumer: DFP-05.

**Invariant:** `reuse_events` is a *measurement*. A family that declares compound value
without a reuse count has written marketing copy, not a metric.

### 1.6 `ProtocolCalibrationRecord`

The output of DFP-05: the protocol grading itself against reality.

| field | type | meaning |
|---|---|---|
| `window` | `str` | the period or the set of records considered |
| `n_dataset_first` | `int` | records decided `DATASET_FIRST_MANDATORY` |
| `n_direct` | `int` | records decided `DIRECT_IMPLEMENTATION` |
| `false_positive_rate` | `float` | corpora demanded that measurably did not pay off |
| `false_negative_rate` | `float` | direct builds that measurably needed the corpus they skipped |
| `threshold_delta` | `dict[str, int]` | the recommended change to the §4 thresholds |
| `retirement_signal` | `bool` | **True ⇒ the protocol recommends its own retirement** |

Producer: `modules/dataset_first/calibrator.py`. Consumer: the Owner, via OWNER_QUEUE.

**Invariant (the retirement clause):** `retirement_signal` must be *reachable*. If no
possible evidence could ever set it True, the protocol is unfalsifiable and must be deleted.
`V-DFP-RETIREMENT-REACHABLE` asserts a synthetic evidence set that flips it.

---

## 2. Taxonomies

### 2.1 `ProjectClass` — four values, closed

| value | meaning | the deciding question |
|---|---|---|
| `DIRECT_IMPLEMENTATION` | Build now. Existing knowledge governs it. | Could a competent engineer, reading what we already have, build this correctly? |
| `EXPERIMENT_FIRST` | Neither code nor corpus. Run a cheap experiment. | Is the *uncertainty* about reality, not about design? |
| `HYBRID` | Partial knowledge + iterative implementation, with the corpus growing alongside. | Is the core understood but the edges genuinely unknown? |
| `DATASET_FIRST_MANDATORY` | Build the governing corpus first. Implementation is blocked until certification. | Would building this now **permanently encode** a decision we do not yet know how to make? |

**Mapping onto DRK's sealed ten-verdict ontology** — DFP does not invent a parallel verdict
space; it maps into DRK's, and adds exactly one member through DRK-07's amendment protocol:

| `ProjectClass` | DRK `Verdict` |
|---|---|
| `DIRECT_IMPLEMENTATION` | `APPROVE` / `APPROVE-WITH-CONDITIONS` |
| `EXPERIMENT_FIRST` | `RUN-EXPERIMENT` *(exists today)* |
| `HYBRID` | `APPROVE-WITH-CONDITIONS` |
| `DATASET_FIRST_MANDATORY` | **`BUILD-KNOWLEDGE-FIRST`** *(the one genuinely-new member — see §6)* |

### 2.2 `KnowledgeType` — seven kinds

Sufficiency is never a single number in isolation; it is *sufficiency of a kind*. A build can
be rich in protocol and starved of ontology, and it will fail exactly where it is starved.

| kind | what it answers | absent ⇒ the failure it produces |
|---|---|---|
| `FOUNDATIONAL_SCIENCE` | Why does this domain behave the way it does? | Architectures that fight the domain's grain |
| `GOVERNANCE` | Who decides, with what authority, and what is forbidden? | Parallel authorities; rules routed around |
| `ONTOLOGY` | What are the things, and what is each one called? | Synonym drift; two modules naming one concept twice |
| `TAXONOMY` | What are the kinds, and where are the boundaries? | Unclassifiable edge cases discovered in production |
| `PROTOCOL` | What is the sequence, and what are the states? | Race conditions; undefined transitions |
| `BENCHMARK` | What does good look like, numerically? | "Looks better" as a verdict; Goodhart drift |
| `EVALUATOR` | How is a claim checked mechanically? | Claims that cannot be falsified; green signals that mean nothing |

### 2.3 `KnowledgeStage` — the eight-stage lifecycle (DFP-02)

The corpus lifecycle. Each stage has an entry gate and an exit gate. **`IMPLEMENTATION` is
unreachable from any stage before `CERTIFIED`** when the class is `DATASET_FIRST_MANDATORY` —
that unreachability *is* the protocol.

```
ARCHITECTURE → ONTOLOGY → AUTHORING → REVIEW → QA → CERTIFIED → FROZEN → IMPLEMENTATION
                                        ↑                 │
                                        └─── amendment ───┘
```

| stage | entry gate | exit gate |
|---|---|---|
| `ARCHITECTURE` | a `KnowledgeSufficiencyVerdict` of `DATASET_FIRST_MANDATORY` | a Reality Scan assigning NEW/EXTEND/REFERENCE **per candidate**, and a declared `parts_planned` |
| `ONTOLOGY` | architecture approved | every canonical object has a producer and a consumer |
| `AUTHORING` | ontology sealed | every planned Part exists and meets the fabrication standard |
| `REVIEW` | all Parts authored | each Part checked against the rejection criteria (§5.2) |
| `QA` | review clean | the mechanical gates pass: no code fences in doctrine, no contamination, depth floor met, cross-refs resolve |
| `CERTIFIED` | QA green ×3 hermetic | a `Certification` naming what the corpus governs and what it does **not** |
| `FROZEN` | certified | the corpus is immutable; changes require a recorded amendment |
| `IMPLEMENTATION` | frozen | the build proceeds, governed |

**The anti-bureaucracy clause (binding).** Knowledge Infrastructure Mode carries a
**terminating condition**: `parts_planned` is declared at `ARCHITECTURE` and is **immutable**.
A family that grows its own denominator mid-flight is gaming the gate, and
`T-DFP-CORPUS-INFLATION-001` catches it. A mode that cannot terminate is not a mode; it is a
permanent blocker wearing a lifecycle's clothes.

---

## 3. Signals

A `Signal` is an observation that moves a classification. Every signal must be **observable
from the repository or the proposal text** — never from the agent's opinion.

| signal | observable | pushes toward |
|---|---|---|
| `PRECEDENT_ABSENT` | D2A returns coverage < 40% against the family registry | `DATASET_FIRST` |
| `PRECEDENT_PRESENT` | D2A returns coverage ≥ 60% | `DIRECT` (extend the parent) |
| `HIGH_TRANSVERSALITY` | the proposal names ≥ 3 existing families, or "universal"/"cross-repo"/"every repo" | `DATASET_FIRST` |
| `LONG_LIFESPAN` | the artifact is a rule, gate, protocol, or ontology (things that outlive their author) | `DATASET_FIRST` |
| `IRREVERSIBLE` | DRK-02 returns Tipo C | `DATASET_FIRST` |
| `LOW_ACIS` | the existing assets top out below E3 (unproven) | `DATASET_FIRST` or `EXPERIMENT_FIRST` |
| `EMPIRICAL_UNCERTAINTY` | the open question is about *reality*, answerable by a cheap probe | `EXPERIMENT_FIRST` |
| `TIER_LOW` | `spec_gate.classify_tier` ≤ 1 | `DIRECT` |
| `SPEC_EXISTS` | `spec_gate.check_spec_gate` finds a spec | `DIRECT` or `HYBRID` |
| `CORPUS_OPEN` | another family in this repo is mid-build with unsealed Parts | **`DEFER`** — see §5.3 |

---

## 4. The ten sufficiency dimensions

Each scored 0–10 by `knowledge_sufficiency.py`. A **number**, never an adjective.

| # | dimension | 0 means | 10 means |
|---|---|---|---|
| 1 | `domain_complexity` | trivially understood | the domain's own science is contested |
| 2 | `reuse_breadth` | one call site | every repo, forever |
| 3 | `cost_of_error` | trivially reverted | irreversible; encoded in downstream artifacts |
| 4 | `governance_need` | no authority questions | decides who may do what |
| 5 | `uncertainty` | fully specified | the right question is not yet known |
| 6 | `lifespan` | this sprint | outlives every current contributor |
| 7 | `transversality` | one module | crosses ≥ 3 sealed families |
| 8 | `criticality` | cosmetic | production-blocking |
| 9 | `institutional_capacity` | the corpus exists and is proven | nothing written; nothing proven |
| 10 | `prior_science_need` | mechanical | requires an ontology before a line of code is meaningful |

**Aggregation.** `score = round(10 * Σ(dimension) / 100)`, giving 0–100. Thresholds:

| score | class |
|---|---|
| ≥ 70 **and** `institutional_capacity` ≥ 6 | `DATASET_FIRST_MANDATORY` |
| ≥ 70 **and** `uncertainty` ≥ 8 **and** the uncertainty is empirical | `EXPERIMENT_FIRST` |
| 40 – 69 | `HYBRID` |
| < 40 | `DIRECT_IMPLEMENTATION` |

**These thresholds are hypotheses, not laws.** They are seeded from the evidence in §5.1 and
are owned by DFP-05, which is required to move them when the records say so. A threshold that
has never moved after twenty records is either perfect or unmeasured, and it is never perfect.

---

## 5. Constitutional invariants

### 5.1 The invariants

- **INV-1 — No corpus without a missing science.** `DATASET_FIRST_MANDATORY` requires at
  least one `KnowledgeType` in `missing`. "This feels big" is not a signal.
- **INV-2 — No self-grading.** DFP never assigns an ACIS level. It reads one.
- **INV-3 — Every necessity decision is recorded with a prediction.** No prediction ⇒
  inadmissible as calibration evidence (§1.3).
- **INV-4 — The protocol is falsifiable.** `retirement_signal` must be reachable by some
  possible evidence set, and a V-gate proves it.
- **INV-5 — Fail-open, absolutely.** Any error in any DFP surface yields silence and the
  session continues. DFP is an advisor wired into an authority (DRK); it is never a new
  authority, and it never blocks on its own account.
- **INV-6 — The corpus terminates.** `parts_planned` is immutable after `ARCHITECTURE`.
- **INV-7 — Compose, never fork.** Every capability in §0.2 is cross-referenced. A DFP Part
  that re-explains DRK, ACIS, graphify, or `spec_gate` is rejected.
- **INV-8 — An override is data, not a defeat.** When the Owner overrides the verdict, the
  override is recorded and becomes *calibration evidence*. A protocol overridden often and
  correctly is a protocol that is wrong, and it must say so about itself.

### 5.2 The fabrication standard (measured, not invented)

Derived at STOP #1 from the approved quality references, by measurement:

| attribute | value | source |
|---|---|---|
| words per dataset | **8,000 – 15,000** | HR-OS engines 8,377–16,209w; OEIS engines 8,046–15,514w |
| words per Part | **800 – 1,500** | the band above, divided by the observed Part counts |
| Parts per dataset | **8 – 15** | same |
| artifact shape | doctrine · architecture · integration anchors are **separately addressable** | the CW UAE split-artifact pattern (5 artifacts/subsystem) |

**Rejection criteria** (a Part failing any one is rewritten, not patched): repetitive ·
generic · padded to a word count · a summary rather than a mechanism · missing its data
flows, failure modes, interfaces, governance, or evaluation · disconnected from its siblings ·
or **re-narrating a parent system instead of cross-referencing it**.

### 5.3 The `CORPUS_OPEN` clause — the invariant this family was born owing

At the moment of DFP's own STOP #1, the repository held **one open corpus with zero sealed
Parts** (SQI, opened the same day). DFP's own signal table (§3) would have returned
`CORPUS_OPEN → DEFER` on itself.

It was built anyway, under an explicit Owner decision to run the two families in parallel
panes. That is a legitimate override — and by **INV-8**, it is recorded here as the family's
first calibration datum rather than hidden. `DFP-0001` carries it. If DFP-05 later shows that
parallel open corpora measurably degrade both, this clause is the evidence that we knew, and
chose, and can now be proven wrong.

**A protocol whose first act is to exempt itself, silently, is a fraud. This one exempts
itself loudly, and writes the receipt.**

---

## 6. The DRK amendment (governed, not assumed)

`DATASET_FIRST_MANDATORY` has no home in DRK's ten-verdict ontology. `REQUEST-EVIDENCE` means
*go get evidence for this decision*; `BUILD-KNOWLEDGE-FIRST` means *the decision is not the
problem — the governing science does not exist yet*. Those are different instructions with
different exits.

DRK-00 declares its ontology **closed**. Extending a closed ontology is exactly the act
DRK-07 (Governance · Evolution · Authority Limits) exists to govern. Therefore the amendment
is **submitted to DRK as a decision and reviewed by DRK's own kernel** before it is made — the
same self-review that caught DRK's length-bias bug (`T-DRK-PRECEDENT-LENGTH-BIAS-001`).

The amendment is recorded as a `DecisionRecord`, the eleventh member is added to
`Verdict`, and `DRK_INDEX.md` records the ontology's new cardinality. Doctrine and code move
together or neither moves.

---

## 7. Naming, versioning, ownership

- Datasets: `dfp_<NN>_<slug>_v1.txt`, in this directory. Prose only — **no markdown headings,
  bullets, tables, or code fences inside a dataset file.** (Governance artifacts like this one
  are markdown; datasets are not.)
- Parts: `PART I` … `PART XV`, each closing with a `PART N FINAL LAW`.
- Code: `modules/dataset_first/`. Governance: this directory.
- A sealed dataset is amended, never silently edited. The amendment names what changed and why.
