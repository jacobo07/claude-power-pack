---
title: "CLAE Part XIX — Evidence-Gated Autonomy"
family: clae
part: XIX
depends_on: [XII, XVIII]
feeds: [XX, XXI, XXV]
status: SEALED
date: 2026-07-26
---

# Part XIX — Evidence-Gated Autonomy

## 1. Purpose

This Part assembles the family. Everything built so far — references, extraction, ranking, cycles,
ledgers, floors, instruments, oracles, deviations — exists to answer one question that no single
Part could answer alone:

> **How does autonomous work proceed without per-step approval and without being unbounded?**

The answer is not *approve less often*. It is a different structure, and the structural move is a
single inversion stated in §3. Everything else in this Part is the consequence of it.

## 2. The two poles

**Per-step approval.** Safe, and it eliminates the value of autonomy — the reviewing capacity
becomes the throughput ceiling. Worse, it degrades: an approver asked to authorize every step stops
reading them. This is Part XVI §5's oracle exhaustion arriving through an approval channel, and it
produces a system that is *formally* supervised and *actually* unsupervised, which is worse than
either pole honestly occupied.

**Unbounded autonomy.** The agent proceeds on its own judgment about its own work, at machine speed.
This is Part I's trap running without friction, and Part XII §7 established why it is worse for
agents than for humans: nothing in immediate feedback distinguishes verified output from unverified,
and the informal model that partially compensates does not survive a session boundary.

Neither pole is a matter of degree from the other. Moving from the first toward the second by
approving less often passes through no safe middle — it simply reduces the supervision without
replacing it.

## 3. The inversion

> **Per-step approval asks: may I do this next thing?**
> **Evidence-gated autonomy asks, once and up front: here is what I will treat as evidence that I
> have done this correctly — do you accept that standard?**

After the standard is accepted, the agent proceeds and **the gate is the evidence, not the human**.

The human's role moves from reviewing outputs to reviewing the **evidence contract**. One judgment
governs many steps, which is precisely Part XVII §5's criterion-over-verdict ladder applied to
autonomy: a verdict on an output resolves one step, a criterion for acceptable evidence resolves
every step of that kind.

This also relocates the human's attention to where their standing actually lies. Whether a step was
done correctly is frequently an instrument question the agent can answer better. Whether a given
kind of evidence *should count* as demonstrating correctness is value-laden and
constituency-dependent — Part XVI's first two marks — and belongs outside the system by
construction.

## 4. The evidence contract

The contract is an assembly of every prior Part's output, which is the payoff of the sequence.

| Component | Source |
|---|---|
| Dimensions in scope, and the measurement-debt register for those out of it | Part XII §8, Part IX §5 |
| A reference per in-scope dimension, with class and direction label | Parts IV, V |
| Extraction level required per dimension | Part VI §3 |
| Floors that must hold, each with its declared escape | Parts X, XI |
| Instruments, with coverage, envelope, perturbation and three-valued output | Part XIII §4, §7 |
| The declared oracle boundary — judgments that will not be self-answered | Part XVI §6 |
| Residual publication obligation at every verdict | Part IX §4 |
| Halt conditions | §6 below |
| Scope: what work this contract covers | §6, and the boundary that matters most |

A contract missing the oracle boundary authorizes self-certification. One missing halt conditions
authorizes unbounded continuation. One missing scope authorizes anything the agent later decides is
related.

## 5. Entry conditions

Four things must be true before autonomy begins. These are not quality improvements; below any of
them, autonomy is unbounded **by construction rather than by degree**.

1. **Phase Zero demonstrated** on the in-scope dimensions — the six capabilities carried end to end
   on at least one, per Part XII. Without observation there is no evidence for the gate to be.
2. **The loop validated** — a first cycle at k = 1 with an explicit verdict, per Part VIII §9. An
   unvalidated loop produces confident numbers from a possibly-broken instrument.
3. **The oracle boundary declared**, per Part XVI §6. Undeclared, every judgment defaults to
   self-answered.
