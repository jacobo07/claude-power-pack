---
title: "CLAE Part XXII — Traps Registry"
family: clae
part: XXII
depends_on: [XXI]
feeds: [XXIII, XXIV, XXV, XXVI]
status: SEALED
date: 2026-07-26
---

# Part XXII — Traps Registry

## 1. Purpose

Twenty-one Parts seeded traps. This Part is the registry: the schema each entry must satisfy, the
consolidation of the seeded set, the organizing principle that makes a registry usable, and the
honest admission of what a registry this size can and cannot be.

The measured seed set, counted from the sealed Parts rather than asserted:

| Quantity | Count |
|---|---|
| Trap seed occurrences across Parts I–XXI | **100** |
| Distinct trap names | **99** |
| Names seeded independently in more than one Part | **1** |

The single duplicate is `T-CLAE-ORACLE-EXHAUSTION`, seeded in Part III from the vocabulary side —
routing mechanical questions to a judgment channel — and again in Part XVI from the boundary side,
where over-wide placement produces the same terminal. Two Parts reasoning from different directions
arrived at the same trap.

That is a signal rather than an error:

> **A trap seeded independently from more than one direction is a strong trap.** It has more than one
> approach path, which means it will be reached more often than its single-Part siblings suggest.

## 2. What a registry is for

A trap is only useful if it can be **recognized before it closes**. That single requirement
determines the registry's organization.

> **A registry organized by name serves its author. A registry organized by symptom serves the person
> already in trouble.**

Someone in a trap does not know its name — that is the condition. They have an observation: a report
that looks wrong, a number that will not move, a check that has never failed. The registry must be
enterable from that observation, which makes the **detection index** of §7 the primary artifact and
the alphabetical listing a secondary convenience.

## 3. The entry schema

Seven fields. Six are familiar; the sixth is where most trap registries fail.

1. **Name** — stating the *condition*, not the remedy, per Part III §11, so the name matches what a
   reader observes before they know what is wrong.
2. **Root** — which of Part XXI's five structural roots it descends from.
3. **Trigger** — the situation in which the trap becomes available.
4. **Symptom** — what is observable from inside, in the observer's own terms.
5. **Detection** — the specific check that distinguishes this trap from its neighbours.
6. **Escape** — what to do, executable **by someone already in the trap**.
7. **Retirement condition** — what would make this entry unnecessary.

Field six carries a constraint that is easy to state and easy to violate:

> **An escape that requires what the trap removed is not an escape.**

*Measure the residual* is not an escape from a trap whose defining property is that measurement was
discarded. *Consult the original intent* is not an escape from a trap that destroyed the intent
record. An escape must be executable from inside, with what remains available there — and a registry
whose escapes assume the healthy state is a registry of laments.

A trap with no valid escape is recorded as **prevention-only**, per §5. That is an honest entry.
Inventing an escape to fill the field is not.

## 4. Organization by root

Every entry descends from one of Part XXI's five roots, and grouping by root is what makes the
registry actionable at scale: an intervention at a root retires every entry beneath it, whereas
treating entries individually is unbounded work.

| Root | Character of its traps | Representative entries |
|---|---|---|
| **R1 Loop closure** | The system judges itself against something it authored | synthesized reference, counterfeit distance, ceiling-from-history, self-certification, self-acceptance |
| **R2 Threshold loss** | A computed magnitude discarded at a predicate | vanishing residual, residual amnesia, count-as-success, done-collapse |
| **R3 Vocabulary limit** | A distinction the system cannot express | two-valued instrument, zero-without-coverage, mode laundering, binary outcomes, undefined omitted |
| **R4 Accounting misalignment** | The record penalizes the correct action | toolsmith-as-failure, halt-as-failure, suppressed deviation ledger, reopening-as-defect |
| **R5 Assumed composition** | Local correctness assumed to aggregate | chain-coverage-union, composition drift, inherited closure |

Root assignment is INFERRED from each trap's originating Part rather than independently derived, and
a small number of entries could defensibly sit under two roots — `T-CLAE-ZERO-WITHOUT-COVERAGE`
descends from R3 by its mechanism and manifests as R1 by its effect. Where an entry is ambiguous the
registry records both, since a reader arriving from either root should find it.

