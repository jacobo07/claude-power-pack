---
name: analyze-roi
description: Rank automation opportunities for a repo by ROI. Reads the Project Profile (from /scan-repo) and emits a prioritized list of recommendations -- each with impact, effort, risk, an ROI score, install mode (local / owner-side / dry-run-only), a rationale, and an explicit "when NOT to install". The Secret Firewall is pinned first when secret-sensitive files exist (Phase 1 doctrine). Pillar 2 of the Setup OS.
---

# /analyze-roi -- Automation ROI Analyzer

## What it does

Turns a scanned ProjectProfile into a ranked recommendation list. ROI =
impact / effort, damped by risk. Anti-over-recommendation: every item
carries a "when NOT to install". Secret Firewall first.

## Run

```
python -m modules.setup_os.roi_analyzer --path <repo>
```

## Output
- N recommendations sorted: secret firewall first, then ROI desc.
- Each: `[category] title  impact / effort / risk / ROI / install_mode`,
  rationale, and "not-yet" condition.

Feed into `/setup-repo` for a dry-run install plan with rollback.
