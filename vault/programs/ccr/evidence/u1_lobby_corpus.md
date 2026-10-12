# U1 Lobby corpus (ccr v3 U1, measured 2026-10-12 by pane c13cda65, handed to owner e10a9f08)

Scope: "Lobby" = LuckyArena's lobby, not SkyParty's (Owner, 2026-10-12). All numbers come from the usage index
(`~/.claude/state/usage_index/index.sqlite`, read-only) and the autorun ledger. Gross = inp+cw+cr+out; weighted =
inp + 0.1 cr + 2 cw + 5 out.

## Ralph mission for the lobby: m-1d270cd85220 (workstream `luckyarena-lobby`)
`python mission_burn.py m-1d270cd85220`
- 26 launches, 2026-09-24 17:35 -> 2026-09-26 ~03:33; HALTED "iterations 24 >= max 24".
- Epochs with model calls: 1, 2, 5-12 (+ epoch 11 has 23 subagent calls): **702 calls, 209,637,501 gross,
  30,270,709 weighted**. Epochs 3-4 have no adopted worker in the ledger.
- Epochs 13-26: 14 relaunches about every 5 min from 2026-09-26 00:22, each transcript ~940 KB with ONE synthetic
  assistant message "You've hit your weekly limit · resets Sep 30" and zero model calls. They consumed the cycle
  cap that halted the mission. Failure signature for U3: a limit-blocked epoch counts as an iteration and the sweep
  relaunches it on a timer; it costs ~0 tokens but ends the mission.

## The 2,044 calls / 755M / 194M figures: NOT reproduced as Ralph burn; CORRECTED
Sessions tagged by what their tool_use inputs touch (`lobby_sessions.py`; tag LUCKYARENA_LOBBY = inputs name both
luckyarena and lobby, luckyarena > skyparty; session-level, so coarse):
- 2026-09-22, LUCKYARENA_LOBBY: **1,953 calls, 756.0M gross**, 107.7M weighted (closest to 2,044 / 755M).
- 2026-09-24, LUCKYARENA_LOBBY: 3,430 calls, 1,209.3M gross, **193.6M weighted** (closest to 194M).
- Single session 089522d5 ("Arena 6 canonical revision reconstruction", 09-22..09-24): 1,994 calls, 739.7M gross.
So the figures look like day- or session-level LuckyArena totals, mostly interactive sessions, not Ralph burn. The
Ralph lobby mission is 702 calls / 210M gross / 30M weighted.

## Corpus totals (KobiiCraft project dirs, all time in the index, session tags)
LUCKYARENA_LOBBY 67 sessions, 29,779 calls, 10.41G gross, 1.52G weighted; SKYPARTY_LOBBY 78 / 24,164 / 7.74G /
1.14G; LUCKYARENA_NO_LOBBY 31 / 3,304 / 1.13G; LOBBY_OTHER 18 / 5,370 / 1.58G; OTHER 387 / 2,645 / 0.82G.
Index has KobiiCraft rows only to 2026-10-06; if live Lobby sessions write now, refresh the index before D1.

## Scripts (this folder)
`lobby_corpus.py` (per-day, project), `lobby_sessions.py` (session tags + join), `ralph_missions.py` (epochs by
title `m-<id>-eN`; misses untitled epochs), `mission_burn.py` (epochs by ledger worker id; authoritative).
