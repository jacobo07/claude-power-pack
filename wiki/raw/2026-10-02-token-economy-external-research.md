# Token / context economy: external research

Purpose: external evidence for PP state-centric execution. Date: 2026-10-02. Bound: <=30 web calls, ~50 min. Tiers: A official/controlled with numbers, B practitioner with numbers, C opinion.

## Q1 Prompt caching mechanics
- Cache write 1.25x base input (5m TTL), 2x (1h TTL); cache read 0.1x standard, 0.05x Opus 5.5, 0.025x Fable 5.1/Mythos 5.1 -- https://platform.claude.com/docs/en/build-with-claude/prompt-caching (accessed 2026-10-02) -- A
- Min cacheable: 512 tok (Fable 5.1, Mythos 5.1, Opus 5.5, Sonnet 5.5); 1,024 (Sonnet 5/4.6/4.5, Opus 4.8); 2,048 (Opus 4.7); 4,096 (Haiku 4.5, Opus 4.6/4.5). Shorter = silently uncached -- same URL -- A
- Invalidation hierarchy tools -> system -> messages. Changing tool definitions invalidates all three levels; toggling web search/citations or speed invalidates system+messages; tool_choice change or adding/removing images invalidates messages; thinking/effort config effects are model-specific -- same URL -- A
- A breakpoint on per-request-changing content (timestamp, user message) never hits; lookback window is 20 blocks; up to 4 breakpoints -- same URL -- A
- API rate limits: cache_read_input_tokens do NOT count toward ITPM; only cache creation + uncached input do -- same URL -- A. The docs do NOT say cache reads are free for SUBSCRIPTION weekly limits; Claude Code costs page says each request re-reads history "at the cached token rate" and a one-line question still "draws usage for the whole conversation". Exact subscription weighting of cache reads: UNKNOWN (not documented numerically).
- Cache lifetime in Claude Code: 1 hour on a subscription; 5 min once on usage credits or on API key/cloud by default; first message after a longer break reprocesses the full context -- https://code.claude.com/docs/en/costs -- A
- /usage shows a "Prompt cache (main)" line (hit share, misses, expected rebuilds; main conversation only, NOT subagents) and a plan-usage attribution by skill/subagent/plugin/MCP plus behaviour flags at >=10% (long context, cache misses) -- same -- A

## Q2 Claude Code specifics (https://code.claude.com/docs/en/costs, accessed 2026-10-02)
- Average ~$13/dev/active day, $150-250/dev/month, <$30/day for 90% of users (API-equivalent) -- A
- /clear between unrelated tasks costs nothing; /compact reads the whole conversation so compacting a large context is itself a large request -- A
- Compact instructions may live in CLAUDE.md under "# Compact instructions" -- A
- MCP tool definitions are deferred by default (tool search): only names + server instructions in context until used; /context shows consumers; CLI tools (gh, aws) cheaper than MCP -- A
- Hooks can preprocess (grep ERROR from a 10k-line log: "tens of thousands of tokens to hundreds"; claim only, no benchmark) -- A(claim)
- Move workflow instructions from CLAUDE.md into skills (loaded on demand); keep CLAUDE.md under 200 lines -- A
- Subagents keep verbose output in their own context, only summary returns, but their requests still draw on usage; use model: haiku for simple ones -- A
- Agent teams use ~7x tokens of a standard session (plan-mode teammates); each loads CLAUDE.md, MCP, skills -- A
- Long-session drivers: full history resent each request, cache misses after idle > TTL, scheduled tasks/loops, cross-session messages, goal check-ins (max 3 idle), subagents/workflows, compaction -- A
- Teams/Enterprise: 5-hour + weekly windows; session/weekly limits shared across models (/model switch does not restore, except model-specific Opus/Sonnet messages) -- A
- Thinking billed as output; /effort and MAX_THINKING_TOKENS reduce; cannot be disabled on Opus 5.5/Sonnet 5.5/Fable -- A
- Plan mode, Esc, /rewind to avoid wasted exploration -- A (qualitative)

