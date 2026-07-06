# Securing, Red-Teaming, and Governing Autonomous Agentic AI: A Synthesis of Defense, Adversarial Testing, and Production Deployment

## Executive Summary

The research corpus converges on a single, load-bearing thesis: **the bottleneck for safe autonomous agentic AI is not model capability but the governance, verification, and architectural scaffolding that surrounds the model.** Failed agentic initiatives almost never fail because "the AI couldn't do it" — they fail because organizations could not govern autonomy: agents were over-permissioned, weakly tested, and inadequately monitored relative to a risk profile that shifts faster than human review cycles can track.

Three threads run through every source:

1. **Defense-in-depth is mandatory.** No single control (not safety training, not a filter, not a policy engine) is sufficient. Microsoft, IBM, and OWASP independently arrive at layered architectures spanning the model, the safety system, the application, and organizational positioning.
2. **Adversarial testing is non-negotiable and asymmetric.** Safety training *reduces but never eliminates* vulnerability. The highest-impact attacks live at the **application boundary** (indirect/cross-prompt injection, tool abuse, RAG poisoning) — precisely the surface that base-model evaluation misses. Multi-turn attacks (Crescendo) materially outperform single-turn jailbreaks, and current tooling is still weaker on multi-turn than single-turn.
3. **Determinism is the reliability multiplier.** The most successful production deployments (Stripe, Anthropic, Shopify, Airbnb) systematically move consequential, infrastructure-touching actions *out* of LLM/tool reasoning and *into* deterministic orchestration code — "the system controls the agent, not the other way around."

This report synthesizes the defensive frameworks, the offensive (red-team) tooling and benchmarks, the governance failure modes, and the production-architecture patterns that reconcile autonomy with reliability.

---

## Part I — Defensive Architecture: Layered Hardening

### 1. Microsoft's Four-Layer Defense-in-Depth Pattern

Microsoft frames secure agentic AI as four mitigation layers, each with distinct controls and a distinct product surface:

| Layer | Purpose | Key Controls |
|---|---|---|
| **Model** | Reduce intrinsic and supply-chain risk | Intentional model selection; supply-chain governance; red teaming via **PyRIT** and the **AI Red Teaming Agent** |
| **Safety System** | Catch what the model lets through | Input/output filtering for prompt injection; agent guardrails; observability; anomaly detection |
| **Application** | Constrain what the agent *can do* | Agents as **microservices with isolated permissions**; **explicit action schemas**; deterministic human-in-the-loop enforced via **orchestrator logic, NOT model reasoning**; least-privilege / least-action with **unique, verifiable agent identities** for RBAC |
| **Positioning** | Manage human-facing trust | Clear AI disclosure; capability transparency |

The single most important architectural commitment in this model: **human-in-the-loop must be enforced by deterministic orchestrator logic, never by asking the model to decide when to pause.** A model can be talked out of pausing; an orchestrator cannot.

**Operationalization stack:** Microsoft Agent 365, Microsoft Entra (identity), Microsoft Purview (data governance), Microsoft Foundry, Microsoft Defender, and Microsoft Sentinel (detection/response).

### 2. IBM BeeAI — Progressive Agent Hardening

IBM's BeeAI framework tutorial demonstrates a "never trust, always verify" (zero-trust) posture realized through concrete, copyable controls within an **Agent Development Lifecycle (ADLC)** that embeds security from threat modeling through monitoring:

- **Local LLM execution** via Ollama (e.g., `ollama:granite:micro`) to shrink the supply-chain and data-leakage surface — the model and data never leave the trust boundary.
- **Bounded memory:** `TokenMemory` buffers capped at **~20k tokens** to enforce a *predictable data lifecycle* and prevent unbounded retention of API keys / PII.
- **Per-invocation tool authorization:** every tool (`ThinkTool`, `OpenMeteoTool`, `DuckDuckGoSearchTool`) wrapped in a `PermissionManager` requiring **explicit approval per call** — not a blanket grant.
- **Audit by default:** an `AuditLogger` writes every decision to `agent_audit.log`.

The BeeAI pattern is the small-scale, inspectable counterpart to Microsoft's enterprise stack: same principles (least privilege, bounded data lifecycle, audit, zero-trust), different blast radius.

### 3. Policy-as-Code Enforcement

Policy-as-code makes governance executable and version-controlled rather than aspirational:

- **Policy Enforcement Points (PEP)** intercept agent actions *before execution* and validate them against a policy engine.
- **Centralized engines:** Azure Policy, Aria Policy, **Open Policy Agent (OPA)**.
- **Distributed local validators** provide connectivity resilience (the agent can still enforce policy when the central engine is unreachable).
- **OPA specifics:** uses the **Rego** language with a **default-deny (`default ... = false`)** posture, queried via REST at `localhost:8181`, decoupled from application code and version-controlled.

**Framing and maturity context:**
- **McKinsey Technology Insights (July 2025)** framed guardrails explicitly as *balancing autonomy with enterprise security* — the trade-off is the design problem, not a side concern.
- **Microsoft's maturity model** spans **Level 100 (Initial — "Shadow AI proliferation")** to **Level 500 (Efficient — "Innovation stagnation")**. Two cautions stand out: (a) do **not treat all agents identically** — *tier by risk*; (b) adopt the **NIST AI Risk Management Framework** as a baseline.

The Microsoft maturity endpoints are notable: both extremes are pathological. Level 100's "shadow AI proliferation" is ungoverned sprawl; Level 500's "innovation stagnation" is governance so heavy it kills velocity. The target is a tiered middle.

---

## Part II — Offensive Testing: Red-Teaming Frameworks and Benchmarks

### 4. PyRIT — Python Risk Identification Toolkit

PyRIT is Microsoft's open-source (MIT-licensed) red-teaming framework — the offensive complement to the defensive stack above.

| Attribute | Detail |
|---|---|
| **Origin** | Created by **Gary Lopez** and the Microsoft AI Red Team; evolved from one-off scripts begun in **2022** |
| **Repository** | `github.com/Azure/PyRIT` |
| **Traction (by 2024-07-01)** | **1.5k GitHub stars, 266 forks** |
| **Operational use** | **100+ red-teaming operations**, including Copilot systems and the **Phi-3** model release |
| **External partnership** | **Stanford** collaboration added the **GCG suffix attack** and **Tree of Attacks with Pruning (TAP)** |

**Architecture — 5–6 composable components:**

| Component | Role / Examples |
|---|---|
| **Targets** | The systems under test |
| **Converters (50+)** | Payload transforms: Base64, ROT13, leetspeak, **Unicode homoglyphs**, translation |
| **Scorers** | `SelfAskTrueFalseScorer`, `SelfAskLikertScorer`, `AzureContentFilterScorer`, `SubStringScorer`, `HumanInTheLoopScorer` |
| **Datasets** | Attack seed corpora |
| **Orchestrators / Attack Strategies** | Compose targets + converters + scorers into campaigns |
| **Memory** | Persistence via DuckDB / SQLite / Azure SQL |

The converter library is the practical heart: the same harmful intent re-expressed through Base64, homoglyphs, or translation routinely bypasses naive filters, which is exactly why output filtering alone (Layer 2) is insufficient without the other three layers.

### 5. The Crescendo Multi-Turn Attack and ASR Benchmarks

Microsoft research on the **Crescendo** attack — *gradual benign-to-adversarial escalation with backtracking* — quantifies why single-turn testing under-measures real risk:

- Crescendo achieves **29–61% higher attack success rates (ASR) on GPT-4** versus direct (single-turn) jailbreaking.

Published **2024–2025 ASR benchmarks** show the defense gradient — and, crucially, that defenses *attenuate but never zero out* the attack surface:

| Attack Class | Base Model ASR | Safety-Trained ASR | Advanced Defenses ASR |
|---|---|---|---|
| **Jailbreaking** | ~90% | ~20–40% | ~5–15% |
| **Prompt Injection** | ~95% | ~30–50% | ~10–20% |

Two takeaways:
1. **Prompt injection is consistently harder to defend than jailbreaking** at every defense tier — and it is the agent-relevant attack, because agents ingest untrusted external content.
2. Even with advanced defenses, **a 10–20% prompt-injection success rate is the residual** — which is why the application layer (least privilege, action schemas, deterministic HITL) must assume the safety system *will* be bypassed some fraction of the time.

### 6. The Application-Boundary Consensus and the Tooling Stack

Practitioner consensus (r/netsec, r/MachineLearning, r/cybersecurity) and the **OWASP Top 10 for LLM Applications** agree that the highest-impact vulnerabilities are **not in the base model** but at the **application boundary**:

- **Indirect / cross-prompt injection** via untrusted inputs
- **Tool abuse**
- **RAG poisoning**