4. **Instruments three-valued**, per Part XIII §7. A two-valued instrument reports failure-to-run as
   a pass, which means the gate can be satisfied by an instrument that did not execute — the single
   most direct way an evidence gate becomes decorative.

## 6. Halt conditions

**A gate that only permits is not a gate.** Autonomy requires declared conditions under which it
stops, and they must be conditions the agent can recognize without judgment, since judgment at the
halt point is exactly what is in question.

- **Seeing-blocker** — the blocker is the ability to observe rather than the work (Part XIV §2).
  Production stops; the instrument is built or the work halts.
- **Null threshold** — consecutive null outcomes on a dimension (Part VIII §7). The instrument, not
  the effort, is the problem.
- **Oracle question with no answer in scope** — a judgment matching one of Part XVI's four marks,
  with no recorded answer covering this artifact and presentation.
- **Floor violated with no available deviation** — per Parts X and XVIII.
- **Residual rising across cycles** — the loop is not converging (Part VIII §7).
- **Contract scope exceeded** — the work has moved outside what the contract covers.

The last is the subtle one and the most consequential.

> **Autonomy is bounded by the contract's scope, and drifting outside it is the commonest way
> autonomy becomes unbounded without anyone deciding to.**

Work naturally extends: an adjacent file, a related dimension, an obvious improvement. Each
extension is reasonable and none is authorized by the accepted standard, because the standard was
accepted against a stated scope. An agent operating outside its contract's scope has no evidence
gate at all — it has the *habits* of one, applied to work nobody agreed they covered.

## 7. Halting is not failing

If a halt is recorded as a failure, the agent's incentive is to avoid halting — and the halt
conditions in §6 are precisely the moments when continuing is most damaging.

> **A halt on a declared condition is a successful outcome of the contract, not a failure of the
> work.**

This is the third time this family has encountered the same structural point. Part XIV §9: a cycle
that builds an instrument must be booked to instrument debt or toolsmithing looks like a wasted
cycle. Part XVIII §3: a deviation read as a discipline failure stops being recorded. Here: a halt
read as a failure stops being taken.

The pattern is general enough to state on its own:

> **The accounting determines the behaviour. An accounting that penalizes the correct action
> reliably produces the incorrect one, without anyone choosing it.**

Halts are therefore recorded with their triggering condition, and a contract's halt count is read as
evidence that its conditions are live — not as a defect rate.

## 8. Evidence quality, not evidence volume

An agent optimizing for an evidence gate will produce evidence. The failure is volume without
checkability: logs nothing parses, records nothing queries, artifacts nobody consumes.

Evidence must be **checkable by the contract**, which means each piece is named in the contract as
satisfying a specific requirement, and something actually evaluates it. Evidence produced outside
that mapping is not part of the gate however voluminous it is.

This is the write-without-read failure this stack has already sealed, arriving in the autonomy layer:
a writer with no reader is a record of intent, not a working system. The test is direct — for each
piece of evidence the agent produces, name what consumes it. Anything unnamed is theatre, and its
production cost is being paid for nothing.

## 9. The trust ratchet must turn both ways

A contract's scope can widen as evidence accumulates. Two constraints.

**Widening is an oracle decision, not an agent one.** Whether accumulated evidence justifies broader
autonomy is value-laden and constituency-dependent. An agent widening its own scope on the strength
of its own record is the self-certification this entire family is organized against, arriving at the
governance layer.

**It must be able to narrow.** A contract that only widens is Part X §6's floor set that only grows,
inverted — an authorization set that only accumulates. Narrowing triggers:

- A halt condition fired that the contract's design implied was impossible.
- A residual was discovered on a dimension outside the contract's scope, meaning the scope was drawn
  wrong.
- An instrument in the contract was found two-valued, meaning some portion of the accumulated
  evidence is uninterpretable.

The third is the one that requires the most discipline, because it retroactively devalues evidence
already banked.

## 10. Boundary

