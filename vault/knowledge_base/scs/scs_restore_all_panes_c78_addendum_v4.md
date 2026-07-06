# SCS C78 addendum v4 — restored terminal name = pane_map topic (not "claude"/"cmd")

**Sealed:** 2026-07-06
**Type:** feature
**Lineage:** C78 pane-map/restore line — v2 tab-order capture ([[scs_tab_order_capture_c78_addendum_v2]]), v3 restore-ALL-panes ([[scs_restore_all_panes_c78_addendum_v3]]); this is v4.
**Files:** `modules/cpc_os/vscode_autorun.py`, `extension/src/extension.js`, `tools/restore_panes.ps1`, `tools/test_vscode_autorun.py`.

---

## Problem
Restored terminals showed the terminal-profile / shell name ("claude", "cmd") as the tab name — the Owner could not tell which session a tab held without opening it. The distinguishing label (`topic`) already existed in `pane_map.json` but never reached the tab.

## Feasibility (PASO -1, empirical)
- Dominant restore path = auto-tasks (`task.allowAutomaticTasks:"on"` confirmed). VS Code names a task's terminal after its task **label** → the reliable lever.
- `pane_map.json` panes carry `topic` (the label source) ✓.
- Cursor had **no** `terminal.integrated.tabs.title` override → default `${process}` shows the shell name; an OSC title (`\x1b]0;…\x07`) lands only in the tab *description* under the default, so an escape-sequence rename (Mechanism A) needs an Owner-side settings change and is host-limited/unverifiable headless.
- `vscode.Terminal.name` is READ-ONLY; the extension can only name terminals it *creates* (`createTerminal({name})`).

## Mechanism (chosen: C + B, Owner-approved)
- **C — task label = topic** (`vscode_autorun.py`): the `folderOpen` task label is now `_term_label(topic, repo, sid8)` = `"<repo> - <topic>"` truncated to 40 chars, with the 8-hex session id appended (the join key `tab_order.js::sidPrefixOf` reads back). The stable "is-this-ours" sentinel moved from the label prefix to the task **`detail`** field, so `merge_tasks`/`_is_cpc_task` still replace only our tasks idempotently while the label is free to be the human-readable topic. Legacy `CPC-Restore:`-prefixed tasks are still detected on merge (back-compat cleanup).
- **B — extension `createTerminal({name})`** (`extension.js`): `resumePane` (click) and `runColdStartRestore` (cold start) now name their terminals via `termName(p)` — the same `<repo> - <topic> <sid8>` shape, mirroring `_term_label`. (Was `${repo} ${sid8}`.)
- `restore_panes.ps1` threads `topic` + `repo` from the pane_map into the records and the auto-run snapshot so `vscode_autorun` has the label source. Fail-open: no topic → repo name; no repo → cwd leaf → `"claude"` — never an empty label.

## Evidence
- `tools/test_vscode_autorun.py`: `AUTORUN_PASS=17/17` — incl. **V-TERMINAL-NAMED-FROM-PANE-MAP** (`'TUA-X - MODO: EXECUTION MODE Business Ph 1022d113'`) and **V-FALLBACK-TO-REPO** (`'repoX deadbeef'`) + V-FALLBACK-TO-CWD-LEAF.
- `tools/test_tab_order.py` 3/3, `tab_order.js --selftest` 5/5, `node --check extension.js` OK, `tools/test_restore_all_panes.py` intact.

## Host-limited done-gate (Owner eyeball — the ONE thing not verifiable headless)
Confirm on one real restored tab that `claude.exe`/`cmd` does NOT stamp its own console title over the task label. If it DOES, Mechanism C is overridden and Mechanism A (OSC from the wrapper) + an Owner-side `terminal.integrated.tabs.title:"${sequence}"` setting is the fallback. Mechanism B (extension-created tabs) is immune to this — `createTerminal` names are authoritative.

## Activation caveat (Owner-side, HR-001)
Mechanism B takes effect only after the PP Sessions `.vsix` is rebuilt + reinstalled + **Reload Window**. Mechanism C takes effect on the next `restore_panes.ps1 -AutoRun` (regenerates tasks.json). Neither is auto-applied by the agent.

## UKDL
**T-TERMINAL-NAME-FROM-PROFILE-001:** "Terminals opened from a Cursor terminal profile (or reconnected by persistent-sessions) inherit the PROFILE name ('claude', 'cmd'), not the pane label. To show the pane label: (a) for task-fired terminals, set the task **label** to the topic — VS Code names the terminal after the task label (no settings change); (b) for extension-created terminals, pass `name` to `createTerminal` (authoritative, immutable by shell OSC); (c) an OSC rename `\x1b]0;<label>\x07` reaches profile terminals but under default `terminal.integrated.tabs.title` surfaces only as the tab *description* — needs `${sequence}` in that setting AND is host-limited. `Terminal.name` is READ-ONLY; existing terminals cannot be renamed via the API. Verify with a real tab before assuming any rename wins — claude.exe/cmd may stamp its own console title."