Critically, **agent-specific tool-use/agentic attacks are a surface that base-model testing structurally misses** — you cannot find them by evaluating the model in isolation.

**Tooling and its limits:**

| Tool / Benchmark | Notes |
|---|---|
| **PyRIT** | Microsoft, composable (see §4) |
| **NVIDIA Garak** | LLM vulnerability scanner |
| **HarmBench** | **200 standard + 110 contextual** behaviors |

Known weaknesses of the current state of the art:
- Frameworks remain **stronger on single-turn than multi-turn** — i.e., they are weakest exactly where Crescendo is strongest.
- **LLM-as-judge** attack-success evaluation has **documented reliability issues**, forcing **expensive human review**.

**The working stack** that the consensus endorses: **PyRIT + HarmBench + targeted manual testing, integrated into CI/CD (pytest)** — automated coverage for breadth, human red-teaming for the multi-turn and contextual tail that automation can't yet judge reliably.

---

## Part III — Governance: Autonomy as an Organizational Risk

### 7. Authorization Risk Is a Governance Failure, Not a Technology Failure

This is the corpus's central governance claim, and it is empirically grounded:

- **Deloitte: only 11% of firms have operationalized agentic AI.**
- Post-mortems on failed initiatives "consistently conclude **the technology worked but the organization couldn't govern autonomy**."

The recurring failure pattern:
- **Over-permissioned agents** — formalized as **OWASP LLM06:2025 "Excessive Agency."**
- **Weak testing.**
- **"Exception hell."**

**The prescribed mitigations form a governance checklist:**

| Mitigation | Mechanism |
|---|---|
| **Least-privilege / bare-minimum access scoping** | Directly counters Excessive Agency |
| **Code-level hard controls** | Hard limits on actions / tool-use / **spend**; **kill switches**; rollback; escalation paths / human approvals |
| **CRO-signed Agentic Workflow Risk Assessment** | Executive accountability before deployment |
| **Adversarial red-teaming before scale** | Find failures before exposure widens |
| **Continuous near-real-time monitoring** | Because **autonomous agents change their risk profile faster than human review cycles** |

The last point is the structural justification for everything else: when an autonomous agent can alter its own behavioral risk between two human review windows, periodic human review is definitionally insufficient — monitoring must be continuous and limits must be coded, not reviewed.

### 8. The Five-Level Agentic Coding Framework and Production Failure

Production deployment risk scales with **autonomy level**. The five-level framework:

| Level | Name | Description |
|---|---|---|
| 1 | **Autocomplete** | Inline suggestions |
| 2 | **Chat-assisted** | Conversational help |
| 3 | **Agentic** | Agent executes multi-step tasks |
| 4 | **Harness-driven** | Agent operates inside a structured harness |
| 5 | **Dark factory** | Ships merged/deployed code with **no human review** |

**Recommended posture for 2026:** most teams should operate at **Level 3–4**. **Level 5** ("dark factory") is reserved for **narrow, well-verified tasks only**.

**Why AI-generated apps fail in production:** *autonomy outruns automated verification.* The prerequisites for safely operating at Level 5 are therefore all *verification* prerequisites, not capability prerequisites:
- High test coverage
- Strong CI
- Observable outputs **with rollback**
- **Progressive (incrementally expanded) agent permissions** — start narrow, widen only as evidence accumulates

This dovetails exactly with the governance checklist (§7): kill switches, rollback, and progressive permissions are the same controls, viewed from the engineering side.

---

## Part IV — Production Architecture: Determinism as the Reliability Multiplier

### 9. Move Consequential Actions Out of the Model

An arXiv production-grade agentic workflow guide (**2512.08769**) gives the sharpest architectural prescription in the corpus:

> Move infrastructure-oriented actions — **GitHub PR creation, API posts, DB writes** — **OUT of LLM tool/MCP calls and INTO deterministic pure functions in the orchestration layer.**

**Rationale:** MCP and tool calls introduced **ambiguous tool-selection, inconsistent parameters, and non-reproducible failures.** Combined with two complementary disciplines:
- **"One agent, one tool"**
- **Single-responsibility design**

…this eliminates missed and misordered tool calls.

**Adoption is already heavy, not theoretical:**
- AI generates **the majority of pull requests at Anthropic**.
- Stripe's Minions harness reportedly produces **over 1,300 AI-generated PRs per week** inside gated review constraints.

### 10. Case Study — Stripe's "Minions"

Stripe's internal coding agents are the corpus's flagship production example of disciplined autonomy at scale:

| Metric | Value |
|---|---|
| **Merged AI-authored PRs / week** | **~1,300** (zero human-written code; **100% human-reviewed**) — roughly **185/day** |
| **Org context** | ~3,400 engineers filing **~8,000 PRs/week** total |
| **LLM-tool daily users** | **~8,500 employees** (65–70% of engineers) |
| **Foundation** | Heavily modified fork of **Block's open-source Goose** agent (forked late 2024, stripped of interactive features) |
| **Invocation** | Slack / CLI / web |
| **Execution environment** | Disposable AWS EC2 **"devboxes"** that **warm-start in ~10 seconds** |
| **Business impact** | Pan-EU local payment-method integration dropped from **~2 months to ~2 weeks** |
| **Leadership** | **Emily Glassberg Sands**, Head of Data & AI |

Note the precise autonomy posture: Minions are **fully unattended in authorship but 100% human-reviewed in merge** — i.e., **Level 4, not Level 5.** The dark factory remains gated even at Stripe's scale.

### 11. The "Blueprint" Orchestration Engine

The core architecture is a **"Blueprint"** orchestration engine: workflow templates that **alternate deterministic nodes with agentic LLM nodes.**

| Node Type | Examples | Property |
|---|---|---|
| **Deterministic** | Linting, test execution, file parsing, PR templating | **Same output every time** |
| **Agentic (LLM)** | Task understanding, code generation, error interpretation | Probabilistic |

The governing principle: **"the system controls the agent, not the other way around."**

**The reliability math that justifies determinism:** a 5-step chain at **95% per-step accuracy** yields only **~77% end-to-end** (0.95⁵ ≈ 0.774). Deterministic guardrails **recover the reliability that pure LLM chains erode** — every deterministic node is a step pinned to 100%, so it doesn't compound the decay.

**Hard limits in the feedback loop** (anti-runaway controls, echoing the §7 governance checklist):
- Local lint **< 5s** (precomputed/cached rules)
- **Selective CI** drawn from a **3M+ test suite**
- **Maximum of 2 CI retry rounds** before escalating to a human — preventing infinite loops and cost spirals

### 12. Context Curation as the Competitive Edge

Stripe treats **context curation — not model choice — as the unlock.**

- An internal MCP server, **"Toolshed,"** hosts **~500 tools** (Sourcegraph code search, doc/ticket retrieval, build status).
- A **deterministic node selects only the relevant subset per agent** — **selection happens in code, not by the agent.**
- **Directory-scoped "rule files"** (analogous to `CLAUDE.md` / Cursor rules) are **loaded conditionally**, not globally.

**Why this is the edge:** Stripe's stack — **hundreds of millions of lines of Ruby with Sorbet typing**, plus proprietary libraries — is **unfamiliar to LLMs.** The proprietary curation infrastructure, not the frontier model, is what makes agents productive on an unfamiliar codebase.

**Peers run parallel structured engines**, confirming this is an industry pattern rather than a Stripe idiosyncrasy:

| Company | Asset |
|---|---|
| **Shopify** | Open-sourced **"Roast"** |
| **Airbnb** | Internal **test-migration tool** |
| **AWS** | Partially disclosed one |

The deterministic-selection insight ties back to the §9 thesis: even *tool selection* — ostensibly a reasoning task — is pulled out of the model and into code wherever reproducibility matters.

---

## Part V — Cross-Cutting Synthesis

### Where the Threads Converge

| Principle | Defensive (MS/IBM/OPA) | Offensive (PyRIT/OWASP) | Governance (Deloitte/OWASP06) | Production (Stripe/arXiv) |
|---|---|---|---|---|
| **Least privilege** | Isolated-permission microservices; per-call tool auth | Excessive Agency is the top finding | Bare-minimum scoping; progressive permissions | One agent, one tool |
| **Determinism over model trust** | HITL via orchestrator, not model | — | Coded hard limits, not reviewed limits | Blueprint deterministic nodes; selection in code |
| **Assume bypass** | Defense-in-depth; output filtering | Residual 10–20% injection ASR | Continuous monitoring; kill switches | 100% human review at merge (Level 4) |
| **Bounded lifecycle** | 20k-token memory cap; audit logs | Memory persistence for forensics | Spend caps; CI retry cap (2 rounds) | 10s disposable devboxes; <5s lint |
| **Verification gates autonomy** | ADLC; red teaming pre-release | PyRIT+HarmBench+manual in CI/CD | Red-team before scale; CRO sign-off | High coverage + CI prerequisites for Level 5 |