Evidence gates govern **conclusions**. They do not govern **actions** reserved on safety grounds —
the reserved-decision list of Part XVI §10 stays reserved regardless of how much evidence
accumulates, because its reservation was never epistemic. No amount of demonstrated judgment makes
an irreversible action self-authorizable.

They also do not apply where the evidence arrives after the consequence. An action whose correctness
can only be established once it is irreversible cannot be evidence-gated; it can only be reserved.

> **Evidence gates govern what a system may conclude. Reserved decisions govern what it may do. Both
> are necessary and neither substitutes for the other.**

This is Part XVI §10's finding restated as a design constraint: a stack with a strong reserved-decision
list and no evidence contract is unsupervised in its conclusions, and a stack with a strong evidence
contract and no reserved decisions is unsupervised in its actions.

## 11. Evidence — this session as an evidence-gated autonomy run

This build is the most direct available example, and examining it against §4 is more useful than
examining a surface that never attempted it.

**Entry conditions — met.** Phase Zero was demonstrated: the gate script was written and proven on
Part I before Part II was drafted (Part XII §10). The loop was validated: the first Part was sealed
and its gates observed before a second was begun. Pathspec scoping was established and verified
against the first commit's file list.

**Contract components — present but distributed.** The dimensions in scope (contamination, code
fences, coherence, depth), the floors (the word floor, the coherence anchor, pathspec scoping), the
instruments (the four gate checks), the publication obligation (gate results in every commit
message) and the halt conditions ("constitutional contradiction or irreversible risk") all exist.

**The contract was never written as one artifact.** It is distributed across the resumption file, the
index's construction rule, and successive prompts. Nobody could read the standard in one place and
accept or reject it, which is §3's inversion performed informally rather than structurally. It
worked here because the components were stable and the operator was present; that is not the same as
the contract existing.

**Halts — taken correctly.** The trim tool was reported rather than applied when its dry-run cut
nothing and the remaining candidates sat inside critical sections. The generated spec skeleton was
reported rather than filled. The push was withheld pending the Owner's word and taken only when
instructed. Each was a halt on a declared condition, and none was recorded as a failure — which is
§7 satisfied in practice.

**The gap — the instruments are two-valued.** Part XIII §11 found this and named this family's own
gate script in the finding. A check whose pattern silently matched nothing would report clean, and
nothing in the output distinguishes that from a genuine pass. Eighteen Parts have been gated by an
instrument that cannot say *I did not observe*. Under §5's fourth entry condition, this run does not
strictly satisfy its own entry requirements. — OBSERVED from this session's own record; the entry-
condition assessment INFERRED against §5.

That last finding is recorded rather than repaired, for the reason Part XIV §11 gave: repairing the
instrument inside the artifact it gates is circular. It belongs in the completion report as declared
instrument debt, with the Parts it affects named.

## 12. Failure modes

| Failure | Mechanism |
|---|---|
| **Formal supervision** | Per-step approval at a rate that guarantees the approver stops reading |
| **Degrees toward unbounded** | Supervision reduced without being replaced; no safe middle is passed through |
| **Contract without oracle boundary** | Self-certification authorized by an accepted standard |
| **Contract without halt conditions** | A gate that only permits |
| **Contract without scope** | Every adjacent extension implicitly authorized |
| **Scope drift** | Reasonable extensions accumulate until the work is outside the accepted standard |
| **Two-valued gate** | An unexecuted check satisfies the gate; the evidence is decorative |
| **Halt recorded as failure** | The agent's incentive opposes the conditions that protect it |
| **Evidence volume** | Large output nothing consumes; production cost paid for theatre |
| **One-way ratchet** | Scope widens with accumulated evidence and never narrows when evidence is invalidated |
| **Self-widening** | The agent expands its own authorization on the strength of its own record |

## 13. Detection signatures

1. **The unread approval stream.** Approval latency far below reading time. Formal supervision.
2. **The halt-free history.** An autonomous run with no halts over substantial work. Either the
   conditions are not live, or halting is being avoided.
