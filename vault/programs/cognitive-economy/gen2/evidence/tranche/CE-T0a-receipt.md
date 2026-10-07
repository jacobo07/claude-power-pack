# CE-T0a receipt -- spend attribution truth

## Finding
`self_spend.py` had no argument parsing. `--session 71ccfa86-...` was silently ignored and the script metered its
hardcoded `sid="87601e81-..."` (the Gen2.1 pane, which DID spawn agents) in the power-pack project dir. The
`files 9 ... subagent calls 284` reading is that session (1 main + 8 subagent files), none of it 71ccfa86.
`tranche_driver.spend` execs the source with `sid=`/`d=` rewritten, so driver readings were not affected; only
CLI `--session` readings were (known: the CE-T0a packet's 83,894,371).

## Classification -- files the BEFORE invocation counted (sid 87601e81, power-pack dir)
| file | bytes | sessionId | isSidechain | usage recs | span | class |
|---|---|---|---|---|---|---|
| C--Users-User--claude-skills-claude-power-pack/87601e81-fc6a-4199-a22a-3848715634a6.jsonl | 3,319,778 | 87601e81 | False | 310 | 2026-10-05T10:35:36..2026-10-05T19:45:04 | OTHER session (hardcoded 87601e81) main: counted before the fix |
| C--Users-User--claude-skills-claude-power-pack/87601e81-fc6a-4199-a22a-3848715634a6/subagents/agent-a62a4e48e744482c5.jsonl | 1,557,220 | 87601e81 | True | 91 | 2026-10-05T18:13:36..2026-10-05T18:44:33 | OTHER session (hardcoded 87601e81) subagent: counted before the fix |
| C--Users-User--claude-skills-claude-power-pack/87601e81-fc6a-4199-a22a-3848715634a6/subagents/agent-a6e5c466ed95710db.jsonl | 1,600,285 | 87601e81 | True | 110 | 2026-10-05T10:41:52..2026-10-05T10:49:14 | OTHER session (hardcoded 87601e81) subagent: counted before the fix |
| C--Users-User--claude-skills-claude-power-pack/87601e81-fc6a-4199-a22a-3848715634a6/subagents/agent-a70c3c99811c6da54.jsonl | 1,615,591 | 87601e81 | True | 72 | 2026-10-05T17:35:40..2026-10-05T17:50:19 | OTHER session (hardcoded 87601e81) subagent: counted before the fix |
| C--Users-User--claude-skills-claude-power-pack/87601e81-fc6a-4199-a22a-3848715634a6/subagents/agent-a9bba1c66e685570e.jsonl | 1,272,983 | 87601e81 | True | 87 | 2026-10-05T19:04:17..2026-10-05T19:31:11 | OTHER session (hardcoded 87601e81) subagent: counted before the fix |
| C--Users-User--claude-skills-claude-power-pack/87601e81-fc6a-4199-a22a-3848715634a6/subagents/agent-aa32763668629417a.jsonl | 1,195,628 | 87601e81 | True | 66 | 2026-10-05T17:51:05..2026-10-05T18:08:32 | OTHER session (hardcoded 87601e81) subagent: counted before the fix |
| C--Users-User--claude-skills-claude-power-pack/87601e81-fc6a-4199-a22a-3848715634a6/subagents/agent-aad9290e4ba27f485.jsonl | 1,406,364 | 87601e81 | True | 77 | 2026-10-05T18:45:10..2026-10-05T19:03:39 | OTHER session (hardcoded 87601e81) subagent: counted before the fix |
| C--Users-User--claude-skills-claude-power-pack/87601e81-fc6a-4199-a22a-3848715634a6/subagents/agent-ac0efaaaee9221fbd.jsonl | 1,250,714 | 87601e81 | True | 58 | 2026-10-05T13:24:38..2026-10-05T13:37:21 | OTHER session (hardcoded 87601e81) subagent: counted before the fix |
| C--Users-User--claude-skills-claude-power-pack/87601e81-fc6a-4199-a22a-3848715634a6/subagents/agent-ac9b1158549d53eb4.jsonl | 757,500 | 87601e81 | True | 43 | 2026-10-05T19:31:36..2026-10-05T19:36:34 | OTHER session (hardcoded 87601e81) subagent: counted before the fix |

## Files for 71ccfa86 (both project dirs that hold the sid)
| file | bytes | sessionId | isSidechain | usage recs | span | class |
|---|---|---|---|---|---|---|
| C--Users-User--claude-skills-claude-power-pack/71ccfa86-6902-4449-a345-dacb4b1ba2de.jsonl | 2,309,577 | 71ccfa86 | False | 202 | 2026-10-07T07:17:03..2026-10-07T10:15:35 | this session's main transcript |
| C--Users-User-Apps-mcp-video-analyzer/71ccfa86-6902-4449-a345-dacb4b1ba2de.jsonl | 2,309,577 | 71ccfa86 | False | 202 | 2026-10-07T07:17:03..2026-10-07T10:15:35 | this session's main transcript |

Message ids shared between the two dirs' copies: 85. 71ccfa86 has no subagent files in either dir,
consistent with "spawned no Agent". The meter reads one project dir (`d`); the sid's copy in the other dir is
reported below, never summed silently.

## Fix
`vault/programs/cognitive-economy/gen2/evidence/stage0/self_spend.py`: honour `--session`/`--dir` only when run as
`self_spend.py` (an exec under tranche_driver keeps the rewritten `sid=`/`d=` lines, same shape); count only
existing files; no transcript -> `processed None`, never 0; output names the sid it metered.

## Test
`python tools/test_self_spend_attribution.py` -> `SELF_SPEND_ATTRIBUTION_PASS=6/6` (own main + own subagent exact, foreign excluded,
missing -> None, driver-exec shape, mutant with flags reverted goes red by metering the foreign sid).

## 71ccfa86 before / after
- before (packet, flag ignored): `files 9 calls 411 processed 83,894,371 (ctx 83,722,227 out 172,144) subagent calls 284 subagent ctx 47,843,339` -- this was sid 87601e81
- after, power-pack dir: `sid 71ccfa86-6902-4449-a345-dacb4b1ba2de files 1 calls 85 processed 17,568,509 (ctx 17,495,044 out 73,465) subagent calls 0 subagent ctx 0`
- after, mcp-video-analyzer dir: `sid 71ccfa86-6902-4449-a345-dacb4b1ba2de files 1 calls 85 processed 17,568,509 (ctx 17,495,044 out 73,465) subagent calls 0 subagent ctx 0`
- 87601e81 today (what the old command measured): `sid 87601e81-fc6a-4199-a22a-3848715634a6 files 9 calls 411 processed 83,894,371 (ctx 83,722,227 out 172,144) subagent calls 284 subagent ctx 47,843,339`

## spent_measured (ledger.json budget_tokens, only key changed)
value = null: S5, WU2, overlaps, GEX44 and the CE-T0 workers are unknown. 13 sources and 7 unknowns are listed in the ledger.

COMMITS: 25203294
