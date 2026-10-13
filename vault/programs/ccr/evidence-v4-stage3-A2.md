# Evidence v4 Stage 3 A2 -- 21K anatomy and hard floor

All numbers: Linux plane GEX44, host 2.1.296 (the receipts of V1 and Madzia sessions were produced on the laptop plane by host 2.1.296 and are analysed here on GEX44; the probes ran on GEX44). Tool: `tools/ccr_anatomy.py` (tests `tools/test_ccr_anatomy.py`, 17/17 PASS). Full per-bucket tables: `vault/programs/ccr/stage3/a2/anatomy-detail.md`, machine form `a2/anatomy.json`.

## Calibration (measured, not assumed)
- Call 1: **2.999 bytes/token**, the pooled within-group slope of ctx(call 1) on sized bytes (sections + sent attachments + prompt) over 35 sessions in 11 groups that share a tool configuration (same offered-tool count, traits, section bytes, deferred tools), so the unknown tool-schema cost cancels.
- Carry: **2.491 bytes/token**, a through-origin fit of the step tokens on the bytes added between calls (1,031 steps with no image change).
- Check: probe P4 (every switch off) decomposes to its ctx with a residual of **-6 tokens**.

## Anatomy, call 1 and carry (tokens)
`tools+framing` = ctx minus every sized bucket. The receipts hold no schema bytes for tools kept in front, so it is a residual and is not split.

| session | run | calls | ctx call 1 | sections | attachments sent | prompt | tools+framing | ctx last | carry: tool results / responses / late attachments / images / residual |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 403d2d16 | V1 r1 OFF | 4 | 74,594 | 3,117 | 44,742 | 156 | 26,576 | 80,375 | 3,409 / 1,376 / 375 / 0 / 621 |
| 8c3d8a8e | V1 r2 CCR | 4 | 18,308 | 2,403 | 5,881 | 156 | 9,865 | 24,573 | 3,148 / 1,694 / 943 / 0 / 481 |
| f898280c | V1 r3 OFF | 6 | 74,809 | 3,117 | 44,896 | 156 | 26,637 | 81,672 | 4,027 / 1,986 / 253 / 0 / 597 |
| fa1e65cd | V1 r4 CCR | 4 | 18,077 | 2,403 | 5,715 | 156 | 9,799 | 22,049 | 1,801 / 1,585 / 929 / 0 / -343 |
| 4f0ecc00 | V1 r5 OFF | 6 | 74,594 | 3,117 | 44,742 | 156 | 26,576 | 82,456 | 4,500 / 1,918 / 390 / 0 / 1,054 |
| 0bdd6fe2 | Madzia unit (lean+print, 7 tools) | 23 | 18,137 | 1,427 | 1,552 | 42 | 15,113 | 65,566 | 12,786 / 31,116 / 1,877 / 5,328 / -3,677 |
| bf6d4b07 | Madzia unit (7 tools) | 26 | 17,235 | 1,427 | 1,430 | 42 | 14,333 | 99,443 | 18,631 / 61,784 / 2,179 / 7,869 / -8,254 |
| f03c1c84 | Madzia unit (7 tools) | 31 | 19,100 | 1,427 | 1,816 | 42 | 15,812 | 83,561 | 15,635 / 48,057 / 1,969 / 7,292 / -8,807 |
| b0de7339 | Madzia unit (2 tools) | 3 | 6,458 | 1,427 | 1,584 | 27 | 3,417 | 18,709 | 0 / 1,595 / 39 / 10,483 / 133 |

Largest attachments in V1 OFF (r1): instructions 26,142, agent_listing_delta 8,750, skill_listing 5,022, hook_additional_context 1,853 tokens. V1 CCR (r2): hook_additional_context 1,853, instructions 1,606 (kernel replace), deferred_tools_delta 1,436, environment 315.

Call-1 by class (V1 r2 CCR, 18,308): REDUCIBLE 14,254 (of which tools+framing 9,865 and hook context 1,853), IRREDUCIBLE 2,264, PAGEABLE 1,436 (deferred_tools_delta), ELIMINABLE 197, UNKNOWN 154. V1 r1 OFF (74,594): REDUCIBLE 55,501, ELIMINABLE 15,390, IRREDUCIBLE 2,264, PAGEABLE 1,436.

