# PRD (Tier 1 -- Standard Task) -- `tools/ccr_compat_probe.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> CCR compat probe driver: runs the ccr-uz-probe plugin headless on the host under test and judges each CCR surface.

**Files:** 1  ·  **LOC:** 221  ·  **Public symbols:** 7

### Public interface
- `seam_prompt(counter: pathlib.Path)` (function, `tools/ccr_compat_probe.py`)
- `processed(usage)` (function, `tools/ccr_compat_probe.py`)
- `sub_processed(rows)` (function, `tools/ccr_compat_probe.py`)
- `judge(case_id: str, rows: list, answer: str, base_sub: int | None, counter_lines: int | None)` (function, `tools/ccr_compat_probe.py`)
- `selftest()` (function, `tools/ccr_compat_probe.py`)
- `run_case(claude: str, case: dict, tmp: pathlib.Path)` (function, `tools/ccr_compat_probe.py`)
- `main()` (function, `tools/ccr_compat_probe.py`)

### Dependencies
`json`, `os`, `pathlib`, `shutil`, `subprocess`, `sys`, `tempfile`, `time`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Brief: _(Owner-defined; fill in during planning.)_
- Acceptance criteria: _(Owner-defined; fill in during planning.)_
- Impact map: _(Owner-defined; fill in during planning.)_
- Test plan: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
