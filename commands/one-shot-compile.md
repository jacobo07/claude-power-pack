---
name: one-shot-compile
description: Compile a One-Shot Contract before starting an L or XL task (BL-ONESHOT-001 / OD3). Turns a task description + size class into a frozen contract with a budget ceiling, derived scope, explicit out-of-scope items, and a done-gate. Paste the rendered contract at the top of the next prompt to lock fidelity -- the Fidelity Lock flags execution that deviates more than 40% from the stated scope.
---

# /one-shot-compile -- compile a task contract

## What it does

Compiles a task description into a frozen `OneShotContract`: a budget
ceiling (OD3 table), the in-scope concern, the implicit out-of-scope
items, and an empirical done-gate. Running it before an L/XL task makes
the budget and scope explicit so scope creep is detectable rather than
silent.

## Usage

```
PP="$HOME/.claude/skills/claude-power-pack"
python "$PP/modules/one_shot/compiler.py" \
  --task "Add JWT refresh-token rotation to the auth service" \
  --size L
```

Size classes (OD3 budget table):

```
S  = $5   small fix / rename / lint
M  = $15  bugfix / single-file feature
L  = $30  multi-file feature / refactor
XL = $100 architecture / cross-cutting initiative
```

On Windows, run via PowerShell with the absolute python path:

```
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
& $py "$env:USERPROFILE\.claude\skills\claude-power-pack\modules\one_shot\compiler.py" --task "..." --size M
```

## Programmatic equivalent

```python
from modules.one_shot.compiler import compile_contract, render_contract

c = compile_contract("Add JWT refresh-token rotation", "L")
print(render_contract(c))
print(c.budget_usd)     # 30.0
```

## Why this exists

Plan-quality is bounded by scope-clarity. A compiled contract gives the
Fidelity Lock (`modules/one_shot` `is_deviated`) a concrete scope to
measure against: if more than 40% of touched files fall outside the
stated concern, that is a HR-ONESHOT-002 STOP, not a silent expansion.
