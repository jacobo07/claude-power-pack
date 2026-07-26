---
title: "CLAE Part I — The Internal-Bar Trap"
family: clae
part: I
status: SEALED
date: 2026-07-26
depends_on: []
feeds: [II, III, XXI, XXII, XXIII]
evidence: [R-009 LAAS, Phase 0 PP audit 2026-07-26]
---

# Part I — The Internal-Bar Trap

## 1. Purpose

Establish, with evidence rather than assertion, the defect this entire family exists to
correct: **a system that authors the criteria by which it judges itself cannot discover
its own ceiling.** Part I does not propose the remedy — Parts II through XX do that. Part I
proves the disease is present in this specific stack, names its mechanism precisely enough
that it can be detected elsewhere, and draws the boundary that separates it from the many
internal criteria that are entirely legitimate.

That boundary is the hard part. The naive reading of "internal criteria are bad" would
condemn the hard-rule corpus, the completion gates and the reality contract, all of which
are internal and all of which are correct. Part I exists to prevent that misreading.

## 2. The institutional problem

Claude Power Pack has an unusually dense quality apparatus: 71 modules, 38 hooks, 322
tools, 156 hard rules, a scaffold auditor, an output-quality scorer, a design reviewer with
a deterministic numeric verdict, an empirical verification pipeline, an artifact done-gate
that refuses to accept an exit code as evidence, and a self-quality index that fails on a
silent decrease.

Every one of these instruments is sound. Every one was paid for by a real incident. And
across all of them there is not a single mechanism that can answer the question:

> *This passed. How far is it from good?*

The apparatus is complete on the axis of **compliance** and absent on the axis of
**distance**. It can prove that nothing forbidden happened. It cannot report what remains
between the delivered artifact and the best that artifact could be, because it has no
representation of "best" that was not authored by the same system doing the judging.

This is not a gap in coverage. Coverage is excellent. It is a gap in **dimensionality**.

## 3. First principles

Three propositions, in order of dependence.

**P1 — A predicate discards magnitude.** Any judgment reduced to pass or fail destroys the
information about how far from the boundary the subject sat. A file scoring 71 against a
threshold of 70 and a file scoring 98 are, to the gate, the same file. The gate is not
wrong; it is lossy by construction. The loss is acceptable for prohibitions and
unacceptable for aspirations.

**P2 — A self-authored ceiling is a mirror.** When the criterion and the subject originate
from the same process, the criterion can only encode quality the process already knows how
to recognize. It therefore cannot detect the class of deficiency the process is blind to —
which is precisely the class that matters, because deficiencies the process can recognize
are the ones it already avoids. The instrument's resolution is bounded by the very
capability being measured.

**P3 — Absence of a bar reads as satisfaction of a bar.** When no external reference is
attached, the natural default is not "unknown quality" but "acceptable quality", because
the system has nothing to contradict its own output. Silence is interpreted as consent.
This is the same structural error catalogued elsewhere in this stack: a component nobody
enrolled in an audit is not scored unknown, it is absent from the denominator, and absence
reads as health.

P3 is the load-bearing proposition. P1 and P2 describe a limitation; P3 explains why the
limitation is *invisible from inside* and therefore never triggers its own correction.

## 4. Mechanism of the trap

The trap is not an event. It is an equilibrium, reached in five stages.

**Stage 1 — Legitimate origin.** An incident occurs. A rule or gate is authored to prevent
recurrence. The criterion is internal because the incident was internal. This is correct
and should not be prevented.

**Stage 2 — Predicate collapse.** For the gate to be enforceable it is expressed as a
boolean or a threshold. Magnitude is discarded at this step, silently and necessarily.

**Stage 3 — Accumulation.** More incidents produce more gates. The apparatus grows dense.
Density is experienced as rigor, because every individual gate genuinely catches something.

**Stage 4 — Substitution.** The aggregate of "no gate is failing" comes to *stand for*
quality, rather than standing for absence of known defects. The substitution is never
decided; it is inherited from the fact that no other quality signal exists.

