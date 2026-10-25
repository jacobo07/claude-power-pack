# W3b receipt - stage tag over mission authority

Changed tools/gsd_mission.py (set_authority ~2580-2650, CLI ~6760-6905; stage lines: 2606, 2639, 6770, 6896, 6903):
- set_authority(stage=): regex-validated, current stage = last receipt's stage; opening a different stage without owner_turn raises MissionError.
- Receipt + ledger row carry stage and stage_opened; replay with same turn/figure but other stage is refused.
- recognize_overrun check untouched; CLI authority --stage; AUTHORITY SET prints stage=.
New: tools/test_w3_stage_authority.py.

Tests: test_w3_stage_authority.py W3B_PASS=6/6 exit 0; test_gsd_mission.py MC_PASS=233/233 exit 0.

COMMITS: d37fed6f369e189640652b527352f7f8e13ab5cd
