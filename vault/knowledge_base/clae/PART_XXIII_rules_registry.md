---
title: "CLAE Part XXIII — Hard Rules and Process Rules Registry"
family: clae
part: XXIII
depends_on: [XXI, XXII]
feeds: [XXIV, XXV, XXVI]
status: SEALED
date: 2026-07-26
---

# Part XXIII — Hard Rules and Process Rules Registry

## 1. Purpose

Twenty-two Parts seeded rules. This Part is the registry: the record schema, the distinction between
a hard rule and a process rule, the **enforcement layer** that determines a rule's actual force
regardless of its wording, and the honest assessment of what happens when this many rules arrive at
once.

The measured set, counted from the sealed Parts:

| Quantity | Count |
|---|---|
| Process rule seeds across Parts I–XXII | **118** |
| Distinct names | **118** |
| Hard rules seeded | **0** |

Two of these numbers need stating rather than celebrating.

**Zero duplicates across 118 rules from 22 Parts** is not evidence of orthogonality. It is evidence
that the *names* are distinct, and names were chosen per-Part by an author who had just written that
Part. Semantic overlap is not detectable by the check that produced this number, and the honest
position is that overlap is likely and unmeasured. §9 records it as an open question rather than
asserting a clean set — applying this family's own discipline to this family's own count.

**Zero hard rules is deliberate.** Part I §6 and Part II §11 placed prohibitions and invariants
explicitly out of scope. A family about how to measure and report should not be issuing prohibitions;
one that did would be overreaching into a domain that already has 156 well-provenanced entries.

## 2. Hard rule versus process rule

| | Hard rule | Process rule |
|---|---|---|
| Form | A prohibition or an invariant | A required behaviour |
| Escape | None, except a declared authorizing phrase | A deviation with a proven constraint and measured loss |
| Violation | Work stops | Quality degrades; the loss is recorded |
| Verdict shape | Binary and exact | Binary at the boundary, graded in effect |

**The promotion test:** a process rule becomes a hard rule when its violation produces an
**unrecoverable** consequence — not when it is violated frequently. Frequency is a floor-derivation
question, per Part XI, and promoting on frequency produces a hard-rule archive full of things that
are merely annoying, which dilutes the entries that genuinely stop work.

By that test, a small number of this family's process rules are promotion candidates — those whose
violation destroys evidence that cannot be reconstructed. They are exactly Part XXII §5's
prevention-only set: record provenance, record intent at origin, assign residual identity once,
widen instrument output. Each of these, violated, forecloses a recovery permanently. Whether they
warrant promotion is a decision belonging to the archive's owner, not to this family.

## 3. The record schema

Eight fields, extending the archive's existing shape with three this family adds.

1. **Name** — imperative, stating the required behaviour, per Part III §11.
2. **Statement** — the rule itself.
3. **Origin** — the Part and the observed failure it derives from.
4. **Root** — which of Part XXI's five.
5. **Enforcement layer** — per §4. *Added by this family.*
6. **Eval** — the check in Part XXIV that verifies compliance. *Added by this family.*
7. **Retirement condition** — what would make it unnecessary. *Added by this family.*
8. **Escape route** — the deviation path, or none for a hard rule.

## 4. The enforcement layer

This is the registry's real content, and the field most rule archives lack.

> **A rule's actual force is determined by its enforcement layer, not by its wording.** A rule at the
> weakest layer, stated in the strongest language, is advisory in fact.

Five layers, ordered by reliability:

| Layer | Mechanism | Reliability |
|---|---|---|
| **1. Structural** | The violation is unrepresentable | Cannot be violated |
| **2. Automated gate** | A check runs and blocks or labels | Fails only if the check fails |
| **3. Automated advisory** | A check runs and reports | Depends on the report being read |
| **4. Checklist** | A human step in a procedure | Depends on the step being performed |
| **5. Doctrine** | Read and applied by judgment | Depends on recall at the moment of decision |

