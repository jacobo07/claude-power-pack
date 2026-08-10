---
title: "CLAE Part 29 — Cognitive Precursors and the Same-Session Repair Loop"
family: clae
part: 29
depends_on: [I, IX, XIII, XV, XVIII, XIX, XXIV, 27, 28]
feeds: [30]
status: SEALED
date: 2026-08-10
---

# Part 29 — Cognitive Precursors and the Same-Session Repair Loop

## 1. Purpose

Parts 27 and 28 detect defects **at closure**. This Part detects the conditions that produce them
**during the session**, and disposes of what the challenge finds instead of listing it.

Three mechanisms, in the order they operate:

- **Preflight and the evidence ledger** (§2–§4) — what must be read before a capability is
  touched, and how every material claim carries its epistemic state so that an inference cannot
  quietly become a fact.
- **The ten precursors** (§5–§7) — behaviours that reliably precede defects, detected while they
  are still cheap.
- **The repair loop and its budget** (§8–§12) — a finding is classified and disposed of in the
  same session, and the review terminates on a stated condition rather than on fatigue.

The Part's organising claim is that closure-time detection is necessary and insufficient. A
defect found at closure has already been paid for; a precursor caught mid-session costs the
correction only. Part XV made this argument for incidents — an incident is a free known-answer
case with a short expiry — and this Part makes it one step earlier, for the behaviour that
produces the incident.

## 2. Preflight

Before modifying a capability, seven surfaces are read:

**current owner · consumers · configuration · tests · manifest · historical decision · equivalent
implementation.**

Six of the seven are conventional. The seventh — *equivalent implementation* — is the one that
prevents the most expensive class of error, because it asks whether the capability being modified
already exists elsewhere. Part XXVI's integration map exists because that question was asked at
compendium scale and answered *yes* for roughly 55–60% of a corpus's proposals.

The sixth, *historical decision*, is the temporal counterpart: a surface may be exactly as it
should be because a decision made it so, and modifying it re-opens a question that was already
settled. Reading the artifact tells you what it is; only the decision record tells you whether
that is deliberate.

> **Preflight is not diligence. It is the positive form of precursor 2**, and it is the only one
> of the ten that can be enforced before the fact rather than detected after it.

## 3. The Session Evidence Ledger

A narrative summary and a command history are both records of *activity*. Neither is a record of
**what is believed and why**, which is the thing a closure needs.

Every material claim is registered with eleven fields:

| Field | What it prevents |
|---|---|
| claim | — |
| **epistemic state** | an inference hardening into a fact |
| evidence | an unsupported assertion |
| provenance | evidence whose origin cannot be re-checked |
| files consulted | an unbounded implied search |
| **files not consulted** | a search whose gaps are invisible |
| associated assumption | a dependency nobody can see to invalidate |
| **consumer of the claim** | a wrong claim propagating with nothing to notify |
| risk if false | uniform treatment of claims with very different blast radii |
| verification required | an open claim with no route to closure |
| actual result | a verification that was planned and never run |

Three fields carry most of the value and all three are unusual.

**Files not consulted** is Part IX's measurement debt at the level of a single claim. A claim
supported by four files read is not interpretable without knowing whether four of five or four of
forty were read.

**Consumer of the claim** turns the ledger from a record into a graph. When a claim is later
refuted, its consumers are enumerable, and everything downstream can be re-examined rather than
silently inheriting the correction. Without this field a refutation repairs one belief and leaves
its descendants standing.

**Risk if false** is what makes §12's budget assignable. It is the per-claim analogue of Part VII's
impact ranking, and it is why not every claim needs the same verification.

### 3.1 The six epistemic states

`VERIFIED` · `OBSERVED` · `INFERRED` · `HYPOTHESIS` · `UNKNOWN` · `REJECTED`.

These are the same six this family already applies to its own claims, named in the charter. The
ledger is therefore not a new vocabulary — it is **the artifact CLAE's existing vocabulary was
missing**. Part XIX §11 recorded exactly this gap in the family's own construction: *"the evidence
contract was distributed rather than written as one artifact."* Every Part labels its claims; no
Part collects them. §3 is the collection. — Convergence OBSERVED between the source's ledger and
this family's charter.

## 4. The law of epistemic closure

A critical claim may not remain `INFERRED` or `HYPOTHESIS` at closure. It must be raised to
`VERIFIED` or `OBSERVED` by evidence, lowered to `REJECTED`, or **explicitly carried as `UNKNOWN`
with its risk, containment and owner** — which is Part 27's certificate `Unknowns` block.

