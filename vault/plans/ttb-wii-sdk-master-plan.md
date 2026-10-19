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

- H3b DONE offline (2026-10-19, `TB-wii-sdk/h3b_nodes.py`, `h3b_place.py`, `h3b_gungan_a_nodes.csv`): every draw of a level scene is referenced by a
  scene node that carries a pointer to its transform 8 bytes before the draw pointer (GUNGAN_A: 420/420 draws, 1432 nodes; NEGOTIATIONS_A: 996/996).
  Control: 420 random pointers give 2 hits at that offset and 8/420 anywhere, real draws give 1204 and 420/420 (NEGOTIATIONS_A: 28 vs 1977).
  Transform = row-major 3x4, translation in column 3 (e.g. the 5.0x3.05x5.0 piece of array@0x76d240 sits at (-1.25, 1.35, -17.99) and again at
  (-62.95, 0.05, 100.01): instancing; editing a shared array moves every instance). Stored scale of the unit is not yet tied to the character scale.
- FINDING that moves the H4 target: GUNGAN_A has 106 decodable draws (35 arrays), NEGOTIATIONS_A has 996 draws but only 1 decodable array
  (the other strides are undecoded, `chg_geom` doc: strides 2,3,4,6,7,9 unmeasured). The Dolphin harness has booted Negotiations, Tatooine and a
  ship level; it has NEVER booted Gungan (only an `area "gungan"` line in a family text, build_two_builders.py:242). So: Gungan = decodable but
  boot path unproven; Negotiations = bootable (known camera, pre-read gate) but geometry mostly undecoded. Level text files hold no world
  coordinates (spawn is in binary).
- H3c INCONCLUSIVE (2026-10-19, `TB-wii-sdk/h3c_strides.py`, NEGOTIATIONS_A, 18 (flags,stride) groups): position field picked by strip coherence
  (median edge / bbox diagonal). CONTROL passes only for the three stride-5 groups (u8@+0); this file has no stride-8 group. For the two biggest
  groups (0x1087 stride 3, 344 draws; 0x1005 stride 2, 267 draws) winner and runner-up are within 0.002, and several tiny groups score 0.000
  (too few vertices to discriminate). Not claimed: the position field of strides 2-4.
- DERIVED, consistent with all 18 groups (by hand, not yet a gate): the level flag word predicts the vertex size: bits 0x1, 0x2, 0x4, 0x40 add 1 byte;
  bits 0x8, 0x10, 0x20, 0x100 add 2 bytes; bit 0x80 adds none. A stronger instrument (cross-draw array extent, triangle area) is needed for the position field.
- PIVOT for H4 that needs no stride knowledge: `chg_mesh.collapse` (any-format hide, already Dolphin-proven) makes a chosen draw vanish; a missing large
  object in the known Negotiations camera is unambiguous evidence that an edited level scene is loaded and drawn. Moving geometry waits for H3c.

## Next
- T2 released by the Owner ("y", 2026-10-19) but NOT spent. H4 candidate: collapse the N largest Negotiations draws in one run, bisect afterwards.
- Packet for the mission worker, not a direct write by this pane: probe `level-geom-<target>` + PREREG (ADMIT) in the tb-m2 clone, one Dolphin run.
- Then collisions (H5) -> event -> pipeline -> decision report by 2026-11-09. PC lane: S2 mesh half and S3 are next, not parked.
