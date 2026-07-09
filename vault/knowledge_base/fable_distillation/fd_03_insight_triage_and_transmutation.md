# FD-03 — Insight Triage & Transmutation (S-TRIAGE ⊕ S-TRANSMUTE)

> The router of the suite. FD-01 classifies a delta; FD-03 decides *where it belongs in the stack* and
> *what form it must take* to belong there. It merges two candidate systems the Reality Scan proved are
> one decision: S-TRIAGE (which destination?) and S-TRANSMUTE (which form?) are the same act, because a
> delta's form is dictated by its destination — a Hard Rule and a benchmark are different shapes of the
> same captured advantage. Parents: the **compound-learnings** decision tree (which already routes
> session *learnings* to SKILL/HOOK/RULE/AGENT destinations) extended to frontier *deltas*, and
> **UKDL** (which stores rules but does not decide what becomes one). Sealed under **SCS C82**.
> Guarantee level (CO-10): **rung-2 routing** — it assigns destination and form; FD-06 executes the
> write.

---

## Part I — Mission, the Destination Problem, and the Transmutation Principle

### I.1 Mission

FD-03 exists to close the gap between a classified delta and a permanent, *usable* piece of
infrastructure. FD-01 hands it a delta with a class (NEW or STRONGER) and a capability summary, but a
capability summary sitting in a session log is not yet advantage — it is a note. Advantage requires the
delta to land in the specific place in the stack where it will be *consulted at the moment it is
needed*, in the *form* that place expects. A concurrency invariant that belongs in a Hard Rule but is
filed as a prose dataset paragraph will never fire when the triggering action occurs; a reusable
protocol that belongs in a CO-05 asset but is written as a UKDL lesson will never be routed to by
CO-03. FD-03's mission is to make that routing decision correctly and to transmute the delta into the
form its destination requires, so that the deposit is not merely stored but *operational*.

The mission is the concrete realization of FD-00's deposit clause. FD-00 guarantees a delta is
deposited; FD-03 guarantees it is deposited *in the right place, in the right shape*. Without FD-03,
the deposit clause degenerates into "write it somewhere," which is exactly the a16z empty-data-moat
failure — accumulation without the closed loop that makes accumulation useful. A delta written to the
wrong destination is worse than not written, because it consumes vault space, dilutes navigation, and
creates the illusion of captured advantage while delivering none. FD-03 is the station that makes the
difference between a vault that compounds and a vault that merely grows.

The second half of the mission is transmutation, and it is why S-TRIAGE and S-TRANSMUTE are one
dataset rather than two. The Reality Scan found that "which destination" and "which form" are not
separable decisions: choosing to route a delta to a Hard Rule *is* choosing to transmute it into a
TRIGGER/STOP/EXCEPTION/ORIGIN contract; choosing a benchmark destination *is* choosing to transmute it
into a metric with a reference value. The form is entailed by the destination, so a system that decided
destination without transmuting would hand FD-06 a half-made deposit, and a system that transmuted
without deciding destination would not know which form to produce. FD-03 does both because they are the
same judgment viewed from two sides.

### I.2 The destination problem (why "store it" is not enough)

A frontier delta can serve the stack in several structurally different ways, and each way has a
different home with a different retrieval trigger. The destination problem is the problem of matching a
delta to the home whose retrieval trigger fires exactly when the delta is needed. Consider a delta that
says "before deploying, verify the backup completed." That capability can live in at least three
places: as prose in a deployment dataset (retrieved when someone reads the dataset — rarely, and not at
deploy time), as a Process Rule in UKDL (retrieved when the deploy checklist is consulted — better), or
as a Hard Rule with a deploy trigger (fires automatically at the moment a deploy command is issued —
best). The *same capability* has radically different value depending on its destination, because value
is a function of whether it is consulted at the decision point, and the destination determines the
retrieval trigger. FD-03's core judgment is selecting the destination whose trigger aligns with the
delta's decision point.

This is why "store it somewhere" is a failure and not a fallback. A delta stored where its trigger
never fires at the relevant moment is a delta that produces zero dependence reduction — the stack still
escalates to the frontier for that capability because the distilled version is never surfaced when
needed. The destination decision is therefore not filing; it is the choice that determines whether the
deposit actually bends the dependence curve or merely occupies disk. The suite's whole promise —
capture the delta, reduce future dependence — is delivered or squandered at this station, because a
correctly-classified, correctly-portable delta routed to a home whose trigger never fires is
indistinguishable, in dependence terms, from a delta that was never captured.

### I.3 The destination taxonomy

FD-03 routes each delta to exactly one primary destination from a closed set, each with a defined
retrieval trigger and a required form:

- **Hard Rule (UKDL §HARD-RULES).** For deltas that must *fire automatically* before a specific
  dangerous or irreversible action. Trigger: a PreToolUse-class event. Form: the TRIGGER/STOP/
  EXCEPTION/ORIGIN contract. Reserved for deltas whose non-application causes a production incident —
  the highest bar, because a Hard Rule interrupts flow.
- **Process Rule (UKDL).** For deltas that should be *consulted* at a decision point but need not
  hard-block. Trigger: consulting the relevant checklist/doctrine. Form: a when-X-do-Y rule with a
  rationale.
- **Trap (UKDL traps).** For deltas that record a *non-obvious failure to avoid re-investigating* — the
  negative knowledge "this path is a dead end." Trigger: encountering the same investigation. Form: a
  symptom→cause→"do not re-investigate" note.
