---
title: "CLAE Part 33 — Deterministic Replay, Effect Virtualization and Replay Fidelity"
family: clae
part: 33
depends_on: [VI, XII, XIII, XV, XXII, XXIII, XXIV, XXV, 31, 32]
feeds: [32]
status: SEALED
date: 2026-08-19
authorization: UPAC STOP #1, Owner option D (2026-08-19)
---

# Part 33 — Deterministic Replay, Effect Virtualization and Replay Fidelity

## 1. Purpose

Part XII §6 requires that a failure record carry a **reproduction handle**, and states the reason
plainly: a failure you cannot reproduce cannot be verified as closed, so every correction against it
is a hypothesis. Part XII §5 requires that variation be **bounded and known** — the noise floor,
established by repeated observation of the same input.

Both are necessary and neither is sufficient, because a reproduction handle names the *input*, and
re-running an input is not re-running an execution. Between the handle and the re-run sits everything
the execution touched that was not the input: the clock, the ambient environment, the filesystem, a
remote service, the interleaving of two concurrent operations, a value read from a global directory
that some other process wrote in the interval.

> What must a re-run capture for it to be **the same run**, and when the re-run disagrees with the
> record, what does the disagreement mean?

This Part answers only that. Two neighbouring capabilities are already owned and are not re-built
here: the **environment fingerprint** — the environment hash, the field-level drift ledger, and the
qualification gate that consumes them — belongs to the estate's environment-qualification discipline
and is treated here strictly as an input; and **bounded-variation characterization** belongs to Part
XII §5 and Part VI §7. What remains unowned, and what this Part specifies, is the effect boundary
that makes a replay possible at all, the contract for capturing a crossing of it, the four fidelity
classes a replay can achieve, and the divergence semantics that make a replay's disagreement
informative rather than merely alarming.

Five mechanisms: the three sources of divergence (§2), the effect boundary and its three properties
(§3), the capture contract (§4), the fidelity ladder (§5), and divergence semantics with the
fail-closed rule (§6). One economic discipline keeps it from being bought where it is not needed
(§7).

## 2. Re-running the input is not replay

Three sources of divergence separate a re-run from a replay, and they need different machinery.

| Source | Examples | Reproduced by |
|---|---|---|
| **Ambient state** | clock, randomness, environment variables, working directory, locale, filesystem contents, whatever another process wrote in the interval | recording and substituting the ambient reads |
| **Ordering** | interleaving of concurrent operations, arrival order of events, iteration order over an unordered collection | recording and enforcing the schedule |
| **External effects** | network calls, subprocess invocations, remote service responses, anything whose result the system does not compute | recording and substituting at the boundary |

A system's replayability is determined by which of these it has arranged to control, and the
arrangement is a **design property established before the failure**, not a tool applied after it.
This is the same structural claim Part XII makes about observability and it fails the same way when
ignored: retrofitting replay after an incident produces a mechanism that works for future incidents
and cannot touch the one that motivated it.

## 3. The effect boundary

Everything in this Part rests on one line: the **effect boundary**, the place where the system's
interaction with the world is named. A crossing is a call that leaves the deterministic core — a read
of the clock, a network request, a subprocess launch, a file read whose contents the system did not
write in this run.

The boundary has three required properties, and each has a characteristic way of not holding.

**Total.** Every effect crosses it. A single unmediated call means replay silently reaches the live
world at that point, and a partial boundary is worse than none because it produces a replay that
*mostly* works and is trusted accordingly.

**Named.** Each crossing identifies its effect kind. A boundary that passes opaque calls through can
record that something happened and cannot substitute it on replay, because it does not know what
kind of thing to substitute.

**Shape-deterministic.** The same logical execution produces the same sequence of crossings. Where
the code's own control flow depends on a value that is itself ambient, the crossing sequence varies
between runs and the record cannot be matched positionally. This is the property most often absent
and the one that makes ordinal matching (§4) fail in confusing ways.

