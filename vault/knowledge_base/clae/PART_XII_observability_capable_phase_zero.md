---
title: "CLAE Part XII — Observability-Capable Phase Zero"
family: clae
part: XII
depends_on: [VI]
feeds: [XIII, XIV, XV, XVI, XIX]
status: SEALED
date: 2026-07-26
---

# Part XII — Observability-Capable Phase Zero

## 1. Purpose

Every mechanism in this family so far has assumed that observation is possible. Part VI's
precondition requires observing both objects; Part VIII's cycle requires re-measurement; Part IX's
ledger requires values to record; Part X's floors require checks that execute.

That assumption is load-bearing and it is never examined, because by the time anyone needs to
measure, the system exists and observing it feels like a tooling question. This Part moves the
examination to the only moment it is cheap: **before the first feature**.

It states the six capabilities a project must demonstrate to be observable at all, argues why the
demonstration cannot be deferred, establishes that the honest output of a partial Phase Zero is a
declared measurement-debt register rather than a failure, and identifies Phase Zero as the entry
condition for autonomous work.

## 2. Why observability cannot be retrofitted honestly

The cost argument is familiar and is the weaker one: retrofitting observation into many features
costs many times what building it once costs.

The epistemic argument is the one that matters.

> **Observability added after the fact is observability shaped by the author's model of what the
> system does.**

Someone instrumenting a working system instruments what they expect to be interesting. They already
know how it behaves — or believe they do — and the instrumentation encodes that belief. The
dimensions along which their model is wrong are precisely the dimensions they do not instrument,
because nothing in their understanding marks those places as worth watching. The result observes
what was expected and is blind exactly where expectation fails, which is Part I's structure
appearing at the instrumentation layer: a self-authored view of what matters, applied by the party
whose view is in question.

There is a second, sharper form. **The first thing a system needs observed is usually whatever broke
before observation existed.** A failure occurs, and the diagnosis requires data that was not being
captured, so the capture is added, so the *next* occurrence is diagnosable. Every incident before
that one is unavailable. A project that establishes observation first pays once; a project that
adds it reactively pays with one undiagnosable incident per capability.

The third form is the quietest. A feature built without observability **has never been observed to
work**. It has been observed not to fail visibly, which is a different and much weaker claim, and
the two are indistinguishable from the inside.

## 3. The six capabilities

Six, and they are **ordered**. Each depends on the ones before it, so a break anywhere terminates
the chain regardless of how well the later capabilities were built.

| | Capability | The demonstration |
|---|---|---|
| 1 | **Boot** | The system reaches a known state, repeatably, from nothing |
| 2 | **Observe** | Its internal state can be inspected while it runs |
| 3 | **Measure** | A quantity of interest is extracted with a recorded unit |
| 4 | **Reproduce** | The same input yields the same observable outcome, within a known envelope |
| 5 | **Compare** | Two runs or two versions can be diffed on the observables |
| 6 | **Fail legibly** | A failure identifies what failed, where, and with what input |

You cannot compare what you cannot measure. You cannot measure what you cannot observe. You cannot
observe what you cannot bring to a known state. The ordering is not a preference about sequence; it
is a dependency structure, and it is why partial provisioning across all six is worth less than it
appears.

## 4. The thin-vertical rule

The instinct in Phase Zero is to provision broadly — some booting, some logging, some measurement,
across many dimensions. This produces a Phase Zero that demonstrates nothing.

> **Prove all six capabilities end to end on one dimension, rather than provisioning all dimensions
> partially.**

Because the capabilities are ordered, a chain broken at any link yields no measurement on that
dimension. Six dimensions each provisioned to capability three produce zero comparable measurements.
One dimension carried through all six produces a working measurement chain, and — more valuable —
proves the chain is *possible* in this project, which is the actual question Phase Zero asks.

Phase Zero is a **capability proof, not a coverage proof**. Its output is the demonstrated
existence of a path from a running system to a comparable number, plus an honest statement of which
dimensions do not yet have one.

## 5. The determinism envelope

Capability four is routinely misread as requiring determinism. It does not. It requires that
**variation is bounded and known**.

Most systems worth measuring vary between runs: timing, ordering, allocation, external state. The
requirement is not to eliminate that variation but to characterize it — to establish, by repeated
observation of the same input, how much the observable moves when nothing changed.

This is precisely Part VI §7's noise floor, and Phase Zero is its natural home. Establishing it
later means every measurement taken before then is uninterpretable in retrospect, because nobody
can say which of those differences exceeded the instrument's own scatter.

> **Phase Zero produces the noise floor as an artifact.**

