# Evidence v4 stage2 W1 -- CCR cost contract in admit_route
Seam: tools/gsd_mission.py `admit_route` -> `_ccr_contract(rec, packet, envelope.stop)` -> `ccr_pgo.contract` (in-process import). Row stored at `admission.ccr_contract`.
Flag: `gsd_mission.py envelope --mission M --ccr-class <cls>` (stored as rec["ccr_class"]). PGO file: ~/.claude/ccr/state/pgo/<cls>.json (override dir: CPP_CCR_PGO_DIR, used by tests).
Obligation = first non-empty line of the WU packet; image = the packet; cap = route envelope stop.
Semantics:
- off/default (no class, no PGO file, any error): `{"verdict":"UNFORECAST"}`, never an error.
- observe (CPP_CCR_ADMISSION unset): contract recorded, admission verdict unchanged.
- enforce (CPP_CCR_ADMISSION=enforce): SPLIT/DEFLATE -> admission verdict RECOMPILE (known, not launchable), reasons start "ccr_contract:<verdict>".
Red first: against HEAD gsd_mission.py the new test fails with KeyError 'ccr_contract'.
Tests:
PASS V-CCRADMIT-NO-CLASS-UNFORECAST / NO-PGO-FILE-UNFORECAST / OBSERVE-RECORDS-ADMITS / ENFORCE-SPLIT-REFUSED / ENFORCE-ADMIT-ADMITTED -> 5 passed, 0 failed
test_ccr_pgo.py: CCRPGO_PASS=7/7
test_gsd_mission.py: MC_PASS=224/230 -- identical on unmodified HEAD (6 V-MC-WORKDIR/SUP-GSD/CARD worktree-path FAILs, because this checkout is itself a git worktree); not caused by W1.
