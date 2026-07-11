# DRK-00 — Foundations & Canonical Objects

> The root dataset of the Decision Review Kernel. It defines the objects, the taxonomy, the verdict
> ontology, and the three models (evidence, confidence, risk) that every other DRK dataset and the
> executable kernel consume. Nothing in DRK is well-formed unless it is expressed in the vocabulary
> fixed here. **Parent it DEEPENs:** SDD-OS Parte V §2 (Decision Object), §9 (Confidence Score),
> §10 (Reversible/Irreversible), §13 (Blast Radius), §21 (Governance Tiering) — named there in one
> line each, given mechanism here. **Cross-references (never re-narrated):** ACIS epistemic ladder
> (evidence levels), D2A engine (build/placement decisions), CO-03 (model routing), spec_gate
> (task tier), owner_queue (escalation).

---

## PART I — THE DECISION AXIS AND ITS CANONICAL OBJECTS

### I.1 What the Decision axis is, and the gap it closes

The Claude Power Pack has, by 2026-07, an axis for almost everything a session *does*: an axis for
its **cost** (CO), for the **epistemic status** of a claim (ACIS), for **duplication** (D2A), for
the **execution** of a frontier session (FIOS), for the **specification** a build obeys (SDD-OS).
What it lacks is an axis for the act that precedes all of them and determines whether they should
run at all: the **decision**. A decision is the selection of one path through a space of options
under uncertainty, with consequences the selector cannot fully see. Systems do not fail primarily
because code is wrong or requirements are missing; they fail because a decision was made invisibly,
impulsively, without alternatives, without recorded reasoning, or without regard to whether it could
be undone. SDD-OS Parte V states this thesis. DRK operationalizes it.

The Decision axis governs a single object — the **decision of consequence** — across its entire
lifecycle: *before* it is acted on (is it correct, necessary, proportional, reversible, evidenced?),
*at* the moment of action (is it recorded, classified, priced, matched against precedent?), and
*after* the outcome is known (was the reasoning that produced it actually sound, independent of
whether the outcome was lucky?). The axis exists because the three questions have three different
owners in most systems and therefore no owner at all: product intuition decides, an implementer
records nothing, and a retrospective — if it happens — judges the outcome and forgets the reasoning.
DRK makes the decision a first-class, auditable engineering asset with one home.

### I.2 The scope boundary — what is a "decision of consequence"

DRK does not review every choice. Reviewing the choice of a variable name would be the
`always-reject`/complexity bias the axis exists to prevent (see DRK-07). A choice enters DRK's scope
only when it crosses at least one **consequence threshold**:

| Threshold | Enters scope when |
|---|---|
| Reversibility | The choice is hard or impossible to undo without cost (Tipo B/C — see DRK-02) |
| Blast radius | The choice affects code, users, cost, infrastructure, roadmap, agents, or data beyond the immediate file |
| Irreversible identity | The choice fixes a public contract, a data schema, a name users will see, or an API others depend on |
| Precedent | The choice contradicts, reverses, or sets a precedent that future choices will cite |
| Evidence gap | The choice is being made under uncertainty the selector has not made explicit |

A choice that crosses **none** of these is **out of scope** and DRK returns `L0 — no review`
immediately. This is the load-bearing boundary: the axis is defined as much by what it refuses to
touch as by what it governs. A DRK that reviews trivial choices is not more complete — it is a tax
(DRK-07 §anti-capture). The kernel's first act is always the scope test, and the honest majority of
choices in any session fail it and pass through un-reviewed.

### I.3 The Decision Object — canonical schema

Every in-scope decision is instantiated as a **Decision Object** (`DEC-<n>`), the DEEPENed and
schema-fixed form of SDD-OS Parte V §2. It is the input to review. Its fields:

| Field | Type | Meaning | Required |
|---|---|---|---|
| `id` | `DEC-<n>` | stable identifier, append-only | yes |
| `statement` | text | the decision in one sentence: "we will X rather than Y" | yes |
| `problem` | text | the problem the decision serves; without it the decision cannot be judged proportional | yes |
| `options` | list | ≥2 considered options (the Default Suspicion Rule: even an obvious choice lists what it ignores) | yes |
| `chosen` | ref | which option was selected | yes |
| `rationale` | text | why chosen over the alternatives — the reasoning, not the outcome | yes |
| `accepted_risks` | list | risks knowingly taken on | yes |
| `discarded_alternatives` | list | options rejected + why | yes |
| `dependencies` | list | what this decision depends on / what depends on it | yes |
| `reversibility` | `A` \| `B` \| `C` | Tipo classification (DRK-02) | derived |
| `blast_radius` | struct | affected surfaces + magnitude (DRK-02) | derived |
| `evidence` | list of `Evidence` | the evidence supporting the choice (I.4, DRK-03) | yes |
| `confidence` | 0–100 | Decision Confidence Score (I.5) | derived |
| `predicted_consequences` | list | what the selector expects to happen, with horizon (DRK-04) | yes |
| `review_tier` | `L0…Ln` | routed review depth (II.3) | derived |
| `verdict` | Verdict | the review outcome (II.2) | derived |
| `owner_override` | struct \| null | if the Owner overrode the verdict: what, why, when | conditional |

The distinction between **required** (author-supplied) and **derived** (kernel-computed) fields is
itself a mechanism: the author cannot self-assign a low review tier or a high confidence; those are
computed from the required fields. This is the same No-Autopromotion discipline ACIS applies to
epistemic levels — the producer never certifies its own claim.

### I.4 The Evidence sub-object

Each element of `evidence` is an **Evidence** record with a `type` drawn from a fixed, ordered
epistemic vocabulary — the model of evidence the axis reasons over:

| Evidence type | Definition | Weight class |
|---|---|---|
| `fact` | verifiable, checked, present-tense true | strong |
| `observed_evidence` | measured from a real run, with a `(metric, source, value)` triple | strong |
| `inference` | a conclusion derived from facts by stated reasoning | medium |
| `hypothesis` | a proposed explanation not yet tested | weak |
| `prediction` | a claim about the future | weak |
| `assumption` | taken as true without support | weak, flagged |
| `preference` | a value judgment, not a truth claim | non-evidential |
| `constraint` | a fixed limit the decision must respect | conditioning |
| `uncertainty` | a named thing the selector does not know | conditioning |
| `unknown` | an acknowledged blind spot (a known-unknown) | conditioning |

The evidence model is deliberately not collapsed into a single "confidence" number at input; the
*types* are preserved because the review reasons differently over each — a decision resting on three
`assumption`s is not the same as one resting on three `observed_evidence` records, even if a naïve
scorer would rate both "3 pieces of evidence." DRK-03 defines the burden: how much and what type of
evidence a decision needs, as a function of its reversibility. The epistemic *level* of any evidence
item that has been through the pipeline is not re-derived here — it is read from ACIS (`E0…E7`),
which owns that ladder. DRK consumes ACIS levels; it does not fork them.

### I.5 The Decision Record — the after-object

A reviewed decision is written to the append-only **Decision Registry** as a **Decision Record**: the
Decision Object *plus* the review trace (which tier, which verdict, which sources cited, which guards
fired) *plus*, later, the accountability fields written when the outcome is known (the realized
consequences, the prediction-error score, the attribution — reasoning vs execution vs luck vs
context; SDD-OS Parte VI). The Record is the institutional-memory unit: five years later the
question "why did we decide this, what did we consider, and was the reasoning sound" is answered from
the Record without human memory. The Registry is append-only for the same reason UKDL is: a decision
retracted is a new Record that supersedes, never an erasure — the reasoning that was once acted on is
part of the permanent trace.

---

## PART II — TAXONOMY, VERDICT ONTOLOGY, AND REVIEW ROUTING

### II.1 The decision taxonomy — the seven axes of classification

