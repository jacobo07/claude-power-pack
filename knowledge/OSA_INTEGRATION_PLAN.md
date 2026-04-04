# OSA + Claude Power Pack + AADEF — Integration Master Plan

## Vision

Crear el agente de desarrollo más completo del mercado fusionando tres capas:
- **OSA** = Runtime + Tools + Multi-LLM + Multi-Canal (el coche)
- **Claude Power Pack** = Governance + Token Discipline + Error Learning (el ABS + airbags)
- **AADEF Engine** = OTP Fault Tolerance + TS Bridge + Swarm (el chasis indestructible)

## Architecture: 3-Layer Stack

```
┌─────────────────────────────────────────────────────┐
│                USER INTERFACES                       │
│  TUI (Rust) │ Desktop (Tauri) │ Telegram │ Discord  │  ← OSA channels
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              GOVERNANCE LAYER (Power Pack)            │
│                                                      │
│  Intent Router ─── Anti-Monolith ─── Blast Radius    │
│  ↓                                                   │
│  ExecutionOS (OBSERVE→PLAN→EXECUTE→VERIFY→HARDEN)    │
│  ↓                                                   │
│  Mistakes Registry (17 patterns) ─── RCA Self-Heal   │
│  ↓                                                   │
│  Token Leash ─── Scaffold Auditor ─── OmniCapture    │
│  ↓                                                   │
│  Memory Flywheel ─── Domain Error Classes             │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│             EXECUTION LAYER (OSA + AADEF)            │
│                                                      │
│  Signal Classifier ─── Tier Router ─── Budget Mgr    │  ← OSA brain
│  ↓                                                   │
│  Agent Loop (ReAct) ─── 25 Tools ─── Streaming       │  ← OSA execution
│  ↓                                                   │
│  Swarm (parallel/pipeline/debate/review) ─── 14 Roles│  ← OSA + AADEF
│  ↓                                                   │
│  OTP Supervisor ─── Circuit Breaker ─── Port Bridge   │  ← AADEF resilience
│  ↓                                                   │
│  Memory: ETS (hot) → SQLite (warm) → Skills (cold)   │  ← OSA + AADEF KAIROS
│  ↓                                                   │
│  7 LLM Providers ─── Credential Pool ─── Fallback    │  ← OSA + AADEF Gateway
└─────────────────────────────────────────────────────┘
```

---

## Phase 1: Governance Injection (Power Pack → OSA)

### 1.1 System Prompt Overlay

**Problem:** OSA's system prompt (IDENTITY.md + SOUL.md) has no governance rules.
**Solution:** Inject Power Pack governance as a middleware layer in OSA's prompt assembly.

**Integration Point:** OSA's `context/assembler.ex` module (builds the final prompt)

**Implementation:**
```elixir
# In OSA's context assembler, after building the base prompt:
defp inject_governance(context, tier) do
  governance = case tier do
    :light -> load_governance("core.md")  # ~200 tokens
    :standard -> load_governance(["core.md", "pre-task.md"])  # ~500 tokens
    :deep -> load_governance(["core.md", "pre-task.md", "during-task.md"])  # ~800 tokens
    :forensic -> load_governance(:all)  # ~1200 tokens
  end

  %{context | system_prompt: context.system_prompt <> "\n\n" <> governance}
end
```

**Files to create in OSA:**
- `priv/governance/core.md` — Adapted from Power Pack governance-overlay/core.md
- `priv/governance/mistakes_registry.md` — The 17 documented mistakes
- `lib/osa/governance/loader.ex` — Tier-aware governance loader

### 1.2 Signal Classification Enhancement

**Problem:** OSA classifies signals by complexity weight (0.0-1.0). Power Pack classifies by blast radius (LOW/HIGH) and tier (LIGHT/STANDARD/DEEP/FORENSIC).

**Solution:** Merge both classification systems:

```
OSA Signal Weight  →  Power Pack Tier  →  Governance Load
0.0 - 0.35         →  LIGHT             →  core.md only (~200 tokens)
0.35 - 0.65        →  STANDARD          →  core + phases 0-10 (~500 tokens)
0.65 - 0.85        →  DEEP              →  core + all phases + overlays (~800 tokens)
0.85 - 1.0         →  FORENSIC          →  full governance + artifacts (~1200 tokens)
```

**Integration Point:** OSA's `signal/classifier.ex` → add a `governance_tier` field to the Signal struct.

### 1.3 Anti-Monolith Gate

**Problem:** OSA accepts any prompt regardless of complexity.
**Solution:** Add a pre-processing step in OSA's input pipeline that detects monolithic prompts.

**Integration Point:** Before signal classification in `agent/loop.ex`

```elixir
defp pre_process(prompt) do
  case Osa.Governance.AntiMonolith.check(prompt) do
    :ok -> {:ok, prompt}
    {:violation, micro_prompts} ->
      {:error, :monolith_detected, "Split into: #{Enum.join(micro_prompts, ", ")}"}
  end
end
```

