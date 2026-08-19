---
title: "CLAE Part 31 — Failure-Family Synthesis and the Sibling Input Space"
family: clae
part: 31
depends_on: [X, XIII, XV, XXI, XXII, XXIII, XXIV, XXV, 29, 30]
feeds: []
status: SEALED
date: 2026-08-19
authorization: UPAC STOP #1, Owner option D (2026-08-19)
---

# Part 31 — Failure-Family Synthesis and the Sibling Input Space

## 1. Purpose

Part XV converts an incident into a probe. Part X §7 converts a recurring class into a floor. Part
XXI names the lineage a failure belongs to, and Part 30 elevates a cause into a protection. Four
mechanisms, and between two of them there is a gap nobody owns.

A probe pins a **point**: this exact input, on this exact day, failed this exact way, and must not
do so again. A floor governs a **class**: every artifact in this domain must clear this minimum. But
a fault is not a point and it is rarely a whole class. It has an **extent** — a neighbourhood of
inputs that reach the same broken code by the same route — and the observed failure is one arbitrary
sample from it.

> Given one input that failed, what is the set of inputs that fail for the same reason, and how much
> of that set has actually been looked at?

Nothing in this family answers that. Part XV §10 does not merely omit it; it **declines** it, and
correctly for its own scope: it routes a recurring class to a floor rather than to fifty probes,
because converting a class into probes is the accumulation failure arriving by the most sympathetic
route available. That ruling is preserved here in full. This Part occupies the territory the ruling
leaves behind — not fifty probes, and not yet a floor, but the bounded search that determines which
of the two the finding actually needs.

Six mechanisms: the point-extent distinction (§2), four sibling generators (§3), the bounding rule
that stops the search from being infinite (§4), discrimination ranking (§5), the three outcomes a
sibling run can produce (§6), and the extent record that survives the session (§7). One discipline
keeps it from becoming a test farm: ascension (§8).

## 2. Point, extent and class

Three scopes, routinely collapsed into two.

| Scope | Object | Owner | Question it answers |
|---|---|---|---|
| **Point** | the observed failing input | Part XV probe | does *this* historical failure reproduce |
| **Extent** | the neighbourhood reaching the same fault | **this Part** | how far does the break actually go |
| **Class** | every artifact in the domain | Part X floor | what minimum must all of them clear |

Collapsing extent into point produces the most common outcome after a repair: a probe is written for
the observed input, the fix is scoped to make that input pass, and the sibling inputs that reach the
same defect remain broken. The repair is real and the record is honest, and the estate is still
broken in three places nobody enumerated.

Collapsing extent into class produces the opposite waste: a single-site defect is promoted to a
domain minimum, and every artifact in the domain now pays a check for a fault that had exactly one
site. Part X §6 named the accumulation this causes; the promotion was premature because the extent
was never measured, so the only two available options were *one probe* or *everything*.

**The extent is what makes the routing decision correct.** Measured extent of one site licenses a
probe. Measured extent across a domain licenses a floor. Unmeasured extent licenses a guess, and the
guess has a bias: it is cheaper to write one probe than to search, so the unmeasured case
systematically under-repairs.

## 3. The four sibling generators

Siblings are generated, not imagined. Four generators, each with a characteristic reach and a
characteristic blind spot.

| Generator | Produces | Finds | Cannot find |
|---|---|---|---|
| **Equivalence partition** | inputs the code treats identically to the failing one | the fault's width inside one parameter | faults that depend on a second parameter |
| **Boundary displacement** | inputs one step either side of every threshold the failing input crossed | off-by-one and comparison-direction faults | faults with no threshold |
| **Metamorphic relation** | a *transformed* input whose correct output is derivable from the original's | faults with no known-good expected value | relations nobody can state for this domain |
| **Precondition inversion** | inputs violating each precondition the failing path assumed | unguarded assumptions and silent fallbacks | assumptions never written down |

The fourth is the highest-yield and the least used, because it requires the assumptions to be
enumerated before they can be inverted — which is the same work that would have prevented the
failure. That is not a reason to skip it; it is the reason the enumeration is worth doing *at repair
time*, when exactly one assumption is known to be false and the rest are under suspicion for the
first and only time.