**Stage 5 — Closure.** New quality ambitions are now evaluated against the existing
apparatus. A proposal to raise the bar must justify itself in terms the apparatus already
understands, and the apparatus understands only its own vocabulary. The system has become
closed with respect to quality. It can still improve *conformance*; it can no longer
discover that its notion of good is too small.

Stage 5 is the trap proper. The preceding four are healthy engineering.

## 5. Evidence — the PP instance

Findings from the Phase 0 audit of this repository, 2026-07-26. Each row states the
question the instrument answers and the information it discards. Classification: OBSERVED
means read directly from the module's own source or contract.

| Instrument | Question it answers | Discarded | Class |
|---|---|---|---|
| `done_gate/artifact_done_gate.py` | Does the named artifact exist with the declared shape? | How good the artifact is | OBSERVED |
| `output_contracts` OQS | Is the composite score at or above 70? | The 30 points not earned | OBSERVED |
| `uqf` per-file scoring | Is this file above threshold? | Residual after the pass | OBSERVED |
| `sqi` | Did the index decrease? | Distance to any target above current | OBSERVED |
| `cdio-reviewer` | Score ≥ 80 and zero critical? | What an 80 lacks that a 95 has | OBSERVED |
| `sleepless_qa` | Is the verdict green? | Depth of the green | OBSERVED |
| `scaffold-auditor` | Are forbidden stub markers present? | Shallow implementations carrying none | OBSERVED |
| `hard_rules` (156) | Did a prohibited trigger fire? | Nothing — correctly, see §6 | OBSERVED |

A repository-wide case-insensitive search for the vocabulary of external measurement —
reference-delta, quality distance, anti-underbuild, human oracle, observability-capable
phase zero, deviation ledger — returned **zero files** across 71 modules, 24 dataset
families, 62 commands, 38 hooks and 322 tools. The absence is total, not partial.

**The single exception, and why it matters.** `cdio` scores a design surface 0–100 against
articulated criteria and refuses approval below 80 with any critical finding present. It is
the one place in the stack where a numeric distance to a quality target is computed rather
than a boolean emitted. Its criteria are still internally authored, so it does not escape
P2 — but it demonstrates that the *shape* is implementable here, in this stack, with
deterministic scoring rather than model opinion. CLAE's central engineering claim is that
this shape generalizes out of the design vertical. Its central risk is that it may not.

## 6. The boundary — what is *not* the trap

This is the section that keeps Part I from becoming a generic complaint about metrics.

**Prohibitions are legitimately internal and legitimately binary.** A hard rule states that
a class of action must not occur. There is no meaningful "distance" from a deletion that
destroyed data; the action either happened or did not. Applying distance accounting to a
prohibition would be a category error, and worse, it would soften a stop into a gradient.
The 156-rule corpus is correctly shaped and is out of CLAE's scope entirely.

**Safety floors are legitimately internal.** Secret redaction, destructive-command guards,
authorization checks and isolation boundaries derive their authority from consequence, not
from comparison. No external reference improves them.

**Invariants are legitimately internal.** A contract stating that observed effects minus
declared effects must be recorded is a structural truth about the system, not an aspiration
toward an external standard.

The trap applies to exactly one class: **criteria expressing how good something should be,
where a better external instance exists or could exist.** Architecture quality, prose
depth, interface design, dataset rigor, performance, diagnostic legibility, research
depth — these have external bars, and judging them internally caps them at the stack's
current imagination.

The diagnostic question that separates the classes:

> *If a demonstrably better instance of this exists in the world, would my criterion
> notice? Or would my artifact still pass unchanged?*

If the artifact still passes unchanged, the criterion is a mirror, and the trap applies.

## 7. The three signatures

Detection heuristics, ordered by reliability. Each is a symptom, not a proof; two or more
present together justify investigation.

