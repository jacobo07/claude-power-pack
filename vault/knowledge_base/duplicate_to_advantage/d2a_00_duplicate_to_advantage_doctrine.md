# D2A-00 — Duplicate-to-Advantage Doctrine & Operating Protocol

> The immune-and-evolution system of the Claude Power Pack ecosystem. Where the
> **Cognitive OS** (CO-00…CO-12) governs the *cost* of a session, the **Parallel Mesh**
> (PM-01…PM-05) governs the *coordination* of many panes, the **Graphify Kernel**
> (GK-00…GK-12) governs *how knowledge is located*, the **Fable Distillation Suite**
> (FD-00…FD-07) governs *converting a frontier delta into permanent advantage*, and
> **FIOS** *executes* that doctrine — the **D2A Engine** governs one thing none of them
> does: **what happens when the ecosystem is asked to build something that already
> partly exists.**
>
> **Root law (`PR-DUPLICATE-TO-ADVANTAGE-001`):** *Ninguna duplicidad termina en
> rechazo. Toda duplicidad se convierte en búsqueda estructurada de la mejor capacidad
> adyacente que aún no existe.* A detected duplicate is never a "no". It is a signal that
> the search for the next non-redundant, highest-compound capability must begin — mapped,
> scored, and reduced to the minimal correct artifact.
>
> **Honesty rule (inherited from CO-10 / CO-12):** every D2A verdict carries numbers, not
> adjectives — a coverage percentage, a per-axis overlap, a 0–10 score per portfolio
> dimension, a pass/fail per anti-inflation rule. A claim without its `(metric, source,
> value)` triple is a hypothesis, never a verdict.
>
> **Anti-inflation is the point, not a footnote:** the D2A Engine, applied to its own
> proposal at STOP #1 (2026-07-10), returned *"do not build 6 prose datasets — one
> doctrine + one engine."* A governor that cannot restrain its own family is theatre.
> This dataset is that one doctrine; `modules/duplicate_to_advantage/d2a_engine.py` is
> that one engine. Sealed as **SCS C85**.

---

## Part I — The Paradigm, the Duplicate Detection Core (D2A-1), and the Capability Gap Mapper (D2A-2)

### I.1 Mission

The D2A Engine exists to convert the most common and most wasteful event in a maturing
ecosystem — *"this proposal overlaps something we already built"* — from a dead end into
a directed search. Every sealed family in this Power Pack was born from a manual version
of this event. CO's Reality Scan found 9 proposed systems and shipped 2 NEW + 8 EXTEND.
PM found and shipped 5 NEW while folding a Reasoning-Dedup engine into PM-03 and dropping
a Portfolio Manager as COVERED by CO-01. GK folded ~40 Owner candidates into 13
boundaries with zero parallel systems. FD mapped 26 candidates to 5 NEW + 3 EXTEND + 2
MERGE + 10 DO_NOT_BUILD — reporting *before building* that ~81 % of the named surface was
already covered. FIOS took 17 proposed systems and shipped 3 code engines + 1 doctrine,
*zero* new prose datasets. Five families, five manual executions of the same procedure:
detect the overlap, map the true gap, generate the adjacent capabilities, score them,
and reduce the winner to the smallest correct artifact. The D2A Engine is that procedure
made repeatable, deterministic, and callable — so the sixth family, and the sixtieth, do
not re-derive it by hand under STOP-#1 pressure.

The paradigm shift is one sentence: **a duplicate is a coordinate, not a verdict.** When
the ecosystem detects that a proposal already lives somewhere, that location is the most
valuable single fact available — it tells you *exactly* where the frontier of the
non-redundant capability space is, because the frontier is always immediately adjacent to
what already exists. The engine's job is to stand at that coordinate and look outward.

### I.2 The exact problem D2A-1 solves

Duplicate detection in software is usually done by *name* — two files with similar titles,
two functions with the same signature. That detection is worthless for architecture,
because the expensive duplicates are the ones with *different names and the same
responsibility*. The PP has lived this: a "Cognitive Portfolio Manager" proposal was a
rename of CO-01's Cognitive Capital; a "Deterministic Replacement Engine" was CO-03's
existing deterministic rung; a "Token Budget Planner" is FD-05 arbitrage plus CO-12 gap
radar plus CO-01 accounting wearing a new hat. None of these collide by name. All of them
collide by *behaviour*.

So D2A-1 detects on three axes, never on the string:

1. **Semantic overlap** — the same *idea* under different words. Measured as the recall of
   a sealed family's responsibility vocabulary against the proposal's tokens: how much of
   what family F is *about* does this proposal talk about?
2. **Functional overlap** — the same *responsibility* at a different layer. Measured as
   precision: how much of the proposal's own substance lands on an existing family's
   surface? A proposal whose every meaningful token is already owned somewhere is a
   functional duplicate regardless of which layer it claims to sit at.
3. **Architectural overlap** — the same *position in the systems graph*. Measured by how
   many sealed families light up at once. A proposal that touches one family is a clean
   EXTEND; a proposal that touches four families is re-occupying an already-densely-owned
   architectural slot, which is the single strongest duplicate signal the engine has.

The output is a **DUPE VERDICT**: the dominant parent (id + human name), a coverage
percentage 0–100, the three per-axis scores, a boolean `is_duplicate`, and up to two
secondary parents. Crucially, `is_duplicate=True` is not a rejection field — it is the
*trigger* for the rest of the pipeline. The detector's contract is explicitly that a high
coverage number **starts** the advantage search, it does not end the proposal.

### I.3 The difference from PM-02, PM-03, FD-01, and the evolution_engine

This is the most important boundary in the whole family, because D2A-1 sits one inch from
four existing detectors and must not duplicate any of them — which would be a self-refuting
first act.

- **PM-02 (Pane Intent & Collision Detector)** detects collision between *live panes* on
  one repo: two agents about to edit overlapping scopes *right now*. Its unit is a running
  session's declared scope; its timescale is seconds; its consequence is a soft pause.
  D2A-1's unit is an *architecture proposal that does not yet exist*; its timescale is a
  design decision; its consequence is a redirected build. Panes vs proposals. Runtime vs
  design-time. They share the word "collision" and nothing else.
