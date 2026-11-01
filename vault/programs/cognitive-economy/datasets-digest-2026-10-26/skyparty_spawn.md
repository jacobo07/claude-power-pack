# Digest: Dataset CPP SkyParty Spawn Optimization 1.md
COVERAGE: total lines 2247; last line read 2247; Read calls 4 (1-600, 601-1200, 1201-1800, 1801-2247). Fully read.

## Structure
- L1-299: pasted Claude Code transcript, Gen2.1 "economic kill-shot" of TOK-18 / Cognitive Economy gen2 (pane 87601e81): sealed Stage-0, A0 floor measurement, B pass-1 ceiling, budget-unit gate, readout.
- L301-1010: Owner question "esto tambien se podria optimizar muchisimo mas?" + first reply (Phases 8-10 of SkyParty/KobiMapEngine spawn reconstruction): Read Once/Reason Once/Prove Once/Observe Once/Reuse Everywhere; compiled closeout; amplification metrics.
- L1012-2247: second reply: 40 numbered ideas; Closeout Transaction, Novelty Fault interrupts, deterministic runner, Spawn Proof Bundle, semantic scene graph, amplification governors, extreme target table.

## Part 1 (L1-299) Gen2.1 transcript
- L1-22: Gen2.1 reduced scope: no A1 probes before 2026-10-11T18:00Z, agents default 0, spend capped at 15M tokens counted from anchor 19,196,694 processed at 2026-10-05T11:13Z; Stage-0 sealed in commit 61e7b083; new metrics Resident Prefix Tax and Meta-Work Tax; canary renamed InfinityOps / odr-device-trust. A call in the old session costs ~2x a fresh session's (L2).
- L24: campaign cost = 19.2M before approval (7.84M was owner-mapping agent) + Gen2.1 spend.
- L30-38: InfinityOps phases 1-3 measured 374.5M tokens, 17.8-25.5M per plan; "about 70M" Phase 4 = plans x average (banned method). Unconfirmed: floor breakdown 35K tool schemas/45K instructions/13K agent listing/12K skill listing/9K hooks; per-role spend planner 14.6M, researcher 8.9M, verifier 7.4M, executor 1.6M. A0 to measure.
- L84-89: bugs in reused scripts: per-worker floor divides by hard-coded 8 workers (KSR has 7, KME 3); KSR double count via io_context_rent.py counting prompt_snapshot; broken chars-to-tokens ratio for 2 KME workers.
- L94-111: B pass 1 zero-model call-elimination ceiling: mechanical calls 3.6-6.7% of calls (2.9-5.4% of tokens), below 10% bar; infinityops calls=1,531 processed=375,580,969; CLEAR 4.0% of calls, TESTRUN 1.4% (test runs marked "possibly eliminable", not waste).
- L63-73, L96-97: cep_gen2.py gate: budget unit must be in BUDGET_UNITS={"processed"}; processed = input + cache_write + cache_read + output deduplicated by message id; "processed vs weighted differed ~6x in this estate"; mutants "untyped-budget" and "weighted-budget" added to self-test; live gate FAIL with 8 open W-units (W3-W9, R).
- L172-184: ledger.json: authorization_boundary 150,000,000; estimates 40M/78M/150M; gen2_1 target 10M, warn 10M, hard_cap 15M; superseded: previous optimized TOK-18 400-650M cap 800M; unoptimized projection 1.3-2.4B.
- L196-207: this pane spent 6.10M since anchor (120 calls, 39 subagent calls, subagent ctx 7.84M); other pane 8.44M; Gen2.1 total 14.54M just under 15M cap; campaign total ~33.7M (L216).
- L221-229 floor per worker: InfinityOps 129k (CPP-controlled ~80k, instructions ~45k); KSR 121k (~79k, instr ~45k); KME 138k (~90k, instr ~54k, agent listing ~18k). Remaining 40-48k = host system prompt + tool schemas; open question = how much is account connectors. Floor = 44-49% of main-worker context (L234). Hook output printed during a run = 11-13% of context (L236).
- L244-249: Do not build Model-Call Admission (mechanical calls <10%). Real tax = planning subagents: ~32% InfinityOps tokens, ~22% KSR, ~1% KME (plans in main session). KME ~11.9M per plan vs 18-28M.
- L264-285 levers: a) stop hooks printing text on success; b) shrink CPP-controlled floor (E1 rules experiment, skill-capability owner); c) remove most planning subagents by compiling work packets; d) bounded fresh workers. ~42% cut central vs 20% pessimistic. Build cost low/central/high 6M/15M/30M; InfinityOps Phase 4 canary 9M/16M/28M; expected savings ~238M central, ~100M pessimistic; return ~5.8x on new spend, ~4.0x incl. 19.2M, pessimistic ~1.1x so stage gates stay.
- L287-288: question to Owner: (1) silence hook output on success ~2-5M after measuring estate cost; (2) compiled work-packet path proven on InfinityOps Phase 4 canary after 2026-10-11T18:00Z; or both with caps.
- L58-60, L298: claude_md_linter WARN ~/.claude/CLAUDE.md = 39812 chars (>=38000); reduce by retiring a rule, not externalizing a trigger.

