---
title: "CLAE Part XI — Floor Derivation Versus Floor Imposition"
family: clae
part: XI
depends_on: [X]
feeds: [XVIII, XIX, XXIII, XXV]
status: SEALED
date: 2026-07-26
---

# Part XI — Floor Derivation Versus Floor Imposition

## 1. Purpose

Part X established that a floor must be derived rather than imported, and made that the first of
five legitimacy properties. It did not say how derivation is performed, nor why importation fails
in a way that borrowing a good idea normally does not.

This Part supplies both. It explains why a number that was correct where it came from is arbitrary
here, gives the procedure that turns a consequence into a minimum, establishes that every failure
class admits **three** different floors rather than one, and argues the practical inversion that
matters most: **qualitative floors are more portable than quantitative ones**, which is the opposite
of the instinct that numbers are the rigorous form.

## 2. The imported floor problem

A threshold arrives from elsewhere — a figure for test coverage, a latency budget, a minimum score,
a retry count. Each was derived once, somewhere, from a real consequence in a real context. The
number travelled. **The derivation stayed behind.**

What arrives is therefore a value stripped of the reasoning that made it correct, and the reasoning
is the only thing that could tell you whether it is correct here.

The compounding problem is that an imported floor is **unarguable**. Nobody can defend it, because
nobody knows what it was derived from. Nobody can attack it for the same reason. It cannot be
tuned, because there is no model of what tuning would change. It cannot be retired, because Part X
§5 requires a named consequence and none came with it.

An unarguable floor has exactly two fates, and both are failures. It is obeyed ritualistically,
becoming ceremony that consumes effort without preventing anything — Part X §6's accumulation
problem, seeded at import. Or it is quietly ignored, teaching that floors in general are advisory,
which damages the floors that *were* derived.

## 3. Four mismatches

Importation fails through four specific mechanisms, and naming them is what makes the failure
predictable rather than mysterious.

**Consequence mismatch.** The origin's failure cost differs from ours. A latency floor derived where
a delay loses a transaction is not the floor where a delay produces a slightly slow report. The
number encodes the origin's cost function invisibly.

**Distribution mismatch.** The number embeds an assumption about the shape of inputs, traffic or
data. A threshold tuned for a heavy tail is wrong for a uniform distribution and vice versa, and
nothing in the number states which it assumed.

**Instrument mismatch.** The origin measured with a different instrument, so the *same number means
something different*. This is Part VI §5's commensurability failure applied to thresholds rather
than to observations, and it is the least noticed of the four because both sides genuinely have "the
same metric".

**Maturity mismatch.** The number was appropriate at a stage the artifact has not reached or has
passed. Floors derived for a mature system applied to an early one block all progress; floors
derived for an early system applied to a mature one permit failures the maturity was supposed to
have eliminated.

## 4. The derivation procedure

Five steps, in order. The order matters: every step after the first is unanswerable without it, and
starting at the number is what produces imposition wearing derivation's clothes.

1. **Name the failure concretely.** The event, not the category. Not "poor reliability" but "the
   operation is interrupted and leaves state a subsequent run cannot proceed from". A category
   cannot be thresholded; an event can.
2. **Establish the consequence.** Who bears it, what it costs them, how it is discovered, and how
   long it persists before discovery. Consequence borne by the producer and consequence borne by a
   consumer yield very different floors for the same event.
3. **Find the thresholds of consequence** — all three, per §5.
4. **Choose which threshold the floor sits at, and record why.** This is a decision about risk
   posture, not a fact about the domain, and §5 explains why stating it is the whole point.
5. **Record the derivation** in full, so the floor can be re-derived when the consequence changes
   rather than defended by seniority.

## 5. Every failure class yields three floors

The sharpest result in this Part. For any failure event there are three distinct thresholds, and
they are routinely collapsed into one.

