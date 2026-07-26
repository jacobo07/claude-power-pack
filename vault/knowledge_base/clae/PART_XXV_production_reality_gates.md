---
title: "CLAE Part XXV — Production Reality Gates"
family: clae
part: XXV
depends_on: [XXIII, XXIV]
feeds: [XXVI]
status: SEALED
date: 2026-07-26
---

# Part XXV — Production Reality Gates

## 1. Purpose

Nineteen gates were seeded across Parts I through XXIV, counted from the sealed text rather than
recalled. This Part consolidates them into an implementable set, states the contract every gate must
satisfy, resolves the floor-gate-eval distinction that has been implicit since Part III, and
establishes the mechanic that lets a non-blocking gate have force: **label propagation**.

Nineteen gates is the accumulation problem in its final form. A gate per rule, at nineteen different
moments, is not a design — it is a list of good intentions that will be implemented at three of the
nineteen points and assumed at the rest.

## 2. Floor, gate, eval — the final disambiguation

Three objects, repeatedly conflated because in practice they are often one piece of machinery.

| | Floor | Gate | Eval |
|---|---|---|---|
| What it is | A minimum an artifact must clear | A decision point emitting a verdict | A check that a rule is followed |
| Subject | The artifact | The artifact, at a moment | The process |
| Source | Domain derivation (Part XI) | The lifecycle | The rule set (Part XXIII) |
| Output | Clear or not | Admit, or admit-with-label | Compliant, non-compliant, could-not-run |

> **Floors are the criteria. Gates are the mechanism. Evals verify the mechanism runs.**

Separating them in the *record* is what makes each debuggable, even when one script performs all
three. A failing check is otherwise ambiguous between a bad artifact, a broken gate and a violated
process rule, and those have three different remedies.

## 3. The gate contract

Every gate specifies:

1. **Trigger point** — the moment in the lifecycle it fires.
2. **Inputs consumed** — which residuals, records and declarations it reads.
3. **Verdict values** — including could-not-run, per Part XIII §7.
4. **Failure action** — block or label, per §5.
5. **Bypass route** — the deviation path, per Part XVIII, or none.
6. **Owner** — who maintains it and answers for its coverage.

Field four is the central design decision, and this family has answered it consistently.

## 4. Consolidation: nineteen gates, four gate points

The nineteen seeded gates group naturally by *when they fire*, and a gate point consuming several
checks is implementable where nineteen separate gates are not.

**G1 — Measurement Admission.** Fires before a residual enters the ledger. Consumes the reference
integrity, provenance integrity, extraction integrity and instrument integrity checks. Answers: *is
this number interpretable?*

**G2 — Artifact Admission.** Fires before an artifact ships. Consumes the underbuild floor check, the
floor derivation check and the deviation integrity check. Answers: *is this a real implementation,
and is what it lacks recorded?*

**G3 — Closure.** Fires before a unit is declared closed. Consumes residual visibility, phase
closure, oracle boundary, ranking integrity and correction cycle. Answers: *does the closing
statement say what remains?*

**G4 — Autonomy Entry.** Fires before autonomous work begins. Consumes Phase Zero, autonomy entry,
toolsmith, incident conversion, eval integrity, trap registry, rule registry and lineage position.
Answers: *can this system's output be checked at all?*

Four points, nineteen checks, one lifecycle. The consolidation loses nothing — every seeded gate
survives as a check within a point — and gains the property that four trigger points can actually be
wired.

## 5. Block or label

Of the nineteen seeded gates, the large majority specify **label, not block**. That was not
incidental; it is Part II §9 operationalized:

> **Distance informs. Floors enforce.** A gate reading distance-derived evidence labels. A gate
> reading a floor blocks.

G2 is the blocking gate, because floors are admissibility criteria and a violated floor with no
available deviation means the artifact is not admissible. G1, G3 and G4 label, because their subject
is the interpretability and completeness of *evidence*, and blocking on incomplete evidence stops
work that may be entirely sound.

Three arguments for labelling where the subject is evidence rather than admissibility:

