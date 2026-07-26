---
title: "CLAE Part XX — Phase Closure Semantics"
family: clae
part: XX
depends_on: [IX, XIX]
feeds: [XXI, XXV, XXVI]
status: SEALED
date: 2026-07-26
---

# Part XX — Phase Closure Semantics

## 1. Purpose

Closure is where the trap makes its last stand. Every measurement can be sound, every reference
external, every instrument three-valued, every residual recorded — and the closing statement can
still say *done*, with the residual left out, and everything upstream is undone by one sentence.

This Part defines what closure is, gives five verdicts where most systems have one, separates the
part of closure a producer may self-declare from the part they may not, and establishes that
**closure does not compose** — which turns out to be the third non-composition this family has
found, and the three together name a pattern worth carrying beyond it.

## 2. What closure is not

- **Not the gate passing.** Admissibility is not completeness, per Part II §9.
- **Not the residual count reaching zero.** Count is not distance, per Part VII §7, and a zero count
  without coverage is unfalsifiable, per Part II §P8.
- **Not the deadline arriving.** Time passing is not work finishing; closing on a date without
  publishing state is deletion of the residual, per Part VIII §6.
- **Not the absence of objection.** Nobody objecting is evidence about attention, not about the
  artifact.

Each of these terminates on a *report* rather than on the world, which Part VIII §6 identified as the
common shape of every illegitimate termination.

## 3. What closure is

> **Closure is a statement about a boundary in time, not a claim about the artifact's quality. It
> says: work on this unit stops here, and this is the state it stops in.**

The state includes what remains. That is not an addendum to closure; it is most of what closure
communicates. A boundary that describes only what was achieved describes half a state.

The reframing that follows is the Part's core:

> **Closure is an accounting act, not a quality claim.**

An accounting can be complete while the thing it accounts for is not. This dissolves the tension that
makes people avoid closing honestly — a closure with a large residual is not a bad closure, it is an
accurate one, and the alternative is not a better artifact but a worse record.

## 4. The closure obligation

To close a unit, publish:

1. **What was done** — against the stated intent.
2. **What remains**, per dimension, with magnitudes and dispositions (Part IX §4).
3. **What could not be measured** — the undefined dimensions and the measurement debt.
4. **What was deviated from**, with the measured loss (Part XVIII).
5. **Which judgments were self-answered and which were oracle-answered**, with scopes (Part XVI).
6. **The pin generations and instrument set** the above was measured against.

This is *residual visibility as a closure obligation*, and the operative word is *obligation*: a
closure without these is not a lighter closure, it is a **different act** — a claim of completeness,
which is a quality claim, which §3 says closure is not.

Item three is the one omitted most and mattering most, for the reason Part IX §5 established: a
report listing only measured dimensions reads as coverage, and the unmeasured scope was chosen from
inside the loop.

## 5. Five verdicts

*Done* collapses five distinct states into one, and the collapse is where the information goes.

| Verdict | Meaning |
|---|---|
| **Complete** | Intent fully served; residual within declared floors; nothing undefined in scope |
| **Complete with residual** | Intent served; measured gap remains, recorded and dispositioned |
| **Complete with deviation** | Intent served by substitution; constraint proven, loss measured |
| **Reduced** | Part of the intent served; the remainder explicitly not, and declared |
| **Halted** | Stopped on a declared condition; state recorded; resumable |

**The second is the common case**, and most systems have no vocabulary for it. Work is genuinely
finished, the intent is genuinely served, and a measured gap genuinely remains — and the only
available words are *done* or *not done*. Choosing *done* is not dishonesty; it is the closest
available term. That is exactly how a vocabulary limit becomes a reporting failure, which Part III §2
established as the reason an ontology is load-bearing.

Providing the second verdict costs nothing and changes what can be said. It is the single cheapest
intervention in this Part.

The fifth matters for autonomy: a halt under Part XIX §6 is a closure state, not an absence of one,
and recording it as a verdict is what makes Part XIX §7's accounting work.

## 6. Who may declare closure

Closure is a **self-referential judgment** in Part XVI's fourth sense: *is this done* asks whether
criteria were met, and the criteria were frequently authored by whoever is now closing.

The resolution is to split the act.

> **The producer closes the accounting. The constituency accepts.**

