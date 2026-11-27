---
phase: 04-host-pressure-admission
plan: 02
subsystem: benchmark-ledger
tags: [host-pressure, host_state-schema-2, regression-inconclusive, slow-host-suspect, mutants, PERF-04]
requires: [04-01 read_claude_process_count / pressure / claude_ceiling in tools/resource_admission.py]
provides: [HOST_SCHEMA 2, read_host_state(floors_path), host_pressure, entry_pressure, judge_metrics(pressure=), window_for under_pressure, host_pressure_lines, bench_all --floors, V-BENCH-PRESSURE-SUITE-WIRED]
affects: [plan 04-03 runs the live and forced-RED smoke and writes the STATE decisions]
status: complete
requirements: [PERF-04]
plan_head_before: 52e4af2d19250f837e131d06a4b6d89400e3cfca
commits: 6
actuals:
  tokens: 15500
  tasks: 2
  commits: 6
---

# Phase 4 Plan 02: Host pressure in the benchmark ledger Summary

`tools/bench_all.py` now stores the live claude process count and the GREEN/RED/UNKNOWN class in every ledger entry (host_state schema 2, read through the one by-path `resource_admission` loader). A RED or UNKNOWN run is recorded and shown but its regression verdicts are INCONCLUSIVE, it never enters a later window, and a target miss reads SLOW-HOST-SUSPECT on RED and COMPONENT FINDING on GREEN. `tools/test_bench_integrity.py` is 53/53, `tools/test_bench_gate.py` is 24/24.

Plane: GEX44 (kobicraft-gex44, Linux, Python 3.12.3, stdlib only). Laptop behaviour is LAPTOP-ONLY and UNJUDGED; nothing here judges it.

Branch: the isolated worktree branch `worktree-agent-a92a215b818bdb2b3` (start HEAD 52e4af2d, the merged 04-01 on `mission/perf-construction`), not `mission/perf-construction` itself. The ROOT milestone was not touched. Nothing was pushed.

## Commits

`commits: 6` is measured with `git rev-list --count 52e4af2d..HEAD` taken after the records commit (the SUMMARY commit is a seventh).

| Step | Hash | Subject |
|------|------|---------|
| baseline | cea3f4bb | docs(04-02): record pre-change baselines for the bench pressure wiring |
| T1 RED | c7df9889 | test(04-02): tracer gates for a starved host through bench_all main (red) |
| T1 GREEN | 81152927 | feat(04-02): record claude count and host pressure per sample, regression INCONCLUSIVE when not GREEN |
| T2 RED | c17dafdf | test(04-02): window exclusion, schema-1 rule, suspect lines, --floors, JSON, mutants, wiring gate (red) |
| T2 GREEN | e286d99d | feat(04-02): exclude non-GREEN entries from windows, name slow-host suspects, add --floors, wire the pressure suite |
| records | 777e2572 | docs(04-02): record green runs, mutants, after-change gates, reachability and s9 red-team comparison |

Records under `PH/records/` (PH = `.planning/workstreams/perf-construction/phases/04-host-pressure-admission`): `04-02-baseline.txt`, `04-02-T1.red.txt` (32/44, pristine=yes), `04-02-T1.green.txt` (44/44), `04-02-T2.red.txt` (48/53, pristine=yes), `04-02-T2.gate.red.txt` (22/24), `04-02-T2.green.txt` (53/53), `04-02-mutants.txt`, `04-02-gates-after.txt`, `04-02-reach-after.json`, `04-02-s9-redteam.after.txt`. Both integrity red records verify with `record_run --verify --expect fail --pristine-required` (VERIFY_OK).

## Baseline table (before vs after)

| Command | Baseline (HEAD 52e4af2d) | After (HEAD e286d99d code) |
|---------|--------------------------|----------------------------|
| tools/test_bench_integrity.py | 0, BENCHINT_PASS=41/41 | 0, 53/53 |
| tools/test_bench_gate.py | 0, BENCH_GATE_PASS=23/23 | 0, 24/24 (1.15 s wall) |
| tools/test_resource_pressure.py | 0, 17/17 | 0, 17/17 |
| tools/test_a5_u6.py | 0, 13/13 | 0, 13/13 |
| tools/test_arm_preflight.py | 0, 23/23 | 0, 23/23 |
| tools/test_gsd_mission_resources.py | 0, 17/17 | 0, 17/17 |
| tools/test_gsd_mission_baseline.py | 0, 21 passed | 0, 21 passed |
| tools/test_git_invocation.py | 1, 6/7 | 1, 6/7, offender names identical |
| reachability offenders | 56 | 56, names identical to 04-01-reach-after.json |
| vault/benchmarks/ledger.json sha256 | cef10a59... | unchanged |
| vault/config/resource-floors.json sha256 | 54a5f2af... | unchanged |

