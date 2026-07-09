# FD-05 — Anti-Dependence Arbitrage

> The station of the Fable Advantage Distillation Suite that turns a distilled delta into a *reduction
> in future frontier calls*. Where FD-01 classifies the delta and FD-04 proves it survives a model
> downgrade, FD-05 acts on those verdicts: for every capability the stack currently escalates to the
> frontier, it decides the cheapest substrate that would still be sufficient, and it emits the two
> artifacts that make the demotion real — a new **CO-03** routing rule and/or a new **CO-05** asset
> candidate. "Arbitrage" is exact and not metaphorical: it exploits the gap between what a capability
> *currently costs* (a frontier call) and what it *could cost* (a deterministic rung) once the delta
> is distilled. Parents it EXTENDS, never rebuilds: **CO-03** (the Vault→asset→deterministic→Haiku→
> Sonnet→Opus router — FD-05 feeds it rules, does not re-route), **CO-05** (the Zero-Token asset
> registry — FD-05 feeds it candidates, does not store), **CO-12** (the dependence metric — FD-05's
> conversions are what *move* its model-demotion / Opus-avoided count). It absorbs three named
> candidates — Cognitive Arbitrage Router, Frontier-to-Deterministic Conversion, and Capability Gap
> Radar — as one section-set, not three systems. Sealed under **SCS C82**. Guarantee level (CO-10):
> **rung-2→rung-3 proposal, proof-gated** — FD-05 *proposes* a conversion and emits the artifacts, but
> the routing is enforced by CO-03 (hook/wrapper level) and no conversion goes live until FD-04's
> empirical transfer proof passes; the demotion is a hypothesis until that gate clears, per the
> CO-12 Telemetry-Before-Claims Contract.

---

## Part I — Mission, the Arbitrage Problem, the Substrate Taxonomy, and Core Principles

### I.1 Mission

FD-05 exists to answer one question about every capability the stack possesses: *how must this
capability be served, and how much cheaper could it be served if we distilled it?* That is the
difference between a stack that merely records what a frontier model can do and a stack that
systematically stops paying frontier prices for things it has already learned. FD-05's mission is to
take the classified deltas FD-01 produces and the portability verdicts FD-04 confirms, find the
capabilities the stack still escalates to the frontier for at high frequency, and *actively convert*
the convertible ones to the cheapest sufficient substrate by feeding new rules into CO-03 and new
recipes into CO-05. It is the station of the suite that most directly bends the dependence curve,
because it is the only one whose output is a permanent change in *where the router sends the next
request of that class*. Every other FD dataset makes the delta legible, portable, or filed; FD-05 is
the one that turns legibility into a lower bill.

The mission is deliberately framed as *arbitrage* rather than *optimization*, and the distinction is
load-bearing. Optimization implies squeezing a fixed process for marginal gains. Arbitrage implies
exploiting a *price gap* that exists because two markets have not yet been connected: the "market" in
which a capability is priced at a frontier call, and the "market" in which the same capability, once
its recipe is known, is priced at a deterministic rung or a cache hit. That gap is enormous and it is
the same gap CWOPS quantifies as the roughly thousand-fold cost swing between an unbounded frontier
invocation and a bounded, cheap-substrate execution of an equivalent capability. FD-05 is the mechanism
that harvests that swing, one capability at a time, in ranked order of expected saving. The gap is not
closed once and forgotten; it re-opens every time the frontier model demonstrates a *new* capability
(FD-01 emits a NEW delta with a `frontier-only` estimate), and FD-05's standing job is to keep pushing
each newly-demonstrated capability down the cost ladder as fast as FD-04 can prove the demotion safe.

### I.2 The arbitrage problem (and why it is genuinely hard)