The third deserves its own note. A metamorphic relation asks what must remain true between two runs
rather than what one run must return, and it is the generator that still works when nobody knows the
correct answer. Where an oracle is absent — the condition Part XVI treats as the human boundary — a
metamorphic sibling is often the only executable sibling available.

## 4. Bounding: the search is finite by rule, not by exhaustion

The sibling space is unbounded in principle. Every generator can be applied to its own output, and
the composition of four generators over any interesting input is effectively infinite. A discipline
that does not bound this produces the test farm this family exists to attack.

Three bounds, applied in order.

**Depth one.** Generators apply to the *observed* failing input, never to a generated sibling. A
sibling of a sibling is two hypotheses deep and its relationship to the original fault is no longer
legible. Second-order search is available only when a first-order sibling actually failed, and then
the failing sibling becomes a new observed input with its own depth-one budget.

**A declared budget, set before the search.** The number of siblings to be executed is fixed in
advance from the incident's cost, using the same four criteria Part XV §4 applies to probe
conversion. A search whose budget is set after the results are seen is not a search; it is a
justification.

**The stop rule with a name.** Stop when either the budget is exhausted, or a stated number of
consecutive siblings pass. Two consecutive passing siblings do not prove the extent is one site;
they say the search found nothing more within its budget, and that distinction is recorded rather
than rounded off. Per Part XIII §7, this is a three-valued outcome: the extent is *confirmed
narrow*, *confirmed wide*, or **unsearched-beyond-budget** — never "narrow because we stopped".

## 5. Discrimination ranking

Siblings are executed in the order of how much they would change the belief about the extent, not in
generation order. Generation order is an artifact of which generator ran first, which is an artifact
of the author, and executing in that order spends the budget on whichever generator happened to be
listed at the top of §3.

A sibling's discrimination is high when the two possible outcomes lead to *different repairs*. A
sibling whose pass and whose failure both lead to the same fix is worth nothing regardless of how
interesting it looks: it cannot separate any two hypotheses about the fault, so its result is
already determined for every purpose the search has.

The operational test is stated as a question answered before execution: **if this sibling fails, what
do I do differently from what I would do if it passes?** No difference means it does not enter the
ranked list. This is the same test the estate applies to a discriminating experiment for environment
attribution — one variable changed, and the outcome distinguishes two named possibilities — applied
to the input space rather than the environment axis.

## 6. Three outcomes and what each licenses

| Outcome | Meaning | Licenses |
|---|---|---|
| **Sibling fails** | the extent is wider than the observed point | widen the repair, then re-derive siblings from the new failing input |
| **Sibling passes** | the extent does not reach this input by this route | narrowing, but only within the executed set |
| **Sibling cannot run** | preconditions absent | nothing at all — recorded as unsearched, never as a pass |

The third row is the one that decays silently. A sibling whose environment has drifted reports
green in a two-valued harness, and an extent that was never searched then reads as an extent that
was searched and found narrow. Part XIII §7's three-valued requirement is not a nicety here; it is
the difference between a measured extent and a fabricated one.

A failing sibling is the valuable outcome and the one that costs the most, because it re-opens the
repair that was believed finished. That cost is the reason the search must happen **before** the
repair is declared complete, at the one moment when re-opening is free.

## 7. The extent record

The artifact that survives the session carries eight fields:

- **The observed failure** — its identity and date, per Part III §5.
- **The fault hypothesis** — the mechanism believed to cause it, stated so that it can be wrong.
- **Generators applied**, and which were declined with the reason. A declined generator is a
  recorded decision; a silently unapplied one is indistinguishable from a forgotten one.
- **Siblings executed**, each with its discrimination rationale and its three-valued outcome.
- **The budget** as declared before the search, and what remained.
- **The measured width** — a point, a bounded region with its bounds named, or an unbounded region —
  with the stop rule that terminated the search.
- **The spread**, read from Part 30 §5's disposition rather than searched here, or `not searched`.
- **The routing** the pair licenses: probe, repair scoped to the width, or promotion to a floor.

