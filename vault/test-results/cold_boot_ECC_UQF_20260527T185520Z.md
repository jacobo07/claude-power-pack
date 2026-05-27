# Cold-boot ECC_UQF -- 20260527T<TS>
## test_uqf.py
PASS  V-UQF-REGISTRY                 loaded 9 principles
PASS  V-UQF-PRE-REPORT-PASS          score=1.0
PASS  V-UQF-PRE-REPORT-FAIL          score=0.0 missing keys
PASS  V-UQF-ZERO-FINDINGS            [] accepted as clean
PASS  V-UQF-FALSE-POS                caught FP: matched FP pattern: 'consider adding error handling'
PASS  V-UQF-PROOF-TRIAD              HIGH without triad rejected score=0.0
PASS  V-UQF-ERROR-SILENT             bare-except detected: 2 violations: ["line 3: bare 'except:' (no excepti
PASS  V-UQF-ERROR-TYPED              typed-except OK
PASS  V-UQF-PROMPT-DEFENSE           CLAUDE.md covered=6/6
PASS  V-UQF-ANTI-BARE                detected at line 3
PASS  V-UQF-ANTI-TYPE-HINTS          detected `public_func`
PASS  V-UQF-AUDITOR-SCORE            ceps.py=20.0% (in 0-100)
PASS  V-UQF-CEPS-CONFIDENCE          compute_confidence(2,True)=0.7
PASS  V-UQF-CEPS-PROMOTE             promotion logic correct
PASS  V-BASELINE-INTACT              rc=0 last='[32m[32m[1m43 passed[0m[32m in 0.99s[0m[0m'

UQF_PASS=15/15  threshold=15/15

## test_tco.py
[isolate] tmp=~\AppData\Local\Temp\tco-test-yj02utde
PASS  V-COMPACT-OK                   pct=3% rec=OK
PASS  V-COMPACT-WARN                 pct=73% rec=WARN
PASS  V-COMPACT-HARD                 governor=2 warns
PASS  V-ROUTE-SONNET                 -> claude-sonnet-4-6
PASS  V-ROUTE-OPUS                   -> claude-opus-4-7
PASS  V-ROUTE-DEFAULT                -> claude-opus-4-7
PASS  V-PROJECTION                   rc=0 fields=ok
PASS  V-BASELINE-INTACT              rc=0 last='[32m[32m[1m43 passed[0m[32m in 0.92s[0m[0m'

TCO_PASS=8/8  threshold=8/8

## test_tis_core.py
[isolate] tmp=~\AppData\Local\Temp\tis-core-2i9ske7m
PASS  V-TIS-APPEND  entries=1
PASS  V-TIS-IDEMPOTENT  delta=2
PASS  V-TIS-SCHEMA  missing=none keys=10
PASS  V-TIS-SESSION  a=34439ff8 b=34439ff8
PASS  V-TIS-PERSIST  path=tis-core-2i9ske7m\token_logs\2026-05-27.jsonl
PASS  V-TIS-NONZERO  in=100 out=50 cr=25 cc=5

TIS_CORE_PASS=6/6  threshold=6/6

## test_tis_e2e.py
[isolate] tmp=~\AppData\Local\Temp\tis-e2e-pqq35m2s
PASS  V-E2E-1 mock-dispatch  sid=e2e-test dispatched=3
PASS  V-E2E-2 entries>=3  count=3
PASS  V-E2E-3 report-summary  rc=0 has_table=True has_session=True has_nonzero=True
PASS  V-E2E-4 handoff-emits  rc=0 files=1 consumed=True savings=True candidate=True

E2E_PASS = 4/4

## test_monitoring.py
V-block tests for Monitoring/Alert Axis
============================================================
  [PASS] V-POLL-ONCE-UP: status=UP alert=None
  [PASS] V-POLL-ONCE-DOWN: status=DOWN alert=UP_TO_DOWN consec_f=3
  [PASS] V-DEBOUNCE-NO-ALERT: status=UP alerts=[None, None]
  [PASS] V-DEBOUNCE-RECOVERY: status=UP alert=DOWN_TO_UP
  [PASS] V-STATE-PERSIST: roundtrip ok: status=DOWN cf=3
  [PASS] V-ALERT-FILE-CREATED: path=20260527T185433Z_fix6_UP_TO_DOWN.md body_len=279
  [PASS] V-ALERT-STDOUT: stdout_chars=73; tag_present=True
  [PASS] V-NO-AUTO-ROLLBACK: call sites of rollback() across monitor/observe/alert: 0
  [PASS] V-CONFIG-INHERIT: defaults applied: deb_f=3, deb_s=2, min_dur=30, interval=60
  [PASS] V-ONCE-FLAG: rc=0 table_has_project=True p23_line=True
  [PASS] V-ONCE-MULTIPROJECT: rc=0 all 3 projects in table: True
  [PASS] V-DAEMON-NO-INSTALL: rc=0 cron+TS in stdout=True install_calls=0
  [PASS] V-RETENTION-PURGE-DROP: dropped=1 files=['20260328T185433Z_fixE_UP_TO_DOWN.md']
  [PASS] V-RETENTION-PURGE-KEEP: dropped=0 remaining=1
  [PASS] V-ALERTS-LIST: top-2 newest-first: ['20260526T120000Z', '20260525T120000Z']
  [PASS] V-STATUS-NO-CHECK: rc=0 run_check_calls=0
============================================================
Result: 16/16 PASS

﻿## test_lateral_thinking.py
PASS  V-LT-FIRE-algorithmic    ctx_len= 468 lt=yes
PASS  V-LT-FIRE-product-ux     ctx_len= 468 lt=yes
PASS  V-LT-FIRE-system-design  ctx_len= 468 lt=yes
PASS  V-LT-FIRE-debugging      ctx_len= 763 lt=yes
PASS  V-LT-FIRE-creative       ctx_len= 468 lt=yes
PASS  V-LT-COLL-arch+lt      lt_absent=yes
PASS  V-LT-COLL-vague+lt     vague=True lt=True both=yes
PASS  V-LT-COLL-only-vague   vague=True lt=False isolated=yes
PASS  V-LT-COLL-neither      lt=False vague=False none=yes
PASS  V-LT-FIXTURE wrote vault\ceps\lt_empirical_20260527T185446Z.json (5458 B)
PASS  V-LT-CARD-CONTENT len=468 contains_keys=yes

All gates PASS. Empirical fixture awaiting Owner scoring.

## test_ceps_closed_loop.py
PASS  V-CEPS  powershell-git-path            sig=92cdf06f top-3 hit
PASS  V-CEPS  parallel-write-batch           sig=0e7d740a top-3 hit
PASS  V-CEPS  shell-heredoc-append           sig=f7d48857 top-1 hit
PASS  V-CEPS  hook-fanout                    sig=3655427a top-3 hit
PASS  V-CEPS  parallel-explore               sig=365d9acc top-3 hit
PASS  V-CEPS  windows-os-open                sig=5614ca2e top-3 hit
PASS  V-CEPS  bypass-permissions             sig=de3ef5b7 top-3 hit
PASS  V-CEPS  jit-loader-cache               sig=4c2c7ae5 top-3 hit
PASS  V-CEPS  verify-spp-stub                sig=6bbefb10 top-3 hit
PASS  V-CEPS  auto-testing-gate-ci           sig=d894548a top-3 hit

CEPS_PASS=10/10  threshold=>=7/10

## test_ceps_full_cycle.py
PASS  V-FULL-1 isolate-paths  tmp=~\AppData\Local\Temp\ceps-full-cycle-g7_u_twy
PASS  V-FULL-2 record_error  id=ceps_182b990097ec38a3 sig=182b990097ec38a3
PASS  V-FULL-3 events.jsonl-append  bytes=657
PASS  V-FULL-4 distribute-to-2-mds  lessons=510b ukdl=234b
PASS  V-FULL-5 propagate  top_k=1 hit=yes
wrote ~\AppData\Local\Temp\ceps-full-cycle-g7_u_twy\tests\ceps_generated\test_182b990097ec.py

written=1  skipped(existing)=0  total_eligible=1
PASS  V-FULL-6 stub-generation  path=tests\ceps_generated\test_182b990097ec.py
PASS  V-FULL-7 pytest-skip-honored  rc=0
PASS  V-FULL-8 baseline-29-PASS  rc=0

CYCLE_PASS=true  (record -> events -> distribute -> propagate -> stub -> pytest-skip-honored -> baseline-intact)

## test_ceps_edge_cases.py
[isolate] tmp=~\AppData\Local\Temp\ceps-edge-sl3nrcbj
PASS  V-NIT1-MAXCHARS  len=300 (cap=300, sub=400)
PASS  V-NIT3-IDEMPOTENT  run1=3 run2=0 delta_jsonl=3
PASS  V-EDGE-LONG-ROOT  600chars=ok 601chars=rejected
PASS  V-EDGE-INVALID-CAT  ret=None
PASS  V-EDGE-FTS-PUNCT  hits=0 (no crash)
PASS  V-EDGE-LONG-PROMPT  prompt_words=760 card=fired

EDGE_PASS=6/6  threshold=6/6

## pytest tests/
[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                              [100%][0m
[32m[32m[1m43 passed[0m[32m in 0.86s[0m[0m

﻿## verify_spp.py
========================================================================
verify_spp � S++ end-to-end umbrella
  PP root : ~\.claude\skills\claude-power-pack
  rows    : 12
  budget  : 60s per row default
========================================================================
  [...] mirror-parity ...
  [FAIL] mirror-parity          rc=5     4.45s  VERIFY_GLOBAL_MIRRORS FAIL: drift:apex-completion-standard.md
  [...] drift-report ...
  [FAIL] drift-report           rc=1     0.30s    loose-ahead    1
  [...] paths+secrets ...
  [OK  ] paths+secrets          rc=0     7.70s  secret (allow)    : 118 in 47 file(s) — ALLOWLISTED (VPS-ops/meta)
  [...] rtk-fusion ...
  [OK  ] rtk-fusion             rc=0     2.17s  PASS: >= 77% contract floor (deterministic pinned-SHA benchmark; content pres...
  [...] intent-lock ...
  [OK  ] intent-lock            rc=0     0.16s  7/7 passed
  [...] l3-engine ...
  [OK  ] l3-engine              rc=0   114.78s  12/12 checks passed
  [...] programmatic-budget ...
  [OK  ] programmatic-budget    rc=0     1.89s  (no output)
  [...] tis-probe ...
  [OK  ] tis-probe              rc=0     0.39s  TIS_PROBE = 4/4
  [...] monitoring-axis ...
  [OK  ] monitoring-axis        rc=0     0.12s  MONITORING_AXIS: 6/6 sub-checks PASS
  [...] tco-gate ...
  [OK  ] tco-gate               rc=0     0.36s  TCO_PROBE = 5/5
  [...] uqf-active ...
  [OK  ] uqf-active             rc=0     0.70s  UQF_PROBE = 5/5
  [...] rules-taxonomy ...
  [OK  ] rules-taxonomy         rc=0     0.08s  RULES_PROBE = 5/5
========================================================================
  total elapsed: 133.12s
  STRICT FAIL: 2 row(s) � ['mirror-parity', 'drift-report']
========================================================================

## uqf_audit.py --scan-all
MODULE                         SCORE  STATUS  TOP ISSUE                 
-----------------------------  -----  ------  --------------------------
tools/ceps.py                  20.0%  FAIL    failed: error_never_silent
tools/tis.py                   20.0%  FAIL    failed: error_never_silent
tools/tco_compact_gate.py      40.0%  WARN    failed: error_never_silent
modules/monitoring/monitor.py  80.0%  OK      detect_magic_numbers x5   
tools/jit_skill_loader.py      20.0%  FAIL    failed: error_never_silent

