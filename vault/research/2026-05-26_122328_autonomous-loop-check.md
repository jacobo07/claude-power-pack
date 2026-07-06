# Autonomous Loop Check — State of the Art (May 2026)

A consolidated technical report on autonomous-loop primitives, observability, and verifier-separated control patterns across Claude Code, the Claude Agent SDK, OpenAI Codex CLI, GitHub Copilot CLI, and the third-party ecosystem.

---

## 1. Executive Summary

By Q2 2026, "autonomous loops" have crystallized into a distinct discipline with three native implementations (Claude Code `/loop`, Claude Agent SDK agentic loop, Codex CLI `/goal`), one wrapper-pattern lineage (Ralph Wiggum Method → ralph.ps1 → ralph-style infinite loops), and a mature observability layer (`ecc loop-status`, Sentient hooks, Sentinel runners). The defining technical lesson across all implementations is **stateless agent + stateful filesystem**: the loop's intelligence lives in on-disk files (`state.json`, `DONE`/`BLOCKED` markers, `last_failure.txt`, `prd.json`, `learnings.md`), never in agent memory, because fresh-context invocations are the only way to bound runaway context growth across long horizons.

The second crystallized lesson is **verifier-agent separation**: self-reported "tests pass" cannot be trusted as a termination signal. Both the third-party `autoloop` plugin and the Codex `/goal` continuation protocol explicitly warn against proxy signals, mandating a separate verification agent or structured `update_goal` tool call.

The third crystallized lesson is **wedge detection**: the predominant failure mode is no longer hallucination but transport-layer death — orphaned `ScheduleWakeup` calls that never fire, and `Bash` tool calls that return no `tool_result` (the Windows MSYS2/Git-Bash bridge `[Tool result missing due to internal error]` pattern). `loop-status.js` exists specifically to scan transcript JSONLs for these two signatures.

---

## 2. Native Implementations

### 2.1 Claude Code `/loop` (v2.1.66–2.1.71, March 5–8, 2026)

| Property | Value |
|---|---|
| Syntax | `/loop [interval] [task]` (e.g., `/loop 30m check build logs`) |
| Default interval | 10 minutes |
| Granularity | 1 minute (seconds round up) |
| Max session lifetime | 3 days (hard) |
| Max scheduled tasks | 50 per session |
| Task ID | 8 characters, cancelable via `/loop cancel [id]` |
| Backing tools | `CronCreate`, `CronList`, `CronDelete` (released v2.1.71, 2026-03-07) |
| Jitter (recurring) | Up to 10% of period, capped 15 min, deterministic offset derived from task ID |
| Jitter (one-shot) | May fire up to 90s early |
| Firing window | Between turns at low priority — **never** interrupts mid-response |
| Time zone | Local TZ, not UTC |
| Kill switch | `CLAUDE_CODE_DISABLE_CRON=1` env var |
| Persistence | Dies on terminal close (session-scoped) |

**Cost envelope (empirical):** a 5-minute loop running 3 days ≈ 1,728 invocations ≈ 3.5M tokens ≈ **$10–$15 on Sonnet 4.6**.

**Persistence complement:** Claude Code Desktop's local schedules are the non-session-bound counterpart for survivable loops past terminal close.

### 2.2 Claude Agent SDK (`@anthropic-ai/claude-code`)

The standalone SDK exposes the same agentic loop as the CLI:

```
Receive prompt → Evaluate → Execute tools → Repeat → ResultMessage
```

**Bounding controls:**

| Control | Purpose |
|---|---|
| `max_turns` / `maxTurns` | Caps tool-use round-trips only (not message count) |
| `max_budget_usd` / `maxBudgetUsd` | Hard cost ceiling |
| `effort` | `low \| medium \| high \| xhigh \| max` — TypeScript defaults to `high`; Python defers to model default. **`xhigh` is explicitly recommended for Opus 4.7 coding/agentic tasks.** |

**Termination semantics — `ResultMessage.subtype`:**