| Threshold | Definition | Floor placed here means |
|---|---|---|
| **Possibility** | Below this value, the failure cannot occur at all | Maximum strictness; often unaffordable, sometimes the only acceptable choice |
| **Likelihood** | Below this value, the failure is probable in normal operation | The usual correct choice; failures remain possible but not expected |
| **Irreversibility** | Below this value, the failure is unrecoverable when it occurs | Minimum strictness; failures are tolerated so long as they can be undone |

**The same failure class therefore yields three different floors, and which one is chosen is a
decision rather than a fact.** Almost every floor in circulation is stated as though it were a fact,
which is precisely what makes it unarguable.

Placing the floor at possibility is correct where the consequence is severe and irreversible, and
wasteful otherwise. Placing it at irreversibility is correct where failures are cheap and recovery
is reliable, and reckless where recovery depends on someone noticing. The likelihood threshold is
the common answer and it is the one that most needs its reasoning recorded, because it embeds a
judgment about what "normal operation" is.

Recording the placement converts a hidden risk posture into a stated one. Two teams disagreeing
about a floor are usually disagreeing about which threshold it should sit at, and they cannot
discover that while both are arguing about a number.

## 6. Prefer the qualitative form

The instinct is that a number is the rigorous form of a floor and a sentence is a soft version of
one. For floors specifically, this is backwards.

> **A qualitative floor carries its derivation in its statement. A quantitative floor does not.**

Compare two statements of the same intent. *"Every loop, retry and recursion carries a declared
bound and a defined behaviour at that bound"* travels intact to any domain, any language, any
maturity level, and can be argued with directly — one can dispute whether a particular construct
needs a bound. *"Retries must not exceed three"* travels as a bare number, is correct only where it
was derived, and can be disputed only as a preference.

The qualitative form is also **checkable without calibration**. Determining whether a bound exists
requires no knowledge of what the right bound is. Determining whether a value clears three requires
knowing that three was right, which is exactly the knowledge that did not travel.

All six of Part X §4's shapes are stated qualitatively for this reason. They are floors that name
the property rather than the value, and that is why they can be offered to any stack without a
derivation attached.

The practical rule: **state the floor qualitatively wherever the intent can be captured that way,
and reach for a number only when the property is genuinely continuous and a line must be drawn.**

## 7. When a number is unavoidable

Some properties are continuous and admit no qualitative statement. Then the number is derived per
§4, and it carries one additional field.

**Sensitivity.** How much does the consequence change if the value moves by a fifth in either
direction?

This yields the test that separates a derived number from a decorated one:

> **If you cannot say what would change at the value plus or minus twenty percent, the number is
> decoration.**

A floor whose consequence is insensitive across a wide band is *arbitrary within that band*, and the
honest form says so — a floor stated as a range with a chosen operating point communicates far more
than a single figure implying a precision that was never established. Recording insensitivity is not
an admission of weakness; it is what prevents later arguments about a digit that never mattered, and
it is what tells a future reader which floors can be relaxed cheaply under pressure.

## 8. Borrowing honestly

This Part is not an argument for ignoring outside practice, which would be absurd and would
contradict Part IV's entire premise that external objects are the only escape from a closed loop.

An externally-authored minimum, with provenance and a standing argument, is a legitimate **reference**
in Part IV's exact sense. The distinction is what happens next.

- **Imposition:** adopt the number and enforce it.
- **Honest borrowing:** adopt the number as a *hypothesis*, then run §4 locally against it — name
  the failure it was protecting against, establish whether that consequence holds here, and confirm
  or revise the value.

The output of honest borrowing is a derived floor that happens to agree with an external one, and it
is now arguable, tunable and retirable. The output of imposition is an unarguable number. The
difference is a derivation, not a value, and frequently the value is unchanged.

Where the derivation cannot be performed in the time available, the honest degradation is to adopt
the external floor **labelled provisional, with the derivation recorded as owed**. A provisional
floor is better than no floor and worse than a derived one, and labelling it keeps it from
calcifying into permanent unarguable ceremony.

## 9. Floor drift and re-derivation