## Q3 Context engineering
- Anthropic: recall accuracy falls as context tokens rise ("context rot"); finite attention budget; recommends just-in-time retrieval (lightweight identifiers + tools), compaction, structured note-taking to memory outside the window, sub-agents with clean windows returning condensed summaries -- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (accessed 2026-10-02) -- A (guidance, no numbers in the extract)
- Anthropic multi-agent research system: agents use ~4x tokens of chat, multi-agent ~15x (VERIFIED); token usage alone explained 80% of BrowseComp performance variance; Opus-4 lead + Sonnet-4 subagents beat single-agent Opus 4 by 90.2%; subagents should write outputs to external storage and return lightweight references -- https://www.anthropic.com/engineering/multi-agent-research-system (accessed 2026-10-02) -- A. Implication: tokens buy quality on breadth tasks; fan-out is a cost choice, not a free win.
- Chroma "Context Rot" (2025-07-14): 18 LLMs (Anthropic, OpenAI, Google, Qwen); performance varies with input length even on simple tasks; LongMemEval shows significant gap between focused (~300 tok) and full (~113k tok) prompts across all families; even a single distractor lowers accuracy; shuffled haystacks beat coherent ones -- https://www.trychroma.com/research/context-rot -- A (controlled, specific percentages not extracted)
- NoLiMa (arXiv 2502.05167, Adobe): at 32K tokens 11 of 13 models fell to <=50% of their short-context baseline; GPT-4o 99.3% base -> 69.7% @32K -> 56% @128K; many models have effective length <=2K on latent-association needles -- https://arxiv.org/abs/2502.05167 (via search snippet, accessed 2026-10-02) -- A. Caveat: older models, not Claude 4/5-class.
- Chroma: Claude models lowest hallucination rates under distractors (their own claim) -- same -- B

