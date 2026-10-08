# W1 notes (append-only, newest last)

- F1 wake_check.py already has `run_gate` (refuses `--probe` and any argv element whose basename starts claude/anthropic) and `consume` (flag -> one `wake` event, GoalLog seq-CAS, sha256 DUPLICATE). EXTEND, no second store.
- F2 `run_gate` refuses on `Path(a).name.startswith("claude")`: a `git -C <repo>` whose directory is `claude-power-pack` would be refused. Decision: git calls pass the repo as subprocess `cwd`, never as an argv element. `run_gate` becomes a thin wrapper over a new `run_cmd` (same refusal, returns stdout) so the refusal stays in one place.
- F3 GoalLog needs repo id = hex 7..64 and goal id = `[a-z0-9][a-z0-9._-]{0,63}`. Decision: one GoalLog per wait, goal_id = wait_id (same grammar enforced on wait_id), repo id = constant 40-hex namespace, base = `<wait dir>/log`.
- F4 `mission_spend.py goal-status --goal G` prints `{goal, cap, used, open, settled, remaining, binding, ok}`; an undeclared goal gives ok false "UNKNOWN: ..." (exit 3). Decision: that is UNKNOWN, never exhausted, never fine.
- F5 `gsd_mission.py status` rows carry no cwd; the mission records do (`cwd`, `state`, `TERMINAL`) via `_scan()`. Decision: live-mission probe imports `_scan` and `TERMINAL`; an unreadable record makes the probe UNKNOWN -> HELD.
- F6 `mutation_drill.py` copies the subject dir plus `modules/`, so a test beside its subject in `tools/` is drillable if it reaches the subject through `Path(__file__)`.
- D1 Module layout: `tools/mission_wait.py` (sibling; all logic) imported lazily by `wake_check.py` for `--waits`, `--delta`, `--declare`. Lazy to avoid a wake_check <-> mission_wait import cycle.
- D2 Verdict policy: live mission on next.cwd -> DENIED (a duplicate launch is refused, not parked); route_admission DEFER -> HELD, RECOMPILE/ESCALATE -> DENIED; RAM unmeasurable or < 4 GB -> HELD; goal remaining < lease -> DENIED; goal undeclared/unreadable -> REFUSED (state unchanged).
