# Architecture Spec -- `tools/test_tab_order.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> test_tab_order.py -- hermetic V-gates for tab-order capture + pane_map overlay.

**Files:** 1  ·  **LOC:** 148  ·  **Public symbols:** 4

### Public interface
- `enc(cwd)` (function, `tools/test_tab_order.py`)
- `iso(dt)` (function, `tools/test_tab_order.py`)
- `write_transcript(path, cwd, topic, ts_iso)` (function, `tools/test_tab_order.py`)
- `run_build(state_dir, proj_base)` (function, `tools/test_tab_order.py`)

### Dependencies
`json`, `os`, `re`, `shutil`, `subprocess`, `sys`, `tempfile`, `datetime`

### Module type
- single-file module
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Design decisions: _(Owner-defined; fill in during planning.)_
- Tradeoffs: _(Owner-defined; fill in during planning.)_
- What this module does NOT do: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