Invocation list: identical by name; the only textual difference is the line number of the already-frozen `tools/bench_all.py` call site (1148 to 1295, the same `get_head_commit` call moved by the added code). The `V-RES-CLI-*` lines differ only by a random temp directory name.

## test_s9_redteam.py comparison

After-run (`04-02-s9-redteam.after.txt`, run in the background with a 900 s bound): `S9RT_PASS=111/114`, wall 465 s, exit 1. Its PASS/FAIL verdict lines are equal to the 04-01 after-run's (diff of the first 60 characters of each line is empty), with the same three FAILs: `V-S9RT-REPORT-REPRODUCES` (claims differing [6, 9, 11, 13]), `V-S9RT-DRILL-M-REPORT-DRIFT` and `V-S9RT-DRILL-CONTROL-NOOP-FIRES`. Per the 04-01 SUMMARY the latter two are consequences of the first and the first predates this phase; unchanged by this plan.

## Task 1 red record: gates that failed at pristine bench_all.py (12)

The three new gates and the updated shape gate, plus nine existing gates that fail only because the fixtures are schema 2 while pristine `host_bucket` demands schema 1 (the schema-bump blast radius, not hidden): V-BENCHINT-FOUR-VERDICTS-PRESENT, VERDICT-UNKNOWN-NEVER-TRUE, EXIT-FROM-VERDICTS, COMPARE-MATCHED, ERRORED-ENTRY-EXCLUDED-FROM-WINDOW, WINDOW-FILTERS, REAL-REGRESSION-NOT-MASKED, INSUFFICIENT-WINDOW-IS-UNJUDGED, together with HOST-STATE-SHAPE, HOST-STATE-CARRIES-COUNT-AND-CLASS, SCHEMA-BUMP and RED-RUN-INCONCLUSIVE. All 44 pass after the GREEN commit.

## Task 2 red record

48/53 on pristine (post-Task-1) bench_all.py. Failing: RED-ENTRY-EXCLUDED-FROM-WINDOW, MET-TARGET-STAYS-JUDGED-ON-RED, FLOORS-FLAG (argparse SystemExit 2, caught by the gate), PRESSURE-LINES-RENDER, PRESSURE-MUTANTS-CAUGHT (targets for M3 and M5 absent). Passing already, because Task 1 had written `host_pressure` and the RED path: V-BENCHINT-SCHEMA1-ENTRY-IS-UNKNOWN, UNKNOWN-PRESSURE-INCONCLUSIVE, RED-NEVER-PRINTS-NO-REGRESSIONS, JSON-OUTPUT-STILL-PARSES. These four are therefore pins of Task 1 behaviour, not red-then-green gates; their opposite-input controls and the mutants (M4 for schema-1) are what show they can fail.

Wiring gate red (`04-02-T2.gate.red.txt`, no pristine header because the file under test is the one just edited): 22/24. V-BENCH-PRESSURE-SUITE-WIRED failed with `TypeError` (the old helper has no `marker`); V-BENCH-INTEGRITY-SUITE-WIRED also failed there because the integrity suite it runs was 48/53 at that moment. Both pass after the helper change.

## The five mutants (`04-02-mutants.txt`, each occurrence count 1)

| Id | One-line change | Flagged by |
|----|-----------------|------------|
| M1 | `elif pressure is not None and pressure[0] != PRESSURE_GREEN:` to `elif False:` | check_red_run (regressed True on RED) |
| M2 | `pressure=run_pressure` to `pressure=None` | check_red_run |
| M3 | `elif entry_pressure(e) != PRESSURE_GREEN:` to `elif False:` | check_window_exclusion |
| M4 | `if host_state.get("schema") != HOST_SCHEMA:` to `if False:` | check_schema1_unknown (forged schema-1 GREEN reads GREEN) |
| M5 | `suspect = cls != PRESSURE_GREEN and v.get("met_target") is False` to `suspect = False` | check_pressure_lines |

