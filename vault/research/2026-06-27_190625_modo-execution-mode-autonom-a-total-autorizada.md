# Bounded Autonomy for Agentic AI: A Governance and Safe-Execution Report

## 0. Framing Note — On "EXECUTION MODE — AUTONOMÍA TOTAL AUTORIZADA"

The directive that opened this brief — *total autonomy authorized* — is, paradoxically, the single most important artifact to interrogate before writing the report, because the entire body of research below converges on one finding: **blanket, mode-level autonomy is not a coherent operating concept for production agentic systems.** Across six independent sources — Microsoft's security engineering, a JACM 2025 survey, MIT-affiliated identity researchers, IBM's observability practice, and the regulatory/analyst consensus (EU, NIST, Gartner, McKinsey) — autonomy is never granted as a global flag. It is **granted per-action, conditioned on reversibility and impact**, revoked by default, and incrementally re-enabled under verifiable identity, policy gates, and human-in-the-loop (HITL) checkpoints.

This report therefore treats "Execution Mode" not as a license to bypass controls but as a **reference operating model**: the disciplined machinery that *makes* high-autonomy execution safe enough to be worth authorizing. The remainder synthesizes all research learnings into that model.

---

## 1. The Core Principle: Autonomy Is Per-Action, Not Per-Session

Every framework reviewed rejects the binary "autonomous vs. supervised" framing in favor of a **continuous, risk-keyed branch on each action**. The decisive variables, recurring across all sources, are:

| Axis | Low end | High end | Consequence for execution |
|---|---|---|---|
| **Reversibility** | Fully reversible (cache write, draft) | Irreversible (payment, deletion, account mod) | Reversible → async audit; irreversible → synchronous approval |
| **Impact / blast radius** | Read-only query | Production write, deployment | Higher impact → more verification steps + HITL |
| **Environment** | Dev/test | Production, customer-facing | Production → HITL regardless of confidence |
| **Confidence (calibrated)** | High, well-calibrated | Low or uncalibrated | Below threshold → escalate to human |

The operating consequence: an agent in "Execution Mode" still executes a *read* with minimal deliberation and a *deletion* only after a serialized human approval. The mode does not change; the **per-action risk classification** does. This is the load-bearing idea of the entire report.

---

## 2. Defense-in-Depth: Microsoft's Four-Layer Architecture

Microsoft's paired guidance — *"Secure agentic AI systems"* (companion to *"Reduce risk for autonomous agentic AI systems"*) — mandates a **defense-in-depth strategy across four mitigation layers**. Critically, it places deterministic enforcement in *orchestrator logic, not model reasoning* — the model is never the last line of defense.

| Layer | Responsibility | Key mechanism |
|---|---|---|
| **Model** | Intrinsic safety of the base model | Alignment, refusal behavior |
| **Safety System** | External guardrails around the model | Content filters, classifiers |
| **Application** | Deterministic control flow | **HITL review for high-risk/irreversible actions via orchestrator logic**; least-privilege / least-action |
| **Positioning / Deployment** | How the agent is situated in the environment | Network/identity boundaries, conditional access |

### 2.1 Least-Privilege *and* Least-Action

The Application layer enforces **zero permitted actions by default**, incrementally enabled by role and risk. Each agent receives a **unique, verifiable identity** for RBAC — autonomy is scoped to an identity, not granted to "the agent" as a category.

### 2.2 The Microsoft Operational Stack

| Product | Function in the control plane |
|---|---|
| **Microsoft Agent 365** | Central control plane for agent fleet |
| **Microsoft Foundry** | Guardrails, content filters, **AI Red Teaming Agent**, **PyRIT** adversarial testing |
| **Microsoft Entra** | Agent identity, conditional access |
| **Microsoft Purview** | Data classification, data-loss governance |

**Takeaway for Execution Mode:** the HITL gate is a deterministic orchestrator check, not a model self-assessment. An agent cannot "decide it is confident enough" to skip the gate — the gate is structurally external to the model.