## 5. Prevention-only traps

Some traps have no escape. The registry must say so rather than fabricate one, and identifying them
is among the most useful things it does — because a prevention-only trap changes the urgency of its
preventive control from good practice to the only available control.

| Trap | Why no escape exists |
|---|---|
| **Replanning amnesia** (Part XXI L5) | The escape would require the original intent, which the trap destroyed. Reconstruction is performed against the drifted artifact |
| **Reference capture, undetected** | The escape requires provenance; if provenance was never recorded, nothing distinguishes the captured reference from a legitimate one |
| **Orphaned residual history** | Identity was re-derived per run; the prior series cannot be reattached to entries that no longer share identifiers |
| **Uninterpretable historical zeros** | Clean results from a two-valued instrument cannot be retroactively separated into observed-nothing and did-not-run |

The pattern across all four: **the trap destroys the evidence that its own escape would need**. This
is the sharpest reason to take the preventive rules seriously — record provenance, record intent,
assign identity once, widen instrument output — because in each case the cost of prevention is small
and the cost of omission is permanent.

The fourth entry is this stack's live position, per Part XIII §11: the clean results already produced
by two-valued instruments cannot be re-interpreted. Widening the instruments now protects future
results and cannot recover past ones.

## 6. The high-recognition subset

Ninety-nine entries is a reference work. Nobody memorizes it, and a registry that expects to be
memorized will be ignored. Ten entries are worth carrying in working memory, selected by three
criteria together: **cheap detection**, **severe terminal**, and **common occurrence**.

1. **Counterfeit distance** — a rubric-anchored score consumed as distance to an external bar.
   *Detect:* does the value saturate when a better external instance appears?
2. **Two-valued instrument** — failure-to-run reported as clean. *Detect:* disable a precondition and
   observe the output.
3. **Zero without coverage** — a residual of zero with no declared detection scope. *Detect:* ask
   what the instrument could have found.
4. **Count as success** — falling residual count against flat total distance. *Detect:* plot both.
5. **Measurement debt invisible** — a summary listing only measured dimensions. *Detect:* look for
   the unmeasured-scope line.
6. **Synthesized reference** — the assessing system generated its own bar. *Detect:* ask for the
   acquisition record.
7. **Targeted re-measurement** — only the corrected delta re-observed. *Detect:* an all-closed
   outcome history.
8. **Halt as failure** — declared halts recorded as defects. *Detect:* read the accounting, not the
   policy.
9. **Done collapse** — five closure states reported through one word. *Detect:* inspect the status
   field's available values.
10. **Scope drift** — autonomous work outside the accepted contract's scope. *Detect:* compare work
    products against the stated scope.

Each of these has a detection costing minutes, and each sits on a lineage whose terminal is
expensive. This subset is what a practitioner carries; the full registry is what they consult.

## 7. The detection index

The registry's primary entry point, keyed by what an observer actually notices.

| Observation | Candidate traps |
|---|---|
| A quality number that never moves | counterfeit distance · stable offset · asymptotic residual |
| A check that has never failed | decorative floor · two-valued instrument · uncalibrated instrument |
| Many items closed, nothing better | fixability bias · count-as-success · targeted re-measurement |
| Every report is good and outcomes are not | measurement debt invisible · confident-blind compound · self-certification |
| The same problem keeps returning | downstream-link treatment · fix-without-probe · oscillation |
| Corrections that change nothing | null escalation · noise-as-signal · mislocalized extraction |
| Work drifted somewhere nobody intended | composition drift · scope drift · replanning amnesia |
| A judgment nobody outside ever made | undeclared boundary · self-acceptance · drift-narrow |
| Effort that appears futile | conflated attribution · bar inflation · starvation |
| A rule everyone follows and nothing enforces | rules-without-checks · advisory-only knowledge |

An observer with any of these ten observations can reach the relevant entries without knowing a
single trap name, which is §2's requirement satisfied.

## 8. Registry hygiene

