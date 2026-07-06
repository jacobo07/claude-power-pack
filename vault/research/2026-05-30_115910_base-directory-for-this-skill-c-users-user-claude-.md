# Claude Code Agent Skills & Plugins — Architecture, Resolution, and Security Reference

*Synthesized research report · 2026-05-30*

## 1. Scope and Purpose

This report consolidates the current understanding of how **Agent Skills** and **Plugins** are structured, discovered, resolved, and secured in Claude Code. It is intended as an authoritative engineering reference for anyone authoring skills (such as those under `C:\Users\User\.claude\skills\claude-power-pack`), packaging them into plugins, or reasoning about precedence, merge semantics, and the trust boundaries that govern execution. Every finding from the underlying research is incorporated, organized by concern: the skill format itself, the resolution/priority model, frontmatter contracts, plugin packaging, merge semantics, and the security restrictions that differentiate plugin-shipped components from project-local ones.

---

## 2. The Agent Skill Format

### 2.1 The self-contained folder + SKILL.md contract

Anthropic's official skills repository (`github.com/anthropics/skills`) establishes the canonical pattern: **each skill is a self-contained folder containing a required `SKILL.md` file**. That file carries YAML frontmatter, and the frontmatter has only **two required fields**:

| Field | Constraint |
|---|---|
| `name` | lowercase, hyphen-separated (kebab-case), max 64 chars |
| `description` | must state both **WHAT** the skill does and **WHEN** to use it; max 1024 chars |

The `description` field is not cosmetic — it is the **sole driver of auto-discovery**. Because of progressive disclosure (Section 4), only the description loads at session start, so a description that fails to encode *when* the skill applies will simply never be surfaced to the model at the right moment.

### 2.2 The Agent Skills standard and the official marketplace

The broader **Agent Skills standard** is documented at **agentskills.io**. Anthropic's repo is installable as a Claude Code **Plugin marketplace**:

```
/plugin marketplace add anthropics/skills
```

This exposes two plugins with materially different licensing:

| Plugin | Contents | Licensing |
|---|---|---|
| `document-skills` | docx / pdf / pptx / xlsx skills | **Source-available, not open source** |
| `example-skills` | reference example skills | **Apache 2.0** |

The licensing distinction matters for downstream redistribution: the document-handling skills cannot be treated as freely reusable open-source components despite being readable.

---

## 3. Skill Resolution and Priority

### 3.1 Three storage locations, strict precedence

Claude Code resolves skills from **three locations** in a **strict priority order**. On a name collision, the higher-priority location wins:

| Priority | Location | Scope | Git |
|---|---|---|---|
| **1 (highest)** | `.claude/skills/<name>/SKILL.md` | Project-local | Committed to the repo |
| **2** | `~/.claude/skills/<name>/SKILL.md` | Personal — applies across **all** projects | Personal config |
| **3 (lowest)** | `<plugin>/skills/<name>/SKILL.md` | Bundled inside a plugin | Distributed with plugin |

The precedence ordering — **Project > Personal > Plugin** — means a project can deliberately shadow a personal or plugin skill of the same name, and a personal skill can shadow a plugin skill. This is the mechanism by which `claude-power-pack` (a personal skill at `~/.claude/skills/claude-power-pack`) is overridable per-project if a repo ships its own `.claude/skills/claude-power-pack`.

### 3.2 Windows path resolution

On Windows, `~/.claude` resolves to **`%USERPROFILE%\.claude`** (here, `C:\Users\User\.claude`). This is overridable via the **`CLAUDE_CONFIG_DIR`** environment variable, which relocates the entire personal config root — relevant for multi-profile or sandboxed setups.

---

## 4. Progressive Disclosure and Context Economy

Skills are loaded through **progressive disclosure** — a deliberate strategy to keep the initial context window small:

- **At session start:** only the `description` frontmatter loads (max 1024 chars).
- **On demand (relevance-triggered):** the full `SKILL.md` body loads. Anthropic recommends keeping `SKILL.md` **under 500 lines**.
- **Further on demand:** supporting files alongside `SKILL.md` are **progressively loaded based on context relevance**, so a skill can bundle large reference material without paying the token cost upfront.

This three-tier loading (description → body → supporting files) is what makes it safe to ship rich skills: the model pays the full cost only when the skill is actually engaged. An important operational nuance: **edits to `SKILL.md` take effect immediately mid-session** — no reload is required for skill-body changes. (This contrasts sharply with hooks/MCP/agents, covered in Section 6.4.)

---

## 5. Frontmatter Contract — Full Field Reference

Beyond the two required fields, `SKILL.md` frontmatter supports a rich set of **optional** controls. Consolidating across the research:

| Field | Purpose / Values |
|---|---|
| `name` | required; lowercase, hyphens, ≤64 chars |
| `description` | required; WHAT + WHEN; ≤1024 chars; drives auto-discovery |
| `allowed-tools` | comma-separated **allowlist** of tools; default = all tools |
| `disallowedTools` | array **denylist** of tools |
| `effort` | `low` / `medium` / `high` |
| `maxTurns` | cap on agent turns |
| `model` | `opus` / `sonnet` / `haiku` |
| `context: fork` | run the skill in an **isolated subagent** |
| `user-invocable: false` | hide from direct user invocation |
| `disable-model-invocation` | prevent automatic (model-triggered) invocation |

### 5.1 Allowlist vs. denylist

Note the dual mechanism: `allowed-tools` (allowlist, comma-separated string) and `disallowedTools` (denylist, array). The default posture is **all tools available**, so authors tighten the surface either by enumerating what's permitted or by subtracting specific tools.

### 5.2 Runtime template variables (plugin-bundled skills only)

Plugin-bundled skills gain two runtime template variables unavailable to loose skills:

| Variable | Resolves to |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | the plugin's source-code directory |
| `${CLAUDE_PLUGIN_DATA}` | a **persistent state directory** that survives across sessions |

`${CLAUDE_PLUGIN_DATA}` is the sanctioned mechanism for a plugin skill to maintain durable state between sessions — distinct from the ephemeral source tree at `${CLAUDE_PLUGIN_ROOT}`.

---

## 6. Plugin Architecture

### 6.1 Convention-based component layout

A Claude Code **plugin** is a self-contained directory whose components live in **convention-based locations**. Claude Code auto-discovers them without explicit registration:

| Component | Default location | Minimum version |
|---|---|---|
| Skills | `skills/<name>/SKILL.md` | — |
| Agents | `agents/` | — |
| Hooks | `hooks/hooks.json` | — |
| MCP servers | `.mcp.json` | — |
| LSP servers | `.lsp.json` | — |
| Monitors | `monitors/monitors.json` | **v2.1.105+** |

### 6.2 The optional manifest

The **`.claude-plugin/plugin.json` manifest is optional**. If omitted:

- Claude Code **auto-discovers** components in their default locations.
- The plugin **name is derived from the directory name**.

When a manifest *is* present, **only `name` (kebab-case) is required**. If both `plugin.json` and a `marketplace.json` set a version, the **`plugin.json` version wins**.

### 6.3 Zero-install plugin variants

Two low-friction loading paths exist:

1. **Skills-directory plugins:** any folder *under a skills directory* that contains a `.claude-plugin/plugin.json` is loaded **in-place** as `<name>@skills-dir` on the next session — **no marketplace, no install step**.
2. **Bare-SKILL.md single-skill plugin:** in **Claude Code v2.1.142+**, a bare `SKILL.md` at a plugin root with **no `skills/` subdirectory** auto-loads as a single-skill plugin.

### 6.4 Hot-reload boundaries

A critical operational distinction for live editing:

| Change | Takes effect |
|---|---|
| `SKILL.md` edits | **Immediately, mid-session** |
| Hooks / `.mcp.json` / agents | Require **`/reload-plugins` or restart** |
| Monitor *path* changes after plugin update | Require **session restart** (not `/reload-plugins`) |

