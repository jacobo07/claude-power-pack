# orca_dws.md (digest, in progress; coverage line filled at end)
## Structure
- L1-98 Part A: DWS token budget report (compiled 2026-10-09 by CPP cost_to_completion)
- L100-398 Part B: first Claude-style reply (10 attack points + Cognitive Recompilation Gate)
- L400+ Part C: second reply, "extreme" 50+ numbered ideas (continues)
## Part A (L1-98)
- L5-6 Phase-average estimate refused by cost_to_completion PHASE_MULTIPLIER: mission m-8bbdf725cd52 planned 4M by phase count, spent 53.7M.
- L16-17 route-floors.json: worker first-call floor 110,835 tokens; compiler: floor<=candidate<=ceiling, novel x deopt 3.0, +20% growth margin.
- L26-34 Measured: 8,066 productive calls, 2.04B tokens, 253k context/call, 19 matrix steps => 424 calls/step (~107M tokens, ~$39/step); $744 productive + $233 for 09-28 memory-starved run; $0.364/M processed tokens.
- L38-47 91 open claims (65 rows, 2 reverify, 21 new, 2 visual +1 pixel gate). Runnable: 11 known_transform/19 bounded_coding/12 novel = 25,683 calls, 6.50B cand, 7.80B margin, 11.0B ceiling, $2,368/$2,841/$4,011. All: 57,105 calls, 14.5B/17.3B/24.3B, $5,264/6,317/8,865. 2 owner_reality, 46 sleeping not costed.
- L53-56 Previous phase-average 2.6B vs 6.5B per claim (2.5x); n=19 uncertain; plan on margin column, ceiling = stop.
- L60-66 usage_index burn MONITOR_FAILURE; weekly window REJECTED out_of_credits 2026-10-07..10-11 18:00Z; estate spent $9,485 API-equiv 09-25..10-03 (84,349 calls); dws ~10%.
- L69-86 Two visual refs must be "identical" (visual not data); each 215M/645M tokens $78/$235; pixel gate deterministic 0 tokens; fixture reproduces six hosts, never invent prod data.
- L90-97 Levers: memory-starved host $233=24% of spend; Opus->Sonnet only ~6% (cache reads $0.20/M both); fewer calls per claim real lever; trim STATE.md (~1,100 lines reread per epoch); stop-and-report at each 25% of margin figure (~1.95B tokens ~$710), abort at ceiling 11.0B.
## Part B (L100-398)
- L117-149 Treat 424 calls/step as economic incident; classify calls into 12 families (irreducible novelty, necessary assurance, implementation, repeated read/verification, control-plane, recovery, status/polling, context repair, rediscovery, transport, closeout).
- L157-159 Compile 91 claims -> shared causal questions -> semantic families -> primitives -> reality observations -> proof closures -> deterministic instances -> true novelty.
- L179-187 known_transform target = deterministic transform -> proof -> receipt, 0 model calls.
- L197-201 Novel instance -> pattern -> certified transform -> N cheap instances.
- L207-237 STATE.md becomes rendering of canonical semantic state; "STATE IS DURABLE; TOKENS TRANSPORT DELTA."
- L255-269 Context: backward dependency slicing, tool linker, proof refs, read-once, zero-copy, delta-only; goal = "minimum context that preserves first-pass verified completion".
- L279-291 change -> affected semantic closure -> affected proof closure; no rerun-all per epoch.
- L297-311 Multiplex reality acquisition; L321-329 visual: reference decomposition, pixel gate, region diff, preserve passed regions.
- L339-347 resource admission: no memory headroom => no launch.
- L356-369 DWS Cognitive Recompilation Gate: 10 questions (independent claims of 42, zero-model known_transform, shared bounded_coding families, multiplexable observations, reusable proofs, calls vs semantic boundaries of 25,683, live closure share of 253K, STATE/history/schema share, control/recovery/status calls, Irreducible Cognitive Lower Bound).
- L376-398 Refuses to claim 6.5B->500M; "No hacer 25.683 calls mas baratas. Hacer que miles dejen de existir."
## Part C so far (L400-1600)
- L410-433 Goal->semantic delta->compiler->deterministic exec->proof; cognitive interrupt only on novelty; maturity trajectory 424->80->15->3->1->0 (direction, not forecast).
- L459-461 Law: "CLAIM COUNT MUST NEVER BE USED AS A PROXY FOR IRREDUCIBLE COGNITIVE WORK." Causal Novelty Graph.
- L468-494 Cognitive Lower-Bound Compiler: irreducible novel decisions, reality observations, necessary independent assurance, owner-only decisions; Cognitive Overhead Multiplier = actual model boundaries / irreducible boundaries.
- L509 "A KNOWN_TRANSFORM MAY NOT RECEIVE A GENERAL MODEL WORKER UNLESS THE CERTIFIED TRANSFORM DEOPTS."
- L531-552 bounded coding: 1 derivation + N applications; deopt only on exception. L568-580 novel: reality compiler, known-state removal, slicing, negative knowledge, only residual unknown to frontier.
- L588-623 Semantic Call vs Physical Call; Semantic Boundary Compression: physical calls -> transaction.
- L628-696 Trace mining of 8,066 paid calls -> candidate transactions -> historical replay -> mutation tests -> shadow -> canary -> CBR; Sequence-to-Primitive compiler.
- L701-748 Call Fusion (db query optimisation), Call Hoisting (loop-invariant: repo root, branch owner, capabilities, tools, test mapping, invariants).
- L753-795 Dead Cognitive Code Elimination; speculative cognition elimination (constraints cut 8 of 10 options before model).
- L797-878 STATE.md off hot path, ~20 semantic objects; state reconstruction O(delta) not O(history); Context SSA (identity/version, invalidate dependency closure).
- L883-954 Context as virtual memory (hot/cold pages, prefetch, faults, GC, thrashing); Context Rent per causal use (10K object over 100 calls ~1M token-rent); Context Utilization Profiler -> CONTEXT_LEAK.
- L956-1001 Tool schemas are memory (Aplicability compiler goal->WU->phase subsets; unload edit tools in proof phase); tool-output virtualization (raw artifact, typed projection+pointers).
- L1006-1062 Proof below the model; Proof DAG (Proof Cost proportional to affected closure); proof extinction > memoization; green costs ~0 tokens, Claude wakes only on red.
- L1066-1120 Reality acquisition compiler = set cover; singleflight; Physical Reality Session Compiler (owner attention scarce).
- L1123-1180 Visual compiler: region decomposition, failure mask, freeze passed regions, pixel gate is no-model terminal verifier ("Machine decides whether done").
- L1182-1223 Memory starvation = admission impossibility; resource profiles per Work Class.
- L1228-1337 Pricing by semantic entropy; Cognitive Entropy Budget (STALL if unchanged after 5 calls); Information Gain per Call; calls need explicit consumer else NO_CALL; budget semantic interrupts (4 unknowns -> 4-8 interrupts, 40 physical calls = wrong); mission-level Amdahl re-profile after each wave.
- L1342-1460 Work-class kernels: known_transform, bounded_coding(template+delta), novel(Frontier Token Firewall), visual_match, physical_reality, proof_only, closeout(zero model), recovery(zero-model for known failures), planning (disappears for known classes), research (stopping criteria).
- L1462-1555 Counterfactual Laboratory over the 8,066 calls (what if no planner, ContextImage 30K, transactions, affected-closure proofs, rotate after N calls); Cognitive Flamegraph, Model Interrupt Flamegraph (NOVELTY/STATE_MISS/CONTROL_LOOP/PROOF/CONTEXT_FAULT/TOOLING/RECOVERY), Decision Flamegraph; Automatic Decision/Sequence/Context/Read Extinction (same decision N times with stable answer -> compile policy->evaluator->primitive).
## Part C continued (L1597-5914)
- L1597-1635 Read extinction (repeated read -> structural index), Review extinction (reviewer always PASS on deterministic evidence -> remove), Owner extinction (mechanical Owner action -> control-plane primitive), Prompt extinction (mechanically enforced rule leaves hot prompt).
- L1637-1704 Economic Diff on every commit (context delta, model-boundary delta, proof radius, Decision Surface, Token Rent); cognitive maintainability: +50K context or 4x proof closure = architecture regression; Token Debt principal+interest; Technical Capital Allocator = lifetime cognition avoided / (CAPEX+maintenance+risk).
- L1757-1780 Extreme benchmark: grow estate knowledge/projects/capabilities/history x100; active semantic surface must stay ~constant; if grows 100x = failure.
- L1784-1812 Terminal DWS pipeline: Owner Goal -> Goal Compiler -> semantic state -> Extinction Compiler -> family compiler -> Context linker -> Tool linker -> Proof compiler -> deterministic executor -> proofs -> receipt; models only as interrupt handlers.
- L1839-1847 Two constitutional gates: no multi-billion-token forecast accepted until work extinction/family factoring/boundary compression/state+proof compilation/context slicing/transaction mining/decision extinction tried; "A FORECAST BASED ON HISTORICAL CALL AMPLIFICATION DESCRIBES THE COST OF THE OLD ARCHITECTURE."
- L1861-1990 Third reply: Universal Cognitive Deflation Fabric (runtime property, not opt-in); unit = Irreducible Semantic Transition; Global Cognitive Conservation Law (model cognition only to reduce unresolved semantic entropy or give necessary assurance); Demand Compiler: postcondition -> current reality -> delta -> entropy -> assurance -> minimum new cognition (e.g. "7 unknown decisions, 2 observations, 1 judgment").
- L1993-2060 Separate semantic from execution work (200 files, 70 tests, 50 receipts ~ zero cognition); Semantic ISA primitives (resolve owner, materialize state, prove no-work, derive affected closure, apply known transform, run proof transaction, reconcile reservation, compile successor, acquire reality, join in-flight derivation, invalidate object).
- L2063-2163 Model calls = privileged interrupts with Cognitive Interrupt Packet (unknown, minimal context, evidence, constraints, required result, proof contract); Global Interrupt Budget per work class (known_transform 0 but opens 12 = trip; bounded repair 1-2 reaches 9 = anomaly); Model-Call Firewall = Proof of Cognitive Necessity (10 checks: state, theorem, negative knowledge, solver, cache, in-flight, transform, tool transaction, proof object, constraint) -> CALL REFUSED with safe deopt.
- L2168-2343 Estate-wide cognitive CSE (Question Identity + Dependency Fingerprint + Scope + Evidence Epoch + Proof Requirement); distributed singleflight (producer + subscribers); cross-project computation market; information acquisition market (cost, latency, reliability, freshness, proof strength); shadow price of uncertainty; Value-of-Information scheduler (spend 1M on decision eliminating 40M); Knowledge Fan-Out (Fact A 500K helps 2 WUs vs Fact B 2M eliminates 500).
- L2345-2467 Semantic dedup; claim graph->theorem graph (illustrative 91 claims -> 20 invariants, 9 transforms, 6 families, 3 human sessions, explicitly not asserted); proof attached to theorem; proof subsumption; assurance priced by consequence/blast radius/reversibility/novelty/security.
- L2472-2580 Materialize by causal requirement (stronger than RAG); context as execution cache; hierarchy L0 decision packet, L1 WU state, L2 project canonical, L3 institutional theorems, L4 raw evidence; semantic compression: 1,100-line STATE.md -> 13 facts, 4 decisions, 5 obligations, 2 invalidators, 3 evidence refs.
- L2584-2660 Zero-prose runtime (typed objects, Markdown human docs); token rent ownership (who owns, guarantee, consumer, retire event); Constitutional garbage collector (guarded/tested/typed rules leave hot CLAUDE.md); tool schema GC/progressive disclosure.
- L2662-2838 Tool-call superoptimizer; transaction mining frequency x cost; Tool-sequence JIT & Cognitive JIT (interpret w/ model -> profile -> specialize -> compile -> deopt on uncommon case); semantic deoptimization with exact violated assumption; speculative prefetch/branch prediction; optimise for recurrence (5,000x repeat justifies CAPEX).
- L2842-3000 Lifetime Cognitive NPV; maintenance cost as metric (Option A 200K vs B 25K context per future change); locality-aware module boundaries; invalidation/proof/observation/Owner radius budgets (feature adding 10 recurring Owner questions = bad); types/schemas as token optimisation; compiler errors instead of model judgment; negative-space representation.
- L3003-3090 Estate constraint propagation ("No Hermes -> Hermes-dependent nodes inactive"); semantic constant folding; dead capability elimination; mission specialization (generic CPP 1,000 capabilities, DWS epoch needs 9); "semantic linked executable" per Work Unit.
- L3092-3260 Model-independent continuation; Cognitive ABI (Goal, State, Unknown, Proof, Effect, Authority, Receipt); multi-provider bidding by expected verified winner; ensemble only when risk reduction > cost; Reviewer extinction when correlation with machine proof 99.9% (shadow test then retire); planner/coordinator/researcher/executor/debugger extinction; Role Extinction Rate.
- L3264-3335 Hot knowledge pays rent or goes cold; generational memory (young/promote/cold/archive); semantic defrag daemon; structural compaction (same fact one object, variants provenance), avoid summaries-of-summaries.
- L3338-3480 Economic truth needs invalidation: "Sonnet saves 6%" is conditional on prices/cache/workload; Economic Theorem Store; Autonomous Economic Scientist (statistical, not always-on agent); experiments by information gain per token; sequential stopping; shadow execution estate; Universal Holdout Estate (no universal CBR until different domains); economic mutation testing.
- L3492-3620 Global Cognitive CI (hot tokens, tool-schema rent, calls, context, proof radius, decision surface); budgets as SLOs p50/p95 not fixed caps; Institutional Cognitive Deflation SLO (month1 X, month3 lower, month12 much lower); maturity half-lives: knowledge embodiment latency, decision, failure, owner-dependency, prompt, model-boundary.
- L3626-3780 Global Cognitive Debt (token, decision, context, proof, owner, architecture, failure); interest = expected recurrence x expected excess cost; Cognitive Balance Sheet (assets: certified transforms, proofs, caches, indices, immunities, typed state, policies); capital depreciation; baseline must shrink as capability grows (hard SLO, e.g. 500 prompt tokens per capability collapses CPP); Zero-Prose Baseline Ratio; compile-or-archive law; five "Why am I still..." detectors; "Why does this Work Unit exist?" Proof of Non-Work before every spawn.
- L3785-3836 Global architecture layers (Reality, Canonical Semantic State, Constraint/Theorem, Economic Science Plane, Demand Compiler, Extinction Compiler, Superoptimizer, Context/Tool Linker, Deterministic Runtime, Interrupt Runtime, Proof Compiler, Embodiment/JIT, Capital Allocator, Scientific Evolution, CBR). Invariant: intelligence scales arbitrarily while active cognitive surface bounded.
- L3843-3869 57,105 calls/14.5B/17.3B/24.3B is a description of current architecture cost; rule: "HISTORICAL CALL AMPLIFICATION MAY BE USED TO PRICE THE OLD EXECUTION STRATEGY, BUT NEVER TO DEFINE THE INTRINSIC COST OF THE SEMANTIC OUTCOME."
- L3873-4000 Fourth reply: Desired State - Certified Current State = Semantic Demand; Global Semantic Demand Graph ("100 claims != 100 cognitive tasks": 13 demands + 87 derivations); Obligation Graph vs Computation Graph; Proof of Non-Compute.
- L4037-4260 Semantic e-graph of equivalent executions; Global Cognitive Superoptimizer minimising Expected Verified Cognitive Cost; ResolveOwner(WorkspaceRef, epoch) shared by DWS/Sidecar; Cognitive Exchange; Institutional Shadow Value = expected consumers x avoided cognition x lifetime x confidence; Demand Netting (Goal A asks if X exists, B builds X).
- L4286-4600 Universal Semantic IR primitives (Goal, Obligation, Fact, Unknown, Decision, Invariant, Proof, Effect, Authority, Capability, Continuation, Failure, Artifact, Invalidator); Markdown is view not state; Semantic SSA; incremental compilation / Bazel-Ninja semantics; content-addressed cognition; Read-Once, Reason-Once, Fail-Once, Prove-Once, Reality-Once fabrics; reality acquisition set-cover (60-min physical test -> 10).
- L4603-4700 Owner Interaction Compiler (batch owner questions when delay harmless); cognitive futures (precompute if probability x avoided cost > cost + staleness risk); knowledge volatility pricing; cache replacement by reuse probability, reload cost, size, volatility, importance; page-fault economics.
- L4710-4960 Context eBPF, Context Flamegraph, object rent = size x resident calls x consumer reach; GC; knowledge liquidity; semantic compression benchmark (10x knowledge, same active context); capability/tool/model universe virtualization (1,000 installed, linker chooses 5); provider arbitrage on expected verified cost (provider cost + context floor + retries + tool reliability + proof burden + latency).
- L4961-5170 QoS classes; cognitive microkernel (laws: Reality, Authority, State, Effects, Evidence, Proof, Learning); constitutional compiler (rule -> type/schema/guard/API/test/runtime transition); Constitutional Residual as debt; Baseline Zero-Prose Ratio; prompt/tool/proof/handoff instruction extinction; agent count as anti-KPI for mastered work; Decision Surface Area/Density.
- L5172-5310 Interrupt provenance classes: NOVELTY, ASSURANCE, STATE_MISS, TOOL_MISS, CONTROL_LOOP, CONTEXT_FAULT, RECOVERY, OWNER_BOUNDARY; interrupt purity target; Semantic Interrupt Budget (predicted 2, actual 15 -> stop/recompile); Global Call Amplification Ratio = physical model boundaries / irreducible boundaries; Semantic Progress Velocity = durable transitions per M processed tokens; Verified Novelty Yield; Cognitive Capitalization Rate.
- L5298-5390 Every expensive incident must capitalize (107M claim-step: what makes next cheaper?); automatic post-spend capitalization (theorem, failure motif, transform, proof, index, context profile); cost-of-ignorance, cost-of-staleness, cost-of-proof-debt, cost-of-context-omission ledgers ("no fetish for minimal prompts").
- L5394-5560 Total Verified Cost objective = execution + expected repair + proof + recovery + human interruption + future maintenance + context rent; economic e-graph; champion/challenger every layer; regret accounting; counterfactual replay factory (8,066 calls = benchmark corpus); microbenchmarks (context-heavy, proof-heavy, coordination-heavy, novel, visual); cognitive mutation testing; optimisation correctness proof (scope, assurance, Production Reality preserved); economic safety envelope separate from learned policy.
- L5551-5660 Capital allocator as portfolio optimiser; diversification; Meta-optimization stop-loss ("burn billions saving millions"); Meta-Cognitive Tax hard SLO; self-hosting; cross-project transfer proof (universal capability from DWS must make another workload cheaper, else DWS-local) and reverse transfer.
- L5650-5707 Economic Theorem Registry with invalidators (pricing, provider, context mix); "No global folklore"; global negative investment memory (Gen1/Gen2 closed loop: Gen1 discovers economic truth, Gen2 compiles/extinguishes, CBR propagates).
- L5709-5827 Hierarchy of zeros: zero-work > zero-model; zero-proof, zero-context, zero-tool-call, zero-handoff, zero-Agent, zero-Owner-operation; extinction-first ordering: eliminate Goal sub-obligation -> decision -> cognition -> Agent -> read -> transport -> proof -> context -> fuse -> route cheaply.
- L5830-5914 Universal Cognitive Deflation Contract; endpoint "No Agent swarm. No giant prompt. No 253K context. No 424 calls."; three laws: (1) marginal cognitive cost of mastered work approaches zero; (2) estate growth must not proportionally grow active cognitive surface; (3) every model token attributable to irreducible novelty, necessary assurance, or institutional capital creation.

