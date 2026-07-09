# FD-01 — Fable Delta Extraction Engine (S-DELTA)

> The irreducible spine of the Fable Advantage Distillation Suite. Where FD-00 declares that a session
> must capture the delta, FD-01 is the engine that *computes* it: given a frontier answer and the
> FD-00 baseline, it isolates the capability the answer demonstrates **above** what the stack could
> already produce, and classifies it `NEW / STRONGER / DUP / DISCARD`. Parent: PM-03 (the findings
> transport it rides), which it extends from *storage* to *differential analysis*. Sealed under
> **SCS C82**. Guarantee level (CO-10): **rung-2 measurement** — it makes the delta legible and
> classifiable at the answer boundary; it does not itself route or write (FD-05/FD-06 do that).

---

## Part I — Mission, the Differential Problem, and the Classification Taxonomy

### I.1 Mission

FD-01 exists to answer one question about every frontier answer, cheaply and repeatably: *what does
this answer prove the model can do that the stack could not already do?* That question is the
difference between a distillation system and a note-taking system, and no existing PP component asks
it. FD-01's mission is to make the answer to that question a **typed object** — a classified delta
with a class, a baseline reference, a portability estimate, and a canonical trace — so that
everything downstream (triage, decay-testing, arbitrage, writeback) operates on a structured delta
rather than on raw prose. The engine is the point in the suite where an unstructured frontier
response becomes a unit of advantage or is honestly discarded.

