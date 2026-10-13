# Constitution -- `modules/prr`

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
- `Proc`
- `role_of(p: Proc, parent: Proc | None)`
- `classify(procs: list, *, now: float, available_mb: float | None=None, total_mb: float | None=None, plane: str=PLANE_LAPTOP)`
- `sample()`
- `run(plane: str | None=None)`
- `summary(rep: dict)`
- `main(argv=None)`
- `profile_run(rows: list, *, workload: str, plane: str, source: dict)`
- `load(ledger: Path)`
- `append(ledger: Path, profile: dict)`
- `recommend_epoch(profiles: list, *, workload: str, plane: str, anon_budget_mb: float)`
- `main(argv=None)`
- `Decision`
- `last_boundary_ts(path: Path)`
- `mark_clear(pid: int, create_time: float, sid: str | None)`
- `cleared_in_process(pid: int, create_time: float)`
- `decide(*, proc_start: float, boundary_ts: float | None, cleared_ts: float | None, has_wrapper: bool, background_tasks: int, session_crons: int, is_subagent: bool=False)`
- `mem_fields(mem)`
- `run_hook(payload: dict, mode: str)`
- `main()`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Invariants that must never change: _(Owner-defined; fill in during planning.)_
- Hard rules specific to this module: _(Owner-defined; fill in during planning.)_
- What breaks downstream if violated: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
