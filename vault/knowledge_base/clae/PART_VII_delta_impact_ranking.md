---
title: "CLAE Part VII — Delta Impact Ranking"
family: clae
part: VII
depends_on: [VI]
feeds: [VIII, IX, XVII, XXI]
status: SEALED
date: 2026-07-26
---

# Part VII — Delta Impact Ranking

## 1. Purpose

Part VI produced a set of deltas. This Part orders them.

Ordering is not a presentation concern. Correction capacity is always smaller than the delta set,
so the ordering **decides what gets fixed** — and therefore decides whether measured distance ever
becomes closed distance. A stack can acquire a legitimate reference, extract deltas at L4, maintain
a perfect ledger, and close nothing that matters, purely through its ordering.

The default ordering is the one extraction produced, and it is always wrong. This Part explains
why it is wrong in a way that is hard to notice, gives a construction that computes most of the
ordering mechanically while forcing the remainder into an auditable record, and names the ranking
biases that survive good intentions.

## 2. Why discovery order dominates

An instrument emits deltas in the order it walked the objects. That order tracks the structure of
the traversal — file layout, module order, the sequence of checks — and has no relationship to
consequence.

The reason it persists is not carelessness. It is that **a list is read as a ranking**. Any
enumeration presented top to bottom is consumed as though its position encoded priority, and this
happens whether or not the producer intended it. Suppressing that reading requires an explicit
counter-signal; absent one, discovery order silently becomes the work queue.

Four further biases push in the same direction, each individually reasonable.

- **Salience.** The best-described delta rises. Extraction quality varies across dimensions, and
  the dimensions that are easiest to describe in detail are rarely the most consequential.
- **Fixability.** The cheapest delta rises, because it can be closed now. §7 shows why this is the
  most damaging bias of the five.
- **Recency.** The most recently discovered delta rises, because it is in view.
- **Magnitude.** The largest number rises, which feels rigorous and ignores everything §3
  establishes.

## 3. What impact is

> **Impact is a property of the consequence of leaving the gap open. It is not a property of the
> gap's size.**

A large delta along a dimension nothing depends on has near-zero impact. A small delta along a
load-bearing dimension can dominate the entire set. Magnitude is one input among several, and
treating it as the whole is the most common ranking error among teams that have already escaped
discovery order.

Impact must also be distinguished from **severity**, which they are routinely confused with.
Severity describes how bad the manifestation is when it occurs. Impact describes the consequence of
not closing it, which combines severity with how often it is reached, whether it compounds, and
what closing it later will cost. A high-severity gap on an unreached surface may rank below a
moderate-severity gap on a universal one. Systems that classify findings by severity and then treat
that classification as a work queue have substituted one for the other.

## 4. The four factors

| Factor | Question | Source |
|---|---|---|
| **Magnitude** | How large is the gap along its dimension? | Part VI, requires L3 |
| **Exposure** | How much of the consuming surface encounters this dimension? | Usage observation, not assumption |
| **Propagation** | Does this gap make other gaps worse, or block their closure? | The residual set's own structure |
| **Irreversibility** | How much more expensive is closing it later than now? | Domain judgment, recorded |

**Exposure** must be observed rather than assumed. Assumed exposure reproduces the author's mental
model of how the artifact is used, and that model is authored inside the loop — Part I's structure
appearing at the ranking layer.

**Propagation** is the factor most often omitted and the one that most changes orderings. A gap
that blocks the closure of three others outranks a larger standalone gap, and this is invisible
unless the residual set is examined as a structure rather than as a list.

**Irreversibility** dominates in architectural dimensions, where a small gap left open becomes
progressively more expensive as work accumulates on top of it. It is the factor that justifies
ranking a currently-harmless delta first, and the only one that can.

## 5. Ranking without collapsing dimensions

Part II §P6 forbids silently summing dimensioned residuals into a scalar, since the weights encode
an undeclared preference. But ranking requires an ordering, and four factors do not order
themselves.

The construction that satisfies both:

1. **Compute the dominance partial order mechanically.** Delta A dominates delta B when A is at
   least as high as B on every factor and strictly higher on at least one. Dominated deltas rank
   below their dominators, with no judgment and no weights.
2. **Identify the frontier** — the deltas dominated by nothing. In practice this is a small
   fraction of the set.
3. **Order the frontier by explicit, recorded judgment.** Only here is a preference required, and
   here it is stated rather than buried in a weight.