### The Operating Model That Emerges

1. **Tier agents by risk** (Microsoft maturity model; NIST AI RMF baseline) — never treat all agents identically.
2. **Wrap every consequential action in deterministic code** (orchestrator-enforced HITL, pure-function infra actions, coded hard limits on actions/spend/retries).
3. **Assume the safety system will be bypassed** ~10–20% of the time for injection — so the application layer must contain the blast radius regardless.
4. **Red-team continuously and adversarially**, with the working stack (PyRIT + HarmBench + manual multi-turn testing in CI/CD), accepting that multi-turn (Crescendo-style) and LLM-as-judge reliability remain open weaknesses requiring human review.
5. **Gate autonomy on verification, not capability** — operate at Level 3–4, reserve Level 5 for narrow, exhaustively verified tasks, and expand permissions progressively against accumulated evidence.
6. **Invest in context curation as the durable moat** — proprietary tool/rule selection infrastructure, selected in code, outperforms model choice on unfamiliar proprietary codebases.

---

## Conclusion

Across defensive architecture, offensive testing, organizational governance, and production engineering, the research tells one story from four angles: **autonomous agentic AI becomes safe and reliable to the exact degree that deterministic, governed scaffolding surrounds the probabilistic model — and dangerous to the degree that autonomy is allowed to outrun verification.** Microsoft's four layers, IBM's zero-trust ADLC, OPA's default-deny policy-as-code, PyRIT's adversarial campaigns, OWASP's Excessive-Agency warning, and Stripe's Blueprint engine are not competing approaches; they are the same doctrine instantiated at the model, safety-system, application, and organizational layers. The empirical anchors — Deloitte's 11% operationalization rate, the 0.95⁵ ≈ 77% reliability decay, the 29–61% Crescendo uplift, the residual 10–20% injection ASR, and Stripe's 1,300 human-reviewed PRs/week — all reinforce the same conclusion: **the model is the easy part; the system that controls the model is the work.**

## Sources

- <https://medium.com/@sahin.samia/how-to-build-safe-ai-agents-best-practices-for-guardrails-and-oversight-a0085b50c022>
- <https://digitalthoughtdisruption.com/2025/07/31/agentic-ai-guardrails-policy-enforcement/>
- <https://learn.microsoft.com/en-us/security/zero-trust/sfi/secure-agentic-systems>
- <https://www.ibm.com/think/tutorials/ai-agent-security>
- <https://learn.microsoft.com/en-us/agents/adoption-maturity-model/maturity-model-security-governance>
- <https://arxiv.org/html/2410.02828v1>
- <https://microsoft.github.io/PyRIT/>
- <https://www.aisecurityinpractice.com/attack-and-red-team/pyrit-zero-to-red-team/>
- <https://www.microsoft.com/en-us/security/blog/2024/02/22/announcing-microsofts-open-automation-framework-to-red-team-generative-ai-systems/>
- <https://learn-prompting.fr/blog/ai-red-teaming-pyrit>
- <https://arxiv.org/html/2512.08769v1>
- <https://deniskisina.dev/posts/agentic-coding-revolution/>
- <https://dev.to/deniskisina/from-code-completion-to-autonomous-development-the-evolution-of-agentic-coding-223m>
- <https://agenticrisks.com/a-3-phase-agentic-workflow-design-process/>
- <https://www.mindstudio.ai/blog/agentic-coding-levels-explained>
- <https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents>
- <https://www.linkedin.com/pulse/agentic-coding-vs-vibe-dead-stripes-minions-just-provedit-gilak-3ov0f>
- <https://www.mindstudio.ai/blog/stripe-minions-blueprint-architecture-deterministic-agentic-nodes>
- <https://ice-ice-bear.github.io/posts/2026-04-01-stripe-coding-agents/>
- <https://www.paperclipped.de/en/blog/stripe-minions-autonomous-coding-agents/>

_Note: 3 URL(s) also appeared in prior runs of this prompt (not duplicates in current run; see index.json for full history)._

## Run metadata

- **Prompt:** MODO: EXECUTION MODE — AUTONOMÍA TOTAL AUTORIZADA
- **Depth / breadth:** 2 / 3
- **Queries used:** 4 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 380.3 s
- **Errors during run:** 0
- **Started at:** 2026-06-05T11:11:09Z
- **Module version:** deep_research 0.1.0