- **PM-03 (Shared Findings Bus + Redundancy Tax)** blocks *work already performed* from
  being repeated: a finding published to the bus must be consumed before it is re-derived.
  Its unit is a completed finding. D2A-1's unit is a *not-yet-started system*. PM-03 stops
  you re-doing yesterday's grep; D2A-1 stops you re-building last month's family.
- **FD-01 (Fable Delta Extraction Engine)** classifies a *frontier model's output* against
  the PP baseline as `NEW / STRONGER / DUP / DISCARD`. Its input is text a model just
  produced; it decides whether that output is worth keeping. D2A-1's input is a *human's
  build intention*; it decides whether that intention is worth building. FD-01 grades an
  answer; D2A-1 grades a plan. The engine deliberately *reuses FD-01's tokenizer surface*
  (via the evolution_engine import shim) precisely so it does not re-implement tokenization
  — composition, never duplication.
- **`frontier_intelligence.evolution_engine` (FIOS IV-1)** is the closest neighbour and the
  one D2A most explicitly extends. The evolution engine scans the *existing* knowledge base
  *retrospectively* and proposes health mutations (compress / split / merge / reinforce /
  deprecate / abstract / specialize) on datasets that already exist. Its `merge` signal is
  a title-Jaccard near-duplicate detector — but only over files already on disk. D2A-1 runs
  the mirror-image direction: *prospectively*, over a proposal that is not yet a file. The
  evolution engine asks "how should what exists evolve?"; D2A-1 asks "should this new thing
  exist, and if not, what adjacent thing should?" Retrospective vs prospective is the whole
  distinction, and it is a real one — no existing surface takes a proposal string as input
  and returns a build-or-redirect verdict.

### I.4 What D2A-1 explicitly does NOT duplicate

It does not stand up a new tokenizer (reuses `evolution_engine._tokens`). It does not
maintain a graph (GK-01 owns coordinates; D2A references families by id, it does not
re-address them). It does not compute a cost metric (CO-01 owns WU/MTok; D2A-5 consumes
scores, it does not re-accountant them). It does not route models (CO-03). It does not
publish findings (PM-03). Its single owned responsibility is: *given a proposal, return
which sealed responsibility it collides with and by how much.*

### I.5 D2A-2 — the Capability Gap Mapper: mission and exact problem

A detector that only says "92 % covered, stop" is a bureaucrat. The entire thesis is that
the detection is the *beginning*. So the instant a duplicate is found, D2A-2 does the
opposite of stopping: it builds the complete map of the capability space *around* the
matched parent, so the engine can see exactly which adjacent capabilities are covered,
which are half-covered, and which are absent. The gap is where the next real system lives.

D2A-2 maps **14 capability dimensions** around the parent, each marked `covered` /
`partial` / `absent`:

1. Covered capabilities — what the parent already fully owns.
2. Partially covered — where the parent gestures but does not complete.
3. Absent capabilities — adjacent responsibilities nobody owns.
4. Parent weaknesses — where the parent is known to be fragile or shallow.
5. Unexploited dependencies — inputs the parent has but does not fully use.
6. Missing interfaces — connections to other families that would compound but do not exist.
7. Still-manual processes — steps a human performs that could be automated.
8. Frontier-required parts — where an Opus/frontier call is currently mandatory.
9. Deterministic-convertible parts — frontier work that could become a deterministic recipe.
10. Uncovered failure modes — ways the parent breaks that have no guard.
11. Missing evals — behaviours with no test / benchmark.
12. Compression & portability opportunities — bloat to shrink, capability to make portable.
13. Telemetry / observability gaps — what the parent does but cannot measure.
14. Writeback gaps — learnings the parent produces but does not persist.

### I.6 D2A-2 difference, non-duplication, contracts, and interfaces

D2A-2 composes **CO-12's Capability Gap Radar** (which measures adoption gaps over
eligible opportunities) and **GK-09's coverage/blind-spot observatory** (which measures
navigation coverage over the graph). It duplicates neither: CO-12 measures *adoption of an
existing lever*, GK-09 measures *coverage of the knowledge graph*, and D2A-2 measures *the
capability neighbourhood of one matched parent, on demand, triggered by a duplicate hit*.
The trigger and the scope are what make it distinct — it does not run continuously over
everything; it runs once, focused, when D2A-1 fires.

**Operative contract.** Input: a `DupeVerdict` (the parent id). Output: a `GapMap` — the
14 dimensions each classified, plus the explicit `absent` and `partial` lists that feed the
generators. **Decision rights:** D2A-2 decides which dimensions are open. **Non-decision
rights:** it does *not* decide what to build in them (that is D2A-3/4/5/6) and it does not
mutate the parent (that is Owner-gated writeback).

### I.7 Failure modes, anti-patterns, quality gates, and benchmarks (Parts I components)

**Failure mode F-1 — the false EXTEND.** D2A-1 reports a duplicate where none exists,
redirecting a genuinely-new system into a needless Part on an unrelated parent. *Diagnostic
protocol:* when coverage ≥ 80 % but only ONE family lit up and its precision (functional
axis) is < 25 %, treat the verdict as low-confidence and surface both the parent and the
"NOVEL fallback" so the Owner rules. *Guard:* the architectural axis requires ≥ 4 families
to floor coverage at 80 % — a single-family match cannot alone manufacture a false
duplicate.

**Failure mode F-2 — the bureaucratic stop.** The engine detects a duplicate and returns
without generating candidates. *This is a root-law violation* (`PR-DUPLICATE-TO-ADVANTAGE-
001`): a verdict with `is_duplicate=True` and an empty portfolio must never be emitted.
*Guard:* `run()` always calls the generators; the quality gate `V-D2A-VERTICAL-GENERATED`
+ `V-D2A-HORIZONTAL-GENERATED` fail if the portfolio is empty on a duplicate.

**Failure mode F-3 — gap-map starvation.** D2A-2 marks every dimension `covered` and leaves
the generators no space. *Diagnostic:* if `absent + partial` is empty, the parent-covers
table is stale — a real parent never covers all 14 dimensions. *Guard:* the mapper falls
back to the full dimension list when the covers-set is suspiciously complete.

**Anti-pattern A-1 — name-only detection.** Matching proposals by title. *Ecosystem
evidence:* the "Cognitive Portfolio Manager" and "Deterministic Replacement Engine"
proposals both had novel names and were pure duplicates by behaviour — caught by
functional/architectural overlap, invisible to name matching.

