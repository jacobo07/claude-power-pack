# PRD (Tier 1 -- Standard Task) -- `tools/test_ccn_census.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> V-CCN-CENSUS-* gates for tools/ccn_census.py. Every detector is driven from both poles

**Files:** 1  ·  **LOC:** 339  ·  **Public symbols:** 8

### Public interface
- `gate(name, cond, evidence)` (function, `tools/test_ccn_census.py`)
- `iso(t)` (function, `tools/test_ccn_census.py`)
- `write_session(root, project, sid, lines, mtime=None)` (function, `tools/test_ccn_census.py`)
- `tool_pair(t, tid, name, inp, result='x' * 100)` (function, `tools/test_ccn_census.py`)
- `first_call(t, write, read)` (function, `tools/test_ccn_census.py`)
- `mutant(replacements)` (function, `tools/test_ccn_census.py`)
- `build_dup_estate(root, now=NOW)` (function, `tools/test_ccn_census.py`)
- `main()` (function, `tools/test_ccn_census.py`)

### Dependencies
`contextlib`, `io`, `json`, `os`, `re`, `subprocess`, `sys`, `tempfile`, `time`, `types`, `ccn_census`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Brief: _(Owner-defined; fill in during planning.)_
- Acceptance criteria: _(Owner-defined; fill in during planning.)_
- Impact map: _(Owner-defined; fill in during planning.)_
- Test plan: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