**Prefer the lowest layer available.** Making a violation unrepresentable beats checking for it,
which beats reporting it, which beats remembering it. Part XIII §7's three-valued output is the
family's clearest layer-1 opportunity: an instrument whose output *type* includes could-not-observe
cannot report a failed run as clean, and the entire class of unfalsifiable-zero rules stops needing
enforcement because the violation stops being expressible.

That is the general shape of a layer-1 move — **change what can be said, and the rules governing what
should be said become unnecessary.** It is rare, cheap when available, and permanent.

## 5. Layer assignment for this family's 118

An honest estimate rather than a completed assignment, since assigning all 118 was not performed
here.

- **Layer 1 — a small handful.** Three-valued instrument output; residual identity assigned once
  rather than re-derived; the five closure verdicts as a status field's enumerated values. Each of
  these makes a class of violation unrepresentable rather than forbidden.
- **Layer 2 — roughly the nineteen gates** seeded across the Parts and consolidated in Part XXV.
  These are the rules that can be checked automatically at a decision point.
- **Layers 3 and 4 — a modest number**, mostly the probes of Part XXIV run periodically.
- **Layer 5 — the majority.**

That last line is this family's central implementation risk, and it deserves to be stated without
softening:

> **A doctrine of 118 rules at layer 5 has approximately the force of a doctrine of zero rules.**

Nobody applies 118 rules from memory at a decision point. The rules that will actually operate are
the ones with a mechanism, and the rest are a reference work — legitimate as such, and not to be
mistaken for governance.

The remedy is not to reduce the doctrine. It is to be explicit about which subset carries the load:
Part XXII §6's ten high-recognition traps, Part XXV's gates, and the small layer-1 set. Those are the
operating rules. The other hundred are consultable, and labelling them that way is more honest than
declaring them all mandatory and watching them be ignored uniformly.

## 6. Origin discipline, and an honest limitation

Every record cites the Part and the failure it derives from. But there is a distinction in the
*kind* of derivation that this family must state plainly about itself.

> **A deductively-derived rule is a hypothesis about a failure. An empirically-derived rule is a
> record of one.**

This stack's hard-rule archive is largely empirical: each entry cites a real incident, with a date
and a consequence. That provenance is stronger than anything this family produced.

CLAE's 118 rules are largely **deductive** — derived from the corpus, from the Phase 0 audit of this
stack's surfaces, and from reasoning within the family. A meaningful subset is grounded in observed
findings: the two-valued instruments, the unregistered gate script, the absent tracing instrument,
the reserved-decisions-without-declared-judgments gap. Those are observations. The rest are
inferences from them.

This does not make the deductive rules wrong. It makes them **untested**, and a rule archive that
does not distinguish tested from untested entries lets the untested borrow standing from the tested —
which is Part XI §11's credibility-borrowing failure, arriving in the rule registry.

Each record therefore carries its derivation kind, and the registry reports the ratio. A family
claiming 118 rules of which most are hypotheses is more useful than one claiming 118 rules.

## 7. Registry hygiene

The same three controls as floors, probes and traps — and by now the repetition is the point, since
every accumulating set in this family needs them.

**Retirement conditions** at creation, per Part X §6. A rule whose retirement condition cannot be
stated indicates its consequence was never identified.

**Growth on observation.** New rules are admitted from observed failures. Deductive rules are
admitted as hypotheses and labelled.

**Periodic review of roots, not entries**, per Part XXII §8. Five roots is a reviewable set; 118
rules is not, and reviewing them item by item is the ritual this family exists to attack.

## 8. Evidence — the rule archive in this stack

The archive carries, per entry: a trigger, the required action, an exception clause with a literal
authorizing phrase, and the origin incident. That is four of §3's eight fields, and the four it has
are the four that are hardest to reconstruct later.

What it lacks: **enforcement layer**, **eval**, **retirement condition**, and **root**.

