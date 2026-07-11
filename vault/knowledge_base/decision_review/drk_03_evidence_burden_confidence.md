# DRK-03 — Evidence Burden & Confidence Calibration

> The dataset that answers "how much evidence, and of what type, does *this* decision need before the
> stack may act on it?" — and how the Decision Confidence Score is *derived* rather than declared.
> DRK-00 fixed the evidence model (the ten `type`s), the DCS field, the Tipo A/B/C reversibility
> classes, and the block-narrow rule; DRK-01 §Stage 5 named "evidence & burden" as a pipeline stage.
> DRK-03 defines the **mechanism** that Stage 5 runs: the burden as a function of reversibility and
> blast radius, and the calibration of confidence into a proxy that routes attention. **Parent it
> DEEPENs:** SDD-OS Parte V §9 (Decision Confidence Score — a six-word enumeration: *datos, evidencia,
> experiencia, validación, riesgo, alternativas exploradas*), given mechanism here. **The critical
> distinction it holds throughout:** the ACIS epistemic ladder (owns evidence *levels* E0–E7 and the
> falsifier discipline) answers *how strong is this claim*; DRK-03 answers *how much strength this
> decision requires* — the burden. Level is an ACIS concept; burden is a DRK concept. DRK composes
> ACIS levels into a burden test; it never re-derives a level. **Cross-references (never re-narrated):**
> ACIS `epistemic_ladder`, DRK-02 (reversibility & blast-radius mechanics), D2A engine, CO-12.

---

## PART I — THE EVIDENCE BURDEN MODEL

### I.1 Burden is a property of the decision, level is a property of the claim

The single confusion this dataset exists to prevent is the conflation of two orthogonal quantities.
The first is the **epistemic level** of an individual piece of evidence — is this measurement E2 (a
model-proposed hypothesis) or E3 (re-derived by a probe or a second substrate)? That axis is owned
entirely by the ACIS epistemic ladder (owns evidence levels E0–E7), and DRK reads it, never sets it.
The second is the **evidence burden** of a decision — the minimum *quantity* and minimum *type-class*
of evidence a decision must accumulate before the stack acts on it autonomously. A decision to rename
a private helper and a decision to freeze a public data schema might each rest on evidence of
identical individual strength, yet the second *demands* far more of it, because it is far harder to
undo. Burden is not about how good any one claim is; it is about how much good-enough claim the
decision's irreversibility entitles it to before action is proportional.

This separation is the DEEPEN of SDD-OS Parte V §9, which listed six *inputs* to a confidence score
(datos, evidencia, experiencia, validación, riesgo, alternativas exploradas) without ever saying how
much of each a given decision needs. That omission is exactly why Parte V was doctrine-that-nothing-runs
at STOP #1: a confidence number with no burden threshold routes no behavior. DRK-03 supplies the
threshold — and makes it a function of reversibility (DRK-02), not a constant.

### I.2 Why reversibility sets the burden

Reversibility is the load-bearing variable because it prices the cost of being wrong. A Tipo A
(reversible, trivially undone) decision can proceed on thin, even `assumption`-based evidence, because
the correction cost if the assumption is false is small — you undo it. The evidence burden of a Tipo A
decision is therefore *low by design*: demanding `observed_evidence` at ACIS E3 before renaming a
local variable would be the cognitive tax DRK-07 forbids, and would violate the scope-first invariant
(DRK-00 §III.1). A Tipo B (difficult to reverse) decision raises the burden: the correction cost is
real, so `assumption`-only support is no longer proportional; the decision wants at least `inference`
from checked `fact`s, and preferably one `observed_evidence` item. A Tipo C (practically irreversible)
decision demands the maximum: strong-typed evidence — `fact` and `observed_evidence` — at ACIS ≥ E3,
and for the L4 foundational tier, evidence re-derived by a **second substrate** (the ACIS
`T-ACIS-MODEL-CONSENSUS-001` requirement that E3→E4 needs a different actor, not consensus among
agents of the same model).

The principle in one line: **the harder a decision is to undo, the less the stack may lean on
weak-typed and low-level evidence to make it.** This is the numeric form of SDD-OS Parte V §10's
"mayor irreversibilidad → mayor rigor," but pushed down from the review-*tier* (which DRK-00 §II.3
already scales) into the evidence *burden* specifically.