---

## 7. Merge Semantics — REPLACE vs. ADD

Plugin component sources do **not** share a single merge rule. This is one of the most error-prone areas for plugin authors, because the behavior of a custom path depends entirely on the component type:

| Component | When a custom path is set |
|---|---|
| `commands` | **REPLACE** the default scan |
| `agents` | **REPLACE** |
| `outputStyles` | **REPLACE** |
| `experimental.themes` | **REPLACE** |
| `experimental.monitors` | **REPLACE** |
| **`skills`** | **ADDS to** the default `skills/` scan |
| `hooks` | own per-source merge rules |
| `mcpServers` | own per-source merge rules |
| `lspServers` | own per-source merge rules |

The asymmetry is the headline: **`skills` is additive** (a custom `skills` manifest entry supplements the default `skills/` directory rather than overriding it), whereas `commands`, `agents`, `outputStyles`, and the experimental themes/monitors entries **wholesale replace** the default directory scan. Misunderstanding this leads to either accidentally hiding default agents/commands or expecting skills to be replaced when they are in fact merged.

### 7.1 Declaration flexibility for hooks/MCP/LSP

Hooks, MCP servers, and LSP servers may be declared **either**:

- as a **dedicated file at the plugin root** (`hooks/hooks.json`, `.mcp.json`, `.lsp.json`), **or**
- **inline within `plugin.json`**.

Both forms are valid; the choice is stylistic, but each follows its own per-source merge rules rather than the blunt REPLACE/ADD dichotomy above.

---

## 8. Security Model and Trust Boundaries

The plugin system enforces meaningful security restrictions that **differentiate plugin-shipped components from project-local ones** — and further restrict the zero-install `@skills-dir` variant.

### 8.1 Plugin agent restrictions

Plugin-shipped agents have **hard restrictions** on frontmatter. The following fields are **explicitly NOT supported** for plugin agents:

- `hooks`
- `mcpServers`
- `permissionMode`

For plugin agents, the **only valid `isolation` value is `worktree`**. The intent is clear: a distributed plugin agent must not be able to silently attach its own hooks, stand up its own MCP servers, or escalate its own permission mode.

### 8.2 Skills-directory plugin (`@skills-dir`) restrictions

The zero-install skills-directory variant is the **most restricted** packaging form. Compared to a fully installed plugin, an `@skills-dir` plugin is constrained as follows:

| Capability | `@skills-dir` behavior |
|---|---|
| MCP servers | Go through the **same per-server approval** as a project `.mcp.json` |
| LSP servers | Start **only after the workspace is trusted** |
| Background monitors | **Do NOT load at all** |

This makes `@skills-dir` a safe drop-in surface: it can ship skills freely, but anything with ambient execution power (MCP, LSP, monitors) is gated behind explicit trust or disabled outright.

### 8.3 Background monitors — trust level and lifecycle

Background monitors (requiring **v2.1.105+**) are the highest-privilege plugin component and carry the strictest operational caveats:

- They run **unsandboxed, at the same trust level as hooks**.
- They run **only in interactive CLI sessions** and are **skipped where the Monitor tool is unavailable**.
- Declared in `monitors/monitors.json` or inline `experimental.monitors`.
- Each runs a **persistent shell command**, piping **every stdout line to Claude as a notification**.
- A `when` field controls activation: **`always`** (default) or **`on-skill-invoke:<skill-name>`**.

**Lifecycle hazards:**

- **Disabling a plugin mid-session does NOT stop already-running monitors** — they stop only at **session end**.
- Picking up **path changes after a plugin update requires a session restart**, *not* `/reload-plugins`.

The combination of "unsandboxed, hook-level trust" + "survives mid-session disable" + "streams arbitrary stdout into the model's notification channel" makes monitors the single component most deserving of scrutiny before installing a third-party plugin. This dovetails with the local doctrine on background-process hygiene: a monitor that spawns a child process tree inherits all the orphan-reaping concerns that already apply to backgrounded dev servers on Windows.

