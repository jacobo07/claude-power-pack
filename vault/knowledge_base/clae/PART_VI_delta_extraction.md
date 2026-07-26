---
title: "CLAE Part VI — Delta Extraction"
family: clae
part: VI
depends_on: [IV, V]
feeds: [VII, VIII, XII, XIII, XVI]
status: SEALED
date: 2026-07-26
---

# Part VI — Delta Extraction

## 1. Purpose

Parts IV and V established the reference: what qualifies, how it is acquired, how it is held. The
artifact was always available. This Part addresses the step that sits between having both objects
and having a residual, and which is routinely assumed to be free.

**Possessing two objects does not give you the difference between them.** Extraction is work, it
has a cost, it has a fidelity, it has failure modes of its own, and — the reason this Part exists
— it fails *silently*. A failed acquisition is obvious, because there is no reference. A failed
extraction produces numbers.

This Part states the precondition extraction must satisfy, grades difference visibility on a
five-level ladder so that "we measure quality" becomes an answerable question, names the
commensurability failures that make a difference an artifact of the instruments rather than of the
objects, establishes the noise floor requirement, and bounds the domains where extraction cannot
be made to work at all.

## 2. The observability precondition

A delta can be extracted along a dimension only when three conditions hold together.

1. The dimension is **observable in the artifact**.
2. The dimension is **observable in the reference**.
3. The two observations are **commensurable** — same instrument, same conditions, same units, same
   granularity.

The first two are checked routinely. The third is skipped almost universally, and it is the one
that matters, because a difference between two non-commensurable observations is **a property of
the instruments, not of the objects**. It is a real number, it is stable, it will trend, and it
describes nothing about the artifact.

Where any of the three fails, the honest output is *undefined* per Part II §7 — not a partial
measurement, not an estimate. A dimension that fails the precondition and is measured anyway
produces the most damaging class of residual: confidently wrong, and indistinguishable in the
ledger from a sound one.

## 3. The extraction ladder

Difference visibility is not binary. Five levels, each strictly stronger than the last, each
enabling a different downstream action.

| Level | Name | What it supports | What it cannot support |
|---|---|---|---|
| **L0** | Undetectable | Nothing; the dimension is undefined | Any claim whatever |
| **L1** | Detectable | A statement that they differ | Where, how much, or what to do |
| **L2** | Localized | Correction — you know where to act | Ordering; every location looks equally urgent |
| **L3** | Quantified | Ranking and trend — magnitudes compare | Efficient correction; cause is still unknown |
| **L4** | Attributed | Efficient correction — the cause is identified | — |

The ladder converts a vague question into a precise one. "Do you measure quality along this
dimension?" is unanswerable; "at what level do you extract this dimension?" has one of five
answers, and each answer states exactly which downstream operations are legitimate.

Two consequences follow immediately.

**A stack at L1 can report distance and cannot act on it.** This is the common state: gates that
detect a difference and report a verdict. Retaining their pre-threshold value, per Part II §2,
usually moves them to L3 for free — the magnitude was computed — but not to L2, since location was
never extracted. That is worth knowing before promising that retention alone yields actionable
residuals.

**Impact ranking requires L3.** Part VII orders residuals by consequence. Ordering L1 or L2
residuals produces an ordering over things whose magnitudes are unknown, which is discovery order
wearing a rank — the exact failure Part VII exists to prevent. The ladder therefore gates Part VII
rather than merely informing it.

## 4. Extraction methods

| Method | How it works | Typical level | Commensurable by construction |
|---|---|---|---|
| **Direct comparison** | Both objects share a representation; compare it | L2–L3 | Yes |
| **Projection** | Both are transformed into a common representation, then compared | L1–L3 | Only if the projection is argued |
| **Probe-and-compare** | The same instrument is run against both; outputs compared | L1–L4 | Yes |
| **Decomposition** | Both are split into parts; parts compared | L2–L4 | No — requires a shared decomposition |
| **Behavioural** | Both are subjected to identical inputs; responses compared | L1–L4 | Yes, if conditions are controlled |