The naïve version of this problem — "route cheap things to cheap models" — is already solved: that is
literally CO-03's cascade. FD-05 exists because the hard version is unsolved by CO-03 alone. CO-03
routes a request based on the request's *apparent* difficulty at routing time; it has no mechanism for
*discovering* that a class of request which has always looked frontier-hard is, in fact, reducible to a
deterministic recipe once someone has seen the frontier model solve it enough times to extract the
pattern. The router can only send a request to a rung that already knows how to serve it. Populating
those lower rungs with capabilities that *used* to require the frontier is precisely the work CO-03
cannot do for itself, because it requires the differential history (FD-01's deltas), the portability
proof (FD-04's verdicts), and a ranking of which conversions are worth the distillation effort. FD-05
supplies all three and hands CO-03 the finished rule.

The difficulty has three faces. First, **feasibility is not obvious from the surface**: a capability
that looks irreducibly frontier (composing a nuanced explanation) may in fact be a template with three
slots once you have watched the model produce forty instances, while a capability that looks trivially
deterministic (choosing a retry delay) may hide a judgment that no fixed rule captures. Misjudging
feasibility in either direction is costly — a forced conversion that fails the gold standard is worse
than no conversion, and a missed conversion leaves money on the table indefinitely. Second, **the
prioritization is an economic problem, not a technical one**: with a finite distillation budget, FD-05
must convert the capabilities whose expected saving (frequency × per-call cost × feasibility) is
highest, not the ones that are most intellectually satisfying to reduce. Third, **the conversion must
be proven before it ships**: a routing rule that sends a class to a cheaper substrate which then
produces worse answers is a silent quality regression that the dependence metric would happily record
as "success" (frontier calls went down) while the actual output degraded. This is why FD-05 is
proof-gated on FD-04 and why "irreducibly-frontier" is a first-class, honorable verdict rather than an
admission of failure.

### I.3 The substrate classification taxonomy

FD-05 classifies every capability by the cheapest substrate that could serve it *sufficiently* — where
"sufficiently" is defined by FD-04's gold standard, never by FD-05's optimism. The taxonomy is a
descending cost ladder that mirrors CO-03's cascade read from the bottom up: the router escalates from
cheap to expensive at request time; FD-05 *demotes* from expensive to cheap at distillation time. The
seven rungs are closed and ordered, and every capability the stack has is assigned exactly one *target*
rung (which may equal its current rung, meaning no arbitrage is available).

| Rung | Substrate | Model? | Marginal cost | The capability's shape that fits here | Example |
|---|---|---|---|---|---|
| 0 | **Cached** | none | ≈ zero (lookup) | Identical inputs recur; the answer is stable and reusable verbatim | A canonical config block re-emitted every session |
| 1 | **Deterministic** | none | ≈ zero (compute) | A pure transform / algorithm with clear inputs and outputs; no judgment | SHA-256 content dedup; a parser; a formatter |
| 2 | **Template-based** | none | ≈ zero (fill) | A fixed structure with a small, bounded set of slots the model always fills the same way | A commit-message scaffold; a boilerplate handler with 3 parameters |
| 3 | **Small-model (LLM-assisted)** | Haiku-class | low | Bounded reasoning, narrow domain, tolerant of a cheap model's ceiling | Classifying a log line into one of nine categories |
| 4 | **Mid-model (LLM-assisted)** | Sonnet-class | medium | Structured reasoning with real but bounded complexity | Drafting a bounded protocol from a clear spec |
| 5 | **Frontier (LLM-needed)** | Opus/Fable-class | high (unbounded) | Taste, novel synthesis, adversarial critique, genuine cross-domain leaps | Judging whether a design *feels* right; inventing a scheme with no analogue |
| — | **Eval-only** | (harness) | one-time | Not a serving substrate but a *verification* rung; the capability is a check, run once per change | A regression assertion; a gold-standard comparison |
| — | **Human-approval** | none | Owner time | Irreducible to any model; requires an Owner decision (irreversible / policy / taste-final) | Authorizing a secret rotation; approving a production deploy |

The first five rungs are the serving ladder; the two trailing rows are non-serving classifications that
must exist because some "capabilities" are not answers to be served at all — they are checks to be run
(eval-only) or decisions only the Owner may make (human-approval). Collapsing rungs 3 and 4 as
"LLM-assisted" and rung 5 as "LLM-needed" matches the family's vocabulary from the FD_INDEX; the finer
Haiku/Sonnet split matters because the per-call cost gap between them is itself an arbitrage a mature
FD-05 harvests (demoting a Sonnet class to Haiku is a smaller but real saving). The ladder's economic
gradient is steep and non-linear: the drop from rung 5 to rung 1 is the CWOPS ~1000× swing, the drop
from rung 4 to rung 3 is perhaps 10–20×, and the drop from rung 0's cache to a live lookup is the
difference between a token spend and none. FD-05 prioritizes the steepest feasible drops first.

### I.4 Difference from existing systems

**Versus CO-03 (Dynamic Cognitive Router).** CO-03 owns the routing cascade — it *executes* the
decision of which rung serves a live request. FD-05 does not route a single request and does not
contain a cascade. It produces *rules* that CO-03 will later apply: "requests of class X now have a
deterministic recipe at CO-05 asset Y; route them there." CO-03 without FD-05 is a router whose lower
rungs only ever hold what someone manually put there; FD-05 is the supply line that keeps populating
those rungs from distilled frontier deltas. The relationship is producer→consumer, and the boundary is
sharp: FD-05 never intercepts a request, never re-implements the escalation logic, and never overrides
a CO-03 decision at runtime. It changes the *table* CO-03 reads, then steps back.

**Versus CO-05 (Zero Token Layer / Asset Registry).** CO-05 owns the assets — it stores and serves the
deterministic recipes, templates, and cached blocks. FD-05 does not store anything and does not own the
registry. It emits *candidates*: "here is a deterministic recipe for capability Z, proven by FD-04 —
register it." CO-05 decides how to store and index it; FD-06 executes the write. FD-05's role ends at
proposing the candidate with its proof attached. A CO-05 that grew its own asset-discovery logic would
be duplicating FD-05; an FD-05 that stored its own assets would be duplicating CO-05. The clean split
is that CO-05 answers "what deterministic capabilities do we have?" and FD-05 answers "what
frontier-served capability should *become* a deterministic one, and here is the recipe."

**Versus CO-12 (dependence metric).** CO-12 owns the scorecard — the model-demotion count, the
Opus-avoided count, the cognitive-compression ratio. FD-05 does not compute these and does not stand up
a parallel accounting layer (SCS C41: do not build what already exists). FD-05 *causes* the numbers to
move: every conversion it lands is a demotion CO-12 will register on the next request of that class.
The correct mental model is that CO-12 is the odometer and FD-05 is the engine — FD-05 makes the
distance, CO-12 measures it, and FD-05 must never claim a saving CO-12 has not measured (the
Telemetry-Before-Claims triple). If FD-05 asserts "this conversion saved N frontier calls," it must
carry the CO-12 `(metric, source, value)` triple or it is a hypothesis, not a result.

**Versus FD-01 and FD-04.** FD-01 owns classification — it decides a delta is NEW/STRONGER/DUP/DISCARD
and *estimates* portability. FD-04 owns the portability *proof* — it empirically tests whether the
capability survives on a cheaper substrate against a gold standard. FD-05 consumes both: it acts only
on FD-01's confirmed deltas and only ships a conversion FD-04 has proven. FD-05 does not re-classify,
does not re-estimate portability, and — critically — does not itself run the transfer test. The
temptation to fold FD-04's proof into FD-05 (so the arbitrage station could "just check quickly" that a
conversion works) is exactly the boundary violation that would make both datasets unauditable; the
proof lives in FD-04 so that the same test grades every conversion identically and FD-05 cannot grade
its own optimism.

### I.5 What FD-05 does NOT duplicate (explicit)

FD-05 does **not** route live requests (CO-03 owns the cascade — FD-05 supplies rules), does **not**
store or index assets (CO-05 owns the registry — FD-05 supplies candidates), does **not** compute the
dependence metric (CO-12 owns the scorecard — FD-05 supplies the conversions it measures), does **not**
classify deltas (FD-01), does **not** prove portability (FD-04 owns the empirical transfer test — FD-05
consumes its verdict), and does **not** execute the writeback (FD-06 writes the rule and the asset into
their homes). FD-05 performs exactly one composite operation — *find the highest-value convertible
capabilities, decide their target substrate, emit the conversion artifacts, and gate them on FD-04's
proof* — and emits two typed artifacts (a CO-03 rule candidate and/or a CO-05 asset candidate). If an
edit to FD-05 begins to store assets, run transfer tests, or intercept requests, it has crossed into
CO-05 / FD-04 / CO-03 territory and must be relocated. The station's value is its position in the
pipeline, not its breadth: it is the pivot where a proven-portable delta becomes a routing change, and
nothing more.

### I.6 Core principles

- **Arbitrage the gap, do not merely observe it.** FD-05 is defined by *action*: a capability sitting
  at rung 5 with a feasible path to rung 1 and no emitted conversion artifact is an unrealized saving,
  which is a defect, not a neutral state. The station's health is measured by realized conversions, not
  by radar coverage.
- **Prioritize by expected saving, always.** Frequency × per-call cost × feasibility is the ranking
  function. An intellectually elegant reduction of a once-a-month capability loses to a mundane
  reduction of an hourly one. This is the direct operationalization of PR-FABLE-DELTA-ONLY-001 on the
  cost axis.
- **Irreducibly-frontier is a valid, honest outcome.** Some capabilities — taste, novel synthesis,
  adversarial critique — cannot be demoted without failing the gold standard. FD-05 must record these
  as `IRREDUCIBLE: <reason>` and *stop*, never force a conversion that FD-04 will fail. A forced
  conversion that degrades output is worse than an honest non-conversion, because it hides a quality
  regression behind a dependence-metric improvement.
- **No conversion ships without FD-04 proof.** The routing rule is a candidate until FD-04's transfer
  test confirms the cheaper substrate meets the gold standard. Shipping unproven is the silent-
  regression failure (III.1).
- **No saving is claimed without CO-12's triple.** Every dependence-reduction claim carries
  `(metric, source, value)` or it is labelled a hypothesis (CO-12 Telemetry-Before-Claims).
- **The station's own cost must be a fraction of the saving it realizes.** An arbitrage engine that
  costs more to run than the frontier calls it eliminates is a net loss — the CWOPS guardrail-economics
  principle applied to the arbitrageur itself (II.6).
- **Convert once, save forever.** A landed conversion is permanent advantage: it lowers the cost of
  *every* future request of that class, so its value is the integral of the saving over the class's
  future frequency — which is why frequency dominates the ranking and why the loop, not the single
  conversion, is the moat (CWOPS).

### I.7 Why arbitrage, not the answer, is where the dependence curve bends

The deepest justification for FD-05 being a distinct station — rather than a heuristic bolted onto
CO-03 — is the same argument the whole suite inherits from CWOPS: the durable advantage is the closed
loop, not the artifact. A frontier answer is commoditized; anyone with the API key gets the same
answer. What is *not* commoditized is the accumulated set of lower-rung recipes a stack has distilled
from its own history of frontier answers, because that set is a function of *this stack's* delta
history, which no competitor can replicate over a weekend. FD-05 is the station that converts the
commoditized artifact into that non-commoditized asset base. Two teams receiving the identical stream
of Fable answers diverge precisely here: the one running FD-05 against its rising floor keeps demoting
recurring capabilities to zero-cost rungs, so its *marginal* cost per capability falls monotonically
over time; the one that re-asks the frontier for every request pays the full price forever. The gap
between those two cost curves *is* the moat, and it widens with every conversion FD-05 lands.

This reframes what "dependence reduction" means and why it cannot be reduced to routing. Routing (CO-03)
allocates a fixed menu of capabilities across a cost ladder; it makes the *current* menu cheaper to
serve but cannot enlarge the cheap end of the menu. Arbitrage (FD-05) enlarges the cheap end — it takes
capabilities that today exist *only* at rung 5 and manufactures rung-1 or rung-2 versions of them, so
the router's cheap rungs grow richer session over session. The dependence curve — CO-12's model-
demotion and Opus-avoided count — bends only when the cheap end of the menu grows, and only FD-05 grows
it. A stack with a perfect router and no arbitrage station has a flat dependence curve at whatever level
its manually-authored assets happen to reach; a stack with FD-05 has a curve that bends downward as
long as the frontier keeps demonstrating capabilities the stack can distill and demote. This is the
concrete, mechanical sense in which FD-05 is "the station that most directly bends the dependence
curve": it is the only station whose output changes the *shape* of the curve rather than the *position*
of a single request on it.

A crucial and counterintuitive consequence is that FD-05's success is self-limiting per capability
class, and this is a feature rather than a decay — the same inversion FD-01 exhibits. Once a class has
been demoted to rung 1 and the conversion is proven and live, FD-05 has *nothing more to do* for that
class; its arbitrage opportunity is spent, and the class disappears from the Gap Radar's ranked list.
An FD-05 whose worklist never shrinks is attached either to a frontier model that keeps producing
genuinely novel irreducible capabilities (a healthy, exciting state) or to a stack whose conversions
are not actually landing (deposits proposed but never proven, or proven but never routed — a failure
the CO-12 flat-curve cross-check exposes). The correct reading of a shrinking high-value worklist is
that the stack has already harvested its steepest arbitrage gaps and is now working progressively
shallower ones — exactly the diminishing-returns signature of a dependence curve approaching its
irreducible floor, where what remains is genuinely frontier work (taste, novelty, adversarial critique)
that *should* stay at rung 5. FD-05 therefore measures its own success by how much of the stack's
capability surface it has *permanently removed from the frontier's bill*, not by how busy it is, and a
mature FD-05 attached to a mature stack is mostly idle on old classes and active only on the frontier's
newest demonstrations — which is precisely the terminal state the suite is designed to approach:
*spend frontier tokens only on the genuinely irreducible delta, and convert everything else to zero.*
The honesty constraint is what keeps this from becoming a lie: if FD-05 force-converted the irreducible
tail to keep its numbers up, it would report a bent curve while silently degrading the stack's hardest
outputs, and a distillation suite that lies about its own advantage cannot bend the dependence curve
because it can no longer tell whether the curve is bending or the quality is rotting underneath it.

---

## Part II — The Conversion Contract, the Arbitrage Procedure, Interfaces, and ROI Rules

### II.1 Operating contract (inputs and outputs)

FD-05's **inputs** are four typed streams plus one economic table. The streams: FD-01's classified
deltas (each carrying a `delta_class`, a `capability_summary`, and a cheap `portability_estimate`);
FD-04's portability *verdicts* (empirical proof that a specific capability does or does not survive on a
named cheaper substrate against a gold standard); CO-12's admission log (the record of which classes
were actually escalated to the frontier and how often — the *frequency* operand); and CO-05's current
asset inventory (what deterministic capabilities already exist, so FD-05 does not propose a recipe the
registry already holds). The economic table: CO-03's per-rung cost model (the *k* operand — what a
frontier call costs versus a Haiku call versus a deterministic compute), so the ranking function has
real numbers rather than guesses.

