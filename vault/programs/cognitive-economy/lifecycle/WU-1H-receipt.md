# WU-1H receipt -- Amendment D L1 (halt continues the mission)

Status: DONE (code + tests committed; no deploy, HR-001).
Commit (code, tests, packets): d948be61 on ce/lifecycle-v2 (subject carries a stray BOM; cosmetic).

## Gates
- tools/test_halt_continues.py: HALT_CONTINUES_PASS=10 FAIL=0 (_logs/wu1h4/test_halt_continues.log)
- Mutants 3/3 KILLED: V-LIFE-HALT-RECEIPT-PRESENT, V-LIFE-HALT-ONCE, V-LIFE-SUCCESS-NO-RECEIPT (_logs/wu1h3/mut1..3.log)

## Suites (WU-1H4, _logs/wu1h4/)
- test_gsd_mission.py: MC_PASS=224/225; sole FAIL V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED is pre-existing (WU-1B receipt).
- test_gsd_mission_admission.py: ADM_PASS=43/43
- test_process_lifecycle.py: LIFE_PASS=5 FAIL=1 -- V-LIFE-PREMODEL-TRANSPORT ("planted block survives the real dispatcher"
  returned '{}'). WU-1B recorded 6/0. NOT attributable to this diff: only tools/gsd_mission.py changed, that test never
  references gsd_mission and hooks/ is unmodified. Not re-proved on a HEAD export (export lacks hooks/). OPEN POINT for
  WU-INST: confirm on clean HEAD whether the live dispatcher environment regressed.

## Epochs
1H 926K, 1H2 755K, 1H3 645K, 1H4 (this; 7-call cap).

## For WU-INST
sha256 tools/gsd_mission.py = 48B2AED4A2BD889A1CEBA64C187B804370F83E6081E17D0BCD7EDF86853698C9 (not deployed).

## Addendum B
Second format, mission-level.