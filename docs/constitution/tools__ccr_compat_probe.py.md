# Constitution -- `tools/ccr_compat_probe.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

The following public surface is the module's behavioural contract. Removing or breaking any of it is a breaking change.

- `seam_prompt(counter: pathlib.Path)`
- `processed(usage)`
- `sub_processed(rows)`
- `judge(case_id: str, rows: list, answer: str, base_sub: int | None, counter_lines: int | None)`
- `selftest()`
- `run_case(claude: str, case: dict, tmp: pathlib.Path)`
- `main()`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Invariants that must never change: _(Owner-defined; fill in during planning.)_
- Hard rules specific to this module: _(Owner-defined; fill in during planning.)_
- What breaks downstream if violated: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