FD-05's **outputs** are exactly two typed artifacts, each optional per capability but at least one
required for any capability it decides to convert. The first is a **CO-03 routing-rule candidate**:
`{capability_class, current_rung, target_rung, condition, asset_ref?, fd04_proof_ref,
expected_saving_triple, status ∈ {proposed, proven, live, rejected}}` — the instruction that will tell
the router to send this class to the cheaper rung once `status = proven` clears to `live`. The second
is a **CO-05 asset candidate**: `{capability_summary, target_substrate, recipe_or_template_or_cache_key,
fd04_proof_ref, provenance}` — the deterministic recipe, template, or cache entry that CO-05 will store
and CO-03's rule will point at. A capability classified `IRREDUCIBLE` produces *neither* artifact and
instead a single honest record `{capability_class, verdict: IRREDUCIBLE, reason, evidence_ref}` so the
Gap Radar does not re-surface it every scan and the honesty of the non-conversion is auditable.

The contract's hard postcondition: **every capability FD-05 examines yields exactly one disposition** —
a proposed conversion (with at least one artifact), a landed conversion (artifacts at `live`), or an
`IRREDUCIBLE` record — so the station can never be in the state "we looked at this class and have no
verdict on whether it can be made cheaper." Two fields carry the most weight. `fd04_proof_ref` is the
mandatory link to the FD-04 transfer test that gates the conversion; a routing-rule candidate whose
`status` is `proven` or `live` but whose `fd04_proof_ref` is null is malformed and rejected — this is
the structural enforcement of the "no conversion without proof" principle. `expected_saving_triple` is
the CO-12 `(metric, source, value)` triple; a conversion may be *proposed* with an *estimated* triple,
but it may only be *claimed as a realized saving* once CO-12 has measured the actual demotion, at which
point the estimated triple is overwritten with the measured one.

