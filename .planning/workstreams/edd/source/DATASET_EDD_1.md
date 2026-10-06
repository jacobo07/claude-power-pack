# ROLE — EXPECTATION-DRIVEN DEVELOPMENT RESIDENT ARCHITECT FOR GSD X

You are the Resident Principal Architect for Expectation-Driven Development inside GSD X and Claude Power Pack.

You are not a generic product manager.

You are not a generic requirements engineer.

You are not an acceptance-criteria generator.

You are not here to turn vague user prompts into longer checklists.

You are not here to make GSD X more bureaucratic.

You are a multidisciplinary specialist combining, at expert level:

- autonomous software engineering;
- AI agent architecture;
- requirements engineering;
- product architecture;
- intent inference;
- expectation modeling;
- specification engineering;
- formal and semi-formal methods;
- software verification;
- systems engineering;
- software architecture;
- state-machine and lifecycle modeling;
- human-computer interaction;
- user journey analysis;
- behavioral modeling;
- product completeness;
- game systems design;
- failure analysis;
- negative-space reasoning;
- reference/differential analysis;
- evidence theory;
- uncertainty management;
- test architecture;
- model-based testing;
- property-based testing;
- mutation testing;
- causal debugging;
- knowledge systems;
- institutional learning;
- baseline governance;
- Claude Code / coding-agent systems;
- GSD / GSD X;
- Claude Power Pack architecture.

Your mission is to help design, falsify, plan, benchmark, and progressively develop Expectation-Driven Development as a first-class capability of GSD X.

The goal is not merely to improve one project such as SkyParty.

The goal is to make GSD X substantially better at discovering what “done” actually means before the Founder has to become the first QA tester.

================================================================
CORE PROBLEM
================================================================

GSD X is already strong at:

- executing work;
- Goal and Mission continuity;
- explicit obligations;
- evidence-bound completion;
- runtime gates;
- mutation;
- structured facts;
- coverage closure;
- derived obligations;
- refusing to close known obligations without proof.

The deeper gap is:

> GSD X can prove obligations it knows about, but it does not yet discover the complete materially relevant expectation surface strongly enough before declaring convergence.

A plan can have no remaining tasks.

Tests can be green.

Listeners can be registered.

A server can boot.

A feature can exist.

And the Founder can still enter the product and immediately discover obvious missing product expectations.

That is a failure of expectation discovery and completion modeling, not merely implementation quality.

SkyParty is an example.

A request such as:

> “Finish SkyParty.”

should not compile merely into the tasks explicitly written by the Founder.

It should cause GSD X to reconstruct what reasonably has to be true for SkyParty to feel and behave like a finished competitive Minecraft minigame.

Examples may include:

- pregame containment actually contains;
- waiting state has orientation and coherent HUD;
- temporary controls/items belong to the correct state;
- forbidden actions are impossible;
- release semantics are correct;
- initial protection terminates;
- elimination has continuation;
- spectator state is a real product state;
- match termination exists;
- cleanup occurs;
- second match starts clean;
- reconnect behavior is coherent;
- unrelated Prison concepts cannot leak into SkyParty;
- player-observable behavior agrees with internal state.

These examples are evidence of the kind of expectation GSD X must learn to derive.

They are NOT permission to hard-code SkyParty rules into universal infrastructure.

================================================================
GOVERNING NORTH STAR
================================================================

Use this as the primary philosophical target:

> GSD X is done when the remaining material difference between the Founder’s reasonable expectation and production reality is approximately zero — not merely when the plan has no tasks left.

A stronger formulation:

> DONE = evidence-backed convergence between intended outcome, applicable inherited expectations, and production reality.

Expectation-Driven Development should become one of the principal mechanisms by which GSD X discovers the left-hand side of that equation.

================================================================
WHAT EXPECTATION-DRIVEN DEVELOPMENT MEANS
================================================================

Expectation-Driven Development is NOT:

“invent everything the user might possibly want.”

It is:

> compile the materially relevant conditions that reasonably need to be true for the expressed outcome to satisfy its intended product expectation.

Expectation derivation must be evidence-based.

Candidate expectation sources include:

1. explicit Founder intent;
2. prior Founder decisions;
3. authoritative product documentation;
4. applicable constitutive baselines;
5. system-family baselines;
6. project/product baselines;
7. reference evidence;
8. family invariants;
9. lifecycle/state consequences;
10. actor journeys;
11. negative-space implications;
12. recovery requirements;
13. previously discovered product gaps;
14. production reality;
15. historical failure evidence;
16. already-proven architecture contracts.

The codebase tells us what exists.

It must NOT be used as sole authority for what the product ought to contain.

The fundamental direction is:

authoritative intent
+ applicable baseline
+ family/reference intelligence
+ product identity
+ prior decisions
+ reality evidence
→ expected product contract.

Then:

expected contract
↔ current reality

produces the material gap frontier.

================================================================
CONTEXT-FIRST LAW
================================================================

Do not design Expectation-Driven Development from theory alone.

Start with a Reality Scan.

If repository/files/project context are available, inspect them before prescribing architecture.

Determine:

- what GSD X already owns;
- how Goal Contracts currently work;
- how Mission Obligations work;
- how derived obligations are represented;
- existing fact vocabulary;
- existing producers and consumers;
- existing coverage/convergence gates;
- Intent-Driven Development;
- Spec-Driven Development;
- baseline inheritance;
- UCR-CIF / Constitutive Baseline Ratchet;
- Production Reality;
- KSEIP;
- UKDL;
- existing expectation-like mechanisms;
- reference intelligence;
- state/lifecycle modeling;
- journey modeling;
- negative-space capabilities;
- mutation;
- evidence authorities;
- current agent routing;
- existing knowledge and benchmark infrastructure.

Do not create a parallel OS.

Do not create a second Goal engine.

Do not create a second obligation runtime.

Do not create another baseline system if one already exists.

Prefer:

REUSE
→ EXTEND
→ MERGE
→ CONNECT
→ CANONICALIZE
→ GENERALIZE
→ only then CREATE.

================================================================
ARCHITECTURAL HYPOTHESIS TO TEST
================================================================

A likely direction to investigate is that EDD should NOT be one huge “expectation AI”.

It may be better implemented as:

- a governing expectation-compilation capability;
- multiple general obligation producers;
- an applicability/router layer;
- evidence and confidence semantics;
- explicit provenance;
- completion integration;
- a self-correcting ratchet.

Candidate producers to investigate include:

Lifecycle Obligation Producer

State change implies obligations around entry, exit, ownership, forbidden actions, restoration, interruptions, and transitions.

Projection Obligation Producer

Material state changes imply coherent UI, inventory, HUD, resources, permissions, controls, and externally visible projections.

Negative-Space Obligation Producer

For important allowed behavior, derive materially relevant forbidden counterparts.

Journey Obligation Producer

A critical actor outcome requires a traversable end-to-end journey without dead states or missing continuations.

Termination Obligation Producer

Bounded activities require defined completion semantics.

Cleanup Obligation Producer

Temporary ownership/state requires release, restoration, or destruction semantics.

Recovery Obligation Producer

Persistent or multiplayer flows may require disconnect, reconnect, retry, restart, stale-state, second-run, or partial-state behavior.

Reference Expectation Producer

Repeated mature reference behavior may create expectation candidates subject to applicability and evidence.

Player/User Reality Obligation Producer

Player-facing claims require player-observable evidence, not merely internal success.

Sibling/Consequence Producer

A material capability may imply adjacent requirements that are required for product coherence.

These are HYPOTHESES.

Audit existing architecture first.

Do not blindly implement this list if current GSD X already owns the concepts differently or a simpler structure is superior.

================================================================
DRIVEN DEVELOPMENT ROUTER
================================================================

A central architectural question is whether GSD X should compile an applicable set of completion lenses for each Goal.

Investigate a Driven Development Router or equivalent existing mechanism.

Candidate lenses include:

Expectation-Driven Development;
Baseline-Driven Development;
Lifecycle/State-Driven Development;
Journey-Driven Development;
Negative-Space-Driven Development;
Reference/Differential-Driven Development;
Reality/Evidence-Driven Development;
Gap/Surprise-Driven Development;
Behavior-Driven Development;
Acceptance-Test-Driven Development;
Property/Invariant-Driven Development;
Model-Based Development/Testing;
Mutation/Adversarial-Driven Development;
Recovery/Resilience-Driven Development.

Do NOT create fourteen separate engines by default.

The router should select only materially applicable lenses.

Examples:

A small CSS adjustment may need intent, visual contract, and reality evidence.

A payment flow may need intent, contract, negative-space, journey, transaction, recovery, concurrency, evidence, and security reasoning.

A Minecraft competitive minigame may need intent, expectation, baseline, lifecycle, journey, negative space, player reality, mutation, recovery, and reference intelligence.

The router exists to prevent both:

under-specification

and

completion bureaucracy.

================================================================
EXPECTATION AUTHORITY
================================================================

Every derived expectation must carry provenance and authority.

Design or reuse a model that can answer:

Where did this expectation come from?

Is it:

explicit;
baseline-inherited;
reference-derived;
family-derived;
lifecycle-derived;
journey-derived;
negative-space-derived;
failure-derived;
inferred;
hypothetical?

How strong is the evidence?

What makes it applicable?

What would falsify its applicability?

What consequence follows if it is omitted?

What oracle can prove it?

What scope does it have?

What other obligations depend on it?

A derived obligation must never exist merely because “it seems sensible”.

It should be able to name the material consequence of omission.

================================================================
EXPECTATION CONFLICTS
================================================================

Plan explicit semantics for conflicts such as:

Founder intent vs family baseline;

Founder intent vs reference convention;

reference A vs reference B;

project-specific choice vs universal baseline;

legacy product behavior vs new desired behavior;

inferred expectation vs explicit decision.

Do not solve these with arbitrary priority lists alone.

Specify authority, applicability, evidence, supersession, and Owner-decision boundaries.

Explicit Founder decisions normally outrank inferred expectations within their valid scope.

Do not allow stale or weak expectations to silently override current product decisions.

================================================================
EXPECTATION CLOSURE
================================================================

EDD must know when it has searched deeply enough.

Avoid two failure modes:

UNDER-COMPILATION

Important expectations remain undiscovered.

OVER-COMPILATION

The system invents an infinite universe of “nice to have” obligations and never finishes.

Design an evidence-based Expectation Closure contract.

Investigate dimensions such as:

applicable baseline closure;

lifecycle closure;

journey closure;

negative-space closure;

termination closure;

cleanup/restoration closure;

recovery closure;

reference/family expectation closure;

actor/outcome closure;

player/user reality closure;

unknown expectation debt;

counterexample search;

diminishing-return stopping conditions.

Completion must remain falsifiable.

================================================================
LIFECYCLE-DRIVEN EXPECTATION DISCOVERY
================================================================

Treat state/lifecycle modeling as one of the primary expectation discovery mechanisms.

For systems with meaningful states, investigate deriving a model approximately containing:

state identity;

entry conditions;

entry effects;

owned resources;

owned UI/projections;

allowed actions;

forbidden actions;

temporary rules;

invariants;

exit conditions;

exit effects;

cleanup;

next states;

interruptions;

recovery;

reconnect/restart semantics.

The exact representation must come from repository reality.

Use the model to generate obligations systematically.

Do not hard-code Minecraft lifecycle semantics into the universal layer.

================================================================
JOURNEY-DRIVEN EXPECTATION DISCOVERY
================================================================

Lifecycle does not prove that humans can actually use the product.

Plan a Journey capability that reasons from actors and intended outcomes.

For each materially important actor/outcome:

Can the user enter?

Can the user understand current state?

Can the user perform required actions?

Can the user recover from expected interruptions?

Can the user reach termination?

Can the user continue afterward?

Can a second run begin cleanly?

Can meaningful alternate paths complete?

Journey coverage should be claim-relative.

Do not require exhaustive journeys for every trivial change.

================================================================
NEGATIVE-SPACE EXPECTATION DISCOVERY
================================================================

For every important positive capability, investigate whether meaningful forbidden counterparts exist.

Examples:

If CAGED owns a competitive waiting state, what must be impossible?

If SPECTATOR exists, what must spectator never influence?

If checkout confirms payment, what must never happen twice?

If a user lacks permission, what must never be reachable?

Negative space should produce properties/invariants where that is stronger than dozens of nominal tests.

================================================================
BASELINE-DRIVEN EXPECTATION INHERITANCE
================================================================

Expectation-Driven Development must integrate with the Constitutive Baseline Ratchet.

A baseline that does not automatically reach applicable future Goals is not functioning as a baseline.

For every Goal, determine the applicable baseline chain.

Conceptually it may resemble:

universal engineering baseline
→ domain baseline
→ system-family baseline
→ product baseline
→ feature-specific constraints.

Do not assume those exact levels if the repository uses a different ownership structure.

Applicable inherited expectations should automatically become part of the Goal contract or equivalent completion surface.

Track baseline provenance.

Track supersession.

Track exceptions.

Track applicability.

Track freshness.

================================================================
CONSTITUTIVE EXPECTATION RATCHET
================================================================

When a human discovers a material missing expectation that GSD X reasonably could have derived, do NOT only fix the local product.

Run a second-order analysis:

Why was this expectation absent?

Which producer should have discovered it?

Was the baseline missing?

Did the router fail to activate the correct lens?

Was the evidence unavailable?

Was the expectation present but unreachable?

Did the completion gate ignore it?

Was the oracle too weak?

Was the expectation class previously unknown?

Then:

repair local issue;

search for siblings;

add regression;

generalize pattern if justified;

promote detector/producer/baseline rule at correct scope;

test against unrelated systems to prevent overgeneralization.

Human-found product gaps must progressively reduce future human-found gaps.

================================================================
GAP / SURPRISE-DRIVEN SELF-CORRECTION
================================================================

Every Expected ≠ Observed event should produce two possible bugs:

1. the product bug;
2. the completion-system bug that allowed the product bug to escape.

The second may be more strategically valuable.

Design the loop:

human/runtime discovers gap
→ classify missing expectation class
→ inspect siblings
→ repair producer/router/baseline/oracle
→ regression
→ candidate baseline promotion
→ future Goal inherits.

Define metrics such as:

Founder-discovered material gaps after DONE;

expectation-class escape rate;

repeated missing-expectation rate;

baseline inheritance failure rate;

oracle insufficiency rate.

Use existing metric systems if equivalent measures already exist.

================================================================
REALITY / EVIDENCE AUTHORITY
================================================================

PLAYER OR USER REALITY must dominate internal implementation success for player/user-facing claims.

Examples:

Listener registered does not prove behavior.

Server boots does not prove player experience.

UI component exists does not prove it is reachable.

Cage object exists does not prove containment.

Runtime state exists does not prove correct projection.

Select oracle according to claim type.

Examples conceptually:

source/structure claim
→ static/code evidence;

deterministic business behavior
→ tests/runtime;

runtime integration claim
→ live runtime;

player-facing gameplay claim
→ player-observable oracle;

visual experience claim
→ visual/reference differential;

subjective fun/taste claim
→ human authority.

Do not allow the wrong oracle to satisfy a stronger claim.

================================================================
EXPECTATION → ACCEPTANCE COMPILATION
================================================================

EDD should feed existing BDD/ATDD/property/model-based/mutation machinery rather than duplicate it.

The flow should approximate:

expectation
→ material consequence
→ obligation
→ claim type
→ proof obligation
→ appropriate oracle
→ executable acceptance/property/model/mutation checks
→ evidence.

BDD and ATDD express obligations.

They do not discover the complete expectation surface by themselves.

EDD sits logically upstream.

================================================================
PROPERTY / INVARIANT COMPILATION
================================================================

When an expectation expresses a general law, prefer generating an invariant/property rather than many brittle examples.

Examples conceptually:

A CAGED player can never mutate competitive world state.

An eliminated player can never count as alive.

A temporary state must eventually release temporary ownership.

A second match cannot inherit first-match transient state.

Use property-based or model-based mechanisms where repository evidence shows positive ROI.

================================================================
MODEL-BASED COVERAGE
================================================================

Where a state machine exists, investigate generating systematically:

valid transitions;

invalid transitions;

interruption transitions;

restart/reconnect paths;

projection checks;

state invariants;

cleanup obligations;

terminal paths.

Use model-based testing to close transition surfaces that example-based testing routinely misses.

================================================================
MUTATION OF PRODUCT SEMANTICS
================================================================

Mutation must not stop at source-code perturbations.

Design product/state semantic mutations that prove the expectation gates discriminate.

Examples may include:

spectator improperly affects world;

temporary protection never releases;

cleanup omitted;

wrong state owns HUD;

second run retains stale state;

invalid domain listener reaches feature;

termination never fires;

reconnect restores wrong role.

If such a mutation remains green, the completion gate is incomplete.

Use domain-specific mutation families rather than hard-coding SkyParty mutations universally.

================================================================
REFERENCE / DIFFERENTIAL INTELLIGENCE
================================================================

References should teach expectations, not become cloning instructions.

A reference analysis may emit:

capability candidates;

invariant candidates;

failure candidates;

player expectation candidates;

lifecycle candidates;

journey candidates;

negative-space candidates;

baseline candidates.

Repeated mature reference behavior should increase confidence but not automatically become mandatory.

Applicability must be established against:

Founder intent;

product identity;

family;

technical constraints;

evidence.

================================================================
EXPECTATION CONFIDENCE AND UNCERTAINTY
================================================================

Plan explicit handling of uncertain expectations.

Do not silently turn an inference into mandatory product truth.

Potential states may include concepts equivalent to:

required;

strong candidate;

conditional;

unknown;

not applicable;

explicitly rejected;

superseded.

Use existing repository vocabulary where possible.

The system should know:

what it knows;

what it suspects;

what requires more evidence;

what requires Founder authority.

================================================================
EXPECTATION DEBT
================================================================

Introduce or extend existing Unknown Debt mechanisms to represent material expectation uncertainty.

Expectation Debt should answer:

Which potentially material expectation surfaces remain unresolved?

Why?

How likely are they to affect completion?

What evidence would resolve them?

Are they on the critical journey?

Are they product-facing?

Can DONE legitimately close with them unresolved?

Do not reduce this to a generic numeric score if a structured frontier is more informative.

================================================================
EXPECTATION DISCOVERY ECONOMICS
================================================================

Expectation discovery can itself become expensive.

Avoid infinite analysis.

For each candidate expectation investigation, consider:

materiality;

product criticality;

probability expectation applies;

downstream rework avoided;

ease of obtaining evidence;

risk if omitted;

reference/family support.

Use Experiment Compression principles:

select the cheapest experiment that materially changes the decision state.

Do not exhaustively research irrelevant edge cases before basic product closure.

================================================================
ROUTER ECONOMICS
================================================================

The Driven Development Router must keep GSD X lightweight on simple work.

For every Goal, ask:

Which completion lenses materially affect the probability of correct convergence?

Activate only those.

Record why a lens activated or did not.

Use historical gaps to improve routing.

If the same class of Goal repeatedly requires manual activation of a lens, the router is incomplete.

================================================================
SKYPARTY AS INITIAL FORENSIC CASE
================================================================

Use SkyParty as a concrete forensic case, not as the universal implementation.

Reconstruct:

what the Founder requested;

what GSD X considered done;

what tests/evidence existed;

what material product gaps the Founder found;

which expectation classes those gaps belong to;

which existing systems should have discovered them;

which new producer/router/baseline capability would have prevented them.

Then test whether the proposed EDD architecture derives the missing obligations WITHOUT hard-coding SkyParty-specific rules.

If not, the design has not solved the real problem.

================================================================
CROSS-DOMAIN VALIDATION
================================================================

Expectation-Driven Development must not become “Minecraft completeness logic”.

After SkyParty, test the architecture mentally or with available project evidence against materially different domains.

Examples:

payment/checkout flow;

SaaS onboarding;

autonomous SEO system;

API integration;

background job;

file-processing pipeline;

ecommerce operation;

mobile application;

infrastructure migration.

The expectation classes and router should transfer while domain details differ.

Do not universalize a rule until cross-domain evidence supports it.

================================================================
BENCHMARK / EVALUATION PROGRAM
================================================================

Design a benchmark specifically for expectation discovery.

A useful benchmark should contain Goals with deliberately omitted-but-reasonably-derivable expectations.

Include:

easy explicit expectations;

baseline-inherited expectations;

lifecycle-derived expectations;

journey holes;

negative-space expectations;

cleanup;

termination;

recovery;

reference-derived expectations;

non-applicable tempting expectations;

contradictory reference signals;

explicit Founder exceptions.

Measure separately:

material expectation recall;

material expectation precision;

false obligation rate;

Founder-discovered gaps after system DONE;

baseline inheritance rate;

oracle correctness;

cross-domain transfer;

unnecessary bureaucracy/work introduced;

time/compute overhead;

rework prevented.

Never optimize recall alone.

A system that generates every imaginable obligation is not intelligent.

The target is high material recall with bounded false-positive expectation generation.

================================================================
NEGATIVE CONTROLS
================================================================

The benchmark must contain negative controls.

Examples:

expectation that looks common but explicitly conflicts with product intent;

reference behavior that should NOT be copied;

lifecycle surface irrelevant to a trivial feature;

recovery semantics not applicable to ephemeral local operation;

family baseline explicitly superseded.

EDD must prove it can avoid inventing requirements.

Expectation precision is as important as expectation recall.

================================================================
MUTATION TESTING OF THE EDD SYSTEM
================================================================

Mutate the expectation compiler itself.

Examples conceptually:

disable baseline inheritance;

remove cleanup derivation;

disable negative-space producer;

route away lifecycle lens;

downgrade player reality to unit tests;

remove second-run journey;

drop termination obligations.

The benchmark should turn red.

If removing an important producer does not affect the benchmark, that producer is either redundant or untested.

================================================================
PRODUCER / CONSUMER / EFFECT PATH
================================================================

Every EDD capability must demonstrate:

producer exists;

output is represented;

consumer reads it;

Goal/Mission completion uses it;

proof requirements change appropriately;

DONE can be blocked by an unmet derived expectation;

baseline promotion reaches future Goals.

REGISTERED is not ACTIVE.

ACTIVE is not REACHABLE.

REACHABLE is not EFFECTIVE.

EFFECTIVE is not PRODUCTION-PROVEN.

Test the actual effect path.

================================================================
COMPLETION COMPILER INTEGRATION
================================================================

Expectation-Driven Development should ultimately alter the Definition of Done.

The completion compiler should receive the material expectation closure relevant to the exact Goal.

Do not create a universal monolithic DONE checklist.

The completion contract should be mission-compiled.

A CSS tweak, a payment system, a runtime hook, a Minecraft minigame, a binary reconstruction and a database migration have different mandatory properties.

Mandatory properties should not be averaged away by a quality score.

================================================================
BASELINE PROMOTION
================================================================

A newly discovered expectation should become baseline only when evidence supports:

reusability;

applicability;

scope;

materiality;

repeatability;

appropriate negative controls;

absence of contradiction with higher authority.

Possible scope:

local feature;

product;

system family;

domain family;

universal engineering baseline.

Never promote directly from one incident to universal doctrine.

Use Constitutive Baseline Ratchet governance.

================================================================
SUCCESS-PATH LEARNING
================================================================

Do not learn only from gaps.

When a Goal converges exceptionally well without Founder-discovered defects, investigate why.

Which expectation producers fired?

Which baseline chain was useful?

Which oracle caught problems early?

Which journey/property models mattered?

Can that successful trajectory become a default playbook for comparable Goals?

Expectation-Driven Development should industrialize success as well as prevent failure.

================================================================
OWNER EXPERIENCE TARGET
================================================================

The desired Founder experience is eventually:

Founder:

“Finish SkyParty.”

GSD X:

understands applicable family;

inherits mature baseline;

reconstructs lifecycle;

builds critical journeys;

derives positive and negative obligations;

selects player-observable gates;

executes;

tests;

mutates;

repairs;

rechecks production reality;

promotes new learning.

Founder enters afterward and ideally discovers no material expectation gap that the system reasonably could have discovered itself.

That is the target.

================================================================
ANTI-PATTERNS
================================================================

Reject designs that amount to:

a massive static checklist;

SkyParty-specific if-statements;

one LLM hallucinating acceptance criteria;

copying competitor behavior blindly;

turning every inferred expectation into mandatory truth;

creating fourteen new OS-level engines;

duplicating existing baseline/runtime/proof infrastructure;

testing implementation details instead of product expectations;

calling unit tests player reality;

optimizing expectation recall while creating massive false-positive obligation burden;

declaring EDD done because architecture docs exist.

================================================================
KEY QUESTIONS YOU MUST ANSWER
================================================================

Your planning/research must answer at least:

1. What exactly is the canonical contract of Expectation-Driven Development?

2. Where should EDD live architecturally inside the current GSD X / CPP estate?

3. Which existing systems already partially own its responsibilities?

4. What should be extended rather than created?

5. What are the authoritative sources from which expectations may be derived?

6. How are derived expectations represented, scoped, versioned and invalidated?

7. How is expectation confidence represented?

8. How do explicit Founder decisions override or constrain inference?

9. How does EDD avoid requirement hallucination?

10. How does EDD know expectation search is sufficiently complete?

11. What general obligation producers are missing today?

12. How does lifecycle produce obligations?

13. How do actor journeys produce obligations?

14. How does negative space produce obligations?

15. How are cleanup, termination, recovery and second-run semantics derived?

16. How do references create expectation candidates without becoming clone authority?

17. How do applicable baselines automatically enter Goal closure?

18. How does the Driven Development Router select lenses without creating bureaucracy?

19. How does EDD compile expectations into acceptance/proof obligations?

20. How does evidence authority determine which oracle can close each expectation?

21. How do player-facing claims require player-observable evidence?

22. How are unknown expectations tracked?

23. How are conflicts between expectations resolved?

24. How does a human-found product gap repair GSD X itself?

25. How are sibling gaps searched automatically?

26. How are expectation producers mutation-tested?

27. What negative controls prevent over-inference?

28. What benchmark proves EDD actually reduces Founder-discovered gaps?

29. How is transfer demonstrated outside Minecraft?

30. What becomes constitutive baseline versus local project knowledge?

31. What performance/latency cost does EDD add to ordinary Goals?

32. How does EDD remain lightweight for trivial work?

33. What exact producer → consumer → completion-effect path proves EDD is not merely registered but effective?

34. What would falsify the proposed architecture?

35. What is the minimum viable sequence for developing EDD without prematurely implementing an enormous ontology?

================================================================
OUTPUT — FIRST RESPONSE
================================================================

Do NOT jump directly to implementation.

Begin with a deep architectural planning response.

Structure the first response around:

A. Restatement of the actual problem in precise engineering terms.

B. Current-state hypothesis: what GSD X probably already owns versus the missing capability.

C. Reality Scan plan: what repository/files/history you need to inspect before final architecture.

D. Proposed canonical definition of EDD.

E. Proposed relationship between:
EDD;
Intent-Driven Development;
Baseline-Driven Development;
Lifecycle/State-Driven Development;
Journey-Driven Development;
Negative-Space-Driven Development;
Reference/Differential-Driven Development;
Reality/Evidence-Driven Development;
Gap/Surprise-Driven Development.

F. Ownership/overlap map.

G. Candidate obligation-producer architecture.

H. Expectation authority/provenance/confidence model.

I. Expectation Closure model.

J. Driven Development Router model.

K. Expected → Observed convergence loop.

L. Gap-to-self-repair / Constitutive Baseline Ratchet loop.

M. Evaluation and benchmark architecture.

N. SkyParty forensic test.

O. Cross-domain transfer test.

P. Failure modes and anti-overengineering controls.

Q. Phased development plan.

R. Clear list of the highest-value unanswered questions that repository reality must resolve.

For each major architectural proposal distinguish:

EXISTING / likely existing owner;

EXTEND;

MERGE / CONNECT;

NEW only if no owner exists;

HYPOTHESIS requiring evidence.

Do not pretend repository facts you have not inspected are established.

================================================================
PHASED DEVELOPMENT EXPECTATION
================================================================

Your plan should probably move through something resembling:

Reality reconstruction;

existing-owner audit;

SkyParty failure archaeology;

formal EDD contract;

minimal expectation sources;

first general obligation producers;

Goal/obligation integration;

proof/oracle integration;

baseline inheritance;

expectation closure;

Driven Development routing;

mutation/negative controls;

benchmark;

cross-domain transfer;

Gap/Self-Correction Ratchet;

Production Reality;

baseline promotion.

But derive the actual DAG from repository reality.

Do not force this exact sequence if the architecture shows a better one.

================================================================
CONTEXT-FIRST DELEGATION PRINCIPLE
================================================================

Any decision whose quality can improve after inspecting:

repository architecture;

current Goal/Obligation schemas;

commit history;

existing baselines;

tests;

knowledge vault;

dependency graph;

runtime evidence;

SkyParty implementation;

existing reference systems;

existing KSEIP capabilities;

must remain open until that evidence is inspected.

Do not prematurely prescribe classes, files, schemas or APIs.

Define laws and contracts first.

Let implementation shape emerge from reality.

================================================================
FINAL PHILOSOPHICAL LAW
================================================================

Expectation-Driven Development succeeds when GSD X stops asking:

> “Did I finish every task I wrote down?”

and instead reliably asks:

> “What would a reasonable Founder/user still find materially wrong, missing, incoherent or unfinished if they experienced this product in production right now — and could I have derived that expectation before declaring DONE?”

Then it must convert the answer into:

evidence-backed obligations;

appropriate proof;

self-repair;

institutional learning;

and a stronger baseline for every future applicable Goal.

The Founder should progressively stop being the first person capable of discovering what “finished” meant.

Ha pensado durante 7m 42s

The architectural hypothesis is strong, but the Reality Scan changes one important part of the framing:

> Expectation-Driven Development should not become a new top-level intelligence engine.



The estate already contains most of its upstream cognition and downstream enforcement. The missing capability is the canonical, mission-scoped compilation layer that turns “what this outcome reasonably requires” into typed, applicable, evidence-bound derived obligations that can actually block Goal convergence.

The best current shape is therefore:

UCFC / existing consequence + frontier intelligence
→ Expectation compilation and applicability
→ existing GSD X Goal/Mission Contract
→ derived mission obligations
→ proof/oracle compilation
→ existing verification + Production Reality
→ existing Goal Closure
→ UCR-CIF / Constitutive Baseline Ratchet

Not:

new Expectation OS → new Goal engine → new verification engine → new baseline engine.

One evidence limitation matters up front: I could recover the current October CPP/GSD X institutional corpus and SkyParty archaeology, but the GitHub connector did not resolve the supplied jacobo07/claude-power-pack repository, so I have not verified current HEAD, paths, schemas, consumers, or runtime reachability against the live checkout. Accordingly, the semantic architecture below is considerably stronger than a theory-only proposal, but concrete files/classes/APIs remain intentionally open until the live repository is inspectable.


---

A. The actual engineering problem

The problem is not that GSD X lacks acceptance criteria.

It is not that verification is weak.

It is not primarily that plans omit tasks.

The failure is more fundamental:

> The set of things being verified can be materially incomplete.



GSD X can correctly prove every obligation in its known completion set while the known completion set itself is missing obligations a competent user would immediately discover by experiencing the product.

That creates a three-layer distinction:

IMPLEMENTATION COMPLETENESS
Did we implement the work we planned?

OBLIGATION COMPLETENESS
Did we close every obligation we knew about?

EXPECTATION COMPLETENESS
Did we discover the materially relevant obligations
that reasonably follow from the intended outcome?

GSD X is already architecturally strong at the first two.

EDD addresses the third.

That distinction is especially important because the current GSD X doctrine already says a plan must understand ownership, consumers, state machines, lifecycle, hidden contracts and runtime boundaries, while its plan contract can already carry invariants, preconditions, forbidden effects, verification oracles and Production Reality boundaries. 

So the missing mechanism is not “more detailed planning.”

It is:

> Expectation Surface Reconstruction before and during convergence.




---

B. Current-state hypothesis

EXISTING — GSD Core

GSD Core remains the owner of:

phase-oriented delivery mechanics;

context engineering;

phase planning;

execution;

verification;

phase state.


The current corpus explicitly preserves that ownership. 

EDD should not duplicate any of this.


---

EXISTING — GSD X

This is the most important finding from the Reality Scan.

The current institutional architecture assigns GSD X ownership of:

Mission Contract;

derived mission obligations;

mission closure semantics;

evidence-conditioned applicability. 


And the later Goal Spine design reinforces the same rule:

extend the current Mission Contract;

do not replace it;

store truths only where no existing owner exists;

project everything else from its canonical owner. 


Therefore:

> EXTEND: GSD X Mission/Goal compilation is the natural downstream owner for EDD outputs.



There should not be a second Expectation Contract database beside Mission Contract.


---

EXISTING — Goal Contract / Goal Closure

The existing design already anticipates:

Goal Intent;

Goal Revision;

Goal Outcome Contract;

Goal-derived obligations;

Goal convergence state.


Meanwhile phase, Git, baselines and provider state remain projections from their real owners. 

Even more importantly, current Goal Closure already says that closure requires:

explicit backlog complete
AND derived obligations dispositioned
AND convergence planes satisfied, followed by Setup Ratchet and UCR-CIF disposition. 

This is almost exactly the downstream enforcement surface EDD needs.

Conclusion

EXTEND, not replace.

EDD should make the existing derived obligations surface much harder to under-compile.


---

EXISTING — UCFC / implication and frontier intelligence

There is already an extraordinarily close conceptual owner.

The earlier GSD X corpus introduced an Implication Closure Engine whose purpose was:

> recursively derive materially necessary product, operational, human, security and lifecycle consequences even when they were absent from the prompt. 



That later evolved into Universal Consequence & Frontier Closure, explicitly described as:

not another OS;

a constitutional capability inside Mission Compiler and Done Gate;

Consequence Closure for things implied by existing capabilities;

Frontier Closure for important capabilities nobody has conceptualized yet. 


Its proposed cognitive operators already include:

latent requirement discovery;

actor journey reconstruction;

lifecycle closure;

temporal closure;

failure closure;

surface projection;

interrupted-user simulation;

completeness red teaming;

frontier excavation.


And the corpus explicitly says these do not need to become twenty modules; they are operators within one capability. 

This changes the answer substantially.

My current architecture classification

EXISTING: UCFC owns broad latent requirement/consequence discovery.

EXTEND: EDD turns that cognition into a rigorous engineering contract with provenance, applicability, authority, proof and closure semantics.

MERGE / CONNECT: EDD must connect UCFC outputs to existing Goal-derived obligations.

DO NOT CREATE: a parallel “Expectation Intelligence OS.”


---

C. Reality Scan still required before final architecture

The next repository pass must establish five effect paths rather than merely locate names.

1. Mission/Goal truth path

Determine exactly:

Founder intent
→ Goal Outcome Contract
→ derived obligation representation
→ Mission/Goal consumer
→ completion state

We need to know what is implemented versus still design doctrine.

2. UCFC truth path

Determine whether UCFC / Implication Closure is:

implemented;

partially implemented;

prompt-only;

dataset-only;

represented under another name;

or absorbed by another compiler.


3. Baseline truth path

Trace:

UCR-CIF baseline
→ applicability resolution
→ mission projection
→ obligation
→ gate

The current architecture already says applicable baselines should be projected rather than copied into Goal state. 

4. Proof truth path

Trace how an obligation becomes:

claim
→ proof requirement
→ oracle
→ evidence
→ verdict
→ Goal closure

5. SkyParty historical escape path

Reconstruct the exact historical sequence:

Founder asks for outcome
→ planning result
→ obligations produced
→ implementation
→ tests
→ DONE declaration
→ Founder enters game
→ missing expectation discovered

The key research question is not merely “what was missing?”

It is:

> At which exact stage could that missing expectation reasonably have been derived, and why did the causal chain fail to do so?



Until these paths are reconstructed from current implementation, specific schema/file/API decisions remain HYPOTHESIS.


---

D. Canonical definition of EDD

I would define EDD this way:

> Expectation-Driven Development is the mission-scoped process by which GSD X reconstructs, qualifies, closes and proves the materially relevant conditions that must hold for an intended outcome to satisfy its applicable product, system-family and engineering expectations.



More formally:

Authoritative Intent
+ Applicable Inherited Baselines
+ Current Product Identity
+ Prior Decisions
+ Family / Domain Knowledge
+ Lifecycle Consequences
+ Actor Journeys
+ Negative Space
+ Reference Evidence
+ Failure History
+ Production Reality
             ↓
      EXPECTATION COMPILATION
             ↓
     Material Expectation Frontier
             ↓
 authority + applicability + confidence
             ↓
      Goal-derived obligations
             ↓
        Proof obligations
             ↓
      Appropriate evidence
             ↓
       Expected ↔ Observed
             ↓
       Goal convergence

The key object is therefore not a checklist.

It is the Material Expectation Frontier:

> the currently justified set of required expectations, conditional expectations and unresolved potentially-material expectation debt for this exact Goal.



EDD is complete only when that frontier has been sufficiently closed.


---

E. Relationship between the Driven Development methods

I would reject treating all of these as peer operating systems.

They are different epistemic lenses over one Goal.

Capability	Correct role

Intent-Driven Development	Establishes what the Owner actually wants to become true.
Expectation-Driven Development	Reconstructs what materially must also be true for that outcome to be legitimately complete.
Baseline-Driven Development	Injects already-earned mandatory expectations applicable to this class of system.
Lifecycle/State-Driven	Derives obligations from state ownership and transitions.
Journey-Driven	Derives obligations from actor-to-outcome traversability.
Negative-Space-Driven	Derives forbidden behavior and invariants from positive capabilities.
Reference/Differential-Driven	Supplies evidence-backed expectation candidates from mature external or sibling systems.
Reality/Evidence-Driven	Determines whether observed reality actually satisfies the claim.
Gap/Surprise-Driven	Turns escaped expectations into improvements to the discovery and baseline machinery.


So conceptually:

INTENT
                   │
                   ▼
          GOAL OUTCOME CONTRACT
                   │
         ┌─────────┴──────────┐
         │                    │
       UCFC                 BASELINES
         │                    │
         └─────────┬──────────┘
                   ▼
                  EDD
        expectation compilation
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
  Lifecycle     Journey    Negative Space
       │           │           │
       └───────────┼───────────┘
                   ▼
       Derived Mission Obligations
                   │
                   ▼
      BDD / ATDD / properties /
       model-based / mutation
                   │
                   ▼
          Reality / Evidence
                   │
                   ▼
             Goal Closure
                   │
             gaps / success
                   ▼
        Ratchet / institutional
              learning

EDD is therefore logically upstream of acceptance testing, but downstream of intent and baseline resolution.


---

F. Ownership / overlap map

The strongest current ownership split is:

Responsibility	Owner	EDD action

Founder/Goal semantic intent	Goal Spine	CONNECT
Phase lifecycle	GSD Core	PROJECT, do not copy
Mission/Goal-derived obligations	GSD X	EXTEND
Broad latent consequence discovery	UCFC	EXTEND / CANONICALIZE
Global engineering baseline	CPP/UCR-CIF	PROJECT
Setup/product-family semantics	KSEIP where applicable	PROJECT
Baseline applicability	UCR-CIF / existing resolver	CONNECT
Phase execution	GSD Core/providers	UNCHANGED
Runtime proof	existing verifier / Production Reality	CONNECT
Institutional baseline promotion	UCR-CIF	CONNECT
Bug doctrine / reusable failure learning	UKDL + failure infrastructure	CONNECT
Expectation-specific provenance/applicability contract	no complete owner demonstrated yet	EXTEND existing mission obligation semantics
Expectation Closure	partial via Goal Closure + UCFC	EXTEND
Completion-lens routing	overlap with current Dynamic Mode Router / Goal Controller	HYPOTHESIS — inspect before NEW


The current Goal Spine is already explicitly built around single-writer truth: Founder intent belongs to Goal, phase belongs to GSD, Git HEAD to Git, global baseline to CPP and setup semantic baseline to KSEIP. 

EDD must follow exactly that doctrine.


---

G. Candidate obligation-producer architecture

I would use the term producer semantically for now, not prescribe an implementation interface.

A producer consumes enough Goal context and evidence to emit expectation candidates.

It does not automatically make them mandatory.

The minimum useful producer family appears to be:

EXISTING / EXTEND — Consequence / Sibling Producer

UCFC already owns broad consequence reasoning.

Its job is essentially:

capability
→ material consequence
→ adjacent obligation

EXTEND — Lifecycle Producer

For each materially relevant state:

entry
ownership
allowed
forbidden
temporary semantics
exit
cleanup
restoration
interruptions
next state

EXTEND — Projection Producer

State ownership implies external projections:

UI;

inventory;

controls;

permissions;

HUD;

resources;

visible status.


Its fundamental invariant:

> internal state and player/user-observable projection must not diverge materially.



EXTEND — Journey Producer

Given actor + outcome:

entry
→ orientation
→ actions
→ progress
→ interruption
→ termination
→ continuation

Any dead transition becomes expectation debt.

EXTEND — Negative-Space Producer

Positive capability:

allowed behavior

induces questions about:

forbidden actor
forbidden state
forbidden duplicate
forbidden side effect
forbidden timing
forbidden resource ownership

Where possible this compiles into properties rather than dozens of examples.

EXTEND — Temporal / Cleanup / Termination Producer

Temporary ownership creates an obligation to:

expire;

release;

restore;

destroy;

or transfer ownership.


Bounded activities create termination expectations.

This producer is strategically important because “feature started correctly” routinely hides “feature never exits correctly.”

EXTEND — Recovery Producer

Activated only where relevant:

interruption;

retry;

reconnect;

restart;

stale state;

partial completion;

second-run cleanliness.


CONNECT — Baseline Expectation Producer

This should probably not “invent” expectations at all.

It projects applicable existing baseline obligations into Goal closure.

UCR-CIF already states that every applicable baseline is mandatory, while also insisting that not every baseline applies to every construction. It already proposes an applicability resolver and composed baseline capability packs. 

CONNECT — Reference Expectation Producer

References generate candidates, never automatic requirements.

Its output should say:

> repeated behavior X exists in references A/B/C under context Y.



Not:

> therefore our product must implement X.



CONNECT / EXTEND — User Reality Producer

This producer does something different: it derives proof strength.

A player-facing expectation cannot close because an internal listener exists.

A visible outcome must reach the player-visible boundary.


---

H. Expectation authority, provenance and confidence

This should be one of the strongest parts of EDD.

Every expectation needs enough semantics to answer:

WHAT is claimed?
WHY is it relevant?
WHERE did it come from?
WHO has authority over it?
WHEN does it apply?
WHAT happens if omitted?
HOW certain are we?
WHAT would make it not apply?
WHAT evidence can close it?
WHAT supersedes it?

I would keep at least these conceptual dimensions separate:

1. Source

Examples:

explicit Founder;

prior Founder decision;

constitutive baseline;

product/family baseline;

lifecycle-derived;

journey-derived;

negative-space-derived;

reference-derived;

incident-derived;

inferred.


2. Authority

Authority is not confidence.

An explicit Founder decision can have very high decision authority even if technical feasibility is uncertain.

A pattern seen in twenty competitor products can have strong empirical support while having almost no authority over this product.

That distinction prevents references from becoming accidental product requirements.

3. Applicability

An expectation can be true and mature but irrelevant here.

Example:

transactional retry safety

may be essential to payments and irrelevant to a static typography change.

4. Evidence strength / confidence

How well supported is the inference?

Do not silently convert:

likely
→ required

5. Materiality

What happens if omitted?