> **A system with no effect boundary cannot be replayed at any price.** This is not a tooling gap to
> be closed by a better recorder; it is a statement about the system's shape, and the only response
> is to introduce the boundary, which is a change to the system rather than to its instruments.

The boundary is also where the estate's own hermeticity rule lives. A gate that writes into a global
directory, or that reads a value with a time window, has an effect crossing that was never named —
which is why running the same suite two or three times detects it. Repeated execution is the cheapest
available detector for an unnamed crossing, and it is the reason a hermetic gate is required to be
observed green more than once rather than once.

## 4. The capture contract

A recorded crossing carries five fields.

- **Ordinal** — its position in the crossing sequence. Position is what a replay matches on, which
  is why shape-determinism is a precondition rather than a nicety.
- **Effect kind** — clock, random, environment read, filesystem read, network, subprocess, and so on.
  The kind determines the substitution strategy.
- **Request identity** — a stable digest of what was asked, not the raw payload. A digest is
  matchable, is cheap to store, and does not carry a credential or a personal record into an artifact
  that will be committed. This is the field that makes a capture archive safe to keep.
- **Observed result** — what came back, and this one **is** the payload, since the replay must return
  it. It is therefore the field that governs where a capture archive may be stored and by what
  retention rule.
- **Outcome class** — returned, raised, timed out, or never completed. The fourth exists because a
  crossing that never returned is a real and common state, and a record that cannot express it will
  express it as one of the other three.

Two crossings with the same ordinal and different request identity is the primary divergence signal
of §6, so the digest's stability matters more than its precision: a digest that varies between
identical logical requests reports drift on every replay and is quickly ignored.

## 5. The fidelity ladder

The central error in replay work is treating it as binary — a run either reproduces or it does not.
Replay comes in classes, each reproducing strictly more and costing strictly more, and **a replay's
class must be declared alongside its result.**

| Class | Captures | Reproduces | Cannot reach |
|---|---|---|---|
| **F0 · input replay** | the input only | that the input was accepted | anything the world contributed |
| **F1 · effect replay** | F0 + crossings, substituted at the boundary | the execution, given unchanged code | faults that depend on ordering or on ambient reads outside the boundary |
| **F2 · schedule replay** | F1 + the interleaving | concurrency and ordering faults | faults driven by real timing rather than order |
| **F3 · ambient replay** | F2 + clock, randomness, environment | the full envelope of the recorded run | genuine hardware and physical-timing effects |

The declaration rule exists because of a specific and common false conclusion. A defect that an F1
replay does not reproduce is routinely recorded as **unreproducible**, and that word then licenses
closing the case as environmental or transient. It licenses nothing of the sort: an F1 failure to
reproduce is evidence that the fault depends on ordering or ambient state — which is a *narrowing*,
and one of the most informative outcomes available, since it eliminates every hypothesis that depends
only on inputs and recorded effects.

> **A non-reproduction is a measurement of the fidelity class, not a property of the bug.**

Written into Part 32's vocabulary: a replay attempt is an experiment, its class is the instrument,
and reporting the outcome without the instrument makes the result uninterpretable.

## 6. Divergence semantics and the fail-closed rule

A replay is only useful if it can tell that the run departed from the record. Three divergences, with
three distinct meanings.

| Divergence | Meaning | Correct response |
|---|---|---|
| **Unrecorded crossing** — the code asks something the record does not hold | the code changed, or the boundary is not total | fail the replay |
| **Out-of-order crossing** — right request, wrong ordinal | shape-determinism does not hold, or the schedule was not captured | raise the fidelity class or fix the shape |
| **Identity mismatch** — same ordinal, different digest | the input or upstream state drifted | re-record; the old capture is stale |

The first row carries the load-bearing rule of this Part:

> **An unrecorded crossing fails the replay. It never falls through to the live world.**

