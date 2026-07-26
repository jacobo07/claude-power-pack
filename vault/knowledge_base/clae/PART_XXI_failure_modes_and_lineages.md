---
title: "CLAE Part XXI — Failure Modes and Failure Lineages"
family: clae
part: XXI
depends_on: [I, II, III, IV, V, VI, VII, VIII, IX, X, XI, XII, XIII, XIV, XV, XVI, XVII, XVIII, XIX, XX]
feeds: [XXII, XXIII, XXIV, XXV]
status: SEALED
date: 2026-07-26
---

# Part XXI — Failure Modes and Failure Lineages

## 1. Purpose

Twenty Parts have each named failures locally. This Part asks the question none of them could:
**how do those failures relate to each other?**

They are not independent. They cause each other, in chains, and the chains are why a failure fixed
at its symptom returns. A per-Part treatment necessarily misses this, because a lineage crosses Part
boundaries by definition — that is what makes it a lineage rather than a failure mode.

This Part reduces every failure named in the family to **five structural roots**, traces **six
lineages** from those roots to their terminal states, and gives the diagnostic rule that makes the
taxonomy usable rather than decorative.

## 2. Why lineages rather than a list

A list of failure modes invites checking for each one. That is useful and it has a specific
limitation: it treats symptoms as independent, so the treatment applied is whatever the symptom
suggests.

> **A failure that recurs after being fixed indicates that a downstream link was treated.**

The chain's origin is still producing, so the symptom regenerates. This is the single most useful
thing a lineage taxonomy provides: it converts *this keeps happening* from a frustration into a
diagnostic, pointing upstream to a link that was never examined because it does not resemble the
symptom.

## 3. The five roots

Every failure in this family reduces to one of five **structural conditions** — states of a system,
not events that occur.

| Root | Condition | First named |
|---|---|---|
| **R1 Loop closure** | The criterion is authored by the party being assessed | Part I |
| **R2 Threshold loss** | A computed magnitude is discarded at a predicate | Part II |
| **R3 Vocabulary limit** | A distinction the system cannot express, and therefore cannot report | Parts III, XIII |
| **R4 Accounting misalignment** | The record penalizes the correct action | Parts XIV, XVIII, XIX, XX |
| **R5 Assumed composition** | Local correctness assumed to aggregate | Parts XIII, XVIII, XX |

R3 and R4 deserve emphasis because they were discovered late and are the most general.

**R3** appeared first as a vocabulary problem in Part III, then as a *type* problem in Part XIII §7 —
an instrument whose output has two states cannot express failure-to-observe — and then as a reporting
problem in Part XX §5, where *done* collapses five closure states. In every case the system is not
concealing anything. It lacks the means to say the true thing, and the nearest available expression
is wrong in a consistent direction.

**R4** appeared four times independently: toolsmithing booked as a zero-distance cycle, deviations
read as indiscipline, halts recorded as failures, reopening treated as defect. Each time the
correct action was penalized by the record, and each time the behaviour changed without anyone
deciding it should.

## 4. Six lineages

### L1 — Blindness

`R1 → no external reference → self-authored criterion → score saturates → "we are at the bar" →
measurement effort reallocated → measurement debt accumulates unpublished → the system improves what
it measures and expands what it does not`

**Terminal state:** a system with excellent measured quality and unbounded unmeasured scope, which
reports as excellent. **Loops back to R1**, since the surviving criteria are all internal.

### L2 — Bar inflation

`reference acquired → no pin generations → silent refresh → work and bar movement conflated → residual
flat despite effort → effort appears futile → ledger abandoned → return to internal criteria`

**Terminal state:** the discipline is abandoned and the system returns to R1, now with evidence that
external measurement "did not work."

This is the cruel lineage. Every step is a consequence of doing the *right* thing — acquiring a real
external reference — without the accounting that makes it survivable. **Adopting a reference without
pin generations and attribution produces a worse end state than never adopting one**, because it
inoculates the organization against trying again.

### L3 — Metric theater

`R2 → magnitude needed but unavailable → proxy adopted → correlation unargued → optimization migrates
to the proxy → proxy improves, property does not → proxy becomes the definition of the property`

**Terminal state:** the proxy is the goal. Nobody remembers it was a substitute, and arguing about
the property is heard as arguing about the metric.

### L4 — Myopia