That single output retroactively determines whether every subsequent residual is a measurement or a
number. It costs one repeated observation per instrument and it is the highest-value thing Phase
Zero delivers.

## 6. Fail legibly

Capability six is last in the ordering and first in consequence, because its absence silently
degrades all five before it.

A failure that does not identify itself converts a diagnosable system into an undiagnosable one, no
matter how well instrumented the success path is. This is Part X §4's unobservable shape, and it
appears here as a capability rather than as a defect because Phase Zero is where it is cheap to
establish.

Three requirements, and a fourth that is usually missing:

1. **What failed** — the operation, named specifically enough to locate.
2. **Where** — the point in the system, not merely the outermost boundary that caught it.
3. **With what input** — the state or arguments that produced it.
4. **A reproduction handle** — enough to re-run the failing case.

The fourth is the one that turns a report into a diagnosis. A failure record satisfying the first
three tells you a failure occurred and describes it; without the fourth you cannot make it happen
again, which means you cannot confirm any fix. **A failure you cannot reproduce cannot be verified
as closed**, so every correction against it is a hypothesis in Part VIII's exact sense.

## 7. Phase Zero and autonomy

The general case for Phase Zero is strong. For autonomous work it is different in kind.

An agent operating without observability produces work at machine speed that nobody, including the
agent, can evaluate. The volume of unfalsifiable output scales with the rate of production, and the
rate of production is the whole reason for the autonomy. **The faster the producer, the more
expensive the missing instrument** — which inverts the usual intuition that fast production makes
tooling investment a distraction.

There is a second reason specific to agents. A human building without observability retains an
informal model of the system in memory and can often diagnose from it. An agent's equivalent
context does not persist across sessions, so the informal channel that partially compensates for
missing instrumentation is absent. What is not written down and observable is not available at all.

> **Phase Zero is the entry condition for autonomous work, not a precondition for good autonomous
> work.**

Below it, autonomy is unbounded in the precise sense that its output cannot be checked against
anything, and this is the entry condition Part XIX's evidence-gated autonomy inherits.

## 8. The verdict and the honest partial

The Phase Zero verdict is binary — the project is observability-capable or it is not — because it is
a floor in Part X's sense and floors are binary at the boundary.

But the *scope* of the verdict is where honesty lives. A project rarely achieves all six
capabilities on every dimension it cares about, and pretending otherwise is worse than the gap.

> **The honest output of a partial Phase Zero is a declared measurement-debt register.**

The dimensions carried through all six are measurable. The dimensions that are not are recorded as
measurement debt in Part IX §5's exact sense — declared at the start, visible in every subsequent
report, rather than discovered years later as an absence nobody noticed.

This is the strongest reason to run Phase Zero even when it cannot be completed. Its failure mode is
a *declared* register of what cannot be seen; the alternative is an undeclared one, and Part IX §5
established that undeclared measurement debt is the trap's final form. Phase Zero is where that
register is cheapest to write and where writing it costs nobody any credibility, because nothing has
been claimed yet.

## 9. Boundary

Phase Zero is disproportionate for genuinely throwaway work: a one-shot script, an exploratory probe
that will be discarded, a calculation performed once. The requirement in these cases is that the
throwaway status is *declared* and that the artifact cannot silently graduate into something durable
while retaining the exemption — the same exploration-capture failure Part X §8 named.

It is non-negotiable for anything autonomous, anything long-lived, and anything with a consumer
other than its author. These three share the property that the informal knowledge compensating for
missing observability is unavailable to whoever needs it.

Phase Zero is also **not** three things it is regularly confused with. It is not a production
monitoring stack, which watches a running system for operational purposes. It is not a test suite,
which asserts intended behaviour where Phase Zero enables observation of actual behaviour. And it is
not full instrumentation coverage, which is a state Phase Zero does not attempt to reach.

## 10. Evidence — Phase Zero in this stack

| Surface | Capabilities demonstrated | Missing |
|---|---|---|
| Gate convention with named checks | Measure, compare, fail legibly for the checked properties | Bounded to what each gate covers; no noise floor |
| Artifact done gate | Observe, measure over a declared artifact set | No reproduction envelope |
| Empirical verification runs | Boot, observe, fail legibly | No noise floor; reproduction handle varies by case |
| Reachability audit | Boot, observe, measure, compare across baselines | Fail-legibly is strong; the debt set is named |
| This compendium's construction | All six on one dimension: the gate script was written and proven on Part I before Part II was drafted | Noise floor not applicable to a deterministic text check |
| Module surface at large | Boot and observe per module | Compare across modules absent — the finding below |

Two findings.

