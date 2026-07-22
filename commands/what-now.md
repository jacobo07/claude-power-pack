---
name: what-now
description: Backlog Autopilot -- given a list of backlog items (or a path to a JSON file), recommend the single highest-ROI actionable item. Filters done + blocked items; scores remaining by priority (0..3, 0=P0), impact (Critical/High/Medium/Low), and effort (S/M/L/XL). Returns the recommendation, score, and reasoning.
---

# /what-now -- Backlog Autopilot

## What it does

`/what-now` consults a backlog (in-memory list or a JSON file path)
and recommends the single highest-ROI actionable item right now.

Algorithm (v1, BL-BACKLOG-001):
- Filter: drop items where `done == True` OR `blockers != []`.
- Score each candidate:
    `score = (PRIORITY_MAX+1 - priority) * 2  +  impact_score  +  effort_score`
    where impact is {Critical: 8, High: 5, Medium: 3, Low: 1}
    and effort is {S: 4, M: 3, L: 2, XL: 1} (smaller effort scores higher).
- Return the highest-scoring item.

## Usage

```
/what-now                                # uses default backlog if registered
/what-now <path-to-backlog.json>          # explicit JSON path
```

Or programmatically:

```python
from modules.backlog_autopilot import BacklogItem, what_now_tracked

items = [
    BacklogItem("FIX-1", "Fix login bug", 0, "S", "Critical"),
    BacklogItem("FEAT-2", "Add 2FA",       1, "L", "High"),
    BacklogItem("BLK-3", "Blocked task",  0, "S", "Critical",
                blockers=("waiting-on-vendor",)),
]
result = what_now_tracked(items)   # what_now() + IAS-C2 opportunity-cost recording
print(result.recommended.id)   # -> FIX-1
print(result.reasoning)
```

`what_now_tracked` (modules/backlog_autopilot/tracked.py) is the recommended
entrypoint: identical recommendation to `what_now`, plus a real IAS-C2
Opportunity Cost Ledger entry (`vault/ias/c2_opportunity_cost_ledger.jsonl`)
naming the highest-ranked item NOT picked this time. `python -m
modules.ias_c2.opportunity_cost --report` prints the per-domain pattern this
produces over time (Part VI of the sealed IAS-C2 corpus). Use bare `what_now`
only when you deliberately want no ledger side effect.

## Why this exists

The Owner often asks "what should I work on right now?". A purely
priority-sorted list ignores effort -- a P0 task locked behind a
3-week migration is not actionable today. The score function picks
the highest-impact item that can actually move today.

## Output shape

```
WhatNowResult:
  recommended            : BacklogItem | None
  score                  : int
  reasoning              : str
  candidates_considered  : int
```

If the backlog has no actionable items (all done or all blocked),
`recommended` is `None` and `reasoning` says so.