**Signature 1 — Threshold stability without outcome change.** A quality threshold has not
moved in a long period while the domain has moved. A stable threshold in a moving domain
means the threshold stopped being a target and became a floor nobody revisits.

**Signature 2 — Uniform passing.** Nearly everything the gate examines passes. A gate with
a very high pass rate is either measuring something already solved or measuring at a
resolution below the variation in its subjects. Both mean it has stopped producing
information.

**Signature 3 — Vocabulary closure.** Discussions of quality in the system use only terms
the system itself defined. When no term in the quality vocabulary refers to anything
outside the system, the bar cannot be raised except by internal fiat.

Applied to this stack: Signature 3 is present and total — the Phase 0 search found no
external-measurement vocabulary at all. Signatures 1 and 2 are HYPOTHESIS pending
measurement, and Part XXIV specifies the eval that measures them.

## 8. Failure lineage

The corpus's own evidence for the disease, recorded as lineage rather than assertion.

**Symptom** (R-009): a project brief that specified features and technologies produced
plausible output that satisfied its feature list. **Discriminating change:** the brief was
replaced by a quality constitution naming an external reference bar, qualitative pillars,
quantitative floors and explicitly banned outcomes, with a mandatory loop that placed each
result beside the reference, enumerated the ten largest differences, ranked them by impact,
corrected the top three and re-rendered. **Observed result:** sustained autonomous
progress over many sessions on a target the agent could not have converged on by asking
itself whether the output was acceptable. **Residual risk:** demonstrated once, in a domain
where the reference is an image and the delta is visible. **Applicability boundary:** the
mechanism is VERIFIED for perceptually-observable domains and HYPOTHESIS elsewhere; Part VI
addresses the extraction problem directly and Part XVI addresses what remains unextractable.

**Second lineage, PP-side.** The `reachability.py` discovery producer was written because
the liveness registry was hand-declared, so an undeclared component was not scored unknown
but was absent from the denominator, and the recovery acceptance arbiter therefore sat
unreached without ever being reported missing. That is P3 operating on the *coverage* axis.
The internal-bar trap is the identical structure operating on the *quality* axis. The
stack has already paid for this lesson once and has not yet generalized it.

## 9. Anti-patterns

- **Bar inflation.** The system raises its own threshold and records the raise as progress.
  The mirror is polished, not replaced.
- **Metric theater.** A number improves while the experience the number was meant to
  represent does not. Emerges when the metric becomes the target and no external instance
  anchors it.
- **Rigor by density.** More gates read as higher quality. Density measures defect classes
  known, not quality achieved.
- **Green mistaken for good.** An all-passing pipeline is treated as evidence of excellence
  rather than as evidence of the absence of catalogued defects.
- **Distance discarded at closure.** A phase closes and the residual is not carried forward,
  so the next phase begins believing it starts from zero gap.

## 10. Trap seeds (formalized in Part XXII)

- **Trap — Internal-Bar Inflation.** A system evaluating its own output against criteria it
  authored will converge to its own ceiling and report convergence as success.
- **Trap — Green Sufficiency.** All-gates-passing is read as quality rather than as absence
  of known defects.
- **Trap — Predicate Amnesia.** Magnitude discarded at threshold collapse is never
  recovered, so the difference between barely-passing and excellent is permanently lost.
- **Trap — Category Confusion.** Distance accounting misapplied to a prohibition, softening
  a stop into a gradient. The inverse error, and equally damaging.

## 11. Rule seeds (formalized in Part XXIII)

- **Hard rule candidate — Quality Requires an External Bar.** A claim of quality about an
  artifact class for which a better external instance exists or could exist must name the
  reference it was measured against. Absent a reference, the claim is downgraded to
  conformance and stated as such.
- **Hard rule candidate — Done Requires Residual Visibility.** Closing a unit of work does
  not discharge the obligation to report the distance that remains.
- **Process rule candidate — Classify Before Measuring.** Determine whether the criterion is
  a prohibition, a safety floor, an invariant or an aspiration before selecting an
  instrument. Only the fourth class takes a reference.

