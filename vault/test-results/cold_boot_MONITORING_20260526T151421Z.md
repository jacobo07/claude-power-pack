# Cold boot suite — Monitoring/Alert Axis

**Run:** 20260526T151421Z UTC
**HEAD:** db2e455

## tools/test_monitoring.py
```
  [PASS] V-ALERTS-LIST: top-2 newest-first: ['20260526T120000Z', '20260525T120000Z']
  [PASS] V-STATUS-NO-CHECK: rc=0 run_check_calls=0
============================================================
Result: 16/16 PASS
```

## tools/test_tis_core.py
```
PASS  V-TIS-PERSIST  path=tis-core-_fyb0lpa\token_logs\2026-05-26.jsonl
PASS  V-TIS-NONZERO  in=100 out=50 cr=25 cc=5

TIS_CORE_PASS=6/6  threshold=6/6
```

## tools/test_tis_e2e.py
```
PASS  V-E2E-3 report-summary  rc=0 has_table=True has_session=True has_nonzero=True
PASS  V-E2E-4 handoff-emits  rc=0 files=1 consumed=True savings=True candidate=True

E2E_PASS = 4/4
```

## tools/test_lateral_thinking.py
```
PASS  V-LT-FIXTURE wrote vault\ceps\lt_empirical_20260526T151430Z.json (5322 B)
PASS  V-LT-CARD-CONTENT len=468 contains_keys=yes

All gates PASS. Empirical fixture awaiting Owner scoring.
```

## tools/test_ceps_closed_loop.py
```
PASS  V-CEPS  verify-spp-stub                sig=6bbefb10 top-3 hit
PASS  V-CEPS  auto-testing-gate-ci           sig=d894548a top-3 hit

CEPS_PASS=10/10  threshold=>=7/10
```

## tools/test_ceps_full_cycle.py
```
PASS  V-FULL-7 pytest-skip-honored  rc=0
PASS  V-FULL-8 baseline-29-PASS  rc=0

CYCLE_PASS=true  (record -> events -> distribute -> propagate -> stub -> pytest-skip-honored -> baseline-intact)
```

## tools/test_ceps_edge_cases.py
```
PASS  V-EDGE-FTS-PUNCT  hits=0 (no crash)
PASS  V-EDGE-LONG-PROMPT  prompt_words=760 card=fired

EDGE_PASS=6/6  threshold=6/6
```

## pytest tests/ (excl cascade_populator preexisting)
```
.............................                                            [100%]
29 passed in 0.55s
```

## verify_spp single-row monitoring-axis
```
  [...] monitoring-axis ...
  [OK  ] monitoring-axis        rc=0     0.23s  MONITORING_AXIS: 6/6 sub-checks PASS
========================================================================
  total elapsed: 0.23s
  STRICT PASS — 1 of 1 rows OK
========================================================================
```

## /observe --once --project all (LIVE network)
```
PP Monitoring -- status

PROJECT        | STATUS   | LAST_CHECK             | EVIDENCE
-------------- + -------- + ---------------------- + ------------------------------------------------------------
infinityops    | UP       | 2026-05-26T15:14:44Z   | curl https://infinityops.ai/ contained pattern 'br.jula' on attempt 1
kobiicraft     | UNKNOWN  | 2026-05-26T15:14:46Z   | tcp connect to 5.9.23.174:25565 failed all 1 attempts; last error: ConnectionRef
tua-x          | UP       | 2026-05-26T15:14:46Z   | curl https://cw.infinityops.ai/ returned HTTP 200 on attempt 1

P2.3 health-all absorbed by --once flag (one snapshot, N projects).
```
