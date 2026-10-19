---
covers: [ttb-wii-sdk, two-builders, wii-breakthrough, naboo-vertical-slice, wii-format-bridge]
tier: T3
status: proposed-awaiting-owner-approval
date: 2026-10-19
---

# TTB Wii breakthrough: master plan (backup of the inline plan)

Brief: Owner paste 2026-10-19 ("MISION - THE TWO BUILDERS: WII BREAKTHROUGH, NATIVE MODDING SDK & THE MEETING AT NABOO").
Related spike: `vault/plans/two-builders-pc-spike.md` (S2 texture half PASS today; S1 deferred; S3 not run).

## Reality scan (measured 2026-10-19)
- Single writer is the GEX44 clone `~/missions/tb-m2` (main 1de00ad, 15:10 today). The laptop repo
  `...\Wii Projects\LEGO-SW-Two-Builders` is main 5fb4493 (2026-10-18), behind it; do not write there.
- F-units (F2A..F6C) are Phase 25 Dolphin runs `tbl-20261019-*` on GEX44; their PREREG_/RESULT_ docs live in tb-m2/docs.
  The Kit v3 tracker (`vault/tower/sources/ttb-fidelity-v3/`) is an external audit from screenshots only
  ("no source build or Wii hardware run provided"); every row: Wii hardware NO, Owner approved NO.
- F3C = outcome B (ears shown; muzzle and tail not separable). F4B = outcome B (animation plays; the tail edit is NOT shown).
  The brief's "F4B shows modified animation playback" is not supported by the repo's own result.
- NEWRIG gate (docs/NEWRIG_GATE.md): new rig projected 174.7M, sum 331.4M against a 200M ceiling -> STOP. 88.7M spent, P80 per unit 2,819,552.
- Brief's 220,000-token budget is about 18x below one measured P80 unit; the budget must be restated in the metered unit.
- Phase 26 TB-EVIDENCE (m-34bc2fe24e53, Owner ratified, +30M over baseline 149,328,731) is armed: overlap and single-writer question.
- No Owner decision "PC primary" found in the record before this brief; the 2026-10-19 answers said PC only if the spike passes. Recorded as stated now.

## Approval (Owner, 2026-10-19)
Approved with two conditions: STAGED budget (T1 offline only, ~8M metered; each later tranche needs new evidence + Owner OK) and PC protected
(Wii must not monopolise GEX44, the Dolphin queue or all agents; PC S2 mesh / S3 not parked). Gate order H1 -> H5; H4+H5 decide on 2026-11-09.
Memory: `project_ttb_wii_sdk_mission.md`.

## Results, T1 offline (2026-10-19)
- D2A sweep (`d2a_engine.py --family-file --repo-evidence`, sees only the PP repo): fidelity layer FOLD into MOD-TOWER (95%); the four Wii
  systems KEEP (16-34% coverage); build pipeline DEFER. The Two Builders repo's own tools (chg*.py, fpk.py, lanes) are not in that evidence.
- CORRECTION of "no vertices have been added": `chg_geom.grow`/`grow_tufts` append vertex positions (copy-on-write array at end of file,
  existing display-list vertices re-pointed). Jacobo hair D9a (7 tufts) and F7B (12 short): tufts-drawn PASS in Dolphin, face intact, no
  crash; Owner CANDIDATES, not approved, not hardware. NOT done: new triangles / new display-list entries.
- H1 PASS 6/6, offline, `C:/Users/User/TB-wii-sdk/h1_identity.py` on womprat.CHG: zero-delta write byte-identical (body draw and all 504
  shared vertices), the kitten reshape touches only the position array (168 bytes), restoring the original positions gives the original
  sha, and a one-step nudge is detected (red branch). Source untouched.
- H3a: level scenes are `*.CSC` NU20 containers and the CHG detectors read them: GUNGAN_A.CSC 195 meshes, 35 decodable position arrays (all
  stride 5 = static, max 256 vertices each, 0.09..5.0 units across); GUNGAN_B 346 meshes. `grow` would refuse them (offset 0 is not the file
  size); in-place `set_positions` does not need it. Scripts: `TB-wii-sdk/h3_scan.py`, `h3_census.py`.
- OPEN H3b: instance transforms (where each piece sits in the world) are not decoded. OPEN H5: `.CTR` (collision candidate, magic = a size-like
  u32) is untouched.
- Hypothesis H6: new geometry inside an existing mesh's byte budget (rewrite a display list that fits) before any relocation.
- Fetched files live in `TB-wii-sdk/files/ro/tools` (from the GEX44 clone 1de00ad, read-only); the full clone is 2 GB+, do not repeat it.

## Next
- T2 needs the Owner: H4 is a Dolphin run (slot + queue behind TB-EVIDENCE). Offline next: H3b instance-transform census.
- Then level geometry proof (H4) -> collisions (H5) -> event -> pipeline -> decision report by 2026-11-09.
