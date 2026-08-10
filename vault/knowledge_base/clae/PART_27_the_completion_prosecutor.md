---
title: "CLAE Part 27 — The Completion Prosecutor"
family: clae
part: 27
depends_on: [I, XIII, XVI, XVII, XIX, XX, XXIV]
feeds: [28, 29, 30]
status: SEALED
date: 2026-08-10
---

# Part 27 — The Completion Prosecutor

## 1. Purpose

Part XVI established that a system cannot verify certain properties about itself. Part XX
established that a producer closes the *accounting* and a constituency *accepts* it. Between
those two results sits a hole this family named and did not fill: **CLAE's own acceptance
line is empty because no constituency existed to sign it.**

This Part specifies the party that would sign it. Not a reviewer, not a second opinion, and
not a more careful executor — a third authority whose success criterion is the opposite of
the executor's, whose independence is structural rather than declared, and which is itself an
instrument subject to Part XIII in full.

The Part answers four questions the role cannot operate without: what makes its independence
real rather than theatrical (§4), what it argues *against* so it does not become an unbounded
critic (§5), what happens when it and the executor cannot converge (§8), and how a prosecutor
that passes broken work is detected (§9).

## 2. The institutional problem

The executor may investigate, plan, modify, repair, run tests and gather evidence. Every one
of those is legitimate and none is in question. The defect is in the last step only:

> **The party that produced the work also grants it the final state.**

This is Part I's internal-bar trap moved from the criterion to the verdict. Part I showed a
system authoring the bar it is measured against; this is the same closure one level up, where
the system authors the *judgment* that the bar was met. The evidence may be genuine, the
tests may pass, and the conclusion still inherits the producer's blind spot — because the
question "is there something I did not check?" is precisely the question a producer is worst
positioned to answer, and it is the only question that matters at closure.

The consequence is not that executors lie. It is that an executor's honest, careful,
well-evidenced closure and a defective one **are the same artifact from the outside**. Nothing
in the record distinguishes them, so a reader must trust the producer's self-assessment or
re-do the work. — Mechanism INFERRED from Parts I and XVI; the empty acceptance line of
Part XXVI §5 is the OBSERVED instance in this family.

## 3. Three authorities

| Authority | Succeeds when | Reads | May grant closure |
|---|---|---|---|
| **Executor** | the mission is delivered | its own plan, the artifacts, its tests | **No** — may only *request* closure |
| **Completion Prosecutor** | it demonstrates the work is **not** finished | the artifacts and the runtime, not the executor's summary | No |
| **Completion Arbiter** | a defensible verdict is issued | the executor's closure pack and the prosecutor's objections | **Yes** |

The prosecutor searches a specific list, and the list is what makes the role mechanical rather
than a matter of diligence: contradictions · assumptions · uninspected surfaces · alternative
routes · residues · duplicated capability · circular results · weak tests · false negatives ·
divergence between declared files and actual runtime.

Eight of those ten are traps this family already registered. The prosecutor is therefore not a
new source of judgment — it is `CLAE_TRAPS.md` given standing and pointed at one closure.

> **The executor never writes "everything is finished". It may only submit a closure request.**

That single restriction is the whole reform, and it is a **layer-1 move** in Part XXIII §4's
sense: the executor's output type stops containing a terminal verdict, so self-certification
becomes unrepresentable rather than forbidden. A rule saying "do not self-certify" is layer 5
and depends on recall. Removing the verdict from the producer's vocabulary cannot be violated.

## 4. Independence — four conditions, none of them declarative

Independence is claimed far more often than it holds. It is real only when all four of these
are true, and each fails silently on its own.

1. **Separate evidence access.** The prosecutor reads the artifacts, the filesystem and the
   runtime directly. A prosecutor that reads the executor's *summary* of the evidence is
   auditing a narrative, and inherits every omission in it. The summary is the thing under
   challenge, not the input to the challenge.
2. **Opposite success criterion.** The prosecutor is credited for sustained objections, not
   for agreeing. Part XVIII §4 established that a zero deviation rate is a broken record; the
   same logic applies here with more force, because an accounting that rewards agreement
   produces agreement.
3. **No shared state with the plan.** If the prosecutor's checklist is derived from the
   executor's plan, then work the plan never contemplated is invisible to both. The
   prosecutor's coverage must be anchored to the *domain*, per §5, not to the executor's map
   of it. This is Part XIII §9's chain-coverage result: coverage of a composition is the
   intersection of its members', and a prosecutor sharing the executor's blind spot adds
   nothing to the intersection.