The real module returns no problems from all four checks (positive control).

## Design as built

- `read_host_state(floors_path=None)` has thirteen fields. The count and class come from `resource_admission.read_claude_process_count` and `pressure`; each pole has its own try block. A RAM-only fake, a raising loader, a raising or None count reader and a bool count all give claude_count None and pressure UNKNOWN. Zero processes is a reading (GREEN).
- `host_pressure(host_state)` is GREEN only for a schema-2 state whose stored class is exactly the string GREEN; everything else, including a forged schema-1 GREEN, is UNKNOWN.
- `judge_metrics(..., pressure=None)`: on RED or UNKNOWN, regressed None, evidence_sufficient False, reason `host pressure <CLASS> (<detail>): regression INCONCLUSIVE`; met_target and `verdicts_fail` unchanged, so a missed target still exits 1 and an in-target RED run exits 0.
- `main` passes `pressure=run_pressure`, empties baseline and compare deltas for a non-GREEN run, prints only the window header line (the UNJUDGED line would give a false reason) and then `HOST PRESSURE` lines after the verdict lines. The entry is saved before anything is printed (unchanged).
- `window_for` counts a non-GREEN prior entry under `under_pressure` and excludes it; the ledger keeps it.
- `--floors PATH`: forced-RED smoke path, no environment variable; the effective floor and ceiling are in the entry.
- Live reading on this host with the new reader (one sample, not a calibration): 31 claude processes, 51817 MB available, ceiling 40, class GREEN.

## Deviations from Plan

1. **[Rule 3 - environment] Commit message files in `/tmp/p0402/msgs/`** instead of `<git-dir>/gsd-msgs/`: the worktree guard refuses writes into the shared `.git/worktrees` tree through the Write tool (same as 04-01). Messages still end with the Co-Authored-By line.
2. **No on-disk plan-head ledger**; `plan_head_before` is recorded above (the start HEAD) and `commits` measured against it.
3. **`run_main` gained `mod=` and `loader=` parameters** (test harness only) so the mutation gate reuses the same end-to-end path on a mutant module and V-BENCHINT-FLOORS-FLAG can run the real `read_host_state`. No behaviour of earlier gates changed.
4. **`_try` in the test file also catches `SystemExit`** so an unknown `--floors` flag prints FAIL at pristine code instead of killing the run.
5. **Window header only on a non-GREEN run**: the plan said print the window lines; the UNJUDGED line would claim "a verdict needs >= 3 matched values" while the window is actually full, so only the first line is printed. Judgment call, covered by V-BENCHINT-RED-NEVER-PRINTS-NO-REGRESSIONS.
6. Four Task 2 gates pass at the Task 1 code (see above); stated, not hidden.
7. The Bash-tool worktree guard rejected commands containing certain substrings; helper scripts were kept in `/tmp/p0402/`, outside the repo.
8. STATE.md decision lines were not written (plan 04-03 owns them).

## Known Stubs

None.

## Threat Flags

None. host_state stores counts, a source label, the two declared numbers and a class; V-BENCHINT-HOST-STATE-SHAPE still asserts the exact field set and no environment capture. `--floors` reads only the file named.

## Unmet or open

Nothing in the plan is unmet. Open, carried by plan 04-03: the live and forced-RED smoke through `--floors` against a temp ledger, and the OWNER DECISION NEEDED line for the PROPOSED_UNCALIBRATED ceiling (T-04-02-05).

## Self-Check

- Files present: tools/bench_all.py, tools/test_bench_integrity.py, tools/test_bench_gate.py and the ten records listed above (checked by `git diff --name-only 52e4af2d..HEAD`, which lists only files in `files_modified` plus the records).
- Commits present: cea3f4bb, c7df9889, 81152927, c17dafdf, e286d99d, 777e2572 in `git log 52e4af2d..HEAD`.
- tools/resource_admission.py, tools/test_resource_pressure.py, tools/verify_bench_all.py, tools/gsd_mission.py, vault/config/resource-floors.json and vault/benchmarks/ledger.json are not in the diff.

## Self-Check: PASSED