The mission is deliberately scoped to *extraction and classification only*. FD-01 does not decide
where a delta goes (FD-03's right), does not write it (FD-06's right), and does not prove it is
portable (FD-04's right). It performs the one operation that must happen before any of those: the
subtraction of the baseline from the answer. This narrowness is what makes the engine reliable — it
has exactly one job, its inputs are fixed, its output is a small typed record, and its correctness is
checkable against a held-out set of hand-labelled answer/baseline pairs. A system that tried to
extract, route, and write in one step would be unauditable; FD-01 is the first, cleanest link, and
the suite's integrity depends on that link being sharp.

### I.2 The differential problem (and why it is genuinely hard)

Computing a delta is not diffing two strings. The baseline is a *capability set* — what the stack can
produce — and the answer is a *capability demonstration* — what the model just produced. The delta is
the set-difference in capability space, and capability space is not lexical. Two answers can be
lexically identical and differ in capability (the same code with one changed constant that makes it
correct under concurrency); two answers can be lexically disjoint and identical in capability (a
recipe and its paraphrase). The differential problem is therefore a *semantic* comparison against a
*structured baseline*, and the hard part is that both operands are fuzzy: the baseline is only as good
as CO-05's freshness, and the answer is natural-language reasoning that must be reduced to its
operative capability before it can be compared.

This is exactly the gap PM-03 does not close. PM-03 is a transport: it publishes a finding to a bus
and taxes redundant reasoning, but it has no representation of "what the stack can already do" to
subtract from, so it cannot tell a genuine capability from a well-phrased restatement of one the stack
already holds. FD-01 supplies the missing operand (the FD-00 baseline) and the missing operation (the
capability subtraction). The difficulty is real and the engine treats it with appropriate humility:
its classification is a *best-effort typed verdict with a confidence*, not an oracle, and it is
designed so that its two most costly errors — calling a restatement NEW (inflates the vault) and
calling a genuine delta DISCARD (loses advantage) — are the ones its rubric and gates most aggressively
guard against.

### I.3 The classification taxonomy

FD-01 classifies every frontier answer, against the baseline for its task class, into exactly one of
four classes. The taxonomy is closed — every answer is one of these, and the closure is what makes
the deposit clause enforceable (a session always has a class to deposit, even if it is DISCARD).

- **NEW** — the answer demonstrates a capability the baseline is entirely silent on. The stack could
  not produce this at any quality before; a genuine above-floor delta. Example: a novel concurrency
  isolation scheme the stack had no analogue for. This is the class that most directly lowers the
  dependence curve, and also the class most vulnerable to inflation (a restatement mislabelled NEW),
  so it carries the highest evidentiary burden (II.5).
- **STRONGER** — the baseline holds a capability for this class, but the answer materially improves it
  (correctness, robustness, efficiency, or coverage). Not a new capability, a better version of an
  existing one. Example: an improved retry policy over an existing CO-05 retry recipe. STRONGER deltas
  are deposited as *mutations* of the existing asset (FD-06's UKDL-extend path), not as new records.
- **DUP** — the answer restates a capability the baseline already holds, at no material improvement. A
  paraphrase, a re-derivation, or a general fact the stack could already retrieve. Not deposited;
  discarded to protect deposit precision. The most common misclassification target — DUP dressed as
  NEW is the vault-inflation failure.
- **DISCARD** — the answer is at-floor in the FD-00 sense (the stack could produce it via a cheaper
  rung) or is not a capability at all (a search result, a pleasantry, an error). Recorded as
  `DISCARD: <reason>` so the session's deposit clause is satisfied honestly, but nothing is stored.

The taxonomy maps cleanly to downstream action: NEW → new deposit; STRONGER → asset mutation; DUP →
nothing (protect precision); DISCARD → nothing (honest at-floor record). This one-to-one mapping is
why the taxonomy has exactly four members — each is a distinct downstream route, and adding a fifth
would either duplicate a route or create an unrouted class.

### I.4 Difference from existing systems

**Versus PM-03 (Shared Findings Bus).** PM-03 publishes and de-duplicates findings across panes; its
RedundancyTax blocks a pane from re-deriving a conclusion another pane already published. That is
lexical/topical dedup within a session set, not capability-differential against the stack's floor.
FD-01 extends PM-03 by adding the baseline operand: it asks not "did another pane already say this?"
but "can the stack already *do* this?" — a stricter and more useful test. FD-01 rides PM-03's
transport (a classified delta is published to the bus so other panes see it), but the classification
logic is the genuine extension PM-03 lacks.

**Versus GK-08 (Session Writeback).** GK-08 writes session discoveries to the graph as coordinates and
edges. It is a *destination*, not a *filter* — it will write a restatement and a breakthrough with
equal fidelity. FD-01 is the filter that runs *before* GK-08: only NEW and STRONGER deltas reach the
writeback (via FD-03/FD-06), and DUP/DISCARD are stopped at FD-01. Without FD-01, GK-08's graph fills
with at-floor nodes and the "navigate, don't explore" promise degrades into "navigate a graph full of
things you already knew."

**Versus CO-05 (Zero Token Layer / Asset Registry).** CO-05 is the baseline FD-01 subtracts from, not
a competitor. CO-05 answers "what assets do we have?"; FD-01 answers "does this frontier answer exceed
them?" The two compose: CO-05 supplies the floor, FD-01 measures the delta over it, and when the delta
is STRONGER, FD-06 writes an improved asset back into CO-05 — closing a loop CO-05 alone cannot close
because it has no notion of "better than what I hold."

### I.5 What FD-01 does NOT duplicate (explicit)

FD-01 does **not** transport findings (PM-03 owns the bus), does **not** store or mutate assets (CO-05
+ FD-06), does **not** write to the graph (GK-08), does **not** route a delta to a destination (FD-03),
does **not** test portability (FD-04), and does **not** compute the dependence metric (CO-12). It
performs one operation — classify an answer against a baseline — and emits one typed record. If an
edit to FD-01 begins to decide destinations or write outputs, it has crossed into FD-03/FD-06
territory and must be relocated. The engine's value is precisely its narrowness: a sharp, auditable
subtraction, nothing more.

### I.6 Core principles

- **Capability comparison, not string comparison.** The delta is semantic; lexical overlap is neither
  necessary nor sufficient for DUP.
- **The two costly errors dominate the design.** NEW-inflation and DISCARD-of-real-delta are the
  errors the rubric and gates most guard against; a wrong STRONGER/DUP boundary is cheaper.
- **Every answer gets a class.** The taxonomy is closed so the deposit clause always has something
  honest to record.
- **Confidence is first-class.** A low-confidence classification is surfaced, not hidden; borderline
  cases are flagged for the FD-04 transfer test rather than force-labelled.
- **The baseline must be fresh or the delta is suspect.** A delta over a stale CO-05 asset is
  re-checked against a refreshed baseline before deposit (FD-00 III.1 baseline-drift).

### I.7 Why extraction, not the answer, is the unit of advantage

The deepest justification for FD-01 being a *separate* engine — rather than a step folded into PM-03
or GK-08 — is the same argument CWOPS makes for why the loop, not the feature, is the moat. CWOPS
observes that in 2026 the *answer* a model gives is commoditized: ~90% of features are weekend-
replicable by a solo founder with an API key, and technical superiority died as a moat when Copilot,
Lovable, and v0 recreated Stripe-grade backends in hours. The durable advantage is not the artifact;
it is the *closed, valid, fast loop* that turns each artifact into a permanent improvement in what
the system can do next. FD-01 is the first and most load-bearing station of exactly that loop for the
Power Pack: it is where the commoditized artifact (a frontier answer anyone with the API key could
also get) is converted into the non-commoditized asset (a classified, baseline-relative delta that
only *this* stack, with *its* accumulated floor, could compute). Two teams could receive the identical
Fable answer; the one running FD-01 against its own rising floor extracts a different, smaller, more
precisely-targeted delta than the one running it against an empty baseline — and that difference is
the moat, because it compounds with the floor's history rather than with the answer's content.

This reframes what "extraction" means and why it cannot be reduced to storage. Storing an answer is
what PM-03 and GK-08 do, and storage of a commoditized artifact produces a commoditized vault — the
a16z "empty promise of data moats" in miniature, where raw accumulation has diminishing returns
because everyone can accumulate the same raw material. Extraction is the operation that makes the
vault *proprietary*: the delta is a function of two operands, the answer *and this stack's floor*, and
the floor is the one thing a competitor cannot replicate over a weekend because it is the deposited
history of every prior distillation. The delta therefore inherits the floor's un-replicability. This
is why FD-01 must hold the baseline as a first-class operand and why its correctness depends on the
baseline being complete and fresh: a partial baseline produces an inflated delta that overstates
advantage (the NEW-inflation failure), and an inflated advantage is a commoditized answer wearing a
moat's costume. The engine's discipline around baseline freshness is not fussiness; it is the
guardrail that keeps the extracted delta genuinely proprietary rather than a re-labelled commodity.

The taxonomy's four classes are, read through this lens, four verdicts on *how much of this artifact is
proprietary advantage*. NEW is "wholly above our floor — maximally proprietary, maximally worth
keeping." STRONGER is "an improvement to something we already own — proprietary in its increment,
folded into the existing asset." DUP is "we already own this — zero marginal advantage, storing it
would dilute the vault." DISCARD is "the market already owns this — a cheaper rung or general
knowledge suffices, no advantage exists to extract." The classification is thus not bookkeeping; it is
a continuous measurement of the proprietary fraction of each frontier interaction, and the suite's
dependence curve is precisely the integral of that measurement over time. An engine that classified
generously (everything NEW) would report a fat moat while building a commodity vault; an engine that
classified honestly reports the true, usually-smaller proprietary delta, and it is the honest, smaller
number that actually compounds. This is the reason NEW carries the highest evidentiary burden and the
reason the two costly errors (NEW-inflation, false-DISCARD) are the design's central concern: they are
the two ways the engine can lie about how much proprietary advantage a session produced, and a
distillation suite that lies about its own advantage cannot bend the dependence curve because it
cannot tell whether the curve is bending.

A final consequence of this framing is that FD-01 is the only engine in the suite whose *output volume
should trend down over a healthy stack's lifetime*, and this is a feature, not a decay. As the floor
rises with every deposit, more and more of what the frontier model produces falls at or below it, so
the NEW and STRONGER rates for mature classes decline while DUP and DISCARD rise. A naive reading
would call a falling NEW rate a failing engine; the correct reading is the opposite — a falling NEW
rate on a class the stack has worked heavily is the visible signature of the dependence curve bending,
because it means the stack now already owns most of what the frontier model can offer for that class.
The engine therefore reports its own diminishing relevance per class as the primary evidence of
success, which is why III.11's deprecation trigger fast-paths saturated classes rather than treating
their low NEW rate as a defect. This inverts the usual instinct that more extraction is better: in a
distillation suite, the goal is to *need* to extract less over time, and an engine whose extraction
volume never falls is an engine attached to a stack that is not actually learning — either the floor
is not rising (deposits are not being written back) or the engine is inflating NEW to keep its volume
up. Both are failures the flat-dependence-metric cross-check exposes, and both are disguised by an
engine that measures itself by how much it extracts rather than by how much its extraction shrinks the
gap between the model and the stack.

This is also why FD-01 is built as the *second* dataset, immediately after the FD-00 doctrine and
before every consumer: the entire suite is a set of theorems whose shared axiom is "the delta is
computable," and that axiom is false until FD-01 exists to compute it. FD-03 cannot route a delta it
was never handed; FD-04 cannot decay-test a capability that was never isolated; FD-05 cannot prioritize
conversion of frontier-only deltas that were never classified; FD-06 cannot write back a form that was
never extracted; FD-07 cannot close a loop whose first station is missing. The dependency ordering in
the FD_INDEX is therefore not a convenience but a logical necessity, and it explains why the engine's
contract is kept deliberately minimal — one input tuple, one typed output record, one closed taxonomy.
Every downstream dataset binds to that contract, so widening it (adding a fifth class, a second
baseline, an extra output field) would ripple through five consumers at once. The narrowness that makes
FD-01 auditable is the same narrowness that makes the suite composable: a sharp, stable extraction
contract is the interface the other seven datasets are written against, and its stability is worth more
to the suite than any local cleverness a wider contract might buy. In this sense FD-01 is less a clever
engine than a disciplined one: its power is in what it refuses to do — route, write, self-grade, or
widen — as much as in the single subtraction it performs.

---

## Part II — The Comparison Contract and Classification Rubric

### II.1 Operating contract (inputs and outputs)

FD-01's **inputs** are: the frontier answer (raw); the FD-00 baseline for the task class (the CO-05
asset set + CO-03 sub-frontier envelope + GK-navigable knowledge + prior FD deposits); and the task
class label. Its **output** is a single typed delta record: `{delta_class ∈ {NEW, STRONGER, DUP,
DISCARD}, confidence ∈ [0,1], baseline_ref, capability_summary, portability_estimate, canonical_trace,
discard_reason?}`. The record is the deposit's core; FD-00 wraps it with the session's
`co12_signals` and hands it to FD-03. The contract's hard postcondition: **every answer yields exactly
one record with a non-null class**, so a session can never be in the state "we called the model but
have no verdict on what it produced."

Two output fields deserve emphasis. `capability_summary` is the reduction of the answer to its
operative capability — the recipe/protocol/constraint the answer contains, stripped of the model's
reasoning path. This is the object actually compared against the baseline, and reducing to it before
comparison is what makes the comparison capability-level rather than lexical. `portability_estimate`
is FD-01's cheap first guess at the least-capable substrate that could run the capability
(`deterministic/small-model/mid-model/frontier-only`); it is an estimate, not a proof — FD-04 owns the
proof — but it seeds FD-05's conversion worklist and FD-04's test queue.

### II.2 The comparison procedure (capability subtraction)

The comparison runs in four steps, each with a defined output, so the verdict is traceable rather than
a single opaque judgment. **Step 1 — reduce.** Reduce the answer to its `capability_summary`: the
minimal statement of what it lets you do, dropping the model's prose reasoning. **Step 2 — locate.**
Query the baseline for the nearest existing capability for this task class (CO-05 asset, prior deposit,
or sub-frontier envelope). **Step 3 — compare.** Judge the reduced capability against the located
baseline capability on four axes: presence (does the baseline have anything for this?), correctness
(is the answer more correct?), robustness (does it handle cases the baseline misses?), and coverage
(does it span more of the class?). **Step 4 — classify.** Map the comparison to the taxonomy: baseline
silent → NEW; baseline present but answer better on ≥1 axis → STRONGER; baseline present and answer no
better → DUP; answer at-floor or non-capability → DISCARD.

The procedure is deliberately explicit because the failure modes cluster at specific steps. A skipped
Step 1 (comparing raw prose instead of the reduced capability) produces lexical-overlap errors — the
paraphrase looks different so it is called NEW. A weak Step 2 (a stale or incomplete baseline) produces
NEW-inflation — the baseline appears silent because it was not fully loaded. Making each step a named,
inspectable output means an audit can localize a misclassification to the step that caused it, which
is how the engine's accuracy is improved over time rather than treated as a black box.

### II.3 Interfaces with existing PP systems

- **PM-03** — FD-01 publishes each NEW/STRONGER delta to the findings bus so concurrent panes consume
  it before re-reasoning; it also *reads* the bus in Step 2 (a delta another pane just published is
  part of the effective baseline).
- **CO-05** — the primary baseline source (assets + freshness); FD-01 reads it in Step 2 and never
  writes it (FD-06 does).
- **CO-03** — supplies the sub-frontier envelope for the DISCARD/at-floor test: if CO-03 says a cheaper
  rung could produce the capability, the answer is DISCARD regardless of how polished it is.
- **FD-00** — supplies the baseline object and the task class; receives the typed record.
- **FD-03/FD-04/FD-05/FD-06** — consumers of the record (destination, decay-test, arbitrage,
  writeback respectively).
- **CO-12** — receives the class distribution as the deposit-precision signal.

### II.4 Decision rights and non-decision rights

FD-01 **may decide**: the `capability_summary` reduction; the nearest baseline capability; the
per-axis comparison; the final class and confidence; and the portability *estimate*. FD-01 **may not
decide**: the destination of a delta (FD-03); whether a STRONGER delta mutates which specific asset
(FD-06 executes, though FD-01 identifies the nearest asset); whether the portability estimate holds
(FD-04 proves it); or the dependence metric (CO-12). The boundary with FD-04 is the subtle one:
FD-01 *estimates* portability cheaply from the shape of the capability (a pure transform → likely
deterministic; a taste judgment → likely frontier-only), while FD-04 *tests* it empirically. FD-01's
estimate is a prior; FD-04's test is the posterior; the estimate seeds the test queue and is
overwritten by the test result.

### II.5 Classification rubric with criteria (binary where possible)

Each class has entry criteria to make the verdict defensible rather than intuitive.

| Class | Entry criteria (all must hold) | Evidentiary burden |
|---|---|---|
| **NEW** | (a) baseline is silent on the reduced capability after a *fresh* baseline load; (b) the capability is a genuine capability, not a fact; (c) confidence ≥ 0.6 or flagged for FD-04 | Highest — must show the baseline was fully loaded and genuinely silent (guards NEW-inflation) |
| **STRONGER** | (a) baseline holds a capability for this class; (b) the answer is better on ≥1 of {correctness, robustness, efficiency, coverage} with a named difference; (c) the named difference is reconstructable | Medium — must name the specific improvement, not "generally better" |
| **DUP** | (a) baseline holds the capability; (b) answer is no better on any axis; (c) any lexical difference is paraphrase, not capability | Low — but must confirm Step 1 reduction ran (guards paraphrase-as-NEW) |
| **DISCARD** | (a) at-floor per CO-03 (a cheaper rung suffices) OR (b) not a capability | Low — must record the reason |

The evidentiary burden is asymmetric on purpose: NEW is the class that inflates the vault and
overstates advantage, so it must prove the baseline was fresh and silent; DISCARD is cheap to assign
but must record its reason so an audit can catch a real delta wrongly discarded. This asymmetry
directly implements the I.6 principle that the two costly errors dominate the design.

### II.6 Token-ROI rules

FD-01 is itself a cost, and the doctrine forbids a classifier that costs more than it saves. The
engine's own ROI rule: classification runs on the *cheapest sufficient* substrate. The Step 1
reduction and Step 3 comparison for most answers are bounded reasoning a Sonnet rung handles; only a
genuinely ambiguous NEW/DUP boundary warrants a frontier-grade judgment, and even then only when the
task class is high-frequency enough that a misclassification is expensive. A low-frequency class with
an ambiguous delta is better flagged low-confidence and sent to FD-04 than resolved with an expensive
frontier classification — the transfer test is a cheaper, more decisive arbiter than a second frontier
opinion. This keeps FD-01 from becoming the CWOPS anti-pattern of a guardrail that costs more than the
loss it prevents.

### II.7 Portability estimation rules

The `portability_estimate` is assigned by capability *shape*, a cheap heuristic FD-01 can apply without
running anything: a deterministic transform (format, dedup, parse) → `deterministic`; a bounded
reasoning recipe with clear inputs/outputs → `small-model` or `mid-model` by complexity; a judgment
requiring taste, cross-domain synthesis, or adversarial reasoning → `frontier-only`. The estimate is
explicitly a prior to be tested, never a claim. A `frontier-only` estimate on a NEW delta means "we do
not yet know how to run this without the frontier model" — an honest statement of current dependence,
and precisely the deposit FD-05 will most want to attack. FD-01 records the estimate; FD-04 tests it;
the gap between estimate and test result is itself a signal (systematic over-optimism in the estimate
means the heuristic needs recalibration).

### II.8 Compression and no-bloat rules

FD-01 enforces no-bloat at the earliest possible point: a DUP is never deposited, and a DISCARD is
never stored beyond its one-line reason. This is the deposit-precision protection at its source —
every DUP correctly caught at FD-01 is a vault entry that never has to be garbage-collected later.
Compression of a deposited delta follows FD-00 II.7: the `capability_summary` is already the
compressed form (the reasoning was dropped in Step 1), so a NEW/STRONGER deposit is compact by
construction. The engine's contribution to suite-wide compression is structural: because it reduces to
capability before storing, nothing verbose ever enters the vault in the first place.

### II.9 A fully worked comparison: the same answer against two floors

The clearest way to specify the comparison contract is to run one frontier answer through the four
steps against two different baselines and show that the *same answer* yields two *different* deltas —
the property that makes the extraction proprietary rather than commoditized. Consider the frontier
answer: "To deduplicate a stream of documents under a token budget, hash each document's normalized
content with SHA-256, store the hash keyed by a semantic-cluster id computed from a cheap embedding,
and on collision within a cluster compare only the cluster members rather than the whole store; evict
the least-recently-matched cluster when the budget is hit." This is a real, compound capability with
several moving parts.

**Against Floor A (a mature stack).** Step 1 reduces the answer to its operative capability:
"semantic-cluster-scoped SHA-256 dedup with LRU cluster eviction under a token budget." Step 2 queries
the baseline and finds CO-05 already holds a plain SHA-256 content-hash dedup recipe *and* a prior FD
deposit for semantic-cluster bucketing, but nothing that combines them with budget-bounded LRU
eviction. Step 3 compares on the four axes: presence — the two component capabilities exist, the
*composition* does not; correctness — equal on the components; robustness — the answer adds the
budget-eviction case the components miss; coverage — the answer spans the budgeted-stream case neither
component covers alone. Step 4 classifies: not NEW (the components are on the floor) and not DUP (a
real improvement exists), therefore **STRONGER**, with the named increment "budget-bounded LRU cluster
eviction," portability `deterministic` (it is a pure algorithm), confidence 0.8. FD-06 will mutate the
existing semantic-cluster asset to incorporate the eviction rule rather than store a new record.

**Against Floor B (a younger stack).** The identical answer, Step 1 identical reduction. Step 2 finds
CO-05 holds *only* plain SHA-256 dedup; there is no semantic-cluster asset at all. Step 3: presence —
the baseline is silent on cluster-scoped dedup entirely; the whole clustering-plus-eviction capability
is above the floor. Step 4 classifies **NEW**, with the full capability as the delta, portability
`deterministic`, confidence 0.85. FD-06 will create a new deposit.

The two runs are the entire argument for the engine. The commoditized artifact — the answer — is
identical; anyone could obtain it. The extracted advantage differs because the floor differs: the
mature stack extracts only the thin budget-eviction increment (because it already owned the rest),
while the younger stack extracts the whole capability (because it owned little of it). This is the
extraction operation making the vault proprietary: the mature stack's delta is *smaller and more
precisely targeted*, which is exactly correct — it should spend its downstream distillation effort
only on the genuinely-missing increment, not re-store what it already has. An engine that ignored the
floor and classified the answer identically in both cases would inflate the mature stack's vault with
a capability it already owned (NEW-inflation) and would misdirect FD-05's arbitrage effort onto
already-distilled work. The worked example also demonstrates why Step 1's reduction is load-bearing:
without reducing to the compound capability, a lexical comparer against Floor A would see substantial
new wording and misclassify NEW; the reduction is what lets Step 3 see that most of the *capability*
was already present even though most of the *words* were not. Confidence differs slightly between the
runs (0.8 vs 0.85) because the STRONGER boundary is intrinsically more ambiguous than the NEW one —
judging "how much better" is harder than judging "present or absent" — and the engine surfaces that
ambiguity rather than hiding it, per the first-class-confidence principle.

### II.10 How confidence is computed, and what a low score triggers

Confidence is not a decorative number; it is the field that decides whether a delta is deposited
directly or routed to FD-04 for an empirical tie-break, so its computation must be principled rather
than a gut feeling appended after the fact. FD-01 derives confidence from three inspectable
components. The first is *baseline completeness*: if CO-05's freshness verdict is green and the task
class has a well-populated floor, a "baseline is silent" judgment is trustworthy and confidence is
high; if the floor is amber or sparse, a NEW verdict is intrinsically less certain because the
silence might be a gap in the baseline rather than a genuine absence in the stack. The second is
*axis clarity*: a STRONGER verdict backed by a single, cleanly-named improvement on one axis
(robustness, say) is more confident than one resting on a diffuse "generally better across several
axes," because the diffuse case is where the DUP boundary blurs. The third is *reduction stability*:
if two independent reductions of the same answer (Step 1 run twice, or by two rungs) produce the same
`capability_summary`, the capability was cleanly extractable and the comparison is on firm ground; if
they diverge, the answer's operative capability is itself ambiguous and any downstream comparison
inherits that ambiguity.

The three components combine into a single score in [0,1], and the important design commitment is what
happens at the low end rather than the high end. A confidence below 0.6 does *not* force a label; it
triggers one of two deferral paths. For a NEW/DUP ambiguity, the delta is provisionally classified and
flagged for a refreshed-baseline re-check — the ambiguity is often a stale-floor artifact that a fresh
CO-05 load resolves. For a STRONGER/DUP ambiguity (is this actually better or just different?), the
delta is routed to FD-04, whose empirical transfer test is a more decisive arbiter than a second
opinion: if the claimed improvement survives on the target substrate and the baseline version does
not, it was genuinely STRONGER; if both perform equally, it was DUP. This is the concrete mechanism by
which FD-01 refuses the oracle pose — it does not manufacture certainty on the cases that are
genuinely uncertain; it defers them to the cheaper, more decisive instrument. The consequence for the
suite is that the confidence distribution is a live health signal in its own right: a healthy engine
shows a spread with a meaningful tail below 0.6 (real ambiguity exists and is being deferred), whereas
a distribution pinned near 1.0 is the confidence-theater failure mode — an engine force-labelling
everything to look decisive, which is precisely the behavior the deferral paths exist to make
unnecessary. The deferral design also has a favorable cost profile: the cases it routes to FD-04 are
by construction the *ambiguous* ones, which are a minority of answers, so the expensive empirical
tie-break is spent only where it changes a decision — never on the clear NEW or clear DISCARD that a
cheap first pass already settles. This is the II.6 token-ROI rule applied to the engine's own
uncertainty: certainty is cheap and resolved inline, ambiguity is rare and resolved by the one
instrument (the transfer test) decisive enough to be worth its cost.

---

## Part III — Failure Modes, Gates, Benchmarks, and Evolution

### III.1 Failure modes with diagnosis protocol

| Failure mode | Symptom | Diagnosis | Root cause |
|---|---|---|---|
| **NEW-inflation** | NEW rate high, dependence metric flat, deposits later reclassify to DUP | re-run classification against a freshly loaded baseline; count NEW→DUP flips | stale/partial baseline in Step 2, or skipped Step 1 reduction |
| **Delta loss (false DISCARD)** | dependence flat despite frontier spend; audit finds discarded answers that were real deltas | sample DISCARDs, re-classify with a second rubric pass | over-aggressive at-floor test, or CO-03 envelope overstated |
| **Paraphrase-as-NEW** | lexically-novel deposits that are capability-identical to existing assets | check whether Step 1 reduction ran; compare `capability_summary`, not raw text | Step 1 skipped; comparison ran on prose |
| **Confidence theater** | all classifications report confidence ~1.0 | inspect confidence distribution; a healthy engine has a spread | confidence not genuinely computed; force-labelling borderline cases |
| **Estimate drift** | FD-04 systematically overturns portability estimates in one direction | join estimates to FD-04 outcomes | the shape heuristic (II.7) is miscalibrated for this class |

The engine's characteristic failure is NEW-inflation because it is the failure that *feels* like
success — a high NEW rate looks like a productive engine, and only the join to the flat dependence
metric reveals that the "new" capabilities were restatements. This is the FD analogue of CWOPS §4.6's
degenerate-feedback trap: the engine optimizing the appearance of novelty rather than real novelty.
The fingerprint-and-metric join (FD-00 III.1) is the cross-check; FD-01's own guard is the fresh-
baseline requirement in NEW's entry criteria.

### III.2 Anti-patterns with evidence

- **The impressed classifier.** Labelling a well-written answer NEW because it is impressive, not
  because the baseline was silent. Evidence: the a16z empty-data-moat finding — quality of expression
  is not advantage; only the differential is. Forbidden by NEW's fresh-baseline entry criterion.
- **Lexical dedup masquerading as capability dedup.** Using string similarity to assign DUP, which
  misses paraphrased duplicates and flags reworded genuine deltas. Evidence: PM-03's RedundancyTax is
  explicitly topical/lexical and FD-01 exists precisely to add the capability layer PM-03 lacks.
  Forbidden by the Step 1 reduction requirement.
- **The oracle pose.** Reporting classification as certain when the NEW/DUP boundary was genuinely
  ambiguous. Evidence: CO-12's honesty rule — unmeasured is surfaced, never faked. Forbidden by the
  first-class confidence field and the FD-04 flag for borderline cases.
- **Expensive classification of cheap classes.** Spending frontier tokens to classify a low-frequency
  answer whose misclassification costs little. Evidence: CWOPS's guardrail-cost caution. Forbidden by
  II.6.

### III.3 Quality gates (binary)

- **G1 — Reduction ran.** Does every classification carry a `capability_summary` distinct from the raw
  answer? Binary.
- **G2 — Baseline freshness.** Was the baseline's freshness verdict green at classification time (or
  the delta flagged for re-check)? Binary.
