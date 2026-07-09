# FD-04 — Intelligence Decay & Transfer-Proof Detector (S-DECAY)

> The portability proof of the Fable Advantage Distillation Suite. Where FD-01 isolates and classifies
> the delta a frontier answer demonstrates above the stack's floor, FD-04 answers the one question that
> decides whether that delta is actually *distilled* or merely *captured*: does the capability still
> produce frontier-grade quality when re-executed on a cheaper substrate — Opus, Sonnet, Haiku, or a
> deterministic rung? Parents: **CO-12** (Cognitive Readiness Telemetry — it measures cost and adoption;
> FD-04 adds the quality-regression axis CO-12 structurally lacks) and **CDIO-05** (the six-lens
> design-review pipeline, generalized here from *design surfaces* to *any distilled capability*). FD-04
> absorbs two named candidates — the *Fable-Grade Output Comparator* and the *Model Benchmark Transfer
> Harness* — into one section-set. Sealed under **SCS C82**. Guarantee level (CO-10): **rung-2
> empirical measurement gated by HIGH-RISK** — it produces a defensible portability verdict against a
> human-curated gold standard, and it is explicitly forbidden from grading against auto-generated tests
> (the test-theater trap the repo rejected at SCS C41). "Si una capacidad solo funciona con el modelo
> frontier, todavía no ha sido destilada" — FD-04 is the instrument that proves distillation actually
> happened, and its verdict is a hypothesis-killer: a deposit's claimed portability target is a
> conjecture until FD-04 confirms it empirically.

---

## Part I — Mission, the Portability Problem, and the Verdict Taxonomy

### I.1 Mission

FD-04 exists to convert a *claim* of portability into a *proof* of portability. Every delta FD-01
extracts carries a `portability_estimate` — a cheap, shape-based guess at the least-capable substrate
that could run the capability (`deterministic / small-model / mid-model / frontier-only`). That
estimate is the load-bearing input to the entire dependence-reduction axis of the suite: FD-05 reads it
to decide which frontier-only deltas are worth the arbitrage effort of converting to a cheaper rung,
and CO-12's dependence metric only *credits* a demotion once a capability genuinely runs at acceptable
quality one rung down. But an estimate is not evidence. FD-01 itself says so plainly (its II.7 declares
the estimate "a prior to be tested, never a claim"), and FD-04 is the instrument that performs the
test. Its mission is to take a distilled deposit plus its claimed portability target, re-execute the
capability on that target substrate, compare the result to a frontier-grade **gold standard** across
defined quality dimensions, and emit a single typed verdict — **PORTABLE**, **DEGRADED**, or
**INCONCLUSIVE** — that either confirms the deposit's portability or exposes it as a false hypothesis.

