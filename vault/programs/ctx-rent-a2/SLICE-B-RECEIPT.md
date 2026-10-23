# Slice B receipt (ctx-rent-a2), measured 2026-10-23

Status: SEALED. Slice B was applied on 2026-10-11 (rules index `~/.claude/rules/skill-rule-index.md`, hot-prose
moves out of both CLAUDE.md files, backup `~/.claude/backups/rules-20261011-114632`). It was not measured
until today.

## 1. File component (controlled: same five sources Slice A attributed, character counts, no session)
| source | Slice A | 2026-10-23 | delta |
|---|---:|---:|---:|
| ~/.claude/CLAUDE.md | 39.8K | 19.2K | -20.6K |
| PP CLAUDE.md | 39.0K | 23.1K | -15.9K |
| ~/.claude/rules (all .md) | 38.0K | 26.4K | -11.6K |
| MEMORY.md | 17.1K | 21.3K | +4.2K (regrowth, debt) |
| ~/CLAUDE.md | 6.0K | 6.0K | 0 |
| total | 139.8K | 96.0K | -43.8K (-31 %) |

## 2. Provider-side call-1 floor (`tools/context_floor_census.py`, measured usage)
| session | call-1 floor | notes |
|---|---:|---|
| Slice A baseline | 122,093 | 32,664 host-cached + 89,427 session |
| 36d35fab (2026-10-23, short first prompt) | 106,769 | host prefix 32,000; session 74,769 |
| 5cadebe8 (2026-10-23) | 147,977 | includes a 31,946-token pasted prompt, so about 116K without it |

- Measured saving on a short-prompt session: **-15,324 tokens per call (-12.6 %)**. The file-character
  estimate predicted about -12K.
- Comparability: the host listings are unchanged (skill_listing 30,102 + agent_listing 27,352 = 57.5K, the
  same 57.5K as Slice A). The model differs (Opus 5.5 today) and so do the MCP servers per session. Those
  sit in the unattributed bracket (55K for 36d35fab), so it is a like-for-like comparison of the attributed
  floor, not a fully controlled A/B.

## 3. Debt that remains
- MEMORY.md regrew 4.2K after Slice B. Compacting it is the cheapest next cut.
- Unattributed 55-64K (tool schemas, framing) is the largest bucket left. The listings need settings, which is an Owner decision.

Census JSON: pane 36d35fab scratchpad `census.json` (sessions 36d35fab 5cadebe8 15f5057c f2a2e4ca).
