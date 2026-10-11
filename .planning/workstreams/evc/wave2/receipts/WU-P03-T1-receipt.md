Status: DONE
Unit: P03-T1 (evc wave 2)
HEAD: 68a53bcb

RED-FIRST: test run before code -> ModuleNotFoundError evc_confidence; then against a stub returning UNKNOWN/empty, 16 of 21 checks FAILED (states n=1,2 / 3,4 / >=5 / 1.1x control, degraded x2, inval3 x2, oom x3, taxonomy x3, admit x2); only the UNKNOWN/INVALIDATED-false controls passed.
VERIFY:
- python tools\test_evc_confidence.py -> exit 0, 21 passed, 0 failed
- python tools\test_cost_to_completion.py -> exit 0, all PASS
- python tools\test_route_admission.py -> exit 1: FAIL V-RADM-SLIM-T2-ADMITTED and V-RADM-SLIM-REPO-FILE-EXISTS (slim-t2 admit returns RECOMPILE). NOT caused by this unit: tools/route_admission.py and vault/config/route-floors.json are unmodified (git status clean for them); only two new files were added. Pre-existing failure, to be fixed by whoever owns slim-t2 floors; Task 2 must keep it no worse.