- **G3 — Class assigned.** Does every answer carry exactly one class? Binary (the closed-taxonomy
  postcondition).
- **G4 — NEW evidence.** Does every NEW carry evidence the baseline was fresh and silent? Binary.
- **G5 — Confidence present.** Does every classification carry a genuine confidence, with borderline
  cases flagged for FD-04? Binary.

### III.4 Evaluation rubric (measurable)

| Dimension | Metric | Source | Target |
|---|---|---|---|
| Classification accuracy | agreement with a held-out hand-labelled answer/baseline set | eval set | ≥ 0.85 |
| NEW precision | fraction of NEW deltas that survive re-check on a fresh baseline | reclassification audit | ≥ 0.9 |
| DISCARD recall | fraction of genuine at-floor answers correctly discarded | sampled audit | ≥ 0.9 |
| Estimate calibration | fraction of portability estimates FD-04 confirms | estimate↔FD-04 join | rising |
| Confidence spread | variance of the confidence distribution (non-degenerate) | classification log | > 0 (not all ~1.0) |

### III.5 Benchmarks with reference values

The engine's benchmarks anchor to the suite's economics. **Precision floor:** NEW precision ≥ 0.9 —
below this, deposit precision (FD-00 II.8) cannot hold ≥ 0.8 and the vault inflates. **Accuracy
floor:** ≥ 0.85 agreement with the hand-labelled set, the threshold below which the classifier is not
trustworthy enough to gate the vault. **Cost ceiling:** FD-01's per-classification cost must be a small
fraction of the frontier answer it classifies — the CWOPS guardrail-economics principle that the
detector must cost far less than the loss it prevents; a classifier that costs as much as a re-ask has
no ROI. **Reclassification stability:** on a fresh baseline, ≥ 0.9 of NEW deltas remain NEW — a lower
stability means the baseline loading is the weak link, not the classifier.