The law's force comes from what it forbids: the *silent* path where a claim enters as an inference,
is acted on, and is reported without its state. That is not a lie and nobody notices it happening.
It is the mechanism by which a closure becomes confidently wrong, and the ledger's epistemic-state
field is the only thing standing in front of it.

> **An inference is a legitimate basis for action and an illegitimate basis for a completion
> claim.** The ledger is what keeps those two uses of the same belief distinguishable.

## 5. The ten cognitive precursors

Behaviours that precede defects. Each is observable *while it happens*, which is what makes them
useful — a defect is detected after it exists, a precursor before.

| # | Precursor | Signature |
|---|---|---|
| 1 | **Undue promotion of uncertainty** | hedged language — *probably*, *seems*, *should*, *surely* — followed by implementation that treats the hedge as settled |
| 2 | **Critical surface not inspected** | a capability modified without reading the seven surfaces of §2 |
| 3 | **Fix before reproduction** | a correction introduced before the failure, its route, its cause and the expected behaviour are demonstrated |
| 4 | **Patch stacking** | a second or third patch on the same region without updating the causal model |
| 5 | **Build-as-done** | a successful compilation used as proof of behaviour |
| 6 | **Test adaptation** | a test fails and is changed to accept the implementation, without demonstrating the test was wrong |
| 7 | **Circular oracle** | the test relies on the same assumption as the implementation |
| 8 | **Reporting instead of repairing** | a self-repairable defect discovered and left as a note for later |
| 9 | **Depth collapse under context exhaustion** | as the session nears its limit, sibling searches, negative tests, rollback review, manual validation and log reading disappear |
| 10 | **Premature narrative closure** | the final report is drafted before the gates finish |

Precursor 1 is the cheapest to detect and the most predictive: the hedge is *right there in the
text*, and the defect is that the next paragraph proceeds as though it were not.

Precursor 5 is this stack's most-recorded failure class in its own governance surfaces — a
compilation demonstrates that the code is well-formed, and well-formedness is not behaviour. —
The precursor set is OBSERVED in the source; that this stack's rule surfaces independently name
build-as-done, unread critical files, workaround-before-root-cause, accumulated fixes and
unexercised production reality is OBSERVED in those surfaces.

## 6. The three that are not carelessness

Precursors 4, 6 and 7 deserve separate treatment because each is a *reasonable-looking local
decision* whose defect is structural. Carelessness is not the mechanism, and telling people to be
careful does not address any of them.

**Patch stacking.** The first patch encoded a causal model. When it does not work, the honest
inference is that the model is wrong — but the cheap action is another patch in the same region,
which encodes the *same* model with a wider net. Each patch raises the cost of revisiting the
model, because more behaviour now depends on it. The failure is not the second patch; it is that
the second patch is applied *without the model being reopened*, which makes the third one nearly
inevitable.

> **The signature is a region with several corrections and no revised explanation.**

**Test adaptation.** A failing test is evidence, and changing it converts evidence into agreement.
The test may well be wrong — tests encode assumptions and assumptions expire, per Part V. The
defect is the *order*: the test is changed first and justified afterwards, if at all. The rule is
narrow and cheap: a test may be changed only after demonstrating what was wrong with it, and the
demonstration is recorded as a claim in the ledger with its own epistemic state.

**Circular oracle.** The test relies on the same assumption as the implementation, so it cannot
fail for the reason it exists to detect. The source's example is exact: the implementation
presupposes that a directory is not consumed, and the test checks only that the directory is absent
from a list the implementation itself declares. The test passes. It has verified that the code is
self-consistent, which was never in doubt.

This is Part I's internal-bar trap at test scale, and it is the reason Part XXIV requires a negative
control: a test that cannot fail and a test that passes are the same observation. A sibling
compendium in this Owner's estate reached the identical shape independently, from comparing a
manifest against the system that generated it — **a comparison whose two sides share an origin
certifies rather than checks**. Two arrivals from unrelated directions is the strongest evidence
this family has that the mechanism is general. — Source example OBSERVED; the independent arrival
OBSERVED in the estate governance compendium.

## 7. Detection response — warn or block

Precursors are not equally actionable, and a system that blocks on all ten will be disabled.