The whole value is in the ratio: most of the ordering is derived without any preference being
expressed, and the residue where preference is unavoidable is small enough to record in full.

This inverts the usual arrangement. A weighted-sum ranking expresses a preference over *every*
comparison, including the many that did not need one, and expresses it invisibly. Dominance
ordering expresses preference only where the factors genuinely conflict, and forces it into the
open.

**The frontier record** — which deltas were incomparable, what ordering was chosen, and on what
grounds — is where preference becomes auditable. It is the single most valuable artifact this Part
produces, because it is the only place a ranking can be argued with after the fact.

## 6. Frontier decisions and the oracle boundary

Some frontier orderings are questions about the world: which dimension is more exposed, which gap
propagates further. These are instrument questions and should be answered by observation rather
than by preference, per Part III's boundary test.

Others are questions about value: whether reliability outranks capability for this artifact, at
this moment, for these consumers. These are oracle questions per Parts XVI and XVII, and answering
them inside the loop is self-certification.

The frontier record therefore labels each ordering decision as observed or judged, and each judged
decision carries who judged it and on what grounds. A frontier fully labelled *judged* with no
recorded grounds is a preference list, and every residual ranked beneath it inherits that status.

## 7. Fixability bias and the counting trap

The most damaging ranking bias is the most reasonable-sounding one: order by ease of correction,
close many things quickly, show progress.

The consequence is precise. **Fixability bias optimizes the throughput of closed items rather than
the amount of closed distance.** Its signature is unmistakable once known: the count of open
residuals falls steadily while the total distance is unchanged. Every report shows movement. The
artifact has not moved toward the reference at all.

This is the same defect this stack sealed as *never gate on a ratio*: a ratio is satisfied by
shrinking its denominator, and a residual count is satisfied by closing whatever is cheapest. The
correct quantity is distance closed — which requires the residuals to carry magnitudes, which
requires L3 extraction, which is why Part VI gates this Part.

The rule: **the success of a ranking is measured by distance closed, never by residuals closed.**
Where magnitudes are unavailable and only counts exist, that limitation is stated, since a count
under those conditions is the only available number and also not evidence of anything.

Cheap fixes are not forbidden. Closing a trivial delta that happens to be on the frontier is
correct. What is forbidden is *ranking by* cheapness, which is a different operation with a
different result.

## 8. Starvation

A ranking recomputed each cycle produces a stable class of residuals that are never top-k and never
closed. They are not ignored — each cycle they are ranked, and each cycle something outranks them.
They accumulate silently and indefinitely.

Starvation is not a ranking error; the ranking is correct each time. It is a *ledger* failure: the
residual set retains items that the ranking has structurally decided never to act on, without ever
saying so.

The remedy is an explicit escape, and it must be explicit because starvation is invisible per
cycle and only visible across cycles.

- **Age-based promotion.** A residual that has been ranked without action for a declared number of
  cycles is promoted for one cycle, forcing a decision rather than a deferral.
- **Explicit acceptance.** The residual is moved to accepted disposition with a reason and an
  owner, per Part III, and leaves the active set honestly.
- **Retirement with the reference.** If it was measured against a retired reference, Part V §9
  marks it.

What must not happen is indefinite ranking without action, which is how a residual ledger fills
with items nobody will ever work and consequently stops being read — the same abandonment failure
Part V §8 addressed from the bar-inflation side, arriving here from the other direction.

## 9. Re-ranking cadence

Impact is a function of the current residual set: closing one delta changes the propagation factor
of others, and closing a blocking delta can promote three items at once. The ranking is therefore
recomputed each correction cycle rather than fixed once.

Two guards. Re-ranking that reorders the top of the queue every cycle produces thrash, where work
starts and never finishes; a delta admitted to the current cycle is completed or explicitly
abandoned within it, not silently displaced. And re-ranking must not be an occasion to re-choose
the frontier weights after seeing which deltas would rank where — §10's frontier laundering.

## 10. Failure modes

| Failure | Mechanism |
|---|---|
| **Discovery-order rank** | The extraction list consumed as a work queue |
| **Fixability bias** | Ordering by cost of correction; count falls, distance does not |
| **Counting success** | Ranking evaluated by residuals closed rather than distance closed |
| **Severity substituted for impact** | Manifestation badness treated as consequence of leaving it open |
| **Magnitude-only rank** | Exposure, propagation and irreversibility ignored |
| **Assumed exposure** | Usage modelled from the author's expectation rather than observed |
| **Silent collapse** | Factors summed with undeclared weights |
| **Frontier laundering** | Weights or grounds chosen after seeing which item they would promote |
| **Starvation** | Perpetually-second residuals accumulate with no escape |
| **Thrash** | Every cycle reorders the top; work starts and nothing completes |

