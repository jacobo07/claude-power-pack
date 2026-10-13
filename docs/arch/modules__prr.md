# Architecture Spec -- `modules/prr`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> prr -- physical runtime working set (goal prr). A package marker: the liveness gate only walks packages.

**Files:** 7  ·  **LOC:** 1028  ·  **Public symbols:** 32

### Public interface
- `proc_mem(pid: int)` (function, `modules/prr/bench/longrun.py`)
- `tree(pid: int)` (function, `modules/prr/bench/longrun.py`)
- `sample(root: int)` (function, `modules/prr/bench/longrun.py`)
- `fit(points: list)` (function, `modules/prr/bench/longrun.py`)
- `last_receipt(path: str, sid: str | None, since: float, wait_s: float=5.0)` (function, `modules/prr/bench/longrun.py`)
- `write_policy_hooks(config_dir: str, hook_cmd: str)` (function, `modules/prr/bench/longrun.py`)
- `default_hook_cmd(repo: str, exe: str)` (function, `modules/prr/bench/longrun.py`)
- `Session` (class, `modules/prr/bench/longrun.py`)
- `main(argv=None)` (function, `modules/prr/bench/longrun.py`)
- `plan_reply(body: dict)` (function, `modules/prr/bench/stub_api.py`)
- `Handler(BaseHTTPRequestHandler)` (class, `modules/prr/bench/stub_api.py`)
- `main(argv=None)` (function, `modules/prr/bench/stub_api.py`)
- `Proc` (class, `modules/prr/census.py`)
- `role_of(p: Proc, parent: Proc | None)` (function, `modules/prr/census.py`)
- `classify(procs: list, *, now: float, available_mb: float | None=None, total_mb: float | None=None, plane: str=PLANE_LAPTOP)` (function, `modules/prr/census.py`)
- `sample()` (function, `modules/prr/census.py`)
- `run(plane: str | None=None)` (function, `modules/prr/census.py`)
- `summary(rep: dict)` (function, `modules/prr/census.py`)
- `main(argv=None)` (function, `modules/prr/census.py`)
- `profile_run(rows: list, *, workload: str, plane: str, source: dict)` (function, `modules/prr/pgo.py`)
- `load(ledger: Path)` (function, `modules/prr/pgo.py`)
- `append(ledger: Path, profile: dict)` (function, `modules/prr/pgo.py`)
- `recommend_epoch(profiles: list, *, workload: str, plane: str, anon_budget_mb: float)` (function, `modules/prr/pgo.py`)
- `main(argv=None)` (function, `modules/prr/pgo.py`)
- `Decision` (class, `modules/prr/recycle_policy.py`)
- `last_boundary_ts(path: Path)` (function, `modules/prr/recycle_policy.py`)
- `mark_clear(pid: int, create_time: float, sid: str | None)` (function, `modules/prr/recycle_policy.py`)
- `cleared_in_process(pid: int, create_time: float)` (function, `modules/prr/recycle_policy.py`)
- `decide(*, proc_start: float, boundary_ts: float | None, cleared_ts: float | None, has_wrapper: bool, background_tasks: int, session_crons: int, is_subagent: bool=False)` (function, `modules/prr/recycle_policy.py`)
- `mem_fields(mem)` (function, `modules/prr/recycle_policy.py`)
- `run_hook(payload: dict, mode: str)` (function, `modules/prr/recycle_policy.py`)
- `main()` (function, `modules/prr/recycle_policy.py`)

### Dependencies
`__future__`, `argparse`, `json`, `os`, `subprocess`, `sys`, `time`, `itertools`, `http`, `math`, `platform`, `socket`, `dataclasses`, `hashlib`, `statistics`, `pathlib`, `datetime`

### Module type
- package
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Design decisions: _(Owner-defined; fill in during planning.)_
- Tradeoffs: _(Owner-defined; fill in during planning.)_
- What this module does NOT do: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