3. **The unlocatable contract.** No single artifact states the accepted standard. It exists as
   habits, which do not survive a change of operator or a session boundary.
4. **The adjacent file.** Work products outside the scope the contract named, arrived at through a
   chain of individually reasonable extensions.
5. **The green two-valued gate.** Any gate in the contract whose instruments cannot report
   could-not-observe. Every clean result it has produced is uninterpretable.
6. **The monotone ratchet.** A scope history that only widens.

## 14. Trap seeds — for Part XXII

- **T-CLAE-FORMAL-SUPERVISION** — per-step approval at a rate that guarantees it is not read,
  producing a system formally supervised and actually unsupervised.
- **T-CLAE-SCOPE-DRIFT** — autonomy extended through individually reasonable adjacencies until the
  work is outside the standard that was accepted.
- **T-CLAE-DECORATIVE-EVIDENCE-GATE** — a gate whose instruments are two-valued, satisfiable by a
  check that did not execute.
- **T-CLAE-HALT-AS-FAILURE** — halts recorded as defects, so the agent's incentive opposes the
  conditions that protect it.
- **T-CLAE-EVIDENCE-VOLUME** — evidence produced in quantity with nothing consuming it, paid for and
  checked by nobody.
- **T-CLAE-SELF-WIDENING-SCOPE** — an agent expanding its own authorization on the strength of its
  own record.

## 15. Rule seeds — for Part XXIII

- **PR-CLAE-CONTRACT-BEFORE-AUTONOMY** — autonomous work begins from a single written evidence
  contract carrying scope, dimensions, references, floors, instruments, oracle boundary, publication
  obligation and halt conditions. A distributed or implicit standard is recorded as absent.
- **PR-CLAE-ENTRY-CONDITIONS** — Phase Zero demonstrated, loop validated, oracle boundary declared,
  instruments three-valued. Below any of these, autonomy is unbounded by construction and is recorded
  as such.
- **PR-CLAE-DECLARED-HALTS** — every contract states conditions under which work stops, recognizable
  without judgment.
- **PR-CLAE-HALT-IS-SUCCESS** — a halt on a declared condition is recorded as a contract outcome.
  Halt counts are read as evidence the conditions are live, never as a defect rate.
- **PR-CLAE-SCOPE-IS-A-BOUNDARY** — work outside the contract's stated scope is not covered by it.
  Extension requires a contract revision, not a judgment that the work is related.
- **PR-CLAE-EVIDENCE-HAS-A-CONSUMER** — each piece of required evidence names what evaluates it.
  Unconsumed evidence is not part of the gate.
- **PR-CLAE-RATCHET-TURNS-BOTH-WAYS** — scope widening is an oracle decision; narrowing is triggered
  by impossible halts, out-of-scope residuals, or instruments found two-valued.

## 16. Eval seeds — for Part XXIV

- **Contract-locatability probe.** Ask for the accepted standard as a single artifact. Failure to
  produce one is the most common finding and the most consequential.
- **Entry-condition probe.** For each autonomous run, verify all four of §5. The instrument arity
  check is expected to fail nearly everywhere, per Part XIII §11.
- **Halt-census probe.** Count halts and their triggering conditions over a run. Zero halts over
  substantial work warrants examining whether the conditions can fire at all.
- **Scope-conformance probe.** Compare work products against the contract's stated scope. Products
  outside it were produced under no gate.
- **Evidence-consumer probe.** For each evidence artifact, name its consumer. Unnamed artifacts are
  volume.
- **Ratchet-direction probe.** Examine the scope history for narrowing events. A monotone history
  means invalidated evidence has never been acted on.

## 17. Production Reality Gate seed — for Part XXV

**Autonomy Entry Gate.** Autonomous work may be recorded as evidence-gated only when a single
written contract exists carrying all §4 components, all four §5 entry conditions are demonstrated
for the in-scope dimensions, halt conditions are stated and recognizable without judgment, and every
required evidence artifact names its consumer. Runs failing any condition are recorded as
unsupervised work — a label applied to their outputs, so the distinction survives into whatever
consumes them, rather than a block.

