---
phase: 02-benchmark-integrity
plan: 01
subsystem: benchmarks
tags: [bench_all, benchmark-integrity, P01, P03, tdd]
requires: []
provides:
  - "bench_all: a TIMED_OUT, FAILED or CRASHED sample is an `_error`, never a primary `_ms` value (P03, bench_all side)"
  - "bench_all: non-zero exit on a primary absolute-target miss, correct per-benchmark tag, host-scope RAM UNJUDGED (P01)"
affects: [02-02, 02-03]
tech-stack:
  added: []
  patterns: ["classifier + per-site rollout table + mutant gate", "red/green verbatim records"]
key-files:
  created:
    - tools/test_bench_integrity.py
  modified:
    - tools/bench_all.py
key-decisions:
  - "Existing owner extended in place; no new owner module (D-01, D-03)."
  - "vgate failure keeps the elapsed total under `vgate_failed_run_ms`, never `vgate_total_ms` (D-03)."
requirements-completed: [PERF-02]
status: complete
plan_head_before: 39f59e28e409518b6c1adebfeb42e911027738e2
actuals:
  tokens: 21000
  tasks: 3
  commits: 6
---

# Phase 2 Plan 01: bench_all failure classification and absolute-target exit Summary

`tools/bench_all.py` can no longer report a failed benchmark as a fast one (a shared `_sample_failure` classifier at all 15 timed sites) and now exits 1 when a primary metric exceeds its absolute `TARGETS` value, backed by 28 falsifying gates in `tools/test_bench_integrity.py`.

## Commits (6, no push, base 39f59e28)

| Task | RED | GREEN |
|------|-----|-------|
| 1 tracer: failed pytest sample is an error | d76e8a9f `test(02-01)` | 4e7b6d0d `fix(02-01)` |
| 2 classifier at every timed site, vgate aggregate, mutant | b9611b73 `test(02-01)` | dcd6dfdc `fix(02-01)` |
| 3 absolute-target exit, tag, host-scope RAM, owner map | 729bf021 `test(02-01)` | 0ef7239f `fix(02-01)` |

## Records (under `phases/02-benchmark-integrity/records/`)

Each red record carries `# head:` (an ancestor of its fix commit), `# pristine: tools/bench_all.py=yes`, the verbatim output and `# exit=1`; all six verify with `record_run.py --verify ... --pristine-required`.

- `02-01-T1.red.txt` (head 39f59e28): `FAIL V-BENCHINT-PYTEST-FAILED-NOT-FAST: main rc=0, expected 1; errors=[] lacks 'pytest'; pytest_total_ms=0.0 recorded for a failed subprocess; console line '  [pytest] ... 0ms [OK] (outer 0ms)' lacks ERROR`, bookend PASS, `BENCHINT_PASS=1/2`. Green: 2/2.
- `02-01-T2.red.txt` (head 4e7b6d0d): 5/21; 14 of the 15 site gates FAIL (pytest, guarded by Task 1, passes), plus V-BENCHINT-VGATE-AGGREGATE and V-BENCHINT-MUTANT-CAUGHT (replacement count 0). Green: 21/21.
- `02-01-T3.red.txt` (head dcd6dfdc): 24/28; FAIL on ABS-MISS-EXITS-NONZERO (rc=0 for 9999 vs 20), RAM-HOST-SCOPE-UNJUDGED (pp 900 MB exited 0), TAG-USES-PRIMARY (`9999ms [OK]`), OWNER-MAP-COMPLETE. Green: 28/28.
- Live witness after the fix on this host: `bench_pytest()` returns `{'pytest_error': 'FAILED rc=1 after 26ms: /usr/bin/python3: No module named pytest'}` (before: `pytest_total_ms: 19.9` vs target 8000).

## Behaviour changes (deliberate, D-03)

