---
type: improvement
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-external-research]
status: IDEA
effort: S
graduated_to:
---

# Attribute mid-session prefix rebuilds

## Problem

In 7 days, 358 calls after the first call of a transcript wrote more than 50k cache tokens: the
prefix was rebuilt mid-session. They cost ~$670, 8.1 % of estimated spend; 98.9 M tokens written
(`wiki/tools/token_economy_cuts2.2026-10-02.out` [D] @ `fd27800`; [[token-economy-levers]]).

## Known causes (caching doc, tier A)

Changing tool definitions invalidates tools, system and messages; toggling features invalidates
system and messages; an idle gap longer than the TTL; compaction
([[2026-10-02-token-economy-external-research]], Q1). Candidates on this host: deferred MCP tools
loading mid-session, `/compact`, idle panes past 1 h, a model switch.

## Proposed steps

1. For each of the 358 calls, record the gap since the previous call, whether a compaction or
   model change preceded it, and whether the tool list changed. Pure transcript read, zero quota.
2. Rank causes by cost. Act only on a cause PP controls.

Owner: none found. Small, read-only, and decides whether an 8 % line is reachable.

## Result (2026-10-02, step 1 done)

Main thread, 307 rebuilds (`wiki/tools/token_economy_deep.2026-10-02.out` [P]): idle > 1 h (cache
expired) 224 (~$541); model switch 36 (~$88); after compaction 31 (~$38); gap ≤ 5 min 16 (~$30).
The dominant cause is not a prefix change but a cold cache after a break. A 5 min TTL would make it
worse (net +$1,262). Next step lives in [[token-economy-brainstorm]] A1 (idle-return rollover) and
A4 (find the model-switch source).

## Correction (2026-10-03): the "model switch" class was an instrument artifact

`token_economy_deep.py` treated `<synthetic>` assistant rows as a model. Those rows are made by
the client, not the model: usage-limit notices, "No response requested.", connection errors. So
every return from a limit wait read as a switch. Measured (`wiki/tools/token_economy_model_switch*.2026-10-03.out`):

- Without synthetic rows: 1 real switch (`opus-5-5 -> opus-5`, $4.68).
- With synthetic rows: 37 rebuilds, reproducing deep.py's 36 (the window moved).
- 25 of the 43 synthetic rows before a rebuild were usage-limit notices. 33 of the 43 rebuilds
  came > 1 h after the previous real call.

deep.py was fixed to skip synthetic rows and re-run (`token_economy_deep.2026-10-03.out` [P]):
idle > 1 h 252 (~$611), after compaction 29 (~$35), gap <= 5 min 18 (~$32), model switch 1 (~$5).
The 2026-10-02 output is kept as it was.
**A4 is closed: not a lever.** The idle class grows, and part of it is returns from a usage limit,
which the Owner cannot shorten. That feeds the S6 proposal
(`vault/proposals/2026-10-03_idle-return-rollover.md`).
