# Constitution -- `tools/ccr_compat_gate.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

The following public surface is the module's behavioural contract. Removing or breaking any of it is a breaking change.

- `host_version(claude: str | None=None)`
- `parse_compat(text: str | None)`
- `read_text(p: pathlib.Path)`
- `check(version: str | None, policy_text: str | None, release: str | None)`
- `active_release(ccr: pathlib.Path=CCR)`
- `plan(version: str | None, verdict_dir: pathlib.Path=VERDICTS)`
- `source_check(tree: pathlib.Path, ccr: pathlib.Path=CCR)`
- `reprobe(confirm: bool, version: str | None, release: str | None)`
- `main(argv: list[str])`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Invariants that must never change: _(Owner-defined; fill in during planning.)_
- Hard rules specific to this module: _(Owner-defined; fill in during planning.)_
- What breaks downstream if violated: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
