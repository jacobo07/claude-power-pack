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
| **DFP-00** Doctrine & Constitution | `dfp_00_doctrine_constitution_v1.txt` | 10/10 | 11,383 | `COMPLETE` |
| **DFP-02** Knowledge Infrastructure Mode | `dfp_02_knowledge_infrastructure_mode_v1.txt` | 10/10 | 14,435 | `COMPLETE` |
| **DFP-05** Protocol Self-Calibration Science | `dfp_05_self_calibration_science_v1.txt` | 10/10 | 14,268 | `COMPLETE` |

Every Part ≥ 800 words; every dataset inside the measured 8k–15k band; 0 code fences;
0 contamination. Verified by `V-DFP-DEPTH` / `V-DFP-NO-CODE-IN-DOCTRINE` /
`V-DFP-CONTAMINATION`, not by assertion.

### Governance artifacts

| artifact | status |
|---|---|
| `CANONICAL_ONTOLOGY.md` | `COMPLETE` |
| `DFP_INDEX.md` (this file) | `COMPLETE` |
| `DFP_D2A_VERDICTS.md` | `COMPLETE` — the 4 not-built candidates + the 2 honest disagreements |
| `DFP_COMPLETION_REPORT.md` | `COMPLETE` — contamination audit, dependency graph, governance, honest state |

### Done-gate

`tools/test_dataset_first_protocol.py` — **17/17, hermetic ×3.**
`V-BASELINE`: DRK 18/18 + D2A 22/22 still green after the amendment.

---

## The three bugs this family found in itself (and did not hide)

The build's most valuable output was not the corpus. It was three defects the corpus's own
gates caught in the corpus's own code — each one an instance of a failure class the doctrine
had already named, committed anyway, by the author who named it.

| # | defect | consequence had it shipped |
|---|---|---|
| 1 | **`EXPERIMENT_FIRST` was gated behind the aggregate score.** A cheap empirical probe is low-scoring *by construction*. | The class was unreachable. A two-hour measurement would have been sent to write a corpus — DFP-00 III.4's named "most embarrassing failure". |
| 2 | **`institutional_capacity` was derived from D2A's `coverage_pct`.** Coverage is inflated by an architectural term that forces ≥80% whenever a proposal's tokens touch ≥4 families — which a long foundational proposal does purely from vocabulary. | **`DATASET_FIRST_MANDATORY` was UNREACHABLE.** The family's central verdict was dead, and with it the eleventh DRK verdict built to host it. The whole protocol was inert. Sealed as `T-DFP-COVERAGE-AS-CAPACITY-001`. |
| 3 | **`V-DFP-INV1-NAMED-MISSING` passed vacuously.** It asserted `all(...)` over a list that was empty because *no case reached the class*. | A green gate concealing defect #2. A gate that cannot fail is not a gate. |

Defect #2 is the important one. DFP-00 VI.6 states, in its own doctrine, that *a provider's
score distribution must be measured before it is mapped to a hard verdict* — the lesson DRK
paid for with `T-DRK-PRECEDENT-LENGTH-BIAS-001`. The first implementation of this family
mapped an unmeasured provider score straight to a hard conjunct anyway. It was caught by
measuring the distribution (`coverage 92% / functional 7%` on a genuinely novel proposal),
exactly as VI.8 prescribes. **The doctrine was right and its author did not obey it.** That is
the strongest available argument for the control-set discipline, and it is why the gate now
asserts both poles are reachable rather than trusting a conjunct.

---

## UKDL rules sealed by this family

- `PR-DATASET-FIRST-001` — before implementing a system of high complexity, long lifespan or
  transversal impact, run the Knowledge Sufficiency Engine. A `BUILD-KNOWLEDGE-FIRST` verdict
  means the governing corpus is built first and implementation begins only after
  certification. **Constitutional, not advisory** — but it fires far less often than its name
  suggests, and that is by design (DFP-00 III).
- `T-DATASET-FIRST-DOGMA-001` — a protocol that always demands a corpus is as harmful as one
  that never does. Systematic false positives turn DFP into bureaucracy the Owner will route
  around, and a rule routed around is not a rule. Recalibration against real evidence
  (DFP-05) is mandatory; the retirement signal must stay reachable.
- `T-DFP-COVERAGE-AS-CAPACITY-001` — never map a composite provider score to a hard verdict
  without measuring its distribution first. D2A's `coverage_pct` rises with proposal length
  and vocabulary breadth; only its per-family `functional` precision separates a true
  duplicate (29) from a rich novel proposal (7). Mapping coverage to capacity killed this
  family's central class silently. Same class as `T-DRK-PRECEDENT-LENGTH-BIAS-001` and
  `T-D2A-LEXICAL-BLINDNESS-001`.
- `T-D2A-REGISTRY-STALENESS-001` — a duplicate-detector whose family registry stops at its own
  ship date grows blinder every week. D2A held 19 families and could not see DRK, ACIS, SQI,
  `spec_gate` or `hard_rules` — the newest half of the stack, and the half a proposal arriving
  today is most likely to duplicate. Registry 19 → 27.
- `T-D2A-LEXICAL-BLINDNESS-001` — D2A's coverage score is a SIGNAL, never a VERDICT. It
  matches words, not architecture. A low score is not clearance to build.

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