| Response | Applies when | Precursors |
|---|---|---|
| **Warn** | the behaviour is often legitimate; the signal is a prior, not a verdict | 1, 3, 8, 10 |
| **Block** | the behaviour invalidates evidence already gathered | 5, 6, 7 |
| **Require a recorded justification** | legitimate but must not be invisible | 2, 4 |
| **Degrade the closure claim** | the detector itself is compromised | 9 |

The blocking three share a property: each **produces a false pass**. Build-as-done, test adaptation
and circular oracle all end with a green result that means nothing, and a green result that means
nothing is worse than a red one because it terminates the search. Warning on those is insufficient,
since the warning arrives attached to a success.

Row 4 is the subject of §8.

## 8. Precursor 9 is different in kind

Nine of the ten are behaviours. The tenth — depth collapse under context exhaustion — is a
**condition that raises the probability of the other nine**, and it does so precisely when the
capacity to notice them is lowest.

The disappearing behaviours are named and they are not random: sibling searches, negative tests,
rollback review, manual validation, log reading. Every one is **expensive, optional-feeling and
externally invisible**. Nothing fails when they are skipped. The work continues to look identical
from outside, which is what makes this the precursor that most needs a mechanical detector rather
than self-awareness — self-awareness is the resource being exhausted.

Its interaction with the others is direct: skipping sibling searches is precursor 2 at estate
scale; skipping negative tests removes Pass C from Part 28; drafting the report early is precursor
10, and a session under pressure has every incentive to start it.

> **A closure produced in the last decile of a session's capacity is not comparable to one produced
> in the first**, and nothing in the artifact records which it was.

The correct response is not to block — the session must be able to end — but to **degrade the
claim**: a closure completed under exhaustion is recorded as such, so a reader can weigh it. The
alternative, which is what happens today, is that both closures present identically. This Part
does not resolve how exhaustion is measured; §17 records the doubt. — Mechanism INFERRED; the
behaviour list is OBSERVED in the source.

## 9. The same-session repair loop

When the prosecutor sustains a finding, the session does **not** end with *"I also found these
recommendations."*

That sentence is precursor 8 wearing the clothes of thoroughness. It converts a repairable defect
into a note, and a note into a permanent condition — because the cheapest moment to repair a defect
is the moment it is found, with the context that found it still loaded.

Every finding is classified into exactly one of three:

### `SELF_REPAIRABLE`

Fixable deterministically and verifiable without altering dangerous contracts. The executor:

1. reopens the mission;
2. corrects;
3. updates the evidence;
4. **re-freezes**;
5. restarts the affected review.

Step 4 is the one that is skipped, and skipping it silently voids the review: evidence gathered
before the correction describes the pre-correction artifact, which is Part 28 §2's failure arriving
through the back door. Step 5 says *affected*, not *all* — the selection rule of Part 28 §8 decides
which passes are affected, and re-running everything is what makes the loop unaffordable.

The boundary of `SELF_REPAIRABLE` is inherited unchanged from this stack's existing rules:
auto-repair is permitted **only** when it is deterministic, does not change public contracts,
schemas or authentication, and is verifiable. Everything else escalates. — Boundary OBSERVED in
the existing rule surfaces.

### `OWNER_REQUIRED`

Deleting potentially important data · deciding whether a capability should be withdrawn · migrating
production · choosing an owner · resolving a product ambiguity · accepting downtime.

The system **contains the risk, quarantines if safe, destroys nothing, prepares the exact decision,
and marks `OWNER_GATE`.**

*Prepares the exact decision* is the load-bearing clause and the one most often missed. An
`OWNER_GATE` that presents a problem has moved the work to the Owner; one that presents a decision
with its options, evidence and recommendation has moved only the *choice*. Part XVII's routing
discipline applies in full: the criterion travels with the question, and a request for approval is
not a question.

### `GOVERNANCE_VIOLATION`

A prohibited mechanism · a bypassed gate · an unauthorized component · a file in a forbidden path ·
an exposed secret.

**Closure is blocked until compliance is restored.** This class does not negotiate, and it is the
only one of the three that cannot be carried as a residual — Part XX's *complete with residual*
requires the residual to be dispositioned, and an active governance violation has no admissible
disposition other than repair.

## 10. Why classification precedes disposition

The three classes are not severity tiers. They are distinguished by **who may act**, which is the
same axis Part 27 used to separate the three authorities:

| Class | Who may act | What blocks |
|---|---|---|
| `SELF_REPAIRABLE` | the executor | nothing, if repaired in-session |
| `OWNER_REQUIRED` | the Owner | closure, until decided |
| `GOVERNANCE_VIOLATION` | the executor, but under compulsion | closure, unconditionally |

