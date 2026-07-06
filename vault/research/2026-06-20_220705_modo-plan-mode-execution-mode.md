# From Plan Mode to Execution Mode: The Claude Code Agentic Harness in 2026

## Executive Summary

"PLAN MODE → EXECUTION MODE" names the single highest-leverage reliability pattern in modern agentic coding: a hard separation between **proposing** what to do and **committing** to doing it. As of mid-2026, this pattern is no longer a manual discipline layered on top of a chat agent — it is encoded into the runtime of Claude Code through three first-class execution modes, a classifier-gated auto-execution path, an isolated read-only exploration agent, and (since May 2026) dynamically generated multi-agent workflows. This report synthesizes the current state of that machinery, the empirical case for it, the doctrine behind a well-formed agentic harness, and the failure modes the pattern exists to suppress.

The throughline: **the model only ever drafts typed proposals; deterministic application code decides whether they execute.** Everything below is an elaboration of that one architectural commitment.

---

## 1. The Three Execution Modes

Claude Code exposes three distinct execution postures. They differ not in capability but in *where the approval boundary sits* between the model proposing an action and that action mutating the world.

| Mode | How to enter | Approval boundary | Best fit |
|---|---|---|---|
| **Edit mode (direct execution)** | Default | Per-action, interactive | Well-scoped single/few-file tasks with one obvious approach |
| **Edit mode w/ auto-approval (Auto mode)** | `claude --enable-auto-mode` then Shift+Tab | A safety **classifier** blocks destructive actions, allows routine edits/test runs | Iterative work where most actions are routine but some are dangerous |
| **Plan mode** | Shift+Tab twice, or `/plan` | Total — Claude investigates and proposes, mutating **no files** until approved | Multi-file/architectural tasks with multiple valid approaches |

### The decision rule

The three modes map cleanly onto task topology:

- **Direct execution** when the task is well-scoped, touches one or a few files, and has an obvious approach.
- **Plan mode** when the task is multi-file or architectural and admits multiple valid approaches. Canonical examples: a monolith→microservices decomposition, a `moment.js`→`dayjs` migration, or a language port.
- **Explore-then-plan** when the codebase state itself is unknown — you must first understand before you can even choose an approach.

The progression direct → auto → plan is a progression in *uncertainty*: the less obvious the path and the more files at stake, the further up the approval-boundary you push.

---

## 2. The Explore Subagent: Cheap Understanding

Plan mode is only as good as the context feeding it, and context is the scarcest resource in a long agentic session. The **Explore subagent** solves this directly.

- **What it is:** a specialized **read-only** agent restricted to `Read`, `Grep`, and `Glob`. It cannot mutate anything.
- **Why it matters:** it runs its investigation in an **isolated context** and returns only a *summary* to the main conversation, so the cost of understanding is paid in the subagent's throwaway window rather than the main window.
- **The headline number:** investigating 20 files consumes roughly **~5% of main context with Explore vs ~60% without** — leaving **95% vs 40%** of the window available for the planning phase that follows.

Explore can be triggered two ways: **automatically**, when Claude judges a question to be a broad investigation; or **forced**, via a skill declaring `context: fork` and `agent: Explore`.

### The power pattern

These pieces chain into a single canonical workflow:

> **Explore (understand) → Plan mode (design) → Direct/Auto execution (implement)**

Explore loads grounded context cheaply; plan mode converts that context into a reviewed design; direct or auto execution carries it out. Each stage hands a clean, bounded artifact to the next.

---

## 3. Dynamic Workflows: Plan→Execute at Scale (May 28, 2026)

On **May 28, 2026**, Anthropic launched **dynamic workflows** in Claude Code — the plan→execute pattern scaled from a single agent to a fleet.

