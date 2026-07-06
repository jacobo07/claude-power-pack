# Plan Mode → Execution Mode: The Architecture of Phased Autonomy in AI Coding Agents

## Executive Summary

The transition from **Plan Mode** to **Execution Mode** has emerged as the dominant control architecture for agentic coding tools in 2025–2026. Rather than letting a model interleave reasoning and irreversible action, the leading agents (OpenAI Codex CLI, Claude Code, Devin, Cline, Windsurf, Cursor) split the work into two discrete regimes: a **read-only planning phase** that gathers context and surfaces a reviewable proposal, and an **execution phase** that mutates state under tighter guardrails. This separation is not a cosmetic UX choice — it rests on a classical AI-planning foundation (HTN task decomposition), is backed by empirical SWE-Bench evidence that per-step execution failures compound to degrade multi-step outcomes, and is increasingly enforced at the *system level* (hard-blocked write tools, cryptographic approval gates) rather than via advisory prompting.

This report synthesizes the current state of the pattern across vendors, the theoretical and empirical basis, the concrete workflow pipelines, the enforcement mechanisms, and the governance layers being built on top of it.

---

## 1. The Cross-Vendor Pattern

The Plan/Execute split is now a convergent design across essentially every major agentic coding tool. The implementations differ in granularity and enforcement, but the conceptual boundary — **decompose before you mutate** — is identical.

| Tool | Modes / Mechanism | Planning constraint | Transition trigger |
|------|-------------------|---------------------|--------------------|
| **OpenAI Codex CLI** | Three modes: **Plan** (read-only, clarifying questions ≤4 rounds), **Pair** (per-action approval), **Execute** (autonomous) | Read-only enforced **at prompt level only — no runtime sandbox** | `Shift+Tab` cycle or `/plan` |
| **Claude Code** | **Plan Mode** (system-level read-only) → Normal / Auto-accept | **Hard-blocked** write tools; OS/tool-level enforcement | `Shift+Tab` (Normal→Plan→Auto-accept), `/plan`, NL directive, or Auto Plan Mode setting |
| **Devin AI** | Explicit `planning` vs `standard` modes | Bounded by `<suggest_plan/>` command requiring **user approval** | User approves suggested plan |
| **VSCode Agent** | Implicit transition | Context-gathering phase implicitly precedes action | Automatic, context-driven |
| **Cline** | **Plan & Act** modes | Editing **disabled** during planning | Mode toggle |
| **Windsurf** | **Plan & Act** modes | Editing **disabled** during planning | Mode toggle |

### Codex CLI specifics

- Plan mode is **on by default from v0.96+**. In v0.93–0.95 it required setting `collaboration_modes=true`.
- The read-only constraint is **prompt-level only** — there is no runtime sandbox enforcing it, an important security distinction from Claude Code's hard block.
- Planning depth is independently tunable: the `plan_mode_reasoning_effort` config key (`none|minimal|low|medium|high|xhigh`, default `medium`) sets planning depth **separately** from `model_reasoning_effort`. Codex plan mode runs on **gpt-5.3-codex**.

### Claude Code specifics

- Plan Mode is a **system-level enforced read-only state**, not advisory prompt-engineering. Write tools (`Edit`, `MultiEdit`, `Write`, `Bash`) are **hard-blocked**; read tools (`Read`, `LS`, `Glob`, `Grep`, `WebSearch`, `WebFetch`, `TodoRead`, `TodoWrite`) remain available.
- The **Auto Plan Mode** setting starts *every* session in Plan Mode — explicitly recommended for teams and production `main` branches.
- **Known failure mode:** Claude can *silently exit* Plan Mode mid-session during long conversations, requiring manual re-activation. This is the principal reliability gap in the enforcement model.

---

## 2. Theoretical Foundation: Why Separate Planning from Execution

The plan/execute separation is not an ad-hoc engineering convenience — it recapitulates **classical AI planning** theory.

- The formal basis is **Hierarchical Task Network (HTN) planning**, specifically the **HDDL 2.1 HTN formalism** (Pellier et al., *arXiv:2306.07353*).
- HTN separates **task decomposition** from **action execution** for a principled reason: **interleaving decomposition and execution produces invalid plans**. If an agent commits to a low-level action before the full decomposition is resolved, downstream subtasks can become inconsistent or unreachable.
- This is precisely the pathology that Plan Mode prevents: by forcing a complete, reviewable decomposition *before* any state mutation, the agent avoids committing to an irreversible action that a later-discovered dependency would have forbidden.

