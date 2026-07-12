# DFP — D2A Verdicts on the Four Datasets That Were Not Built

> **What this file is.** The source specification proposed seven datasets. Four of them
> duplicated capabilities the Power Pack already owns. Rather than delete them by assertion,
> they were routed through the stack's own duplicate-handling engine — **D2A**
> (`modules/duplicate_to_advantage`, SCS C85, contract: *propose, never build*).
>
> This is the protocol obeying its own first anti-inflation rule, `R1_extend_before_create`.
>
> **What this file is not.** It is not a rubber stamp. D2A and the architectural Reality Scan
> **disagreed on two of the four**, and the disagreements are recorded below rather than
> tuned away. Where they disagree, the disagreement is the finding.

Generated 2026-07-12 against `FAMILY_REGISTRY` at 27 families.

---

## 0. The precondition: D2A was blind to half the stack

D2A's `FAMILY_REGISTRY` — its entire source of truth for "what already exists" — held **19
families**, all sealed at or before D2A's own ship date (SCS C85). It contained **no row for
DRK, ACIS, SQI, `spec_gate`, `hard_rules`, or D2A itself.**

The consequence is not subtle: **D2A could not detect a duplicate of the newest half of the
stack** — which is precisely the half that a proposal arriving today is most likely to
duplicate. Running the DFP candidates through it unmodified would have returned "novel" for
proposals that duplicate DRK almost line for line, and the protocol would have cited that
false clearance as evidence.

A duplicate-detector whose registry stops at its own birthday is a detector that grows blinder
every week it is not updated. **Sealed as `T-D2A-REGISTRY-STALENESS-001`.**

**Fix shipped:** eight rows added (`DRK-01`, `DRK-02`, `DRK-03`, `ACIS`, `SQI-02`,
`SPEC-GATE`, `HR`, `D2A`), registry 19 → 27. The keyword sets are drawn from each family's own
master index, **not** reverse-engineered to make a chosen proposal light up. The gate that
pins the registry (`V-D2A-NO-DUPLICATE`) was extended with the new ids because its contract is
*"the registry names real sealed families"* — and these are real.

---

## 1. The measured verdicts

Two control cases bracket the run and prove the detector was not simply made trigger-happy:

| control | parent | coverage | duplicate | expected |
|---|---|---|---|---|
| **CANON** — Token Budget Planner (a known duplicate) | FD-05 | **95%** | True | > 80%, True ✅ |
| **NOVEL** — Sonar Haptics (genuinely unrelated) | — | **0%** | False | < 50%, False ✅ |

### The four candidates

| candidate | D2A parent | cov | sem | func | arch | D2A verdict | artifact |
|---|---|---|---|---|---|---|---|
| **DFP-01** Knowledge Sufficiency Engine | DRK-03 (Evidence Burden & Confidence) | **86%** | 25 | 10 | 100 | **DUPLICATE** | `dataset_part` |
| **DFP-03** Dataset Necessity Court | DRK-01 (Review Kernel & Verdict Engine) | **63%** | 45 | 56 | 75 | **DUPLICATE** | `dataset_part` |
| **DFP-04** Detection Engine | HR (Hard Rules) *(mis-attributed — see §2.2)* | **80%** | 12 | 4 | 100 | **DUPLICATE** | `dataset_part` |
| **DFP-06** Compound Effect Architecture | FD-06 (Permanent Advantage Writeback) | **31%** | 43 | 27 | 50 | *not* duplicate | `dataset_part` |

### The two that were built (the control that matters most)

| candidate | D2A parent | cov | D2A verdict |
|---|---|---|---|
| **DFP-02** Knowledge Infrastructure Mode | PM-04 | **21%** | **NOVEL** ✅ |
| **DFP-05** Protocol Self-Calibration Science | FIOS-IRR | **17%** | **NOVEL** ✅ |

**The engine independently cleared exactly the two datasets the Reality Scan judged genuinely
new, and flagged three of the four it judged duplicates.** The scope collapse from seven to
three is not an aesthetic preference — it is a machine-checkable result.

