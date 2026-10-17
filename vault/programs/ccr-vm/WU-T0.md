# WU-T0 -- CCR Cognitive VM, Tranche 0: reality delta, Mod capability matrix, Tennis economic forensics, then the T1+ plan

Source brief: the Owner's 2026-10-17 "CCR Cognitive Virtual Machine" prompt. It was not executed in coordinator pane 85b7c296 on
purpose: that pane costs about 300k tokens per call and is the incident being studied. Run this in a FRESH, small-context
worker. Read no prior transcript. Never use pane 85b7c296 as a status reader or scheduler.
Budget: hard 3.5M, P50 2.5M. Stop and write the receipt at 3.0M. Goal: `ccr-vm` (institutional CAPEX; not tennis-rf).
Mode: EXECUTION (scan), then PLAN (the T1+ plan file).

## Facts already measured (do not re-derive; verify only where marked)
- Tennis RF ledger (`python tools/mission_spend.py goal-lineage --goal tennis-rf`):
  - settled 152,187,636 against programme 150,000,000, so 2,187,636 over
  - coordinator 85b7c296 booked post hoc into three leases:
    - L40 `coord-85b7c296` 21.6M
    - L42 `:2` 7.06M
    - L45 `:3` 8.41M
  - the coordinator's whole transcript is 49.47M processed, of which 12.39M was mis-booked earlier on D9's L29
  - productive workers in the same window: PX m-f2db50c1c362 1.16M (2 commits: 55dacad, 545e983); R2 0.06M
- Bypass (confirmed in-session): the interactive coordinator was never admitted before its calls. Every settle was
  manual and after the fact (`goal-settle --measured`), and `goal_settle` without `--measured` caps a marked session at
  mark + holds (`tools/mission_spend.py:536-544`), so later coordinator spend is hidden by default. Workers are
  admitted (chain envelope, route admission `RECOMPILE`, session breaker). Interactive panes are not.
- Deterministic status already exists as CLIs, read by a model:
  - `python tools/gsdx_chain.py tick --chain <chain.json> --dry-run`
  - `python tools/gsd_mission.py status`
  - `python tools/mission_spend.py programme-status --goal <g>`
  - `~/.claude/state/trf-chain-tick.log`
- Known scheduling already runs with zero model calls: the PP-TrfChain-Tick task arms the next unit every 10 min.
  Observed gaps:
  - capital-apply does not raise chain.json `envelope` (memory feedback_capital_raise_must_raise_chain_envelope)
  - a refused arm leaves a PREPARED held record that blocks the unit, with no command to end it (gsdx_chain.py:382-386;
    ended by hand via `gsd_mission.transition`)
  - the steward never settles a never-launched mission (wait_steward forever)
  - host pre-arm checks are manual
- R2: UNKNOWN abrupt termination during host-wide tool starvation. The slim runner records no exit code or host state
  (gsd_mission.py:952-983). Plan `vault/plans/r2-failure-recompile-2026-10-16.md`.

## Scan (bounded: open named files, no tree-wide Glob/Grep; <= 40 tool calls)
1. `claude --version`; CCR install (`tools/ccr_release.py status` or equivalent; memory project_ccr_runtime_installed).
   For every surface in the brief's "Mod capability matrix" list, classify DIRECT_ENFORCEMENT / REWRITE / FILTER /
   OBSERVE / HOST_FALLBACK / PROTECTED_BY_HOST / UNAVAILABLE / UNKNOWN from the installed host's actual hook and type
   surface. Each class needs a file:line or probe output; no claim from memory.
2. Provider-boundary coverage: for each caller class (interactive pane, bg worker, slim worker, subagent,
   planner/reviewer, successor, closeout), which admission runs BEFORE a call (file:line) and which only after.
3. Owners: Mission Runtime, Economic Kernel, chain, sweep, events (ledger jsonl files), status CLIs, capital path
   (`capital-status` / `capital-apply`), UCVM, Tool Execution Compiler, agent admission, Planning/Review admission.
   Class each PRODUCTION / PARTIAL / SHADOW / SPEC_ONLY / UNREACHABLE / DUPLICATED / SUPERSEDED / HOST_LIMITED / MISSING.
4. Tennis forensics: classify pane 85b7c296's calls since 2026-10-14 into status / control (route, lease, arm fixes) /
   approval handling / strategy (plans) / productive, by reading the transcript with a script (count and tokens per
   class; the script prints totals only). Report Control Plane Tax and Observer Tax.

## Output
- `vault/programs/ccr-vm/T0-reality.md`: capability matrix, coverage table, owner map, Tennis forensics with numbers.
- `vault/plans/ccr-vm-tranches.md`: T1-T11 from the brief, each with necessity re-checked against T0 facts, budgets
  (floor / lower / P50 / P80 / P95 / hard), and the first tranche that closes the interactive-pane bypass.
- Receipt `WU-T0-receipt.md`. Commit by pathspec (the PP tree has many concurrent writers).
Limits: no code changes in T0, no capital requests, no Tennis state changes.