**Anti-pattern A-2 — the infinite gap.** Treating every dimension as absent to justify a
big build. *Ecosystem evidence:* FD's honest scan found 81 % *covered*; a gap map that
finds 81 % *absent* is lying to inflate the build.

**Quality gates (binary).** `V-D2A-DETECTION-SEMANTIC`: a genuinely-overlapping proposal
scores > 80 % coverage. `V-D2A-GAP-MAPPED`: ≥ 8 of 14 dimensions classified on every
detection. Both are binary and measured by the test suite, not asserted.

**Benchmarks (numeric reference values).** On the canonical Token-Budget-Planner proposal
the engine returns coverage **95 %** (semantic 56, functional 33, architectural 100),
parent **FD-05**, secondaries **CO-01 + FIOS-IRR**, gap map **7 absent / 4 partial /
3 covered** of 14 dimensions. A clean NEW proposal (e.g. a genuinely novel modality) must
score coverage < 50 % and `is_duplicate=False`. Detection latency is a single in-process
pass over 20 registry families — sub-millisecond, no model call, no I/O — so the engine is
free to run on every proposal at design time. Token ROI: **0 frontier tokens** per
verdict; the entire detection + mapping is deterministic Python. That zero is the point —
the governor of build-cost must itself cost nothing.

### I.8 The three-axis detection, worked numerically

The detection is not a black box; every number is reproducible by hand, which is what makes
the whole family auditable. Consider the canonical proposal, whose meaningful tokens (after
stop-word removal) are roughly {route, model, budget, price, frontier, token, cost, capital,
plan, reuse, deterministic, conversion, adapt, session}. Fourteen tokens. The detector walks
the twenty registry families and counts, for each, how many of those fourteen tokens fall in
that family's responsibility vocabulary.

- **FD-05 (Anti-Dependence Arbitrage)** owns {frontier, deterministic, convert, budget,
  planner, gap, adapt, arbitrage, dependence}. It catches frontier, deterministic, budget,
  adapt — four hits. Its *semantic* recall is 4 of its ~9 keywords ≈ 44–56 %. Its
  *functional* precision is 4 of the proposal's 14 tokens ≈ 29–33 %.
- **CO-01 (Operating Economics)** owns {cost, economics, capital, work, unit, budget, token,
  ledger, roi}. It catches cost, capital, budget, token — four hits. It is a strong
  secondary.
- **FIOS-IRR (Token IRR)** owns {irr, payback, reuse, multiplier, compound, capital,
  dependence, index}. It catches reuse, capital — a lighter secondary.
- **CO-03 (Router)** catches route, model. **CO-05** catches reuse, deterministic.

So five-plus families light up. That is the architectural axis: `min(1, lit/4) = 1.0 → 100`.
The owned-fraction — how many of the fourteen proposal tokens land in *some* family — is
roughly {route, model, budget, frontier, token, cost, capital, reuse, deterministic, adapt,
session} ≈ 11 of 14 ≈ 0.79. The coverage blend `0.70·0.79 + 0.15·0.33 + 0.15·1.00 ≈
0.553 + 0.050 + 0.150 = 0.75 → 75 %`, and because five families lit up (≥ 4), the duplicate
floor lifts it to 95 %. Every one of these numbers is deterministic and re-derivable — there
is no hidden model call, no learned weight, no randomness. That is the property that makes
the tests hermetic and the verdict defensible to an Owner who wants to see the arithmetic.

### I.9 The negative trace — a genuinely-NEW proposal

The detector must be equally trustworthy when it says *"this is new."* Feed it **"holographic
tactile feedback surface for underwater sonar imaging."** Its tokens — holographic, tactile,
feedback, surface, underwater, sonar, imaging — land on *zero* registry families. Owned
fraction 0.0, no family lights up, architectural axis 0, coverage **0 %**, `is_duplicate =
False`, note **NOVEL**. The engine does not manufacture a false parent to have something to
say; a proposal outside the ecosystem's vocabulary is correctly reported as new territory,
and it is still routed to the minimal artifact (a genuinely-new capability gets the smallest
correct form, never an automatic full family). This negative case is a first-class quality
gate (`V-D2A-NOVEL-NOT-FLAGGED`): a duplicate detector that cannot recognize novelty is a
rubber stamp, and a rubber stamp that always says "duplicate" would strangle the ecosystem
exactly as surely as one that always says "new" would bloat it. The engine's honesty lives
in the gap between the 95 % canonical verdict and the 0 % sonar verdict — both are correct,
both are numeric, and both are reproducible on any host under any model.

### I.10 Token ROI and the cost of detection itself

A governor of build-cost that is itself expensive is a contradiction, so the detection and
mapping stages spend **zero frontier tokens** and run in a single sub-millisecond in-process
pass over the twenty-family registry — no I/O, no network, no model. This is deliberate and
load-bearing: because a verdict costs nothing, the engine can be run on *every* proposal at
design time without the Owner ever weighing "is it worth checking?" The moment detection
required a model call, its own cost would exceed the small builds it most often governs
(a Part, a rule), and rational actors would skip it — which is precisely how the manual
Reality Scan was skipped often enough for the ecosystem to accrete near-duplicates before
D2A existed. Zero-cost detection is what lets the discipline be universal rather than
occasional.

---

## Part II — The Reinforcement Generators (D2A-3, D2A-4) and the Alternative Portfolio Optimizer (D2A-5)

### II.1 Mission of the generators

Once D2A-2 has drawn the map, the generators populate it with concrete candidates. There
are exactly two directions in which a matched parent can be reinforced, and the family
gives each its own generator so neither is forgotten:

- **D2A-3 Vertical Reinforcement** goes *down* — it deepens the parent itself: more
  autonomy, more precision, more resilience, lower cost, less model dependence, better
  evaluation, faster recovery. A vertical candidate is *the layer that was missing beneath
  the parent.* It never proposes "a system that does the same thing but better" — that is a
  rename (anti-inflation rule 3). It proposes the specific sub-capability the parent
  assumed but never built.
- **D2A-4 Horizontal Reinforcement** goes *sideways* — it connects the parent to another
  family so a capability *emerges from the link* that neither system has alone. A horizontal
  candidate names the interface it creates, the family it connects to, and the compounding
  it activates.

### II.2 The exact problem D2A-3 solves and its difference from evolution_engine