## Part 2 (L301-1010) first reply
- L307: remaining Phases 8-10 projected 70-140M = epochs of ~34M each, each ~100-150 calls loading ~280K; "shows what the old architecture costs", not what 8-10 needs.
- L309-323 law: Read Once (immutable source ingested once per version/hash; consumers get symbols/ranges/contracts/projections), Reason Once (resolved uncertainty becomes durable Fact/Decision/Invariant), Prove Once (receipt tied to dependencies; revalidate only affected closure), Observe Once (one staging run collects all compatible observations), Reuse Everywhere.
- L327-343: provider processes whatever context is sent, so the fix is to stop sending it: source -> indexed semantic artifact -> durable external state; work unit gets small projections. Goal is not cache the 280K but make it stop crossing the model boundary.
- L352: Phases 1-7 already paid ~211M context + ~694K output; convert to durable capital. New worker input table (L359-370): HEAD/build, open obligations, final contracts, proof receipts, staging contract, bot scenarios, KobiMapEngine interfaces, open unknowns, claims, rollback contract.
- L397-407: Phase 8 = deterministic experiment compiler -> deployment artifact -> staging -> deterministic bot scenario -> structured observations -> assertion engine -> Proof Receipt; model only on failed/ambiguous/unexpected. "Evidence Multiplexing" (L436-442): one run, many claims; causally isolated claims run separately.
- L449-465 Model only on anomaly: happy path tool->receipt->validator->next; failure -> tiny Failure Delta -> model -> rerun affected proof.
- L472-549: Phase 9 benchmark = analytics, software generates before/after, cost per obligation, FPVY, calls, context; maybe one bounded call. Phase 10 compiled from semantic commits; handoff = view of canonical state. Remove historical planner for 8-10 (L553-569); compiler emits Work Graph; planner only if Reality Scan finds unresolved architecture.
- L574-588 arithmetic: historical epoch ~100 calls x ~280K ~ 28M; bounded closure worker 5 calls x 120K ~ 0.6M. Fewer calls beats smaller context.
- L599-616 challenge table: Phase 8 ~4-10M if green (was tens of M); Phase 9 ~0.5-2M; Phase 10 ~0.5-2M; total green ~5-14M (vs 70-140M); with one real repair ~10-25M. Soft target <=15M; hard economic stop ~25M; 5-10x+ reduction.
- L621-639 stop condition: if 10-15M burned and still doing planner calls, status narration, full-file rereads, raw-log interpretation, repeated proof setup -> stop (compiled path not active).
- L644-754 metrics: Raw Read Amplification (bytes read repeatedly / source size; ideal ~1x), Model Read Amplification, Reasoning Amplification (times a Decision ID is re-derived; target ~1), Proof Amplification (claim+dependency fingerprint; caveat Gen1 found only 0.5% of proof reusable, accept that number), Reality Acquisition Amplification, Semantic I/O vs Raw I/O.
- L757-808: execution unit = bounded closeout mission (one Work Packet, one staging experiment, one anomaly budget, one proof closure, one institutionalization pass); runtime envelope derived from Work Graph; hard limit by semantic progress: after N model calls with no change in open obligation count, proof frontier or runtime claim status, stop.
- L813-866: bot is deterministic actor, not an Agent; log parser extracts claim-relevant events, exceptions, timing violations, state divergences; raw log stays addressable; visual evidence via registered check, not kept in text context.
- L869-976: after first reconstruction (expensive, discovery), 2nd known family, 3rd certified, Nth near-zero frontier cognition; next comparable rebuild should not cost 280-350M. Golden Reconstruction Artifact (semantic geometry, contracts, assets, registrations, invariants, build identity, deployment recipe, bot proof, failure signatures). Generalise as universal CPP law (L955-959); benefits KME, KSR, InfinityOps, QuickLease, TUA-X.
- L984-996 decision: do not arm new Phase 8-10 mission under historical runtime; first deterministic cheap compile of the Obligation/Proof/Reality Graph from current HEAD + Phase 1-7 receipts, then single bounded Closeout Packet; challenger 5-14M green, <=25M hard stop; rebudget only on true novelty.

