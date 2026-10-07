# A3-U1 receipt -- per-call autopsy of the coordinating panes

Zero model calls. Source: `~/.claude/projects/*/<sid>*.jsonl`, whole transcript, deduped by `message.id|requestId`
(last streamed line wins). Processed = input + cache_creation + cache_read + output. Raw output:
`U1-autopsy.json`, table: `U1-table.md`.

## Commands
```
python tools/test_a3_pane_autopsy.py          # A3AUTOPSY_PASS=10/10 (each gate driven green and red)
python tools/a3_pane_autopsy.py --json vault/programs/cognitive-economy/gen2/evidence/a3/U1-autopsy.json --md vault/programs/cognitive-economy/gen2/evidence/a3/U1-table.md
```

## Table (all five transcripts found; none UNKNOWN)
| pane | calls | processed | floor (1st call) | median ctx | p90 ctx | slope tok/call | floor x calls | growth above floor | rent share | no-effect calls | repeat Reads (est tok) | Agent spawns | CF saving (ESTIMATED) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 423e33b0 | 125 | 36,395,667 | 121,423 | 319,586 | 386,808 | 2,340 | 15.18M | 21.10M | 58.0% | 41 | 6 (6,940) | 3 | 28.26M |
| b9bd9469 | 206 | 58,225,678 | 122,544 | 272,834 | 417,093 | 1,510 | 25.24M | 32.82M | 56.4% | 60 | 11 (8,408) | 0 | 44.13M |
| 886d7bb9 | 81 | 19,977,276 | 120,127 | 258,483 | 297,086 | 1,956 | 9.73M | 10.18M | 50.9% | 28 | 5 (1,356) | 0 | 14.86M |
| 0f9b771b | 79 | 13,430,412 | 121,931 | 164,860 | 207,018 | 1,241 | 9.63M | 3.75M | 27.9% | 24 | 3 (1,940) | 0 | 8.13M |
| e6e0eca7 | 148 | 34,598,953 | 119,930 | 227,562 | 339,346 | 1,523 | 17.75M | 16.73M | 48.4% | 52 | 8 (1,946) | 1 | 25.32M |

Calls-vs-rent: "floor x calls" is what a call costs before the pane has learned anything; "growth above floor" is the
context rent. Output tokens are 0.2-0.4% of every pane. Subagent cost (separate transcripts, not in the rows above):
423e33b0 1 file / 1,330,462 processed for 3 spawns; e6e0eca7 1 file / 1,985,280 for 1 spawn. The other panes
spawned no Agent, so 0 subagent files is a measured 0.

Tool_result share (ESTIMATED, chars/4; the transcript carries no per-result token count):
| pane | PowerShell | Read | Grep | Glob | Edit |
|---|---|---|---|---|---|
| 423e33b0 | 35.6% | 49.5% | 7.0% | 3.3% | 2.1% |
| b9bd9469 | 46.2% | see JSON | 8.1% | 0.6% | 2.6% |
| 886d7bb9 | 33.6% | 45.7% | 6.5% | 12.0% | 0.5% |
| 0f9b771b | 53.9% | 32.1% | 8.0% | 1.1% | 2.1% |
| e6e0eca7 | 64.0% | 25.4% | 2.7% | 0.0% | 3.4% |

## Top-5 rent classes across panes (by size)
1. **Floor re-paid every call**: 15.2M-25.2M per pane, 42-72% of processed; every pane starts at ~120-123k.
2. **Growth above the floor** (accumulated tool results re-read every call): 3.7M-32.8M; slopes 1.2k-2.3k tok/call, p90 context 207k-417k.
3. **Shell and Read output** dominates what accumulates: PowerShell 34-64% and Read 25-50% of tool_result tokens.
4. **No-effect (pure deliberation) calls**: 24-60 per pane, 28-34% of calls, each paying floor plus accumulated rent.
5. **Agent spawns**: 3.3M processed across the two panes that spawned any.
Repeated Reads of one path are negligible (1k-8k est tokens per pane) -- not a rent class.

## Counterfactual (ESTIMATED, not measured)
Effect-bearing calls (edit/test/git/shell) x 95,695 fresh-worker floor, no growth, plus their actual output. The saving
column above is processed minus that. It assumes the effect calls could run in fresh workers unchanged, which is untested.

## Caveats
- Figures are whole transcript. The A3 card quotes smaller windowed figures (e.g. 423e33b0 24.7M vs 36.4M here;
  886d7bb9 16.92M vs 19.98M); the difference was not reconciled -- window bounds were not applied here. UNRECONCILED.
- Effect = any edit/test/git/shell tool category from `turns.tool_cat`; a call using only Read/Grep/Glob/coord tools
  or no tool counts as no-effect, even when it set up an effect.
- Per-spawn subagent cost is not separable: one total per pane.
- b9bd9469 Read share and per-pane Monitor/AskUserQuestion shares: see `U1-autopsy.json`.
