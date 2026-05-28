# Cold-boot evidence -- OSA v1.0 + TCO context-fix

- ISO: 2026-05-28T09:06:42.586551+00:00
- Branch: main (post-OSA build, post-TCO fix)
- Host: Windows (claude-power-pack repo)
- Sealed: 2026-05-28 (BL-OSA-001)

## Suite results

### PASS -- `test_osa.py` (rc=0)
```
PASS  V-OSA-NEVER-INJECT               jsonl rows=1
PASS  V-OSA-NEVER-RECUR                recurrence=2 jsonl rows=1
PASS  V-OSA-GPU-SKIP                   status=SKIPPED passed=None
PASS  V-OSA-DISPATCHER-SLEEP           reason=sleepy
PASS  V-OSA-DISPATCHER-T3              distinct=3 threshold=3
PASS  V-OSA-DISPATCHER-PROJ            resolved='claude-power-pack'
PASS  V-OSA-NONBLOCKING                returned in 0ms
PASS  V-TCO-CONTEXT-SINGLE             pct=5% max_single=10000
PASS  V-TCO-CONTEXT-REAL               pct=85% max_single=170000
PASS  V-BASELINE-INTACT                rc=0 last='[32m[32m[1m43 passed[0m[32m in 0.88s[0m[0m'

OSA_PASS=15/15  threshold=15/15
```

### PASS -- `test_tco.py` (rc=0)
```
PASS  V-COMPACT-OK                   pct=2% rec=OK
PASS  V-COMPACT-WARN                 pct=70% rec=WARN
PASS  V-COMPACT-HARD                 governor=2 warns
PASS  V-COMPACT-CONTEXT-SINGLE       pct=5% max_single=10000
PASS  V-COMPACT-CONTEXT-REAL         pct=85% max_single=170000
PASS  V-ROUTE-SONNET                 -> claude-sonnet-4-6
PASS  V-ROUTE-OPUS                   -> claude-opus-4-7
PASS  V-ROUTE-DEFAULT                -> claude-opus-4-7
PASS  V-PROJECTION                   rc=0 fields=ok
PASS  V-BASELINE-INTACT              rc=0 last='[32m[32m[1m43 passed[0m[32m in 0.88s[0m[0m'

TCO_PASS=10/10  threshold=10/10
```

### PASS -- `test_uqf.py` (rc=0)
```
PASS  V-UQF-PROOF-TRIAD              HIGH without triad rejected score=0.0
PASS  V-UQF-ERROR-SILENT             bare-except detected: 2 violations: ["line 3: bare 'except:' (no excepti
PASS  V-UQF-ERROR-TYPED              typed-except OK
PASS  V-UQF-PROMPT-DEFENSE           CLAUDE.md covered=6/6
PASS  V-UQF-ANTI-BARE                detected at line 3
PASS  V-UQF-ANTI-TYPE-HINTS          detected `public_func`
PASS  V-UQF-AUDITOR-SCORE            ceps.py=20.0% (in 0-100)
PASS  V-UQF-CEPS-CONFIDENCE          compute_confidence(2,True)=0.7
PASS  V-UQF-CEPS-PROMOTE             promotion logic correct
PASS  V-BASELINE-INTACT              rc=0 last='[32m[32m[1m43 passed[0m[32m in 0.91s[0m[0m'

UQF_PASS=15/15  threshold=15/15
```

### PASS -- `test_tis_core.py` (rc=0)
```
[isolate] tmp=C:\Users\User\AppData\Local\Temp\tis-core-nrtbyzdc
PASS  V-TIS-APPEND  entries=1
PASS  V-TIS-IDEMPOTENT  delta=2
PASS  V-TIS-SCHEMA  missing=none keys=10
PASS  V-TIS-SESSION  a=be97b93f b=be97b93f
PASS  V-TIS-PERSIST  path=tis-core-nrtbyzdc\token_logs\2026-05-28.jsonl
PASS  V-TIS-NONZERO  in=100 out=50 cr=25 cc=5

TIS_CORE_PASS=6/6  threshold=6/6
```