A finding routed to the wrong class fails in a characteristic direction. `OWNER_REQUIRED`
misclassified as `SELF_REPAIRABLE` produces an agent making a product decision by implementing one.
`SELF_REPAIRABLE` misclassified as `OWNER_REQUIRED` produces a queue of trivia the Owner must
process, which trains the Owner to approve without reading — and that is the more insidious of the
two, because it degrades the oracle Part XVI depends on.

> **An Owner queue full of decisions the agent could have made is not caution. It is the oracle
> being spent on questions that did not need it**, and Part XVII §10's economics say the supply is
> finite.

## 11. Review budget by risk

Without a bound, the loop of §9 can run indefinitely: each repair legitimately re-opens a review,
and each review legitimately finds something. Four tiers, by what the change touches:

| Change class | Review scope |
|---|---|
| **Simple change** | local review · direct callers · affected test · **no full-estate scan** |
| **Mode feature** | capability · dependencies · overlay · integration · regression |
| **Architectural change** | multipass · siblings · manifests · build · runtime |
| **Production, economy, data, security or constitution** | full forensic review · rollback · negative verification · owner gate where applicable |

The first row's prohibition is as important as the other rows' requirements. A full-estate scan on
a simple change is not extra safety — it consumes the budget that the fourth row needs, and it
trains everyone that reviews are disproportionate, which is how the fourth row eventually gets
skipped too.

The fourth row is the only one that names `negative verification` explicitly, which ties it to
Part 28 §7: the categories where an absence claim matters are exactly the categories where
withdrawal, migration and prohibition occur.

## 12. The stop condition

The review ends when **all seven** hold:

1. no blockers remain;
2. critical claims are verified;
3. repairable findings have been repaired;
4. the remainder are contained or escalated;
5. reality has been exercised;
6. the necessary immunization is installed;
7. **a further pass produces no material findings.**

And the source states the negative form, which is the part worth keeping verbatim in substance:

> **It does not end because the agent has thought about it enough.**

Condition 7 is the empirical one and it is what makes the set terminate rather than recede. It is
also Part 28's `NOT_SUSTAINED` aggregated: a pass that runs and finds nothing material is evidence
of convergence, whereas a pass not run is evidence of nothing. Condition 6 is the hook into
Part 30 — the `IMMUNIZATION_REQUIRED` state of Part 27 §6 is discharged here or not at all.

Condition 2 says *critical* claims, not all claims, and that qualifier is what keeps the stop
condition reachable. Criticality comes from the ledger's `risk if false` field, which is why §3 has
to exist before §12 can.

## 13. Boundary

- This Part does not specify how precursors are detected mechanically. Several are textual and
  cheap; precursor 9 is not, and §17 records that as the open problem.
- It does not define the immunization installed at condition 6. That is Part 30.
- It does not set the exhaustion threshold at which a closure is degraded, only that the degradation
  is recorded rather than the closure blocked.
- The `SELF_REPAIRABLE` boundary is adopted from this stack's existing rules unchanged. CLAE adds
  the loop around it and does not redefine it.

## 14. Failure modes

| Failure | Mechanism |
|---|---|
| **Findings listed as recommendations** | a repairable defect becomes a note and the note becomes permanent |
| **Repair without re-freeze** | the review's evidence describes the pre-repair artifact |
| **Whole review restarted per repair** | the loop becomes unaffordable and is abandoned entirely |
| **Hedge then implement** | an inference acted on as a fact, with the hedge still in the text |
| **Patch without a revised model** | corrections accumulate over an explanation nobody reopened |
| **Test changed before it is disproved** | evidence converted into agreement |
| **Oracle sharing the implementation's assumption** | a test that cannot fail for the reason it exists |
| **Owner queue full of agent-decidable items** | the oracle is trained to approve without reading |
| **Full scan on a simple change** | the budget the forensic tier needs is spent, and reviews come to be seen as disproportionate |
| **Review ends on fatigue** | no stop condition; the terminating event is the reviewer, not the estate |

## 15. Detection signatures

1. **Hedged verbs in a session log followed by unhedged implementation.** Textual, cheap, and the
   highest-yield single grep in this Part.
2. **A region with three or more corrections and one causal explanation.** Patch stacking, visible
   in history alone.
3. **Tests modified in the same commit as the code they test, with no note on why the test was
   wrong.** Test adaptation's fingerprint.
