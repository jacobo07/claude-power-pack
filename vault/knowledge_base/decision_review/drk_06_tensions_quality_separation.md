# DRK-06 — Irreducible Tensions & Quality-Type Separation

> Two models the kernel needs to avoid its own worst failure: pretending a decision has a right
> answer when it has a *balance point*, and blaming the wrong ledger when something goes wrong.
> Part I formalizes the irreducible tensions a decision sits on — pairs of goods that cannot both be
> maximized, only traded — so the review forces an explicit position instead of a hidden default.
> Part II separates the six kinds of quality a system confuses at its peril, so that a bad outcome is
> attributed to the right ledger. **Parent it DEEPENs:** SDD-OS Parte V had no tension model and no
> quality-type separation; this is a genuine extension, not a restatement. **Cross-references (never
> re-narrated):** D2A (owns the build/keep/generalize decision), Parte VI (owns outcome attribution),
> code_review (owns implementation quality), spec_gate/SDD-OS (own specification quality), CO
> (owns operational cost), FD (owns learning quality).

---

## PART I — THE IRREDUCIBLE TENSIONS

### VI.1 Why a decision authority must name tensions, not resolve them

The failure that most discredits a decision authority is the pretense of a universally right answer.
"Always prefer simplicity," "always reuse," "always keep optionality open" — each is true until it
is not, and an authority that hard-codes one side of a trade becomes the bias DRK-07 warns against
(always-platform, always-consolidate). The mature move is the opposite: to recognize that most
consequential decisions sit on an **irreducible tension** — a pair of genuine goods that cannot both
be maximized, where more of one is necessarily less of the other — and that the authority's job is
not to pick the winning side in the abstract but to *make the trade explicit and appropriate to this
decision's context*. A tension is irreducible when no amount of cleverness dissolves it; it can only
be positioned. The kernel's contribution is to detect which tension a decision sits on, force the
decider to state a position, and check that the position fits the decision's reversibility, blast
radius, and horizon rather than an ambient habit.

### VI.2 The tension catalog

Each tension is a pair `A ↔ B` where a decision must choose a point on the line between them. The
catalog is not exhaustive by construction — a project may name a new tension — but these are the ones
that recur across the stack:

| Tension | Pull toward A | Pull toward B | When A wins | When B wins |
|---|---|---|---|---|
| **Optionality ↔ Simplicity** | keep future paths open | fewer moving parts now | irreversible/high-uncertainty decisions | reversible, well-understood decisions |
| **Reuse ↔ Coupling** | one implementation, DRY | independent, decoupled parts | stable, proven abstraction | divergent needs, premature abstraction (D2A KEEP-LOCAL) |
| **Consistency ↔ Autonomy** | one way across the stack | each part decides locally | cross-cutting contracts, public interfaces | local concerns with no downstream contract |
| **Speed ↔ Evidence** | decide and move | gather more proof first | reversible, cheap-to-undo (DRK-02 Tipo A) | irreversible, high blast radius |
| **Reversibility ↔ Performance** | keep the exit open | commit for efficiency | uncertainty is high | the path is proven and the cost of the option is real |
| **Governance ↔ Autonomy** | review, record, gate | let the agent proceed | Tipo-C ∧ under-evidenced (the block case) | everywhere else (recommend-wide) |
| **Generality ↔ Fit** | solve the class | solve exactly this | the class is real and recurring | the class is speculative; YAGNI |
| **Centralization ↔ Locality** | one home, one owner | distributed, near the use | shared contract, single source of truth | independent lifecycles, blast-radius isolation |

### VI.3 How the kernel uses the catalog

At L3+ the review identifies which tension(s) a decision sits on and requires the Decision Object's
`rationale` to state a *position*, not a default. A decision that generalizes a capability is sitting
on Generality↔Fit and Reuse↔Coupling; the review checks that the position (generalize) is warranted
by a *real, recurring* class rather than a speculative one — and if it is not, the D2A engine's
KEEP-LOCAL verdict (which owns exactly this call) is the outcome. A decision to commit to an
irreversible optimization sits on Reversibility↔Performance; the review checks that the performance
gain is proven and the lost option is genuinely not needed, escalating to L4 if the commit is Tipo-C.
The tension model is therefore not a philosophy section — it is the mechanism that converts "this
feels over-engineered" into "this decision took the Generality side of Generality↔Fit on a
speculative class, which is premature abstraction." The vague aesthetic judgment becomes a named,
checkable position, which is the difference between a design opinion (DRK-07 forbids) and a design
criterion.

### VI.4 The meta-rule: match the position to the decision's physics

The single principle that governs every tension: **let the decision's reversibility, blast radius,
and horizon pick the side, not the decider's habit.** High reversibility buys speed over evidence,
simplicity over optionality, locality over centralization — because being wrong is cheap. Low
reversibility inverts all three — because being wrong is permanent. This is why DRK-02 (reversibility)
and DRK-04 (horizon) are prerequisites to DRK-06: the tension position is a *function* of the
decision's physics, and a review that positioned a tension without first classifying the decision's
reversibility would be guessing. A decider who always takes the same side of a tension regardless of
the decision's physics has a bias, and that bias is detectable in the Record population (Parte VI
calibration, DRK-07 §II.4).

---

## PART II — QUALITY-TYPE SEPARATION

### VI.5 Six qualities, six ledgers, six owners

