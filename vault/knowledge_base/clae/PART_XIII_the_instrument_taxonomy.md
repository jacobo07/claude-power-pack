---
title: "CLAE Part XIII — The Instrument Taxonomy"
family: clae
part: XIII
depends_on: [XII]
feeds: [XIV, XV, XXIV, XXV]
status: SEALED
date: 2026-07-26
---

# Part XIII — The Instrument Taxonomy

## 1. Purpose

Part XII established that instruments must exist before the work they measure. This Part says what
kinds there are, how to choose among them, and what every instrument must declare about itself.

The framing that motivates it: **most measurement failures are not missing instruments, they are
wrong instruments.** A missing instrument announces itself — there is no number. A wrong instrument
produces data, on schedule, in the expected format, answering a question nobody asked. It is
consumed as though it answered the intended one, and the substitution is invisible because both
questions have the same name.

This Part also resolves, structurally, the failure that has recurred in every Part since Part II:
the unfalsifiable zero. §7 states the requirement that eliminates it, and §11 finds that essentially
no instrument in this stack currently satisfies it.

## 2. Seven kinds

| Kind | Observes | Native level | Cannot see |
|---|---|---|---|
| **Probe** | One specific question at one point | L1–L2 | Anything it was not aimed at |
| **Capture** | An object's state, held for later re-examination | L2–L4 | Whatever the capture format omitted |
| **Diff** | The difference between two representations | L2–L3 | Anything the representation does not carry |
| **Sample** | A subset, at intervals | L3, statistically | Rare events, by construction |
| **Trace** | The sequence of operations, in order | **L4** | Whatever happens between recorded points |
| **Profile** | Attribution of a resource to its consumers | **L4**, for resource dimensions | Non-resource properties |
| **Harness** | Responses to declared inputs | L1–L4 | Behaviour outside the declared input set |

Three observations shape everything downstream.

**Trace is the only kind that natively yields attribution.** Part VI's ladder placed L4 —
identifying the *cause* of a difference — as the level that makes correction efficient, and Part
VIII showed that null outcomes are usually attribution failures. A stack with no tracing instrument
is structurally capped at L3 outside resource dimensions, which means its corrections will be
guesses whose success rate is a property of the guesser.

**Capture is the instrument that buys future options.** It is the only kind whose value increases
after the fact: a captured object can be re-examined along a dimension nobody had thought of, which
is exactly Part V §4's argument for holding the object rather than the numbers, and exactly what
makes Part VI's paired observation possible later. Every other kind answers only the question it
was built for.

**Sample cannot see rare events, and this is not a tuning problem.** No sampling rate makes a
sampler reliable for events rarer than its interval. Where the property of interest is a rare
failure, sampling is the wrong kind regardless of its configuration, and increasing its rate
consumes budget without changing the conclusion.

## 3. Selection

Five questions, in order. Selection is the skill this Part exists to transmit; construction is
comparatively mechanical.

1. **What extraction level does the residual need?** Ranking requires L3 (Part VII); efficient
   correction requires L4 (Part VIII). Choosing an instrument whose native level is below what the
   downstream operation requires guarantees that operation will be performed on inadequate data.
2. **Is the property static or behavioural?** Static properties are reached by capture and diff.
   Behavioural properties — what the object *does* rather than what it *is* — are reached only by
   harness and trace, and no amount of inspection substitutes.
3. **Is the event common or rare?** Rare events exclude sampling entirely.
4. **Does the observation perturb?** Per §5.
5. **What is the cost per observation against the cycle rate?** Part VIII re-measures every cycle
   and Part VIII §4 requires whole-dimension re-measurement, so an instrument affordable once and
   unaffordable forty times is the wrong instrument for a correction loop even if it is the right
   one for an audit.

Question five is the one that most often goes unasked, and it produces a specific failure: an
excellent instrument selected during a careful design phase, run twice, and then quietly replaced by
a cheap proxy nobody argued for.