## 18. Pseudoflow — establishing and running under a contract

Before any autonomous work, write the contract as one artifact. State the scope first and narrowly:
what work this covers, and by implication what it does not. Then the dimensions in scope, and
register the ones out of scope as declared measurement debt rather than omitting them.

For each in-scope dimension, name the reference with its class and direction, the extraction level
required, the instruments with their coverage, envelope and output arity, and the floors that must
hold with their declared escapes.

Declare the oracle boundary: which judgments this run will not self-answer. A contract without this
section authorizes self-certification no matter what else it contains.

Declare the halt conditions, and make each recognizable without judgment — the agent must be able to
identify a halt without exercising the judgment the halt exists to protect.

Verify the four entry conditions before starting. Demonstrate Phase Zero on at least one in-scope
dimension. Run the first cycle at k = 1 and issue its validation verdict. Confirm every instrument
can report could-not-observe; where one cannot, either widen it or record that this run does not
meet its entry conditions and label its outputs accordingly.

Present the contract for acceptance. This is the one oracle question that governs the run, and it
should be asked in Part XVII's window — while the standard can still be changed cheaply.

Then proceed. Publish the residual summary at every verdict. Record halts with their triggering
condition as contract outcomes rather than as defects.

When work approaches the scope boundary, stop and revise the contract rather than deciding the new
work is related. Relatedness is the mechanism by which scope drift happens, and it always feels
reasonable at each step.

At run close, review the ratchet in both directions: what evidence justifies widening, and what
invalidation requires narrowing.

## 19. Integration

This Part consumes nearly the whole family: Part XII's entry condition, Part XIII's arity
requirement, Part XVI's boundary as the contract's central section, Part XVII's routing for the
acceptance question and any in-run oracle traffic, Part XVIII's deviation records as evidence of
judgment, Parts IX and X for publication and floors. Part XX takes the contract as the specification
of what closure means for autonomous work. Part XXI treats scope drift as a failure lineage.

Outside the family, the reserved-decision surfaces are endorsed unchanged and explicitly held
separate: they govern actions, this Part governs conclusions, and §10 states why both are required.

## 20. Open questions

1. Can halt conditions be made recognizable without judgment in general? §6 requires it and the
   scope-exceeded condition in particular seems to need a judgment about relatedness — which is
   exactly the judgment scope drift corrupts. — UNKNOWN, and the weakest link in the Part.
2. How is contract acceptance kept meaningful as contracts grow? A contract assembling every prior
   Part's output is long, and Part XVII §4's wall anti-pattern applies to it: an acceptance decision
   on an artifact too large to read is a ratification. — HYPOTHESIS: the contract needs a summary
   that is itself the object of acceptance, which reintroduces the presentation-bound problem of
   Part XVII §6.
3. Does the ratchet need a horizon? Accumulated evidence justifying a widened scope was gathered
   under conditions that move, and no mechanism currently expires it. — HYPOTHESIS: contracts need
   validity scopes exactly as oracle answers do.

## 21. Institutional writeback

Six trap seeds, seven process-rule seeds, six eval seeds and one production gate.

Three portable results. **The inversion**: approve the evidence contract, not the steps — which moves
the human from reviewing outputs, where an agent often has the advantage, to deciding what should
count as evidence, which is value-laden and belongs outside the system by construction. **Autonomy is
bounded by its contract's scope**, and drift across that boundary through individually reasonable
adjacencies is the commonest way autonomy becomes unbounded with nobody deciding to. And the general
form of a pattern this family has now hit three times: **the accounting determines the behaviour** —
an accounting that penalizes the correct action produces the incorrect one, without anyone choosing
it, which is why halts, deviations and instrument-building must each be booked as outcomes rather
than as failures.

The self-assessment in §11 is the Part's own demonstration in both directions: this run met its entry
conditions on observation and loop validation, halted correctly three times on declared conditions —
and gated eighteen Parts with an instrument that cannot report that it did not run.
