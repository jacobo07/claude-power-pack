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