A decision is classified along seven independent axes. The axes are independent because a decision
can be high on one and low on another (a cheap-to-build but irreversible schema choice is low-cost,
high-reversibility-risk), and conflating them is the E3 Layer-Flattening error the PP core warns
against. The kernel classifies on all seven; the review tier (II.3) is a function of the maxima.

| Axis | Low ⟶ High |
|---|---|
| **Impact** | cosmetic ⟶ foundational (touches core/auth/payment/identity) |
| **Scope** | one file ⟶ cross-repo / platform |
| **Reversibility** | Tipo A (trivially undone) ⟶ Tipo C (practically irreversible) |
| **Criticality** | non-blocking ⟶ safety/security/data-integrity critical |
| **Uncertainty** | fully known ⟶ deciding under acknowledged unknowns |
| **Blast radius** | isolated ⟶ affects users, cost, infra, roadmap, agents |
| **Identity/compat** | private/internal ⟶ fixes a public contract, schema, or user-visible name |

These seven are the DEEPEN of SDD-OS Parte V's scattered mentions (§10 reversibility, §13 blast
radius, §21 tiering) unified into one orthogonal classification. The taxonomy is what makes the
review *proportional*: rigor is spent where the axes are high and withheld where they are low.

### II.2 The verdict ontology — ten outcomes, with entry conditions

The review emits exactly one verdict. The ontology is closed (a verdict outside this set is a bug)
and each verdict has a **precise entry condition** — the mechanism that prevents the verdict from
being an opinion. The set is ordered from most-restrictive to least:

| Verdict | Entry condition (when the kernel emits it) |
|---|---|
| **REJECT** | The decision is unsound on its face: it contradicts a Hard Rule, a sealed veto (arch-decision COLLISION on a veto source), or a proven invariant. Reserved — rejection needs a cited contradiction, never a preference. |
| **REFRAME** | The stated `problem` is wrong or mis-scoped; the decision solves a non-problem or the wrong problem. The kernel returns the corrected framing, not a yes/no. |
| **REQUEST-EVIDENCE** | The evidence burden (DRK-03) for the decision's reversibility tier is unmet: too few, or too-weak-typed, evidence items. The kernel names exactly which evidence is missing. |
| **RUN-EXPERIMENT** | The uncertainty is resolvable cheaply by a test/probe/spike, and the decision's reversibility makes deciding-blind wasteful. The kernel proposes the experiment. |
| **DEFER** | The decision is not yet forced; deciding now spends optionality for no gain, or a dependency is unresolved. Also the fail-open verdict for pathological input. |
| **KEEP-LOCAL** | A proposal to generalize/platformize/centralize is premature; the local/duplicated form is correct for now (the D2A "temporary duplication acceptable" case; DRK-06 tension). |
| **CONSOLIDATE** | The decision duplicates an existing capability; D2A routing says the honest move is to reinforce/extend the existing one, not build anew. |
| **REMOVE** | The best action is to delete/retire rather than build or keep (D2A RETIRE; the "build nothing" answer). |
| **APPROVE-WITH-CONDITIONS** | Sound, but contingent: proceed *if* named conditions hold (a monitor, a rollback path, a re-review trigger). The conditions are recorded on the Record. |
| **APPROVE** | Sound, evidenced for its tier, reversibility-appropriate, no cited contradiction. |

The ontology answers the prompt's demand that the axis be able to conclude "build / don't build /
defer / experiment / keep local / consolidate / remove / the question is wrong" — each is a verdict
with a condition, not a mood. Note what the set encodes: **six of the ten verdicts are non-approval
and non-rejection.** An authority whose only outputs were APPROVE and REJECT would be the binary
gate DRK-07 forbids; the richness of the middle (REFRAME, REQUEST-EVIDENCE, RUN-EXPERIMENT, DEFER,
KEEP-LOCAL, CONSOLIDATE) is where a decision authority earns its keep.

### II.3 Risk-based review routing — L0 through Ln

