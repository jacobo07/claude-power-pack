# Research Report — INSUFFICIENT DATA

Prompt: How do Wii/GameCube decompilation projects identify, from the binary alone, which Metrowerks CodeWarrior build (GC 1.x/2.x/3.x, Wii 1.0-1.7 etc.) and which compiler flags (-O4,p vs -O4,s, -inline auto/deferred, -fp_contract, -sdata/-sdata2 thresholds, -schedule, -use_lmw_stmw, -enum, -str pool/readonly, #pragma per function) compiled each translation unit? What codegen fingerprints (prologue/epilogue shape, lmw/stmw use, register save order, scheduling, float constant placement, string pooling) discriminate them, and how do dtk configs (configure.py, mw_version, cflags per object) record the answer? For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.

The research run completed without extracting any learnings. This can happen when SERP results were empty across all queries, page-fetch failed for every result, or every source landscape was vendor-only and the coverage gate refused to build claims on it. Re-run with different keywords or check vault/cache_hints/CEILING.md for the layer-by-layer failure log.

## Sources

_(none collected)_

## Run metadata

- **Prompt:** How do Wii/GameCube decompilation projects identify, from the binary alone, which Metrowerks CodeWarrior build (GC 1.x/2.x/3.x, Wii 1.0-1.7 etc.) and which compiler flags (-O4,p vs -O4,s, -inline auto/deferred, -fp_contract, -sdata/-sdata2 thresholds, -schedule, -use_lmw_stmw, -enum, -str pool/readonly, #pragma per function) compiled each translation unit? What codegen fingerprints (prologue/epilogue shape, lmw/stmw use, register save order, scheduling, float constant placement, string pooling) discriminate them, and how do dtk configs (configure.py, mw_version, cflags per object) record the answer? For every claim give the primary source (repo file, issue, PR, compiler manual) and state it as a falsifiable prediction: 'with X, mwcc emits Y; with X', it emits Y''. Mark anything unverified.
- **Depth / breadth:** 2 / 4
- **Queries used:** 0 (budget 30)
- **Layers fired:**
  - search: (none)
  - markdown: (none)
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 125.3 s
- **Errors during run:** 2
- **Started at:** 2026-11-11T19:00:24Z
- **Module version:** deep_research 0.4.0
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 0 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 0/5 axes searched
- **E2 landscape:** no sources classified · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** no learnings persisted · 0 label(s) demoted by the evidence gates
- **E4 contradictions:** 0 unresolved conflict(s) (detector: skipped-too-few-learnings)
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `generate_serp_queries: claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '--model', 'claude-sonnet-5-5', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--setting-sources', 'local', '--strict-mcp-config', '--append-system-prompt', "You are an expert researcher. Today is 2026-11-11. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 120 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `no SERP queries generated`

</details>


## Evidence ledger

- **Claims:** 0 · with a verified quote: 0 (rate None)
- **Quotes:** 0 offered, 0 rejected (not verbatim / unknown source / length)
- **Sources:** 0 snapshots in 0 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 0
- **Sources with instruction-like text (treated as data):** 0