**Probe-and-compare is the workhorse.** It is commensurable by construction, since one instrument
observes both objects, and it reaches L4 when the instrument reports cause rather than only
outcome. Where a dimension admits it, it should be preferred over every alternative.

**Behavioural extraction is the only option for dimensions with no static representation.** Where
what matters is what the object *does* rather than what it *is*, no amount of inspection reaches
the dimension. Its cost is that conditions must be controlled, which is the subject of §7.

**Decomposition is the seductive one.** Splitting both objects into parts and comparing part-wise
feels rigorous and produces detailed output. Its failure is §6.

## 5. Commensurability failures

Six ways two honest observations become an incomparable pair.

1. **Different instruments.** Two measurement tools with different conventions, calibration or
   coverage. The difference reports the tools.
2. **Different conditions.** Cold versus warm, loaded versus idle, different inputs, different
   environment. The difference reports the conditions.
3. **Different granularity.** One observation aggregates where the other itemizes. The difference
   reports the aggregation.
4. **Different sampling.** Different subsets, or one sampled and one exhaustive. The difference
   reports the sampling rule.
5. **Different times.** The artifact measured now, the reference measured at acquisition. The
   difference includes everything that changed in between, including the instrument.
6. **Different observers.** Where the instrument is a judgment, two judgments made at different
   times by different parties are not one measurement performed twice.

The remedy for all six is one discipline.

> **Paired observation: observe both objects in the same act, with the same instrument, under the
> same conditions.**

Not the same procedure applied twice — the same act. A fresh measurement of the artifact compared
against a stored measurement of the reference violates the discipline even when the stored
measurement was taken correctly, because the instrument, conditions and environment have all moved
in the interval and none of that movement is recorded.

This is where Part V §4's preference resolves. Holding the *object* rather than derived numbers is
what makes paired observation possible later: the captured artifact can be re-measured now,
alongside the current artifact, with today's instrument under today's conditions. Holding only
numbers forecloses paired observation permanently, and every subsequent comparison silently
carries failure five.

## 6. The projection trap and the structure trap

Two extraction strategies destroy the dimension while producing detailed output.

**The projection trap.** Both objects are transformed into a common representation and compared
there. The trap is that the projection may not preserve the dimension of interest — and the
comparison will still yield differences, which will be reported as though they described the
originals. The classic form is comparing two systems by comparing their descriptions: the
projection is into a representation both authors control, which reintroduces the closed loop of
Part I at the extraction layer, after a legitimately external reference was acquired.

The requirement: **a projection must carry an argument that it preserves the dimension being
measured.** Absent that argument, the extraction level is L0 regardless of how much output it
produced.

**The structure trap.** Decomposition compares part-wise, which requires both objects to share a
decomposition. When a reference and an artifact solve the same problem with different structures —
the common case, since structural difference is often the point — part-wise comparison generates
deltas that are structural rather than substantive. "The reference has a component we lack" is a
delta only if the component's *effect* is absent from the artifact. If the artifact achieves the
same effect differently, the delta is spurious, and acting on it means importing the reference's
structure for its own sake.

The requirement: **deltas are extracted at the level of effect, not structure.** Structural
comparison is admissible only where the structure is itself the dimension. Everywhere else it
manufactures work that closes no gap, which is worse than no extraction because it consumes the
correction budget Part VIII allocates.

## 7. Determinism, variance, and the noise floor

Extraction over a surface that varies between observations yields differences that mix the objects
with the variation. Fixed seeds, fixed conditions and controlled environments reduce it; nothing
eliminates it.

This produces a requirement almost universally skipped:

> **A difference smaller than the observation's own variance is not a difference.**

Determining that requires measuring the **noise floor** — repeatedly observing *the same object*
under the same conditions and recording the spread. Only then can a delta between two objects be
distinguished from the instrument's own scatter.

