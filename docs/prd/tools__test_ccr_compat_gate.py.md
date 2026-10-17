# PRD (Tier 1 -- Standard Task) -- `tools/test_ccr_compat_gate.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> V-COMPAT-* gates for tools/ccr_compat_gate.py (spec vault/specs/ccr-compat-gate.md). Run from the repo root:

**Files:** 1  ·  **LOC:** 135  ·  **Public symbols:** 6

### Public interface
- `ok(name: str, ev: str)` (function, `tools/test_ccr_compat_gate.py`)
- `fail(name: str, why: str)` (function, `tools/test_ccr_compat_gate.py`)
- `gate(name: str, cond: bool, ev: str)` (function, `tools/test_ccr_compat_gate.py`)
- `mutant(old: str, new: str)` (function, `tools/test_ccr_compat_gate.py`)
- `verdict_file(d: pathlib.Path, version: str, host: str, verdicts: dict, flag: bool=True, limits=None)` (function, `tools/test_ccr_compat_gate.py`)
- `main()` (function, `tools/test_ccr_compat_gate.py`)

### Dependencies
`json`, `pathlib`, `shutil`, `subprocess`, `sys`, `tempfile`, `ccr_compat_gate`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Brief: _(Owner-defined; fill in during planning.)_
- Acceptance criteria: _(Owner-defined; fill in during planning.)_
- Impact map: _(Owner-defined; fill in during planning.)_
- Test plan: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