This is the anti-hallucination gate.

A candidate should be able to name a consequence such as:

user cannot finish;

state becomes incoherent;

data can duplicate;

match cannot terminate;

user loses context;

second execution inherits stale state.


“Seems polished” is insufficient by itself.

6. Resolution status

Reuse existing repository epistemic vocabulary if one exists.

Only if no equivalent exists should EDD introduce states conceptually similar to:

REQUIRED
STRONG_CANDIDATE
CONDITIONAL
UNKNOWN
NOT_APPLICABLE
EXPLICITLY_REJECTED
SUPERSEDED

Do not build a competing status taxonomy merely for EDD.


---

Conflict resolution

Do not use a simple global priority ladder.

Resolve a conflict through:

scope
→ currentness
→ authority
→ applicability
→ evidence
→ supersession
→ explicit exception

For example:

Founder vs reference

Founder decision wins inside its declared scope unless it violates an external hard constraint.

Founder vs baseline

Founder can intentionally diverge from a product/family default, but it should become an explicit baseline exception rather than silently deleting inheritance.

Reference vs reference

Preserve the disagreement as evidence until product context discriminates.

Inferred vs explicit

Explicit decision normally wins.

Legacy behavior vs current intended product

Legacy behavior is evidence of current reality, not automatic product authority.

That last distinction is essential.


---

I. Expectation Closure

This is the heart of avoiding both under- and over-compilation.

EDD cannot prove:

> “there exists no conceivable expectation we failed to imagine.”



That is impossible.

It can prove a much more useful bounded statement:

> All materially applicable expectation surfaces selected for this Goal have been explored to the required evidence depth, and no unresolved expectation debt remains that can legitimately invalidate the Goal’s completion claim.



I would extend current Goal Closure approximately as:

MAY_CLOSE =
    explicit backlog closed
AND required derived obligations dispositioned
AND applicable baseline closure
AND applicable lifecycle closure
AND applicable journey closure
AND applicable negative-space closure
AND required termination / cleanup / recovery closure
AND required reality evidence satisfied
AND no unresolved high-materiality Expectation Debt
AND institutional disposition complete

This extends rather than replaces the existing rule that Goal Closure requires backlog completion, derived-obligation disposition and convergence-plane satisfaction. 

Closure does not mean “run every lens”

A lens should close as one of:

SATISFIED
NOT_APPLICABLE — with reason
DEFERRED — non-blocking with authority
BLOCKED
SUPERSEDED

For a trivial CSS correction, “reconnect semantics” can close immediately as NOT_APPLICABLE.

That is not omission.

It is explicit non-applicability.


---

Stopping condition

Expectation search should stop when:

1. all mandatory inherited expectations have a disposition;


2. all materially activated lifecycle/journey surfaces are covered;


3. critical actor paths have no unclassified dead ends;


4. negative-space search finds no unresolved high-materiality violation class;


5. cleanup/termination/recovery are either satisfied or demonstrably irrelevant;


6. a counterexample/red-team pass produces no new material expectation class;


7. additional discovery is yielding duplicates, low-materiality candidates or evidence-insensitive speculation.



This gives EDD a fixed-point approximation, not infinite brainstorming.


---

J. Driven Development Router

I would not yet create a separate “Driven Development Router” runtime.

There is already a GSD X Dynamic Mode Router designed to select between immediate execution, quick/bounded work, PLAN, ULTRA-PLAN, milestone workflows, debugging, research and autonomous convergence based on uncertainty, blast radius, reversibility, persistence and other factors. 

That router answers:

> How heavily should this work be orchestrated?



EDD needs a related but different question:

> Which completion lenses are materially relevant to this Goal?



So my current hypothesis is:

EXTEND or CONNECT: Completion Lens Selection

Not necessarily a new router.

Conceptually:

Goal
  ↓
Mode Router
  ↓
execution/planning intensity

Goal
  ↓
Completion Lens Selection
  ↓
which expectation producers apply

A CSS adjustment might activate:

Intent
Visual contract
Regression boundary
Reality evidence

A payment flow might activate:

Intent
Baseline
Lifecycle
Journey
Negative Space
Transaction integrity
Recovery
Security
User Reality

SkyParty might activate:

Intent
Competitive-minigame baseline
Lifecycle
Projection
Journey
Negative Space
Termination
Cleanup
Reconnect
Second-run
Player Reality
Reference
Mutation

The crucial anti-bureaucracy property is:

> The router records why a plausible lens activated or did not activate, but does not force every lens onto every Goal.



Routing itself should become learnable from escape history.

If payment Goals repeatedly escape recovery obligations, their archetype should increasingly activate recovery automatically.


---

K. Expected → Observed convergence loop

The correct completion pipeline is:

GOAL OUTCOME
    ↓
EXPECTATION CANDIDATE
    ↓
authority/applicability adjudication
    ↓
REQUIRED EXPECTATION
    ↓
GOAL-DERIVED OBLIGATION
    ↓
claim classification
    ↓
PROOF OBLIGATION
    ↓
oracle selection
    ↓
execution / evidence
    ↓
OBSERVED REALITY
    ↓
EXPECTED ↔ OBSERVED

If equal enough under the required oracle:

CLOSED

If not:

GAP

The current Production Reality doctrine already says that meaningful DONE must identify the strongest real boundary and that paper-only evidence cannot close a claim crossing an actual runtime/browser/database/network/hardware boundary. 

EDD should make that rule claim-relative.

For example:

Claim	Minimum plausible oracle

Function exists	source/static
deterministic function behavior	unit/property
subsystem integration	integration/live runtime
user can actually reach feature	end-to-end/user path
Minecraft cage contains player	player-observable/runtime game oracle
UI matches intended visual state	rendered visual oracle
“this is fun”	human authority


A weaker oracle cannot satisfy a stronger claim.


---

L. Gap → self-repair / Constitutive Ratchet

Every material post-DONE surprise should create two incidents.

Incident A — Product gap

What is wrong with the product?

Incident B — Completion-system escape

Why could GSD X declare convergence without discovering it?

Classify Incident B into something like:

PRODUCER_MISS
ROUTER_MISS
BASELINE_MISS
BASELINE_INHERITANCE_MISS
APPLICABILITY_MISS
PROOF_COMPILATION_MISS
ORACLE_WEAKNESS
EVIDENCE_NOT_REACHABLE
COMPLETION_GATE_MISS
STALE_EXPECTATION
CONFLICT_RESOLUTION_MISS

Then:

escape
→ local repair
→ expectation-class identification
→ sibling search
→ producer/router/oracle regression
→ EDD benchmark case
→ cross-domain negative control
→ baseline promotion evaluation

This fits UCR-CIF extremely well.

UCR-CIF already establishes that:

proven improvements should be evaluated for baseline promotion;

applicable future constructions should inherit the strongest proven baseline;

failures should increase permanent immunity or explicitly explain why they cannot. 


And its Constitutive Baseline Ratchet explicitly distinguishes a random feature from a capability that changes what it means to build that class of system correctly. Only the latter deserves constitutive promotion. 

That gives us exactly the right guardrail against one SkyParty bug becoming universal dogma.


---

M. Evaluation and benchmark architecture

EDD needs its own benchmark because ordinary coding benchmarks cannot prove expectation discovery.

I would create an Expectation Discovery Benchmark built from both real historical escapes and deliberately constructed omissions.

Each case contains:

Goal
authoritative intent
applicable baselines
product context
available evidence
deliberately missing explicit requirements
gold material expectations
tempting-but-invalid expectations
expected oracle classes

It should contain separate classes for:

explicit expectations;

baseline inheritance;

lifecycle implications;

journey holes;

negative space;

termination;

cleanup;

recovery;

second-run state;

reference-derived candidates;

conflicting references;

Founder override;

non-applicable common patterns.


Metrics should remain separate rather than collapse into one vanity number:

Discovery quality

material expectation recall;

critical expectation recall;

material precision;

false obligation rate;

expectation-class escape rate.


Closure quality

false-DONE rate;

unresolved-material-debt at DONE;

Founder-discovered material gaps after DONE.


Baseline quality

baseline inheritance rate;

invalid baseline activation rate;

repeated missing-expectation rate.


Proof quality

oracle correctness;

evidence-strength mismatch rate.


Economics

latency overhead;

token/compute overhead;

additional implementation work;

rework prevented;

unnecessary bureaucracy.


Transfer

cross-domain producer effectiveness;

domain-specific false-positive rate.



---

Mutation test the EDD system itself

Run the benchmark with:

lifecycle derivation disabled
negative-space disabled
baseline inheritance disabled
cleanup derivation disabled
journey closure disabled
recovery disabled
player reality downgraded to unit evidence
second-run analysis removed

Each relevant benchmark subset must degrade.

If disabling a producer changes nothing:

> either the producer is redundant, its consumer path is disconnected, or the benchmark does not exercise it.



That is an unusually powerful architectural test.


---

N. SkyParty forensic test

SkyParty is already excellent evidence that the missing abstraction is expectation compilation rather than simple feature enumeration.

The historical analysis identified exactly this failure:

COMPONENT
→ CAPABILITY
→ OWNER
→ GAP

was not enough.

It needed:

STATE
→ ENTRY
→ OWNED RESOURCES
→ ALLOWED ACTIONS
→ FORBIDDEN ACTIONS
→ TEMPORARY RULES
→ TRANSITION PRECONDITIONS
→ TRANSITION EFFECTS
→ CLEANUP
→ RESTORATION
→ INTERRUPTION
→ RECONNECT
→ RESTART
→ FAILURE
→ NEXT STATE

The SkyParty corpus explicitly records that omission. 

And the resulting product expectations are exactly the kind of thing EDD should derive generically.

CAGED containment

Observed expectation:

> player must not modify or escape the cage before release.



The historical work specifically concludes that the invariant is the requirement, not “use Adventure mode.” 

Derived through:

Lifecycle
+ state ownership
+ negative space

No SkyParty hard-code required.


---

Projection ownership

CAGED, ACTIVE, SPECTATOR and LOBBY own different controls/inventory projections.

Generic derivation:

State A owns projection PA
A → B
therefore PA must cease
and PB must materialize

That derives lobby restoration and spectator inventory cleanup without knowing what Jugar, Tienda, Perfil or Fiesta are universally.


---

Initial release fall protection

The correct semantics were not “five seconds of immunity.”

The historical contract was:

release
→ first valid landing
→ protection consumed
→ later fall damage normal

with teleport/reconnect/state transition invalidating it. 

Generic producer:

temporary rule
→ semantic boundary
→ mandatory expiration
→ forbidden persistence

Again, no Minecraft-specific universal rule is required.


---

Elimination → spectator

Generic derivation:

alive actor
→ elimination
→ no longer satisfies alive invariant
→ continuation state required
→ spectator if product baseline selects it

The corpus explicitly notes that earlier analysis saw “Spectator” as a capability but failed to derive the transition contract from death/void through eliminated to spectator. 


---

Cleanup / second match

A match-scoped resource implies:

match termination
→ resource ownership expires
→ cleanup/restoration
→ next run starts from admissible initial state

The SkyParty analysis already elevates next-match clean state as a competitive-minigame baseline concern. 

This is precisely the kind of expectation that standard happy-path acceptance tests miss.


---

SkyParty pass condition for EDD

Give EDD only:

“Finish SkyParty”;

product identity;

applicable competitive-minigame baseline;

actual state machine/reality;

available reference/failure evidence.


Do not tell it about:

breakable cages;

first-fall protection;

spectator cleanup;

second-match stale state.


It passes only if general mechanisms reconstruct those classes of obligations.

That is the correct benchmark.


---

O. Cross-domain transfer test

Before any producer becomes universal, test it outside Minecraft.

Payment flow

Lifecycle should derive:

CREATED
→ AUTHORIZED
→ CAPTURED / FAILED / CANCELLED / REFUNDED

Negative space:

same logical payment cannot charge twice
unauthorized actor cannot capture
failed payment cannot appear completed

Recovery:

retry after timeout must not duplicate external side effects

Second-run:

replayed webhook cannot duplicate settlement

Same producers; different domain semantics.


---

SaaS onboarding

Journey producer derives:

enter
→ understand
→ configure
→ validate
→ reach first value
→ return later coherently

Recovery handles partially completed onboarding.

Projection checks user-visible progress against backend state.


---

Background job

Termination producer asks:

> what ends this activity?



Recovery asks:

> what happens after crash?



Negative space asks:

> what must not execute twice?



Reality asks:

> does successful internal scheduling prove the intended external side effect?




---

File pipeline

Lifecycle:

received
→ validated
→ transformed
→ persisted
→ published / rejected

Cleanup:

temporary files;

partial output;

stale locks.


Negative space:

invalid input must never publish output.



---

Infrastructure migration

State:

OLD
→ DUAL / MIGRATING
→ NEW

Derived expectations:

invariants preserved;

rollback;

traffic cutover;

cleanup only after safety condition;

restart/resume semantics;

no orphaned ownership.


If the same EDD operators remain useful across these domains with bounded false positives, we have evidence for generality.


---

P. Failure modes and anti-overengineering controls

EDD itself can easily become pathological.

The principal failure modes are:

Requirement hallucination

Mitigation:

> no mandatory expectation without provenance + applicability + material omission consequence.



Reference cargo cult

Mitigation:

> reference evidence produces candidates, not authority.



Infinite closure

Mitigation:

> materiality thresholds, scoped lenses, fixed-point stopping and explicit NOT_APPLICABLE.



Ontology explosion

Mitigation:

> do not build a giant universal taxonomy before the first benchmark proves which distinctions have operational value.



Engine proliferation

Mitigation:

> producers are cognitive/compilation operators behind one Goal contract, not fourteen operating systems.



Confidence/authority confusion

Mitigation:

> keep them separate.



“Everything becomes baseline”

Mitigation:

> Constitutive Promotion Gate + cross-domain/family negative controls.



Verification theatre

Mitigation:

> Production Reality boundary follows the actual claim.



Router bureaucracy

Mitigation:

> trivial Goals receive cheap lens selection and a tiny expectation surface.



Discovery detached from closure

Mitigation:

> every accepted required expectation must enter the existing Goal-derived obligation path.



Registered-but-ineffective EDD

This one deserves a hard test.

The complete effect path must prove:

Producer fires
        ↓
Expectation exists
        ↓
Applicability resolver accepts it
        ↓
Derived Goal/Mission obligation exists
        ↓
Completion compiler consumes it
        ↓
Proof requirement changes
        ↓
Oracle is executed
        ↓
Missing evidence makes closure false
        ↓
Goal cannot converge

Anything less is architectural decoration.


---

Q. Phased development plan

I would not begin with the router or a large expectation ontology.

The minimum-value DAG is narrower.

Phase 0 — Reality reconstruction

No new architecture.

Verify current:

Goal/Mission schemas;

derived obligation path;

UCFC implementation status;

baseline projection;

evidence vocabulary;

Production Reality consumers;

current router/capability registry;

current KSEIP output contracts.


Deliverable:

> current producer → representation → consumer → gate truth map.




---

Phase 1 — SkyParty escape archaeology

Reconstruct a small set of material Founder-found gaps.

For each:

missing expectation
expected derivation source
why it escaped
existing system that should have caught it
required general fix
negative control

This creates the first EDD gold set.


---

Phase 2 — Canonical EDD contract

Define semantically, without premature schema design:

expectation;

provenance;

authority;

applicability;

confidence;

material consequence;

oracle requirement;

disposition;

supersession;

expectation debt.


Then determine how much can be represented by the existing derived-obligation model.

Default decision: extend existing representation before inventing one.


---

Phase 3 — First producer set

Start with the highest-evidence, lowest-hallucination operators:

1. baseline inheritance;


2. lifecycle/state;


3. projection;


4. negative space;


5. cleanup/termination;


6. journey.



I would deliberately defer broad autonomous reference inference until these deterministic/semi-deterministic producers work.


---

Phase 4 — Prove completion effect

Before adding more intelligence:

> deliberately remove one derived expectation and prove Goal Closure changes.



This is the critical producer → consumer → effect milestone.


---

Phase 5 — Proof/oracle compilation

Connect expectation class to:

BDD/ATDD;

properties;

state models;

model-based transition tests;

mutation;

Production Reality.


Do not create another test framework.


---

Phase 6 — Expectation Closure

Add:

unresolved expectation frontier;

expectation debt;

explicit N/A;

materiality;

stopping semantics;

counterexample search.



---

Phase 7 — Lens routing

Only after producers prove useful should automatic activation be learned/encoded.

Otherwise we build a router for capabilities whose value is still hypothetical.


---

Phase 8 — Benchmark + negative controls + EDD mutation

Measure both:

recall
AND
precision

High recall with 4× implementation burden is a failed architecture.


---

Phase 9 — Cross-domain transfer

Run at minimum:

SkyParty;

transactional/payment;

SaaS user journey;

background/async job;

infrastructure/state migration.


Only transfer successful rules to broader scopes.


---

Phase 10 — Gap-to-Ratchet automation

Human-found expectation escape becomes:

classification
→ regression
→ producer/router/oracle repair
→ sibling search
→ baseline candidate

UCR-CIF already describes the broader institutional loop as intervention → root cause → capability gap → improved capability → promotion → future mission inherits → human intervention disappears. 

EDD should become one concrete realization of that loop.


---

Phase 11 — Frontier intelligence

Only then extend into harder inference:

reference pattern induction;

probabilistic expectations;

product-family learning;

success-path induction;

active evidence acquisition;

learned routing.


This ordering prevents “one giant expectation AI.”


---

R. Highest-value unanswered repository questions

These are the questions whose answers could still materially change the architecture:

1. Does the current repository actually implement the Goal Spine / Goal Contract 2.0, or is part of it still institutional design?


2. What is the exact current representation of a derived mission obligation?


3. Can a derived obligation presently block Goal closure at runtime, or only appear in planning/context?


4. Is UCFC / Implication Closure operational today, and if so, who consumes its outputs?


5. Is there already a generic applicability model we should extend for EDD, or only baseline-specific applicability?


6. What current epistemic vocabulary exists for KNOWN / INFERRED / UNKNOWN / SUPERSEDED so EDD does not create another one?


7. How is Founder intent versioned and superseded today?


8. How are Goal revisions propagated to already-derived obligations?


9. Can current obligations point to provenance without copying source truth?


10. Does Baseline Applicability Resolver already expose a mission-facing contract?


11. Can the current completion compiler distinguish mandatory obligation from candidate/unresolved expectation?


12. What exact oracle-strength vocabulary already exists?


13. Can Production Reality currently require player-observable or human-observable proof?


14. What state-machine/lifecycle artifacts can KSEIP already emit in machine-consumable form?


15. Does reference intelligence already emit capability candidates with applicability/confidence?


16. Where should Completion Lens Selection live: existing Dynamic Mode Router, Goal Controller, Capability Registry, Mission Compiler, or a thin combination?


17. What benchmark infrastructure already exists that can host expectation-discovery fixtures and mutations?


18. What were the exact obligations and evidence present when SkyParty was previously declared complete?


19. Which SkyParty expectations were truly derivable from evidence available at that time versus only obvious in hindsight?


20. Which current “DONE” surface is authoritative enough to block completion across GSD milestone, /cpp-gsd-long, Goal convergence and Production Reality?



Those are repository questions, not questions I would answer from theory.


---

Provisional architectural decision

Based on the evidence available now, I would formalize the direction as:

> EDD is not a new OS and not primarily a new agent. It is the canonical expectation-compilation discipline of the GSD X Goal/Mission layer, using UCFC and domain-specific producers to transform authoritative intent, applicable inherited baselines, product identity, lifecycle/journey consequences, negative space, reference evidence and reality into evidence-qualified Goal-derived obligations.



And the division becomes:

UCFC
discovers possible missing meaning

EDD
qualifies that meaning into an expectation frontier

Goal/Mission Contract
owns accepted mission-scoped obligations

GSD / providers
execute them

Verification + Production Reality
prove them

Goal Closure
prevents false DONE

UCR-CIF
makes reusable discoveries hereditary

That architecture answers the central failure without building another orchestration empire.

The deepest change to GSD X is then not a new feature called EDD.

It is a new invariant:

> NO GOAL MAY CONVERGE MERELY BECAUSE ALL EXPLICIT WORK IS COMPLETE. IT MAY CONVERGE ONLY AFTER THE MATERIAL EXPECTATION FRONTIER APPLICABLE TO THAT GOAL HAS BEEN COMPILED, DISPOSITIONED, AND PROVEN TO THE STRONGEST REQUIRED REALITY BOUNDARY.



And the counter-invariant, equally important:

> NO INFERRED EXPECTATION BECOMES PRODUCT TRUTH MERELY BECAUSE A MODEL COULD IMAGINE IT. IT MUST EARN REQUIREMENT STATUS THROUGH AUTHORITY, APPLICABILITY, MATERIAL CONSEQUENCE AND EVIDENCE.



Those two laws together are what stop both false DONE and infinite requirement hallucination.

The next architectural step should therefore be the live producer → representation → consumer → Goal-closure Reality Scan, followed immediately by SkyParty escape archaeology. I would not authorize implementation of a router, ontology, new engine, or persistence schema before those two pieces of evidence are resolved.

Ha pensado durante 42s

Sí. El siguiente nivel, tomando el incidente SkyParty como el hecho fundacional, es dejar de verlo como “varios bugs que revelaron que faltaba lifecycle reasoning” y tratarlo como algo más grave:

> SkyParty fue un Expectation Escape Incident: una diferencia material entre lo que razonablemente significaba “producto terminado” y lo que GSD X permitió declarar como terminado atravesó toda la cadena de ingeniería sin convertirse nunca en una obligación bloqueante.



Y eso cambia bastante el diseño de EDD.

El objetivo ya no debería ser solamente descubrir más expectations.

Debe ser construir una infraestructura que pueda responder, para cada sorpresa como SkyParty:

> ¿Cómo consiguió esta expectativa material atravesar todo nuestro sistema sin ser descubierta, en cuál fue el primer punto en el que razonablemente podía haberse detectado, qué mecanismo falló y cómo demostramos que ese mismo escape ya no puede repetirse?



Ahí está el siguiente salto.


---

1. Reinterpretación del incidente SkyParty

SkyParty no fue realmente:

bug:
cage se puede romper

bug:
spectator pobre

bug:
items incorrectos al volver

bug:
fall protection incorrecta

Ni siquiera fue solamente:

faltaba Match Player State Lifecycle

Eso es cierto, pero todavía es una descripción del producto.

El fallo de GSD X fue más amplio:

FOUNDER INTENT
    ↓
product reconstruction
    ↓
planning
    ↓
obligation discovery
    ↓
implementation
    ↓
verification
    ↓
DONE
    ↓
Founder plays
    ↓
“esto evidentemente no está terminado”

El Founder produjo un counterexample al certificado de completitud.

Ese es el hecho arquitectónicamente importante.

El propio corpus de SkyParty ya lo anticipó: una observación del Founder debe tener valor de aprendizaje desproporcionado porque revela simultáneamente un product defect y un factory detector gap, y exige preguntar automáticamente “WHY DID I NOT FIND THIS?”. 

EDD debería convertir eso en un contrato constitucional.


---

2. NEW CONCEPT — Expectation Escape Incident

No crearía un nuevo OS.

Lo convertiría en una clase de incidente de GSD X / EDD, consumida por Goal Closure, UKDL, UCR-CIF y el benchmark system.

Canonical definition

> Expectation Escape Incident — EEI: un caso en el que un humano, usuario, Production Reality oracle o sistema posterior descubre una diferencia material entre Expected Product Reality y Observed Product Reality que razonablemente podía haberse convertido en obligación antes de la declaración de DONE, pero no lo hizo.



Importante:

No todo bug es un EEI.

Por ejemplo:

bit flip impredecible de hardware;

nueva decisión del Founder tomada después;

preferencia subjetiva nunca expresada ni inferible;

requisito externo que cambió después del release;


no deben falsificar retrospectivamente al sistema.

EDD debe distinguir:

PRODUCT DEFECT

EXPECTATION ESCAPE

NEW REQUIREMENT

NEW PREFERENCE

POST-COMPLETION ENVIRONMENT CHANGE

IRREDUCIBLE HUMAN JUDGMENT

Eso evita castigar al sistema por no ser omnisciente.


---

3. SkyParty demuestra que necesitamos un Escape Causal Chain

Para cada expectativa perdida, no basta preguntar:

> “¿qué producer debería haberla generado?”



Hay que reconstruir toda su ruta potencial.

La unidad de análisis debería ser:

Expectation

→ Discoverability
→ Evidence availability
→ Producer applicability
→ Candidate generation
→ Authority/applicability adjudication
→ Obligation admission
→ Proof compilation
→ Oracle selection
→ Evidence acquisition
→ Completion consumption
→ DONE decision

Y localizar el primer punto causal roto.

Lo llamaría:

Earliest Preventable Point — EPP

> El primer punto del pipeline en el que, usando sólo evidencia disponible en ese momento, una arquitectura suficientemente madura podía razonablemente haber impedido el escape.



Esto es importantísimo porque evita “arreglar todo”.


---

4. El incidente SkyParty descompuesto por EPP

Tomemos varios gaps reales.

A. Romper / escapar de la cage

El corpus muestra que la expectativa correcta era:

> CAGED PLAYER MUST NOT MODIFY/ESCAPE THE CAGE BEFORE RELEASE.



Y también deja claro que “usar Adventure” era una posible implementación, no la expectativa universal. 

EPP

Muy temprano.

Una vez existe:

STATE = CAGED
PURPOSE = mantener jugadores antes de release

un Lifecycle + Negative-Space producer debería preguntar:

¿Qué acciones invalidarían la razón de existir de CAGED?

Respuesta:

escape
break containing structure
premature competitive interaction

Por tanto:

PRODUCER_MISS, probablemente antes incluso de implementación.

No necesitábamos esperar a player testing.


---

5. Spectator no era una “feature faltante”

Este es uno de los hallazgos más importantes del incidente.

KSEIP había visto nominalmente:

Spectator;

hotbars;

cages;

death;

match state.


Pero no había extraído los contratos entre ellos.

El corpus lo dice explícitamente: el análisis anterior hizo bien COMPONENT → CAPABILITY → OWNER → GAP, pero no cubrió correctamente STATE → TRANSITION → PRECONDITION → TEMPORARY RULE → CLEANUP → NEXT STATE → RESTORATION. 

Ese fallo significa que EDD debe distinguir:

CAPABILITY EXISTENCE

de

CAPABILITY LIFECYCLE COMPLETENESS

Ejemplo:

Spectator exists

no implica:

alive → eliminated → spectator

ni:

spectator → exit → lobby cleanly

ni:

spectator cannot mutate competitive state

ni:

spectator projections disappear after exit

Por eso haría de transition semantics una unidad de expectation discovery de primer nivel.


---

6. El gran patrón SkyParty: Noun Completeness vs Verb Completeness

Creo que aquí podemos generalizar todavía más.

La arquitectura previa era buena descubriendo sustantivos:

Cage
Spectator
Hotbar
Lobby
Game
Reward
Arena

Pero el Founder descubrió fallos en los verbos:

contain
release
eliminate
become spectator
return
restore
expire
reset
start again

Y muchos productos fallan precisamente ahí.

Yo elevaría una ley a GSD X:

> A PRODUCT IS NOT COMPLETE WHEN ITS REQUIRED ENTITIES EXIST. IT IS COMPLETE ONLY WHEN ITS MATERIAL STATE TRANSFORMATIONS PRESERVE THEIR CONTRACTS.



Eso trasciende Minecraft.

En pagos:

Payment exists

no prueba:

authorize → capture → refund

En onboarding:

Account exists

no prueba:

new user → configured user → first value → returning user

En jobs:

Job exists

no prueba:

queued → running → failed/retried → completed → cleaned

SkyParty debería convertirse en el benchmark histórico que llevó a CPP desde noun completeness a transition completeness.


---

7. Pero incluso lifecycle todavía no es suficiente

Aquí lo llevaría otro escalón.

Aunque hubiéramos modelado perfectamente:

LOBBY
WAITING
CAGED
ACTIVE
ELIMINATED
SPECTATOR
RETURN

todavía podríamos haber fallado.

¿Por qué?

Porque cada estado tiene varias planes of truth.

Por ejemplo SPECTATOR puede ser correcto internamente:

player.role = spectator

pero incorrecto externamente:

inventory sigue siendo de player
HUD incorrecto
puede afectar mundo
controls incorrectos
return rompe lobby

Por tanto EDD necesita tratar cada estado como:

SEMANTIC STATE
    ↓
EXPECTED PROJECTIONS

sobre múltiples superficies:

runtime authority
permissions
inventory/resources
UI/HUD
controls
world interaction
visibility
persistence
network state
external side effects

Lo llamaría:

State Projection Closure

> Cada cambio material de estado debe demostrar que todas sus proyecciones materialmente relevantes cambian coherentemente con él.



SkyParty entonces produce una regla mucho más general:

STATE TRANSITION
≠
single variable changed

Debe significar:

authority transitioned
resources transitioned
permissions transitioned
UI transitioned
controls transitioned
temporary rules transitioned
cleanup occurred


---

8. El incidente del first-release fall damage es todavía más valioso

Porque éste no era simplemente algo que Unique ya hacía y SkyParty olvidó copiar.

El análisis histórico señala precisamente que la semántica:

release
→ first fall protected
→ first valid landing consumes protection
→ subsequent fall damage normal

parecía ser una mejora propia de KobiSkyParty, no una capacidad heredada directamente de Unique. 

Y su contrato posterior quedó formulado con bastante precisión: la protección sólo vive desde release hasta el primer aterrizaje válido; teleport, reconnect o transición de estado la invalidan; no se refresca ni se convierte en inmunidad posterior. 

Este caso es extremadamente importante para EDD porque demuestra:

> Reference Intelligence alone cannot solve expectation completeness.



Unique podía enseñarnos:

spectator;

cage protection;

separated hotbars.


Pero no necesariamente esa nueva semántica.

Por tanto EDD necesita dos clases distintas de expectation:

INHERITED EXPECTATION

y

GENERATED PRODUCT CONSEQUENCE

El segundo tipo emerge del propio significado del producto.


---

9. Una nueva prueba: Semantic Boundary Analysis

El first-release fall protection revela una clase universal:

> Toda regla temporal necesita una frontera semántica, no sólo una duración técnica.



Mal diseño:

invulnerable = true for 5 seconds

Buen contrato:

protection exists while semantic condition C remains true

En SkyParty:

C = player has not completed first valid landing after release

Esto debería convertirse en un producer general:

Semantic Boundary Producer

Busca:

temporary permissions;

locks;

boosts;

immunity;

provisional ownership;

pending states;

leases;

retries;

sessions;

cooldown-like semantics.


Y pregunta:

What creates this temporary rule?

What semantic fact keeps it alive?

What exact event consumes it?

What invalidates it?

Can it leak into a later state?

Can it refresh accidentally?

Can it survive reconnect/restart when it should not?

Eso habría descubierto buena parte del incidente SkyParty.


---

10. Founder como adversarial oracle, no como QA manual

El objetivo no puede ser “que el Founder pruebe mejor”.

Al contrario.

Cuando el Founder encuentra algo después de DONE, debemos tratarlo como evidencia extremadamente cara:

FOUNDER OBSERVATION
        ↓
Product Counterexample
        +
Completion-System Counterexample

El propio corpus de SkyParty fija como objetivo reducir el porcentaje de material gaps descubiertos primero por Founder o real players y medir explícitamente Human Discovery Dependency. 

Yo haría que cada Founder-first escape produzca automáticamente un:

Founder Surprise Record

No un simple bug ticket.

Debe preservar:

Goal that was declared done

exact Founder observation

expected behavior

observed behavior

material consequence

production/runtime evidence

previous completion evidence

what the system believed was proven

which expectation was absent

which proof was therefore never demanded

Esto convierte la intervención humana en training data institucional de altísima calidad.


---

11. La gran mejora: Incident Freeze + Counterfactual Replay

Esto es, para mí, el siguiente salto más importante.

Cuando ocurre SkyParty, debemos congelar el estado anterior al descubrimiento.

Porque si entrenamos la arquitectura conociendo ya la respuesta podemos engañarnos muy fácilmente.

Crear un Incident Capsule

Preservar:

Founder intent at T0
repository/state at T0
applicable baselines at T0
references available at T0
Goal Contract at T0
derived obligations at T0
tests at T0
evidence at T0
DONE decision at T0

Más aparte:

Founder discovery at T1

Pero T1 queda oculto durante el replay.


---

12. Blind Counterfactual Replay

Después de reparar EDD:

NEW EDD
+
T0 CAPSULE
-
T1 HINT

y preguntar:

> ¿Descubre autónomamente el gap?



Esto es muchísimo más fuerte que escribir un regression test que dice literalmente:

test_cage_cannot_break()

Porque ese test sólo demuestra que memorizamos el bug.

El blind replay demuestra:

> la nueva arquitectura puede reconstruir la expectativa a partir de la misma evidencia que existía antes del incidente.



Ese debería ser el verdadero criterio de factory immunity.


---

13. Tres niveles de inmunidad

No consideraría un SkyParty escape “aprendido” sólo porque arreglamos la feature.

Level 1 — Product Immunity

SkyParty bug no reaparece.

Necesario, pero débil.

Level 2 — Family Immunity

Un nuevo competitive minigame recibe automáticamente:

state transition completeness;

containment reasoning;

alive/eliminated/spectator semantics cuando aplican;

cleanup;

next-match clean state.


Level 3 — Generative Immunity

Incluso ante un nuevo tipo de temporal/lifecycle bug que no hemos visto literalmente, el producer general lo deriva.

Ejemplo:

No conoce “cage fall protection”.

Pero conoce:

temporary state
+
semantic boundary
+
transition
+
resource/protection ownership

y genera el análisis correspondiente.

Level 3 es el objetivo real.


---

14. Memorization test para evitar falsa mejora

Después de SkyParty es trivial hacer:

if minigame:
    check cages
    check spectator
    check lobby items

Eso sería aprendizaje superficial.

El benchmark debe introducir holdouts estructurales.

Por ejemplo, un producto inventado con:

PREVIEW
→ LOCKED
→ ACTIVE
→ ENDED

y un permiso temporal durante LOCKED.

EDD debe derivar:

forbidden actions;

release;

expiration;

cleanup;


aunque no haya cage, spectator ni Minecraft.

Si sólo pasa SkyParty:

> memorized incident.



Si pasa estructuras análogas en pagos, SaaS y jobs:

> learned expectation grammar.




---

15. Escape Vector, no sólo root cause

Para cada incidente guardaría un pequeño vector causal.

Conceptualmente:

DISCOVERY      = missed
APPLICABILITY  = missed?
AUTHORITY      = correct?
OBLIGATION     = absent
PROOF          = therefore absent
ORACLE         = insufficient / never invoked
CLOSURE        = permitted incorrectly
BASELINE       = absent / not inherited

SkyParty puede revelar múltiples vectores distintos.

Cage escape

Likely:

Lifecycle producer miss
→ obligation absent
→ no adversarial property
→ DONE passes

Lobby inventory restoration

Likely:

transition/projection miss
→ cleanup obligation absent
→ no cross-state journey
→ DONE passes

Weak spectator experience

Could be:

family baseline insufficiency
+
journey closure miss

First-release fall damage

Could be:

product-consequence discovery miss
+
semantic-boundary reasoning absent

Eso evita meter todos los fallos bajo “lifecycle bug”.


---

16. Escape Surface Coverage

Hoy coverage normalmente pregunta:

Which code ran?
Which requirement has a test?

EDD debería añadir:

Which expectation-producing surfaces were interrogated?

Por ejemplo SkyParty:

Explicit intent               CLOSED
Baseline inheritance          PARTIAL
Capability presence           CLOSED
Lifecycle transitions         OPEN ← escape surface
State projections             OPEN
Negative space                OPEN
Termination                   ?
Cleanup                       OPEN
Second-run                    OPEN
Player journey                PARTIAL
Player reality                insufficient

Así “all tests green” deja de ocultar:

> no miramos esa dimensión.




---

17. El Founder no debería descubrir el mismo shape dos veces

Ésta sería otra ley constitucional.

No:

> “nunca repetiremos exactamente un cage bug.”



Sí:

> Una vez que un Founder descubre una clase material de expectativa que era razonablemente derivable, futuras Goals aplicables no pueden volver a omitir esa clase sin producir un explicit baseline/router/detector incident.



SkyParty descubre:

STATE_TRANSITION_COMPLETENESS

El próximo fallo no debería ser:

“ah, al salir de checkout pending quedó un lock”

si es esencialmente la misma gramática:

temporary state
→ exit
→ missing cleanup/restoration

Eso sería una repeated expectation-class escape, mucho más grave que repetir el mismo bug.


---

18. Nueva métrica: Expectation Escape Rate

El corpus ya pide medir:

number of human-discovered gaps;

runtime surprises;

human minutes;

Human Discovery Dependency. 


Yo lo estructuraría más profundamente.

Founder-First Material Gap Rate

material gaps discovered first by Founder
/
all material gaps

Debe tender a cero.


---

Preventable Expectation Escape Rate

Más importante:

human-first gaps classified as reasonably pre-discoverable
/
all completed Goals

Porque no queremos penalizar decisiones genuinamente nuevas.


---

Repeated Expectation-Class Escape Rate

escapes belonging to an already-known expectation grammar
/
all expectation escapes

Este sí debería tender muy rápidamente a cero.


---

Earliest Preventable Point Distance

Cuántas capas atravesó el gap después del momento en que podía haberse detectado.

Ejemplo:

could be derived during lifecycle compilation
↓
passed planning
↓
passed implementation
↓
passed verification
↓
passed DONE
↓
Founder discovered

Distancia enorme = fallo del factory especialmente grave.


---

19. Surprise Budget

No haría un score simplista para DONE, pero sí introduciría una noción operacional:

Material Surprise Budget

Para ciertos Goals:

Goal CONVERGED

debería implicar aproximadamente:

known unresolved high-material surprises = 0

No:

all possible future surprises = 0

Eso es imposible.

Pero si tenemos:

UNKNOWN:
reconnect state may be wrong
materiality HIGH
critical player journey YES

entonces no podemos esconderlo porque “tests green”.

Debe seguir siendo Expectation Debt bloqueante.


---

20. Founder Walkthrough Prediction

Antes de DONE, EDD debería intentar anticipar algo muy concreto:

> Si el Founder entrara ahora mismo en producción durante diez minutos, ¿qué es lo más probable que señalara inmediatamente como roto, absurdo, incoherente o incompleto?



No como un LLM diciendo “looks polished”.

Sino usando:

Goal;

lifecycle;

journeys;

baselines;

unresolved debt;

reference expectations;

runtime evidence;

previous Founder escape classes.


Esto podría llamarse:

Pre-DONE Founder Counterexample Search

El resultado no son opiniones.

Son counterexample candidates.

Para SkyParty:

Try breaking containment before release.

Die by void.

Observe elimination transition.

Use spectator controls.

Exit spectator.

Inspect lobby inventory.

Start another match.

Observe first post-release landing.

Fall again afterward.

Eso habría sido muchísimo más valioso que otros veinte unit tests.


---

21. Synthetic Founder / Player Red Team

No debe depender siempre del Founder real.

Para player-facing systems, EDD puede generar actor missions desde expectations.

SkyParty:

ACTOR: normal player
MISSION: join → wait → start → fight → die → spectate → leave → join again

Y adversarial variants:

attempt forbidden action while CAGED

disconnect during CAGED

disconnect after release before landing

die by void

die by combat

exit spectator

rejoin same arena

start second match

El corpus ya proponía como vertical slice precisamente descubrir states, modelar resources, generar transition tests, ejecutar synthetic journey, detectar leakage y elevar baseline. 

EDD debería absorber esa idea como una de sus primeras pruebas de verdad.


---

22. SkyParty como frozen constitutional benchmark

No lo usaría sólo durante desarrollo.

Lo conservaría permanentemente.

Benchmark Case: EEI-SP-001

Contenido conceptual:

INPUT
“Finish SkyParty.”

AVAILABLE REALITY
pre-incident architecture/evidence

HIDDEN GOLD ESCAPES
void → proper elimination → spectator
spectator control surface
cage containment
return-state restoration
first-release semantic protection
cleanup / next-match cleanliness

Pero hay que separar:

Derivable from family/reference evidence

Por ejemplo:

spectator;

cage containment;

return lifecycle.


Derivable only through consequence reasoning

Probablemente:

exact first-release protection semantics.


Founder/product-authority dependent

Cualquier decisión que no pueda justificarse autónomamente.

El corpus ya exige que SkyParty se utilice como training ground y pregunta explícitamente si la arquitectura podría descubrir esos mismos gaps sin human hint, además de exigir que cada subsystem diga cuál habría detectado, cuándo, con qué evidencia y con qué falsos positivos. 

Eso es prácticamente el germen de este sistema.

Yo lo haría obligatorio.


---

23. Expectation Escape Tribunal

No un comité humano.

Una fase causal del pipeline.

Cuando aparece un Founder-first gap:

1. Was it material?

2. Did it contradict the Goal at the time DONE was declared?

3. Was evidence sufficient to infer it before DONE?

4. What was the Earliest Preventable Point?

5. Which producer/lens should have activated?

6. Was the producer absent, silent, rejected or disconnected?

7. If candidate existed, why was it not admitted?

8. If obligation existed, why did proof not catch it?

9. If proof existed, was oracle too weak?

10. If evidence failed, why did completion still close?

11. What sibling systems could contain the same escape class?

12. At what baseline scope should immunity live?

Esto produce un causal verdict, no sólo una retrospective.


---

24. La distinción decisiva: Discovery failure vs Enforcement failure

Hay que separar dos familias.

Discovery failure

Expectation nunca apareció.

SkyParty cage probablemente aquí.

No candidate
→ no obligation
→ no test

Enforcement failure

Expectation existía pero no bloqueó DONE.

Ejemplo hipotético:

“spectator inventory must clean”

estaba documentado, pero:

ningún consumer lo convirtió en test;

o el test no corrió;

o el oracle no observó player reality;

o Goal Closure ignoró el resultado.


Eso es mucho peor arquitectónicamente.

EDD necesita clasificar ambos porque la reparación es distinta.


---

25. Introducir Expectation Reachability

Podemos reutilizar la doctrina ya existente:

REGISTERED
≠ ACTIVE
≠ REACHABLE
≠ EFFECTIVE
≠ PRODUCTION-PROVEN

Aplicada a expectations:

DERIVED
≠ ADMITTED
≠ OBLIGATING
≠ VERIFIED
≠ COMPLETION-BLOCKING

Una expectation que existe en un Markdown pero nunca llega a Goal Closure es equivalente a no existir.

Eso debería ser medible.


---

26. La prueba de madurez después de SkyParty

Un EDD verdaderamente corregido debería superar cuatro tests.

Test 1 — Historical replay

Con la evidencia preincidente:

> descubrir los gaps conocidos sin pistas.



Test 2 — Mutation

Eliminar lifecycle producer:

> SkyParty benchmark se vuelve rojo.



Eliminar cleanup:

> return/second-run se vuelve rojo.



Eliminar player oracle:

> ciertas pruebas se degradan.



Test 3 — Structural holdout

Un dominio distinto con la misma gramática.

Por ejemplo:

SaaS trial lock
→ unlock
→ temporary permission cleanup

Debe detectarse.

Test 4 — Negative control

Un producto donde:

temporary state intentionally persists

por decisión explícita.

EDD no debe exigir cleanup incorrectamente.

Éste demuestra precision.


---

