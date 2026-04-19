# Power Pack Execution — Always Loaded

## PART J — MEMORY FLYWHEEL

1. Before ANY task: check if `USER_CRITERIA_MEMORY.md` exists. If yes, read it.
2. Apply silently. On conflict with request: ASK user.
3. Anti-Monolith: >1 file = STOP after PLAN, wait for approval.

## PART K — RCA SELF-HEALING

> Context: Uses PART A0 assimilation. All paths in TRACE/HEAL/FIX must be relative to `$PWD`.

On user correction or build/test failure:
1. **HALT** — Stop. Don't fix yet.
2. **TRACE** — Missing context? Missing rule? Wrong assumption? Hardcoded path? (check E11)
3. **HEAL** — Append lesson to `./USER_CRITERIA_MEMORY.md` (relative path, never absolute)
4. **FIX** — Only now apply the code fix.

| Error Class | Symptom | Fix |
|-------------|---------|-----|
| Callee Without Caller | "X doesn't work" | Trace call chain UPWARD |
| Compile Without Deploy | "nothing changed" | "Fixed" = live, not in build |
| Scaffold Without Wiring | Created file nothing uses | Every creation needs verified consumer |
| Approximation as Implementation | Wrong at edges | Implement real algorithm |

## PART L — VIBE CODING & SECURITY

- **Opus**: Plan Mode, architecture, complex debugging
- **Sonnet**: Sub-agents, mechanical tasks, searches
- **Skills > MCP tools** (MCP costs 13-14% context window)
- Sub-agents by TASK not ROLE
- Auth by default. RLS mandatory. Secrets audit before commit.
- 3-Strike Recovery: 3 failed fixes → SCRAP → REBUILD from scratch
- **Language Routing**: Elixir for agents/daemons/real-time. Python for ML. TS for frontend.
- **Governance-Code Alignment Gate**: Before writing code that touches Settings, module exports, or enum definitions:
  1. Verify Settings attributes exist in the Pydantic class (CD#21)
  2. Verify module exports match what consumers import (CD#22)
  3. Verify code enums match schema enums at 00_Governance/schemas/ (CD#24)
  4. Never `except: pass` — always log with context (CD#23)

## PART N — EXTREME ARCHITECTURAL DEPTH

On any new system/product/pipeline/architecture:
1. **CHALLENGE** — Reject surface-level. "What's the REAL problem?"
2. **REVERSE-ENGINEER** — How do top 3-5 companies solve this?
3. **DECOMPOSE** — Macro (services, data flow, failure domains) + Micro (modules, APIs, state)
4. **TOOLING FIRST** — Build tools that build the product.

## PART T — ELIXIR-FIRST DIRECTIVE

For new systems matching >=2: long-running, concurrent, fault-tolerant, real-time, multi-node, state management, background jobs → recommend Elixir/OTP.

NOT for: CLI scripts (Python), frontend (TS), ML (Python), embedded (C/Rust), existing codebases.

| Problem | Fragile Pattern | Elixir Solution |
|---------|----------------|-----------------|
| Spawn leak | Raw spawn | Task.Supervisor |
| Cache race | Direct ETS write | Route through GenServer |
| No graceful shutdown | Hand-rolled SIGTERM | OTP Application lifecycle |
| Cascading failure | One crash kills loop | Supervision tree isolates |
| Memory leak | Single heap GC | Per-process heap + GC |

### Auto-Detection: Fragile Language Patterns
When encountering existing code in fragile languages that exhibits these patterns, FLAG for Elixir migration:
- spawn/fork without supervisor → FLAG: Elixir Task.Supervisor
- global mutable state across requests → FLAG: GenServer
- hand-rolled retry/circuit-breaker → FLAG: OTP Supervisor
- cron-based job scheduling → FLAG: Quantum/Oban
- WebSocket server in Node/Python → FLAG: Phoenix Channels
- process.env-driven config with no validation → FLAG: Application config + runtime.exs
- try/catch error swallowing → FLAG: let-it-crash + Supervisor restart

Action: Note "FRAGILITY: [pattern] — Elixir equivalent: [solution]" in session summary for user awareness. If fragility score >=4, recommend migration plan.

## PART U — ANTI-CRASH PROTOCOL

> Context: Operates on PART A0 workspace. Checkpoint paths use `./` only.

>10 files OR >3 outputs OR scope keyword ("entire repo", "all files") → micro-batch:
1. HALT — don't begin full scope
2. DECOMPOSE — max 5-8 files per step
3. EXECUTE step → checkpoint `kobii_state_cache.json` → PAUSE
4. Context 35% remaining → auto-pause

## PART M — SESSION REBIRTH

- `/kclear` (v2): one transactional call to `python tools/session_checkpoint.py record` writes handoff + MEMORY.md index + insights.json atomically. Dedup by hash. See `~/.claude/commands/kclear.md`.
- `Inicia el handoff`: Read `memory/project_session_handoff.md` → resume from its summary + pending list.
- Context rot >15 exchanges OR context budget <30% free → suggest `/kclear` pre-emptively.
- Insights with `path` field surface via Token Shield gatekeeper when that file is next read.
