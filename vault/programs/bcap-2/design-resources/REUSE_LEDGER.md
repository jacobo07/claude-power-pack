# BCAP-2 Phase 8 — 21 design resources: Workstream A slice (PARTIALLY_PROVEN) — 2026-11-19

Owner: `modules/cdicf` (EXTEND; component selection stays in selector.js, on-disk licence tiers stay in lib/license_gate.js). No new registry, no new owner.
Built: `SOURCES.json` (21 source records parsed from the backlog table: id, name, slide group, canonical URLs, screenshot claim, rights posture from backlog section 2),
`modules/cdicf/source_intake.py` (pinned 21-id denominator, coverage, count drift, fail-closed `admit_code`, item/version-aware `asset_license_ok`, `done_check`),
gate `python3 tools/test_bcap2_d21.py` (27 checks, both poles, on the real registry): V-D21-01/02/03/04/05/06/07/09/10/24/25/31/36 + A06 known conflicts.

**No network was used.** Every record is `live_verified: false`, `last_checked: null`; rights postures are the backlog's own statements, not re-read from the sites.
Capability denominators (A03) are `UNKNOWN (not derived)` for all 21; catalog entries (A04), pinned SHAs (A05) not captured.
D21-13 Anime.js is owned by Phase 4 (juliangarnier/anime MIT @ 01b81be1); the other 20 have no absorption.

## Residuals (not hidden)
- 23 of 36 falsification scenarios not driven (V-D21-08, 11-23, 26-30, 32-35: need browser, real catalogs, or Workstreams B-H).
- Workstreams B-H (reference intelligence, DESIGN.md compiler, component fabric, motion/effects, maps, art, routing) not started; DESIGN.md Apache-vs-"Proprietary" drift (D21-05) recorded, not reconciled.
- Next: fetch-read-only per-source licence/terms (batch with other owed upstream reads), derive capability denominators, then B/C pilot.