4. **Objections survive the reply.** An objection is recorded, and the party objected to
   cannot close it. The executor may *repair* it or *contest* it; only the arbiter resolves
   it. Where the objected-to party may mark an objection resolved, the record converges on
   silence — which is Part XVIII §10's suppressed-ledger failure arriving at closure.

Condition 4 is the one most often lost in practice, because it looks like efficiency. — All
four INFERRED from the named prior Parts; none has been operated here.

## 5. Anchoring — what the prosecutor argues against

An unanchored prosecutor is worse than none. It generates unbounded objections, the objections
cannot be discharged, and the role is disabled within a few cycles for obstructing delivery —
after which the system has a *disabled* control and believes it has a control. Part VII §8's
starvation result predicts this exactly.

The prosecutor argues against **three declared things, and nothing else**:

| Anchor | Source | An objection is admissible when it names |
|---|---|---|
| The mission's declared intent | the closure pack | a stated objective that the evidence does not reach |
| The external reference | Part IV | a delta to the reference that the closure did not record |
| The registered failure set | `CLAE_TRAPS.md`, `CLAE_PROCESS_RULES.md` | a specific registered trap or rule the work exhibits |

An objection outside all three anchors — *"this could be better"*, *"I would have done it
differently"* — is **inadmissible by construction**. It is not overruled by the arbiter; it
never reaches the arbiter, because it names no anchor.

> **A prosecutor bounded by declared anchors is a control. A prosecutor bounded by taste is a
> veto with no retirement condition.**

This is also what makes the role automatable in principle: all three anchors are documents,
and an objection that must cite one of them is a check rather than an opinion.

## 6. The closure state machine

Thirteen states. The mechanism is that no state may be skipped, so the machine's value is in
the transitions it *forbids* rather than the ones it permits.

| State | Meaning |
|---|---|
| `IN_PROGRESS` | the mission is still executing |
| `CHANGE_FROZEN` | changes stop so the result can be audited |
| `EVIDENCE_INCOMPLETE` | mandatory proofs are missing |
| `READY_FOR_CHALLENGE` | the executor has submitted its closure pack |
| `ADVERSARIAL_REVIEW` | defects and omissions are being sought |
| `REPAIR_REQUIRED` | a self-repairable fault was found |
| `OWNER_GATE` | a human decision or action is required |
| `REALITY_VERIFICATION` | effective behaviour is being tested |
| `IMMUNIZATION_REQUIRED` | the fix works but does not prevent recurrence |
| `CLOSURE_CANDIDATE` | all principal gates have passed |
| `DONE_VERIFIED` | closure granted |
| `PARTIAL_VERIFIED` | only part of the work is demonstrated |
| `BLOCKED` | no safe route to completion exists |

Three properties carry the machine, and each is a mechanism rather than a label:

**`CHANGE_FROZEN` precedes evidence.** Evidence gathered while the artifact is still moving
describes a state that no longer exists. Part 28 develops the freeze; here it matters only
that it sits *before* `READY_FOR_CHALLENGE`, so the prosecutor and the executor are looking at
the same artifact.

**`IMMUNIZATION_REQUIRED` is a state, not an afterthought.** A working fix that does not
prevent recurrence cannot reach `CLOSURE_CANDIDATE`. This is the transition that converts
Part 30's failure-to-immunity work from good practice into a blocking condition.

**A single `BLOCKED` prevents closure, and the blocking conditions are already registered.**
An absent reference, a branch with no fallback, an unvalidated input, or an unresolved marker
of incomplete work each block delivery. So does the weaker and more common case: **an existing
file is not proof of function.** — Blocking conditions OBSERVED in this stack's existing rule
surfaces; their placement in this machine INFERRED.

## 7. Why the machine needs the role, and not the reverse

A state machine with no independent occupant is a naming scheme. Any of these thirteen states
can be entered, exited and reported by the executor alone, and the resulting trace looks
identical to a governed one.

The states that are *load-bearing* are exactly those the executor cannot self-serve:
`ADVERSARIAL_REVIEW` requires a party whose success is refutation, and `DONE_VERIFIED` requires
a party that is neither producer nor challenger. Remove the three authorities and the machine
degrades to a progress bar — which is the shape most closure workflows already have.

