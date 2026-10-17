# Evidence UZ2
Host: claude 2.1.302 | Date: 2026-10-17 | Plan: run prebuilt probe, widen COMPAT only on PASS

## Step 1-2 source check
policy.ts 531 lines, register.ts 410 lines, policy.ts line 8 `export const COMPAT = ['2.1.296']`. OK. RAM free 11.26 GB (>=4).

## Probe (host 2.1.302; guard 1,500,000; spent 829,597)
Selftest 13/13 UZ_SELFTEST=PASS.
| case | verdict | why |
|---|---|---|
| S1a | PASS | baseline subagent processed=52605 |
| S1b | PASS | subagent processed 20624 vs baseline 52605 (ratio 0.39, max 0.6) |
| S2 | PASS | instructions replaced by the marker |
| S3 | PASS | result rewritten through next(e), command ran once |
| S4 | PASS | 331 tools deferred |
| S5 | PASS | memory section dropped |
all_required_pass=true. No named limits.

## Decision
Widened policy.ts line 8 to `['2.1.296', '2.1.302']` (+11 bytes, only change).

## Gates
- claude plugin test: 38 pass / 0 fail
- test_ccr_release.py: CCR_PASS=20/20
- test_ccr_main_shadow.py: CCR_PASS=11/11
- ccr_estate_gate.py: verdict PASS (sum10x 3697 <= 8000, slope -0.000615)

## Release
Released 0.1.0-f79e3c46. Diff vs 0.1.0-54f1824b: 7 files each; only RELEASE.json (new id) and hooks/policy.ts differ; policy.ts 531 lines both, only line 8 (COMPAT). register.ts identical (hash). No rollback.