The registry is subject to every control this family applies to accumulating sets — Part X §6 for
floors, Part XV §7 for probes, and now itself.

**Retirement conditions.** Each entry states what would make it unnecessary: usually that its root
has been structurally eliminated in this system. An entry that cannot state one indicates its
mechanism was never clearly identified.

**Growth control.** New entries are admitted when a trap is *observed*, not when one is imagined. A
registry admitting hypothetical traps grows without bound and dilutes the entries that were paid for
in real failures.

**The honest admission.** Ninety-nine entries is a reference work, and treating it as a checklist
reproduces exactly the ritual accumulation Part X §6 warned about — this family's own machinery
producing the compliance artifact it was built to attack. The registry is indexed for *retrieval*,
consulted on a symptom, and never enumerated as a periodic review. What *is* reviewed periodically is
the five roots, which is a five-item review rather than a ninety-nine-item one.

## 9. Evidence — the registry pattern in this stack

This stack already has a trap registry, and it is better-formed than this one in the dimension that
matters most.

The known-false-positives register carries, per entry: what the signal really is, the symptom as
observed, and the response — bounded explicitly to two minutes. That is §3's schema minus root and
retirement, plus a cost bound this Part does not require and probably should. Its entries are
symptom-keyed, per §2. And it is **small** — a handful of entries, each earned from a real
recurrence.

That register was consulted successfully during this build: the third-write anti-thrash block fired
with no reason string, the register named the cause and the response, and the work continued in one
step. A ninety-nine-entry registry would not have been consulted that way.

The contrast is the finding, and it is not a criticism of either:

> **A small, symptom-keyed, cost-bounded register is an operational tool. A large one is a reference
> work. They are different artifacts and conflating them makes the first unusable and the second
> unread.**

The correct relationship is that the reference work is where entries live, and the operational
register holds the subset that has actually recurred here — which is §6's high-recognition subset
narrowed further by local evidence. — Register behaviour and its use in this session OBSERVED; the
two-artifact distinction INFERRED.

## 10. Failure modes of a trap registry

| Failure | Mechanism |
|---|---|
| **Name-keyed organization** | Enterable only by someone who already knows what they are in |
| **Escape requiring the removed thing** | An escape written from the healthy state, unusable from inside |
| **Fabricated escapes** | Prevention-only traps given invented escapes to fill the field |
| **Hypothetical admission** | Imagined traps admitted alongside observed ones, diluting the earned entries |
| **Enumerated as a checklist** | A reference work reviewed item by item, becoming ritual |
| **No retirement conditions** | Growth without pruning; the registry outlives its roots |
| **Conflated with the operational register** | A large reference treated as the thing consulted mid-incident |

## 11. Rule seeds — for Part XXIII

- **PR-CLAE-SYMPTOM-KEYED-REGISTRY** — the registry's primary index is by observable symptom. Name
  and root listings are secondary.
- **PR-CLAE-ESCAPE-FROM-INSIDE** — every escape is executable with what remains available inside the
  trap. Escapes requiring what the trap removed are recorded as prevention-only.
- **PR-CLAE-NO-FABRICATED-ESCAPE** — a trap with no valid escape is recorded as prevention-only, and
  its preventive rule is promoted in priority accordingly.
- **PR-CLAE-ADMIT-ON-OBSERVATION** — entries are admitted when a trap has been observed, not when one
  is imagined.
- **PR-CLAE-REVIEW-ROOTS-NOT-ENTRIES** — periodic review covers the five roots. The entry set is
  consulted on symptom and never enumerated.
- **PR-CLAE-SEPARATE-THE-OPERATIONAL-REGISTER** — the small, symptom-keyed, cost-bounded register of
  locally-recurring traps is maintained separately from the reference registry.

## 12. Eval seeds — for Part XXIV

- **Symptom-entry probe.** Give a reader one of §7's observations and no trap names, and measure
  whether they reach the relevant entry. This is the registry's actual usability test.
- **Escape-validity probe.** For each escape, verify it is executable given the trap's own
  conditions. Escapes assuming the healthy state are the most common defect in trap registries.
