# G1 — Editor State Capture/Apply — Extension-JS Spec (Owner-run gate)

**Status:** Spec (Path A). The Python-feasible half ships in
`modules/session_resilience/ui_state.py` (tested); the 7 capture/apply entities
below are **extension-JS** because Python cannot touch Cursor's UI. The headline
visual gate ("indistinguishable from a Reload Window") is **Owner-run** — a
GUI-only check with no CLI (SCS C50 precedent). Nothing here is shipped as
runnable-but-unverified code; it is a contract for the extension to implement.

## Why JS, not Python
Editor tabs/order/focus/scroll live in the editor host. Only an extension can
read them (`vscode.window.tabGroups`, `TextEditor.visibleRanges`,
`window.activeTextEditor`) and re-apply them (`window.showTextDocument`,
`TextEditor.revealRange`). Python has zero UI access. Cursor/VS Code already
restores most editor layout + scroll on a normal reload via hot-exit; this spec
covers the **cold-start / post-OOM-reboot** case where host state is gone.

## The 7 capture/apply entities (extension responsibilities)

1. **Editor Tab Inventory** — `vscode.window.tabGroups.all[*].tabs[*]` → for each
   tab emit `{path, group, order, pinned, preview, kind}`. Untitled/unsaved tabs
   flagged unrestorable-by-path.
2. **Tab Ordering** — tab index within its group is the `order` field; order is
   state, captured on reorder.
3. **Active Focus** — `tabGroups.activeTabGroup` + `activeTextEditor` →
   `{window_id, group, path}`. Validate the target is in the inventory.
4. **Scroll & Cursor Position** — `editor.visibleRanges[0].start.line` /
   `editor.selection` → store as a **fraction of document** (`line / lineCount`).
   **Apply is approximate** via `revealRange(..., InCenter)`; exact pixel scroll
   is NOT a public API → declared a host limit (handled by G4 scroll tolerance).
5. **Panel Layout** — sidebar/panel/auxbar visibility + active view via workbench
   state where exposed; sizes are best-effort (host may not expose exact dims).
6. **Editor Split Topology** — `tabGroups.all` arrangement (rows/cols) → rebuild
   groups BEFORE placing tabs (topology-before-content, mirrors CETTG).
7. **Pinned & Preview Classifier** — `tab.isPinned` / `tab.isPreview` → restore
   pinned as pinned; preview may be skipped per policy to avoid noise.

## Data contract (capture → Python)
The extension writes one window's editor manifest in the exact shape
`ui_state.build_editor()` produces: `{tabs:[{path,group,order,pinned,preview}],
focus:{window_id,group,path}|null, scroll:{<path>:0..1}, panels:{...},
splits:{...}}`. The Python side canonicalizes it (diff adapter), marks
host-unrestorable properties (`mark_unrestorable`), and the manifest becomes the
`editor` portion of a window in the canonical StateDescription that
`multi_window.window_state_description()` assembles, G3 versions, and G4 scores.

## Wiring
Extend `extension/src/extension.js`: on capture cadence write each window's editor
manifest beside `pane_map.json`; on cold-start restore (the existing guarded path)
apply tabs → focus → scroll (approximate). Reuse the `restore_guard.js` pattern
(pure decision logic, side-effects at the edge).

## Capability-aware acceptance
`ui_state.g4_host_capabilities()` yields the G4 dimension set the host can
restore. Where a property is genuinely unavailable on a host/version, it is
excluded from G4's equivalence denominator (reported, not failed); a property the
host COULD restore but didn't remains a real miss. Scroll stays in the set but is
graded by tolerance, not exact match.

## Done-gate (Owner-run, not agent-certifiable)
1. Pre-crash: open tabs in a known order, one focused, scrolled.
2. Kill the Cursor process (true cold start).
3. Reopen → observe tabs/order/focus restored, scroll within tolerance.
4. G4 returns RECOVERED (or PARTIAL with the scroll/host gap logged by G5).
5. Owner confirms it is visually indistinguishable from a Reload Window.

The agent-run gates (`tools/test_session_resilience_build.py`) cover the Python
half: manifest model, diff adapter, capability marking, and the G1→G2→G3→G4
compose path. Step 5 is the Owner's to run after the extension lands.
