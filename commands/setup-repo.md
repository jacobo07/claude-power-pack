---
name: setup-repo
description: Produce a DRY-RUN install plan for a repo's automation recommendations, with a rollback recipe and a Secret Firewall scan run FIRST. Never applies changes autonomously -- local steps are proposed, owner-side (global ~/.claude) steps are surfaced for Owner approval, and a CRITICAL secret hit blocks the plan until rotated/scrubbed (Phase 1: firewall before installer). Pillar 3 of the Setup OS.
---

# /setup-repo -- Secure Installer (dry-run + rollback)

## What it does

Scans -> analyzes -> builds a **dry-run** install plan. This engine
NEVER applies changes itself:
- Secret Firewall scan runs first; CRITICAL hits -> plan BLOCKED (no raw
  values surfaced, HR-SECRET-002).
- Every step ships an explicit rollback action (no change without an undo).
- Owner-side steps (global config) are listed for Owner approval, never
  auto-applied (HR-001).

## Run

```
python -m modules.setup_os.secure_installer --path <repo>   # dry-run plan
```

`--apply` is intentionally refused: the Owner applies after reviewing the
plan (dry-run-first doctrine).

## Output
- secret scan result + `safe_to_apply` (or BLOCKED reason),
- the dry-run steps with per-step rollback,
- owner-side actions, and the full rollback recipe.
