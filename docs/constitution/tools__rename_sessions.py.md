# Constitution -- `tools/rename_sessions.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

The following public surface is the module's behavioural contract. Removing or breaking any of it is a breaking change.

- `clean_prompt(text: str)`
- `sub_name(first_user: str, cmd_name: str, branch: str)`
- `scan_session(path: Path)`
- `effective_base(custom_raw: str | None)`
- `is_reclaimable_title(base: str, repo: str)`
- `is_canonical_location(proj_dir: Path, cwd: str)`
- `repo_of(proj_dir: Path, cwd: str)`
- `derive_name(s: dict)`
- `make_title(source: str, repo: str, repo_prefix: bool)`
- `build_record(uuid: str, title: str)`
- `plan_project(proj_dir: Path, repo_prefix: bool, skip_sids: set[str])`
- `iter_project_dirs()`
- `repo_sort_key(repo: str)`
- `apply_one(path: Path, uuid: str, title: str)`
- `summarize(rows: list[dict])`
- `source_breakdown(rows: list[dict])`
- `print_group(label: str, proj_name: str, rows: list[dict], verbose: bool, sample: int)`
- `main()`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Invariants that must never change: _(Owner-defined; fill in during planning.)_
- Hard rules specific to this module: _(Owner-defined; fill in during planning.)_
- What breaks downstream if violated: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