## Distinctive claims
1. L32 "Calls per claim step 424" (8,066 calls for 19 matrix steps).
2. L90-92 memory-starved single run = $233, 24% of dws spend.
3. L91-92 Opus->Sonnet saves only ~6% (cache reads $0.20/M both models).
4. L5-6 phase-count plan 4M vs 53.7M actual (mission m-8bbdf725cd52).
5. L53-55 per-claim 6.5B is 2.5x the phase-average 2.6B.
6. L509 known_transform may not receive a general model worker unless the certified transform deopts.
7. L1841 no multi-billion-token forecast accepted as plan until extinction options exhausted.
8. L2155-2157 Model-Call Firewall: any cheaper resolution => "CALL REFUSED. No recommendation. Refused."
9. L3778 "The most efficient worker is a Work Unit eliminated before birth."
10. L5597 meta-optimisation stop-loss: "burn billions saving millions".
11. L5088-5090/L3720 baseline prose must stay bounded or shrink as capabilities grow (hard SLO).
12. L5736-5754 zero-work superior to zero-model.

## Open items left unresolved
- L61-66 weekly usage UNKNOWN (MONITOR_FAILURE); account blocked until 2026-10-11 18:00Z.
- L85-86 vis-2 may drop to bounded_coding after Phase 25 reality scan.
- L53-56 n=19 makes per-step rate uncertain; no re-forecast done.
- L356-371 Cognitive Recompilation Gate: 10 questions posed, none answered; ICLB not computed.
- L2396-2398 theorem-graph collapse numbers deliberately not asserted.
- L46 sleeping 46 claims and 2 owner_reality uncosted.
- All 100+ ideas (transaction miner, JIT, etc.) are proposals, none specified as build tasks or thresholds (N for extinction undefined, e.g. L1560, L3166 only 99.9%).## Coverage
- Total lines 5914; last line read 5914; Read calls 6 (1-700, 701-1600, 1601-2600, 2601-3600, 3601-4700, 4701-5914).