Most extraction never measures its noise floor, which produces two failures of opposite sign. Small
deltas are reported as real and consume correction effort that changes nothing measurable. And
genuine improvements smaller than the noise are reported as no change, which teaches that the work
does not matter.

The rule that follows: **a residual below the noise floor is recorded as indistinguishable, not as
small.** These are different claims. *Small* says the gap is nearly closed. *Indistinguishable*
says the instrument cannot tell — which may mean the gap is closed, or that a better instrument is
required. Conflating them lets an instrument's limits be read as an artifact's quality, which is
Part II §P8 appearing again at the extraction layer.

The noise floor is a property of the instrument and the conditions, measured once per instrument
rather than per assessment, and recorded alongside coverage. It is cheap and it is the difference
between a number and a measurement.

## 8. Sampling

Exhaustive extraction is often unaffordable. Sampling is legitimate under three conditions, all
from Part II §7 applied here.

1. The sampling rule is **declared** — what was covered, what was not, and how the subset was
   chosen.
2. The unsampled region is recorded as **undefined**, never as zero. An unexamined region reporting
   no gap is the unfalsifiable zero.
3. The sample is **not chosen by the party whose residual it measures**, or the choice is recorded
   with its reasoning, per Part IV §6's selection-laundering hole.

Condition three is the one that decides whether sampled extraction is measurement or theatre.
Sampling exactly the regions expected to look good is a complete closed loop, executed inside a
legitimately external reference relationship.

## 9. Domains where extraction fails

Six classes where the precondition cannot be satisfied. Recognizing them is what keeps *undefined*
an honest verdict rather than an admission of laziness.

1. **No corresponding representation.** The reference achieves the effect through means with no
   counterpart in the artifact. Nothing to compare against, and decomposition here produces the §6
   structure trap.
2. **Counterfactual dimensions.** Whether an artifact *would have* behaved differently under
   conditions that never occurred. No observation of either object reaches it.
3. **Relational dimensions.** Fit with a specific codebase, team or context. The property is not in
   the object; it is in the relation, and the reference's relation is to a different context.
4. **Emergent-over-time dimensions.** Properties realized over a horizon longer than any
   observation window. Proxies exist and their correlation must be argued, per Part II §7.
5. **Dimensions where observation changes the object.** Measuring perturbs what is measured.
6. **Judgment dimensions.** Properties that are irreducibly evaluative. These are not extraction
   failures but oracle questions, per Part III's boundary test, and route to Parts XVI and XVII.

For classes one through five, the honest sequence is: attempt a formal bound, attempt a discovered
set per Part IV §7, attempt a proxy with an argued correlation, and failing all three, record
undefined with the class. That sequence converts more of this list into measurable dimensions than
its length suggests — most notably class one, where the effect-level reframing of §6 often
restores comparability that structural comparison had destroyed.

## 10. Evidence — extraction levels across this stack

| Surface | Extraction performed | Level | Note |
|---|---|---|---|
| Reachability audit | Names the discovered-minus-reachable set | **L2** | Localized; the set is enumerated, not counted |
| Design review scorer | Graded values plus classified findings against criteria | **L3** | Quantified within its criteria; no external reference |
| Index-direction monitor | Direction and magnitude against a prior value | **L3** | Paired by construction — same instrument, both generations |
| Code quality framework | Per-file scores with fix hints | **L3–L4** | Fix hints reach attribution where the hint names a cause |
| Artifact done gate | Present-versus-absent over a declared set | **L2** | Localized; the absent members are nameable |
| Slop detector | Token match | **L1** | Correct — a prohibition needs only detection |
| This compendium's Phase 0 audit | Named the owning module per proposed mechanism | **L4** | Attributed; the cause of each duplication was identified |

Two observations. The stack extracts at a higher level than it *reports* — several surfaces reach
L2 or L3 internally and publish L1, which is Part II's retention thesis restated in this Part's
vocabulary. And no surface records a noise floor, so no residual in the stack can currently
distinguish a small difference from an indistinguishable one. — Surface behaviours OBSERVED during
the Phase 0 audit; level assignments INFERRED against §3.

