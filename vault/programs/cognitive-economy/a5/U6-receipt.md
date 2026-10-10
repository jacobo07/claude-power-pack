STATUS: DONE
COMMITS: 7c2b6225
GATE A5_U6_PASS=13/13 (python3 tools/test_a5_u6.py, 0.08 s)
GATE ADM_PASS=43/43 (python3 tools/test_gsd_mission_admission.py)
Files: tools/resource_admission.py, vault/config/resource-floors.json, tools/test_a5_u6.py, tools/gsd_mission.py (launch_worker: new mem_reader kwarg + check before claim/spawn).
Refusal: ledger launch_refused_resources with reading; returns ok False, epoch unchanged, no spawn. Kill switch CPP_RESOURCE_ADMISSION=off (docstring of launch_worker).
Profile used: slim_profile(rec) else top-level-worker. Unreadable or raising reader -> UNKNOWN_REFUSE.
Mutant: comparator inverted (mb >= floor -> mb < floor) admits low / refuses adequate, so the refusal and control gates would fail. It is checked at the verdict level, not by rerunning the whole suite.
Host reading at test time: 54299 MB MemAvailable (/proc/meminfo).
Deviation: Windows and macOS readers are written but not run (Linux host).
HANDOFF NOTE: U6 done; run the sweep suites if other tests call launch_worker on a low-RAM host.