The FIOS evolution_engine already emits `reinforce`, `specialize`, and `abstract` mutation
proposals — but only retrospectively, on datasets that exist, driven by health thresholds
(a file below the depth floor, a file spanning too many topics). D2A-3 is the prospective
twin: it generates reinforcement candidates for a *parent implicated by a proposal*, driven
by the *gap map's absent/partial dimensions*, not by file health. Each absent dimension
maps deterministically to an operation — an absent capability → **DEEPEN**, a parent
weakness → **HARDEN**, a still-manual process → **AUTOMATE**, a frontier-required part →
**DETERMINIZE**, a missing eval → **EVALUATE**, a compression opportunity → **COMPRESS**.
The engine guarantees at least three vertical candidates per detection (padding the pool
from the full dimension list if the specific gaps are few), because a generator that
sometimes returns nothing cannot be relied on as the second half of the root law.

**Each vertical candidate carries three mandatory fields:** *what it improves exactly*
(the named gap it closes), *how the improvement is measured* (a before/after count plus a
green regression suite — a number, never "better"), and *what it does not touch* (the
parent's existing covered surface, so the reinforcement is strictly additive and cannot
regress the parent). That third field is the anti-rename guard: a candidate that cannot
name what it leaves intact is proposing a rewrite, not a reinforcement.

### II.3 D2A-4 — horizontal generation, difference, and non-duplication

D2A-4 composes the evolution_engine's `merge`/`abstract` instincts and GK-04's typed
cross-family edges, but again prospectively and for emergent capability rather than graph
hygiene. It reads a small edge registry of the most productive connections for each
parent — for FD-05, the links to CO-12 (adaptation signal feeds the readiness instrument),
to FD-07 (per-session arbitrage joins the cross-session flywheel), and to the Token IRR
calculator (counterfactual spend priced as R&D capital). Each horizontal candidate names
its interface, its partner family, and — the field that justifies it — the *emergent
capability*: the thing that only exists once the two systems are connected. A horizontal
candidate whose emergent field is empty is a wire with nothing on the other end and is
dropped. At least three horizontal candidates are guaranteed, so the portfolio always
contains both axes and the anti-inflation rule "reinforce ≥ 1 vertical and ≥ 2 horizontal"
can always be satisfied by the pool.

**Non-duplication:** D2A-4 does not create graph edges (GK-04 owns the typed edge
registry; D2A-4 *reads* the productive-edge hints and proposes an interface). It does not
publish to the bus (PM-03). It proposes; it never wires.

### II.4 D2A-5 — the Alternative Portfolio Optimizer: mission and the 16 dimensions

Now the engine has a pool of vertical and horizontal candidates and must choose. The
naïve choice is "the biggest" — the most ambitious system. That instinct is exactly what
produces bloat, and the optimizer exists to defeat it. **The winner is the best *ratio*,
not the biggest *value*.**

Every candidate is scored 0–10 on **16 dimensions** — and every score is a *number*, which
is the hard requirement of `V-D2A-NUMERIC-BENCHMARKS` (an evaluation rubric with an
adjective and no number is rejected):

1. **Novelty** — inversely tied to how much the parent already covers.
2. **Non-redundancy** — inversely tied to semantic overlap.
3. **Vertical reinforcement** — high for vertical candidates.
4. **Horizontal reinforcement** — high for horizontal candidates.
5. **Compound effect** — high when the candidate connects or determinizes (compounds across
   uses).
6. **Reuse potential** — high for deterministic and connective candidates.
7. **Frontier-token savings** — high for DETERMINIZE/COMPRESS/AUTOMATE.
8. **Deterministic conversion potential** — high when the candidate turns a model call into
   a recipe.
9. **Integration value** — high for connective candidates.
10. **Long-term value** — high for deterministic and evaluative candidates.
11. **Maintenance cost** *(inverse — a cost)* — low for deterministic/vertical.
12. **Complexity introduced** *(inverse)* — low for vertical (a Part), higher for horizontal
    (an interface across two systems).
13. **Regression risk** *(inverse)* — low for pure evaluation/compression.
14. **Portability** — high for deterministic candidates.
15. **Measurability** — high for evaluative candidates.
16. **Production readiness** — high for vertical candidates that ride an existing dataset.

The three inverse dimensions (11, 12, 13) are *costs* — they form the denominator. The
thirteen positive dimensions form the numerator. The selection formula is:

> **ratio = Σ(positive scores) / max(1, Σ(cost scores))**  ≡  *expected compound value per
> unit of complexity + maintenance + debt.*

The portfolio is sorted by ratio, with novelty as the tiebreaker. The top candidate is the
**RECOMMENDED ACTION**. This is a direct composition of the accounting the PP already owns:
the reuse-multiplier and compound-ROI language is `token_irr.py`'s; the ROI-ranked-spend
discipline is PM-04's Budget Auction; the WU/MTok cost frame is CO-01's; the portability
verdict is the kind FD-04 produces. D2A-5 does not stand up a new accountant — it arranges
the existing numbers into a build-decision score.

### II.5 The Token Budget Planner worked example (canonical trace + 5 alternatives)

This is the operative example every downstream reader must be able to reproduce. A
contributor proposes **"Token Budget Planner"** — plan and allocate the frontier token
budget for a session.

- **D2A-1 detects:** dominant parent **FD-05 (Anti-Dependence Arbitrage)** at **coverage
  95 %** (semantic 56, functional 33, architectural 100 — four-plus families light up:
  FD-05, CO-01, FIOS-IRR, CO-12, PM-04). Secondary parents **CO-01** and **FIOS-IRR**.
  `is_duplicate = True`. The Planner is not new; budget planning is already owned by FD-05
  arbitrage + CO-12 gap radar + CO-01 accounting + FIOS token-IRR + PM-04 auction. In the
  old world this is a rejection. In D2A it is the starting coordinate.
- **D2A-2 maps the gap:** of 14 dimensions, 3 covered, 4 partial, 7 absent. The single
  most interesting absent dimension: **budget *adaptation during the session*** according
  to real novelty observed and current performance — everyone plans the budget *up front*;
  nobody adjusts it *mid-flight* on evidence.
