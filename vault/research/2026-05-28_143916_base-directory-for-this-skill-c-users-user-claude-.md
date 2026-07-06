# Research Report — LLM CEILING

Prompt: Base directory for this skill: C:\Users\User\.claude\skills\claude-power-pack

All learnings + URLs are below (raw, unsynthesized) because the report-generation LLM call failed:
claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--append-system-prompt', "You are an expert researcher. Today is 2026-05-28. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 240 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set

## Raw learnings (12)
- Claude Code skills live in two scopes: project-scoped at `.claude/skills/<name>/SKILL.md` (committed to repo, shared with team) and global at `~/.claude/skills/<name>/SKILL.md` (personal, applies across all projects). On Windows `~/.claude` resolves to `%USERPROFILE%\.claude`, overridable via the `CLAUDE_CONFIG_DIR` environment variable. Each skill is a self-contained folder with a SKILL.md file requiring only two YAML frontmatter fields: `name` (lowercase, hyphens) and `description`.
- Skills can be packaged and distributed as Claude Code Plugins via marketplaces — e.g., `/plugin marketplace add anthropics/skills` then `/plugin install document-skills@anthropic-agent-skills` or `example-skills@anthropic-agent-skills`. Anthropic's official skills repo (github.com/anthropics/skills) includes `./skills`, `./spec` (Agent Skills specification), and `./template` (starting template); document skills like docx/pdf/pptx/xlsx are source-available rather than Apache 2.0.
- Real-world skill suites follow a memory-backed pattern: Microsoft's Power Platform Build Tools `.claude/skills/` contains specialized skills (architecture, pac-cli-update, fix-dependencies, security-alerts, workitem, review, debug-agent, knowledge-sync) that share a persistent `memory/ado-knowledge.md` knowledge base auto-refreshed by knowledge-sync when older than 7 days. Plugin orphaned versions are auto-deleted 7 days after update/uninstall under `~/.claude/plugins`.
- A SKILL.md file requires YAML frontmatter delimited by triple-dash markers with two mandatory fields: `name` (unique lowercase/kebab-case identifier, defaults to directory name) and `description` (truncated at 1,536 characters in skill listings). Optional frontmatter fields include `disable-model-invocation` (prevents Claude auto-loading, default false), `user-invocable` (default true), `allowed-tools`/`disallowed-tools`, `model`, `effort` (low/medium/high/xhigh/max), `context: fork` (runs in subagent), `agent`, `hooks`, `argument-hint`, and `arguments`. Skills live at `~/.claude/skills/<name>/SKILL.md` (user-global) or `.claude/skills/<name>/SKILL.md` (project), and the directory name becomes the slash command.
- Skills use a progressive disclosure architecture with three tiers: discovery loads only name+description (~100 tokens per skill) into the system prompt at session start; activation loads the full SKILL.md body (~1K-5K tokens) when Claude determines relevance; execution loads supporting files in `scripts/` or `references/` only when needed. Once invoked, SKILL.md content stays in context for the rest of the session (Claude Code does not re-read it on later turns). Auto-compaction re-attaches the most recent invocation of each skill keeping the first 5,000 tokens, with a combined 25,000-token budget across re-attached skills. Recommended SKILL.md body limit is under 500 lines.
- Dynamic context injection uses ``!`<command>`` syntax (inline, only recognized when `!` starts a line or follows whitespace) or fenced ` ```!` blocks for multi-line — commands execute before Claude sees content, output replaces the placeholder, and a single resolution pass means placeholders cannot recursively emit other placeholders. String substitutions include `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N` shorthand, `$name` for declared arguments, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, and `${CLAUDE_SKILL_DIR}`. The open Agent Skills standard (agentskills.io, released Dec 2025) is portable across Claude Code, Claude.ai, the API, and was adopted by OpenAI for Codex/ChatGPT; Claude Code extends it with invocation control, subagent execution (`context: fork`), and dynamic context injection. The setting `disableSkillShellExecution: true` disables `!` command execution for user/project/add-dir skills (bundled skills are exempt).
- Claude Code SKILL.md frontmatter supports a `hooks` field that accepts the same JSON structure as `.claude/settings.json` hooks, scoped to the skill's lifecycle. All hook events are supported (PreToolUse, PostToolUse, UserPromptSubmit, Stop, etc.), with the structure: `hooks: {EventName: [{matcher: 'ToolName', hooks: [{type: 'command', command: './script.sh'}]}]}`. For subagents (and skills with `context: fork`), `Stop` hooks are automatically converted to `SubagentStop` events at runtime. Skills declaring `hooks` or `allowed-tools` are treated as elevated-permission requests and require user approval before first use (per Claude Code changelog 2.1.19).
- Hook matcher syntax follows specific evaluation rules: `*`/empty/omitted matches all; only letters/digits/`_`/`|` is treated as exact string or pipe-separated exact-string list (e.g., `Bash` or `Edit|Write`); any other character triggers JavaScript regex evaluation (e.g., `^Notebook`, `mcp__memory__.*`). MCP tools follow `mcp__<server>__<tool>` naming and require `.*` to match by server prefix (bare `mcp__memory` is treated as exact-string and matches nothing). Events without matcher support — UserPromptSubmit, PostToolBatch, Stop, TeammateIdle, TaskCreated, TaskCompleted, WorktreeCreate, WorktreeRemove, CwdChanged — silently ignore any matcher field.
- Hook handlers support five `type` values: `command` (shell, default timeout 600s), `http` (POST with JSON body, default 600s), `mcp_tool` (calls tool on connected MCP server, default 600s), `prompt` (single-turn LLM evaluation, default 30s), and `agent` (subagent with Read/Grep/Glob, experimental, default 60s). The `if` field uses permission-rule syntax (e.g., `Bash(rm *)`, `Edit(*.ts)`) for fine-grained filtering on tool events only — on non-tool events, hooks with `if` set never run. Command hooks use exec form (when `args` is set, no shell, direct spawn) vs shell form (when `args` is absent, uses sh -c / Git Bash / PowerShell); on Windows, `.cmd`/`.bat` shims require shell form or invoking via `node` directly.
- The SERP results contain no direct documentation, repository, or reference for 'claude-power-pack modules executionos-lite governance-overlay'—the query appears to map to a private/local toolkit (referenced in the user's CLAUDE.md at ~/.claude/skills/claude-power-pack/modules/executionos-lite/ and modules/governance-overlay/) rather than any indexed public project. Public results instead surface adjacent ecosystems: Anthropic's official claude-plugins-official marketplace (2.8k stars), the Claude Code plugin schema (plugin.json with skills/agents/hooks/mcpServers/lspServers/monitors components), and Jesse Vincent's Superpowers plugin (~174k stars) built by Prime Radiant.
- The Claude Code plugin manifest reference (code.claude.com/docs) defines a tiered component architecture relevant to any 'executionos-lite' style module: skills (SKILL.md with YAML frontmatter), agents (with isolation:'worktree' as the only valid value; hooks/mcpServers/permissionMode forbidden in plugin-shipped agents for security), 25+ hook events (SessionStart, PreToolUse, PostToolUse, Stop, PreCompact, etc.), and persistent state via ${CLAUDE_PLUGIN_DATA} resolving to ~/.claude/plugins/data/{id}/ with a 7-day orphan-version grace period. Plugin monitors require Claude Code v2.1.105+; displayName requires v2.1.143+.
- The Superpowers methodology (obra/superpowers, MIT-licensed by Jesse Vincent at Prime Radiant) implements a tiered execution model conceptually parallel to 'executionos-lite': brainstorming → using-git-worktrees → writing-plans (2-5 minute tasks) → subagent-driven-development with two-stage review (spec compliance then code quality) → test-driven-development (RED-GREEN-REFACTOR) → requesting-code-review → finishing-a-development-branch. It installs across 8 harnesses (Claude Code, Codex CLI/App, Factory Droid, Gemini CLI, OpenCode, Cursor, GitHub Copilot CLI) via separate marketplace registration per harness.

## Raw URLs
- https://code.claude.com/docs/en/claude-directory
- https://deepwiki.com/microsoft/powerplatform-build-tools/6.5-claude-ai-skills
- https://github.com/anthropics/skills
- https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf
- https://code.claude.com/docs/en/skills
- https://deepwiki.com/travisvn/awesome-claude-skills/9.1-skill.md-specification
- https://evomap.ai/blog/claude-code-skills-developer-reference
- https://duet.so/guides/claude-code-skills-complete-guide
- https://code.claude.com/docs/en/hooks
- https://allahabadi.dev/blogs/ai/claude-code-skills-frontmatter-complete-guide/
- https://www.agentpatterns.ai/tool-engineering/skill-frontmatter-reference/
- https://sjramblings.io/building-skills-for-claude-part-2/
- https://github.com/obra/superpowers
- https://code.claude.com/docs/en/plugins-reference
- https://www.scriptbyai.com/claude-code-resource-list/
- https://hackernoon.com/how-to-build-a-governance-layer-for-claude-code-with-hooks-skills-and-agents
- https://www.mcpworld.com/en/detail/a43bf675a202ccaf88f9793b5588cda4

## Sources

- <https://code.claude.com/docs/en/claude-directory>
- <https://deepwiki.com/microsoft/powerplatform-build-tools/6.5-claude-ai-skills>
- <https://github.com/anthropics/skills>
- <https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf>
- <https://code.claude.com/docs/en/skills>
- <https://deepwiki.com/travisvn/awesome-claude-skills/9.1-skill.md-specification>
- <https://evomap.ai/blog/claude-code-skills-developer-reference>
- <https://duet.so/guides/claude-code-skills-complete-guide>
- <https://code.claude.com/docs/en/hooks>
- <https://allahabadi.dev/blogs/ai/claude-code-skills-frontmatter-complete-guide/>
- <https://www.agentpatterns.ai/tool-engineering/skill-frontmatter-reference/>
- <https://sjramblings.io/building-skills-for-claude-part-2/>
- <https://github.com/obra/superpowers>
- <https://code.claude.com/docs/en/plugins-reference>
- <https://www.scriptbyai.com/claude-code-resource-list/>
- <https://hackernoon.com/how-to-build-a-governance-layer-for-claude-code-with-hooks-skills-and-agents>
- <https://www.mcpworld.com/en/detail/a43bf675a202ccaf88f9793b5588cda4>

## Run metadata

- **Prompt:** Base directory for this skill: C:\Users\User\.claude\skills\claude-power-pack
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 722.0 s
- **Errors during run:** 5
- **Started at:** 2026-05-28T12:39:16Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://mcpmarket.com/tools/skills/claude-skill-boilerplate-...': page-fetch: https://mcpmarket.com/tools/skills/claude-skill-boilerplate-structure: HTTP Error 429: Too Many Requests`
- `web_search '"claude-power-pack" skill SKILL.md modul...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `fetch_page 'https://github.com/shanraisshan/claude-code-best-practice/bl...': page-fetch: https://github.com/shanraisshan/claude-code-best-practice/blob/main/CLAUDE.md: HTTP Error 429: Too Many Requests`
- `web_search '"claude-power-pack" OR "executionos-lite...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`
- `generate_report: claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--append-system-prompt', "You are an expert researcher. Today is 2026-05-28. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 240 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set`

</details>
