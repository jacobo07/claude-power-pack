---
type: source
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-external-research]
raw: raw/2026-10-02-token-economy-external-research.md
kind: note
origin: research subagent output, 2026-10-02, ~28 web calls (committed @ 3b07419)
---

# Source — Token / context economy: external research (2026-10-02)

Agent-compiled survey with an evidence tier per claim (A official/controlled, B practitioner with
numbers, C opinion) and a 30-item checklist. Spot-checked here: the cache multipliers agree with
PP's price table (see [[token-economy-levers]], caveats). Other figures are as the agent reported.

## Key takeaways

1. **Cache mechanics decide cost.** Write 1.25× (5 m) or 2× (1 h) input; read 0.05× on Opus 5.5.
   Changing tool definitions invalidates tools, system and messages; a breakpoint on changing
   content never hits (raw, Q1). Claude Code uses a 1 h TTL on a subscription (raw, Q1).
2. **Masking old tool output is as good as summarising, and cheaper.** JetBrains, SWE-bench
   Verified: masking 52 % cheaper and +2.6 % solve rate on Qwen3-Coder 480B; summaries lengthen
   runs 13-15 % (raw, Q4, tier A).
3. **Context editing cut tokens 84 %** in a 100-turn vendor eval; compaction rewrites the prefix
   and breaks the cache (TokenPilot preprint) — compaction is not free (raw, Q4).
4. **Subagent cold start is ~54k cache-create, not 436k** (practitioner, self-corrected); fan-out
   is a cost choice: multi-agent ~15× chat tokens for +90.2 % on research tasks (raw, Q3-Q4).
5. **Deterministic work belongs in code.** Agentless ~10× cheaper per issue (2024); code execution
   with MCP 150k → 2k tokens in one vendor scenario (raw, Q5).
6. **Long context degrades recall** (NoLiMa, Chroma, Lost in the Middle), measured on older or
   non-Claude-5 models (raw, Q3).
7. **Unknown:** how the subscription meter weighs cache reads; no official coefficient (raw,
   Contradictions).

## Pages touched

[[token-economy-levers]], [[tool-output-at-source]], [[mid-session-prefix-rebuilds]],
[[sdk-probe-floor]], [[always-loaded-prefix-audit]].