---

## Phase 2: Error Learning (Power Pack → OSA)

### 2.1 Mistakes Registry as Tool

**Problem:** OSA has no pre-built error pattern library.
**Solution:** Expose Power Pack's 17 Mistakes Registry as an OSA tool.

```elixir
defmodule Osa.Tools.MistakesCheck do
  @behaviour Osa.Tools.Behaviour

  def name, do: "check_mistakes"
  def description, do: "Check code against 17 known AI coding mistake patterns"

  def execute(%{"file_path" => path}) do
    content = File.read!(path)
    violations = Osa.Governance.MistakesScanner.scan(content, path)
    {:ok, format_violations(violations)}
  end
end
```

### 2.2 RCA Self-Healing in Agent Loop

**Problem:** When OSA's agent makes an error and the user corrects it, OSA fixes the code but doesn't update its governance rules.
**Solution:** Inject RCA protocol into OSA's error handling.

**Integration Point:** OSA's `agent/loop.ex` — when a tool returns an error or user sends a correction.

```elixir
# In the agent loop, when user corrects:
defp handle_correction(correction, state) do
  # 1. HALT
  Logger.info("RCA: Correction detected. Halting execution.")

  # 2. TRACE
  root_cause = Osa.Governance.RCA.trace(correction, state.recent_actions)

  # 3. HEAL — save lesson to persistent memory
  Osa.Memory.LongTerm.save(%{
    type: :governance_patch,
    lesson: root_cause.lesson,
    category: root_cause.category,
    timestamp: DateTime.utc_now()
  })

  # 4. FIX — then apply the actual code fix
  apply_fix(correction, state)
end
```

### 2.3 Domain Error Classes

**Problem:** OSA's memory has no concept of domain-specific learned errors.
**Solution:** Extend OSA's memory schema with a `domain_errors` table.

```elixir
# New Ecto migration
create table(:domain_errors) do
  add :domain, :string       # "minecraft", "python", "web"
  add :error_code, :string   # "E-KC-001"
  add :description, :text
  add :prevention, :text
  add :occurrence_count, :integer, default: 1
  timestamps()
end
```

Pre-seed with Power Pack's KobiiCraft (4), CostaLuz (6), OmniCapture (3) error classes.

---

## Phase 3: Token Discipline (Power Pack → OSA)

### 3.1 The Leash

**Problem:** OSA's agent can burn unlimited tokens on mass-search operations.
**Solution:** Implement token budgeting middleware.

**Integration Point:** OSA's tool execution pipeline.

```elixir
defmodule Osa.Governance.Leash do
  @max_files_per_turn 3
  @max_file_lines 500

  def check_tool_call(:file_read, %{"path" => path}, state) do
    lines = count_lines(path)
    if lines > @max_file_lines do
      {:ask_permission, "File #{path} has #{lines} lines. Read specific section instead?"}
    else
      :allow
    end
  end

  def check_tool_call(:file_grep, %{"pattern" => _, "path" => path}, state) do
    files_read_this_turn = state.files_read_count
    if files_read_this_turn >= @max_files_per_turn do
      {:ask_permission, "Already read #{files_read_this_turn} files this turn. Continue?"}
    else
      :allow
    end
  end
end
```

### 3.2 Token Forensics

**Problem:** OSA tracks token usage per-request but doesn't analyze waste patterns.
**Solution:** Periodic analysis of OSA's token logs.

**Implementation:** A scheduled job (OSA already has Scheduler) that:
1. Reads the last 24h of token usage from OSA's budget table
2. Identifies: redundant file reads, repeated prompts, mass-grep waste
3. Generates a TOKEN_BURN_REPORT.md
4. If waste > 20% of budget, creates a governance patch

### 3.3 Prompt Cache Integration

**Problem:** OSA has its own ETS-based cache. Power Pack has SHA-256 prompt caching.
**Solution:** Merge into one layer — keep OSA's implementation but add SHA-256 fingerprinting from Power Pack for cross-session dedup.

---

## Phase 4: Runtime Verification (OmniCapture → OSA)

### 4.1 OmniCapture as OSA Tool

**Problem:** OSA has no runtime telemetry verification.
**Solution:** Register OmniCapture query as an OSA tool.

```elixir
defmodule Osa.Tools.RuntimeCheck do
  @behaviour Osa.Tools.Behaviour

  def name, do: "runtime_check"
  def description, do: "Query OmniCapture for runtime errors, crashes, performance metrics"

  def execute(%{"project" => project, "since" => since}) do
    case Req.get("http://#{omnicapture_host()}/api/v1/query/summary",
      params: [project_id: project, since: since],
      headers: [{"authorization", "Bearer #{api_key()}"}]
    ) do
      {:ok, %{status: 200, body: body}} -> {:ok, format_summary(body)}
      _ -> {:error, "OmniCapture unavailable"}
    end
  end
end
```

