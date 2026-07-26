---
title: "CLAE Part VIII — The Top-K Correction Cycle"
family: clae
part: VIII
depends_on: [VII]
feeds: [IX, XIV, XIX, XXI]
status: SEALED
date: 2026-07-26
---

# Part VIII — The Top-K Correction Cycle

## 1. Purpose

Parts IV through VII produce a ranked residual set. This Part acts on it, and it is where the loop
actually closes: where measured distance becomes closed distance, or fails to, observably.

The cycle is the family's unit of work. Its structure is unremarkable — select, correct,
re-measure, account, decide. Everything of value is in four properties that are routinely absent:
re-measurement sits *inside* the cycle rather than after the programme; the whole dimension is
re-measured rather than the corrected delta; corrections have four possible outcomes rather than
two; and both distance closed and **distance opened** are recorded.

The last of these is the field almost nobody keeps, and it is the one that distinguishes a loop
that converges from one that merely runs.

## 2. Why re-measurement belongs inside the cycle

> **A correction that has not been re-measured is a hypothesis.**

Deferring re-measurement to the end of a programme — a release, a quarter, a milestone — makes
every intermediate correction unfalsifiable while it is being built on. By the time measurement
returns, dozens of corrections have interacted and none can be attributed. The programme learns
one aggregate fact where it could have learned one fact per cycle.

Worse, deferred re-measurement means the *loop itself* is never validated. If the extraction is
mislocalized or the reference is wrong, that is discovered after the entire correction budget has
been spent against it. §9 makes this the special obligation of the first cycle.

## 3. Choosing k

The usual instinct is to set k from available capacity. That is the wrong variable.

> **k is chosen by how much attribution the cycle needs, not by how much capacity it has.**

With k corrections applied between two measurements, the residual change can be attributed to any
of them or to their interaction. At k = 1 attribution is unambiguous. As k rises, attribution
degrades, and the cycle's throughput rises with it. The tradeoff is exactly that and nothing else.

| Condition | k | Reason |
|---|---|---|
| First cycle against a new reference | **1** | The loop is being validated, not the artifact — §9 |
| Correction mechanism unproven for this dimension | **1–2** | Null outcomes must be attributable to a single act |
| Mechanism well understood, residuals independent | **larger** | Attribution is cheap when the causal model is known to hold |
| Residuals known to interact | **1**, or the interacting set together | Splitting coupled residuals across cycles produces oscillation, §7 |
| Any k above correction capacity | **invalid** | Work starts and does not finish, which is Part VII §9's thrash |

The capacity constraint is a ceiling on k, never its source. A team with capacity for ten
corrections and an unproven mechanism should run k = 1 and spend the remaining capacity on
extraction quality, because ten unattributable corrections teach less than one attributable one.

## 4. Re-measure the dimension, not the correction

Re-measuring only the delta that was corrected **guarantees** the appearance of improvement. The
correction was aimed at that delta; of course it moved. This is self-confirming measurement, and
it is the most common way a correction cycle produces reassuring numbers while the artifact drifts.

Two things are invisible under targeted re-measurement.

**Regression.** A correction can open new deltas along the same dimension. A cycle that closes
three and opens two has closed one, and the report will say three unless the whole dimension was
re-measured.

**Displacement.** A correction can close a delta by moving the problem to a dimension that was not
re-measured at all. The residual falls, the artifact is not closer to the reference, and the
displaced gap surfaces cycles later where nothing connects it to its cause.

The requirement therefore: **re-measure the whole dimension under paired observation against the
same pin generation.** Where whole-dimension re-measurement is unaffordable every cycle, the
sampling rules of Part VI §8 apply — declare the rule, record the unsampled region as undefined,
and do not let the corrected delta be the sample.

## 5. The four outcomes

Recording corrections as closed-or-not discards most of what a cycle produces.

