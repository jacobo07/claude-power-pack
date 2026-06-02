---
name: cost-autopsy
description: Session token-burn autopsy (TCO v1). Reads the TIS telemetry log and reports per-session token spend (input / output / cache-hit ratio / USD), top skills by cost with model-routing audit, and a cost projection comparing actual spend vs TCO-routed spend with the top-3 cheapest-model opportunities. Use it to see where tokens went and which skills are mis-routed to an expensive model.
---

# /cost-autopsy -- session token-burn report

## What it does

Surfaces where the tokens went this session and whether any skill is
running on a more expensive model than the router recommends. Composes
`tools/tis_report.py` (the TIS Capa 2 analytics CLI) -- it does not
re-implement pricing or aggregation.

## Usage

```
PP="$HOME/.claude/skills/claude-power-pack"
python "$PP/tools/tis_report.py" --summary           # per-session aggregate
python "$PP/tools/tis_report.py" --by-skill --top 10 # top skills by cost
python "$PP/tools/tis_report.py" --cache-ratio       # overall cache-hit %
python "$PP/tools/tis_report.py" --cost-projection   # actual vs routed cost
```

Filter to a date range:

```
python "$PP/tools/tis_report.py" --summary --since 2026-06-01
```

On Windows, run via PowerShell with the absolute python path:

```
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
& $py "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\tis_report.py" --summary
```

## How to read it

- **cache%** -- higher is cheaper; a low cache-hit ratio on a long
  session is the signal to `/compact` sooner.
- **audit = MISMATCH** in `--by-skill` -- that skill is running on a
  model more expensive than its routed recommendation; re-route it.
- **--cost-projection** -- `estimated_savings_pct` plus the top-3 skills
  where routing grunt work to a cheaper model would have saved the most.

Pairs with the TCO compact-gate (`tools/tco_compact_gate.py`) and the
model-routing table (`vault/config/model-routing.json`).
