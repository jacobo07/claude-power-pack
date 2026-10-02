---
type: source
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-external-research-2]
raw: raw/2026-10-02-token-economy-external-research-2.md
kind: note
origin: research subagent output, 2026-10-02, ~29 web calls (wave 2, gaps of wave 1)
---

# Source — Token economy external research, wave 2 (2026-10-02)

Agent survey of Claude Code knobs, history processors, prompt compression, code retrieval and
coding-agent cost studies, with tiers per claim. Spot-checked here: the installed CLI (2.1.288)
lists `--exclude-dynamic-system-prompt-sections`, `--autocompact`, `--safe-mode`,
`--setting-sources`, `--system-prompt-snapshot`, `--strict-mcp-config`, `--effort`, `--bare` in
its help text. Other claims are as the agent reported; snippet-only numbers are marked in raw.

## Key takeaways

1. **The cache TTL is a setting** (`promptCacheTtl` / `CLAUDE_CODE_PROMPT_CACHE_TTL`); subagents,
   compaction and forks default to 5 min on a subscription, the main thread to 1 h (raw, Q8).
2. **Cache scope is per machine + directory**; sequential sessions share cache only when the
   startup context matches; `--exclude-dynamic-system-prompt-sections` "improves prompt-cache
   reuse" (raw, Q1, Q8).
3. **Hooks can rewrite tools**: PreToolUse `updatedInput`, PostToolUse `updatedToolOutput`
   ("replaces the tool's result"; per-tool scope UNKNOWN) (raw, Q2).
4. **Skills can be hidden**: `skillOverrides` on | name-only | user-invocable-only | off;
   listing budget 1 % of the context window (raw, Q1).
5. **Auto-compact window is settable** (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`, `--autocompact`);
   warm compaction "costs a fraction of what the context size suggests" (raw, Q1).
6. **Built-in Explore runs on the Opus alias on a subscription**; `CLAUDE_CODE_SUBAGENT_MODEL`
   overrides (raw, Q1).
7. **Measured studies:** re-sent input dominates coding-agent cost, runs vary ~2× on the same
   task; developer-written skills that stop repeat retrieval save 7.9-41.7 %; LSP raises tokens
   +6 % to +118 % on localisation; query-aware prompt compression breaks caching (+40.1 % cost)
   while compressing a static prefix once saved 51.7 % (raw, Q4-Q6).
8. **Still unknown:** how subscription limits weigh cache reads (raw, Contradictions).

## Pages touched

[[token-economy-brainstorm]], [[token-economy-levers]], [[cold-start-cache-sharing]],
[[hide-unused-skills]], [[hook-injection-diet]], [[tool-output-at-source]].