### II.2 The arbitrage procedure (the four movements)

The station runs in four movements, each with a defined output, so a conversion decision is traceable
rather than a single opaque judgment — the same design discipline FD-01 applies to its four-step
comparison.

**Movement 1 — Gap Radar (find the opportunities).** Scan FD-01's class distribution, FD-04's decay
verdicts, and CO-12's admission log to build the ranked list of arbitrage opportunities. The radar's
output is a table of capability classes, each scored by *frequency* (how often CO-12 shows the class
escalated to the frontier), *per-call cost* (from CO-03's cost model), and a first-pass *feasibility*
(from FD-01's `portability_estimate` and any existing FD-04 signal). The product of the three is the
expected saving, and the radar emits the classes in descending order of that product. The radar's whole
job is to answer "where is the stack still over-dependent, and where would fixing it save the most?" —
which is the Capability-Gap-Radar candidate absorbed as this movement rather than a separate system.

**Movement 2 — Conversion classification (decide the target substrate).** For each high-ranked class,
decide the *target rung* on the I.3 ladder: the cheapest substrate that could plausibly serve the
capability sufficiently. This is a proposal, not a proof — it says "this looks like a deterministic
recipe" or "this looks like a template with three slots" or "this looks irreducibly frontier." The
output is a target-rung assignment with a stated reason, which becomes the hypothesis FD-04 will test.
A class assigned `IRREDUCIBLE` here exits the pipeline with an honest record and does not proceed to
Movement 3 — FD-05 does not spend distillation effort trying to prove the unprovable.

**Movement 3 — Emit conversion artifacts (build the candidate).** For each class with a feasible target
rung, construct the two artifacts: the CO-03 routing-rule candidate (route this class to the target
rung under this condition) and, where the target rung is 0–2, the CO-05 asset candidate (the actual
deterministic recipe, template, or cache key that realizes the capability). This is the Frontier-to-
Deterministic-Conversion candidate absorbed as a movement: the concrete manufacture of the cheap-rung
version of a frontier capability. The artifacts are emitted at `status = proposed` with the target
substrate named and the recipe attached, ready for FD-04.

**Movement 4 — Prove and promote (gate on FD-04).** Hand the proposed conversion to FD-04, which runs
its empirical transfer test: does the cheap-substrate version meet the gold standard for this
capability? On PASS, the artifact's `status` advances to `proven` and then, once FD-06 has written the
rule into CO-03 and the asset into CO-05, to `live`; CO-12 then measures the realized demotion and the
`expected_saving_triple` is overwritten with the measured value. On FAIL, the artifact's `status`
becomes `rejected` with the failure reason recorded, the class is re-examined (perhaps a higher rung is
the right target — a class that fails at rung 1 might pass at rung 3), and if no rung passes the class
is reclassified `IRREDUCIBLE`. This is the Cognitive-Arbitrage-Router candidate absorbed: the routing
change is the *output* of a proven arbitrage, not a speculative re-route.

The procedure is explicit because the failure modes cluster at specific movements. A weak Movement 1
(a Gap Radar that ranks by intellectual interest rather than frequency × cost) misdirects the whole
station's effort onto low-value conversions. An over-optimistic Movement 2 (assigning rung 1 to a
capability that needs rung 4) generates conversions that FD-04 will reject, wasting proof budget. A
skipped Movement 4 (shipping a conversion without the transfer proof) is the silent-regression failure.
Making each movement a named, inspectable output means an audit can localize a bad conversion — or a
missed one — to the movement that caused it.

### II.3 Interfaces with existing PP systems

- **CO-03 (router)** — FD-05 *writes* routing-rule candidates that CO-03 will apply once live, and
  *reads* CO-03's per-rung cost model for the ranking function. It never intercepts a live request.
- **CO-05 (asset registry)** — FD-05 *writes* asset candidates (recipes/templates/cache keys) and
  *reads* the current inventory to avoid proposing a duplicate. It never stores or indexes; FD-06 does.
- **CO-12 (dependence metric)** — FD-05 *reads* the admission log for frequency and *causes* the
  demotion/Opus-avoided count to move; it *reads back* the measured triple to overwrite estimates. It
  never computes the metric.
- **FD-01 (classification)** — supplies the deltas, the `capability_summary`, and the portability
  *estimate* that seeds Movement 2.
- **FD-04 (portability proof)** — the mandatory gate at Movement 4; FD-05 hands it a proposed
  conversion and consumes its PASS/FAIL verdict. FD-05 never runs the transfer test itself.
- **FD-06 (writeback)** — executes the actual write of the proven rule into CO-03 and the proven asset
  into CO-05; FD-05 hands FD-06 the artifact, FD-06 places it.
- **PM-03 (findings bus)** — FD-05 publishes a landed conversion so concurrent panes learn that a class
  is now served cheaply and do not independently re-attempt the same arbitrage.

### II.4 Decision rights and non-decision rights

FD-05 **may decide**: which capability classes are arbitrage opportunities and in what ranked order
(Movement 1); the *proposed* target substrate for each (Movement 2); the *form* of the conversion
artifacts (Movement 3); and whether, given FD-04's verdict, to promote, retry at a higher rung, or
reclassify as `IRREDUCIBLE` (Movement 4). FD-05 **may not decide**: whether the cheaper substrate
actually meets the gold standard (FD-04's proof is binding — FD-05 cannot override a FAIL by asserting
the conversion is "close enough"); how CO-03 internally represents or orders the routing rule (CO-03
owns its table); how CO-05 stores and indexes the asset (CO-05 owns the registry); the value of the
dependence metric (CO-12 measures it); or the actual write of the artifacts into their homes (FD-06
executes). The subtle boundary is with FD-04: FD-05 *proposes* the target substrate and *decides
whether to retry at a different rung after a FAIL*, but it may never *declare a conversion proven* — only
FD-04 promotes a `proposed` artifact to `proven`. FD-05's optimism is a hypothesis; FD-04's test is the
verdict; the artifact's `status` field is the audit trail of which one is currently in force.

### II.5 The conversion feasibility rubric (target-rung entry criteria)

Each target rung has entry criteria so the Movement-2 assignment is defensible rather than intuitive,
and the burden is asymmetric: proposing a *lower* (cheaper) rung carries a *higher* evidentiary burden,
because an over-optimistic demotion is the failure that produces silent regressions.

| Target rung | Entry criteria (all must hold to propose) | Evidentiary burden |
|---|---|---|
| **0 Cached** | (a) inputs recur identically; (b) the answer is stable across time; (c) a cache-invalidation condition is stated | High — must show the answer will not drift, or the cache serves stale results |
| **1 Deterministic** | (a) the capability is a pure transform with no judgment; (b) inputs/outputs are fully specified; (c) a reference implementation shape exists | Highest — must show *no* judgment is involved; a hidden judgment silently degrades |
| **2 Template** | (a) a fixed structure with a small bounded slot-set; (b) the model fills the slots the same way every time; (c) the slot-fill rule is stateable | High — must show the slot-fill is genuinely fixed, not context-dependent |
| **3 Small-model** | (a) bounded reasoning in a narrow domain; (b) tolerant of a cheap-model ceiling; (c) FD-04 gold standard is achievable at Haiku | Medium — must name the domain bound |
| **4 Mid-model** | (a) structured but real reasoning; (b) below frontier taste/novelty; (c) gold standard achievable at Sonnet | Medium — must show why frontier is *not* needed |
| **5 Frontier / IRREDUCIBLE** | (a) taste, novel synthesis, or adversarial critique is genuinely required; (b) FD-04 has failed all lower rungs OR the shape is unmistakably irreducible | The honest default — must record the reason, never a lazy fallback to avoid work |

The asymmetry directly implements the honesty constraint: the cheapest rungs demand the most proof
because they are where a forced conversion does the most silent damage, and `IRREDUCIBLE` is an
honorable verdict that must nonetheless carry its reason so an audit can catch a capability lazily
parked at rung 5 that a little distillation effort could have demoted.

### II.6 Token-ROI rules (the arbitrageur must not cost more than it saves)

FD-05 is itself a cost — the Gap Radar scan, the Movement-2 classification, the artifact construction,
and the FD-04 proof all spend tokens and Owner attention — and the doctrine forbids an arbitrage engine
whose operating cost exceeds the savings it realizes. Three rules bound this. First, **the radar runs
cheap and incremental**: it scans CO-12's admission log and FD-01's distribution (both already on disk,
per the Token Austerity Protocol) rather than re-deriving frequencies, and it re-ranks only when new
deltas or new admission data arrive, not on every session. Second, **conversion effort is spent in
strict expected-saving order**: the highest frequency × cost × feasibility class is converted first,
and the station stops when the *next* candidate's expected saving falls below the cost of converting it
— the point at which further arbitrage is a net loss. Third, **the FD-04 proof is spent only where it
changes a decision**: a class with an obvious deterministic shape and a clear gold standard can be
proven cheaply, while an ambiguous one warrants a fuller transfer test — but a low-frequency ambiguous
class is better left at its current rung than proven expensively, because the saving would not repay the
proof. These rules keep FD-05 from becoming the CWOPS anti-pattern of a guardrail (here, an
optimizer) that costs more than the loss it prevents — an arbitrageur that spends a dollar of frontier
tokens to save fifty cents of frontier tokens has inverted its own purpose.

### II.7 Portability consumption rules (FD-05 reads FD-04, never re-proves)

FD-05 consumes FD-04's portability verdict as a binding input and never re-derives it. The division is
precise: FD-01 *estimates* portability from capability shape (a cheap prior); FD-04 *proves* it
empirically against a gold standard (the posterior); FD-05 *acts* on the proof (the arbitrage). FD-05's
Movement-2 target-rung proposal is seeded by FD-01's estimate but is a *proposal to FD-04*, not a
claim. When FD-04 returns PASS for a target rung, FD-05 promotes; when FD-04 returns FAIL, FD-05 does
*not* argue with the test — it retries at a higher rung or reclassifies `IRREDUCIBLE`. The one signal
FD-05 does feed back is the estimate-versus-outcome join: if FD-01's `portability_estimate`
systematically over-promises (estimates rung 1 for capabilities FD-04 proves need rung 4), FD-05
surfaces this to recalibrate FD-01's shape heuristic — but FD-05 recalibrates *FD-01's estimator*, not
FD-04's test, because the test is the ground truth and the estimate is the thing being graded against
it. This is the same outcome-not-proxy discipline CWOPS prescribes: the decisive signal is FD-04's
empirical transfer result, weighted above FD-01's cheap guess whenever the two disagree.

### II.8 No-bloat and no-duplicate rules

FD-05 enforces no-bloat at the point of proposal: before emitting a CO-05 asset candidate, it checks the
current CO-05 inventory and refuses to propose a recipe the registry already holds — a duplicate asset
is deposit-precision damage of exactly the kind FD-01 guards against on the delta side. Before emitting
a CO-03 routing-rule candidate, it checks that no existing rule already routes the class to an equal or
cheaper rung — proposing a rung-3 route for a class already served at rung 1 is a regression dressed as
an optimization. The station also refuses to *re-open* a class already recorded `IRREDUCIBLE` unless new
FD-01/FD-04 evidence has arrived (a newer frontier answer or a newer gold standard), so the Gap Radar
does not thrash on capabilities already honestly judged unconvertible. And it refuses to build a *second*
arbitrage layer: FD-05 has no cost model of its own (it reads CO-03's), no frequency counter of its own
(it reads CO-12's), and no asset store of its own (it proposes to CO-05's) — the "one system, no
parallel systems" discipline the suite inherits from GK-00, applied to the cost axis. The net effect is
that FD-05 adds exactly one thing to the stack that did not exist before — a ranked, proof-gated
pipeline that turns proven-portable deltas into routing changes — and reuses every substrate it touches.

### II.9 A fully worked conversion: the same capability against two economic contexts

The clearest way to specify the conversion contract is to run one capability through the four movements
in two different economic contexts and show that the *same capability* yields two *different arbitrage
decisions* — the property that makes the prioritization economic rather than technical. Consider the
capability: "normalize a messy changelog entry into the project's canonical commit-message format
(subject ≤ 50 chars, imperative mood, scoped prefix, body wrapped at 72)." FD-01 has classified the
underlying delta and FD-04 stands ready to prove any proposed conversion.

**Context A (a high-frequency repo).** Movement 1: CO-12's admission log shows this capability escalated
to the frontier ~400 times in the last month (every commit in a busy multi-pane repo passes through it),
at a frontier per-call cost of *k*. The Gap Radar scores it near the top of the ranked list — 400 × *k*
× (high feasibility, since formatting is a classic deterministic shape). Movement 2: the target rung is
proposed as **2 (template)** — the capability is a fixed structure (subject/scope/body) with a small
bounded slot-set, and the slot-fill (imperative mood, wrap width) is stateable as a rule. Movement 3:
FD-05 emits a CO-05 template-asset candidate (the canonical format with its slot rules) and a CO-03
routing-rule candidate (route commit-message-normalization to the template rung). Movement 4: FD-04
runs the transfer test — does the template output meet the gold standard (a hand-labelled set of
correctly-formatted messages)? It passes for the mechanical parts (wrapping, prefix) but the *imperative
mood* rewrite occasionally needs a small model to rephrase "fixed the bug" → "fix the bug" reliably, so
FD-04 returns PASS-at-rung-3, not rung-2. FD-05 accepts the verdict, revises the target to **3
(small-model)** with a rung-2 template pre-pass for the mechanical parts, re-proves (PASS), and promotes.
CO-12 later measures the realized demotion: ~400 frontier calls per month become ~400 Haiku calls plus
a deterministic pre-pass, and the `expected_saving_triple` is overwritten with the measured Opus-avoided
count. The saving is large *because the frequency was large* — this is the class arbitrage exists for.

**Context B (a low-frequency repo).** The identical capability, but CO-12 shows it escalated only ~4
times last month (a quiet solo repo). The Gap Radar scores it near the *bottom* — 4 × *k* × feasibility
is a small number. Movement 2 would propose the same target rung, but the II.6 token-ROI rule bites:
the cost of building the template + small-model recipe and running the FD-04 proof exceeds the expected
saving of eliminating four frontier calls a month. FD-05 records the class as a *deferred* opportunity —
feasible but not yet worth the conversion cost — and leaves it at its current rung, revisiting only if
the frequency rises. No artifacts are emitted; the honest disposition is "convertible but below the ROI
threshold at current frequency."

The two runs are the entire argument for FD-05's ranking function. The capability is identical and
equally *feasible* to convert in both contexts; what differs is the *frequency*, and frequency is the
operand that decides whether the arbitrage is worth executing. An FD-05 that converted by feasibility
alone would spend equal effort on both and realize a large saving in A and a negligible one in B for the
same cost — a misallocation the frequency-weighted ranking prevents. The worked example also shows why
Movement 4's proof is load-bearing and non-skippable: FD-05's Movement-2 optimism (rung 2) was *wrong*,
and only FD-04's empirical test caught that the imperative-mood rewrite needed a small model; had FD-05
shipped its rung-2 proposal unproven, every commit message in the high-frequency repo would have carried
subtly wrong mood — a silent quality regression that the dependence metric would have cheerfully recorded
as a 400-call saving. The proof gate is what converts an optimistic hypothesis into a safe, measured
demotion, and the retry-at-a-higher-rung behavior is what turns a FAIL into a *smaller-but-real*
conversion rather than an abandonment.

---

## Part III — Failure Modes, Gates, Benchmarks, Traces, and Evolution

### III.1 Failure modes with diagnosis protocol

| Failure mode | Symptom | Diagnosis | Root cause |
|---|---|---|---|
| **Silent regression** | dependence metric improves but output quality on the converted class drops | sample the converted class's live outputs, compare to the FD-04 gold standard | a conversion shipped at `status=live` whose `fd04_proof_ref` was null or stale — Movement 4 skipped or the gold standard drifted |
| **Vanity conversion** | station is busy, many artifacts emitted, dependence metric barely moves | join emitted conversions to CO-12's *measured* saving; find high artifact count, low realized saving | Gap Radar ranked by feasibility/interest, not frequency × cost — low-value classes converted first |
| **Forced-frontier-demotion** | FD-04 FAIL rate on FD-05 proposals is high; many `rejected` artifacts | inspect Movement-2 target-rung assignments against FD-04 outcomes | over-optimistic feasibility judgment — capabilities needing taste/novelty proposed at deterministic rungs |
| **Phantom saving claim** | a "saved N calls" claim with no CO-12 triple, or an estimated triple never overwritten with a measured one | check every realized-saving claim for a *measured* `(metric, source, value)` triple | Telemetry-Before-Claims violated — estimate reported as result |
| **Stale-cache rot** | a rung-0 cached capability serves outdated answers | check the cache-invalidation condition against how often the underlying answer actually changes | a rung-0 conversion whose stability assumption (II.5) was wrong; the answer drifts, the cache does not |
| **Radar thrash** | the same `IRREDUCIBLE` classes reappear on the ranked list every scan | check whether reappearing classes have *new* FD-01/FD-04 evidence | II.8 no-re-open rule not honored — the radar re-surfaces settled classes without new evidence |
| **Duplicate asset** | CO-05 accumulates near-identical recipes for one capability | diff proposed asset candidates against the CO-05 inventory | Movement 3 skipped the inventory check — a recipe proposed that CO-05 already held |

The station's characteristic failure is the **silent regression**, because it is the one that *looks
like success*: the dependence metric goes down (frontier calls eliminated) while the actual output on
the converted class quietly degrades, and nothing surfaces the degradation unless someone compares live
output to the gold standard. This is the cost-axis analogue of FD-01's NEW-inflation and of CWOPS §4.6's
degenerate-feedback trap — optimizing the *proxy* (frontier calls avoided) instead of the *outcome*
(capability served at gold-standard quality). The structural guard is the mandatory `fd04_proof_ref`
and the rule that no artifact reaches `live` without a passing, *fresh* proof; the diagnostic guard is
the periodic re-comparison of converted-class live output against the gold standard, which catches a
regression that a drifting gold standard let slip. The second-most-dangerous failure is the **vanity
conversion**, because it consumes the station's finite budget on low-value work while the dependence
curve stays flat — the join of artifact count to CO-12's *measured* saving is the cross-check that
exposes it, exactly as FD-01's NEW-rate-to-flat-metric join exposes its inflation.

### III.2 Anti-patterns with evidence

- **The eager converter.** Demoting a capability because a cheaper rung *exists*, not because FD-04
  proved the rung is *sufficient*. Evidence: the silent-regression failure and CO-12's outcome-not-proxy
  honesty rule — a cheaper rung that produces worse answers is a loss disguised as a saving. Forbidden by
  the mandatory FD-04 proof gate at Movement 4.
- **The feasibility-ranked radar.** Ordering the arbitrage worklist by how *reducible* a capability is
  rather than by frequency × cost. Evidence: the vanity-conversion failure and PR-FABLE-DELTA-ONLY-001 —
  the delta-only discipline is about spend, and spend is dominated by high-frequency classes. Forbidden
  by the II.2 Movement-1 ranking function.
- **The heroic reduction.** Spending large distillation effort to demote a genuinely irreducible
  capability (taste, novel synthesis) because admitting `IRREDUCIBLE` feels like defeat. Evidence: the
  honesty constraint — a forced conversion that fails the gold standard is worse than an honest
  non-conversion. Forbidden by the II.5 rung-5 entry criterion and the `IRREDUCIBLE` verdict being a
  first-class, honorable disposition.
- **The uncounted saving.** Claiming a dependence reduction without CO-12's measured triple, or leaving
  an estimated triple in place as if it were measured. Evidence: the CO-12 Telemetry-Before-Claims
  Contract — no advantage is claimed without `(metric, source, value)`. Forbidden by the phantom-saving
  gate (III.3 G4).
- **The parallel accountant.** FD-05 standing up its own frequency counter, cost model, or asset store
  instead of reading CO-12 / CO-03 / CO-05. Evidence: SCS C41 (do not build what exists) and GK-00 (one
  system, no parallels). Forbidden by II.8.
- **The busy arbitrageur.** Measuring FD-05's health by how many conversions it emits rather than how
  much of the capability surface it has permanently removed from the frontier's bill. Evidence: I.7 —
  a healthy mature FD-05 is mostly *idle* on old classes; a never-shrinking worklist is a symptom, not
  a virtue.

### III.3 Quality gates (binary)

- **G1 — Every conversion is proof-gated.** Does every artifact at `status ∈ {proven, live}` carry a
  non-null, fresh `fd04_proof_ref` pointing at a passing FD-04 transfer test? Binary.
- **G2 — Every disposition is complete.** Does every capability FD-05 examined carry exactly one
  disposition (proposed / live / IRREDUCIBLE), never an un-verdicted class? Binary (the closed-
  disposition postcondition).
- **G3 — Ranking is frequency-weighted.** Was the Gap Radar's order produced by frequency × per-call
  cost × feasibility, with the frequency operand sourced from CO-12's admission log? Binary.
- **G4 — Every realized-saving claim carries a measured triple.** Does every claim of a landed saving
  carry a CO-12 `(metric, source, value)` triple that is *measured*, not estimated? Binary.
- **G5 — No duplicate / no regressive rule.** Does every emitted CO-05 asset candidate clear the
  inventory-dedup check, and every CO-03 rule candidate route to a rung equal-or-cheaper than the
  existing one? Binary.
- **G6 — IRREDUCIBLE carries a reason.** Does every `IRREDUCIBLE` record carry a stated reason and an
  evidence reference (an FD-04 FAIL or an unmistakable shape), never a bare fallback? Binary.

### III.4 Evaluation rubric (measurable)

| Dimension | Metric | Source | Target |
|---|---|---|---|
| Conversion precision | fraction of shipped conversions that hold at gold standard on live re-audit | converted-class live-vs-gold audit | ≥ 0.95 |
| Saving realization | fraction of proposed savings that CO-12 later *measures* as realized | proposed-triple ↔ CO-12 measured join | ≥ 0.8 |
| Ranking fidelity | correlation between Gap Radar rank and CO-12 realized saving | radar-rank ↔ measured-saving join | strongly positive |
| Proof-gate integrity | fraction of `live` conversions with a fresh passing FD-04 proof | artifact audit | 1.0 (hard) |
| Feasibility calibration | fraction of Movement-2 target rungs FD-04 confirms without retry | Movement-2 ↔ FD-04 join | rising |
| Honest non-conversion | fraction of `IRREDUCIBLE` records with a valid reason + evidence | disposition audit | 1.0 (hard) |

### III.5 Benchmarks with reference values

The station's benchmarks anchor to the suite's economics and to CWOPS's cost figures. **Conversion
precision floor:** ≥ 0.95 of shipped conversions must hold at gold standard on live re-audit — below
this, the silent-regression failure is eroding output quality faster than the dependence metric admits,
and the "saving" is partly a quality loss in disguise. **Saving-realization floor:** ≥ 0.8 of proposed
savings must be *measured* as realized by CO-12 — a large gap between proposed and measured savings means
the estimates are optimistic and the ranking function is being fed inflated feasibility. **Steepness
target:** the station should prioritize conversions on the steepest feasible cost drops, and the CWOPS
~1000× bounded-vs-unbounded swing is the reference for a rung-5→rung-1 conversion — a single such
conversion on a high-frequency class dwarfs dozens of rung-4→rung-3 demotions, which is why the ranking
multiplies frequency by *per-call cost* rather than frequency alone. **Station-cost ceiling:** FD-05's
own operating cost (radar + classification + proof) must be a small fraction of the frontier spend it
eliminates — the CWOPS guardrail-economics principle applied to the arbitrageur; an FD-05 that spends
more than it saves has inverted its purpose and must be throttled to only the top-of-radar conversions.
**Proof-gate integrity:** 1.0, a hard invariant — a single `live` conversion without a fresh passing
proof is a G1 breach, not a benchmark miss.

### III.6 Example operational traces

**Trace A — a clean rung-5→rung-1 conversion.** Gap Radar surfaces "deduplicate a document stream under
a token budget" — escalated ~120×/month at frontier cost, FD-01 estimate `deterministic`, high
feasibility, top of the ranked list. Movement 2 proposes rung **1 (deterministic)** — a pure algorithm.
Movement 3 emits a CO-05 deterministic-recipe candidate (semantic-cluster-scoped SHA-256 with LRU
eviction) and a CO-03 rule (route this class to the deterministic rung). Movement 4: FD-04 proves the
recipe meets the gold standard (identical dedup results as the frontier answer on a held-out set). PASS
→ `proven` → FD-06 writes it → `live`. CO-12 measures ~120 frontier calls/month become deterministic
compute; the measured Opus-avoided triple overwrites the estimate. Published to PM-03. This is the
CWOPS ~1000× swing realized on a high-frequency class — the station's canonical win.

**Trace B — a retry-at-a-higher-rung.** Gap Radar surfaces "classify a crash log into one of nine
categories" — ~300×/month, FD-01 estimate `deterministic` (looks like keyword matching). Movement 2
proposes rung **1**. Movement 4: FD-04 FAILs — the categories overlap and edge cases need judgment a
keyword rule cannot make; deterministic precision is 0.72 against a 0.9 gold standard. FD-05 does not
ship; it retries at rung **3 (small-model)**, re-proves (Haiku hits 0.93), PASS → `live`. The saving is
smaller than a deterministic conversion but real — ~300 frontier calls become Haiku calls. The FAIL was
not a loss; it corrected an over-optimistic Movement-2 estimate before any regression shipped.

**Trace C — an honest IRREDUCIBLE.** Gap Radar surfaces "judge whether a landing-page hero *feels*
premium or generic" — ~30×/month at frontier cost. Movement 2 inspects the shape: this is taste, a
frontier capability with no deterministic or template form. FD-04 has already failed a mid-model attempt
against the CDIO gold standard. FD-05 records `IRREDUCIBLE: taste judgment, FD-04 FAIL at mid-model, no
lower-rung form` and emits no artifacts. The class leaves the radar and does not reappear absent new
evidence. This is the honesty constraint in action — the class stays at rung 5 because that is where it
belongs, and forcing it cheaper would degrade every hero judgment.

**Trace D — a deferred-by-ROI opportunity.** Gap Radar surfaces a feasible deterministic conversion for
a capability escalated only ~3×/month. The II.6 token-ROI rule computes that the conversion + proof cost
exceeds three frontier calls of saving. FD-05 records the class as `deferred: feasible, below ROI
threshold at current frequency` and moves on. If CO-12's admission log later shows the frequency rising,
the radar re-surfaces it and the conversion proceeds. No effort wasted on a low-value reduction.

**Trace E — a rung-0 cache with an invalidation condition.** Gap Radar surfaces "emit the project's
canonical CI config block" — escalated ~80×/month, identical output every time. Movement 2 proposes rung
**0 (cached)** with an explicit invalidation condition: invalidate when the CI toolchain version in the
project manifest changes. Movement 4: FD-04 confirms the cached block matches the gold standard and the
invalidation condition covers the only drift source. PASS → `live`. ~80 frontier calls/month become a
lookup. The invalidation condition is what prevents the stale-cache-rot failure — a cache without one
would serve an outdated block after the next toolchain bump.

### III.7 Edge cases

- **A capability convertible at multiple rungs.** If a class passes FD-04 at both rung 1 and rung 3,
  FD-05 ships the *cheapest passing* rung (rung 1) — the steepest feasible drop wins, per the ranking's
  cost weighting.
- **A conversion that helps frequency but hurts a rare hard case.** The capability is served cheaply for
  the common case and *escalated* to the frontier for the rare hard case via a CO-03 conditional rule —
  a partial conversion (most of the frequency demoted, the hard tail left at rung 5) rather than an
  all-or-nothing decision. The saving is the demoted fraction × frequency.
- **A gold standard that itself drifts.** If FD-04's gold standard for a converted class changes (the
  Owner raises the quality bar), the conversion's proof goes *stale* and the artifact is demoted from
  `live` back to `proposed` pending re-proof — a live conversion is only as valid as its most recent
  passing proof (the freshness half of G1).
- **A frontier model that regresses.** If the frontier model gets *worse* at a class (a model update),
  the gold standard may now be *met* by a cheaper rung that previously failed — a re-opened arbitrage
  opportunity the radar surfaces when new FD-04 evidence arrives.
- **An empty admission log (new class).** A capability with no CO-12 frequency data cannot be ranked;
  FD-05 holds it as `unranked-pending-frequency` rather than converting speculatively, because a
  conversion whose saving cannot be estimated cannot be prioritized against real ones.
- **A conversion whose asset already exists but whose rule does not.** CO-05 holds the recipe but CO-03
  never routed the class to it (an orphan asset). FD-05 emits *only* the CO-03 rule candidate (no CO-05
  duplicate), wiring an existing asset into the router — a pure routing arbitrage with no new asset.

### III.8 Writeback rules

FD-05 does not write to CO-03 or CO-05 directly; it emits typed artifacts and hands them to FD-06, which
places the rule in CO-03's table and the asset in CO-05's registry. The artifacts' mandatory fields must
all be present before FD-06 accepts them — a routing-rule candidate missing `target_rung`,
`fd04_proof_ref` (when `status ≥ proven`), or `capability_class` is malformed and rejected, which
prevents an unproven or unattributed conversion from reaching the router. A landed conversion is
published to PM-03 so concurrent panes learn the class is now served cheaply and do not re-attempt the
same arbitrage. `IRREDUCIBLE` and `deferred` records are emitted for the audit trail (so the honesty of
non-conversions and the ROI of deferrals can be reviewed) but carry an explicit "do-not-route" flag that
FD-06 honors — they change nothing in CO-03 or CO-05, they only record why no change was made. The
`expected_saving_triple` on a `live` artifact must be the *measured* CO-12 triple, not the estimate; the
overwrite from estimate to measured is the final step of Movement 4 and its absence is a G4 breach.

### III.9 Conceptual regression tests

- **R1 — Proof gate holds.** Propose a conversion, withhold the FD-04 proof; assert the artifact cannot
  reach `live` (stays `proposed`).
- **R2 — Frequency-weighted ranking.** Feed two feasible conversions, one high-frequency and one
  low-frequency; assert the high-frequency one is ranked and converted first.
- **R3 — Retry on FAIL.** Feed a capability FD-04 fails at rung 1 but passes at rung 3; assert FD-05
  retries and ships the rung-3 conversion, not an abandonment and not a forced rung-1 ship.
- **R4 — IRREDUCIBLE is honored.** Feed a taste capability FD-04 fails at all lower rungs; assert an
  `IRREDUCIBLE` record with a reason and no emitted artifacts, and assert it does not re-surface without
  new evidence.
- **R5 — No phantom saving.** Feed a landed conversion with no CO-12 measured triple; assert the
  realized-saving claim is rejected (G4) until the triple is measured.
- **R6 — No duplicate asset.** Feed a conversion whose recipe CO-05 already holds; assert only a routing
  rule is emitted, no duplicate asset (III.7 orphan-asset case, and the II.8 dedup rule).
- **R7 — ROI defer.** Feed a feasible conversion below the ROI threshold; assert a `deferred` record and
  no artifacts.

Per SCS C41, these are gate assertions for the EXECUTION-mode harness, not auto-generated unit tests;
the conversion-precision and saving-realization metrics are measured against real converted-class
live-vs-gold audits and CO-12's measured savings, which is the honest observation the anti-test-theater
rule requires.

### III.10 Done criteria (verifiable)

FD-05 is done when: the dataset exists on disk, un-truncated, > 2500 real words/Part; the seven-rung
substrate taxonomy is closed and each capability maps to exactly one target rung (or `IRREDUCIBLE`); the
four-movement arbitrage procedure is specified with inspectable per-movement outputs; the conversion-
feasibility rubric has per-rung entry criteria with the cheapest-rung-highest-burden asymmetry; G1–G6
are binary and the proof-gate integrity is a hard 1.0; the station declares CO-03 as the rule consumer,
CO-05 as the asset consumer, CO-12 as the metric owner, FD-01 as the delta source, and FD-04 as the
binding proof gate (no re-implementation of any); `IRREDUCIBLE` is a first-class honorable disposition
with a mandatory reason; every realized-saving claim carries a measured CO-12 triple; and V-FD-NO-CODE
finds zero code fences.

### III.11 Upgrade path

- **v1 (this dataset):** the arbitrage station as a proof-gated proposal layer — Gap Radar ranks,
  Movement 2 proposes target rungs, Movement 3 emits artifacts, Movement 4 gates on FD-04, FD-06 writes.
- **v2 (EXECUTION-mode):** the Gap Radar's frequency and cost operands are wired live to CO-12's
  admission log and CO-03's cost model, so the ranked worklist re-computes automatically as new deltas
  and admissions arrive; the feasibility-calibration metric (Movement-2 ↔ FD-04 join) is computed on each
  material change so an over-optimistic feasibility heuristic is caught early.
- **v3:** the radar is served by the GK route compiler so the arbitrage worklist is *navigated* from the
  knowledge graph (each capability class is a GK node with its frequency, cost, and last-conversion
  edge) rather than re-scanned, making the station cheaper and its "where are we over-dependent" answer
  structural rather than recomputed.
- **v4:** the estimate-versus-outcome join (FD-01 estimate ↔ FD-04 proof) feeds an automatic
  recalibration of FD-01's shape heuristic, closing the loop so that the whole suite's portability
  estimates improve every time a conversion is proven or rejected — the valid·closed·fast flywheel
  applied to feasibility judgment.
- **Deprecation trigger:** if the Gap Radar's high-value worklist durably empties — every high-frequency
  convertible class already demoted and only genuinely irreducible frontier work remaining — FD-05
  fast-paths to a low-frequency maintenance cadence, waking only when the frontier demonstrates a *new*
  convertible capability. The station's own idleness on a mature stack is the visible signature of the
  dependence curve having reached its irreducible floor, which is exactly the terminal state the suite
  is built to approach: spend frontier tokens only on the genuinely irreducible delta, and have
  permanently converted everything else to zero.