### III.6 Example operational traces

**Trace A — NEW.** Answer: a novel pane-isolation scheme. Step 1 reduces to a 3-rule protocol. Step 2:
baseline (PM-02 collision detection) is silent on this scheme. Step 3: presence axis — baseline
absent. Step 4: NEW, confidence 0.8, portability estimate `mid-model` (expressible as a Sonnet
protocol). Published to PM-03; handed to FD-03.

**Trace B — STRONGER.** Answer: an improved retry policy. Step 1 reduces to the policy. Step 2: CO-05
holds a retry recipe. Step 3: robustness axis — the answer handles a jitter case the recipe misses,
named explicitly. Step 4: STRONGER, confidence 0.75, portability `deterministic`. FD-06 will mutate
the existing recipe.

**Trace C — DUP (paraphrase).** Answer: a reworded explanation of an existing dedup pattern. Step 1
reduces to "SHA-256 content-hash dedup." Step 2: CO-05 holds exactly this. Step 3: no axis improved.
Step 4: DUP despite ~0 lexical overlap with the stored asset — the reduction caught the capability
identity. Not deposited.

**Trace D — DISCARD.** Answer: a correct but general explanation of OAuth PKCE. Step 2/CO-03: a
sub-frontier rung produces this. Step 4: `DISCARD: at-floor (sub-frontier sufficient)`. Recorded, not
stored.