The accounting is checkable: did the six items of §4 get published, are the numbers what the
instruments reported, are the dispositions recorded. A producer can and should self-declare that,
and it requires no external standing.

Acceptance is different: *is this good enough for the purpose it serves* is value-laden and
constituency-dependent — Part XVI's first two marks — and belongs to whoever bears the consequence.

Conflating the two is self-certification at the last possible step, and it is the most common form
because it is the most invisible: a closure statement that reads as an accounting and functions as
an acceptance. Publishing them as two separate lines, with the acceptance line empty until someone
with standing fills it, is what keeps the distinction visible.

## 7. Closure decays

A closure is dated, and everything in it is as-of that date. Three of its components decay
independently:

- **Residuals** become unverified after the re-measurement interval (Part IX §8).
- **References** go stale, drift, or lose relevance (Part V §7).
- **Oracle answers** lapse at their validity scope (Part XVI §8).

Therefore a closure carries a **validity horizon**, and:

> **A phase closed long ago and never revisited is not still closed. It is unverified.**

This is Part IX §8's ledger rule applied to the closure statement itself. Treating an old closure as
current asserts that nothing in its three decaying components has moved, which is a claim nobody
made and which is usually false.

## 8. Reopening

Legitimate grounds: the residual grew; a floor's derivation changed; the reference moved or was
retired; an oracle answer lapsed; a probe fired.

**Reopening is not failure.** This is the fourth appearance of the accounting pattern Part XIX §7
named — if reopening is recorded as a defect, units will not be reopened, and the closures will
persist past their validity while looking healthy.

And its converse, which is sharper:

> **A unit that can never be reopened is not closed. It is abandoned.**

Closure with no reopening path is a statement that the unit's state will never be re-examined
regardless of what changes, which is not a boundary in time — it is a decision to stop looking. The
existence of a reopening path is part of what makes closure meaningful rather than terminal.

## 9. Closure does not compose

A phase composed entirely of closed units is **not thereby closed**.

Residuals aggregate. Units each within their floors can produce an aggregate that violates a floor no
unit violated, because floors at the phase scale measure a different thing than floors at the unit
scale. Undefined dimensions accumulate: five units each with one unmeasured dimension yield a phase
with five, and the phase's measurement debt is the union, not any member's.

Closure must therefore be **computed at each scale**, not inherited from the scale below. A phase
closure re-runs §4's obligation over the aggregate, against phase-scale floors and phase-scale
references.

This is the third non-composition the family has found, and the three are worth stating together:

| Non-composition | Part | Consequence |
|---|---|---|
| **Intent preservation** | XVIII §5 | A chain of locally-correct deviations arrives where nobody intended |
| **Instrument chain coverage** | XIII §6 | Assembling broad instruments yields narrow intersected coverage |
| **Closure** | here | Closed units do not make a closed phase |

> **Local correctness does not aggregate.** In each case the parts are individually sound, the
> composition is individually reasonable, and the whole has a property no part has. Any claim about
> a composite must be established at the composite's own scale — never inherited from its parts.

## 10. Boundary

Closure semantics apply to bounded units of work. They do not apply to continuous activity with no
unit boundary, where the honest analogue is a periodic state publication rather than a closure.

They do not apply to prohibitions, which are not closed but simply held.

And closure does not certify an artifact for a use nobody evaluated it for. A closure is bounded by
the intent it was measured against, exactly as an oracle answer is bounded by what was shown (Part
XVII §6). A unit closed against one intent, then used for another, has no closure covering that use.

## 11. Evidence — closure surfaces in this stack

| Surface | Verdicts available | Residual published? |
|---|---|---|
| Handoff block | **Three** — complete, blocked with reason, standby | **Yes** — a debt field, plus next action |
| Done means observed evidence, not exit code | Two | No |
| Completion gates | Two | No |
| This compendium's per-Part commits | Two, implicitly | **Yes** — gate results published in every message |
| Phase closure across the family | Not yet defined | The completion report is pending |

**The handoff block is the strongest closure instrument in this stack**, and it was not designed as
one. It carries three verdicts where nearly everything else carries two, it names a blocking reason
rather than merely a blocked state, it requires a next action, and — most unusually — it has a
**debt field**, which is a residual publication obligation in Part IX §4's exact sense.

