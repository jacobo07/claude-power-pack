---
title: Live terminal registry — measure open terminals instead of inferring them
date: 2026-08-11
tier: T2
status: APPROVED — Owner: "en CursorProjects tengo 6 terminales abiertas, en Jacobo tengo 2, eso no se actualiza en tiempo real, corrigelo" (2026-08-11)
covers: [terminal_registry, live_terminals, pane_map_liveness, beacon_pid_reuse, pp_sessions_extension]
origin: T-COLLECTION-GATE-DROPS-LIVE-PANE-001 follow-up
---

# Spec — live terminal registry

## Problem, measured

Owner observation, 2026-08-11: **CursorProjects has 6 open terminals, Jacobo has 2.**
`pane_map.json` at that instant reported:

| repo | Owner sees | `OPEN-NOW` in pane_map | error |
|---|---|---|---|
| CursorProjects | 6 | 4 | **undercount −2** |
| Jacobo | 2 | 3 | **overcount +1** |

The error runs in BOTH directions, which rules out a single off-by-one and names
two independent defects in the same proxy.

### Defect 1 — overcount: the reader has no pid-identity guard

`modules/cpc_os/beacon.py::owning_pane_pid` is careful at WRITE time: it walks to
the ancestor `claude.exe` and rejects a chain whose "parent" is younger than its
child, because *"Windows reuses pids, so a stale ppid can point at an unrelated
live process"*.

`tools/build_pane_map.ps1` then reads those beacons with:

```powershell
if (-not $alivePids.ContainsKey($wpid)) { continue }
```

Presence in the process table only. The writer's own reasoning about pid reuse
was never mirrored on the read side, so a beacon whose `claude.exe` died and
whose pid was recycled by any unrelated process reads as a live pane forever.
275 beacon files are on disk against ~20 real panes, so the recycling surface is
large and grows all session.

### Defect 2 — undercount: a terminal with no beacon is invisible

A beacon exists only if `kclaude.ps1` (resume path) or the SessionStart hub
(fresh path) wrote one. A terminal opened by any other route, or one whose
beacon `%TEMP%` file was swept, cannot be counted at all. No amount of
beacon-reading fixes this: the information is not on disk.

`vscode.window.terminals` is the only authoritative list, and it is reachable
ONLY from inside the extension — the same argument that already justified
`tab_order.js` (`T-TAB-ORDER-EXTENSION-ONLY-001`).

### Why the existing extension does not already do this

`extension/src/extension.js` declares in its own header that it *"never derives
pane data itself"*. It is a reader. It subscribes to `onDidChangeTabGroups` /
`onDidChangeTabs`, never to `onDidOpenTerminal` / `onDidCloseTerminal`. It reads
`vscode.window.terminals` exactly once, 2.5 s after activation, takes `.length`
to distinguish cold start from reload, and discards it.

Measured consequence: `tab_order.json` currently holds **0 tabs**, because
`vscode.window.tabGroups` enumerates EDITOR tabs and every one of the Owner's
terminals lives in the bottom panel.

## Scope

1. **Extension writes the registry.** On activate, and on every
   `onDidOpenTerminal` / `onDidCloseTerminal` (debounced), write
   `~/.claude/state/terminals/<sanitized-workspace-path>.json`.
2. **One file per window.** Each Cursor window runs its own extension host; a
   single shared file would be clobbered by whichever window wrote last, and 4
   windows would report as 1. The workspace folder path is the natural key and
   joins directly to `pane_map`'s `cwd`.
3. **`build_pane_map.ps1` consumes it**: union the registry's session ids into
   `$liveSids`, and add a reader-side pid-identity guard for beacons.
4. **The discrepancy is reported, never hidden**: each repo carries the measured
   `terminalsOpen` count next to its derived pane count.

## Non-negotiable constraints

| # | Constraint | Defect avoided |
|---|---|---|
| 1 | Fail-open at every step: absent/corrupt registry → today's behaviour exactly | The extension must never be able to take the pane map down (matches the existing `$liveSids` fail-open contract) |
| 2 | A registry file whose writing extension host is dead is ignored | A crashed window would otherwise pin its terminals live forever — the same latching defect as `$inSnap` (`T-REVIVAL-SELF-REINFORCING-LOOP-001`) |
| 3 | The registry may only ADD liveness, never remove it | A window with the extension disabled must not delete panes the beacons prove are alive |
| 4 | Canonical and installed copies updated in the same change | `extension.js` was already drifted (canonical ahead by `termName`), and a fix that lands only in git changes nothing at runtime |
| 5 | Measured count and derived count are distinct fields | Collapsing them makes the remaining gap unobservable — absence would read as health (`PR-COVERAGE-BY-CONSTRUCTION-001`) |
| 6 | Pid identity = name AND creation time, never presence | Presence is exactly the check that fails under pid reuse |

## Acceptance criteria

| Gate | Asserts |
|---|---|
| `V-TERMREG-WRITTEN` | Registry payload from a fake terminal list has the required fields and correct sid8 extraction |
| `V-TERMREG-PER-WINDOW` | Two workspaces produce two distinct files; neither clobbers the other |
| `V-TERMREG-DEAD-HOST-IGNORED` | A registry file whose `hostPid` is dead contributes zero live sids |
| `V-TERMREG-FAIL-OPEN` | Missing directory / corrupt JSON → zero sids, no throw |
| `V-TERMREG-ADDS-ONLY` | A pane live by beacon stays live when the registry omits it |
| `V-BEACON-PID-IDENTITY` | A beacon whose pid is alive but is NOT `claude.exe` is rejected |
| `V-BEACON-PID-CTIME` | A beacon whose process started AFTER the beacon timestamp is rejected (reuse) |
| `V-TERMINALS-OPEN-REPORTED` | `terminalsOpen` appears per repo in `pane_map.json` |

## Done-gate

Eight gates pass; existing suites unchanged (`test_session_revival` 9/9,
`test_restore_all_panes` 7/7, `test_pane_map_snapshot` 6/6,
`test_recovery_control_plane` 6/6); canonical and installed extension byte-identical;
pathspec-scoped commit; `REMOTE_DELTA = 0 0`.

**Production Reality Gate (Owner-only):** the extension is loaded at window
activation, so the registry is empty until each window is reloaded. After a
reload of all windows, `pane_map.json` must report `terminalsOpen` = 6 for
CursorProjects and 2 for Jacobo.

## Out of scope

Mapping a terminal that carries no session id in its name (e.g. a bare
"Last session" profile tab) to a specific session. Such a terminal is counted in
`terminalsOpen` but cannot be resumed by id — naming it requires the launcher,
not the registry.