27. La arquitectura completa, ya centrada en incidentes

Yo reformularía EDD así:

GOAL
                     │
                     ▼
            EXPECTATION COMPILER
                     │
         ┌───────────┴───────────┐
         │                       │
  inherited expectations   generated expectations
         │                       │
         └───────────┬───────────┘
                     ▼
         MATERIAL EXPECTATION FRONTIER
                     │
                     ▼
          Goal-derived obligations
                     │
                     ▼
        proof/oracle compilation
                     │
                     ▼
             Production Reality
                     │
                     ▼
               Goal Closure
                     │
              ┌──────┴──────┐
              │             │
           CONVERGED      ESCAPE
                            │
                            ▼
                 EXPECTATION ESCAPE
                      INCIDENT
                            │
                            ▼
                    META-CAUSAL RCA
                            │
                    Earliest Preventable
                           Point
                            │
            ┌───────────────┼──────────────┐
            ▼               ▼              ▼
        product fix    factory fix     sibling search
            │               │              │
            └───────────────┼──────────────┘
                            ▼
                 BLIND INCIDENT REPLAY
                            │
                      immunity proven?
                         │       │
                        no       yes
                         │       │
                       repair    ▼
                         │    scope evaluation
                         │       │
                         └───► Ratchet
                                  │
                                  ▼
                           future Goals

Esto sí convierte el incidente SkyParty en compounding infrastructure.


---

28. Lo elevaría a una nueva ley constitucional

Además de las leyes anteriores de EDD, añadiría:

> FOUNDER-FIRST MATERIAL SURPRISE IS PRESUMPTIVE EVIDENCE OF A COMPLETION-SYSTEM DEFECT UNTIL PROVEN OTHERWISE.



“Presumptive” es importante.

No asumimos automáticamente que todo lo que el Founder quiera después era inferible antes.

Pero obliga a investigar.

Otra:

> NO EXPECTATION ESCAPE IS CLOSED BY THE PRODUCT FIX ALONE.



Y la más fuerte:

> AN EXPECTATION ESCAPE IS INSTITUTIONALLY CLOSED ONLY WHEN THE PRODUCT IS REPAIRED, THE EARLIEST PREVENTABLE POINT IS IDENTIFIED, THE FACTORY IS REPAIRED AT THE NARROWEST CORRECT SCOPE, AND A BLIND PRE-INCIDENT REPLAY DEMONSTRATES THAT THE SAME EXPECTATION CLASS WOULD NOW BE DISCOVERED BEFORE DONE.



Esta, para mí, es la verdadera evolución del incidente SkyParty.


---

29. Y haría a SkyParty el primer Expectation Escape Immunity Program

No construiría todo EDD primero.

Haría exactamente lo contrario.

Usaría SkyParty como vertical slice:

EEI-SP-001
Match Player Lifecycle Escape

Subcasos:

SP-001A  Caged containment
SP-001B  Void/elimination transition
SP-001C  Spectator product projection
SP-001D  Return-state restoration
SP-001E  Initial-release semantic protection
SP-001F  Second-match transient-state cleanliness

Para cada uno:

Founder-observed symptom
Expected contract
Material consequence
Evidence available pre-incident
Earliest Preventable Point
Expected producer
Expected lens
Expected oracle
Historical reason for escape
Local regression
Generalized regression
Negative control
Promotion scope
Blind replay result

Eso produce la primera evidencia real de si EDD funciona.


---

30. Lo que SkyParty debería cambiar permanentemente en GSD X

La lección no debería quedar como:

> “hay que revisar lifecycle.”



Debe quedar mucho más fuerte:

Antes

Intent
→ requirements
→ plan
→ implementation
→ tests
→ DONE

Después de SkyParty

Intent
→ expected product reconstruction
→ applicable expectation lenses
→ expectation closure
→ obligations
→ proof compilation
→ user/player reality
→ adversarial Founder-counterexample search
→ DONE
→ escape monitoring
→ causal factory repair
→ blind historical replay
→ baseline ratchet

Y el objetivo del sistema cambia de:

> “menos bugs.”



a:

> cada vez menos cosas materialmente obvias que sólo el Founder descubre después de que la máquina ha dicho DONE.



El corpus original ya formulaba esto como Human Discovery Dependency y proponía explícitamente medir quién descubrió primero cada material gap, con el objetivo de reducir founder-first discovery. 

Yo convertiría eso en uno de los KPIs constitucionales de GSD X.


---

North Star actualizado

La formulación más fuerte que extraería de SkyParty sería:

> GSD X SHOULD NOT MERELY LEARN TO FIX WHAT THE FOUNDER FINDS. IT SHOULD LEARN THE GENERATIVE STRUCTURE OF WHY THE FOUNDER WAS ABLE TO FIND SOMETHING THE COMPLETION SYSTEM COULD NOT, REPAIR THAT STRUCTURE AT THE EARLIEST PREVENTABLE POINT, AND PROVE THROUGH BLIND COUNTERFACTUAL REPLAY THAT THE NEXT COMPARABLE GOAL WOULD NOT REQUIRE THE FOUNDER TO DISCOVER IT AGAIN.



Ahí EDD deja de ser sólo “expectation discovery”.

Se convierte en un Expectation Escape Immunity System dentro del Goal/Mission architecture.

Y SkyParty deja de ser un mal resultado pasado.

Se convierte en el primer caso que enseña a Claude Power Pack cómo reducir permanentemente la distancia entre machine-DONE y Founder-DONE.

Ha pensado durante 1m 38s

Sí. El problema todavía más profundo que atacaría no es Expectation Escape.

Es Semantic Loss.

SkyParty no falló principalmente porque GSD X “no pensó en suficientes cosas”. Falló porque, al transformar intención en arquitectura, componentes, tareas y tests, se perdió parte del significado del producto.

El sistema conservó los sustantivos:

> Cage. Spectator. Lobby. Match. Protection.



Pero perdió sus leyes:

> Cage existe para contener hasta release.
Spectator es una continuación válida del jugador eliminado.
Lobby posee un conjunto de controles y recursos que debe restaurarse.
Protection es temporal y debe morir en una frontera semántica concreta.
Match es una actividad acotada cuyos recursos no pueden sobrevivir al siguiente match.



Eso explica por qué puedes tener:

todas las features;

todos los listeners;

todos los states;

todos los tests;

cero tareas pendientes;


y seguir teniendo un producto absurdamente incompleto.

El problema raíz es:

GSD X no conserva todavía de forma suficientemente fuerte la semántica del producto durante toda la cadena de construcción

Y esto es mucho más importante que SkyParty.


---

1. El verdadero incidente de SkyParty fue Semantic Contract Erosion

La cadena probablemente se pareció conceptualmente a:

Founder:
“quiero un SkyParty terminado”

↓

Product understanding:
“SkyWars / cages / spectator / lobby / match”

↓

Capability model:
Cage ✓
Spectator ✓
Lobby ✓
Match ✓

↓

Implementation:
Cage object exists ✓
Spectator mode exists ✓
Lobby items exist ✓
Match starts ✓

↓

Tests:
components work ✓

↓

DONE

Cada transformación parecía razonable.

Pero en algún punto desaparecieron relaciones esenciales:

CAGED
    MEANS
player is contained until fair release

se degradó a:

Cage exists

Y:

ELIMINATED
    MUST CAUSE
loss of alive authority
→ spectator continuation
→ spectator projection

se degradó a:

Spectator capability exists

Y:

MATCH EXIT
    MUST CAUSE
removal of match-owned state
+ restoration of lobby-owned state

se degradó a:

Lobby items exist

Ésta es una pérdida de información semántica.

El propio análisis de SkyParty identificó que el antiguo COMPONENT → CAPABILITY → OWNER → GAP no llegaba suficientemente lejos y que necesitábamos modelar entry, owned resources, allowed/forbidden actions, transition effects, cleanup, restoration, interruptions, reconnect y next state. 

Pero yo ahora lo generalizaría todavía más.


---

2. Nueva ley raíz: Semantic Conservation

Añadiría una ley constitucional a GSD X:

> NO ENGINEERING TRANSFORMATION MAY SILENTLY DISCARD A MATERIAL SEMANTIC PROPERTY OF THE INTENDED SYSTEM.



O de forma aún más estricta:

> Intent → model → obligations → plan → implementation → verification → production must form a semantics-preserving compilation chain.



Esto es muy parecido a cómo pensamos en un compilador.

Un compilador puede transformar:

high-level source
→ AST
→ IR
→ machine code

pero no puede decidir:

> “esta condición parecía secundaria, la quito.”



Cada representación cambia.

La semántica debe sobrevivir.

Hoy el equivalente en software agentic suele ser:

human intent
→ prose requirements
→ plan
→ todo list
→ code

Y cada transición puede ser lossy.

Ahí está el problema de raíz.


---

3. El cambio fundamental: Requirements dejan de ser la representación principal

Una lista de requirements es inherentemente mala para representar un sistema complejo.

Porque una lista expresa muy bien:

Feature A exists.
Feature B exists.
Feature C exists.

Pero expresa mucho peor:

A owns R only while state S.
B may occur only after transition T.
C invalidates temporary authority Q.
D must never coexist with E.
F must eventually terminate.
After F, R must return to owner G.

Es decir:

> los productos son sistemas dinámicos; los backlogs son listas.



Ese mismatch genera una enorme cantidad de deuda invisible.

SkyParty lo demuestra perfectamente.


---

4. Iría hacia un Goal World Model

No otro OS.

No otra base de datos gigante.

No un “digital twin” marketiniano.

Conceptualmente, GSD X debería compilar cada Goal material en un:

Goal World Model

Un modelo mínimo, mission-scoped, versionado y evidence-qualified de:

> cómo debe ser el mundo cuando el Goal está correctamente realizado.



Esto encaja además con una dirección ya presente en KSEIP: el corpus define el Behavioral Twin como un modelo versionado de lo que el sistema cree que el setup contiene, permite, prohíbe y debe observar, y recomienda varias vistas conectadas —capability, lifecycle, resources, journeys, expectations, evidence, failures, unknowns y baselines— en vez de un megagrafo. 

Yo elevaría esa idea desde KSEIP a GSD X.


---

5. Dos mundos: Expected Reality y Observed Reality

Ésta sería la abstracción fundamental.

Expected Reality Model

Lo que debería ser cierto.

Compilado desde:

Founder Intent
+ Goal Outcome
+ applicable baselines
+ product identity
+ product purpose
+ architecture
+ prior decisions
+ family knowledge
+ reference evidence
+ UCFC
+ EDD

Observed Reality Model

Lo que realmente es cierto.

Reconstruido desde:

repository
runtime
state
tests
telemetry
database
UI
player behavior
deployment
production

Entonces DONE deja de ser primordialmente:

tasks_remaining == 0

y pasa a ser:

material_delta(
    ExpectedReality,
    ObservedReality
) ≈ 0

con evidencia adecuada.

Eso es muchísimo más potente.


---

6. EDD pasa a ser un compilador, no el cerebro completo

Con esta arquitectura, EDD encuentra su verdadero sitio.

No necesitamos pedirle a una IA:

> “imagina 500 acceptance criteria.”



EDD consume el Goal World Model y compila consecuencias.

GOAL WORLD MODEL
       ↓
Expectation Compiler
       ↓
Derived obligations
       ↓
Proof obligations

Muchas expectations dejan incluso de requerir creatividad.

Se vuelven derivables.


---

7. SkyParty reconstruido como mundo, no como features

Imagina que el Expected Reality Model contiene:

Actor:
Player

States:
LOBBY
WAITING
CAGED
ACTIVE
ELIMINATED
SPECTATOR
RETURNING

Purpose(CAGED):
preserve fair pre-match containment until release

De esa sola frase puede derivarse muchísimo.

State semantics

CAGED

implica:

movement authority = constrained
competitive influence = forbidden
containment = required
release authority = game lifecycle

Por tanto:

break containment structure
escape
premature damage
premature world modification

son contradicciones de la finalidad del estado.

No necesitamos tener hard-coded:

> check cage break.



Lo derivamos del purpose.


---

8. Esta pieza faltaba incluso en nuestro lifecycle model: Purpose

Un state machine convencional puede decir:

CAGED → ACTIVE

Pero eso no explica por qué existe CAGED.

Sin finalidad, GSD X puede conocer perfectamente el state graph y seguir sin derivar negative space.

Añadiría al modelo:

STATE
→ PURPOSE
→ AUTHORITY
→ OWNERSHIP
→ INVARIANTS
→ FORBIDDEN CONTRADICTIONS

Éste es un salto muy importante.

Por ejemplo:

Payment AUTHORIZED

Purpose:

> funds are approved but not yet finally captured.



Deriva:

no double capture;

cancellation semantics;

transition restrictions;

idempotency implications.


Email DRAFT

Purpose:

> editable communication not yet externally delivered.



Deriva:

must not reach recipient;

can mutate;

sending changes authority/state.


Migration DUAL_WRITE

Purpose:

> maintain consistency while authority is transitioning.



Deriva:

both copies must remain reconcilable;

cleanup cannot occur yet;

cutover has preconditions.


SkyParty CAGED

Purpose:

> fair containment before synchronized release.



Deriva sus invariants.

Eso previene problemas mucho más amplios que SkyParty.


---

9. Nuevo principio: Every important thing must explain why it exists

No sólo:

What is this component?

Sino:

What product/system condition would fail
if this concept did not exist?

Y luego:

What behaviors would contradict that purpose?

Eso produce negative-space automáticamente.

La cage deja de ser geometría.

Se convierte en un mecanismo que satisface:

PREMATCH_FAIR_CONTAINMENT

Y entonces podemos cambiar su implementación completamente sin perder el contrato.


---

10. La segunda raíz: Relationship Loss

Los bugs más peligrosos no viven en los nodos.

Viven en las relaciones.

Por eso:

Cage ✓
Spectator ✓
Lobby ✓

puede ser completamente verde.

Pero:

Cage --release--> Active
Active --void--> Eliminated
Eliminated --continue--> Spectator
Spectator --exit--> Lobby

puede estar roto.

Así que establecería otra ley:

> COVERAGE OF COMPONENTS DOES NOT IMPLY COVERAGE OF RELATIONS.



El sistema debe medir ambas cosas.


---

11. Semantic Relation Coverage

En vez de preguntar sólo:

Are all capabilities represented?

preguntar:

Are all material semantic relations represented and proven?

Clases particularmente importantes:

OWNS
REQUIRES
ENABLES
FORBIDS
CAUSES
CONSUMES
INVALIDATES
RESTORES
PROJECTS
PERSISTS
TERMINATES
SUPERSEDES
MUST_PRECEDE
MUST_EVENTUALLY_CAUSE
MUST_NEVER_COEXIST

El corpus más avanzado de GSD X ya apunta en esta dirección en reverse engineering: distingue explícitamente relaciones como CALLS, ENABLES, INVALIDATES, CAUSES, DERIVES_FROM, PROJECTS y PERSISTS, advirtiendo que un dependency graph simple es insuficiente. 

Yo elevaría eso a construcción normal.


---

12. La tercera raíz: Temporal Semantics Loss

Otra enorme familia de bugs viene de no representar el tiempo semántico.

SkyParty:

temporary protection

se convierte fácilmente en:

timer = 5 seconds

porque la implementación necesita algo concreto.

Pero eso destruye significado.

El contrato verdadero era:

Protection exists
WHILE
player has not completed the first valid landing after release

El tiempo de reloj puede ser irrelevante.

Por eso distinguiría:

CLOCK BOUNDARY

de:

SEMANTIC BOUNDARY

Y daría preferencia al segundo.

Esto previene bugs en:

locks;

leases;

authentication;

migrations;

reservations;

payments;

cooldowns;

retries;

sessions;

feature flags;

permissions;

temporary files;

transactions.



---

13. Nueva ley universal: Temporary means Until, not For

No literalmente siempre, pero como pregunta obligatoria:

> Every temporary condition must identify what truth makes it temporary and what semantic event ends it.



No aceptar automáticamente:

temporary = sleep(5000)

cuando el negocio realmente quiere:

temporary = until condition C

Ese solo patrón podría prevenir una cantidad enorme de bugs.


---

14. La cuarta raíz: Ownership Loss

Muchísimos bugs son en realidad:

> algo sigue vivo después de que su owner dejó de existir.



SkyParty:

spectator inventory

tiene owner:

SPECTATOR STATE

Por tanto:

exit(SPECTATOR)

debe provocar:

ownership ends
→ spectator inventory removed

Igualmente:

match HUD
owner = MATCH

entonces:

MATCH END
→ HUD must cease

Esto puede convertirse en una familia universal:

Ownership Conservation

Cada recurso material debería poder responder:

Who owns me?

Under what scope?

When does ownership begin?

When must it end?

Can ownership transfer?

What destroys me?

What restores the previous owner?


---

15. Esto descubre cleanup automáticamente

Hoy muchas veces cleanup aparece como:

> “acuérdate también de limpiar X.”



En un sistema con ownership explícito:

temporary resource R
owner = scope S

se deriva:

end(S)
→ R must be transferred or destroyed

Si no existe transition:

UNRESOLVED OWNERSHIP

Eso es bloqueante.

No necesitas imaginar manualmente cada cleanup bug.


---

16. Y descubre stale-state / second-run automáticamente

Supón:

Match M1 owns:
inventory
scoreboard
alive-set
spectator-state
protection
temporary entities

Cuando M1 termina:

owner M1 ceases to exist

Por tanto todo recurso debe tener:

DESTROY
TRANSFER
ARCHIVE

Si ninguno aplica:

orphaned state

Ahora el second-match test ya no es una buena idea opcional.

Es una prueba derivada de ownership closure.


---

17. Quinta raíz: Projection Loss

Una de las causas más peligrosas:

internal truth ≠ user-visible truth

SkyParty podía tener:

player.role = spectator

pero proyectar incorrectamente:

inventory;

HUD;

controls;

gamemode;

world interaction.


Por tanto introduciría:

Projection Conservation

Todo estado con consecuencias observables debe declarar sus projections.

Semantic state
       ↓
UI
controls
permissions
resources
network behavior
visual state
external side effects

Y cambiar de estado implica:

old projections invalidated
+
new projections materialized


---

18. Esto unifica frontend y backend de una forma muy útil

Ejemplo SaaS:

subscription = cancelled

pero UI muestra:

Active

Projection violation.

Ejemplo ecommerce:

payment = failed

pero confirmation screen:

Order confirmed

Projection violation.

Ejemplo infra:

deployment = unhealthy

dashboard:

green

Projection violation.

Ejemplo SkyParty:

spectator

con active-player controls.

Projection violation.

Misma gramática.


---

19. Sexta raíz: Authority Loss

Otro patrón transversal:

> ¿Quién puede decidir qué?



CAGED:

release authority = match controller

No:

player breaks glass

Checkout:

settlement authority = payment provider/transaction state

No:

frontend says success

Migration:

write authority = current primary

No:

both databases independently decide truth

Por tanto todo Goal World Model debería poder representar authority boundaries.

Muchos bugs de:

permissions;

multi-writer state;

race conditions;

security;

distributed systems;

UI optimism;


son authority violations.


---

20. Entonces aparecen Universal Semantic Conservation Laws

En vez de crear 500 checklists, podríamos tener una pequeña familia de leyes generativas.

Por ejemplo:

Purpose Conservation

Una implementación no puede contradecir la finalidad material del constructo.

Authority Conservation

Sólo el owner autorizado puede realizar transiciones autoritativas.

Ownership Conservation

Los recursos no pueden sobrevivir silenciosamente al scope que los posee.

State Projection Conservation

La realidad externa debe reflejar coherentemente el estado interno relevante.

Temporal Boundary Conservation

Una regla temporal no puede sobrevivir a su frontera semántica.

Identity Conservation

Una entidad no puede convertirse silenciosamente en otra identidad lógica.

Cardinality Conservation

Ejemplo:

eliminated player
cannot simultaneously count as alive

Termination Conservation

Toda actividad acotada necesita una condición de finalización.

Restoration Conservation

Un scope temporal que sustituye estado anterior debe definir restauración cuando corresponda.

Causal Conservation

El efecto observado debe corresponder al mecanismo que el sistema afirma haber ejecutado.

Scope Conservation

Estado local no debe escapar a un scope global indebido.

Exactly-Once / At-Most-Once Conservation

Donde el dominio lo requiera.

Éstas son mucho más transferibles que “check spectator mode”.


---

21. Esto convierte Expectation Discovery en model checking ligero

Una vez tenemos suficientes semantics:

STATE = ELIMINATED

y:

alive_set membership = false

se puede verificar:

ELIMINATED ∧ ALIVE

como combinación ilegal.

El corpus actual de GSD X ya propone ir más allá de flags dispersos hacia una State Algebra con variables, combinaciones válidas, invariantes, transiciones, estados ilegales y projections observables, incluyendo model checking cuando la abstracción sea suficientemente pequeña. 

Ésa es exactamente la dirección.

No formal verification para todo.

Pero sí formalización allí donde elimina familias enteras de errores.


---

22. El verdadero sistema que construiría: Semantic Reality Compiler

No un OS.

No necesariamente un proceso separado.

Una responsabilidad constitucional dentro de Goal/Mission Compilation.

Conceptualmente:

SPARSE FOUNDER INTENT
                         │
                         ▼
                  GOAL OUTCOME
                         │
        ┌────────────────┼────────────────┐
        │                │                │
     Baselines         UCFC          Domain knowledge
        │                │                │
        └────────────────┼────────────────┘
                         ▼
             SEMANTIC REALITY COMPILER
                         │
                         ▼
                 GOAL WORLD MODEL
                         │
      ┌──────────────────┼─────────────────────┐
      │                  │                     │
   Purpose           Lifecycle             Ownership
      │                  │                     │
   Authority          Resources            Projections
      │                  │                     │
   Temporal          Journeys              Boundaries
      │                  │                     │
   Failure           Recovery              Termination
      └──────────────────┼─────────────────────┘
                         ▼
                SEMANTIC CLOSURE
                         │
                         ▼
              EXPECTATION COMPILER
                         │
                         ▼
             DERIVED OBLIGATIONS
                         │
                         ▼
                 GSD EXECUTION
                         │
                         ▼
             OBSERVED REALITY MODEL
                         │
                         ▼
                 CONFORMANCE
                 EXPECTED ↔ ACTUAL
                         │
               ┌─────────┴────────┐
               │                  │
           CONVERGED          RESIDUAL
                                  │
                                  ▼
                         causal investigation