**A block will be negotiated; a label cannot be argued down.** Blocking creates pressure, and the
pressure resolves against the gate — the bar is lowered, the check is bypassed, or the gate is
disabled. A label produces no pressure because it stops nothing, and so it survives.

**A label costs nothing to produce.** It is a field on an existing record.

**A label travels.** A block is a moment; once passed, nothing about it persists. A label attaches to
the claim and moves with it into whatever consumes it downstream.

## 6. Label propagation — what gives a non-blocking gate teeth

The mechanic that makes §5 work rather than making gates advisory:

> **A claim built on a labelled input inherits the label.**

A residual admitted as *unverified* propagates that label to every ranking, trend and closure that
consumes it. A closure marked *accounting-only* propagates to any release claiming that unit is done.
A quality claim from a system labelled *structurally unfalsifiable* carries that label wherever it is
cited.

Propagation is what makes labelling comparable in force to blocking without its costs. A block stops
one action; a label degrades every conclusion drawn from the flawed input, permanently and
automatically, and it does so at the point where someone is relying on it rather than at the point
where someone is producing it.

The label set this family uses:

| Label | Meaning |
|---|---|
| **Unverified** | The measurement may be right; nothing established that it could have been wrong |
| **Uninterpretable** | Missing pin, mode or coverage; the number cannot be read |
| **Self-certified** | Every judgment in the chain was answered by the system |
| **Structurally unfalsifiable** | Internal criteria plus verification that cannot fail — Part XXI's confident-blind compound |
| **Accounting-only** | The producer closed the accounting; no constituency accepted |
| **Provisional** | An imposed floor or borrowed threshold with the derivation owed |

Each is a statement about *what is known about the claim*, never about whether the claim is true. A
self-certified claim may be entirely correct. The label says only that nothing outside the system
could have contradicted it, which the reader is entitled to know.

## 7. Gates are instruments too

The recursion applies here as it has everywhere: a gate is an instrument, so Part XIII's contract
holds. Coverage, envelope, three-valued output, and a negative control per Part XXIV §5.

The arity requirement is not optional decoration at this level. **A gate that cannot report it did
not run is the exact mechanism of Part X §6's decorative floor and Part XXI's L6 lineage** — the gate
reports clean, the floor shows no violations, the floor is retired as unnecessary, and the protection
disappears with its removal justified by the evidence of its own broken instrument.

Every one of the four gate points must therefore emit could-not-run as a first-class verdict, and
that verdict must propagate as a label like any other.

## 7a. Gate decay

Every accumulating object in this family goes stale, and gates decay in a way distinct from the
instruments inside them.

**The trigger point moves.** A gate fires at a moment in a lifecycle, and lifecycles change. A gate
wired to a step that has been reorganized away does not report an error — it simply stops firing, and
its last recorded verdict was clean. This is the most common gate failure and it is silent by
construction, which is why §13's trigger-wiring probe checks that something fires there rather than
checking that the gate exists.

**The subject moves out of scope.** A gate's checks were chosen against the artifacts of the time. As
the work changes, artifacts appear that the gate was never designed to examine and that it passes
without objection, because they exercise none of its checks. Coverage that was adequate becomes
partial, and nothing in the verdict distinguishes the two.

**The floor beneath it is re-derived.** A blocking gate enforces floors, and Part XI §9 requires
floors to be re-derived when their consequence changes. A gate still enforcing a superseded floor
blocks the wrong things and permits the right ones, with complete confidence in both directions.

The control is the same as everywhere: each gate point records a validity horizon and a re-validation
date, and re-running its negative control is what detects all three decay modes at once. A gate whose
negative control still fires is wired, in scope for at least that case, and enforcing something. A
gate whose negative control silently passes has decayed, and the moment it did so is not otherwise
recoverable.

## 8. Boundary

Gates are wrong for genuinely exploratory work, where the artifact is declared throwaway and the
declaration is enforced against silent graduation, per Part XII §9.

They are wrong where the gate costs more than the failure it prevents — the same economics as floors
(Part X §8) and instruments (Part XIV §4).