Findings:
1. **The "21K floor" is mostly tool schemas, and they are controllable.** In V1 CCR, tools+framing is 9.9K of 18.3K (54 %). In the Madzia 7-tool workers it is 14.3-15.8K of 17-19K (about 83 %). The 2-tool Madzia session drops to 3.4K at equal attachments. Tool schemas are controllable through `--tools` and unit deferral, so they are REDUCIBLE, not a floor. Deferring tools outside the unit took tools+framing from 26.6K (V1 OFF) to 9.9K (V1 CCR).
2. Madzia rent is carry. Assistant turns (responses) dominate it: 31-62K by the last call against 13-19K of tool results. The carry residual there is -3.7K to -8.8K, which means the response bytes overcount what is re-sent: thinking and sealed blocks of earlier turns are not carried 1:1. The `carry:response` class (HOST_LIMITED) is therefore an estimate with that error.
3. V1 carry is small (5-7K at the last call). The V1 saving is entirely the call-1 closure.
4. Classes and their evidence are listed in `CLASSIFICATION` in `tools/ccr_anatomy.py`. Tool-result carry is EMBODIABLE for V1 because its answer is script-computable (truth.py): DETERMINISTIC_PATH. In other sessions it is PAGEABLE.

## Hard-floor registry (`vault/programs/ccr/hard_floor_registry.json`)
Four one-call probes: `claude -p --model haiku` (host 2.1.296, `~/.local/bin/claude`), run from /home/kobii/missions/ccr-s3 with `--plugin-dir mods/cpp-cognitive-runtime` and `CCR_WORK_UNIT={"class":"bounded-code-worker","id":"a2-probe"}`. RAM admission: MemAvailable 54.5-57.7 GB before each probe. Every probe answered `OK` in 1 turn.

| probe | config | tools in init | ctx call 1 | delta | what the delta removed |
|---|---|---:|---:|---:|---|
| P1 | defaults + unit | 35 | 14,269 | -- | -- |
| P2 | P1 + `--tools ""` | 8 (MCP) | 13,361 | -908 | built-in tools kept in front by the unit |
| P3 | P2 + `--strict-mcp-config --disable-slash-commands` | 0 | 10,155 | -3,206 | MCP tools, deferred_tools_delta, remote_session_change, skills |
| P4 | P3 + `--setting-sources ""` | 0 | 3,119 | -7,036 | hook prose (10,569 B) and the CLAUDE.md kernel (6,452 B) |

- **Hard floor: NOT ISOLATED.** P4's 3,119 tokens break down entirely into sized buckets: lean system sections 2,357 (replaceable through `--system-prompt`), environment, session_context, model and date 726, prompt 23, and a residual of -6. All of it is controllable, so the registry records 3,119 as an UPPER BOUND on any host-imposed floor and calls none of it a floor. Host framing is within calibration error of 0.
- P3's residual is 1,354 tokens UNKNOWN: plugins were still loaded and P4 removed them along with the settings.
- One invocation, P2a, made no model call. Passing `--tools ""` before the prompt argument let the variadic flag swallow the prompt, and the host exited with "Input must be provided"; it had 0 assistant events. Probes P2-P4 feed the prompt through stdin.
- Laptop plane: its rows are UNKNOWN (no probe there). The observed V1 and Madzia call-1 values are recorded only as observations.

## Minimum safe CWS proposal: short lookup class (NOT enforced)
- Code: `tools/ccr_cws_proposal.py` (decide_tool, decide_attachment, check_safe, simulate). Its TypeScript diff, `vault/programs/ccr/stage3/a2/cws-short-lookup.patch`, passes `git apply --check` and has **not** been applied. Test V-CCRANAT-09 asserts that policy.ts has no `short-lookup` class.
- Closure: the tools in front are Read, Grep, Glob and ToolSearch, and the runtime page tool always stays. On top of the unit drops (skill_listing, agent_listing_delta, mcp_instructions_delta, memory section, instructions replaced by kernel+index), it drops hook_additional_context and remote_session_change. It KEEPS deferred_tools_delta, because that list is how a deferred tool is found again (page fault). The safety invariants are: ToolSearch stays in front; no required attachment is dropped; no write-capable tool is in front. `check_safe` rejects a variant that breaks any of them (V-CCRANAT-08b).
- Projected call-1 saving beyond what each session already sent, attachments only (simulate, 2.999 B/token): V1 r2 18,308 -> 16,274 (-2,034, -11 %); V1 r4 18,077 -> 16,043 (-2,034); Madzia 0bdd6fe2 -902, bf6d4b07 -780, f03c1c84 -1,166; probe P1 -3,705. The saving from the narrower tool list is UNKNOWN until a probe with `--tools Read,Grep,Glob` runs. Any adoption needs a parity canary first, because the hook prose may carry rules that a lookup still needs.