The practical corollary is the **Propose-before-Write** discipline: every recommended pipeline forces *all dependencies to be surfaced* before the first edit (see §4).

---

## 3. Empirical Evidence: Execution Errors Compound

A March 2025 arXiv study provides the strongest empirical case for gating execution.

**Study:** *"Beyond Final Code"* — Zhi Chen et al., **arXiv:2503.12374**, last revised 9 Apr 2026.

**Method / scale:**
- Analyzed **3,977 solving-phase trajectories** and **3,931 testing-phase logs**.
- Drawn from **8 top-ranked agents** on **500 SWE-Bench GitHub issues**.

**Key findings:**
- **Python execution errors during issue resolution correlate with LOWER resolution rates and INCREASED reasoning overhead.** Per-step failures don't stay local — they compound to degrade the multi-step outcome.
- **Most prevalent error types:** `ModuleNotFoundError` and `TypeError`.
- **Most debugging-effort-intensive:** `OSError` and `IntegrityError` demanded the most debugging effort to resolve.
- A meta-finding: the study uncovered **3 confirmed bugs in the SWE-Bench platform itself**, affecting benchmark fairness.

**Interpretation:** This is direct evidence that the cost of an execution error is not bounded to the step that produced it. It propagates as additional reasoning overhead and depresses the probability of eventual success. The architectural response — minimize and gate execution actions, validate each before proceeding — is empirically justified, not merely intuitive.

---

## 4. The Execution Model: ReAct and the Validation Loop

### 4.1 The ReAct (Reason + Act) loop

The core execution engine for agentic coding (Claude Code, Cursor, Cline, Aider) is the **ReAct loop**, a four-phase cycle:

> **Observe → Think → Act → Reflect**

- Each sub-task typically takes **3–8 iterations** before lint / type-check / tests pass.
- Runaway loops are capped by guardrails: **max iteration count + token budget**.
- **Diff-boundary enforcement** auto-rolls-back any file modified *outside* the task's pre-defined scope.
- **Sandboxed execution** (no network, scoped writes) plus **human-in-the-loop checkpoints** (auto-approve low-risk; manual review for schema migrations / security) constrain autonomy *at each step* rather than batching all approvals up front.

### 4.2 The validation-loop pattern

A specialized form of ReAct dedicated to closing on a clean build:

1. AI runs `tsc` / ESLint / tests.
2. Parses **structured output**.
3. Self-corrects.
4. Re-runs until clean.

- This loop is **reliably automated only by CLI / agentic tools** (aider, custom LLM-API loops). **Editor copilots (GitHub Copilot, Cursor) remain human-driven** in their iteration — the human still presses the loop.
- A **structured JSON tool-use protocol** makes per-step feedback machine-readable, e.g.:
  ```json
  test_run → { "status": "fail", "passed": 14, "failed": 2, "errors": [ ... ] }
  ```

**Documented risks of the loop without per-step gating:**
- **Infinite / unproductive loops** — fix one error, introduce another.
- **Overly-aggressive fixes** — `any`-casting, disabling ESLint rules, deleting "unused" code.

**Mitigations:**
- Frequent **git commits**.
- **Behavioral tests** beyond type/lint checks (which only assert shape, not behavior).
- **Max-iteration stop criteria**.

### 4.3 The 9-step plan→execute pipeline

The recommended end-to-end workflow:

> **Read → Map → Propose → Review → Approve → Edit → Apply → Verify → Report**

The **Propose** step is the load-bearing one: it forces surfacing *all* dependencies before any write (the HTN principle from §2 in operational form).

**Adoption / pain-point statistics cited:**
- **66%** of developers report AI solutions are "almost right" — subtle bugs that take hours to debug.
- **45%** report debugging AI code takes *longer than writing it themselves*.
- Claude spends **~30–90s researching** before proposing.

**Advanced patterns layered on top:**
- Pair Plan Mode with **`/effort max`** for architecture and security audits.
- **Dual-Claude review** — Session A generates the plan; a *fresh* Session B critiques it, eliminating confirmation bias.
- **Subagent pre-research** — isolated context window for research saves **40%+ input tokens** in the main session.