## 4. What every instrument declares

An instrument that does not declare these is not usable in this family's accounting, because
residuals inherit all of them.

- **Coverage** — the set of deficiencies it *can* detect. Without it, a zero result is
  unfalsifiable (Part II §P8).
- **Envelope** — its variation under repeated observation of one unchanged object; the noise floor
  (Part VI §7, established in Phase Zero per Part XII §5).
- **Perturbation** — how much observing changes the observed.
- **Extraction level** — its native level from Part VI §3.
- **Cost per observation** — so §3's question five is answerable.
- **Failure behaviour** — what it does when it cannot observe. Per §7, this is the field that
  matters most and is almost never specified.

## 5. Perturbation

Some instruments change what they measure. Tracing alters timing; profiling consumes the resource it
attributes; a harness exercises paths that would not otherwise run.

The requirement is not to avoid perturbing instruments, which would eliminate the two kinds that
reach L4. It is to **characterize the perturbation rather than assume it negligible**, and there is
a specific threshold at which the assumption fails:

> **If an instrument's perturbation exceeds its envelope, the instrument is measuring itself.**

Both quantities are already required by §4, so the comparison costs nothing beyond making it. Below
that threshold, perturbation is a recorded caveat. Above it, the observations describe the
instrument's own effect and any residual derived from them is a measurement of the measuring.

## 6. Composition

Instruments chain: a capture feeds a diff, a harness feeds a profile. Chains have properties that do
not follow from their parts in the way intuition suggests.

**Coverage of a chain is the intersection of its members' coverages, not the union.** This is the
counterintuitive one. Adding an instrument to a chain cannot widen what the chain can detect,
because anything the first member does not capture is unavailable to every member after it. Chains
therefore narrow monotonically, and a long chain assembled from individually broad instruments can
have very narrow coverage that no member's documentation reveals.

**Envelope compounds.** Each stage adds its own variation, so a chain's noise floor is worse than
its worst member's, not equal to it. A chain of individually precise instruments can be too noisy to
detect the differences any of them could detect alone.

**Fidelity takes the minimum**, resolving the question left open in Parts V and VI. A chain is no
more trustworthy than its weakest acquisition, and reporting the chain's output at the fidelity of
its best stage is the composition form of Part V §4's fidelity-propagation failure.

## 7. The three-valued output requirement

The most consequential requirement in this Part, and the structural fix for a failure that has
appeared in every Part since Part II.

An instrument must return one of **three** values, never two:

1. **A value** — the observation, with its mode.
2. **Observed nothing** — the instrument ran, within its declared coverage, and found no
   deficiency.
3. **Could not observe** — the instrument did not run, or ran outside its preconditions, or its
   target was unreachable.

Two-valued instruments — value or nothing — collapse the third state into the second. When such an
instrument fails to run, its output is indistinguishable from a clean result, and every consumer
downstream reads a passing signal. **This is the manufacturing process for the unfalsifiable zero**,
and it explains why the failure has been so persistent across this family: it is not a reporting
habit, it is a property of instruments whose output type has only two states.

The corollary is that *zero cannot fall* is a type error before it is a discipline problem. An
instrument whose output type cannot express "I did not observe" will always report absence of
observation as absence of deficiency, no matter how carefully its consumers are instructed.

This also gives Part X §6's decorative floor a mechanical remedy. A floor whose check returns
three-valued output cannot be decorative in silence: an unexecuted check reports *could not observe*
rather than *no violations*, and the gap becomes visible in the ordinary record rather than
requiring a special audit to detect.

## 8. Instruments are artifacts

An instrument has its own residuals, its own drift, and its own quality. Nothing in this family
exempts it, and the question follows immediately: **what measures the instrument?**

The regress is real and it terminates in three places.

**A known-answer case.** An input whose true value is established independently of this instrument.
Running the instrument against it validates it in the same way Part VIII §9's first cycle validates a
loop — and it is the instrument's own Phase Zero, performed once at construction and repeated when
the instrument changes.

