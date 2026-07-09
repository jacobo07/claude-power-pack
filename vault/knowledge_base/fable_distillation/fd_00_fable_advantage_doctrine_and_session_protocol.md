# FD-00 — Fable Advantage Doctrine & Session Operating Protocol

> The root law of the Fable Advantage Distillation Suite and the sibling of CO-00. CO-00 caps what a
> session may *spend*; FD-00 governs what a session must *keep*. It absorbs the S-PROTOCOL candidate:
> the per-model operating manual that turns an ordinary Fable session into a distillation event.
> **Delta-Only is the law; the session protocol is how the law is obeyed turn by turn.**
> Sealed under **SCS C82**. Guarantee level (CO-10 honest): **rung-2 doctrine + rung-3 wrapper**
> where the protocol's preflight is enforced by the kclaude launch surface, rung-1 advisory elsewhere.

---

## Part I — Mission, the Delta-Only Law, and What This Is Not

### I.1 Mission

FD-00 exists to make one sentence enforceable across every session that touches a frontier model:
*spend frontier tokens only on the delta, and never let the delta leave the session unwritten.* The
delta is the capability a frontier model demonstrates **above** the floor the Claude Power Pack can
already reach on its own — through CO-03 routing, CO-05 cached and deterministic assets, GK
navigation, or a prior distilled protocol. Everything at or below that floor is, by definition, not
worth a frontier token: the PP can produce it more cheaply, more repeatably, and with zero
dependence on the model of the week. FD-00 is the doctrine that names this boundary and the
operating protocol that walks a session across it without waste.

The mission is deliberately narrow because the thesis is deliberately austere. The suite does not
try to make the PP *better at using* frontier models; three sealed families already do that (CO for
cost, PM for coordination, GK for knowledge location). FD-00's mission is to make the PP **less
dependent** on frontier models over time — to convert each interaction into infrastructure so that
the same class of work, next month, needs a smaller model, a cached asset, or no model at all. The
measure of success is therefore not throughput and not answer quality; it is the slope of the
dependence curve. A session that produced a brilliant answer but left the stack exactly as dependent
as before has, under this doctrine, failed its distillation obligation even if it succeeded at its
surface task. This is the single most counter-intuitive commitment in the suite and the reason a
separate doctrine dataset is warranted: every other family rewards a good answer; FD-00 rewards a
good answer *that made the next answer cheaper*, and treats the two as different events.

The dependence curve deserves a precise definition because the whole suite is oriented to bend it.
For a given task class `c`, define dependence `D(c, t)` as the probability that, at time `t`, the PP
must invoke a frontier model to satisfy a request of class `c` at acceptable quality. `D(c, 0)` is
the starting state — for a novel class it is near 1.0. Each successful distillation event lowers
`D(c, t)` by moving some fraction of the class's demand to a cheaper substrate (a deterministic
recipe, a cached asset, a Sonnet-runnable protocol). FD-00's mission, stated formally, is to make
`dD/dt` reliably negative across the classes the Owner actually works in. Not zero — negative. A
suite that holds `D` flat while accumulating deposits is failing regardless of how full the vault
looks, and Part III's metric-decoupling check exists precisely to catch that failure.

### I.2 The Delta-Only Law (FD-00 root law)

The root law reads, verbatim and inheritable by every FD dataset: **"When a frontier model is
available, spend its tokens only on what the existing PP systems cannot already produce. If the PP
can produce the result — by routing, asset reuse, navigation, determinism, or a prior distilled
protocol — the frontier model is not invoked. Every frontier interaction that *does* occur must
deposit a classified delta before the session closes."** This is sealed separately as
`PR-FABLE-DELTA-ONLY-001` in UKDL so it survives independently of this dataset.

