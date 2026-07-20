# PP Activation Audit — 2026-07-20

## FASE 0 — ACTIVATION REALITY AUDIT (evidence)

### A. Activation mechanisms that exist

| # | Mechanism | Where | What it actually does | Reaches a non-PP repo? |
|---|---|---|---|---|
| 1 | Skill auto-invoke | `~/.claude/skills/claude-power-pack/SKILL.md:3` | The model reads the `description` string and decides. Current string: `"Universal AI execution framework — tiered loading, zero-issue delivery, self-healing"` | Yes, but the string carries **zero task vocabulary** |
| 2 | `Auto-Invoke: On STANDARD+ tasks` | `~/.claude/CLAUDE.md`, ExecutionOS Lite section | One line, ~55 lines deep, no definition of who assigns the tier | Yes, but unenforceable |
| 3 | SessionStart hooks (8) | `settings.json:288-360` | 7 Owner hooks + `session_start_hub.js`. Hub emits `additionalContext` **only** for a restart-resume marker < 5 min old | Runs everywhere, **says nothing about PP** |
| 4 | UserPromptSubmit chain (4) | `hook-dispatcher.js:240-249` | correction-guard, prd-keyword-sentinel, d2a_gate, `jit_skill_loader.py` | Runs everywhere |
| 5 | `jit_skill_loader.py` TRIGGERS | `tools/jit_skill_loader.py:71+` | Regex set is **Apollo/GraphQL only** (graphql_ops, apollo_client, apollo_server, federation, rover, connectors…) + "ACTIVE PROJECT SPEC" injection | Injects nothing PP-related unless cwd is the PP repo |
| 6 | PreToolUse/PostToolUse/Stop hooks | `settings.json` | ~25 PP hooks (gates, CEPS, CDIO advisory, KG sync, mistake-ingest) | Fire everywhere — but all are **guards**, never **offers** |

Observed this session: the JIT loader injected `vault/specs/deep-research-agent.md` (20,569 B) — because cwd **is** the PP repo. In TUA-X that path resolves to nothing.

### B. Per-project reality (30 dirs under `Cursor Projects`, scripted check)

- `CLAUDE.md` present: **26** projects (20 TUA-X worktrees, 4 InfinityOps, Jacobo, GEO-audit, Club Náutico, LaptOps)
- `CLAUDE.md` referencing PP (`power-pack` / `Power Pack` / `cpp-`): **1** — `LaptOps` only
- TUA-X: 0/20. InfinityOps: 0/4. KobiiCraft/KobiiSpy/CostaLuz/AKOS/NexumOps: no `CLAUDE.md` at all.

**1/30 = 3%.**

### C. Root cause

**PP's trigger vocabulary lives inside the skill it is supposed to trigger.**

`SKILL.md:27-39` holds a rich sleepy-trigger table — ~14 rows, hundreds of keywords (React, dashboard, token audit, VPS, knowledge graph, destilar, subagent routing…). Every one of those is only readable **after** the skill is invoked. The one string the model sees *before* deciding names what PP **is**, not **when to use it**.

Compare the skills that do fire in this same session listing:
- `frontend-design` — "Use this skill when the user asks to build web components, pages, artifacts… websites, landing pages, dashboards, React components…"
- `ui-ux-pro-max` — enumerates Actions / Projects / Elements / Styles / Topics
- `agent-reach` — "MUST USE when user wants to research/search/look up…"

They win because their description is a **trigger list**. PP's is a **tagline**.

### Gap classification

| Gap | Status | Evidence |
|---|---|---|
| **A** — skill exists, nobody invokes it | **CONFIRMED — dominant** | `SKILL.md:3` description carries no task nouns/verbs |
| **B** — JIT loader doesn't detect repo as PP candidate | **CONFIRMED** | `jit_skill_loader.py` TRIGGERS are Apollo/GraphQL-only |
| **C** — session start injects nothing in non-PP repos | **CONFIRMED** | `session_start_hub.js` emits context only on restart marker |
| **D** — tier never reaches STANDARD+ | **CONFIRMED (secondary)** | tier is self-assessed, undefined, buried |
| **E** — Owner doesn't know PP has relevant capability | **CONFIRMED (consequence of A/C)** | 40+ modules, 100+ commands, no surface anywhere but inside PP |

Gaps C/D/E are downstream of A. **Fixing A alone likely moves activation more than everything else combined**, and it is a one-file edit.

---

## FASE 1 — Fixes, ordered by ROI