- **CO-05 asset (deterministic/template/cache).** For deltas whose capability is a *reusable, runnable*
  recipe. Trigger: CO-03's router reaching the asset rung. Form: a deterministic recipe or template.
  This is the destination that most directly reduces frontier dependence, because it makes the
  capability model-free.
- **Dataset Part (a knowledge_base dataset).** For deltas that are *architectural knowledge* — a design,
  a protocol, a rationale — too large or too contextual for a rule. Trigger: GK navigation to the
  coordinate. Form: a structured dataset section.
- **Benchmark (a reference value).** For deltas that establish a *measurable standard* — a gold example,
  a performance figure, a quality threshold. Trigger: FD-04 decay-testing or a quality gate. Form: a
  metric with a reference value.
- **Prompt fragment.** For deltas that improve *how the stack asks* — a compiled question pattern, a
  reasoning scaffold. Trigger: FD-02 compilation or a skill's prompt assembly. Form: a compact,
  reusable prompt snippet.
- **DISCARD.** For deltas that, on routing inspection, turn out to have no home whose trigger adds
  value — the routing-side no-bloat catch. Recorded, not stored.

The taxonomy is closed and each destination has a distinct trigger, so no two destinations compete for
the same delta on the same trigger — a property that makes the routing decision a genuine choice rather
than an arbitrary one. When a delta plausibly fits two destinations, the tie-break is trigger
alignment: route to the destination whose trigger fires *earliest relative to the delta's decision
point*, because earlier firing means the distilled capability is surfaced before the stack would
otherwise escalate.

### I.4 The transmutation principle (form follows destination)

Transmutation is the operation of reshaping the delta's capability summary into the form its
destination requires, and the principle governing it is that *form follows destination without
residue*. A delta routed to a Hard Rule must become a complete TRIGGER/STOP/EXCEPTION/ORIGIN contract —
not a prose description of a rule, but the actual four-field structure the Hard Rule mechanism consumes.
A delta routed to a CO-05 asset must become a runnable recipe with declared inputs and outputs — not a
narrative about the recipe. A delta routed to a benchmark must become a metric with a concrete
reference value — not "it should be fast" but "p50 under N ms." The "without residue" clause is the
quality bar: after transmutation, the delta's entire operative capability must be captured in the
destination's form, with nothing important left only in the original prose. If transmutation cannot
capture the capability in the destination's form without losing something load-bearing, the
destination was wrong — the delta belongs somewhere its form can hold it fully.

This principle is what makes transmutation a *decision* rather than a mechanical reformatting. Choosing
the form is choosing what the destination's structure forces you to make explicit: a Hard Rule forces
you to name the exact trigger and the exact stop action; a benchmark forces you to name the metric and
its value; a deterministic asset forces you to name the inputs and outputs precisely enough to run
without a model. The forcing function is the point — transmutation extracts the operational essence of
the delta by demanding it fit a structured form, and a delta that resists all forms is often a sign it
was misclassified (it is not actually a reusable capability, just an observation) and should be
DISCARDed. Transmutation is thus also a second-pass filter on FD-01's classification: a NEW delta that
cannot be transmuted into any operational form was probably not a genuine capability.

### I.5 Difference from existing systems

