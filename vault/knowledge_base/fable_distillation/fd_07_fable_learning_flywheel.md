# FD-07 — Fable Learning Flywheel (S-FLYWHEEL)

> The operating loop of the Fable Advantage Distillation Suite — the protocol that composes FD-01…FD-06
> into a single **closed, valid, fast** feedback cycle so that using a frontier model compounds into
> permanent, model-independent stack improvement, session after session, automatically. Parents: **GK-08**
> (the Stop-hook session writeback, ridden as the loop's close-boundary trigger) and the **learning-sentinel**
> (the accrual trigger, ridden as the loop's cadence). FD-07 is genuinely NEW *as a composed operating
> protocol* but is explicitly NOT new plumbing: it orchestrates existing hooks, sequences existing
> stations, and reports through the existing CO-12 metric. Sealed under **SCS C82**. Guarantee level
> (CO-10 honest): **rung-2 orchestration + rung-3 close-boundary** where the loop's close is enforced by
> the GK-08 Stop hook that already runs at every session end, rung-1 advisory for the cadence and
> boundedness discipline until the v2 hook lands. **The thesis this dataset carries most fully: the loop
> is the moat.** CWOPS proved that in 2026 the durable advantage is not any feature the frontier model
> produces — those are commoditized, weekend-replicable — but the feedback flywheel a system's own
> execution deposits, provided that flywheel is valid (behavior actually changes), closed (action →
> capture → changed behavior), and fast (reusable within the same week, <30-day latency). FD-07 is the
> dataset that engineers all three preconditions for the Power Pack and names the failure that kills most
> loops: **capture without close — a loop that stalls into a log file.**

---

## Part I — Mission, the Problem a Loop Solves, and the Loop Definition

### I.1 Mission

FD-07 exists to make one guarantee true across the whole suite: that the six stations FD-01…FD-06 do not
merely *exist* as capable components but *turn together as a single wheel*, so that the act of using a
frontier model this week measurably reduces the need to use it next week — and does so without any human
remembering to run a pipeline. It is the operating loop, not a new mechanism. Every other FD dataset owns
one operation: FD-02 compiles the high-leverage question, FD-00 admits or declines the frontier call,
FD-01 extracts and classifies the delta, FD-03 triages and transmutes it to a destination form, FD-06
writes it back permanently, FD-04 proves it survives a model downgrade, FD-05 converts it into a cheaper
routing or asset. Each is correct in isolation. None of them, alone, *closes the loop* — none guarantees
that the extracted delta actually changes what the next session does, that the write actually lowers the
CO-12 dependence metric, that the risen floor actually sharpens the next question. FD-07's mission is
exactly that guarantee: to wire the stations into a cycle whose output is fed back as the next cycle's
input, and to prove the cycle is spinning up rather than merely spinning.

The mission is deliberately austere in the same way FD-00's is. FD-07 does not try to make any station
better; six sealed datasets already do that. It does not add a seventh operation; that would be bloat
and the anti-pattern the FD_INDEX's DO_NOT_BUILD column exists to forbid. Its entire contribution is
*compositional* — the closed-loop guarantee, the cadence-and-boundedness discipline that keeps the loop
running "hasta completar" without burning unbounded cost, and the compounding measurement that
distinguishes a wheel gaining momentum from a wheel merely turning in place. The measure of success is
inherited verbatim from the suite and never re-invented: frontier-dependence reduction via CO-12's
model-demotion / Opus-avoided count and cognitive-compression ratio. If that number does not move over
weeks, the flywheel is not spinning up no matter how many deposits the vault accrued, and FD-07 has
failed its one job — a failure it is engineered to *detect and surface*, not to hide behind deposit
volume.

There is a reason the loop, and not any station, is where the moat lives, and it is the reason FD-07
carries the CWOPS thesis most fully. A frontier answer is a commodity: ~90% of what a model produces is
replicable by anyone with the same API key, and technical superiority died as a defensible advantage the
moment Copilot, Lovable, and v0 could reconstruct Stripe-grade systems in an afternoon. What is *not*
commoditized is the loop that converts each commoditized answer into a permanent, proprietary reduction
in a specific stack's dependence on the model that produced it. Two teams receive the identical Fable
answer; the one whose loop is closed extracts the delta, writes it back against its own rising floor,
proves it portable, and converts it to a deterministic rung — and next week does not need the model for
that class at all. The other team consumed an answer. The difference between them is not the answer and
not any single station; it is whether the wheel closed. FD-07 is the dataset that makes the wheel close.

### I.2 The problem a loop solves (that running the stations does not)

The problem FD-07 solves is that a pipeline of correct stations is not automatically a loop, and the gap
between "pipeline" and "loop" is precisely where advantage leaks. A pipeline runs A → B → C → D → E → F
and stops; its output is a deposit on disk. A loop runs A → … → F and then *feeds F's result back into A*,
so that the next A starts from a state the previous F improved. The pipeline produces a vault; the loop
produces a rising floor that makes the next pipeline pass cheaper. Running FD-01…FD-06 as a pipeline
gives you classified, triaged, written-back, portability-proven, arbitraged deltas — a full vault — and
leaves the dependence curve exactly where it was, because nothing guaranteed that the write actually
changed the next session's behavior. This is the "stalls into a log file" failure named in the header
and it is the single most common way a learning system fails: it captures diligently and never closes,
so the capture is documentation, not learning.

Three specific leaks appear when the stations run as a pipeline rather than a loop, and each maps to one
of the three flywheel preconditions FD-07 engineers. The first leak is *validity*: a station can execute
flawlessly and still not change behavior — FD-06 can write a beautiful deposit to a graph node no future
session ever navigates to, so the deposit exists but the behavior it should have changed never changes.
A loop is valid only if the write demonstrably alters the next relevant action; a write that changes
nothing is not a loop turn, it is a log entry. The second leak is *closure*: the pipeline's output (a
deposit) is never re-consumed as the next pipeline's input (a risen floor). FD-01 subtracts against the
FD-00 baseline, but if FD-06's write never actually updates that baseline object, then FD-01 next session
subtracts against the *same old floor* and re-extracts the same delta — the classic no-progress loop that
looks maximally productive (deposits every session) while the underlying state (dependence) never moves.
The third leak is *latency*: even a valid, closed loop is worthless as a moat if its cycle time is a
quarter. CWOPS is explicit that a loop reusable only monthly or quarterly is, by the moat literature, not
a closed loop at all; the deposit must be reusable *within the same week* it was captured or the
advantage decays before it compounds. A pipeline has no notion of its own latency; a loop must engineer
for <30-day — and ideally same-week — reuse.

No existing PP system solves the pipeline-to-loop problem because no existing system's job is the
composition. GK-08 writes back at session close but does not verify the write changed behavior; the
learning-sentinel fires when learnings accrue but does not sequence the stations that would close on
them; PM-03 transports findings but does not feed them back as a floor; CO-12 measures dependence but
does not *cause* it to fall. Each is a station or an instrument; none is the operator that turns the
crank and checks the wheel is gaining momentum. FD-07 is that operator, and it is genuinely new as an
operating protocol even though — and this is the honest, load-bearing qualification — it invents no new
plumbing to be it. It rides GK-08's Stop hook as its close-boundary trigger and the learning-sentinel's
accrual signal as its cadence, and orchestrates the six stations that already exist. Its delta over "just
run the stations" is the closed-loop *guarantee*, the boundedness *discipline*, and the compounding
*measurement* — three things a pipeline lacks by construction.

### I.3 Difference from "just running the stations"

The sharpest way to specify FD-07 is to say exactly what it adds to the naive act of running FD-01…FD-06
in sequence, because everything it adds is a guarantee the naive sequence cannot make. First, it adds the
**close verification**: after FD-06 writes, FD-07 asserts the write actually landed where a future
session will consume it (a GK-navigable coordinate, an updated CO-05 asset, a mutated UKDL rule) and that
the FD-00 baseline for that class now *includes* the deposit — so the next FD-01 subtraction genuinely
starts from the risen floor. A naive pipeline writes and trusts; FD-07 writes and verifies the loop
closed. Second, it adds **cadence and boundedness**: it declares *when* the loop turns (rides the
learning-sentinel accrual and the GK-08 Stop boundary), *how many stages it will attempt before
stopping* (a max-step cap so a stuck station cannot spin the wheel forever), *how it detects it is not
making progress* (the state-fingerprint divergence check inherited from FD-00 III.1), and *what `done`
means as a recorded state transition* rather than a vibe. A naive pipeline runs until it errors or a
human stops it; FD-07 runs to a bounded, recorded completion. Third, it adds the **compounding
measurement**: it does not report "six stations ran" as success; it reports whether the CO-12 dependence
metric, the deposit precision, and the portability slope all moved in the direction that proves the wheel
is spinning up. A naive pipeline's success metric is "it ran"; FD-07's is "the floor rose and the next
question got smaller."

The difference is the same one CWOPS draws between a company that ships features and a company that owns a
flywheel. Shipping features (running stations) is table stakes and commoditized; owning a flywheel
(closing the loop, bounding it, measuring its momentum) is the moat. A stack that runs the six stations
perfectly but never verifies closure is a feature factory: it produces deposits the way a feature factory
produces features, and both have diminishing returns because neither compounds. FD-07 converts the feature
factory into a flywheel by adding the one thing a factory lacks — the feedback edge from output back to
input, verified to actually carry signal — and the three disciplines that keep that edge valid, closed,
and fast.

### I.4 What FD-07 does NOT duplicate (explicit)

To satisfy the anti-bloat gate that governs the whole suite, FD-07 names its non-responsibilities in
writing, and the list is longer than any other FD dataset's because FD-07 *composes* the others and the
temptation to re-implement a station inside the orchestrator is the exact bloat the GK-00 "one system, no
parallel systems" law forbids. FD-07 does **not** re-implement any of FD-01…FD-06 — it *sequences* them;
if an edit to FD-07 begins to compute a delta, assign a destination, prove portability, or convert a
routing rule, that logic belongs to the owning station and the edit is out of scope by construction. It
does **not** build a new writeback transport — GK-08 already writes at session close and FD-06 already
routes to the exact stack location; FD-07 *rides* GK-08's Stop hook and *verifies* FD-06's write, it does
not carry the bytes itself. It does **not** build a new metric — CO-12 owns dependence measurement
(model-demotion / Opus-avoided + cognitive-compression ratio); FD-07 *reports the loop's health through
CO-12*, it never stands up a parallel accountant, which would violate SCS C41 and CO-12's own
anti-pattern against a parallel corpus reader. It does **not** build a new trigger — it rides the GK-08
Stop-hook boundary and the learning-sentinel accrual signal, both of which already fire; a session close
and an accrual threshold are events the harness already emits, and FD-07 subscribes rather than
re-implements. It does **not** build a new baseline — the FD-00 floor object is the single shared
baseline every station subtracts against, and FD-07's close verification confirms the write updated *that*
object, never a private copy. Its genuine, defensible delta over the parents it rides is exactly three
things and nothing else: the **closed-loop guarantee** (verified closure, not trusted writes), the
**cadence/boundedness discipline** (bounded "hasta completar" execution), and the **compounding
measurement** (momentum, not volume). Everything else is delegated to a named owner, and the reviewer of
any FD-07 change applies the same test FD-00 prescribes: does this sentence *do* work another system
owns, or does it *orchestrate* that system? Orchestration stays; re-implementation is rejected.

### I.5 The loop definition (stages, owner stations, close-conditions)

The loop is the operational core of FD-07. It is a closed cycle of nine stages; the first six each hand
off to exactly one FD station, the seventh and eighth land in the CO substrate the suite reports through,
and the ninth feeds back to the first — the feedback edge that makes it a loop rather than a pipeline.
Each stage names its owner and its **close-condition**: the observable state transition that proves the
stage actually closed rather than merely ran. A stage that ran without meeting its close-condition has
leaked, and FD-07's close verification (II.1) is precisely the check that every close-condition was met
before the loop is recorded `done`.

| # | Stage | Owner station | Close-condition (the observable transition that proves the stage closed) |
|---|---|---|---|
| 1 | High-leverage question | **FD-02** | A leverage-ranked question set exists and the highest-leverage question is selected; low-leverage/at-floor questions are dropped or routed cheaper. |
| 2 | Admitted frontier call | **FD-00** | The admission clause returned `ADMIT` with a typed `frontier_call_admitted` reason naming why no cheaper rung sufficed — or returned DECLINE/ROUTE_CHEAPER/ANSWER_FROM_ASSET and the loop short-circuits to an honest `DISCARD: at-floor` close. |
| 3 | Delta extraction + classification | **FD-01** | Exactly one typed delta record emitted with a non-null class (`NEW/STRONGER/DUP/DISCARD`), a `capability_summary`, and a `baseline_ref` to the floor it was measured against. |
| 4 | Triage + transmutation | **FD-03** | A destination is assigned (Hard Rule / Process Rule / Trap / dataset Part / benchmark / prompt fragment / asset mutation / discard) and the delta is transmuted to that destination's *form*. |
| 5 | Permanent writeback + reinforcement | **FD-06** | The transmuted form is written to its exact stack location and a GK node (`type: fd_dataset`) with typed edges to its parents exists; cross-system reinforcement fired. |
| 6 | Portability / decay proof | **FD-04** | The deposit's portability target is *tested*, not estimated: the capability reproduces on the declared least-capable substrate against the gold standard, or is honestly relabelled `frontier-only` hypothesis. |
| 7 | Anti-dependence conversion | **FD-05** | A new CO-03 routing rule and/or CO-05 deterministic-or-asset candidate is proposed for the class, so the *next* demand of this class clears at a cheaper rung. |
| 8 | Metric movement | **CO-12** (reported through) | The dependence signals (`frontier_call_admitted`, `delta_deposited`, and the downstream model-demotion / Opus-avoided count) are emitted and the cohort WU/MTok gap is observable. |
| 9 | Floor rise → sharper next question | **FD-00 floor → FD-02** | The FD-00 baseline for the class now *includes* the deposit, so the next session's FD-02 question is compiled against a higher floor and targets a smaller, more precise delta — the feedback edge closed. |

The ninth stage is the whole point and the reason this is a loop. Each turn raises the floor; the risen
floor means the next FD-01 subtraction yields a *smaller* delta (the stack now owns more of what the model
offers for that class); the smaller delta means FD-02's next question must be *more precisely targeted* to
find anything above-floor at all. This is the compounding dynamic stated concretely: the loop does not
produce the same-sized delta each turn — it produces a *shrinking* delta, because it is eating its own
dependence. A loop whose extracted delta does not shrink over turns on a worked class is a loop that is
not closing stage 9 — it is re-extracting against a floor that never rose, the degenerate no-progress case
III.1 exists to catch. The shrinking delta is not decay; it is the visible signature of the moat
compounding, exactly as FD-01 I.7 argues its own falling NEW-rate is the signature of success rather than
failure.

### I.6 The three flywheel preconditions (valid · closed · fast), as engineered gates

CWOPS's central claim is that a feedback loop is a moat only if it is simultaneously valid, closed, and
fast; a loop missing any one of the three is not a moat, it is a cost. FD-07 treats each precondition as
an *engineered gate* with a defined detection for its failure — not as an aspiration. This table is the
core of the dataset: it is where the CWOPS thesis becomes a set of mechanical checks rather than a slogan.

| Precondition | What it demands | How FD-07 engineers it | Detection of its failure |
|---|---|---|---|
| **VALID** | The loop must *improve behavior*, not merely accumulate. A deposit that does not change what the next session does is not a loop turn. | Stage 9 close verification: the deposit must update the FD-00 floor object such that the next FD-01 subtraction demonstrably starts higher; FD-04 must prove the capability transfers, not just that it was written. | The CO-12 cognitive-compression ratio is flat while deposits accrue → deposits are not changing behavior → the loop is capturing but not improving (the a16z empty-data-moat failure). |
| **CLOSED** | Action → capture → *changed behavior*. If behavior does not change, the loop is open — it stalled into a log file. | The feedback edge (stage 9) is verified, not assumed: FD-07 asserts the write landed where a future session consumes it (GK-navigable, CO-05-updated, or UKDL-mutated) and re-reads the floor to confirm the deposit is in it. | A deposit exists on disk but no future session navigates to it / the FD-00 baseline for the class does not include it → the write is documentation, not a closed loop (the "stalls into a log file" failure). |
| **FAST** | Reusable within the same week; <30-day latency. A loop reusable only quarterly is not a closed loop by the moat literature. | Cadence rides the learning-sentinel (fires on accrual, not on a calendar) and the GK-08 Stop boundary (fires every session close), so a captured delta is available to the *next* session, not a scheduled batch. | Time-from-capture-to-first-reuse exceeds one week → the loop's latency has decayed past the CWOPS threshold; the deposit is aging before it compounds. |

The three gates are not independent — a loop can pass two and fail one, and each single failure is fatal
to the moat. A valid, fast loop that is not closed captures excellent deltas quickly and never feeds them
back: a fast log file. A valid, closed loop that is not fast improves behavior and feeds back but on a
quarterly cycle: the advantage decays between turns and never compounds. A closed, fast loop that is not
valid feeds back quickly and often but the deposits do not actually improve behavior (they are DUPs or
at-floor restatements dressed as deltas): a fast, closed *degenerate* loop — the worst case, because it
looks maximally healthy (deposits every session, immediately reused, floor "rising") while the true
dependence metric never moves. FD-07 therefore checks all three gates on every loop turn and treats any
single failure as a defect to diagnose, never a category to accept — the same "no classified FAILs at the
done-gate" discipline the whole suite enforces.

### I.7 Core principles (each with its rationale)

- **The loop is the moat; the answer is a commodity.** FD-07 optimizes the *cycle*, never the artifact.
  Rationale: CWOPS — technical superiority died as a moat in 2026; the durable advantage is the valid,
  closed, fast feedback flywheel a system's own execution deposits, not any feature it ships.
- **Capture without close is a log file, not learning.** A deposit that does not change the next
  session's behavior is documentation. Rationale: the single most common learning-system failure — the
  loop stalls after capture and never closes; only verified closure (stage 9) makes it a loop.
- **`done` is a recorded state transition, not a vibe.** A loop turn is complete when the nine
  close-conditions are recorded met, not when the stations "ran." Rationale: CWOPS §2.3 — the most common
  infinite-loop root cause is `done` defined as a heuristic; FD-07 inherits FD-00's discipline that
  `done` is a written fact.
- **Bounded "hasta completar," never unbounded.** The loop runs to completion but under a max-step cap,
  a state-fingerprint divergence check, and an error-class→action map. Rationale: CWOPS Part II — an
  unbounded loop costs ~1000× a bounded one ($50 vs $0.05); a flywheel that spins without a governor is a
  budget hole, not a moat.
- **Reuse the metric, never re-invent it.** Loop health is CO-12's dependence number, reported not
  rebuilt. Rationale: SCS C41 + CO-12's parallel-reader anti-pattern; a second metric forks the suite.
- **Momentum, not volume.** Success is the *slope* of the dependence curve and the *shrinkage* of the
  extracted delta, never the deposit count. Rationale: the thesis's "nunca volumetría" — a vault that
  doubled its deposits while the CO-12 gap stayed flat got worse, not better.
- **Guard the degenerate-feedback trap.** A loop must never train on its own ranked output. Rationale:
  CWOPS §4.6 — optimizing a proxy (deposit count) instead of the target (dependence reduction) amplifies
  the proxy; FD-07's momentum measurement is the antidote.
- **Honesty over completeness.** An unmeasured loop-health claim is a hypothesis (CO-12 contract); an
  unenforceable guarantee is advisory (CO-10). Rationale: a faked momentum number decays trust in every
  real one, and FD-07's whole value is being trusted to say honestly whether the wheel is spinning up.

---

## Part II — The Operating Contract, Cadence, Interfaces, and Compounding Measurement

### II.1 Operating contract (inputs, outputs, the hard postcondition)

FD-07's contract is a *cross-session* envelope, which is the property that most distinguishes it from
every other FD dataset: FD-00…FD-06 operate within a single session, and FD-07 is the only station whose
unit of work spans sessions, because a loop by definition closes when this session's output becomes next
session's input. Its **inputs** per loop turn are: the set of classified deltas FD-01 produced this
session (via FD-00's deposits); the destinations and forms FD-03 assigned; the writes FD-06 committed; the
portability verdicts FD-04 returned; the arbitrage candidates FD-05 proposed; the FD-00 floor object as it
stood at session start; and the two trigger signals it rides — the learning-sentinel accrual count and the
GK-08 Stop-hook boundary. Its **outputs** are: a **closed-loop verdict** per turn (`CLOSED` with the nine
close-conditions recorded met, or `OPEN:<stage>` naming the first stage whose close-condition failed); the
three **momentum signals** (dependence-slope direction, deposit-precision, portability-slope) reported
*through* CO-12; and a **next-session seed** — the risen floor plus the FD-02 hint that the next question
for this class must target a smaller delta. The contract's single hard postcondition mirrors FD-00's and
extends it across the session boundary: **no loop turn is recorded `CLOSED` unless stage 9 verified the
deposit is in the floor the next session will subtract against.** A turn that wrote a deposit but cannot
verify the floor rose is recorded `OPEN:9` — an honest admission that the wheel did not close — never a
silent success. This is the structural expression of "capture without close is a log file": the verdict
literally cannot be `CLOSED` on an unverified feedback edge.

The verdict carries a fixed schema so CO-12 and the next session's FD-02 can consume it without re-parsing
prose: `{turn_id, class, delta_fingerprint, close_conditions_met[9], loop_verdict, momentum_signals,
next_floor_ref, boundedness_record}`. Each field has an owner: `close_conditions_met` is assembled by
FD-07's close verification from each station's own close-condition report; `momentum_signals` are computed
from CO-12's existing readers, never a parallel calc; `next_floor_ref` points at the FD-00 floor object
FD-06's write updated; `boundedness_record` is the cadence procedure's log of steps taken, fingerprint
divergence, and the recorded `done` transition. A verdict missing `close_conditions_met` or `next_floor_ref`
is rejected — the same "the write is the last stage, never the first" discipline FD-00 III.8 enforces,
applied to the loop close.

### II.2 The cadence and boundedness procedure ("hasta completar" without unbounded burn)

The flywheel must run to completion — a loop that captures a delta and then does not close it is exactly
the failure FD-07 exists to prevent — but "run to completion" is the precise phrasing that, taken naively,
produces the unbounded-loop budget hole CWOPS prices at ~1000× a bounded loop. FD-07 therefore borrows
CWOPS Part II's bounded-loop discipline wholesale and applies it to the distillation cycle. Four
mechanisms bound the loop:

**Cadence (when the loop turns).** FD-07 does not poll and does not run on a calendar. It rides two
existing signals. The **learning-sentinel accrual trigger** fires when enough new learnings have
accumulated (the sentinel's existing >5-new-files threshold), which is the natural cadence for "there is
enough captured delta to be worth closing a loop turn on." The **GK-08 Stop-hook boundary** fires at every
session close, which is the natural cadence for "this session's deltas must be closed before the session
ends, or they leak." The two compose: the Stop hook guarantees no session ends with an un-closed deposit
(the close-boundary), and the sentinel guarantees the cross-session accrual is periodically consolidated
(the accrual cadence). Neither is new plumbing; both already fire. FD-07's contribution is to *subscribe*
the loop close to them.

**Max-step cap (the loop cannot spin forever).** A single loop turn attempts its nine stages at most once
each; a station that fails to meet its close-condition does not get retried indefinitely inside the turn.
If a stage cannot close after its bounded attempt, the turn is recorded `OPEN:<stage>` and the wheel stops
for this turn — the failure is surfaced, not spun on. This is the direct analogue of CWOPS's max-step
cap: a bounded number of iterations, then a recorded stop, never an open-ended "keep trying."

**State-fingerprint divergence detection (the loop must make progress).** The state fingerprint for a
loop turn is `hash(task_class + baseline_ref + delta_class + portability_target)` — the same fingerprint
FD-00 III.1 defines. If successive loop turns on the same class repeat this fingerprint *without the CO-12
gap moving*, the loop is degenerate: it is re-depositing the same capability against a floor that never
rose, the no-progress case. FD-07's boundedness procedure detects the repeated fingerprint and *refuses
further same-class turns* until FD-04 confirms the prior deposit actually downgraded (i.e., stage 6
genuinely closed). This is CWOPS §2.3's divergence check: the failure is almost never an exact error, it
is a *no-progress spin*, and the fingerprint-vs-metric join is what distinguishes a wheel gaining
momentum from a wheel slipping.

**Error-class → action mapping (`done` as a recorded transition).** Each way a stage can fail to close
maps to a defined next action rather than an undefined retry: a stale-baseline failure at stage 3 maps to
"refresh the CO-05 floor and re-subtract" (not "re-ask the model"); a write-verification failure at stage
5 maps to "re-route through FD-06 with the destination re-confirmed" (not "write again blindly"); a
transfer failure at stage 6 maps to "relabel the deposit `frontier-only` hypothesis and queue FD-05
conversion" (not "declare portable anyway"). And `done` is a *recorded state transition*: the turn is
`done` when `boundedness_record` logs either `CLOSED` (nine conditions met) or `OPEN:<stage>` (a named,
surfaced stall) — never an implicit "the stations finished." This is the discipline that makes the loop
"hasta completar" honest: it completes to a *recorded* state, and an open state is a legitimate,
surfaced completion, not a hang.

### II.3 Interfaces with GK-08, the learning-sentinel, and every FD station

- **GK-08 (Stop-hook session writeback)** — FD-07's close-boundary trigger. GK-08 already re-indexes the
  repo at session close; FD-07 subscribes its loop-close verification to that boundary so no session ends
  with an un-closed deposit. FD-07 does *not* write through GK-08 itself (FD-06 does); it *verifies*, at
  the GK-08 boundary, that FD-06's write landed navigably. The relationship is rung-3 at this one point:
  the Stop hook is a real enforcement surface, so the close-boundary check is the sharpest gate FD-07 has.
- **learning-sentinel (accrual trigger)** — FD-07's cadence. The sentinel fires when >5 new learning
  files accrue; FD-07 rides that signal as "there is enough captured delta to consolidate a loop turn."
  It does not re-implement the sentinel's accrual counting; it consumes the signal the sentinel already
  emits (the same signal `/cpp-compound` consumes), which keeps the two consolidation surfaces coherent
  rather than competing.
- **FD-00 (doctrine + floor)** — FD-07 reads the floor object at session start (the baseline stage 9 must
  raise) and honors the eight-stage session protocol; FD-07's nine-stage *loop* is the cross-session
  superset of FD-00's per-session protocol — FD-00 governs a single distillation event, FD-07 governs the
  chain of events. FD-07 confirms stage 9 updated FD-00's floor; FD-00 never re-sequences FD-07's loop
  (one-directional handoff, Invariant 4).
- **FD-01 (extraction)** — supplies the classified delta record that is the loop's stage-3 output; FD-07
  reads the class and the delta fingerprint for the divergence check, never re-classifies.
- **FD-02 (question compiler)** — the loop's stage-1 owner *and* its stage-9 consumer: FD-07 feeds the
  risen floor back to FD-02 so the next question targets a smaller delta. FD-02 is the only station FD-07
  touches on both ends of the loop, which is what makes it a loop and not a line.
- **FD-03 (triage + transmutation)** — supplies the destination + form (stage 4); FD-07 verifies a
  destination was assigned before allowing stage 5, never picks the destination itself.
- **FD-04 (decay / transfer proof)** — supplies the portability *verdict* (stage 6) that FD-07's validity
  gate depends on; a deposit FD-04 has not confirmed portable cannot close the validity precondition and
  is recorded a `frontier-only` hypothesis, excluded from any dependence-reduction claim.
- **FD-05 (anti-dependence arbitrage)** — supplies the CO-03/CO-05 conversion candidates (stage 7); FD-07
  verifies a candidate was proposed for a high-frequency `frontier-only` class, the demand-ranked worklist
  FD-00 II.9's admission log feeds.
- **FD-06 (permanent writeback)** — the loop's stage-5 owner; FD-07 verifies FD-06's write landed at its
  exact stack location with a GK node, but carries none of the write itself.
- **CO-12 (dependence telemetry)** — the instrument FD-07 reports *through*. FD-07 emits no new metric; it
  arranges the loop so CO-12's existing readers observe a moving dependence trend, and it reads CO-12's
  numbers back to compute the momentum verdict. Building a parallel accountant here is the single most
  tempting bloat FD-07 must refuse (I.4).
- **CO-03 / CO-05** — the substrate stage 7 updates: FD-05's converted routing rule lands in CO-03 and its
  deterministic/asset candidate in CO-05, so the *next* demand of the class clears cheaper. FD-07 verifies
  the update was proposed; CO-03/CO-05 own whether to adopt it.
- **PM-03** — the transport the deltas ride between panes; under concurrency (six to ten panes on one
  repo), FD-07 relies on PM-03's consume-before-reason gate so two panes do not each close a loop turn on
  the same delta, exactly as FD-01 III.13 relies on it for extraction.

### II.4 Decision rights and non-decision rights

FD-07 **may decide**: whether a loop turn is `CLOSED` or `OPEN` (the close verification is its right); the
cadence at which loop turns fire (subject to the sentinel and Stop-hook signals it rides); the max-step
cap and the fingerprint-divergence stop (the boundedness discipline); whether a class is in a degenerate
no-progress spin and must be paused; and whether the momentum signals show the wheel spinning up or merely
turning. FD-07 **may not decide**: the *classification* of a delta (FD-01's right); the *destination* of a
deposit (FD-03's right); whether a capability *is* portable (FD-04's right); which *routing rule* to adopt
(CO-03's right); whether an *asset is fresh* (CO-05's right); or the *dependence number itself* (CO-12's
right — FD-07 reports through it, never computes it). The separation is the P-t-E control-flow discipline
from CWOPS §1.3 applied at the loop level: FD-07 is the planner that locks the loop's control flow and
verifies its closure; each station is the tactical executor of one locked stage. FD-07 never reaches into
a station's decision, and no station rewrites the loop's sequence. This is not tidiness; it is the same
indirect-prompt-injection resistance CWOPS attributes to a locked plan — because the loop's control flow
is fixed before any frontier answer arrives, no answer can re-route the loop's own governance (an answer
that says "skip the portability proof" cannot, because FD-07 owns stage 6's gate and the model is an
executor of a locked stage, not the planner).

### II.5 The compounding measurement (proving the wheel spins up, not just turns)

This is the measurement that distinguishes FD-07 from a pipeline runner, and it is deliberately built from
three signals that already exist or are one small emission away, so it can be computed from the corpus
without new instrumentation — the CO-12 discipline of measuring what the disk already supports. A wheel
that *turns* produces deposits; a wheel that *spins up* produces deposits *and* a falling dependence curve
*and* a shrinking extracted delta *and* a rising portable fraction. FD-07 measures all three and requires
them to move together, because any one alone can be gamed.

The first signal is **CO-12's dependence metric** — the model-demotion / Opus-avoided count plus the
cognitive-compression ratio (adopting-cohort WU/MTok ÷ non-adopting). This is the ground truth and it is
*reused, never re-invented*. If it does not move over weeks, the flywheel is not spinning up regardless of
how full the vault looks; this is the metric-decoupling (Goodhart) check, and it is the master signal all
others are subordinate to.

The second signal is **deposit precision** — `above_floor_non_dup_deposits ÷ total_deposits`, the same
ratio FD-00 II.8 defines, targeted ≥ 0.8. A loop can pump deposit *count* while precision falls (storing
DUPs and at-floor restatements to look busy); rising count with falling precision is volume theater and
FD-07 reads precision, not count, as the deposit-side health signal. This is the direct expression of the
thesis's "nunca volumetría."

The third signal is the **portability slope** — `1 − (frontier-only deposits ÷ total)` over time, rising.
This is the signal that proves the loop is *reducing dependence* and not merely *recording* it: a deposit
that stays `frontier-only` is a hypothesis of advantage, not realized advantage (FD-00 II.6), and a loop
whose deposits never downgrade to `deterministic`/`small-model`/`mid-model` is distilling nothing
portable. The portability slope rising is FD-04 and FD-05 doing their jobs inside the loop; flat, and the
loop is capturing frontier-bound trophies.

The compounding claim is the conjunction: the wheel is spinning up iff **the CO-12 gap widens AND deposit
precision holds ≥ 0.8 AND the portability slope rises AND the per-class extracted delta shrinks**. Any
single signal moving alone is a warning, not a win: a widening CO-12 gap with falling precision is luck or
mismeasurement; rising precision with a flat CO-12 gap is careful capture that isn't closing; a rising
portability slope with a flat gap is downgrading deposits nobody re-uses. The four-way conjunction is what
makes the momentum claim honest, and it is why FD-07 never reports "the loop ran" as success — running is
necessary and worthless alone. And every momentum claim carries its `(metric, source, value)` triple or is
labelled a hypothesis, per CO-12's Telemetry-Before-Claims contract: FD-07 may say "dependence for class
`c` fell — source CO-12 model-demotion count, value 3 Opus calls avoided this week vs 0 last week," and it
may *never* say "the flywheel made us Nx faster" without that triple, because an un-triangulated Nx claim
is exactly the faked metric that decays trust in every real one.

### II.6 Token-ROI rules (the loop must cost less than it saves)

FD-07 is itself a cost — the close verification, the boundedness bookkeeping, the momentum computation all
consume tokens — and the doctrine forbids an orchestrator that costs more than the dependence it removes,
the same CWOPS guardrail-economics principle FD-01 II.6 applies to itself. The loop's ROI is measured over
the *class*, not the *turn*, exactly as FD-00 II.5 prices the admission gate over the class: a single loop
turn's overhead is justified only if closing it converts a recurring frontier bill into a near-zero
deterministic or cheaper-rung cost for every future demand of that class. Concretely, if a class is asked
`n` times a month at `k` tokens per frontier answer, a pipeline that never closes pays `n·k` forever; a
closed loop pays `k` (the first answer) + the loop's overhead + `ε` (the near-zero cost of serving the
rest from the distilled replacement FD-05 produced), for a saving of `(n−1)·k − overhead − ε`. The loop is
worth turning iff that saving is positive, which for a frequently-asked class it overwhelmingly is, and
for a one-off class it may not be — so FD-07 prioritizes closing loops on *high-frequency `frontier-only`*
classes (the FD-05 worklist) and lets low-frequency deltas close lazily at the Stop boundary without a
dedicated turn. The boundedness discipline (II.2) is itself an ROI mechanism: the max-step cap and the
fingerprint-divergence stop are what prevent the loop from becoming the ~1000× unbounded-cost hole; a
flywheel with no governor is not a moat, it is the single most expensive way to accumulate a log file.
The close verification runs on the cheapest sufficient substrate — asserting a write landed navigably and
a floor rose is bounded bookkeeping a deterministic check or a Haiku rung handles; only a genuinely
ambiguous "did behavior actually change" judgment warrants anything dearer, and even then FD-04's transfer
test (already paid for at stage 6) is the decisive arbiter rather than a fresh frontier opinion.

### II.7 Portability rules (the loop's output must outlive the model)

A loop turn only counts toward dependence reduction if its deposit outlives the frontier model that
produced it — the suite's north star restated as a loop property. FD-07 therefore makes FD-04's
portability verdict a *gating input to the validity precondition*, not an afterthought: a deposit whose
portability target FD-04 has not confirmed cannot close stage 6, and a turn that cannot close stage 6 is
recorded `OPEN:6` and its deposit is labelled a `frontier-only` hypothesis, explicitly excluded from the
compounding measurement's portability slope. This is the mechanism that keeps the momentum honest — the
portability slope can only rise on *proven* downgrades, never on estimated ones, so a loop cannot inflate
its momentum by optimistically declaring deposits portable. The loop also *drives* portability rather than
merely recording it: stage 7 hands FD-05 the high-frequency `frontier-only` deposits as its conversion
worklist, and a subsequent loop turn on the same class should show the deposit's portability target having
fallen from `frontier-only` toward `mid-model`, `small-model`, or `deterministic` — the visible slope. A
class whose deposits stay `frontier-only` turn after turn is a class the loop is capturing but not
distilling, and III.1's frontier-lock-accumulation diagnosis exists to catch exactly that: the wheel is
turning (deposits accrue) but not spinning up (nothing becomes portable). The portability rule is thus the
sharpest operational expression of "si una capacidad solo funciona con el modelo frontier, todavía no ha
sido destilada" — a loop that never downgrades its deposits has, under the thesis, not closed a single
distillation, only recorded several.

### II.8 No-bloat rules (the loop must not manufacture turns)

FD-07 enforces the same anti-bloat discipline on itself it enforces on the stack, and the specific bloat
an orchestrator is prone to is *manufacturing loop turns to look busy* — closing turns on DUPs, on
at-floor deposits, or on the same fingerprint repeatedly. Three no-bloat rules govern the loop. First, a
turn is only worth closing if its stage-3 delta is `NEW` or `STRONGER`; a `DUP` or `DISCARD` closes the
*session* honestly (per FD-00's deposit clause) but does not trigger a dedicated loop turn, because there
is no delta to feed back — closing a loop on a DUP is spinning the wheel against a floor that already
contains the capability. Second, the state-fingerprint divergence check (II.2) forbids repeated turns on
the same `hash(class + baseline + delta_class + portability_target)` without the CO-12 gap moving; a
repeated fingerprint is the wheel slipping, and FD-07 pauses the class rather than logging another
identical turn. Third, the loop's success is measured by deposit *precision* and the momentum conjunction,
never by turn count — a stack that closed twice as many turns while the CO-12 gap stayed flat did worse,
not better, and FD-07's momentum report makes that legible rather than celebrated. This is the loop-level
mirror of FD-00 II.8's no-bloat rule and FD-01 II.8's earliest-point DUP rejection: just as not every call
deserves a token and not every answer deserves a deposit, not every deposit deserves a loop turn, and the
orchestrator that closes turns for the metric rather than for the dependence curve is Goodharting its own
momentum — the CWOPS §4.6 degenerate-feedback trap at the level of the loop itself.

---

## Part III — Failure Modes, Gates, Benchmarks, Traces, and Evolution

### III.1 Failure modes with diagnosis protocol

The loop's characteristic failures are all variants of one theme — the wheel turns but does not spin up —
and the diagnosis discipline mirrors CWOPS §2.3: the failure is almost never an exact repeated error, it
is a *no-progress spin*, so the diagnosis is always a join between an activity signal (deposits, turns)
and the ground-truth state signal (the CO-12 dependence gap). If activity rises while the gap stays flat,
the loop is failing regardless of how healthy the activity looks.

| Failure mode | Symptom | Diagnosis protocol | Root cause |
|---|---|---|---|
| **Stalls into a log file** (the canonical failure) | Deposits accrue every session; the CO-12 gap is flat; no future session navigates to the deposits | For a sample of deposits, check whether any subsequent session's FD-01 subtracted against a floor that *included* them; if the floor never rose, stage 9 never closed | The feedback edge is open — FD-06 wrote but FD-07 never verified closure; capture without close |
| **Degenerate feedback (Goodhart)** | Turn count and deposit count rising; the CO-12 cognitive-compression ratio not moving | Compare the loop's optimized quantity (deposits/turns) against the target (CO-12 gap); if the two diverge, the loop is amplifying a proxy | Optimizing deposit/turn *count* instead of the dependence curve — the loop training on its own ranked output (CWOPS §4.6): e.g. rewarding "deposits made" the way CWOPS's example rewards deposit *count* over dependence *reduction* |
| **Unbounded spin** | A loop turn runs long / repeats a stage without a recorded `done`; token burn on the class rises with no deposit | Check `boundedness_record` for a max-step-cap breach or a missing `done` transition | The bounded-loop discipline was bypassed — no max-step cap or no fingerprint-divergence stop (the ~1000× cost hole) |
| **No-progress fingerprint loop** | Same `hash(class+baseline+delta_class+portability)` deposited across turns; gap flat | Join the fingerprint stream to the CO-12 gap; a repeated fingerprint with a flat gap is degenerate | FD-06's write never raised the floor, so FD-01 re-extracts the same delta each turn (stage 9 open) |
| **Frontier-lock accumulation** | Deposit count rising; the `frontier-only` fraction not falling; portability slope flat | Slice deposits by portability target over turns; a flat slope means FD-04/FD-05 never ran inside the loop | Stage 6/7 skipped — deposits captured but never proven portable or converted; capturing trophies, not distilling |
| **Slow loop (latency decay)** | Deposits reused only weeks/quarters after capture; the moat never compounds | Measure time-from-capture-to-first-reuse; > 1 week fails the CWOPS fast precondition | Cadence decoupled from the sentinel/Stop-hook — loop turns batched on a calendar instead of riding the accrual/close signals |
| **Volume theater** | Vault growing fast; deposit precision falling; CO-12 cohort gap absent | Read deposit precision (above-floor fraction), not count; check the WU/MTok cohort ratio | No-bloat rule not applied — DUP/at-floor deposits closing turns |

The single most important operational safeguard is the fingerprint-vs-metric join, because it is the one
that distinguishes a compounding loop from a busy one: a loop can *look* maximally productive — a closed
turn every session, the vault growing fast, the floor apparently rising — and be in a perfect no-progress
spin, and only the join between the repeated state fingerprint and the flat CO-12 gap reveals it. When the
join fires, stage 8's momentum gate rejects further same-class turns until FD-04 confirms a real downgrade,
which is the loop-level version of FD-00 III.1's degenerate-loop stop.

### III.2 Anti-patterns with evidence

- **The log-file flywheel.** Running the six stations, writing the deposit, and never verifying the write
  changed the next session's behavior. Evidence: the a16z "empty promise of data moats" — raw accumulation
  without a closed loop has diminishing returns; CWOPS's insistence that a loop is not closed unless
  behavior changes. Forbidden by the stage-9 close verification and the `OPEN:9` verdict; detected by the
  stalls-into-a-log-file diagnosis.
- **Deposit-count Goodharting.** Optimizing how many deposits or loop turns are made rather than the
  dependence curve. Evidence: CWOPS §4.6 degenerate-feedback trap — a loop that trains on its own ranked
  output amplifies a proxy (apparent activity) instead of the target (dependence reduction), the same way
  optimizing deposit count instead of dependence reduction rewards busyness over the moat. Forbidden by the
  momentum-conjunction measurement and the no-bloat rule; detected by the metric-decoupling check.
- **The unbounded wheel.** Letting the loop "run to completion" with no max-step cap, no divergence stop,
  no recorded `done` — spinning on a stuck stage. Evidence: CWOPS Part II's ~1000× cost swing between a
  bounded and an unbounded loop ($50 → $0.05). Forbidden by II.2's four bounding mechanisms; detected by
  the `boundedness_record` audit.
- **The parallel accountant.** Building an FD-07 loop-health metric instead of reporting through CO-12.
  Evidence: SCS C41 ("do not build what already exists") and CO-12's own anti-pattern against a parallel
  corpus reader. Forbidden by I.4 and Invariant 1; detected at review by the "does this sentence do work
  another system owns" test.
- **New plumbing for the trigger.** Building a fresh scheduler/daemon for the loop's cadence instead of
  riding the learning-sentinel and the GK-08 Stop hook. Evidence: the "no n8n, ever" doctrine and the
  automation-mechanism-by-measurement rule — a signal that already fires must be subscribed to, not
  re-implemented. Forbidden by I.4; detected by any new always-on process in the loop's wiring.
- **The frontier-only trophy loop.** Closing turns on deposits that only work with the frontier model and
  counting them as dependence reduction. Evidence: the thesis — "si una capacidad solo funciona con el
  modelo frontier, todavía no ha sido destilada." Forbidden by II.7's portability gate; detected by the
  frontier-lock-accumulation slice.
- **Cadence-on-a-calendar.** Batching loop turns quarterly instead of riding the accrual/close signals,
  so deposits age past the same-week reuse window. Evidence: CWOPS's <30-day, same-week fast precondition —
  a loop reusable only quarterly is not a closed loop. Forbidden by the sentinel/Stop-hook cadence;
  detected by the latency-decay measurement.

### III.3 Quality gates (binary criteria)

- **G1 — Loop closed or honestly open.** Does every loop turn carry a `loop_verdict` of `CLOSED` (nine
  close-conditions recorded met) or `OPEN:<stage>` (a named, surfaced stall)? Binary; a turn with no
  verdict is a defect.
- **G2 — Feedback edge verified.** For every `CLOSED` turn, did stage 9 verify the deposit is in the floor
  the next session subtracts against? Binary; this is the hard postcondition — no `CLOSED` on an unverified
  edge.
- **G3 — Bounded.** Does every turn carry a `boundedness_record` with a max-step-cap outcome, a
  fingerprint-divergence check, and a recorded `done` transition? Binary.
- **G4 — Portability proven, not estimated.** For every turn counted toward the portability slope, did
  FD-04 *test* (not estimate) the deposit's transfer? Binary.
- **G5 — Metric reported through CO-12.** Were the momentum signals computed from CO-12's readers (not a
  parallel calc), and does every advantage claim carry its `(metric, source, value)` triple or the word
  hypothesis? Binary.

A loop turn passes FD-07 iff G1–G5 are all yes. Any `no` is a defect, not a category — consistent with the
"no classified FAILs at the done-gate" doctrine; a genuinely no-delta session passes with an honest
`DISCARD` close (no turn owed), it does not get to skip G2. The gates are deliberately binary and few: a
loop enforced by a long subjective checklist is enforced by nobody, so FD-07 reduces its enforcement to
five yes/no questions the GK-08 Stop hook can answer mechanically in v2.

### III.4 Evaluation rubric (measurable)

| Dimension | Metric | Source | Target |
|---|---|---|---|
| Closure integrity | fraction of loop turns recorded `CLOSED` with a verified stage-9 edge | loop verdict log | rising toward 1.0 |
| Loop validity | CO-12 cognitive-compression ratio movement per closed turn on a class | **CO-12 (reused)** | positive slope |
| Loop latency (fast) | median time from delta capture to first reuse | capture/reuse timestamps | < 1 week |
| Delta shrinkage | trend of extracted-delta size per turn on a worked class | FD-01 `capability_summary` size over turns | falling |
| Portability slope | 1 − (`frontier-only` deposits ÷ total) over turns | deposit portability targets | rising |
| Dependence reduction | model-demotion / Opus-avoided count + cognitive-compression ratio | **CO-12 (reused)** | rising cohort gap |
| Boundedness | fraction of turns with a recorded `done` and no cap breach | `boundedness_record` | 1.0 |
| Deposit precision | above-floor non-DUP deposits ÷ total | FD-01 class distribution | ≥ 0.8 |

The rubric is anchored to signals that already exist or are one small emission away, computed from the
corpus without new instrumentation — the CO-12 discipline of measuring what the disk supports and marking
the rest instrument-pending rather than faking it. The two CO-12-sourced rows are explicitly *reused*, not
re-derived, which is the anti-duplication boundary the whole suite guards.

### III.5 Benchmarks with reference values

Anchored to the sources FD-07 inherits, and this is the dataset where the CWOPS moat-timing figures are
most load-bearing. **Loop economics:** CWOPS documents a ~1000× cost swing ($50 → $0.05) between an
unbounded and a bounded loop — FD-07's boundedness discipline is the direct analogue, and the reference
expectation is that closing a loop on a high-frequency class drops its recurring frontier bill to ~zero on
re-ask once FD-05 has produced the deterministic replacement. **Flywheel latency (fast precondition):**
CWOPS's valid·closed·<30-day rule sets the benchmark that a deposit must be reusable *within the same week*
it is captured, not quarterly; a deposit that cannot be reused for a month is, by the moat literature, not
a closed loop — so FD-07's latency target is < 1 week, hard-failing at 30 days. **Moat timing (the
central benchmark):** CWOPS's **18–36-month** figure for a defensible feedback flywheel sets the honest
expectation that dependence reduction is a slope measured over *many months*, not a single-session or
single-quarter win. FD-07 does not promise a fast collapse of dependence; it promises a reliably negative
`dD/dt` that, sustained over the 18–36-month window, produces a moat a competitor cannot replicate over a
weekend because they cannot replicate the *accumulated floor* the loop deposited across that window. This
number is the antidote to over-claiming: any FD-07 report that implies the flywheel produced a moat in
weeks is dishonest against the CWOPS reference, and any report that abandons the loop because dependence
did not collapse in a month is impatient against it. **Adoption floor:** CO-12's readiness ladder
(2×/3×/4×) supplies the concrete gate — FD-07's closed turns feed the 4× tier's asset-writeback rate, and
the loop is "working" only when that rate and the cohort WU/MTok gap both move. **Precision floor:**
deposit precision ≥ 0.8 is the internal benchmark below which the no-bloat rule is presumed lapsed and the
loop is manufacturing turns. **Commoditization reference:** CWOPS's ~90%-of-features-are-weekend-replicable
figure is the benchmark that justifies the entire loop-is-the-moat thesis — it is *why* FD-07 optimizes
the cycle and not the artifact, because the artifact's defensibility is, by that figure, approximately
zero.

### III.6 Example operational traces (one full loop turn)

**Trace A — one full closed turn (the canonical success).** Session on the KobiiCraft repo. **Stage 1
(FD-02):** the question compiler ranks candidate questions and selects "design a pane-isolation scheme
that survives a mid-session rebase," dropping three at-floor questions. **Stage 2 (FD-00):** the admission
gate returns `ADMIT` with the typed reason "floor silent on rebase-safe isolation; CO-03 sub-frontier
rungs insufficient — prior Sonnet attempt failed this exact class (logged)." **Stage 3 (FD-01):** the
frontier answer is reduced to a 3-rule protocol; the baseline (PM-02 collision detection) is silent on
rebase-safety; classified `NEW`, confidence 0.8, portability estimate `mid-model`, delta fingerprint
recorded. **Stage 4 (FD-03):** triaged to a new dataset Part + a Process Rule; transmuted to the
rule-form. **Stage 5 (FD-06):** written to its stack location; a GK node `type: fd_dataset` with edges to
PM-02 and CO-03 exists; cross-system reinforcement fired. **Stage 6 (FD-04):** the portability target
`mid-model` is *tested* — the protocol reproduces acceptable output on Sonnet against the gold standard;
target confirmed, not merely estimated. **Stage 7 (FD-05):** a CO-03 routing rule is proposed so the next
rebase-isolation demand routes to Sonnet, not Fable; a CO-05 checklist-asset candidate is filed. **Stage 8
(CO-12):** `frontier_call_admitted` and `delta_deposited` emitted; the model-demotion count for this class
increments (next demand is Sonnet-routable). **Stage 9 (floor → FD-02):** FD-07 verifies the FD-00 floor
for the pane-isolation class now *includes* the deposit; the next session's FD-02 question for this class
must target the residual gap (the rebase edge case the protocol left open), a *smaller* delta. `boundedness_record`:
nine conditions met, `done: CLOSED`. This turn spun the wheel *up* — the floor rose and the next question
shrank.

**Trace B — the stall caught (log-file failure surfaced).** Same six stations run; FD-06 writes the
deposit. But at **stage 9**, FD-07's close verification finds the FD-00 floor for the class does *not*
include the deposit — the write landed at a graph coordinate no FD-02 route navigates to. Verdict:
`OPEN:9`. The turn is *not* recorded `CLOSED`; the deposit is flagged as an un-closed capture, and the
error-class→action map routes to "re-route through FD-06 with the destination re-confirmed against a
GK-navigable coordinate." This is the canonical failure caught *before* it became a silent log file — the
whole reason G2 is the hard postcondition.

**Trace C — the degenerate spin stopped.** Third loop turn in a week on the same "config-formatter"
class; the state fingerprint `hash(class+baseline+delta_class+portability)` repeats and the CO-12
cognitive-compression ratio has not moved. FD-07's fingerprint-divergence check fires: the loop is
re-depositing a capability the floor already holds. The turn is refused as no-progress and FD-04 is flagged
to prove whether the *first* deposit actually downgraded. The wheel is stopped before it becomes volume
theater — the loop-level analogue of FD-00 Trace C.

**Trace D — portability drives the next turn.** A prior turn deposited a `frontier-only` capability
(confidence high, but no cheaper substrate proven). This turn, stage 7's FD-05 conversion has produced a
deterministic recipe for it; stage 6 re-tests and the portability target falls from `frontier-only` to
`deterministic`. The portability slope rises; the CO-12 model-demotion count increments (the class now
needs no model at all). Dependence *fell* not because a new delta was captured but because an old one was
*distilled* — the loop closing on its own backlog, which is exactly the compounding dynamic.

**Trace E — honest at-floor, no turn owed.** Session answers "explain OAuth PKCE." FD-01 classifies
`DISCARD: at-floor`. No loop turn is triggered (no delta to feed back); the session closes honestly with
the discard recorded. FD-07 does *not* manufacture a turn to look busy — the no-bloat rule protecting the
loop from a turn with nothing to compound.

### III.7 Edge cases

- **Multi-delta session, multiple turns.** One session produces several NEW/STRONGER deltas across turns;
  each closes an independent loop turn with its own fingerprint, and G2 requires each to verify its own
  stage-9 edge — one session can close several loop turns, but each must close on its own.
- **Concurrent panes, shared floor.** Six-to-ten panes on one repo each running loops against the same
  rising floor. FD-07 relies on PM-03's consume-before-reason gate so two panes do not close a turn on the
  same delta; a delta another pane just published is part of the floor a concurrent pane subtracts against,
  and the RedundancyTax blocks the duplicate close — no new coordination layer, per FD-01 III.13.
- **`OPEN` turn at session close.** A session ends with a delta captured but a stage un-closed. The GK-08
  Stop-hook boundary records `OPEN:<stage>` honestly rather than forcing a false `CLOSED`; the next session
  resumes the open turn from the recorded stage, so the capture is not lost but is not falsely counted.
- **Class fully distilled (terminal state).** A class whose deposits have all downgraded to `deterministic`
  and whose CO-12 dependence has reached a durable floor no longer triggers loop turns — the loop has done
  its job for that class and narrows to novelty-only, the intended terminal state of any distillation
  system (it works itself toward irrelevance for what it has fully distilled).
- **Contradicting deposit.** A new delta contradicts a prior deposit the loop closed. FD-06's mutation
  path supersedes the old deposit with a back-reference (never silent-delete), and FD-07 re-verifies stage
  9 against the superseded floor — the append-with-supersede discipline UKDL uses.
- **Stale floor at loop start.** If the CO-05 baseline was amber at session start, a `NEW` this turn is
  provisional; FD-07 requires a refreshed floor before recording `CLOSED`, per FD-00 III.1 baseline-drift.
- **Sentinel silent but session closing with a delta.** If the learning-sentinel accrual threshold has not
  fired but a session closes with a captured delta, the GK-08 Stop boundary still closes the turn — the two
  triggers are a floor (Stop-hook: every close) and a cadence (sentinel: on accrual), and the floor
  guarantees no delta leaks even when the cadence is quiet.

### III.8 Writeback rules

FD-07 does not itself write a deposit — FD-06 does; FD-07 *verifies the write closed the loop*. Its rule:
a loop turn reaches `CLOSED` only after FD-06 has written to the exact stack location, FD-04 has confirmed
(not estimated) portability, FD-05 has proposed the conversion, CO-12 has received the signals, and — the
gating check — stage 9 has verified the FD-00 floor now includes the deposit. What FD-07 *does* write is
its own turn record: the `loop_verdict`, the `close_conditions_met[9]`, the `momentum_signals`, the
`next_floor_ref`, and the `boundedness_record` — and this record is itself governed by the deposit
discipline, routed through the GK-08 Stop hook at the close boundary, carrying no raw frontier prose (all
of which was reduced away at FD-01's stage 1). FD-07 forbids recording a `CLOSED` verdict that a future
session cannot act on: the turn record must name the `next_floor_ref` a future FD-02 will subtract against,
or the write fails — the loop-level expression of "the write is the last stage, never the first."

### III.9 Conceptual regression tests

- **R1 — Closure verified.** Feed a turn whose FD-06 write landed at a non-navigable coordinate; assert the
  verdict is `OPEN:9`, not `CLOSED`.
- **R2 — Stall detected.** Feed a session that captures a delta and skips stage 9; assert the turn is
  recorded `OPEN` and the deposit flagged un-closed, never silently `done`.
- **R3 — Degenerate spin stopped.** Feed three same-fingerprint turns with a flat CO-12 gap; assert the
  fingerprint-divergence check refuses the third and flags FD-04.
- **R4 — Boundedness holds.** Feed a stage that cannot close; assert the max-step cap records a `done`
  transition to `OPEN:<stage>` rather than spinning, and the `boundedness_record` shows the cap outcome.
- **R5 — Portability gated.** Feed a turn counting an *estimated* (untested) portability toward the slope;
  assert it is excluded until FD-04 tests it.
- **R6 — Metric reuse holds.** Assert the momentum signals are computed from CO-12's readers and no
  parallel dependence calc exists.
- **R7 — No-bloat holds.** Feed a `DUP` delta; assert no dedicated loop turn is manufactured.
- **R8 — Cadence rides existing triggers.** Assert the loop fires on the learning-sentinel accrual and the
  GK-08 Stop boundary, with no new scheduler/daemon introduced.

Per SCS C41, these are gate assertions for the EXECUTION-mode harness, not auto-generated unit tests; the
momentum and latency metrics are measured against the live corpus, which is the honest observation the
anti-test-theater rule requires.

### III.10 Done criteria (verifiable)

FD-07 is done when: the dataset exists on disk, un-truncated, at > 2,800 real words/Part across three
Parts; the nine-stage loop names exactly one owner station per stage (or the CO substrate it reports
through) with zero mechanics duplicated from a parent; the three flywheel preconditions (valid/closed/fast)
are specified as engineered gates each with a named failure detection; the cadence is declared as *riding*
the learning-sentinel and the GK-08 Stop hook (no new plumbing); the boundedness discipline names the
max-step cap, the fingerprint-divergence stop, and `done` as a recorded transition; the compounding
measurement is declared as the four-way conjunction reported *through* CO-12 (not re-invented); G1–G5 are
binary; the stalls-into-a-log-file and degenerate-feedback failures are both diagnosed; and the
V-FD-NO-CODE check finds zero code fences. Verified against the FD_INDEX V-gate scorecard and the
`PR-FABLE-DELTA-ONLY-001` seal.

### III.11 Upgrade path

- **v1 (this dataset):** the composed operating loop as rung-2 orchestration + rung-3 close-boundary,
  advisory for cadence and boundedness; the loop verdict, momentum conjunction, and boundedness record
  specified as the turn schema.
- **v2 (EXECUTION-mode):** wire the stage-9 close verification into the GK-08 Stop hook so `OPEN:9` is
  *enforced* (a session cannot record a false `CLOSED` on an unverified edge), and wire the
  fingerprint-divergence stop into the loop-turn dispatch so a degenerate spin is blocked, not advised —
  the same advisory→hook maturation CO-08, PM-02, and FD-00's own admission gate went through.
- **v3:** momentum auto-reporting — the CO-12 readers surface the four-way conjunction as a leading-
  indicator readiness signal without a manual pull; and cadence auto-tuning — the learning-sentinel
  threshold adapts to the class's demand frequency (a high-frequency `frontier-only` class closes loops
  more eagerly than a rarely-asked one), the ROI discipline of II.6 made automatic.
- **Deprecation trigger:** if CO-12's dependence metric shows the `frontier-only` fraction has fallen to a
  durable floor across all the Owner's active task classes, the flywheel has done its compounding job — the
  loop narrows to novelty-only turns and its surface shrinks, the intended terminal state of any
  distillation loop: it spins itself toward irrelevance for the classes it has fully distilled, exactly as
  FD-00's admission gate and FD-01's classifier narrow toward their own success. The moat, by then, is the
  accumulated floor the 18–36 months of closed loops deposited — which is the one thing a competitor with
  the same frontier model cannot replicate over a weekend, because they can copy the answer and never the
  loop that turned it into a floor.