- **D2A-3 generates vertical candidates**, among them the **Frontier Budget Adaptation
  Engine** — DEEPEN FD-05 so the budget is re-priced in real time as the session's actual
  novelty and yield are observed (measured by: budget-vs-yield error before/after; regression
  suite green; leaves FD-05's up-front planning untouched).
- **D2A-4 generates horizontal candidates**, among them the **Cross-Session Budget Learning
  Loop** — CONNECT FD-05 × FD-07 so each session's realized ROI teaches the next session's
  opening budget (emergent capability: a budget that compounds across sessions; measured by
  opening-estimate error trend across N sessions).
- **D2A-5 scores the portfolio** and a third, generated candidate wins on *ratio*: the
  **Counterfactual Frontier Spend Simulator** — DETERMINIZE, which simulates *"what would
  this session have cost, and yielded, had we used Opus vs Sonnet vs the deterministic
  rung?"* It wins because it scores highest on novelty (nobody simulates the counterfactual
  spend), compound effect and frontier-token savings (it directly reduces future Opus
  calls), portability and measurability (its output is a number), at low complexity (it
  rides FD-05's existing arbitrage data) — the best value-per-cost ratio of the pool.
- **D2A-6 decides the artifact:** because FD-05's coverage is 95 % (deep), the minimal
  correct form is **a new Part in FD-05, not a new dataset.** The **BUILD CONTRACT**:
  *extend FD-05 Part III with the counterfactual Opus-cost simulation; reinforces FD-05 +
  CO-12; does not re-own FD-05's covered arbitrage surface; retires a class of speculative
  Opus calls by making their cost knowable in advance; evaluated by counterfactual-vs-actual
  spend error; operation DETERMINIZE; anti-inflation 10/10.*

The five alternatives the engine surfaced and the Owner can inspect — Frontier Budget
Adaptation Engine (vertical DEEPEN), Cross-Session Budget Learning Loop (horizontal
CONNECT), Counterfactual Frontier Spend Simulator (vertical DETERMINIZE, *winner*), an
FD-05 × CO-01 shared-ledger interface, and an FD-05 evaluation harness (EVALUATE) — are the
"structured search for the best adjacent capability" the root law demands. The proposal
that arrived as a duplicate leaves as a scored portfolio and a one-Part build contract.

### II.6 Failure modes, anti-patterns, quality gates, benchmarks (Part II)

**Failure mode F-4 — biggest-wins drift.** The optimizer ranks by raw value and the most
ambitious candidate wins, reintroducing bloat. *Diagnostic:* if the winner has the highest
numerator but not the highest ratio, the sort key is wrong. *Guard:* the sort key is `ratio`
first, `novelty` only as tiebreaker; the denominator can never be dropped.

**Failure mode F-5 — degenerate portfolio.** All candidates score identically because the
scoring features are too coarse. *Diagnostic:* if the top three ratios are equal to three
decimal places, the feature set has collapsed. *Guard:* the scoring blends axis, operation
class, and coverage so vertical/horizontal and deterministic/connective always separate.

**Anti-pattern A-3 — the padded portfolio.** Generating ten weak candidates to look
thorough. *Ecosystem evidence:* GK folded 40 candidates to 13 by merging, not by listing
all 40 — a portfolio's value is in its ranking, not its length; the engine caps the
rendered portfolio at five.

**Quality gates (binary).** `V-D2A-VERTICAL-GENERATED`: ≥ 3 vertical candidates, each with
numeric scores. `V-D2A-HORIZONTAL-GENERATED`: ≥ 3 horizontal candidates, each with numeric
scores. `V-D2A-PORTFOLIO-SCORED`: every candidate carries all 16 dimension scores.

**Benchmarks.** On the canonical proposal: portfolio size ≥ 6 (4 vertical + ≥ 2
horizontal), winning ratio ≈ 5.9, spread between top and bottom ratio ≥ 0.5 (a real
ranking, not a tie). Every candidate carries exactly 16 numeric scores — count them; the
gate fails at 15. Zero frontier tokens spent generating and scoring the entire portfolio.
Token ROI rule: the optimizer's own cost must remain a rounding error against the build it
governs — a scorer that needs a model call to rank candidates has become the waste it
polices. Model-portability rule: because every score is a deterministic function of the
candidate's structural features, the optimizer produces byte-identical rankings on any host
and under any model — it is model-independent by construction.

### II.7 The ratio formula worked with numbers

The optimizer's central claim — *best ratio, not biggest value* — is only credible if the
arithmetic is shown. Take two candidates from the canonical portfolio. The winning
**Counterfactual Frontier Spend Simulator** is a DETERMINIZE candidate: deterministic and
evaluative, riding FD-05's existing arbitrage data. Its positive scores land high on novelty
(≈ 8), compound effect (≈ 6), reuse potential (≈ 9), frontier-token savings (≈ 9),
deterministic conversion (≈ 9), portability (≈ 9), long-term value (≈ 8), measurability
(≈ 7) — a numerator near 90 across the thirteen positive dimensions. Its cost scores are low:
maintenance ≈ 3, complexity ≈ 3 (it is a Part on an existing dataset), regression risk ≈ 2
(pure additive simulation) — a denominator of 8. Ratio ≈ 90 / 8 ≈ 5.9.

Now take a hypothetical *"Universal Budget Meta-Framework"* — an ambitious new family that
would subsume FD-05, CO-01, PM-04, and FIOS-IRR under one roof. Its raw numerator might be
higher on integration value and long-term value (say 95), because it touches everything. But
its cost scores climb sharply: maintenance ≈ 8 (a whole family to keep alive), complexity ≈ 9
(it spans four sealed systems), regression risk ≈ 8 (it re-owns four covered surfaces).
Denominator 25. Ratio ≈ 95 / 25 ≈ 3.8. The meta-framework has the bigger *numerator* and
loses decisively on *ratio* — which is exactly the outcome the ecosystem needs, because the
meta-framework is the accretion, and the one-Part simulator is the delta. The formula is not a
decoration; it is the mathematical encoding of "deepen what exists, do not multiply it," and it
produces that verdict without a human having to feel the difference. The three cost dimensions
are never allowed to leave the denominator — a scorer that ranks by numerator alone would
recommend the meta-framework every time, and the ecosystem would fill with ambitious silos.

### II.8 Why two generators, not one

It would be simpler to have a single generator emit a flat list of candidates. The family
splits it deliberately into vertical (D2A-3) and horizontal (D2A-4) because the two axes
answer different questions and, left merged, one always crowds out the other. Vertical
candidates are cheaper, safer, and more immediately measurable — a single generator ranking
by ratio would return an all-vertical portfolio and the ecosystem would never build the
connective tissue between families, slowly fragmenting into deep-but-isolated silos. That is
the exact failure PM-01/PM-03 were built to prevent at the pane level, reappearing at the
architecture level. By guaranteeing at least three of each axis in the pool *before* scoring,
the family forces the anti-inflation rule "reinforce ≥ 1 vertical and ≥ 2 horizontal" to be
satisfiable, and forces the Owner to at least *see* the horizontal options even when a vertical
wins on ratio. The Cross-Session Budget Learning Loop in the canonical trace is a horizontal
candidate that did not win — but its presence in the rendered portfolio is what tells the Owner
that a cross-session compounding capability exists and could be built next. A merged generator
would have buried it beneath four cheaper verticals and it would never have been seen.

### II.9 Anti-patterns, edge cases, and portability of the scoring (Part II, extended)

**Anti-pattern A-5 — the vanity dimension.** Adding a seventeenth or eighteenth scoring
dimension to look thorough. *Ecosystem evidence:* CO-01's Work-Unit metric stayed a single
tied-to-reality number rather than a wall of decorative metrics; the sixteen D2A dimensions
are fixed and each maps to a real trade-off (value or cost). A dimension that changes no
ranking carries no information and is rejected. **Edge case E-1 — the tie.** When two
candidates share a ratio to three decimals, novelty breaks the tie; if novelty also ties, the
deterministic registry order decides, so the ranking is stable across runs (a requirement for
hermetic tests). **Edge case E-2 — the empty gap.** If D2A-2 returned no absent or partial
dimensions, the generators fall back to the full dimension list so the portfolio is never
empty — the root law forbids a duplicate verdict with no candidates. **Portability rule
(restated with teeth):** because every score is a pure function of the candidate's axis,
operation class, and the parent's coverage — with no learned weights and no model call — the
optimizer emits byte-identical rankings on Windows, Linux, or macOS, under Opus, Sonnet, or
Haiku. This is not an aspiration; it is verified by running the suite three times and diffing
the output, and it is the reason the optimizer can be trusted as infrastructure rather than as
a suggestion that drifts with the model of the day. The deeper point is that a ranking which
changes when the model changes is not a ranking at all — it is the model's opinion wearing a
number, and an ecosystem that made build decisions on such opinions would re-litigate every
choice each time a new model shipped. By grounding every score in structural features of the
candidate and the sealed registry, the optimizer produces a decision that is *the ecosystem's*,
stable across time and hardware, and therefore compoundable: last month's ranking and this
month's ranking of the same portfolio are identical, so a decision once made stays made and the
graph of past choices becomes a durable asset rather than a snapshot that decays.

---

## Part III — The Reinforcement Build Governor (D2A-6), the Anti-Inflation Contract, and the Operating Protocol

### III.1 Mission of the Build Governor

Everything upstream produces a *recommendation*. D2A-6 turns it into a *contract* — and its
central act is restraint. The governor's job is to choose the **minimal correct artifact**
for the recommended capability, because the most expensive mistake in a mature ecosystem is
building a whole new dataset (or module, or family) when a single Part, a single UKDL rule,
or a single eval would have carried the entire delta. The governor is the codified memory
of every family that got this right: FIOS shipping code + one doctrine instead of 17 prose
datasets; FD reporting 10 DO_NOT_BUILDs before writing a line; PM folding a whole
Reasoning-Dedup engine into one gate of PM-03.

### III.2 The 15 operations — the vocabulary of restraint

Every D2A recommendation resolves to **exactly one** of fifteen operations, and the choice
of operation *is* the choice of how much to build:

**DEEPEN, HARDEN, AUTOMATE, DETERMINIZE, EVALUATE, COMPRESS, GENERALIZE, SPECIALIZE** are
the reinforcement operations — they extend or strengthen an existing parent and almost
always resolve to a Part, an eval, a tool, or a rule, never a new family. **CONNECT** and
**COMPOSE** are the interface operations — they create a thin adapter between two families.
**PORT** makes an existing capability model- or host-independent. **MUTATE** proposes a
structural change to an existing dataset (the evolution_engine's territory, referenced not
duplicated). **REPLACE** and **RETIRE** are the subtractive operations — the ones a bloated
ecosystem forgets exist: sometimes the right move is to delete, not add. And **DO_NOT_BUILD**
is the operation that makes the whole family honest — it is always in scope, it is what the
engine recommended to its own proposal, and a governor that never emits it is not governing.

### III.3 The Anti-Inflation Contract — 10 binding rules

Before any BUILD CONTRACT is emitted, the governor evaluates ten rules, each a binary
predicate recorded in the contract:

1. **Extend before create** — every candidate must reinforce an existing parent; a
   free-floating new system is rejected.
2. **New needs demonstrable new capability** — a genuinely new artifact must clear a novelty
   floor (score ≥ 4); a low-novelty "new" thing is a rename.
3. **Rename is not novelty** — non-redundancy must clear a floor; the same idea renamed
   fails here.
4. **Reinforce ≥ 1 vertical and ≥ 2 horizontal** — a new system that does not strengthen its
   parent *and* connect to at least two others is a silo, and silos are debt.
5. **Declare what it retires** — every contract must name what becomes unnecessary; a build
   that retires nothing is pure accretion.
6. **Reduce cost, risk, or dependence** — the candidate must lower at least one of the three,
   measured (frontier-token savings ≥ 4 or regression-risk ≤ 4).
7. **Docs-only does not exist** — an artifact that only adds prose and changes no behaviour is
   not a build; it is a note.
8. **Part or rule before dataset** — the artifact ladder is climbed from the bottom; a full
   dataset requires an explicit escalation past Part, eval, tool, and interface.
9. **Compared against not building** — every candidate is scored against DO_NOT_BUILD; if
   doing nothing scores higher, nothing is built.
10. **More files is not success** — the contract that touches the fewest files to carry the
    delta wins; file count is a cost, never an achievement.

A BUILD CONTRACT records the pass/fail of all ten. `V-D2A-ANTIINFLATION` fails if any
contract omits the rule ledger. The canonical Token-Budget-Planner contract passes 10/10 —
because a new Part in FD-05 extends a parent, adds real behaviour, retires speculative Opus
calls, reduces dependence, sits low on the ladder, and touches one file.

### III.4 The artifact ladder and the minimal-artifact decision

The governor selects from an ordered ladder — **ukdl_rule < eval < dataset_part < benchmark
< interface < tool < gate < protocol < dataset** — and the decision is coverage-driven: the
more the parent already covers, the lighter the artifact. A ≥ 60 % duplicate resolves to a
Part (you are extending something deep). A horizontal winner resolves to an interface. An
EVALUATE operation resolves to an eval. A RETIRE/REPLACE resolves to a rule. A *full new
dataset* is reachable only for a genuinely-new, low-coverage, low-reuse candidate that has
climbed past every lighter rung — which, in a mature ecosystem, is rare, and is exactly why
the D2A family itself is one doctrine + one engine rather than six datasets.

### III.5 Contracts, decision rights, interfaces, and writeback

**Operative contract of D2A-6.** Input: the winning `Candidate` + the `DupeVerdict` +
`GapMap`. Output: a `BuildContract` — *build* (operation + what it improves), *artifact*
(a ladder rung), *lives_in* (a concrete disk location), *reinforces* (the parent(s)),
*does_not_duplicate* (the explicit non-duplication statement), *retires* (what becomes
unnecessary), *evaluated_by* (the done-gate), *operation* (one of 15), and the
*anti_inflation* ledger. **Decision rights:** the governor decides the artifact form and
the operation. **Non-decision rights:** it does **not** execute the build (propose-never-
build, Owner-gated, mirroring `evolution_engine` + `T-FIOS-EVOLUTION-LOCK-001`), it does
not write to any sealed dataset, and it does not choose the family for a NEW artifact
without Owner confirmation. **Writeback rule:** the engine writes nothing automatically; a
verdict is rendered for the Owner (or serialized to JSON for a caller), and only the Owner
promotes a BUILD CONTRACT into an actual Part/rule/tool — the same discipline that keeps
`pending_mutations.md` advisory.

### III.6 Interfaces with the existing stack

D2A-6 reads FD-03's destination taxonomy (8 homes) as the conceptual parent of its artifact
ladder and extends it with the explicit anti-inflation gate and the 15-operation vocabulary.
It references one_shot's compiler and spec_gate as prior art in scope-bounding. When a
verdict is promoted, the resulting Part/rule is indexed by Graphify (GK-03/04) as a node
with edges to its parent — so a future session navigates to the decision instead of
re-litigating it. When a build reduces frontier dependence, that reduction is reported
through CO-12's single instrument (never a parallel accountant), exactly as FIOS's token_irr
feeds CO-12.

### III.7 Failure modes, anti-patterns, edge cases, quality gates, benchmarks (Part III)

**Failure mode F-6 — dataset drift.** The governor recommends a full dataset when a Part
would carry the delta. *This is `T-D2A-ANTIINFLATION-VIOLATION-001`.* *Diagnostic:* if the
artifact is `dataset` while coverage ≥ 40 %, the ladder was skipped. *Guard:* rule 8 forces
a Part below the escalation threshold; the test `V-D2A-CONTRACT-MINIMAL` asserts the
canonical proposal resolves to a Part, not a dataset.

**Failure mode F-7 — the silent retire.** The governor recommends RETIRE/REPLACE but the
contract's `retires` field is empty. *Guard:* rule 5 requires a named retirement; a
subtractive operation with nothing named is incoherent.

**Edge cases.** *Empty proposal* → DEFER, never a raise (fail-open). *Proposal matching zero
families* → coverage 0, `is_duplicate=False`, NOVEL note, still routed to a minimal artifact
(a genuinely-new thing still gets the smallest correct form). *Proposal matching exactly one
family weakly* → low-confidence verdict surfaced with the NOVEL fallback. *Any internal
exception* → DEFER with the exception class named, never a crash and never a wrong block —
the governor of builds must never itself block a build by failing.

**Anti-pattern A-4 — the self-exempt governor.** A build-restraint system that exempts its
own family from the contract. *Ecosystem evidence:* the D2A Engine ran itself through the
pipeline at STOP #1 and returned "1 doctrine + 1 engine, not 6 datasets" — the family obeys
its own rule 8, or it has no standing to enforce it.

**Quality gates (binary).** `V-D2A-CONTRACT-MINIMAL`: the Build Governor selects the minimal
correct form (Part over dataset when coverage warrants). `V-D2A-ANTIINFLATION`: all 10 rules
recorded on every contract. `V-D2A-NO-DUPLICATE`: the engine's registry references real
sealed families and the doctrine declares its non-duplication of each — the family does not
duplicate CO/PM/GK/FD/FIOS. `V-D2A-DEPTH`: each Part of this dataset exceeds 2500 real words.
`V-D2A-NUMERIC-BENCHMARKS`: zero adjectives-without-numbers in any rubric.
`V-D2A-BASELINE`: the FD and FIOS suites still pass — no regression.

**Benchmarks.** The governor's decision is a single deterministic pass — zero frontier
tokens. On the canonical proposal it emits a 10/10 anti-inflation contract resolving to a
`dataset_part` in FD-05. Across a mix of proposals the governor's artifact distribution
should skew heavily toward the light end of the ladder (Part / rule / eval / interface); a
run where `dataset` is the modal recommendation is itself a signal the registry or
thresholds have drifted toward inflation and must be audited.

### III.8 The Operating Protocol — how a session uses D2A

1. **On any new-system or new-dataset proposal**, before building, run
   `modules.duplicate_to_advantage.run(Proposal(description, name))`. Cost: zero tokens,
   sub-millisecond.
2. **Read the DUPE VERDICT.** If `is_duplicate=False` and coverage is low, the proposal is
   genuinely new — proceed, but still take the minimal-artifact recommendation.
3. **If a duplicate is detected, do not stop** — read the REINFORCEMENT MAP and the
   CANDIDATE PORTFOLIO. The duplicate has become a coordinate.
4. **Inspect the RECOMMENDED ACTION and its ratio**, and the four runners-up.
5. **Read the BUILD CONTRACT** — its artifact rung, its operation, its 10/10 (or lower)
   anti-inflation ledger. If any rule fails, the contract tells you which and why.
6. **The Owner promotes** the contract into an actual Part / rule / tool / interface. The
   engine never writes it. Propose-never-build.
7. **The promoted artifact is indexed by Graphify** and its dependence-reduction reported
   through CO-12, so the decision compounds and is never re-litigated.

### III.9 Compression, portability, regression, done criteria, and upgrade path

**Compression & no-bloat rules.** The engine is ~450 lines carrying six stages; it must
never grow a seventh stage that duplicates a sealed family. The doctrine is three Parts; it
must never spawn five sibling datasets — that would be the exact inflation `PR-DUPLICATE-TO-
ADVANTAGE-001` and `T-D2A-ANTIINFLATION-VIOLATION-001` forbid. **Token ROI rule.** Every
D2A operation is deterministic Python: zero frontier tokens per verdict, forever. The moment
D2A needs a model call to reach a verdict, it has become the cost it governs. **Model
portability rule.** Every number the engine emits is a deterministic function of the
proposal and the sealed registry — byte-identical on any host, under any model, across the
Opus/Sonnet/Haiku ladder; this is what makes the tests hermetic ×3. **Regression tests
(conceptual).** The canonical proposal must always resolve to FD-05 + a Part + 10/10; the
FD (12/12) and FIOS (13/13) suites must remain green; the engine must never raise on any
input. **Done criteria (binary):** the engine runs, the doctrine's three Parts each exceed
2500 words, the Token-Budget-Planner trace is reproducible, every rubric carries numbers,
the anti-inflation contract is verified, `test_duplicate_to_advantage.py` passes ×3
hermetic, the two UKDL rules are appended, SCS C85 is sealed, and the push shows
`REMOTE_DELTA = 0 0`. **Upgrade path (measured milestones):** *M1* — a live PreToolUse/Stop
advisory hook that runs D2A automatically when a session declares an intent to build a new
dataset/module (the same staging discipline as FIOS's deferred kclaude preflight). *M2* —
feed promoted BUILD CONTRACTs back into the FAMILY_REGISTRY so the detector learns new
responsibilities as the ecosystem grows. *M3* — a cross-repo registry so the same proposal
is deduplicated across projects, riding GK-10's propagation transport. Each milestone is an
EXTEND of this engine, never a new family — because the D2A Engine, applied to its own
future, will keep returning the same verdict: *deepen what exists; do not multiply it.*

### III.10 Per-operation semantics — the 15, each with its trigger

The vocabulary is small on purpose, and each operation has a precise trigger so the governor's
choice is deterministic rather than a matter of taste. **DEEPEN** fires when an absent
capability sits directly beneath the parent — build the missing sub-layer. **HARDEN** fires on
an uncovered failure mode or a parent weakness — add the guard. **AUTOMATE** fires on a
still-manual process — remove the human step. **DETERMINIZE** fires on a frontier-required part
that could become a recipe — this is the highest-value operation because it directly reduces
future Opus dependence, and it is why the canonical winner is a DETERMINIZE. **EVALUATE** fires
on a missing eval — the capability exists but is unmeasured, so the artifact is a test, not a
feature. **COMPRESS** fires on bloat with low unique-token density — shrink without losing
capability, the evolution_engine's `compress` seen prospectively. **GENERALIZE** fires when a
missing interface would let a scoped capability serve more callers. **SPECIALIZE** fires when a
parent tries to be general where a scoped child is warranted — the mirror of GENERALIZE.
**CONNECT** and **COMPOSE** are the horizontal operations — CONNECT builds a direct interface,
COMPOSE arranges several systems into a pipeline. **PORT** fires when a capability is trapped on
one host or one model and could be made independent. **MUTATE** defers to the evolution_engine's
territory — a structural change to an existing dataset — and the governor references it rather
than performing it. **REPLACE** and **RETIRE** are the operations a growing system forgets: when
a new capability supersedes an old one, the old must be named for removal, not left to rot as
debt. And **DO_NOT_BUILD** is the operation that keeps the family honest — it is always a
candidate, it is compared against every proposal (rule 9), and it is precisely what the D2A
Engine recommended for five of its own six proposed prose datasets. An operation vocabulary
without a "do nothing" verb is a machine that can only add; the ecosystem already has enough of
those.

### III.11 The decision-rights ledger

Every stage of the pipeline has explicit decision rights and, more importantly, explicit
*non*-decision rights — because the most dangerous governor is one that quietly expands its own
authority. D2A-1 decides *what a proposal collides with*; it does not decide whether to build.
D2A-2 decides *which capability dimensions are open*; it does not decide what to build in them.
D2A-3/4 decide *what candidates exist*; they do not decide which wins. D2A-5 decides *the
ranking*; it does not decide the artifact. D2A-6 decides *the artifact form and the operation*;
it does not *execute*. And across the whole pipeline, one authority is reserved entirely for the
Owner: **promotion.** The engine proposes a BUILD CONTRACT; only the Owner turns that contract
into an actual Part, rule, tool, or interface. This is the same propose-never-apply discipline
that governs the FIOS evolution_engine (`T-FIOS-EVOLUTION-LOCK-001`), the cdio-standards-
librarian, and the graphify writeback agents — a deliberate, load-bearing pattern across the
Power Pack: automated systems that *analyze and recommend* are trusted; automated systems that
*mutate sealed artifacts on their own* are not permitted to exist. The D2A Engine can see the
whole board and name the best move, but it never moves the piece. That boundary is what lets it
run on every proposal without fear: the worst a wrong verdict can do is put a bad recommendation
in front of an Owner who declines it, never silently reshape the ecosystem. A governor that
could both judge and execute would be the single most dangerous component in the stack; a
governor that can only judge, and must hand every execution to a human, is safe to make
universal — and universal is the only scale at which an immune system works. This is the final
inversion the family asks the ecosystem to internalize: the value of the D2A Engine is not in
what it builds, because it builds nothing. Its value is in what it *stops* being built, and in
how precisely it redirects the energy that would have gone into a redundant system toward the
one adjacent capability that genuinely does not yet exist. Every family before it proved the
procedure by hand under pressure; this engine makes the procedure free, repeatable, and
honest — including honest about itself, which is why it ships as one doctrine and one engine
rather than the six datasets it was asked for. A duplicate detected is a frontier discovered.
That is the whole doctrine, and the engine is only its faithful, deterministic servant.
