# kclaude scope auto-export -- EXECUTION report (2026-07-05)

Goal (Owner): make the CO-08 scope-gate activate automatically on each launch
instead of a manual per-launch `PP_PANE_SCOPE` export. PASO -1 disproved the
stated mechanism; the sprint delivered the two automatable cases honestly.

## PASO -1 -- premise disproved (SCOPE-EXPORT READINESS)

- **`PP_PANE_SCOPE` format** = comma-separated normalized path tokens
  (`modules/x.py`), NOT a pane label / cwd / UUID. Source: `pm_02_intent`
  `_norm_token`/`norm_scope` + `prelaunch._gate` docstring.
- **`PP_PANE_SID`** = the session_id, used only to exclude the pane's own prior
  intent (`exclude_sid`). Optional.
- **No `pane_map` exists** and cwd->scope is architecturally impossible: scope is
  per-pane INTENT (one repo -> many panes -> many distinct scopes by design).
  `vault/terminal_slots.json` is keyed one-per-cwd -> cannot hold N scopes.
  A cold new pane has no sid and no prior intent at launch.
- Therefore the only honest scope sources are (a) the Owner naming it for a fresh
  pane, (b) recalling what the pane itself previously declared.

## Delivered

- `pm_02_intent.resolve_launch_scope(cwd, sid, ...)` -- pure, hermetic-tested
  resolver: the comma-joined fresh declared scope for `(cwd, sid)`, else "".
  Single source of truth for enc/freshness/JSON (PowerShell shells out; no drift).
- `prelaunch._apply_launch_scope` + `run_fast(cwd, sid=None)` + `--sid` +
  `launch_scope`/`launch_sid` in the fast JSON. An explicit `--scope`/env wins;
  otherwise the pane's own intent is recalled. Fail-open at every hop.
- `kclaude.ps1`: `--scope <tokens>` flag (one-command declaration for a cold
  pane, stripped before passthrough); passes the resume sid to `prelaunch --sid`;
  re-exports `launch_scope`/`launch_sid` to the launched/rehydrated/restarted
  claude via `Set-LaunchScopeEnv`. Parses clean.

## Verification

- `test_parallel_mesh` 34/34 (+3: RESOLVED-FROM-INTENT / EMPTY-WITHOUT-INTENT /
  FAILOPEN-STALE). Regression: cognitive_os 68/68, scope_a 7/7.
- E2E on the real path: `--scope` env -> emitted `launch_scope` (PASS); declared
  intent -> `--sid` recall -> emitted `launch_scope`+`launch_sid` (PASS, synthetic
  intent retired).

## Failsafe

No `--scope` and no fresh prior intent -> nothing exported -> CO-08 blunt
`SAME_REPO_CAP=1` unchanged. `SAME_REPO_CAP` never removed, only bypassed by a
proven-disjoint declared scope.

## Owner-side (HR-001, documented not executed)

- Copy-Item `tools/kclaude.ps1` -> `~/.claude/bin/kclaude.ps1` (clean
  fast-forward; live tracked pre-edit canonical).
- `~/.claude/kclaude.ps1` is a legacy pre-W6 52-line stub -- confirm the terminal
  profile points at `bin/kclaude.ps1`; consider deleting the stale root stub.

## Honest note

This is the third consecutive "built-but-inert-at-the-call-site" wiring (PM-03
publish, CO-08 gate live-path, now CO-08 scope auto-export). The recurring shape
is now doubly sealed: `[[T-INERT-ARCHITECTURE-TAX-002]]` (logic unreachable at the
call site) and `[[T-SCOPE-GATE-OPT-IN-ANTIPATTERN-001]]` (a gate that needs a
manual per-launch action is inert -- automate it in the wrapper or it does not run).