## 8. Deadlock

Two parties with opposed success criteria will not always converge. Three deadlock shapes, with
the resolution each requires:

| Shape | Mechanism | Resolution |
|---|---|---|
| **Objection treadmill** | each repair exposes an adjacent objection; the work never stabilises | the objection budget of Part 29 §20's review bound; exhaustion routes to the arbiter, not to closure |
| **Unfalsifiable objection** | the objection names an anchor but no check that could discharge it | inadmissible — an objection must state what evidence would settle it, or it is not an objection |
| **Arbiter absent** | no third party exists, so the two parties must agree | the state is `OWNER_GATE`, not `DONE_VERIFIED`. A deadlock with no arbiter is an oracle question, per Part XVII |

The second row is the important one and it is symmetrical with §5. An objection must carry its
own discharge condition — *what would have to be true for this to be answered*. Without it the
prosecutor holds an unbounded veto, and Part XI §6's rule applies: a criterion that cannot be
falsified is not a criterion.

> **Deadlock is not a failure of the design. It is the design refusing to convert an unresolved
> disagreement into a verdict**, which is exactly what a single self-certifying party does
> automatically and invisibly.

## 9. False acquittal — the prosecutor is an instrument

The failure mode that matters most is not the prosecutor that objects too much. It is the one
that passes work which is broken, because that failure is silent and it *manufactures*
confidence rather than merely failing to add any.

Part XXIV §5 gives the detection directly, and it applies to this role without modification:

> **A prosecutor that has never sustained an objection is indistinguishable from a prosecutor
> that cannot.**

So the role inherits all of Part XIII. It is an instrument, and it declares what every
instrument declares:

- **Coverage** — which of the ten search classes of §3 it actually exercised, and which it did
  not. A prosecutor reporting "no objections" without a coverage statement has reported
  nothing, per Part II's zero-without-coverage result.
- **Three-valued output** — `SUSTAINED` · `NOT_SUSTAINED` · `COULD_NOT_ASSESS`. The third value
  is the whole point: a prosecutor unable to reach the runtime must be able to say so, rather
  than returning no-objections and having that read as a pass. Making the arity three-valued is
  the second **layer-1 move** in this Part.
- **A negative control** — a known-defective closure pack the prosecutor is periodically run
  against. If it does not reject that pack, its clean verdicts carry no information, and every
  closure it has approved is retroactively uninterpretable — Part XXII §5's fourth
  prevention-only trap, arriving in the acceptance record.

The negative control is cheap and almost never built. It is the single highest-value item in
this Part. — Framing INFERRED from Parts XIII and XXIV; Part XXIV §9 is the one OBSERVED
instance of a negative control actually being run in this family.

## 10. The Completion Certificate

Only the arbiter may issue one. It is structured, and its structure is what makes a closure
auditable after the session that produced it has ended.

| Block | Contents |
|---|---|
| **Mission closure** | objective satisfied · final scope · deviations from plan · changes made |
| **Current-state proof** | filesystem · manifest · artifacts · versions · hashes · runtime · configuration · dependencies |
| **Positive proof** | what is required is present · loads · works · persists · survives restart |
| **Negative proof** | what is prohibited is absent · what was withdrawn is unreachable · no aliases remain · no active residues remain · no duplicated owners remain |
| **Drift coverage** | macroclasses evaluated · not applicable · **not evaluated, with the reason** |
| **Unknowns** | remaining uncertainties · impact · containment · owner · resolution date |
| **Immunization** | tests · gates · detectors · candidate rules · template corrections · sibling audits |
| **Reality Gate** | environment · date · evidence · result · limitations |
| **Verdict** | one and only one |

Two blocks deserve emphasis because they are the ones a conventional completion report omits.

**Negative proof** is the half that positive testing structurally cannot supply. "The feature
works" and "the withdrawn thing is unreachable" are different claims requiring different
evidence, and only the first is produced by the tests an executor naturally writes. Part 28
develops negative proof as a first-class obligation.

**Drift coverage's third row** — *not evaluated, and why* — is Part IX's measurement debt with
a mandatory field. A certificate listing only what was evaluated is the measurement-debt-
invisible trap in certificate form.

The **Unknowns** block is the one that keeps this from being a compliance artifact: it carries
an owner and a date, which converts an uncertainty from a caveat into a tracked object.

