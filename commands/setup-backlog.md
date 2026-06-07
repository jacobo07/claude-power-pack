---
name: setup-backlog
description: Turn a repo scan into a prioritized, ROI-ordered backlog with a done-gate per item, then pick the single next action. Bridges the Setup OS ROI analyzer into the existing backlog_autopilot what_now engine (composition, not duplication). Secret-firewall items are pinned P0.
---

# /setup-backlog -- scan -> ROI -> backlog -> next action

Composes `setup_os.roi_analyzer` (recommendations) + `backlog_autopilot.
what_now` (next-action picker). Each backlog item carries an empirical
done-gate.

## Run

```
python -m modules.setup_os.backlog_generator --path <repo>
```

## Output
- N backlog items, ROI-ordered (secret firewall P0 first), each with
  priority / impact / effort / ROI and a done-gate,
- the single next action (`what_now`).
