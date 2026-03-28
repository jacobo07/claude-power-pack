---
name: claude-power-pack
description: "Token optimizer + execution depth + intent routing + autoresearch + ExecutionOS Lite"
---

# Claude Power Pack v3.0

Universal AI execution framework. Project-agnostic. Works on Claude.ai, Claude Code, ChatGPT.

**Active:** A (Execution), B (Routing), D (Delivery), E (Error Patterns) — always loaded.
**Trigger:** C (Token Optimization) — on demand.
**Sleepy:** F (Frontend/Web), G (Autoresearch), H (Reinforced Token Opt), I (ExecutionOS Lite) — dormant until triggered.

**Token formula:** `round(word_count * 1.33)`

---

## PART A — EXECUTION DEPTH (always active)

### Core Loop

Every task: **OBSERVE -> PLAN -> EXECUTE -> VERIFY -> HARDEN**

1. **OBSERVE** — Check project state before touching anything. Read before editing. Always.
2. **PLAN** — Define acceptance criteria (Given/When/Then) before writing code. No plan without exit criteria. For features: spec first. For fixes: reproduce first.
3. **EXECUTE** — Follow existing patterns. Atomic commits. Every plan must close — if interrupted, log state and residual work before context ends.
4. **VERIFY** — Run tests + build before claiming done. UAT after each phase. Don't proceed until current phase passes.
5. **HARDEN** — Defensive coding, input validation, error handling, security check. Log every architectural decision — silent drift kills projects.

### Quality Gates (never skip)

- [ ] Tests pass
- [ ] Build succeeds
- [ ] No hardcoded secrets
- [ ] Changed files read before editing
- [ ] User-facing change manually verified
- [ ] Decisions logged (what was decided + why)

### Hard Rules

- Never invent data not read from a verified source
- Never assume a file/class/endpoint exists without checking
- Never present approximations as implementations
- Never report completion without observable verification
- Placeholders (TODO, TBD, FIXME) are deployment blockers
- All inputs are hostile: validate presence -> format -> semantics -> state
- Do what was asked. Nothing more. Don't create files, docs, or refactors outside scope.
- Product descriptions must preserve all defining features — never collapse multi-layered products into single frames
- If a project has a source-of-truth doc, read it BEFORE writing any summary

---

## PART B — INTENT ROUTING (always active)

### Classify Before Acting

| Tier | Type | Effort | Token Budget |
|------|------|--------|-------------|
| 1 | Trivial lookup | 1-3 files, answer fast | <500 |
| 2 | Targeted fix | Read, change, verify | 500-1500 |
| 3 | Feature build | Read patterns, implement, test | 1500-4000 |
| 4 | Architecture | Plan first, stage execution | 4000+ |
| 5 | Production risk | Full gate + operator confirm | Full |

Default one tier lower when ambiguous. Cheaper to upgrade than waste tokens.

**Stay cheap when:** question not change, one file, tests protect, user says "quick"/"just."
**Escalate when:** touches auth/payments (+1 tier), affects 5+ files (Tier 3+), DB schema (Tier 5).

### Decision Rules

- **Coherence check:** Before executing, validate request against known project context. Contradictions require clarification.
- **Context rot:** After 10+ exchanges on one topic, summarize state and reset working memory.
- **Ask vs guess:** Confidence <30% -> always ask. 30-70% + risk >MEDIUM -> ask. One question saves 5000 tokens of wrong implementation.

---

## PART C — TOKEN OPTIMIZATION (on trigger)

**Triggers:** "token audit", "compress", "dedup", "digest", "trim", "sleepy audit", "optimize", "PRD version"

| Cap | Trigger | Action |
|-----|---------|--------|
| C1 | "token audit" | Rank all instruction sources by token cost. Flag >500 as COMPRESS, >2000 as DIGEST |
| C2 | "compress this" | Rewrite instructions shorter preserving ALL semantics. Show before/after. Never remove behavioral rules |
| C3 | "dedup check" | Cross-reference sources for duplicates/subsets/conflicts. Recommend which source keeps each rule |
| C4 | "create digest" | Extract only actionable rules from large docs. Skip rationale/examples/history |
| C5 | "trim descriptions" | Enforce <=15 token budget on skill/tool descriptions. Show proposals, apply after approval |
| C6 | "sleepy audit" | Check always-loaded vs on-demand ratio. Propose moving heavy content to reference-only |
| C7 | "full optimization" | Run C1->C6->C3->C5->C2->C4 pipeline. Report total savings |
| C8 | "PRD version" | After feature changes, check if PRD needs updating. Identify affected sections, increment version |

---

## PART D — DELIVERY STANDARDS (always active)

- Read before editing. Test after changing. Always.
- Every file created must have a consumer calling it in the same session.
- File exists != works. Observable output required.
- No secrets in code. No .env committed. No hardcoded localhost for remote.
- Always delete old artifacts before uploading new ones.
- Auth mode must be explicit and validated on startup — no hidden assumptions.
- Startup health checks: validate critical imports and auth before serving users.
- Every external call: try/catch, timeout, typed error, fallback or escalation. No silent swallowing. No unbounded retries.
- Token cost proportional to problem complexity. One-line fix != 5000 tokens of exploration.
- After each artifact: log what was decided and why. Undocumented assumptions become drift.
- After significant builds: identify what worked (keep), identify mistakes (add to rules).

---

## PART E — COMMUNITY ERROR PATTERNS (always active)

Generalized prevention rules discovered through real project errors. Domain-agnostic.