### F1 (quick win, ~10 min) — Rewrite `SKILL.md` frontmatter description
Convert the tagline into a trigger list, hoisting the sleepy table's vocabulary into the one string the model reads before deciding. Target shape:

> Use when a task involves architecture decisions, multi-file features, debugging a recurring failure, QA/done-gates, deploys, dataset or knowledge-vault work, token/context audits, governance or hard rules, session recovery, or infra/VPS operations — in ANY repo. Also on: "is this done", "audit this", "why does this keep breaking", `/cpp-*`, `/ultra`, `/liveness`, `/kclear`. Provides tiered execution doctrine, zero-issue gates, CEPS error prevention, and 100+ commands.

Keep it a trigger list, not prose. No other file changes.

### F2 (~20 min) — `~/.claude/CLAUDE.md`: replace the implicit tier with explicit criteria
Replace `Auto-Invoke: On STANDARD+ tasks` with a short IF/THEN table (task shape → PP capability), so activation stops depending on per-session tier judgement. Net line count roughly neutral (the 40 k char ceiling is respected).

### F3 (~30 min) — Repo-side references, 3 projects
Add a 3–5 line PP block to `TUA-X/CLAUDE.md`, `InfinityOps/CLAUDE.md`, `GEO-audit/CLAUDE.md` naming the 2–3 PP capabilities actually relevant to each repo. Not a copy of the global doctrine — a pointer.

### F4 (~45 min) — `jit_skill_loader.py`: a PP-capability trigger family
Add a low-priority TRIGGERS entry (a `pp_capability` family) that matches task-shaped prompts (audit / done / deploy / recurring failure / dataset / vault) and injects a **compact capability card** (~80 tok discovery tier, the existing cheap tier), not a full SKILL.md. Rules:
- Priority last → yields to Apollo under the 40 KB breaker.
- Session-dedupe already exists → once per session maximum.
- Fail-open on any error.
- Silent when cwd is the PP repo (the active-project-spec path already covers it).

**Explicitly rejected**: injecting on *every* prompt. That is the spam failure mode the constraints forbid.

### F5 — session_start_hub capability note
**Deferred, pending F1–F4 measurement.** If F1 lands, a session-start injection is redundant noise. Revisit only if activation is still low after a week.

Micro-commit per fix, pathspec-scoped.

---

## FASE 2 — Tests: `tools/test_pp_activation.py`

- `V-PP-DESC-TRIGGERS` — `SKILL.md` description contains ≥8 distinct task-trigger terms (not a tagline)
- `V-PP-AUTOINVOKE-DEFINED` — global `CLAUDE.md` holds explicit IF/THEN activation criteria
- `V-PP-SKILL-DISCOVERABLE` — `~/.claude/skills/claude-power-pack/SKILL.md` exists with valid frontmatter
- `V-PP-SESSION-START` — `session_start_hub.js` present and wired in `settings.json`
- `V-PP-JIT-PP-FAMILY` — the `pp_capability` trigger family exists, is lowest priority, and is fail-open
- `V-PP-REPOS-CONFIGURED` — ≥3 active repos' `CLAUDE.md` reference PP
- `V-BASELINE` — existing suite, no regression

Done-gate: all ×3 hermetic (guard against the non-hermetic time/global-write class already catalogued).

---

## UKDL

**T-PP-SILENT-SKILL-001** — A skill whose `description` names what it *is* rather than *when to use it* will not be auto-invoked, however rich its internals. PP carries a ~14-row trigger table at `SKILL.md:27-39` that is unreadable until after invocation: the trigger vocabulary is inside the box it is meant to open. Measured consequence: 1/30 of the Owner's repos reference PP.

**PR-PP-ACTIVATION-EXPLICIT-001** — For any capability that must activate in real projects, the activation criterion belongs in the string the model reads *before* deciding — the skill `description` and an IF/THEN table in `CLAUDE.md`. A criterion stated only inside the artifact it gates ("the agent should know") is not a criterion; it is a wish without enforcement. Corollary: activation is measurable — count the repos that reference it, not the modules that exist.

## DONE-GATE
- [ ] Audit report (this file)
- [ ] `SKILL.md` description = trigger list
- [ ] Explicit criteria in global `CLAUDE.md`
- [ ] ≥3 repos referencing PP
- [ ] `pp_capability` JIT family, fail-open, dedupe-once, lowest priority
- [ ] `test_pp_activation.py` ×3 hermetic
- [ ] REMOTE_DELTA = 0 0
