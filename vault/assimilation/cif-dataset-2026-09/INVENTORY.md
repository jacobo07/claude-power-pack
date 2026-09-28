# CIF Dataset Absorption Inventory

Source: `C:\Users\User\Downloads\Dataset Context Intelligence Fabric 1.md` (~336 KB, ~15,600 lines, 9 user turns).
Repo: `C:\Users\User\.claude\skills\claude-power-pack` (branch `feature/knowledge-acquisition`).
Method: full sequential read of the source in chunks, candidate extraction, Grep-based owner search in `modules/ tools/ vault/ commands/ hooks/` before concluding absence (HR-NOVELTY-001 spirit: default EXTEND/CONNECT over NEW).

This file is written incrementally — each candidate is appended immediately after classification so a timeout only costs the tail.

---

## Candidates

**Read note:** the source's own line-range estimate (~15,600 lines) undercounts it — the real file
is **17,681 lines**, 9 user turns (boundaries confirmed by reading: 1, 397, 616, 1483, 2514, 3661,
4943, 7068, 8148, 10062, 11231, 12939, 14547, then continuing unannounced to 17681 — turn 9 is
longer than the brief implied and has no further topic break). Full file read end to end in ~600–900
line chunks, no gaps.

**Governing prior art found during search (changes almost every disposition below).** A plan file
already exists at `vault/plans/cognitive-resource-os-2026-09-27.md`, dated one day before this
dataset was apparently processed, titled **"Cognitive Resource OS"**, whose D2A table maps almost
1:1 onto this dataset's own cluster names (Repo intelligence, Tool I/O firewall, Memory reuse /
negative cache, Agent foundry / gym / counterfactual, Durable execution, Model routing, Instruction
economics, Baseline ratchet). Its governing decision already invoked **HR-NOVELTY-001**: *"0 new
mega-systems. CONNECT orphans, MERGE overlaps, EXTEND owners; NEW only for 3 primitives with no
owner."* Status: **AWAITING OWNER APPROVAL, nothing in it implemented** (line 3). Where a CIF
candidate matches one of its rows I cite the row directly rather than re-deriving a disposition.

Separately, `vault/assimilation/genesis-2026-09/ASSIMILATION_MANIFEST.json` (today, 2026-09-28,
package `"for cpp-gsd-long.zip"`) is a **different source bundle** already ingested today, and
several of its capabilities are already **LIVE** and cover CIF recommendations directly (task
ledger, evidence collector, regression memory, paired experiments, routing metrics, context budget
meter). Where that is the case I mark `COVERED_BY_TODAY_ASSIMILATION` and cite the capability id.

---

### CIF-01 — Symbol/LSP-level code navigation instead of whole-file reads
Source lines: 48–85 (Serena), 406 (jCodeMunch), 407 (codegraph), 416 (pith), 413 (semtree), 414
(opencode-codebase-index), 415 (dotcommander/repomap), 412 (Probe), 13046 (ContextGraph AST scope
graph).
Kind: EXTERNAL_RESOURCE cluster (mechanism: symbol/AST/call-graph retrieval, never whole-file).
Existing owner: `tools/audit_cache.py` — confirmed by Grep it stores `neural_summary`,
`semantic_dna`, `depends_on` at **file granularity** (audit_cache.py:26,124,166,207,309,324-326), no
symbol/LSP layer. `modules/graphify/indexer.py` also has no `symbol`/`call_graph`/`AST` matches
(Grep, 0 hits) — confirmed no existing symbol-level owner.
Plan of record: `vault/plans/cognitive-resource-os-2026-09-27.md` row "Repo intelligence | CONNECT |
harness LSP symbol-first; audit_cache stays; no new index" — phase P5, **PLANNED, not executed**.
Disposition: CONNECT (decision already made upstream of this inventory; execution pending).
Measurable claim: jCodeMunch benchmark "15.6×–39.7× fewer tokens vs grep+read" (line 406) — UNVERIFIED, no reproduction in CPP.
Priority: P1 (real mechanism gap, but already queued and decided — no new decision needed here).

### CIF-02 — Repo dependency/call-graph precompute (repo-map ranking)
Source lines: 24–46 (Aider RepoMap), 87–111 (GitNexus), 637 (CodeNib), 638 (compiler-knowledge-graph), 639 (CALM), 13021–13058 (Repository Cognitive Cache).
Kind: EXTERNAL_RESOURCE + MECHANISM.
Existing owner: `modules/graphify` (knowledge graph, confirmed present via Glob) — plan row
"genesis-context-graph | EXTEND | modules/graphify (knowledge graph) | hash-bound cards with
freshness, applicability, contraindications, approval-aware retrieval" (today's manifest, id
`genesis-context-graph`, status **PLANNED**, slice T2).
Disposition: EXTEND_EXISTING_OWNER (already decided, PLANNED not LIVE).
Measurable claim: none reproducible; "Context Value Ranker" formula in source (lines 42-46) is prose, not a number.
Priority: P1.

