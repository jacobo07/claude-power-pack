---
phase: 05-bi-15-35-on-the-cli-path
status: passed
verified: 2026-11-21
---
# Phase 05 Verification

Requirement BCAP2B-05.

| # | Criterion | Evidence | Status |
|---|---|---|---|
| 1 | Every built BI validator with a config-declarable input is reachable from `ccf package` | `python3 tools/test_bcap2_cli15.py` exit 0: 12 checks x (pass, fail, absent) enforce poles, report-mode FAIL not enforced, path traversal refused, 2 mutants turn poles red | PASS |
| 2 | AC1: existing CCF suites unchanged | test_ccf 16 passed, test_asc_ccf PASS, test_bcap2_brand PASS, test_bcap2_activation PASS, done_gate PASS | PASS |
| 3 | Not wired, stated: BI-16 CCF adapter + cross-platform (LAPTOP_STEPS B2), BI-34 `applicable` (routes agent prompts, not a project config), BI-21/27/30 (principles/read only), BI-32/33 (BI-33 forbidden by CLAUDE.md) | STATE.md Phase 5 | PARTIAL by design |
