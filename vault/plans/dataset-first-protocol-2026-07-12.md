# Dataset First Protocol (DFP) — DISCOVERY REPORT + STOP #1

> Status: **BLOCKED at FASE -1 / PASO 1.** Source dataset not found on disk.
> Date: 2026-07-12. Repo HEAD at scan: `8b9fc13` (SQI canonical ontology).
> Owner decision required before any FASE 1 commit.

---

## 1. PASO 1 — Source dataset: NOT FOUND

The blocking step failed. No file on this host contains the DFP thesis or its
vocabulary as a source specification.

### Paths inspected

| Surface | Method | Result |
|---|---|---|
| `C:\Users\User\Downloads\` (recursive, all files) | filename match on `dataset.?first`, `knowledge.?first`, `knowledge.?infra`, `dataset.?necess`, `DFCP`, `KICP` | 7 hits, **all unrelated** (see below) |
| `C:\Users\User\Downloads\` (recursive, `*.txt` + `*.md`) | content match on `infraestructura permanente`, `Dataset First Protocol`, `Knowledge Sufficiency`, `Dataset Necessity`, `DATASET_FIRST` | 4 files, **all pre-existing quarantined corpora**, none a DFP source |
| `C:\Users\User\Downloads\Promptsss\` (working dir) | full listing | no DFP artifact |
| `C:\Users\User\Downloads\` — files modified in the last 3 days | mtime sweep | 3 datasets landed today: UQII, CW Autonomous Ecommerce, Multimodal Commercial Reality. **None is DFP.** |
| `/mnt/user-data/uploads/`, `C:\mnt\user-data\uploads`, `C:\Users\User\uploads` | `Test-Path` | do not exist on this host |

### Why every hit is a false positive

- `Dataset First Win Engine 1.txt` — "First Win" is the TUA-X monetization engine.
  Lexical collision on the word *First*, not the DFP thesis.
- `PART_32_BILLION_SCALE_KNOWLEDGE_INFRASTRUCTURE.md`, `BILLION-SCALE AI SYSTEMS &
  KNOWLEDGE INFRASTRUCTURE ARCHITECT.txt` — infrastructure *for* AI systems at scale.
  Unrelated to the knowledge-before-code discipline.
- The 4 content hits on `infraestructura permanente` — CW Ops Risk Shield, CW Permanent
  Innovation Engine, `Qué es TUAX`, MundiCraft event design. These are **inside the
  conceptual quarantine** declared by this prompt and are unusable as source material.

**Consequence:** the constraint is explicit — *"Si no se encuentra: reportar rutas
inspeccionadas y solicitar la ruta exacta — no continuar sin el fuente."* FASE 1 is not
started. No file has been written under `vault/knowledge_base/dataset_first/`.

---

## 2. PASO 2 — Quality standard extracted (fabrication attributes only)

Measured, not asserted. Zero concepts, terminology, or domain imported.

| Reference | Unit | Words per unit | Structure |
|---|---|---|---|
| **Human Resonance OS** | one engine `.md` | **8,377 – 16,209** (median ≈ 12,500) | one engine = one dataset; deep single-file |
| **Operator Essence Intelligence System** | one engine `.md` | **8,046 – 15,514** (median ≈ 13,100) | identical shape |
| **CW Unfair Advantage Engine** (preferred ref) | one subsystem = 5 artifacts | ≈ 7,700 total (`DATASET` 2,700 · `CONSTITUTION` 1,280 · `PRD` 1,500 · `ARCHITECTURE` 1,200 · `INTEGRATION_ANCHORS` 1,030) | **split-artifact**: doctrine, spec, architecture and wiring are separate files |
| CW UAE single-file variant | one `.txt` | 20,502 across 43 Parts → **477 w/Part** | the low-density outlier |

### The fabrication standard this yields

- **Dataset depth: 8,000–15,000 words per dataset file.** This is the reference band.
- **Part depth: 800–1,500 words**, and a dataset carries **8–15 Parts**.
- The CW UAE **split-artifact** pattern is the structurally superior one: doctrine,
  architecture, PRD and integration anchors are separate addressable files, so the
  wiring contract does not have to be excavated out of prose.

### The uncomfortable comparison against PP's own recent output

| PP family | Words per dataset | Verdict against the reference band |
|---|---|---|
| DRK-00…07 (sealed 2026-07-11) | 2,500 – 4,405 | **~3x below** the 8k–15k reference |
| SQI fabrication contract (sealed today) | 1,200–1,500 w/Part × 20 Parts = 24k–30k | **~2x above** the reference band, and **0 of 80 Parts written** |

PP has no shared, measured fabrication standard. Each family invents its own and lands in
a different order of magnitude. That is a real finding and it belongs to DFP-02 below.

---

## 3. PASO 3 — Reality Scan of the PP

`grep -ri "dataset.first|knowledge.first|knowledge.sufficiency|knowledge.infrastructure|
dataset.necessity"` across the whole repo → **1 hit**, in `vault/audits/mydeepchat_skills_raw.jsonl`
(an unrelated third-party skill dump).

