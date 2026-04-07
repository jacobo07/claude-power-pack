# Governance Overlay — Pre-Task Gate

> Loaded for STANDARD, DEEP, and FORENSIC tiers. ~150 tokens.

## 1. CLASSIFY Complexity

Before writing any code:
- Count files that will be created or modified
- Identify cross-module dependencies (does change A require change B?)
- Check if this touches shared utilities, types, or config

## 2. LOAD Project Governance

> Inherits workspace context from PART A0 Assimilation Scan. Uses `./governance/` relative paths only.

Check and read (if they exist):
- `/governance/domain/PROJECT_DOMAIN_RULES.md` — project-specific constraints
- `/governance/domain/PROJECT_DATA_MODEL.md` — data entities and relationships
- `CLAUDE.md` — project-level behavioral rules
- Domain rules can ONLY add restrictions — they never weaken universal rules

Authority hierarchy: **CONSTITUTION (00-03) > GOVERNANCE (04-09) > OPERATIONAL (10-19) > DOMAIN (PROJECT_*)**

## 3. IDENTIFY Existing Patterns

Before creating anything new:
- Grep for existing implementations of similar functionality — **never rebuild what exists** (Mistake #9)
- Verify no duplicate file/module exists with similar name
- Map the call chain UPWARD from the entry point — understand who calls what before modifying (Mistake #14)
- Check for established naming conventions, file organization patterns

## 4. SET Verification Scope

Determine for this specific project:
- Which quality gates apply? (TypeScript? Python? Both?)
- What test framework is configured? (`jest`, `pytest`, `vitest`?)
- What linter runs? (`eslint`, `ruff`, `mypy`?)
- What's the commit convention?
- Are there pre-commit hooks?

## 5. Language Fragility Gate (Core Directive #11) — BLOCKING

Before writing ANY new backend/infrastructure code, run the fragility detector:

### 5a. Score Criteria (1 point each)

| # | Criterion | Signal |
|---|-----------|--------|
| C1 | Long-running process (daemon, agent, worker) | Runs >1hr or indefinitely |
| C2 | Concurrent operations (parallel calls, multi-agent) | >3 simultaneous async ops |
| C3 | Fault tolerance required (production, user-facing) | Crash = user impact or data loss |
| C4 | Stateful across requests (sessions, caches, queues) | State outlives a single request |
| C5 | Real-time communication (WebSocket, SSE, streaming) | Bidirectional or push-based |
| C6 | Multi-provider failover (LLM gateways, API routing) | 2+ providers with fallback |
| C7 | Background job processing (pipelines, ETL) | Jobs queued, retried, tracked |
| C8 | Distributed clustering needed | Multi-node coordination without external tooling |
| C9 | Hot code reload valuable | Zero-downtime deploys matter |
| C10 | Cost-per-request at scale matters | >10K req/day, cost efficiency is KPI |

### 5b. Fragility Score

- **Score = count of YES answers**
- **0-1:** No gate. Proceed with any language.
- **2-3:** ADVISORY — Recommend Elixir, Language Decision Record (LDR) required if declined.
- **4+:** BLOCKING — Elixir is the default. Non-Elixir requires LDR + explicit user override.

### 5c. Bypass Conditions (score resets to 0)

- Extending existing codebase — score resets to 0 ONLY IF: (a) the existing codebase has <500 lines of the fragile language, OR (b) a retroactive LDR exists documenting the language choice with justification. If neither condition is met, the fragility score stands. This prevents the bypass from silently excusing large non-Elixir services that should have been evaluated. Retroactive LDR still required per Section 5e.
- ML/AI model training or inference (Python ecosystem advantage)
- Browser frontend (TypeScript/React)
- Team has zero Elixir experience AND deadline < 2 weeks
- User explicitly requests a specific language with stated rationale (must be documented in LDR)

### 5d. Language Decision Record (if score >= 2 and non-Elixir chosen)

```
LDR: [project-name] [date]
Score: [N]/10 — [list matched criteria]
Chosen language: [X]
Bypass reason: [which condition OR explicit user override]
OTP equivalents needed:
  - [ ] Supervision / process restart strategy
  - [ ] Circuit breakers
  - [ ] Graceful shutdown handlers
  - [ ] Backpressure handling
  - [ ] State isolation
Risk accepted by: user (explicit override)
```

If score >= 4 and no bypass applies, **DO NOT PROCEED** without user confirmation of the LDR.

### 5e. Retroactive Assessment for Existing Projects

When modifying an existing project built in a potentially fragile language:

1. Score the project against C1-C10 on first interaction
2. If score >= 4 AND no LDR exists in the project's governance/ directory:
   a. CREATE the LDR retroactively (see LDR template in pre-output.md)
   b. FLAG as `LDR_MISSING — built without governance gate`
   c. Add "Elixir Migration Candidate" note to the LDR
   d. On EACH subsequent modification: include a one-line note in response: "Note: This project scores [N]/10 on the Language Fragility Gate. LDR filed."
3. This does NOT block work on the existing project (bypass condition: extending existing codebase)
4. But it DOES require the LDR to be filed for audit trail
5. After 3+ sessions modifying the same project without LDR: escalate to user with migration recommendation

## 6. Anti-Crash Scope Gate (PART U) — ADVISORY

Before starting execution of any Tier 3+ task:

### 6a. Scope Scan
- How many files will be read or modified?
- How many distinct outputs are requested?
- Does the prompt contain scope keywords: "entire", "all files", "full codebase", "every", "complete"?
- Rough token estimate for total output?

### 6b. Micro-Batching Trigger
If ANY threshold hit (>10 files, >3 outputs, >5000 est. tokens, scope keyword):
1. Flag: "MICRO-BATCHING REQUIRED"
2. Decompose into steps (max 5-8 files OR 1 deliverable per step)
3. Present plan, wait for approval
4. After each step: write `kobii_state_cache.json`, report, await go-ahead

### 6c. Step Sizing
- File reads: max 5-8 per step
- Output generation: 1 deliverable per step
- Analysis: chunk by module/directory, not individual files
- If single file >500 lines: section reads only (PART Q compatibility)

## 7. Agent Governance Gate (PART W) — ADVISORY

Before starting any task involving agent systems:

### 7a. Agent Detection
Check for agent system indicators:
- Framework imports: `langchain`, `langgraph`, `crewai`, `autogen`, `ag2`, `claude_agent_sdk`, `semantic_kernel`
- Agent loop patterns: `while`/`for` with tool calls inside
- Multi-agent coordination: message passing, delegation, shared memory
- Tool registration/definition code: `@tool`, `Tool(`, `tools=[`

### 7b. If Agent Detected
1. Load overlay: `modules/executionos-lite/overlays/agent-governance.md`
2. Check: Does project have an AGT policy file? If not, scaffold from `modules/agent-governance/policy-templates.md`
3. Map agent privilege model to Ring 0-3 (default = Ring 3, least privilege)
4. Verify kill switch exists in every agent loop (`max_iterations`, `circuit_breaker`, `cost_limit`)
5. If multi-agent: verify trust declarations between agents

### 7c. OWASP ASI Quick Check (10 items)
Before any agent deployment or completion claim:

| # | Risk | Verify |
|---|------|--------|
| ASI-01 | Unrestricted Agency | `allowed_tools` explicitly defined? |
| ASI-02 | Data Poisoning | Input validation on agent memory/context? |
| ASI-03 | Insecure Agent-Agent | Trust/auth between agents? |
| ASI-04 | Supply Chain | Plugin signatures verified? |
| ASI-05 | Improper Output | Output sanitization + saga rollback? |
| ASI-06 | Excessive Functionality | Minimal tool set (not "all tools")? |
| ASI-07 | Prompt Injection | Input filtering + trust scoring? |
| ASI-08 | Cascading Failures | Circuit breakers + error budgets? |
| ASI-09 | Insufficient Oversight | Human-in-the-loop for critical actions? |
| ASI-10 | Inadequate Logging | All agent actions logged? |

## 8. Intent-Lock Protocol (STANDARD+) — ADVISORY

> Triggers when: writing >50 lines of new code, refactoring async/concurrent code, or building a new module/service. Fills the gap between Phase 1 (INTENT) and Phase 5 (PLAN). Prevents Mistakes #37-39.

### 8a. API Bounding (Declare Your Tools)

Before writing implementation code, declare:
1. **Key libraries and APIs** you will use — cite specific methods/classes, not just library names
2. **Concurrency model** — what runs async, what stays on main/UI thread, where the sync↔async boundary is
3. **Existing patterns** — grep for prior implementations of similar functionality. If one exists, declare you'll reuse it (Mistake #9). If choosing between modern and legacy API, declare the modern one.

### 8b. Never-Do Matrix (Task-Specific Prohibitions)

Write 3+ prohibitions specific to THIS task, drawn from:
- The project's known failure patterns (`./governance/12_FAILURE_PATTERNS.md` if it exists)
- The mistakes registry — especially #37 (Silent Degradation), #38 (Producer-Consumer Gap), #39 (Sync Trap)
- The stack's known pitfalls (e.g., no `readFileSync` in Node async, no `:infinity` in Elixir GenServer, no `requests.get` in FastAPI async, no `block.setType()` in game tick loops)

### 8c. Sovereign Doubt (Red Team Your Architecture)

Before presenting the plan, answer 3 questions:
1. **"Where does this collapse under 10x load?"** → identify the bottleneck, propose mitigation
2. **"What if the external dependency fails?"** → map every error path, verify no silent swallowing
3. **"Is this a structural fix or a surface patch?"** → if surface → flag to user before proceeding

### 8d. Gate Output

The Intent-Lock produces a mental artifact (internal, not printed unless FORENSIC tier or user requests it) that feeds into Phase 5 (PLAN). The implementation plan MUST be consistent with declared API bounding and MUST NOT violate the Never-Do Matrix. Pre-output checklist item 11 verifies this consistency at delivery time.