The record is what makes the next occurrence cheap. When a sibling of this fault surfaces in six
months, the extent record says whether it was inside the searched region — a regression — or outside
it, which means the original search was correctly bounded and the extent has genuinely grown. Those
two situations demand different responses and are indistinguishable without the record.

## 8. Ascension — when a family becomes a floor

The hand-off to Part X §7 is a rule, not a judgement.

> **When the measured width is more than a point, and Part 30 §5's campaign reports the fault found
> across more than one artifact and more than one author, the finding stops being a defect and
> becomes a domain minimum.**

The rule spans both axes deliberately, and each contributes a condition the other cannot supply.
Width alone is a scope statement about one site: half an input space broken in one function is a
large repair, not a domain minimum. Spread alone can be one author's habit, which is a repair
campaign, or one shared artifact, which is a defect in that artifact. Only the conjunction
establishes that a wide fault is reachable by independent people working normally, which is the
precise condition a domain minimum exists to address.

The spread half is **read from Part 30 §5's disposition, never re-derived here.** Where that
campaign reports *not searched*, the ascension is undecidable and is recorded as such — not resolved
downward, which is the direction that quietly declines every promotion.

Below the line, the finding takes a repair scoped to the measured width plus one probe at the
original point. Above it, Part X §7 owns it, this Part hands over the extent record as the
promotion's width evidence, and no probe is written per site — which is the accumulation Part XV §10
forbids and this ascension rule is designed to route around rather than trip over.

## 9. Boundary

This Part does not own probe conversion (Part XV), floors or their retirement (Part X), lineage
classification (Part XXI), cause elevation and immunity (Part 30), or finding disposition within a
session (Part 29). It owns exactly one interval: from a single observed failure to a measured extent,
and the routing decision that extent licenses.

### 9.1 The two axes, and why Part 30 §5 is not this

Part 30 §5 already runs a sibling search, and confusing the two would produce exactly the duplication
this family forbids. They search orthogonal spaces.

| | Part 30 §5 — the sibling defect campaign | Part 31 — the sibling input space |
|---|---|---|
| Searches | **artifacts** — where else does this defect exist | **inputs** — which inputs reach this defect |
| Keyed by | failure family | the observed failing input |
| Produces | per-family disposition: clean · found · not searched | the extent, with a three-valued stop rule |
| Answers | **spread** — how many places hold it | **width** — how much of the input space it breaks |

A defect can be narrow and everywhere: one input triggers it, in forty artifacts. It can be wide and
nowhere else: half the input space is broken, in exactly one function. The two measurements are
independent, and neither substitutes for the other.

The composition rule follows from that independence: **width licenses the scope of the repair;
spread licenses the promotion.** Part 30 §5's campaign is what establishes that the fault reaches
more than one artifact and more than one author, so the ascension rule in §8 consumes its
disposition rather than re-deriving it. This Part never searches the artifact space, and a sibling
search that starts enumerating other files has crossed into Part 30 §5 and should be run there,
under its family keys, with its disposition contract.

It does not own environment attribution. The estate's environment-qualification discipline decides
whether the product is the suspect at all — toolchain, dependency, host, fixture, pipeline, hardware
— and this Part begins only after that attribution has named the product. A sibling search run
against a failure whose axis is environmental will produce siblings that fail for the environmental
reason and a fabricated extent, which is the most expensive way to use this mechanism.

It does not own test generation as a capability. `modules/auto-testing` holds the per-language
generators and reads recorded failure history. This Part supplies what that machinery has never had:
which siblings are worth generating, in what order, and when to stop.

## 10. Evidence — sibling searches in this stack

Three recorded instances, each producing a different extent and therefore a different routing.

**Extent wider than the point, found by precondition inversion.** A dependency-sovereignty module
recommended absorbing an image library outright. The observed failure was one wrong recommendation.
Inverting the assumption behind it — that an import count measures usage — generated siblings for
every declaration with zero call sites, and two more wrong recommendations appeared immediately. The
extent was not "this library"; it was "every declaration whose consumers live outside the scanned
root". The repair moved accordingly: zero call sites now yields an explicit unknown rather than a
low usage reading, and the rung that depended on unavailable information was withdrawn entirely.