Derived floors go stale, and they go stale differently from references.

A reference goes stale when the world advances past it. A floor goes stale when **the consequence
changes** — the failure becomes more expensive, or cheaper, or recoverable, or reaches a different
bearer. The floor's value can be entirely untouched while the reasoning beneath it has been
invalidated.

The re-derivation trigger is therefore a change in consequence, **not a calendar**. Periodic floor
review catches accumulation, per Part X §6, but it does not catch drift, because the floor looks
exactly as it always did. Drift is caught by noticing that the consequence moved — which is why §4
step five requires the consequence to be recorded alongside the value. A floor recorded as a bare
number cannot be checked for drift by anyone, including its author a year later.

## 10. Where imposition is correct

Three situations. Deriving in these would be the error.

**Regulatory, contractual or externally-mandated minima.** Imposed by definition, and not the
agent's to derive. The correct handling is to record them as imposed, with their source, and to
place any *additional* derived floor above them rather than re-litigating the mandate.

**Physical and formal limits.** A bound that follows from a conservation argument or an
information-theoretic limit is not derived from consequence at all — it is a fact about the world,
Part IV's formal-bound reference class appearing on the enforcement side. It needs no derivation and
cannot go stale.

**Time-constrained adoption**, per §8's provisional path. An unlabelled imported floor is
imposition; a labelled one with the derivation recorded as owed is a legitimate temporary state.

## 11. Evidence — derived and imposed floors in this stack

| Floor | Derivation recorded? | Assessment |
|---|---|---|
| Parallel tool-call caps: reads at four, writes at three, shells at two | **Yes** — the empirical break threshold is recorded with the date and the observed failure | The model example in this stack. Derived, arguable, re-derivable, and it states what broke at the value above it |
| Two consecutive failures then pivot | **Yes** — derived from repeated observed loop histories | Derived; the consequence is named and the count follows from it |
| Context thresholds for compaction, warning and blocking | **Partly** — the mechanism is named, the specific percentages are not derived | Provisional by this Part's test; the mechanism is sound, the values are conventional |
| Output quality score at seventy | **No** | Imposed. Nothing records where seventy came from or what changes at fifty-six or eighty-four |
| Design score at eighty with zero critical findings | **Mixed** — "zero critical" is a well-formed qualitative floor; eighty is unrecorded | The qualitative half is exemplary and portable; the numeric half is decoration by §7's test |
| Three failed fixes then scrap and rebuild | **No** | Imposed count; the consequence is plausible and unstated |

The contrast is instructive and internal to one stack. The parallel caps are a textbook derived
floor: a named failure, an observed threshold, a recorded date, and a statement of what happens at
the value above. The score thresholds are bare numbers. Both live in the same governance document
and are enforced with equal authority, which is exactly how imposed floors borrow credibility from
derived ones. — Floor statements OBSERVED from this stack's governance surfaces; derivation
assessments INFERRED against §4.

The actionable finding: the numeric quality thresholds should be re-derived or relabelled
provisional, and the qualitative floors beside them ("zero critical findings", "declared bound",
"observed evidence") need no such work — which is §6's argument demonstrated inside this stack
rather than asserted about it.

## 12. Failure modes

| Failure | Mechanism |
|---|---|
| **Transplanted number** | A value correct in its origin domain enforced here with its derivation left behind |
| **Unarguable floor** | No recorded consequence, so it can be neither defended, tuned nor retired |
| **Collapsed thresholds** | Possibility, likelihood and irreversibility treated as one, hiding the risk posture inside a number |
| **False precision** | A figure implying a precision never established; nobody can say what changes at plus or minus a fifth |
| **Numeric reflex** | A property statable qualitatively expressed as a threshold, losing portability and checkability |
| **Silent drift** | The consequence changed; the floor did not; nothing in the record shows it |
| **Credibility borrowing** | Imposed floors enforced alongside derived ones with equal authority, inheriting their standing |
| **Permanent provisional** | An externally adopted floor labelled provisional and never derived, calcifying into ceremony |

