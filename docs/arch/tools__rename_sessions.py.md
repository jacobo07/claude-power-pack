# Architecture Spec -- `tools/rename_sessions.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> rename_sessions.py -- safe retroactive session rename via inline custom-title append.

**Files:** 1  ·  **LOC:** 639  ·  **Public symbols:** 18

### Public interface
- `clean_prompt(text: str)` (function, `tools/rename_sessions.py`)
- `sub_name(first_user: str, cmd_name: str, branch: str)` (function, `tools/rename_sessions.py`)
- `scan_session(path: Path)` (function, `tools/rename_sessions.py`)
- `effective_base(custom_raw: str | None)` (function, `tools/rename_sessions.py`)
- `is_reclaimable_title(base: str, repo: str)` (function, `tools/rename_sessions.py`)
- `is_canonical_location(proj_dir: Path, cwd: str)` (function, `tools/rename_sessions.py`)
- `repo_of(proj_dir: Path, cwd: str)` (function, `tools/rename_sessions.py`)
- `derive_name(s: dict)` (function, `tools/rename_sessions.py`)
- `make_title(source: str, repo: str, repo_prefix: bool)` (function, `tools/rename_sessions.py`)
- `build_record(uuid: str, title: str)` (function, `tools/rename_sessions.py`)
- `plan_project(proj_dir: Path, repo_prefix: bool, skip_sids: set[str])` (function, `tools/rename_sessions.py`)
- `iter_project_dirs()` (function, `tools/rename_sessions.py`)
- `repo_sort_key(repo: str)` (function, `tools/rename_sessions.py`)
- `apply_one(path: Path, uuid: str, title: str)` (function, `tools/rename_sessions.py`)
- `summarize(rows: list[dict])` (function, `tools/rename_sessions.py`)
- `source_breakdown(rows: list[dict])` (function, `tools/rename_sessions.py`)
- `print_group(label: str, proj_name: str, rows: list[dict], verbose: bool, sample: int)` (function, `tools/rename_sessions.py`)
- `main()` (function, `tools/rename_sessions.py`)

### Dependencies
`__future__`, `argparse`, `hashlib`, `json`, `os`, `re`, `sys`, `pathlib`

### Module type
- single-file module
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Design decisions: _(Owner-defined; fill in during planning.)_
- Tradeoffs: _(Owner-defined; fill in during planning.)_
- What this module does NOT do: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