## 11. Boundary

Extraction discipline applies where a difference is to be measured. It does not apply to
prohibitions, which need only detection and are correctly L1. It does not apply to admissibility
gates with no downstream consumer of magnitude.

It also does not apply *upward*: extraction cannot rescue a bad reference. A flawlessly extracted
delta against a captured, stale or synthesized reference is a precise measurement of nothing, and
the precision makes it more convincing. Where Parts IV and V fail, this Part cannot compensate, and
the sequencing of the family reflects that.

## 12. Failure modes

| Failure | Mechanism |
|---|---|
| **Non-commensurable pair** | Differences report the instruments or conditions rather than the objects |
| **Dimension-destroying projection** | Both objects transformed into a representation lacking the dimension; output still produced |
| **Structural delta** | Part-wise comparison generates differences of form where effect is equivalent |
| **Noise reported as signal** | Deltas below the unmeasured noise floor consume correction effort |
| **Signal reported as noise** | Real improvements below the noise floor read as no change, teaching futility |
| **Unsampled read as clean** | The unexamined region reports no gap |
| **Self-selected sample** | The measured party chooses what is measured |
| **Stored-versus-fresh comparison** | The artifact measured now against the reference measured then |

## 13. Detection signatures

1. **The stable offset.** A residual that is nearly constant across artifact versions. Constant
   differences usually indicate an instrument or condition mismatch, not a persistent gap.
2. **The structural inventory.** A delta list reading as an inventory of the reference's components.
   Effect-level extraction rarely produces one-to-one component lists.
3. **The absent noise floor.** No instrument in the pipeline reports its own variance. Every small
   residual downstream is uninterpretable.
4. **The description comparison.** Both objects represented by documents written by their own
   authors. The projection is into a representation both parties control.
5. **The convenient sample.** The sampled region and the region the measured party is confident
   about coincide, with no recorded selection rule.

## 14. Trap seeds — for Part XXII

- **T-CLAE-INCOMMENSURABLE-PAIR** — artifact and reference observed with different instruments,
  conditions or times; the resulting difference describes the observation.
- **T-CLAE-PROJECTION-DESTROYS-DIMENSION** — both objects projected into a common representation
  that does not carry the measured dimension; detailed output, level L0.
- **T-CLAE-STRUCTURAL-DELTA** — differences of form reported where effect is equivalent, importing
  the reference's structure for its own sake.
- **T-CLAE-NOISE-AS-SIGNAL** — deltas below an unmeasured noise floor treated as real and ranked.
- **T-CLAE-CONVENIENT-SAMPLE** — the measured party selects the sampled region without a recorded
  rule.

## 15. Rule seeds — for Part XXIII

- **PR-CLAE-PAIRED-OBSERVATION** — artifact and reference are observed in the same act, with the
  same instrument, under the same conditions. A fresh-versus-stored comparison is labelled as
  such and its residuals carry that fidelity.
- **PR-CLAE-DECLARE-EXTRACTION-LEVEL** — every residual records its extraction level from §3.
  Ranking consumes only L3 or above.
- **PR-CLAE-ARGUE-THE-PROJECTION** — a projection-based extraction records an argument that the
  projection preserves the dimension. Absent it, the extraction is L0.
- **PR-CLAE-EFFECT-NOT-STRUCTURE** — deltas are extracted at the level of effect. Structural
  comparison is admissible only where structure is itself the dimension.
- **PR-CLAE-MEASURE-THE-NOISE-FLOOR** — every instrument records its variance under repeated
  observation of one object. Residuals below it are recorded as indistinguishable, never as small.
- **PR-CLAE-DECLARE-THE-SAMPLE** — sampled extraction declares its rule, records the unsampled
  region as undefined, and records who chose the sample and why.

## 16. Eval seeds — for Part XXIV

- **Commensurability probe.** For each extraction in use, verify artifact and reference are observed
  by one instrument under one set of conditions. Any fresh-versus-stored pair is relabelled.