4. **A closure whose last quarter contains no negative tests or log reads, where its first quarter
   did.** Precursor 9, measurable from the session's own record without any new instrument.
5. **`OWNER_GATE` items that a deterministic rule could have decided.** Count them; the ratio is
   the oracle's dilution.
6. **Reviews that ended without condition 7 being stated.** The stop was declared, not reached.

## 16. Trap seeds — for Part XXII

- **T-CLAE-HEDGE-THEN-ASSERT** — hedged language recording genuine uncertainty, followed by
  implementation and reporting that treat the hedge as settled.
- **T-CLAE-PATCH-OVER-STALE-MODEL** — successive corrections to one region without reopening the
  causal model, each raising the cost of reopening it.
- **T-CLAE-TEST-ADAPTED-TO-CODE** — a failing test changed to accept the implementation before
  anything demonstrated the test was wrong.
- **T-CLAE-SHARED-ASSUMPTION-ORACLE** — a check relying on the same assumption as the thing checked,
  so it verifies self-consistency and reports it as correctness.
- **T-CLAE-EXHAUSTION-DEPTH-COLLAPSE** — the expensive and externally invisible checks disappear as
  a session nears its limit, and the resulting closure is indistinguishable from a full one.
- **T-CLAE-FINDING-AS-RECOMMENDATION** — a repairable defect disposed of as a note for later,
  converting a cheap in-session repair into a permanent condition.
- **T-CLAE-ORACLE-DILUTION** — agent-decidable items routed to the Owner, training the Owner to
  approve without reading and degrading the oracle for the questions that need it.

## 17. Rule seeds — for Part XXIII

- **PR-CLAE-PREFLIGHT-SEVEN-SURFACES** — before modifying a capability, read owner, consumers,
  configuration, tests, manifest, historical decision and equivalent implementation.
- **PR-CLAE-LEDGER-EVERY-MATERIAL-CLAIM** — each material claim is registered with its epistemic
  state, evidence, provenance, the files not consulted, its consumer and its risk if false.
- **PR-CLAE-NO-CRITICAL-CLAIM-LEFT-INFERRED** — at closure a critical claim is verified, rejected,
  or carried explicitly as unknown with risk, containment and owner.
- **PR-CLAE-DISPROVE-BEFORE-ADAPTING-A-TEST** — a test may be changed only after what was wrong with
  it is demonstrated and recorded.
- **PR-CLAE-REOPEN-THE-MODEL-BEFORE-THE-SECOND-PATCH** — a second correction to the same region
  requires the causal model to be restated, not extended.
- **PR-CLAE-CLASSIFY-BEFORE-DISPOSING** — every sustained finding is classified self-repairable,
  owner-required or governance-violation before any action is taken on it.
- **PR-CLAE-REFREEZE-AFTER-REPAIR** — a repair returns the artifact to the frozen state and restarts
  the affected passes, not all passes.
- **PR-CLAE-PREPARE-THE-DECISION-NOT-THE-PROBLEM** — an owner gate carries options, evidence and a
  recommendation; a gate presenting a problem has moved the work rather than the choice.
- **PR-CLAE-BUDGET-BY-RISK** — review scope is set by what the change touches, and a simple change
  does not receive a full-estate scan.
- **PR-CLAE-STOP-ON-CONDITION-NOT-FATIGUE** — the review ends on the seven stated conditions,
  including a further pass producing no material findings.

## 18. Eval seeds — for Part XXIV

- **Hedge-to-assertion probe.** Grep session records for hedged verbs and check whether the
  corresponding claim carries a non-`VERIFIED` state in the ledger. Mismatches are precursor 1.
- **Ledger-completeness probe.** Sample material claims from a closure and check how many appear in
  the ledger. The unlisted fraction is the ledger's real coverage.
- **Circular-oracle probe.** For each test, ask what it would take for it to fail. Tests with no
  answer share the implementation's assumption.
- **Re-freeze probe.** For each in-session repair, compare the artifact hash at repair time and at
  the restarted review. A difference means the review ran against a moving artifact.
- **Exhaustion-profile probe.** Split each session into quarters and count negative tests, log reads
  and sibling searches per quarter. A monotone decline is precursor 9, measured.
- **Owner-gate necessity probe.** Classify past owner gates as agent-decidable or not. The
  agent-decidable fraction is the oracle dilution rate.
- **Stop-condition audit.** For closed reviews, check that condition 7 was evaluated rather than
  assumed.

## 19. Production Reality Gate seed — for Part XXV

