---
plan: 01-01
status: complete
---

# 01-01 SUMMARY

- Added tools/ccr_rent_ledger.py (schema in code, classes from ccr_anatomy.classify) and tools/test_ccr_rent_ledger.py.
- Verify: python -I tools/test_ccr_rent_ledger.py -> RENT_PASS=10/10, exit 0 (poor-fit, negative-residual and G1 both poles driven).
- Calibration is a pooled OLS (tokens/byte fitted, intercept = unsplit tool schemas + framing); it is OBSERVED-grade, never PROVEN.
