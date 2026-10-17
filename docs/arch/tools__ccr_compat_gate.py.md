# Architecture Spec -- `tools/ccr_compat_gate.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> CCR compat gate (spec vault/specs/ccr-compat-gate.md): detect a host version CCR was not measured on, re-measure it,

**Files:** 1  ·  **LOC:** 158  ·  **Public symbols:** 9

### Public interface
- `host_version(claude: str | None=None)` (function, `tools/ccr_compat_gate.py`)
- `parse_compat(text: str | None)` (function, `tools/ccr_compat_gate.py`)
- `read_text(p: pathlib.Path)` (function, `tools/ccr_compat_gate.py`)
- `check(version: str | None, policy_text: str | None, release: str | None)` (function, `tools/ccr_compat_gate.py`)
- `active_release(ccr: pathlib.Path=CCR)` (function, `tools/ccr_compat_gate.py`)
- `plan(version: str | None, verdict_dir: pathlib.Path=VERDICTS)` (function, `tools/ccr_compat_gate.py`)
- `source_check(tree: pathlib.Path, ccr: pathlib.Path=CCR)` (function, `tools/ccr_compat_gate.py`)
- `reprobe(confirm: bool, version: str | None, release: str | None)` (function, `tools/ccr_compat_gate.py`)
- `main(argv: list[str])` (function, `tools/ccr_compat_gate.py`)

### Dependencies
`json`, `pathlib`, `re`, `shutil`, `subprocess`, `sys`

### Module type
- single-file module
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Design decisions: _(Owner-defined; fill in during planning.)_
- Tradeoffs: _(Owner-defined; fill in during planning.)_
- What this module does NOT do: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