**There is no Dataset First / Knowledge First system in the PP.** The naming space is free.

But the *thesis* is heavily pre-covered by systems built under other names.

### 3.1 The thesis is already law — under a different name

`modules/spec_gate/gate.py` (verified at source, HR-PREMISE-001):

- `classify_tier(description) → TierResult(tier 0–3, size S/M/L/XL, requires_spec, requires_prd)`
- Tier ≥ 2 ⇒ `requires_prd=True`. The SDD-OS dataset it implements states literally:
  *"ejecutar sin PRD queda prohibido"*.
- `check_spec_gate(desc, cwd, size) → SpecGateResult(has_spec, gate_passed, action)` where
  `action ∈ {proceed, read_spec, create_spec}`.
- Sealed as **HR-SPEC-001** in the project CLAUDE.md.

That IS "no permanent construction before the governing artifact exists." **The DFP thesis
is already a Hard Rule in this repo.** What spec_gate demands is a *spec*; what DFP demands
is a *corpus*. That distinction is the only doctrinal delta, and it is thinner than the
prompt assumes.

### 3.2 Overlap with DRK (sealed yesterday, 2026-07-11) — severe

DRK's verdict ontology already contains, verbatim:
`REJECT · REFRAME · REQUEST-EVIDENCE · RUN-EXPERIMENT · DEFER · KEEP-LOCAL · CONSOLIDATE ·
REMOVE · APPROVE-WITH-CONDITIONS · APPROVE`.

The DFP project taxonomy maps almost 1:1 onto it:

| DFP proposed class | Already emitted by |
|---|---|
| `DIRECT_IMPLEMENTATION` | DRK `APPROVE` / `APPROVE-WITH-CONDITIONS` |
| `EXPERIMENT_FIRST` | DRK **`RUN-EXPERIMENT`** — exists today |
| `HYBRID` | DRK `APPROVE-WITH-CONDITIONS` |
| `DATASET_FIRST_MANDATORY` | **the one verdict DRK does not have** |

`modules/decision_review/decision_kernel.py` already composes `arch_check · one_shot.compiler ·
spec_gate.classify_tier · d2a_engine · acis.epistemic_ladder · cost_collapse.route · owner_queue`,
computes reversibility Tipo A/B/C + blast radius + a Decision Confidence Score, and blocks
only on `Tipo-C irreversible ∧ ACIS < E3`.

**DRK-03 is an evidence-burden-scaled-by-irreversibility engine. ACIS is an 8-level knowledge
maturity ladder (E0–E7).** A "Knowledge Sufficiency Engine" that scores complexity, reuse,
cost, governance, uncertainty, lifespan, transversality and criticality is, in this repo,
**a composition of DRK-02 (blast radius/entropy) + DRK-03 (evidence burden) + ACIS (maturity)
+ spec_gate (tier)** — not a new science.

### 3.3 Overlap with SQI (in flight, approved today) — a scheduling conflict

`vault/knowledge_base/sqi/SQI_INDEX.md` was committed at HEAD **today**. Its state:

- 14 datasets approved at its own STOP #1; spearhead = SQI-00…03.
- Build status of every dataset: **`NOT_STARTED` — 0/20 Parts, ×4.**
- It sealed `T-SQI-PARALLEL-SYSTEM-001`: *"SQI never forks a capability that ACIS, DRK, FD,
  graphify, output_contracts or hard_rules already owns."*

A second pane is (or was) mid-build on SQI. Opening a 7-dataset DFP family right now means
**two unfinished permanent knowledge infrastructures in parallel, with zero Parts written
between them.**

### 3.4 D2A verdict on DFP itself

The prompt mandates D2A on every *additional* dataset proposal. Applied to the *primary*
proposal, `modules/duplicate_to_advantage` returns the finding above: the capability is
substantially present, distributed across DRK + spec_gate + ACIS + D2A + graphify. D2A's
contract is **propose-never-build**, and its proposal is the collapsed scope in §5.

---

## 4. The self-refutation (the finding that should decide this)

