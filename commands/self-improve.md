---
description: Status and control of the autonomous self-improve loop -- what it applied, validated or reverted, and why. It runs daily on its own (PP-SelfImprove, 04:30); this command reports, dry-runs or stops it.
argument-hint: "[status | dry-run | run | off | on]"
---

# /self-improve

The loop is autonomous (Owner, 2026-11-22: "100% autonomo"): every day it analyses all transcripts, first
rectifies what it applied before (reverts a change whose gate goes red because of it, or whose target got worse),
tunes its own parameters, then applies at most one new change that passed a failing-first test, the merged-tree
tests and the regression block. Spec: `vault/specs/self-improve-unattended.md`.

```powershell
& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\self_improve_unattended.py" --status
```

| argument | do |
|---|---|
| (none) / `status` | run `--status` and show the report as printed |
| `dry-run` | `--dry-run`: observe and decide, no agent, no git writes |
| `run` | `--once`: one full cycle now (spends one model call if a candidate is eligible) |
| `off` | create `~/.claude/state/self-improve/OFF` (the loop stops at its next start) |
| `on` | delete that file |

## Boundaries

- Show the report; do not re-derive its numbers. Receipts: `~/.claude/state/self-improve/receipts.jsonl`.
- The fixed core (`tools/self_improve_guard.py`, `tools/self_improve_unattended.py`) is hash-pinned. If the
  report says the core changed, that is for the Owner to review; re-pinning is
  `python tools/self_improve_guard.py --pin` and only on the Owner's word.
- Nothing here pushes. Publication stays with ovo-push-gate.
- Transcript-derived snapshots stay local under `~/.claude/state/self-improve/`; never paste them into a subagent or
  an external service.

Gate: `python tools/test_self_improve_unattended.py` (V-SIU-*).