### E1: Selection Scope Confusion
When choosing between candidates, NEVER mix candidates from different layers. If the user defines a selection pool, score ONLY within that pool. Existing/baseline options inform strategy but must NOT appear as candidates. Before scoring: list the candidate pool, verify every candidate belongs to defined scope.

### E2: Scaffolding vs Identity Lock
When using existing infrastructure as temporary scaffolding, ALWAYS declare it as temporary. Label every scaffolding decision with: (1) what it scaffolds, (2) when it gets replaced, (3) final evaluation criteria (which must NOT reference the scaffold).

### E3: Layer Flattening
When a task has multiple distinct layers (selection, implementation, evaluation, identity), NEVER collapse them into one decision. Enumerate layers. Make one decision per layer. Cross-reference only AFTER each layer has its own answer.

### E4: WordPress REST API — Content Destruction
When modifying WordPress pages/posts via REST API, ALWAYS use `content.raw` (with `?context=edit`), NEVER `content.rendered`. Pushing rendered HTML back destroys all block editor structure irreversibly. For meta-only changes (Yoast), send ONLY the `meta` field — do NOT include `content`.

---

## PART F — SLEEPY: FRONTEND/WEB [DORMANT]

> **ACTIVATION:** React, Next.js, Vue, Svelte, CSS, UI, component, design, layout, landing page, web app, frontend, Tailwind, shadcn.
> When no trigger is present, skip entirely. Zero cost when dormant.

When active, use 21st.dev MCP tools: `21st_magic_component_builder`, `21st_magic_component_inspiration`, `21st_magic_component_refiner`, `logo_search`. Prefer 21st.dev over manual CSS scaffolding. After task completes, return to dormant.

---

## PART G — SLEEPY: AUTORESEARCH ENGINE [DORMANT]

> **ACTIVATION:** /autoresearch, "competitive research", "market intelligence", "monitor competitors", "what's new in [domain]"
> Runs 2x/day via scheduler. Manual trigger available. Zero session cost when dormant.

Autonomous competitive intelligence: RSS feed monitoring, YouTube channel tracking, cross-project signal relay with relevance scoring. Scheduled execution (not session-exit) eliminates trigger flood. Signals scored 0.0-1.0 with 6-hour dedup window.

**Setup:** `python modules/autoresearch/setup_schedule.py`
**Config:** `modules/autoresearch/config.json` (projects, feeds, channels, thresholds)
**Manual run:** `python modules/autoresearch/nightcrawler.py`

---

## PART H — SLEEPY: REINFORCED TOKEN OPTIMIZATION [DORMANT]

> **ACTIVATION:** "deep optimize", "lint CLAUDE.md", "find waste", "cross-project dedup", "estimate cost", "compress ExecutionOS", "prompt patterns"
> Extends C1-C7 with project-wide analysis tools. Zero cost when dormant.

| Tool | Command | What it does |
|------|---------|-------------|
| H1 | `python modules/token-optimizer/executionos_compressor.py <file>` | Score sections for universality, generate tiered structure |
| H2 | `python modules/token-optimizer/claudemd_linter.py` | Enforce <1500 word limit across all project CLAUDE.md files |
| H3 | `python modules/token-optimizer/cross_project_dedup.py` | Find duplicate rules across CLAUDE.md files (SequenceMatcher >=0.8) |
| H4 | `node modules/token-optimizer/plugin_waste_detector.js` | Find enabled but unused plugins, estimate waste |
| H5 | `python modules/token-optimizer/prompt_pattern_optimizer.py` | N-gram analysis of repeated instruction patterns |
| H6 | `python modules/token-optimizer/session_cost_estimator.py --tier <1-5>` | Predict session token cost before executing |

---

## PART I — SLEEPY: EXECUTIONOS LITE [DORMANT]

> **ACTIVATION:** "load ExecutionOS", "execution framework", "full governance", "domain overlay", "forensic mode"
> Tiered loader: core always available, deeper sections load on demand by execution depth.

Distilled from ExecutionOS v20 (16KB/365 lines -> 3KB/80 lines core). Full 25 constitutional rules and 20 phases preserved across tiers.

| Depth | Loads | Est. Tokens |
|-------|-------|-------------|
| LIGHT | core.md only | ~1000 |
| STANDARD | + phases-0-4, phases-5-10 | ~2000 |
| DEEP | + overlays/{domain}.md, phases-11-15 | ~3000 |
| FORENSIC | + phases-16-20, artifacts.md | ~4500 |

**Core:** `modules/executionos-lite/core.md`
**Migrate:** `python modules/executionos-lite/migrate.py <full-executionos.md> --verify`
**Overlays:** minecraft, python, typescript, seo, product, live-ops

---

## Quick Reference

| Trigger | What It Does | Part |
|---------|-------------|------|
| "token audit" | Rank all sources by token cost | C1 |
| "compress this" | Rewrite instructions shorter | C2 |
| "dedup check" | Find overlapping rules | C3 |
| "create digest" | Extract actionable rules from large docs | C4 |
| "trim descriptions" | Enforce <=15 token descriptions | C5 |
| "sleepy audit" | Check always-loaded vs on-demand ratio | C6 |
| "full optimization" | Run complete C1-C7 pipeline | C7 |
| "PRD version" | Check/update PRD after changes | C8 |
| /autoresearch | Run competitive intelligence cycle | G |
| "deep optimize" | Project-wide token analysis tools | H |
| "lint CLAUDE.md" | Enforce word limits across projects | H2 |
| "find waste" | Detect unused plugins | H4 |
| "estimate cost" | Predict session token usage | H6 |
| "load ExecutionOS" | Activate tiered execution framework | I |

Parts A, B, D, E are always active. C activates on trigger. F, G, H, I are sleepy (dormant until needed).