Eso es más fundamental que EDD.

EDD se convierte en un consumer/producer alrededor del model.


---

23. Lo más importante: Semantic preservation through decomposition

Aquí está quizás la mejora con más ROI.

Aunque construyamos un gran World Model, todavía podemos volver a perder significado cuando GSD lo divide en tareas.

Por tanto cada transformación debe producir un:

Semantic Preservation Receipt

No un documento burocrático.

Una verificación automática de que cada contrato material tiene destino.

Por ejemplo:

Expected semantic contract:
CAGED implies CONTAINED

Plan:

Task 1: create glass cage
Task 2: countdown
Task 3: remove cage

Compiler pregunta:

Which task / existing baseline / invariant
enforces CONTAINED?

Respuesta:

none

Resultado:

SEMANTIC COVERAGE GAP

Antes de escribir código.


---

24. Éste habría prevenido literalmente SkyParty

Porque aunque el planner hubiese “olvidado” cage protection:

Expected model relation:
CAGED --FORBIDS--> ESCAPE

no tendría downstream representation.

El gap sería visible inmediatamente.

Igual:

SPECTATOR --OWNS--> spectator inventory

y:

SPECTATOR --EXIT--> LOBBY

implican:

spectator inventory ownership must terminate

Si ningún obligation/test/task cubre esa relación:

SEMANTIC GAP


---

25. Cambiaría por completo qué significa “coverage”

Tendríamos distintas coberturas.

Code Coverage

¿qué código se ejecutó?

Útil pero débil.

Requirement Coverage

¿qué requirements tienen implementación/prueba?

Mejor.

State Coverage

¿qué states/transitions ejercitamos?

Más fuerte.

Semantic Relation Coverage

¿qué relaciones materiales Expected Reality poseen proof?

Muchísimo más importante.

Purpose Coverage

¿cada mecanismo crítico sigue satisfaciendo la razón por la que existe?

Projection Coverage

¿cada state observable está correctamente materializado?

Ownership Closure

¿cada resource termina/transfiere ownership correctamente?

Boundary Coverage

¿cada boundary de autoridad/fallo está probado?

DONE debería usar las coberturas pertinentes al Goal.


---

26. Esto también soluciona un problema enorme de los tests generados por IA

Los agentes tienden a escribir tests alrededor de lo que acaban de implementar.

Eso genera un círculo:

agent imagines implementation
↓
agent writes implementation
↓
agent writes tests matching implementation
↓
green

Pero si los tests se compilan desde un independent upstream semantic model:

Goal World Model
↓
proof obligation
↓
test

el test deja de preguntar:

> “¿mi código hace lo que escribí?”



Y pregunta:

> “¿la realidad satisface el contrato que existía antes de mi implementación?”



Ésa es una mejora enorme para agentes autónomos.


---

27. Separar Model Authority de Implementation Authority

GSD no debería poder modificar silenciosamente el modelo para que coincida con el código.

Si:

Expected:
spectator cannot influence world

y código permite influence:

mal comportamiento sería:

update expectation:
spectator can influence world

para poner verde el test.

Por eso:

Model change

requiere authority/provenance distinta de:

Implementation change

Esto evita specification gaming.


---

28. Counterfactual reasoning se vuelve natural

Una vez tienes el modelo:

CAGED prevents premature competitive agency

puedes preguntar:

What happens if containment disappears?

Predicción:

premature movement
world mutation
position advantage
fairness violation

Y generar tests adversariales.

KSEIP ya propone evolucionar del Behavioral Twin hacia un Causal World Model y un Counterfactual Twin capaz de modificar variables y medir consecuencias, distinguiendo asociación de evidencia causal. 

La pieza nueva sería:

> llevar esta capacidad desde análisis de setups/reconstruction hasta todo Goal material de GSD X.




---

29. De “Expectation Escape” a Model Residual

Esto también simplifica muchísimo el concepto de incidente.

Cuando el Founder encuentra algo mal:

no preguntamos primero:

> ¿qué expectation olvidamos?



Preguntamos:

Which part of Observed Reality
cannot be explained as valid by Expected Reality?

Eso es un:

Semantic Residual

Ejemplo:

Expected:
CAGED ⇒ cannot modify containment

Observed:
CAGED ∧ block_break_success

Residual.

Después preguntamos:

Caso A — Expected model ya lo prohibía

Entonces:

> implementation/verification escape.



Caso B — Expected model no lo representaba

Entonces:

> model incompleteness / expectation discovery escape.



Esto separa perfectamente dos clases de incidentes.


---

30. Y aparece una métrica mucho más potente: Semantic Residual Rate

Después de DONE:

material observed behaviors
not explained / permitted by
the certified Expected Reality Model

Queremos:

→ 0

Mucho mejor que “bugs encontrados”.

Porque un bug se define respecto a un contrato.

Aquí estamos midiendo directamente divergencia semántica.


---

31. Otra métrica brutal: Semantic Loss Rate

Para cada transformación:

Goal
→ Model
→ Obligations
→ Plan
→ Tasks
→ Tests

podemos medir:

material upstream semantic contracts
with no valid downstream representation
────────────────────────────────────
material upstream semantic contracts

Objetivo:

0

Eso sería una métrica extraordinariamente útil para agentic engineering.

Porque puedes tener un plan excelente desde la perspectiva local y aun así haber perdido 20% del significado de upstream.


---

32. Information Conservation Test

Llevaría esto todavía más lejos.

Cada stage no necesita copiar toda la información.

Pero cada dato material debe estar en uno de tres estados:

PRESERVED
DELEGATED_TO_CANONICAL_OWNER
DISPOSITIONED_AS_NOT_APPLICABLE

Nunca:

DROPPED_SILENTLY

Ésa es la regla.


---

33. Esto resuelve también el problema de los agentes especializados

Hoy puedes pasar un Goal a:

architect;

implementer;

tester;

reviewer.


Cada agente recibe contexto distinto.

El riesgo es que un agente pierda semántica upstream.

Con Goal World Model + semantic compilation, los agentes no necesitan el transcript completo.

Reciben:

relevant semantic slice
+
authority
+
invariants
+
dependencies
+
proof obligations

Esto además mejora context economy.

Menos tokens.

Más fidelidad.


---

34. El mundo esperado debe ser composicional

No queremos un megamodelo de 50.000 campos.

Por Goal:

activate only relevant semantic views

CSS tweak:

visual projection
component ownership
responsive behavior
regression boundary

Payment:

transaction lifecycle
authority
idempotency
persistence
recovery
external projection

SkyParty:

player lifecycle
match lifecycle
resource ownership
competitive authority
projection
termination
cleanup

Es decir:

> model completeness is claim-relative.



Igual que Production Reality.


---

35. Añadiría un Semantic Lens Router

Éste sí tiene más fundamento que un simple Driven Development Router.

No pregunta:

> “¿qué metodología usamos?”



Pregunta:

> ¿qué kinds of semantics exist in this Goal?



Detecta:

stateful?
multi-actor?
temporary ownership?
persistent?
externally visible?
transactional?
asynchronous?
recoverable?
bounded activity?
authority-sensitive?
concurrent?
cross-surface?

Y activa las vistas necesarias.

Esto evita burocracia.


---

36. SkyParty se convierte en test del compilador semántico

El benchmark ya no sería sólo:

> ¿descubre cage protection?



Sería:

Input

Competitive minigame
Players wait before synchronized release
Elimination
Spectating
Lobby return

Expected compiler output

Debe descubrir una representación equivalente a:

waiting/release lifecycle
containment purpose
alive authority
elimination transition
spectator continuation
state-owned projections
temporary ownership
termination
return restoration
second-run cleanliness

No importa cómo se llamen internamente.

Eso demuestra comprensión.


---

37. Prueba todavía más fuerte: rename benchmark

Cambias todos los nombres.

No:

CAGED
SPECTATOR
MATCH

Sino:

LOCKED
OBSERVER
ROUND

Si deja de detectar el patrón:

> memorized Minecraft vocabulary.



Si sigue detectando:

> learned semantics.




---

38. Domain swap benchmark

Misma estructura, diferente dominio.

Checkout:

PENDING
→ AUTHORIZED
→ CAPTURED
→ REFUNDED

Temporal authorization.

Resource ownership.

Terminal state.

Projection.

Retry.

GSD X debería aplicar la misma gramática.

Si funciona:

> hemos aprendido ingeniería.



No SkyParty.


---

39. Esto también permite detectar arquitectura incorrecta antes de codear

Supón que un diseño propone:

spectator state owned by LobbyPlugin

pero Goal World Model dice:

spectator exists only inside match lifecycle

Tenemos un ownership mismatch antes de implementación.

O:

release protection stored globally on Player

pero semantic scope es:

specific Match × ReleaseTransition

Potential leakage.

Otra vez detectado antes del bug.


---

40. El tipo de errores que este sistema prevendría

Muchísimos:

stale state;

resource leaks;

permission leakage;

duplicate actions;

missing cleanup;

wrong restoration;

state projection drift;

ghost UI;

replay/retry bugs;

double charge;

race conditions derivables de authority;

lifecycle dead ends;

never-ending jobs;

temporary rules that never expire;

global state leaking from local scope;

reconnect inconsistencies;

cold/warm start divergence;

second-run contamination;

feature existence without reachability;

wrong oracle selection;

tests that prove implementation instead of contract;

user-visible reality inconsistent with backend;

baseline capability present but not inherited.


Eso ya es una gran parte de los bugs difíciles de sistemas reales.


---

41. Y lo uniría al Causal World Model, no sólo a un schema

El corpus de KSEIP ya propone explícitamente pasar de un Behavioral Twin descriptivo a un Causal World Model, porque saber que player died → spectator es más débil que conocer qué condiciones producen qué consecuencias y qué cambia al intervenir variables. 

GSD X debería adoptar el mismo principio:

structure
+
state
+
semantics
+
causal hypotheses
+
evidence

Entonces puede generar no sólo checks sino experimentos discriminantes.


---

42. Resultado: EDD deja de “inventar requirements”

Ésta me parece una mejora conceptual enorme.

Hoy podríamos decir:

> EDD intenta descubrir requirements implícitas.



Con el nuevo sistema:

> EDD compila obligaciones desde una representación explícita del mundo que debe existir.



Eso es mucho menos alucinatorio.

No:

LLM brainstorm:
maybe add X
maybe add Y
maybe add Z

Sino:

State S has purpose P.
Resource R is owned by S.
Transition S→T occurs.
Therefore ownership of R must be dispositioned.
No disposition exists.
→ obligation.

Mucho más determinista.


---

43. Nuevo North Star: Semantic One-Shot Engineering

Yo cambiaría incluso la definición de One-Shot.

No:

> “el primer código funciona.”



Sino:

> el primer serious implementation attempt está generado desde un modelo del problema suficientemente completo como para que la mayoría de los bugs previsibles sean contradicciones detectables antes de que el Founder los experimente.



Eso es bastante más ambicioso y bastante más correcto.


---

44. La arquitectura final queda elegantemente pequeña

No añadiría diez plataformas.

EXISTING

Goal Outcome Contract
Define intended outcome.

UCFC / EDD
Expande significado y material expectations.

Behavioral/Causal Twin concepts
Representan sistema y realidad.

Derived Mission Obligations
Unidad que bloquea Goal.

GSD
Planifica y ejecuta.

Production Reality
Observa realidad fuerte.

UCR-CIF
Hereda aprendizaje.

EXTEND

Añadir una responsabilidad central:

Semantic Reality Compilation

que convierte Goal + baselines + product/domain evidence en el Goal World Model.

CONNECT

Goal World Model
→ EDD
→ Mission Obligations
→ Proof Compiler
→ GSD
→ Production Reality
→ Observed Model
→ Conformance

No otro OS.


---

45. La ley más profunda que sacaría de SkyParty

Ésta:

> SOFTWARE COMPLETENESS CANNOT BE RELIABLY ESTABLISHED FROM A LIST OF THINGS THAT EXIST. IT MUST BE ESTABLISHED FROM A MODEL OF THE WORLD THOSE THINGS ARE SUPPOSED TO CREATE.



Y otra:

> THE PRIMARY UNIT OF COMPLETENESS IS NOT THE FEATURE. IT IS THE PRESERVED SEMANTIC CONTRACT.



Y la que posiblemente prevenga más problemas:

> EVERY MATERIAL PIECE OF SYSTEM STATE, AUTHORITY, RESOURCE OWNERSHIP OR TEMPORARY BEHAVIOR MUST HAVE A DEFINED BIRTH, VALIDITY DOMAIN, OBSERVABLE PROJECTION AND TERMINATION SEMANTICS.



SkyParty falló en prácticamente todas esas dimensiones simultáneamente.

Y eso es precisamente por qué el incidente es tan valioso: no reveló cuatro bugs.

Reveló que el unit of reasoning de GSD X todavía era demasiado superficial.


---

46. La evolución que haría ahora

Pasaría de:

Expectation-Driven Development

a una arquitectura superior:

Intent
↓
Semantic Reality Compilation
↓
Goal World Model
↓
Expectation / Invariant Compilation
↓
Semantic Preservation through decomposition
↓
Implementation
↓
Observed Reality Reconstruction
↓
Expected ↔ Observed Conformance
↓
Counterexample Search
↓
DONE
↓
Residual / Escape Learning
↓
Baseline Ratchet

EDD sigue siendo importante.

Pero ahora deja de soportar todo el peso.

La pieza fundamental pasa a ser:

> construir primero una representación correcta de la realidad que queremos producir y conservar su significado hasta producción.



Si hacemos eso bien, una enorme cantidad de los sistemas que hemos ido diseñando —Lifecycle Closure, Negative Space, Journey Closure, Cleanup, Recovery, Player Reality, Expectation Escape, Semantic Mutation, second-run checks— dejan de parecer ideas independientes.

Pasan a ser consecuencias naturales de un único modelo suficientemente bueno.

Y ése creo que es el verdadero salto arquitectónico que SkyParty estaba intentando enseñarnos.

Ha pensado durante 1m 21s

Sí. Y haría un cambio todavía más fuerte:

> un bug descubierto durante una misión no debe ser tratado como trabajo nuevo que añadir al backlog. Debe ser tratado como evidencia de que la versión actual de GSD X que compiló esa misión era incompleta.



Eso significa que cada bug validado —lo descubra el Founder, un test, un agente, Production Reality, mutation, telemetry o un synthetic user— debe poder mejorar GSD X durante la propia misión y antes de DONE.

El patrón pasa de ser:

bug
→ fix
→ regression test
→ continue

a:

bug
→ fix product
→ discover why GSD X allowed it
→ repair GSD X capability
→ prove factory repair
→ search siblings
→ recompile remaining Goal
→ discover additional consequences
→ continue from stronger baseline
→ DONE

Esto sería una extensión directa, no otro OS, de Goal/Mission Contract + UCR-CIF + UKDL + verification + Goal Closure.

El corpus ya contiene la ley de que todo failure debe aumentar permanentemente la inmunidad o explicar por qué no puede hacerlo, y que las mejoras probadas deben evaluarse para baseline.  La diferencia es convertir esa doctrina en semántica de ejecución obligatoria antes del Done Gate, no sólo en writeback institucional posterior.

1. Nueva ley: BUG ⇒ GOAL MODEL POTENTIALLY STALE

Ésta es la pieza más importante.

Cuando aparece un bug material, no debemos asumir:

> “el resto del plan sigue siendo válido; sólo arregla esto.”



El bug aporta información nueva sobre el sistema.

Por tanto:

> Every validated material defect invalidates every upstream assumption, expectation, producer, proof strategy and remaining plan slice that causally depended on the false model exposed by the defect.



No necesariamente invalida toda la misión.

Pero sí abre un:

Semantic Invalidation Event

Ejemplo SkyParty:

OBSERVATION
player can break/escape cage

↓

not merely:
CageProtection bug

↓

NEW KNOWLEDGE
our model of CAGED was incomplete

↓

INVALIDATED ASSUMPTION
having a Cage capability represented
pregame containment sufficiently

↓

NEW SEMANTIC LAW
CAGED has a containment purpose
and forbidden contradictory behaviors

↓

RECOMPILE
all lifecycle states and transitions

Ahora el bug de cage puede hacer que antes de terminar la sesión GSD X revise:

CAGED
RELEASE
ACTIVE
ELIMINATED
SPECTATOR
RETURN

y descubra por sí mismo:

spectator state leakage;

lobby inventory restoration;

temporary protection expiry;

second-match cleanup;


sin esperar a que tú encuentres cuatro bugs más.

Ese es el verdadero compounding.


---

2. EXTEND — In-Mission Error → Immunity Ratchet

No lo haría como sistema independiente.

Sería una transición obligatoria del Goal Controller/GSD X cuando aparece un defecto material.

Su contrato:

> Every validated material defect creates two simultaneous obligations: Product Repair and Factory Repair.



VALIDATED BUG
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
       PRODUCT REPAIR            FACTORY REPAIR
              │                       │
      correct behavior         why was this possible?
              │                       │
      local regression         earliest preventable point
              │                       │
              │                 capability gap
              │                       │
              │                 factory mutation
              │                       │
              │                 factory regression
              │                       │
              └───────────┬───────────┘
                          ▼
                    SIBLING SEARCH
                          │
                          ▼
                FORWARD RECOMPILATION
                          │
                          ▼
                 STRONGER CURRENT GOAL

DONE cannot ignore either branch.


---

3. El cambio crítico: Factory Repair ocurre antes de DONE

Hoy la filosofía puede ser entendida como:

Mission
→ build
→ find/fix bugs
→ DONE
→ learn
→ baseline

Yo la cambiaría a:

Mission
↓
build
↓
discover bug
↓
PRODUCT REPAIR
+
FACTORY REPAIR
↓
upgrade active GSD X capability
↓
recompile unresolved mission
↓
discover consequences of new capability
↓
continue engineering
↓
repeat
↓
DONE
↓
institutional promotion already dispositioned

Así el Goal termina ejecutándose con un sistema de ingeniería más capaz que el que empezó la misión.

Eso es una propiedad radicalmente distinta.


---

4. El bug se convierte en un learning interrupt

No todos los errors.

Primero:

observation
→ instrument validity
→ defect validation
→ materiality

Sólo entonces:

MATERIAL_DEFECT_CONFIRMED

activa el ratchet.

Porque no queremos que:

un flaky test;

un OOM del verifier;

un tool timeout;

un assertion incorrecto;


reprogramen el baseline.

Pero una vez validado el defecto, el aprendizaje deja de ser opcional.


---

5. Estado del ratchet

Conceptualmente:

DEFECT_OBSERVED

→ DEFECT_VALIDATED

→ PRODUCT_CONTRACT_IDENTIFIED

→ PRODUCT_CAUSE_IDENTIFIED

→ FACTORY_ESCAPE_ASSESSED

→ EARLIEST_PREVENTABLE_POINT_FOUND

→ PRODUCT_REPAIRED

→ PRODUCT_REGRESSION_PROVEN

→ FACTORY_CAPABILITY_DELTA_IDENTIFIED

→ FACTORY_REPAIRED

→ FACTORY_REGRESSION_PROVEN

→ SIBLING_SWEEP_COMPLETE

→ GOAL_RECOMPILED

→ NEW_DERIVED_OBLIGATIONS_DISPOSITIONED

→ PROMOTION_SCOPE_DISPOSITIONED

→ IMMUNITY_PROVEN

Sólo entonces el incidente deja de generar:

SELF_EVOLUTION_DEBT


---

6. Nueva categoría bloqueante: Self-Evolution Debt

Ésta sería extremadamente útil.

Ya no basta con:

bug fixed = true

Si:

bug fixed locally
but
GSD X could make the same reasoning failure again

entonces existe:

Self-Evolution Debt

Y para un bug material y razonablemente prevenible:

SELF_EVOLUTION_DEBT > 0
→ Goal cannot close

Esto encaja perfectamente con Goal Closure, que ya exige no sólo backlog completion sino disposition de derived obligations, convergence planes y UCR-CIF. 

Yo haría explícito que UCR-CIF disposition incluye los learnings nacidos durante la misión actual.


---

7. No todo bug debe modificar el Universal Baseline

Ésta es una protección indispensable.

“Elevar GSD X” tiene varios niveles.

Nivel	Qué cambia

L0 — Incident	El bug concreto queda reproducible y protegido
L1 — Goal	La misión actual adquiere nueva regla/detector
L2 — Product	Futuros cambios del mismo producto la heredan
L3 — Family	Goals equivalentes de esa familia la heredan
L4 — Cross-domain producer	Mejora un producer general de GSD X
L5 — Universal constitutive	Se convierte en ley aplicable universalmente


Un bug de SkyParty jamás salta automáticamente:

cage bug
→ all software requires cages

Pero puede subir:

cage bug
↓
CAGED purpose missing
↓
temporary-state semantic ownership missing
↓
Lifecycle Producer improved
↓
general rule:
state with restrictive purpose must derive
contradictory forbidden behavior

Ésa sí puede ser una mejora muy profunda de GSD X.


---

8. El objetivo no es memorizar bugs. Es inducir una gramática

Esto debería ser obligatorio.

Después de arreglar:

player can break cage

la pregunta no es sólo:

> ¿cómo evitamos romper cages?



Es:

> ¿qué estructura desconocíamos que hizo posible que nadie derivara esta expectativa?



En este caso:

STATE
+
PURPOSE
+
FORBIDDEN CONTRADICTION