## 11. Detection signatures

1. **The falling count with the flat distance.** The clearest signature in the family. Open
   residuals decline steadily; total distance is unchanged. Fixability bias, §7.
2. **The traversal-shaped queue.** The work order matches the file, module or check order of the
   instrument that produced it.
3. **The unanimous frontier.** Every frontier decision labelled judged, with no grounds recorded.
4. **The perpetual second.** Residuals appearing in the top five for many cycles and never in the
   worked set.
5. **The retroactive weight.** Frontier grounds changing between cycles with no change in the
   artifact or the reference.

## 12. Boundary

Ranking is unnecessary where the delta set is smaller than the correction capacity, where all
deltas are comparably cheap and independent, or where the deltas are prohibitions — which are not
ranked but closed, since a prohibition admits no partial satisfaction.

Ranking is also inapplicable below L3 extraction. Ordering L1 or L2 residuals produces an ordering
over unknown magnitudes, which is discovery order with a rank column added, and is worse than no
ranking because it looks like one.

Finally, ranking does not decide admissibility. A high-impact residual does not block a release;
that is a floor's job, per Part II §9. Ranking allocates correction effort and nothing else.

## 13. Evidence — ranking surfaces in this stack

| Surface | Ordering performed | Assessment |
|---|---|---|
| Design review scorer | Findings classified critical, major, minor | A severity tier, not impact — §3's substitution, and correct for its own purpose of gating admission |
| Code quality framework | Per-file scores with hints | Scores present, no ordering across files; magnitude-only if consumed as a queue |
| Reachability audit | Named unreachable set | Unordered by design; the standing debt is a named set, deliberately not a ranked one |
| Owner-facing queue | Admission to human attention | No admission criterion — the gap this family was chartered to supply |
| Findings transport | Distribution of findings between surfaces | No impact field; consumers reconstruct ordering independently and inconsistently |
| This compendium's Phase 0 audit | Gaps enumerated, families ordered by dependency | Ordered by dependency rather than impact; correct for construction sequencing, and not an impact ranking |

The finding is that this stack has severity classification and has no impact ranking, and that the
two are not the same operation. Severity gates admission; impact allocates effort. The
owner-facing queue's missing admission criterion is the same gap seen from the human-attention
side. — Surface behaviours OBSERVED during the Phase 0 audit; assessments INFERRED against §3.

## 14. Trap seeds — for Part XXII

- **T-CLAE-DISCOVERY-ORDER-RANK** — an extraction list consumed as a work queue because a list is
  read as a ranking.
- **T-CLAE-FIXABILITY-BIAS** — ordering by cost of correction; residual count falls steadily while
  distance is unchanged.
- **T-CLAE-COUNT-AS-SUCCESS** — ranking evaluated by residuals closed rather than distance closed,
  satisfiable by closing whatever is cheapest.
- **T-CLAE-FRONTIER-LAUNDERING** — the grounds for a frontier ordering chosen after seeing which
  delta they would promote.
- **T-CLAE-STARVATION** — residuals perpetually ranked and never worked, accumulating with no
  escape and eventually rendering the ledger unread.

## 15. Rule seeds — for Part XXIII

- **PR-CLAE-DOMINANCE-FIRST** — the ordering is derived mechanically by dominance over the declared
  factors. Preference is expressed only on the incomparable frontier.
- **PR-CLAE-RECORD-THE-FRONTIER** — every frontier ordering records the incomparable set, the
  chosen order, the grounds, and whether each decision was observed or judged.
- **PR-CLAE-OBSERVE-EXPOSURE** — exposure is observed from actual use. An assumed exposure is
  labelled as such and the ranking beneath it inherits that status.
- **PR-CLAE-DISTANCE-NOT-COUNT** — ranking effectiveness is reported as distance closed. Where only
  counts exist, the limitation is stated alongside them.
- **PR-CLAE-NO-RANK-BELOW-L3** — residuals below extraction level L3 are not ranked. They are
  recorded and their extraction improved first.
- **PR-CLAE-STARVATION-ESCAPE** — a residual ranked without action for a declared number of cycles
  is promoted for one cycle or explicitly accepted with an owner. Indefinite ranking without action
  is not a disposition.

## 16. Eval seeds — for Part XXIV