`no L3 extraction → magnitudes unavailable → ranking impossible → fixability bias → count falls,
distance flat → success declared on count → R4 rewards closing many items → the bias is reinforced`

**Terminal state:** high throughput of closed items, no movement toward the reference, and an
incentive structure that maintains it.

### L5 — Replanning amnesia

`intent not recorded at origin → constraint encountered → intent reconstructed at deviation time →
substitution chosen → repeat → composition drift → artifact serves an unchosen purpose → new plans
written against the current state → the original intent is unrecoverable`

**Terminal state: unrecoverable.** This is the only lineage that destroys its own reference point.
The others degrade a system that can still be measured; this one removes the thing measurement would
be against. Once no record of the original intent survives, no amount of later rigour reconstructs
it — later reconstruction is performed against the drifted artifact, which is Part V §3's
perishability at the scale of a whole system.

**L5's point of no return is the loss of the last recorded original intent**, and it passes without
any visible event.

### L6 — Instrument decay

`two-valued instrument → failure-to-run reported as clean → unfalsifiable zero → check becomes
decorative → floor shows no violations → floor read as structurally satisfied → floor retired as
unnecessary → the failure class returns undetected`

**Terminal state:** the protection is gone and its removal was justified by the evidence of its own
broken instrument.

This lineage is worth stating slowly because its shape is unusual: **the defective instrument causes
the retirement of the very floor it was meant to check**, and every step is a reasonable inference
from the available evidence. Part X §6's requirement to verify the check before concluding anything
from a zero exists precisely to break the fifth link.

## 5. Lineage properties

**They cross Part boundaries.** L6 begins in Part XIII, passes through Part II's principle and Part
X's floors, and terminates in a retirement decision. No single Part's failure list contains it.

**They have points of no return.** L5's is the loss of recorded intent. L2's is ledger abandonment,
after which re-adoption faces institutional resistance. L3's is the proxy becoming the definition,
after which the substitution is no longer visible as one. Identifying the point of no return is what
determines urgency.

**They are self-reinforcing at the terminal.** L1 and L2 both return to R1. L4's terminal state
includes an incentive that maintains it. A lineage that has reached its terminal does not drift back
on its own; it requires deliberate intervention against a system that is reporting success.

## 6. Diagnosis — reading backwards

Given an observed symptom, walk the chain upward and treat the earliest link still reachable.

> **Treat the earliest reachable link, not the symptom.**

Worked example. Symptom: *our quality scores are all excellent and customers keep finding problems.*
That is L1's terminal state. Walking upward: is the criterion external? If the references are
internally authored, the useful intervention is at the second link — acquire a real reference — not
at the terminal, where "improve the scores" would make the situation worse by increasing confidence.

Second example. Symptom: *we close a lot of issues and nothing gets better.* L4's terminal. Upward:
is the ranking by magnitude? If magnitudes are unavailable, the intervention is at extraction level,
not at prioritization. Reordering an unmagnituded list produces a differently-ordered guess.

The general form: the symptom is at the end of the chain, the leverage is near the beginning, and
they never resemble each other. That non-resemblance is why lineages must be written down — an
engineer reasoning from the symptom will not arrive at the root by thinking harder about the symptom.

## 7. Compounds

Lineages interact, and two combinations are worth naming.

**L3 + L4 — maximum theater.** A proxy that is easy to move, plus a bias toward cheap fixes, plus
success measured by count. Every incentive points at moving the proxy in the cheapest available way,
and the resulting reports are excellent along every axis the organization reads.

**L1 + L6 — the confident blind state.** No external reference, and checks that cannot report their
own failure to run. The system's criteria are its own, and its verification of those criteria cannot
fail. Nothing internal can produce a negative signal.

> **A system in L1 + L6 is maximally confident and minimally informed.** It is not merely
> unmeasured — it is structurally incapable of generating a discouraging observation.

## 8. Which lineages this stack is in

| Lineage | Status | Evidence |
|---|---|---|
| **L6 Instrument decay** | **Confirmed, active** | Every instrument two-valued, including this family's gate script (Part XIII §11). Links one through four are in place |
| **L1 Blindness** | **Partial** | Two surfaces have legitimate references; all other quality surfaces use internal criteria (Part IV §10). Measurement debt undeclared (Part IX §11) |
| **L4 Myopia** | **Likely** | No tracing or profiling instrument, so L4-level extraction is unavailable outside resource dimensions (Part XIII §11); severity classification used where impact ranking is needed (Part VII §13) |
| **L3 Metric theater** | **Partial** | Numeric quality thresholds with no recorded derivation (Part XI §11) — proxies whose correlation was never argued |
| **L2 Bar inflation** | **Not present** | No references are pinned because few references exist |
| **L5 Replanning amnesia** | **Not assessable** | Would require reading the intent records of past work, which was outside this build's scope |