| Outcome | Observation | What it means | Next action |
|---|---|---|---|
| **Closed** | Residual fell by approximately the expected amount | The causal model held | Proceed; the model is usable |
| **Partial** | Fell, but materially less than expected | The model of the cause was incomplete | Re-extract at a higher level; a second cause is present |
| **Null** | Did not move | Wrong cause, mislocalized extraction, or the delta was always below the noise floor | Stop correcting; investigate the instrument — §7 |
| **Adverse** | This residual or another rose | The correction was harmful, or the dimensions are coupled | Revert or trade off explicitly; record the coupling |

**Null outcomes are the most informative result a cycle can produce.** A closed outcome confirms a
model that was already believed. A null outcome *falsifies* it, which is the only way the causal
understanding improves. A cycle history consisting entirely of closed outcomes has learned nothing
beyond that the existing model held — a legitimate state, and one that should prompt the question
of whether the corrections were ever difficult enough to be informative.

Null outcomes also have three distinct causes that must be separated before acting: the correction
addressed the wrong cause, the extraction pointed at the wrong location, or the delta was never
distinguishable from noise. Part VI §7's noise floor is what makes the third separable — without
it, a null outcome is uninterpretable, and teams facing uninterpretable nulls default to assuming
the correction was insufficient and applying more of it.

## 6. Legitimate and illegitimate termination

**Legitimate terminations:**

1. Correction capacity for the period is exhausted. Honest and common; the ledger persists.
2. Every remaining residual is explicitly accepted, with an owner and a reason.
3. Every remaining residual is below the noise floor and recorded as indistinguishable — which is
   a statement about the instrument, and carries an implicit next step of improving it.
4. The reference's horizon has expired, per Part V §6. Correction stops until it is re-argued;
   continuing would close distance to a bar the world has passed.
5. The frontier consists entirely of oracle questions and no oracle is available. The loop is
   blocked rather than complete, and says so.

**Illegitimate terminations:**

- **The residual count reached zero.** Count is not distance, per Part VII §7, and a zero count
  without coverage declarations is the unfalsifiable zero of Part II §P8.
- **The gate passed.** Admissibility is not completeness, per Part II §9. This is the trap of Part
  I arriving at the last possible moment.
- **The deadline arrived and the ledger was cleared.** The residuals did not close; they were
  deleted. Part V §9's mark-don't-delete applies with equal force here.

The pattern across the illegitimate three is that each terminates on a *report* rather than on the
world. A loop that ends because its own accounting looks finished has closed itself, which is the
defect this family exists to prevent, reappearing at its final stage.

## 7. Non-termination

Four ways a loop runs forever without converging. Each has a signature and a pivot.

**The null-cycle loop.** Repeated corrections producing null outcomes. After a small number of
consecutive nulls the problem is no longer the correction — it is the causal model, the extraction
localization, or an unmeasured noise floor. Continuing to correct is retrying a failed shape.

> **Pivot rule: after a declared number of consecutive null outcomes on a dimension, stop
> correcting and improve the instrument.**

This is the two-consecutive-failures law this stack already holds, specialized to correction: the
second identical failure is a signal to change the approach, not to try harder. Here the approach
to change is measurement, not effort.

**The oscillation loop.** Correcting A opens B; correcting B reopens A. Signature: the same
residual identifiers reappearing across cycles with adverse outcomes between them. It means the two
dimensions are coupled and cannot be corrected independently. The pivot is to admit the coupled set
into one cycle and correct it together, or to declare an explicit trade-off and accept one residual
with a reason.

**The bar-inflation loop.** The reference advances faster than corrections close the gap, per Part
V §8. Signature: residual flat or rising with substantial distance closed each cycle. Only the
work-versus-bar decomposition separates this from failure to work, which is why that decomposition
is a precondition for interpreting any long-running loop.

**The diminishing-return loop.** Each cycle closes less than the last, and the loop continues
because no stopping economics were declared. The pivot is to declare, in advance, the distance-per-
cycle below which correction effort moves elsewhere. Without a declared threshold the loop runs
until attention is exhausted rather than until value is.