**Trace E — low-confidence, deferred.** Answer: a data-pipeline design that partly overlaps an existing
asset. Step 3 is genuinely ambiguous (better on coverage, worse on simplicity). Confidence 0.5.
Classified provisional-STRONGER, flagged for FD-04 to test whether the coverage gain survives on a
mid-model substrate before FD-06 mutates anything.

### III.7 Edge cases

- **Empty baseline (new task class).** Everything is trivially NEW; FD-01 flags the class as
  un-baselined so NEW-inflation cannot be inferred from a high NEW rate on a class that legitimately
  has no floor yet.
- **Answer mixing delta and at-floor content.** The answer is decomposed; the above-floor part is
  extracted as the delta, the at-floor part discarded. A single answer can yield one NEW plus one
  DISCARD.
- **Contradictory delta.** The answer contradicts an existing deposit. Classified STRONGER with a
  supersede flag; FD-06 supersedes the old deposit with a back-reference, never silent-deletes.
- **Non-reconstructable capability.** The answer's capability cannot be summarized without the model's
  full reasoning (rare, usually a sign of a genuinely frontier-only capability). Deposited NEW with
  portability `frontier-only` and an explicit note that compression failed — an honest hypothesis for
  FD-04.
- **Stale baseline suspected.** If CO-05 freshness is amber, the NEW verdict is provisional pending a
  refresh, per FD-00 III.1.