**A formal bound.** Where the dimension admits one, the instrument's output can be checked against a
limit that cannot itself be wrong.

**An oracle**, where neither is available, per Parts XVI and XVII.

Instruments also drift: their environment changes, their dependencies move, their calibration
lapses. Because a drifted instrument produces confident wrong numbers rather than obvious failures,
drift is caught only by periodic re-validation against the known-answer case. An instrument with no
known-answer case cannot be re-validated, which means its drift is undetectable in principle — a
strong argument for establishing one at construction even when the instrument seems obviously
correct.

## 9. Boundary

Instrumentation is disproportionate where the observation costs more than the decision it informs,
where the property is already directly visible without an instrument, and for genuinely throwaway
work per Part XII §9.

This Part also does not govern production monitoring, which observes a running system for
operational purposes and answers different questions with different economics. Overlap in tooling is
common; the requirements are not the same, and importing monitoring's assumptions into measurement
produces sampled, aggregated data that cannot support Part VI's paired observation.

## 10. Failure modes

| Failure | Mechanism |
|---|---|
| **Wrong kind** | An instrument that produces data answering a question nobody asked, consumed as though it answered the intended one |
| **Level shortfall** | An instrument below the level the downstream operation requires; ranking or correction proceeds on inadequate data |
| **Sampling a rare event** | A sampler configured for an event it cannot see at any rate |
| **Unmeasured perturbation** | Perturbation assumed negligible; where it exceeds the envelope, the instrument measures itself |
| **Chain coverage assumed union** | A long chain of broad instruments with narrow intersected coverage that no member's documentation reveals |
| **Two-valued output** | Failure to observe reported as nothing observed; the unfalsifiable zero, manufactured by type |
| **Cost collapse** | An excellent instrument selected in design, run twice, silently replaced by a cheap proxy nobody argued for |
| **Uncalibrated instrument** | No known-answer case, so drift is undetectable in principle |

## 11. Evidence — this stack's instruments by kind

| Surface | Kind | Output values |
|---|---|---|
| Marker-token detector | Probe | Two |
| Source map with content hashes and summaries | **Capture** | Two |
| Coordinate graph over the repository | Capture plus diff | Two |
| Reachability audit | Probe over a discovered set | Two |
| Quality and design scorers | Probe, composite | Two |
| Empirical verification runs | Harness | Two |
| Recurring-error log | Sample over incidents | Two |
| Session and cost telemetry | Sample | Two |
| This compendium's gate script | Probe, four checks | Two |

Three findings.

**The stack has no tracing instrument and no profiling instrument.** It is therefore capped at L3
outside resource dimensions, which means the attribution Part VIII needs for efficient correction is
unavailable — and explains why corrections here have historically been reasoned rather than
measured.

**Capture exists and is under-used.** The source map and the coordinate graph are genuine captures,
and they are the two surfaces that could support re-examination along a dimension nobody has thought
of yet. Nothing currently consumes them that way.

**Every instrument in the stack is two-valued, including this compendium's own gate script.** A gate
that fails to execute is indistinguishable from a gate that passed, everywhere. This is the single
most actionable finding in the Part: the remedy is a type change at each instrument's boundary
rather than a discipline change in its consumers, and it retires an entire class of failure that
this family has otherwise been fighting with rules. — Instrument kinds and output arities OBSERVED
from the surfaces during the Phase 0 audit; level implications INFERRED against Part VI §3.

The gate script's inclusion in that list is deliberate. It aborts on a failed check, so a genuine
failure is loud — but a check that silently matched nothing because its pattern was wrong would
report clean, and nothing in its output distinguishes the two. The family's own instrument has the
defect the family is describing.

## 12. Detection signatures

1. **The instrument nobody chose.** No record of which kinds were considered. Selection was
   availability, not §3.