Not every in-scope decision gets the full pipeline; that would be the cognitive tax again. The
kernel routes each decision to a **review tier** as a function of the taxonomy maxima. The tiers are
defined by the *rigor* they invoke, not an arbitrary number:

| Tier | Trigger (taxonomy maxima) | Review applied |
|---|---|---|
| **L0 — none** | crosses no consequence threshold (I.2) | pass-through; no Record |
| **L1 — record** | in-scope but all axes low; reversible (Tipo A) | instantiate Decision Object, write Record, no adversarial pass |
| **L2 — standard** | any axis medium; Tipo B; module scope | + reversibility & blast-radius compute, evidence-burden check, precedent-collision (arch-check) |
| **L3 — deep** | high impact OR high uncertainty OR system scope | + adversarial pass, counterfactual simulation (DRK-04), multi-perspective review |
| **L4 — foundational** | Tipo C (irreversible) OR identity/public-contract OR cross-repo/platform | + full block-gate authority, mandatory Owner routing, second-substrate evidence requirement (ACIS `T-ACIS-MODEL-CONSENSUS-001`) |

`Ln` is open by construction: a project that needs an `L5` (e.g. a regulated-data tier) defines it by
naming the trigger and the added rigor, without changing L0–L4. The routing is the operational core
of "mayor irreversibilidad → mayor rigor" (SDD-OS Parte V §10) and the risk-based-review-router
capability from the proposal — realized as a deterministic function of the taxonomy, not a judgment.
The kernel's authority to **block** (refuse to let a decision proceed autonomously) exists **only at
L4** and only under the twin condition *Tipo-C irreversible ∧ evidence < ACIS E3*. At every other
tier the kernel **recommends**; the Owner or the calling agent decides. This single asymmetry —
block-narrow, recommend-wide — is the constitutional limit of the authority, sealed in
`PR-DECISION-AUTHORITY-LIMITS-001` and elaborated in DRK-07.

### II.4 The confidence model — Decision Confidence Score

The **DCS** (0–100, DEEPEN of SDD-OS Parte V §9) is *derived*, never author-supplied. It is a
function of: the count and weight-class of evidence items (I.4), the number of genuine alternatives
explored (a decision with one option caps low — the Default Suspicion Rule made numeric), the
proportion of `assumption`/`unknown` conditioning items, and the ACIS epistemic level of the
strongest supporting evidence. The DCS is a *proxy* and is treated as one (ACIS `T-ACIS-GOODHART-001`):
it routes attention, it does not certify. A high DCS on a Tipo-C decision still triggers L4; a low
DCS never *blocks* a reversible decision (cheap-to-undo decisions are allowed to be low-confidence —
that is what reversibility buys). Confidence and reversibility are separate ledgers, and the review
reasons over both; DRK-03 gives the burden mechanics, DRK-02 the reversibility mechanics.

---

## PART III — INVARIANTS, STATES, FAILURE MODES, INTEGRATION

### III.1 Invariants (the kernel holds these or it is broken)

1. **Scope-first.** The kernel's first act is the I.2 scope test; an out-of-scope choice is `L0` and
   is never instantiated. (Prevents the tax.)
2. **No self-certification.** `review_tier`, `reversibility`, `blast_radius`, `confidence`, and
   `verdict` are derived; an author cannot set them. (No-Autopromotion, inherited from ACIS.)
3. **Block-narrow.** The kernel blocks only at L4 under Tipo-C ∧ <E3. Any block outside this is a
   defect, not a stricter policy. (Constitutional limit.)
4. **Record-or-passthrough.** Every review at L1+ writes a Record; every L0 writes nothing. There is
   no in-between "reviewed but unrecorded" state.
5. **Override-recorded.** An Owner override never mutates the original verdict; it appends an
   `owner_override` struct. The disagreement is part of the permanent trace.
6. **Cross-ref, not re-narrate.** Evidence levels come from ACIS, placement from D2A, routing from
   CO-03. The kernel cites; it does not re-implement. (GK-00 one-system.)