---

## 5. Multi-Session Persistence: The ExecPlan / PLANS.md Pattern

The interactive TUI plan is **ephemeral** — it disappears at session end. For multi-hour or multi-session tasks this is a fatal gap, so OpenAI's Cookbook prescribes a **persistent on-disk plan**.

**The PLANS.md ExecPlan** (referenced from `AGENTS.md`) with mandatory sections:

| Section | Purpose |
|---------|---------|
| **Purpose** | Why the work exists |
| **Progress** (checkboxes) | Resumable state |
| **Surprises** | Discoveries that invalidated assumptions |
| **Decision Log** | Recorded rationale |
| **Outcomes** | Results so far |
| **Plan of Work** | The decomposition |
| **Concrete Steps** | Executable actions |
| **Validation** | How to confirm done |

- A **self-containment requirement** enables a **novice or subagent to resume** the work cold.
- This approach has driven **single Codex sessions running over 7 hours from one prompt**.

**A Cursor-based replica of the pattern:**
- **Gemini 2.5 Pro Max** (1M context, **edit-tools-disabled**) does the planning.
- **Claude Sonnet 4** does the execution.
- The user types **`go`** to advance through `plan.md` tasks, with **per-task commits**.

This two-model split — a large-context, edit-disabled planner feeding a capable executor — is the manual analogue of Codex's mode-switch within a single agent.

---

## 6. Claude Code's ExitPlanMode Tool (V2)

The mechanism by which Claude Code crosses the plan→execute boundary is the **ExitPlanMode tool** (V2: `ExitPlanModeV2Tool`), which carries several non-obvious rules and capabilities.

**Constraints:**
- It must **NOT** be used for research / information-gathering tasks (searching, reading, understanding a codebase) — **only** for tasks requiring *code implementation* planning.
- In **V2**, the plan is **read from a dedicated plan file on disk** (written via `Write`/`Edit`) rather than passed as a tool parameter. **Calling `ExitPlanMode` before writing the plan file fails.**

**V2 capabilities:**
- **Semantic Permissions** via `allowedPrompts` — the plan can request *action categories* (e.g., "run tests"), which `buildPermissionUpdates` converts into **session rules** on approval. This lets the human pre-authorize classes of action rather than approving each one.
- **Leader-approval mailbox flow** — can set `awaitingLeaderApproval=true` to route the plan to a designated approver.
- **Auto session-naming** — `autoNameSessionFromPlan` / `generateSessionName` names the session from the **first 1000 chars of the plan**.

---

## 7. Portable and Open-Source Enforcement Layers

Beyond vendor-native modes, the ecosystem has produced portable skills and full governance frameworks.

### 7.1 agent-plan-mode-skill (MIT)

*github.com/wildanfadh/agent-plan-mode-skill* — a **single portable `SKILL.md`** that forces *any* AI coding agent into read-only planning mode.

- **Allows:** `Read`, `SELECT`, `git status`/`diff`/`log`, `grep`.
- **Forbids:** file edits, DB writes, commits/pushes, dependency installs, file-rewriting formatters.
- Switches to full implementation **only** on an explicit approval trigger — `'lanjut'`, `'implement'`, or `'approved'` — then follows the approved plan.

### 7.2 Eric J. Ma's safe-autonomy doctrine (2025-11-08)

Draws the autonomy boundary precisely at **state-modification**:

| Auto-approve (non-destructive reads) | Require explicit approval (mutations) | Gray area |
|--------------------------------------|----------------------------------------|-----------|
| `grep`, `find`, read-only `pytest`, `mypy`, `ruff check` (no `--fix`), `gh pr view`, `git log`/`diff`/`show` | `rm`, `mv`, `git commit`, `git push`, `pip add` | `git add` (tolerated — reversible) |

- Paired with **plan mode** (Cursor/Claude), **prescriptive prompts naming the exact pre-approved CLI commands**, and recording corrections to `AGENTS.md`.
- **Cautionary mishap:** the **Comet agentic browser** interpreted "how to archive repo" as a *command* and **archived his LlamaBot repo** — a concrete demonstration of why read/intent must be separated from action.

---

## 8. Governed Workflow: Zero-Trust Phase Orchestration

