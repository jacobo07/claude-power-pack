# DRK-08 — Architecture Synthesis & the Unproposed Alternative

> The dataset that governs the **input** to the review rather than the review itself. DRK-00–07
> assume a `DecisionObject` already exists: someone proposed an architecture, and the kernel decides
> whether it is reversible enough, evidenced enough, proportional enough. That discipline improves
> the odds that the proposed thing is sound. It does nothing about the odds that the proposed thing
> was the right thing to propose. **A review is closed over its input — no amount of rigour applied
> to one option detects the absence of a better one that was never authored.** DRK-08 supplies the
> option set, its derivation from observed forces, and the two artifacts a candidate architecture
> must carry before the kernel is allowed to score it. **Parent it EXTENDs:** `modules/arch-decision`
> (`arch_check` ranks prior art and returns a verdict over precedent — it consumes options, it does
> not generate them). **Cross-references (never re-narrated):** DRK-01 (the sieve that scores each
> option), DRK-02 (blast radius per option), DRK-04 (counterfactual horizons per option), DRK-05
> (precedent registry), `architecture_horizon` (the executable that measures what invalidates first).
>
> **Origin:** UPAC ownership audit 2026-08-18, system 02 (UASE), verdict
> `EXISTS_PARTIALLY → EXTEND_EXISTING_OWNER`. Owner selected option D at STOP #1.

---

## PART I — THE BLIND SPOT

### VIII.1 Review is closed over its input

Every mechanism in this family operates on a decision that already exists. The sieve stages of
DRK-01 refine a verdict about *this* proposal. DRK-02 prices *this* proposal's blast radius. DRK-03
sets the evidence burden *this* proposal must clear. DRK-05 checks whether *this* proposal collides
with precedent. Each is sound, and collectively they share one structural property: **the option set
is an input, and an input is never the thing a function validates.**

The consequence is a verdict asymmetry that is easy to miss because the words look symmetric.
`APPROVE` means *this passed the review*. It has never meant *this is the best available*, and the
kernel has no vocabulary in which the second claim could even be expressed, because the alternatives
were never objects. A stack that reviews well and synthesizes badly produces a long record of
well-reviewed mediocre architectures, each individually defensible, and the record itself reads as
evidence of rigour.

### VIII.2 The three options that are always present and rarely authored

Three alternatives exist for every architectural decision whether or not anyone writes them down.

| Option | Always available because | Cost of leaving it unauthored |
|---|---|---|
| **The null option** — do nothing, or keep the current shape | the current architecture is running | the proposal is never compared against the incumbent, so *any* improvement looks like *the* improvement |
| **The incremental option** — extend an existing owner | most territory in a mature estate is owned | the estate grows a sibling for a responsibility it already had |
| **The structural option** — change a boundary rather than add inside one | boundaries are always movable at some cost | the estate accretes complexity inside a boundary that should have moved |

The null option is the one most reliably lost. It has no author and no advocate; nobody is assigned
to argue for the shape that already exists, so it enters the comparison only if the synthesis
discipline puts it there deliberately.

### VIII.3 Recorded instance in this estate

This dataset was authored out of an audit that is itself the cleanest available example. A proposal
arrived specifying twenty-five sibling systems, a Constitution and a Master Compendium — **one
option, fully elaborated, with no alternative and no null case**. The review machinery available at
the time could score that option's evidence and precedent, and it did: twenty-two of the twenty-five
systems resolved to existing owners. But the alternatives that eventually decided the matter — wire
the one unwired harness, build the three genuine residues, extend the six partial owners — did not
exist until the audit authored them. They were not rejected by the proposal; they were **absent from
it**, and absence is exactly what a review cannot see.

The record is `vault/audits/upac/SYSTEM_OWNERSHIP_OVERLAP_MAP.md`, and the four-option set it
produced is the artifact this dataset generalizes.

---

## PART II — FORCES BEFORE BOUNDARIES

### VIII.4 A force is an observed constraint with a change rate

Synthesis begins before any boundary is drawn, with the forces the architecture must absorb. A force
is admissible only when it carries three fields: the **constraint**, the **source** that observed it,
and the **change rate** — how often this constraint has actually moved, measured rather than
estimated.

The third field is the one that does the work, and the one usually omitted. An architecture is a bet
about which constraints will hold. Recording a constraint without its volatility produces a design
that treats a requirement that changed four times last quarter and a requirement that has never
moved as the same kind of thing.

