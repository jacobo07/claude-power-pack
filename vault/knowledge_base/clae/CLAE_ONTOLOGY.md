---
title: "CLAE — Ontology"
family: clae
type: registry
kind: extract
sources: [Part III]
derivation: mechanical extraction from the sealed Parts; no entry carries information absent from its source
status: POPULATED
date: 2026-08-10
---

# CLAE — Ontology

> **What this file is.** Part XXVI §5 defines the twelve companion artifacts as *"extracts for retrieval convenience"* — the schemas, consolidations and measured counts live in the Parts. This file locates entries; it does not restate, resolve or extend them.
> **Reading rule.** Every row cites the Part that seeded it. Where a row's source is ambiguous, the ambiguity is transcribed rather than resolved.

Part III §2 states why this is load-bearing: the family's terms are *"the confusion matrix"* between adjacent ideas, and a document using them loosely re-imports the defect the family exists to name.

## 4. Tier one — the core objects

### Reference

- **Is** — a canonical instance, external to this stack, that an artifact is compared
  against. It is a *thing that exists*, with provenance, a version and a date.
- **Is not** — a bar, a criterion, a rubric, a target, or an aspiration.
- **Boundary** — a reference can be pointed at. If what is being cited is a level rather than
  an instance, it is a bar. If it was authored inside this stack, it is a criterion.
- **Confusion failure** — reference capture, Part II §12: an internally-authored object is
  cited as a reference, the closed loop is restored, and every downstream report continues to
  say "distance" while measuring conformance to itself.
- **Owner** — Parts IV and V.

### Artifact

- **Is** — the thing this stack produced, at a specific version, in the state under
  assessment.
- **Is not** — the process that produced it, nor the intent behind it.
- **Boundary** — an artifact is inspectable after the producing run ends. Anything that only
  exists during the run is an observation, not an artifact.
- **Confusion failure** — assessing the intent rather than the object, which always passes,
  because intent is authored by the same party being assessed.
- **Owner** — the producing system; CLAE only requires that it be versioned.

### Delta

- **Is** — a single observed difference between artifact and reference, along one dimension.
  It is an *item*, countable and enumerable.
- **Is not** — a distance, which is an aggregate; nor a defect, which presumes a judgment
  already made.
- **Boundary** — a delta can be listed. A distance can only be stated.
- **Confusion failure** — treating the enumeration order of deltas as a priority ordering,
  which substitutes discovery sequence for consequence. Part VII exists because this
  substitution is the default human behaviour.
- **Owner** — Parts VI and VII.

### Distance

- **Is** — the aggregate magnitude of what remains of the reference, along a declared
  dimension, satisfying the four properties of Part II §5: referenced, observable, ordered,
  carried.
- **Is not** — a score, unless that score's maximum is defined by an observed external
  instance rather than by an internal rubric.
- **Boundary** — the saturation test of Part II §13: if a demonstrably superior external
  instance appeared, would the value move? A distance moves. A rubric score saturates.
- **Confusion failure** — counterfeit distance: graded compliance reported and consumed as
  distance, which is more dangerous than a plain predicate because its numeric texture
  suppresses the suspicion a bare pass would provoke.
- **Owner** — Part II defines it; Part IX accounts for it.

### Residual

- **Is** — the recorded, dispositioned portion of distance that remains after an assessment
  concludes, carried durably against the artifact version that produced it.
- **Is not** — a distance. Distance is a measured quantity; a residual is an *institutional
  object* with a lifecycle, an owner and a disposition.
- **Boundary** — a residual survives the run that computed it and can be found by someone who
  was not watching that run. A distance that is not written down is not a residual.
- **Confusion failure** — residual amnesia: the quantity is computed each run, reported to
  nobody durable, and re-derived from scratch by a later audit that believes it is
  discovering something new.
- **Owner** — Part IX.

## 5. Tier two — the measurement vocabulary

### Instrument

- **Is** — a capability that observes a class of property and yields observations of declared
  scope.
- **Is not** — a gate. An instrument produces a value; a gate produces a verdict. Most gates
  contain an instrument, which is precisely why Part II's retention thesis is cheap.
- **Boundary** — remove the threshold. What remains is the instrument.
- **Confusion failure** — an instrument reported as a gate loses its magnitude; a gate
  reported as an instrument implies a measurement that was never made.
- **Owner** — Part XIII.

### Probe

- **Is** — a specific, durable, re-runnable instrument bound to one known failure, derived
  from an incident that actually occurred.
- **Is not** — a test. A test asserts intended behaviour; a probe reproduces a historical
  failure. Every probe is an instrument; not every instrument is a probe; a probe and a test
  may examine the same surface for entirely different reasons.
- **Boundary** — a probe can name the incident that created it. An instrument without a
  lineage is not a probe.
- **Confusion failure** — incidents leave no durable artifact and recur, while the test suite
  reports full health because it asserts intent and the incident was never intended.
