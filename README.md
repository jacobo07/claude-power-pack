# Claude Power Pack v5.0

Universal AI execution framework. Project-agnostic. Works on Claude.ai, Claude Code, ChatGPT.

## What It Does

- **Prompt Quality Gate**: Rejects monolithic prompts with 3+ disconnected tasks
- **Anti-Monolith**: Forces plan-first execution with approval gates
- **Memory Flywheel**: Learns from corrections, reads preferences before every task
- **RCA Self-Healing**: Fixes governance before code on every error (HALT > TRACE > HEAL > FIX)
- **Vibe Coding Security**: Enforces auth, RLS, sandboxing, model routing, 3-strike recovery
- **Token Optimization**: 6 tools for cost analysis, waste detection, and context compression
- **ExecutionOS Lite**: 25-rule constitution with 20 phases across 4 depth tiers
- **Autoresearch**: Self-improving competitive intelligence (2x/day, scheduled)

## Install

```bash
# Unix/macOS/Linux
bash install.sh /path/to/project

# Windows PowerShell
.\install.ps1 -TargetDir "C:\project"
```

This generates:
- `USER_CRITERIA_MEMORY.md` — persistent learning file (AI reads before every task)
- Doctrine block in `CLAUDE.md` — execution rules injected into project governance

## Parts (12 total)

| Part | Name | Status |
|------|------|--------|
| A | Execution Depth (OBSERVE > PLAN > EXECUTE > VERIFY > HARDEN) | Always active |
| B | Intent Routing + Prompt Quality Gate | Always active |
| C | Token Optimization (6 tools) | On trigger |
| D | Delivery Standards | Always active |
| E | Community Error Patterns | Always active |
| F | Frontend/Web (21st.dev MCP) | Sleepy |
| G | Autoresearch (RSS + YouTube + Signals) | Sleepy |
| H | Reinforced Token Optimization (6 tools) | Sleepy |
| I | ExecutionOS Lite (25 rules, 20 phases, 6 overlays) | Sleepy |
| J | Memory Flywheel & Execution Discipline | Always active |
| K | RCA Self-Healing + Universal Error Classes | Always active |
| L | Vibe Coding & Security Constraints | Always active |

**Always active** = loaded every session (~800 tokens).
**Sleepy** = zero cost until triggered by keyword.

## Key Principles

1. **Skills > MCP tools** — MCP consumes 13-14% of context window. Skills load on-demand.
2. **Sub-agents by TASK** — (Linter, Tester, Deployer), not by role (Frontend Dev).
3. **3-Strike Recovery** — After 3 failed fix attempts: stop, scrap, rebuild from scratch.
4. **Security by default** — Auth, RLS, sandbox required. No exceptions.
5. **Learning compounds** — Every correction makes the system permanently smarter via Memory Flywheel.

## Token Budget

| Scenario | Estimated Tokens |
|----------|-----------------|
| Minimal (always-active parts only) | ~800 |
| Standard (+ one overlay) | ~1,500 |
| Full featured (+ ExecutionOS DEEP) | ~3,500 |
| Production (FORENSIC + all overlays) | ~5,000 |

## License

MIT