2. **The rate that never helped.** A sampler whose rate has been increased repeatedly without
   changing conclusions — the event is rarer than any rate will reach.
3. **The silent green.** A check reporting clean during an interval when its preconditions were
   known to be absent. Two-valued output.
4. **The narrowing chain.** A chain whose end-to-end coverage was never computed, only its members'.
5. **The uncalibrated veteran.** A long-serving instrument with no known-answer case. Its drift has
   been undetectable for as long as it has run.

## 13. Trap seeds — for Part XXII

- **T-CLAE-WRONG-INSTRUMENT-KIND** — an instrument producing data that answers a different question
  under the same name, consumed as though it answered the intended one.
- **T-CLAE-TWO-VALUED-INSTRUMENT** — an instrument whose output cannot express "could not observe",
  reporting failure-to-run as nothing-found and manufacturing unfalsifiable zeros by type.
- **T-CLAE-CHAIN-COVERAGE-UNION** — chain coverage assumed to be the union of its members' when it
  is the intersection, yielding a narrow chain nobody's documentation describes.
- **T-CLAE-SELF-MEASURING-INSTRUMENT** — perturbation exceeding the envelope, so the observations
  describe the instrument's own effect.
- **T-CLAE-UNCALIBRATED-INSTRUMENT** — no known-answer case, so drift produces confident wrong
  numbers that nothing can detect.

## 14. Rule seeds — for Part XXIII

- **PR-CLAE-THREE-VALUED-OUTPUT** — every instrument returns a value, observed-nothing, or
  could-not-observe. Two-valued instruments are not admitted, and existing ones are widened at their
  boundary rather than governed by rules on their consumers.
- **PR-CLAE-DECLARE-INSTRUMENT-PROPERTIES** — coverage, envelope, perturbation, extraction level,
  cost per observation and failure behaviour are declared before an instrument is used in
  accounting.
- **PR-CLAE-SELECT-BY-LEVEL** — instrument selection begins from the extraction level the downstream
  operation requires, not from what is available.
- **PR-CLAE-PERTURBATION-UNDER-ENVELOPE** — an instrument whose perturbation exceeds its envelope is
  recorded as measuring itself, and residuals from it are withdrawn.
- **PR-CLAE-CHAIN-COVERAGE-INTERSECTED** — a chain declares its end-to-end coverage as the
  intersection of its members', and its envelope as compounded.
- **PR-CLAE-KNOWN-ANSWER-CASE** — every instrument has a case whose true value is established
  independently, run at construction and repeated when the instrument changes. Instruments without
  one have undetectable drift by construction.

## 15. Eval seeds — for Part XXIV

- **Arity probe.** For every instrument, determine whether it can express could-not-observe. This is
  the cheapest high-value check in the family and is expected to fail nearly everywhere.
- **Silent-green probe.** Disable an instrument's preconditions deliberately and observe its output.
  If it reports clean, it is two-valued and its entire history of clean results is uninterpretable.
- **Chain-coverage probe.** For each instrument chain, compute the intersected coverage and compare
  it against what consumers believe the chain detects.
- **Perturbation probe.** For each perturbing instrument, compare its measured perturbation against
  its envelope.
- **Calibration probe.** For each instrument, look for a known-answer case and the date it last ran.
  Instruments without one, or with a stale one, have unbounded drift.

## 16. Production Reality Gate seed — for Part XXV

**Instrument Integrity Gate.** A residual may be admitted to the ledger only from an instrument that
declares coverage, envelope, perturbation, extraction level and failure behaviour, that returns
three-valued output, whose perturbation is below its envelope, and that has passed its known-answer
case within the declared re-validation interval. Instruments failing any of these produce
observations recorded as unverified rather than as measurements — a status change, not a block,
consistent with distance never enforcing.

## 17. Pseudoflow — selecting and qualifying an instrument