**Session Integrity Gate.** A session's evidence may support a closure claim only when preflight was
performed for each modified capability, every material claim appears in the ledger with an epistemic
state, no critical claim remains inferred or hypothetical without an explicit unknown record, every
sustained finding carries a classification and a disposition, each in-session repair was followed by
a re-freeze, and the review terminated on the stated stop condition. Sessions failing this are
recorded as **unaudited work** — legitimate, correctly labelled — rather than as verified.

## 20. Pseudoflow — a session under the protocol

At the start, preflight the surfaces for each capability the mission will touch, and open the
ledger. Every material claim goes in with its state; `INFERRED` is a normal and useful state to act
from, and an illegitimate state to close from.

During execution the precursor detector runs. Hedged-then-asserted language warns. A second patch on
one region demands a restated model. A successful build presented as behavioural evidence blocks. A
test changed without a disproof blocks. A test that cannot fail blocks.

At `REQUEST_CLOSURE` the artifact freezes and Part 28's passes run. Each sustained finding is
classified. Self-repairable ones are repaired now — reopen, correct, update evidence, re-freeze,
restart the affected passes only. Owner-required ones are contained and prepared as an exact
decision. A governance violation blocks unconditionally.

The budget bounds the scope by what the change touched. The review ends when the seven conditions
hold — including that a further pass finds nothing material — and not before, and not merely because
the session is long.

If the session is near exhaustion, the closure is completed and **recorded as produced under
exhaustion**, so that a reader can weigh it against one that was not.

## 21. Integration

Part I supplies the internal-bar trap that the circular oracle instantiates at test scale. Part IX
supplies measurement debt, which the ledger's *files not consulted* field applies per claim.
Part XIII makes every precursor detector an instrument with its own coverage and arity. Part XV
converts a sustained finding into a durable probe rather than a one-time fix, which is the bridge to
condition 6. Part XVII governs the owner gate's presentation and its economics. Part XVIII's
deviation contract is what an `OWNER_REQUIRED` acceptance produces. Part XIX supplies the evidence
contract this Part finally gives a single artifact. Part XXIV supplies the negative control the
circular-oracle probe depends on.

Backward: Part 27's `IMMUNIZATION_REQUIRED` and `OWNER_GATE` states are entered from §9's
classification; Part 28's selection rule decides what *affected* means in step 5.

Forward: Part 30 takes condition 6 and asks what immunization is sufficient.

Outside the family, this stack's recurring-error log is the nearest existing precursor instrument —
it records repeats after the fact, and what it lacks is the in-session signal. The proposal is
additive: the precursor set is a producer for that log, not a replacement.

## 22. Open questions

1. Can precursor 9 be measured without a reliable exhaustion signal? The behavioural profile in §15
   is measurable retrospectively, which detects the collapse after the closure it degraded. A
   prospective signal would need the session to know its own remaining capacity, and whether that is
   available at the right granularity is unresolved. — UNKNOWN, and the most consequential gap in
   this Part.
2. Is the ten-precursor set complete? It was assembled from observed behaviour in one estate plus
   this stack's own rule surfaces, which is two sources and neither is a systematic enumeration.
   The honest expectation is that it is a well-evidenced sample. — HYPOTHESIS.
3. Does classification into three classes survive contact with findings that span two? A finding may
   be self-repairable in its mechanism and owner-required in its consequence. §10 routes by who may
   act, which resolves the ambiguity in principle; whether it resolves it in practice is untested. —
   UNKNOWN.

## 23. Institutional writeback

Seven trap seeds, ten rule seeds, seven eval seeds, one production gate.

Three portable results. **An inference is a legitimate basis for action and an illegitimate basis
for a completion claim** — the epistemic-state field is the only thing that keeps those two uses of
one belief apart, and its absence is how a closure becomes confidently wrong without anyone lying.
**Block the three precursors that manufacture a false pass** — build-as-done, test adaptation and
circular oracle all terminate the search with a green result that means nothing, and a warning
attached to a success is not read. And **a review ends on a stated condition, never on fatigue**,
where the empirical condition is that a further pass finds nothing material.

The structural finding: **precursor 9 is a condition, not a behaviour.** It raises the probability
of the other nine precisely when the capacity to notice them is lowest, and every check it removes
is expensive, optional-feeling and externally invisible — so nothing fails when they are skipped and
the closure looks identical from outside. That is the one precursor self-awareness cannot catch,
because self-awareness is the resource being exhausted, and it is therefore the one that most needs
a mechanical detector and currently has none.