## 13. Detection signatures

1. **The round number.** Floors at seventy, eighty, three, five. Derived thresholds rarely land on
   round values; round values indicate a choice made for legibility rather than from consequence.
2. **The unanswerable why.** Asking what the floor prevents yields a category rather than an event.
3. **The absent sensitivity.** Nobody can say what changes at the value plus or minus a fifth.
4. **The travelling threshold.** The same number appearing across unrelated domains within one
   organization, which is the signature of a value that propagated rather than being re-derived.
5. **The bare-number record.** A floor recorded as a value with no consequence beside it. Drift
   becomes undetectable, including by its own author later.

## 14. Trap seeds — for Part XXII

- **T-CLAE-TRANSPLANTED-FLOOR** — a threshold enforced with its derivation left in the domain it
  came from, correct there and arbitrary here.
- **T-CLAE-UNARGUABLE-FLOOR** — a floor with no recorded consequence, therefore untunable and
  unretirable, whose only fates are ritual obedience or quiet disregard.
- **T-CLAE-COLLAPSED-THRESHOLDS** — possibility, likelihood and irreversibility treated as one
  threshold, concealing the risk posture inside a number nobody can locate.
- **T-CLAE-FALSE-PRECISION** — a floor stating a precision never established, prompting arguments
  about a digit whose movement changes nothing.
- **T-CLAE-CREDIBILITY-BORROWING** — imposed floors enforced beside derived ones with equal
  authority, inheriting standing they did not earn.

## 15. Rule seeds — for Part XXIII

- **PR-CLAE-DERIVE-FROM-CONSEQUENCE** — a floor records the concrete failure event, who bears the
  consequence, and the reasoning from that consequence to the minimum. A value without this chain is
  labelled imposed or provisional.
- **PR-CLAE-STATE-THE-THRESHOLD-CHOICE** — a floor records whether it sits at possibility,
  likelihood or irreversibility, and why. The placement is a risk posture and is stated as one.
- **PR-CLAE-QUALITATIVE-FIRST** — a floor is stated qualitatively wherever the intent permits.
  Numbers are used only for genuinely continuous properties where a line must be drawn.
- **PR-CLAE-RECORD-SENSITIVITY** — a numeric floor records what changes at plus or minus a fifth of
  its value. Where nothing does, the floor is stated as a range with a chosen operating point.
- **PR-CLAE-BORROW-AS-HYPOTHESIS** — an externally sourced minimum is adopted as a hypothesis and
  derived locally. Where time does not permit, it is labelled provisional with the derivation
  recorded as owed.
- **PR-CLAE-REDERIVE-ON-CONSEQUENCE-CHANGE** — floors are re-derived when their consequence changes,
  not on a calendar. Periodic review catches accumulation; only the recorded consequence catches
  drift.

## 16. Eval seeds — for Part XXIV

- **Derivation-presence probe.** For every floor in force, require the recorded consequence chain.
  Floors without one are relabelled imposed or provisional, which is a labelling change rather than
  a removal, and is cheap.
- **Sensitivity probe.** For every numeric floor, ask what changes at plus or minus a fifth. Silence
  identifies decoration and is the fastest discriminator in this Part.
- **Threshold-placement probe.** For every floor, determine which of the three thresholds it sits
  at. Floors whose authors cannot say have a risk posture nobody chose.
- **Qualitative-restatement probe.** For each numeric floor, attempt a qualitative restatement of
  the same intent. Success indicates the number was a numeric reflex and the restatement is
  strictly more portable.
- **Travelling-threshold probe.** Search for identical values across unrelated domains in the same
  organization. Repetition of a specific figure indicates propagation rather than derivation.

## 17. Production Reality Gate seed — for Part XXV