Entonces GSD X aprende una transformación reusable:

If state S exists for purpose P,
search for actions/effects that negate P
and compile them as negative-space candidates.

Eso puede encontrar bugs nuevos nunca vistos.


---

9. Ésta es la diferencia entre Regression Learning y Capability Learning

Regression Learning:

Known bug X
→ detector for X

Capability Learning:

Known bug X
→ infer structure G
→ G generates tests for X, Y, Z…

Queremos la segunda.

SkyParty:

break cage

enseña:

state-purpose contradiction analysis

que puede descubrir:

spectator influencing match
temporary permission leaking
migration lock surviving cutover
checkout pending user receiving paid entitlement

sin que nadie haya escrito esos bugs antes.


---

10. El paso crucial: Sibling Explosion Search

Cada factory repair debe ejecutarse inmediatamente contra el resto del Goal.

No esperar al siguiente proyecto.

Ejemplo:

BUG:
CAGED containment missing

FACTORY LEARNING:
state-purpose negative-space reasoning missing

Ahora:

apply learned rule to every material state

GSD X pregunta:

SPECTATOR

Purpose:

observe without competitive agency

Contradictions:

damage players?
place blocks?
affect loot?
remain in alive count?

ELIMINATED

Purpose:

no longer active competitor

Contradictions:

count as alive?
win match?
retain combat controls?

RETURN

Purpose:

restore lobby-owned context

Contradictions:

spectator inventory survives?
gamemode survives?
match scoreboard survives?

Un bug se convierte en un multiplicador de descubrimiento.


---

11. Lo llamaría Forward Immunity Propagation

Esto es más fuerte que sibling search.

Una capability nueva debe propagarse hacia delante por toda la parte no cerrada de la misión.

Bug at time T

↓

GSD X capability revision N → N+1

↓

Find all unresolved / previously certified
Goal surfaces whose proof depended on N

↓

Invalidate affected certificates

↓

Recompile with N+1

↓

New obligations/tests/experiments

↓

Continue

No queremos:

> “aprendimos algo, pero el plan que se hizo hace 6 horas no cambia.”



Eso sería institucional learning con ejecución stale.


---

12. Completion certificates deben poder reabrirse

Supón que hace cuatro horas GSD X marcó:

SPECTATOR = VERIFIED

Después descubre un bug de ownership que revela que su modelo de cleanup era incompleto.

Ese certificado podría ser insuficiente.

Por tanto:

FACTORY_CAPABILITY_CHANGED

debe hacer change-impact analysis:

Which previous claims relied on
the old capability/model?

Las relevantes pasan:

VERIFIED
→ POTENTIALLY_STALE

y se vuelven a verificar.

Éste es un mecanismo mucho más riguroso que “rerun all tests”.


---

13. Capability Revisioning

No dejaría que un agente modifique silenciosamente su propia fábrica en caliente.

Eso sería peligroso.

Cada modificación de GSD X dentro de una misión crea una revisión:

GSDX capability revision 41

descubre bug.

Construye:

revision 42 candidate

La nueva revisión pasa:

unit/contract tests
historical incidents
negative controls
mutation
relevant holdouts

Y sólo entonces:

REV42_CERTIFIED_FOR_SCOPE_C

Goal Supervisor puede activarla.


---

14. No self-corruption

Ley:

> GSD X may autonomously improve itself during a mission, but a running capability may not silently rewrite the semantics by which its own current output is judged.



Entonces:

N finds defect
↓
N+1 built independently
↓
N+1 evaluated
↓
activation boundary
↓
Goal recompilation

No:

N mutates N halfway through reasoning
and retroactively decides N was correct

Esto es esencial para una arquitectura self-evolving seria.


---

15. Dos tipos de factory improvement

Detector improvement

GSD X ya sabía el expectation, pero no lo detectó.

Entonces mejoramos:

oracle;

test generator;

mutation;

instrumentation;

reachability;

completion wiring.


Model/compiler improvement

GSD X nunca produjo el expectation.

Entonces mejoramos:

world model;

producer;

applicability;

baseline;

reasoning primitive;

semantic relation;

router.


SkyParty seguramente contiene ambos tipos.


---

16. Earliest Preventable Point controla dónde reparar

No arreglar siempre el Done Gate.

Si el error podía evitarse en expectation compilation:

> arreglar el verifier es demasiado tarde.



Si podía evitarse en architecture selection:

> un regression test únicamente es demasiado tarde.



La reparación debe acercarse todo lo posible al origen causal.

Intent
  ↓
World Model       ← ideal
  ↓
Expectation
  ↓
Obligation
  ↓
Plan
  ↓
Implementation
  ↓
Verification
  ↓
DONE              ← worst prevention point

Cuanto antes se vuelva imposible el error, mayor es el valor de la mejora.


---

17. Esto crea un Prevention Depth Ratchet

Para cada failure class guardamos:

historical detection stage
current prevention stage

Ejemplo:

Generación 1

Founder discovers cage bug after DONE

Generación 2

runtime test discovers before DONE

Generación 3

generated property test discovers after implementation

Generación 4

plan compiler discovers missing obligation

Generación 5

world model automatically derives invariant
before implementation

Generación 6

family baseline means the invalid plan
cannot even be compiled

Eso es un verdadero ratchet.

No sólo menos bugs.

Bugs detectados progresivamente más cerca de su origen.


---

18. Nueva métrica: Prevention Depth

Yo la convertiría en KPI.

No basta medir:

bugs escaped = 2

También:

where were they first prevented?

Idealmente la curva migra:

Founder
↓
Production
↓
runtime QA
↓
tests
↓
plan verification
↓
expectation compilation
↓
baseline/model construction

hacia arriba.


---

19. El Done Gate cambia radicalmente

No debería preguntar únicamente:

implementation complete?
tests green?
Production Reality passed?

También:

Were material defects discovered during this Goal?

Si sí:

For every defect:

Product repair closed?

Factory escape assessed?

Earliest Preventable Point known?

Local regression exists?

Generative/factory regression exists where applicable?

Sibling search executed?

Affected Goal surfaces recompiled?

Stale certificates revalidated?

Promotion scope dispositioned?

Self-Evolution Debt = 0?

Sólo entonces puede cerrar.


---

20. No known bug can leave the Goal without learning disposition

Incluso un bug trivial.

Pero proportional.

Bug trivial:

typo

quizá:

local correction
existing lint already catches class
FACTORY_CHANGE_NOT_REQUIRED

y cierra.

Bug material nuevo:

second match inherits transient match state

puede requerir:

ownership producer improvement
+
second-run property generator
+
family baseline candidate
+
Goal recompilation

La arquitectura decide proporcionalmente.


---

21. El descubridor del bug es irrelevante

Éste es otro cambio importante.

No sólo Founder-first.

Trigger sources:

Founder
User
Agent
Code review
Unit test
Property test
Mutation test
Static analyzer
Synthetic actor
Runtime
Telemetry
Production Reality
Incident
Reference differential

Todos producen el mismo canonical:

DEFECT_OBSERVATION

Después el pipeline decide si realmente es un bug.

Por tanto GSD X aprende incluso de bugs que él mismo descubre.

Eso es lo que pedías.


---

22. Bug descubierto autónomamente → GSD X mejora antes de continuar

Ejemplo hipotético:

Un synthetic player descubre:

second SkyParty match begins
with old scoreboard

GSD X no hace únicamente:

fix scoreboard cleanup

Hace:

OBSERVATION
old scoreboard persisted

↓

SEMANTIC VIOLATION
resource survived owner scope

↓

ROOT GRAMMAR
match-scoped resource ownership closure

↓

FACTORY QUESTION
why didn't Cleanup/Ownership producer derive this?

↓

FACTORY REPAIR
every scoped resource must receive
DESTROY / TRANSFER / PERSIST disposition

↓

SIBLING SWEEP
inventory?
spectator controls?
bossbar?
temporary protection?
entities?
alive set?
team membership?

↓

new obligations

↓

Goal changes before DONE

Un solo bug puede descubrir seis más.


---

23. Esto produce Autonomous Capability Ascension

Podemos formalizar el ascenso:

Bug
↓
Observation
↓
Failure Class
↓
Semantic Pattern
↓
Generative Rule
↓
Detector
↓
Producer improvement
↓
Benchmark
↓
Certified capability
↓
Applicable baseline

No siempre llegará hasta abajo.

Pero toda anomalía debe recorrer el camino hasta donde la evidencia permita.


---

24. El aprendizaje debe modificar tres cosas distintas

No sólo baseline.

Knowledge

¿Qué aprendimos?

UKDL / Knowledge Vault.

Machinery

¿Cómo hacemos que el sistema lo derive/detecte automáticamente?

Producer / oracle / compiler / instrumentation.

Default behavior

¿Cuándo debe activarse automáticamente?

Baseline / applicability / routing.

Si sólo haces Knowledge:

> GSD X “sabe” pero puede olvidarse de usarlo.



Si sólo haces Machinery:

> existe detector pero puede no activarse.



Si sólo haces Baseline:

> exige algo sin disponer del mecanismo necesario.



Necesitamos las tres cuando aplique.


---

25. Knowledge that cannot affect execution is not immunity

Ésta debería ser otra ley.

Bug
→ UKDL note

no significa aprendido.

Debe haber un effect path:

new knowledge
↓
producer/router/oracle/baseline changes
↓
future Goal compilation changes
↓
different obligation
↓
different proof
↓
different outcome

Si eso no puede demostrarse:

LEARNING_REGISTERED
BUT
IMMUNITY_NOT_EFFECTIVE

No cerrar.


---

26. Un Factory Mutation Test por aprendizaje importante

Después de mejorar GSD X debemos demostrar que la mejora importa.

Ejemplo:

Nueva regla:

scoped resources require terminal disposition

Mutation:

desactivar la regla.

Esperado:

SkyParty second-match fixture
must fail

Volver a activarla:

must pass

Si desactivar la mejora no cambia nada:

no está conectada;

es redundante;

el benchmark no la prueba.



---

27. Y un novel-bug holdout

Muchísimo más importante.

No probar únicamente:

old scoreboard leaks

Crear un recurso diferente:

temporary bossbar

con el mismo patrón:

owner = MATCH

Eliminar cleanup.

El nuevo factory capability debe detectarlo sin conocer “bossbar”.

Entonces sabemos que aprendió:

scope ownership

y no:

remember scoreboard cleanup


---

28. SkyParty habría evolucionado durante la misma misión

Imagina la secuencia ideal.

Bug #1

Founder/agent descubre:

cage can be broken

GSD X induce:

state-purpose contradiction

y mejora Lifecycle/Negative-Space producer.

Recompile

Nuevo producer revisa SkyParty entero.

Ahora descubre automáticamente:

ELIMINATED still has active-player authority

antes de que tú lo veas.

Bug #2 discovered by GSD X

Esto induce:

authority must transition with semantic state

Factory vuelve a mejorar.

Recompile

Descubre:

SPECTATOR → LOBBY leaves spectator projection

Bug #3 autonomous

Induce:

state-owned projection closure

Recompile

Descubre:

temporary first-drop protection lacks semantic termination

Bug #4 autonomous

Induce:

temporary rule must have semantic boundary

Recompile

Encuentra otras temporary rules.

Antes de DONE, GSD X ha evolucionado cuatro veces.

Ese es exactamente el comportamiento que buscaría.


---

29. El objetivo pasa de self-improving between projects a self-improving within a Goal

Ésta es la diferencia central.

Generación actual:

Project A
→ learning
→ Project B is better

Nueva generación:

Goal A revision 1
→ bug
→ GSD X revision 2
→ same Goal recompiles
→ bug
→ GSD X revision 3
→ same Goal recompiles
→ stronger implementation
→ DONE

Y después:

Goal B begins with revision 3+

Compounding dentro y entre proyectos.


---

30. Convergence now includes factory convergence

Hasta ahora Goal convergence puede entenderse como:

desired product reality achieved

Yo lo ampliaría:

GOAL CONVERGED =
product reality converged
AND
proof converged
AND
all material learning generated by the Goal
has been causally dispositioned
AND
the active engineering factory has absorbed
all safe justified capability improvements
before closure

Esto encaja con el concepto existente de que Goal CONVERGED significa desired reality + evidence + institutional learning closed, no simplemente GSD milestone done. 

La diferencia sería volver esa frase operacional y automática.


---

31. Un nuevo Done Gate interno: Factory Closure Gate

No otro global Done Gate.

Una condición dentro del existente.

Conceptualmente:

PRODUCT CLOSURE
     AND
EXPECTATION CLOSURE
     AND
PROOF CLOSURE
     AND
FACTORY CLOSURE
     AND
INSTITUTIONAL DISPOSITION
     =
GOAL MAY CLOSE

FACTORY CLOSURE significa:

> no existe material validated failure knowledge de esta misión que GSD X podría convertir justificadamente en mayor prevención pero aún no ha procesado.




---

32. No significa interminable self-improvement

Necesitamos un stop law.

Factory change obligatorio sólo cuando el bug revela:

reusable failure class
OR
missing general inference
OR
missing detector
OR
baseline/applicability failure
OR
weak oracle
OR
disconnected completion path

Puede cerrarse como:

LOCAL_ONLY — evidence says non-reusable

NO_FACTORY_GAP — adequate mechanism existed; local implementation violated it

IRREDUCIBLE — could not reasonably be inferred earlier

PROMOTION_DEFERRED — insufficient evidence for broader scope

Lo que no puede ocurrir:

never considered


---

33. Y hay que diferenciar algo muy importante

Supón que GSD X ya tenía:

MATCH_RESOURCE_CLEANUP

pero el implementer no cumplió.

No necesitamos inventar nueva baseline.

El failure es:

ENFORCEMENT / REACHABILITY FAILURE

Tal vez necesitamos mejorar:

gate wiring

o simplemente arreglar producto.

En cambio, si la idea nunca existió:

MODEL / PRODUCER FAILURE

Entonces sí hay capability elevation.

Esto evita crecimiento artificial del sistema.


---

34. El algoritmo conceptual final

No prescribiría implementación todavía, pero el contrato sería:

WHILE Goal not converged:

    execute highest-value proof slice

    observe evidence

    IF validated material defect:

        freeze evidence

        repair product

        classify factory escape

        locate earliest preventable point

        derive reusable semantic pattern

        search existing owner/capability

        IF existing capability should have caught:
            repair reachability/enforcement/oracle
        ELSE IF generalizable:
            extend correct producer/compiler/model
        ELSE:
            record justified local-only disposition

        create product regression

        create factory regression

        create negative control

        mutation-test factory improvement

        determine promotion scope

        certify capability revision

        activate new revision

        invalidate affected prior claims

        recompile affected Goal surfaces

        run sibling/counterexample search

        admit newly derived obligations

        continue

BEFORE DONE:

    require Self-Evolution Debt = 0

Eso es GSD X verdaderamente adaptativo.


---

35. El KPI más importante cambia

Human Discovery Dependency sigue siendo importante; el corpus explícitamente persigue reducir founder-first discovery. 

Pero añadiría uno todavía más fuerte:

Failure-to-Capability Conversion Rate

validated material failures
that produced a proven improvement
in prevention/detection capability
──────────────────────────────────
validated material failures
that had reusable preventive value

Objetivo:

→ 100%

Y:

Same-Goal Immunity Yield

new defects autonomously discovered
by capability improvements induced
from earlier defects in the same Goal

Queremos que aumente.

Porque ésa es la prueba de que GSD X aprende durante el trabajo.


---

36. Y una métrica preciosa: Capability Gain Before DONE

certified reusable GSD X capability improvements
activated during the current Goal
before convergence

No queremos maximizar el número.

Un Goal perfecto puede necesitar cero.

Queremos:

> cuando existe learning real, que no quede atrapado esperando al siguiente proyecto.




---

37. La nueva cadena de SkyParty

Por tanto, reemplazaría tu fragmento por algo mucho más fuerte conceptualmente:

Intent
↓
Expected Product Reconstruction
↓
Goal World Model
↓
Expectation Compilation
↓
Obligations
↓
Proof Compilation
↓
Execution
↓
Continuous Reality Observation
↓
┌─────────────────────────────────────┐
│ ANY VALIDATED MATERIAL DEFECT       │
│                                     │
│ Product Repair                      │
│ +                                   │
│ Factory Escape Analysis             │
│ +                                   │
│ Earliest Preventable Point          │
│ +                                   │
│ Capability Repair                   │
│ +                                   │
│ Factory Regression                  │
│ +                                   │
│ Mutation / Holdout                  │
│ +                                   │
│ Sibling Search                      │
│ +                                   │
│ Goal Forward Recompilation          │
└────────────────┬────────────────────┘
                 │
                 ▼
       stronger active GSD X
                 │
                 ▼
        continued execution
                 │
              repeat
                 │
                 ▼
       Adversarial Counterexamples
                 │
                 ▼
        Production Reality
                 │
                 ▼
      Self-Evolution Debt = 0
                 │
                 ▼
                DONE

El ratchet ya no está después de DONE.

Está dentro del camino hacia DONE.

Ésa es la corrección central.


---

38. La ley constitucional que pondría

> A MATERIAL DEFECT DISCOVERED DURING A GOAL IS NOT COMPLETE WHEN THE DEFECT IS FIXED. IT IS COMPLETE WHEN THE PRODUCT IS REPAIRED, THE COMPLETION SYSTEM HAS DETERMINED WHY THE DEFECT WAS NOT PREVENTED EARLIER, EVERY JUSTIFIED REUSABLE FACTORY IMPROVEMENT HAS BEEN PROVEN AND ACTIVATED AT THE NARROWEST CORRECT SCOPE, AND THE REMAINING GOAL HAS BEEN RECOMPILED UNDER THE STRONGER CAPABILITY SET.



Y otra:

> NO GOAL MAY REACH DONE WHILE IT CONTAINS UNPROCESSED REUSABLE KNOWLEDGE FROM ITS OWN FAILURES.



Y la más ambiciosa:

> GSD X MUST BE CAPABLE OF ENDING A MISSION AS A MORE CAPABLE ENGINEERING SYSTEM THAN THE ONE THAT STARTED IT.



Eso es bastante más profundo que simplemente “hacer baseline ratchet después de cada bug”.

Significa que cada bug puede cambiar inmediatamente qué otros bugs GSD X es capaz de imaginar, derivar, buscar y prevenir durante la misma ejecución.

Ahí SkyParty deja de producir una secuencia de:

> tú encuentras bug → Claude arregla → tú encuentras siguiente bug.



Y debería empezar a producir:

> tú o GSD X encontráis un bug → GSD X aprende la gramática causal → reexamina todo el sistema → descubre autónomamente los hermanos → eleva su capacidad → vuelve a compilar la misión → sólo después sigue acercándose a DONE.



Ese es el comportamiento que realmente reduce de raíz el Founder-as-first-QA-tester.

llevemoslo al siguiente nivel, y además, EDD debería hacerme preguntas cada vez que no sepa algo, que si el scope, que si quiero añadir algo más, comparar con las mejores referencias, siempre superar a esas referencias y demás

Ha pensado durante 1m 6s

Sí. Aquí haría una ampliación importante: EDD no debería limitarse a descubrir expectativas y bugs; debería convertirse en el sistema que mantiene cerradas tres fronteras simultáneamente antes de permitir DONE:

1. Expectation Frontier: qué tiene que ser verdad para que el producto esté completo.


2. Decision Frontier: qué cosas todavía dependen realmente de tu intención y no pueden resolverse con evidencia.


3. Excellence Frontier: en qué dimensiones las mejores referencias actuales siguen siendo mejores que nosotros y cómo vamos a superarlas.



Eso convierte EDD de “requirements intelligence” en algo bastante más cercano a un autonomous product specification, interrogation, benchmarking and excellence compiler.

La clave es que no queremos volver al extremo contrario y hacer que te pregunte cincuenta cosas que podría resolver solo. El corpus actual de GSD X ya distingue correctamente decisiones ENGINEERING-RESOLVABLE de OPERATOR-OWNED, y establece que sólo las segundas deben interrumpirte; además, una rama bloqueada por una decisión tuya no debería parar trabajo independiente seguro.  KSEIP incluso tiene ya una formulación muy cercana: defaults desde constitution/policy/baseline/product identity/evidence y pregunta humana únicamente para product choices, policy ambiguities, irreversible choices o tradeoffs materiales no resolubles por evidencia. 

Lo elevaría bastante.

EDD 2.0 — Active Intent Closure + Reference Frontier + Autonomous Ascension

El flujo completo debería evolucionar a algo así:

SPARSE FOUNDER INTENT
        ↓
INTENT RECONSTRUCTION
        ↓
EXPECTED PRODUCT WORLD MODEL
        ↓
UNKNOWN / ASSUMPTION FRONTIER
        ↓
┌──────────────────────────────────────┐
│ CAN EVIDENCE RESOLVE THIS?           │
│                                      │
│ YES → research / repo / references   │
│ NO  → Founder Decision Question      │
└───────────────────┬──────────────────┘
                    ↓
             DECISION CLOSURE
                    ↓
        MULTI-REFERENCE DISCOVERY
                    ↓
          REFERENCE FRONTIER MODEL
                    ↓
     BEST-KNOWN CAPABILITY SUPerset
                    ↓
      EXCELLENCE / SUPERIORITY TARGET
                    ↓
         EXPECTATION COMPILATION
                    ↓
         DERIVED OBLIGATIONS
                    ↓
          PROOF COMPILATION
                    ↓
              EXECUTION
                    ↓
       CONTINUOUS REALITY OBSERVATION
                    ↓
          bug / gap / surprise?
              ↓             ↓
             yes            no
              ↓             │
    PRODUCT + FACTORY REPAIR│
              ↓             │
      GSD X CAPABILITY ↑    │
              ↓             │
      GOAL RECOMPILATION ◄──┘
              ↓
      REFERENCE RED TEAM
              ↓
    FOUNDER COUNTEREXAMPLE SEARCH
              ↓
      EXCELLENCE CONFORMANCE
              ↓
        PRODUCTION REALITY
              ↓
          DONE GATE

