# D11 step 0 -- Wii Sports Tennis: location and overlap with the Resort factory binary (zero-model, 2026-10-08)

Work dir: `C:\Users\User\Apps\recon_work\wst_tennis\step0\` (disc dump, file list, extracted DOLs, DTK split, `probe_tennis.py`,
`step0_report.json`). No model tokens were spent; everything below is a tool reading.

## Disc (wit 3.05a DUMP/FILES on SP2P01.wbfs)
- PAL, IOS 56, one DATA partition, 854 files. `sys/main.dol` (1,367,168 B) is the launcher.
- Wii Sports = `files/EU/sys/sports/SportsPackEP.dol` (4,343,616 B, sha256 prefix fa0f39d839a178e8). No RELs: Tennis
  lives inside this DOL (scenes `RPTnsScene`, assets `sports/Common/RPTnsScene/common.carc`).
- Resort = `files/EU/sys/resort/WiiSports2P.dol` (7,348,032 B, sha256 prefix e6e37e6bcae3f229). It is NOT the factory's
  binary (main.dol sha256 855e4ffe...). Resort work transfers by shape, not by identity.

## DTK v1.8.4 (the certified binary) on SportsPackEP.dol
- `dol config` + `dol split`: 14,885 functions found, 560 objects, 9.1 s.
- The probe's `.fn` count is 18,820 (Resort split: 38,358 = 34,159 census + 4,199 gap fillers, same convention).

## Tennis location (heuristic, stated as such)
- 21 data objects carry Tennis strings (`RPTnsScene/`, `Tns_ply_good_*`, `tennisText_*.brlan`, ...), 9 pointer tables
  reach them, 13 functions reference them, spread over 6 DTK objects (58 to 973 functions each).
- Candidate Tennis = those 6 objects = 1,797 functions, 100,947 instructions. This is an UPPER bound: DTK's auto
  objects are coarse. The real Tennis code and its motion closure need a call-graph walk from the scene.

## Shape overlap with the Resort factory split (symbols masked = exact; symbols and numbers masked = loose)
| scope | functions | exact shape in Resort | loose |
|---|---|---|---|
| whole SportsPackEP.dol | 18,820 | 11,935 (63%) | 13,035 (69%) |
| Tennis candidate | 1,797 | 408 (23%) | 574 (32%) |

Reading: the engine and libraries are mostly shared with Resort; the sport code is mostly novel (Resort has no tennis).
A shape match is a donor, not a MATCH; each still needs its own compile and both oracles.

## Consequence for the estimate
- Onboarding the Wii Sports DOL (corpus, census, split certification, oracle parity) is a fixed cost, and most of its
  engine can be solved through Resort donors once those exist.
- Tennis-specific novel code is ~1,200-1,400 functions at most (candidate minus exact overlap); the motion closure is
  a subset, sized by the next probe (call-graph walk from the Tennis scene and the Wiimote/KPAD read path).