Apply the DFP thesis to DFP.

> *"Nunca construyas una infraestructura permanente si todavía no existe la ciencia
> institucional que debe gobernarla."*

- The **science does not exist**: the source dataset is not on disk (§1).
- The **infrastructure would be permanent**: 7 datasets, an ontology, a court, a detection
  engine wired into `UserPromptSubmit`, a UKDL law, a Hard Rule.
- PP is **already carrying an unfinished corpus**: SQI, 0/80 Parts, opened today.

**DFP's own Knowledge Sufficiency Engine, run on DFP, returns `DATASET_FIRST_MANDATORY` —
and the dataset is missing.** Building it now would be the exact failure the protocol was
written to forbid. This is not a rhetorical point; it is the protocol's first real test case,
and it fails.

---

## 5. Recommended action per candidate system

| # | Proposed | Verdict | Rationale |
|---|---|---|---|
| DFP-00 | Doctrine & Constitution | **NEW-thin** | The thesis is real but 80% already law via HR-SPEC-001 + SDD-OS Tier≥2. The genuine delta is the **spec-vs-corpus distinction**: when is a *spec* insufficient and a *governing corpus* required? That is one Part, not one dataset. |
| DFP-01 | Knowledge Sufficiency Engine | **EXTEND** | Compose DRK-02 + DRK-03 + ACIS ladder + `spec_gate.classify_tier`. Ship as `modules/decision_review/` extension, not a dataset family. Zero new science. |
| DFP-02 | **Knowledge Infrastructure Mode** | **NEW — highest value** | Genuinely absent. PP has shipped ≥10 dataset families (ACIS, DRK, SQI, FD, CO, graphify, CDIO, D2A, SDD-OS, FIOS) with **no governing lifecycle**: no shared fabrication standard, no Knowledge QA, no Certification, no Freeze. Each family re-invents its own rubric and lands 3x apart in density (§2). This is the real, evidenced hole. |
| DFP-03 | Dataset Necessity Court | **DO_NOT_BUILD** | DRK-01 already ships a review kernel with an adversarial pass, a 10-verdict ontology and an authority block-gate. A second colegiado authority is a **parallel authority** — precisely what `T-DECISION-AUTHORITY-CAPTURE-001` and `T-SQI-PARALLEL-SYSTEM-001` forbid. Correct move: **add the one missing verdict `BUILD-KNOWLEDGE-FIRST` to DRK's existing ontology.** |
| DFP-04 | Detection Engine | **EXTEND** | `spec_gate` is already a keyword tier classifier, already reachable from the `UserPromptSubmit` JIT loader. Extend it; do not build a second detector on the same surface. |
| DFP-05 | **Protocol Self-Calibration Science** | **NEW — highest strategic value** | Genuinely absent and uniquely fundable: PP has ~10 real families as data points. Nothing in the repo measures whether knowledge-first actually paid off versus direct implementation. Without it, DFP is dogma — which the prompt itself names as the failure mode (`T-DATASET-FIRST-DOGMA-001`). |
| DFP-06 | Compound Effect Architecture | **EXTEND-thin / REFERENCE** | `graphify` (868 coordinates, cross-family edges) + FD-03 + D2A already own cross-family compounding. Cross-reference; do not re-narrate. |

### Collapsed proposal

**2 genuinely-new datasets, not 7**: `DFP-02 Knowledge Infrastructure Mode` and
`DFP-05 Protocol Self-Calibration Science`, plus a thin `DFP-00` constitution carrying the
spec-vs-corpus distinction, plus **one verdict added to DRK** (`BUILD-KNOWLEDGE-FIRST`) and
one extension to `spec_gate`. No new court. No new detector. No parallel authority.

At the reference density (§2) that is ≈ 8,000–15,000 words × 3 datasets — deliverable and
defensible — versus 7 datasets of which 4 would be re-narrations of DRK.

---

## 6. Owner decision required (STOP #1)

1. **Provide the exact path to the DFP source dataset**, or state that none exists and that
   the thesis in the prompt *is* the source. PASO 1 is blocking and I will not proceed on
   an assumed corpus.
2. **Approve or reject the collapsed scope** (§5). If the full 7-dataset family is ordered
   regardless, DFP-03 remains a `DO_NOT_BUILD` in my assessment and I will record the
   override rather than silently comply.
3. **Sequencing versus SQI.** SQI is 0/80 Parts and was opened today. Decide whether DFP
   precedes it, follows it, or runs in a separate pane — but two open corpora with zero
   Parts written is the failure DFP itself names.
