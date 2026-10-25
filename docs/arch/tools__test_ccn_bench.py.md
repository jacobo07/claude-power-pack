# Architecture Spec -- `tools/test_ccn_bench.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> V-CCN-BENCH gates for tools/ccn_bench.py: pricing, message-id dedupe, grading, CAF verdicts.

**Files:** 1  ·  **LOC:** 78  ·  **Public symbols:** 4

### Public interface
- `check(name, cond, ev)` (function, `tools/test_ccn_bench.py`)
- `rec(mid, **u)` (function, `tools/test_ccn_bench.py`)
- `write(recs)` (function, `tools/test_ccn_bench.py`)
- `rows(seq, p4, reps=2)` (function, `tools/test_ccn_bench.py`)

### Dependencies
`json`, `os`, `sys`, `tempfile`, `ccn_bench`

### Module type
- single-file module
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Design decisions: _(Owner-defined; fill in during planning.)_
- Tradeoffs: _(Owner-defined; fill in during planning.)_
- What this module does NOT do: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
