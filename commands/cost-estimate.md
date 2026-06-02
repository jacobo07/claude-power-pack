---
name: cost-estimate
description: Per-session token-overhead estimator (BL-READINESS-001 sibling). Breaks down the fixed context cost a session pays at startup -- global + project CLAUDE.md, memory files, plugins, MCP servers, governance and planning docs -- and converts it to an estimated USD overhead on Opus / Sonnet / Haiku. Use it to see where the session-start token budget goes and what to trim. On-demand diagnostic, not a hook.
---

# /cost-estimate -- session-start token overhead

## What it does

Estimates the fixed token cost a session pays before the first real
prompt: the context the harness loads (CLAUDE.md global + project,
memory files, plugins, MCP servers, governance + planning docs). Wraps
`modules/token-optimizer/session_cost_estimator.py` -- it does not
re-implement the counting.

This is distinct from `/cost-autopsy` (which reports tokens already
SPENT this session from the TIS log). `/cost-estimate` is the *a-priori*
startup overhead; `/cost-autopsy` is the *a-posteriori* burn.

## Usage

```
PP="$HOME/.claude/skills/claude-power-pack"
python "$PP/modules/token-optimizer/session_cost_estimator.py" \
  --tier 2 --project-dir .
```

Tier sets the assumed reasoning overhead (1 Light .. 5 Full-Context):

```
1 Light        ~500 tok    simple Q&A, quick edits
2 Standard    ~2000 tok    feature implementation, debugging
3 Deep        ~5000 tok    architecture, multi-file refactoring
4 Forensic   ~10000 tok    complex debugging, system analysis
5 Full       ~20000 tok    complete codebase reasoning
```

On Windows, run via PowerShell with the absolute python path:

```
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
& $py "$env:USERPROFILE\.claude\skills\claude-power-pack\modules\token-optimizer\session_cost_estimator.py" --tier 2
```

## How to read it

The breakdown lists each overhead source with its token count and a
bar. The TOTAL is the per-session-start estimate; the USD lines are the
input-only overhead at public Opus / Sonnet / Haiku rates. Sources over
3,000 tokens are flagged as trim candidates when the total exceeds the
high-overhead threshold.

## Pairs with

- `/cost-autopsy` -- tokens actually spent (TIS log).
- The `budget_monitor` SessionStart hook -- programmatic-credit runway
  (register via `tools/register_global_hooks.py`).
