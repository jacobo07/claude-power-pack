# Claude Power Pack v2.0

All-in-one skill that makes AI coding tools dramatically better at building software. Project-agnostic — works on any stack, any project.

## What's New in v2.0

- **Loop integrity** — Every plan must close. Interrupted work gets logged, not lost.
- **Acceptance-driven development** — Define "done" (Given/When/Then) before writing code.
- **Drift prevention** — Log every decision. Silent architectural drift is the #1 project killer.
- **Context rot awareness** — Quality degrades with session length. Active reset after 10+ exchanges.
- **PRD auto-versioning (C8)** — After completing features, check if PRD needs updating. Track versions.
- **21st.dev frontend module (Part F)** — Sleepy module that activates for frontend/web work. Uses 21st.dev MCP tools for component generation, design inspiration, and refinement. Zero cost when dormant.
- **UAT after each phase** — Don't proceed until current work passes verification.
- **Coherence validation** — Validate requests against project context before executing.

## Install

### Claude.ai (Project Knowledge)
1. Open your Project → Add Project Knowledge
2. Upload this zip (or just SKILL.md)

### Claude Code (Skill)
```bash
mkdir -p ~/.claude/skills/claude-power-pack
cp SKILL.md ~/.claude/skills/claude-power-pack/
```

### ChatGPT (Project Instructions)
1. Open your Project → Settings → Instructions
2. Paste the contents of SKILL.md

## Capabilities

| Part | Capability | Always Active? | Trigger |
|------|-----------|---------------|---------|
| A | Execution Depth (OBSERVE→PLAN→EXECUTE→VERIFY→HARDEN) | Yes | — |
| A | Loop integrity + acceptance criteria | Yes | — |
| A | Drift prevention + decision logging | Yes | — |
| B | Intent Routing (5 tiers) | Yes | — |
| B | Coherence validation + context rot awareness | Yes | — |
| C1 | Context Audit | On trigger | "token audit" |
| C2 | Prompt Compressor | On trigger | "compress this" |
| C3 | Dedup Finder | On trigger | "dedup check" |
| C4 | Governance Digest | On trigger | "create digest" |
| C5 | Description Trimmer | On trigger | "trim descriptions" |
| C6 | Sleepy Architecture Audit | On trigger | "sleepy audit" |
| C7 | Full Optimization Pipeline | On trigger | "full optimization" |
| C8 | PRD Auto-Versioning | On trigger | "PRD version" |
| D | Delivery Standards | Yes | — |
| E | Community Error Patterns (E1-E4) | Yes | — |
| F | 21st.dev Frontend Module | Dormant | React, Next.js, Vue, etc. |

## Sleepy Modules

Part F is a **sleepy module** — it costs zero tokens when dormant. It only activates when your conversation involves frontend/web keywords (React, Next.js, Vue, Svelte, CSS, UI, component, design, landing page, Tailwind, shadcn, etc.).

When active, it instructs Claude to use 21st.dev MCP tools for component generation and design. Requires the `magic-ui` MCP server connected. Falls back to manual implementation if unavailable.

## Community Error Patterns

Part E contains generalized error patterns discovered through real production errors. These are domain-agnostic prevention rules that apply to any stack:

- **E1: Selection Scope Confusion** — Don't mix candidates from different layers
- **E2: Scaffolding vs Identity Lock** — Declare temporary scaffolding as temporary
- **E3: Layer Flattening** — Don't collapse multi-layer decisions into one
- **E4: WordPress Content Destruction** — Use `content.raw`, never `content.rendered`

These patterns grow over time as new errors are discovered and generalized.

## Token Budget

SKILL.md: ~1100 words (~1463 tokens). 40% leaner than v1.0 while adding 8 new capabilities + preserving all community error patterns.

## Origin

Distilled from 180+ governance files, 20+ production projects, the PAUL framework principles, and 3 years of iteration. Every rule exists because something failed without it.

## Credits

- Loop integrity and acceptance-driven patterns inspired by [PAUL](https://github.com/ChristopherKahler/paul) (ChristopherKahler)
- Frontend module powered by [21st.dev](https://21st.dev) MCP tools
- Community error patterns from KobiiClaw auto-discovery
