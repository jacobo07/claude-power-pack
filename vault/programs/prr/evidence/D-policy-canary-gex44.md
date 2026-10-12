# D -- Policy canary: the real recycle_policy hook decides, GEX44 plane (2026-10-12)

Same plane as B/C (Linux, 2.1.296 Bun/JSC, isolated config, zero provider tokens). Driver: `longrun.py --mode policy`
(commit 24619fba). The bench config registers the real hook on SessionStart + Stop
(`cd ~/missions/prr && CPP_PRR_RECYCLE=observe python -m modules.prr.recycle_policy`); the driver issues a boundary
every 10 turns and recycles (`--resume <sid>`) only when the hook's Stop receipt says RECYCLE.
Raw rows: GEX44 `~/prr-bench/runs/canary-{compact,clear}.jsonl` + `.receipts.jsonl`. 40 turns, 4 epochs each.

## Decisions (driver row receipts, 40 per run)
| run | sequence | RECYCLE at turn | reason in receipt |
|---|---|---|---|
| compact | KEEP x10, RECYCLE, KEEP x9, RECYCLE, KEEP x9, RECYCLE, KEEP x9 | 11, 21, 31 | `compact boundary` |
| clear | same shape | 11, 21, 31 | `/clear inside this process` |

- Exactly one RECYCLE per boundary, on the first Stop after it. Every Stop in a resumed process before its own
  boundary is KEEP (`no boundary crossed inside this process`): **no recycle loop**.
- /clear: SessionStart `source=clear` writes a MARK (marker file) under the new sid; the next Stop reads it.
- Session identity: compact keeps one sid across all 4 processes (c13b7e94). /clear mints a new sid each epoch (as
  the host does); the recycle resumes *that* sid, so `sid_in == sid_out` at every epoch.
- `acted` is false on every receipt: the hook ran in observe mode and the bench performed the relaunch. **The act path
  (`CPP_PRR_RECYCLE=act` -> `restart-claude.ps1`) is not exercised here**; that is the Windows canary.

## Memory (RssAnon MB, main process; tree_n = 1 throughout)
| run | t1 fresh | right after each resume (epochs 2-4) | resume s | epoch-start drift |
|---|---|---|---|---|
| compact | 110 | 128, 131, 137 | 0.47, 0.40, 0.38 | +4.5 MB/epoch (n=3) |
| clear | 110 | 123, 123, 122 | 0.35, 0.37, 0.37 | -0.5 MB/epoch (n=3) |

The run's own in-epoch slope fit (60 / 82 MB per 100 turns) uses 5 samples spread over 4 epochs and is not a
growth rate; read the epoch-start column. The compact +4.5 MB/epoch is larger than C's +0.27 (8 epochs). With n=3 it
is unresolved, not a contradiction; the Windows canary and a longer GEX44 rerun should report it.

## Receipt defect found by this run (fixed in the commit that adds this note)
Receipts reported `private_mb` 5,476-5,484 for a process with a 278-284 MB working set: off Windows psutil has no
`private`, and the old fallback used `vms`. `mem_fields()` now reports `private_mb: null` when the platform has no
private bytes. Pinned by `test_mem_fields_never_reports_virtual_size_as_private`.
