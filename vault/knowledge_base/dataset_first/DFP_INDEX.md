# DFP — Dataset First Protocol — Master Index

> **The Knowledge-Necessity axis of Claude Power Pack.** Founded 2026-07-12.
> Where **DRK** governs whether a *decision* is sound, **ACIS** the *epistemic status* of a
> claim, **SQI** whether the executable reality is *verified*, **D2A** what happens when the
> stack is asked to build something that *already exists*, and **`spec_gate`** whether a task
> has a spec — **DFP governs one thing none of them does: whether the institutional science
> that must govern a build exists yet, and what it costs to demand it when it does not.**
>
> Architecture approved at STOP #1: `vault/plans/dataset-first-protocol-2026-07-12.md`
> Binding ontology: `CANONICAL_ONTOLOGY.md` — read before authoring any Part.

---

## Root law

> **Never build permanent infrastructure when the institutional science that must govern it
> does not yet exist.**
>
> And its inseparable second half: **a protocol that always demands a corpus is as
> destructive as one that never does.** The discipline earns its authority by being
> calibrated against evidence (DFP-05), never by being asserted.

---

## Scope decision (Owner, STOP #1, 2026-07-12)

The source specification proposed **seven datasets**. The Reality Scan found the thesis
already partly law (`HR-SPEC-001` + SDD-OS Tier ≥ 2) and four of the seven substantially owned
by DRK, `spec_gate`, D2A and graphify.

**Approved: three datasets, not seven.** The four duplicate candidates are **not built** —
they are routed through the Power Pack's own duplicate-handling engine (**D2A**), which
converts each into a reinforcement of the parent that already owns the surface. Their verdicts
and build contracts are recorded in `DFP_D2A_VERDICTS.md`.

This is the protocol obeying itself: `R1_extend_before_create`.

---

## Family tree

```
PARENT SUBSTRATE (composed, never re-narrated — see CANONICAL_ONTOLOGY §0.2)
DRK (decisions) · ACIS (epistemics) · SQI (verification) · D2A (duplicates)
spec_gate / SDD-OS (tiers + PRD gate, HR-SPEC-001) · graphify (graph) · FD (frontier)
CO (cost) · hard_rules (invariants)
│
└── DFP — Dataset First Protocol
    │
    ├── DFP-00  Doctrine & Constitution              NEW-thin — the corpus-vs-spec distinction
    ├── DFP-02  Knowledge Infrastructure Mode        NEW      — the unowned lifecycle
    └── DFP-05  Protocol Self-Calibration Science    NEW      — the falsifier
```

**Numbering is preserved from the source specification on purpose.** The gaps at 01, 03, 04
and 06 are not omissions — they are the four DO-NOT-BUILD verdicts, and the holes are the
evidence. A reader who asks "where is DFP-03?" is answered by `DFP_D2A_VERDICTS.md`.

---

## Build status

Status vocabulary: `NOT_STARTED` · `IN_PROGRESS` · `DRAFTED` · `VERIFIED` · `COMPLETE`.
A dataset is `COMPLETE` only when every Part is `VERIFIED` against the §5.2 rubric.
**`COMPLETE` is never declared while any Part is `NOT_STARTED`.**

| dataset | file | Parts | words | status |
|---|---|---|---|---|
| **DFP-00** Doctrine & Constitution | `dfp_00_doctrine_constitution_v1.txt` | 0/10 | — | `NOT_STARTED` |
| **DFP-02** Knowledge Infrastructure Mode | `dfp_02_knowledge_infrastructure_mode_v1.txt` | 0/10 | — | `NOT_STARTED` |
| **DFP-05** Protocol Self-Calibration Science | `dfp_05_self_calibration_science_v1.txt` | 0/10 | — | `NOT_STARTED` |

### Governance artifacts

| artifact | status |
|---|---|
| `CANONICAL_ONTOLOGY.md` | `COMPLETE` |
| `DFP_INDEX.md` (this file) | `IN_PROGRESS` — updated after every sealed unit |
| `DFP_D2A_VERDICTS.md` | `NOT_STARTED` (FASE 2) |
| `DFP_DEPENDENCY_GRAPH.md` | `NOT_STARTED` (FASE 4) |
| `DFP_GOVERNANCE.md` | `NOT_STARTED` (FASE 4) |
| `DFP_CONTAMINATION_AUDIT.md` | `NOT_STARTED` (FASE 4) |
| `DFP_COMPLETION_REPORT.md` | `NOT_STARTED` (FASE 4) |

---

## What each dataset owns

**DFP-00 — Doctrine & Constitution.** The thesis and, more importantly, its boundary. The
**corpus-versus-spec distinction**: `spec_gate` already forbids executing a Tier ≥ 2 task
without a PRD, so DFP's doctrinal delta is not "write things down first" — that is settled
law. The delta is the level above: *when is a spec itself insufficient, and a governing
corpus required?* The four project classes and where each one's boundary genuinely lies. When
the protocol does **not** apply, stated as forcefully as when it does. The `CORPUS_OPEN`
self-exemption and why it was written loudly rather than hidden.
*Composes:* `spec_gate` (HR-SPEC-001), DRK-02 (reversibility), ACIS (levels).

