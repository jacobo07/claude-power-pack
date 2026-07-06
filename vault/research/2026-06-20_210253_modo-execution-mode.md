# Execution Mode in AI Coding Agents: A Technical Survey

## Scope and Framing

"Execution mode" denotes the operational posture an AI coding agent adopts when it moves from *understanding* a task to *acting* on it — the bundle of tool permissions, approval semantics, and reasoning discipline that governs how an agent reads, writes, and runs commands against a real codebase. This report synthesizes the current state of the art across the major terminal-native agents (Cline, Claude Code, GitHub Copilot CLI, OpenCode), the reasoning architectures underneath them, and the safety machinery that makes high-autonomy execution viable.

The central thesis that emerges from the research: **execution mode is not a single setting but a spectrum of trust**, and mastery consists of *gear-shifting* between postures per-task based on blast radius — not committing to one mode permanently.

---

## 1. The Foundational Shift: From Prompt Engineering to Context Engineering

Anthropic's engineering team frames the entire discipline as an evolution:

| | Prompt Engineering | Context Engineering |
|---|---|---|
| Core question | "What are the *right words*?" | "What is the *optimal set of information* the model should have at every point during execution?" |
| Unit of concern | The instruction string | The full token state across a multi-step run |
| Failure it fights | Ambiguous phrasing | Context degradation over a long run |

Two physical constraints motivate this shift:

- **Context rot** — documented by Chroma research (`research.trychroma.com/context-rot`): recall and reasoning accuracy *degrade as the context window's token count grows*. More tokens is not strictly more capability; past a point it is actively harmful.
- **The attention budget** — in a transformer, every token competes for a finite pool of attention. Padding the window with low-value content dilutes the model's focus on what matters.

Execution mode is, in this light, a *context-management* device: Plan modes deliberately front-load the right context before any action, while autonomous modes manage the accumulating context of a long agentic loop.

---

## 2. Reasoning Architectures: Reliability Without a Model Upgrade

A recurring empirical finding is that *how* an agent structures its reasoning materially boosts reliability — independent of swapping in a stronger base model. The key building blocks:

- **Chain-of-Thought (CoT)** — Wei et al. 2022, Google (`arxiv.org/abs/2201.11903`). The simple "Let's think step by step" scaffold raised Game-of-24 success from **4% → 74%**. Reasoning made explicit beats reasoning left implicit.
- **ReAct** — interleaves a **Thought → Action → Observation** loop, grounding each reasoning step in evidence returned by a tool call rather than in the model's unverified imagination.
- **Reflexion** — adds a *post-step self-correction / self-check* loop, letting the agent critique and revise its own output before proceeding.
- **Lilian Weng's four-component framework** — defines an agent's context as: (1) the **system prompt**, (2) **tools**, (3) **examples / few-shot**, and (4) **message-history / state**.

These architectures are the substrate on which execution modes are built. Plan mode is essentially a structured CoT/ReAct pass with writes disabled; Reflexion-style self-checks reappear inside the Auto-mode classifiers discussed below.

---

## 3. The Universal Taxonomy: Three Trust Levels

Despite platform-specific branding, coding agents have converged on **three trust levels of identical shape**:

| Trust Level | Aliases | Reads / Searches | Writes / Commands | Mental Model |
|---|---|---|---|---|
| **Plan / Read-Only** | Plan, Read-Only | Allowed | **All blocked** | "Look, don't touch" |
| **Default / Standard** | Default, Standard | Free | **Pause for per-step approval** | "Act, but ask" |
| **Auto / Autopilot** | Auto, Autopilot, YOLO | Free | Run freely, review later | "Go, review after" |

Mode-switching ergonomics differ by platform:

- **Claude Code:** `Shift+Tab` cycles modes.
- **OpenCode:** `Tab` cycles modes.
- **Copilot CLI:** `Shift+Tab` or `/plan` for Plan Mode.

---

## 4. The Plan / Act Split: Cline's Explicit Implementation

Cline (an open-source IDE coding agent) makes the Plan/Act boundary an explicit, tool-level split rather than a soft convention:

