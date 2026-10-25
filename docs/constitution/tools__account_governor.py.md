# Constitution -- `tools/account_governor.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

The following public surface is the module's behavioural contract. Removing or breaking any of it is a breaking change.

- `load_json(path)`
- `parse_when(v)`
- `assistant_events(roots, since)`
- `infer_reset(roots, now, lookback_s=WEEK_S + 86400)`
- `current_window(reset, now)`
- `measure_spend(roots, reset_at, now)`
- `config(state_dir)`
- `host_files(state_dir)`
- `status(state_dir, now=None, roots=None)`
- `read_override(state_dir, now)`
- `decide(st, override, action)`
- `append_ledger(state_dir, row)`
- `check(state_dir, action, now=None, roots=None)`
- `cmd_measure(a)`
- `main(argv=None)`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Invariants that must never change: _(Owner-defined; fill in during planning.)_
- Hard rules specific to this module: _(Owner-defined; fill in during planning.)_
- What breaks downstream if violated: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
