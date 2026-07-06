# SCS C78 addendum v3 — restore_panes opens ALL panes per repo, in order, via kclaude

**Sealed:** 2026-07-06
**Type:** bug fix + premise correction
**Lineage:** C78 pane-map/restore feature line — v2 was tab-order capture ([[scs_tab_order_capture_c78_addendum_v2]]); this is v3. Related: C79 pane_map freshness + resume-via-kclaude ([[scs_c79_pane_map_kclaude_resume]]).
**Files:** `tools/restore_panes.ps1`, `modules/cpc_os/vscode_autorun.py`, `tests/tools/test_restore_all_panes.py`.

---

## Reported bugs
1. Only 1 pane per repo restored after a crash (evidence: `[Lazarus] Degraded to latest valid session`, KobiiCraft got 1 of ~5).
2. Order not preserved.

## ROOT CAUSE (premise corrected)
- `restore_panes.ps1` had **no** `-First 1` / `break` / `[0]` — it never capped at 1 pane. Grep across all limiting patterns returned nothing.
- The observed 1-pane + "Degraded to latest valid session" is a **different mechanism**: `hooks/lazarus-shell-autoresume.bat:190-200` — the per-terminal profile autoresume. When a restored terminal's mapped session has no main transcript (or a FIFO collision, MC-LAZ-22), it degrades to the single latest session for the repo. That is per-terminal resolution, not `restore_panes`.
- `restore_panes.ps1`'s real limiters were: (a) it read `session_snapshot.json` (under-records — 2 panes), not `pane_map.json` (complete — 49); (b) `vscode_autorun.build_cpc_tasks` truncated to Cursor's live tab count.

## Fix
- `restore_panes.ps1` now drives from **`pane_map.json`** (all RESUMABLE/LIVE panes per repo), falling back to the snapshot only if the map is absent. Order preserved from the pane_map (which already incorporates `tab_order.json` upstream in `build_pane_map.ps1`), with LIVE panes floated to the top as a stable partition. Pause between repo-window opens (`OpenDelayMs` 500 / `LargeRepoDelayMs` 1200 for >5-pane repos). Fail-open: a repo that fails to open is logged and skipped. Printed commands use `kclaude --resume`.
- `vscode_autorun.py` gains `--no-truncate` / `truncate=False`: write ONE task PER pane (no tab-count cap); when off it skips the topology read entirely. Tasks already launch via `kclaude.bat` (Cognitive OS active). The default cap is retained for the snapshot-driven path.

## Evidence
- `restore_panes.ps1 -DryRun`: 49 panes across 6 repos (KobiiCraft 8, TUA-X 22, InfinityOps 7, power-pack 8, GEO-audit 3, Jacobo 1), LIVE-first, `kclaude --resume`.
- `tools/test_restore_all_panes.py`: `RESTORE_PASS=5/5` (ALL-PANES, ORDER, USES-KCLAUDE, TRUNCATE-DEFAULT intact, GEN-NO-TRUNCATE).

## Caveat
Auto-fire of the per-pane tasks on folder-open still needs Cursor `"task.allowAutomaticTasks":"on"` (currently `off`); otherwise the printed `kclaude --resume` lines are the deterministic manual fallback. The Lazarus per-terminal degrade (real cause of the screenshot) is a separate fix (FIFO/termkey population) — not addressed here.

## UKDL
**T-RESTORE-PANES-ONE-PER-REPO-001:** "A post-crash '1 terminal per repo' symptom is NOT necessarily a `-First 1` in the restore script — verify WHICH mechanism restored (restore_panes vs the per-terminal lazarus-shell-autoresume degrade). restore_panes must drive from the COMPLETE source (pane_map, not the under-recording snapshot) and must not let vscode_autorun truncate to the live tab count when a full restore is intended. Iterate the full per-repo array; float LIVE first; never break/-First."