The law has two clauses and they are equally binding. The **admission clause** ("spend only on the
delta") is a gate *before* the call — it is the same reversibility-aware branch the CWOPS engine
draws from the JACM agent-transformer: low-value, already-answerable queries take the cheap path;
only genuinely novel demand triggers the expensive model. The **deposit clause** ("deposit a
classified delta before close") is a gate *after* the call — it is the CWOPS "define `done` as a
recorded state transition" discipline applied to learning: a Fable session is not `done` when the
answer is delivered, it is `done` when the delta the answer contained has been extracted, classified,
and handed to the triage layer. A session that satisfies the admission clause but skips the deposit
clause is the exact degenerate case FD-00 is built to forbid: a frontier token was spent on a real
delta, and the delta evaporated at session end — a moat's worth of capital treated as a log line.

Both clauses are asymmetric in cost, and the asymmetry is the reason the law is worth enforcing
mechanically rather than trusting to good intentions. A wrongly-*declined* call costs one retry: the
session notices the cheap path was insufficient and escalates, a bounded and self-correcting error.
A wrongly-*admitted* call costs the recurring frontier bill for that entire class every time it is
asked again, because nothing was distilled to replace it — an unbounded, silent, compounding error.
Symmetrically, a missed deposit is not a one-session loss; it is the loss of every future session
that would have started from the higher floor that deposit would have created. FD-00 therefore
weights the gates toward *declining* on the admission side and *forcing* on the deposit side: it is
cheaper to occasionally under-call and over-capture than the reverse.

### I.3 The problem this solves (and why it is not already solved)

The PP today captures *findings* (PM-03), it captures *graph nodes* (GK-08), it routes *cost*
(CO-03), and it measures *adoption* (CO-12). None of these asks the one question that separates a
distillation system from a note-taking system: **what capability did this response demonstrate that
the stack did not already have?** PM-03 will happily store a brilliant answer and a trivial one with
identical fidelity; it has no notion of "above the floor." GK-08 will write both to the graph as
coordinates; it has no notion of novelty. CO-12 will count that a frontier call happened and whether
a cheaper rung was available, but it does not ask whether the *content* of that call was worth
keeping. The result is a vault that grows in volume without growing in *advantage* — the a16z "empty
promise of data moats" failure, where raw accumulation has diminishing returns because it is not the
compounding, valid, closed loop that actually defends.

The gap is structural, not incidental, and that is why a new dataset rather than a patch to an
existing one is the honest answer. Each existing system is optimized for a different unit: CO for the
token, PM for the pane, GK for the coordinate. The delta is a fourth unit — a *differential* between
two capability states (the stack's floor and the model's output) — and no existing system holds a
representation of the stack's floor to subtract from. FD-00 introduces that representation (the
CO-05-derived baseline surfaced at preflight) and makes the subtraction the point of the session.
Everything downstream — FD-01's classification, FD-04's decay test, FD-05's arbitrage — depends on
this baseline existing; without FD-00 declaring it, the delta cannot even be named.

FD-00 solves the problem by making the delta the unit of account. It reframes every frontier session
from "get an answer" to "capture the advantage that answer proves the model has and the stack lacks."
The reframe is what makes the downstream datasets coherent: FD-01 can only extract a delta once
FD-00 has defined the floor it is measured against; FD-05 can only reduce dependence once FD-00 has
declared that reduction is the goal rather than a side effect; FD-07 can only close a loop once FD-00
has defined what a completed distillation *is*. In dependency terms, FD-00 is the axiom the other
seven datasets are theorems of.

### I.4 Difference from existing systems

Three differences are load-bearing and each maps to a specific parent the doctrine refuses to
duplicate.

**Versus CO-00 (Hard Context Budget Contract).** CO-00 is a *ceiling* — it stops a session from
exceeding 60% effective context, defended from the 45–55% action band. FD-00 is a *filter and a
floor* — it decides which spend is worthwhile in the first place and guarantees a minimum deposit of
captured advantage. CO-00 asks "can we afford this?"; FD-00 asks "is this worth a frontier token, and
did we keep what it bought?" They compose cleanly and never overlap: CO-00 bounds the envelope
(quantity of spend), FD-00 governs the *quality* of the spend (was it on the delta) and the
*retention* of its product (was the delta kept). A session can be well inside CO-00's ceiling and
still be a total FD-00 failure — plenty of budget, spent entirely at-floor, nothing deposited.

**Versus CO-12 (Cognitive Readiness Telemetry).** CO-12 *measures* whether the machinery designed to
save reasoning is actually consulted, and it already houses the model-demotion / Opus-avoided count
and the cognitive-compression ratio — the exact numbers FD-00 uses as its dependence metric. FD-00
does not re-measure; it *reuses* CO-12's metric and adds the upstream behavior CO-12 can then
observe. The relationship is deliberate and is the sharpest anti-duplication boundary in the suite:
CO-12 is the instrument, FD-00 is the discipline the instrument measures. Building a parallel
accountant would violate SCS C41 and CO-12's own anti-pattern against a parallel corpus reader.
Concretely, FD-00 emits two new session-level signals (`frontier_call_admitted`, `delta_deposited`)
into the corpus CO-12 already reads; CO-12's existing readers turn them into the dependence trend
with no new reader stood up.

**Versus the session-handoff-protocol skill.** That skill is a *generic* end-of-session checklist
that compounds learning on a tracked project — it updates session-state, progress, standards, and
blockers. FD-00's protocol is *model-specific and delta-specific*: it prescribes preflight against
the CO-05 baseline, high-leverage question selection (FD-02), delta classification at each answer
(FD-01), and a deposit gate that will not let the session close with an unwritten delta. Generic
closure is necessary but not sufficient; a project can be perfectly handed off and still have leaked
every delta it produced. FD-00 is the frontier-session specialization that the generic handoff does
not and should not contain.

### I.5 What FD-00 does NOT duplicate (explicit)

To keep the anti-bloat gate satisfied, the doctrine names its non-responsibilities in writing.
FD-00 does **not** implement cost routing (CO-03 owns the Vault→asset→deterministic→Haiku→Sonnet→
Opus cascade), does **not** implement the asset registry or deterministic replacement (CO-05), does
**not** implement the findings transport (PM-03), does **not** implement graph writeback mechanics
(GK-08), does **not** implement the readiness metric (CO-12), and does **not** implement the
insight→destination decision tree (compound-learnings). FD-00 is doctrine and protocol only: it
*declares the law, sequences the session, and defines done*. Every mechanical action the protocol
prescribes is delegated to a named parent or a downstream FD dataset. If a future edit to FD-00
begins to re-specify routing logic, asset freshness, or graph mechanics, that edit is out of scope
by construction and must be relocated to the owning system. This clause is itself a quality gate:
the reviewer of any FD-00 change asks "does this sentence *do* work another system owns, or does it
*orchestrate* that system?" — orchestration stays, re-implementation is rejected.

### I.6 Core principles (each with its rationale)

- **The delta is the unit of account.** Volume is not progress; classified, above-floor deltas are.
  Rationale: a16z's empty-data-moat finding — accumulation without a closed loop has diminishing
  returns; only the differential compounds.
- **`done` is a recorded state transition, not a vibe.** A session is complete when the delta is
  written. Rationale: CWOPS §2.3 — the most common infinite-loop root cause is `done` defined as a
  heuristic rather than a written fact; the same discipline prevents the "answer delivered, delta
  lost" failure.
- **Admission before brains, deposit before close.** The two clauses of the root law bracket every
  frontier call. Rationale: the cost asymmetry of I.2 — cheap to under-call, expensive to
  over-admit; cheap to over-capture, expensive to miss a deposit.
- **Reuse the metric, never re-invent it.** Dependence reduction is CO-12's number; FD feeds it.
  Rationale: SCS C41 + CO-12's parallel-reader anti-pattern.
- **Honesty over completeness.** An unmeasured advantage is a hypothesis (CO-12 contract), and an
  unenforceable guarantee is labelled advisory (CO-10). Rationale: a faked metric is worse than a
  missing one because it decays trust in every real one.
- **Portability is the proof of distillation.** A capability that only works with the frontier model
  is not yet distilled (FD-04 is the test). Rationale: the thesis verbatim — "si una capacidad solo
  funciona con el modelo frontier, todavía no ha sido destilada."

### I.7 The floor, concretely: what "above the floor" means

Because the entire suite pivots on the word "delta," the floor it is measured against must be a
concrete, retrievable object and not a rhetorical gesture. The floor for a task class `c` is the
union of four things the PP can already produce for `c` without a frontier call: (1) the CO-05 asset
set — every registered deterministic recipe, cached answer, and template whose freshness verdict is
green for `c`; (2) the CO-03 sub-frontier envelope — what a Haiku or Sonnet rung can produce for `c`
at acceptable quality, as evidenced by prior successful routings; (3) the GK-navigable knowledge —
anything the graph already holds a coordinate for, retrievable rather than re-derived; and (4) the
prior FD deposits for `c` — capabilities already distilled in earlier sessions. FD-00's preflight
stage assembles exactly this union into the one-screen baseline, and FD-01 subtracts a frontier
answer from it to compute the delta.

The subtraction is not string comparison; it is capability comparison, and the distinction is what
keeps the suite honest. Two answers can share no words and yet be the same capability (the model
paraphrased a recipe the floor already contains), and two answers can share most of their words and
yet differ by a real capability (the model added the one constraint that makes the recipe correct
under concurrency). FD-01 owns the comparison logic; FD-00's contribution is to guarantee the floor
object exists and is fresh before the comparison is attempted. A worked example makes the boundary
concrete: asked to "write a function that dedups a list," the floor already contains the recipe
(SHA-256 content-hash dedup is a known CO-05 pattern), so a frontier answer restating it is at-floor
and discarded; asked to "dedup a list where equality is semantic, not byte-identical, under a token
budget," the floor is silent, and a frontier answer that supplies the semantic-equality-under-budget
strategy is a genuine delta. The word "dedup" appears in both; only one is above the floor. This is
why the floor must be loaded, not imagined — a session that skips preflight will call the first case
a delta because it never checked what the stack already knew, and the entire dependence curve is
corrupted by that one skipped step. The floor is the axis of the whole suite, and I.7 exists to make
it an object rather than an intuition.

One further consequence follows from treating the floor as a live object: the floor *rises* every time
the suite deposits, which means the same frontier answer that was a delta last month may be at-floor
this month because a prior session already distilled it into the baseline. This is the dependence
curve working as designed — as `D(c, t)` falls, the set of demands that clear the admission gate for
class `c` shrinks, and the suite becomes progressively harder to justify calling the frontier model
for. A rising floor that quietly reclassifies yesterday's deltas as today's at-floor is not a bug in
FD-01's comparison; it is the single clearest signal that distillation is compounding, and III.1's
baseline-drift diagnosis exists precisely to distinguish this healthy rise (the floor grew because we
deposited) from the unhealthy one (the floor object went stale and mislabels genuine deltas).

---

## Part II — The Operating Contract and the Session Protocol

### II.1 Operating contract (inputs and outputs)

FD-00's contract is a session-level envelope, not a function call. Its **inputs** are: the session's
declared task; the CO-05 asset baseline for that task class (what can the PP already produce?); the
CO-03 routing verdict (what is the cheapest sufficient model?); the CO-00 context band; and the
active project's UKDL and prior FD deposits. Its **outputs** are: an *admission decision* per
frontier call (invoke / route-cheaper / answer-from-asset / decline); a *sequenced session* that
follows the eight-stage protocol below; and a *deposit guarantee* — at least one classified delta
(or an explicit, recorded `DISCARD` with reason) handed to FD-03 before the session is allowed to
report `done`. The contract's single hard postcondition: **no frontier session closes `done` with an
undeposited delta.** A session that cannot deposit (because the answer was entirely at-floor) closes
`done` only with a recorded `DISCARD: at-floor` note, which is itself a valid, honest deposit.

The deposit carries a fixed schema so downstream datasets can consume it without re-parsing prose.
The mandatory fields are `{task_class, baseline_ref, delta_class, portability_target,
canonical_trace, co12_signals}`, and each has an owner: `delta_class` is assigned by FD-01,
`portability_target` is declared at capture and later confirmed by FD-04, `baseline_ref` points at
the CO-05 asset set surfaced in preflight, and `co12_signals` are the two session signals FD-00
emits. A deposit missing any mandatory field is rejected at the writeback stage — this is the
structural expression of "deposit before close": the write cannot succeed on a malformed deposit, so
a session that produced a real delta but failed to classify or destine it cannot fake completion.

### II.2 Interfaces with existing PP systems

- **CO-00** — FD-00 reads the context band to decide whether a distillation deposit must be
  compressed (Warm band) or may be full (fresh band); it never overrides CO-00's ceiling. When CO-00
  signals the 45–55% action band, FD-00 pre-emptively compresses new deposits so the act of
  depositing does not itself push the session over the ceiling.
- **CO-03** — the admission decision *consults* CO-03's cascade. If CO-03 says a Haiku/Sonnet rung or
  a deterministic rung suffices, FD-00's admission clause declines the frontier call outright. FD-00
  does not second-guess CO-03's model choice; it only asks CO-03 "is anything below frontier
  sufficient?" and treats a yes as a decline.
- **CO-05** — the baseline the delta is measured against; FD-00 hands FD-01 the CO-05 asset set for
  the task class so "above the floor" is a concrete comparison, not a feeling. CO-05's freshness
  verdict matters: a stale asset does not count as a floor, so a delta over a stale asset is still a
  real delta.
- **CO-12** — FD-00 emits, per session, `frontier_call_admitted` (with the reason it was not routed
  cheaper) and `delta_deposited` (class + destination). CO-12 turns these into the dependence-
  reduction trend and the cohort WU/MTok gap.
- **compound-learnings** — the destination decision tree FD-03 extends; FD-00 hands the session's
  deposits to FD-03, which consults that tree.
- **FD-01…FD-07** — FD-00 is the sequencer; each protocol stage below hands off to exactly one
  downstream FD dataset, and the handoff is one-directional (P-t-E: the planner does not reach into
  the executor).
- **kclaude launch surface** — the protocol's preflight is the one stage with a wrapper-level
  enforcement point (rung-3): a Fable session launched through kclaude can be made to print the
  baseline + the leverage-question prompt before the first turn. A bare `claude` session demotes
  preflight to rung-1 advisory and records the unguarded path for the CO-10 un-gated-session audit.

### II.3 Decision rights and non-decision rights

FD-00 **may decide**: whether a frontier call is admitted or declined against the CO-03/CO-05
baseline; the sequence and gating of the session's eight stages; whether a session may report `done`
(the deposit gate); and the compression level of a deposit given the CO-00 band. FD-00 **may not
decide**: which model a call routes to (CO-03's right); whether an asset is fresh enough to serve
(CO-05's right); the *classification* of a delta (FD-01's right); the *destination* of a deposit
(FD-03's right); or whether a distilled capability has decayed (FD-04's right). The separation is
the P-t-E control-flow discipline from CWOPS §1.3: FD-00 is the planner that locks the session's
control flow; the downstream datasets are the tactical executors of each locked stage. FD-00 never
reaches into an executor's decision, and an executor never rewrites the plan. This is not
bureaucratic tidiness — it is the same indirect-prompt-injection resistance CWOPS attributes to a
locked plan: because FD-00's control flow is fixed before the frontier model speaks, no answer the
model produces can re-route the session's own governance (e.g. an answer that says "skip the deposit
step" cannot, because FD-00 owns that gate and the model is an executor of a locked stage, not the
planner).

### II.4 The Fable Session Operating Protocol (the eight stages)

The protocol is the operational core FD-00 absorbs from S-PROTOCOL. It is a locked, ordered
sequence — the "hasta completar" loop of a distillation session, bounded exactly as CWOPS Part II
prescribes. Each stage names its downstream owner and its enforcement rung.

1. **Preflight (baseline load).** Before the first frontier turn, load the CO-05 asset baseline and
   the CO-03 routing verdict for the task class, and surface the active project's prior FD deposits
   for this class. Output: a one-screen "what the stack can already do here" summary. This is the
   floor every subsequent delta is measured against. Enforcement: rung-3 on kclaude, rung-1 elsewhere.
   Failure surface: skipped preflight means every delta is guessed against an imagined floor
   (III.2 preflight-skip).
2. **Context minimization.** Assemble the *minimal* context pack for the task by **referencing
   GK-06** (never rebuilding it). The admission clause is cheaper to satisfy when the model is given
   only the delta-relevant context; a bloated context invites at-floor answers dressed as novel ones,
   because a model given the whole repo will re-derive things the repo already contains and present
   them as insight. Enforcement: rung-1 advisory. Owner: GK-06 (referenced).
3. **Question selection.** Hand off to **FD-02**: compile the leverage-ranked question set
   (irreversible, system-generating, critique, dependence-reducing). The session asks the highest-
   leverage question first; low-leverage questions are the ones most likely to be at-floor and should
   be routed cheaper or dropped. Owner: FD-02.
4. **Admission gate.** For each intended frontier call, apply the root law's admission clause against
   the CO-03/CO-05 baseline. Decline, route-cheaper, or answer-from-asset when the demand is at-floor.
   Enforcement: rung-1 today, rung-2 hook in v2 (II.11 of the upgrade path). Owner: FD-05 supplies the
   arbitrage rules; FD-00 applies them.
5. **Output classification.** For each frontier answer, hand off to **FD-01**: classify the delta as
   `NEW / STRONGER / DUP / DISCARD` against the baseline. This is the deposit clause beginning to fire.
   Owner: FD-01.
6. **Compression.** Compress each captured delta to the CO-00-band-appropriate size (II.7). A deposit
   that will not fit the Warm band is compressed to its contract + trace, not dropped. Owner: FD-00.
7. **Writeback.** Hand off to **FD-03** (destination + form) then **FD-06** (the permanent write).
   The deposit clause completes here: the delta lands in its exact stack location. Owners: FD-03,
   FD-06.
8. **Closure (eval + done gate).** Create the conceptual regression check for the deposited delta
   (FD-04 seed), emit the CO-12 signals, and only then permit `done`. A session with an undeposited
   delta cannot pass this gate. Owner: FD-00 (the gate) + FD-04 (the seed) + FD-07 (the loop close).

### II.5 Token-ROI rules (Fable vs Opus vs deterministic)

The admission clause needs a concrete ladder. FD-00 prescribes the following default preference
order, all subordinate to CO-03's live routing but expressed as *distillation* intent:

| Demand class | Preferred path | Frontier justified only when |
|---|---|---|
| Reproducible transform, known recipe | deterministic rung (CO-05) | never — a deterministic recipe is the distilled endpoint |
| Answerable from a prior FD deposit or CO-05 asset | asset reuse | never — this *is* the reduced dependence working |
| Bounded reasoning, well-specified | Haiku / Sonnet (CO-03) | the cheaper rung has already failed this exact class (logged) |
| Novel architecture, taste, cross-domain synthesis, adversarial critique | frontier (Fable/Opus) | the delta is plausibly above-floor *and* will be deposited |

The rule of thumb, inherited from CWOPS's ~1000× cost differential between bounded and unbounded
loops: **the cost of a wrongly-admitted frontier call is not one token bill — it is the recurring
bill every time that at-floor class is asked again without a distilled replacement.** The ROI of the
admission gate is therefore measured over the *class*, not the *call*. A concrete model: if a task
class is asked `n` times over a month and each frontier answer costs `k` tokens, then admitting all
`n` costs `n·k`; admitting the first, distilling a deterministic replacement, and serving the rest
from it costs `k + ε` where `ε` is the near-zero deterministic cost. The savings is `(n−1)·k − ε`,
which for a frequently-asked class dwarfs the one-time distillation overhead. This is why the
admission gate is worth enforcing even when a single call looks cheap: the gate is pricing the class,
and a class asked twenty times is twenty bills the distillation collapses to one.

### II.6 Model-portability rules

A deposit is only advantage if it outlives the model. FD-00 requires every deposit to declare its
**portability target** at capture time — the least-capable substrate on which the distilled form is
expected to work: `deterministic` (no model at all — a recipe, checklist, or transform), `small-
model` (Haiku-runnable), `mid-model` (Sonnet-runnable), or `frontier-only` (still model-bound). Each
level has a concrete test administered by FD-04: a `deterministic` deposit must reproduce its output
byte-for-byte without any model; a `small-model` deposit must produce acceptable output on Haiku
against the gold standard; and so on. A `frontier-only` deposit is explicitly a *hypothesis of
advantage*, not realized advantage, until FD-04 proves it can be downgraded — it is labelled as such
and excluded from any dependence-reduction claim. The portability target is the field FD-05 reads to
decide what to convert next (it prioritizes high-frequency `frontier-only` deposits for conversion)
and FD-04 reads to decide what to test. The doctrine's north star, restated as a measurable slope:
**the fraction of deposits at `frontier-only` should fall over time**; a suite whose deposits stay
frontier-bound is distilling nothing portable and is, under the thesis, not distilling at all.

### II.7 Compression rules

Compression is subordinate to the CO-00 band and never lossy on the contract. A deposit compresses
in this priority order: (1) drop the model's prose reasoning, keep the *operational contract*
(inputs/outputs/decision rights); (2) drop redundant example traces, keep exactly one canonical
trace; (3) replace narrative with a decision table; (4) reference — never inline — anything GK-06
can navigate to. The invariant: **a compressed deposit must still let a future session reconstruct
the capability without the original model in the room.** If compression would break that invariant,
the deposit is kept larger and the session's CO-00 band, not the deposit's fidelity, is what gives.
Worked example: a frontier answer that spends 1,200 tokens reasoning about a concurrency scheme and
then states a 200-token protocol compresses to the 200-token protocol plus a one-line rationale
pointer — a ~6× reduction that loses nothing reconstructable, because the reasoning was the model's
path to the protocol, not the protocol itself. The test for whether a compression was lossy is
exactly FD-04's transfer test: if the compressed deposit still passes the decay check on the target
substrate, the compression preserved the capability; if it fails, compression cut a load-bearing
detail and must be reverted.

### II.8 No-bloat rules

FD-00 enforces the same discipline on itself it enforces on the stack. A candidate deposit is
rejected as bloat if: it duplicates an existing FD deposit or CO-05 asset (DUP — discard, do not
re-store); it is at-floor (the PP could already produce it); or it is a general fact with no
above-floor delta (a search result, not a capability). The no-bloat rule is the deposit-side mirror
of the admission clause: just as not every call deserves a frontier token, not every answer deserves
a deposit. Deposit precision is defined as `above_floor_non_dup_deposits ÷ total_deposits` and the
suite targets ≥ 0.8; a falling precision is the leading indicator of volume theater and triggers the
III.1 diagnosis. The suite's health is measured by deposit *precision*, not deposit count — the
direct application of the thesis's "nunca volumetría." A vault that doubled its deposit count while
precision fell from 0.9 to 0.5 got *worse*, not better, and the no-bloat rule is what makes that
legible instead of celebrated.

### II.9 The admission decision as a typed contract

The admission clause is the suite's highest-frequency decision and therefore the one most worth
making mechanical rather than judgmental. FD-00 types it as a four-valued verdict over a fixed input
tuple, so it can eventually be a hook rather than a habit. The input is `{task_class, baseline,
co3_verdict, demand_novelty}` where `demand_novelty` is FD-01's cheap pre-classification of whether
the request even *plausibly* exceeds the floor. The output is exactly one of: `DECLINE` (the floor
already covers it — serve from asset or deterministic rung, no model), `ROUTE_CHEAPER` (a sub-
frontier rung suffices per CO-03 — Haiku/Sonnet, no frontier), `ANSWER_FROM_ASSET` (a prior deposit
or cached answer is a direct hit — serve it), or `ADMIT` (genuinely above-floor demand — the frontier
call is justified and a deposit is now owed). The four-valued shape matters: a boolean "call or not"
loses the distinction between "the stack can do this for free" and "a cheaper model can do this,"
and that distinction is exactly where most of the dependence reduction lives — the majority of
wrongly-admitted calls are not "should have been free" but "should have been Sonnet."

The verdict is auditable by construction because it names its reason. Every `ADMIT` writes a
`frontier_call_admitted` reason of the form "floor silent on `<capability>`; CO-03 sub-frontier rungs
insufficient because `<evidence>`," and CO-12 later audits these reasons against the actual CO-03
verdicts to compute admission precision. A session that admits a call whose reason, on audit, reduces
to "I didn't check" is the at-floor-admission failure, and the typed reason is what makes the audit
possible — an untyped "I decided to call the model" is unauditable and therefore forbidden. The
contract also gives the v2 hook a clean surface: a PreToolUse hook on the frontier-model invocation
can compute this exact tuple and downgrade an `ADMIT` to a warning when the baseline plainly covers
the demand, which is the same advisory→enforcement maturation CO-03's own router went through. Until
that hook exists, the typed verdict is the discipline a session applies by hand, and the reason field
is what keeps the hand-applied version honest enough to audit. The four verdicts are also the exact
signal FD-05 needs to prioritize its arbitrage work: a task class that repeatedly returns
`ROUTE_CHEAPER` is one CO-03 already handles well and needs no attention, whereas a class that
repeatedly returns `ADMIT` for the same reason is the prime candidate for a distilled replacement —
the admission log, read over a month, is itself the ranked worklist of what to convert next, which is
why FD-05 consumes it rather than re-deriving demand from scratch.

---

## Part III — Failure Modes, Gates, Benchmarks, and Evolution

### III.1 Failure modes with diagnosis protocol

| Failure mode | Symptom | Diagnosis protocol | Root cause |
|---|---|---|---|
| **Silent evaporation** | session closes `done`, no deposit recorded | grep the session's CO-12 signals for `delta_deposited`; absent → the closure gate (stage 8) was bypassed | deposit clause not enforced; kclaude preflight skipped |
| **At-floor admission** | frontier calls rising, dependence metric flat | join `frontier_call_admitted` reasons against CO-03 verdicts; many admissions where a cheaper rung sufficed | admission gate advisory-only on the bare-`claude` surface |
| **Frontier-lock accumulation** | deposit count rising, `frontier-only` fraction not falling | slice deposits by portability target over time | FD-04 not exercised; deposits never downgraded |
| **Volume theater** | vault growing, dependence metric flat, WU/MTok cohort gap absent | check deposit precision (above-floor fraction) and the CO-12 cohort ratio | no-bloat rule not applied; DUP/at-floor deposits stored |
| **Metric decoupling (Goodhart)** | deposit count and readiness rising, WU/MTok gap not | the CO-12 cognitive-compression ratio is the ground truth; if it does not move, the deposits are not saving | optimizing the deposit count instead of the dependence curve |
| **Baseline drift** | deltas classified NEW that are actually at-floor | re-run FD-01 against a refreshed CO-05 baseline; NEW→DUP reclassifications reveal a stale floor | preflight loaded a stale CO-05 asset set |

The diagnosis discipline mirrors CWOPS §2.3: the failure is almost never an exact repeat, it is a
*no-progress* loop — the suite spins (deposits accrue) while the underlying state (dependence) does
not improve. The state fingerprint for FD is `hash(task_class + baseline + delta_class +
portability_target)`; when deposits repeat this fingerprint without the CO-12 gap moving, the loop
is degenerate and stage 8's eval gate must reject further same-class deposits until FD-04 confirms
a real downgrade. This is the single most important operational safeguard in the doctrine because it
is the one that distinguishes a compounding suite from a busy one: a suite can *look* maximally
productive — deposits every session, vault growing fast — and be in a perfect no-progress loop, and
only the fingerprint-vs-metric join reveals it.

### III.2 Anti-patterns with evidence

- **The brilliant-answer log line.** Evidence: the a16z "empty promise of data moats" — raw
  accumulation without a closed loop has diminishing returns. A session that delivers a great answer
  and stores it as a finding, not a classified delta, is the direct analogue. Forbidden by the
  deposit clause; detected by the silent-evaporation diagnosis.
- **The parallel accountant.** Building an FD dependence metric instead of feeding CO-12. Evidence:
  SCS C41 ("do not build what already exists") and CO-12's own anti-pattern against a parallel corpus
  reader. Forbidden by I.5; detected at review by the "does this sentence do work another system
  owns" test.
- **The frontier-only trophy.** Depositing a capability that only works with the frontier model and
  calling it advantage. Evidence: the thesis — "si una capacidad solo funciona con el modelo
  frontier, todavía no ha sido destilada." Forbidden by II.6; such a deposit is labelled hypothesis
  until FD-04 downgrades it; detected by the frontier-lock-accumulation slice.
- **Deposit-count Goodharting.** Optimizing how many deposits are made rather than the dependence
  curve. Evidence: CWOPS §4.6 degenerate-feedback trap — training on your own ranked output amplifies
  a proxy instead of the target. Forbidden by the no-bloat rule and III.1's metric-decoupling check.
- **Preflight skip.** Starting a Fable session without loading the baseline, so "above the floor" is
  guessed. Forbidden by stage 1; the reason it is rung-3 on kclaude is precisely that advisory-only
  enforcement was empirically skipped in analogous protocols (the same pattern that made CO-08's cap
  a hard wrapper block rather than an advisory).
- **Context maximalism.** Feeding the frontier model the whole repo "to be safe," which invites
  at-floor answers dressed as insight. Evidence: GK-06's minimal-context-pack rationale — a minimal
  pack is not just cheaper, it is *more discriminating*, because the model is not handed the answers
  the repo already contains. Forbidden by stage 2.

### III.3 Quality gates (binary criteria)

- **G1 — Baseline loaded.** Did stage 1 emit the CO-05 baseline before the first frontier turn?
  Binary: yes/no.
- **G2 — Admission logged.** Does every admitted frontier call carry a `frontier_call_admitted`
  reason that names why a cheaper rung did not suffice? Binary.
- **G3 — Deposit present.** Did the session hand FD-03 at least one classified delta, or a recorded
  `DISCARD: at-floor`? Binary; this is the hard postcondition.
- **G4 — Portability declared.** Does every deposit carry a portability target? Binary.
- **G5 — Metric emitted.** Were the two CO-12 signals emitted at closure? Binary.

A session passes FD-00 iff G1–G5 are all yes. Any `no` is a defect, not a category — consistent with
the "no classified FAILs at done-gate" doctrine; a genuinely at-floor session passes with a
`DISCARD` deposit, it does not get to skip G3. The gates are deliberately binary and few: a doctrine
enforced by a long subjective checklist is enforced by nobody, so FD-00 reduces its enforcement to
five yes/no questions a Stop hook can answer mechanically in v2.

### III.4 Evaluation rubric (measurable)

| Dimension | Metric | Source | Target |
|---|---|---|---|
| Admission precision | fraction of frontier calls that were genuinely above-floor | CO-12 `frontier_call_admitted` reasons audited vs CO-03 verdicts | rising toward 1.0 |
| Deposit precision | fraction of deposits above-floor and non-DUP | FD-01 class distribution | ≥ 0.8 |
| Portability progress | 1 − (`frontier-only` deposits ÷ total) | deposit portability targets | rising over time |
| Dependence reduction | model-demotion / Opus-avoided count + cognitive-compression ratio | **CO-12 (reused)** | rising cohort gap |
| Closure integrity | fraction of sessions passing G1–G5 | session gate log | 1.0 |

The rubric is deliberately anchored to signals that already exist or are one small emission away, so
it can be computed from the corpus without new instrumentation — the CO-12 discipline of measuring
what the disk already supports and marking the rest instrument-pending rather than faking it.

### III.5 Benchmarks with reference values

Anchored to the sources FD-00 inherits. **Loop economics:** CWOPS documents a ~1000× cost swing
($50 → $0.05) between an unbounded and a bounded loop — FD-00's admission gate is the direct analogue
for distillation spend, and the reference expectation is that a class with a distilled deterministic
replacement drops from a recurring frontier bill to ~zero on re-ask. **Flywheel latency:** CWOPS's
valid·closed·<30-day precondition sets the benchmark that a deposit must be reusable *within the same
week* it is captured, not quarterly; a deposit that cannot be reused for a month is, by the moat
literature, not a closed loop. **Moat timing:** the 18–36-month figure for a defensible flywheel sets
the honest expectation that dependence reduction is a slope measured over months, not a single-
session win — FD-00 does not promise a fast collapse of dependence, it promises a reliably negative
`dD/dt`. **Adoption floor:** CO-12's readiness ladder (2×/3×/4×) supplies the concrete gate — FD-00's
deposits feed the 4× tier's asset-writeback rate, and a suite is "working" only when that rate and
the cohort WU/MTok gap both move. **Precision floor:** deposit precision ≥ 0.8 is the internal
benchmark below which the no-bloat rule is presumed to have lapsed.

### III.6 Example operational traces

**Trace A — admission decline (the common case).** Task: "reformat this config file." Stage 1
baseline shows CO-05 has a deterministic formatter for this class. Stage 4 admission gate: DECLINE —
routed to the deterministic rung. No frontier token spent; deposit = `DISCARD: at-floor`. Session
`done` with an honest discard. This trace is a *success*: the dependence curve is served by *not*
calling the model, and G3 passes on the discard.

**Trace B — real delta, deposited.** Task: "design a novel isolation scheme for concurrent panes."
Stage 1 baseline shows PM-02 handles collision but not this scheme. Stage 3 asks the leverage
question (FD-02). Stage 4 admits the frontier call (above-floor, novel architecture). Stage 5 FD-01
classifies the answer `NEW`. Stage 6 compresses 1,400 tokens of reasoning to a 220-token protocol +
one trace. Stage 7 FD-03 routes it to a new dataset Part; FD-06 writes it. Stage 8 seeds an FD-04
decay check, portability target `mid-model` (the scheme is expressible as a Sonnet-runnable
protocol), emits CO-12 signals, `done`.

**Trace C — the degenerate loop caught.** Third session in a week deposits the same
`task_class + delta_class` fingerprint; CO-12 cohort gap has not moved. Stage 8 eval gate rejects the
deposit as no-progress and flags FD-04 to prove whether the *first* deposit actually downgraded. The
loop is stopped before it becomes volume theater.

**Trace D — STRONGER, not NEW.** Task: "improve the existing retry policy." Baseline shows CO-05 has
a retry recipe. The frontier answer does not introduce a new capability but materially improves the
existing one. FD-01 classifies `STRONGER`; FD-06 mutates the existing CO-05 asset rather than
creating a new deposit (a dataset mutation, FD-06's UKDL-extend surface). Portability `deterministic`
— the improvement is a recipe change, no model needed to run it. Dependence *falls* because the
better recipe now serves more of the class without escalation.

**Trace E — DISCARD despite a good answer.** Task: "explain how OAuth PKCE works." The frontier
answer is excellent but entirely at-floor — it is general knowledge the PP can retrieve or a smaller
model can produce. FD-01 classifies `DISCARD: at-floor`. No deposit is stored; the good answer is
used for the immediate task and not treated as advantage. G3 passes on the discard. This trace is the
no-bloat rule protecting the vault from a plausible-but-worthless deposit.

### III.7 Edge cases

- **Entirely at-floor session.** Valid; closes with `DISCARD: at-floor`. G3 passes.
- **Delta above-floor but not yet portable.** Deposit with `frontier-only` target + hypothesis
  label; FD-04 owns the follow-up. Not a failure, a staged truth.
- **Context-starved session (CO-00 Warm/Cold band).** Deposit is compressed to contract + trace;
  fidelity of the *capability* is preserved, prose is dropped (II.7).
- **Non-Fable frontier model.** The doctrine is model-agnostic; "Fable" names the role (the frontier
  model in play), not a specific id. A session on Opus 4.8 as the frontier obeys the same law.
- **Bare `claude` (non-kclaude) session.** Preflight demotes to rung-1 advisory; G1 may be `no`
  without a hard block, but the defect is recorded so the dependence audit sees the unguarded path
  (CO-10 un-gated-session honesty).
- **Multi-delta session.** One session may produce several deltas across several turns; each is
  classified and deposited independently, and G3 requires at least one but does not cap the number.
- **Contradicting deposit.** A new delta contradicts a prior deposit (the model revised its own
  earlier advice). FD-06's mutation path supersedes the old deposit with a back-reference, never
  silently deletes it — the same append-with-supersede discipline UKDL uses.

### III.8 Writeback rules

FD-00 does not itself write; it *gates* the write. Its rule: a deposit reaches FD-06 only after FD-03
has assigned a destination and FD-01 has assigned a class, and it carries the mandatory fields
`{task_class, baseline_ref, delta_class, portability_target, canonical_trace, co12_signals}`. FD-00
forbids a "raw answer" reaching GK-08 — everything is classified and destined first. This is the
deposit clause made structural: the write is the *last* stage, never the first, and a malformed
deposit fails the write rather than landing half-formed in the graph.

### III.9 Conceptual regression tests

- **R1 — Delta-Only holds.** Feed a known at-floor task; assert the admission gate DECLINES and no
  frontier signal is emitted.
- **R2 — Deposit gate holds.** Feed an above-floor session and force-skip the deposit; assert stage 8
  refuses `done`.
- **R3 — Portability discipline holds.** Feed a `frontier-only` deposit; assert it is labelled
  hypothesis and an FD-04 follow-up is seeded.
- **R4 — No-bloat holds.** Feed a DUP answer; assert it is discarded, not stored.
- **R5 — Metric reuse holds.** Assert the dependence signals land in CO-12, not a parallel store.
- **R6 — Baseline freshness holds.** Feed a delta over a stale CO-05 asset; assert it is flagged for
  re-classification against a refreshed baseline before deposit.

These are conceptual (architecture-level) checks; per the anti-test-theater rule (SCS C41), they are
specified as gate assertions the eventual EXECUTION-mode harness verifies, never auto-generated unit
tests standing in for real observation.

### III.10 Done criteria (verifiable)

FD-00 is done when: the dataset exists on disk, un-truncated, at >2500 real words/Part across three
Parts; the Delta-Only law is sealed as `PR-FABLE-DELTA-ONLY-001` in UKDL; the eight-stage protocol
names exactly one downstream owner per stage with zero mechanics duplicated from a parent; G1–G5 are
defined as binary gates; the dependence metric is declared as CO-12-reused (not re-invented); and the
V-FD-NO-CODE check finds zero code fences. Verified against the FD_INDEX V-gate scorecard.

### III.11 Upgrade path

- **v1 (this dataset):** doctrine + protocol, rung-1 advisory except kclaude preflight (rung-3).
- **v2 (EXECUTION-mode):** wire the admission gate into CO-03's decision point as a rung-2 hook so an
  at-floor admission is warned in-band; wire the deposit gate into the Stop hook so G3 is enforced,
  not advised. This is the same advisory→hook maturation CO-08 and PM-02 went through.
- **v3:** portability-target auto-suggestion from FD-04 history, so the doctrine proposes the least-
  capable substrate rather than asking the session to declare it; and baseline auto-refresh so III.1
  baseline-drift cannot accrue silently.
- **Deprecation trigger:** if CO-12's dependence metric shows the `frontier-only` deposit fraction has
  fallen to a durable floor across all task classes, FD-00's admission gate has done its job for those
  classes and narrows to novelty-only sessions — the doctrine's own success shrinks its surface, which
  is the intended terminal state of any distillation system: it works itself toward irrelevance for
  the classes it has fully distilled.

### III.12 Cross-suite integration invariants

FD-00 is the axiom the other seven datasets depend on, so a set of invariants must hold across the
whole suite or the doctrine's guarantees are hollow. These are the load-bearing joins a reviewer
checks before sealing any FD dataset. **Invariant 1 — single metric.** Exactly one dependence metric
exists, and it lives in CO-12; any FD dataset that computes its own dependence number is in
violation. Verification: grep the suite for a dependence calculation not sourced from CO-12; expect
zero hits. **Invariant 2 — single baseline.** Every "above-floor" judgment in the suite subtracts
from the same CO-05-derived floor object FD-00 defines; no dataset invents its own notion of the
floor. Verification: each dataset's delta logic references `baseline_ref`, never an ad-hoc baseline.
**Invariant 3 — deposit schema stability.** The six mandatory deposit fields are fixed; a dataset
that consumes deposits reads these fields and no others it invented. Verification: the writeback
rejects a deposit missing any of the six, and no consumer depends on a seventh. **Invariant 4 —
one-directional handoff.** Control flows FD-00 → executors, never executor → FD-00; a downstream
dataset never rewrites the session plan. Verification: no FD dataset contains logic that re-sequences
FD-00's eight stages. **Invariant 5 — honest levels.** Every guarantee in every FD dataset carries a
CO-10 rung and every advantage claim carries the CO-12 triple or the word hypothesis. Verification:
no unqualified "this reduces dependence by N×" statement exists anywhere in the suite.

These invariants are what make the eight datasets one system rather than eight overlapping ones. The
GK-00 root law — "one system, no parallel systems" — applies inside the FD family exactly as it
applies across CO/PM/GK: the moment two FD datasets hold two baselines, two metrics, or two deposit
schemas, the suite has forked and its dependence guarantee is unverifiable. FD-00 owns these
invariants because it owns the axioms they protect; the seal of any later FD dataset is gated on the
five checks passing, and a failing check is a defect to fix before seal, never a deviation to
document. This is the structural reason the doctrine is a separate dataset and the first one built:
it is cheaper to enforce a shared axiom from the start than to reconcile eight divergent ones after
the fact, which is precisely the reconciliation cost the CO/PM/GK families paid down by building
their own index-and-invariants layer first.