The L2 result is worth stating plainly because it is easy to misread as good news. **This stack
cannot suffer bar inflation because it has not adopted the discipline that produces it.** That is not
a strength; it is the absence of the precondition. The correct reading is that L2 becomes a live risk
the moment references are adopted, which makes Part V's pin generations and attribution decomposition
a *precondition* for that adoption rather than a refinement of it.

The L1 + L6 compound is partially present and is the finding this Part exists to surface. It was not
visible from any individual Part — Part IV found the reference gap, Part XIII found the arity gap, and
neither could see that together they constitute the confident-blind state. — Component findings
OBSERVED across the family's evidence sections; lineage assignments INFERRED against §4.

## 9. Boundary

A lineage is a **common path, not a causal law**. Systems reach these terminals by other routes and
sometimes stop partway for reasons the model does not contain. Treating a lineage as deterministic
produces false confidence about where a system is going.

Nor is presence at one link evidence of the rest. A two-valued instrument does not mean a floor will
be retired; it means the fifth link is available. Lineages describe what is *possible* from a
position, not what is inevitable.

And this Part is subject to its own R4. **A lineage taxonomy can become the ritual checklist** that
Part X §6 warned about — six chains dutifully checked each quarter, producing a compliance artifact
rather than a diagnosis. The controls are the same: each lineage carries a retirement condition,
which is the structural elimination of its root, and a lineage whose root is structurally impossible
is retired rather than checked forever.

## 10. Trap seeds — for Part XXII

The lineages themselves are this Part's contribution to the trap registry, since a trap that names
only a terminal state cannot be escaped from the terminal.

- **T-CLAE-LINEAGE-BLINDNESS** — L1, from loop closure to unbounded unmeasured scope reporting as
  excellence.
- **T-CLAE-LINEAGE-BAR-INFLATION** — L2, where adopting a reference without attribution produces a
  worse end state than never adopting one.
- **T-CLAE-LINEAGE-METRIC-THEATER** — L3, terminating in the proxy becoming the definition.
- **T-CLAE-LINEAGE-MYOPIA** — L4, terminating in a reinforced incentive to close cheap items.
- **T-CLAE-LINEAGE-REPLANNING-AMNESIA** — L5, the only lineage whose terminal is unrecoverable.
- **T-CLAE-LINEAGE-INSTRUMENT-DECAY** — L6, where a defective instrument causes the retirement of the
  floor it was meant to check.
- **T-CLAE-COMPOUND-CONFIDENT-BLIND** — L1 with L6: a system structurally incapable of generating a
  discouraging observation.

## 11. Rule seeds — for Part XXIII

- **PR-CLAE-TREAT-THE-EARLIEST-LINK** — on a recurring failure, identify its lineage and intervene at
  the earliest reachable link. Recurrence after a fix is evidence that a downstream link was treated.
- **PR-CLAE-ATTRIBUTION-BEFORE-REFERENCE** — pin generations and work-versus-bar decomposition are
  established before a reference discipline is adopted, since L2 makes unattributed adoption worse
  than none.
- **PR-CLAE-VERIFY-BEFORE-RETIRING-A-FLOOR** — a floor's zero-violation record justifies retirement
  only alongside evidence its check executed. This breaks L6 at its fifth link.
- **PR-CLAE-RECORD-INTENT-AT-ORIGIN** — original intent is recorded when an approach is chosen. L5 is
  the only lineage with an unrecoverable terminal, and this is its sole preventive.
- **PR-CLAE-LINEAGES-RETIRE** — each lineage carries a retirement condition naming the structural
  elimination of its root. Lineages are not checked in perpetuity.

## 12. Eval seeds — for Part XXIV

- **Lineage-position probe.** For each of the six, determine which links are currently in place. The
  output is a position, not a pass or fail, and it is the only form in which this Part is actionable.