- **Count-versus-distance probe.** Over several cycles, plot open residual count against total
  distance. Falling count with flat distance is fixability bias, and this probe is the cheapest
  high-value check in the family.
- **Traversal-correlation probe.** Compare work order against the extraction instrument's traversal
  order. Strong correlation indicates discovery-order ranking.
- **Frontier-completeness probe.** Verify every frontier decision carries grounds and an
  observed-or-judged label. Frontiers that are entirely judged with no grounds are preference lists.
- **Starvation probe.** List residuals present in the top-k for many cycles and never in the worked
  set. Their existence is expected; their invisibility is the failure.
- **Exposure-provenance probe.** For each exposure value, determine whether it was observed or
  assumed. Assumed exposure reproduces the author's model of usage inside the loop.

## 17. Production Reality Gate seed — for Part XXV

**Ranking Integrity Gate.** A correction cycle may consume a ranking only when every ranked residual
carries extraction level L3 or above, the dominance order was computed before any preference was
applied, the frontier record exists with grounds and observed-or-judged labels, and the previous
cycle published distance closed rather than count closed. A ranking failing any of these is
consumed as an unordered set, which is honest, rather than as a priority order, which would not be.

## 18. Pseudoflow — ranking a residual set

Take the residual set for the current cycle. Discard from ranking every residual below extraction
level L3; record them as unrankable and improve their extraction instead of guessing their place.

For each remaining residual, establish the four factors. Take magnitude from the extraction. Observe
exposure from actual use rather than expectation, and where only an expectation is available, label
it assumed. Determine propagation by examining the residual set as a structure: which gaps block the
closure of others. Record irreversibility as a judgment with its grounds.

Compute dominance across all pairs. Where one residual is at least as high on every factor and
strictly higher on one, it ranks above. This step expresses no preference and requires no weights.

Collect the residuals dominated by nothing. This is the frontier and it is usually small. For each
ordering decision within it, determine whether the question is about the world or about value.
Answer world questions by observation. Route value questions to the declared judgment authority and
record who decided and on what grounds.

Publish the ordering together with the frontier record. Without the frontier record the ordering is
unarguable, and an unarguable ordering is indistinguishable from a preference.

Admit the top of the queue into the correction cycle up to capacity. Complete or explicitly abandon
each admitted item within the cycle rather than letting the next re-ranking displace it silently.

At cycle close, report distance closed. Report residual count as well if useful, never instead.

Before the next cycle, check for residuals ranked without action beyond the declared threshold and
force each to a decision — promote it or accept it with an owner. Neither outcome is a failure;
leaving it ranked forever is.

## 19. Integration

Part VIII consumes this ordering as its cycle input and inherits the completion-or-abandonment rule
from §9. Part IX stores frontier records alongside residuals, since a residual's history is
incomplete without why it was or was not worked. Part XVII receives §6's value questions as oracle
traffic and gains from this Part exactly what the owner-facing queue was missing: an admission
criterion, namely frontier membership with a value question attached.

Outside the family, the design review scorer's severity classification is endorsed unchanged for
its own purpose of gating admission, and explicitly not adopted as an impact ranking. The findings
transport is the natural carrier for an impact field so that consumers stop reconstructing
orderings independently.

## 20. Open questions

1. Are the four factors sufficient, and are they independent? Dominance ordering assumes the factor
   set is complete enough that incomparability signals genuine conflict rather than a missing
   factor. — HYPOTHESIS.
2. How is propagation determined without a dependency model of the residual set? §4 requires knowing
   which gaps block others, and where that structure is not explicit, propagation may be as assumed
   as exposure. — UNKNOWN, and the weakest link in the construction.
3. Does the dominance frontier stay small in practice? The whole argument for the construction rests
   on most comparisons resolving mechanically. With four factors and heterogeneous residuals, the
   frontier could be most of the set, which would reduce the method to a fully judged ordering with
   extra steps. — UNKNOWN; directly measurable on the first real set.

## 21. Institutional writeback

Five trap seeds, six process-rule seeds, five eval seeds and one production gate.

Two portable results. The **dominance-then-frontier construction** gives an ordering that expresses
preference only where the factors genuinely conflict, and forces that preference into a record
instead of a weight — usable by any team with a list of findings and no machinery at all. And the
**count-versus-distance signature**: an open-item count falling steadily while total distance is
flat is the fingerprint of fixability bias, it is cheap to plot, and it explains the common
experience of a quality programme that closes a great deal and improves nothing.