- **Prevention-only census.** Confirm the four §5 entries are marked, and check for others whose
  escape silently assumes destroyed evidence.
- **Provenance probe.** For each entry, identify the observed failure that produced it.
  Hypothetical entries are dilution.
- **Consultation probe.** Count registry consultations and their outcomes over a period. A registry
  never consulted mid-incident is a reference work and should be labelled one rather than expected to
  operate.

## 13. Production Reality Gate seed — for Part XXV

**Trap Registry Gate.** The registry is usable as a control only when every entry carries all seven
fields, every escape is executable from inside its trap or the entry is marked prevention-only, the
symptom index resolves each of §7's observations, and the operational register is maintained
separately from the reference set. A registry failing these is recorded as documentation — which is
a legitimate artifact, correctly labelled, rather than a control that is assumed to be operating.

## 14. Pseudoflow — using and maintaining the registry

**To use it:** start from what you observed, not from what you suspect. Enter through §7's detection
index. Read the candidate entries' symptoms and pick the one that matches your observation rather
than the one that matches your theory — the theory is frequently the trap.

Apply the detection check to distinguish among neighbours. Then apply the escape, and confirm it is
executable with what you actually have; if it requires something the situation has removed, you are
in a prevention-only trap and the correct action is to stop the damage and record the preventive rule
for next time, not to search for a cleverer escape.

**To maintain it:** admit an entry when a trap has been observed here. Record all seven fields.
Assign the root, and where the mechanism and the manifestation point at different roots, record both.

Test the escape against the trap's own conditions before recording it. Writing an escape from the
healthy state is the default failure and it is invisible until someone in the trap tries to use it.

Review the five roots periodically. Do not enumerate the entries — a ninety-nine-item review is the
ritual this family exists to prevent.

Maintain the operational register separately: the small subset that has actually recurred in this
system, symptom-keyed, with a cost bound on investigation.

## 15. Integration

Part XXI supplies the roots and the lineages, without which this registry is a flat list of
independent hazards. Part XXIII takes §11's six rules plus the preventive rules of the prevention-only
entries, which inherit elevated priority. Part XXIV takes the detection checks as eval bodies. Part
XXV's gate governs whether the registry counts as a control. Part XXVI records the relationship
between this reference set and the stack's operational register.

Outside the family, the known-false-positives register is the model for the operational half and is
endorsed unchanged, including its two-minute investigation bound — a constraint this Part's schema
does not require and which §9 identifies as an improvement worth adopting.

## 16. Open questions

1. Is ninety-nine the right size, or is the seeded set inflated by Parts that seeded traps because the
   section existed? §8's admit-on-observation rule was applied retroactively to a set produced
   deductively, and some entries may be hypothetical by that standard. — HYPOTHESIS; a provenance
   probe would settle it and was not run here.
2. Can escapes be validated without entering the trap? §14 requires testing an escape against the
   trap's conditions, and for prevention-only traps that is impossible by construction. — UNKNOWN.
3. Does symptom-keying survive as the registry grows? Ten observations index ninety-nine entries
   comfortably; at several hundred the index becomes the discrimination problem it was meant to
   solve. — UNKNOWN.

## 17. Institutional writeback

Six rule seeds, five eval seeds and one production gate.

Three portable results. **Organize by symptom, not by name** — the person who needs a trap registry is
by definition someone who does not know which trap they are in. **An escape that requires what the
trap removed is not an escape**, and registries written from the healthy state are full of them; the
honest alternative is to mark entries prevention-only, which raises the priority of their preventive
rules from good practice to sole control. And **a small operational register and a large reference
registry are different artifacts** — this stack's five-entry, symptom-keyed, two-minute-bounded
register was consulted successfully mid-incident during this very build, which a ninety-nine-entry
reference work never would have been.

The structural finding: the four prevention-only traps share one property — **each destroys the
evidence its own escape would require**. That is the strongest available argument for the family's
cheapest rules, since recording provenance, recording intent, assigning identity once and widening
instrument output each cost almost nothing at the time and are the only moments those options exist.