| Class | Change rate | Design consequence |
|---|---|---|
| **Invariant** | has never moved and has a structural reason not to | may be compiled into the shape — assumed, not abstracted |
| **Slow** | moves on the order of the system's own major versions | belongs at a boundary; abstraction is affordable |
| **Fast** | moves within a release cycle | must be data or configuration, never structure |
| **Unmeasured** | no observation history exists | treated as **fast** until measured — the asymmetry is deliberate |

The unmeasured row is a rule, not a default. Treating an unmeasured force as invariant is how a
constant gets compiled into a boundary; treating it as fast costs an indirection that can be removed
once observation exists. The cheap error is the recoverable one.

### VIII.5 The change-rate discontinuity rule

> **A boundary that does not separate two different change rates is decoration.**

This is the single most productive test in synthesis. Boundaries exist to stop change from
propagating. Where the two sides of a proposed boundary move at the same rate and for the same
reasons, the boundary absorbs no change; it only adds a hop, a translation, and a place for the two
sides to drift apart while pretending to be independent.

The test is mechanical: for each proposed boundary, name the force that changes on one side and not
the other. A boundary for which that force cannot be named is provisional at best and, more often,
is an organizational artifact — a boundary drawn where two authors met rather than where two rates
diverge.

### VIII.6 The measured instance

`architecture_horizon`, built as residue R2 of the same audit, measured eighty-three units of this
estate and found an **eleven-unit mutually-dependent core** in which every member transitively
reaches every other. Twelve units tie at twenty-seven to twenty-nine transitive dependents, and the
tie is not a coincidence of the metric — it is the signature of a group inside which nothing
invalidates first.

That is the change-rate discontinuity rule failing in production. Eleven boundaries exist between
those units, and none of them separates two different rates, because a cycle guarantees that a change
anywhere reaches everywhere. Each of the eleven was individually reasonable; none was ever compared
against the null option of *not* drawing it, and no review stage in DRK-00–07 asks that question.

---

## PART III — STATE OWNERSHIP IS THE PRIMARY OUTPUT

### VIII.7 The ownership table contract

The deliverable of synthesis is not a diagram. A diagram shows components and arrows, both of which
survive any amount of vagueness about who is allowed to write what. The deliverable is the **state
ownership table**, and an option that does not carry one has not been designed.

Every state item in the option carries six fields:

| Field | Admissibility rule |
|---|---|
| **Item** | the state, named at the granularity at which it can be independently wrong |
| **Owner** | exactly one component; the field does not accept a list |
| **Writers** | must equal the owner, or the item is reclassified as shared-mutable and flagged |
| **Readers** | enumerated; an unbounded reader set is a coupling the option must price |
| **Derivation** | for derived state, the inputs and the function; `none` marks it primary |
| **Invalidation** | what event makes the current value wrong, and who observes that event |

Two rules govern the table. **Exactly one owner** — a second writer is not a design detail to be
resolved later, it is the defect that produces the class of failure where two components are each
correct in isolation and jointly wrong. And **derived state names its derivation** — a derived value
whose derivation is unrecorded is indistinguishable from primary state, and will eventually be
written to directly by someone who could not tell the difference.

### VIII.8 Why this is the primary output rather than a supporting one

The ownership table is the artifact that makes the rest falsifiable. Blast radius (DRK-02) is
computable from readers. Reversibility is computable from whether an owner change requires a data
migration. The invalidation column is what `architecture_horizon` needs to answer what invalidates
first. A proposal that supplies boundaries without ownership hands the kernel a picture, and the
kernel then scores its own guesses about what the picture meant.

---

## PART IV — BOUNDARY DERIVATION

### VIII.9 Four generators, and the corroboration rule

Candidate boundaries are not invented; they are generated from the force table by four independent
generators, each of which proposes a seam.

| Generator | Proposes a boundary where | Fails alone because |
|---|---|---|
| **Change-rate seam** | two adjacent responsibilities move at different rates | rate can be measured over too short a window |
| **Failure-isolation seam** | a failure on one side must not reach the other | over-applies — every function boundary isolates something |
| **Ownership seam** | one component must be the sole writer of a state cluster | follows current code rather than intended design |
| **Cadence seam** | two parts must be deployable, testable or reviewable independently | reflects team structure, which is not an architectural force |