### I.3 Blast radius as the burden's second dimension

Reversibility is necessary but not sufficient. A decision can be *technically* reversible yet have a
blast radius so wide that undoing it is expensive in a second currency — user trust, agent
coordination, downstream data. The Decision Blast Radius (DBR, computed in DRK-02) therefore acts as a
**burden multiplier** stacked on the reversibility base. A Tipo B decision with an isolated blast
radius keeps the Tipo B burden; the same Tipo B decision touching users, cost, and three downstream
agents is escalated toward the Tipo C burden even though its raw reversibility class is unchanged.
Criticality (the taxonomy axis for safety/security/data-integrity, DRK-00 §II.1) applies the same
ratchet: a data-integrity-critical decision inherits the strong-typed, second-substrate burden
regardless of its nominal Tipo, because a silent data-integrity error is functionally irreversible.

### I.4 The burden table

The kernel computes the burden for each decision at Stage 5 as a deterministic function of
(reversibility Tipo × effective criticality, where criticality is raised by blast radius). For each
cell the table fixes two thresholds: the **minimum count** of qualifying evidence items and the
**minimum type-class + ACIS level** each qualifying item must meet. `conditioning` items
(`constraint`, `uncertainty`, `unknown`) and `non-evidential` items (`preference`) never count toward
the burden count — they condition the decision but do not discharge its burden.

| Tipo × effective criticality | Min qualifying count | Min type-class of a qualifying item | Min ACIS level | Second-substrate required |
|---|---|---|---|---|
| **Tipo A · non-critical** | 0 (record the gamble) | any, incl. `assumption` (flagged) | E0 | no |
| **Tipo A · critical** | 1 | ≥ `inference` from checked `fact` | E2 | no |
| **Tipo B · non-critical** | 1 | ≥ `inference` | E2 | no |
| **Tipo B · critical** | 2 | ≥ 1 `observed_evidence` + 1 `fact`/`inference` | E3 | no |
| **Tipo C · non-critical** | 2 | ≥ 1 `fact` + 1 `observed_evidence` | E3 | recommended |
| **Tipo C · critical (L4)** | 2 strong + 0 unmet | both strong-typed (`fact` ∧ `observed_evidence`) | E3 | **yes** (ACIS `T-ACIS-MODEL-CONSENSUS-001`) |