### 4.2 Governance Gate: DEEP+ requires runtime check

**Integration Point:** OSA's completion flow.

When the agent claims "done" at DEEP+ tier:
1. Query OmniCapture for the project
2. If CRITICAL/FATAL events in last 5 min → block completion
3. If WARNING only → log but allow

---

## Phase 5: Scaffold Auditor (Power Pack → OSA)

### 5.1 Pre-Commit Hook

**Problem:** OSA doesn't check for scaffold illusions before committing.
**Solution:** Register scaffold auditor in OSA's git tool.

**Integration Point:** OSA's `tools/git.ex` — before executing `git commit`:

```elixir
defp pre_commit_check(repo_path) do
  violations = Osa.Governance.ScaffoldAuditor.scan(repo_path)
  case violations do
    [] -> :ok
    list ->
      {:blocked, "#{length(list)} scaffold violations found. Fix before committing."}
  end
end
```

### 5.2 Patterns Ported

Port all 11 patterns from scaffold-auditor.js to Elixir:
- Commented-out supervisor children
- TODO/FIXME placeholders
- :infinity timeouts
- Empty catch/rescue blocks
- Stub return values

---

## Phase 6: AADEF as OSA's Resilience Layer

### 6.1 OTP Supervision for OSA Channels

**Problem:** If OSA's Telegram channel crashes, it takes down the whole system.
**Solution:** Run each OSA channel under AADEF's DynamicSupervisor.

### 6.2 Circuit Breaker for LLM Providers

**Problem:** OSA has basic fallback chains but no stateful circuit breaker.
**Solution:** Replace OSA's provider fallback with AADEF's stateful Gateway (closed/open/half-open per provider).

### 6.3 TS Bridge for Legacy Tools

**Problem:** Some Power Pack tools (token-optimizer Python scripts) need to run from Elixir.
**Solution:** Use AADEF's TSWorker/Port.open pattern to call Python scripts from within OSA's Elixir runtime.

---

## Phase 7: Memory Unification

### 7.1 3-Layer Unified Memory

```
Layer 1: HOT (ETS)
  - Current session context
  - Prompt cache (SHA-256)
  - Agent state

Layer 2: WARM (SQLite)
  - Conversation history (OSA)
  - Task contexts (AADEF)
  - Domain errors (Power Pack)
  - Governance patches (Power Pack RCA)

Layer 3: COLD (File System)
  - Auto-generated skills (OSA SICA)
  - USER_CRITERIA_MEMORY.md (Power Pack Flywheel)
  - KAIROS consolidated summaries (AADEF Dreamer)
  - Token burn reports (Power Pack Forensics)
```

### 7.2 Cross-System Memory Query

An agent should be able to ask: "Have I seen this error pattern before?" and get results from all three systems:
- Power Pack: checks Mistakes Registry + Domain Errors
- OSA: checks long-term memory + skills
- AADEF: checks KAIROS consolidated tasks

---

## Implementation Roadmap

| Phase | Scope | Effort | Dependencies |
|-------|-------|--------|--------------|
| 1.1 | Governance prompt injection | 2 days | Fork OSA, understand prompt assembly |
| 1.2 | Signal → Tier mapping | 1 day | Phase 1.1 |
| 1.3 | Anti-Monolith gate | 1 day | Phase 1.1 |
| 2.1 | Mistakes as OSA tool | 1 day | Phase 1.1 |
| 2.2 | RCA in agent loop | 2 days | Phase 1.1 |
| 2.3 | Domain error migration | 1 day | Phase 2.2 |
| 3.1 | The Leash middleware | 1 day | Phase 1.1 |
| 3.2 | Token Forensics job | 2 days | Phase 1.1 |
| 4.1 | OmniCapture tool | 1 day | OmniCapture running on VPS |
| 4.2 | DEEP+ runtime gate | 1 day | Phase 4.1 |
| 5.1 | Scaffold auditor | 1 day | Phase 1.1 |
| 6.1-6.3 | AADEF integration | 3 days | AADEF v0.3.0 |
| 7.1-7.2 | Memory unification | 3 days | Phases 1-6 |

**Total estimated: ~20 days of focused work**

---

## Success Metrics

After integration, the combined system should:

1. **Token efficiency**: 30%+ reduction in token waste vs standalone OSA
2. **Error prevention**: Catch scaffold illusions before commit (0 false "done" claims)
3. **Learning compounding**: Domain errors from one project prevent same error in all projects
4. **Resilience**: Any single channel/provider crash recovers in <5 seconds
5. **Runtime verification**: No "compiles but crashes" passes the DEEP+ gate
6. **Audit score**: External audit scores ≥8/10 on all categories
