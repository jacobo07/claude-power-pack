# Architecture Spec -- `tools/ccn_bench.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> CCN Phase 2: matched concurrency benchmark.

**Files:** 1  ·  **LOC:** 245  ·  **Public symbols:** 11

### Public interface
- `price(usage)` (function, `tools/ccn_bench.py`)
- `transcript_cost(path)` (function, `tools/ccn_bench.py`)
- `grade(question, answer)` (function, `tools/ccn_bench.py`)
- `find_transcript(session_id, cwd)` (function, `tools/ccn_bench.py`)
- `run_one(q, mode, repeat, nonce, wt)` (function, `tools/ccn_bench.py`)
- `load_runs(path)` (function, `tools/ccn_bench.py`)
- `cmd_run(a)` (function, `tools/ccn_bench.py`)
- `mean(xs)` (function, `tools/ccn_bench.py`)
- `analyze(rows)` (function, `tools/ccn_bench.py`)
- `cmd_report(a)` (function, `tools/ccn_bench.py`)
- `main(argv=None)` (function, `tools/ccn_bench.py`)

### Dependencies
`argparse`, `concurrent`, `json`, `os`, `re`, `subprocess`, `sys`, `time`, `uuid`, `ccn_census`

### Module type
- single-file module
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Design decisions: _(Owner-defined; fill in during planning.)_
- Tradeoffs: _(Owner-defined; fill in during planning.)_
- What this module does NOT do: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