## 8. Cycle accounting

Each cycle records:

- **k** and the admitted set, with the frontier record it was drawn from.
- **Per-residual outcome** from §5, with the expected magnitude alongside the observed one, since
  partial is only distinguishable from closed by comparing them.
- **Distance closed** across the whole dimension.
- **Distance opened** — new residuals or increases created by this cycle's corrections.
- **Net distance change**, which is the only figure that answers whether the cycle helped.
- **Pin generation**, so the cycle is interpretable after a pin update.
- **Instrument changes**, since a residual change following an instrument change is not
  attributable to the correction.

**Distance opened is the field to insist on.** Without it, a cycle that closed four units and
opened four reports as productive, oscillation is undetectable, and displacement per §4 is
invisible. It costs nothing beyond the whole-dimension re-measurement §4 already requires — it is
the other half of a measurement already being taken, and it is discarded because reports are
conventionally shaped around progress.

## 9. The first cycle is a loop validation

The first cycle against a new reference has a different purpose from every subsequent one. It is
not primarily correcting the artifact; it is **testing whether the loop works at all**.

If the first correction produces a null outcome, one of the upstream stages is broken — the
extraction is mislocalized, the reference lacks standing on this dimension, the observations were
not commensurable, or the noise floor was never measured. Continuing from there spends the entire
correction budget against a broken instrument, and every number produced will be confident and
meaningless.

The obligation therefore: **the first cycle against a new reference runs at k = 1 and issues an
explicit loop-validation verdict** — did the residual move in the predicted direction by
approximately the predicted amount? A negative verdict halts correction and returns to Parts IV
through VI. It is not a failure of the cycle; it is the cycle performing its most valuable
function, at the only moment the finding is still cheap.

## 10. Boundary

The cycle does not apply to prohibitions, which are closed on detection rather than ranked and
scheduled. It does not apply where the delta set is smaller than capacity, since there is nothing
to select. It does not apply to exploratory work with no reference, where there is no residual to
close and the correct posture is Part II's *undefined*.

It also does not decide admissibility. A cycle ending with open residuals does not block a release;
that is a floor's decision, per Part II §9. The cycle allocates and verifies correction effort, and
nothing more.

## 11. Evidence — correction loops in this stack

| Surface | Cycle behaviour | Assessment |
|---|---|---|
| Empirical verification runs | Executes checks, reports verdicts | Re-runs, does not re-measure distance; outcomes are binary, so §5's four are collapsed to two |
| Design review pipeline | Review, revise, re-review | The closest existing instance: re-measurement is inside the loop and uses the same scorer, so paired observation holds by construction |
| Recurring-error analysis | Surfaces classes recurring three or more times | A non-termination detector, not a correction cycle; it identifies loops that are not converging |
| Reachability audit with baseline | Names the debt set, re-baselines after wiring | Records distance closed by name; does not record distance opened |
| This compendium's construction | One Part per commit, gates re-run each time | A cycle with re-measurement inside it; whole-set contamination and coherence checks re-run per Part, not just the new file |

Two findings. The stack has verification loops and no *measurement* loops — surfaces re-run checks
and re-derive verdicts, and none re-measures a distance to compare against the previous cycle. And
no surface records distance opened, so a correction that displaces a problem rather than closing it
is currently undetectable everywhere. — Surface behaviours OBSERVED during the Phase 0 audit;
assessments INFERRED against this Part.

## 12. Failure modes

| Failure | Mechanism |
|---|---|
| **Deferred re-measurement** | Corrections accumulate unfalsified; attribution is lost and the loop itself is never validated |
| **Targeted re-measurement** | Only the corrected delta is re-observed; improvement is guaranteed by construction |
| **Binary outcomes** | Partial, null and adverse collapsed into not-closed; the falsifying information is discarded |
| **Uninterpretable null** | No noise floor, so a null outcome cannot be separated from an indistinguishable delta |
| **k from capacity** | Attribution sacrificed for throughput without the trade being noticed |
| **Unrecorded distance opened** | Displacement and oscillation invisible; net-zero cycles report as productive |
| **Termination on a report** | The loop ends because the count reached zero or the gate passed |
| **Undeclared stopping economics** | Diminishing returns run until attention is exhausted |

