# ESTATE: one week of floor rent (plane: laptop, 2026-10-18T00:00Z to 2026-10-25T00:00Z)

Tranche 2, W6. Command: `python vault/programs/ctx-rent-obs/b2/w6_estate.py 2026-10-18T00:00:00Z 2026-10-25T00:00:00Z
vault/programs/ctx-rent-obs/b2/estate-week.json` (40 s, streams every `~/.claude/projects/**/*.jsonl` touched since
10-17). All figures are processed input tokens, cache reads included (the ledger unit).

Method: calls = unique assistant `message.id` with usage inside the window. Floor = the session's real call 1 (input +
cache_read + cache_creation), even when call 1 is before the window. Floor rent = calls x floor, the part of every call
that the session would carry with an empty history. Class: mission owner session -> worker by owner kind; a file under
`subagents/` -> subagent; everything else -> top-level (interactive panes, plus any headless run that is not a mission
owner).

| class | sessions | calls | mean floor | floor rent | processed | floor share |
|---|---:|---:|---:|---:|---:|---:|
| top-level | 257 | 35,586 | 108,197 | 4,018,738,657 | 8,491,240,902 | 47.3% |
| subagent | 225 | 4,042 | 62,697 | 266,759,851 | 490,962,757 | 54.3% |
| worker:background | 13 | 1,176 | 111,366 | 129,732,597 | 190,683,738 | 68.0% |
| worker:slim | 9 | 88 | 20,014 | 1,758,095 | 2,374,042 | 74.1% |
| **total** | **504** | **40,892** | - | **4,416,989,200** | **9,175,261,439** | **48.1%** |

## What it says
- **Top-level sessions are 92.5% of the week's processed tokens** and 91% of the floor rent. Mission workers are 2.1%.
- Floor carriage is about half of everything processed (48.1%). The other half is history.
- **Lever sizes per week, measured here:**
  - each 10K removed from the top-level floor: 35,586 calls x 10K = **~356M** (3.9% of the week);
  - moving every background worker to the slim floor (111K -> 20K): 1,176 x ~91K = **~107M** (1.2%), and only if those
    units still complete on slim, which is not measured (B2).
- So the next lever is the top-level boot floor (B1 laptop 106,769 on 36d35fab; B2 attributes ~46-48K of a 104K boot to
  named sources and ~52K to tool schemas and framing), not worker routing.

## Limits
- One week, one plane. GEX44 is the same account (token audit of 18-24/10) and is not in these numbers.
- "top-level" mixes interactive panes with non-mission headless runs; they are not separated here.
- Floor rent is an upper bound on what floor reduction can reach: a call's floor is partly cache read, and removing a
  source also changes cache behaviour, which this count does not model.
- Processed counts cache reads at full weight; billing weights them lower. Payback in money is not derived here.