The consequence of the missing layer field is the one that matters. The archive's entries are
enforced through mechanisms ranging from a compiled digest read at four declared triggers — layer 2
for those triggers — down to entries that operate purely by being read. Nothing in the record
distinguishes them, so every entry appears equally binding, and a reader cannot tell which rules will
actually stop them and which depend on recall.

The compiled-digest mechanism is itself notable as a layer-2 move on a corpus that would otherwise be
layer 5: it makes a subset of the archive fire at declared triggers rather than depending on the
agent having read 156 entries. That is the correct architectural response to the §5 problem, applied
before this family articulated it.

> **The finding: this stack has better rule provenance; this family has better rule structure. The
> useful action is a merge, not a replacement.**

Adding enforcement layer, retirement condition and root to the existing archive would cost four
fields per entry and would make visible, for the first time, how much of a 156-rule corpus actually
operates. — Archive schema and digest mechanism OBSERVED from the governance surfaces; the
layer-distribution assessment INFERRED.

## 9. Failure modes

| Failure | Mechanism |
|---|---|
| **Wording mistaken for force** | A layer-5 rule in mandatory language read as binding |
| **Uniform mandate** | All rules declared equally binding; readers cannot tell which will stop them |
| **Layer-5 accumulation** | A doctrine grows past the point where any of it is applied from memory |
| **Deductive borrowing empirical standing** | Untested rules indistinguishable from incident-derived ones |
| **Name-distinctness read as orthogonality** | Semantic overlap concealed by fine-grained naming |
| **Promotion on frequency** | Process rules promoted to hard rules because they are violated often rather than unrecoverably |
| **No retirement** | The archive only grows; its roots are never eliminated |
| **Missing eval** | A rule with no check is advisory regardless of its layer claim |

## 10. Detection signatures

1. **The uniform archive.** Every entry equally mandatory, no layer field. Nobody can tell which
   rules operate.
2. **The unapplied majority.** A large archive with a small recurring subset actually cited in
   practice. The cited subset is the real doctrine.
3. **The unstated derivation.** Rules with no indication of whether an incident produced them.
4. **The layer-1 opportunity unclaimed.** A rule forbidding something that could have been made
   unrepresentable — the cheapest available improvement and the least often taken.
5. **The frequency promotion.** Hard rules whose origins describe annoyance rather than
   irrecoverability.

## 11. Rule seeds — for this registry itself

- **PR-CLAE-DECLARE-THE-LAYER** — every rule records its enforcement layer. A rule without one is
  recorded at layer 5 by default, since that is what it is until a mechanism exists.
- **PR-CLAE-PREFER-THE-LOWEST-LAYER** — where a violation can be made unrepresentable, do that
  instead of forbidding it. Structural enforcement retires the rule rather than enforcing it.
- **PR-CLAE-LABEL-THE-DERIVATION** — each rule records whether it derives from an observed failure or
  from inference. The registry reports the ratio.
- **PR-CLAE-PROMOTE-ON-IRRECOVERABILITY** — a process rule becomes a hard rule when violation
  forecloses recovery, never because violation is frequent.
- **PR-CLAE-NAME-THE-OPERATING-SUBSET** — the registry states which rules actually operate. A
  doctrine that declares all of itself mandatory has declared none of itself enforceable.
- **PR-CLAE-EVERY-RULE-HAS-AN-EVAL** — a rule with no corresponding check in the eval set is
  advisory, and is recorded as advisory rather than as required.

## 12. Eval seeds — for Part XXIV

- **Layer-census probe.** Assign every rule a layer and report the distribution. The layer-5
  proportion is the fraction of the doctrine that depends on recall.
- **Citation probe.** Over a period, count which rules were actually invoked in decisions. The cited
  set is the operating doctrine; the gap between it and the archive is the reference work.
- **Derivation-ratio probe.** Count observed versus inferred origins. A high inferred ratio means the
  archive is largely hypothesis and should say so.
- **Layer-1 opportunity probe.** For each rule, ask whether its violation could be made
  unrepresentable. Positives are the cheapest permanent improvements available.