## 13. Detection signatures

1. **The all-closed history.** Every correction succeeds exactly as predicted. Either the causal
   model is excellent or the re-measurement is targeted; §4 distinguishes them.
2. **The reappearing identifier.** The same residual across multiple cycles with adverse outcomes
   between — coupling and oscillation.
3. **The productive net-zero.** Cycles reporting distance closed, with total distance flat across
   the programme. Distance opened is being created and not recorded.
4. **The escalating null.** Consecutive nulls on one dimension with correction effort increasing.
   The pivot in §7 was not taken.
5. **The missing first-cycle verdict.** A programme with no record of whether its first correction
   behaved as predicted has never validated its own loop.

## 14. Trap seeds — for Part XXII

- **T-CLAE-TARGETED-REMEASURE** — re-measuring only the corrected delta, which guarantees apparent
  improvement and hides regression and displacement.
- **T-CLAE-BINARY-OUTCOME** — corrections recorded as closed or not, discarding the null outcomes
  that carry the falsifying information.
- **T-CLAE-UNRECORDED-OPENING** — distance opened by a correction is not recorded, so net-zero and
  oscillating cycles report as productive.
- **T-CLAE-NULL-ESCALATION** — consecutive null outcomes met with more correction effort rather
  than instrument investigation.
- **T-CLAE-REPORT-TERMINATION** — the loop ends because the residual count reached zero or a gate
  passed, rather than because of a fact about the world.

## 15. Rule seeds — for Part XXIII

- **PR-CLAE-REMEASURE-IN-CYCLE** — re-measurement occurs inside the cycle. A correction not
  re-measured before the next is admitted is recorded as a hypothesis, not a closure.
- **PR-CLAE-WHOLE-DIMENSION** — re-measurement covers the whole dimension, not the corrected delta.
  Where sampled, the sampling rule is declared and the corrected delta is not the sample.
- **PR-CLAE-FOUR-OUTCOMES** — every correction records closed, partial, null or adverse, with the
  expected magnitude alongside the observed one.
- **PR-CLAE-K-FROM-ATTRIBUTION** — k is set by the attribution the cycle requires; capacity is a
  ceiling on k, never its source.
- **PR-CLAE-RECORD-DISTANCE-OPENED** — every cycle records distance opened alongside distance
  closed, and reports the net.
- **PR-CLAE-NULL-PIVOT** — after a declared number of consecutive nulls on a dimension, correction
  stops and instrument investigation begins.
- **PR-CLAE-VALIDATE-THE-LOOP** — the first cycle against a new reference runs at k = 1 and issues
  a loop-validation verdict. A negative verdict halts correction and returns to extraction.

## 16. Eval seeds — for Part XXIV

- **Outcome-distribution probe.** Over a programme's history, count closed, partial, null and
  adverse. A distribution of nearly all closed indicates targeted re-measurement rather than an
  excellent model.
- **Net-versus-gross probe.** Compare summed distance closed against the change in total distance.
  A large divergence is unrecorded distance opened.
- **Recurrence probe.** Identify residual identifiers appearing in multiple cycles. Their presence
  with adverse outcomes between is oscillation and indicates coupling.
- **First-cycle probe.** For each reference in use, verify a loop-validation verdict exists. Absent
  one, the loop beneath it was never tested and its outputs are unwarranted.
- **Null-response probe.** For each null outcome, verify whether the next action was instrument
  investigation or more correction. The latter is the §7 failure and is cheap to detect.

## 17. Production Reality Gate seed — for Part XXV

