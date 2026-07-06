# Pane Map Versioning + Workspace Session Registry -- Plan (backup)

Status: **SHIPPED 2026-07-06** (SCS C80). ULTRA-PLAN, Reality Scan STOP #1 approved by Owner.

## Problem (observed)

`pane_map.md` led with a TOTAL count -- 54 in TUA-X, 31 in PP, 32 in KobiiCraft --
totals that read as "impossible open-tab counts". Root cause (Reality Scan):
the builder lists every transcript touched within the collection window; the
`live` boolean already isolated open tabs (10 globally) but the display led with
the total. No versioning (each build overwrote). No record of which repos were
open simultaneously.

## Reality Scan findings

- **Cause of N>20:** `build_pane_map.ps1` listed every `.jsonl` touched within
  `OldHours=48h` per active repo. TUA-X had 54 recent conversations; only 5 LIVE.
  A display/framing bug, not bad data.
- **"active" today:** repo-active = snapshot cwd UNION transcript <24h; pane
  listed = transcript <48h OR in snapshot; `live` = in snapshot OR internal-ts
  <12min (anti-false-LIVE floor, RCA `T-PANE-MAP-FALSE-LIVE-MTIME-001`).
- **Versioning infra:** G3 `SessionVersionStore` (session_resilience) reusable in
  PATTERN only (atomic write + protected retention). Its `diff()` couples to
  `models.EXTRACTORS` (session dims) -- useless for pane diff. Spec asks for flat
  timestamped snapshots + 7-day prune + set-diff -> lean pane-map-native module.
- **Premise correction:** CO-12 telemetry does NOT reference a parallel-session
  concept today (grep: 0 matches). `workspace_sessions.jsonl` is a NEW source
  CO-12 *may* later consume, not an existing dependency.

## Owner decisions (STOP #1)

1. **4 tiers** -- OPEN-NOW <12min / ACTIVE <2h / RECENT <7d / ARCHIVE. Keep the
   12-min anti-false-LIVE floor (do not break what works).
2. **Snapshot cadence** -- snapshot only when the pane SET changed AND >=15min
   since the last snapshot. No duplicate files.
3. **Real-time** -- keep the existing 5-min `PP-PaneMapUpdate` task. The
   false-LIVE RCA showed sub-5min adds noise, not signal. Done-gate: update <5min.

## Implementation (shipped)

- **Sprint 1** -- `tools/build_pane_map.ps1`: 4-tier classification by internal-ts;
  ARCHIVE split to `pane_map_archive.json/.md`; panel-facing map leads with
  OPEN-NOW; legacy `live`/`status` fields preserved additively. TUA-X 54 -> 26
  panel panes (5 OPEN-NOW / 21 RECENT), 28 stale-content demoted to ARCHIVE.
- **Sprint 2** -- `tools/pane_map_snapshot.py`: timestamped snapshots under
  `~/.claude/state/pane_map_history/pane_map_YYYYMMDD_HHMM.{json,md}`, topology-
  hash change gate + >=15min interval, 7-day retention prune, `diff_snapshots`
  (added / closed / tier-changed / topic-changed). Wired into the builder
  fail-open (versioning never fails the live build).
- **Sprint 3** -- Workspace Session Registry: append-only
  `~/.claude/state/workspace_sessions.jsonl` `{timestamp, repos_live, pane_count,
  session_hash}` on each snapshot; deduped on repos_live+count.
- **Sprint 4** -- `tools/test_pane_map_snapshot.py` (6 V-gates, hermetic);
  existing `tools/test_pane_map.py` 8/8 (regression healed after restoring the
  JSON sort contract -- tier ordering is render-only).

## Done-gate evidence

- `test_pane_map_snapshot.py` 6/6 ; `test_pane_map.py` 8/8 (baseline intact).
- Live build: TUA-X panel 26 (5 OPEN-NOW), archive 108, `workspace_sessions.jsonl`
  written with repos_live, `pane_map_history/` seeded, build 13s (< 5-min task).
- Snapshot dedup verified: re-build with unchanged pane set -> no new snapshot.

## UKDL / SCS

- `PR-PANE-MAP-LIVE-ONLY-001` (ukdl-universal.md).
- SCS C80 (`scs_c80_pane_map_versioned.md` + SCS_INDEX row).