### III.8 Writeback rules

FD-01 does not write; it emits the typed record and publishes NEW/STRONGER to PM-03. The record's
mandatory fields must all be present before FD-03 accepts it — a record missing `capability_summary`,
`delta_class`, or `baseline_ref` is malformed and rejected, which prevents an unclassified answer from
reaching the graph. DUP and DISCARD records are emitted for the audit trail (so precision can be
measured) but carry an explicit "do-not-store" flag that FD-06 honors.

### III.9 Conceptual regression tests

- **R1 — Capability dedup.** Feed a paraphrase of a stored asset; assert DUP (not NEW).
- **R2 — Fresh-baseline NEW.** Feed a genuine novel capability; assert NEW with baseline-silent
  evidence.
- **R3 — At-floor discard.** Feed a sub-frontier-answerable question; assert DISCARD with reason.
- **R4 — STRONGER names the diff.** Feed an improved recipe; assert STRONGER with a named improvement
  axis.
- **R5 — Confidence non-degenerate.** Feed an ambiguous case; assert confidence < 0.6 and an FD-04
  flag, not a forced label.
- **R6 — Malformed reject.** Feed a record with no reduction; assert the writeback rejects it.

Per SCS C41, these are gate assertions for the EXECUTION-mode harness, not auto-generated unit tests;
the accuracy metric is measured against a hand-labelled eval set, which is the honest observation the
anti-test-theater rule requires.