**Width equal to a whole region, found by equivalence partition.** A graph builder read a
module-level constant instead of its passed base, so a file under an alternate root raised, was
swallowed by a skip, and an empty graph was reported as a real one. The observed failure was one
synthetic root. The partition — every input whose root differs from the default — showed the failure
was not a property of that root but of *all* of them: the width was the entire non-default region,
and the sole reason the estate had not noticed was that its own invocation always passes the default.
A probe on the observed root would have been the narrowest possible reading of a fault whose width
was everything except one point.

The routing followed from the width: the repair moved the base through the resolver rather than
patching the observed call, and the swallowing branch was **removed** rather than widened, because a
skip that can hide a construction defect is not a tolerance. Whether the same defect existed in other
artifacts is a Part 30 §5 question and was answered there, not here.

**Extent as a range, found by boundary displacement.** A duplication gate stayed silent on a
proposal it should have caught. The observed failure was one prompt. Displacing the thresholds the
prompt crossed showed the gate considered inputs only up to a length cap, and the fault's extent was
therefore *every* input above that cap — an unbounded region, not a point. A probe on the one prompt
would have passed forever while the region stayed open.

The three routings differ, and in each case the extent — not the incident's severity — is what
selected it.

## 11. Failure modes

| # | Failure | Why it survives |
|---|---|---|
| 1 | **Point repair** — fix scoped to the observed input | the probe passes and the record shows a closed incident |
| 2 | **Premature floor** — one site promoted to a domain minimum | promotion looks like diligence; the cost is paid by everyone later |
| 3 | **Unbounded search** | each sibling is individually justifiable; the budget is never declared |
| 4 | **Generation-order execution** | the budget is spent on the first generator listed |
| 5 | **Two-valued siblings** | an unrunnable sibling reports green and a fabricated extent reads as measured |
| 6 | **Post-hoc budget** | the search stops when it finds nothing and the budget is written to match |
| 7 | **Sibling search on a misattributed failure** | siblings fail for the environmental reason and the extent looks enormous |
| 8 | **Depth creep** | siblings of siblings; the relationship to the original fault becomes unstatable |
| 9 | **Extent record discarded** | the next occurrence cannot be classified as regression or growth |

## 12. Detection signatures

- A repair whose diff touches exactly the lines named in the incident.
- A probe suite with several probes whose reproduction sections differ only in one literal.
- A floor whose promotion evidence names one artifact.
- A sibling set with no declined generators recorded — four applied every time is a ritual, not a
  search.
- A sibling harness with two-valued output.
- An extent record whose stop rule reads *budget exhausted* with a budget written after the results.
- A repair declared complete before any sibling ran.

## 13. Trap seeds — for Part XXII

- **The passing sibling that never ran.** Two-valued output makes an absent precondition
  indistinguishable from a pass, and the extent it fabricates is *narrow*, which is the direction
  that closes the incident.
- **The sympathetic promotion.** Promoting a single-site defect to a domain minimum feels like the
  responsible choice, and it is the accumulation failure with a good motive.
- **The interesting sibling.** A sibling chosen because it is intellectually attractive rather than
  discriminating spends budget without moving belief.
- **Siblings against an unattributed failure.** The extent measured is the environment's, and it is
  large, and it will be attributed to the product.

## 14. Rule seeds — for Part XXIII

- **A repair is not complete until the extent is measured or the search is recorded as unperformed.**
  Unperformed is an acceptable state; unstated is not.
- **The sibling budget is declared before the first sibling runs.**
- **Generators apply to the observed input only.** Depth two requires a failing depth-one sibling.
- **Every sibling is three-valued.** An unrunnable sibling is never a pass.
- **Promotion to a floor requires an extent crossing more than one artifact and more than one
  author.**
- **A sibling that leads to the same repair under either outcome does not enter the ranked list.**

## 15. Eval seeds — for Part XXIV

- Take repairs closed in the last quarter and run a depth-one sibling search against each. The
  proportion that surfaces an unrepaired sibling is the estate's point-repair rate, and it is the
  number that decides whether this Part earns its cost.