The most rigorous realization of the pattern is **Governed Workflow** (*github.com/IgnatRozhkoTR/governed-workflow*) — a **zero-trust orchestration layer** for Claude Code shipping as agent definitions, hook scripts, skills, and a **Flask-based admin panel with an MCP server**.

### 8.1 The 7-phase workflow with 4 human gates

| Phase | Gate |
|-------|------|
| 1. Assessment | **Gate 1.4 — Preparation Review** |
| 2. Research | **Gate 2.1 — Plan Review** |
| 3. Planning / Execution | **Gate 3.N.3 — Code Review** |
| 4. Review | **Gate 4.2 — Final Approval** |
| 5. Reflection (5.1/5.2) | auto-advances |
| 6. Delivery | auto-advances |

- The four **USER GATES** generate **cryptographic nonces presentable only via the admin panel UI**, so **the agent cannot self-approve**.
- Phases **5.1 / 5.2 / 6 advance automatically**.

### 8.2 Enforcement mechanics

- **Server-side phase progression** — the server, not the agent, controls advancement.
- **Pre-tool hooks** enforce **per-sub-phase 'must'/'may' file-pattern scope locking at edit time**.
- **Updating the plan auto-revokes plan approval**, forcing re-approval — the plan and its authorization stay coupled.
- **Fail-closed:** if the admin API is unreachable, **all tools are denied**.

### 8.3 The Research Proving phase (1.2) and ReviewGuard

- The **Research Proving phase (1.2)** requires researchers to save findings with **typed proofs**: `code:file:line`, `web:url`, `diff:commit`.
- A separate **Prover agent verifies** each before the workflow advances. **Rejected entries must be re-researched and re-proven** — no unproven claims pass.
- A cross-cutting **ReviewGuard** blocks phase advancement until **all review items** in the single `discussions` table (`scope='review'`, resolution states `open`/`fixed`/`false_positive`/`out_of_scope`) are **user-resolved** — applies to phases 3.N.K, 4.1, and 4.2.

### 8.4 Role separation (16 agents)

- The orchestrator coordinates **16 specialized agent roles** with **strict separation**:
  - **Engineers never write tests; test engineers never write production code.**
  - **Phase 4.0 blind reviewers receive zero implementation context** — eliminating the reviewer's confirmation bias.

### 8.5 Security architecture

- **Admin bearer token:** SHA-256 hash in SQLite `device_settings`, minted **only via CLI** (`python3 admin-panel/backend/app.py auth-token`).
- **Fail-closed pre-tool hooks** deny all tools when the admin API is unreachable.
- **0600 DB permissions.**
- The governed-workflow tree path **blocks `Edit`/`Write`/`Bash` to `localhost:5111`** (the admin endpoint), so the agent can't reach in and rewrite its own governor.
- **`yolo_mode`** bypasses scope/plan checks **but never the user gates or the path block** — the human-approval and self-tamper protections are inviolable even in the escape hatch.

---

## 9. Synthesis: A Spectrum of Enforcement Strength

The pattern can be read as a spectrum from advisory to cryptographically enforced:

| Enforcement tier | Examples | Mechanism | Weakness |
|------------------|----------|-----------|----------|
| **Advisory (prompt-level)** | Codex CLI Plan mode | Model instructed to stay read-only | No runtime sandbox — model can disregard |
| **Tool-level hard block** | Claude Code Plan Mode | Write tools disabled by the harness | Can silently exit mid-session |
| **Portable skill** | agent-plan-mode-skill | `SKILL.md` rules + explicit approval trigger | Relies on agent honoring the skill |
| **Doctrine + prescriptive prompts** | Eric J. Ma's boundary | Human pre-approves named commands | Manual, human-discipline-dependent |
| **Zero-trust orchestration** | Governed Workflow | Server-side gates, cryptographic nonces, fail-closed hooks, self-tamper path block | Operational complexity, admin-panel dependency |

The clear trajectory across 2025–2026 is **rightward on this table** — from "the model promises to behave" toward "the system structurally cannot let it misbehave." The empirical driver (§3) is that execution errors compound; the theoretical driver (§2) is that premature commitment produces invalid plans; and the practical driver (§4) is the 66%/45% pain statistics showing that ungated AI output costs more to debug than it saves.

---

## 10. Key Takeaways