| | PLAN MODE | ACT MODE |
|---|---|---|
| Purpose | Gather context, ask clarifying questions, brainstorm | Execute the plan step-by-step |
| Signature tool | `plan_mode_response` | `attempt_completion` (presents results) |
| Tool access | Has `plan_mode_response` | **All tools EXCEPT** `plan_mode_response` |

Cline layers two additional disciplines on top:

- **One-tool-per-message** — the agent may only call a single tool per turn.
- **Mandatory user confirmation** — each tool call awaits explicit user sign-off.

Together these create a tight **feedback loop that minimizes cascading errors**: a wrong step is caught and corrected before it can compound into a chain of wrong steps.

---

## 5. Claude Code Auto Mode: The Classifier-Gated Frontier

The most architecturally novel execution mode is Claude Code's **Auto mode** — distinct from a naive "YOLO" mode in that **an AI classifier reviews every action before it runs**, silently passing safe operations while intercepting risky ones.

### 5.1 Positioning and Rollout

- **Announced:** 24 March 2026, as a research preview on the **Team plan**, rolling to **Enterprise/API**.
- **Compatible models:** Sonnet 4.6 and Opus 4.6.
- **Flag:** `--dangerously-skip-permissions`.
- **Mechanism:** replaces human approval prompts with a **two-stage transcript classifier running on Sonnet 4.6**.
- **Authored by:** John Hughes. Configuration is inspectable via `claude auto-mode defaults / config / critique`.

It intercepts exactly the canonical dangerous patterns: `curl | bash`, secret exfiltration, force-pushing `main`.

### 5.2 The Self-Demotion Backstop

Auto mode does not trust itself indefinitely. A denial-tracking backstop (`denialTracking.ts`, `DENIAL_LIMITS`) escalates back to a **human permission prompt**:

| Trigger | Threshold | Reset Condition |
|---|---|---|
| Consecutive denials | **3** | Reset to 0 on **any success** |
| Cumulative denials per session | **20** | (per-session) |

Behavior diverges by environment at the limit:

- **Interactive UI:** escalates to a human permission prompt.
- **Headless mode (`claude -p`):** with no UI to prompt, it instead **terminates the process** — `"Agent aborted: too many classifier denials in headless mode"`.

There is also a **hard approval floor**: **protected paths** such as `.git` and `.env` always require approval regardless of classifier verdict.

### 5.3 The Three-Tier Classifier Pipeline

Not every action reaches the expensive classifier. Actions are triaged across three tiers:

| Tier | What it covers | Handling |
|---|---|---|
| **Tier 1** | Fixed safe-tool allowlist (file reads, Grep/Glob, todo/task tools) + user always-allow rules | Auto-passed |
| **Tier 2** | In-project file edits | Auto-allowed (reviewable via `git diff`) |
| **Tier 3** | Shell / web / external / subagent actions | Sent to the **Sonnet 4.6 transcript classifier** |

### 5.4 The Two-Stage Classifier and Its Error Profile

The Tier-3 classifier itself runs in two stages — a cheap filter and an expensive escalation:

| | Stage 1 | Stage 2 |
|---|---|---|
| Form | Single-token yes/no filter | Adds chain-of-thought |
| `max_tokens` | 64 | 4096 |
| Other params | `stop_sequence </block>`, `temperature 0`, **"err on the side of blocking"** | — |
| When it runs | Always | **Only when Stage 1 flags** |
| FPR (false positive — blocks safe ops) | ~8.5% | **0.4%** |
| FNR (false negative — misses risky ops) | 6.6% | **17%** on real overeager actions (n=52) |

Key dynamics of this design:

- The aggressive **"err on the side of blocking"** posture of Stage 1 produces a high false-positive rate (8.5%), which is *acceptable* because Stage 2's chain-of-thought reconsideration drives FPR down to **0.4%** — but at the cost of *raising* FNR to 17% on the n=52 real-overeager-action set.
- On a **synthetic exfiltration recall test (n=1000)**, FNR moved 1.8% → 5.7% across the staging — i.e., the system catches the overwhelming majority of synthetic exfil attempts.
- **Stage 2's input is near-identical to Stage 1's**, so it is **mostly a cache-hit** — the second stage is cheaper in practice than its 4096-token budget suggests.

