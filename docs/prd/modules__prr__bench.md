# PRD (Tier 2 -- Feature / System Task) -- `modules/prr/bench`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

> prr bench -- GEX44 long-run fixture (stub API + driver). A package marker: the liveness gate only walks packages.

**Files:** 3  ·  **LOC:** 448  ·  **Public symbols:** 12

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

### Dependencies
`__future__`, `argparse`, `json`, `os`, `subprocess`, `sys`, `time`, `itertools`, `http`
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Problem: _(Owner-defined; fill in during planning.)_
- Objective (observable): _(Owner-defined; fill in during planning.)_
- Non-objectives: _(Owner-defined; fill in during planning.)_
- Users / actors: _(Owner-defined; fill in during planning.)_
- Functional requirements: _(Owner-defined; fill in during planning.)_
- Non-functional requirements: _(Owner-defined; fill in during planning.)_
- Acceptance criteria: _(Owner-defined; fill in during planning.)_
- Architecture Spec: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