**Versus compound-learnings.** The compound-learnings skill already routes session *learnings* to
destinations via a decision tree (sequence-then-SKILL, automatic-then-HOOK, when-X-do-Y-then-RULE,
agent-fit-then-AGENT-UPDATE). FD-03 extends this tree in two ways: it adds the destinations specific to
*frontier deltas* (Hard Rule, CO-05 asset, benchmark, dataset Part, prompt fragment — richer than the
skill/hook/rule/agent set), and it adds the transmutation step (the skill materializes an artifact but
does not reshape a captured capability into a destination-specific operational form with the "without
residue" bar). FD-03 is the frontier-delta specialization of the same routing instinct, reusing the
skill's decision-tree pattern and its materialization machinery rather than re-implementing them.

**Versus UKDL.** UKDL is an append-only ledger that *stores* Hard Rules, Process Rules, and Traps and
cross-references lessons. It is a destination, not a decider — it holds the rules FD-03 routes to it,
but it does not judge whether a given delta should *become* a rule. FD-03 supplies exactly the judgment
UKDL lacks: the decision that this delta warrants a Hard Rule (and its transmutation into the
four-field contract) rather than a Process Rule or a dataset Part. FD-03 writes *to* UKDL (via FD-06);
it does not duplicate UKDL's storage.

**Versus FD-06.** FD-06 executes the permanent write. FD-03 decides *what* to write and *where*; FD-06
performs the write to the chosen location and handles the mechanics (append-with-supersede, mirror
sync, graph node creation). The split is planner/executor: FD-03 is the routing planner, FD-06 the
write executor. FD-03 never touches disk; FD-06 never makes a routing decision.

### I.6 What FD-03 does NOT duplicate (explicit)

FD-03 does **not** classify the delta (FD-01 owns NEW/STRONGER/DUP/DISCARD; FD-03 receives a
classified delta), does **not** store anything (UKDL/CO-05/GK are destinations; FD-06 writes), does
**not** test portability (FD-04), does **not** compile questions (FD-02), and does **not** re-implement
the compound-learnings decision tree or its artifact materialization (it extends them). It performs one
compound decision — destination plus form — and emits a routed, transmuted deposit ready for FD-06. If
an edit begins to classify, store, or test, it has left its lane.

### I.7 Core principles

- **Destination determines value.** A delta's advantage is realized only if its home's trigger fires at
  the delta's decision point; routing is the choice that makes a deposit operational or inert.
- **Form follows destination without residue.** Transmutation must capture the whole operative
  capability in the destination's form; a delta that resists all forms was likely misclassified.
- **Triage and transmutation are one decision.** Choosing the destination entails choosing the form;
  they cannot be separated without producing half-made deposits.
- **Prefer the earliest-firing trigger.** On a tie, route to the destination whose trigger surfaces the
  capability soonest relative to its decision point.
- **Routing is auditable against consultation.** A destination whose trigger never fires for a routed
  delta is a mis-route, measured by whether deposits are actually consulted (CO-12 adoption).

### I.8 Why routing is where the suite's advantage is won or lost

It is worth stating plainly, because it is easy to underrate a station that neither extracts nor writes:
FD-03 is where the largest fraction of the suite's total value is decided, and a mis-route here wastes
everything the upstream stations spent. Consider the full cost that flows into a single delta by the
time it reaches FD-03. FD-02 spent compilation effort finding a high-leverage question; FD-00 admitted a
frontier token against its gate; the frontier model produced the answer; FD-01 spent classification
effort extracting and typing the delta. All of that investment is realized only if the delta lands
somewhere its trigger fires at the decision point — and it is FD-03 alone that makes that determination.
A perfect extraction routed to an inert home yields exactly zero dependence reduction, which means the
entire upstream chain — the good question, the admitted token, the careful classification — produced
nothing. This is the precise sense in which routing is the suite's highest-stakes decision per unit of
its own cost: the router is cheap to run but expensive to get wrong, because getting it wrong voids the
much larger investment that precedes it.

The point generalizes into a principle the CWOPS moat literature makes explicit and FD-03 inherits:
*the value of captured knowledge is not in its capture but in its retrieval at the decision point.*
CWOPS observes that a data flywheel stalls into a "log file" precisely when its captured signal does not
close back into changed behavior — when the loop is not, in its terms, *closed*. A distilled delta filed
where its trigger never fires is exactly a log-file entry: captured, stored, and behaviorally inert,
producing the appearance of a moat with none of the substance. FD-03 is the station that closes the loop
by ensuring the delta lands where behavior actually consults it, and this is why its primary metric is
not routing "correctness" in the abstract but *consultation rate* — the measured fraction of routed
deposits whose trigger fires and whose content is used at the moment it matters. A router optimized for
anything else — for filing deltas quickly, for filling every destination, for matching topics neatly —
would be optimizing a proxy while the target (consulted-at-decision-point) went unmet, which is the
degenerate-feedback trap one level up. The router that internalizes this treats every routing decision
as a bet that a specific trigger will fire at a specific decision point, and it grades those bets against
whether the trigger actually fired and was used, because only that outcome distinguishes a route that
bent the dependence curve from one that merely tidied the vault. The discipline this imposes on the
router is the same one FD-00 imposes on the session and FD-01 on the classifier: measure the thing that
matters (consultation, dependence, advantage) and refuse the flattering proxy (deposit count, tidy
filing, apparent novelty), because in every station of the suite the proxy is the easy number to move
and the target is the hard one, and only the discipline of grading against the target keeps the station
honest about whether it is compounding advantage or merely producing the appearance of it. It is this
shared discipline, applied identically at every station, that lets the eight datasets behave as one
system rather than eight independently-optimized ones: each measures the same underlying quantity — the
dependence curve, seen from its own vantage — and each refuses the local proxy that would let it look
productive while the curve stayed flat. FD-03's vantage is retrieval, and its refusal is of tidy filing;
but the discipline is the suite's, not the station's, and that shared refusal of the flattering proxy is
what makes the whole family trustworthy as a single mechanism for turning frontier interactions into
permanent, compounding, model-independent advantage.

---

## Part II — The Routing Contract and the Transmutation Forms

### II.1 Operating contract (inputs and outputs)

FD-03's **input** is a classified delta record from FD-01: `{delta_class, capability_summary,
portability_estimate, baseline_ref, canonical_trace}`. Its **output** is a routed, transmuted deposit:
`{destination, transmuted_form, trigger, form_completeness, supersedes?, routing_rationale}` — the same
record now carrying the destination decision, the delta reshaped into that destination's form, the
retrieval trigger the destination implies, a completeness flag (did transmutation capture the whole
capability without residue?), an optional supersede pointer (if this delta improves an existing
deposit), and the rationale for the routing choice. FD-06 consumes this to perform the write. The
contract's postcondition: **every routed deposit carries a destination whose trigger is named and a
transmuted form whose completeness is asserted** — a deposit with an unnamed trigger or an incomplete
form is malformed and rejected, because either would produce an inert or lossy write.

The `form_completeness` field is the transmutation quality gate made structural. It is not a boolean
the router sets optimistically; it is an assertion that the destination's form holds the delta's entire
operative capability, checkable by asking whether the original `capability_summary` can be reconstructed
from the `transmuted_form` alone. If it cannot — if something load-bearing survives only in the prose —
completeness is false, and the router must either choose a destination whose form can hold the delta or
flag it for a human decision. This prevents the silent capability loss where a rich delta is squeezed
into a form too small for it and the lost part is discovered only when the deposit fails to work months
later.

### II.2 The routing decision procedure

Routing runs in four steps. **Step 1 — decision-point identification.** Determine *when* in the stack's
operation this capability is needed — at a deploy, at a design choice, during an investigation, at
question-compilation time. The decision point dictates which triggers are relevant. **Step 2 —
destination candidate generation.** Enumerate the destinations whose triggers could fire at that
decision point (a deploy-time capability could be a Hard Rule or a Process Rule; an architectural
capability could be a dataset Part or a CO-05 asset). **Step 3 — trigger-alignment ranking.** Rank the
candidates by how early and how reliably their trigger fires relative to the decision point, weighted by
the delta's severity (a delta whose non-application causes an incident warrants the hard-blocking Hard
Rule; a helpful-but-not-critical delta warrants the lighter Process Rule). **Step 4 — transmutation and
completeness check.** Transmute the delta into the top-ranked destination's form and verify completeness;
if completeness fails, fall to the next candidate whose form can hold the delta.

The procedure is explicit so mis-routes localize. A skipped Step 1 routes by the delta's surface topic
rather than its decision point (filing a deploy-safety delta under "deployment docs" instead of a
deploy-trigger Hard Rule). A weak Step 3 over-uses Hard Rules (interrupting flow for non-critical
deltas, the Hard-Rule-inflation failure) or under-uses them (filing a critical delta as prose that
never fires). A failed Step 4 that is ignored produces lossy deposits. Each step's output is inspectable
so the routing quality can be audited against whether deposits are actually consulted at their decision
points.

### II.3 The transmutation forms (destination → required shape)

| Destination | Required form | Forcing function (what it makes explicit) |
|---|---|---|
| Hard Rule | TRIGGER / STOP / EXCEPTION / ORIGIN | the exact firing event and the exact stop action |
| Process Rule | when-X → do-Y + rationale | the precise condition and the precise response |
| Trap | symptom → cause → do-not-re-investigate | the recognizable symptom and the dead-end conclusion |
| CO-05 asset | inputs → transform → outputs (runnable) | enough precision to run with no model |
| Dataset Part | structured section (mission/contract/failure-modes) | the architecture and its rationale |
| Benchmark | metric + reference value | the measurable quantity and its target |
| Prompt fragment | compact reusable snippet | the reusable phrasing/scaffold |

Each form's forcing function is the reason transmutation is a decision, not a reformat: fitting the
delta to the form compels the router to make explicit exactly what that destination needs, and a delta
that cannot supply what the form demands (a "Hard Rule" with no identifiable trigger) is signaling that
the destination is wrong. The forms are the destinations' contracts, and transmutation is the act of
honoring them.

### II.4 Interfaces with existing PP systems

- **compound-learnings** — FD-03 extends its decision tree and reuses its artifact-materialization
  machinery for the SKILL/HOOK/RULE-class destinations; it adds the frontier-delta destinations on top.
- **UKDL** — the destination for Hard Rule / Process Rule / Trap deposits; FD-03 decides, FD-06 appends.
- **CO-05** — the destination for deterministic/asset deposits; a STRONGER delta often mutates an
  existing CO-05 asset here.
- **CO-03** — indirectly served: a CO-05 asset deposit becomes a rung CO-03 can route to, which is how
  a routed delta reduces future frontier calls.
- **GK-08 / graph** — dataset-Part deposits become graph nodes (`type: fd_dataset`) FD-06 writes.
- **FD-01** — supplies the classified delta; **FD-04** — receives benchmark deposits as decay-test
  references; **FD-06** — executes every write FD-03 routes.

### II.5 Decision rights and non-decision rights

FD-03 **may decide**: the delta's decision point; the candidate destinations; the trigger-alignment
ranking; the chosen destination; the transmuted form; and the supersede relationship to an existing
deposit. FD-03 **may not decide**: the delta's class (FD-01); whether the delta is portable in fact
(FD-04); the physical write mechanics (FD-06); or whether the destination's trigger is *implemented*
(that is a stack-capability fact, not a routing choice — FD-03 routes to the best available trigger and
flags when the ideal trigger does not yet exist). The last point is a subtle honesty boundary: if the
ideal destination is a Hard Rule but the triggering hook does not exist yet, FD-03 routes to the best
available destination now and records the ideal as a follow-up, rather than pretending a non-existent
trigger fires — the CO-10 honest-guarantee discipline applied to routing.

### II.6 Token-ROI and no-bloat rules

FD-03's ROI is realized downstream: a correctly-routed delta reduces future frontier calls because its
trigger surfaces it at the decision point; a mis-routed delta reduces nothing and wastes the frontier
call that produced it. The routing decision itself is cheap (it is a structured judgment over a small
candidate set), so its ROI is almost entirely in avoiding the mis-route. Its no-bloat rule is the
routing-side DISCARD: a delta with no destination whose trigger adds value is discarded rather than
filed into a low-value home to look productive. This catches deltas that survived FD-01 (genuinely
above-floor) but have no operational home — a rare but real case (a one-off insight with no recurring
decision point) — and prevents them from bloating a destination they do not fit.

### II.7 Portability's effect on routing

The delta's portability estimate biases the destination choice toward the most model-independent home
the capability can support. A `deterministic` delta is routed to a CO-05 asset if at all possible,
because a deterministic asset is the destination that most reduces dependence (it makes the capability
model-free and CO-03-routable). A `mid-model` delta may be routed to a dataset Part or a prompt
fragment that a Sonnet rung can execute. A `frontier-only` delta is routed to a dataset Part or a
benchmark and explicitly flagged as not-yet-portable, so FD-05 and FD-04 know it is a conversion
candidate. Routing thus operationalizes the portability slope: FD-03 prefers, wherever the delta's
portability allows, the destination that removes the most model dependence, which is the mechanism by
which the routing station actively bends the dependence curve rather than merely filing.

### II.8 A worked routing: one delta, four plausible homes, one correct one

The routing contract is clearest when a single delta is walked through the four-step procedure against
its candidate homes, because the wrong homes are all *plausible* and only the decision-point analysis
separates them. Take the delta FD-01 hands over: "when the concurrent-pane scheduler admits a new pane,
it must verify the pane's declared scope is disjoint from every already-admitted pane's scope, or two
panes will silently duplicate work." This is a real, above-floor, `deterministic`-portability capability
(it is a checkable invariant, not a judgment). It could plausibly live in four homes, and a careless
router would pick by topic.

**Home 1 — a dataset Part under 'concurrency architecture.'** Plausible, because the delta is *about*
concurrency architecture. But the retrieval trigger for a dataset Part is GK navigation — someone
reading the concurrency dataset. That trigger does NOT fire at the moment a pane is admitted; it fires
when a human happens to read the docs. Step 1 (decision-point identification) rules this out: the
capability's decision point is *pane admission*, and a dataset-Part trigger is nowhere near it. Routing
here produces an inert deposit — the invariant is recorded but never surfaced when a pane is actually
admitted, so panes keep duplicating work and the stack keeps escalating the bug to the frontier. This
is the inert-deposit failure in its purest form: correctly classified, correctly portable, filed by
topic, operationally dead.

**Home 2 — a Process Rule in UKDL.** Better: a Process Rule's trigger is consulting the relevant
checklist, which is closer to the decision point. If pane-admission is a step that consults a checklist,
this could fire. But Step 3 (trigger-alignment ranking, weighted by severity) asks whether the delta's
non-application causes an incident. Silent double-processing of work items IS an incident-class failure
(it corrupts state, wastes frontier spend, and is hard to detect after the fact). A Process Rule that is
merely *consulted* can be skipped under pressure; the severity warrants a home whose trigger fires
*automatically*, not one that relies on someone remembering to consult a checklist.

**Home 3 — a CO-05 deterministic asset.** Very plausible, because the delta is `deterministic` and the
portability preference (II.7) biases toward the most model-independent home. A CO-05 asset's trigger —
CO-03's router reaching the asset rung — is early and reliable. If pane admission were a routable task,
this would be excellent. But the scope-disjointness check is not a task the router *invokes*; it is a
guard that must fire *inside* the admission code path regardless of routing. The asset home is right
about portability but wrong about the trigger's location — CO-05 assets are pulled when CO-03 decides
to pull them, and pane admission does not go through CO-03's routing decision at all.

**Home 4 — a Hard Rule with a pane-admission trigger.** Correct. Step 1: the decision point is pane
admission. Step 2: candidates are the four above. Step 3: incident-class severity + a decision point
that is a specific, interceptable event (admitting a pane) → the destination whose trigger fires
automatically at exactly that event is the Hard Rule. Step 4: transmute to the four-field contract —
TRIGGER (scheduler admits a new pane), STOP (verify scope disjointness against all admitted panes;
refuse admission on overlap), EXCEPTION (an Owner phrase that authorizes an overlapping admission for
one turn), ORIGIN (the observed silent-double-processing incident). Completeness check: the entire
invariant is captured in the contract with no residue in prose. FD-06 appends it to UKDL §HARD-RULES.

The four homes are the whole lesson. Every one is defensible on a surface reading; the delta is
genuinely *about* concurrency (Home 1), genuinely a *process* concern (Home 2), and genuinely
*deterministic* (Home 3). Only the decision-point analysis — *when is this capability actually needed,
and which home's trigger fires then* — selects Home 4, and only Home 4 produces a deposit that actually
prevents the next occurrence of the bug. Note that the portability-preference heuristic (II.7), which
pulled toward Home 3, is correctly *overridden* here by the trigger-alignment analysis: portability
preference is a tie-breaker among homes whose triggers fire at the decision point, not a reason to
choose a home whose trigger fires elsewhere. This is why Step 1 precedes Step 3 in the procedure — the
decision point is the primary filter, and portability only adjudicates among the survivors. A router
that applied portability first would have filed a genuinely deterministic invariant as a CO-05 asset
that CO-03 never pulls at admission time, producing exactly the inert deposit the whole station exists
to prevent, and it would have done so while *looking* correct because the portability preference is a
real and usually-good rule — just not the primary one.

### II.9 The consultation-feedback loop: how the router learns it mis-routed

Routing, unlike classification, cannot be graded at the moment it happens — a route is correct if the
deposit's trigger fires at the decision point and the capability is consulted, and that verdict only
arrives *later*, when the decision point recurs. FD-03 therefore closes a feedback loop against CO-12's
adoption signals exactly as FD-01 closes one against FD-04's transfer tests. The mechanism: every routed
deposit carries its named trigger, and CO-12 already records whether a deposit's trigger fired and
whether the surfaced deposit was consulted. Joining the routing decision to that adoption record
produces, per deposit, a retrospective verdict: *consulted-at-decision-point* (the route was correct),
*trigger-fired-but-ignored* (the home was right but the transmuted form was unusable — a
transmutation-quality problem), or *trigger-never-fired* (the home was wrong — a decision-point
mis-identification, the inert-deposit failure). This three-way retrospective verdict is the router's
only honest grade, because it is measured against actual consultation, not against how sensible the
route looked at decision time — the same outcome-not-proxy discipline CWOPS §4.6 demands and the same
one FD-01 applies to its own classifications.

The loop's value is that it makes the two failure modes distinguishable and separately fixable. A
*trigger-never-fired* verdict points at Step 1 — the decision point was mis-identified, and the fix is
to re-route to a home whose trigger fires at the real decision point (Home 1 → Home 4 in II.8's terms).
A *trigger-fired-but-ignored* verdict points at Step 4 — the home was right but the form was lossy or
awkward (a Hard Rule whose STOP action is too vague to act on, a CO-05 asset whose inputs are
under-specified), and the fix is re-transmutation, not re-routing. Without the loop these two failures
look identical from the outside (a deposit that reduced no dependence), and the router would have no way
to tell whether it chose the wrong home or the wrong form. With the loop, each mis-route becomes a
localized, actionable correction, and — critically — the accumulated verdicts recalibrate the router's
Step 1 decision-point heuristics for future deltas of the same shape, so the router that mis-routed a
pane-admission delta to a dataset Part once learns that admission-time capabilities belong in
auto-firing homes and routes the next one correctly. This is the router earning the CWOPS "valid,
closed, fast" flywheel property for itself: its routing decisions are graded against a valid outcome
(consultation), the grade closes back into its heuristics, and the loop updates every time a decision
point recurs rather than on a distant review — so the router's aim improves with the same compounding
dynamic the whole suite is built to produce.

---

## Part III — Failure Modes, Gates, Benchmarks, and Evolution

### III.1 Failure modes with diagnosis protocol

| Failure mode | Symptom | Diagnosis | Root cause |
|---|---|---|---|
| **Inert deposit** | deposits stored, dependence flat, deposits never consulted | join deposits to CO-12 consultation signals; find deposits whose triggers never fire | Step 1 decision-point mis-identified; routed by topic not trigger |
| **Hard-Rule inflation** | flow interrupted by low-value auto-firing rules | audit Hard Rule deposits for severity; find non-critical deltas routed to Hard Rules | Step 3 over-weighting; every helpful delta made a hard block |
| **Lossy transmutation** | deposit fails to work; capability incomplete in its form | check `form_completeness`; reconstruct `capability_summary` from `transmuted_form` | Step 4 completeness check skipped; delta squeezed into too-small form |
| **Orphan trigger** | deposit routed to a trigger that is not implemented | check whether the destination's trigger mechanism exists | routed to an ideal-but-absent trigger without flagging |
| **Home-of-convenience bloat** | a destination fills with deltas that do not fit it | audit a destination's deposits for form-fit | no-bloat DISCARD not applied; homeless deltas filed anywhere |

The characteristic failure is the inert deposit — a correctly-classified, correctly-portable delta
routed to a home whose trigger never fires at the relevant moment. It is dangerous because it looks
like success: the vault grew, the deposit exists, the metrics of *capture* are green. Only the join to
*consultation* (CO-12 adoption) reveals that the deposit is never surfaced when needed and therefore
reduces no dependence. This is the routing analogue of the whole suite's central risk (volume without
dependence reduction), and it is why FD-03's primary evaluation metric is consultation rate, not
deposit count.

### III.2 Anti-patterns with evidence

- **Filing by topic, not trigger.** Routing a deploy-safety delta to "deployment documentation" because
  it is *about* deployment, rather than to a deploy-trigger Hard Rule. Evidence: the CO-12 finding that
  a built-but-unconsulted system produces zero savings — a deposit whose trigger never fires is exactly
  that. Forbidden by Step 1 decision-point identification.
- **The Hard-Rule hammer.** Making every useful delta a hard-blocking Hard Rule, interrupting flow for
  non-critical capabilities. Evidence: the existing HR discipline reserves hard blocks for production-
  incident-class triggers; inflation erodes the signal. Forbidden by Step 3 severity weighting.
- **Reformat-not-transmute.** Copying the delta's prose into the destination without honoring the
  form's forcing function (a "Hard Rule" with a vague trigger). Evidence: I.4 — form follows destination
  without residue; a form not fully honored is a lossy deposit. Forbidden by the completeness check.
- **The convenient home.** Filing a homeless-but-real delta into whatever destination is nearest to look
  productive. Evidence: the no-bloat discipline shared with FD-00/FD-01. Forbidden by the routing-side
  DISCARD.
- **Pretending an absent trigger fires.** Routing to an ideal destination whose trigger is not
  implemented and claiming the deposit is operational. Evidence: CO-10 honest-guarantee levels.
  Forbidden by the II.5 flag-the-absent-trigger rule.

### III.3 Quality gates (binary)

- **G1 — Decision point identified.** Does every deposit name the decision point its capability serves?
  Binary.
- **G2 — Trigger named.** Does every deposit's destination carry a named, existing (or flagged-absent)
  trigger? Binary.
- **G3 — Form complete.** Is `form_completeness` true — the whole capability reconstructable from the
  form? Binary.
- **G4 — Severity-appropriate.** Is a Hard Rule destination justified by incident-class severity?
  Binary.
- **G5 — Homeless discarded.** Are deltas with no value-adding home DISCARDed rather than filed? Binary.

### III.4 Evaluation rubric (measurable)

| Dimension | Metric | Source | Target |
|---|---|---|---|
| Consultation rate | fraction of routed deposits whose trigger actually fires and is consulted | CO-12 adoption signals | rising toward 1.0 |
| Routing precision | fraction of deposits whose destination a re-audit confirms | routing audit | ≥ 0.9 |
| Transmutation completeness | fraction of deposits with `form_completeness` true and no later capability-loss | completeness audit | ≥ 0.95 |
| Hard-Rule discipline | fraction of Hard Rule deposits that are genuinely incident-class | severity audit | high; inflation flagged |
| Portability routing | fraction of `deterministic` deltas routed to CO-05 assets | routing↔portability join | high |

### III.5 Benchmarks with reference values

**Consultation floor:** a routed deposit's trigger must fire at its decision point — a destination
whose consultation rate is near zero is a mis-route, and this is the routing analogue of CO-12's PM-03-
inert-day proof that built-but-unconsulted equals absent. **Completeness floor:** ≥ 0.95 of deposits
must be reconstructable from their form; below this, lossy transmutation is eroding the vault. **Hard-
Rule severity:** the existing HR archive is the reference — a Hard Rule is warranted only at the
severity of the sealed production bugs already in HARD_RULES.md, not for every helpful tip. **Routing
latency:** the routing decision must be cheap relative to the frontier call it follows (CWOPS guardrail
economics) — a router that reasoned as long as the model did would have no ROI.

### III.6 Example operational traces

**Trace A — deploy-safety delta → Hard Rule.** FD-01 hands FD-03 a NEW delta: "a deploy without a
verified backup caused data loss." Step 1: decision point is deploy-time. Step 2: candidates are a
Process Rule and a Hard Rule. Step 3: incident-class severity → Hard Rule. Step 4: transmute to
TRIGGER (deploy command) / STOP (verify backup) / EXCEPTION (Owner phrase) / ORIGIN (the incident).
Completeness true. FD-06 appends to UKDL §HARD-RULES.

**Trace B — reusable transform → CO-05 asset.** A STRONGER delta improves a dedup recipe, portability
`deterministic`. Step 1: decision point is any dedup task. Step 3: the CO-05-asset destination has the
earliest trigger (CO-03's asset rung fires before any model call). Step 4: transmute to inputs→
transform→outputs. Supersedes the existing recipe. FD-06 mutates the CO-05 asset.

**Trace C — architectural design → dataset Part.** A NEW delta is a multi-part concurrency scheme too
large for a rule. Step 3: dataset Part (GK-navigable) is the right home; a rule cannot hold the
architecture. Step 4: transmute to a structured section. Portability `mid-model`, flagged for FD-04.
FD-06 writes the graph node.

**Trace D — homeless insight → DISCARD.** A NEW delta is a genuinely novel but entirely one-off
observation with no recurring decision point. No destination's trigger would ever fire usefully. Step
2 finds no value-adding home. Routing-side DISCARD, recorded with reason. The vault is protected from a
deposit that would never be consulted.

**Trace E — ideal trigger absent.** A delta ideally belongs in a Hard Rule, but the triggering hook is
not implemented. FD-03 routes it to a Process Rule now (best available), transmutes accordingly, and
records "ideal: Hard Rule pending trigger hook" as a follow-up — honest about the guarantee level
rather than pretending an absent hook fires.

### III.7 Edge cases

- **Delta fits two destinations equally.** Tie broken by earliest-firing trigger; if still tied, route
  to the more model-independent home (portability preference).
- **Delta improves multiple existing deposits.** Routed as a supersede to the primary and cross-
  referenced to the others; FD-06 handles the multi-supersede with back-references.
- **Delta whose form completeness fails on every candidate.** Flagged for human decision rather than
  force-filed; usually a sign the delta is really several capabilities that should be split.
- **STRONGER delta whose target asset was deprecated.** Routed as NEW to a fresh asset rather than
  mutating a dead one, with a note that the old asset is superseded.
- **Frontier-only delta.** Routed to a dataset Part or benchmark, flagged not-yet-portable, queued for
  FD-05 conversion and FD-04 decay-testing.

### III.8 Writeback rules

FD-03 does not write; it hands FD-06 a fully-routed, fully-transmuted deposit with the mandatory fields
`{destination, transmuted_form, trigger, form_completeness, supersedes?, routing_rationale}`. FD-06
rejects a deposit missing the destination, an unnamed trigger, or a false completeness that was not
flagged for follow-up. The separation guarantees that the write mechanics (append-with-supersede,
mirror sync, graph node) operate only on a deposit whose destination and form are already decided, so a
routing error cannot be masked by the write succeeding.

### III.9 Conceptual regression tests

- **R1 — Trigger alignment.** Feed a deploy-safety delta; assert routing to a deploy-trigger
  destination, not to topical documentation.
- **R2 — Hard-Rule severity.** Feed a helpful-but-non-critical delta; assert it is *not* routed to a
  Hard Rule.
- **R3 — Completeness enforcement.** Feed a rich delta and a too-small destination; assert completeness
  fails and the router falls to a form that holds it.
- **R4 — Homeless discard.** Feed a one-off insight with no decision point; assert routing-side DISCARD.
- **R5 — Absent-trigger honesty.** Feed a delta whose ideal trigger is unimplemented; assert best-
  available routing with a flagged follow-up, not a pretended fire.

Per SCS C41, these are gate assertions for the EXECUTION-mode harness; the consultation-rate metric is
measured against real CO-12 adoption data, the honest observation the anti-test-theater rule requires.

### III.10 Done criteria (verifiable)

FD-03 is done when: the dataset exists on disk, un-truncated, >2500 real words/Part; the destination
taxonomy is closed with a distinct trigger per home; the transmutation forms are specified with their
forcing functions; the four-step routing procedure localizes each failure; the "form follows
destination without residue" completeness bar is a binary gate; the dataset declares compound-learnings
and UKDL as parents (extended, not duplicated); and V-FD-NO-CODE finds zero fences.

### III.11 Upgrade path

- **v1 (this dataset):** the routing-and-transmutation decision as a rung-2 layer feeding FD-06.
- **v2 (EXECUTION-mode):** the consultation-rate metric is computed from CO-12 adoption so mis-routes
  are caught by falling consultation rather than discovered as inert deposits; the compound-learnings
  decision tree is extended in code with the frontier-delta destinations.
- **v3:** trigger-existence is checked automatically against the live hook/asset registry so the
  absent-trigger flag is set mechanically rather than by judgment, and routing to an implemented trigger
  is preferred structurally.
- **Deprecation trigger:** if a destination's consultation rate proves durably zero across many routed
  deltas, that destination is retired from the taxonomy for the relevant delta classes — the router
  stops offering a home whose trigger never adds value, tightening the taxonomy against measured
  uselessness rather than assumption.

### III.12 Routing under concurrency and the supersede-race

FD-03 inherits the same multi-pane reality as FD-01 and FD-02: several panes on one repo may route
deltas concurrently, and two coordination hazards arise that a single-pane design would miss. The first
is the *duplicate-destination race*: two panes extract related deltas and both route them to the same
home — two Hard Rules for overlapping triggers, or two CO-05 assets for the same capability — producing a
destination cluttered with near-duplicates that dilute rather than compound. The second is the
*supersede-race*: pane A routes a STRONGER delta as a supersede of an existing deposit at the same moment
pane B routes a different improvement to the same deposit, and if both writes land naively, one silently
clobbers the other. Both hazards are resolved by leaning on machinery the stack already provides rather
than inventing new coordination. For the duplicate-destination race, FD-03 consults the PM-03 findings
bus in Step 2: a delta another pane has already routed to a home is visible on the bus with its
destination, so a concurrent pane sees the in-flight route and either defers (the other pane's deposit
covers it) or routes a genuinely distinct increment as a supersede rather than a duplicate. For the
supersede-race, FD-03 defers to FD-06's append-with-supersede-and-back-reference discipline, which is the
same append-only, never-silent-delete contract UKDL itself uses: concurrent supersedes are serialized as
a chain of back-referenced revisions, so no improvement is lost and the deposit's revision history stays
legible. The router does not implement locking or merge logic of its own; it consumes the bus for
visibility and FD-06 for write-serialization, keeping the "one system, no parallel systems" discipline
intact.

There is a subtler concurrency benefit that mirrors the one FD-01 and FD-02 gain. Because routed deltas
are published to the bus with their destinations, the *destination landscape* becomes shared across
panes in near-real-time, which lets the router avoid a specific and otherwise-invisible waste: two panes
each independently deciding that a capability warrants promotion to a Hard Rule, and both spending the
transmutation effort to produce the four-field contract, when one contract would serve both. Seeing the
first pane's in-flight Hard-Rule route on the bus, the second pane's router recognizes the destination is
already being populated and redirects its effort to cross-referencing or to a distinct increment, rather
than duplicating the promotion. Over a repo worked by six to ten panes, this turns what would be a
scattering of overlapping, half-redundant routes into a coordinated deposition where each pane's routing
effort lands on a distinct home or a distinct increment of a shared one. Achieving this purely by
consuming PM-03 and FD-06 — without a bespoke routing coordinator — is what keeps FD-03 a single station
in a single system rather than the seed of a parallel coordination layer, and it is the reason the router
treats the bus's destination landscape as a first-class Step-2 input rather than an optimization bolted
on for the multi-pane case.

### III.13 The relationship between routing quality and the whole dependence curve

A final synthesis makes explicit why FD-03's consultation-rate metric is, in a real sense, the suite's
own dependence curve read from the routing station. Every station in the suite contributes to bending
`D(c, t)` — the probability the stack must escalate class `c` to the frontier — but FD-03 is where the
contribution becomes irreversible or is squandered. FD-05 will later convert frontier-only deltas to
cheaper substrates, but it can only convert deltas that were routed to a home where their conversion is
actionable; FD-04 will prove portability, but only for deposits it can find and re-execute; CO-03 will
route future work to a cheaper rung, but only if FD-03 deposited the capability as a rung CO-03 can
reach. In each case the downstream dependence-reducing action is gated on FD-03 having routed the delta
to a home that the downstream action can act on. This is why a mis-route is not a local error but a
curve-flattening one: a delta routed to an inert home does not merely fail to reduce dependence itself,
it also removes itself from the reach of every downstream mechanism that could have reduced dependence
through it. Correct routing, conversely, is what keeps the delta *live* for the rest of the suite —
available to FD-04's proof, FD-05's conversion, and CO-03's future routing — so that the single act of
routing determines whether a captured delta becomes a durable downward pressure on the dependence curve
or a one-time observation that never compounds. The consultation-rate metric therefore measures not just
whether deposits are read, but whether the suite's own compounding machinery still has access to the
advantage each delta represents, which is the most complete single indicator of whether the routing
station is doing its job of keeping captured advantage alive and reachable. A suite whose extraction and
question stations are excellent but whose routing is careless is a suite that finds gold and buries it
where no map leads back — which is why FD-03, quiet as it is, carries as much of the suite's fate as the
spine that precedes it.
