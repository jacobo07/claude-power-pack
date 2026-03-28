# Claude Power Pack v3.0

All-in-one skill that makes AI coding tools dramatically better at building software. Project-agnostic — works on any stack, any project.

## What's New in v3.0

- **Module G: Autoresearch Engine** — Autonomous competitive intelligence via RSS + YouTube monitoring. Scheduled 2x/day (not session-exit), with signal scoring and 6-hour dedup. Eliminates trigger flood that consumed 25%+ of weekly token budget.
- **Module H: Reinforced Token Optimization** — 6 CLI tools: ExecutionOS compressor, CLAUDE.md linter, cross-project dedup, plugin waste detector, prompt pattern optimizer, session cost estimator.
- **Module I: ExecutionOS Lite** — Tiered loader that compresses 16KB/365-line ExecutionOS into ~3KB/80-line core. Full capability preserved via on-demand section loading.

## What It Does

**Always active (zero trigger needed):**
- Execution depth loop: OBSERVE -> PLAN -> EXECUTE -> VERIFY -> HARDEN
- Intent routing: classifies complexity and scales effort proportionally
- Quality gates: prevents shipping broken code
- Anti-fabrication + anti-drift rules
- Community error patterns from real project failures
- Proportional cost: simple requests stay cheap, complex ones get full rigor

**On trigger:** C1-C8 token optimization tools
**Sleepy:** F (Frontend), G (Autoresearch), H (Token Opt), I (ExecutionOS Lite)

## Install

### Claude Code
```bash
git clone https://github.com/jacobo07/claude-power-pack.git
cd claude-power-pack

# Unix
bash install.sh

# Windows
powershell -File install.ps1
```

### Claude.ai
Upload SKILL.md as Project Knowledge.

### ChatGPT
Paste SKILL.md into Project Instructions.

## Module Setup

### G: Autoresearch Engine
```bash
# Configure projects/feeds/channels
edit modules/autoresearch/config.json

# Install scheduler (2x/day)
python modules/autoresearch/setup_schedule.py

# Manual run
python modules/autoresearch/nightcrawler.py

# Uninstall
python modules/autoresearch/setup_schedule.py --uninstall
```
Requires: Python 3.10+, httpx, feedparser

### H: Token Optimization Tools
```bash
python modules/token-optimizer/claudemd_linter.py          # Lint CLAUDE.md files
python modules/token-optimizer/cross_project_dedup.py       # Find duplicate rules
node modules/token-optimizer/plugin_waste_detector.js       # Detect unused plugins
python modules/token-optimizer/prompt_pattern_optimizer.py   # Analyze patterns
python modules/token-optimizer/session_cost_estimator.py --tier 3  # Estimate cost
python modules/token-optimizer/executionos_compressor.py <file.md> # Compress prompts
```

### I: ExecutionOS Lite
```bash
# Migrate from full ExecutionOS
python modules/executionos-lite/migrate.py <executionos.md> --verify

# Reference core.md in your CLAUDE.md instead of the full file
```

## Capabilities

| Code | Capability | State |
|------|-----------|-------|
| A | Execution Depth | Always active |
| B | Intent Routing | Always active |
| C1-C8 | Token Optimization | On trigger |
| D | Delivery Standards | Always active |
| E | Error Patterns | Always active |
| F | Frontend/Web | Sleepy |
| G | Autoresearch | Sleepy |
| H | Reinforced Token Opt | Sleepy |
| I | ExecutionOS Lite | Sleepy |

## Token Budget

SKILL.md: ~1700 tokens. Sleepy modules add ~0 when dormant.

## Changelog

- **v3.0** (2026-03-28) — Autoresearch engine, reinforced token optimization, ExecutionOS Lite
- **v2.0** — PAUL integration, PRD versioning, 21st.dev sleepy module, context rot awareness
- **v1.0** — Execution depth, intent routing, token optimization, delivery standards, error patterns

## Origin

Distilled from 180+ governance files, 20+ production projects, and 3 years of iteration. Real failures, not theory.