## Q4 Measured techniques
- JetBrains Research (2025-12), SWE-bench Verified 500 instances, Qwen3-32B/Qwen3-Coder 480B/Gemini 2.5 Flash, up to 250 turns: observation masking (hide old tool outputs, keep 10-turn window) and LLM summarization (21 turns at a time, keep 10 recent) both cut cost >50% vs unmanaged; masking on Qwen3-Coder 480B 52% cheaper and +2.6% solve rate; hybrid 7% cheaper than masking, 11% cheaper than summarization; summarization lengthened trajectories ~13-15% -- https://blog.jetbrains.com/research/2025/12/efficient-context-management/ -- A. Cheap masking matches costly summarization.
- OpenHands LLMSummarizingCondenser (blog 2025-04-09): up to 2x per-turn cost reduction; cost grows linearly instead of quadratically; SWE-bench Verified ~54% with vs ~53% without -- https://www.openhands.dev/blog/openhands-context-condensensation-for-more-efficient-ai-agents -- A (vendor, small delta within noise)
- Anthropic context editing + memory tool: in a 100-turn web-search eval, context editing cut token use 84% and let workflows finish that otherwise exhausted context; +29% (editing) / +39% (editing+memory) vs baseline on internal agentic-search set; the blog does not discuss cache interaction -- https://claude.com/blog/context-management (accessed 2026-10-02) -- A (vendor, internal eval). Default trigger 100k input tokens, keeps 3 recent tool results (secondary source, medium-confidence).
- TokenPilot (arXiv 2606.17016): compressing/evicting context rewrites the prefix and invalidates the cache; keeping cache continuity limits compression. Stabilising the prefix + conservative eviction gave 56-87% cost reduction across modes -- https://arxiv.org/abs/2606.17016 -- A/B (single preprint, not replicated). KEY for PP: compaction is not free under caching; cache-aware layout matters.
- Subagent fixed cost (practitioner, JSONL-measured): headline "436k tokens fixed overhead per subagent" was later CORRECTED: it was cumulative billed tokens (cached prefix re-delivered each request); true cold-start was ~54,154 cache_creation tokens for a probe subagent; payload ~46k. Overhead = system prompt + MCP schemas + skills, constant per spawn -- https://dev.to/rulestack/what-a-claude-code-subagent-actually-costs-measuring-the-436k-token-fixed-overhead-46g6 -- B (single author, self-corrected). Consistent with PP's internal ~95k median first call. Recommendations: merge overlapping agents, spawn only for genuine independence, trim MCP/CLAUDE.md.
- Claude Code issue #46526: users report CLAUDE.md+rules+memory index+skill listings+MCP schemas re-sent every turn dominate usage; issue has no per-component numbers and was closed as duplicate -- https://github.com/anthropics/claude-code/issues/46526 -- C
- A search snippet (unfetched) cites ~2,900 base system-prompt tokens + 18+ tool definitions and 10-20K per-subagent startup in other write-ups; unverified, tier C.
- Aider repo map: tree-sitter symbols -> file/reference graph -> personalised PageRank -> binary-search packing into a fixed token budget (--map-tokens default 1,024) sent each request -- https://aider.chat/2023/10/22/repomap.html (via search, accessed 2026-10-02) -- B (design; no savings number)
- Agentless (arXiv 2407.01489): fixed 3-phase pipeline (localize, repair, validate), no agent loop: 27.33% SWE-bench Lite at $0.34/issue vs ~$3.34 for some agent approaches (~10x) -- https://github.com/OpenAutoCoder/Agentless (via search, 2024 numbers, accessed 2026-10-02) -- A. Dated: models/agents have since improved.
- Anthropic advanced tool use (via secondary summaries; primary page fetched next): Tool Search 77K -> 8.7K tokens (85%); Programmatic Tool Calling 43,588 -> 27,297 avg tokens (37%); tool-use examples 72% -> 90% accuracy -- https://ascii.co.uk/news/article/news-20251125-85f14942/anthropic-releases-three-advanced-tool-use-features-for-ai-a -- B pending primary check
- Anthropic "code execution with MCP": 150,000 -> 2,000 tokens (98.7%) when the agent writes code against tool APIs and intermediate results stay in the execution environment; loops/conditionals run in code, not model turns; needs sandbox -- https://www.anthropic.com/engineering/code-execution-with-mcp (accessed 2026-10-02) -- A (vendor example, single scenario)
- Model routing: FrugalGPT (Stanford 2023) up to 98% cost cut at GPT-4 parity or +4% accuracy at equal cost; RouteLLM (Berkeley, ICLR 2025) >85% cost cut on MT-Bench at ~95% of GPT-4 quality, 45% on MMLU, 35% on GSM8K -- https://arxiv.org/abs/2305.05176 and secondary summaries (search, accessed 2026-10-02) -- A for FrugalGPT, B for RouteLLM figures (secondary). Chat/QA benchmarks, not agentic coding.
- Subscription limits: Anthropic support says usage depends on conversation length/complexity, features, model and effort; tools and connectors are "token-intensive"; tips: lower effort, disable thinking, turn off unneeded tools/connectors, concise project instructions -- https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work -- A. No weekly numbers published there.
- Practitioner measurement (one heavy Claude Code user, Sept 2026 logs): Max 20x weekly cap hit at ~1.9B tokens; 7.0B cache-read tokens = 96% of volume and 50% of an API-equivalent $6,986 Opus bill; article asserts cache reads DO count toward weekly limits but this is inferred from totals, not from Anthropic documentation -- https://finopsllm.com/research/claude-pro-max-tokens-limit -- C/B (n=1, inferred). Matches the Owner's incident shape (cache reads dominate).
- Anthropic announced on 2026-05-06 doubled Claude Code 5-hour limits for Pro/Max/Team (via secondary search snippets, not primary) -- C.
- Message Batches API: 50% cost reduction, most batches finish <1 hour, asynchronous -- https://platform.claude.com/docs/en/build-with-claude/batch-processing (accessed 2026-10-02) -- A. Fits non-interactive gate/eval workloads; Claude Code subscription sessions cannot use it directly (unknown/not applicable).
- Skills progressive disclosure: startup loads only name+description (~100 tok each per secondary sources), body (<5k) on invoke, references on demand -- https://claude.com/blog/skills-explained and https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (search snippets, accessed 2026-10-02) -- B. Implication: a listing of ~190 skills is a standing per-call cost (PP-specific arithmetic, unmeasured here).
- Ordinary subagents do not inherit the parent conversation or files read; they get a delegation message + CLAUDE.md and re-discover the codebase -- secondary summary (levelup.gitconnected.com, search snippet) -- C; consistent with Owner's premise.
- Lost in the Middle (Liu et al., arXiv 2307.03172): accuracy is highest when relevant info is at the start or end of the context and degrades significantly in the middle, even for long-context-trained models -- https://arxiv.org/abs/2307.03172 -- A (2023 models). Implication: put the goal/state at the top and the current ask at the end; keep middle small.
- Not verified this session (no fetch, bound/time): LangGraph checkpoints, Letta/MemGPT memory tiers, SWE-agent history processors. Design is public but no savings numbers obtained -- UNKNOWN.

