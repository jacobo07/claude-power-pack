# U3 receipt: W4 pricing source (LOW-2) + credential filter digit-prefix residual (U1 LOW-1)

## Changed
- tools/w4_benchmark.py: removed hardcoded PRICING; `resolve_pricing()` calls `pricing_source.current_pricing_path`; report text prints the resolved path (`render_md(..., pricing_path)`); `main()` returns 2 with a stderr message if no pricing file resolves (never prices at 0).
- tools/test_w4_benchmark.py: V-7 (report uses resolved path, not literal), V-8 (default resolves via pricing_source).
- CREDENTIAL lookahead, byte-identical in all three copies (index.cjs, genesis-task-context/lib, genesis-batch-drafts/lib):
  `(?!\s*["']?(?:\$?\{|\d+(?:\/\d+)?(?:\s*[,}]?\s*(?:\r?\n|$)|[,\s]\s*["']?\w+["']?\s*[:=])))`
  Admits only a wholly-numeric value (digits, optional /digits) ending at end of line, or followed by the next `key:`/`key=`.
- tools/test_credential_filter_fp.py: FIX updated; new fixtures (own file each, runtime-built): `password=42,hunter2` BLOCKED, `token=7/Qx...` BLOCKED; numeric controls `"budget": 100,`, `FLOOR_PASS=0/1`, `"authorization_boundary": 100` ADMITTED; 3 original controls stay ADMITTED.
- governance/KNOWN_FALSE_POSITIVES.md: U1 entry fix + residual line updated (no second entry).

## Red before (new tests, old regex in builder)
```
FAIL V-CFP-FAKE-STILL-BLOCKED digit-prefix-comma
FAIL V-CFP-FAKE-STILL-BLOCKED digit-prefix-slash
CFP_PASS=8/14
```
(The old regex admitted both; COPY-SYNC/auth-num/MUTANT also red against the new FIX.)

## Green after
```
CFP_PASS=14/14           (tools/test_credential_filter_fp.py, exit 0)
W4_PASS=8/8              (tools/test_w4_benchmark.py, exit 0)
tools/test_floor_regression_gate.py exit 0
node --test test/index.test.cjs: genesis-source-packets, genesis-task-context, genesis-batch-drafts all exit 0
```
Not observed: the no-pricing-file exit-2 path was not exercised by a test (code path only).

COMMITS: 08ab33ab