Its gaps against §4 are specific and small: the debt is free text rather than dimensioned with
magnitudes, there is no undefined-dimensions field, and there is no separation between the producer's
accounting and a constituency's acceptance. Adding a dimensioned debt and an unmeasured-scope line
would bring it close to complete, and it is already closer than the formal completion gates that sit
alongside it.

This compendium's per-Part commits satisfy joint publication in practice — every commit message
carries the gate results alongside the claim — which is Part IX §4 observed rather than asserted. What
they do not carry is the undefined set, and the family's own phase closure has not yet been
computed at the phase scale, per §9. — Closure surfaces OBSERVED from the governance archive and this
session's own record; assessments INFERRED against §4 and §5.

## 12. Failure modes

| Failure | Mechanism |
|---|---|
| **Done as the only verdict** | Five states collapsed into one; the common case has no vocabulary |
| **Closure without residual** | A different act performed under closure's name: a completeness claim |
| **Undefined omitted** | Measured dimensions listed alone; unmeasured scope reads as coverage |
| **Self-acceptance** | The producer's accounting functions as the constituency's acceptance |
| **Permanent closure** | A dated statement treated as current after its components have decayed |
| **Unreopenable unit** | No reopening path; abandonment recorded as closure |
| **Inherited closure** | A phase declared closed because its units were, with aggregate floors unchecked |
| **Closure reused for another intent** | A unit closed against one purpose relied on for a different one |

## 13. Detection signatures

1. **The binary status field.** Any closure surface offering done or not-done. The common case will
   be reported as the first.
2. **The residual-free closure.** A closing statement with no remaining-gap section. It is a
   completeness claim.
3. **The single signature.** One party's name on both the accounting and the acceptance.
4. **The ageless closure.** Closed units with no validity horizon and no re-examination since.
5. **The empty reopening log.** No unit ever reopened. Either nothing has changed anywhere, or
   reopening is being read as failure.
6. **The rolled-up phase.** A phase closure whose evidence is a list of closed units, with no
   aggregate measurement of its own.

## 14. Trap seeds — for Part XXII

- **T-CLAE-DONE-COLLAPSE** — five closure states reported through one word, so the common case
  (complete with residual) is reported as complete.
- **T-CLAE-CLOSURE-WITHOUT-RESIDUAL** — a completeness claim performed under closure's name,
  undoing sound upstream measurement in one sentence.
- **T-CLAE-SELF-ACCEPTANCE** — the producer's accounting functioning as the constituency's
  acceptance; self-certification at the last and least visible step.
- **T-CLAE-PERMANENT-CLOSURE** — a dated closure treated as current after its residuals, references
  and oracle answers have decayed.
- **T-CLAE-INHERITED-CLOSURE** — a phase closed because its units were, with aggregate residuals and
  phase-scale floors never computed.
- **T-CLAE-ABANDONMENT-AS-CLOSURE** — a unit with no reopening path recorded as closed.

## 15. Rule seeds — for Part XXIII

- **PR-CLAE-FIVE-VERDICTS** — closure is recorded as complete, complete with residual, complete with
  deviation, reduced, or halted. A binary status field is recorded as insufficient.
- **PR-CLAE-CLOSURE-PUBLISHES-STATE** — closure publishes all six items of §4, including the
  undefined dimensions. A closure omitting them is a completeness claim and is labelled as one.
- **PR-CLAE-SPLIT-ACCOUNTING-FROM-ACCEPTANCE** — the producer closes the accounting; acceptance is
  recorded separately by the constituency. The acceptance line stays empty until filled by someone
  with standing.
- **PR-CLAE-CLOSURE-HAS-A-HORIZON** — every closure records a validity horizon. Past it, the unit is
  unverified rather than closed.
- **PR-CLAE-REOPENING-IS-NOT-FAILURE** — reopening on declared grounds is recorded as a closure
  outcome. A unit with no reopening path is recorded as abandoned.
- **PR-CLAE-COMPUTE-AT-EACH-SCALE** — phase closure re-runs the closure obligation over aggregate
  residuals against phase-scale floors. Closure is never inherited from constituent units.

## 16. Eval seeds — for Part XXIV

- **Verdict-vocabulary probe.** Inspect closure surfaces for available states. Binary fields
  guarantee the common case is misreported, and this is the cheapest finding in the Part.
- **Residual-in-closure probe.** For each closure statement, check for remaining-gap and
  undefined-dimension sections.
- **Signature probe.** Compare the accounting signatory against the acceptance signatory. Identity
  indicates self-acceptance.
