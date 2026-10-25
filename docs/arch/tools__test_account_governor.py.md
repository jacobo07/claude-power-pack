# Architecture Spec -- `tools/test_account_governor.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> V-CCN-GOV gates for tools/account_governor.py.

**Files:** 1  ·  **LOC:** 162  ·  **Public symbols:** 5

### Public interface
- `gate(name, cond, ev)` (function, `tools/test_account_governor.py`)
- `jdump(path, obj)` (function, `tools/test_account_governor.py`)
- `env(tmp, spend, cfg_extra=None, hosts=('gex44',), calib=CALIB, reset=NOW - 3 * 86400)` (function, `tools/test_account_governor.py`)
- `run(sd, action='arm')` (function, `tools/test_account_governor.py`)
- `mutant_module()` (function, `tools/test_account_governor.py`)

### Dependencies
`json`, `os`, `subprocess`, `sys`, `tempfile`, `time`, `types`, `account_governor`

### Module type
- single-file module
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Design decisions: _(Owner-defined; fill in during planning.)_
- Tradeoffs: _(Owner-defined; fill in during planning.)_
- What this module does NOT do: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