### PASS -- `test_monitoring.py` (rc=0)
```
  [PASS] V-ALERT-STDOUT: stdout_chars=73; tag_present=True
  [PASS] V-NO-AUTO-ROLLBACK: call sites of rollback() across monitor/observe/alert: 0
  [PASS] V-CONFIG-INHERIT: defaults applied: deb_f=3, deb_s=2, min_dur=30, interval=60
  [PASS] V-ONCE-FLAG: rc=0 table_has_project=True p23_line=True
  [PASS] V-ONCE-MULTIPROJECT: rc=0 all 3 projects in table: True
  [PASS] V-DAEMON-NO-INSTALL: rc=0 cron+TS in stdout=True install_calls=0
  [PASS] V-RETENTION-PURGE-DROP: dropped=1 files=['20260329T090651Z_fixE_UP_TO_DOWN.md']
  [PASS] V-RETENTION-PURGE-KEEP: dropped=0 remaining=1
  [PASS] V-ALERTS-LIST: top-2 newest-first: ['20260526T120000Z', '20260525T120000Z']
  [PASS] V-STATUS-NO-CHECK: rc=0 run_check_calls=0
============================================================
Result: 16/16 PASS
```

### PASS -- `test_lateral_thinking.py` (rc=0)
```
PASS  V-LT-FIRE-product-ux     ctx_len= 468 lt=yes
PASS  V-LT-FIRE-system-design  ctx_len= 468 lt=yes
PASS  V-LT-FIRE-debugging      ctx_len= 763 lt=yes
PASS  V-LT-FIRE-creative       ctx_len= 468 lt=yes
PASS  V-LT-COLL-arch+lt      lt_absent=yes
PASS  V-LT-COLL-vague+lt     vague=True lt=True both=yes
PASS  V-LT-COLL-only-vague   vague=True lt=False isolated=yes
PASS  V-LT-COLL-neither      lt=False vague=False none=yes
PASS  V-LT-FIXTURE wrote vault\ceps\lt_empirical_20260528T090651Z.json (5458 B)
PASS  V-LT-CARD-CONTENT len=468 contains_keys=yes

All gates PASS. Empirical fixture awaiting Owner scoring.
```

### PASS -- `test_ceps_closed_loop.py` (rc=0)
```
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
```

### PASS -- `test_ceps_full_cycle.py` (rc=0)
```
PASS  V-FULL-2 record_error  id=ceps_182b990097ec38a3 sig=182b990097ec38a3
PASS  V-FULL-3 events.jsonl-append  bytes=657
PASS  V-FULL-4 distribute-to-2-mds  lessons=510b ukdl=234b
PASS  V-FULL-5 propagate  top_k=1 hit=yes
wrote C:\Users\User\AppData\Local\Temp\ceps-full-cycle-oap0ccnk\tests\ceps_generated\test_182b990097ec.py

written=1  skipped(existing)=0  total_eligible=1
PASS  V-FULL-6 stub-generation  path=tests\ceps_generated\test_182b990097ec.py
PASS  V-FULL-7 pytest-skip-honored  rc=0
PASS  V-FULL-8 baseline-29-PASS  rc=0

CYCLE_PASS=true  (record -> events -> distribute -> propagate -> stub -> pytest-skip-honored -> baseline-intact)
```

### PASS -- `test_ceps_edge_cases.py` (rc=0)
```
[isolate] tmp=C:\Users\User\AppData\Local\Temp\ceps-edge-cj2h8mxw
PASS  V-NIT1-MAXCHARS  len=300 (cap=300, sub=400)
PASS  V-NIT3-IDEMPOTENT  run1=3 run2=0 delta_jsonl=3
PASS  V-EDGE-LONG-ROOT  600chars=ok 601chars=rejected
PASS  V-EDGE-INVALID-CAT  ret=None
PASS  V-EDGE-FTS-PUNCT  hits=0 (no crash)
PASS  V-EDGE-LONG-PROMPT  prompt_words=760 card=fired

EDGE_PASS=6/6  threshold=6/6
```

### PASS -- `pytest tests/` (rc=0)
```
[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                              [100%][0m
[32m[32m[1m43 passed[0m[32m in 1.12s[0m[0m
```

