# cwops_opt.md (digest; coverage line at end)
## Structure
- L1-50 Part A: pasted Claude Code output: Phase 4 cost estimate for ODR/device-trust mission (m-608c8d8d761f), plus Stop-hook/FIOS and CLAUDE.md linter lines
- L52-962 Part B: first Owner-asked reply: cache-read is a global structural tax (Resident Prefix Tax), TOK-18 proposals, Phase 4 as canary
- L964-3300+ Part C: second reply: 117+ numbered ideas, Cognitive Memory Traffic / Context MMU (continues)
## Part A (L1-50)
- L1 Phase 4 finish est. 55-100M tokens, most likely ~70M, ~98% cache reads.
- L5-19 Measured phases 1-3 (31 transcript files, 1,531 messages, 55 commits assigned to next commit's phase): P1 457 msgs 113.9M cache reads/2.37M writes/268k out = 116.5M (7 reqs, 5 plans); P2 530 msgs 127.4M (5 reqs, 5 plans); P3 342 msgs 89.1M (4 reqs, 5 plans); P4 so far 202 msgs 41.6M; total 374.5M (365.6M cache reads, 8.11M writes, 809k output).
- L22 Fresh non-cached input only ~3,000 tokens in whole run.
- L26-30 Plan cost 18-25M all-in (P3 17.8M, P1 23.3M, P2 25.5M); P4 3-4 plans x 18-25M = 54-100M; real figure should fall lower half.
- L37-39 Unmeasured: plan count (each extra plan ~20M); milestone audit/closeout cost.
- L42-46 Mission m-608c8d8d761f BLOCKED, worker dfc0acda alive, asking to run gsd-tools workstream.set odr-device-trust; arming new mission would create two writers.
- L47-50 Stop hook FIOS: 216 assets/17,822,058 tok; ~/.claude/CLAUDE.md = 39,812 chars (>= 38000 warn); "Reduce by retiring a rule, not by externalizing a trigger."
## Part B (L52-962)
- L58 365.6M of 374.5M = cache reads, ~239K per message; KSR: 267.7M of 273.9M (97.7%), ~240K per call: convergence = institutional resident-prefix tax.
- L66 "Cache hit != architectural efficiency."; L70-91 Cognitive carriage ~ Model calls x Resident prefix; sensitivity table: current 1,531 x 239K = 366M; 60K prefix = 92M; +50% fewer calls (~765) = 46M; working sets ~40K = 31M; compiled mature ~400 x 30K = 12M (not a promise).
- L99-113 Context Rent = size x future invocations; 10K rule resident 100 calls ~1M; 20K explanation 200 calls ~4M; true cost = size x reach x lifetime x invocation frequency.
- L122-183 Global Resident Context Profiler: decompose 239K into kernel, CLAUDE.md, rules, Skill/Agent descriptors, tool/MCP schemas, goal/WU state, history, source, tool outputs, proof output, agent results, misc; per block size/calls resident/consumers/last use/page faults/criticality/reload cost; example "47K kernel, 35K capability descriptors, 28K tool schemas, 72K historical state, 31K stale tool output".
- L188-216 Metrics Global Context Rent and Dead Context Rent (30K object resident from call 40 to 170 => ~3.9M dead).
- L225 Rule: no context object resident merely because previously seen; needs open consumer, proven high-reuse role, or critical need-time guarantee.
- L240-264 Context GC continuously after decision sealed/proof/commit/root cause/WU closed (not /clear at 400K or rollover 180K).
- L269-289 Three prefix categories: resident kernel (tiny), need-time guaranteed, cold pageable.
- L294-312 CLAUDE.md ~39.8K chars warns; three valid destinations: compile to runtime enforcement, tiny trigger + pageable procedure, retire.
- L317-363 Skills: 500 skills must not mean 500 descriptions resident (tiny directory -> resolver -> signature -> body only if needed); 95 Agents not 95 specs resident (ephemeral specialist); tool schemas virtualized (Git+fs+tests only).
- L385-448 History replaced by facts/decisions/falsified hypotheses/proofs/commits/side effects/open obligations; tool outputs lifetime seconds/minutes (40K test -> ProofReceipt; evict).
- L453-496 Context lease (admit, declare consumers, evict when closed); Cognitive Leak Detector ranked by bytes x calls x frequency.
- L501-535 Model Call Admission: poll/count/hash/query/run test/move artifact/check status/known fact/reuse proof => 0 model calls.
- L540-558 "Each extra plan adds ~20M" = defective architecture signal; budget unit should be remaining semantic obligations not plan count.
- L563-577 Global Prefix Compiler: Kernel + WU + live deps + applicable capabilities + authority + proof = ContextImage.
- L582-598 Context budget per WU: mechanical 10-20K, known implementation 20-50K, novel architecture ~80-150K (to be measured).
- L611-629 Cache-Read Amplification = cache-read tokens / useful live semantic info; L634-676 Global Resident Prefix Floor measured with empty WU; floor bounded as Skills 100->1,000->10,000.
- L678-717 Physical prefix cache secondary; semantic cache > token cache (Fact A17 + Decision D9 + Proof P2; ~700 tokens materialised vs 20K).
- L720-759 Cross-project kernel: admission, paging, liveness, eviction, proof reuse, singleflight, telemetry (KME, KSR, ODR, QuickLease, TUA-X, InfinityOps).
- L763-796 Before/after benchmark table (cache-read/call, calls/obligation, active context surface, dead rent, proof reuse, raw rereads, agent fan-out, correctness, production reality).
- L801-821 Sensitivity: 120K/msg ~184M; 60K ~92M; 40K ~61M; ~750x60K 45M; ~500x40K 20M.
- L830-902 Recommendation: do not unblock Phase 4 at ~70M by default; first build TOK-18 vertical slice (Global Prefix Profiler, ContextImage compilation, semantic checkpoint, fresh bounded worker, tool-output eviction, model-call admission, proof reuse), then use Phase 4 as canary/challenger vs champion ~55-100M (central ~70M); outcomes: 15-30M with equal proof = strong; 60M = insufficient; fail = deopt.
- L907-925 Candidate baseline laws: no long-run workload enters scaled execution while cache-read dominated by dead/non-applicable resident context; "A HIGH CACHE-HIT RATE IS NOT EVIDENCE OF COGNITIVE EFFICIENCY."
- L930-958 FIOS target report: "Cache reads 40M; Required resident 31M; Deliberate reusable rent 6M; Dead/non-applicable rent 3M; Avoided by Context MMU 290M; Calls eliminated by admission 620" (illustrative).
## Part C (L964-3300)
- L968 KSR corpus: 273.9M context for 670K output; 0.35-1.2B extrapolation; problem named Cognitive Memory Bandwidth.
- L1003-1048 Traffic classes: Required, Reusable, Avoidable, Dead; example 365M = 48M required + 37M reusable + 280M avoidable (unknown, TOK-18 to measure).
- L1053-1097 Rent = size x invocations resident; Dead Rent after final consumer; 20K held 300 calls = ~6M; Universal Residence Multiplier = size x reach x invocation freq x lifetime governs what lives in CLAUDE.md/rules/listings/schemas.
- L1102-1137 Global Cognitive Memory Profiler classes (Kernel, doctrine, capability directory, project state, goal, WU, history, source, tool results, proof, dead/unowned); flamegraph e.g. "92M history, 41M capability listing, 27M stale tool output, 18M doctrine".
- L1142-1215 Cognitive RSS: Useful, Speculative, Dead, Pinned; Working set declared per WU (ODR Phase 4 UI route example); Context MMU computes closure.
- L1219-1280 Four surfaces L0 kernel, L1 WU working set, L2 warm semantic cache, L3 cold institutional memory; AVAILABLE vs WARM vs RESIDENT (page 400 tokens, not 30K).
- L1282-1345 Physical prefix cache vs semantic cache (entries = derived object with inputs, dependency fingerprints, version, proof, scope, freshness, invalidation).
- L1379-1426 KPIs: Cognitive Bandwidth Efficiency (live semantic info / tokens transported), Context Utilization (prefetch miss, lifetime bug, good resident candidate).
- L1429-1520 Context TLB (semantic need -> object IDs), page table fields (identity, location, size, epistemic type, freshness, fingerprint, page cost, last access, consumer set, criticality); eviction by reuse probability, reload cost, size, proof strength, criticality, open consumers, dependency centrality, horizon (not LRU).
- L1522-1563 Belady oracle benchmark over historical trajectories (actual 365M vs oracle lower bound vs candidate); Semantic Belady / Semantic Last Necessary Use.
- L1568-1640 Liveness states LIVE, POTENTIALLY_LIVE, DEAD, PINNED, COLD_DURABLE; generational GC (nursery tool outputs, goal gen, project gen, institutional gen); Durability != Residency.
- L1642-1713 GC at semantic checkpoints (decision sealed, proof committed, WU closed, hypothesis falsified, agent result consumed, commit sealed); DEAD_CONTEXT_LEAK alert (zero consumers still resident after 20 calls); Context Leak Budget with observe -> shadow gate -> canary -> enforce ratchet.
- L1717-1800 Prefix decomposition P0 stable kernel, P1 project overlay, P2 goal overlay, P3 WU overlay, P4 ephemeral evidence; co-design semantic sparsity with provider cache stability (stable -> variable ordering, Authority -> Goal -> WU -> evidence).
- L1804-1865 Semantic fragmentation, Cognitive Huge Pages (KME: map-generator contract + ownership + verification contract; KSR: build identity + lifecycle contract + evidence), promotion/split.
- L1867-1985 Cross-session object sharing; cross-agent zero-copy; Agent Communication Amplification = tokens exchanged / semantic payload needed; parent context inheritance opt-in; copy-on-write cognition; semantic merge.
- L2000-2060 Model call coalescing, estate-wide singleflight across panes/accounts/machines ("Accounts become processors"); Global Derived Fact Store; build-system semantics; mission startup = linking not loading.
- L2099-2142 Startup floor split: Hard Floor (platform) vs Soft Floor (CPP choices: rules, listings, schemas, doctrine); scale test 100 -> 10,000 capabilities.
- L2145-2221 Hierarchical capability directory/tool schemas; learned routing only after deterministic pruning (don't route among 500 when rules eliminate 490); cached tool invocation plans.
- L2223-2287 Narrative amplification: 2K assistant explanation resident over 100 calls ~200K carriage; Narrative Rent; explainability on demand from provenance graph (Evidence -> Decision -> Action -> Proof); review reports as diff receipts.
- L2310-2386 Plans compiled to work graph (20K plan with 5 WUs, workers read their node); Plan Amplification Ratio = cognition spent / novel planning decisions; "Plan cost 20M" = red alarm; Plan CSE; integration-boundary reviews instead of phase reviews; verification contracts precomputed.
- L2389-2470 Proof results cached semantically; test logs never long-lived (pass = small receipt); git/search/source outputs projected; Cognitive DMA (tool -> artifact store -> consumer tool; "The LLM should never be a byte transport mechanism").
- L2486-2548 Goal snapshot + delta log (LSM-tree semantics); deterministic semantic compaction at runtime; conversation compaction obsolete.
- L2550-2605 Context wall as exception metric: most WUs close at 20-60K; pressure feeds work graph (split if 140K across domains; fuse if many tiny workers page same 30K); locality scheduler.
- L2608-2677 Provider KV reuse = L5 optimisation; LMCache-style later; ContextImage compiled to provider-specific layout; prefix cost in provider fitness.
- L2674-2750 Cache-read budget per verified obligation (known KME change should not use 50M cache reads; goes into CI); PR increasing startup floor +5K, global rule residency +3K, tool listing +4K needs justification; global resident context = protected resource; Resident Context Admission Gate (safety-critical before runtime can intervene? near-universal? small? miss catastrophic? tiny trigger instead?).
- L2769-2868 Two CBR ratchets: Knowledge/Behavior Promotion vs Residency Promotion (second extremely rare); compile guarantees to enforcement; Instruction Elimination metric (tokens of doctrine retired); classify each resident instruction: irreducible judgment / temporary scaffold / trigger / legacy debt; Global Prompt GC; "Protected doctrine" != permanent.
- L2886-2936 Hook output budget (tiny structured receipts; hooks event-specific; hook run 100K times can dominate); agents/skills/tools signature global, body on spawn.
- L2950 Universal law: "EVERYTHING IS PAGEABLE EXCEPT THE MINIMUM TRUSTED KERNEL AND THE CURRENT LIVE WORKING SET."
- L2957-3060 Bandwidth-bound vs compute-bound; Cognitive Roofline (KME/KSR/ODR near bandwidth wall); Amdahl (cut cache reads 90% -> verification 45% next); Global Hotspot Tournament; score = cost/event x events x estate reach x persistence / fix cost (500-token global leak can beat 500K local leak at 1M runs).
- L3073-3180 Prevent meta-optimisation addiction (20-line change removing 80% wins); kill switches (shadow -> compare ContextImage -> canary -> enforce); false-negative context severe, false-positive = rent; context coverage tests vs historical needs; context mutation testing; page-fault recovery; confidence from dependencies not model self-confidence.
- L3188-3290 Context Compiler as optimizing compiler with JIT (monomorphic/polymorphic/megamorphic templates; memoized templates); delta encoding; prefix as ABI (Kernel, Goal ID, WU contract, pointers); 240K -> low tens of K for routine WUs is a hypothesis; KSR scenario 50-70K plus fewer calls.## Part C continued (L3292-5743)
- L3292-3308 Known certified transformation: tiny kernel + parameters + affected state + proof, single-digit/low-tens-K context, maybe no model.
- L3313-3345 Frontier Cognition Purity (share of model-bound cognition that is novel); target is "zero unjustified cache-read rent", not zero cache read.
- L3351-3445 Three controllers: Memory (minimise data movement), Compute (model-call admission, provider selection, agent spawn, concurrency, singleflight, budgets, deopt), Proof (obligations, cache, freshness, affected closure, assurance escalation); FIOS as performance-counter layer (cache traffic, working-set size, page faults, dead rent, reuse hits, deopts, model calls, proof hits, scheduler waits); counters always, sampling selectively, full trace only on anomaly.
- L3494-3585 Regression alarms relative to Work Class (known UI route 40K -> 180K = alarm; novel arch 180K may be fine); Cognitive Performance CI over CLAUDE.md/rules/Skill listing/Agent defs/tool schemas/Context Compiler; Projected Estate Rent in review (2K resident x 50,000 calls/month = 100M token-context/month); removal of 4K global block = high priority; Context ROI = benefit (failures prevented, calls improved, misses avoided) vs cost (rent, complexity).
- L3602-3656 Laws: "THE COST OF KNOWING SOMETHING MUST NOT BE CONFUSED WITH THE COST OF KEEPING IT PRESENT"; "CACHE SHOULD PRESERVE COMPUTATION, NOT JUST PRESERVE BLOAT CHEAPLY"; "A CACHE HIT ON AN UNNECESSARY OBJECT IS STILL AN ARCHITECTURAL MISS"; "PRIMARY OPTIMIZATION TARGET IS... THE MINIMUM VERIFIED WORKING SET"; "GLOBAL RESIDENCY MUST REQUIRE GLOBAL VALUE."
- L3689-3760 Cognitive Memory Fabric; constitutional objective "No pagar por mover hacia un modelo ningun estado que pueda permanecer fuera de el sin degradar correctness, authority o proof"; three levels physical cache hit / semantic reuse / residency avoidance.
- L3736-3780 Traffic classes: kernel, live working set, reuse, speculative, dead, duplicate, historical; illustrative FIOS line "Cache reads 365M; live 51M; justified reuse 24M; speculative 11M; historical/dead/duplicate 279M; avoidable 76%" (not measured).
- L3787-3840 Semantic Memory Address Space: Fact F932, Proof P208, Decision D51, Contract C17, Skill K9, ArchitectureSlice A31, FailureMotif M8, HardwareObservation O77; "access to millions of objects, 18 resident".
- L3844-3990 Content-addressed objects (content/version + source deps + transform version + scope); zero-copy between workers; shared immutable base + private overlays, merge deltas at join; cognitive cache coherence via dependency edges (F932 depends on source hash S19, parser P3, architecture revision R81).
- L3996-4025 Semantic cache hierarchy L0 pinned microkernel, L1 WU resident set, L2 Goal cache, L3 Project cache, L4 institutional capability cache, L5 indexed raw evidence, Archive; goal: L1 small while L3-L5 grow unbounded.
- L4030-4050 KME and KSR as two reference workloads (KME 100x repo/history without 100x working set; KSR 100x experiments without 100x diagnosis cognition).
- L4097-4190 Compute order: deterministic -> semantic-cache hit -> certified transformation -> specialised capability -> cheap model -> general model -> frontier -> Owner; Proof Controller; bottleneck shifts (KME proof/build-bound, KSR hardware/observation-bound).
- L4194-4345 Cognitive IPC (object IDs, events, deltas, receipts, faults; NL only for novel reasoning/Owner/ambiguity); semantic event bus ("dependency D17 changed and invalidated Proof P4 consumed by Goal G8"); semantic interrupts (DEPENDENCY_INVALIDATED, PROOF_STALE, NEW_EVIDENCE, HARDWARE_RESULT, AUTHORITY_GRANTED, QUOTA_AVAILABLE, NOVELTY_FAULT); Cognitive DMA (50MB build logs never cross model); RDMA between laptop and GEX44; NUMA-aware scheduling.
- L4348-4410 Cognitive I/O scheduler (one extraction for 10 WUs; one build for two goals; share one boot for 3 KSR experiments); model call fusion (5 x 40K -> 1 x 45K if independent) and fission (180K with 3 disconnected concerns -> 3 x 35K = 105K).
- L4415-4535 Prefix algebra: Stable Kernel + Project Overlay + Goal Overlay + WU Overlay + Evidence Pages with identity/version/size/lifetime; prefix normalisation; Prefix ABI versioning (Kernel ABI v12, Project Overlay v4, Goal contract v9); instruction cache vs data cache; semantic instruction cache; routine prompts become opcodes (CHANGE_STATE_MACHINE).
- L4543-4605 Micro-op fusion; Work Unit JIT; deopt packet content (failed assumption, affected object IDs, evidence, required proof, current state); "if deoptimization reloads ~240K, the architecture has failed" proposed as done-gate (L4601-4603).
- L4608-4700 Context speculation outside context, speculation budget (low prefetch hit rate => disable policy); Cognitive Cache Miss Cost (500 tokens retrieval vs 20K archaeology vs Owner interrupt); criticality (300-token authority invariant pinned; 10K optional history evicted); working-set estimation per Work Class; work-class Context SLOs (no universal static cap).
- L4732-4800 Resident Prefix Tax as estate budget (+1,500 resident tokens x 50K future calls = 75M exposure); global residency changes treated like kernel hot-path; Residency Budget per layer (kernel, capability directory, project overlay, goal, WU).
- L4801-4883 Importance != frequency != residency; five separate decisions Durable/Available/Warm/Resident/Pinned; proofs resident as status+hash not body; UKDL globally available not globally read (applicability index first); CBR guarantees as compiler constraint/guard/test/runtime invariant not 500 tokens of prose.
- L4888-4975 New metrics: Enforcement-to-Prose Ratio, Prompt-to-Infrastructure Ratio, Semantic Payload Density, Resident Knowledge Entropy, Context Churn; multi-objective context compiler (correctness, recall of critical deps, size, cache stability, fault cost, churn, latency).
- L4978-5060 Cross-machine/account content-addressed cache; secure semantic sharing (scope, tenant, sensitivity, authority; "KME can't page CostaLuz raw object merely because hash exists"); taint tracking; institution-level GC; knowledge LSM compaction; semantic Bloom filters; hierarchical capability indexes.
- L5130-5265 Attention budget (semantic branching factor; 30K coherent may beat 20K fragmented); graph-cut framing; cross-cut edges = architecture debt; cognitive locality refactoring; NFRs Cognitive Locality, Stability, Discoverability, Portability => "AI-Operability" standard (locality, discoverability, proofability, observability, typedness, reconstructability, effect clarity, dependency clarity).
- L5281-5348 Technical Capital Allocator ranks refactors by context-rent savings (refactor 5M cognition reduces avg WU by 8K over 5,000 calls = 40M avoided); Estate-wide Context Rent NPV, top 20 lifetime context liabilities; context debt = recurring interest (40K CLAUDE.md residual, large Skill descriptions, tool schema bloat, huge GSD docs).
- L5353-5455 Asymptotic law ActiveSurface(W) ~ f(dependency closure) not f(K+C+H); for mastered WUs cost decreases as institution grows; end-state example: 20,000 skills, 50M messages, 200 projects, "Fix known KME map registration regression" -> ~12K ContextImage, no agent fanout, maybe zero-LLM.
- L5460-5485 Reframe TOK-18 as "Cognitive Memory + Compute + Proof Fabric": memory moves minimum semantic state; compute invokes minimum sufficient intelligence; proof revalidates minimum affected truth.
- L5490-5550 Phase 4 as first global cache-read canary: before unblocking old worker compile remaining obligations, run candidate runtime, compare with ~55-100M (central ~70M); target is meaningful reduction in cache-read per verified obligation with unchanged proof quality (e.g. 70M->25M strong; 70M->60M another bottleneck); KME and KSR second/third canaries.
- L5576-5743 Final reply to Owner question "no habiamos armado ya workstreams para esto?": yes - owner is PLAN-COGNITIVE-ECONOMY-PROGRAM / Goal cpp-cognitive-economy; audit said EXTEND not create; TOK-18 created as extension; backlog items (exclude worktrees from searches, dedupe transcript readers by realpath); do NOT open another cache-read workstream; first step of new prompt should be an ownership table (Fresh epochs ADOPT/EXTEND; Context lifetime ADOPT; Startup floor EXTEND; Reread reduction CONNECT; Source virtualization CONNECT; Skill virtualization CONNECT; Proof reuse CONNECT; Context MMU EXTEND; Resident-object liveness BUILD only if missing; Dead Context Rent accounting BUILD/EXTEND; estate-wide cache-read attribution (FIOS?) EXTEND; admission/eviction EXTEND; CBR enforcement CONNECT); gap is a certified closed circuit: consumer closes -> object dead -> Context MMU evicts -> future worker references durable object -> pages only if dependency returns -> FIOS records avoided rent -> CBR prevents regression; attribution illustrative "38M kernel, 22M reuse, 180M dead rent, 60M capability leakage, 40M historical, 25M tool-output carriage".

## Distinctive claims
1. L58 Two different workloads converge at ~239-240K cache-read per call (365.6M/1,531; KSR 267.7M/273.9M=97.7%).
2. L22 Fresh non-cached input ~3,000 tokens across the whole run.
3. L558 "each additional plan adds ~20M" is an architecture defect signal, not a production law.
4. L66 "Cache hit != architectural efficiency."
5. L225 No context object may stay resident merely because previously seen.
6. L503-535 Model Call Admission: polling/counting/hashing/known-fact/proof reuse must be 0 model calls.
7. L539-541 Recommends NOT unblocking Phase 4 at ~70M; use it as canary after TOK-18 slice.
8. L2242-2250 A 2K assistant narration persisting over 100 calls ~ 200K carriage (Narrative Rent).
9. L3057 500-token global leak can beat 500K local leak at 1M runs (hotspot score).
10. L4601 "if deoptimization reloads ~240K, the architecture has failed" (done-gate).
11. L5018 KME cannot page CostaLuz raw object merely because hash exists (secure sharing).
12. L5580-5582 Owner already has PLAN-COGNITIVE-ECONOMY-PROGRAM; extend, do not create a new workstream.

## Open items left unresolved
- L36-39 Phase 4 plan count and closeout cost unmeasured.
- L42-46 Question to Owner whether to run workstream.set odr-device-trust unblock; unanswered in dataset.
- L1046, L3780, L5681-5690 Breakdown of the 365M cache reads (required/reusable/dead) is stated "not known yet; TOK-18 must measure".
- L597-598 Context budgets per Work Unit class (10-20K/20-50K/80-150K) "to be measured".
- L3283, L5306 Hypotheses (240K -> low tens of K) not tested; Belady oracle lower bound not computed (L1536-1541).
- L5712-5729 Ownership table rows left as "verificar" with "?" owners for liveness, dead-rent accounting, admission/eviction.
- L4602 deopt done-gate proposed, not specified numerically.
- L39812-char CLAUDE.md reduction path (L296-312) discussed but no concrete rules retired.
## Coverage
- Total lines 5743; last line read 5743; Read calls 5 (1-1000, 1001-2100, 2101-3300, 3301-4500, 4501-5743).