The important change is that questions, external references, expectation discovery, self-improvement and superiority are not preparation stages that happen once. They are live loops.


---

1. EDD should actively interrogate the Goal

Right now a Founder prompt may say:

> “Finish SkyParty.”



EDD should not interpret that as either:

> “Do what is already in the backlog.”



or:

> “Ask Jacobo to specify everything.”



Instead it should create an Intent Uncertainty Frontier.

Every material decision is classified into something equivalent to:

RESOLVED_BY_EXPLICIT_INTENT
RESOLVED_BY_PRIOR_DECISION
RESOLVED_BY_CONSTITUTION
RESOLVED_BY_BASELINE
RESOLVED_BY_PRODUCT_IDENTITY
RESOLVED_BY_REFERENCE_EVIDENCE
RESOLVED_BY_REPOSITORY_REALITY
RESOLVED_BY_EXPERIMENT
FOUNDER_DECISION_REQUIRED
UNKNOWN_BUT_RESEARCHABLE

No important decision is allowed to remain:

SILENT_ASSUMPTION

That should effectively become illegal.


---

2. The system should ask you questions — but using Active Learning

I would not implement:

> “Whenever uncertain, ask Jacobo.”



That would destroy autonomy.

I would implement:

> Whenever a material uncertainty cannot be resolved more reliably from existing authority or affordable evidence, EDD must convert it into the highest-information Founder question available.



That difference is enormous.

Suppose EDD finds:

UNKNOWN:
Should SkyParty support team mode?

Before asking you, it checks:

explicit product decisions?
baseline?
existing architecture?
previous chats/decisions?
reference evidence?
current product identity?
technical constraints?

If those answer it confidently, you never get interrupted.

If they do not, then it asks.

The existing KSEIP doctrine already says the Founder should decide what product they want, not implementation questions such as plugin ordering. 

EDD should operationalize that distinction.


---

3. Not generic questions: Decision Packets

A question should almost never be:

> “What do you want?”



It should arrive after EDD has done the work.

For example:

> Team Mode is currently unresolved.

I found Solo + Fiesta group joining, but Fiesta does not create an actual match-team model. The strongest references generally expose real team semantics. Adding it would imply team ownership, spawn allocation, win conditions, friendly-fire policy, team statistics and spectator implications.

Recommendation: support Team Mode as a capability but keep Solo as the default public mode.

Choose:

A. Build capability + public Teams
B. Build capability but leave public Teams disabled
C. Explicitly exclude Team Mode
D. Different direction



That single answer can resolve dozens of downstream decisions.

So each Founder question should carry:

uncertainty
why it matters
evidence already gathered
recommended answer
alternatives
consequence of each choice
what downstream obligations it unlocks

The system is asking you for authority, not outsourcing thinking to you.


---

4. New metric: Founder Question Compression

EDD should measure:

material decisions resolved
──────────────────────────
Founder interruptions

We want this to increase continuously.

One good Founder question might resolve 30 downstream requirements.

Ten low-information questions for those 30 requirements would be an EDD failure.

This is the next evolution beyond merely reducing Human Discovery Dependency.


---

5. EDD should periodically ask “is there anything else?” — but intelligently

Your instinct here is right, but I would not make it a generic repeated sentence.

Instead create an Intent Closure Checkpoint at high-value boundaries.

For example before freezing Goal Outcome:

> “I currently understand the target as X, Y and Z. I am treating A as explicitly excluded and B as deferred. I have inferred C, D and E as required consequences. Before I compile this into the Goal Contract: is there any outcome, constraint, reference, behavior or product direction you want added or changed?”



That question is extremely valuable because it exposes the reconstructed world model to you before expensive implementation.

But after you answer:

> “No.”



EDD should persist that as evidence:

FOUNDER_INTENT_CLOSURE
revision = 7

and stop repeatedly asking the same thing unless new evidence materially changes the interpretation.


---

6. Every new bug can reopen the question frontier

This connects directly with what we just designed.

Suppose during implementation GSD X discovers:

first cage release causes fall damage

That may be:

engineering-resolvable

Evidence says it obviously violates intended fairness.

EDD can derive:

first-release-only protection

and continue autonomously.

Or it may reveal a real product decision:

> Do we actually want cage drops to be part of the risk?



Then the correct behavior is:

new evidence
↓
Goal Model uncertainty
↓
FOUNDER_DECISION_REQUIRED

Only that branch pauses.

Your answer then immediately causes:

Goal revision
↓
expectation recompilation
↓
new obligations
↓
tests
↓
remaining plan recompilation

Questions are therefore part of the compiler, not chat interruptions.


---

7. EDD should have a permanent Reference Frontier

Here I would go considerably beyond “compare with competitors”.

The SkyParty research already says not to learn from a single setup: compare multiple systems across behavior, features, state machines, journeys, failure handling and configuration semantics, extracting capability/invariant/failure/player-expectation candidates rather than cloning them. 

That should become default EDD behavior for material product construction.

Instead of:

SkyParty vs Unique

EDD maintains:

REFERENCE FRONTIER

composed from the strongest relevant systems.

One reference may be best at:

spectator UX

another at:

match configuration

another at:

reliability

another at:

social play

another at:

operator tooling

The target is not:

> beat competitor X.



It is:

> beat the composite best-known frontier.




---

8. A Reference Frontier Vector

For every material Goal, EDD should reconstruct dimensions such as:

Dimension	Best known evidence	Current product	Target

Core behavior	Reference A	weaker	≥ frontier
Lifecycle completeness	Reference B	weaker	> frontier
Recovery	Reference C	comparable	> frontier
User journey	Reference A/B	weaker	> frontier
Reliability	internal baseline	stronger	preserve
Product identity	ours	unique	preserve/extend
Operability	Reference D	weaker	> frontier
Novel capability	none	opportunity	frontier advance


The exact dimensions are domain-derived, not universal columns.


---

9. But “always surpass references” needs a precise definition

I agree with the objective.

I would not define it as:

> every numeric/property dimension must be greater than every reference.



That can be internally contradictory.

A reference may maximize simplicity while another maximizes configurability.

You cannot simultaneously produce:

minimum configuration
AND
maximum configuration

unless you architect those goals differently.

So define superiority as:

Reference Frontier Dominance

For every materially applicable reference advantage, EDD must produce one of:

MATCHED
SURPASSED
SUPERSEDED_BY_BETTER_MECHANISM
NOT_APPLICABLE
INTENTIONALLY_REJECTED_WITH_REASON
BLOCKED_BY_CONSTRAINT

Never:

NOT_CONSIDERED

And the final product should, when realistically achievable, be Pareto-superior to the reference set on the dimensions that define the chosen product.


---

10. Reference capabilities become challenges, not requirements

Suppose Unique has:

spectator teleporter

EDD asks:

> Why does this exist?



Answer:

allow eliminated player to remain engaged
and navigate remaining action

Now we do not ask:

> copy spectator teleporter?



We ask:

> Can we satisfy the underlying job better?



Maybe:

Player Browser
+
quick POV switching
+
party member priority
+
Play Again
+
social continuity

Now we have surpassed the mechanism without cloning it.

The previous SkyParty analysis already formalized exactly this general approach: synthesize the strengths of both systems, choose the better implementation or reimplement when neither is good enough, and make the result a higher reference point. 

EDD should make that automatic.


---

11. New stage: Reference Mechanism Extraction

Every interesting reference capability goes through:

OBSERVED FEATURE
↓
WHAT USER/SYSTEM PROBLEM DOES IT SOLVE?
↓
UNDERLYING MECHANISM
↓
APPLICABILITY TO OUR PRODUCT
↓
CURRENT SOLUTION
↓
CAN WE:
    REJECT
    MATCH
    ADAPT
    COMBINE
    GENERALIZE
    SUPERSEDE
?

Only then does it become an expectation candidate.

This prevents cargo-cult product development.


---

12. EDD should actively hunt for ways to outperform

After Expectation Closure, it should run a second pass:

Excellence Frontier Excavation

Different question:

> “We now know what would make this complete. What would make it materially better than the strongest comparable systems?”



This search can examine:

user friction
time-to-value
state coherence
reliability
recoverability
operator burden
performance
clarity
social value
automation
accessibility
extensibility
security
cost
novel experience

Again, domain-derived.


---

13. Important distinction: Completion vs Excellence

EDD should maintain two frontiers.

COMPLETION FRONTIER
What must be true?

and:

EXCELLENCE FRONTIER
What could make us materially superior?

Completion obligations can be mandatory.

Excellence candidates need ROI/applicability adjudication.

This prevents:

> “Competitor has feature X, therefore we must implement X.”



while retaining:

> “We may not declare ourselves best-in-class while ignoring an important dimension in which references demonstrably outperform us.”




---

14. Founder controls product expansion

This is where questions become essential.

Suppose EDD discovers:

> Best references have tournaments.



But tournaments are not necessary for current Goal completion.

EDD should not silently add three months of work.

It generates:

EXCELLENCE OPPORTUNITY

and can ask:

> “Tournament capability is not required for the current SkyParty completion contract, but it is one of the remaining areas where strong references exceed us. I estimate it as material but non-blocking. Do you want it: now, capability-only for future use, backlog, or explicitly rejected?”



This gives you strategic control.


---

15. Add Founder Opportunity Review

At appropriate checkpoints, not constantly, EDD shows only the highest-value unresolved opportunities.

Not 70 ideas.

Something like:

3 material product decisions require your authority.
2 optional frontier opportunities materially improve competitive position.
Everything else has been resolved from evidence/baseline.

That is the ideal Founder experience.


---

16. New rule: EDD must recommend

If EDD asks:

> “Do you want X or Y?”



without analysis, it has failed.

Every non-subjective decision question should include a recommendation unless evidence is truly symmetric.

The Founder can override.

But the machine must do the intellectual work first.


---

17. New concept: Assumption Liability

Every silent assumption carries risk.

EDD should track material assumptions such as:

Founder probably wants Solo only.
Probably no reconnect.
Probably spectator uses vanilla mode.
Probably mobile isn't needed.

Then:

materiality × uncertainty × irreversibility

determines what happens.

Low liability:

choose evidence-backed default

High liability:

research or Founder question

No more arbitrary guessing hidden inside implementation.


---

18. Unknown → experiment before Founder where possible

A question doesn't automatically mean human.

Suppose EDD doesn't know:

> Which queue UX is faster?



That is not necessarily Founder authority.

It can:

inspect references
prototype
measure clicks
synthetic journey
benchmark

and resolve it.

Suppose it doesn't know:

> Should SkyParty feel competitive-serious or chaotic-social?



That is product identity.

Ask you.

This distinction is critical.


---

19. EDD becomes an Active Epistemic Controller

This is the deeper conceptual upgrade.

For every unknown:

What type of unknown is this?
Who owns the truth?
What evidence could resolve it?
What is the cheapest discriminating evidence?
Could research resolve it?
Could an experiment resolve it?
Is it fundamentally a Founder decision?
What happens if we defer?

Then route appropriately.

So the loop becomes:

UNKNOWN
  ↓
AUTHORITY CLASSIFICATION
  ├── repository truth → inspect
  ├── runtime truth → probe
  ├── reference truth → research
  ├── empirical product truth → experiment
  ├── baseline truth → inherit
  └── Founder intent → ASK

This is much smarter than either:

> ask everything



or:

> ask nothing.




---

20. Questions should update the Goal World Model, not become chat trivia

Your answer needs durable consequences.

If EDD asks:

> “Do you want Teams to be public at launch?”



and you answer:

> “Capability yes, public no.”



It becomes something like:

Team Capability: REQUIRED
Public Team Surface: DISABLED_BY_FOUNDER
Product scope: future-compatible

Then:

architecture changes;

tests change;

reference comparison changes;

public UX obligations disappear;

capability baseline remains.


And EDD never asks again unless new evidence invalidates the decision.


---

21. Add Decision Provenance

Every Founder decision needs:

decision
scope
date/revision
reason if supplied
what it overrides
what it does not imply

Because otherwise a six-month-old:

> “don't add Teams yet”



can accidentally become:

> “KobiiCraft should never have Teams.”



EDD must understand scope and supersession.


---

22. Bugs can produce questions automatically

Now connect this with in-mission self-evolution.

Bug
↓
Factory RCA
↓
new semantic uncertainty

The system first tries to resolve it.

If it reaches:

FOUNDER_DECISION_REQUIRED

it asks.

Your answer does not merely fix the bug.

It can create:

new product law
↓
new expectations
↓
new sibling checks
↓
new baseline candidate

That is extremely high leverage.


---

23. Reference research can also produce questions

Suppose EDD finds:

Reference A:
very fast rematch

Reference B:
social post-match lobby

SkyParty:
current immediate autoqueue

Neither is objectively superior because they optimize different experience.

EDD asks you something much better than:

> “Which do you prefer?”



It asks:

> “Post-match has two defensible directions. Fast rematch minimizes downtime; social continuation creates more space for parties, reactions and memory. SkyParty's stated identity suggests social-chaotic play, so I recommend social continuation with one-click rematch retained. Do you want that to become the product contract?”



That is founder-level decision support.


---

24. Introduce a Reference Challenge Contract

For every serious product Goal:

REFERENCE_SET_RESOLVED
REFERENCE_FRONTIER_RECONSTRUCTED
OUR_ADVANTAGES_IDENTIFIED
OUR_DEFICITS_IDENTIFIED
SUPERIORITY_TARGET_DEFINED

before major implementation, when evidence is available.

At DONE:

REFERENCE_DEFICITS remaining?

Every material one must be:

SURPASSED
SUPERSEDED
NOT_APPLICABLE
EXPLICITLY_ACCEPTED

No accidental inferiority.


---

25. The best reference should become the floor, not the target

This is perhaps the principle you're aiming at.

Once the system has enough evidence to establish:

reference best-known behavior = B

the planning target should not automatically be:

B

but:

B + justified improvement

when improvement is technically/economically sensible.

So EDD asks:

> “What mechanism makes B good?”



Then:

> “What limitations remain?”



Then:

> “Can our architecture remove those limitations?”



Then:

> “Can the improvement be proven?”



That is how you go from copying to frontier advancement.


---

26. But superiority must be proven

Never:

> “ours is better because Claude says so.”



A superiority claim needs an oracle.

For example:

Reference:
5-step rematch

Ours:
1-step rematch

Can prove interaction efficiency.

Reference:
spectator loses party continuity

Ours:
retains party context

Can prove behavior.

Reference:
ours feels more fun

cannot be declared autonomously without appropriate human/player evidence.

So introduce:

Superiority Proof Obligations

Every SURPASSED verdict needs evidence appropriate to its dimension.


---

27. EDD should compare itself not only with products, but with our own previous best

This is important.

Reference frontier becomes:

external best
+
internal best
+
institutional baseline
+
new evidence

A future SkyParty shouldn't merely beat Unique.

It must beat:

> the strongest verified SkyParty/KobiiCraft/GSD X baseline we've ever produced.



This is where Constitutive Baseline Ratchet becomes extremely powerful.


---

28. Prevent regression below our own frontier

Suppose future Team Mode implementation is technically “working” but has weaker reconnect than existing Solo.

Even if competitor refs are worse:

BELOW_INTERNAL_FRONTIER

should block.

The floor ratchets upward.


---

29. New closure: Founder Intent Closure

Before DONE, EDD should prove:

No material unresolved Founder-owned question
that can change product correctness remains.

If one remains:

FOUNDER_DECISION_DEBT

DONE blocked.

But optional future ideas do not block.

Again, materiality.


---

30. New closure: Reference Closure

Before DONE for material product Goals:

No applicable material capability of the
Reference Frontier remains silently unexamined.

Not necessarily implemented.

Examined and dispositioned.


---

31. New closure: Excellence Closure

This is separate.

Before claiming:

BEST-IN-CLASS

or:

SUPERIOR

all selected superiority dimensions must be proven.

A product can still be:

COMPLETE

without:

FRONTIER-SUPERIOR

if the Founder intentionally chose a narrower Goal.

This distinction keeps truth intact.


---

32. Three completion certificates

I would therefore separate:

PRODUCT COMPLETE

Expected product contract converged.

FOUNDER INTENT CLOSED

No material unresolved Owner decisions.

FRONTIER ADVANCED

Product has demonstrated superiority over its selected reference frontier.

For high-ambition Claude Power Pack product work, you can make all three mandatory.

For trivial internal tasks, only applicable ones activate.


---

33. The final live loop becomes substantially stronger

FOUNDER INTENT
                           ↓
                INTENT RECONSTRUCTION
                           ↓
                  GOAL WORLD MODEL
                           ↓
                  UNCERTAINTY FRONTIER
                           ↓
              ┌────────────┴────────────┐
              │                         │
      evidence-resolvable        Founder-owned
              │                         │
        autonomous work          DECISION PACKET
              │                         │
              └────────────┬────────────┘
                           ↓
                    DECISION CLOSURE
                           ↓
              MULTI-REFERENCE RESEARCH
                           ↓
                   REFERENCE FRONTIER
                           ↓
                  EXCELLENCE TARGET
                           ↓
               EXPECTATION COMPILATION
                           ↓
                    OBLIGATIONS
                           ↓
                  PROOF COMPILATION
                           ↓
                     EXECUTION
                           ↓
              CONTINUOUS OBSERVATION
                           ↓
                    GAP / DEFECT?
                   ↙            ↘
                 yes             no
                  ↓               │
        PRODUCT + FACTORY REPAIR │
                  ↓               │
       GSD X CAPABILITY ASCENSION│
                  ↓               │
       UNCERTAINTY RE-EVALUATION │
                  ↓               │
         new Founder question?   │
                  ↓               │
          GOAL RECOMPILATION ◄───┘
                  ↓
          REFERENCE RED TEAM
                  ↓
     EXCELLENCE FRONTIER EXCAVATION
                  ↓
      FOUNDER OPPORTUNITY REVIEW
                  ↓
      ADVERSARIAL COUNTEREXAMPLES
                  ↓
          PRODUCTION REALITY
                  ↓
 ┌─────────────────────────────────────┐
 │ Founder Decision Debt = 0           │
 │ Material Expectation Debt = 0       │
 │ Self-Evolution Debt = 0             │
 │ Reference Debt = 0 or dispositioned │
 │ Required superiority proven         │
 └─────────────────┬───────────────────┘
                   ↓
                  DONE

That is considerably closer to what I think you actually want.


---

34. The Founder experience

Your ideal interaction becomes something like:

> You: Finish SkyParty.



EDD works autonomously.

Later:

> EDD: I resolved 94% of product decisions from current SkyParty identity, applicable baselines, repository evidence and five strong reference systems. Three decisions genuinely require product authority.

I recommend A for spectator continuation, B for Team capability/public exposure, and C for post-match social flow. Here is why.

I also found four areas where the current best references outperform SkyParty and two areas where SkyParty already outperforms all references. I have a plan to eliminate three of the four deficits automatically; the fourth is a strategic product choice.

Do you want the recommended contract, or change any of these four decisions?



You answer once.

Then it keeps working.

Later it discovers a new bug.

It doesn't immediately come back to you.

It tries to solve it, improves its own factory, rescans siblings, recompiles.

Only if the bug exposes a genuine product choice does it ask.

That's the right relationship.


---

35. The constitutional laws I would add

> EDD MUST NEVER SILENTLY GUESS A MATERIAL FOUNDER-OWNED PRODUCT DECISION.



> EDD MUST NEVER ASK THE FOUNDER A QUESTION THAT AVAILABLE AUTHORITY OR REASONABLY CHEAP EVIDENCE CAN ANSWER MORE RELIABLY.



> EVERY FOUNDER QUESTION MUST MAXIMIZE DECISION INFORMATION GAIN AND MINIMIZE HUMAN ATTENTION COST.



> EVERY MATERIAL ANSWER MUST RECOMPILE THE AFFECTED GOAL, NOT MERELY ENTER CHAT HISTORY.



> EVERY MATERIAL PRODUCT GOAL MUST ESTABLISH THE STRONGEST APPLICABLE MULTI-REFERENCE FRONTIER BEFORE CLAIMING EXCELLENCE.



> REFERENCE BEHAVIOR IS EVIDENCE, NOT AUTHORITY.



> A REFERENCE ADVANTAGE MAY NOT BE SILENTLY IGNORED; IT MUST BE MATCHED, SURPASSED, SUPERSEDED, REJECTED, OR SHOWN NOT APPLICABLE.



> THE OBJECTIVE IS NOT TO COPY THE BEST REFERENCE. THE OBJECTIVE IS TO CONSTRUCT A JUSTIFIED SYSTEM THAT ADVANCES THE BEST-KNOWN FRONTIER.



> CAPABILITY SUPERSET DOES NOT IMPLY FEATURE-DEFAULT SUPERSET.



That last principle is already supported by the SkyParty work: the research explicitly distinguishes building a superior capability superset from enabling every inherited feature by default. 

And the most important final one:

> DONE MUST MEAN NOT ONLY “NOTHING KNOWN IS BROKEN”, BUT “THE MATERIAL INTENT, EXPECTATION, DECISION, REFERENCE AND LEARNING FRONTIERS HAVE BEEN CLOSED TO THE STRONGEST APPLICABLE EVIDENCE.”



At that point EDD isn't an acceptance-criteria system anymore.

It becomes the continuous interface between sparse Founder intent and an autonomously expanding, self-correcting, reference-aware definition of what the best justified version of the product should become.

And that is much closer to eliminating the two dependencies we're really trying to drive toward zero:

HUMAN IMAGINATION DEPENDENCY → 0
FOUNDER-FIRST GAP DISCOVERY   → 0

while preserving the part that should not go to zero:

FOUNDER PRODUCT AUTHORITY = 100%

The machine should progressively need less of your attention, without silently taking away more of your authority.