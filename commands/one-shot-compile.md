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

## Reasoning-execution coherence (B3, CO-03 x one_shot)

`compile_contract(description, size, cwd=...)` -- when a `cwd` is supplied --
also checks the declared budget against CO-03's own keyword-derived route
for the same description (`modules/one_shot/reasoning_route.py`). If CO-03
would independently route the description more than 2x above the declared
budget (HR-COST-002's own threshold), a `[REASONING ROUTE]` advisory prints
to stderr naming the CO-03 route class it derived -- a signal that the
chosen size may be too small for the description's actual weight, surfaced
at compile time rather than after spend. Advisory only: it never blocks or
mutates the frozen contract, and it is silent when no `cwd` is passed (the
same opt-in discipline as the Spec Gate check above).

The same module resolves `modules/one_shot/escalation.py`'s
`recommend_action` output to a real model ID via `model_for_action`: only
`"escalate-to-opus"` names one (CO-03's `MODEL_MACRO`), because the other
actions either need no new model or are the HR-ONESHOT-003 Owner-decision
STOP, never a model pick.
