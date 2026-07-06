# SCS C78 addendum v2 — PP Sessions tab-order capture

Sealed: 2026-07-06 | Downstream of SCS C78 (CDIO) numbering; this is an addendum
to the PP Sessions pane-map subsystem, not a new C-number (multi-pane worktree —
avoids a fresh-number collision race).

## Statement

PP Sessions captures the real visual order of Cursor tabs via
`vscode.window.tabGroups` → `~/.claude/state/tab_order.json`.
`build_pane_map.ps1` consumes `tab_order.json` to order the pane map by the real
visual tab order instead of `lastActivity`.

## UKDL — T-TAB-ORDER-EXTENSION-ONLY-001

The real left-to-right order of Cursor tabs is ONLY accessible from inside an
extension via `vscode.window.tabGroups`. `build_pane_map.ps1` cannot read the
order directly — it needs the extension to write it to `tab_order.json` first. If
the extension is not active (or the panes are panel terminals, not editor-area
tabs), the order falls back to `lastActivity`.

## Mechanism

- **Writer** (`extension/src/extension.js` + pure `extension/src/tab_order.js`):
  on activation and on `onDidChangeTabGroups` / `onDidChangeTabs`, normalizes
  `tabGroups.all` → atomically writes `tab_order.json` (tmp + rename). The join
  key back to a pane is the 8-hex session-id prefix PP Sessions embeds in each
  pane terminal's name (`${repo} ${sid8}`).
- **Reader** (`tools/build_pane_map.ps1`): ranks panes by the first tab whose
  `sidPrefix` matches `sessionId[:8]`; matched panes lead in tab order, the
  unmatched tail stays most-recent-first.
- **Fail-open (absolute):** `tabGroups` unavailable, capture throws, file absent
  or malformed, or zero matches → `tab_order.json` not consumed → pure
  `lastActivity` order, no error. Failsafe identical to prior behavior.

## Gates (hermetic ×3 — `tools/test_tab_order.py`)

- `V-TAB-ORDER-WRITTEN` — `tab_order.js --selftest` proves the transform emits
  `label + group_index + tab_index + sidPrefix` in stable visual order.
- `V-PANE-MAP-USES-TAB-ORDER` — build with `tab_order.json` present orders panes
  by tab position, overriding `lastActivity`.
- `V-FALLBACK-LAST-ACTIVE` — build with no `tab_order.json` → recent-first.

Plus `tools/test_pane_map.py` `V-SORTED-RECENT-FIRST` made tab-order-aware
(unmatched tail must stay recent-first).

## Owner activation

Rebuild + install: `pwsh tools/install_pp_extension.ps1` (shipped
`kobii.pp-sessions@0.3.0`). Then **Ctrl+Shift+P → Developer: Reload Window** to
activate the capture. On reload, `~/.claude/state/tab_order.json` is written; the
`PP-PaneMapUpdate` scheduled task (5-min, SCS C79) then regenerates the pane map
in real tab order automatically.

Reality contract satisfied for editor-area terminal tabs (Owner-confirmed setup):
reorder a tab in Cursor → `tab_order.json` updates → regenerated `pane_map`
reflects the new order.