### III.10 Done criteria (verifiable)

FD-01 is done when: the dataset exists on disk, un-truncated, >2500 real words/Part; the four-class
taxonomy is closed and each class maps to exactly one downstream route; the comparison procedure is
specified as four inspectable steps; the classification rubric has per-class entry criteria with the
NEW-highest evidentiary asymmetry; G1–G5 are binary; the engine declares CO-05 as its baseline source
and PM-03 as its transport (no re-implementation); and V-FD-NO-CODE finds zero code fences.

### III.11 Upgrade path

- **v1 (this dataset):** the classification engine as a rung-2 measurement layer applied per answer.
- **v2 (EXECUTION-mode):** the eval set is materialized (hand-labelled answer/baseline pairs) and the
  accuracy metric is computed on each PP change, so classifier drift is caught; the shape heuristic
  (II.7) is recalibrated from the accumulated estimate↔FD-04 join.
- **v3:** the baseline query (Step 2) is served by the GK route compiler so the floor is navigated,
  not re-scanned, making classification cheaper and the baseline freshness structural.
- **Deprecation trigger:** if a task class's NEW rate falls to a durable near-zero (the floor has
  risen to cover the class), FD-01 stops deep-classifying that class and fast-paths its answers to
  DISCARD/DUP — the engine's own success narrows its work, mirroring FD-00's terminal state.