A replay that silently reaches the real world on a cache miss produces two harms at once, and the
second is worse than the first. It yields a conclusion that appears to come from the recorded run and
does not, which is a confidently wrong diagnosis; and it performs a real effect — a real request, a
real write, a real charge — from a context whose whole purpose was that it would not. Fail-closed is
not a preference here. A fall-through replay is strictly more dangerous than having no replay, because
no replay is at least honest about touching the world.

This is the same shape as Part XIII §7's three-valued instrument requirement and Part 32 §6's
*could not run*: the mechanism must be able to say **I cannot answer that**, or it will answer
anyway, in the direction that closes the case.

## 7. Fidelity is bought per failure class

Every rung costs. F1 requires the boundary to be total, which is invasive. F2 requires a controllable
schedule, which usually means the concurrency primitives themselves are mediated. F3 requires the
clock and the randomness source to be injected everywhere they are read, and the estate pays that in
every module that ever calls one directly.

The discipline is a single ordering rule: **name the failure class first, then buy the fidelity that
class requires.** Buying F3 across an estate that has never had an ordering-dependent defect is the
accumulation failure Part X §6 describes, arriving with unusually good engineering credentials. Buying
F1 for the surfaces where an incident has already been irreproducible twice is cheap and repays
immediately.

The observable that decides it is already recorded elsewhere: incidents whose reproduction handle
failed. When a class of incident repeatedly cannot be re-run, the class names the rung.

## 8. Replay and the hypothesis tree

Part 32 ranks experiments by how evenly they split belief. That ranking assumes an experiment's
outcome is a fact about the system, and without replay it is a single sample from a distribution.

Two consequences, both operational.

**An experiment whose effect is smaller than the noise floor cannot prune.** Part XII §5's floor is
what says how large that is. Running such an experiment produces an outcome, and the outcome is
scatter; recorded as *contradicted*, it eliminates a live hypothesis for no reason.

**Replay converts a flaky experiment into a reliable one, which is the third factor in Part 32 §5's
ranking.** An experiment that must be run against the live world is discounted for unreliability; the
same experiment run against a capture is not. The value of a replay capability is therefore visible
directly in the diagnosis budget — it moves experiments up the ranked list by making them trustworthy,
which is a more concrete benefit than the usual argument from convenience.

## 9. Boundary

**Bounded variation** is Part XII §5 and Part VI §7. That machinery characterizes how much an
observable moves when nothing changed; this Part reproduces a specific run. The noise floor is an
input here, not an output — it is what says whether a replay's disagreement with the record exceeds
the instrument's own scatter.

**The environment fingerprint** — hash, field-level drift ledger, qualification gate — is owned by the
environment-qualification discipline. F3's ambient record *consumes* the fingerprint; it does not
recompute it, and a second fingerprint in this estate would be a second source of truth for the same
fact with the later one silently wrong.

**Observed system reconstruction** builds a typed model of an **external** system that the estate does
not control, from observations of it. This Part replays **this** system's own execution. The two share
the word reconstruction and nothing else; keeping them apart is what stops a second reconstruction
engine from appearing beside the first, which is exactly what the ownership audit that authorized this
Part declined to build.

**Tiered capture** is the transport and the retention tiering for recorded material. This Part
specifies what a crossing record must contain and what a replay owes its caller; where those bytes
live and how long they are kept is not its decision.

**Test isolation** is not owned here. Whether a given gate is hermetic is a property of that gate;
this Part supplies the reason repeated execution detects the defect — an unnamed effect crossing —
and no more.

## 10. Evidence — replay-shaped findings in this stack

**The hermetic-run rule is an unnamed-crossing detector.** This estate requires its gates to be
observed green two or three times rather than once, and the rule was not derived from theory: a gate
that wrote into a global directory, and another whose result depended on a time window, both passed
in isolation and failed on repetition. In this Part's vocabulary both had an effect crossing that was
never named, and repeated execution is the cheapest detector that exists for one. The practice is
already live and this Part supplies its mechanism.