- **Owner** — Part XV.

### Observation

- **Is** — a single act of measurement producing a value with a mode and a timestamp.
- **Is not** — an inference. An inference derives from observations; only an observation
  touches the object.
- **Boundary** — an observation names what it looked at. An inference names what it reasoned
  from.
- **Confusion failure** — inference labelled as observation, which inflates the evidence tier
  and defeats the labelling discipline this compendium is built on.
- **Owner** — Part XIII.

### Mode

- **Is** — how a residual was obtained: exact, sampled, proxy, ordinal, undefined, or
  unmeasured by choice, per Part II §7.
- **Is not** — a confidence level. Mode describes the method; confidence describes belief.
- **Boundary** — mode is a property of the procedure and is knowable before the value is.
- **Confusion failure** — mode laundering: a skipped measurement recorded as undefined,
  converting a decision into an apparent property of the world.
- **Owner** — Part II defines the set; Part IX enforces its presence.

### Coverage

- **Is** — the declared set of deficiencies an instrument is capable of detecting.
- **Is not** — the set it did detect on this run.
- **Boundary** — coverage is a property of the instrument and is stable across runs. Findings
  vary per run.
- **Confusion failure** — the unfalsifiable zero of Part II §P8: nothing found, nothing
  declared detectable, and the two are indistinguishable in the record.
- **Owner** — Part XIII.

## 6. Tier three — the governance vocabulary

### Bar

- **Is** — a level, derived from a reference, at which an artifact is being compared.
- **Is not** — a reference, which is an instance; nor a floor, which enforces.
- **Boundary** — a bar can move without anything failing. A floor cannot move without
  changing what is admissible.
- **Confusion failure** — a bar authored without a reference is the trap of Part I in its
  purest form: a level chosen by the party being measured.
- **Owner** — Part IV.

### Floor

- **Is** — a minimum below which work is not admissible, derived from the domain rather than
  imported, catching the real-but-shallow implementation that a token-matching detector
  cannot see.
- **Is not** — a bar. A floor is imposed from below and enforces; a bar is observed from
  outside and informs.
- **Boundary** — crossing a floor changes admissibility. Crossing a bar changes only the
  reported residual.
- **Confusion failure** — collapsing them fails in both directions. Treat the bar as a floor
  and nothing ever ships, because the reference always exceeds current work. Treat the floor
  as a bar and it drifts down to whatever was built, which is the trap wearing a new word.
- **Owner** — Parts X and XI.

### Gate

- **Is** — a decision point that consumes observations and emits a verdict on admissibility.
- **Is not** — a measurement, and not a rule. It is the mechanism that applies a rule.
- **Boundary** — a gate has a verdict and a downstream consumer of that verdict.
- **Confusion failure** — a passing verdict read as a statement of completeness, which is the
  composition-rule violation of Part II §9.
- **Owner** — Part XX; the enforcement surfaces themselves.

### Prohibition

- **Is** — a state that must never occur.
- **Is not** — a quality criterion. It admits no partial satisfaction and no residual.
- **Boundary** — ask whether a *less bad* version of the violation would be acceptable. If
  not, it is a prohibition and binary is exact.
- **Confusion failure** — applying distance discipline to prohibitions dilutes rules that
  currently work, and manufactures meaningless quantities.
- **Owner** — the sealed hard-rule archive; explicitly outside this family.

### Invariant

- **Is** — a property that must hold at every moment, not merely at checkpoints.
- **Is not** — a prohibition, which forbids a state; an invariant requires one. They are
  duals and both are correctly binary.
- **Boundary** — an invariant is checkable at any instant without reference to history.
- **Confusion failure** — checking an invariant only at gates, which permits it to be
  violated between them and restored before the next check.
- **Owner** — outside this family.

## 7. Tier four — the boundary vocabulary

### Oracle

- **Is** — a source consulted for a *judgment* the stack structurally cannot make about
  itself.
- **Is not** — a human being, and not an instrument. A person running a comparison is
  operating an instrument. The same person answering whether the result feels right is acting
  as an oracle. The distinction is the nature of the question, not the identity of the
  answerer.
- **Boundary** — could a sufficiently capable procedure answer this in principle? If yes, it
  is an instrument question and asking a person is an unnecessary cost. If no, it is an
  oracle question and having a procedure answer it is a fabricated result.
- **Confusion failure** — in one direction, oracle exhaustion: people are asked mechanical
  questions until they stop answering carefully. In the other, self-certification: the stack
  answers a question about itself that it has no standing to answer, which is Part I's trap
  at its most direct.
- **Owner** — Parts XVI and XVII.

### Horizon

- **Is** — the span over which a reference remains valid before it must be re-acquired or
  re-argued.
- **Is not** — the age of the reference. Age is observed; horizon is declared in advance.
- **Boundary** — a horizon is set when the reference is pinned, not when staleness is
  suspected.