And they are wrong where the check is a judgment. A gate implementing an oracle question will verify
that a determination was made rather than that it was correct, per Part XXIV §9a, and will report
compliance whenever the field is filled.

## 9. Evidence — gate surfaces in this stack

| Surface | Verdict shape | Subject |
|---|---|---|
| Secret firewall | **Block** | A prohibition — correctly absolute |
| Marker-token detector | **Block** | A prohibition |
| Completion gates | **Pass/fail** | Floors and process steps |
| Compiled hard-rule digest at four declared triggers | **Stop** | Prohibitions and invariants |
| Artifact done gate | **Pass/fail** | A declared artifact set |
| Reachability gate | **Pass/fail** | Module reachability |
| This build's per-Part gate | **Pass/abort** | Content floors |

Every gate in this stack is **binary and blocking**. There is no labelling gate anywhere.

That is correct for most of them — prohibitions and invariants *should* block, and the digest firing
at declared triggers is a well-designed layer-two mechanism for exactly that. But it means the stack
has no way to ship something with a recorded qualification. An artifact is either admitted cleanly or
refused, and the middle state — *admitted, and here is what is unknown about it* — has no
representation.

This is the same shape as three earlier findings, now at the gate layer: Part XX found closure had
two verdicts where five were needed; Part XIII found instruments had two outputs where three were
needed; Part XXIII found rules had one force where five layers exist. In each case the missing
expressiveness caused the true state to be reported as its nearest available neighbour, and the
neighbour was always the more favourable one.

> **A system with only blocking gates cannot express a qualified pass, so every qualified pass is
> recorded as a clean one.**

The remedy is additive and small: a label field on existing gate outputs, and propagation of that
field into whatever consumes the result. No existing gate needs to change its verdict. — Gate
behaviours OBSERVED from the enforcement surfaces and this session's own gate; the absence of a
labelling path INFERRED across the observed set.

## 10. Failure modes

| Failure | Mechanism |
|---|---|
| **Gate per rule** | Nineteen trigger points; three get implemented and the rest are assumed |
| **Blocking on evidence quality** | Pressure resolves against the gate; the bar is lowered or the check disabled |
| **Labels that do not propagate** | A qualification recorded once and lost at the first consumer |
| **Two-valued gate** | Could-not-run reported as clean; the decorative-floor mechanism |
| **No negative control** | A gate never shown to fail, indistinguishable from one that cannot |
| **Floor, gate and eval conflated in the record** | A failing check is ambiguous among three remedies |
| **Judgment gated** | A gate verifying that a determination exists rather than that it is right |
| **Binary-only vocabulary** | Qualified passes recorded as clean passes, always in the favourable direction |

## 11. Detection signatures

1. **The unlabelled pass.** Every gate output is a boolean. Qualified states have nowhere to go.
2. **The orphaned qualification.** A label recorded at one gate and absent from every downstream
   claim built on it.
3. **The negotiated block.** A blocking gate whose threshold has moved downward over time.
4. **The never-red gate.** No failure in memory and no negative control.
5. **The assumed trigger.** A gate specified in doctrine with no wiring at its trigger point.

## 12. Rule seeds — for Part XXIII

- **PR-CLAE-GATE-POINTS-NOT-GATES** — checks are consolidated into a small number of lifecycle gate
  points. A gate per rule is recorded as unimplemented doctrine.
- **PR-CLAE-LABEL-EVIDENCE-BLOCK-FLOORS** — gates reading distance-derived evidence label; gates
  reading floors block. Blocking on evidence quality creates pressure that resolves against the gate.
- **PR-CLAE-LABELS-PROPAGATE** — a claim built on a labelled input inherits the label. A label that
  does not propagate is a note.
- **PR-CLAE-GATES-ARE-INSTRUMENTS** — every gate declares coverage, emits could-not-run, and carries a
  negative control demonstrated within its re-validation interval.
- **PR-CLAE-SEPARATE-THE-THREE** — floor, gate and eval are distinguished in the record even when one
  mechanism performs all three.

## 13. Eval seeds — for Part XXIV

