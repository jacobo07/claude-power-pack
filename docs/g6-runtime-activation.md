# G6 Runtime — Activation & Manual Verification

The G6 runtime backbone (power-beacon classifier + reentry recorder + resume
identity) is built and hermetically tested (`tools/test_session_resilience_build.py`,
gates `V-G6-*` / `V-RESUME-*`, 49/49 ×3). This doc covers the two legs a headless
agent cannot self-activate: **wiring the canonical edits into the live host**, and
the **Owner-run GUI verification** of the end-to-end "reboot → panes back" flow.

## What is already live vs what needs an Owner step

| Capability | Status |
|---|---|
| Cold-start pane reentry (relaunch `claude --resume`) | **LIVE** — `extension/src/restore_guard.js` + `extension.js` (SCS C50), *if the PP Sessions `.vsix` is installed* |
| Snapshot freshness before crash | **LIVE** — `session_start_hub.js` hook 8 + `ram_guard.py` |
| Active power-beacon at SessionStart | **Canonical edited** — needs live-mirror sync (step 1) |
| Beacon at pre-OOM threshold | **LIVE after pull** — `ram_guard.py` (no mirror needed; PP-internal) |
| Graceful-exit beacon at SessionEnd | **Owner step** — register the SessionEnd hook (step 2) |
| Reentry recording (G5 event + G4 verdict) on cold start | **Owner step** — extension shell-out (step 3) |

## Step 1 — Sync the SessionStart hub to the live host

The canonical `hooks/session_start_hub.js` now writes the active beacon. The LIVE
hook is a separate copy (split-brain; `feedback_hook_dispatcher_split_brain_mirror`).
Activate:

```
Copy-Item "C:\Users\User\.claude\skills\claude-power-pack\hooks\session_start_hub.js" `
          "C:\Users\User\.claude\hooks\session_start_hub.js" -Force
```

Then `/restart` (hooks load once at session start). Verify after restart:
`Test-Path "$env:USERPROFILE\.claude\state\power_beacon.json"` → `True`, and its
`kind` is `active`.

## Step 2 — Graceful-exit beacon at SessionEnd (accurate classification)

Without this, a clean full-quit is *mislabeled* ungraceful (harmless — the restore
still fires — but the G5 log is then inaccurate). Register a SessionEnd hook that runs:

```
python -m modules.session_resilience.power_beacon --graceful --session-id "$SID" --cwd "$CWD"
```

(add to `~/.claude/settings.json` SessionEnd array, alongside the lazarus hooks).
After this, a clean close writes `kind=graceful` → next startup reads
`graceful-reopen`, not `ungraceful-shutdown`.

## Step 3 — Record the recovery on cold start (G5 event + G4 verdict)

The extension already relaunches panes; to also RECORD the recovery (so
`recovery_events.jsonl` carries the `ungraceful-shutdown` event and the G4 verdict
the done-gate wants), have `extension.js::runColdStartRestore` shell out once when
it acts:

```
python -m modules.session_resilience.reentry --state-dir "%USERPROFILE%\.claude\state" --live-terminals 0
```

(invoke after the restore loop, fire-and-forget). Repackage + reinstall the `.vsix`
to ship this. The reentry module is import-safe and CLI-ready today; this is the
only packaging step.

## Step 4 — Confirm the extension is installed (your actual protection)

The auto-restore depends entirely on the PP Sessions extension being active in
Cursor. Verify:

```
cursor --list-extensions | Select-String -Pattern "pp-sessions|ppSessions"
```

If absent, install the bundled VSIX: `cursor --install-extension "C:\Users\User\.claude\skills\claude-power-pack\pp-sessions.vsix"`, then reload.

## Manual GUI verification (the leg no CLI can prove)

Run this once to confirm the end-to-end contract on your machine:

1. Open Cursor with ≥2 Claude panes across a repo. Confirm `pane_map.json` is fresh
   (`build_pane_map.ps1` or just wait for the SessionStart hub).
2. Confirm `power_beacon.json` exists with `kind=active`.
3. **Simulate the power-loss:** Task Manager → End Task on Cursor (ungraceful kill;
   do NOT File→Exit). This is the closest safe analogue to the freeze→power-off.
4. Reopen Cursor.
5. **Observe (the done-gate):** after ~2.5 s the panes auto-relaunch as
   `claude --resume <id>` terminals; Cursor opens into the workspace, **not** the
   Home/Agents screen; you did nothing.
6. **Confirm the record:** `Get-Content "$env:USERPROFILE\.claude\state\recovery_events.jsonl" -Tail 5`
   shows a `recovery_started` with `cause: ungraceful-shutdown` and a
   `recovery_completed` with a verdict (RECOVERED when all live panes were restorable).

If step 5 lands on Home/Agents: the extension is not installed (step 4) or
`window.restoreWindows` was changed from `all` — both are config, not code.

## Honest boundary

A headless agent proved the backbone (classification, fsync survival, G5 event,
G4 verdict, catalog, search) with `V-G6-*`/`V-RESUME-*` gates ×3. Steps 1–3 are
host/extension wiring (gated live hooks + `.vsix` packaging); the GUI test (steps
above) is the Owner-run visual gate — the same split SCS C50 used for the cold-start
restore itself.