- **Confusion failure** — silent staleness. Every residual measured against an expired
  reference is wrong in an unknown direction, and nothing in the record indicates it.
- **Owner** — Part V.

### Deviation

- **Is** — a recorded substitution of the intended approach, justified by a proven
  constraint, preserving the original intent, with the resulting loss measured.
- **Is not** — a compromise, a shortcut, or a decision to defer. Those have no record and no
  measured loss.
- **Boundary** — a deviation names the constraint, proves it, states what intent was
  preserved, and quantifies what was given up. Missing any of the four, it is an
  unrecorded change of plan.
- **Confusion failure** — accumulated silent substitutions produce an artifact nobody
  intended, with no record of where intent was left behind.
- **Owner** — Part XVIII.

### Disposition

- **Is** — the lifecycle state of a residual: open, scheduled, accepted with a reason and an
  owner, or closed by a named observation.
- **Is not** — a severity or a priority, which describe consequence rather than state.
- **Boundary** — a disposition changes through an action by someone. Severity changes through
  reassessment.
- **Confusion failure** — the ledger fills with entries that are neither open nor closed, and
  becomes a list nobody can act on, which is how a residual ledger dies.
- **Owner** — Part IX.

## 8. The confusion matrix

The pairs most often collapsed, with the failure each collapse produces. This table is the
operational core of the Part; the entries above exist to make it precise.

| Collapsed pair | Institutional failure | Detection |
|---|---|---|
| Reference / bar | Reference capture — an internal object cited as external | Ask for provenance and a version |
| Distance / residual | Residual amnesia — measured, never carried | Look for the value in the durable record, not the run log |
| Bar / floor | Nothing ships, or the bar sinks to current work | Ask whether crossing it changes admissibility |
| Instrument / gate | Magnitude discarded, or a measurement implied that never happened | Remove the threshold and see what remains |
| Instrument / oracle | Oracle exhaustion, or self-certification | Ask whether a procedure could answer it in principle |
| Probe / test | Incidents recur while the suite reports health | Ask which incident created it |
| Delta / impact | Discovery order substituted for consequence | Ask what ordered the list |
| Coverage / findings | The unfalsifiable zero | Ask what the instrument could have found |
| Undefined / unmeasured by choice | A decision laundered into a fact | Ask who decided and when |
| Deviation / compromise | Intent lost with no record of where | Ask for the constraint and the measured loss |

## 9. Vocabulary drift — banned usages inside this family

These are not stylistic preferences. Each is a specific way the closed loop reasserts itself
while the language of distance is retained.

1. **"Distance" for a rubric-anchored score.** Use *score* or *graded criterion value*.
2. **"Reference" for an internally-authored criterion, rubric or standard.** Use *criterion*.
   The word reference is reserved for external instances with provenance.
3. **"The bar" as a synonym for the floor.** Floors enforce and bars inform; the sentence
   must say which is meant.
4. **"Verified" for an inference.** The evidence labels of this compendium are load-bearing
   and this family's own claims are subject to them, as Part II §6 demonstrated against its
   own charter.
5. **"Zero residual"** without an accompanying coverage declaration. Use *no residual within
   the declared coverage of the named instrument*, or record it as undefined.
6. **"Done" as a claim about quality.** Done is admissibility and is owned by the artifact
   gate. Quality is distance and is owned here. Both may be reported; neither may be said in
   the other's name.

## 10. Terms deliberately not defined here

This family does not own every word it uses, and redefining a term another module owns would
create exactly the two-meanings-one-family failure §1 warns against.

| Term | Canonical owner | CLAE's relationship |
|---|---|---|
| Done | the artifact done gate | consumed unchanged; CLAE adds residual after its verdict |
| Reachable | the reachability audit | pattern reused; definition untouched |
| Design quality score | the design review scorer | cited as the stage-two instance; its criteria are not CLAE's |
| Slop | the token-matching detector | a prohibition; CLAE adds only the shallow-but-real case it cannot see |
| Hard rule | the sealed rule archive | out of scope entirely, per Part I §6 and Part II §11 |
| Findings bus | the findings transport | used as residual transport; its semantics are not redefined |

## 11. Naming conventions inside this family

- Traps are named `T-CLAE-<CONDITION>`, stating the condition rather than the remedy, so the
  name matches what a reader observes before they know what is wrong.
- Process rules are named `PR-CLAE-<IMPERATIVE>`, stating the required behaviour, because a
  rule named after the failure it prevents cannot be read as an instruction.
- Evals are named for what they probe, not for what they expect to find; an eval named after
  its expected result biases its own reading.
- Residual dimensions are named as nouns of the property, never as verdicts.

## Completeness

Terms extracted: **19** across Part III's four tiers. This file is a locator; Part III carries the reasoning for each entry and the ten-pair confusion matrix in full.