### PASS -- `tco_compact_gate.py` (rc=0)
```
context-pct (estimate): 5%  [warn>=70%]
session-tokens:         258,106
session-duration:       152870s
recommendation:         OK contexto 5% < 70% -- continuar
  [TCO debug] calls=220  max_single_input=20,846  proxy_used=10,423  pct=5%
governor:
  - session-tokens 258106 > 100000 (consider /compact)
  - session-duration 152870s > 7200s (loop hygiene -- /compact every 2h)
```

### PASS -- `modules.osa.osa_command --status` (rc=0)
```
      "fix": "Replace sum() with max() of last-3 input_tokens, half-global fallback",
      "recognizer": "If pct>=70% but session has only a few high-token calls, suspect the cumulative bug",
      "severity": "HIGH",
      "recurrence": 2,
      "tags": [
        "tco",
        "context",
        "observability"
      ]
    }
  ]
}
```

### PASS -- `modules/osa/dispatcher.py --check` (rc=0)
```
      "threshold": 3
    },
    "T4_SESSION_TIMER": {
      "fired": true,
      "minutes": 2547,
      "threshold": 120
    },
    "T5_MANUAL": {
      "fired": false
    }
  }
}
```

### PASS -- `modules/osa/gpu_eyes.py` (rc=0)
```
{
  "status": "SKIPPED",
  "reason": "GPU_NOT_REACHABLE",
  "visual_qa_passed": null,
  "screenshot": null,
  "project": "unknown",
  "intent": null,
  "iso": "2026-05-28T09:06:58Z",
  "note": "Visual QA NOT executed -- GPU host unreachable. Do not report as PASS. Text-only audit is the fallback path."
}
```

### PASS -- `verify_osa.py` (rc=0)
```
PASS  osa-imports              5 modules imported
PASS  osa-config               max_daily=150
PASS  osa-throttle-check       -> GO
PASS  osa-dispatcher           active=True reason=T4_SESSION_TIMER
PASS  osa-agent-file           valid frontmatter, no triggers:/throttle: keys

OSA_PROBE=5/5
```

### PASS -- `uqf_audit.py --scan-all` (rc=0)
```
MODULE                         SCORE  STATUS  TOP ISSUE                 
-----------------------------  -----  ------  --------------------------
tools/ceps.py                  20.0%  FAIL    failed: error_never_silent
tools/tis.py                   20.0%  FAIL    failed: error_never_silent
tools/tco_compact_gate.py      20.0%  FAIL    failed: error_never_silent
modules/monitoring/monitor.py  80.0%  OK      detect_magic_numbers x5   
tools/jit_skill_loader.py      20.0%  FAIL    failed: error_never_silent
```

## verify_spp.py (umbrella)
- rc=1
```
  [...] l3-engine ...
  [OK  ] l3-engine              rc=0   113.49s  12/12 checks passed
  [...] programmatic-budget ...
  [OK  ] programmatic-budget    rc=0     3.91s  (no output)
  [...] tis-probe ...
  [OK  ] tis-probe              rc=0     0.52s  TIS_PROBE = 4/4
  [...] monitoring-axis ...
  [OK  ] monitoring-axis        rc=0     0.16s  MONITORING_AXIS: 6/6 sub-checks PASS
  [...] tco-gate ...
  [OK  ] tco-gate               rc=0     0.64s  TCO_PROBE = 5/5
  [...] uqf-active ...
  [OK  ] uqf-active             rc=0     1.00s  UQF_PROBE = 5/5
  [...] rules-taxonomy ...
  [OK  ] rules-taxonomy         rc=0     0.20s  RULES_PROBE = 5/5
  [...] osa-active ...
  [OK  ] osa-active             rc=0     0.17s  OSA_PROBE=5/5
========================================================================
  total elapsed: 125.22s
  STRICT FAIL: 2 row(s) — ['mirror-parity', 'drift-report']
========================================================================
```

**Total suites: 16 PASS / 0 FAIL** (verify_spp drift on apex-completion-standard.md is pre-existing Pane-N governance drift, resolved in M14 below).