| Subtype | Meaning | `result` populated? |
|---|---|---|
| `success` | Normal completion | Yes |
| `error_max_turns` | Turn budget exhausted | No |
| `error_max_budget_usd` | Dollar budget exhausted | No |
| `error_during_execution` | Tool / runtime failure | No |
| `error_max_structured_output_retries` | Schema retries blown | No |

**Permission modes (gate every tool exec):** `default`, `acceptEdits` (auto-approves `mkdir`/`touch`/`mv`/`cp`), `plan` (read-only), `dontAsk`. TypeScript adds `auto` and `bypassPermissions`.

**Hook surface for sentinel-style self-check:** `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `SubagentStart`/`SubagentStop`, `PreCompact`. The `compact_boundary` message fires when the SDK auto-summarizes to free context — critical for long-horizon loops crossing context windows.

### 2.3 OpenAI Codex CLI `/goal` (v0.128.0, 2026-04-30)

The closest public analog to a `ScheduleWakeup`-style "autonomous-loop-dynamic" protocol.

**Activation:** `[features] goals = true` in `~/.codex/config.toml` (gated).

**Lifecycle states (5):** `pursuing`, `paused`, `achieved`, `unmet`, `budget-limited`.

**Loop drivers (templates at `codex-rs/core/templates/goals/`):**
- `continuation.md` — re-invocation with audit protocol
- `budget_limit.md` — graceful exhaustion exit

**Structured tool:** `update_goal` (model-callable).

**Anti-proxy-signal mandate:** Codex explicitly instructs the model *not* to accept proxy signals like "tests pass" as completion — a direct codification of the verifier-separation lesson.

**Known bug:** Issue **#19910** — continuation prompt can be lost after mid-turn compaction (a real-world manifestation of the `PreCompact` hook category being load-bearing).

---

## 3. Third-Party Wrappers & Verifier-Separated Loops

### 3.1 `autoloop` Plugin (`yaoshengzhe/autoloop` marketplace)

- **Invocation:** `/autoloop:autoloop <task> --max-iterations N`
- **Verifier:** Spawns a **separate verification agent with no conversation access** that runs actual tests/build/lint before allowing loop termination.
- **Doctrine:** Defeats self-reporting bias by structural isolation — the verifier cannot see the loop's narrative, only the artifacts.

### 3.2 `agentic-loop` (npm, MIT, by @allierays / AllThrive AI)

**Two-terminal split topology:**

| Terminal | Role |
|---|---|
| 1 | Plan-mode + `/prd` generates `.ralph/prd.json`, with auto-`prd-check` |
| 2 | `npx agentic-loop run` executes per-story |

**5-stage code-check pipeline per iteration:**
1. Lint
2. Tests
3. PRD test steps
4. API smoke
5. Frontend smoke

**Failure persistence:** failures written to `last_failure.txt` — picked up as next-iteration context. Pure stateless-agent / stateful-disk pattern.

**Requirements:** `claude --dangerously-skip-permissions`, Node 18+, `jq`.

### 3.3 Everything-Claude-Code (ECC) by @affaan-m — 6 Loop Levels (50K+ ⭐)

| Level | Pattern | State medium |
|---|---|---|
| 1 | Sequential Pipeline | Implicit (single session) |
| 2 | NanoClaw REPL | Markdown in `~/.claude/claw/` |
| 3 | Infinite Agentic Loop | `state.json` bridges fresh `claude -p` sessions (context-blowup defeat) |
| 4 | Continuous PR Loop | Cron-triggered backlog drain |
| 5 | De-Sloppify | `PreToolUse` hook scrubs `console.log` / magic numbers pre-commit |
| 6 | RFC-Driven DAG | `tmux-worktree-orchestrator.js` with `task.md` / `status.md` / `handoff.md` |

**Observability bridge:** `loop-status.js` (see §5).

### 3.4 Claude Sentient (thebiglaskowski/claude-sentient)

**7-phase orchestration loop:** `INIT → UNDERSTAND → PLAN → EXECUTE → VERIFY → COMMIT → EVALUATE`.

**4 fail-closed quality gates:** lint, test, build, git-clean.

**15 hook scripts** including:
- `session-start.cjs`
- `dod-verifier.cjs` (Stop event)
- `teammate-idle.cjs`
- `pre-compact.cjs`

**9 auto-detected language profiles:** Python, TS, Go, Rust, Java, C++, Ruby, Shell, general.

**ClaudeFast Ralph+Threads model — cost frame:**

| Worker | Cost |
|---|---|
| Sonnet autonomous agent | ~**$10.42/hr** |
| Human engineer (reference) | ~**$100/hr** |

**Thread types** (Base / P / C / F / B / L / Z) map to escalating verification automation — from manual review to automated tests + Stop hooks.

### 3.5 The Ralph Wiggum Method (Geoffrey Huntley, ghuntley.com/ralph/)

**Doctrine:** Run fresh-context AI agent iterations against persistent on-disk state with `DONE` / `BLOCKED` files. Agent is fungible and amnesiac by design. Iteration count, not iteration intelligence, is the productive force.

### 3.6 Benjamin Abt's `github-copilot-ralph-loop` (PowerShell)

| Property | Value |
|---|---|
| Script | `ralph.ps1` |
| Default model | `gpt-5-mini` |
| Fallback | `gpt-5.1-codex-mini` |
| Timeout | 600s |
| Autonomous flag | `--yolo` |
| Input set | `ralph/prd.json`, `ralph/AGENTS.md`, `ralph/learnings.md`, `ralph/state/` |
| Observed convergence | Working .NET 10 console app + xUnit tests in ~3 iterations (78s, 88s, 165s) |

**Universal lesson it confirms:** loop intelligence lives in files (DONE / BLOCKED / state), **not** in the agent. The agent must remain stateless and fungible.

---

## 4. Comparative Termination & Bounding Matrix

| System | Hard turn cap | Hard $ cap | Hard time cap | Verifier separation | State medium |
|---|---|---|---|---|---|
| Claude Code `/loop` | None (per-fire) | None | 3 days session | No (loop fires same agent) | In-session conversation |
| Claude Agent SDK | `max_turns` | `max_budget_usd` | None | Via `SubagentStart` hooks | Caller-supplied |
| Codex `/goal` | None | Budget state `budget-limited` | None | `update_goal` structured tool + anti-proxy mandate | App-server APIs |
| `autoloop` plugin | `--max-iterations` | None | None | **Yes** — isolated verification agent | Plugin-managed |
| `agentic-loop` | Per-story | None | None | **Yes** — 5-stage pipeline | `.ralph/prd.json` + `last_failure.txt` |
| ECC Infinite Loop | None | None | None | Optional per level | `state.json` |
| Claude Sentient | None | None | None | **Yes** — 4 gates + DoD verifier | 15 hook scripts |
| Ralph / `ralph.ps1` | None | None | None | File-based DONE/BLOCKED | `ralph/state/` |

---

## 5. Observability — `ecc loop-status`

The `ecc loop-status` CLI (npx `--package ecc-universal`) is the canonical sibling-terminal observability layer for autonomous loops.

**What it scans:** Claude transcript JSONL files under `~/.claude/projects/**`.

**What it flags (wedge signatures):**
1. **Stale `ScheduleWakeup` calls** — scheduled fires that never executed.
2. **`Bash` tool calls lacking matching `tool_result`** — transport drop / hung child. This is the exact signature of the Windows MSYS2 / Git-Bash bridge `[Tool result missing due to internal error]` failure documented at length across KobiiCraft sessions.

**Key flags:**

| Flag | Purpose |
|---|---|
| `--bash-timeout-seconds` | Configurable stale-Bash threshold (default example: **1800s / 30 min**) |
| `--watch` | Continuous monitoring |
| `--exit-code` | Set exit code based on findings (requires `--watch-count` to bound iterations) |
| `--write-dir` | Emits `index.json` + per-session JSON snapshots for sibling-terminal observability |

**Exit codes:**

| Code | Meaning |
|---|---|
| `0` | Clean |
| `1` | Transcripts unscannable |
| `2` | Stale loop / tool signals found |

**Critical limitation:** the `--write-dir` snapshots are **read-only** — they do NOT control or timeout Claude Code runtime tool calls. They are observation only; remediation requires out-of-band action.

**Source of truth:** `affaan-m/everything-claude-code` repo, commit `841beea4`:
- `scripts/loop-status.js` lines 14–37 (wedge detection logic)
- `scripts/ecc.js` lines 56–59 (CLI wiring)

This script is the canonical observability bridge for all six ECC loop levels (Sequential Pipeline, NanoClaw REPL, Infinite Agentic Loop, Continuous Claude PR Loop, Multi-Model Workflow, Ralphinho DAG via `tmux-worktree-orchestrator.js`).

---

## 6. Cross-Cutting Architectural Lessons

### 6.1 Stateless Agent + Stateful Filesystem
Every long-horizon loop that works in 2026 puts intelligence on disk and treats the agent as a fungible compute unit. ECC's `state.json`, Ralph's `DONE`/`BLOCKED`, `agentic-loop`'s `last_failure.txt`, Codex's app-server-persisted goals, `ralph.ps1`'s `ralph/state/` — same pattern, six implementations.

### 6.2 Verifier-Agent Separation
Self-reporting bias is the dominant failure mode at scale. Structural isolation (separate verifier with no conversation access — `autoloop`) and structured tool calls with explicit anti-proxy warnings (`update_goal` in Codex) are the two converged solutions. The `agentic-loop` 5-stage pipeline is the heaviest practical instantiation.

### 6.3 Wedge Detection > Hallucination Detection
The Windows MSYS2 / Git-Bash bridge `[Tool result missing due to internal error]` failure is now a named, scanned-for pattern in observability tools. Orphaned `ScheduleWakeup` calls are its twin. Together they account for the bulk of "stuck" autonomous-loop reports in 2026.

### 6.4 Compaction Boundary Is Load-Bearing
Codex issue **#19910** (continuation prompt loss after mid-turn compaction) and the Claude Agent SDK's explicit `compact_boundary` message + `PreCompact` hook prove that auto-summarization is now an explicit failure surface that long-horizon loops must handle.

### 6.5 Loops Run Between Turns, Never Mid-Response
Claude Code's `/loop` firing-window discipline (low priority, between-turn) is the design pattern that prevents the recursive self-interruption antipattern. Any homemade scheduler should adopt the same constraint.

### 6.6 Effort Tier Selection
For Opus 4.7 specifically: `xhigh` is the explicitly recommended effort tier for coding/agentic tasks. TypeScript SDK defaults to `high` — explicitly bump to `xhigh` for any loop driving non-trivial code work.

---

## 7. Practical Recommendations

| Use case | Recommended primitive |
|---|---|
| Quick in-session cron (≤3 days) | Claude Code `/loop [interval] [task]` |
| Long-running survivable schedule | Claude Code Desktop local schedules |
| Programmatic embedding | Claude Agent SDK with `max_turns` + `max_budget_usd` + `xhigh` effort |
| PRD-driven feature buildout | `agentic-loop` (5-stage verification) |
| Backlog drain / PR farm | ECC Continuous PR Loop (cron-triggered) |
| Quality-gated dev loop | Claude Sentient 7-phase + 4 fail-closed gates |
| OpenAI ecosystem parallel | Codex CLI `/goal` (gated behind `[features] goals = true`) |
| Wrapper / cross-CLI portability | Ralph pattern via `ralph.ps1` or fresh-context `claude -p` |
| Observability / wedge detection | `npx --package ecc-universal ecc loop-status --bash-timeout-seconds 1800` |

---

## 8. Open Questions & Speculative Notes

> The following are flagged as **speculation / prediction** per the assistant's research mandate.

1. **Convergence prediction:** the `autoloop` verifier-separation pattern and Codex's anti-proxy `update_goal` will likely be folded into Claude Code `/loop` natively within 1–2 minor releases — the friction between "self-reported done" and "verified done" is too large to leave to plugins.
2. **Compaction-aware loop continuation** (the inverse of Codex #19910) is the next obvious primitive: a `PreCompact` hook that re-injects the goal definition into the summary boundary. ECC's `state.json` bridging across fresh `claude -p` sessions is the manual version of this.
3. **Wedge-detection feedback loop:** `ecc loop-status` is currently read-only; an obvious next step is `--auto-kill` or `--auto-restart` flags that issue `/loop cancel [id]` against detected stale tasks. The constraint is that no current Claude Code API exposes cron control from outside the session.
4. **Cost convergence:** the **~$10.42/hr Sonnet** vs **~$100/hr human** ratio cited in ClaudeFast doctrine will likely compress as Opus 4.7 `xhigh` effort becomes the default for agentic tasks — the per-iteration cost is materially higher than Sonnet, and verifier-separation adds a second agent's cost on top.

---

## 9. References (Inline)

- Claude Code v2.1.66–v2.1.71 release notes (2026-03-05 → 2026-03-08)
- Claude Agent SDK — `@anthropic-ai/claude-code`
- OpenAI Codex CLI 0.128.0 (2026-04-30), `/goal` command, templates at `codex-rs/core/templates/goals/`, issue #19910
- `yaoshengzhe/autoloop` (Claude Code marketplace plugin)
- `agentic-loop` npm package (MIT, @allierays / AllThrive AI)
- `affaan-m/everything-claude-code` (50K+ ⭐, commit `841beea4`)
- `thebiglaskowski/claude-sentient`
- Geoffrey Huntley, "The Ralph Wiggum Method," ghuntley.com/ralph/
- Benjamin Abt, `github-copilot-ralph-loop` (`ralph.ps1`)

## Sources

- <https://code.claude.com/docs/en/agent-sdk/agent-loop>
- <https://skillsplayground.com/guides/claude-code-agents/>
- <https://letitloop.dev/>
- <https://github.com/allierays/agentic-loop>
- <https://www.contextstudios.ai/blog/claude-code-loop-autonomous-agent>
- <https://deepwiki.com/affaan-m/everything-claude-code/10.7-autonomous-loop-patterns>
- <https://github.com/thebiglaskowski/claude-sentient>
- <https://gu-log.vercel.app/en/posts/en-sp-143-20260402-ecc-autonomous-loops>
- <https://claudefa.st/blog/guide/mechanics/autonomous-agent-loops>
- <https://github.com/ssd1212/everything-claude-codeSS/blob/main/commands/loop-status.md>
- <https://sangampandey.info/blog/claude-code-loop-command>
- <https://benjamin-abt.com/blog/2026/01/19/ralph-loop-github-copilot-cli-dotnet/>
- <https://www.learncisco.net/courses/icnd-1/ip-routing-technologies/dynamic-routing.html>
- <https://opencode.ai/docs/agents/>
- <https://ralphable.com/blog/codex-goal-command-ralph-loop-openai-built-in-autonomous-coding-agent-2026>

## Run metadata

- **Prompt:** # Autonomous loop check
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 619.3 s
- **Errors during run:** 4
- **Started at:** 2026-05-26T10:23:28Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `extract_learnings: claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--append-system-prompt', "You are an expert researcher. Today is 2026-05-26. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 120 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `fetch_page 'https://mcpmarket.com/tools/skills/loop-execution-monitor...': page-fetch: https://mcpmarket.com/tools/skills/loop-execution-monitor: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://github.com/pjt222/agent-almanac/blob/main/guides/sel...': page-fetch: https://github.com/pjt222/agent-almanac/blob/main/guides/self-continuation-loops-playbook.md: HTTP Error 429: Too Many Requests`
- `web_search '"<<autonomous-loop-dynamic>>" OR "autono...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`

</details>