## Q5 Deterministic work offloaded from LLMs
- Agentless: fixed pipeline with no agent loop reached 27.33% at $0.34/issue vs ~$3.34 for agent approaches on SWE-bench Lite (2024) -- see Q4 -- A
- Code execution with MCP: loops/filters/aggregation in code, 150k -> 2k tokens -- see Q4 -- A (vendor)
- Programmatic tool calling: orchestrating tools by script cut avg tokens 43,588 -> 27,297 (37%) and removed 19+ inference passes -- secondary source (ascii.co.uk) -- B, primary not fetched
- Claude Code hooks: preprocessing tool output with grep/filters "tens of thousands of tokens to hundreds" -- https://code.claude.com/docs/en/costs -- A (claim, no benchmark)
- Anthropic multi-agent: write artifacts to filesystem, return references -- see Q3 -- A
- No controlled study found of "scheduler that runs only deterministic gates" specifically (quality or cost). Interpretation: the evidence above supports it by analogy (Agentless, code-exec), not directly. UNKNOWN.

## Checklist
1. Treat cache reads as the cost driver: measure cache_read vs output per session (/usage Prompt cache line) | A | Owner incident 6.23B cache read vs 19.1M output; cache read priced 0.1x but still counted | costs doc
2. Keep fixed floor small (system prompt, CLAUDE.md, rules, skill listing, MCP) because it is re-read every request, in every subagent | A | PP floor ~91-111k; each subagent cold start ~54k cache-create in one probe | costs doc, dev.to
3. Keep CLAUDE.md under 200 lines; move workflow detail to skills | A | smaller always-on prefix | costs doc
4. Skills: description-only at startup; keep descriptions short and prune unused skill listings | B | ~100 tok/skill listed | skills-explained
5. Rely on deferred MCP tool search; disable unused MCP servers; prefer CLI (gh) over MCP | A | tool search 77K -> 8.7K (85%) | advanced-tool-use summary
6. Never change tool definitions mid-session (invalidates tools+system+messages cache) | A | avoids full re-write at 1.25x/2x | caching doc
7. Layout static first, dynamic last: tools, system, stable state, then volatile task; no timestamps in prefix | A | cache hits require identical prefix | caching doc
8. Put the goal/state at start and current ask at end of context | A | mitigates lost-in-the-middle | arXiv 2307.03172
9. Compile per-invocation context from on-disk state instead of replaying transcripts | B | JetBrains/OpenHands: bounded context gives linear not quadratic cost, >50% savings | JetBrains, OpenHands
10. Mask old tool outputs (keep last ~10 turns) before paying for LLM summarisation | A | masking 52% cheaper, +2.6% solve vs unmanaged; as good as summarising | JetBrains 2025-12
11. Use context-editing / tool-result clearing for long loops | A | 84% token cut in 100-turn eval | claude.com/blog/context-management
12. Be aware compaction/clearing rewrites the prefix and breaks cache; do it at deliberate boundaries, not continuously | B | TokenPilot 56-87% savings when prefix stabilised | arXiv 2606.17016
13. /clear between unrelated tasks (free); /compact is a large request itself | A | no re-read of stale history | costs doc
14. Resume large idle sessions from summary; avoid idling beyond cache TTL (1h subscription) | A | avoids full-context cache miss | costs doc
15. Use a disposable worker with a fresh minimal context per task, handing off a structured file (path + facts), not a transcript | A | Anthropic subagent pattern: write to storage, return reference | multi-agent post
16. Do not spawn a subagent for a small task; merge overlapping subagents; spawn only for independence or parallelism | B | each spawn pays fixed floor | dev.to
17. Budget fan-out explicitly: multi-agent ~15x chat tokens, agents ~4x; justify with quality gain | A | 90.2% gain on research tasks at 15x | multi-agent post
18. Right-size subagent model: Haiku/Sonnet for exploration/tests/docs | A | smaller per-token price; Anthropic doc recommends | costs doc
19. Route by task difficulty (cascade/router) | B | 45-85% cost cuts on chat benchmarks, not agentic coding | FrugalGPT, RouteLLM
20. Offload deterministic checks to scripts/hooks/schedulers; model sees only the failing lines | A | hook example tens of thousands -> hundreds tokens | costs doc
21. Prefer fixed pipelines over agent loops when the procedure is known | A | Agentless $0.34 vs ~$3.34 per issue (2024) | Agentless
22. Let code orchestrate tool calls and keep intermediates out of context | A | 150k -> 2k; 43.6k -> 27.3k | code-exec-with-MCP, PTC
23. Pre-filter tool output (head/limit/grep, repo-map style budgeted summaries) | B | Aider fixes map at ~1k tokens | aider.chat
24. Use batch API for non-interactive gate/eval jobs run via API | A | 50% off | batch doc
25. Lower /effort and thinking budget for routine steps | A | thinking is billed as output | costs doc
26. Cap background loops, scheduled tasks and idle check-ins | A | each fires with full context | costs doc
27. Keep durable notes outside context (memory files) and re-read only needed parts | A | memory+editing +39% | claude.com/blog/context-management
28. Specific prompts with file targets; plan mode for big tasks | A | avoids broad scans and rework | costs doc
29. Use /usage attribution (skills, subagents, MCP, behaviour flags) to find the top 10% sinks before optimising | A | direct per-source shares | costs doc
30. Verify any saving with an A/B on the same task (the cache makes per-call estimates misleading) | C | n/a | interpretation