- Compare extents measured at repair time against sites of the same fault discovered later. Extent
  under-measurement is the difference, and it should shrink as the generators are used.
- Track the ratio of promotions to floors that were later retired as unnecessary. A rising ratio
  indicates the ascension rule's two conditions are being satisfied on paper rather than in fact.
- Run the sibling harness with its preconditions deliberately removed and confirm it reports
  unrunnable rather than green.

## 16. Production Reality Gate seed — for Part XXV

A repair may not be recorded as complete while its extent field is empty. The field accepts three
values — a measured extent, an explicit unsearched with a reason, or a hand-off identifier to Part X
§7 — and rejects blank. The gate does not require a search; it requires the estate to know whether
one happened, which is the distinction that separates a bounded repair from an unbounded belief.

## 17. Pseudoflow — from one failure to a routed repair

Attribute the failure to the product before anything else; if the axis is environmental, stop and
hand off. State the fault hypothesis in a form that can be wrong. Declare the sibling budget from the
incident's cost. Apply the four generators to the observed input at depth one, recording any
generator declined and why. Rank the generated siblings by whether their two outcomes lead to
different repairs, discarding those that do not. Execute in ranked order against three-valued
output, stopping at budget exhaustion or the stated run of consecutive passes. Record the extent with
the stop rule that terminated the search. Route: one site to a wider repair plus the Part XV probe at
the original point; multiple artifacts and multiple authors to Part X §7 with the extent record as
promotion evidence. Write the extent record before the incident is closed, because after closure the
cost of re-opening is what stops it being written at all.

## 18. Integration

Upstream: the environment attribution that names the product; Part XXI's lineage, which suggests
which generator is most likely to be productive for this failure family; Part 29's finding
disposition, which decides that this finding is being repaired at all. Downstream: Part XV's probe at
the original point; Part X §7's floor when the extent ascends; Part 30's cause elevation, which
consumes the extent as the width evidence its sibling campaign needs; `modules/auto-testing`, which
generates the sibling inputs this Part has decided are worth generating; CEPS, which records the
extent alongside the incident so recurrence can be classified as regression or growth.

## 19. Open questions

- **The stop rule's consecutive-pass count is unset.** Two is stated here as an illustration and has
  no measurement behind it. The number that matters is the one at which additional siblings stop
  finding sites, and it is almost certainly different per generator and per lineage. Until it is
  measured, this rule carries a hidden author, which is the property this family objects to
  elsewhere.
- **Metamorphic relations resist enumeration.** The generator with the best reach where no oracle
  exists is the one whose output depends most on the author's domain knowledge, and nothing here
  makes that dependence smaller.
- **Discrimination is judged, not computed.** The test — do the two outcomes lead to different
  repairs — is mechanical to *ask* and not mechanical to *answer*. Whether it survives contact with
  an author who wants a particular sibling to run is unmeasured.
- **The ascension rule's author condition assumes attributable authorship.** Where an artifact has
  one author by construction, the condition can never be met and every extent stays below the line.

## 20. Institutional writeback

Four trap seeds, six rule seeds, four eval seeds, one production gate.

Three portable results. **A repair scoped to the observed input is a repair scoped to a sample** —
the input that failed is one draw from the fault's extent, and treating it as the whole is the
default behaviour of every incident process that ends at a green probe. **An unmeasured extent
biases toward under-repair**, because writing one probe is cheaper than searching, so the missing
measurement is not neutral; it fails in a consistent direction, which is what makes it a structural
defect rather than an occasional lapse. And **the routing decision between a probe and a floor is
not a matter of severity** — it is a matter of measured extent, and the two available options in the
absence of that measurement are exactly the two failures this family already names: the point repair
and the premature promotion.

The structural finding is the stop rule's third value. An extent that was searched to the edge of a
budget and an extent that was searched exhaustively are different claims, and a two-valued harness
renders them identically. **Unsearched-beyond-budget is the honest state, and it must be
representable**, because a mechanism that can only report *narrow* or *wide* will report *narrow*
every time the budget runs out — which is most times, and always in the direction that closes the
incident.