Two design choices in this table are load-bearing. First, the **Tipo A · non-critical** cell requires
*zero* qualifying evidence — it is legitimate to make a cheap, reversible decision on an explicit
`assumption`, provided the assumption is *recorded as such*. This is the answer to DRK-00 §III.6's open
question ("the minimum evidence burden below which even a Tipo-A decision should be recorded as a known
gamble"): the floor is not "gather evidence," it is "name the bet." A Tipo A decision with zero
evidence is not blocked and not faulted; it is written to the Record as a **known gamble** — a decision
the stack consciously made blind because blindness was cheap. Second, the **Tipo C · critical (L4)**
cell is the *only* cell where the burden being unmet can escalate past a recommendation to a block, and
even there the block fires only under the DRK-00 block-narrow rule: **block iff Tipo-C AND evidence <
ACIS E3.** Every other unmet-burden cell yields `REQUEST-EVIDENCE` as a recommendation, never a block.

### I.5 REQUEST-EVIDENCE — naming exactly what is missing

When the supplied evidence fails to meet the burden for its cell, Stage 5 sets a provisional
`REQUEST-EVIDENCE` verdict (DRK-00 §II.2). The mechanism's non-negotiable property is that the verdict
**names exactly which evidence is missing**, computed as the *set difference* between the burden cell's
requirement and what the Decision Object actually carries. It does not say "insufficient evidence"; it
says, for example: "Tipo B · critical requires ≥1 `observed_evidence` at E3; the object carries two
`inference` items at E2 and one `assumption` — missing: one `observed_evidence` item, e.g. a measured
run of the affected path." This precision is what makes `REQUEST-EVIDENCE` a *routing* verdict rather
than a rejection: it hands the caller a concrete, minimal shopping list — the smallest evidence
acquisition that would discharge the burden — instead of an opaque "no." An authority that says "not
enough evidence" without naming the gap is the review theater DRK-01 §III.4 guards against; the set
difference is the anti-theater mechanism.

The pipeline still *completes* after emitting the provisional `REQUEST-EVIDENCE` (DRK-01 §Stage 5): the
Decision Record captures both the burden that was required and the exact gap, so that later — when the
missing `observed_evidence` arrives — the re-review is a delta, not a fresh review. The gap is
institutional memory, not a transient error string.

---

## PART II — CONFIDENCE CALIBRATION

### II.1 The DCS is derived, never author-supplied

The Decision Confidence Score (DCS, 0–100, DRK-00 §II.4) is computed by the kernel from the *required*
fields of the Decision Object; the author cannot set it, for the same No-Autopromotion reason ACIS
forbids a producer certifying its own claim. Self-supplied confidence is the confidence-inflation
failure mode (II.5): an author who could type "confidence: 95" would route their own decision away
from scrutiny. By deriving the DCS from the evidence and the alternatives, the kernel makes confidence
a *consequence* of the object's substance, not a claim about it.

The DCS is a weighted composition of four derived signals, each a direct mechanization of one or more
of the SDD-OS Parte V §9 inputs:

| Signal | What it measures | Parte V §9 input deepened | Direction |
|---|---|---|---|
| **Evidence weight** | Σ over evidence items of (type-class weight × ACIS-level weight), normalized by the burden count for the cell | *datos · evidencia · validación* | more strong-typed, higher-level evidence → higher DCS |
| **Alternatives explored** | count and genuineness of `options` vs `discarded_alternatives` (the Default Suspicion Rule made numeric) | *alternativas exploradas* | ≥2 genuine options with recorded rejection reasons → higher; a single option caps the DCS low |
| **Assumption/unknown load** | proportion of `assumption` + `unknown` + `uncertainty` items among all support | *riesgo* | higher proportion of conditioning/flagged items → lower DCS |
| **Strongest-support level** | the ACIS level of the highest-level supporting item | *evidencia (experiencia proxied by level)* | a single E3+ item lifts the ceiling; all-E2 support caps it |

The **evidence weight** signal is where the type distinction from DRK-00 §I.4 pays off: three
`assumption`s and three `observed_evidence` items both count as "three pieces of evidence" to a naïve
scorer, but the DCS weights the former near zero and the latter near the maximum, because their
type-classes (weak-flagged vs strong) and their ACIS levels differ. The **alternatives explored**
signal makes the Default Suspicion Rule numeric: a decision presented with one option and no discarded
alternatives cannot exceed a hard DCS ceiling (empirically set low), *regardless* of how strong its
single option's evidence is — because a well-evidenced answer to an unexamined question is still an
unexamined question. This is the calibration that stops a confident monoculture from scoring high.

### II.2 Confidence and reversibility are separate ledgers

The most important calibration invariant is that **the DCS and the reversibility class are separate
ledgers, and the review reasons over both independently.** They are not multiplied into a single
"safety" number, because they answer different questions and a blend would erase both. Four
combinations make the separation concrete:

| | Reversible (Tipo A) | Irreversible (Tipo C) |
|---|---|---|
| **Low DCS** | Fine — proceed. A cheap-to-undo decision is *allowed* to be low-confidence; that is precisely what reversibility buys you. Record it as a known gamble (I.4). | Danger zone. Low confidence + irreversible = the burden is almost certainly unmet → `REQUEST-EVIDENCE`, and at L4 critical, the block. |
| **High DCS** | Proceed freely; the DCS is barely consulted — reversibility already made the decision cheap. | Still requires the burden to be met. A high DCS does **not** waive the Tipo C strong-typed, second-substrate requirement. Confidence is not a substitute for evidence of the right type. |

The bottom-right cell is the subtle one and the reason the ledgers must stay separate: a high DCS on an
irreversible decision is *not* a green light. The DCS can be high because the author explored many
alternatives and holds several E2 inferences — genuinely good reasoning — while the Tipo C burden still
demands E3 second-substrate `observed_evidence` the object lacks. If confidence and reversibility were a
single number, that high DCS would drown the burden gap and let an irreversible, under-typed decision
through. Keeping them separate means the burden test (Part I) and the confidence signal (Part II) each
get a vote, and the burden test wins on irreversible decisions. The top-left cell is the mirror
insight: a *low* DCS must never *block* a reversible decision — DRK-00 §II.4 and the block-narrow rule
both forbid it. Blocking a cheap-to-undo decision because its confidence is low would destroy the entire
value of reversibility, which is the license to move fast and correct cheaply.

### II.3 The DCS is a proxy that routes attention, not a certifier

The DCS obeys the ACIS anti-Goodhart discipline (`T-ACIS-GOODHART-001`): it is a **proxy** and is
treated as one. Its job is to *route attention* — a low DCS on a consequential decision is a flag that
says "look here," a high DCS says "the substance is present, spend scrutiny elsewhere." It is not a
certifier: no DCS value, however high, certifies that a decision is correct, and no DCS value is the
ground-truth signal for anything. The ground-truth signals live elsewhere and the DCS points at them
rather than replacing them: the **burden test** (Part I) is the ground truth for "is this decision
adequately evidenced for its irreversibility," and the **CO-12 ratio / accountability scoring**
(SDD-OS Parte VI, prediction scored against realized outcome) is the ground truth for "was the reasoning
that produced this decision actually sound." The DCS proxies both and certifies neither.

Treating the DCS as a certifier is the specific way this mechanism could be Goodharted, so the doctrine
names the ground-truth pointer explicitly and refuses to re-derive it here: **confidence routes
attention; the burden test decides sufficiency; accountability decides soundness.** Anywhere the stack
is tempted to gate on the DCS number itself rather than on the burden or the outcome, it has mistaken
the proxy for the thing — exactly the failure ACIS `T-ACIS-GOODHART-001` was sealed to prevent, and DRK
inherits that pointer rather than restating its mechanics.

---

## PART III — INVARIANTS, FAILURE MODES, INTEGRATION

### III.1 Invariants (the mechanism holds these or it is broken)

1. **Burden-by-reversibility.** The evidence burden is a deterministic function of (Tipo ×
   effective criticality); a constant burden across Tipos is a defect. (I.4)
2. **Level is read, never set.** Every evidence item's E-level is read from the ACIS epistemic ladder;
   DRK never assigns or overrides a level. (I.1)
3. **DCS is derived.** The confidence score is computed from required fields; an author-supplied
   confidence is ignored and flagged. (II.1)
4. **Separate ledgers.** Confidence and reversibility are never blended into one number; the burden
   test wins on irreversible decisions, and a low DCS never blocks a reversible one. (II.2)
5. **Proxy, not certifier.** The DCS routes attention; sufficiency is decided by the burden test,
   soundness by accountability. (II.3)
6. **Block-narrow inheritance.** An unmet burden escalates past a recommendation to a block only in the
   Tipo-C-critical cell, and only under Tipo-C ∧ <E3. Every other unmet burden yields
   `REQUEST-EVIDENCE`. (I.4, DRK-00 block-narrow)
7. **Name the gap.** `REQUEST-EVIDENCE` always emits the exact set-difference of missing evidence, never
   an opaque "insufficient." (I.5)
8. **Record the gamble.** A Tipo A decision with zero qualifying evidence is recorded as a known gamble,
   not blocked and not faulted. (I.4)

### III.2 Failure modes and the guard for each

| Failure mode | Symptom | Guard |
|---|---|---|
| **Evidence theater** | Many evidence items listed, all `assumption`/`preference`; burden count "met" superficially | Conditioning and non-evidential items never count toward the burden count; only qualifying type-classes at the required ACIS level discharge it (I.4) |
| **Assumption laundering** | An `assumption` re-labeled `fact`/`inference` to clear a higher cell | The E-level is read from ACIS, not from the author's label; an unsupported claim cannot reach E3 by renaming (II.1, invariant 2) |
| **Confidence inflation** | Author asserts high confidence to skip scrutiny | DCS is derived from required fields; author-supplied confidence ignored (invariant 3); single-option decisions hard-capped (II.1) |
| **Burden gaming** | Decision mis-classified as Tipo A to attract the zero-evidence floor | Reversibility Tipo is derived by the DRK-02 classifier, not author-set; blast radius and criticality ratchet the effective burden upward (I.3) |
| **Proxy capture (Goodhart)** | Stack gates on the DCS number itself | Invariant 5; `T-ACIS-GOODHART-001` pointer to the ground-truth burden + accountability signals (II.3) |
| **Over-burden (the tax)** | Trivial reversible decisions asked for E3 evidence | Tipo A · non-critical burden is zero; scope-first (DRK-00 §III.1) keeps trivial choices at L0/L1 entirely |
| **Ledger blending** | A single safety number hides an unmet burden on a high-DCS irreversible decision | Invariant 4; the burden test and the DCS each vote; the burden wins on irreversible (II.2) |

### III.3 Integration with the stack (consumer ↔ provider)

- **Feeds DRK-01 Stage 5.** The burden table (I.4) *is* the mechanism DRK-01 §Stage 5 invokes; the
  provisional `REQUEST-EVIDENCE` verdict and its named gap flow into the Stage 9 precedence resolution.
  The DCS (Part II) is the value written to the Decision Object's `confidence` field and consulted by
  the routing and adversarial stages.
- **Consumes ACIS levels.** Every qualifying-count and burden comparison reads each Evidence item's
  E-level from the ACIS `epistemic_ladder`. DRK-03 supplies no level-assignment logic; it composes the
  levels ACIS owns into the burden test. This is the cleanest boundary in the family: ACIS says *how
  strong*, DRK-03 says *how much strength is required*.
- **Consumes DRK-02.** The reversibility Tipo and the DBR blast-radius magnitude that select the burden
  cell and the burden multiplier come from DRK-02; DRK-03 does not classify reversibility, it *prices
  evidence against* a reversibility class DRK-02 has already assigned. DRK-02 and DRK-03 are a
  provider/consumer pair: reversibility (DRK-02) sets the stakes, burden (DRK-03) sets the entry fee.
- **Consumes D2A for build decisions.** For a "should we build X" decision, the evidence supporting the
  build-vs-consolidate choice is burden-tested like any other; the D2A DUPE VERDICT is itself a strong
  `observed_evidence`-class input when it is measured, not asserted.
- **Feeds CO-12.** The DCS at decision time is one input the accountability layer (SDD-OS Parte VI)
  later compares against the realized outcome — a systematically over-confident DCS is a calibration
  error the accountability ledger surfaces, closing the loop between predicted confidence and observed
  soundness.

### III.4 Open questions (carried to DRK-07 / Generation-One)

- **Burden decay.** Does an `observed_evidence` item's contribution to the burden decay with age — is a
  measurement from six months ago still E3 for today's decision, or does staleness demote it? DRK-03
  currently reads the ACIS level as-of-now and leaves temporal decay to ACIS; whether the *burden* should
  impose its own freshness window is open.
- **Cross-decision evidence reuse.** When two decisions share a supporting `observed_evidence` item, does
  discharging one decision's burden "spend" the evidence, or is evidence non-rival across decisions? The
  Registry makes reuse traceable; the calibration consequence is unresolved.
- **DCS weighting drift.** The four-signal weights in II.1 are fixed by doctrine now; whether the
  accountability ledger (Parte VI) should be allowed to *tune* them from observed calibration error — and
  how to do so without the producer certifying its own proxy — is a Generation-One question for DRK-07.

### III.5 Done criteria for DRK-03

The evidence-burden-and-confidence mechanism is complete when: the burden table (I.4) is realized as a
deterministic function keyed on (Tipo × effective criticality) inside `decision_kernel.py` Stage 5;
qualifying-count excludes conditioning and non-evidential types; the burden comparison reads E-levels
from the ACIS `epistemic_ladder` and never assigns one; the DCS is computed from the four derived signals
with the author-supplied value ignored; a low DCS provably does not block a reversible decision while an
unmet Tipo-C-critical burden provably does block under Tipo-C ∧ <E3; and `REQUEST-EVIDENCE` emits the
exact set-difference of missing evidence in every unmet-burden case. Until the kernel demonstrably asks a
real Tipo-C decision for one named missing `observed_evidence` item — and lets a low-confidence Tipo-A
decision proceed as a recorded gamble in the same run — the separate-ledgers invariant is asserted but
not demonstrated, which is the exact doctrine-that-nothing-runs state DRK exists to leave behind.