- **Trigger-wiring probe.** For each specified gate point, verify something fires there. Doctrine-only
  gates are the most common finding in any consolidated set.
- **Propagation probe.** Label an input deliberately and trace whether downstream claims inherit it.
  Non-propagating labels are notes with no force.
- **Gate-arity probe.** Confirm each gate point emits could-not-run.
- **Gate negative control.** Present each gate point with a deliberately failing artifact and confirm
  it fires — the same discipline Part XXIV §9 applied to this build's own gate.
- **Threshold-drift probe.** For blocking gates, examine whether their thresholds have moved
  downward. Downward drift is the negotiated-block signature.

## 14. Pseudoflow — implementing the four gate points

Wire the trigger points first, before any checks. Four points with nothing behind them is a skeleton
that can be filled; nineteen checks with no trigger points is doctrine.

At each point, declare the verdict values including could-not-run, and decide block or label by the
subject: floors block, evidence labels. Do not block on evidence quality — the pressure will resolve
against the gate and the gate will lose.

Implement label propagation before implementing the checks. A label that does not travel is a note,
and propagation is the property that makes non-blocking gates worth building at all. Every consumer
of a gated result must carry the labels of its inputs.

Give each gate point a negative control: an artifact that should fail it. Run it. A gate never
observed to fire is indistinguishable from one that cannot, and this costs minutes once.

Record each check's origin — which floor, which rule, which eval it derives from — so a failure names
its remedy rather than merely its symptom.

Assign an owner per gate point, who answers for its coverage and re-runs its negative control when
its environment changes.

Finally, publish what each gate point does **not** check. A gate's coverage declaration is what stops
its clean verdict from being read as a general endorsement, and it is the same requirement Part II
§P8 places on every zero in this family.

## 15. Integration

Part X and XI supply the floors G2 enforces. Part IX supplies the residual summary G3 requires. Part
XII and XIX supply G4's entry conditions. Part XIII supplies the instrument contract §7 applies to
gates themselves. Part XXIII assigns each gate to enforcement layer two, which is where a check that
runs and blocks or labels sits. Part XXIV supplies the negative controls §13 requires and receives
§12's five rules.

Outside the family, the compiled digest firing at declared triggers is the model layer-two mechanism
and the natural host for G4. The completion gates are the natural host for G2, since they already
fire at artifact admission. The handoff block is the natural host for G3, since Part XX found it
already carries three verdicts and a debt field.

## 16. Open questions

1. Can label propagation be implemented without a common record format across surfaces? §6 requires
   labels to travel between systems that currently share no schema, and the propagation may be the
   expensive part rather than the labelling. — UNKNOWN, and the principal obstacle to this Part.
2. Do four gate points cover the lifecycle, or is there a fifth at input rather than output? Every
   gate here fires on something produced; a system consuming external artifacts may need one on
   intake. — HYPOTHESIS: yes, and it was not seeded because this family measured production.
3. How many labels can a claim carry before it is ignored? §6 assumes labels are read; a claim
   carrying six qualifications may be treated exactly as one carrying none. — UNKNOWN.

## 17. Institutional writeback

Five rule seeds, five eval seeds, and the consolidated four-point gate set.

Three portable results. **Gate points, not gates per rule** — nineteen trigger points is a list of
intentions, four is a design. **Label evidence, block floors** — blocking on evidence quality creates
pressure that resolves against the gate, while a label costs nothing, cannot be argued down, and
survives into whatever consumes the claim. And **label propagation is what gives a non-blocking gate
teeth**: a block stops one action at the point of production, while an inherited label degrades every
conclusion drawn from a flawed input, automatically, at the point where someone is relying on it.

The finding: **this stack has no labelling gate at all.** Every gate is binary and blocking, which is
correct for the prohibitions and floors most of them enforce, and leaves no way to admit something
with a recorded qualification. That is the fourth instance of one pattern — closure with two verdicts
where five were needed, instruments with two outputs where three were needed, rules with one force
where five layers exist, and now gates with two verdicts where a qualified pass has no
representation. Each time, the true state was reported as its nearest available neighbour, and the
neighbour was always the more favourable one.