- **Availability (GA):** CLI, Desktop, and the VS Code extension for **Pro / Max / Team / Enterprise**, plus the API, **Amazon Bedrock**, **Vertex AI**, and **Microsoft Foundry**.
- **Mechanism:** Claude dynamically *writes its own orchestration scripts* that run **tens-to-hundreds of parallel subagents** with **adversarial verification** (agents checking each other's work).
- **How to enable:** the `ultracode` setting (which sets effort to `xhigh`), or simply asking Claude to "create a workflow."
- **Guardrails:** the **first trigger requires explicit user confirmation**, and the mode consumes substantially more tokens than a normal session.

### The flagship demonstration

The proof point was **Jarred Sumner's rewrite of Bun from Zig to Rust**:

- **99.8%** of the existing test suite passing
- **~750,000 lines** of Rust produced
- **11 days** from first commit to merge
- **two reviewers per file** (adversarial verification at scale)

This is plan→execute taken to its structural limit: the orchestrator plans the decomposition, hundreds of subagents execute in parallel, and adversarial reviewers gate each unit — the same draft/commit separation, replicated across a swarm.

---

## 4. Auto Mode: The Classifier That Guards Execution

Auto mode is the runtime embodiment of "execute the routine, pause on the dangerous." It is the bridge between plan and execution where most real iteration happens.

### Enablement

- **CLI flag:** `--permission-mode auto`
- **Env / settings:** `CLAUDE_CODE_ENABLE_AUTO_MODE` / `autoMode.environment`
- **Availability:** all Anthropic API users; **admin enablement required** on Bedrock, Vertex AI, Microsoft Foundry, and Team/Enterprise plans.

### The 4-tier precedence classifier

Every tool call routes through a classifier with a strict precedence ladder:

| Tier | Behavior | Examples |
|---|---|---|
| **`hard_deny`** | Unconditional block, cannot be overridden | Data exfiltration, auto-mode bypass |
| **`soft_deny`** | Blocks destructive actions, **but overridable** by user intent or an `allow` | Force push, `curl \| bash`, prod deploys |
| **`allow`** | Explicit exceptions | (Project-defined safe operations) |
| **Explicit user intent** | The operator's stated will | (Resolves soft denials) |

### Configuration semantics (subtle and important)

- The classifier reads **CLAUDE.md** plus `autoMode` blocks from `~/.claude/settings.json`, `.claude/settings.local.json`, and managed settings.
- Entries are **additive** — developers can *extend* the lists but **cannot remove managed entries**.
- **Critical gotcha:** omitting the literal string **`"$defaults"`** from any array **replaces the entire built-in list** rather than appending to it. Always include `"$defaults"` unless you intend a full override.
- **Inspection commands:** `claude auto-mode defaults | config | critique`.
- **`permissions.deny` in managed settings runs BEFORE the classifier and cannot be overridden** — it is the true hard floor, independent of the classifier's own `hard_deny` tier.

This layering — managed `permissions.deny` → classifier `hard_deny` → `soft_deny` → `allow` → user intent — is precisely the "deterministic permission check in application code, not the model" doctrine made concrete.

---

## 5. Model, Effort, and the `ultracode` Distinction

The execution layer's power is modulated by model choice and reasoning effort, and the terminology here is easy to conflate.

### Models (Claude Code 2.1.x, validated against 2.1.162)

- **Default: Opus 4.8** (requires v2.1.154+)
- Also available: **Sonnet 4.6**, **Haiku 4.5**
- Aliases: `opus`, `sonnet`, `haiku`, `opusplan`, `opus[1m]`, `sonnet[1m]`, `default`, `best`

### Reasoning effort — 6 levels

Set via `/effort` or `CLAUDE_CODE_EFFORT_LEVEL` (the env var **overrides all**):

| Level | Notes |
|---|---|
| low | |
| medium | |
| **high** | **Opus 4.8 default** |
| **xhigh** | **Opus 4.7 default**; Opus 4.8 + 4.7 only |
| **max** | No token cap; **session-only** |

### Three terms that are NOT the same thing

- **`/effort ultracode`** — a Claude Code **setting, not a model level**. It sends `xhigh` *per message* and orchestrates a dynamic workflow of background agents for substantive tasks. **Session-only.** This is the lever for §3's dynamic workflows.
- **`ultrathink`** — an **in-prompt keyword** that adds one-turn deep reasoning.
- **Legacy `think` / `think hard` / `think harder`** — **no longer special keywords**; they have no effect.

The practical mapping: use `ultracode` when you want the *swarm*; use `ultrathink` when you want *this single turn* to reason harder.

---

## 6. Keybindings: Driving the Mode Transitions

Mode-cycling is the muscle memory of the plan→execute workflow, so keybinding hygiene matters. Customizable keybindings require **Claude Code v2.1.18+**.

- **`/keybindings`** opens `~/.claude/keybindings.json`, **hot-reloaded** on save.
- **25+ contexts** (Chat, Global, Confirmation, Doctor, etc.); actions use `namespace:action` form.
- **Reserved / un-rebindable:** Ctrl+C (interrupt), Ctrl+D (exit), Ctrl+M (= Enter), Caps Lock.

Notable defaults and recent changes:

| Action | Binding | Notes |
|---|---|---|
| `chat:cycleMode` | **Shift+Tab** | The mode-cycle key; falls back to **Meta+M on Windows** without VT mode (Node <24.2.0 / <22.17.0) |
| `chat:fastMode` | Meta+O | |
| `chat:killAgents` | Ctrl+X Ctrl+K | |
| `task:background` | **Ctrl+X Ctrl+B** | Added v2.1.169 as a chord, to avoid the tmux prefix conflict |
| `permission:toggleDebug` | (Ctrl+D removed) | v2.1.146 removed Ctrl+D here — it shadowed `app:exit` |

The Shift+Tab fallback to Meta+M on older Node/Windows is worth flagging: the primary gesture for *entering plan mode* is exactly the one that silently rebinds on certain Windows configurations.

---

## 7. The Leveled Agentic Harness: Draft vs Commit

Underneath the product features sits a general architectural pattern, and it is the conceptual core of everything above.

> **The model only proposes typed tool calls. Application code — not the model — validates against schema, runs deterministic permission checks, and either executes or pauses for an approval record stored OUTSIDE the prompt.**

The two phases — **draft** and **commit** — are kept structurally separate. This is what makes "plan mode" trustworthy: the proposal genuinely cannot mutate state, because mutation is gated by code the model does not control.

### Risk-class routing

The harness splits tool calls by **risk class** into distinct permission paths:

| Risk class | Path |
|---|---|
| **Reads** (scoped) | Autonomous |
| **Drafts** (labeled) | Autonomous |
| **External writes** | Approval record required |
| **Deploys** | Approval record required |
| **Destructive actions** | Approval record required |
| **Privileged access** | Approval record required |
| **Financial operations** | Approval record required |

The approval record lives **outside the model** — it is a deterministic artifact in application state, not a token in the prompt the model could hallucinate or rationalize past.

### The canonical harness loop

```
user/task
  → context builder
  → model call
  → typed tool call
  → schema validation
  → permission check
  → execution OR approval pause
  → structured observation
  → next step
```

### Banned tools

The doctrine **bans generic broad tools** — `send_message`, `write_database`, `run_command`, `execute_anything` — in favor of **narrow typed tools** with schema validation and structured results. A broad tool defeats the entire risk-class split: if the model can call `run_command`, every risk class collapses into one ungated path.

### The reference implementation

This doctrine is codified in **DenisSergeevitch/agents-best-practices**:

- Provider-neutral, **MIT-licensed Agent Skill**
- **~1,985–1,990 GitHub stars**, 171 forks
- Scanned **PASSED** by SkillsLLM (2026-05-17), updated 2026-06-20
- Install: `npx skills add DenisSergeevitch/agents-best-practices -g` — into **Codex** (`~/.codex/skills/`) or **Claude Code** (`~/.claude/skills/`)
- Core contract file: `references/tools-and-permissions.md` (typed tools, risk classes, approvals)

Its worked example — a **Level 2 launch gate** — makes the abstraction concrete:

- **20 historical accounts** traced
- Trace review completed
- **No unapproved external sends**
- **≥80% human acceptance** of draft actions

These are the empirical thresholds at which a draft-producing agent earns expanded autonomy.

---

## 8. The Empirical Case for Plan-Then-Execute

Plan-then-execute is described as **the single highest-impact reliability pattern** for non-trivial agent tasks — defined as anything touching **>2–3 files**, architectural changes, or refactors.

### The numbers

- Teams adopting it report **40–60% fewer 'start over' moments**.
- Planning adds **<10% of total cost** — roughly **$0.03–0.10 to plan vs $0.10–0.80 to execute**.
- The economics are decisive: a cheap plan that prevents even one expensive false-start pays for itself many times over.

### The hard 5 steps

The workflow is not a vibe — it is five mandatory steps:

1. **Plan** — explicitly instruct *"do not write code yet."*
2. **Review** — read the plan.
3. **Approve.**
4. **Execute step-by-step** — **commit after each step.**
5. **Checkpoint** — verify the result against the plan.

The per-step commit in step 4 is what makes the execution phase reversible at fine granularity; the checkpoint in step 5 is what catches drift between intent and outcome.

---

## 9. The Bias the Pattern Exists to Suppress

There is a documented, specific failure mode that motivates the grounding discipline inside plan mode: agents **'invent instead of reuse.'**

- Agents default to **pattern completion from training data** rather than discovering existing code in the repository.
- The measured result: **8× more duplicated code blocks** than human-written code.

### Mitigations

- **Require evidence** — file paths, line numbers, actual values — to *force grounding*. (This is why the Explore subagent's grep/glob-based investigation matters: it produces citations, not recollections.)
- **Use clarifying questions as a context-loading tool** before implementation, not as a formality after.
- **Review the plan's REASONING, not just its output** — ask: *was the grounding thorough? were security / GDPR / edge cases considered?*

### Reversibility infrastructure

Two mechanisms make execution safely reversible:

- **Checkpointing** — **ESC-ESC in Claude Code** saves *both* conversation context and code state.
- **Git worktrees** — `git worktree add ../proj-feature branch` enables conflict-free **parallel agent instances**, each in its own working tree.

Worktrees are the practical substrate for §3's parallel swarms: hundreds of subagents can mutate code simultaneously only because each operates in an isolated tree that merges cleanly.

---

## 10. Synthesis: One Architecture, Many Surfaces

Every feature in this report is the same idea viewed from a different altitude:

| Surface | The draft/commit separation appears as… |
|---|---|
| **Plan mode** | The model proposes a design; no file mutates until you approve. |
| **Explore subagent** | A read-only agent that *cannot* commit — pure draft-context gathering. |
| **Auto mode classifier** | Deterministic code, not the model, decides which proposals execute. |
| **Dynamic workflows** | The orchestrator drafts a decomposition; adversarial reviewers gate each commit. |
| **Leveled harness doctrine** | Typed proposals + out-of-band approval records, formalized. |
| **Risk-class routing** | The *granularity* of the commit gate, by danger level. |

The transition **PLAN MODE → EXECUTION MODE** is therefore not a toggle between two unrelated states. It is the moment a *validated, grounded, reviewed draft* crosses a *deterministic, code-enforced permission boundary* into reality — at whatever scale, from a single edit to a 750,000-line language port.

### Practical recommendations

1. **Default to Explore-then-plan** for any task touching >2–3 files or any unfamiliar codebase. The context economics (95% vs 40% window remaining) are too good to skip.
2. **Use Auto mode for iteration**, but always retain the literal `"$defaults"` string in `autoMode` arrays — dropping it silently disarms the entire built-in safety list.
3. **Reserve `ultracode` for genuinely large, parallelizable work** (ports, sweeping refactors); budget for substantially higher token spend and confirm the first trigger deliberately.
4. **Commit after every execution step** and lean on ESC-ESC checkpoints + git worktrees so that any "start over" is cheap rather than catastrophic.
5. **Review plan reasoning, not just plan output** — interrogate whether the agent *grounded* (cited real files/lines) or *invented* (pattern-completed from training). This single check is the highest-yield defense against the 8×-duplication bias.

## Sources

- <https://claude.com/blog/introducing-dynamic-workflows-in-claude-code>
- <https://www.anthropiccertifications.com/learn/claude-code-workflows/plan-mode-vs-direct>
- <https://claudeai.dev/docs/mechanics/foundation/plan-mode/>
- <https://cuong.io/blog/2025/07/15-claude-code-best-practices-plan-mode>
- <https://agentfactory.panaversity.org/docs/General-Agents-Foundations/claude-code-teams-cicd/plan-mode-vs-direct-execution>
- <https://code.claude.com/docs/en/auto-mode-config>
- <https://code.claude.com/docs/en/keybindings>
- <https://hidekazu-konishi.com/entry/claude_code_features_settings_reference_2026.html>
- <https://computingforgeeks.com/claude-code-cheat-sheet/>
- <https://github.com/DenisSergeevitch/agents-best-practices>
- <https://www.sashido.io/en/blog/coding-agents-best-practices-plan-test-ship-faster>
- <https://agenticoding.ai/docs/practical-techniques/lesson-7-planning-execution>
- <https://medium.com/@elisheba.t.anderson/building-with-ai-coding-agents-best-practices-for-agent-workflows-be1d7095901b>
- <https://sahaavi.github.io/agentic-playbook/reference/patterns/plan-then-execute.html>
- <https://github.com/DenisSergeevitch/agents-best-practices/blob/main/README.md>
- <https://agentskill.work/en/skills/DenisSergeevitch/agents-best-practices>
- <https://dudarik.com/en/blog/agents-best-practices-mcp/>
- <https://skillsllm.com/skill/agents-best-practices>

_Note: 1 URL(s) also appeared in prior runs of this prompt (not duplicates in current run; see index.json for full history)._

## Run metadata

- **Prompt:** MODO: PLAN MODE → EXECUTION MODE
- **Depth / breadth:** 2 / 3
- **Queries used:** 4 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 332.5 s
- **Errors during run:** 1
- **Started at:** 2026-06-20T20:07:05Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://www.quantizelab.dev/articles/claude-shortcuts-keyboa...': page-fetch: https://www.quantizelab.dev/articles/claude-shortcuts-keyboard-guide-2026: HTTP Error 404: Not Found`

</details>
