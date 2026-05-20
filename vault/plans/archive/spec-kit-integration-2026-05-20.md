# Spec Kit Integration — 2026-05-20

> Integrate Spec-Driven Development (github.com/github/spec-kit) as the
> mandatory PASO -1 of any feature built on top of the Power Pack.

## PASO 0 — Grounding (read-only, completed)

Cloned `github/spec-kit` (96K+ stars, 200+ contributors, latest main) to
`/tmp/spec-kit`. Key structure:

- `templates/commands/` — 7 SDD slash commands (constitution, specify,
  clarify, plan, tasks, implement, analyze) + checklist + taskstoissues.
- `templates/*-template.md` — 5 artifact templates (constitution, spec,
  plan, tasks, checklist).
- `src/specify_cli/` — Python CLI that scaffolds `.specify/` into a
  project + writes integration files for the chosen coding agent.
- Core flow: **Spec → Plan → Tasks → Implement**; constitution starts
  the project, clarify resolves ambiguities mid-spec, analyze does
  cross-artifact consistency before implement.

### 4-column grounding table

| Spec Kit artifact / command | PP equivalent (today) | Gap | Value of absorbing |
|---|---|---|---|
| `/speckit.constitution` | `knowledge_vault/core/*` + global `CLAUDE.md` | Per-project constitution not formalized | Project-scoped governance distinct from global doctrine |
| `/speckit.specify` | `/cpp-prd-parse` (one-shot PRD parser) | One-shot; no iterative spec; no ambiguity surface | Iterative spec refinement with explicit ambiguity markers |
| `/speckit.clarify` | `/ultra` Phase 2 Q&A (in-conversation only) | Ambiguities live in chat, not in an artifact | Structured ambiguity log; one-pass resolution before plan |
| `/speckit.plan` | `/ultra` Phase 1+3 + `/gsd:plan-phase` | Plan exists only in conversation, dies on compaction | Persistent `plan.md` survives compaction and handoff |
| `/speckit.tasks` | `TaskCreate` / `TaskList` (in-session) | Tasks live in harness state, gone after session ends | `tasks.md` decouples task list from session lifecycle |
| `/speckit.implement` | `/ultra` Phase 6 + Auto Mode | Execution one-shot; no artifact-driven resumption | Drives implementation from `tasks.md`; agent resumes mid-flow |
| `/speckit.analyze` | (none — OVO is post-commit) | No cross-artifact drift check BEFORE code | Spec ↔ plan ↔ tasks consistency proof pre-implementation |
| `constitution-template.md` | `apex-completion-standard.md` (global only) | No project-scoped template | Per-project principles as PASO -1 |
| `spec-template.md` | (none) | Standard shape (P1/P2/P3 stories, FR-###, SC-###, ambiguity markers) missing | Universal artifact shape; reduces structural variance |
| `plan-template.md`, `tasks-template.md` | `/ultra` phases (transient) | Not persisted to disk | Persistence + handoff support across sessions |

### Net value absorbed

1. **PASO -1 spec-first discipline** — no code without an approved spec.
2. **Per-project constitution** — currently only global; SDD adds a project-scoped layer the Power Pack honors automatically.
3. **Persistent artifacts** — survives compaction, handoff, multi-pane work. Conversation transcripts no longer carry the load alone.
4. **Cross-artifact `/analyze`** — drift detection before implement, complementing OVO post-commit verdict.
5. **Structured ambiguity markers** — typed log replaces ad-hoc Q&A back-and-forth that currently bleeds tokens.

## Plan

### C1 — 7 PP slash commands wrapping the SDD workflow

For each of the 7 Spec Kit commands, ship a Power-Pack-flavoured wrapper at `commands/speckit-{constitution,spec,plan,tasks,implement,clarify,analyze}.md`. Each command:

- Mirrors the upstream Spec Kit process (recognizable to any SDD user).
- Layers PP context: Reality Contract, done-gates, micro-commit discipline, OVO push gate, Intent-Lock semantics.
- Points at `vault/templates/speckit/<artifact>.md.template` (C2) for the structural shape it produces.
- Names the next command in the chain so the Owner can skim a single file and know where to go next.

Gate: each command produces its artifact in under 60 s without preventable back-and-forth, on the first run of a stranger.
Commit: `feat(speckit): 7 PP commands — full SDD workflow integrated`.

### C2 — PP-flavoured templates in `vault/templates/speckit/`

`constitution.md.template`, `spec.md.template`, `plan.md.template`, `tasks.md.template` — each starts from the upstream Spec Kit template and pre-embeds the Power Pack contract:

- Reality Contract block (no fabricated numbers, no scaffold illusion).
- Done-Gate skeleton showing the shape of evidence-of-completion criteria the author must fill in.
- Micro-commit discipline (one commit per logical step).
- Cross-link to the relevant PP standard (`apex-completion-standard.md`, `programmatic-budget-standard.md`, etc.).

Gate: an agent picking up an empty project can produce all four artifacts using only the templates, with zero PP-internal knowledge.
Commit: `feat(speckit-templates): SDD artifacts with PP standards baked in`.

### C3 — JIT auto-inject the active spec

`tools/jit_skill_loader.py` gains a project-aware injection path: when a `.specify/spec.md` OR `vault/specs/<feature>.md` exists in the project cwd, the loader injects it as a priority context block before any Apollo trigger module. The injection is size-capped (same 40 KB BL-0068 circuit breaker as the trigger modules) and counts against the same budget.

Gate: `tools/measure_compression.py --programmatic` exit 0 unchanged (the spec is additional priority context, not a replacement for the Apollo task profiles). New row in the umbrella reports spec auto-injection status.
Commit: `feat(jit-spec): auto-inject active spec in context`.

### C4 — Spec-Driven Gate in `apex-completion-standard.md`

New section "Spec-Driven Gate (sealed 2026-05-20)" added to the global apex standard (and mirrored to PP). Codifies:

- Every feature post-2026-05-20 starts with an approved `spec.md`.
- No agent writes implementation code without a `tasks.md` that traces to a parent spec.
- The PASO -1 (constitution + spec) precedes the existing PASO 0 (Apex onboarding) which precedes the existing 4-clause S+ Criteria.
- Cross-link to the seven `speckit-*.md` PP commands.

Gate: global ↔ PP byte-identical (verify_global_mirrors apex pair OK).
Commit: `standard(speckit): Spec-Driven Gate as PASO -1 in apex standard`.

### VERIFICACIÓN FINAL

A fresh project with zero PP context:

1. `/speckit-constitution` → produces `constitution.md`.
2. `/speckit-spec "<feature description>"` → produces `spec.md` with structured ambiguity markers where appropriate.
3. `/speckit-clarify` → resolves the ambiguities; `spec.md` updated.
4. `/speckit-plan` → produces `plan.md` aligned with spec.
5. `/speckit-tasks` → produces `tasks.md` aligned with plan.
6. Agent runs `/speckit-implement`; completes the feature with **zero preventable clarifications** (any clarification needed during implement = template gap, iterate the template, not the spec).

Gate: real run on a synthetic feature; transcript shows zero back-and-forth that the spec should have answered. OVO A+ on the spec-kit-integration scope.

## Done-Gate

- `commands/speckit-*.md` × 7 land + each produces its artifact in <60s.
- `vault/templates/speckit/*.template` × 4 land + agent can start cold.
- `tools/jit_skill_loader.py` auto-injects `.specify/spec.md` when present.
- `apex-completion-standard.md` Spec-Driven Gate section sealed + global/PP mirror byte-identical.
- Synthetic-feature verification shows zero preventable clarifications.
- OVO **A+** on the integration scope.
- `git rev-list` clean post-push.

## Reality Contract enforcement

- Each command emits a REAL end-to-end artifact, never a deferred-work stub.
- Templates pass the slop-detector clean by construction.
- "Zero preventable clarifications" means: on the synthetic verification, the implementing agent does NOT ask a question whose answer is in the spec. Any such question = template gap = iterate.
- Spec ↔ plan ↔ tasks drift is caught by `/speckit-analyze` BEFORE implementation; OVO confirms post-commit.