---

## 9. Synthesis — Practical Implications

Drawing the findings together into actionable guidance for authoring under `claude-power-pack` or any skill/plugin directory:

1. **Write the `description` for discovery, not documentation.** It is the only text loaded at session start and must encode WHEN, not just WHAT. A skill with a vague description is effectively invisible.

2. **Keep `SKILL.md` under 500 lines and push bulk into supporting files.** Progressive disclosure means supporting files cost nothing until relevant — exploit this rather than inlining large references.

3. **Use precedence deliberately.** Project skills shadow personal skills shadow plugin skills. To override `claude-power-pack` for one repo, drop a same-named skill in that repo's `.claude/skills/`.

4. **Remember `skills` ADDS but `commands`/`agents`/`outputStyles` REPLACE.** Setting a custom `agents` or `commands` path silently hides the defaults; setting `skills` does not.

5. **Treat the manifest as optional but version-authoritative.** Omitting `plugin.json` triggers auto-discovery and directory-name naming; when present, `plugin.json`'s version beats `marketplace.json`.

6. **Plan for hot-reload boundaries.** Iterate freely on `SKILL.md` (instant), but budget a `/reload-plugins` or restart for hooks/MCP/agent changes — and a full restart for monitor path changes.

7. **Default to the least-privileged packaging.** `@skills-dir` is the safest distribution surface; reserve installed plugins (and especially monitors) for cases that genuinely need ambient execution, and audit any third-party plugin's monitors before trusting it.

8. **Account for the security asymmetry.** Plugin agents cannot ship their own hooks/MCP/permissionMode; `@skills-dir` MCP/LSP are trust-gated and its monitors never load. Anything that needs those must come through a fully installed, trusted plugin.

---

## 10. Open Questions / Gaps

The research did not surface details on: the exact per-source merge algorithm for `hooks`/`mcpServers`/`lspServers` (only that they have "their own rules"); the precise relevance-scoring mechanism that decides when supporting files load; or whether `effort`/`maxTurns`/`model` frontmatter fields interact with the host session's own model routing (e.g., the TCO model-routing doctrine). These would be worth confirming against the live `agentskills.io` standard and the Claude Code changelog before relying on them in production tooling.

## Sources

- <https://github.com/anthropics/skills>
- <https://code.claude.com/docs/en/claude-directory>
- <https://computingforgeeks.com/claude-code-dot-claude-directory-guide/>
- <https://dotclaude.com/skills>
- <https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf?hsLang=en>
- <https://code.claude.com/docs/en/plugins-reference>
- <https://www.paradime.io/guides/claude-code-skills-plugins-rules-guide>
- <https://skillsplayground.com/guides/claude-code-plugins/>
- <https://github.com/jeremylongshore/claude-code-plugins-plus-skills>
- <https://deepwiki.com/victor-software-house/claude-code-docs/3.5.1-plugin-system>
- <https://www.morphllm.com/install-claude-code>
- <https://alexop.dev/posts/understanding-claude-code-full-stack/>

_Note: 3 URL(s) also appeared in prior runs of this prompt (not duplicates in current run; see index.json for full history)._

## Run metadata

- **Prompt:** Base directory for this skill: C:\Users\User\.claude\skills\claude-power-pack
- **Depth / breadth:** 2 / 3
- **Queries used:** 4 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 583.7 s
- **Errors during run:** 2
- **Started at:** 2026-05-30T09:59:10Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `extract_learnings: claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--append-system-prompt', "You are an expert researcher. Today is 2026-05-30. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 120 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `fetch_page 'https://mcpmarket.com/tools/skills/claude-code-plugin-refere...': page-fetch: https://mcpmarket.com/tools/skills/claude-code-plugin-reference-2026: HTTP Error 429: Too Many Requests`

</details>
