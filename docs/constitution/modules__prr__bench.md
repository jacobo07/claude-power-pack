# Constitution -- `modules/prr/bench`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

The following public surface is the module's behavioural contract. Removing or breaking any of it is a breaking change.

- `proc_mem(pid: int)`
- `tree(pid: int)`
- `sample(root: int)`
- `fit(points: list)`
- `last_receipt(path: str, sid: str | None, since: float, wait_s: float=5.0)`
- `write_policy_hooks(config_dir: str, hook_cmd: str)`
- `default_hook_cmd(repo: str, exe: str)`
- `Session`
- `main(argv=None)`
- `plan_reply(body: dict)`
- `Handler(BaseHTTPRequestHandler)`
- `main(argv=None)`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Invariants that must never change: _(Owner-defined; fill in during planning.)_
- Hard rules specific to this module: _(Owner-defined; fill in during planning.)_
- What breaks downstream if violated: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