- **Overlap probe.** Cluster rules by the behaviour they require rather than by name, and count
  clusters. This is the check that §1's distinct-name count could not perform.

## 13. Production Reality Gate seed — for Part XXV

**Rule Registry Gate.** A rule set may be described as governance only when every entry carries its
enforcement layer, derivation kind, retirement condition and eval reference, and the operating subset
is named separately from the reference set. Sets failing this are described as doctrine — a
legitimate artifact, correctly labelled — so that a reader knows whether a given entry will stop them
or merely inform them.

## 14. Pseudoflow — admitting and maintaining a rule

When a failure is observed, first ask whether a rule is the right response at all. A violation that
can be made unrepresentable needs a structural change, not a rule. A recurring class across many
artifacts needs a floor, per Part X §7. A specific historical failure needs a probe, per Part XV. A
rule is the correct response when the required behaviour is general, the violation is representable,
and no mechanism can prevent it.

Write the record: name in the imperative, the statement, the origin with its Part and observed
failure, the root, the escape route, and the retirement condition.

Assign the enforcement layer honestly. If no mechanism exists, it is layer 5, and writing MANDATORY
beside it does not change that. Then ask whether a lower layer is reachable — a check that could run,
a type that could exclude the violation. The gap between the assigned layer and the reachable layer
is the actionable work.

Name the eval that verifies compliance. A rule with no check is advisory; record it as advisory
rather than as required, so the archive's stated force matches its actual force.

Label the derivation as observed or inferred. Inferred rules are hypotheses and are useful; they are
not evidence, and the archive should be able to report what fraction of itself is which.

Periodically, review the five roots. Do not enumerate the entries. And report the operating subset —
the rules with mechanisms — separately from the reference set, so that nobody mistakes a large
archive for strong governance.

## 15. Integration

Part XXI supplies the roots. Part XXII supplies the traps whose preventive rules populate the
prevention-only subset and which carry elevated priority. Part XXIV supplies the evals field six
requires — a rule without one is advisory by §11. Part XXV consolidates the nineteen gates, which are
this registry's layer-2 population. Part XXVI records the merge relationship with the stack's
existing archive.

Outside the family, the existing hard-rule archive is the provenance model and the compiled digest is
the layer-2 mechanism worth extending. The recommendation is additive: four fields on 156 entries,
which would make the archive's real operating surface visible for the first time.

## 16. Open questions

1. How much semantic overlap exists among the 118? Name-distinctness does not establish behavioural
   distinctness, and the clustering probe of §12 was not run. The honest expectation is that the
   effective rule count is materially lower than 118. — UNKNOWN, and the most likely place this
   family overstates itself.
2. What is the practical ceiling on layer-5 rules before the marginal rule has negative value? Each
   additional doctrine rule dilutes attention across the set, and the point at which addition
   subtracts is unmeasured. — HYPOTHESIS: it is well below 118.
3. Can derivation kind be verified rather than self-declared? An author labelling their own rule
   observed-or-inferred is subject to exactly the self-assessment problem Part XVI describes. —
   UNKNOWN.

## 17. Institutional writeback

Six rule seeds, five eval seeds and one production gate.

Three portable results. **A rule's force is its enforcement layer, not its wording** — and a rule at
layer 5 in mandatory language is advisory in fact, which every archive that lacks the field is
concealing from its readers. **Prefer the lowest layer available**: making a violation unrepresentable
retires the rule rather than enforcing it, and it is the cheapest permanent improvement that exists.
And **a deductively-derived rule is a hypothesis about a failure, not a record of one** — which this
family must say about the majority of its own 118, since an archive that does not separate tested
from untested lets the untested borrow standing it did not earn.

The finding worth acting on: **this stack has better rule provenance and this family has better rule
structure.** Four added fields — layer, root, retirement condition, eval — on an archive that already
carries trigger, action, exception and origin would produce something neither has alone, and would
reveal for the first time how much of a 156-entry corpus actually operates rather than being read.