## 11. Verdict vocabulary — the alias table

The source vocabulary and this family's are not the same set, and they are not merged. **CLAE's
five closure verdicts, defined in Part XX §4, remain authoritative.** The operational states are
recorded as a presentation alias so that a certificate written in either vocabulary can be read
in the other.

| Certificate verdict | CLAE closure verdict (Part XX) | Note |
|---|---|---|
| `DONE_VERIFIED` | **Complete** | the only alias that is a clean one-to-one |
| `PARTIAL_VERIFIED` | **Complete with residual** | the residual is the undemonstrated part, and must be named |
| `DONE_WITH_ACCEPTED_EXCEPTION` | **Complete with deviation** | requires Part XVIII's proven constraint and measured loss |
| `OWNER_GATE` | **Halted** | a declared halt awaiting an oracle, per Part XVII — not a failure, per Part XIX §6 |
| `BLOCKED` | **Halted** | same verdict, different cause: no safe route rather than a pending answer |
| `FAILED` | **Halted** | see below |

Three findings fall out of building this table, and none was visible before it was built:

1. **The source's two verdict lists disagree with each other.** Its §1 gives the arbiter six
   outcomes including `DONE_WITH_ACCEPTED_EXCEPTION`; its §17 gives the certificate five,
   dropping that one and adding `BLOCKED` and `FAILED`. A closure vocabulary that differs
   between the deciding step and the recording step is Part XX §2's done-collapse in its
   earliest form. — OBSERVED directly in the source text.
2. **Three operational states collapse to one CLAE verdict.** `OWNER_GATE`, `BLOCKED` and
   `FAILED` are all *Halted*. That is not a defect in either vocabulary: the operational states
   distinguish *what to do next*, while the closure verdicts distinguish *what was accounted
   for*. They answer different questions and a system needs both. The alias table is the
   mapping, not a replacement.
3. **CLAE has no verdict meaning "failed".** All five of Part XX's verdicts are accounting
   states; none asserts that the work was bad. `FAILED` maps to *Halted* with the loss recorded,
   because in this family a stopped mission with an honest account is not a lesser outcome than
   a completed one — Part XIX §6, halting is not failing.

**`Reduced`**, Part XX's fifth verdict, has no operational alias at all. Nothing in the source's
state machine expresses "the scope was narrowed and the narrower scope was completed". That is a
gap in the operational vocabulary, not in CLAE's. — INFERRED by exhaustion over both lists.

## 12. Evidence — this family is the instance

CLAE closed at 26 Parts with the verdict *complete with residual* and, in Part XXVI §5's words,
**"Acceptance line: empty."** The reason recorded there is that the producer closes the
accounting and a constituency accepts, and no constituency existed.

Part XXVI §9 records the same shape from the other side: *"Judgments self-answered versus
oracle-answered: almost all self-answered… Every quality judgment about this family's own
content was made by its author."* One oracle question was routed in twenty-six Parts.

So the family that wrote Part XVI's self-verification limit spent twenty-six Parts operating
inside it, said so, and could not do otherwise — there was no third authority to route to.
**This Part specifies the missing authority, and it does not thereby fill the acceptance line.**
The line is filled by a constituency accepting, not by a producer specifying who could have.

That distinction is the reason this Part can be written by its own subject without circularity:
writing the charter of a role is not occupying it. — Both quotations OBSERVED in Part XXVI.

## 13. Boundary — what this Part does not claim

- It does not claim the prosecutor must be a different *system*. Different **standing**,
  **evidence access** and **success criterion** are the requirements; whether that is a person,
  a separate agent or a separately-invoked pass is an implementation choice this Part does not
  make.
- It does not claim three authorities are always warranted. The cost is real and Part 29 §20
  bounds it. For work whose failure is cheap and visible, a self-closed accounting with a
  published residual is proportionate.
- It does not define the passes the prosecutor runs. That is Part 28.
- It does not make the arbiter human. The arbiter must be *neither producer nor challenger*;
  Part XVI's four marks decide when it must additionally be a human oracle.

## 14. Failure modes