**Floor Derivation Gate.** A floor may be enforced at full authority only when it records the
concrete failure event, the consequence and its bearer, the threshold placement with its reasoning,
and — if numeric — its sensitivity. Floors lacking these are enforced as provisional and are
reported as such wherever floor compliance is published, so that a passing floor set states how much
of its own authority is derived. Imposed floors from regulatory or formal sources are recorded as
imposed with their source and are exempt from derivation, not from disclosure.

## 18. Pseudoflow — deriving a floor

Begin with the failure, never with the number. State the event concretely enough that its occurrence
would be recognizable; if the statement is a category, it cannot be thresholded and the derivation
stops here.

Establish who bears the consequence, what it costs them, how it is discovered and how long it
persists before discovery. A consequence borne by a downstream consumer and discovered late is a
different derivation from the same event borne by the producer and discovered immediately.

Identify all three thresholds: the value below which the failure cannot occur, the value below which
it is probable in normal operation, and the value below which it is unrecoverable. Where a threshold
cannot be located, record that rather than assuming the others cover it.

Choose the placement and write down why. This is the risk posture and it is the part of the floor
most worth recording, because disagreements about floors are usually disagreements about placement
conducted as arguments about numbers.

Before settling on a value, attempt a qualitative statement of the same intent. If the intent can be
captured as a property rather than a threshold, prefer it — it will travel, it will be checkable
without calibration, and it will remain arguable on its merits.

Where a number is unavoidable, record its sensitivity. If nothing meaningful changes at plus or
minus a fifth, state the floor as a range with a chosen operating point rather than as a figure
implying precision.

Record the whole derivation beside the value, along with the retirement condition Part X requires.
A floor recorded as a bare number cannot be checked for drift by anyone, including whoever wrote it.

When adopting an external minimum, run all of the above against it. Agreement with the external
value is a fine outcome and a different object from adopting it unexamined.

## 19. Integration

Part X supplies the floor properties this Part operationalizes, and receives from it the derivation
that its first property requires. Part XVIII's deviations are the escape route, and a deviation
argued against a floor whose derivation is unrecorded cannot state what loss it incurred — so
derivation is a precondition for the escape working at all. Part XXIII carries the consequence,
threshold placement and sensitivity as required rule fields. Part IX's ledger supplies the recurring
residuals that Part X §7 promotes into floor candidates, and this Part is what turns a candidate into
a defensible minimum.

Outside the family, the parallel tool-call caps are cited as the stack's model derived floor and are
the pattern new floors should follow. The numeric quality thresholds are identified as the
re-derivation work this Part implies, and the qualitative floors beside them are endorsed unchanged.

## 20. Open questions

1. Can the three thresholds be located for failure classes with no observable frequency? §5 assumes
   likelihood is estimable, and for rare high-consequence failures it may be estimable only after
   the failure has occurred, which defeats the purpose. — UNKNOWN.
2. Is the twenty percent sensitivity band itself derived or conventional? It is a heuristic chosen
   for legibility, and by this Part's own §13 signature a round number is a warning sign. It is
   recorded here as provisional, which is the honest application of §8 to this Part's own content. —
   HYPOTHESIS.
3. How is a floor derived for a consequence borne by a party who cannot be consulted? Step two
   requires knowing what the failure costs its bearer, and where the bearer is a future maintainer
   or an unreached consumer, the cost is inferred rather than established. — UNKNOWN.

## 21. Institutional writeback

Five trap seeds, six process-rule seeds, five eval seeds and one production gate.

Two portable results. **Every failure class yields three floors** — possibility, likelihood,
irreversibility — and which one a floor sits at is a decision about risk posture rather than a fact
about the domain. Recording the placement turns arguments about numbers into arguments about
posture, which is what they always were. And **prefer the qualitative form**: a floor that names the
property rather than the value carries its own derivation, travels between domains intact, and is
checkable without calibration. The instinct that numbers are the rigorous form of a minimum is, for
floors specifically, exactly backwards — and this Part's own §11 shows both forms sitting side by
side in one governance document, the qualitative half portable and the numeric half undefended.
