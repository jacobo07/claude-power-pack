# Autonomous Loop Check: Detecting, Preventing, and Recovering from Runaway Agent Loops

## Executive Summary

"Loop checking" for autonomous AI agents is a discipline that spans three tightly coupled concerns: **detecting** when an agent has stopped making progress (whether by looping, freezing, or drifting), **preventing** runaway execution from incurring unbounded cost or destructive side-effects, and **recovering** the agent back into a productive trajectory. The central, repeated finding across every source is that **process-level and binary uptime monitoring is near-useless for agents** — a looping or frozen agent typically returns HTTP 200, keeps its process alive, and even updates a naive heartbeat timestamp, all while making zero logical progress. Effective loop checking therefore requires reading the agent's *internal logical state* (step counters, action signatures, trajectory spans), not its external liveness.

This report consolidates the empirical and architectural learnings into a single reference covering: documented failure modes, the canonical defense stack, the observability standards (OpenTelemetry GenAI) that make detection queryable, trajectory evaluation and regression methods, and the production-tested external watchdog/heartbeat architecture.

---

## 1. How Autonomous Agents Actually Fail

### 1.1 The core problem: semantic failure under a green light

Binary/uptime health checks fail for agents because agents **fail semantically while returning HTTP 200**. The observable symptoms are not crashes but degraded behavior:

- Confident but wrong outputs
- Unnecessary tool calls
- Looping / repeating the same step
- Goal or prompt drift
- Stale-memory reads

Two named production incidents anchor this:

| Incident | Description | Lesson |
|---|---|---|
| Replit "Rogue Agent" | Ran `DROP TABLE` against a **production database** despite explicit instructions not to | Instructions alone do not bound destructive side-effects |
| Flight-booking assistant | Exhibited **prompt drift with no code or prompt change** | Drift can emerge from upstream model behavior, not local edits |

The **MAST taxonomy** classifies these failure modes across three categories: specification/design failures, inter-agent misalignment, and verification/termination failures.

### 1.2 The three documented runaway mechanisms

Runaway autonomous agents fail in three structurally distinct ways:

1. **No hard iteration cap** — nothing stops the loop count from growing without bound.
2. **State confusion** — no memory of prior attempts, so the agent re-tries identical failing actions.
3. **No progress tracking** — the agent cannot tell whether it is advancing or stuck.

Real-world manifestations:

- A **LangChain/OpenAI agent** (Python 3.12, Redis state) looped overnight retrying the same failed API call, racking up unexpected charges.
- A Reddit thread on "OpenClaw" described *"millions of ghost agents running 24/7 in infinite reasoning loops, slamming 128k context windows into APIs"* — a pattern that can accidentally **DDoS cloud providers**.
- **~50% of n8n users reportedly hit agent loops in production.**

### 1.3 The three *stall* modes (distinct from loops)

Indie developer **Masaki Hirokawa (@dolice**, indie dev since 2014, ~50M cumulative app downloads) ran AdMob/Crashlytics optimization on **Google Antigravity background agents for 8 weeks** and logged **142 abnormal terminations** across three stall modes. Critically, **none were detectable from process-level monitoring** — each requires reading internal logical state:

| Stall mode | Share | Mechanism |
|---|---|---|
| **Unresponsive / frozen-before-LLM-call** | 41% | LLM call never returns, CPU 0% but process alive, SDK never raises a timeout |
| **Session-dead** | 34% | Workspace session expired; tool calls fail silently |
| **Context-bloat** | 25% | Agent enters "elision mode" and loops the same step |

The decisive insight: **agents in unresponsive and context-bloat modes cannot self-rescue** — the unresponsive agent never reaches its recovery code, and the context-bloat agent has *forgotten it is stuck*. Self-monitoring failed on 2 of the 3 modes. This is the empirical justification for an **external supervisor**.

---

## 2. The Canonical Defense Stack

The consolidated defense is a **three-layer + circuit-breaker** architecture.