**The compendium's own construction ran a thin vertical.** The gate script — contamination, code
fences, coherence against the filesystem, word floor — was written and demonstrated on the first
Part before the second was drafted, and every Part since has been gated by the same instrument
under the same conditions. That is Phase Zero's thin-vertical rule applied in practice, and it is
why the gate results across eleven Parts are comparable to each other. — OBSERVED.

**The 156-module finding is a Phase Zero failure at system scope.** Modules existed, imported
cleanly, and passed their tests while nothing reached them. Per-module boot and observe were
established; *compare at the system level* — which modules are reached versus which exist — was
never a capability, so the question could not be asked until an instrument was built to ask it. The
reachability audit is that instrument, built after the fact, and its first run found a debt that had
been accumulating invisibly the entire time. That is §2's reactive-instrumentation cost, paid in
full. — OBSERVED from the liveness finding; the Phase Zero framing is INFERRED.

## 11. Failure modes

| Failure | Mechanism |
|---|---|
| **Retrofitted observability** | Instrumentation encodes the author's model; blind exactly where the model is wrong |
| **Broad shallow provisioning** | Many dimensions provisioned partially; the ordered chain breaks on each, yielding no measurements |
| **Determinism confused with reproducibility** | Variation treated as a defect to eliminate rather than an envelope to characterize; no noise floor results |
| **Silent failure** | Failures that do not identify themselves, degrading all five preceding capabilities |
| **Unreproducible failure** | A report with no reproduction handle; no correction against it can be verified |
| **Undeclared partial** | Phase Zero completed on some dimensions, with the uncovered ones never registered as measurement debt |
| **Exploration capture** | Throwaway exemption retained as the artifact becomes durable |
| **Autonomy before Phase Zero** | Unfalsifiable output produced at machine speed with no informal channel to compensate |

## 12. Detection signatures

1. **The instrumentation that matches the design document.** Observables corresponding one-to-one
   with the author's described components. Retrofit signature; nothing is watched that the model did
   not predict.
2. **The undiagnosable first incident.** Every capability was added after a failure that required
   it. The reactive pattern, visible in the instrumentation's own history.
3. **The absent envelope.** No record anywhere of how much an observable moves when nothing changes.
4. **The outermost stack frame.** Failures reported at the boundary that caught them rather than the
   point they originated. Capability six is partial.
5. **The unregistered dimension.** A quality claim about a dimension with no Phase Zero chain behind
   it. The measurement debt was never declared.

## 13. Trap seeds — for Part XXII

- **T-CLAE-RETROFIT-BLINDNESS** — observability added by someone who already believes they know the
  system, instrumenting expectation and remaining blind where expectation fails.
- **T-CLAE-BROAD-SHALLOW-PHASE-ZERO** — all dimensions provisioned partially, the ordered chain
  broken on each, producing no comparable measurement anywhere.
- **T-CLAE-NO-REPRODUCTION-HANDLE** — failures reported without enough to re-run them, so no
  correction can be verified as closed.
- **T-CLAE-UNDECLARED-PARTIAL-ZERO** — Phase Zero completed on some dimensions with the remainder
  never registered as measurement debt.
- **T-CLAE-AUTONOMY-BEFORE-ZERO** — autonomous production begun without an observation chain,
  generating unfalsifiable output at the rate the autonomy was adopted for.

## 14. Rule seeds — for Part XXIII

- **PR-CLAE-PHASE-ZERO-FIRST** — the six capabilities are demonstrated on at least one dimension
  before the first feature. Work begun without it records the omission as declared measurement debt.
- **PR-CLAE-THIN-VERTICAL** — Phase Zero proves all six capabilities end to end on one dimension
  rather than provisioning many dimensions partially.
- **PR-CLAE-ENVELOPE-NOT-DETERMINISM** — capability four is satisfied by a characterized variation
  envelope. Phase Zero produces the noise floor as a recorded artifact.
- **PR-CLAE-REPRODUCTION-HANDLE** — every failure record carries what failed, where, with what
  input, and enough to re-run it. Records lacking the handle are notifications, not diagnoses.
- **PR-CLAE-DECLARE-THE-UNCOVERED** — dimensions without a complete Phase Zero chain are registered
  as measurement debt at the outset, not discovered later as an absence.
- **PR-CLAE-ZERO-GATES-AUTONOMY** — autonomous work requires a demonstrated Phase Zero on the
  dimensions it will affect. Below it, autonomy is unbounded by construction.

## 15. Eval seeds — for Part XXIV

- **Chain-completeness probe.** For each dimension claimed measurable, walk all six capabilities and
  identify the first that breaks. Dimensions breaking before capability five produce no comparable
  measurements regardless of their instrumentation.