7. **Fail-open.** Pathological, unparseable, or contradictory input yields `DEFER`, never a raise and
   never a silent APPROVE. (Same discipline as every PP engine.)

### III.2 States of a decision

`PROPOSED` (Decision Object instantiated) → `ROUTED` (tier assigned) → `REVIEWED` (verdict emitted) →
`ACTED` (verdict acted on, or overridden) → `OBSERVED` (outcome known; accountability written) →
`ATTRIBUTED` (reasoning/execution/luck/context separated; Parte VI). A decision may be `SUPERSEDED`
by a later Record at any point after `REVIEWED`. There is no `DELETED` state — the Registry is
append-only.

### III.3 Failure modes and the guard for each

| Failure mode | Symptom | Guard |
|---|---|---|
| Review theater | Everything gets APPROVE | `V-DRK-3-BIAS` never-reject scenario must produce a non-APPROVE |
| The tax | Trivial choices reviewed | I.2 scope-first invariant; L0 pass-through |
| Complexity bias | Everything routes to platform/CONSOLIDATE | DRK-07 always-platform bias scenario |
| Block creep | Kernel blocks reversible decisions | Invariant 3; `V-DRK-BLOCK-GATE` asserts block iff Tipo-C ∧ <E3 |
| Outcome-only judgment | A lucky bad decision counts as a win | Parte VI attribution; reasoning ledger separate from outcome ledger |
| Self-certification | Author sets low tier to skip review | Invariant 2; derived fields |
| Re-narration bloat | DRK re-explains ACIS/D2A | `V-DRK-CROSS-REF-NOT-RENARRATE` |

### III.4 Integration with the stack (consumer ↔ provider)

- **Consumes:** arch-decision `arch_check` (precedent COLLISION/WARNING on a candidate decision) ·
  spec_gate `classify_tier` (task tier as one taxonomy input) · d2a_engine (for build/placement
  decisions: the DUPE VERDICT and CONSOLIDATE/KEEP-LOCAL/REMOVE recommendation) · ACIS
  `epistemic_ladder` (evidence level of each Evidence item) · CO-03 router (what model, if any, the
  review itself should cost) · owner_queue (L4 escalation transport).
- **Provides:** the Verdict + the Decision Record to the calling agent; the accountability signal to
  CO-12 (a decision whose prediction was scored is a readiness data point); the precedent (each
  Record becomes a future arch-check source).
- **Invocation:** a calling agent (or a future `kclaude`/Stop-chain hook) hands the kernel a
  candidate decision; the kernel is **advisory and fail-open by default** (rung-1/2 in CO-10 terms),
  escalating to a **block** only at L4. It never fires autonomously on a trivial choice, and it never
  blocks a reversible one.

### III.5 Done criteria for DRK-00

The foundations are complete when: the Decision Object and Decision Record schemas are fixed and
consumed by `decision_record.py`; the seven-axis taxonomy, the ten-verdict ontology, and the L0–Ln
routing are each realized as deterministic functions in `decision_kernel.py`; the evidence and
confidence models are wired to ACIS levels; and `V-DRK-RECORD-CANONICAL`, `V-DRK-VERDICT-ONTOLOGY`,
and `V-DRK-DEPTH` pass ×3 hermetic. Until the kernel instantiates and records a real decision, DRK-00
is doctrine, not an operating floor — and doctrine that nothing runs is exactly the state SDD-OS
Parte V was found in at STOP #1.

### III.6 Open questions (carried to DRK-07 / Generation-One)

- How does the kernel detect a decision that *should* have been in scope but was never presented to
  it? (The unknown-unknown of decisions; cross-ref FIOS II-1.)
- When two Records conflict (a precedent reversal), how is the superseding reasoning weighted against
  the precedent it overturns? (DRK-05 precedent registry + DRK-07 override evaluation.)
- What is the minimum evidence burden below which even a Tipo-A decision should be recorded as a
  known gamble rather than a decision? (DRK-03.)