> **Corroboration rule: a boundary proposed by two or more generators is strong; a boundary proposed
> by exactly one is provisional and is recorded as such.**

The rule exists because each generator has a characteristic false positive, listed above, and the
false positives are uncorrelated. A seam that the change-rate generator and the ownership generator
both propose is unlikely to be an artifact of either one's blind spot. A seam only the cadence
generator proposes is very likely to be an organizational boundary wearing an architectural costume —
the most common way team structure is mistaken for design.

### VIII.10 Provisional boundaries are carried, not resolved

A provisional boundary is not an error to be fixed before the option ships. It is a bet whose basis
is recorded, so that when the boundary later proves wrong the record says which single generator
proposed it and what force it assumed. This converts a boundary reversal from an embarrassment into
a measurement, which is the property DRK-05's precedent registry needs and cannot manufacture after
the fact.

---

## PART V — THE OPTION SET CONTRACT

### VIII.11 What synthesis must emit

An option set is admissible to the kernel when it satisfies four conditions.

1. **Minimum three options**, and the null option is always one of them. Two options is a
   comparison; three is the smallest set in which a dominated option can be detected.
2. **Each option carries** its boundary set (with corroboration counts), its state ownership table,
   what it makes cheap, what it makes expensive, and — the field that is usually missing — **the
   force it bets on being stable**.
3. **Each surviving option wins on at least one named axis.** An option that wins on nothing is not
   an alternative; it is scenery.
4. **Dominated options are withdrawn, not scored.** An option worse on every axis than another is
   removed from the set with the domination recorded. Scoring it produces the appearance of a
   comparison that did not occur.

### VIII.12 The straw-alternative failure

The characteristic failure of option-set synthesis is not the absence of alternatives — it is the
presence of alternatives that exist to lose. Three options are authored; two of them are versions of
the third at different scales; the third is adopted, and the record shows a deliberation.

Three detection signatures, all mechanical:

- **Scale-only variation** — the options differ only in a magnitude (how many, how large, how long),
  and share every boundary and every ownership assignment. This is one option with a parameter.
- **No axis winner** — some option wins on no named axis. Condition 3 above rejects it directly.
- **Uniform authorship posture** — every option's "what it makes expensive" field is empty or
  identical. A genuine alternative is expensive somewhere specific; an option with no named cost has
  not been thought through far enough to lose honestly.

The corrective is condition 3 stated as a test with a human referent: **each surviving option must
be somebody's genuine first choice under some stated weighting.** If no weighting exists under which
an option wins, it is not in the set.

---

## PART VI — BOUNDARY WITH `arch-decision` AND THE REST OF THE FAMILY

### VIII.13 The ordering contract

DRK's coverage cross-reference lists precedent-collision detection as `Reference (DO_NOT_BUILD)`,
owned by `modules/arch-decision`. That entry is untouched and this dataset builds no part of it.

The two are sequential, not overlapping:

| Stage | Owner | Operates on | Emits |
|---|---|---|---|
| 1 · Force capture | DRK-08 | observations | the force table with change rates |
| 2 · Option synthesis | DRK-08 | the force table | ≥3 options, each with boundaries + ownership |
| 3 · Precedent check | `arch_check` | **each** option, separately | a verdict over prior art, per option |
| 4 · Review | DRK-01–04 | the surviving options | reversibility, blast radius, burden, horizons |
| 5 · Decision | DRK-01 | the scored set | the `DecisionObject` and its record |

Stage 3 is where the extension is most concretely visible. `arch_check` today is invoked once, on
the thing someone proposed. Under this contract it is invoked once **per option**, and its verdict
becomes a per-option field rather than a gate on the only candidate. Nothing inside `arch_check`
changes; what changes is how many times it runs and on what.

A recorded hazard applies at this seam and is inherited rather than rediscovered: `arch_check`'s
score rises with input length, sealed as `T-DRK-PRECEDENT-LENGTH-BIAS-001`. An option set whose
options differ in elaboration length would therefore receive precedent verdicts that track prose
volume. **Options must be submitted to stage 3 at equal granularity** — statement-only, per the
existing fix — or the comparison measures authorship effort.

### VIII.14 What this dataset does not own

It does not own the scoring of an option (DRK-01), the pricing of its blast radius (DRK-02), the
evidence burden it must clear (DRK-03), the temporal horizons of its consequences (DRK-04), or the
verdict over its precedent (`arch-decision`). It owns the set that arrives at those, and the two
artifacts each member of the set must carry.