- **Recurrence-lineage probe.** For each failure that has recurred after a fix, identify which link
  the fix addressed. Downstream fixes predict recurrence and this makes the prediction checkable.
- **Compound probe.** Test specifically for L1 with L6 — internal criteria plus two-valued
  verification. This compound is invisible to any single-dimension check.
- **Point-of-no-return probe.** For lineages with links in place, determine the distance to the point
  of no return. L5's proximity is the highest-urgency measurement in the family.
- **Root-census probe.** For each of the five roots, count the surfaces exhibiting it. Roots are
  where interventions have the widest effect.

## 13. Production Reality Gate seed — for Part XXV

**Lineage Position Gate.** A system may claim measured quality only when its lineage position is
published alongside the claim: which links of which lineages are currently in place. A claim from a
system with L1 and L6 links present is labelled structurally unfalsifiable, since no internal
observation could contradict it. This is a label carried with the claim, not a block — the claim may
still be correct, and the reader is entitled to know it could not have been shown otherwise.

## 14. Pseudoflow — diagnosing with lineages

On observing a symptom, do not treat it. Locate it among the terminal and intermediate states in §4,
and identify which lineage it belongs to.

Walk the chain upward, link by link, asking at each whether that link is currently in place. Stop at
the earliest link that is both present and reachable — reachable meaning something can be changed
there now, without a decision that is not yours to make.

Intervene there, and record which link was treated. That record is what makes a future recurrence
diagnostic rather than merely frustrating: if the symptom returns, the treated link was downstream
of the cause and the walk continues upward from where it stopped.

Where the earliest present link is not reachable — it requires authority, budget or a decision
belonging to someone else — that is an oracle question or an escalation, not a licence to treat the
symptom instead. Treating the symptom while the root produces will consume effort indefinitely and
generate evidence that the problem is intractable.

Check the compounds explicitly. L1 with L6, and L3 with L4, are not visible from any single
lineage's walk, and both produce systems whose reports are uniformly good.

Periodically, review the five roots rather than the six lineages. A root eliminated structurally
retires every lineage descending from it, which is a far larger intervention than treating any
individual chain.

## 15. Integration

This Part consumes every prior Part's failure section and supplies Part XXII with lineage-shaped
traps, Part XXIII with five root-level process rules, Part XXIV with position-probes rather than
pass-fail evals, and Part XXV with a gate that labels rather than blocks.

Its relationship to Part XXII is worth stating: a trap registry entry names a condition and its
escape, and is most useful when the condition is *recognized*. A lineage is what tells you which trap
you are in when the symptom you can see is three links downstream of the trap you are actually
caught by.

Outside the family, the recurring-error analysis is the natural host for §2's diagnostic — it already
detects recurrence, and recurrence is precisely the signal that a downstream link was treated.

## 16. Open questions

1. Are the five roots exhaustive? They were derived by reducing this family's own twenty Parts, which
   bounds them by what this family noticed. A sixth root would most plausibly concern incentives
   external to the system, which no Part here examined. — HYPOTHESIS.
2. Can lineage position be measured without a full audit? §12's position probe requires checking
   every link, and a cheaper leading indicator per lineage would make this Part operational rather
   than periodic. — UNKNOWN.
3. Is L5 detectable before its point of no return? Its terminal is unrecoverable and its progression
   is invisible — no event marks the loss of the last intent record. A detector would need to notice
   an absence, which is exactly what Part II §P8 says instruments do worst. — UNKNOWN, and the most
   consequential open question in the Part.

## 17. Institutional writeback

Seven trap seeds, five process-rule seeds, five eval seeds and one production gate.

Three portable results. **Five roots generate every failure in this family** — loop closure,
threshold loss, vocabulary limit, accounting misalignment, assumed composition — and intervening at a
root retires every lineage descending from it. **A failure that recurs after being fixed indicates a
downstream link was treated**, which converts the most common frustration in quality work into a
diagnostic pointing upstream. And **adopting a reference without attribution is worse than not
adopting one** — L2 terminates in abandonment plus evidence that external measurement does not work,
which makes Part V's pin generations a precondition for reference discipline rather than a refinement
of it.

The finding this Part exists to produce could not have come from any single Part: **L1 with L6 is the
confident-blind compound**, and this stack has links of both in place. Part IV saw the reference gap.
Part XIII saw the arity gap. Neither could see that together they describe a system structurally
incapable of generating a discouraging observation about itself.