**A suite whose result depended on the session that ran it.** A baseline test was observed to fail
because of the token burn of the very session executing it — an ambient read from outside the
boundary, in a gate believed hermetic. The failure was real, the code was correct, and no amount of
input-level reproduction would have shown it, because the input was never the variable. F0 reproduces
nothing here; the finding is only visible once ambient reads are treated as crossings.

**A class of failure the estate handles by avoidance rather than replay.** The documented transport
hangs on this host are recorded as a set of avoidance rules — do not chain this, do not background
that — rather than as diagnosed defects. That is the correct engineering response given the tools
available, and it is also precisely what an unreplayable failure class looks like from the inside:
the doctrine grows, the mechanism stays unknown, and the rules accumulate because nothing can be
re-run to test whether any of them is still necessary. It is offered here as the honest cost of
absent replay, not as a defect to be repaired by this Part.

## 11. Failure modes

| # | Failure | Why it survives |
|---|---|---|
| 1 | **Fall-through replay** | it works, right up until the cache misses; then it is confidently wrong and has touched the world |
| 2 | **Partial boundary** | replay works for most crossings and is trusted at full strength |
| 3 | **Undeclared fidelity class** | a result reads as *unreproducible* rather than *not reproducible at F1* |
| 4 | **Non-reproduction closed as transient** | the case closes and the narrowing is discarded |
| 5 | **Ordinal matching without shape-determinism** | divergences appear at unrelated positions and the record is blamed |
| 6 | **Raw payload as request identity** | the archive becomes unstorable, and is then not stored |
| 7 | **Fidelity bought without a named class** | it is defensible engineering and it is unbounded |
| 8 | **Stale capture** | identity mismatch is read as a product defect rather than as drift |
| 9 | **Experiment beneath the noise floor** | it returns an outcome, and the outcome prunes |

## 12. Detection signatures

- A replay implementation with a live-call path reachable on a record miss.
- A replay result recorded without its fidelity class.
- An incident closed as *could not reproduce* with no statement of what was attempted.
- A capture record with no outcome class, or with only success and failure values.
- A crossing record storing a raw request payload.
- A gate observed green exactly once.
- A suite whose second consecutive run differs from its first.
- A diagnosis whose experiment result is smaller than the recorded noise floor.

## 13. Trap seeds — for Part XXII

- **The replay that reached the world.** A miss falls through, the answer looks recorded, and a real
  effect has occurred from a context defined by not having effects.
- **Unreproducible as a verdict.** It is a measurement of the instrument, and it is routinely
  recorded as a property of the bug — in the direction that closes the case.
- **The mostly-total boundary.** One unmediated call, and the replay is trusted at the strength of
  the ninety-nine that work.
- **Fidelity as virtue.** Buying F3 estate-wide is excellent engineering, unbounded cost, and
  justified by no observed failure class.

## 14. Rule seeds — for Part XXIII

- **An unrecorded crossing fails the replay.** No live fall-through exists on any path.
- **Every replay result declares its fidelity class.** A non-reproduction without a class is not a
  result.
- **A crossing record stores a digest as request identity, never the raw request.**
- **Outcome class is four-valued**, including never-completed.
- **Fidelity is bought against a named failure class**, evidenced by incidents whose reproduction
  handle failed.
- **A gate is observed green more than once**, because repetition is the cheapest unnamed-crossing
  detector.
- **An experiment whose effect is under the noise floor does not prune a hypothesis.**

## 15. Eval seeds — for Part XXIV

- Take incidents closed as irreproducible and re-attempt at the next fidelity rung. The proportion
  that reproduces is the mis-closure rate and is the number that justifies buying the rung.
- Introduce an unrecorded crossing deliberately and confirm the replay fails rather than reaching the
  world. This is the single highest-value regression in the Part.
- Run every gate twice in one invocation and compare. Any difference is an unnamed crossing, and the
  count is the estate's hermeticity residual.
- Compare replay-backed experiments against live-world experiments for outcome stability across
  repetitions. If they are equally stable, this estate's failures do not need replay and the rung
  should not be bought.
