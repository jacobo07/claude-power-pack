---
type: source
created: 2026-09-30
updated: 2026-09-30
sources: [2026-09-30-system-prompts-leaks]
raw: raw/2026-09-30-system-prompts-leaks/
kind: repo
origin: https://github.com/asgeirtj/system_prompts_leaks @ b632b67
---

# system_prompts_leaks (asgeirtj)

CC0-licensed repo of what it presents as verbatim system prompts from AI products; 735 files at
`b632b67` (2026-09-30), 547 under `Anthropic/`. Includes Claude Code's system prompts per model
(~370 KB each), built-in agents (Explore, Plan, general-purpose, ...), `/compact`, output styles,
and skills.

**Status: reported, not official.** Leaked captures; authenticity and completeness unverified. Cite as
"reported Claude Code behaviour @ b632b67", never as documentation.

## Storage policy

`raw/` holds `MANIFEST.txt` (full file list at the pinned commit) plus only the files a wiki page
cites, byte-for-byte. Currently: `Anthropic/claude-code/commands/compact.md`.

## Key points so far

- The `/compact` summarizer reportedly tells the model to follow "additional summarization
  instructions" found in context, with `## Compact Instructions` as the example.
  → [[compact-instructions-section]]
- It also keeps all user messages, the pending tasks, and security constraints verbatim, and quotes
  the most recent request word for word to prevent drift.
- The Claude Code base prompt (~368 KB for Opus 5.5; the size includes tool definitions) is the
  reference for which PP rules only restate built-in behaviour. → [[always-loaded-prefix-audit]]

## Not yet read

Built-in agents, output styles, advisor-tool prompt, the Claude Code base prompt itself. Read on
demand, one file per question; copy into `raw/` when cited.