## Part 3 (L1012-2247) second reply
- L1016-1018: "ingest once -> compile once -> deploy once -> observe once -> prove once -> institutionalize once", model only as novelty exception handler. Refers to GSD X reconstruction doctrine: Scope, Representation, Inference, Search, Proof, Institutional Compression are multipliers not additive (L1023, L2231).
- L1031-1039 fingerprint table: Read Once (content/version -> projection), Reason Once (question+dependencies -> existing Decision), Build Once (source+config+toolchain), Prove Once (claim+dependency state), Observe Once (build+env+scenario), Deploy Once (artifact+environment).
- L1045-1055: Full-Read Admission Gate: re-read of unchanged-hash file triggers "why do you need full materialization?"; default symbol/range/query/projection.
- L1060-1129: floor ~120K x 100 calls still expensive; first model turn gets Closeout Capsule (exact state, HEAD/build id, open obligations 8-10, closed decisions, KobiMapEngine contracts, staging authority, bot proof contract, Production Reality contract, deopt semantics); model emits durable Closeout Program; deterministic runner does build, deploy, readiness, bot, assertions, logs, evidence, proof, benchmark. Today model->tool->model->tool; target model -> compiled transaction -> deterministic runtime -> receipt.
- L1176-1196 four interrupt classes: NOVELTY_FAULT, PROOF_FAULT, REALITY_FAULT, AUTHORITY_FAULT; otherwise 0 new reasoning calls; Claude = exception handler not scheduler.
- L1213-1237 Failure Capsule (failed claim, observed vs expected, relevant events, affected contracts, build id, minimal source closure, live hypotheses); one call, fix, rerun only affected closure.
- L1290-1292: scenario compiler turns 20-80 reasoning/tool loops into one invocation boundary.
- L1387-1411: CLOSEOUT_TRANSACTION with subgraphs Reality Closure -> Economic Closure -> Institutional Closure; phase elimination without scope elimination.
- L1416-1473: content-addressed build, staging lease, one deployed artifact for all compatible scenarios, proofs tied to artifact hash; no rebuild if source/config unchanged; checkpointable staging (fresh env only for claims needing clean boot).
- L1477-1520: reality-question fingerprint (build B, config C, env E, scenario S -> answer A) and evidence subsumption: query Evidence Graph before any experiment (extends Oracle Memoization to experiments subsuming new questions).
- L1525-1569: Spawn Proof Bundle; next rebuild = compare Current Spawn Image vs Certified Spawn Image -> apply delta -> prove affected closure.
- L1613-1750: Semantic Scene Graph as source of truth, KobiMapEngine as backend compiler; map change = semantic delta ("move portal 3 blocks"); spatial proof compilation (collision, bounds, symmetry, distance, portal reachability, protected anchors, spawn safety) machine-checked; incremental visual proof by region; invalidation cone (e.g. other 34 arenas unaffected).
- L1754-1804: One-read at five levels (Source, Project, Mission, Worker, Model); Read Amplification Governor with three metrics (Raw Source, Model Source, Semantic Page); repeated 20x flags and is classified: necessary attention / host limitation / bad indexing / bad context lifetime; "No invisible reread".
- L1809-1853: Reasoning (decision re-derived 7x = institutional state not consumed), Experiment, Proof, Build Amplification Governors.
- L1855-1936: tool-call amortization: compile deterministic operation batch; runner needs preconditions, step identities, timeouts, failure stop, receipts, idempotency, rollback/compensation, checkpointing (observable, not opaque). A model turn must change unknown->known, decision, architecture, failure hypothesis, repair, or authority; no semantic delta = probably no model call. Call coalescing: run all independent checks then one call.
- L1957-2033: failure-directed source loading (JIT debugging via dependency cone), failure diagnosis tree signature->discriminator->branch, push failure detection left (bad geometry before server build, bad config before deploy, etc.), Phase 8 preflight everything before staging.
- L2037-2139: Cost Receipt emitted on every execution so Phase 9 = aggregate; Phase 10 incremental (Fact, Decision, Failure Motif, UKDL candidate, CBR candidate); handoff generated from state; RECONSTRUCT_KME_SPAWN certified transformation family.
- L2148-2155 extreme target table (model-bound processed tokens): historical 70-140M; first optimisation 5-14M; extreme compiled green path 1-5M; one anomaly + repair 3-8M; multiple novel failures 8-15M; >15M mandatory recompile/rebudget. Math: 10 calls x 150K ~1.5M; 20 calls ~3M; from ~200-400 future API messages to single/low-double-digit.
- L2177-2200: Phase 8 green path 0 planner, 0 researcher, 0 model calls between bot actions or for passing assertions, 1-3 reasoning calls max; Phase 9 0 calls; Phase 10 0-1 calls.
- L2206-2229: universal contract: One-Version Read, One-Uncertainty Reason, One-Artifact Build, One-Environment Observation, One-Valid Proof, One-Derivation across compatible consumers, with dependency-based invalidation.