### CIF-03 — Tiered progressive disclosure (K0 locator → K1 capsule → K2 full → K3 raw)
Source lines: 113–150 (OpenViking L0/L1/L2), 255–277 (PageIndex/ChatIndex), 10862–10892 (AMA
multi-resolution M0–M4), 14660–14684 (turn 8's own restatement).
Kind: EXTERNAL_RESOURCE + MECHANISM.
Existing owner: HCMH ("Hierarchical Cognitive Memory Hierarchy") — per
`vault/plans/cognitive-resource-os-2026-09-27.md:19`: **"concept names only
(vault/knowledge_base/ucr_cif/); prior D2A audit exists; Owner A/B/C ruling OPEN."** i.e. CPP already
has this exact tiering doctrine on paper (K0/K1/K2/K3 in the CLAUDE.md excerpt matches almost
verbatim), unbuilt.
Disposition: EXTEND_EXISTING_OWNER (HCMH) — no new concept, doctrine already named, blocked on the
same open A/B/C ruling as everything else in that plan.
Measurable claim: OpenViking defaults "~256 chars L0 / 4000 L1" (line 124) — UNVERIFIED, external project's own numbers.
Priority: P2 (doctrine already exists; this is not a new gap).

### CIF-04 — Command-output token compression (RTK)
Source lines: 408 ("RTK — Rust Token Killer... reducciones típicas del 60–90%"), 434 (RTK applying the stdout-firewall principle to dev commands).
Kind: EXTERNAL_RESOURCE.
Existing owner: **ALREADY LIVE.** `modules/rtk-core/rtk-rewrite.js`, `tools/rtk_corpus.py`,
`tools/rtk_install.py`, `tools/rtk_savings_export.py`, `vault/knowledge_base/rtk_baseline.md`, 1000+
telemetry files under `vault/telemetry/rtk_*.jsonl` (Glob confirmed). User's own global CLAUDE.md
independently documents "Sovereign RTK Baseline (Token Proxy)" as an active PreToolUse rewriter.
Disposition: ALREADY_LIVE.
Measurable claim: source's "60–90%" — UNVERIFIED against upstream rtk-ai/rtk's own numbers; CPP's own `rtk_savings_export.py` is the real measurement instrument and should be consulted directly rather than re-deriving from this source.
Priority: P2 (nothing to build; note only).

### CIF-05 — Raw tool-output firewall ("stdout never enters model context by default")
Source lines: 405, 432–445 (Context Mode ~98% claimed savings + FTS5 sandbox), 14995–15029 (turn 9 restatement: "RAW TOOL OUTPUT NEVER ENTERS THE MODEL CONTEXT").
Kind: EXTERNAL_RESOURCE + MECHANISM.
Existing owner: plan row "Tool I/O firewall | EXTEND | RTK (live) + persisted raw artifact locator" —
RTK half is LIVE (see CIF-04); the "persisted raw artifact locator" half is **PLANNED (P5)**, not built.
Disposition: EXTEND_EXISTING_OWNER (half live, half planned; decision already made).
Measurable claim: Context Mode "~98% ahorro en determinados workflows" (line 405) — UNVERIFIED, source project's own claim, no CPP reproduction.
Priority: P1.

### CIF-06 — Lazy capability/tool-schema loading before injection
Source lines: 409–410 (mcp-context-proxy, mcp-gateway), 450–476 (MCP schema overhead ~1000 tokens/tool), 12985–13018 (bigtool-ts, "Capability Directory → Search → Materialize").
Kind: EXTERNAL_RESOURCE + MECHANISM.
Existing owner: `tools/jit_skill_loader.py` (confirmed present via Glob; referenced in the governing
plan as the mechanism already logging "JIT injection" chars/4 estimates, `jit_skill_loader.py:1153-1162`).
This is CPP's existing lazy-capability-materialization primitive, for Skills specifically. CPP has no
MCP servers of its own to gate (its tool surface is Claude Code's native tools + Skills), so the
literal "150 MCP schemas" problem the source describes does not exist here at the scale claimed.
Disposition: ALREADY_LIVE for the skill-loading analog; CONNECT (no new work) for MCP specifically since CPP is not exposing 150 MCP schemas.
Measurable claim: "decenas de miles de tokens" MCP overhead (line 452) — UNVERIFIED and inapplicable (CPP's MCP surface here is 4 failed servers + a handful of connected ones per the session's own MCP list, not "150 schemas").
Priority: P2.

### CIF-07 — Agent Memory as a cognitive memoization/cache layer (the dataset's largest cluster)
Source lines: 10062–12936 (turns 5 and 6 in full — ~30 named "memory" sub-types: Search, Symbol
Inspection, Repo Topology, Decision, Negative Decision, Tool Result, Test Evidence, Failure, Plan
Fragment, Verification, Agent Dispatch, Tool Routing, Context Recipe, Evidence Path, Assumption,
Runtime Environment, Resume, Agent-to-Agent, Skill, Meta-Memory, Semantic Result Cache, Derived Fact
Cache, Temporal Memory, Context Assembly/Delta Cache, Reasoning Artifact Cache, Negative Reasoning
Cache, Proof Memory, Tool Strategy Memory, Model Routing Memory), plus agentmemory (line 19),
Graphiti (424), Letta/MemGPT tiering (10310, 10808-10826), CoMem async curator (13740).
Kind: EXTERNAL_RESOURCE + MECHANISM (single mechanism repeated ~30 times with different nouns:
dependency-fingerprinted, freshness-scored result cache with invalidation).
Existing owner: plan row **"Memory reuse / negative cache | EXTEND | graphify writeback +
session_delta, with freshness fields"** — phase **P5, PLANNED**. HCMH (doctrine-only, see CIF-03) is
the conceptual parent that already names Memory Hit Utility / Memory Miss Cost / staleness /
eviction accuracy (`cognitive-resource-os-2026-09-27.md:19`).
Disposition: EXTEND_EXISTING_OWNER — this entire two-turn cluster is one decision already on the
books (PLANNED, not executed). No new candidate needed per sub-type; HR-NOVELTY-001 spirit says
build ONE dependency-aware cache primitive, not 30 named caches.
Measurable claim: agentmemory "~2000 token default budget" (line 237, self-reported benchmark) — explicitly flagged UNVERIFIED by the source itself; no CPP reproduction.
Priority: P0 (highest-value single mechanism in the whole dataset if it converts rediscovery into cache hits — but it is already decided, just not built; the work is EXECUTE P5, not decide).

### CIF-08 — Temporal/graph-structured knowledge dedup (canonical node, not N copies)
Source lines: 424 (Graphiti), 425 (A-MEM), 10895–10976 (Memory DAGs, Delta Memory, Letta Code
git-backed memory filesystem), 13985–14003 (knowledge-graph-as-dedup-layer).
Kind: EXTERNAL_RESOURCE + MECHANISM.
Existing owner: same as CIF-02 — `modules/graphify`, plan id `genesis-context-graph` EXTEND, PLANNED T2.
Disposition: EXTEND_EXISTING_OWNER (folds into CIF-02's owner; not a separate build).
Measurable claim: none.
Priority: P2.

### CIF-09 — Canonical agent trajectory IR / cross-harness trace normalization
Source lines: 426 (Letta trajectory), 4569–4600 (Canonical Agent Trajectory Dataset), 4591 (AgentRL trajectory-first design + cost_per_success metric).
Kind: EXTERNAL_RESOURCE + MECHANISM.
Existing owner: today's manifest id `genesis-routing-metrics` — "mission ledger + worker
transcripts... consumed by tools/gsd_epoch.py certify" — **status LIVE**, proof
`python tools/test_routing_metrics.py`, real ledger "448 attempts, 66 unjudged, 389
provider-refusal" (ASSIMILATION_MANIFEST.json:151-160).
Disposition: COVERED_BY_TODAY_ASSIMILATION.
Measurable claim: none from CIF; genesis-routing-metrics' own numbers are the CPP-side measurement.
Priority: P2 (already live).

### CIF-10 — Inference-level KV/prefix caching + speculative decoding
Source lines: 427 (LMCache), 13253 (vLLM Automatic Prefix Caching), 13280 (vllm-project/speculators), 16459 (vLLM adaptive speculative verification).
Kind: EXTERNAL_RESOURCE.
Existing owner: none — CPP runs entirely on the hosted Claude API (Sonnet/Opus/Haiku via Claude
Code), never self-hosts inference; Anthropic's own prompt caching already provides prefix/KV reuse
transparently server-side (visible in genesis-routing-metrics' own "cache reads 98% of observed
input on rotation epochs", manifest line 159).
Disposition: REJECT — cost>value; duplicates a capability the provider already supplies, and CPP has
no self-hosted inference layer to apply LMCache/speculative decoding to.
Measurable claim: n/a.
Priority: — (rejected).

### CIF-11 — Token/cost observability and per-artifact resource ledger
Source lines: 429 (Langfuse), 3196–3266 (Token Attribution Ledger), 16497–16528 (Resource Accounting multidimensional).
Kind: EXTERNAL_RESOURCE + MECHANISM.
Existing owner: `tools/tis.py`, `pp-tco-advisor`, `pp-token-auditor`, `tools/token_autopsy.py` (all
named in the governing plan). Plan row: "Resource ledger | EXTEND | tools/tis.py: add `observed`
source from transcript usage; relabel chars/4 as `estimate`" — phase **P1, PLANNED**.
Disposition: EXTEND_EXISTING_OWNER.
Measurable claim: plan's own measurement "first model call = 157,256 cache-creation tokens" (plan line 12) is the real CPP number, already gathered — no need to import Langfuse.
Priority: P1.

### CIF-12 — Context/instruction ablation harness (A/B, held-out, ContextRot-style)
Source lines: 421–422 (ContextRot, Chroma context-rot), 418–420 (ACON, ACM, ReSum), 14863–14899 (Instruction Ablation Testing).
Kind: EXTERNAL_RESOURCE + MECHANISM.
Existing owner: plan row "Instruction economics | NEW harness inside rule_compiler
(effect_harness/counterfactual exist) | ablation over frozen tasks" — phase **P3, PLANNED**.
`modules/rule_compiler/effect_harness.py` and `counterfactual.py` confirmed present (Glob). Separately,
today's manifest id `genesis-paired-experiments` — "preregistered hash-frozen comparisons, holdout
split" — **status LIVE**, real run `exp-successor-packet-002`, "4/4 vs 4/4... registered before 4
real headless successors" (manifest lines 216-224).
Disposition: COVERED_BY_TODAY_ASSIMILATION for the A/B harness mechanism (genesis-paired-experiments,
LIVE) + EXTEND_EXISTING_OWNER for the instruction-specific ablation (rule_compiler, PLANNED P3).
Measurable claim: none from CIF usable; genesis-paired-experiments' own "tokens +0.08%" result (manifest line 224) is the real measured number.
Priority: P1.

### CIF-13 — Agent Foundry: ephemeral agent synthesis, genome, lifecycle, merge/fission/retirement
Source lines: 2512–7065 (turn 3 in its entirety — Agent Genesis Engine, Agent Compiler, Mission IR,
Uncertainty Graph, Agent Spawn Gate, Cognitive Genome, Agent Darwinism/lineage, Agent
Merge/Fission/Retirement, "CPP-CEOS", "CPP Cognitive Capital Operating System"), plus ADAS,
AgentSquare, EvoAgentX, GEPA, HSI, Hydra, canvas-org/meta-agent, AgentBreeder, Group Evolving Agents
(scattered 3675–4880).
Kind: EXTERNAL_RESOURCE + MECHANISM cluster (a single proposal for a brand-new institutional
mega-system, by the source's own admission escalating five times within one turn: "Context
Intelligence Fabric" → "CPPCOS" → "Cognitive Resource Allocation & Learning Fabric" → "COCF" →
"CPP-CEOS" → "Autonomous Engineering Science & Cognitive Capital Fabric").
Existing owner: none found for the mega-system as proposed (searched `Agent Genome|Agent Foundry|Mission IR|Uncertainty Graph` across `modules/` `tools/` — no hits beyond the plan doc itself). Governing decision already made: plan row **"Agent foundry / gym / counterfactual | DEFER to shadow experiments | keos_qwen ledger + rule_compiler/counterfactual"**, under the explicit heading "Governing decision (HR-NOVELTY-001)... 0 new mega-systems."
Disposition: REJECT (rhetorical layer — this is the textbook case HR-NOVELTY-001 was written for: a
proposal that keeps renaming itself upward without a discovered-denominator gap check; the Owner's
own prior audit already ruled DEFER on this exact cluster one day before this dataset).
Measurable claim: AgentFactory "57% reduction in orchestration tokens vs ReAct" (line 2520) — UNVERIFIED, self-reported by an external ACL 2026 paper, never reproduced in CPP.
Priority: — (rejected; would need the 13-question novelty proof per HR-NOVELTY-001 before reopening).

### CIF-14 — Evidence/verification epistemic plane (proof-carrying claims, stale-evidence degradation)
Source lines: 1489–1510 (AET, backcheck, 2119, SWE-Mutation, ecodex table), 1518–1616 (evidence
valid-only-for-exact-world-state law; Completion Claim Verifier), 1618–1655 (2119 requirement→proof
binding), 5420–5450 (Proof-carrying agent outputs).
Kind: EXTERNAL_RESOURCE + MECHANISM.
Existing owner: today's manifest — `genesis-task-ledger` (artifact sha256 binding + reviewer!=worker,
MERGED into `modules/gsd_x/goal/convergence.py`, **status PLANNED** pending UWCP S6 liveness) +
`genesis-evidence-collector` (`tools/evidence_bundle.py`, **status LIVE**, found and fixed a real
"HIGH false green" per its own evidence field) + `genesis-regression-memory`
(`tools/regression_memory.py`, **status LIVE**, "reopen when bytes move"). Also `output_contracts`
(user's own doctrine file references OQS gates already enforcing evidence-backed DONE claims).
Disposition: COVERED_BY_TODAY_ASSIMILATION (strong match — the exact "claim must be bound to exact
world state" law CIF proposes is already implemented and live in genesis-evidence-collector /
genesis-regression-memory).
Measurable claim: none reliable from CIF (AET/backcheck/2119 are unreleased or unverified GitHub projects per the source's own hedging language "no voy a inventar su comportamiento").
Priority: P2 (already covered).

### CIF-15 — Mine successful trajectories into regression tests
Source lines: 2131–2166 (agent-trace-to-evals: "successful sessions → mine invariants → candidate regression test").
Kind: EXTERNAL_RESOURCE.
Existing owner: `tools/regression_memory.py` (genesis-regression-memory, LIVE) already converts
V-gate failures into committed regressions with reopen-on-byte-move semantics; this is the sibling
capability (mine successes rather than failures) and is not built.
Disposition: EXTEND_EXISTING_OWNER (regression_memory.py) — small, well-scoped gap.
Measurable claim: source itself flags "sólo ha probado su pipeline sobre corpus sintético" (line 2142) — UNVERIFIED.
Priority: P2.

### CIF-16 — Retrieval stack: HippoRAG / ColBERT / GraphRAG / RAGChecker / RAGLAB / FlashRAG / Mem0 benchmarks
Source lines: 640, 649–651, 657–661 (turn 2 table), repeated 10914–10915 (Graphiti/graph memory), 13317 (Chisel).
Kind: EXTERNAL_RESOURCE cluster.
Existing owner: none — CPP has no vector-embedding/dense-retrieval stack; its retrieval primitives
are grep/Glob, `tools/audit_cache.py` (file-level dependency graph), and FTS5 full-text search
(`vault_search.py`, `cpp-resume-sovereign` skill — "Sovereign History Vault (46k+ records)... FTS5 +
dedup picker", confirmed in the skill's own description). Searched: `HippoRAG|ColBERT|GraphRAG|embed` across `modules/` `tools/` — no hits.
Disposition: REJECT — cost>value. No CPP corpus currently needs multi-hop associative retrieval over
embeddings; FTS5 already serves the measured use case (session/knowledge recall), and building a
second retrieval stack duplicates it without a demonstrated gap.
Measurable claim: none carried over (all are external benchmark papers, none reproduced against CPP data).
Priority: — (rejected).

### CIF-17 — LLM-as-Verifier / Best-of-N tournament / adversarial verifier compute
Source lines: 1881–1940 (LLM-as-a-Verifier, Probabilistic Pivot Tournament, prefix-cache optimization), 5452–5560 (Verifier Compiler).
Kind: EXTERNAL_RESOURCE.
Existing owner: none dedicated; folds into the same Agent Foundry/Gym cluster the plan already DEFERs (CIF-13).
Disposition: REJECT (same governing decision as CIF-13; no standalone gap that survives the DEFER ruling).
Measurable claim: "cache hit 5.2%→78.4%, ~3.4× less uncached input" (line 1889) — UNVERIFIED, external project's own optimization, unrelated to Claude API usage.
Priority: — (rejected).

### CIF-18 — Multi-agent-to-skill distillation cost model (coordination tax)
Source lines: 13360–13416 (AdaSkill, Trace2Skill), 12965–12966 ("dispatch innecesario → learned topology selection"), 3401–3419 (turn 3's own version).
Kind: EXTERNAL_RESOURCE.
Existing owner: `compound-learnings` skill — confirmed live in the available-skills listing:
"Transform ephemeral session learnings into permanent, compounding capabilities... signal thresholds
(1=skip, 2=consider, 3+=strong, 4+=create), categorizes via decision tree
(sequence-then-SKILL, automatic-then-HOOK, when-X-do-Y-then-RULE, agent-fit-then-AGENT-UPDATE),
and materializes approved artifacts." This is trajectory→skill distillation with a recurrence gate,
already built, gated behind `/cpp-compound` (sleepy, human/driver-invoked, never autorun).
Disposition: ALREADY_LIVE (compound-learnings skill) for the trajectory→skill mechanism itself; the
narrower "coordination-tax accounting for WHEN to distill a multi-agent team into one" is not
separately built, but is a small delta on an existing owner.
Measurable claim: AdaSkill "fuertes reducciones de coste en sus propios benchmarks" (line 13390) — UNVERIFIED.
Priority: P2.

### CIF-19 — Skill/instruction ROI accounting and lifecycle-to-enforcement compilation
Source lines: 13421–13519 (SkillLens, Instruction Cost Accounting, "Prompt debt → infrastructure"), 6367–6430 (turn 3's "Instruction Debt" / cognitive compilation ladder), 14816–14930 (turn 8's Instruction Utility Analyzer / Instruction Ablation Testing).
Kind: EXTERNAL_RESOURCE + MECHANISM.
Existing owner: same plan row as CIF-12 — "Instruction economics | NEW harness inside rule_compiler
(effect_harness/counterfactual exist)", phase P3, PLANNED. This is the single owner for the whole
"which rules are worth their recurring token tax" family across all four turns that raise it.
Disposition: EXTEND_EXISTING_OWNER (already decided).
Measurable claim: none usable.
Priority: P1 (merges four separate re-statements into one already-decided build item).

### CIF-20 — Model/route selection: cost-per-verified-success, learned online routing
Source lines: 632–636 (Agent Lightning, GEPA), 2976–3031 (routing memory), 13206–13240 (turn 7),
15810 (llm-token-router), 15904 (ParetoBandit), 16022 (NESTRA), 16160 (BudgetMem).
Kind: EXTERNAL_RESOURCE cluster.
Existing owner: plan row "Model routing | MERGE 7→1 | modules/cost_collapse/router.py canonical;
refresh ids; others delegate; shadow first" — phase **P6, PLANNED**. Today's manifest also has
`genesis-worker-router` MERGED into `tools/gsd_mission.py` provider circuit breaker +
`modules/cost_collapse` routing, **status LIVE** for the circuit-breaker half.
Disposition: EXTEND_EXISTING_OWNER / partially COVERED_BY_TODAY_ASSIMILATION (breaker half LIVE, full merge-7-routers-into-1 PLANNED).
Measurable claim: Agent Lightning "41.8%→56.4% SWE-bench Verified with Qwen3.5-9B" (line 632) — UNVERIFIED, unrelated model family to CPP's Claude-only routing.
Priority: P1.

### CIF-21 — Interactive-session context rollover (kclear → clear → kresume transaction)
Source lines: 7066–10061 (turns 4/5: two-phase cognitive commit, Safe-to-Forget Gate, rollover
ledger, reality-refresh reconciliation, exact-once continuation, fencing).
Kind: MECHANISM.
Existing owner: **ALREADY LIVE.** `vault/specs/interactive-context-rollover.md` (read in full):
status "ACTIVE LIVE, ON by default (37a3144 reset gate, 42da3d1 crossing... 2026-09-28)". Gates:
`test_rollover` 48/48, `test_rollover_active_path` 10/10, `test_gsd_long_run` 100/100, 4/4 mutants.
Implements almost exactly what CIF proposes: state machine `CANDIDATE -> CAPSULE_SEALED (sha256 +
read-back) -> SAFE_TO_FORGET | REFUSED(reasons)` then `RESET_REQUESTED -> SUCCESSOR_CLAIMED ->
REALITY_REFRESHED -> RESUME_CERTIFIED | RESUME_FAILED`; the gate is "consulted immediately before the
destructive step, never at the wall a turn earlier — that would authorise forgetting whatever
happened in between" (spec §7) — this is CIF's own "PREPARE-TO-FORGET / COMMIT-FORGET" two-phase
commit, already built.
Disposition: ALREADY_LIVE.
Measurable claim: none from CIF; spec's own §8 records "a real fresh-session crossing... is OWED, not claimed" — the one remaining gap, already tracked by the owning spec, not new.
Priority: — (nothing to add; flagged so the Owner knows this exact recommendation predates and matches production).

### CIF-22 — Durable mission/epoch runtime (event log, OTP supervision, fencing, process-tree lease)
Source lines: 8150–10060 (turn 5 continuation — Mission Event Log, two-phase cognitive commit for
epochs, OTP/Erlang supervision tree analogy, failure-taxonomy→restart-strategy, fencing tokens,
Active Writer Lease, Temporal/DBOS references).
Kind: EXTERNAL_RESOURCE (Temporal, DBOS, Erlang/OTP) + MECHANISM.
Existing owner: plan rows "Durable execution | EXTEND | gsd_mission.py: H1 progress, H3 freshness on
arm, H4 resume exam, H9, H10 retire v2 sweep" + "Write fencing | CONNECT | modules/lease/store.py
(fenced, unused) → mission epoch; checked at commit" + "Convergence | CONNECT (shadow) |
gsd_x/goal/judge consulted beside ALL_COMPLETE" — phase **P4, PLANNED**. `modules/lease/store.py`
confirmed present (Glob). This is the epoch/mission-level sibling of CIF-21 (which is the
interactive-pane-level piece and is already live); the spec I read explicitly separates them:
"Interactive-pane rotation is a SEPARATE brief... P3 here is exactly that brief"
(interactive-context-rollover.md:22-23, quoting the epoch spec).
Disposition: EXTEND_EXISTING_OWNER (already decided; PLANNED not built).
Measurable claim: none from CIF (Temporal/DBOS mechanisms cited as inspiration, not reproduced).
Priority: P0 (largest remaining concrete gap in the whole dataset with a named owner and a decision already made — just not executed).

### CIF-23 — Side-effect/idempotency ledger for tool mutations (ACTION_INTENT → COMMITTED)
Source lines: 8625–8746 (Idempotency/Side-Effect Ledger, Mutation ID, tool recovery-semantics contract).
Kind: MECHANISM.
Existing owner: the governing plan lists, under "Documented-not-executed": **"...side_effect_ledger,
modules/lease"** (`cognitive-resource-os-2026-09-27.md:21`) — i.e. CPP already has a module literally
named for this exact concept, on disk, unwired.
Disposition: EXTEND_EXISTING_OWNER (documented-not-executed primitive; matches CIF's proposal almost
by name).
Measurable claim: none.
Priority: P1 (name-matched existing module, cheap to connect once P4 durable-execution work starts).

### CIF-24 — Representation compiler (canonical JSON/relational → compact LLM projection / IR)
Source lines: 524–544 (jCodeMunch "~46% smaller than JSON", TOON), 13524–13591 (Representation Compiler, Agent ABI / structured IR between agents), 14935–14990 (Agent Communication ABI).
Kind: EXTERNAL_RESOURCE + MECHANISM.
Existing owner: none dedicated found (searched `TOON|wire format|LLM projection` across `tools/` `modules/` — no hits); closest neighbor is RTK (CIF-04, ALREADY_LIVE), which compresses command *output*, not inter-agent/tool-result payloads generally.
Disposition: CONNECT — fold into RTK's existing mandate rather than building a new "IR" system; no
stated gap large enough to justify a NEW module per HR-NOVELTY-001 (the source's own numbers are
unverified and the effect substantially overlaps CIF-05/CIF-07's dependency-aware result cache,
which already returns compact capsules instead of raw payloads by construction).
Measurable claim: jCodeMunch "~46% reducción media en bytes sobre JSON" (line 526) — UNVERIFIED.
Priority: P2.

### CIF-25 — Embedded "95% Token Reduction — Operating Doctrine" document (found, not a GitHub repo)
Source lines: 14220–14546 (the full embedded doctrine text: quality floor, reference-over-inline,
output discipline, routing-before-reasoning, memory hygiene, delta protocols, honest token
accounting, three-tier router binding).
Kind: MECHANISM (a complete, portable, self-contained operational doctrine, not a repo link).
**Notable finding:** `vault/plans/cognitive-resource-os-2026-09-27.md:22` records: *"95-token-reduction
doc: NOT FOUND in Downloads (home-wide search timed out → unlocated, not absent)."* That document is
this exact text, embedded inside this CIF dataset file, one folder over from where the prior session
searched. This closes a standing gap in the plan of record.
Existing owner: `tools/tco_compact_gate.py`, `modules/cost_collapse/`, RTK doctrine
(`vault/knowledge_base/rtk_baseline.md`) — the doctrine's "quality floor / two invariants override
everything / honest token accounting (compression vs permanent-memory-growth vs doctrine-install,
never netted)" sections are directly implementable rules for these existing owners; nothing here
requires a new module.
Disposition: EXTEND_EXISTING_OWNER, but flagged **P0 procedurally** — the Owner should be told this
document was located, independent of whether its content is adopted, because the prior plan spent
effort searching for it and came up empty.
Measurable claim: "~93–95% combined (router + doctrine)... doctrine alone saves single-digit percent" (lines 14226-14235) — UNVERIFIED, and the document is explicit that the headline number depends on a three-tier local/cheap/premium router CPP does not have (CPP is Claude-only, no local/cheap tier).
Priority: P0 (the finding itself, independent of adoption decision).

### CIF-26 — Baseline/institutional promotion ratchet (held-out validation before any capability ships)
Source lines: 6186–6335 (Replication before constitutional promotion, minimum recurrence, held-out gates), 15505–15544 ("Universal Construction Ratchet"), 17643–17654 (final "UCR-CIF Ratchet Gate").
Kind: MECHANISM.
Existing owner: plan row "Baseline ratchet | EXTEND | modules/tower (CBR slice) receives certified
items only" — phase **P8, PLANNED**. This is CPP's own pre-existing ratchet doctrine (mutation
ratchet ledger, HR-NOVELTY-001 itself is an instance of this pattern); the source's proposal adds
nothing beyond what CPP's HARD RULES doctrine (HR-ONESHOT-002/003, mutation_ratchet.json) already
states.
Disposition: EXTEND_EXISTING_OWNER (already decided; PLANNED).
Measurable claim: none.
Priority: P2.

---

## Summary

### Counts per disposition (26 candidates, cap 60 — not reached; source content over-clusters into
far fewer distinct mechanisms than its ~150 individual GitHub links suggest)

| Disposition | Candidates |
|---|---|
| ALREADY_LIVE | CIF-04 (RTK), CIF-21 (interactive rollover), CIF-18 (compound-learnings, partial), CIF-06 (jit_skill_loader, partial) |
| COVERED_BY_TODAY_ASSIMILATION | CIF-09, CIF-14, CIF-12 (partial, genesis-paired-experiments), CIF-20 (partial, genesis-worker-router) |
| EXTEND_EXISTING_OWNER | CIF-01, 02, 03, 05, 07, 08, 11, 12 (partial), 15, 18 (partial), 19, 20 (partial), 22, 23, 25, 26 |
| CONNECT | CIF-06 (MCP-specific half), CIF-24 |
| REJECT | CIF-10, CIF-13, CIF-16, CIF-17 |

(Several candidates split cleanly into a live/covered half and a planned half and so appear under
two rows; 26 candidate IDs total, zero left unclassified.)

### Top 8 candidates, ranked by (token-saving potential x build readiness), one line each

1. **CIF-07** — Agent Memory as a dependency-aware memoization cache: the dataset's single largest
   cluster (turns 5+6, ~2900 lines), already decided (EXTEND graphify, PLANNED P5) but unbuilt — the
   highest expected payoff in the whole dataset once executed.
2. **CIF-22** — Durable mission/epoch runtime (event log, fencing, OTP-style supervision): largest
   concrete engineering gap with a named owner and an already-approved-pending-execution decision
   (gsd_mission.py H1/H3/H4/H9/H10, modules/lease).
3. **CIF-25** — The embedded "95% Token Reduction" doctrine document: closes a standing "NOT FOUND"
   search gap from the prior plan; procedurally P0 regardless of adoption.
4. **CIF-21** — Interactive context rollover: already fully live in production
   (interactive-context-rollover.md), confirms CIF turns 4/5 correctly anticipated CPP's actual build.
5. **CIF-05** — Raw tool-output firewall: RTK half live, persisted-locator half planned; closes the
   "80k-token pytest dump enters context" leak.
6. **CIF-19 / CIF-12** — Instruction/context ablation economics via rule_compiler (effect_harness +
   counterfactual already exist): converts four separate turns' worth of "which rules earn their
   tokens" proposals into one already-scoped P3 build.
7. **CIF-14** — Evidence/verification epistemic plane: already live today via
   genesis-evidence-collector and genesis-regression-memory, which caught a real false-green bug
   during their own build — stronger evidence than anything CIF cites.
8. **CIF-20** — Model routing merge (7 routers to 1, modules/cost_collapse/router.py): partial
   (circuit breaker live), full merge planned P6.

### Source sections not fully decomposed into individual candidates (by design, not omission)

- **Turn 3 (lines 2512-7065, ~4,550 lines)** — the Agent Foundry/Genesis/Evolution mega-cluster —
  deliberately compressed to one candidate (CIF-13, REJECT) rather than the ~60 sub-ideas it
  contains (Agent Genome, Mission IR, Uncertainty Graph, Verifier Compiler, Counterfactual Lab,
  Cognitive A/B testing, process rewards, hidden holdouts, agent merge/fission, SEED, GEPA, ADAS,
  AgentSquare, EvoAgentX, HSI, Hydra, AgentBreeder, Group Evolving Agents, etc.) because the Owner's
  own prior audit (cognitive-resource-os-2026-09-27.md, one day older) already applied
  HR-NOVELTY-001 to this exact territory and ruled DEFER. Decomposing it further would have produced
  ~50 more REJECT rows citing the same one governing decision.
- **Turn 9 (lines 14547-17681, ~3,100 lines, "CROS" elaboration)** — read in full; contains no
  resource or mechanism not already covered by CIF-07/11/19/20/22/26 (it is the same "Cognitive
  Resource Operating System" proposal, restated with OS-scheduler vocabulary: work-stealing,
  backpressure, priority inheritance, anytime execution, invalidation graphs, three control loops).
  No new candidate rows were warranted; flagged here so the Owner knows it was read, not skipped.
- Every individual GitHub URL inside turns 1-2's tables (~50 repos) was mapped to a cluster
  candidate above rather than given its own row, per the task's merge-near-duplicates instruction.

### Correction to the task's stated source size
The source file is **17,681 lines**, not ~15,600 — the brief's line estimate undercounted by about
2,000 lines (all of turn 9, the "CROS" elaboration). This was discovered mid-read (offset 19000
returned a length error) and the read continued to the true end; nothing was skipped.