## Contradictions / unknowns
- Subscription weekly-limit weighting of cache reads: API ITPM excludes cache reads (A), Claude Code docs say history re-read "draws usage" (A), a practitioner infers they count (C). No official coefficient. Needs Owner-side measurement (before/after weekly % vs cache-read tokens).
- Compression vs caching: context editing/compaction saves tokens but breaks the prefix cache; TokenPilot is a single unreplicated preprint; Anthropic's context-management post is silent on this.
- Summarisation vs masking: OpenHands reports summarisation equal quality; JetBrains finds masking as good and cheaper and summaries lengthen runs 13-15%.
- Multi-agent: 15x tokens but +90.2% quality on research tasks; Claude Code costs doc says subagents isolate verbose output. Net cost depends on task; for coding (less parallelisable) evidence is not given.
- "436k per subagent" figure circulated and was self-corrected to ~54k cold-start; do not quote 436k.
- Long-context studies (NoLiMa, Chroma, Lost in the Middle) predate or exclude Claude 5-class models; magnitude for current Claude is unmeasured here.
- Plan limits changes (e.g. doubled 5-hour limits 2026-05-06) come only from secondary snippets.
- Model names/prices in the official docs (Opus 5.5, Fable 5.1, Sonnet 5.5) were read from fetched pages as of 2026-10-02; not independently cross-checked.
- Not covered: LangGraph checkpoints, Letta tiers, SWE-agent history processors, output styles, --bare mode, auto-compact threshold value (docs reference a configurable window; value not extracted).
- Web calls used: about 28 of 30.