## 12. Eval seeds (formalized in Part XXIV)

- **Internal-Bar Detection Eval.** Present an artifact that passes every existing gate and
  is demonstrably inferior to an available external instance. The stack currently reports
  success; a CLAE-equipped stack must report the residual. Failure to distinguish these two
  cases is the defect, measured directly.
- **Threshold Staleness Eval.** For each quality threshold, measure elapsed time since last
  revision against domain movement in the same period. Surfaces Signature 1.
- **Pass-Rate Information Eval.** For each gate, measure pass rate. A rate approaching unity
  is flagged for resolution review. Surfaces Signature 2.
- **Category Assignment Eval.** For a mixed set of criteria, verify correct classification
  into prohibition, safety floor, invariant or aspiration. Guards against the §6 error in
  both directions.

## 13. Production Reality Gate seed (formalized in Part XXV)

A quality claim about an aspirational artifact class is admissible only when: the criterion
class is declared · a named external reference is attached with its version and acquisition
date · the measured delta is recorded · the residual after correction is stated · and the
absence of any of the above is reported as unmeasured rather than omitted silently.

## 14. Pseudoflow — detection pass

Stated in natural language; no executable form appears in this dataset.

Enumerate every quality criterion the stack enforces. For each, classify it as prohibition,
safety floor, invariant or aspiration. Discard the first three from further consideration —
they are correctly internal. For each remaining aspiration, ask whether a better external
instance of the judged artifact class exists or could exist. Where none could exist, record
the criterion as legitimately internal with the reason. Where one could exist, check whether
the criterion names it. If it does not, record an internal-bar finding carrying the
criterion's identity, its owner, the artifact class it governs, the external instance that
should anchor it, and whether that instance is currently obtainable. Rank the findings by
the consequence of the artifact class being capped. Emit the ranked set. Change nothing —
this pass observes and does not correct, because correction requires the reference machinery
that Parts IV through IX define.

## 15. Counterexamples

- **A criterion with no possible external instance.** A rule governing this repository's
  own commit-scoping convention on a multi-pane host has no external better instance; it is
  an invariant of a local condition. Correctly internal. Not a finding.
- **A high pass rate that is correct.** A destructive-command guard should approach a unit
  pass rate, because the behaviour it forbids should be rare. Signature 2 does not apply to
  prohibitions — which is why §6 classification precedes signature detection, and why
  applying the signatures without the classification step generates false findings.
- **An external reference that is worse.** An available external instance may be inferior
  to current output. The mechanism must therefore measure signed distance and be capable of
  reporting that the reference has been exceeded, rather than treating any reference as a
  ceiling to approach. Part IV addresses reference qualification for exactly this reason.

## 16. Integration

Feeds Part II (the remedy's first principles), Part III (ontology), Part XXI (failure
modes), Parts XXII–XXV (registries). Consumes nothing — Part I is the family root.

Cross-family: the P3 structure it names is the same one `liveness/reachability.py` corrects
on the coverage axis; Part XXVI records that relationship formally so the two are understood
as one principle with two applications rather than two coincidentally similar mechanisms.

## 17. Open questions

- Does the `cdio` shape generalize to domains where quality is not perceptually observable?
  This is the family's central unresolved question and Part VI is where it is confronted.
- What is the correct cadence for re-qualifying an external reference before the bar itself
  goes stale? Deferred to Part V.
- Can the four-way criterion classification be performed reliably without human judgment,
  or is it itself an oracle-boundary property? Deferred to Part XVI.

## 18. Institutional writeback

On sealing this family, the trap entries in §10 and the rule candidates in §11 enter UKDL
as candidates carrying this Part as originating evidence — never as automatic promotions,
per the risk-weighted promotion discipline this stack already enforces. The Phase 0 finding
that the external-measurement vocabulary is entirely absent is recorded as the empirical
origin of the family.