---

## 3. The Risk-Aware, Budgeted Controller (JACM 2025 Survey)

The JACM 2025 survey *"AI Agent Systems"* (arXiv 2601.01743v1) formalizes the execution loop as a **risk-aware, budgeted controller** that branches on reversibility and impact:

- **Low-risk, read-only queries** → minimal deliberation, run directly.
- **High-risk, irreversible operations** (writes, deployments, payments) → trigger **additional verification, multi-step evidence gathering, or human confirmation.**

### 3.1 Planner / Executor Separation

The survey's strongest architectural prescription is the **explicit separation of planning from execution**:

- A **planner** proposes a plan with **constraints and success criteria**.
- An **executor** runs the plan under **stricter tool permissions and validation.**

This separation **reduces failure blast radius** — the component that reasons broadly (planner) never directly touches side-effecting tools; the component that touches tools (executor) operates under tight, validated permissions.

### 3.2 Typed Action Schemas + Policy-as-Code Pre-Gates

> Structured/typed action schemas **must pass schema validation and policy-as-code gates before any side effect.**

This is a hard ordering constraint: **validate → authorize → execute**, never execute-then-check. It pairs directly with the synchronous-approval pattern in §6.

---

## 4. Identity, Delegation, and Authorization — The Emerging Frontier

*"Identity Management for Agentic AI"* (arXiv 2510.25819v1, CC BY-SA 4.0; Tobin South, Alex Pentland et al.) treats **authorization for autonomous agents as a distinct, unresolved frontier** — agents act *on behalf of* principals, so authority must be **delegated and chained**, not assumed.

### 4.1 Standards Anchoring Agent Authorization

| Standard / RFC | Role in agent auth |
|---|---|
| **OAuth 2.1** | Baseline delegated authorization |
| **RFC 8693** (token exchange) | Identity-chaining; agent acts with exchanged tokens |
| **RFC 7591** (dynamic client registration) | Agents register as clients programmatically |
| **RFC 7636** (PKCE) | Proof-key flow hardening |
| **CIBA** (Client-Initiated Backchannel Auth) | Out-of-band human approval for agent actions |
| **OpenID Connect for agents** | Federated agent identity |
| **SCIM agent schema** | Provisioning/deprovisioning agent identities |
| **Capability tokens** (macaroons, biscuits) | Attenuable, delegatable, fine-grained capabilities |

### 4.2 Governance References

- **EU AI Act** — legal backstop (see §8).
- **NIST SP 800-162** — **ABAC (Attribute-Based Access Control)** as the access model for dynamic, context-rich agent decisions.

**Takeaway for Execution Mode:** "Autonomy authorized" must resolve to a **scoped, attenuable, revocable credential chain** (ideally capability tokens that can be narrowed at each delegation hop), not a session-wide elevation. CIBA in particular is the standards-native mechanism for *out-of-band human approval* of an in-flight agent action — the protocol embodiment of the HITL gate.

---

## 5. The Three-Tier Risk Continuum (IBM Agentic Observability)

IBM's framework (*"Agentic AI in Observability,"* The New Stack) operationalizes the risk continuum into **three execution tiers keyed to reversibility + production status**:

| Tier | Trigger | Execution model |
|---|---|---|
| **1 — Automated execution** | Low-risk, fully reversible, **non-prod** | Agent acts directly |
| **2 — Supervised automation** | Medium-risk | **Agent proposes, human approves before execution** |
| **3 — Human-in-the-loop** | High-risk, **customer/production-facing** | HITL **regardless of agent confidence** |

The phrase *"regardless of agent confidence"* is decisive: high confidence **never** buys a downgrade out of Tier 3. Confidence calibrates *within* a tier; it does not move actions *between* tiers.

### 5.1 Mandatory MELT Across All Tiers