### 5.5 "Reasoning-Blind by Design"

The single most important security property: the classifier is **deliberately reasoning-blind**.

- `buildTranscriptEntries` **strips assistant text and tool outputs**, sending only **user messages + tool calls (name + input)**, serialized as JSONL.
- **Consequence 1:** the agent **cannot rationalize its way past the gate** — its persuasive natural-language justifications never reach the classifier.
- **Consequence 2:** **prompt-injected tool content never reaches the classifier** — a malicious payload embedded in a fetched web page or file output cannot manipulate the gatekeeper, because tool outputs are stripped.
- **Fail-closed:** unparseable Stage 2 output **blocks** (fails closed, not open).

Two further hardening measures:

- **Dangerous blanket-allow stripping** — on entering auto mode, pre-existing blanket allow rules that grant code execution (`Bash *`, `python:*`, `node`, `npx`, `ssh`, `eval`, etc. — enumerated in `dangerousPatterns.ts`) are **stripped**, so the classifier actually *sees* damaging commands instead of having them waved through by a user's prior over-broad rule.
- **Subagent double-checking** — subagents are checked at **both** the **delegation (outbound)** boundary **and** the **handoff-return** boundary (where the classifier reviews the *full subagent action history*). A subagent cannot be used as a laundering channel for a forbidden action.

---

## 6. GitHub Copilot CLI: Terminal-Native, Host-Independent

GitHub Copilot CLI represents the other major terminal-native execution surface:

- **Install:** `npm install -g @github/copilot` — available on **all plans, including Free**.
- **Lineage:** replaces the **deprecated `gh copilot`** (deprecated October 2025).
- **Git-host independence:** works with **GitLab and Azure Repos**, not just GitHub — it is terminal-native, not tied to a specific host.

### 6.1 Three CLI-Exclusive Features (vs. VS Code Agent Mode)

| Feature | Invocation | Purpose |
|---|---|---|
| **Plan Mode** | `Shift+Tab` or `/plan` | Read-only planning pass |
| **Autopilot** | `--autopilot` (+ `--max-autopilot-continues N`) | Autonomous execution, capped to N steps to **prevent infinite loops** |
| **`/fleet`** | `/fleet` | Splits a task across **parallel subagents** |

### 6.2 Cross-Surface Portability

- **Multiple models:** Claude Opus 4.6, Claude Sonnet 4.6, GPT-5.3-Codex, Gemini 3 Pro.
- **Memory across sessions.**
- **Custom agents** (`.agent.md` files in `.github/agents/` or `~/.copilot/agents/`) and **Skills** are **shared between the CLI and VS Code** — the same agent definitions run in both surfaces.

The `--max-autopilot-continues N` cap deserves emphasis: it is Copilot's answer to the same problem Claude Code solves with denial-limit self-demotion — bounding the runaway autonomous loop, just via a step budget rather than a failure-rate trigger.

---

## 7. The Optimal Workflow: Gear-Shifting by Blast Radius

The research converges firmly: **the right strategy is to shift modes per-task based on blast radius / cost-of-wrong-action, never to pick one mode permanently.**

| Situation | Recommended Mode | Rationale |
|---|---|---|
| Unfamiliar codebase, or change touching **>3 files** | **Plan** | High uncertainty → front-load context before acting |
| Well-understood, mechanical **80%** — scaffolding, migrations, bulk refactors | **Auto** | Low cost-of-wrong, high volume → autonomy pays off |
| **Sensitive paths** — auth, payments, infra | **Default** (downshift) | High blast radius → per-step human approval |

Supporting evidence and tooling:

- **University of Chicago study:** experienced developers are **more likely to plan before generating code** — planning is a marker of expertise, not a beginner's crutch.
- **Armin Ronacher** (Flask creator) characterizes Claude Code's Plan mode as essentially **"a strong predefined prompt plus tool restrictions"** — demystifying it as disciplined context-loading rather than magic.

---

## 8. The Documented Failure Mode: Approval Fatigue

Autonomy and approval each have a failure mode, and the most-cited one is **approval fatigue**:

- **Anthropic's own docs flag it:** too many approval prompts **train blind approval** — the human starts rubber-stamping, which defeats the purpose of the gate. (This is precisely why Auto mode's classifier exists: to absorb the high-volume safe approvals so humans only see the genuinely ambiguous ones.)
- **The cited antidote — OpenCode's per-tool permission rules:** declarative, granular rules that pre-decide categories so the human is only asked about the genuinely uncertain. Example:

```
{
  bash: {
    'git status*': allow,
    'rm *':        deny,
    '*':           ask
  }
}
```

This pattern — *allow the obviously safe, deny the obviously dangerous, ask only on the residual* — is the structural solution to approval fatigue, and it mirrors the same triage logic that Claude Code's three-tier classifier pipeline implements automatically.

---

## 9. Synthesis: Common Design Principles

Reading across all platforms, a coherent set of converged principles emerges for any execution-mode design:

1. **Separate reading from writing.** Every system has a read-only posture (Plan) where the agent can gather context with zero blast radius.
2. **Triage, don't gate uniformly.** Both Claude Code's three tiers and OpenCode's per-tool rules pre-classify the safe majority so scarce human attention goes to the ambiguous minority.
3. **Bound autonomous loops.** Claude Code caps via denial limits (3 consecutive / 20 cumulative) and headless-abort; Copilot caps via `--max-autopilot-continues N`. An unbounded autonomous loop is universally treated as a defect.
4. **Make the gatekeeper un-persuadable.** Claude Code's reasoning-blind classifier is the strongest expression: strip the agent's rationalizations and strip injected tool content so neither the agent nor an attacker can talk past the gate.
5. **Fail closed.** Unparseable verdicts block; protected paths (`.git`, `.env`) always require approval; over-broad allow rules are stripped on entering high-autonomy mode.
6. **Hard floors over soft trust.** Even at maximum autonomy, certain paths and patterns are non-negotiable approval points.

The throughline is that execution mode is fundamentally a **context- and trust-management problem**. The reasoning architectures (CoT, ReAct, Reflexion) make a single step reliable; the trust taxonomy (Plan / Default / Auto) governs how many steps the human stays in the loop for; and the classifier/permission machinery (Claude Code's reasoning-blind two-stage pipeline, OpenCode's per-tool rules, Copilot's step caps) is what makes the high-autonomy end of that spectrum safe enough to actually use. Mastery is the gear-shift: matching posture to blast radius, task by task.

## Sources

- <https://machinelearningmastery.com/prompt-engineering-for-agentic-ai/>
- <https://www.prompthub.us/blog/prompt-engineering-for-ai-agents>
- <https://www.dataknobs.com/agent-ai/prompt-engineering/>
- <https://www.promptingguide.ai/agents>
- <https://skywork.ai/blog/agent/plan-mode-vs-agent-mode-understanding-githubs-revolutionary-coding-workflows/>
- <https://www.aibuilderclub.com/blog/agent-modes-plan-default-auto>
- <https://smartscope.blog/en/generative-ai/github-copilot/github-copilot-cli-practical-guide-2026/>
- <https://cursor.com/blog/agent-best-practices>
- <https://arxiv.org/pdf/2509.08646>
- <https://code.claude.com/docs/en/auto-mode-config>
- <https://claude.com/blog/auto-mode>
- <https://www.anthropic.com/engineering/claude-code-auto-mode>
- <https://gist.github.com/sc0tfree/11c86116df4c2281a976d796f9493cd7>
- <https://simonwillison.net/2026/Mar/24/auto-mode-for-claude-code/>

## Run metadata

- **Prompt:** MODO: EXECUTION MODE
- **Depth / breadth:** 2 / 3
- **Queries used:** 4 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 331.6 s
- **Errors during run:** 2
- **Started at:** 2026-06-20T19:02:53Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://blogs.oracle.com/fusioncoe/basics-of-prompt-engineer...': page-fetch: https://blogs.oracle.com/fusioncoe/basics-of-prompt-engineering: HTTP Error 403: Forbidden`
- `web_search '"ACT mode" vs "plan mode" agent reliabil...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`

</details>