- **Horizon probe.** List closures past their validity horizon with no re-examination. Each should
  read as unverified and probably reads as closed.
- **Aggregate probe.** For each closed phase, verify an aggregate measurement exists at phase scale
  rather than a roll-up of unit closures.
- **Reopening probe.** Count reopenings and their grounds. Zero over a long period indicates
  reopening is read as failure.

## 17. Production Reality Gate seed — for Part XXV

**Phase Closure Gate.** A unit may be recorded as closed only when its verdict is one of the five,
its statement publishes all six obligation items including the undefined dimensions, its accounting
and acceptance are separately attributed, it carries a validity horizon, and — for a composite — its
residuals were aggregated and checked against composite-scale floors rather than inherited from its
parts. Closures failing any of these are recorded as completeness claims, which is a label carried
forward wherever the closure is cited.

## 18. Pseudoflow — closing a unit

Establish the verdict first, from the five. Most work is complete with residual, and reaching for it
rather than for *complete* is the single decision that makes the rest of the closure honest.

Publish the state: what was done against the stated intent; what remains, per dimension, with
magnitudes and dispositions; what could not be measured at all; what was deviated from and the
measured loss; which judgments were self-answered and which were oracle-answered, with their scopes;
and the pin generations and instruments the whole was measured against.

Publish the undefined dimensions even when the list is long. A closure listing only what was measured
reads as coverage, and the reader has no way to know otherwise.

Sign the accounting. Leave the acceptance line empty. It is filled by whoever bears the consequence,
or it stays empty and the closure is accounting-only — which is an honest and common state, and far
better than a signature that means nothing.

Record the validity horizon, derived from the fastest-decaying component: usually the shortest of the
re-measurement interval, the reference horizon, and the oracle answers' scopes.

Record the reopening grounds. A unit with no path back is abandoned, and if that is the intent, say
so with that word.

For a composite, do not roll up. Aggregate the residuals of the constituent units, add their undefined
dimensions as a union, and check the aggregate against composite-scale floors. A phase whose units
each cleared their floors may still violate one of its own.

## 19. Integration

Part IX supplies the residual summary that §4 publishes and the unverified disposition that §7
applies to closures themselves. Part XVI supplies the acceptance standing §6 requires. Part XVIII
supplies the deviation records item four carries. Part XIX supplies the halt verdict and the
contract whose scope bounds what a closure can cover. Part XXV's Phase Closure Gate is the
enforcement surface, and Part XXVI's integration map is itself a composite closure and must be
computed at its own scale per §9.

Outside the family, the handoff block is identified as the stack's strongest closure instrument and
the natural host for a dimensioned debt field and an unmeasured-scope line — two small additions to
something already three-valued.

## 20. Open questions

1. How are residuals aggregated across units measured against different references? §9 requires
   composite aggregation, and Part IX §7's equivalence classes may forbid summing exactly the
   residuals a phase closure needs to combine. — UNKNOWN, and likely the practical obstacle to §9.
2. Who is the constituency for an internal unit with no external consumer? §6 requires acceptance
   from whoever bears the consequence, and for internal infrastructure the bearer may be a future
   maintainer who cannot be consulted — Part XVI §7's unavailable-constituent problem, arriving at
   closure. — UNKNOWN.
3. Should the validity horizon be derived from the fastest-decaying component, or per component? A
   single horizon is simpler and expires the whole closure when only one part has decayed. —
   HYPOTHESIS: per component, with the closure reporting which parts are stale rather than becoming
   wholly unverified.

## 21. Institutional writeback

Six trap seeds, six process-rule seeds, six eval seeds and one production gate.

Three portable results. **Closure is an accounting act, not a quality claim** — which dissolves the
pressure to close dishonestly, since a closure with a large residual is accurate rather than bad.
**The producer closes the accounting; the constituency accepts** — two lines, separately signed,
because conflating them is self-certification at the last and least visible step. And **closure does
not compose**, which together with the two non-compositions found earlier gives the family's most
general result: *local correctness does not aggregate*, so any claim about a composite must be
established at the composite's own scale and never inherited from its parts.

The cheapest single intervention in this Part is the second verdict. **Complete with residual** is
the state most work is actually in, and systems that lack the phrase report it as *complete* — not
from dishonesty, but because it is the nearest available word.
