Status: DONE
Unit: WU-P04-T1
HEAD: 4a34ad8f

HEAD: 4a34ad8f (pre-commit base)
RED-FIRST: test_evc_distribution.py failed before the code: importing gsdx_reforecast ran main() and exited rc 2 (no distribution, no __main__ guard); the LIVEPATH scan and CLI gates were also unmet.
VERIFY: python tools\test_evc_distribution.py -> exit 0, ALL PASS; python tools\test_gsdx_reforecast.py -> exit 0, ALL PASS
