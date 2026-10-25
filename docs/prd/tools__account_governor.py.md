# PRD (Tier 1 -- Standard Task) -- `tools/account_governor.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> CCN Phase 4: account-level weekly governor shared by laptop and GEX44.

**Files:** 1  ·  **LOC:** 245  ·  **Public symbols:** 15

### Public interface
- `load_json(path)` (function, `tools/account_governor.py`)
- `parse_when(v)` (function, `tools/account_governor.py`)
- `assistant_events(roots, since)` (function, `tools/account_governor.py`)
- `infer_reset(roots, now, lookback_s=WEEK_S + 86400)` (function, `tools/account_governor.py`)
- `current_window(reset, now)` (function, `tools/account_governor.py`)
- `measure_spend(roots, reset_at, now)` (function, `tools/account_governor.py`)
- `config(state_dir)` (function, `tools/account_governor.py`)
- `host_files(state_dir)` (function, `tools/account_governor.py`)
- `status(state_dir, now=None, roots=None)` (function, `tools/account_governor.py`)
- `read_override(state_dir, now)` (function, `tools/account_governor.py`)
- `decide(st, override, action)` (function, `tools/account_governor.py`)
- `append_ledger(state_dir, row)` (function, `tools/account_governor.py`)
- `check(state_dir, action, now=None, roots=None)` (function, `tools/account_governor.py`)
- `cmd_measure(a)` (function, `tools/account_governor.py`)
- `main(argv=None)` (function, `tools/account_governor.py`)

### Dependencies
`argparse`, `json`, `os`, `socket`, `sys`, `time`, `ccn_bench`, `ccn_census`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Brief: _(Owner-defined; fill in during planning.)_
- Acceptance criteria: _(Owner-defined; fill in during planning.)_
- Impact map: _(Owner-defined; fill in during planning.)_
- Test plan: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