**Correction Cycle Gate.** A cycle may be recorded as complete only when re-measurement covered the
whole dimension under paired observation against the same pin generation, every admitted residual
carries one of the four outcomes with expected and observed magnitudes, distance opened is recorded
alongside distance closed, and the net is published. A programme's first cycle against any reference
additionally requires a loop-validation verdict. Failing cycles are recorded as hypotheses rather
than closures — a status, not a block, consistent with distance never enforcing.

## 18. Pseudoflow — running a cycle

Take the ranked set and its frontier record. Choose k from the attribution the cycle needs: one if
the reference is new, one if the correction mechanism for this dimension is unproven, one if the top
residuals are known to interact. Confirm k does not exceed correction capacity; if it does, lower k
rather than admitting work that cannot finish.

Before correcting, state for each admitted residual the magnitude the correction is expected to
close. Without a prediction, partial cannot be distinguished from closed and the cycle's most
informative outcome is unavailable.

Apply the corrections. Change no instrument during the cycle; an instrument change makes the
residual movement unattributable and the cycle uninterpretable.

Re-measure the whole dimension under paired observation, against the same pin generation, with the
same instrument.

Assign each admitted residual one of the four outcomes by comparing observed movement to predicted.
Record distance closed, and separately every new or increased residual as distance opened. Publish
the net.

Where any outcome is null, do not increase correction effort. Determine first whether the cause was
wrong, the extraction mislocalized, or the delta below the noise floor. Where the count of
consecutive nulls on this dimension has reached the declared threshold, stop correcting it and
investigate the instrument.

Where any outcome is adverse, record the coupling between the residuals involved so the next
ranking admits them together rather than alternating between them.

Decide termination against §6. Terminate on a fact about the world — capacity, acceptance, noise
floor, expired horizon, unavailable oracle. Do not terminate because the count reached zero or a
gate passed.

If this was the first cycle against this reference, issue the loop-validation verdict before
admitting a second cycle.

## 19. Integration

Part IX receives cycle accounting as ledger entries, including distance opened, which is what makes
the ledger's trend interpretable. Part XIV's toolsmith behaviour is triggered by §7's null pivot:
when the instrument is the problem, building an instrument becomes the work. Part XIX's evidence-
gated autonomy uses the loop-validation verdict as its entry condition, since autonomous correction
against an unvalidated loop is unbounded by construction. Part XV converts adverse outcomes into
durable probes, so a coupling discovered once is not rediscovered.

Outside the family, the design review pipeline is the nearest existing instance of in-cycle
re-measurement and is cited as the pattern. The recurring-error analysis is endorsed as a
non-termination detector and is the natural place §7's null-pivot threshold would be enforced.

## 20. Open questions

1. What is the correct null threshold before pivoting to the instrument? Two follows this stack's
   existing law, and whether correction has a different characteristic count than general tool
   failure is unmeasured. — HYPOTHESIS.
2. Can distance opened be attributed to a specific correction when k exceeds one? §8 requires
   recording it; attributing it may require k = 1, which would make the attribution/throughput
   trade sharper than §3 states. — UNKNOWN.
3. Is whole-dimension re-measurement affordable at realistic cycle rates? §4 requires it and Part
   VI's sampling rules are the escape, but a sampled whole-dimension measurement may reintroduce
   the self-confirmation it was meant to prevent if the sampling correlates with the correction. —
   UNKNOWN, and the most likely practical obstacle in this Part.

## 21. Institutional writeback

Five trap seeds, seven process-rule seeds, five eval seeds and one production gate.

Three portable results. **Re-measure the dimension, not the correction** — targeted re-measurement
guarantees the appearance of improvement, and the fix costs nothing beyond measuring what was
already going to be measured. **Record distance opened** — the other half of a measurement already
being taken, whose absence makes displacement and oscillation undetectable and lets net-zero cycles
report as productive. And **the first cycle validates the loop, not the artifact** — a k = 1 cycle
with an explicit verdict, taken at the one moment when discovering that the instrument is broken is
still cheap.