Every candidate was routed to `dataset_part` or lighter. **D2A recommended a new `dataset`
artifact for none of them** — which is the anti-inflation ladder working: a Part before a
dataset, always.

---

## 2. Where D2A and the architectural scan disagree (recorded, not resolved by fiat)

### 2.1 DFP-06 — D2A says 31% (novel); the scan says REFERENCE

D2A places DFP-06 below its 50% duplicate line. The architectural reading is that
"compound effect between sibling datasets" is **owned outright** by FD-06 (permanent
cross-dataset advantage), graphify GK-04 (typed edges between families), and FD-03 (insight
transmutation).

**The disagreement is real and the machine is under-reporting.** The reason is structural:
D2A's detector is **lexical** — a bag-of-words overlap against keyword tuples. DFP-06's
proposal text describes FD-06's exact subject matter using almost none of FD-06's vocabulary.
Raising its coverage would require adding the proposal's own words to the parent's keyword
set, which is overfitting the detector to a conclusion already held.

**Resolution: DFP-06 is NOT built.** The architectural verdict (REFERENCE) stands, and D2A's
disagreement is preserved as evidence against the detector, not against the verdict.

### 2.2 DFP-04 — right verdict, wrong parent

D2A flags DFP-04 as an 80% duplicate, which matches the scan. But it names **HR (Hard Rules)**
as the parent, when the true owner is **`spec_gate`** (`classify_tier` already classifies a
free-text task by domain complexity and impact, and is already wired to `UserPromptSubmit`).

The `arch=100` score carried the verdict; the `sem=12 / func=4` scores show the parent
attribution rested on almost nothing. **A high architectural score with near-zero semantic and
functional scores means "this position is already occupied" — not "by this family."**

**Resolution: DFP-04 is NOT built.** The verdict is honored; the parent is corrected by hand
to `spec_gate`, and the mis-attribution is recorded.

### 2.3 The law both disagreements teach

> **`T-D2A-LEXICAL-BLINDNESS-001` — D2A's coverage score is a SIGNAL, never a VERDICT.**
> The detector matches words, not architecture. It systematically under-reports a duplicate
> whose proposal is written in vocabulary different from its parent's index, and it can carry
> a correct duplicate verdict on a wrong parent (high `arch`, near-zero `sem`/`func` is the
> tell). A low coverage score is **not** clearance to build. Read the parent's index before
> trusting either the number or the name attached to it.
>
> *Origin: DFP's own STOP #1. D2A cleared DFP-06 at 31% and mis-attributed DFP-04 to HR. Both
> were caught by reading the parent indexes, and neither was fixed by tuning keywords until
> the machine agreed.*

This is the same failure class as `T-DRK-PRECEDENT-LENGTH-BIAS-001` (DRK's `arch_check` score
rising with input length): **a provider's score distribution must be measured before it is
mapped to a hard verdict.** DRK learned it about length; D2A now carries it about vocabulary.

---

## 3. What was built instead of the four

| not built | shipped instead |
|---|---|
| DFP-01 Knowledge Sufficiency Engine (dataset) | `modules/dataset_first/knowledge_sufficiency.py` — composes DRK-02 (blast radius) + DRK-03 (evidence burden) + ACIS (level ceiling) + `spec_gate` (tier). Code, not doctrine. |
| DFP-03 Dataset Necessity Court (dataset) | **One verdict** added to DRK's existing ontology — `BUILD-KNOWLEDGE-FIRST` — through DRK-07's amendment protocol, reviewed by DRK's own kernel. No second court. |
| DFP-04 Detection Engine (dataset) | An extension to `spec_gate`, on the `UserPromptSubmit` surface it already owns. |
| DFP-06 Compound Effect (dataset) | Cross-references to FD-06 · GK-04 · FD-03 in `CANONICAL_ONTOLOGY.md` §0.2. |

Four proposed datasets → **zero new datasets, one enum member, two modules, one set of
cross-references.** That ratio is the entire point of D2A, and it is the first time the engine
has been run against a live proposal that was not its own worked example.
