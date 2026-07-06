# SCS C80 -- Pane-Map-Versioned + Workspace Session Registry

Sealed: 2026-07-06 | State: Sealed | UKDL: `PR-PANE-MAP-LIVE-ONLY-001`

## Summary

The pane map is now **versioned, tiered, and correlated with a workspace
registry**. Snapshots every change (>=15min gate), 7-day retention, diff between
versions. LIVE/RECENT/ARCHIVE separated: the panel-facing map shows OPEN-NOW +
ACTIVE + RECENT; ARCHIVE (content dragged into the window by a batch mtime-touch)
is written separately. The Workspace Session Registry records which repos held
OPEN-NOW panes at each snapshot instant.

Downstream of C79 (pane_map + PP Sessions resume uses kclaude). C79 made resume
correct; C80 makes the map's *counts* honest and its *history* durable.

## What shipped

| Piece | Artifact |
|---|---|
| 4-tier classification + ARCHIVE split | `tools/build_pane_map.ps1` (OPEN-NOW <12m / ACTIVE <2h / RECENT <7d / ARCHIVE) |
| Versioning + registry engine | `tools/pane_map_snapshot.py` (`take_snapshot`, `diff_snapshots`, `prune`, `append_workspace`) |
| V-gates | `tools/test_pane_map_snapshot.py` (6/6) |
| New outputs | `pane_map_archive.{json,md}`, `pane_map_history/pane_map_YYYYMMDD_HHMM.{json,md}`, `workspace_sessions.jsonl` |

## Key design points

- **Tier = internal-timestamp age, not mtime** -- immune to batch mtime-touch
  (RCA `T-PANE-MAP-FALSE-LIVE-MTIME-001`). The 12-min OPEN-NOW floor is retained.
- **Change gate = topology hash** (set of sessionIds). A snapshot is written only
  when a pane opened/closed AND >=15min elapsed -> no duplicate files. Pure tier
  aging does not trip a snapshot; the diff still surfaces tier/topic changes.
- **G3 reuse = pattern, not class** -- atomic write + protected retention borrowed
  from `modules/session_resilience/snapshot_versioning.py`; flat timestamped
  snapshots stored instead of a baseline+delta chain (spec verbatim; G3's diff is
  EXTRACTOR-coupled).
- **JSON sort contract preserved** -- `panes` array keeps tab-rank-then-
  lastActivity order (extension + `V-SORTED-RECENT-FIRST` hold). Tier-led ordering
  is render-only in the `.md`/card.
- **Workspace registry is standalone** -- `repos_live` is a NEW source CO-12
  telemetry MAY later consume; it does not reference it today (premise corrected
  at STOP #1).

## Evidence

- `test_pane_map_snapshot.py` 6/6 ; `test_pane_map.py` 8/8 (baseline intact).
- Live: TUA-X 54 -> 26 panel panes (5 OPEN-NOW), 108 archived, registry + history
  seeded, build 13s (< 5-min `PP-PaneMapUpdate` task).

## Owner-side / pending

- The 5-min `PP-PaneMapUpdate` scheduled task already invokes the builder, which
  now calls the snapshot step fail-open -- no task change required.
- `pane_map_history/` retention is self-managing (7-day prune inside the module).
