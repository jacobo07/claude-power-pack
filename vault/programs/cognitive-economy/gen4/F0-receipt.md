# F0 receipt -- per-call floor split, host vs Power Pack (2026-10-09)

Method changed from the card's pass-through mod to transcript telemetry: every transcript records the typed blocks
injected before the first call AND that call's usage, so the split is deterministic with zero model calls. The mod is
kept only for what transcripts cannot show (the system prompt and tool schemas, here the regression intercept).
Reproduce: `python vault/programs/cognitive-economy/gen4/f0/floor_split.py 3` (raw output beside it).

## Sample (MEASURED)
618 fresh sessions (first assistant call, no prior assistant entry), 62 project dirs, transcripts modified in the
3 days to 2026-10-09, laptop host. Models: opus-5-5 482, sonnet-5-5 96, opus-5 37, haiku 3.
Floor = input + cache_creation + cache_read of the first call: median 121,465 (min 5,380, max 216,794).

## Fit (DERIVED): floor = unseen + rate x injected chars
| variant | unseen (system prompt + tool schemas) | tokens/char | R2 |
|---|---|---|---|
| all blocks | 31,769 | 0.3554 | 0.828 |
| without hook_success / prompt_snapshot | 33,162 - 34,339 | 0.360 - 0.368 | 0.821 - 0.827 |
Per-type multivariate fit rejected: collinear small blocks gave impossible coefficients (-1.05, 2.31 tok/char).
Whether hook_success / prompt_snapshot reach the model is UNKNOWN (fits indistinguishable; ~2-3k tokens each).

## Split of the median floor (~121k) at 0.355 tok/char
| component | owner | median chars (MEASURED) | ~tokens (DERIVED) |
|---|---|---|---|
| system prompt + tool schemas | host (tools partly config) | not in transcript | 31.8-34.3k |
| instructions: CLAUDE.md x3, rules, MEMORY.md | Power Pack / user | 134,995 | ~48k |
| skill_listing | Power Pack + plugins (few host-bundled) | 34,963 | ~12k |
| agent_listing | Power Pack + plugins | 28,265 | ~10k |
| hook_additional_context + hook_success | Power Pack hooks | 15,129 | ~5k (part UNKNOWN) |
| mcp_instructions + deferred tool names | user MCP config | 9,354 | ~3k |
| prompt_snapshot, environment, date, model, ... | host | ~9k | ~3k (part UNKNOWN) |
| user prompt (the task) | task | 3,187 | ~1k |
Controllable by Power Pack / user config: ~78k of ~121k (~64%). Host-forced: ~35-37k (~30%). Task: ~1%.

Instructions by file, PP repo fresh worker 62ac7eb5 (MEASURED chars): ~/.claude/CLAUDE.md 40,116; PP CLAUDE.md
34,549 (inlines test entries such as HR-002 "...pipeline ZZZ"); MEMORY.md 17,034; two long rules 12,386; home
CLAUDE.md 5,988; ~20 rule stubs ~20k.

## Profiles (MEASURED floors, p25 / median / p75)
opus-5-5 117,243 / 122,582 / 130,356 (n 482); sonnet-5-5 18,226 / 81,103 / 119,038 (n 96); opus-5 median 197,746 (n 37).
PP repo median 126,528 (n 121) vs other repos 120,457 (n 497). Sub-20k Sonnet floors exist on this host: which
launch profile produces them is UNKNOWN (not attributed in this unit).

## Implication for A4 (stated, not applied)
A4's ~120k assumption matches today's default top-level Opus floor (122.6k), so it was not stale -- but ~64% of it
is Power Pack's own injection, and a slim profile is measured far below it. Units that need neither the doctrine
nor the skill/agent listings should be priced on a slim profile, not on 120k.

## Done-gate
Split measured with provenance: yes. Host vs PP separated: yes, via regression intercept (DERIVED). Profiles: yes.
Sample sufficiency: n=618 for the aggregate; per-type small blocks insufficient (stated UNKNOWN). Cost of F0: this pane's
calls only (zero model calls inside the measurement); measured at closeout in the A4 reforecast.