**DFP-02 — Knowledge Infrastructure Mode. ★ The genuinely-absent axis.** The Power Pack has
shipped ten-plus dataset families — ACIS, DRK, SQI, FD, CO, graphify, CDIO, D2A, SDD-OS,
FIOS — with **no governing discipline for how a corpus is built.** Each family invents its own
fabrication rubric and lands an order of magnitude apart in density (DRK: 2,500–4,405 words
per dataset; SQI's contract: 24,000–30,000). None of them defines Knowledge QA, Knowledge
Certification, or Knowledge Freeze. This dataset owns the eight-stage lifecycle, its entry and
exit gates, the immutable `parts_planned` denominator, and the anti-bureaucracy terminating
condition that stops the mode from becoming a permanent blocker.
*Origin:* the measurement at this family's own STOP #1 — an order-of-magnitude density spread
across sibling families that each believed they had a standard.

**DFP-05 — Protocol Self-Calibration Science. ★ The falsifier.** Without this, DFP is dogma,
and the source specification says so itself (`T-DATASET-FIRST-DOGMA-001`). Compares the
records: builds that went knowledge-first against builds that went direct, measured on
velocity, rework, regression count, reuse, and maintenance cost. Recalibrates the §4
thresholds from evidence. Carries the **retirement clause** — the protocol must be able to
recommend its own deletion, and a V-gate proves that verdict is reachable.
*Origin:* the Power Pack holds ~10 real families as data points and has never once measured
whether the knowledge-first discipline paid for itself.

---

## The four that were not built (D2A-routed)

| proposed | verdict | routed to |
|---|---|---|
| DFP-01 Knowledge Sufficiency Engine | **EXTEND** | composed from DRK-02/03 + ACIS + `spec_gate` — ships as `modules/dataset_first/`, not a dataset |
| DFP-03 Dataset Necessity Court | **DO_NOT_BUILD** | DRK-01 *is* the court. A second colegiado authority is forbidden by `T-DECISION-AUTHORITY-CAPTURE-001`. Delta shipped instead: the **eleventh DRK verdict**, `BUILD-KNOWLEDGE-FIRST`, via DRK-07's amendment protocol |
| DFP-04 Detection Engine | **EXTEND** | `spec_gate.classify_tier` already classifies free-text tasks on the `UserPromptSubmit` surface |
| DFP-06 Compound Effect Architecture | **REFERENCE** | graphify (edges) + FD-03 (transmutation) + D2A (anti-duplication) already own cross-family compounding |

---

## Executable

| Module | Contract |
|---|---|
| `modules/dataset_first/classifier.py` | free-text proposal → `ProjectClassification` (delegates tier to `spec_gate`, never re-derives it) |
| `modules/dataset_first/knowledge_sufficiency.py` | → `KnowledgeSufficiencyVerdict`; ten dimensions, each a number; reads the ACIS ceiling, never assigns it |
| `modules/dataset_first/necessity_record.py` | append-only `DatasetNecessityRecord` writer, fail-open; **a record without a prediction is inadmissible** |
| `modules/dataset_first/manifest.py` | the eight-stage `KnowledgeInfrastructureManifest` + its gates; immutable `parts_planned` |
| `modules/dataset_first/calibrator.py` | records → `ProtocolCalibrationRecord`; moves the thresholds; can emit `retirement_signal` |
| `modules/decision_review/` | **extended**: the eleventh verdict + a DFP provider adapter (fail-open, budgeted) |
| `modules/duplicate_to_advantage/d2a_engine.py` | **extended**: `FAMILY_REGISTRY` gains the post-C85 sealed families (DRK · ACIS · SQI · spec_gate · hard_rules · D2A) so it can detect duplicates against them at all |

---

## V-gates (FASE 5 done-gate) — planned scorecard

`tools/test_dataset_first_protocol.py`, hermetic ×3:
`V-DFP-DOCTRINE-EXISTS` · `V-DFP-ONTOLOGY-COMPLETE` (every canonical object has a producer
**and** a consumer) · `V-DFP-DETECTOR-FAILOPEN` (pathological input → silence, never a block) ·
`V-DFP-NO-DOGMA` (DFP-05 present and its thresholds are movable) ·
`V-DFP-RETIREMENT-REACHABLE` (a synthetic evidence set flips `retirement_signal` True) ·
`V-DFP-LIVENESS` (row in the D1 Liveness Ledger, probe earns LIVE) ·
`V-DFP-CONTAMINATION` (zero CW-Ops entity/terminology hits in the corpus) ·
`V-DFP-COMPOUND` (each dataset declares its parents and its non-duplication) ·
`V-DFP-DEPTH` (≥ 800 real words per Part; 8,000+ per dataset) ·
`V-DFP-NO-CODE-IN-DOCTRINE` · `V-DFP-CROSS-REF-NOT-RENARRATE` ·
`V-DFP-D2A-REGISTRY` (D2A now detects DRK/ACIS/spec_gate as parents) ·
`V-DFP-DRK-AMENDMENT` (the eleventh verdict is reachable and recorded) ·
`V-BASELINE` (DRK 18/18, D2A 22/22, ACIS 48/48, strategic-gaps 21/21 still green).

---

## The fundamental property

> **Demand the science before the concrete — and prove that the demand paid for itself.**
> DFP asks one question no sibling asks: does the knowledge that must govern this build exist
> yet? When it does, DFP is silent and the build proceeds. When it does not, DFP routes the
> work through a corpus lifecycle that is *required to terminate*. And it keeps the receipts —
> every necessity decision carries a prediction, every override is data, and the protocol is
> built to be proven wrong. It composes DRK, ACIS, D2A and `spec_gate` and forks none of them;
> it is three datasets, five modules, and a ledger that can recommend its own deletion.