- **Envelope-existence probe.** For each instrument, look for a recorded variation envelope. Absence
  means every residual from it is uninterpretable at small magnitudes.
- **Reproduction-handle probe.** Sample failure records and attempt to re-run each from the record
  alone. The success rate is the real value of capability six.
- **Retrofit-history probe.** Examine when each observable was added relative to the incident that
  needed it. A consistent after-the-incident pattern quantifies §2's cost in undiagnosable events.
- **Debt-register probe.** Compare the dimensions a project makes quality claims about against the
  dimensions with a Phase Zero chain. The difference is measurement debt, and whether it was
  declared or discovered is the finding.

## 16. Production Reality Gate seed — for Part XXV

**Phase Zero Gate.** A project may begin feature work, and an agent may begin autonomous work, only
when at least one dimension has demonstrated all six capabilities end to end, the variation envelope
is recorded for each instrument in use, failure records carry reproduction handles, and every
dimension the project intends to make quality claims about either has a chain or is registered as
measurement debt. A partial Phase Zero passes this gate with its register attached; an undeclared
partial does not.

## 17. Pseudoflow — establishing Phase Zero

Choose one dimension that matters and carry it the whole way, rather than provisioning several
partially.

Establish boot: bring the system to a known state from nothing, twice, and confirm the two states
are the same. If they are not, characterize the difference before proceeding — that difference is
already part of the envelope.

Establish observation: inspect internal state while the system runs, along the chosen dimension.
Confirm the observation does not require modifying the system to take it, or record that it does,
since an observation that perturbs is a different instrument.

Establish measurement: extract a quantity with a recorded unit and a recorded instrument.

Establish the envelope: observe the same unchanged input repeatedly and record the spread. This is
the noise floor, and it is the artifact Phase Zero exists to produce.

Establish comparison: diff two runs, or two versions, on the observable. Confirm the diff is
commensurable in Part VI's sense — same instrument, same conditions.

Establish legible failure: induce a failure deliberately and confirm the record identifies what
failed, where, with what input, and carries enough to re-run it. Deliberate induction is the only
reliable way to test this; waiting for a real failure means discovering the gap at the worst moment.

Then register every dimension that did not receive this treatment as measurement debt, with the
reason. Publish that register alongside the Phase Zero verdict, so the project's first quality
statement already says what it cannot see.

## 18. Integration

Part XIII takes the instruments Phase Zero establishes and classifies them, inheriting the envelope
and coverage as required instrument properties. Part XIV's toolsmith behaviour is what happens when
a needed capability is absent mid-work — Phase Zero front-loads the common cases so that toolsmithing
becomes exceptional rather than constant. Part XV converts induced and real failures into durable
probes, extending capability six from a one-time demonstration into an accumulating asset. Part XVI
receives the dimensions where no chain is possible as candidate oracle questions. Part XIX takes §7
as its entry condition.

Within the family, Part VI's noise-floor requirement is satisfied here rather than left as an
obligation on every future measurement, and Part IX's measurement-debt register receives its initial
contents from §8.

Outside the family, the reachability audit is cited as the instrument built reactively at system
scope, and the compendium's own gate script as the thin vertical proven before the work it gates.

## 19. Open questions

1. Can Phase Zero be established for a dimension whose observation requires the feature that does
   not yet exist? The ordering assumes observation precedes construction, and for some dimensions the
   thing to be observed is the thing to be built. — UNKNOWN; the likely resolution is an initial
   thin vertical on a proxy dimension, which inherits proxy fidelity.
2. How much of Phase Zero transfers between projects in the same stack? If the six capabilities are
   largely properties of the substrate rather than of the project, the cost is paid once per stack
   rather than once per project, which changes the economics substantially. — HYPOTHESIS.
3. Is the ordering strict? Capability six appears partially independent of three through five — a
   system can fail legibly without being measurable. If the ordering is a dependency structure with
   an exception, §4's thin-vertical argument needs qualification. — UNKNOWN.

## 20. Institutional writeback

Five trap seeds, six process-rule seeds, five eval seeds and one production gate.

Three portable results. **Observability retrofitted is observability shaped by the author's model**,
blind exactly where the model is wrong — which reframes instrumentation timing from a cost question
into an epistemic one. **The thin-vertical rule**: prove all six capabilities on one dimension rather
than provisioning many partially, because the capabilities are ordered and a broken chain yields
nothing. And **the honest output of a partial Phase Zero is a declared measurement-debt register** —
which makes an incomplete Phase Zero strictly more valuable than a skipped one, and writes the
register at the only moment when admitting what cannot be measured costs no credibility at all.