The mission is scoped narrowly and deliberately. FD-04 does not classify deltas (FD-01's right), does
not decide destinations or forms (FD-03's right), does not write anything permanent to the stack
(FD-06's right), and does not decide which frontier-only capabilities to prioritize converting (FD-05's
right). It performs one operation that none of those can: it *empirically observes whether a distilled
capability degrades in quality on a cheaper model*. This is the portability proof, and it is the single
most consequential gate in the suite's honesty chain, because it is the only place where a claimed
advantage is subjected to an outcome test rather than a design argument. A suite that classified,
routed, and wrote back deltas without ever proving they survive a model downgrade would be a suite that
*asserts* it is reducing frontier dependence without ever *measuring* whether the reduction is real —
the precise self-deception the CWOPS Unfair Advantage Engine warns against when it insists the moat is
the *valid* loop, not the loop that merely looks closed. FD-04 is the validity check on the whole
flywheel: it is where "we distilled this" stops being a story the suite tells itself and becomes a
number it can defend.

### I.2 The portability problem (and why it is genuinely hard)

Proving that a capability survives a model downgrade is not running the same prompt on a cheaper model
and checking that it does not error. That is the trap FD-04 is built to avoid — it tests "does X still
produce *frontier-grade quality*", not "does X still *run*". The PP already has functional test suites
that answer "does it run"; they pass on output that is syntactically valid and semantically wrong, on a
summary that is fluent and misses the point, on a design that renders and is ugly. The portability
problem is a *quality-regression* problem, and quality regression is hard for three compounding
reasons.

First, quality is multi-dimensional and the dimensions are not fungible. A Sonnet re-execution of a
distilled summarization capability might preserve factual accuracy perfectly while losing the crisp,
non-hedging voice that made the frontier output valuable — high on one axis, collapsed on another, and
a single scalar "score" would hide exactly the failure that matters. This is why FD-04 borrows
CDIO-05's *six-lens* review discipline rather than a one-number verdict: the same reason CDIO refuses
to say "looks better" and instead names a criterion and an observed value (T-DESIGN-OPINION-VS-CRITERIA-001),
FD-04 refuses to say "quality dropped" and instead reports which lens dropped, by how much, against
what reference.

Second, the reference is the hard part, not the re-execution. To say a cheaper substrate's output
*degraded*, you must have something frontier-grade to degrade *from*. That something cannot be
machine-generated — an auto-generated assertion is, at best, a codification of what the machine already
believed the answer should be, and grading a capability against the machine's own expectation is the
degenerate-feedback trap CWOPS §4.6 names: you train the appearance of quality, not quality. FD-04's
gold standards therefore come from human-curated reference examples deposited by the sibling
Gold-Standard-Factory destination (FD-06's writeback surface) and from FD-03's benchmark deposits —
outcome data from an instrumented process, weighted toward outcome over the machine's own confidence,
exactly the antidote CWOPS prescribes. The scarcity and cost of that gold standard is *the* binding
constraint on FD-04, which is why INCONCLUSIVE is a first-class verdict: a portability question the
suite cannot honestly answer because it lacks a reference is not force-answered, it is deferred.

Third, the substrate space is not a single axis and the acceptable-quality threshold is
target-relative. "Portable" against a `deterministic` target means the capability must be reproducible
by a pure algorithm with *zero* quality loss on the dimensions that matter — a deterministic dedup
either produces the correct output set or it does not. "Portable" against a `mid-model` target means
the capability must survive on Sonnet at a quality *close enough* to the frontier gold standard that a
downstream consumer would not notice the downgrade — a graded, not binary, judgment. The same
capability can be PORTABLE to `mid-model` and DEGRADED to `small-model`, and the verdict is meaningless
without naming the target. FD-04 therefore never emits a bare "portable"; it emits "portable *to*
`<target>` at quality `<observed>` against gold `<ref>`", and a DEGRADED verdict always carries the
substrate one rung above where it broke, which is the actionable output FD-05 needs.

The problem is genuinely hard, and FD-04 treats it with the same humility FD-01 treats classification:
the verdict is a *best-effort empirical observation with a confidence and a named gold reference*, not
an oracle. Its two most costly errors — declaring DEGRADED-when-actually-PORTABLE (loses a real
dependence reduction, keeps the stack needlessly on the frontier model) and declaring
PORTABLE-when-actually-DEGRADED (writes a false portability into the stack, and worse, credits CO-12
with a dependence reduction that will silently fail in production) — are the errors the rubric and
gates most aggressively guard against.

### I.3 The verdict taxonomy

FD-04 emits, for every (deposit, claimed-target) pair it tests, exactly one of three verdicts. The
taxonomy is closed — every transfer test resolves to one of these — and the closure is what makes the
detector's contract enforceable: FD-05 and CO-12 always receive a defined signal, never a silence they
must interpret.

- **PORTABLE** — the capability, re-executed on the claimed target substrate, produces output whose
  quality meets or exceeds the acceptance threshold against the frontier-grade gold standard, across all
  *critical* lenses (no critical lens below floor) and with the aggregate quality above the target's
  minimum. The deposit's portability hypothesis is *confirmed*. Downstream: FD-05 promotes the
  capability into CO-03's routing (route this to the cheaper rung) or CO-05's asset registry (if
  `deterministic`); CO-12 credits a *realized* dependence reduction — an Opus-avoided or model-demotion
  count that is now backed by an outcome, not a guess; FD-01's portability-estimate calibration join
  records a confirmed estimate.
- **DEGRADED** — the capability, on the target substrate, drops below the acceptance threshold on at
  least one critical lens, or its aggregate quality falls below the target's minimum. The deposit's
  portability was a *false hypothesis*: the capability is still frontier-dependent (or dependent on a
  substrate higher than claimed). The verdict names the specific lens(es) that failed and the
  observed-versus-floor gap, and it records the highest substrate at which the capability *did* pass (or
  `frontier-only` if none did). Downstream: this is the highest-value signal FD-05 receives — it is the
  worklist of "capabilities we thought we had freed from the frontier but have not", precisely the
  arbitrage targets worth converting; FD-01's estimate calibration records an *overturned* estimate
  (the shape heuristic was over-optimistic for this capability class); CO-12 does *not* credit a
  demotion — a DEGRADED verdict is the detector refusing to let the metric claim a reduction that is not
  real.
- **INCONCLUSIVE** — the gold standard is insufficient to make a defensible verdict: no frontier-grade
  reference exists for this capability, the reference is stale relative to the deposit, or the reference
  covers a case the deposit does not exercise. The portability question is *unanswerable at acceptable
  confidence*, and FD-04 refuses to manufacture an answer. Downstream: the deposit retains FD-01's
  *estimate* (still a hypothesis, now explicitly un-tested), the (deposit, target) pair is queued for
  the Gold-Standard-Factory to produce a reference, and CO-12 is told the demotion is *unproven* — never
  credited, never refuted. INCONCLUSIVE is not a failure of the detector; it is the detector being
  honest about the one input it cannot self-supply.

The taxonomy maps one-to-one to a downstream consequence, exactly as FD-01's four classes do: PORTABLE
→ FD-05 promotes + CO-12 credits; DEGRADED → FD-05 arbitrage-worklist + CO-12 withholds; INCONCLUSIVE →
gold-standard queue + CO-12 unproven. Three members, three routes, no unrouted verdict and no route
without a verdict. A fourth verdict would either duplicate a route or manufacture a state the detector
cannot honestly stand behind — which is why the taxonomy stops at three, and why INCONCLUSIVE exists at
all rather than being folded into DEGRADED (folding "we could not test" into "it failed" would let the
detector report false negatives as if they were measured failures, corrupting exactly the FD-05
worklist that depends on DEGRADED meaning *tested-and-failed*).

### I.4 Difference from existing systems

**Versus CO-12 (Cognitive Readiness Telemetry).** CO-12 is the suite's scorecard: it counts
model-demotions, Opus-avoided invocations, and the cognitive-compression ratio (adopting-cohort WU/MTok
divided by non-adopting). It measures *cost and adoption* — how cheaply the stack ran and how widely a
routing rule was taken up. What CO-12 structurally *cannot* measure is whether a demotion it counted
preserved quality. A demotion from Opus to Sonnet that produces worse output still counts as a demotion
in CO-12's cost ledger; the metric is blind to the quality-regression axis because it never had a
frontier-grade reference to compare against. FD-04 supplies exactly that axis. It does not stand up a
parallel accounting layer (SCS C41: do not build what already exists) — it *reuses* CO-12's data and
*gates* CO-12's credit: a demotion is only credited when FD-04 returns PORTABLE. FD-04 is the quality
conscience of the cost metric; CO-12 is the metric FD-04 protects from crediting hollow reductions.

**Versus CDIO-05 (the six-lens design-review pipeline).** CDIO-05 established a review discipline —
score a visual surface across multiple named lenses, compute the score deterministically in
`modules.cdio.scorer` (the agent supplies verdicts, the code computes the number), and gate DONE on
score ≥ 80 with zero critical issues (PR-CDIO-REVIEW-GATE-001). FD-04 borrows the *pattern* —
multi-lens, criterion-named, observed-value, deterministic aggregation, verdict-gated — and generalizes
its *domain* from design surfaces to any distilled capability. Where CDIO-05 asks "is this UI
frontier-grade?", FD-04 asks "is this capability still frontier-grade one model down?". FD-04 does not
duplicate CDIO's scorer for design; it reuses the review-pipeline architecture and instantiates a
capability-quality lens set beside CDIO's visual lens set. A distilled *design* capability's transfer
test can and should *call* CDIO's own scorer as its lens — FD-04 is the harness, CDIO-05 is a plug-in
lens for the design domain, not a competitor.

**Versus PP functional test suites.** The repo's pytest suites and V-gate harnesses test "does X run
without error / return the expected shape". FD-04 tests "does X still produce *frontier-grade quality*
on a cheaper model". A functional test passes on a Sonnet summary that is fluent and wrong; FD-04 fails
it against the gold standard. The two are complementary and must not be conflated: a capability that
fails its functional test is *broken* and never reaches FD-04; a capability that passes its functional
test but fails FD-04 *runs but degraded* — the exact state the portability proof exists to catch. This
distinction is the crux of the HIGH-RISK constraint (I.6, III.1): FD-04 must never substitute a
functional pass for a quality pass, and it must never grade against auto-generated tests, because an
auto-generated test *is* a functional check dressed as a quality check.

**Versus FD-01 (classification) and FD-06 (writeback).** FD-01 *estimates* portability from capability
shape (a prior); FD-04 *tests* it (the posterior that overwrites the prior). FD-01 hands FD-04 a
`portability_estimate`; FD-04 hands back a verdict that either confirms or refutes it, and the
(estimate, verdict) pairs are the continuous calibration join that keeps FD-01's shape heuristic honest
(III.13). FD-06 *writes* deposits to the stack; FD-04 *reads* the gold standards FD-06's
Gold-Standard-Factory destination produced, and FD-04's verdict is one of the inputs FD-06 uses to
decide whether a deposit is written as `portable` (safe to route cheaper) or `frontier-only` (keep on
the model). FD-04 writes nothing permanent itself — it emits a verdict record that FD-05, FD-06, and
CO-12 consume.

### I.5 What FD-04 does NOT duplicate (explicit)

FD-04 does **not** measure cost or adoption (CO-12 owns the dependence metric; FD-04 *gates* its
credit, never re-computes it). It does **not** classify deltas as NEW/STRONGER/DUP/DISCARD (FD-01). It
does **not** decide a delta's destination or transmuted form (FD-03). It does **not** write anything
permanent to the stack, the graph, CO-03's routing table, or CO-05's registry (FD-06 executes writes;
FD-05 proposes the routing rule; FD-04 only emits the verdict that authorizes them). It does **not**
test "does the capability run" (PP functional suites). It does **not** build a design scorer (CDIO-05
owns visual scoring; FD-04 calls it as a lens for the design domain). And — the load-bearing negative —
it does **not**, under any circumstance, grade a capability against machine-generated assertions or
auto-synthesized tests; its reference is always a human-curated, frontier-grade gold standard sourced
from the Gold-Standard-Factory or an FD-03 benchmark deposit. If an edit to FD-04 begins to synthesize
its own reference answers, count demotions, or write routing rules, it has crossed into a sibling's
territory or violated its core constraint and must be reverted. The detector's value is its narrowness
plus its incorruptible reference: it performs one comparison — target-substrate output versus
human-gold — and emits one typed verdict.

### I.6 Core principles

- **Anti-test-theater is the founding constraint.** FD-04 grades against human-curated gold standards,
  never against auto-generated tests or machine-synthesized assertions. This is not a preference; it is
  the SCS C41 line the repo already drew, elevated here to a founding law and a failure mode (III.1). An
  auto-generated reference is the machine grading itself — the degenerate-feedback trap — and it would
  make every PORTABLE verdict a self-fulfilling one. The gold standard must originate outside the
  substrate under test.
- **The target names the threshold.** There is no absolute "acceptable quality"; there is only
  "acceptable *for* `deterministic` / `small-model` / `mid-model`". Every verdict is target-relative and
  states its target, its observed quality, and its gold reference — the CDIO criterion-and-observed-value
  discipline, applied to portability.
- **Multi-lens, never a single scalar.** Quality regression hides in the non-fungible dimension. FD-04
  reports per-lens, and a critical-lens collapse is DEGRADED even if the aggregate looks fine — the
  CDIO-05 "zero critical issues" gate, generalized.
- **The two costly errors dominate the design.** False-PORTABLE (writes a hollow demotion the stack will
  silently pay for) and false-DEGRADED (abandons a real dependence reduction) are the errors the rubric
  and gates most guard against; INCONCLUSIVE is the release valve that keeps the detector from
  force-answering into either error.
- **Outcome over the machine's confidence.** When the substrate-under-test's own self-report ("this
  looks good") disagrees with the gold-standard comparison, the gold standard wins. This is CWOPS's
  outcome-not-proxy grading made concrete: a capability does not get to certify its own portability.
- **INCONCLUSIVE is honesty, not failure.** A missing or stale gold standard yields INCONCLUSIVE, never
  a manufactured PORTABLE or DEGRADED. The detector's guarantee level is capped by its reference supply,
  and it says so (CO-10 honesty rule, inherited).
- **The verdict is the flywheel's validity check.** FD-04 is the one station where "we distilled this"
  becomes measurable. A distillation suite whose portability claims are never outcome-tested is a loop
  that looks closed but is not *valid* — and CWOPS is explicit that validity, not mere closure, is the
  moat.

### I.7 Why the transfer proof is the collateral that makes the moat bankable

The deepest justification for FD-04 being a *separate, empirical* station — rather than trusting
FD-01's shape estimate, or letting CO-12's cost ledger stand as the scorecard — is the same argument
CWOPS makes for why an *unvalidated* feedback loop is not a moat at all. CWOPS's thesis is that the
durable 2026 advantage is the **valid · closed · <30-day** flywheel, and it puts *valid* first for a
reason: a loop that is closed and fast but feeds on a proxy instead of an outcome compounds error, not
advantage. It cites the degenerate-feedback trap — a recommender trained on the clicks its own ranking
produced learns to reproduce its own predictions, amplifying the proxy (engagement) while the target
(genuine relevance) drifts away unmeasured. The FD suite has an exactly-isomorphic failure available to
it: a distillation loop that *classifies* deltas, *routes* them cheaper, and *credits* the demotion in
CO-12 — all without ever checking that the cheaper substrate preserved quality — would compound a
proxy (apparent dependence reduction) while the target (real, quality-preserving dependence reduction)
silently rots. Every hollow demotion it credited would be a production regression waiting to surface,
and the dependence curve it reported bending would be bending on paper only. FD-04 is the validity
gate that makes this impossible: it is the outcome test standing between "FD-01 estimated this is
portable" and "CO-12 credits a dependence reduction", and nothing crosses that gap without an empirical
PORTABLE verdict against a human gold standard.

Read through the CWOPS lens, the three verdicts are three statements about the *bankability* of a
claimed advantage. PORTABLE is collateral: the dependence reduction is proven, so CO-12 may bank it and
FD-05 may promote the routing rule with confidence that production will not regress. DEGRADED is a
margin call: the advantage the suite *thought* it had booked is not real, the capability is still
frontier-dependent, and — crucially — this is not a loss but the single most valuable signal the
arbitrage engine can receive, because a DEGRADED verdict is a precisely-located, empirically-confirmed
frontier dependency, which is exactly the highest-ROI conversion target FD-05 exists to attack.
INCONCLUSIVE is an un-audited asset: the suite is holding a portability claim it cannot yet value, and
honest accounting refuses to book it either way until the Gold-Standard-Factory produces the reference
that would let FD-04 render a defensible verdict. This framing explains why the anti-test-theater
constraint is not fastidiousness but the core of the whole enterprise: an auto-generated gold standard
is a forged valuation. If FD-04 graded a Sonnet re-execution against an assertion the machine itself
synthesized, every PORTABLE it emitted would be the capability certifying its own portability — the
degenerate loop in its purest form — and the suite would be marking its own advantage to a model it
controls rather than to an outcome it cannot game. The entire value of the portability proof collapses
the instant the reference stops being external, which is why SCS C41's rejection of auto-generated
tests is elevated here from a testing-hygiene rule to the constitutional constraint of the detector.

There is a second, subtler reason the transfer proof must be empirical and separate, and it is the one
that ties FD-04 to the suite's terminal purpose. FD-00's root law is *spend frontier tokens only on the
delta*, and the suite's whole point is to bend the dependence curve downward over time — to *need* the
frontier model less as the floor rises. But the dependence curve can only bend if demotions are real.
A suite that demotes optimistically (trusting FD-01's estimate, never testing it) would report a
steeply-bending curve while accumulating a backlog of hollow demotions that each degrade some
production surface; the reported curve and the lived experience would diverge, and the divergence would
be invisible precisely because nothing measured it. FD-04 is the instrument that keeps the reported
curve and the lived experience the same object. It does this by being the *only* place a portability
claim is converted from FD-01's cheap prior to a tested posterior, and by feeding the (estimate,
verdict) disagreements back to recalibrate FD-01's heuristic so the priors themselves improve over time
(III.13). The result is a suite whose two hardest judgments — is this a genuine delta (FD-01) and does
it survive a downgrade (FD-04) — are both graded against external outcomes the suite cannot game: FD-01
against a hand-labelled classification set, FD-04 against a human gold standard. This is the only
configuration under which a self-improving distillation loop can be trusted to bend the dependence
curve rather than merely to report that it is bending, and it is the reason FD-04 is built as the fifth
dataset, after the extraction spine and before the arbitrage and flywheel that depend on its verdict:
FD-05 cannot prioritize converting frontier-only deltas it cannot distinguish from portable ones, and
FD-07's flywheel cannot claim to be *valid* — in the CWOPS sense that is the whole thesis — until its
portability station empirically proves that what it distilled actually distilled.

---

## Part II — The Transfer-Test Contract and Six-Lens Quality Rubric

### II.1 Operating contract (inputs and outputs)

FD-04's **inputs** are: a distilled deposit (the `capability_summary` plus the operative
recipe/protocol/constraint FD-01 extracted, and — for a re-execution — the input case or cases that
exercise it); the deposit's *claimed portability target* (`deterministic / small-model / mid-model`,
sourced from FD-01's `portability_estimate` or an FD-05 conversion proposal); and the *gold standard* —
one or more frontier-grade reference outputs for the capability, sourced from the Gold-Standard-Factory
destination (FD-06's writeback surface) or an FD-03 benchmark deposit, each carrying its provenance and
freshness. Its **output** is a single typed verdict record: `{verdict ∈ {PORTABLE, DEGRADED,
INCONCLUSIVE}, target_substrate, per_lens_scores, critical_lens_status, aggregate_quality,
acceptance_threshold, gold_ref, gold_freshness, highest_passing_substrate?, failed_lenses?,
confidence ∈ [0,1], inconclusive_reason?}`. The record's hard postcondition: **every (deposit, target)
pair yields exactly one verdict with a non-null gold reference or an explicit `inconclusive_reason`** —
so the suite is never in the state "we demoted a capability but have no verdict on whether it survived".

Three output fields deserve emphasis. `per_lens_scores` is the vector of six lens observations (II.5),
never collapsed into the aggregate before it is recorded — the non-fungible dimension must remain
visible, per the CDIO discipline. `highest_passing_substrate` is the actionable core of a DEGRADED
verdict: if the capability failed at `small-model` but passed at `mid-model`, the deposit's real
portability is `mid-model`, and this field tells FD-05 exactly how far the capability *can* be demoted
even though its claimed target was too aggressive — a DEGRADED verdict that names the highest passing
rung is a partial win, not a total loss. `gold_freshness` gates the whole verdict: a stale gold
standard (the deposit has since been mutated by an FD-06 supersede, or the reference predates a
material capability change) forces INCONCLUSIVE rather than a comparison against an outdated reference,
because a verdict against a stale gold is a false posterior.

### II.2 The transfer-test procedure (six-lens quality comparison)

The transfer test runs in five steps, each with a defined, inspectable output, so the verdict is
traceable rather than a single opaque judgment — the same auditability discipline FD-01's four-step
comparison uses. **Step 1 — reference check.** Confirm a frontier-grade gold standard exists for this
capability and is fresh against the current deposit. If none exists, or it is stale, halt to
INCONCLUSIVE with the reason; no re-execution is attempted, because a re-execution with nothing to
compare against is wasted spend. **Step 2 — re-execute.** Run the capability on the claimed target
substrate over the exercising input case(s): the deterministic rung for a `deterministic` target, a
fixed Haiku/Sonnet/Opus rung for the small/mid model targets. Capture the raw output as the *candidate*.
**Step 3 — six-lens grade.** Grade the candidate against the gold standard across the six lenses (II.5),
producing an observed value per lens with a named criterion — never "worse", always "lens L: candidate
observed V, gold observed W, gap G". **Step 4 — aggregate and gate.** Compute the deterministic
aggregate quality and apply the target's acceptance threshold *and* the critical-lens gate: any critical
lens below its floor forces DEGRADED regardless of aggregate; otherwise, aggregate ≥ threshold →
candidate PORTABLE-at-this-substrate. **Step 5 — verdict.** If the candidate passed at the claimed
target → PORTABLE. If it failed, and the test was run as a substrate ladder, record the
highest_passing_substrate and emit DEGRADED. If Step 1 could not supply a defensible reference →
INCONCLUSIVE (this branch is taken at Step 1, before spend).

The procedure is deliberately explicit because the failure modes cluster at specific steps, exactly as
FD-01's do. A skipped Step 1 (re-executing before confirming a gold exists) burns substrate tokens on a
test that can only end INCONCLUSIVE — the wasteful ordering error. A weak Step 3 (grading on a single
scalar instead of six lenses) produces the hidden-regression failure — the aggregate looks fine while a
critical lens has collapsed. A Step 4 that ignores the critical-lens gate produces false-PORTABLE — the
most costly error, a hollow demotion credited to CO-12. Making each step a named, inspectable output
means an audit can localize a bad verdict to the step that caused it, which is how the detector's
accuracy is improved over time rather than treated as a black box. The deterministic aggregation in
Step 4 is inherited directly from CDIO-05's architecture: the agent (or rung) supplies the per-lens
verdicts, but the *number* and the *gate* are computed by fixed logic, not by the grading model's
opinion — so the verdict cannot be argued up by an eloquent candidate.

### II.3 Interfaces with existing PP systems

- **CO-12** — FD-04's primary metric parent. FD-04 *reads* CO-12's cost/adoption baseline (what a
  demotion would save) and *gates* CO-12's dependence credit: a demotion is credited only on PORTABLE.
  FD-04 never writes CO-12's metric; it authorizes CO-12 to bank a reduction.
- **CDIO-05** — the review-pipeline pattern FD-04 generalizes, and a plug-in lens for the design domain:
  a distilled design capability's transfer test calls `modules.cdio.scorer` as its quality lens rather
  than re-deriving one.
- **FD-01** — supplies the deposit's `capability_summary` and `portability_estimate` (the claimed
  target); receives the verdict as the posterior that overwrites the estimate, and the (estimate,
  verdict) join that recalibrates its shape heuristic.
- **FD-03 / Gold-Standard-Factory (FD-06 surface)** — the *only* sources of gold standards. FD-04 reads
  benchmark deposits (FD-03) and curated frontier references (the Factory); it never synthesizes them.
- **FD-05** — the primary verdict consumer: PORTABLE authorizes an arbitrage promotion (new CO-03
  routing rule or CO-05 asset candidate); DEGRADED populates the conversion worklist (frontier
  dependencies worth attacking); INCONCLUSIVE holds the estimate un-tested.
- **FD-06** — reads the verdict to write the deposit as `portable`-tagged (route cheaper) or
  `frontier-only`-tagged (keep on model); FD-04 authorizes, FD-06 executes the write.
- **FD-07 / PM-03** — the verdict is published to the PM-03 bus so concurrent panes see a settled
  portability result rather than re-running the transfer test, and FD-07's flywheel consumes the verdict
  as its validity signal.
- **CO-03 / CO-05** — the *target substrates* and the deterministic/asset destinations a PORTABLE
  verdict unlocks (via FD-05); FD-04 re-executes *on* CO-03's rungs but proposes no routing itself.

### II.4 Decision rights and non-decision rights

FD-04 **may decide**: whether a defensible gold standard exists (Step 1); the candidate re-execution's
raw output (Step 2); each per-lens observed value and criterion (Step 3); the deterministic aggregate
and the critical-lens gate result (Step 4); the final verdict, its confidence, and the
highest_passing_substrate (Step 5). FD-04 **may not decide**: the delta's class (FD-01); the deposit's
destination or form (FD-03); whether to *promote* a PORTABLE capability into CO-03/CO-05 (FD-05
proposes, FD-06 writes); whether to *credit* the demotion (CO-12 does, gated by FD-04's PORTABLE); or
what the gold standard *should* be (the Gold-Standard-Factory curates it; FD-04 consumes it). The
boundary with FD-05 is the important one: FD-04 says "this capability *is* portable to `mid-model` at
quality X" (an empirical fact); FD-05 says "therefore route it to Sonnet and retire the Opus call" (a
policy decision). FD-04 produces the evidence; FD-05 acts on it. The boundary with FD-01 mirrors that:
FD-01's estimate is the prior FD-04 tests; FD-04's verdict is the posterior FD-01's calibration join
consumes; neither overwrites the other's field silently — the estimate is retained alongside the
verdict so the disagreement remains visible for recalibration.

### II.5 The six-lens quality rubric (with criteria)

FD-04 grades a candidate against the gold standard across six lenses, generalized from CDIO-05's
design-review lens set to the capability-quality domain. Each lens has a named criterion and a
floor; lenses marked *critical* trigger DEGRADED on a below-floor observation regardless of aggregate.

| Lens | Criterion (candidate vs gold) | Critical? | Below-floor meaning |
|---|---|---|---|
| **Correctness** | Does the candidate produce the same *operative result* as the gold on the exercising cases — right answer, right transformation, right constraint satisfied? | **Yes** | The capability produces wrong output on a cheaper model — a hollow demotion; DEGRADED. |
| **Robustness** | Does the candidate handle the edge/adversarial cases the gold handles, or does it collapse on the cases the frontier output covered? | **Yes** | The capability works on the happy path but loses the frontier's edge coverage — DEGRADED. |
| **Completeness** | Does the candidate cover the full scope the gold covers, or does it drop parts of the capability the frontier delivered? | No | Partial coverage — degrades aggregate, DEGRADED only if it pushes below threshold. |
| **Fidelity/voice** | For capabilities where *form* is the value (summaries, copy, design), does the candidate preserve the frontier's crispness, non-hedging voice, or aesthetic (CDIO scorer for design)? | Domain-dependent | The output is factually fine but loses the quality that made it valuable — critical for form-bearing capabilities, else advisory. |
| **Efficiency** | Does the candidate reach the result without pathological cost (excess tokens, retries, or — for `deterministic` — correct algorithmic complexity)? | No | Works but expensive — informs FD-05's ROI, rarely alone a DEGRADED. |
| **Determinism/stability** | Re-run on the substrate, does the candidate produce a stable result, or does quality swing run-to-run (a hallmark of a capability living at the substrate's competence edge)? | **Yes** for `deterministic`/`small-model` targets | Unstable output one rung down means the demotion is unreliable in production — DEGRADED for lower targets. |

The critical-lens set (Correctness, Robustness, and Determinism-for-lower-targets, plus Fidelity for
form-bearing capabilities) is where the false-PORTABLE error is stopped: an aggregate-only verdict would
pass a candidate that is correct-and-complete-but-unstable, or fluent-but-wrong, and that candidate is
exactly the hollow demotion the detector exists to catch. The asymmetry is deliberate and mirrors
FD-01's evidentiary asymmetry: PORTABLE (the class that lets CO-12 bank a reduction and FD-05 change
routing) must clear *every* critical lens *and* the aggregate; DEGRADED needs only one critical-lens
collapse *or* a sub-threshold aggregate. The burden is heaviest on the verdict that changes production
behavior, lightest on the verdict that keeps the status quo (still-frontier-dependent).

### II.6 Token-ROI rules

FD-04 is itself a cost — it re-executes capabilities on substrates and grades against gold standards —
and the doctrine forbids a detector that costs more than the dependence reduction it validates. Three
ROI rules bound it. First, *Step 1 before spend*: the gold-standard check runs before any re-execution,
so a capability with no reference costs one cheap lookup (INCONCLUSIVE) rather than a full re-execution
that could only end INCONCLUSIVE anyway. Second, *test where the estimate is uncertain, trust where it
is clean*: a `deterministic` estimate on a pure transform (format, dedup, parse) is cheap and near-
certain to be PORTABLE, so it is verified by a single deterministic re-execution, not a six-lens
frontier grade; the expensive multi-lens test is reserved for the graded `mid-model`/`small-model`
boundary where the verdict is genuinely uncertain and a wrong answer is expensive. Third, *grade on the
cheapest sufficient grader*: the six-lens comparison for most capabilities is a bounded reasoning task a
Sonnet rung handles against the gold; only a genuinely ambiguous Fidelity/voice judgment on a
high-frequency capability warrants a frontier-grade grader — and even then, the deterministic aggregate
and gate are code, not model opinion, so the grader's cost is bounded to producing per-lens
observations, not to computing the verdict. These rules keep FD-04 from becoming the CWOPS anti-pattern
of a guardrail whose cost exceeds the loss it prevents: the transfer test must cost far less than the
frontier-call it would retire, or the demotion it validates has negative net ROI.

### II.7 Gold-standard sourcing rules (the anti-test-theater discipline, operationalized)

The gold standard is the one input FD-04 cannot self-supply, and the rules governing it are the
detector's constitution. **Rule G1 — external origin only.** A gold standard is a frontier-grade
reference output curated by a human or produced by an instrumented outcome process (the
Gold-Standard-Factory, FD-03 benchmark deposits); it is *never* a machine-synthesized assertion, an
auto-generated test, or the substrate-under-test's own output. This is SCS C41 elevated to law: an
auto-generated reference is the machine grading itself. **Rule G2 — provenance and freshness carried.**
Every gold standard travels with its provenance (which frontier model, which session, curated by whom)
and a freshness stamp against the current deposit; a gold whose deposit was later superseded by an FD-06
mutation is stale and forces INCONCLUSIVE (Step 1). **Rule G3 — coverage match.** The gold must exercise
the same case(s) the candidate is tested on; a gold that covers a different input than the deposit
exercises cannot ground a verdict, and the mismatch is an INCONCLUSIVE reason, not a silent
comparison-across-cases. **Rule G4 — outcome weighting.** Where the substrate-under-test's self-report
disagrees with the gold comparison, the gold wins; a capability never certifies its own portability.
**Rule G5 — INCONCLUSIVE is the honest default under scarcity.** When G1–G4 cannot be satisfied, the
verdict is INCONCLUSIVE and the (deposit, target) pair is queued for the Gold-Standard-Factory —
FD-04 never manufactures a reference to avoid an INCONCLUSIVE, because a manufactured reference is a
forged valuation (I.7). These five rules are the operational form of the anti-test-theater constraint,
and together they guarantee that every PORTABLE and DEGRADED verdict rests on an external outcome the
detector cannot game.

### II.8 No-bloat and compression rules

FD-04 enforces no-bloat structurally. It does not store re-execution transcripts beyond the per-lens
observed values and the verdict record — the raw candidate output is discarded once graded (it is
reproducible by re-running the substrate). It does not deposit anything to the vault (FD-06 does); it
emits a compact verdict record. It does not re-test a settled (deposit, target) pair whose verdict is
fresh — the PM-03 bus carries the verdict so concurrent panes and future sessions read it rather than
re-run the expensive transfer test. And it never widens its own contract: a verdict is one of three
values with a bounded field set, so a downstream consumer (FD-05, FD-06, CO-12) binds to a stable
interface. The detector's contribution to suite-wide compression is that it *retires* re-testing: once
a capability is proven PORTABLE-to-`mid-model`, that fact is a permanent deposit and the transfer test
never runs again for that (deposit, target) unless the deposit is mutated — the same "navigate, don't
re-derive" discipline GK gives knowledge, applied to portability verdicts.

### II.9 A fully worked transfer test: one capability against two substrates

The clearest specification of the contract is to run one distilled capability through the five steps
against two different target substrates and show that the *same capability* yields two *different*
verdicts — the property that makes the target-relative discipline load-bearing. Consider a deposit FD-01
classified NEW and estimated `mid-model`: a capability that "given a raw customer-support transcript,
produces a three-line resolution summary that (a) states the root cause, (b) states the action taken,
and (c) flags any unresolved risk, in a terse non-hedging voice." The gold standard is a
Gold-Standard-Factory reference: five frontier-produced summaries over five held-out transcripts,
human-curated as frontier-grade, carrying provenance and a fresh stamp.

**Against the `mid-model` (Sonnet) target.** Step 1: a fresh gold exists covering the five exercising
transcripts — proceed. Step 2: re-execute the capability's recipe on Sonnet over the five transcripts,
capturing five candidate summaries. Step 3 — six-lens grade against the gold: Correctness — all five
root causes correct, matches gold (observed: 5/5, floor 5/5) ✓ critical; Robustness — on the one
transcript with an ambiguous root cause, Sonnet correctly flags the ambiguity as the gold does (observed:
handles the edge, floor: handles) ✓ critical; Completeness — all three required lines present in all
five (observed: 15/15) ✓; Fidelity/voice — Sonnet's summaries are terse and non-hedging, near-identical
register to the gold (observed: high, this is a form-bearing capability so Fidelity is critical here) ✓
critical; Efficiency — within token budget, no retries ✓; Determinism — three re-runs produce stable
summaries, no quality swing (observed: stable) ✓ critical-for-lower-target. Step 4: no critical lens
below floor, aggregate above the `mid-model` threshold. Step 5: **PORTABLE to `mid-model`**, confidence
0.85, gold_ref cited. FD-05 will propose retiring the Opus call for this capability and routing it to
Sonnet; CO-12 credits a *realized* model-demotion; FD-01's calibration join records a confirmed
`mid-model` estimate.

**Against the `small-model` (Haiku) target.** The identical capability, identical gold. Step 1: same
fresh gold — proceed. Step 2: re-execute on Haiku over the five transcripts. Step 3: Correctness — four
of five root causes correct, but on the transcript with two intertwined issues Haiku collapses them into
one and states the wrong primary cause (observed: 4/5, floor 5/5) ✗ **critical lens below floor**;
Robustness — on the ambiguous-cause transcript Haiku does not flag the ambiguity, it commits to a guess
(observed: misses the edge) ✗ critical; Fidelity — voice is fine; Determinism — worse, two re-runs
disagree on the intertwined-issue transcript (observed: unstable) ✗ critical-for-lower-target. Step 4:
three critical lenses below floor — DEGRADED regardless of aggregate. Step 5: **DEGRADED at
`small-model`**, highest_passing_substrate = `mid-model` (it passed there), failed_lenses =
[Correctness, Robustness, Determinism], confidence 0.9. FD-05 learns this capability's real floor is
`mid-model`, not `small-model` — it can retire the Opus call but must *not* push to Haiku; CO-12 credits
only the Opus→Sonnet demotion, not an Opus→Haiku one; FD-01's calibration join records that the
`mid-model` estimate was *correct* (the capability was portable to mid, and the more-aggressive
small-model push was never FD-01's estimate — this run confirms the estimate and bounds it).

The two runs are the entire argument for target-relative verdicts. The capability is identical; the
gold is identical; the only variable is the substrate, and the verdict flips from PORTABLE to DEGRADED
across one rung. A detector that emitted a bare "portable/not-portable" without naming the target would
be meaningless here — the capability is *both*, depending on the rung. The worked example also
demonstrates why the critical-lens gate is load-bearing: on the Haiku run, if FD-04 had graded on
aggregate alone, four-of-five correctness plus perfect fidelity and completeness might have averaged
above threshold, and the detector would have emitted false-PORTABLE — crediting CO-12 with a demotion to
Haiku that produces a wrong root cause on any transcript with intertwined issues, a hollow demotion the
support team would silently pay for in production. The critical-lens gate stops exactly that: a
below-floor Correctness observation is DEGRADED no matter how good the average looks. And it
demonstrates the value of highest_passing_substrate: the DEGRADED verdict is not a dead end, it is the
precise instruction "portable to mid, not to small" — a partial, bankable win plus a bounded
frontier-dependency for FD-05 to note.

### II.10 How the acceptance threshold is computed, and what an INCONCLUSIVE actually gates

The acceptance threshold is not a global constant; it is a function of the target substrate and the
capability's consequence class, and its computation must be principled rather than a magic number, for
the same reason FD-01's confidence must be principled: it is the field that decides whether a demotion
is banked. FD-04 derives the threshold from two inputs. The first is the *target's expected competence
gap*: a `deterministic` target admits **zero** quality loss on critical lenses (a deterministic rung
either reproduces the operative result exactly or it is DEGRADED — there is no "close enough" for an
algorithm), while a `mid-model` target admits a small, bounded gap against the frontier gold (the
capability may be marginally less polished so long as every critical lens holds and the aggregate stays
above the mid floor). The threshold is therefore *strictest at the deterministic end and graded toward
the model end* — the inverse of intuition, because the deterministic target is the one whose promise
(zero-token, perfectly stable) is falsified by *any* quality loss, whereas a model target's promise was
always "close to frontier, much cheaper" and tolerates a defined margin. The second input is the
*capability's consequence class*: a capability whose output feeds a production surface (a routing
decision, a customer-facing summary) carries a higher threshold than one feeding an internal advisory,
because a hollow demotion on the former is a production regression and on the latter a tolerable
degradation — the consequence weighting FD-05 and CO-12 both respect.

The two inputs combine into a per-verdict threshold, and the important design commitment is what happens
when the detector *cannot* apply it — the INCONCLUSIVE branch. INCONCLUSIVE does not mean "the
capability failed"; it means "FD-04 cannot render a defensible verdict because the reference is missing,
stale, or coverage-mismatched" (G2/G3). What INCONCLUSIVE *gates* is precisely the CO-12 credit and the
FD-05 promotion: an INCONCLUSIVE (deposit, target) pair keeps FD-01's estimate as an explicit,
un-tested hypothesis; it is *never* credited as a demotion and *never* promoted into CO-03/CO-05
routing, because promoting on an untested estimate is exactly the optimistic-demotion failure I.7
warns against. The pair is queued for the Gold-Standard-Factory, and when a reference is produced, the
transfer test re-runs and resolves to PORTABLE or DEGRADED. This is the concrete mechanism by which
FD-04 refuses the oracle pose: it does not manufacture a portability verdict on the capabilities it
cannot reference; it defers them, visibly, to the one instrument (a human-curated gold) decisive enough
to ground the verdict. The consequence for the suite is that the INCONCLUSIVE rate is a live health
signal in its own right: a healthy detector on a mature suite shows a *falling* INCONCLUSIVE rate as the
Gold-Standard-Factory backfills references, whereas a persistently high INCONCLUSIVE rate is the signal
that the suite is distilling faster than it is producing gold standards — a real bottleneck the Owner
must resource, and one the detector surfaces honestly rather than papering over with manufactured
verdicts. A detector that force-answered its INCONCLUSIVE cases into PORTABLE to keep its "proven
portable" count up would be the confidence-theater failure FD-01 names, transposed to portability: an
engine optimizing the appearance of validation rather than real validation, and precisely the behavior
the INCONCLUSIVE verdict exists to make unnecessary.

---

## Part III — Failure Modes, Gates, Benchmarks, and Evolution

### III.1 Failure modes with diagnosis protocol

| Failure mode | Symptom | Diagnosis | Root cause |
|---|---|---|---|
| **Test theater (auto-generated gold)** | high PORTABLE rate, but production regressions surface on demoted capabilities | audit the gold provenance field; check whether any gold's origin is machine-synthesized rather than human/outcome-curated | G1 violated — the machine graded itself; every such PORTABLE is a self-fulfilling verdict |
| **False-PORTABLE (hollow demotion)** | CO-12 shows a credited demotion; the demoted surface later degrades in production | re-run the transfer test with the critical-lens gate enforced; inspect whether the verdict was aggregate-only | Step 4 critical-lens gate skipped, or a critical lens mis-marked non-critical (fluent-but-wrong passed) |
| **False-DEGRADED (abandoned reduction)** | dependence curve flatter than it should be; capabilities kept on frontier that a cheaper rung actually handles | sample DEGRADED verdicts, re-grade against a *fresh* gold with the correct target threshold | over-strict threshold for the target, or graded against a stale/harder-than-fair gold |
| **Stale-gold verdict** | verdict flips on re-test with no capability change | check gold_freshness against the deposit's mutation history | G2 violated — graded against a reference the deposit had superseded |
| **Coverage mismatch** | verdict looks confident but does not predict production behavior | compare the gold's exercised cases to the candidate's input cases | G3 violated — gold covered a different case than the deposit exercises |
| **Single-scalar collapse** | aggregate passes, a critical dimension silently failed | inspect per_lens_scores; look for a below-floor critical lens masked by a high average | Step 3 collapsed six lenses to one number before the gate |
| **Substrate-edge instability** | verdict swings run-to-run for the same (deposit, target) | run the Determinism lens explicitly across ≥3 re-runs | capability living at the substrate's competence edge; correct verdict is DEGRADED for that target |

The detector's characteristic failure is **test theater**, because it is the failure that *feels* like
rigor — an auto-generated gold gives a clean, fast, high PORTABLE rate that looks like a well-validated
suite, and only the join to production regressions (or an audit of gold provenance) reveals that the
machine was grading itself. This is the FD-04 analogue of CWOPS §4.6's degenerate-feedback trap, and it
is the exact failure SCS C41 already named for the repo; FD-04's founding constraint (I.6, G1) exists
precisely to make it structurally impossible, and III.12 details why the gold cannot be self-generated.
The second-most-costly failure is false-PORTABLE via a skipped critical-lens gate, because it is the one
that writes a hollow demotion into CO-12's ledger and FD-05's routing — a self-inflicted production
regression credited as an advantage.

### III.2 Anti-patterns with evidence

- **The self-certifying capability.** Grading a Sonnet re-execution against a reference the same model
  (or the machine's own expectation) produced. Evidence: CWOPS §4.6 degenerate-feedback — training on
  your own algorithm's top-ranked outputs amplifies the proxy, not the target. Forbidden by G1
  (external-origin gold only) and the whole anti-test-theater constraint.
- **The functional pass masquerading as a quality pass.** Concluding PORTABLE because the capability
  *ran* on the cheaper model without erroring. Evidence: PP functional suites already answer "does it
  run"; FD-04 exists to answer "does it run *at frontier quality*", and conflating them is the exact gap
  I.4 draws. Forbidden by the six-lens rubric and the critical-lens gate.
- **The single number.** Collapsing six lenses to one score and gating on the aggregate. Evidence:
  CDIO-05's discipline — name a criterion and an observed value, never "looks better"
  (T-DESIGN-OPINION-VS-CRITERIA-001) — plus the "zero critical issues" gate FD-04 generalizes.
  Forbidden by per_lens_scores + the critical-lens gate.
- **The optimistic demotion.** Crediting CO-12 or changing CO-03 routing on FD-01's *estimate* without
  FD-04's *test*. Evidence: FD-01 II.7 declares the estimate "a prior, never a claim"; I.7's bankability
  argument — an untested demotion is an un-audited asset. Forbidden by CO-12 crediting only on PORTABLE
  and FD-05 promoting only on PORTABLE.
- **The manufactured verdict.** Force-answering an un-referenceable capability into PORTABLE/DEGRADED to
  avoid an INCONCLUSIVE. Evidence: CO-12's honesty rule — unmeasured is surfaced, never faked; I.7's
  forged-valuation framing. Forbidden by INCONCLUSIVE being a first-class verdict and G5.
- **The stale-gold comparison.** Grading against a reference the deposit has since superseded. Evidence:
  FD-01 III.7's stale-baseline discipline, transposed — a delta over a stale floor is suspect; a verdict
  against a stale gold is a false posterior. Forbidden by G2 + Step 1 freshness.

### III.3 Quality gates (binary)

- **G1 — Gold is external.** Does every verdict cite a gold standard whose provenance is human-curated
  or outcome-instrumented, never machine-synthesized? Binary. (The anti-test-theater gate.)
- **G2 — Gold is fresh.** Was the gold's freshness green against the current deposit at test time, or
  the verdict forced INCONCLUSIVE? Binary.
- **G3 — Coverage matched.** Did the gold exercise the same case(s) the candidate was tested on? Binary.
- **G4 — Six lenses recorded.** Does every non-INCONCLUSIVE verdict carry all six per-lens observed
  values, un-collapsed? Binary.
- **G5 — Critical-lens gate applied.** Does every PORTABLE verdict show every critical lens at or above
  floor? Binary. (The false-PORTABLE gate.)
- **G6 — Target named.** Does every verdict state its target substrate and the acceptance threshold used?
  Binary. (No bare "portable".)
- **G7 — Verdict assigned.** Does every (deposit, target) pair carry exactly one verdict with a gold_ref
  or an inconclusive_reason? Binary. (The closed-taxonomy postcondition.)

### III.4 Evaluation rubric (measurable)

| Dimension | Metric | Source | Target |
|---|---|---|---|
| Verdict accuracy | agreement with a held-out hand-labelled (deposit, target, correct-verdict) set | eval set | ≥ 0.85 |
| PORTABLE precision | fraction of PORTABLE verdicts that do *not* later produce a production regression on the demoted surface | production-regression audit | ≥ 0.9 |
| DEGRADED recall | fraction of genuinely-still-frontier-dependent capabilities correctly caught as DEGRADED | sampled re-grade audit | ≥ 0.9 |
| Estimate-verdict calibration | fraction of FD-01 portability estimates FD-04 confirms (the join) | estimate↔verdict join | rising / trackable |
| INCONCLUSIVE honesty | fraction of INCONCLUSIVE verdicts that genuinely lacked a defensible gold (not force-deferred to dodge a hard grade) | audit sample | ≥ 0.95 |
| Gold externality | fraction of golds with human/outcome provenance (never machine-synthesized) | provenance audit | 1.0 (hard) |

### III.5 Benchmarks with reference values

The detector's benchmarks anchor to the suite's economics and its honesty chain. **PORTABLE precision
floor: ≥ 0.9** — below this, CO-12's credited demotions are more than 10% hollow, and the dependence
metric is reporting a curve that diverges from lived production; this is the single most important
benchmark because a false-PORTABLE is a credited-but-regressing demotion. **Gold externality: exactly
1.0** — this is not a floor but an invariant; a single machine-synthesized gold is a G1 violation and
corrupts every verdict grounded on it, so the benchmark is binary-hard, not graded. **Verdict accuracy:
≥ 0.85** agreement with the hand-labelled set — the threshold below which the detector is not
trustworthy enough to gate CO-12's credit; identical in spirit to FD-01's ≥ 0.85 classification-accuracy
floor, and measured the same way (against an external hand-labelled set, never self-graded). **Cost
ceiling:** FD-04's per-verdict cost (re-execution + six-lens grade) must be a small fraction of the
frontier-call the validated demotion would retire — the CWOPS guardrail-economics principle: the
transfer test that validates a demotion must cost far less than the demotion saves, or the demotion has
negative net ROI and should not be pursued. **DEGRADED actionability: 100%** of DEGRADED verdicts must
carry a highest_passing_substrate (or `frontier-only`) — a DEGRADED verdict that does not tell FD-05 how
far the capability *can* be demoted is an incomplete signal.

### III.6 Example operational traces

**Trace A — PORTABLE.** Deposit: a deterministic dedup capability (FD-01 NEW, estimate `deterministic`).
Step 1: gold is an FD-03 benchmark deposit with the expected output set for five inputs, fresh. Step 2:
re-execute the deterministic rung. Step 3: Correctness 5/5 (exact set match, critical) ✓; Determinism
stable across runs (critical-for-deterministic) ✓; other lenses trivially met. Step 4: zero quality loss
admitted for `deterministic`, met. Step 5: **PORTABLE to `deterministic`**, confidence 0.98. FD-05
promotes it into CO-05's asset registry; CO-12 credits a Zero-Token replacement.

**Trace B — DEGRADED.** Deposit: an adversarial-reasoning capability (FD-01 NEW, estimate `mid-model`).
Step 2: re-execute on Sonnet. Step 3: Correctness holds, but Robustness collapses — on the two
adversarial inputs the gold handles, Sonnet misses the attack the frontier caught (observed: misses
2/2, critical) ✗. Step 4: critical lens below floor → DEGRADED. Step 5: **DEGRADED at `mid-model`**,
highest_passing_substrate = `frontier-only` (it passed nowhere below frontier), failed_lens =
[Robustness], confidence 0.88. FD-05 logs it as a high-value frontier dependency; CO-12 credits nothing;
FD-01's join records an *overturned* `mid-model` estimate — the shape heuristic was over-optimistic for
adversarial reasoning, a recalibration signal.

**Trace C — INCONCLUSIVE (no gold).** Deposit: a niche cross-domain synthesis capability, no prior
frontier reference exists. Step 1: no gold — halt. Step 5: **INCONCLUSIVE (no-gold)**, the (deposit,
`mid-model`) pair queued for the Gold-Standard-Factory. FD-01's estimate retained as explicit
un-tested; CO-12 told the demotion is unproven.

**Trace D — INCONCLUSIVE (stale gold).** Deposit was mutated by an FD-06 supersede after its gold was
curated. Step 1: gold_freshness amber — the reference predates the mutation. Halt to **INCONCLUSIVE
(stale-gold)**, re-curation queued. Prevents a false posterior against an outdated reference.

**Trace E — PORTABLE-with-caveat (design capability).** Deposit: a distilled landing-hero design
capability, estimate `mid-model`. Step 3's Fidelity lens *is* CDIO-05's scorer, invoked as a plug-in;
CDIO returns Design Quality Score 82, zero critical issues → Fidelity ✓ critical (form-bearing). Other
lenses met. Step 5: **PORTABLE to `mid-model`**, confidence 0.8, with the CDIO score cited as the
Fidelity observed value — the six-lens harness delegating the design lens to the domain owner rather
than re-deriving it.

### III.7 Edge cases

- **No gold exists for a genuinely-novel capability.** The common case for a fresh NEW delta —
  INCONCLUSIVE (no-gold), queued for curation. Never force-verdicted; a novel capability with no
  reference cannot be portability-proven, only estimated.
- **Capability whose value *is* the frontier model.** A capability that FD-01 estimated `frontier-only`
  is tested only to confirm it degrades everywhere below frontier — a DEGRADED-everywhere verdict is the
  *expected, correct* outcome and the honest record that this is a genuine irreducible frontier
  dependency (the deposit FD-05 will most want to attack but may not be able to convert).
- **Partial portability.** A capability portable on some exercising cases but not others — graded per
  case; if the failing cases are the ones that matter (a critical lens on a production case), DEGRADED;
  the per-case breakdown is carried so FD-05 knows *which* cases force the frontier.
- **Gold covers a superset of the deposit.** The gold exercises cases the deposit does not — grade only
  the overlapping cases (G3), flag the uncovered gold cases as a coverage note, not a failure.
- **Deterministic target with any quality loss.** A `deterministic` verdict admits zero critical-lens
  loss; a single wrong output → DEGRADED, because a deterministic promise is falsified by any deviation
  (II.10).
- **Grader disagrees with itself run-to-run.** If the six-lens grade is itself unstable (the *grader*,
  not the candidate), the verdict confidence drops and the case is re-graded on a firmer rung — the
  detector must not inherit its grader's noise as a candidate's instability.

### III.8 Writeback rules

FD-04 does not write anything permanent — it emits the typed verdict record and publishes it to PM-03.
The record's mandatory fields (verdict, target_substrate, gold_ref-or-inconclusive_reason,
per_lens_scores-for-non-INCONCLUSIVE, critical_lens_status, confidence) must all be present before FD-05
or FD-06 accepts it — a verdict missing its gold_ref or per-lens vector is malformed and rejected, which
prevents an ungrounded portability claim from reaching CO-03 routing or CO-12's ledger. The verdict
authorizes downstream writes it does not perform: PORTABLE authorizes FD-05 to propose a CO-03 routing
rule or CO-05 asset and FD-06 to tag the deposit `portable`; DEGRADED authorizes FD-06 to tag the
deposit `frontier-only` (or `portable-to-<highest_passing>`) and populates FD-05's conversion worklist;
INCONCLUSIVE authorizes nothing but a Gold-Standard-Factory queue entry. CO-12's dependence credit is
gated on PORTABLE and executed by CO-12, never by FD-04. The verdict is published to PM-03 with its
provisional/settled status so concurrent panes read a settled portability result rather than re-run the
transfer test — the concurrency discipline FD-01 III.13 established, applied to verdicts.

### III.9 Conceptual regression tests

- **R1 — External gold enforced.** Feed a verdict request whose only available gold is machine-
  synthesized; assert INCONCLUSIVE (or rejection), never a PORTABLE grounded on it (G1).
- **R2 — Critical-lens gate.** Feed a candidate that is fluent-but-wrong (Correctness below floor, high
  aggregate); assert DEGRADED, not PORTABLE (G5).
- **R3 — Target-relative flip.** Feed one capability against `mid-model` and `small-model`; assert it can
  return PORTABLE for one and DEGRADED for the other with the correct highest_passing_substrate.
- **R4 — Stale gold forces INCONCLUSIVE.** Feed a deposit mutated after its gold was curated; assert
  INCONCLUSIVE (stale-gold), not a comparison against the old reference (G2).
- **R5 — Deterministic zero-loss.** Feed a deterministic capability with a single wrong output; assert
  DEGRADED (II.10).
- **R6 — DEGRADED names the floor.** Feed a capability portable to mid but not small; assert DEGRADED
  carries highest_passing_substrate = `mid-model`.
- **R7 — INCONCLUSIVE not force-answered.** Feed an un-referenceable capability; assert INCONCLUSIVE +
  gold queue, never a manufactured verdict.

Per SCS C41, these are gate assertions for the EXECUTION-mode harness, **not** auto-generated unit tests
— which would be the exact test-theater the detector forbids. The accuracy and PORTABLE-precision
metrics are measured against a hand-labelled eval set and a production-regression audit, the honest
observations the anti-test-theater rule requires. FD-04 grading itself with tests it generated would be
the detector committing its own founding sin.

### III.10 Done criteria (verifiable)

FD-04 is done when: the dataset exists on disk, un-truncated, >2500 real words/Part; the three-verdict
taxonomy is closed and each verdict maps to exactly one downstream consequence (PORTABLE → FD-05
promote + CO-12 credit; DEGRADED → FD-05 worklist + CO-12 withhold; INCONCLUSIVE → gold queue); the
transfer-test procedure is specified as five inspectable steps with Step-1-before-spend ordering; the
six-lens rubric names each lens's criterion, floor, and critical status, with the critical-lens gate
enforcing the PORTABLE burden; the gold-standard sourcing rules G1–G5 are stated with G1 (external
origin only) as the founding constraint; G1–G7 quality gates are binary; the detector declares CO-12 as
its metric parent (gates credit, never re-computes), CDIO-05 as its review-pipeline pattern and design
lens, and the Gold-Standard-Factory/FD-03 as its only gold sources (no self-synthesis); and
V-FD-NO-CODE finds zero code fences. The V-FD-DECAY-DETECTABLE gate (FD_INDEX) is satisfied by the
six-lens rubric graded against gold standards with no auto-generated tests.

### III.11 Upgrade path

- **v1 (this dataset):** the transfer-test detector as a rung-2 empirical measurement, HIGH-RISK-gated,
  graded per (deposit, target) against curated gold standards.
- **v2 (EXECUTION-mode):** the eval set is materialized (hand-labelled deposit/target/verdict triples)
  and verdict accuracy + PORTABLE precision are computed on each material PP change, so detector drift is
  caught; the estimate↔verdict join (III.13) accumulates and begins recalibrating FD-01's shape
  heuristic from real data.
- **v3:** the substrate re-execution is run as a *ladder* by default (test the claimed target, then one
  rung down and one rung up) so every DEGRADED verdict comes with a fully-characterized
  highest_passing_substrate for free, and every PORTABLE verdict is stress-tested one rung further to
  find the true floor rather than stopping at the first pass — turning FD-04 from a pass/fail on the
  claimed target into a floor-finder that maximizes the demotion FD-05 can safely take.
- **v4:** the Gold-Standard-Factory is driven by FD-04's own INCONCLUSIVE queue — the detector's
  un-referenceable cases become the Factory's prioritized curation worklist, closing a loop where the
  detector tells the reference supply exactly what gold it most needs, so the INCONCLUSIVE rate falls
  fastest where portability verdicts are most valuable.
- **Deprecation trigger:** if a capability class's PORTABLE-to-`deterministic` rate reaches a durable
  near-100% (the class is reliably reducible to algorithms), FD-04 stops deep-testing new deposits in
  that class and fast-paths them to a single deterministic-reproduction check — the detector's own
  success narrows its work, mirroring FD-01's deprecation trigger and FD-00's terminal state: a suite
  that needs to *prove* portability less over time because portability has become the default for that
  class.

### III.12 The gold-standard ground-truth and why it cannot be auto-generated

FD-04 is, alongside FD-01, one of only two FD datasets whose correctness is a *measurable* quantity
rather than a design property, and — like FD-01 — that raises a specific integrity risk it must
engineer against: the temptation to manufacture its own reference. A detector that graded against a
gold standard it (or the substrate under test) generated would drift toward whatever maximizes its
self-score, which for a portability detector is almost always over-reporting PORTABLE — the verdict
that makes the suite look most successful at reducing dependence. This is the exact degenerate-feedback
trap CWOPS §4.6 names: an algorithm trained on the outputs it itself ranked first learns to reproduce
its own predictions, amplifying a proxy (apparent portability) instead of the target (real,
quality-preserving portability). The antidote CWOPS prescribes — *outcome data, not usage logs, from an
instrumented process, weighted toward outcome over the model's own confidence* — maps directly onto
FD-04's constitution: the gold standard is an external, human-curated or outcome-instrumented reference
(G1), never the substrate's own output or a machine-synthesized assertion, and the decisive downstream
outcome (does the demoted capability later regress in production?) is the audit that grades FD-04's
PORTABLE precision, weighted above the detector's own verdict confidence when the two disagree.

The reason auto-generated gold is not merely lower-quality but *categorically invalid* deserves to be
stated precisely, because it is the line SCS C41 drew and this dataset elevates to a founding law. A
gold standard is supposed to answer the question "what does frontier-grade quality *look like* for this
capability?" — and that answer must originate from an intelligence at least as capable as the frontier
model whose output is being replaced, or from a human who can recognize frontier quality. An
auto-generated assertion, by construction, encodes only what the *generating* machine believed the
answer should be. If that generator is the substrate under test, the capability certifies its own
portability — a tautology (the Haiku output matches the Haiku-generated expectation, therefore Haiku is
"portable"). If the generator is the frontier model itself producing an assertion rather than a
reference output, the "gold" is a self-report, and CWOPS is explicit that a system grading itself on its
own confidence rather than on an outcome is the degenerate configuration. The only valid gold is one
whose origin is *outside the grading loop*: a human curator who recognizes frontier quality, or an
instrumented outcome (the capability's output was used in production and the result was observed). This
is why the Gold-Standard-Factory is a *human/outcome* destination and why FD-03's benchmark deposits are
curated, not synthesized — and it is why FD-04's gold externality benchmark is a hard 1.0 invariant
rather than a graded floor: a single self-generated gold does not merely add noise, it converts the
verdicts grounded on it from measurements into self-fulfilling prophecies.

There is a second, temporal-fidelity subtlety FD-04 inherits from FD-01's ground-truth discipline. A
portability verdict is only correct *relative to the deposit as it was tested*: grading a past PORTABLE
verdict against a gold curated for a later mutation of the deposit would spuriously mark it wrong when
it was right at the time. FD-04 therefore snapshots the (deposit-version, gold-version, target, verdict)
tuple, so the eval set preserves the deposit and gold *as they were* — the same "fingerprint the stable
separately from the volatile" discipline the suite applies throughout: the target and the verdict are
stable, the deposit and the gold are volatile and must be versioned with the tuple. The verdict-accuracy
metric (≥ 0.85) is computed on this frozen set on every material PP change, so a change that quietly
degrades the detector — a gold-freshness regression, a critical-lens mis-marking, a threshold drift — is
caught by a falling agreement number rather than discovered months later as a CO-12 ledger full of
credited-but-hollow demotions. The detector that results is one whose portability verdicts are graded
against two external outcomes it cannot game — a hand-labelled verdict set and a production-regression
audit — which is the only configuration under which a portability-proving component can be trusted to
gate CO-12's dependence credit rather than merely to inflate it.

### III.13 The estimate-verdict calibration loop and the suite's validity closure

The most consequential thing FD-04 produces beyond any single verdict is the continuous
*estimate-versus-verdict join* it feeds back to FD-01 — the mechanism that turns two separate cheap
guesses and expensive tests into one self-improving system, and the concrete place the CWOPS
valid·closed·<30-day flywheel is instantiated for the portability axis. FD-01 estimates portability
cheaply from capability shape (a pure transform → `deterministic`; a taste judgment → `frontier-only`);
FD-04 later proves or refutes that estimate empirically against a gold standard. The distribution of
(estimate, verdict) pairs is a free, continuously-generated calibration signal, and it is designed to be
*valid, closed, and fast* in exactly the CWOPS sense. It is **valid** because FD-04's verdict is an
outcome (does the capability survive on the cheaper substrate against a human gold?), not a proxy — it
cannot be gamed by an eloquent estimate. It is **closed** because the verdict flows back to recalibrate
FD-01's shape heuristic: if FD-01 systematically estimates `mid-model` for capabilities FD-04 proves are
`frontier-only` (adversarial reasoning, cross-domain taste), the heuristic is over-optimistic for those
shapes and is recalibrated downward; if the reverse — FD-01 estimates `frontier-only` for capabilities
FD-04 proves run fine on Sonnet — the suite is leaving portable advantage un-attacked by
under-estimating, and the heuristic is recalibrated upward, directly widening what FD-05 will convert.
It is **fast** because the join updates every time a deposit is decay-tested, not on a quarterly review
— a <30-day, per-deposit cadence, the flywheel velocity CWOPS identifies as the moat's actual source.

This calibration loop is why FD-04's placement in the suite is a logical necessity rather than a
convenience. The suite's terminal purpose is to bend the dependence curve — to spend frontier tokens
only on the delta and to need the frontier model less as the floor rises. That curve can only bend if
demotions are *real*, and demotions are only real if the portability estimates driving them are
*calibrated*, and the estimates are only calibrated if something tests them against outcomes and feeds
the disagreement back. FD-04 is that something. Without it, FD-01's estimates would be uncalibrated
priors forever — the shape heuristic would never learn that adversarial reasoning does not survive a
downgrade, or that a whole class of bounded-reasoning recipes runs fine on Haiku — and FD-05 would
either over-convert (pushing capabilities to substrates that degrade them, hollow demotions) or
under-convert (leaving frontier-only tags on capabilities that were actually portable, a curve that
never bends). The detector closes the gap between what the suite *thinks* it has distilled and what it
*has* distilled, and it closes it continuously, so that over a healthy suite's lifetime the estimate and
the verdict converge — FD-01's cheap priors become progressively better because FD-04's expensive tests
keep correcting them, and the expensive tests are needed less often on mature classes because the priors
they trained are now trustworthy. This is the CWOPS thesis made mechanical: the moat is not any single
portability verdict (a competitor with the same frontier model could run the same transfer test); the
moat is the *closed loop* in which every verdict sharpens the next estimate, so the suite's judgment
about what can be freed from the frontier improves with every deposit it decay-tests — a judgment
grounded, at every step, in an external gold the suite cannot generate for itself, which is the one
property that keeps the whole flywheel valid rather than merely spinning.