- `verify_spp`, `pytest`, `vgate_suites` and every other timed benchmark now ERROR instead of reporting a time when the subprocess times out, cannot spawn, exits outside `COMPLETED_RCS`, or prints a crash signature ("Traceback (most recent call last)" / "No module named") on stderr. `session_start` and `monitoring` keep rc 1 as a verdict. On this host `pytest` always errors (not installed); `vgate_suites` and `verify_spp` will error whenever any suite or row exits non-zero.
- vgate: any failed suite sets `vgate_error` (label, count, first three names), keeps `vgate_count/passes/fails/suites`, drops `vgate_total_ms`, records `vgate_failed_run_ms`. Suite rows gain a `failure` field and a verdict label (`FAILED(rc=N)` instead of `FAIL(rc=N)`) only when failing; nothing in the repo reads the old string. Suite results are now sorted by name.
- `main` exits 1 when a primary metric of a selected, non-errored benchmark is strictly above its target; prints `TARGET MISSES (n):` and `UNJUDGED (n):` blocks (after the JSON entry and before the `bench_all exit rc=` trailer in `--json` mode, pinned by a gate). Host-scope `ram_footprint_mb` is always UNJUDGED and never gates; scope `pp` gates. The per-benchmark tag now reads `[OK]/[WARN]/[FAIL]` from the benchmark's own primary metrics (it used to be always OK).
- Ledger entry fields, `detect_regressions` and the legacy `history[-1]` baseline are byte-for-byte unchanged (plan 02-03 owns them).

## Exceptions in the site table

None needed: every one of the 15 sites does its timed work through `ba._run`, so one `_run` stub covers all of them. `bench_vgate_suites` is reached through `_run_suite` which also calls `_run`; the aggregate rule is additionally driven by patching `_run_suite`. The crash-signature case (rc 0 plus a Traceback) is applied to all 15 sites, including `session_start` and `monitoring` (the plan listed it only for `(0,)` sites); a Traceback on stderr is a crash whatever the rc.

## Existing gates (all run in this worktree)

| Command | Result | Exit |
|---------|--------|------|
| `python3 tools/test_bench_integrity.py` | BENCHINT_PASS=28/28 (0.2 s) | 0 |
| `python3 tools/test_bench_gate.py` | BENCH_GATE_PASS=13/13 | 0 |
| `python3 tools/test_ram_optimization.py` | RAM_PASS=10/10 | 0 |
| `python3 tools/test_git_invocation.py` | GIT_INVOCATION_PASS=6/7, only V-GITINV-NO-GROWTH fails, same 14 unfrozen offenders as baseline, V-GITINV-NO-STALE-EXEMPTION PASS, `[frozen] tools/bench_all.py` line moved 628 to 826 (diff of `02-01-gitinv.after.txt` vs `after-t3.txt` shows only the line number) | 1 (baseline) |

`scope_check.py` with the plan's allow list: `violations=0`. `vault/benchmarks/ledger.json` untouched (gates use a temp ledger; `tools/verify_bench_all.py` and `tools/verify_spp.py` were not run, and `bench_all` was not run live).

## Deviations from Plan

**1. [Process] Commit-message and ledger scratch location.** The plan said `<absolute git dir>/gsd-msgs/`; the sandbox refuses writes to the shared `.git` path from an isolated worktree, so message files and the plan-head ledger (`39f59e28...`) live in the gitignored `_audit_cache/gsd-msgs/` inside the worktree, as the spawning instruction allowed. `commits: 6` is measured with `git rev-list --count 39f59e28..HEAD` before the docs commit.

**2. [Test scope] `--json` ordering assertion.** Added inside V-BENCHINT-ABS-MISS-EXITS-NONZERO in the Task 3 GREEN commit (not in its RED record): the JSON entry must be first on stdout and the miss block plus rc trailer must follow it. No gate was added, count stays 28.

**3. [Observation] V-BENCHINT-UNSELECTED-NOT-A-MISS passes on pristine code** (as the plan expected) because its end-to-end half cannot distinguish; the direct `target_misses` half runs only once the function exists, and V-BENCHINT-OWNER-MAP-COMPLETE guards its existence.

No Rule 1-4 auto-fixes were needed. No stubs, no new network or auth surface, no threat flags.

## Self-Check: PASSED

- Files present: `tools/test_bench_integrity.py`, `tools/bench_all.py`, six record pairs and three `*.green.txt` gate outputs plus two `gitinv.after*.txt`.
- Commits d76e8a9f, 4e7b6d0d, b9611b73, dcd6dfdc, 729bf021, 0ef7239f exist and `git log -1 --format=%s` matched each message subject.