When something goes wrong, the reflex is to ask "was that a good decision?" — but the question is
under-specified, because a delivered system's quality is the product of six distinct qualities, each
owned by a different part of the stack, each failing independently. Conflating them is the deepest
form of the attribution error Parte VI addresses: it blames the decision for an implementation bug,
or credits the reasoning for an operational win. The six:

| Quality | Question | Owner in the stack |
|---|---|---|
| **Decision quality** | Given what was knowable, was this the right choice? | DRK (this axis) |
| **Specification quality** | Was the chosen thing specified correctly and completely? | SDD-OS / spec_gate |
| **Implementation quality** | Was the spec built correctly, cleanly, safely? | code_review / UQF |
| **Operational quality** | Does it run reliably and affordably in production? | monitoring / CO / liveness |
| **Outcome quality** | Did the result meet the goal? | Parte VI (the outcome ledger) |
| **Learning quality** | Did we extract durable knowledge from it? | FD / compound-learnings |

Each is owned by a system that already exists; DRK-06 does not build six quality evaluators — it
provides the **separation model** so that a failure is routed to the ledger that actually owns it. A
correct decision (DRK), correctly specified (SDD-OS), badly implemented (code_review), is an
implementation failure — and calling it a bad decision would teach the wrong lesson and degrade the
decision authority's calibration with noise it does not own.

### VI.6 The separation mechanism

The kernel separates the qualities by tracing a delivered result backward through the stack's own
artifacts, each of which is owned by a different system, and asking at each layer whether *that*
layer held:

- **Decision layer** — did the Decision Record's reasoning hold given what was knowable? (DRK + Parte
  VI reasoning residual.)
- **Specification layer** — did the spec capture the decision correctly? (SDD-OS contracts /
  invariants; a gap here is a spec failure, not a decision failure.)
- **Implementation layer** — did the code match the spec? (code_review; a gap here is an
  implementation failure. This reuses the Parte VI execution-isolation step.)
- **Operational layer** — did it run within cost/reliability? (CO / monitoring; a gap here is
  operational.)
- **Outcome layer** — did it meet the goal? (Parte VI outcome ledger.)
- **Learning layer** — was the lesson captured? (FD; a gap here is a learning failure — the decision
  and its outcome taught nothing durable.)

The mechanism is deliberately a *router*, not a re-implementation: each layer's verdict is read from
the system that owns it. DRK-06's genuine contribution is the insistence that the layers are separate
and the trace that keeps them so — which is exactly the cross-ref-not-re-narrate discipline the whole
corpus obeys, applied to the concept of quality itself.

### VI.7 Why the separation is load-bearing for the authority

The separation is not academic. It is the precondition for the authority to audit its own decision
quality honestly (DRK-07 §VII.6): a high-confidence decision that ended badly can only teach the
decision authority something if the badness is *attributable to the decision layer* and not to a
downstream implementation or operational failure. Without the six-way separation, every downstream
failure would contaminate the decision authority's calibration, and it would learn to be gun-shy
about decisions that were, in fact, sound. Quality-type separation is therefore the firewall that
keeps the decision ledger clean enough to be worth calibrating — the same role reversibility plays for
the evidence burden and attribution plays for the outcome.

---

## PART III — INVARIANTS, INTEGRATION, DONE CRITERIA

### VI.8 Invariants

1. **Tensions are positioned, never resolved in the abstract.** The kernel forces an explicit
   position and checks its fit; it never hard-codes a winning side.
2. **Position follows physics.** A tension's position is a function of the decision's reversibility,
   blast radius, and horizon — not the decider's habit.
3. **Six qualities, separately owned.** No failure is attributed to a ledger that does not own it;
   each layer's verdict is read from its owning system.
4. **Separation is a router, not a rebuild.** DRK-06 traces; it does not re-implement spec, code,
   operational, or learning evaluation.
5. **Keep the decision ledger clean.** Downstream failures never contaminate decision-quality
   calibration; that is the whole point of the separation.

### VI.9 Failure modes and guards

| Failure mode | Symptom | Guard |
|---|---|---|
| Hidden default | A tension decided by habit, unstated | L3+ requires an explicit position in the rationale |
| Aesthetic verdict | "Feels over-engineered" with no criterion | tension catalog names the position (Generality↔Fit); DRK-07 forbids opinion |
| Quality conflation | Implementation bug blamed on the decision | six-way separation router; Parte VI execution isolation |
| Calibration contamination | Decision authority spooked by downstream failures | invariant 5; only decision-layer failures update decision calibration |
| Tension monism | Always the same side of a tension | Parte VI population calibration flags the bias (DRK-07 §II.4) |

### VI.10 Integration and done criteria

DRK-06 is consumed by DRK-01 Stage 8 (the adversarial pass names the tension and checks the position)
and by DRK-07 (bias detection over tension positions). It consumes DRK-02 (reversibility/blast) and
DRK-04 (horizon) to know which side of a tension the decision's physics favors, D2A for the
build/keep/generalize verdict when a decision sits on Reuse↔Coupling or Generality↔Fit, and Parte VI
for the quality-separation trace. It is done when the tension catalog is wired into the L3+ review so
that a decision sitting on a tension cannot be APPROVEd without a stated, physics-appropriate
position; when the six-way quality router reads each layer's verdict from its owning system rather
than re-deriving it; and when a decision whose downstream implementation failed is shown *not* to
degrade the decision-quality calibration (the firewall observably holds). Open questions for
Generation-One: whether the tension catalog should be project-extensible at runtime or fixed; and
whether a decision sitting on three or more tensions at once should be automatically escalated a tier,
on the theory that multi-tension decisions are inherently harder to position correctly.
