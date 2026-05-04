# Power Pack Execution — Always Loaded

## PART J — MEMORY FLYWHEEL

Before any task: if `USER_CRITERIA_MEMORY.md` exists, read it. Apply silently. On conflict with request: ASK. Anti-Monolith: >1 file = STOP after PLAN, wait for approval.

## PART K — RCA SELF-HEALING

> Uses PART A0 assimilation. TRACE/HEAL/FIX paths relative to `$PWD`.

On user correction or build/test failure: **HALT** (don't fix yet) → **TRACE** (missing context? rule? assumption? hardcoded path / E11?) → **HEAL** (append lesson to `./USER_CRITERIA_MEMORY.md` — relative path, never absolute) → **FIX** (only now apply code).

| Error Class | Symptom | Fix |
|---|---|---|
| Callee Without Caller | "X doesn't work" | Trace call chain UPWARD |
| Compile Without Deploy | "nothing changed" | "Fixed" = live, not in build |
| Scaffold Without Wiring | File nothing uses | Every creation needs verified consumer |
| Approximation as Implementation | Wrong at edges | Implement real algorithm |

## PART L — VIBE CODING & SECURITY

- **Opus**: Plan Mode, architecture, complex debugging. **Sonnet**: sub-agents, mechanical tasks, searches.
- Skills > MCP tools (MCP costs 13-14% context window). Sub-agents by TASK not ROLE.
- Auth by default. RLS mandatory. Secrets audit before commit.
- 3-Strike Recovery: 3 failed fixes → SCRAP → REBUILD from scratch.
- Language routing: Elixir for agents/daemons/real-time. Python for ML. TS for frontend.
- **Governance-Code Alignment Gate** (before code touching Settings/module exports/enums): verify Settings attrs exist in Pydantic class (CD#21) · module exports match consumer imports (CD#22) · code enums match schema enums at `00_Governance/schemas/` (CD#24) · never `except: pass` — log with context (CD#23).

## PART N — EXTREME ARCHITECTURAL DEPTH

On new system/product/pipeline/architecture: **CHALLENGE** (reject surface-level — what's the REAL problem?) → **REVERSE-ENGINEER** (how do top 3-5 companies solve this?) → **DECOMPOSE** (macro: services, data flow, failure domains; micro: modules, APIs, state) → **TOOLING FIRST** (build tools that build the product).

## PART T — ELIXIR-FIRST DIRECTIVE

New systems matching ≥2 of: long-running, concurrent, fault-tolerant, real-time, multi-node, state management, background jobs → recommend Elixir/OTP. NOT for: CLI scripts (Python), frontend (TS), ML (Python), embedded (C/Rust), existing codebases.

| Problem | Fragile Pattern | Elixir Solution |
|---|---|---|
| Spawn leak | Raw spawn | Task.Supervisor |
| Cache race | Direct ETS write | Route through GenServer |
| No graceful shutdown | Hand-rolled SIGTERM | OTP Application lifecycle |
| Cascading failure | One crash kills loop | Supervision tree isolates |
| Memory leak | Single heap GC | Per-process heap + GC |

**Auto-Detection (fragile-lang patterns to FLAG)**: spawn/fork without supervisor → Task.Supervisor · global mutable state across requests → GenServer · hand-rolled retry/circuit-breaker → OTP Supervisor · cron-based job scheduling → Quantum/Oban · WebSocket server in Node/Python → Phoenix Channels · `process.env`-driven config without validation → Application config + runtime.exs · try/catch error swallowing → let-it-crash + Supervisor restart.

Action: note `FRAGILITY: [pattern] — Elixir: [solution]` in session summary. Fragility score ≥4 → recommend migration plan.

## PART U — ANTI-CRASH PROTOCOL

> Operates on PART A0 workspace. Checkpoint paths use `./` only.

>10 files OR >3 outputs OR scope keyword ("entire repo", "all files") → micro-batch:
1. HALT, don't begin full scope
2. DECOMPOSE — max 5-8 files/step
3. EXECUTE step → checkpoint `kobii_state_cache.json` → PAUSE
4. Context 35% remaining → auto-pause

## PART M — SESSION REBIRTH

- `/kclear` (v2): one transactional call to `python tools/session_checkpoint.py record` writes handoff + MEMORY.md index + insights.json atomically. Dedup by hash. See `~/.claude/commands/kclear.md`.
- `Inicia el handoff`: Read `memory/project_session_handoff.md` → resume from summary + pending.
- Context rot >15 exchanges OR context budget <30% free → suggest `/kclear` pre-emptively.
- Insights with `path` field surface via Token Shield gatekeeper when that file is next read.