- Re-run a capture against a deliberately drifted upstream and confirm the divergence is reported as
  identity mismatch rather than as a product defect.

## 16. Production Reality Gate seed — for Part XXV

An incident may not be closed with a reproduction verdict of *could not reproduce* unless the record
names the fidelity class attempted. The gate accepts `F0` through `F3` and accepts `no replay
capability on this surface`; it rejects a bare *could not reproduce*, because that phrasing asserts a
property of the defect on the strength of an observation about the instrument.

## 17. Pseudoflow — capturing and replaying a failure

Establish the effect boundary before the incident, as a design property: every effect crosses, each
crossing names its kind, and the crossing sequence is shape-deterministic for a given logical
execution. On a recorded run, capture each crossing with its ordinal, kind, request digest, observed
result and outcome class, and attach the environment fingerprint the qualification discipline already
computes. To reproduce, declare the fidelity class the failure class requires; substitute the recorded
results at the boundary; match by ordinal and verify request identity. On an unrecorded crossing,
fail — never fall through. On an out-of-order crossing, report a shape or schedule defect rather than
a product one. On an identity mismatch, treat the capture as stale and re-record. Report the result
with its fidelity class attached, and where the failure did not reproduce, record the class as the
narrowing it is and return it to Part 32 as an eliminated hypothesis family rather than as a closed
case.

## 18. Integration

Upstream: Part XII §6's reproduction handle, which this Part gives a contract; Part XII §5's noise
floor, which decides whether a divergence is a signal; the environment fingerprint, consumed as F3's
ambient record; tiered capture, which carries the bytes. Downstream: Part 32's hypothesis tree, whose
experiment reliability factor this Part is the mechanism for, and whose *could not run* outcome an
un-replayable experiment produces; Part 31's sibling execution, which needs a stable substrate or its
extent measurement is scatter; Part XV's probe, whose reproduction section is exactly a capture and
which is decorative without one; Part XIII, which receives the instrument request when a required
fidelity rung does not exist.

## 19. Open questions

- **Shape-determinism is asserted, not checked.** Nothing here detects a system whose crossing
  sequence varies; it is discovered when ordinal matching produces confusing divergences, which is
  late and misattributes the cause to the record.
- **Capture retention has no owner in this Part.** Observed results are payloads, and payloads have a
  retention rule, a storage location and a redaction obligation this Part deliberately does not
  legislate. Left unowned, the practical outcome is that captures are kept where it was convenient.
- **The rung-purchase rule needs an incident corpus that records reproduction failure.** It asks for
  evidence from incidents whose reproduction handle failed, and that field is not consistently
  recorded, so the rule currently depends on data the estate does not yet reliably produce.
- **F2 assumes schedule control the estate mostly lacks.** Where concurrency is provided by an
  external runtime, the interleaving is not the system's to record, and the honest position is that
  F2 is unavailable there rather than expensive.

## 20. Institutional writeback

Four trap seeds, seven rule seeds, five eval seeds, one production gate.

Three portable results. **Reproducing an input is not reproducing an execution** — the handle Part
XII requires names one of the three sources of divergence, and the other two are usually the ones
that matter. **A non-reproduction measures the instrument, not the bug**: an F1 failure to reproduce
eliminates every hypothesis that depends only on inputs and recorded effects, which is a narrowing of
real value, and it is routinely converted into the word *transient* and thrown away. And **replay
must be able to refuse** — an unrecorded crossing that falls through to the live world produces a
wrong answer that looks recorded and a real effect that was supposed to be impossible, which is the
same structure as a two-valued instrument reporting a pass it never ran.

The structural finding is that replayability is a property of the system rather than of its tools.
There is no recorder good enough to replay a system with no effect boundary, and the estate's own
practice already demonstrates the consequence from the other side: where a failure class cannot be
re-run, the response is a growing set of avoidance rules that nothing can ever retire, because
retiring one would require re-running the failure it was written for.