---

## PART VII — FAILURE MODES AND DETECTION

### VIII.15 Failure modes

| # | Failure | Why it survives review |
|---|---|---|
| 1 | **Single-option deliberation** | the review is rigorous and passes; rigour on one option is indistinguishable from rigour on the right one |
| 2 | **Null option unauthored** | nobody is assigned to defend the incumbent, so the incumbent never enters the comparison |
| 3 | **Straw set** | three options are recorded; the record reads as deliberation |
| 4 | **Boundary without a force** | the boundary is reasonable and locally defensible; only the cycle it eventually forms is visible |
| 5 | **Ownership deferred to implementation** | the diagram passes review; the second writer appears months later as a data bug |
| 6 | **Unmeasured force treated as invariant** | the constraint has not moved *yet*, which reads as evidence that it will not |
| 7 | **Options at unequal elaboration** | the longest option wins the precedent stage on length, per the sealed length bias |
| 8 | **Corroboration count discarded** | provisional and strong boundaries look identical once the design is drawn |

### VIII.16 Detection signatures

- A decision record whose option field has exactly one entry.
- An option set with no null option.
- Two or more options sharing an identical boundary set and ownership table.
- A boundary whose force column is empty, or whose named force has no change-rate observation.
- A state item with two or more writers, or a derived item with an empty derivation.
- A group of units in which every member transitively reaches every other — the cycle signature that
  `architecture_horizon` reports directly.
- An option whose "makes expensive" field is empty.

---

## PART VIII — SEEDS, INTEGRATION AND OPEN QUESTIONS

### VIII.17 Rule seeds

- **A boundary that does not separate two different change rates is decoration.** Name the force or
  withdraw the boundary.
- **An option set with fewer than three members, or without the null option, is not a set.**
- **Every surviving option wins on at least one named axis**, under a stated weighting.
- **Exactly one writer per state item.** A second writer reclassifies the item and the option prices
  the reclassification.
- **An unmeasured force is fast until measured** — never invariant.
- **Options enter the precedent stage at equal granularity**, per the sealed length bias.

### VIII.18 Eval seeds

- Replay a recorded architectural decision from this estate; count the options its record carried.
  The expected finding, given the base rate, is one.
- For each boundary in a shipped design, attempt to name its force and change rate. The proportion
  that cannot be named is the decoration ratio.
- Compare an option set's boundary corroboration counts against which boundaries later moved. If
  provisional boundaries do not move more often than corroborated ones, the corroboration rule is
  not earning its cost and should be withdrawn.
- Submit two options of deliberately unequal length to the precedent stage and confirm the verdicts
  do not track length — the standing regression for `T-DRK-PRECEDENT-LENGTH-BIAS-001`.

### VIII.19 Integration

Upstream: observations from `graphify` coordinates, `drift_registry`, CEPS incidents and the force
history they contain. Downstream: `arch_check` per option; DRK-01's sieve on the survivors;
DRK-02's blast radius computed from the readers column; `architecture_horizon` consuming the
invalidation column to answer what invalidates first; DRK-05 recording which provisional boundaries
later moved, which is the only way the corroboration rule becomes falsifiable.

### VIII.20 Open questions

- **Change rate needs a window, and the window is not derived.** Measuring volatility over one
  quarter and over three years can classify the same force differently. Nothing here fixes the
  window, and a rule whose parameter is unstated is a rule with a hidden author.
- **Corroboration is asserted, not yet measured.** The claim that two-generator boundaries survive
  longer than one-generator boundaries is the eval seed above, and until it runs, the rule rests on
  the argument that the generators' false positives are uncorrelated — which is itself unmeasured.
- **The null option has no natural advocate.** Requiring it produces a written null option; it does
  not produce a *well-argued* one, and a perfunctory null option satisfies the letter of the contract
  while restoring the defect.

### VIII.21 The fundamental property

> **The review is closed over its input; therefore the input must be governed separately.** No
> proposal is scored until at least three options exist, one of them the incumbent, each carrying its
> boundaries with the force each boundary separates and its state ownership table with exactly one
> writer per item, and each winning on some named axis under some stated weighting. Options are
> withdrawn by domination rather than defeated by score, and are submitted to the precedent stage at
> equal granularity so that the comparison measures architecture rather than prose. An approved
> decision then means what it has never meant before: not merely that this one passed, but that it
> was compared.