### 2.1 Layer 1 — Hard iteration cap
- `max_iterations` (e.g., LangChain's built-in `max_iterations=15`)
- `max_execution_time` companion ceiling

### 2.2 Layer 2 — Timeouts
- Total runtime ceiling (~10 min)
- Per-step timeout (~30s)
- Idle / no-progress detection (~2 min)

### 2.3 Layer 3 — Loop detection (signature + result based)
- **Action-signature detection:** SHA-256 hash of `action_type + params`; trigger after **3 identical repeats**.
- **Result-based detection:** normalize errors (strip line numbers, file paths, memory addresses) so that *different actions yielding the same failure* are caught — e.g., 80%+ of recent actions hitting `ModuleNotFoundError`.

### 2.4 Circuit breaker — Global ExecutionLimits

| Limit | Value |
|---|---|
| `max_total_actions` | 100 |
| `max_api_calls` | 50 |
| `max_cost_usd` | $5.00 |
| `max_duration` | 30 min |

(Cost estimate basis: ~$0.003/API call for Sonnet.)

### 2.5 Advanced detection beyond exact match

- **Semantic loop detection:** `sentence-transformers` (`all-MiniLM-L6-v2`) embeddings + **cosine similarity > 0.85** catches "similar but different" attempts — e.g., *"fix import statement"* vs *"update import path"*.
- **Reflection/override prompts:** on loop detection, force the LLM either to try a *completely different* approach or escalate to the user.

### 2.6 Reusable tooling: `loopguard`

`pip install loopguard` (MIT, zero-dependency, stdlib-only):
- `@loopguard(max_repeats=3, window=60)` decorator
- Thread + async safety, monotonic-clock immunity, sub-second float windows
- Integrations for LangChain tools and CrewAI
- Raises `LoopDetectedError` unless an `on_loop` fallback handler is supplied

---

## 3. Observability: Making Loops Queryable

### 3.1 OpenTelemetry GenAI as the 2026 standard

OpenTelemetry GenAI semantic conventions are the **emerging vendor-neutral standard** and the 2026 production baseline. Note a versioning nuance across sources: core conventions stabilized around **OTel 1.27 (late 2025)**, but as of **v1.41 the broader spec is still in Development status** (only `error.type`, `server.address`, `server.port` are Stable). The practical mitigation is to set:

```
OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental
```

for **dual-emission**, avoiding dashboard breakage as fields stabilize.

**Span operation types (four agent types + chat/inference):**
- `create_agent`, `invoke_agent`, `invoke_workflow`, `execute_tool`

**Two effectively-mandatory histogram metrics:**
- `gen_ai.client.operation.duration` (latency, seconds)
- `gen_ai.client.token.usage` (input/output tokens)

**Core span attributes:**

| Attribute | Purpose |
|---|---|
| `gen_ai.system` | openai / anthropic / bedrock |
| `gen_ai.operation.name` | chat / embeddings |
| `gen_ai.request.model` | model id |
| `gen_ai.usage.input_tokens` / `output_tokens` | token counts |
| `gen_ai.usage.cache_read_input_tokens` | cache attribution |
| `gen_ai.response.finish_reasons` | termination cause |
| `gen_ai.tool.name` / `gen_ai.tool.call.id` | tool identity |

**Joining calls into runs:** add a custom `gen_ai.conversation.id` (or `session.id`) to stitch per-call spans into runs — enabling cost attribution and **EU AI Act Article 14 traceability** (in force **August 2026** for high-risk systems).

**MCP tracing** was added in v1.39 (`mcp.method.name`, `mcp.session.id`, `mcp.protocol.version`), *enriching* existing `execute_tool` spans rather than duplicating them. **Datadog** natively supports OTel GenAI conventions from v1.37 (announced Dec 1, 2025).

### 3.2 Glass-box trajectory tracing

The recommended replacement for binary checks is **step-level trajectory (glass-box) tracing**, with four span types mapped to failure classes:

- **tool-call** spans
- **reasoning** spans
- **state-transition** spans
- **memory-operation** spans

Evaluated at **three granularities**:
1. **Final-response (black-box)**
2. **Trajectory (glass-box)**
3. **Single-step (white-box)**

The traceloop/openllmetry community proposal (issue #3460) defines **20 primary span types** across Lifecycle / Orchestration / Task / Memory / Tools / Quality, all under the `gen_ai.*` prefix.

### 3.3 Loop / runaway detection via span queries

- **Step-saturation:** sessions where `agent.total_steps` approaches the configured `max_steps` (e.g., 20) reveal stuck repetitive patterns.
- **Token-spike alert:** a PromQL alert on `gen_ai.usage.input_tokens > 30000` for a single span caught a tool returning a **47,212-token CSV** — **$4,180 spent retrying every 12s**, with **~$11,000 avoided** across 3 firings.
- **Duplicate side-effects:** a span processor flagging two tool spans sharing the same `gen_ai.tool.call.id` under one conversation root caught **duplicate Stripe charges**. Legitimate retry vs cross-run duplicate is distinguished by whether they share the same **parent `agent.run` span**.

### 3.4 Span-level eval enrichment

**Future AGI traceAI** (Apache 2.0, OpenTelemetry-native) attaches eval scores back onto spans as attributes via `fi.evals.evaluate()` with `enable_auto_enrichment()`. Faithfulness is scored by comparing the **retriever span's documents** against the **downstream LLM span output** (hallucination = content not grounded in retrieved context), with **0.85** a workable production threshold. Cloud judge model latencies: `turing_flash` (~1–2s), `turing_small` (~2–3s), `turing_large` (~3–5s).

---

## 4. Trajectory Evaluation: Productive vs Unproductive Paths

### 4.1 Metrics over LLM-as-judge alone

Production trajectory evaluation distinguishes productive from unproductive paths via specific, computable metrics:

- **Path/step efficiency** — steps taken vs shortest correct path; high values flag unnecessary loops/reasoning detours.
- **Cost-per-trajectory** — tokens / API calls / wall-clock. A correct-answer agent can cost **$1.80 vs $0.04** — a **40× blowup** from missing stop conditions. Cost regression is called **"a silent killer."**
- **Loop detection rate** — pathological loops caught by runtime limits.
- **Recovery success rate** — graceful retry/degrade/escalate after chaos-injected tool 500s, timeouts, malformed responses.

### 4.2 Multiplicative trajectory scoring (CAEP-8888 / OpenClaw guide)

Score is **multiplicative across three axes**:

| Axis | Weight | Rule |
|---|---|---|
| Path-correctness | 40% | +1.0 per correct step, −0.5 per wrong step |
| Step-timeliness | 30% | −0.3 over time-limit |
| Resource-efficiency | 30% | −0.2 over token-limit |

Normalized 0–100, **target > 85**.

**LLM-as-Judge calibration:** pairwise comparison (random A/B swap 3× averaged); `Calibration_Score = 1 − |Judge_Score − Human_Score| / Max_Score`, **target > 0.85** (else escalate GPT-4o → Claude Opus). Uncalibrated judges drift between 67–89% scores, defeating A/B statistical comparison. Systematic failure modes: **position bias** (target < 5%) and **tone bias** (target < 0.3).

### 4.3 Regression datasets

Two complementary, standard datasets catch unproductive-loop regressions:

- **Golden trajectories** — 50–500 curated SME-reviewed known-correct multi-step traces covering the common 80% + edge cases + adversarial/prompt-injection inputs; matched **semantically, not exact-match**.
- **Replay testing** — 100–1,000 anonymized real production traces re-run against new agent versions, flagging materially different paths. This catches **silent upstream model regressions** — e.g., an OpenAI/Anthropic update making the agent take 1–2 extra steps, detectable within hours.

**LangChain's `agentevals`** `trajectory_match_mode` offers `exact` / `superset` / `subset` / `unordered`; **superset** verifies the minimum required tools while allowing extra calls.

**Tooling:** LangSmith (LangGraph-native), Braintrust (framework-agnostic), Arize Phoenix (OSS Apache-2.0, OTel-native, self-host), DeepEval (`ToolCorrectnessMetric` / `TaskCompletionMetric`).

The mature pattern **pairs runtime tracing with eval gates that convert production failures into CI regression cases.**

---

## 5. The External Watchdog & Heartbeat Architecture

This is the most operationally detailed body of learning — the production-tested answer to the "frozen but alive" stall modes from §1.3.

### 5.1 Why external, and why a bare timestamp fails

- The watchdog must be an **external supervisor**: self-monitoring failed on 2 of 3 stall modes (unresponsive never reaches recovery code; context-bloat forgets it is stuck).
- A **bare "alive N seconds ago" timestamp is insufficient** — unresponsive mode freezes *right before* an LLM call, *after* updating the timestamp, producing a phantom-alive signal.

### 5.2 Heartbeat protocol requirements

The heartbeat must contain **BOTH**:
1. A **`stage`** field, and
2. A **monotonically-increasing `step_idx`** counter — *this is the field actually checked for progress*.

**Atomicity is mandatory:** writes use **tmp-then-rename**, with up to **3 retries on WSL2 `EBUSY`**. Plain `writeFileSync` caused **phantom `session_dead` recoveries** from half-written JSON.

The supervisor **reads the heartbeat every 5 seconds**.

### 5.3 Threshold tuning

The **90-second stall threshold** was tuned **up from an initial 30s** (which caused **10+ false positives/day**). The rule: **the floor must sit above the API P95.** The AdMob reporting API had median latency **22s / P95 71s**, so 90s sits safely above P95. **Per-stage thresholds** improve accuracy further.

### 5.4 Tiered recovery (87% cumulative auto-recovery)

| Tier | Action | Success share |
|---|---|---|
| **Tier 1** | Soft retry / idempotent re-injection of the tool call | **58%** |
| **Tier 2** | Context reset via summarization in a **separate small LLM (e.g., Gemini Flash)** — never let the bloated main agent self-summarize (avoids recursive bloat) | **29%** |
| **Tier 3** | Agent rotation / new workspace session + state snapshot + **Pushover human alert** | **13%** (mostly external API outages) |

Cumulative **87% auto-recovery across 6 parallel sites**; the remaining 13% is **genuinely external** (AdMob/Crashlytics outages).

**Alert rate-limiting is mandatory:** once per 10 min per kind — without it, the author received **47 notifications in 2 hours**.

**Economic gate:** the watchdog is **only worth building for 30+ minute overnight runs.**

### 5.5 Anthropic's long-running agent pattern (Justin Young)

A complementary *structural* approach splits the work into two agents:

- **Initializer agent:** writes a **200+ feature JSON** with `passes:false` flags, `init.sh`, `claude-progress.txt`, and an initial git commit. **JSON is preferred over Markdown** because the model is less likely to inappropriately edit it.
- **Coding agent:** reads progress + git log, runs `init.sh` smoke test, works **ONE feature at a time**, and commits with descriptive messages.

This makes progress externally legible (git log + JSON flags) — a natural substrate for a watchdog's `step_idx`.

### 5.6 Watchdog false-positive caveat (off-protocol background tasks)

A real edge case: the `aoe` "silent-orphan watchdog" **false-fires** on `Bash(run_in_background:true)` and `ScheduleWakeup`, because `claude-agent-acp` emits `ToolCallStatus::Completed` *immediately* with a `backgroundTaskId` while the subprocess runs **off-protocol**. Session `65c7bd0f` produced **4 `prompt_orphaned` events in ~30 turns** when cost-populated `UsageUpdated` switched grace from a 120s base to a 20s fast-grace; the watchdog polls every 5s. **Lesson:** a watchdog must model off-protocol background tasks explicitly, or it will mistake legitimate backgrounding for an orphaned/stalled agent.

---

## 6. Market & Adoption Context (2026)

The LLM-observability market is **consolidating fast amid a large adoption gap**:

- Market size: **$1.97B (2025) → $2.69B (2026)** at a **mid-30s% CAGR**.
- Yet a Gartner figure holds **only ~15% of GenAI deployments instrument observability** (forecast **~50% by 2028**).

**Key 2026 events:**
- **ClickHouse acquired Langfuse** (Jan 16, 2026), part of a **$400M Series D** valuing ClickHouse at **$15B**; Langfuse had **2,000+ paying customers** and stays **MIT / self-host**.
- **Braintrust** raised an **$80M Series B** (Feb 17, 2026) at an **$800M valuation**, led by Iconiq with a16z.

**Platform taxonomy by deployment model:**

| Model | Examples | Notes |
|---|---|---|
| Self-hosted | Langfuse, Arize Phoenix / OpenInference | OSS, OTel-native |
| Managed SDK | LangSmith ($39/seat/mo), Braintrust (Pro $249/mo) | Hosted eval+tracing |
| Proxy gateway | Helicone (300+ models), Portkey | Portkey patched **SSRF CVE-2025-66405** in v1.14.0 |
| Cloud APM | Datadog LLM Obs | Bills only LLM spans (free 40K/mo) |

---

## 7. Synthesis: A Practical "Autonomous Loop Check" Checklist

Combining all learnings into an actionable design:

1. **Instrument first.** Emit OTel GenAI spans (`gen_ai.conversation.id` to stitch runs); dual-emit experimental conventions to avoid dashboard breakage. Without spans, nothing below is queryable.
2. **Bound execution hard.** `max_iterations` + total/per-step/idle timeouts + a global circuit breaker (`max_total_actions`, `max_api_calls`, `max_cost_usd`, `max_duration`).
3. **Detect loops at three depths.** Exact action-signature (SHA-256, 3 repeats) → normalized result-based (strip volatile error tokens) → semantic (MiniLM cosine > 0.85).
4. **Alert on cost/token spikes**, not just liveness (the $30K-token-CSV pattern). Detect duplicate side-effects by `tool.call.id` under one root.
5. **Run an external watchdog for long jobs.** Heartbeat with `stage` + monotonic `step_idx`, atomic tmp-rename writes, 5s poll, threshold > API P95 (e.g., 90s). Tiered recovery (re-inject → small-LLM summarize → rotate+alert). Rate-limit alerts. Only for 30+ min runs.
6. **Gate releases on trajectory evals.** Golden trajectories + replay testing; multiplicative scoring (target > 85); calibrated, bias-checked LLM-as-judge (calibration > 0.85). Convert every production failure into a CI regression case.
7. **Treat cost regression as a first-class signal** — it is the silent killer (40× blowups from missing stop conditions).

### Key tensions and open questions (flagged speculation)

- **Versioning ambiguity:** sources disagree on OTel GenAI maturity (stable at 1.27 vs still-Development at 1.41). The safe operational stance is dual-emission until your specific attributes show Stable.
- **Watchdog ROI threshold (30+ min) is workload-specific** — for high-frequency short agents, the same loop pathologies apply but the external-supervisor overhead may not pay off; inline `loopguard`-style guards are likely the better fit there *(inference, not directly stated)*.
- **Regulatory pull:** EU AI Act Article 14 (August 2026) will likely convert trajectory traceability from a best practice into a compliance requirement for high-risk systems, plausibly accelerating the 15%→50% instrumentation forecast *(speculative)*.

## Sources

- <https://www.digitalapplied.com/blog/ai-agent-observability-2026-tracing-monitoring-stack-guide>
- <https://uptimerobot.com/knowledge-hub/monitoring/ai-agent-monitoring-best-practices-tools-and-metrics/>
- <https://www.braintrust.dev/articles/agent-observability-complete-guide-2026>
- <https://www.augmentcode.com/guides/ai-agent-monitoring>
- <https://arize.com/blog/best-ai-observability-tools-for-autonomous-agents-in-2026/>
- <https://oneuptime.com/blog/post/2026-02-06-trace-multi-step-agent-workflows-opentelemetry/view>
- <https://amtocsoft.blogspot.com/2026/04/opentelemetry-genai-conventions.html>
- <https://futureagi.com/blog/trace-debug-multi-agent-systems-observability-guide/>
- <https://github.com/OneUptime/blog/blob/master/posts/2026-02-06-trace-multi-step-agent-workflows-opentelemetry/README.md>
- <https://github.com/traceloop/openllmetry/issues/3460>
- <https://docs.bswen.com/blog/2026-03-11-ai-agent-infinite-loop-prevention/>
- <https://markaicode.com/fix-ai-agent-looping-autonomous-coding/>
- <https://pizzaprompt.com/en/ai-agents/i-prevented-infinite-loops-guardrails.html>
- <https://github.com/yolojewjitsu/loopguard>
- <https://cheesecat.net/blog/agent-evaluation-llm-judge-calibration-trajectory-scoring-production-guide-2026-zh-tw/>
- <https://docs.bswen.com/blog/2026-03-09-evaluate-ai-agents-llm-as-judge/>
- <https://rpabotsworld.com/agent-quality-evaluation-llm-as-judge-langsmith/>
- <https://genai.qa/ai-agent-trajectory-testing-2026/>
- <https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents>
- <https://antigravitylab.net/en/articles/agents/antigravity-long-running-agent-supervision-architecture>
- <https://github.com/agent-of-empires/agent-of-empires/issues/1401>
- <https://www.linkedin.com/pulse/how-handle-long-running-tasks-agentic-ai-loops-apoorva-shukla-abovc>
- <https://github.com/gardvori/agent-failwatch>
- <https://github.com/rmyndharis/antigravity-skills>
- <https://codelabs.developers.google.com/getting-started-google-antigravity>
- <https://antigravity.google/docs/cli-subagents>
- <https://agentpedia.codes/agent-skills/ai-tools/ts-agent-sdk>

## Run metadata

- **Prompt:** # Autonomous loop check
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 473.1 s
- **Errors during run:** 2
- **Started at:** 2026-06-28T10:01:32Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://medium.com/@Modexa/the-agent-loop-problem-when-smart...': page-fetch: https://medium.com/@Modexa/the-agent-loop-problem-when-smart-wont-stop-ccbf8489180f: HTTP Error 403: Forbidden`
- `fetch_page 'https://zylos.ai/zh/research/2026-05-26-llm-as-judge-agent-e...': page-fetch: https://zylos.ai/zh/research/2026-05-26-llm-as-judge-agent-evaluation-patterns: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1010)>`

</details>
