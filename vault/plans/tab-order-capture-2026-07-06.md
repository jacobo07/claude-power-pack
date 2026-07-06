# Plan Backup — Tab Order Capture via tabGroups (SCS C78 addendum v2)

Date: 2026-07-06 | Mode: EXECUTION | Owner-approved premise: Claude panes are
editor-area terminals (real tabs), so `vscode.window.tabGroups` sees them.

## Problem
`build_pane_map.ps1` orders panes by `lastActivity` (timestamp). The Owner wants
the real **visual** left-to-right tab order in Cursor. Only an extension can read
that, via `vscode.window.tabGroups` — a `.ps1` cannot. So the extension must write
the order to disk and the builder must consume it.

## Reality contract
Not done until: `pane_map.md` reflects the real tab order (not `last_active`), AND
reordering tabs in Cursor → regenerated `pane_map` reflects the new order.

## Join key
PP Sessions names each pane terminal `${repo} ${sid8}` (extension.js `resumePane`
/ `runColdStartRestore`). The **8-hex session-id prefix** in the tab label is the
join key back to a pane in `pane_map.json`.

## Steps
- **E1** `extension/src/tab_order.js` — pure vscode-free transform (mirrors
  `restore_guard.js`): `tabsToOrder(groups)` → ordered `{label, group_index,
  tab_index, is_active, is_terminal, sidPrefix}`. `extension.js` normalizes
  `tabGroups.all`, resolves `is_terminal` via `TabInputTerminal`, atomically
  writes `~/.claude/state/tab_order.json` on startup + `onDidChangeTabGroups` +
  `onDidChangeTabs`. Fail-open: any throw → no write.
- **E2** `build_pane_map.ps1` — read `tab_order.json` if present; rank panes by
  first tab whose `sidPrefix` matches `sessionId[:8]`; sort matched-first in tab
  order, unmatched tail most-recent-first. Absent/malformed/zero-match → pure
  `last_active` (failsafe intact).
- **E3** rebuild the `.vsix` via `tools/install_pp_extension.ps1` (plain JS, no
  TS compile; new `src/tab_order.js` auto-packed). Owner reloads:
  `Ctrl+Shift+P → Developer: Reload Window`.
- **E4** hermetic V-gates ×3 (`test_tab_order.py`) + `test_pane_map.py`
  V-SORTED made tab-order-aware. UKDL `T-TAB-ORDER-EXTENSION-ONLY-001`.

## Fail-open invariant
tabGroups unavailable / capture throws → `tab_order.json` not written →
`pane_map` uses `last_active` with no error.