Begin from the downstream operation. Determine the extraction level it requires: L3 to rank, L4 to
correct efficiently. Choose among kinds by whether the property is static or behavioural, and by
whether the event is common or rare — a rare event excludes sampling at any rate.

Estimate cost per observation against the cycle rate the correction loop will run at. An instrument
affordable for an audit and unaffordable forty times is the wrong instrument for a loop, and
selecting it guarantees a later silent substitution.

Before first use, establish the instrument's declarations. Determine coverage by asking what
deficiencies it structurally cannot detect. Establish the envelope by repeated observation of one
unchanged object. Measure perturbation and compare it against the envelope; if it exceeds, this
instrument measures itself and a different kind is required.

Specify failure behaviour explicitly. Confirm the instrument can distinguish observed-nothing from
could-not-observe, and if it cannot, widen its output before using it — this is a change at the
instrument, not an instruction to its consumers, and instructing consumers has never worked.

Establish a known-answer case: an input whose true value is known independently. Run it. Record the
date. This is the instrument's own Phase Zero and it is what makes future drift detectable at all.

Where instruments are chained, compute the chain's coverage as the intersection of its members' and
its envelope as compounded, and report the chain's fidelity as the minimum of its stages.

Re-run the known-answer case whenever the instrument, its dependencies or its environment change,
and at the declared interval otherwise. A drifted instrument produces confident wrong numbers rather
than visible failures, so nothing else will surface it.

## 18. Integration

Part XIV takes the case where no suitable instrument exists and the work becomes building one; §3's
selection questions are what determine that no existing kind fits. Part XV converts incidents into
probes, which are the narrowest kind and the correct one for a known failure. Part XVI receives
dimensions where no instrument kind applies as candidate oracle questions. Part XXIV's evals are
themselves instruments and inherit every requirement in §4, including the three-valued output — an
eval that cannot report could-not-run is the same defect one level up.

Within the family, this Part resolves the fidelity-composition question Parts V and VI left open,
supplies the mechanical remedy for the decorative floors of Part X §6, and gives the unfalsifiable
zero a type-level fix rather than a procedural one.

Outside the family, the source map and the coordinate graph are identified as genuine captures whose
re-examination value is currently unused, and the absence of tracing and profiling instruments is
recorded as the reason attribution is unavailable stack-wide.

## 19. Open questions

1. Can two-valued instruments be widened at their boundary without modifying them? A wrapper that
   verifies preconditions and reports could-not-observe on its own authority would retrofit §7
   cheaply, but it can only detect the precondition failures it knows to check. — HYPOTHESIS; likely
   partial.
2. What is the correct re-validation interval for a known-answer case? It plainly depends on how
   fast the instrument's environment moves, and deriving it rather than choosing it is unresolved —
   the same shape as Part V's horizon question. — UNKNOWN.
3. Is capture's re-examination value realizable in practice, or does the capture format always
   foreclose the dimension nobody anticipated? The argument for capture assumes stored objects can
   answer unanticipated questions; every capture format is itself a projection, and Part VI §6
   established that projections destroy dimensions. — UNKNOWN, and it bounds how much §2's second
   observation is worth.

## 20. Institutional writeback

Five trap seeds, six process-rule seeds, five eval seeds and one production gate.

The portable result is **three-valued output**. The unfalsifiable zero has appeared in this family
as a principle (Part II), a coverage requirement (Part IX), a decorative floor (Part X) and a
detection signature (Part XII), and each treatment was procedural — a rule telling consumers to
demand coverage. This Part locates the cause: an instrument whose output type has two states cannot
express failure-to-observe, so it reports it as absence-of-deficiency by construction, and no
instruction to its consumers can change that. Widening the output type retires the entire class. The
finding that every instrument in this stack, including this family's own gate script, is currently
two-valued makes it the most actionable item the family has produced.

Secondarily: **chain coverage is the intersection, not the union**, which means assembling
instruments narrows what a pipeline can see, monotonically, in a way no member's documentation
reveals.