## Distinctive claims
1. L307: "Los 70-140M restantes son una proyeccion basada en epochs de ~34M" - the projection measures the old architecture's cost, not the work's need.
2. L574: biggest reduction is lowering calls, not 280K->200K (100 calls x 280K ~28M vs 5 x 120K ~0.6M) (L574-588).
3. L1196: "Claude deja de ser el scheduler y pasa a ser el exception handler de inteligencia."
4. L2238-2241: an API call should represent "the runtime found an uncertainty its machinery cannot resolve", not "the next agent step".
5. L244: mechanical calls are 3-6% of tokens, below the 10% bar: "Don't build Model-Call Admission."
6. L246: real tax is planning by subagents, ~32% InfinityOps, ~22% KSR, ~1% KME.
7. L234: the floor is 44-49% of each workload's main-worker context.
8. L63: "A budget whose unit can be read two ways is not a gate (processed vs weighted differed ~6x)".
9. L1411: "phase elimination without scope elimination."
10. L2154: extreme target 1-5M for green path vs 70-140M historical.
11. L1930: "No semantic delta: probably no model call."
12. L283: pessimistic return only ~1.1x so stage gates stay.
13. L708: Gen1 proof reuse measured ~0.5%; "No inventar reuse."

## Open items
- L287-288, L292-295: Owner must pick next build (hook silence ~2-5M and/or compiled work packets) and cap; BLOCKED on 15M cap.
- L295: adaptive A1 (host vs account connectors) after 2026-10-11T18:00Z; KME context-type split low-confidence; 8 open gen2 W-units.
- L35-38: floor breakdown and per-role spend unconfirmed; A0 to measure.
- L43: "blocked mission can renew itself into old architecture" reproduced only via relayed scan.
- L608: challenge numbers (5-14M, 1-5M) explicitly not forecasts; unvalidated until obligations compiled.
- L984-994: deterministic Phase 8-10 Obligation/Proof/Reality Graph compile and Closeout Packet proposed, not built; compiler/deterministic runner/bot scenario compiler "if exist or cheap to extend" (L2144).
- L1778-1850 governors, L1780 Read Amplification Governor, L1055 Full-Read Admission Gate: proposed only.
- L2113-2137: RECONSTRUCT_KME_SPAWN family is "eventually".