1. **Plan→Execute is a convergent, cross-vendor architecture**, not a single product feature — Codex, Claude Code, Devin, Cline, Windsurf, and Cursor all implement it.
2. **The separation is theoretically grounded** in HTN planning (interleaving decomposition with execution yields invalid plans) and **empirically justified** by SWE-Bench evidence that execution errors compound to lower resolution rates.
3. **Enforcement strength varies sharply** — Codex's plan mode is prompt-level only (no sandbox), while Claude Code hard-blocks write tools and Governed Workflow uses cryptographic, fail-closed, server-side gates.
4. **The execution phase itself is a guarded ReAct/validation loop** — 3–8 iterations per subtask, capped by max-iteration and token budgets, with diff-boundary rollback and structured-JSON test feedback; the loop is only reliably automated by CLI/agentic tools, not editor copilots.
5. **Persistence is the multi-session unlock** — the ephemeral TUI plan must be externalized into a self-contained `PLANS.md` ExecPlan to enable 7-hour single-prompt runs and cold resume by a subagent or novice.
6. **The frontier is governance** — typed proofs (`code:file:line`/`web:url`/`diff:commit`) verified by a Prover agent, blind reviewers with zero implementation context, role separation between production and test authorship, and the rule that **the agent can never self-approve** the gate that authorizes its own execution.

## Sources

- <https://codex.danielvaughan.com/2026/03/27/planning-mode-in-practice/>
- <https://deepwiki.com/ablueocean/system-prompts-and-models-of-ai-tools/2.2-planning-and-execution-modes>
- <https://skywork.ai/blog/agent/plan-mode-vs-agent-mode-understanding-githubs-revolutionary-coding-workflows/>
- <https://carlrannaberg.medium.com/my-current-ai-coding-workflow-f6bdc449df7f>
- <https://dev.to/varun_pratapbhardwaj_b13/separation-of-planning-and-execution-the-key-pattern-for-reliable-ai-coding-agents-5b53>
- <https://codeables.dev/article/which-ai-coding-tools-can-iterate-on-lsp-eslint-tsc-errors>
- <https://arxiv.org/abs/2503.12374>
- <https://medium.com/@gavinbuilds/agentic-coding-workflows-how-ai-agents-autonomously-write-test-and-ship-production-code-5b8e8b60bf38>
- <https://tweag.github.io/agentic-coding-handbook/WORKFLOW_AUTO_VALIDATIONS/>
- <https://arxiv.org/html/2508.11126v1>
- <https://deepwiki.com/windowdotonload/claude-code/4.4-plan-mode-and-exit-plan-mode>
- <https://deepwiki.com/marckrenn/cc-mvp-prompts/5.1-plan-mode>
- <https://claudeai.dev/docs/mechanics/foundation/plan-mode/>
- <https://github.com/gregkonush/claude-system-prompts/blob/main/exit-plan-mode-instructions.md>
- <https://baeseokjae.github.io/posts/claude-code-plan-mode-guide-2026/>
- <https://github.com/IgnatRozhkoTR/governed-workflow>
- <https://github.com/wildanfadh/agent-plan-mode-skill>
- <https://ericmjl.github.io/blog/2025/11/8/safe-ways-to-let-your-coding-agent-work-autonomously/>
- <https://www.nibzard.com/agentic-handbook>
- <https://github.com/IgnatRozhkoTR/governed-workflow/tree/main/>
- <https://code.claude.com/docs/en/workflows>
- <https://www.zingnex.cn/en/forum/thread/governed-workflow-claude-code>

## Run metadata

- **Prompt:** MODO: PLAN MODE → EXECUTION MODE
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 451.5 s
- **Errors during run:** 3
- **Started at:** 2026-06-20T17:55:22Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `extract_learnings: llm-parse: no valid JSON in 3088 chars; head: '{"learnings":["Anthropic\'s \'Auto mode\' for Claude Code (documented at code.claude.com) replaces --dangerously-skip-permissions using two defense layer'; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `fetch_page 'https://www.tim-dennis.com/vibe-coding-lesson/instructor/04-...': page-fetch: https://www.tim-dennis.com/vibe-coding-lesson/instructor/04-validation.html: HTTP Error 404: Not Found`
- `fetch_page 'https://mcpmarket.com/server/governed-workflow...': page-fetch: https://mcpmarket.com/server/governed-workflow: HTTP Error 429: Too Many Requests`

</details>