| Failure | Mechanism |
|---|---|
| **Prosecutor reads the summary** | audits a narrative; inherits every omission in it |
| **Prosecutor rewarded for agreement** | the accounting produces the verdict it pays for |
| **Checklist derived from the plan** | shares the executor's blind spot; adds nothing to the coverage intersection |
| **Objected-to party closes the objection** | the ledger converges on silence |
| **Unanchored objections** | unbounded veto; the role is disabled for obstructing delivery and the system keeps the disabled control |
| **Objection with no discharge condition** | cannot be answered, only outlasted |
| **Two-valued prosecutor** | inability to assess is reported as no-objections |
| **No negative control** | clean verdicts carry no information and prior approvals become uninterpretable |
| **Arbiter is the executor** | the entire structure reduces to self-certification with extra states |
| **Certificate without the not-evaluated row** | measurement debt made invisible at the moment it matters most |

## 15. Detection signatures

1. **The unbroken approval record.** A prosecutor with no sustained objection in its history.
   The cheapest check in this Part, and it invalidates everything beneath it.
2. **Objections that never name an anchor.** Read ten objections; count how many cite an
   intent, a reference delta or a registered trap. A low ratio predicts the role's disablement.
3. **Closure packs with no negative proof.** Positive tests only. The withdrawn thing was never
   checked for unreachability.
4. **Certificates whose drift-coverage block has two rows.** Evaluated and not-applicable, with
   not-evaluated silently absent.
5. **`DONE_VERIFIED` reached without passing through `IMMUNIZATION_REQUIRED` or an explicit
   determination that it does not apply.** A skipped state in a machine that forbids skipping.

## 16. Trap seeds — for Part XXII

- **T-CLAE-SELF-GRANTED-CLOSURE** — the producing party writes the terminal verdict, so a
  careful closure and a defective one are the same artifact from outside.
- **T-CLAE-PROSECUTOR-READS-THE-SUMMARY** — the challenge is run against the executor's account
  of the evidence rather than the evidence, inheriting its omissions.
- **T-CLAE-AGREEMENT-REWARDED** — the accounting credits the prosecutor for concurrence, and the
  role produces the concurrence it is paid for.
- **T-CLAE-UNANCHORED-OBJECTION** — objections bounded by taste rather than by declared intent,
  reference or registered failure; the role is disabled and its absence is not noticed.
- **T-CLAE-OBJECTION-WITHOUT-DISCHARGE** — an objection that states no condition which would
  settle it, converting review into attrition.
- **T-CLAE-ACQUITTAL-WITHOUT-CONTROL** — a prosecutor never shown capable of rejecting, whose
  entire approval history is therefore uninterpretable.

## 17. Rule seeds — for Part XXIII

- **PR-CLAE-EXECUTOR-REQUESTS-NEVER-GRANTS** — the executing party's output vocabulary does not
  contain a terminal verdict; it may submit a closure request only.
- **PR-CLAE-PROSECUTOR-READS-PRIMARY-EVIDENCE** — the challenge is run against artifacts,
  filesystem and runtime, never against the closure summary.
- **PR-CLAE-ANCHOR-EVERY-OBJECTION** — an admissible objection cites a declared intent, a
  reference delta, or a registered trap or rule.
- **PR-CLAE-OBJECTION-CARRIES-ITS-DISCHARGE** — every objection states what evidence would
  settle it; one that cannot is not recorded as an objection.
- **PR-CLAE-ONLY-THE-ARBITER-CLOSES-AN-OBJECTION** — the party objected to may repair or
  contest, never resolve.
- **PR-CLAE-PROSECUTOR-IS-THREE-VALUED** — the role reports could-not-assess as a distinct
  outcome from no-objections.
- **PR-CLAE-CERTIFICATE-CARRIES-NOT-EVALUATED** — drift coverage records what was not assessed
  and why, alongside what was.

## 18. Eval seeds — for Part XXIV

- **Negative-control acquittal probe.** Submit a known-defective closure pack. A prosecutor
  that approves it has been shown to be decorative, and every prior approval is void.
- **Anchor-citation census.** Over a period, what fraction of objections cite one of the three
  anchors? The uncited fraction predicts the role's disablement.
- **Summary-dependence probe.** Withhold the executor's summary and re-run the challenge. A
  materially different objection set means the prosecutor was auditing the narrative.
- **Arity probe.** Deny the prosecutor runtime access and observe the output. If it reports
  no-objections rather than could-not-assess, it is two-valued.
- **State-skip probe.** Walk closure traces and count transitions into `DONE_VERIFIED` whose
  predecessor was not `CLOSURE_CANDIDATE`.
