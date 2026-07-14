# Cursor: startup layout (IDE vs Agents) + tab revival

Sealed 2026-07-14. Host: Windows 11, Cursor 3.11.13.

## PR-CURSOR-STATE-VSCDB-AUTHORITY-001

The startup layout (IDE vs Agents) is **not** a `settings.json` setting. It lives in
the reactive-storage DB:

```
%APPDATA%\Cursor\User\globalStorage\state.vscdb   table ItemTable
key:   cursor/unifiedAppLayout
values: "agent" | "editor"        (factory default: "editor")
```

Evidence in the bundle (`resources\app\out\vs\workbench\workbench.desktop.main.js`):
`unifiedAppLayout: _Be(aD.Editor, -1, 0)` and `e.Agent="agent", e.Editor="editor"`.

Cursor registers only **4** `cursor.*` keys in the VS Code settings registry
(`blame.hoverDelay`, `debug.timeoutPrevention`, `rpcFileLogger.enabled`,
`rpcFileLogger.folder`). No mode/view/startup key among them. Searching
`settings.json` for a startup-mode key is a dead end by construction.

When the value is `agent`, the layout hides the editor outright
(`agentLayout.shared.v6` carries `editorVisible:false`). This is why
`workbench.startupEditor: "none"` has no effect on the symptom: the editor is not
opening on the wrong page, it is not being shown at all.

**Flip it from the UI, not from the DB.** The commands
`workbench.action.toggleAgents` and `cursor.toggleAgentWindowIDEUnification` are
registered and reach this key; Cursor persists the new value itself. A direct
sqlite write while Cursor is running is worse than useless — the app flushes its
in-memory storage over the DB on exit, silently reverting the write. A DB write is
only correct with every Cursor window closed, and it needs a backup first.

## T-CURSOR-OBSOLETE-KEYS-001

`window.reopenFolders` is a removed VS Code key, superseded by
`window.restoreWindows`. It does not exist in Cursor. Writing it produces an inert
"Unknown Configuration Setting" and no behavior. The live key is
`window.restoreWindows: "all"`.

## T-CURSOR-TAB-LIMIT-RAM-TRADEOFF-001

`workbench.editor.limit.enabled: true` + `workbench.editor.limit.value: 3` closes
tabs beyond 3 per group. It is a RAM guard, and it caps tab revival regardless of
`window.restoreWindows` / `files.hotExit` / `workbench.editor.restoreViewState`.
Raise the value (50) rather than disabling the limit — keep the ceiling, move it.

## Validating this settings.json

`settings.json` is **JSONC** (it carries `//` comments), so `python -m json.tool`
rejects it and that rejection is not evidence of corruption. Strip comments outside
string literals, then `json.loads`. A malformed settings.json stops Cursor from
starting: back up to `settings.json.bak` before any write.

## Post-restart procedure

1. Open Cursor — starts in IDE once `cursor/unifiedAppLayout` is `editor`.
2. Let it restore windows, folders and tabs (up to 50 per group).
3. Revive the `claude.exe` panes in waves rather than all at once.

Step 3 has no shipped tool yet: `staged_revival.py` does not exist in this repo
(verified by glob). It belongs to the staged-revival sprint; do not improvise a
substitute here.
