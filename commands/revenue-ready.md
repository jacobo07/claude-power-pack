---
name: revenue-ready
description: Revenue Readiness check (BL-READINESS-001). The stricter superset of /demo-ready run before a project goes live: everything demo-ready requires PLUS monitoring/telemetry config present AND Hard Rules installed (>= 5 HR-NN entries). Exit 0 = revenue-ready, exit 1 = not ready with the failing checks named.
---

# /revenue-ready -- is this safe to go live?

## What it does

Runs the revenue-tier readiness checks: the full demo-ready set plus the
two production gates. Composes `tools/readiness_check.py` at `--level
revenue`.

Revenue checks = demo checks PLUS:
- **Monitoring active** -- a `vault/monitor`, `vault/telemetry`,
  `modules/monitoring`, or `monitoring/` config exists.
- **Hard Rules (>=5)** -- at least 5 `HR-NN` entries are installed in
  `vault/hard_rules/HARD_RULES.md` (or the inline `CLAUDE.md` mirror).

## Usage

```
PP="$HOME/.claude/skills/claude-power-pack"
python "$PP/tools/readiness_check.py" --level revenue --path .
```

On Windows, run via PowerShell with the absolute python path:

```
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
& $py "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\readiness_check.py" --level revenue
```

## Programmatic equivalent

```python
from tools.readiness_check import readiness

r = readiness("revenue", ".")
print(r["ready"], r["passed"], r["total"])
for name, passed, detail in r["checks"]:
    print(name, passed, detail)
```

## Why two tiers

Demo-ready answers "can I show this without leaking a key or exposing a
half-built shell?". Revenue-ready answers the harder question: "if this
takes real traffic, will I see it break and is the bug-to-Hard-Rule
loop installed?". A project can be demo-ready long before it is
revenue-ready.
