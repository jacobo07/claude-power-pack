---
name: demo-ready
description: Demo Readiness check (BL-READINESS-001). Verifies a project is safe to show: no CRITICAL secrets anywhere in the tree, no unresolved scaffold markers in source modules, and a tests directory present (or honestly skipped). Exit 0 = demo-ready, exit 1 = not ready with the failing checks named. Run before any demo or client meeting.
---

# /demo-ready -- is this safe to show?

## What it does

Runs the demo-tier readiness checks against the current project and
reports a single ready / not-ready verdict with per-check detail.
Composes the Secret Firewall detector for the secret check -- no
re-implemented scanning.

Demo checks:
- **No CRITICAL secrets** -- scans every `.py` in the tree.
- **No scaffold markers** -- no unresolved scaffold markers left in
  `modules/`, `src/`, `lib/`, `tools/`.
- **Tests present** -- a `tests/` dir exists (honestly skipped if the
  project legitimately has none).

## Usage

```
PP="$HOME/.claude/skills/claude-power-pack"
python "$PP/tools/readiness_check.py" --level demo --path .
```

On Windows, run via PowerShell with the absolute python path:

```
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
& $py "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\readiness_check.py" --level demo
```

## Programmatic equivalent

```python
from tools.readiness_check import readiness

r = readiness("demo", ".")
print(r["ready"], r["passed"], r["total"])
for name, passed, detail in r["checks"]:
    print(name, passed, detail)
```

## Pairs with

- `/revenue-ready` -- the stricter superset (adds monitoring + Hard
  Rules) you run before going live.
- `/secret-scan` -- the deeper, severity-tunable credential sweep.