### III.12 The accuracy ground-truth and why it cannot be self-graded

FD-01 is the one FD dataset whose correctness is a *measurable* quantity rather than a design
property, and that raises a specific integrity risk the engine must engineer against: the temptation
to grade its own classifications. A classifier that scores itself will drift toward whatever
maximizes its self-score, which for a delta engine is almost always over-classifying NEW — the class
that makes the engine look most productive. This is the exact degenerate-feedback trap CWOPS §4.6
names: training on the outputs your own algorithm ranked first teaches the model to reproduce its own
predictions, amplifying a proxy (apparent novelty) instead of the target (real advantage). The
antidote CWOPS prescribes — *outcome data, not usage logs, from an instrumented process, weighted
toward outcome over engagement* — maps directly onto FD-01's design: the engine's accuracy is graded
against an external, hand-labelled ground-truth set of answer/baseline/correct-class triples, never
against its own prior verdicts, and the decisive downstream outcome (does FD-04 confirm the extracted
delta actually transferred to a cheaper substrate?) is weighted above the engine's own confidence when
the two disagree.

The ground-truth set is therefore a first-class artifact of the suite, not an afterthought. It is
assembled from real sessions: a sample of frontier answers, each paired with the baseline that was
live at classification time and a class hand-assigned by inspection. Crucially, the pairing preserves
the *baseline as it was*, because a classification is only correct relative to the floor it was made
against — grading a past NEW verdict against today's higher floor would spuriously mark it wrong when
it was right at the time. This temporal fidelity is the same discipline Agent Studio's fingerprinting
applies (fingerprint what is stable separately from what is volatile): the answer and the label are
stable, the baseline is volatile and must be snapshotted with the pair. The accuracy metric (≥ 0.85
agreement) is computed on this frozen set on every material PP change, so that a change which quietly
degrades the classifier — a baseline-loading regression, a reduction-step weakening — is caught by a
falling agreement number rather than discovered months later as a vault full of inflated NEWs.

There is a second, subtler ground-truth: the estimate-versus-test join between FD-01's portability
*estimate* and FD-04's portability *test*. FD-01 guesses, cheaply, that a capability is
`deterministic` or `mid-model` or `frontier-only` from its shape; FD-04 later proves or refutes that
guess empirically. The distribution of (estimate, test-result) pairs is a free, continuously-generated
calibration signal: if FD-01 systematically estimates `mid-model` for capabilities FD-04 proves are
`frontier-only`, the shape heuristic is over-optimistic and must be recalibrated downward; if the
reverse, the engine is leaving portable advantage on the table by under-estimating what a cheaper
substrate can run. This join is the engine's self-correction loop, and it is designed to be *valid,
closed, and fast* in exactly the CWOPS sense — valid because FD-04's test is an outcome not a proxy,
closed because the test result flows back to recalibrate the estimator, and fast because the join
updates every time a deposit is decay-tested rather than on a quarterly review. The engine that
results is one whose two hardest judgments — is this genuinely NEW, and how far can it be downgraded —
are both continuously graded against external outcomes it cannot game, which is the only configuration
under which a self-measuring component can be trusted to bend the dependence curve rather than merely
to report that it is bending.

### III.13 Interaction with the Parallel Mesh: extraction under concurrency

A subtlety the engine must handle explicitly is that FD-01 rarely runs in isolation — the Parallel
Mesh permits several panes on one repo, and each pane may be running its own Fable session against the
*same* rising floor. This creates a race that, mishandled, produces two failure modes. The first is
*duplicate extraction*: two panes receive different frontier answers to related questions, both
extract a delta, and both deposit near-identical capabilities because neither saw the other's
in-flight work. The second is *baseline staleness within a session*: pane A deposits a delta that
raises the floor, and pane B, whose baseline was snapshotted before that deposit, then extracts the
same capability as NEW because its floor is a few minutes out of date. Both are the concurrency
analogue of the NEW-inflation failure, and both are resolved by the same mechanism the Mesh already
provides: PM-03's findings bus, consumed *before* reasoning. FD-01's Step 2 therefore reads the live
bus as part of the effective baseline, so a delta another pane published seconds ago is part of the
floor pane B subtracts against, and PM-03's RedundancyTax blocks pane B from re-depositing what pane A
already published. The engine does not invent new concurrency machinery for this; it consumes the
Mesh's existing consume-before-reason gate, which is exactly the "one system, no parallel systems"
discipline the suite inherits. The only FD-specific addition is that the bus entry for an in-flight
delta carries its provisional class, so a concurrent pane can tell a confirmed NEW from a still-being-
tie-broken provisional one and avoid depositing against an unsettled verdict. This keeps the extraction
engine correct under the exact concurrency the Owner actually runs — six to ten panes on one repo —
rather than only in the single-pane case, and it does so by leaning on PM-03 rather than by building a
second, competing coordination layer that would fracture the shared floor into per-pane floors and
destroy the very un-replicability I.7 identifies as the source of the moat.