- **Alias-collision probe.** Read certificates and check that each verdict maps to exactly one
  Part XX verdict, and that `Reduced` closures are not being recorded as `PARTIAL_VERIFIED`.

## 19. Production Reality Gate seed — for Part XXV

**Completion Authority Gate.** A closure may be described as *accepted* only when the granting
party is neither the producer nor the challenger, the prosecutor's coverage statement is
attached, the prosecutor has a negative control with a recorded rejection inside its validity
window, every sustained objection is resolved by the arbiter rather than by the objected-to
party, and the certificate carries a not-evaluated row. Closures failing this are recorded as
**self-closed accountings** — a legitimate artifact, correctly labelled — rather than as
accepted work.

## 20. Pseudoflow — one closure

The executor freezes changes and submits a closure pack: intent, evidence, deltas, residual,
and the states it believes it has satisfied. It does not write a verdict, because its output
type does not have one.

The prosecutor reads the artifacts and the runtime — not the pack's narrative — and works the
ten search classes of §3, recording coverage for each: exercised, or not, with a reason. For
each finding it writes an objection naming an anchor and the evidence that would discharge it.
If it cannot reach a surface, it emits could-not-assess for that class rather than silence.

The executor repairs or contests. It does not close anything.

The arbiter reads the pack and the objections and issues one verdict from §11's left column,
mapped to one Part XX verdict. If no arbiter exists, the state is `OWNER_GATE` and the question
is routed per Part XVII with a criterion attached, not a request for approval.

Periodically, and independently of any mission, the negative control runs. If the prosecutor
fails to reject the known-defective pack, closures approved since its last passing control are
relabelled self-closed accountings — because that is what they have been shown to be.

## 21. Integration

Part I supplies the internal-bar trap this Part moves to the verdict. Part XIII makes the
prosecutor an instrument, which is where its coverage, arity and negative-control obligations
come from. Part XVI decides when the arbiter must be a human oracle and Part XVII routes the
question when it is. Part XIX §6 supplies halting-is-not-failing, without which `OWNER_GATE`
and `BLOCKED` are recorded as defects and the role is punished for working. Part XX supplies
the five authoritative verdicts and the producer-closes-constituency-accepts rule this Part
implements. Part XXIV supplies the negative control.

Forward: Part 28 takes the freeze and the adversarial passes; Part 29 takes the objection budget
and the repair loop; Part 30 takes the immunization state.

Outside the family, this stack's handoff block is the nearest existing closure instrument, and
the relationship is additive: it already carries a status enumeration and a debt line, and what
it lacks is a granting party distinct from its author.

## 22. Open questions

1. Can a prosecutor and an executor implemented as the same model with different prompts satisfy
   §4's four conditions? Conditions 1, 2 and 4 appear satisfiable by construction; condition 3 —
   not sharing the plan's blind spot — is the doubtful one, and it is the condition that
   determines whether the coverage intersection actually grows. — HYPOTHESIS, and the question
   that decides whether this Part is cheap or expensive to adopt.
2. What is the correct validity window for a negative control? Too long and a prosecutor decays
   undetected between runs; too short and the control dominates the cost. Part V's horizon
   machinery applies but the period is unmeasured. — UNKNOWN.
3. Does an arbiter need its own negative control? It is a third instrument making a decision, so
   Part XIII says yes; but its output is a judgment over two evidence sets rather than an
   observation, and this family has not established what a known-answer case looks like for a
   judgment. — UNKNOWN.

## 23. Institutional writeback

Six trap seeds, seven rule seeds, six eval seeds, one production gate.

Three portable results. **Remove the verdict from the producer's vocabulary** — self-certification
is best stopped by making it unrepresentable rather than forbidding it, which is the cheapest
permanent control this family has found twice now. **An objection must carry its own discharge
condition**, or review becomes attrition and the control is disabled for obstructing delivery
rather than for being wrong. And **a prosecutor is an instrument**, so the question "has it ever
rejected anything?" is not a performance metric but a validity precondition: without a recorded
rejection, its entire approval history carries no information.

The structural finding: **this family is an instance of the gap this Part closes.** CLAE's
acceptance line is empty because no constituency existed to sign it, and Part 27 specifies that
constituency. Writing the specification does not fill the line — a producer specifying who could
accept its work has not thereby had it accepted — and that distinction is the difference between
documenting the mechanism and performing the defect it names.
