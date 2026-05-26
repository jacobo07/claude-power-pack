# Cold-boot S+++ evidence -- 20260526T110207Z

## LT 11/11
```
PASS  V-LT-FIRE-algorithmic    ctx_len= 468 lt=yes
PASS  V-LT-FIRE-product-ux     ctx_len= 468 lt=yes
PASS  V-LT-FIRE-system-design  ctx_len= 468 lt=yes
PASS  V-LT-FIRE-debugging      ctx_len= 628 lt=yes
PASS  V-LT-FIRE-creative       ctx_len= 468 lt=yes
PASS  V-LT-COLL-arch+lt      lt_absent=yes
PASS  V-LT-COLL-vague+lt     vague=True lt=True both=yes
PASS  V-LT-COLL-only-vague   vague=True lt=False isolated=yes
PASS  V-LT-COLL-neither      lt=False vague=False none=yes
PASS  V-LT-FIXTURE wrote vault\ceps\lt_empirical_20260526T090208Z.json (5322 B)
PASS  V-LT-CARD-CONTENT len=468 contains_keys=yes

All gates PASS. Empirical fixture awaiting Owner scoring.
```

## CEPS closed-loop 10/10
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

## CEPS full-cycle 8/8
```
PASS  V-FULL-2 record_error  id=ceps_182b990097ec38a3 sig=182b990097ec38a3
PASS  V-FULL-3 events.jsonl-append  bytes=581
PASS  V-FULL-4 distribute-to-2-mds  lessons=510b ukdl=234b
PASS  V-FULL-5 propagate  top_k=1 hit=yes
wrote C:\Users\User\AppData\Local\Temp\ceps-full-cycle-rdv21kw_\tests\ceps_generated\test_182b990097ec.py

written=1  skipped(existing)=0  total_eligible=1
PASS  V-FULL-6 stub-generation  path=tests\ceps_generated\test_182b990097ec.py
PASS  V-FULL-7 pytest-skip-honored  rc=0
PASS  V-FULL-8 baseline-29-PASS  rc=0

CYCLE_PASS=true  (record -> events -> distribute -> propagate -> stub -> pytest-skip-honored -> baseline-intact)
```

## CEPS edge-cases (M4 new)
```
[isolate] tmp=C:\Users\User\AppData\Local\Temp\ceps-edge-b3rmgg5c
PASS  V-NIT1-MAXCHARS  len=300 (cap=300, sub=400)
PASS  V-NIT3-IDEMPOTENT  run1=3 run2=0 delta_jsonl=3
PASS  V-EDGE-LONG-ROOT  600chars=ok 601chars=rejected
PASS  V-EDGE-INVALID-CAT  ret=None
PASS  V-EDGE-FTS-PUNCT  hits=0 (no crash)
PASS  V-EDGE-LONG-PROMPT  prompt_words=760 card=fired

EDGE_PASS=6/6  threshold=6/6
```

## pytest baseline
```
[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                                            [100%][0m
[32m[32m[1m29 passed[0m[32m in 0.53s[0m[0m
```

## verify_spp.py (post-fix; mirror-parity still pending commit)
```
  [...] l3-engine ...
  [OK  ] l3-engine              rc=0   141.97s  12/12 checks passed
  [...] programmatic-budget ...
  [OK  ] programmatic-budget    rc=0     2.01s  (no output)
========================================================================
  total elapsed: 148.08s
  STRICT FAIL: 1 row(s) � ['mirror-parity']
========================================================================
```