Every action in every tier must capture **MELT — Metrics, Events, Logs, Traces** (the EU AI Act's framing of observability). There is no "too small to log" action.

### 5.2 Deployment Reality

- **~60–70% of automation occurs in dev/test; 30–40% in production.** The bulk of safely-automatable work is non-prod — consistent with Tier 1 dominance.
- **AI gateways act as runtime enforcement points**, validating each action against policy rules *before execution* — the runtime embodiment of the policy-as-code pre-gate from §3.2.

This framework aligns explicitly with the **NIST AI RMF** and the **EU AI Act continuous-monitoring** requirements.

---

## 6. Confidence Thresholds, Calibration, and Approval Architecture

### 6.1 Set by Risk Tolerance, Calibrated Empirically

Confidence thresholds should be **set by risk tolerance, then calibrated empirically against the system's own production task distribution — not generic industry benchmarks.** Two *independent* properties must be measured:

| Property | Definition | Why it matters |
|---|---|---|
| **Calibration** | Stated confidence matches actual success rate | A "90% confident" action should succeed ~90% of the time |
| **Discrimination** | Confidence separates correct from incorrect outcomes | A model can be calibrated on average yet useless at telling good from bad |

> **Verbalized LLM confidence scoring shows systematic overconfidence.** A model's self-reported confidence is a *hypothesis*, not a measurement — it must be validated against observed outcomes before being trusted as a gating signal.

### 6.2 Synchronous Approval vs. Asynchronous Audit

| Pattern | When | Mechanism | Trade-off |
|---|---|---|---|
| **Synchronous approval** | Irreversible actions (financial transfers, data deletion, account modification) | **Pause + serialize state, return an invocation ID**, await human decision | Adds latency; eliminates irreversible-error exposure |
| **Asynchronous audit** | Reversible decisions | Act immediately; review after the fact | Near-zero latency; **delayed detection** of errors |

The choice maps cleanly onto the reversibility axis: **irreversible → synchronous; reversible → async.** The serialized-state-plus-invocation-ID pattern is what makes a paused agent *resumable* after human approval — it is the technical substrate of CIBA-style out-of-band approval.

---

## 7. Policy-as-Code: Separating Control Placement from Enforcement

A recurring architectural pattern centralizes policy while distributing its hooks:

- A **`@control()` decorator** (or equivalent) marks control-hook *placement* — the responsibility of **developers**.
- A **central policy server** owns enforcement *logic* — the responsibility of **compliance**.
- This maps to **NIST PDP / PEP** (Policy Decision Point / Policy Enforcement Point) and **OPA-style policy-engine** concepts.

### 7.1 Why This Separation Pays Off

| Benefit | Mechanism |
|---|---|
| **Fleet-wide policy updates** | Change the central policy without redeploying any agent |
| **Separation of duties** | Developers place hooks; compliance writes policy — neither can unilaterally weaken controls |
| **Auditability** | Every decision flows through a PDP that can log its rationale |

### 7.2 Two Required Companions

1. **Idempotent action execution** — so a retried/resumed action (after a paused approval, or a network retry) does not double-execute (e.g., a duplicate payment).
2. **Immutable provenance / audit trails** — tamper-evident records of who/what authorized each side effect.

**Takeaway for Execution Mode:** the autonomy "switch" should live in the **central policy server**, not in agent code. This is what lets an operator *narrow or revoke* autonomy fleet-wide in seconds without touching a single agent binary.

---

## 8. Regulatory and Analyst Pressure — Concrete and Near-Term

The governance case is no longer speculative; it is dated and enforceable.

### 8.1 Regulation

| Instrument | Provision | Timeline / status |
|---|---|---|
| **EU AI Act, Article 14** | Mandates **human oversight via human-machine interface tools** for high-risk AI (healthcare, credit, employment, critical infrastructure) | **Enforceable Aug 2, 2026** |
| **EU AI Act risk tiers** | 4-tier categorization: **unacceptable / high / limited / minimal** | In force |
| **NIST IR 8596** (Initial Preliminary Draft) | Calls for **HITL checks + confidence thresholds** | Draft |
| **CFPB** | Requires **explainability for AI credit decisions** | In force |

Article 14's "human-machine interface tools" requirement is, in effect, a legal mandate for the synchronous-approval / HITL machinery described in §5–6 — for high-risk domains it is not optional.

### 8.2 Analyst Forecasts

| Source | Prediction |
|---|---|
| **Gartner** | By **2030, 50%** of AI agent deployment failures will stem from **insufficient governance-platform runtime enforcement** |
| **Gartner** | **>40%** of agentic AI projects **canceled by end-2027** |
| **McKinsey** | **62%** experimenting with agents; only **23% scaling** in ≥1 function; **≤10% per function** |

The Gartner runtime-enforcement prediction is the analyst restatement of this report's thesis: the dominant future failure mode is **not** model capability — it is **missing runtime governance**. The McKinsey gap (62% experimenting vs. 23% scaling) is the empirical footprint of teams that built capable agents but could not safely *operate* them.

---

## 9. Synthesis — A Reference Operating Model for "Execution Mode"

Combining all sources into a single executable model:

### 9.1 The Per-Action Decision Pipeline

```
1. Agent (executor) proposes a typed, schema-valid action
2. SCHEMA VALIDATION        — reject malformed actions (JACM)
3. POLICY-AS-CODE GATE      — PDP/PEP/OPA check before any side effect (JACM, IBM gateway)
4. RISK CLASSIFICATION      — reversibility × impact × environment (all sources)
5. CONFIDENCE CHECK         — empirically calibrated threshold for this task class
6. BRANCH:
     • Tier 1 (low / reversible / non-prod)  → execute, ASYNC AUDIT
     • Tier 2 (medium)                        → propose, await human approval
     • Tier 3 (high / irreversible / prod)    → SYNCHRONOUS APPROVAL
                                                (serialize state, return invocation ID,
                                                 CIBA-style out-of-band human decision)
7. EXECUTE idempotently under scoped, attenuable credentials (capability token)
8. CAPTURE MELT             — metrics, events, logs, traces (every tier)
9. WRITE immutable provenance record
```

### 9.2 Architectural Invariants (non-negotiable across all sources)

| # | Invariant | Source(s) |
|---|---|---|
| 1 | **Zero actions by default**; incrementally enabled by role/risk | Microsoft |
| 2 | **Planner ≠ executor**; executor has stricter permissions | JACM |
| 3 | **HITL via orchestrator logic, not model reasoning** | Microsoft |
| 4 | **High-risk/prod → HITL regardless of confidence** | IBM |
| 5 | **Validate → authorize → execute**, never reorder | JACM, IBM |
| 6 | **Irreversible → synchronous; reversible → async** | Confidence/approval research |
| 7 | **Per-agent verifiable identity**; delegated, attenuable, revocable auth | Microsoft, South/Pentland |
| 8 | **Policy centralized, hooks distributed** (PDP/PEP) | Policy-as-code research |
| 9 | **Idempotent execution + immutable provenance** | Policy-as-code research |
| 10 | **MELT on every action, every tier** | IBM (EU AI Act) |

### 9.3 What "Total Autonomy Authorized" Can Legitimately Mean

It cannot mean "skip the gates." It *can* legitimately mean a defensible, bounded posture:

- **Maximize Tier-1 throughput** — run all reversible, non-prod work directly with no approval friction (consistent with the 60–70% of automation that is dev/test).
- **Keep Tier-2/3 gates intact** — proposal-and-approve for medium risk; synchronous approval for irreversible/production actions.
- **Pre-authorize scoped capabilities** — issue narrow, time-boxed, attenuable capability tokens so the agent does not re-prompt for each in-scope action, while remaining instantly revocable centrally.

This is the difference between *velocity within bounds* (defensible) and *unbounded side effects* (the failure mode Gartner forecasts and Article 14 forbids in high-risk domains).

---

## 10. Contrarian and Forward-Looking Considerations *(flagged as analysis/speculation)*

- **Verbalized confidence is a trap.** *(High confidence in this claim — directly supported.)* Because LLM self-reported confidence is systematically overconfident, any Execution Mode that gates on the model's *stated* confidence is building on sand. Gate on **empirically calibrated, task-class-specific** thresholds derived from your own production outcome logs, and refresh them as the task distribution drifts.

- **Capability tokens (macaroons/biscuits) are underused relative to their fit.** *(Speculative.)* OAuth-centric stacks dominate, but attenuable capability tokens map more naturally to agent delegation chains — each hop can *narrow* authority without a round-trip to an authorization server. Expect this to become a differentiator as multi-agent delegation deepens.

- **The "AI gateway as PEP" pattern will likely consolidate the market.** *(Speculative, Gartner-adjacent.)* If 50% of 2030 failures are runtime-enforcement gaps, the highest-leverage investment is a **single runtime choke point** (gateway/PDP) through which all side-effecting actions must pass — rather than per-agent guardrails that drift out of sync.

- **CIBA + serialized-state-with-invocation-ID is the canonical "pause for a human" primitive.** *(High confidence.)* Teams building HITL should adopt this pattern explicitly rather than inventing bespoke approval queues; it is standards-native, resumable, and audit-friendly.

- **The regulatory clock is the binding constraint, not the technology.** *(High confidence.)* With EU AI Act Article 14 enforceable **Aug 2, 2026**, any high-risk-domain agent shipping without human-machine-interface oversight tooling is non-compliant on arrival. Governance is now a **launch gate**, not a roadmap item.

---

## 11. Bottom Line

The research is unanimous and mutually reinforcing: **safe high-autonomy execution is achieved by *removing* autonomy as a global setting and re-granting it per-action under a risk-tiered, identity-scoped, policy-gated, fully-observed pipeline.** "EXECUTION MODE — AUTONOMÍA TOTAL AUTORIZADA," read against this literature, is best implemented not as a bypass but as a **maximally efficient Tier-1 lane with intact Tier-2/3 gates**, scoped credentials, idempotent side effects, immutable provenance, and MELT on every action. That is the configuration that is simultaneously fast, defensible, and — as of August 2026 — legally compliant.

## Sources

- <https://learn.microsoft.com/en-us/security/zero-trust/sfi/secure-agentic-systems>
- <https://arxiv.org/html/2601.01743v1>
- <https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/03/agentic-ai-autonomy-levels-control-framework-v2-csa-styled.pdf>
- <https://cdn.prod.website-files.com/625447c67b621ab49bb7e3e5/69388ca4cdb5836ee83b10f5_69388ca257d8a9675e92aeb8_agentic-ai-workflow-patterns-whitepaper.pdf>
- <https://arxiv.org/pdf/2510.25819>
- <https://www.linkedin.com/pulse/three-tier-risk-model-agents-based-production-status-ken-priore-hunfe>
- <https://galileo.ai/blog/human-in-the-loop-agent-oversight>
- <https://galileo.ai/blog/agent-evaluation-framework-metrics-rubrics-benchmarks>
- <https://suhasbhairav.com/blog/building-human-in-the-loop-approval-gates-for-high-risk-agent-actions>

_Note: 1 URL(s) also appeared in prior runs of this prompt (not duplicates in current run; see index.json for full history)._

## Run metadata

- **Prompt:** MODO: EXECUTION MODE — AUTONOMÍA TOTAL AUTORIZADA
- **Depth / breadth:** 2 / 3
- **Queries used:** 2 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 262.0 s
- **Errors during run:** 1
- **Started at:** 2026-06-27T17:06:25Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://zylos.ai/en/research/2026-01-30-ai-agent-human-hando...': page-fetch: https://zylos.ai/en/research/2026-01-30-ai-agent-human-handoff/: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1010)>`

</details>