- **Noise-floor probe.** For each instrument, observe one unchanged object repeatedly and record the
  spread. Any residual currently reported below that spread is reclassified as indistinguishable.
  This probe is cheap and is expected to invalidate a meaningful share of existing residuals, which
  is the point.
- **Level-declaration probe.** Verify every residual carries an extraction level, and that no
  ranking consumes residuals below L3.
- **Projection-argument probe.** For each projection-based extraction, require the preservation
  argument. Those without one are reclassified L0 and their residuals withdrawn.
- **Structure-versus-effect probe.** Sample delta lists and classify each entry as structural or
  effect-level. A list dominated by structural entries indicates the §6 trap.

## 17. Production Reality Gate seed — for Part XXV

**Extraction Integrity Gate.** A residual may enter the ledger only when it records its extraction
level, its instrument, that instrument's noise floor, whether the observation was paired, and — if
sampled — its sampling rule and unsampled region. A residual below the recorded noise floor enters
as indistinguishable. A residual from an unargued projection does not enter at all, since its level
is L0 and L0 supports no claim.

## 18. Pseudoflow — extracting a delta

Given an artifact, a pinned reference and a dimension: first ask whether the dimension is
observable in both objects and whether the two observations can be made commensurable. If any of
the three fails, record undefined with the failing condition and stop.

Choose the method. Prefer probe-and-compare, which is commensurable by construction. Where the
dimension has no static representation, use behavioural extraction and control the conditions.
Where a projection is unavoidable, write the argument that it preserves the dimension before
extracting anything; if the argument cannot be made, the level is L0 and no residual follows.

Observe both objects in the same act. Where the reference is held as a captured artifact,
re-measure it now rather than reading its stored numbers.

Before interpreting any difference, observe one unchanged object repeatedly and record the spread.
Any difference within that spread is recorded as indistinguishable.

Record the extraction level actually achieved, not the level intended. Localization and attribution
are separate achievements from detection, and claiming them without performing them makes the
residual unusable downstream in a way nobody can see.

Where extraction was sampled, record the rule, the unsampled region as undefined, and who chose the
sample.

Where the delta list resembles an inventory of the reference's components, re-derive it at the level
of effect before it goes further.

## 19. Integration

Part VII consumes extraction levels as a precondition: ranking requires L3. Part VIII's correction
cycle requires L2 to act and works far more efficiently from L4. Part XII's observability-capable
phase zero is, read through this Part, the requirement that the extraction precondition be
satisfiable *before* the first feature exists. Part XIII's instrument taxonomy inherits the noise
floor and coverage as instrument properties. Part XVI receives §9's class six, the judgment
dimensions, as its admission criterion.

Outside the family, the index-direction monitor is noted as the one surface already performing
paired observation by construction, and the reachability audit as the one already extracting at L2
by naming its set rather than counting it.

## 20. Open questions

1. Is the noise floor stable enough to measure once per instrument, or does it vary with the object
   observed? Treating it as an instrument property is the assumption in §7 and it is unmeasured. —
   HYPOTHESIS.
2. Can effect-level extraction be performed without a shared model of what the effect *is*? §6
   requires comparing effects across structurally different objects, which presumes an effect
   vocabulary neither object supplies. — UNKNOWN, and the principal obstacle to applying this Part
   outside domains with obvious observable outputs.
3. Does extraction level compose? Where a residual is derived from several extractions at different
   levels, whether the result takes the minimum is assumed and unverified. — HYPOTHESIS: minimum.

## 21. Institutional writeback

Five trap seeds, six process-rule seeds, five eval seeds and one production gate.

Two portable results. The **extraction ladder** turns an unanswerable question about measurement
quality into a five-valued one, and each value states precisely which downstream operations are
legitimate — usable immediately by any team, with no machinery. And the **noise floor requirement**:
a difference below an instrument's own variance is not small, it is indistinguishable, and the
distinction is the difference between a number and a measurement. Measuring it costs one repeated
observation per instrument, and this stack currently has none.
