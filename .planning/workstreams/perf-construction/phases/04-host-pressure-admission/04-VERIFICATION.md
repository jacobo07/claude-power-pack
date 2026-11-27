---
phase: 04-host-pressure-admission
verified: 2026-11-23T12:00:00Z
status: passed
verdict: passed_with_unknowns  # GSD routes only passed|gaps_found|human_needed; unknowns below stay open
score: 3/3 roadmap success criteria verified on GEX44 (laptop behaviour, ceiling value and s9 red-team caveat UNJUDGED)
verified_head: 7bca4f52
behavior_unverified: 0
gaps: []
unknowns:
  - "LAPTOP-ONLY: the Windows tasklist and macOS ps count parsers are pinned on fixture text and stub subprocess results only. No real reading was taken on those hosts. LP-07 stays UNJUDGED"
  - "LAPTOP-ONLY: the claude process ceiling 40 is PROPOSED_UNCALIBRATED (LP-08). GEX44 readings (22-31 processes at healthy samples) do not calibrate the laptop and no claim is made that the count predicts timing. The headroom on GEX44 is thin (29 live versus 40) because the count includes every open claude process on this shared host"
  - "The laptop motivating case (28 claude.exe, 275-1563 MB free) is RED on the RAM pole and NOT RED on the count pole at ceiling 40 (re-observed by input, see Spot-checks). The count pole therefore explains nothing about that case; the RAM pole carries it. Not a defect, but the count pole is unproven as a timing predictor"
  - "tools/test_s9_redteam.py: 111/114 with V-S9RT-REPORT-REPRODUCES, V-S9RT-DRILL-M-REPORT-DRIFT and V-S9RT-DRILL-CONTROL-NOOP-FIRES failing. I did not re-run it (814 s). There is no clean control run, so 'these three are pre-existing and not caused by this phase' is UNJUDGED, not passed. Partial evidence only: the 04-01 baseline record (taken before any phase code change, but timed out at 900 s) shows V-S9RT-REPORT-REPRODUCES FAIL, and the other two name it as their cause"
  - "tools/verify_bench_all.py is unedited (OWNER DECISION (7)). Its sample() returns only the results block and drops host_state, so that gate cannot tell a slow host from a slow component. It judges absolute bands, not regression, so SC2 as worded still holds, but a RED host can fail that gate without a SLOW-HOST-SUSPECT line. Each bench_all run it triggers does still write a ledger entry carrying host_state"
  - "The launch-admission path in tools/gsd_mission.py still judges RAM only: refusal(count_reader=...) is opt-in and no caller passes it (OWNER DECISION (4)). The launch half of P16/P17 stays PARTIALLY_FIXED. The phase goal clause 'work is admitted against the host's real state' is met for benchmark judging and not for launch admission"
  - "UNKNOWN pressure is treated like RED for regression purposes and the HOST_SCHEMA 2 bump restarts regression windows (the first three same-bucket runs print UNJUDGED). Both are recorded Owner decisions (5) and (6), safest and reversible; they are behaviour beyond the literal ROADMAP text"
  - "Pre-existing, unchanged by name and not claimed fixed: 56 reachability offenders, tools/test_git_invocation.py 6/7 (14 unfrozen offenders), tools/test_s9_redteam.py 111/114"
human_verification: []
---

# Phase 4: Host-pressure admission - Verification Report

**Phase goal:** Work is admitted against the host's real state; a starved host is reported as such.
**Plane:** GEX44 (kobicraft-gex44, Linux, Python 3.12.3, stdlib only). Every number below was observed by me on this host in this session; the laptop was not measured and nothing here is a laptop result.
**Re-verification:** No, initial verification. Base HEAD 7bca4f52 (all three plans merged).
**Status: passed_with_unknowns.** The three roadmap success criteria are met on evidence I re-observed. Nothing failed. The unknowns above are not counted as passes.

Method: code reading of `tools/resource_admission.py`, the `bench_all.py` diff (0a94118a..HEAD), `vault/config/resource-floors.json`; re-run of the cheap gates and the phase smoke; my own input-level pole probes written outside the repo (not the phase's tests); two throw-away mutants applied to a `git archive` copy under /tmp (the repo was not mutated). SUMMARY.md and 04-EVIDENCE.md were used only to know where to look.

## Observable Truths (ROADMAP Phase 4 success criteria)

| # | Truth | Status | Evidence (re-observed) |
|---|-------|--------|------------------------|
| 1 | resource_admission reads free RAM and live claude process count and returns RED below a declared floor, tested from both poles | VERIFIED (GEX44; Windows/macOS readers LAPTOP-ONLY) | `read_claude_process_count()` and `pressure()` exist in `tools/resource_admission.py`; `pressure()` returns RED when `verdict()` is REFUSE_LOW_MEMORY or `count > ceiling`, UNKNOWN when a pole is unreadable, GREEN only when both read. `python3 tools/test_resource_pressure.py`: `PRESSURE_PASS=17/17`, exit 0. My own probe (14 input cases, not the phase's tests): fine/fine GREEN; RAM 1000 MB RED; count 41 RED; count equal to ceiling 40 GREEN; RAM equal to floor GREEN; RAM unreadable UNKNOWN; count unreadable UNKNOWN; both None UNKNOWN; RAM unreadable with count 99 RED; bool, negative and NaN readings UNKNOWN. Fake /proc tree: 2 counted (one `claude` comm, one semver comm with a `claude/versions` exe), 1 `ambiguous` (semver comm, unreadable exe), `bash` and a non-versions `node` not counted; empty tree and missing root give count None with an `unreadable:` source, never 0. Real run `python3 -I tools/resource_admission.py`: count 29, source `proc:exe+comm`, RAM 52928 MB, class GREEN, exit 0. I cross-checked the 29 independently: 9 processes with comm `claude`/`claude.exe` plus 10 live and 10 `(deleted)`-exe processes under `claude/versions/` (the module's own rules; a looser count of mine gave 22 because it left out the comm-name group, a difference I traced rather than waved off). Mutant (mine) `count > ceiling` to `>=` is caught by V-PRESS-TRACER-COUNT-OVER-IS-RED, V-PRESS-BOUNDARY-CEILING and V-PRESS-MUTANTS-CAUGHT (14/17). `test_a5_u6.py` 13/13, `test_arm_preflight.py` 23/23, `test_gsd_mission_resources.py` 17/17, `test_gsd_mission_baseline.py` 21 passed 0 failed: old callers unchanged. No kill, signal or terminate call exists in the module (grep empty). The count refusal REFUSE_HIGH_PROCESS_COUNT is opt-in and unreached by any launch path (see unknowns). |
| 2 | Every benchmark sample carries the host state; samples under RED are INCONCLUSIVE for regression purposes | VERIFIED (bench_all ledger entries; verify_bench_all gate not extended) | `read_host_state()` in `tools/bench_all.py` writes schema 2 with `claude_count`, `claude_count_source`, `claude_ceiling`, `ram_floor_mb`, `pressure`, `pressure_reasons` into every ledger entry, reading through the one by-path loader of `resource_admission` (one parser, not two). `judge_metrics(..., pressure=)` returns `regressed=None`, `evidence_sufficient=False` with a reason naming the pressure when the class is not GREEN, while `met_target` stays judged. `window_for` excludes non-GREEN entries (`under_pressure`), and `host_pressure()` makes a schema-1, forged or missing-class entry UNKNOWN, never GREEN. `test_bench_integrity.py` `BENCHINT_PASS=53/53`, `test_bench_gate.py` `BENCH_GATE_PASS=24/24` (includes V-BENCH-PRESSURE-SUITE-WIRED with a negative control). I re-ran `smoke_pressure.py --forced-red` end to end through the shipped `bench_all.main`: `SMOKE_PASS=7/7`, exit 0. Control stub 18.0 against three seeded 10.0 runs on a GREEN host prints `REGRESSIONS (1)` and rc=1. The same data through the count pole (RED, `claude_count_over_ceiling` only) and through the RAM pole (RED, `ram_below_floor` only) gives `regressed None`, `evidence_sufficient False`, `met_target True`, `HOST PRESSURE: RED (...)`, `REGRESSION: INCONCLUSIVE ...`, rc=0, no REGRESSIONS block, the entry kept in the (temp) ledger. The next GREEN run reports `under_pressure=2` and its own `regressed=False`. The real `vault/benchmarks/ledger.json` (sha256 cef10a59...) and `vault/config/resource-floors.json` (sha256 54a5f2af...) are byte-identical before and after my run. My mutants: removing the `under_pressure` window exclusion fails V-BENCHINT-RED-ENTRY-EXCLUDED-FROM-WINDOW (window kept the 500/600 RED values); replacing the pressure branch of `judge_metrics` with `elif False` fails V-BENCHINT-RED-RUN-INCONCLUSIVE (`regressed=True` on a RED run). The classification is behaviour-dependent and each pole has a behavioural test, so no truth is left at presence only. Doubt: `tools/verify_bench_all.py` `sample()` returns only `results` and discards `host_state`; it judges absolute bands, not regression, so the criterion's wording holds, but that gate is blind to host pressure (unknown 5). |
| 3 | Laptop evidence (28 claude.exe, 12 revived in one minute, 275-1563 MB free) is cited as the motivating case, LAPTOP-ONLY | VERIFIED (cited, not measured) | 04-EVIDENCE.md sections 1, 6, 8 cite the figures only as motivation and say no laptop number was measured; LP-07 (reader on the laptop) and LP-08 (ceiling calibration) are written with a procedure and a falsifier and marked UNJUDGED. `vault/config/resource-floors.json` `claude_process.basis` and `plane` say the same and carry status PROPOSED_UNCALIBRATED. The live smoke prints a plane line from a pure function with no override path; `--selftest-plane` gives `PLANE_SELFTEST=4/4` (GEX44 only for exactly kobicraft-gex44 on linux, UNVERIFIED for win32, another node, and a laptop name). |

**Score:** 3/3 criteria verified; 0 present-but-behavior-unverified truths.

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/resource_admission.py` | reader + `pressure()`, old verdicts intact | VERIFIED | 295 lines; extends the existing module (D4-01), stdlib only |
| `tools/test_resource_pressure.py` | both-pole gates + mutants | VERIFIED | 17/17 re-run; wired into `test_bench_gate.py` with a negative control |
| `vault/config/resource-floors.json` | declared ceiling with basis | VERIFIED | `claude_process` key; `default` and `profiles` keys unchanged; reader falls back to 40 on a bad value |
| `tools/bench_all.py` | host_state schema 2, INCONCLUSIVE, window exclusion | VERIFIED | diff read in full; main prints the INCONCLUSIVE line on a non-GREEN host |
| `tools/test_bench_integrity.py`, `tools/test_bench_gate.py` | new gates | VERIFIED | 53/53 and 24/24 re-run |
| `phases/04-host-pressure-admission/smoke_pressure.py` | live and forced-RED harness | VERIFIED | re-run; temp ledger and temp floors; real files untouched |
| `04-EVIDENCE.md`, `records/` | commands, exit codes, red records, mutants | VERIFIED | numbers I re-ran match; records for red-then-green and mutants present |

## Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `bench_all.read_host_state` | `resource_admission.read_claude_process_count` and `pressure` | by-path loader `_load_resource_admission`, each pole in its own try block | WIRED (forced-RED smoke exercises it) |
| `bench_all.main` | `judge_metrics(pressure=)`, `window_for`, `host_pressure_lines` | `run_pressure = host_pressure(host_state)` | WIRED |
| `bench_all.main --floors` | `read_host_state(floors_path)` | temp floors for forced-RED | WIRED |
| `resource_admission.refusal` | `pressure()` | opt-in `count_reader` | PARTIAL by design: no launch caller passes it (OWNER DECISION (4)) |
| `test_resource_pressure.py` | bench gate row | V-BENCH-PRESSURE-SUITE-WIRED | WIRED, negative control passes |

## Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Real data | Status |
|----------|---------------|--------|-----------|--------|
| host_state.available_mb | `/proc/meminfo` MemAvailable | `read_available_mb` | yes (52 GB observed) | FLOWING |
| host_state.claude_count | `/proc/<pid>/comm` and `exe` link | `count_claude_procs` | yes (29, traced to 9 + 10 + 10) | FLOWING |
| host_state.pressure | `pressure()` of both readings | declared floors file | yes (GREEN live, RED in forced run) | FLOWING |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Pressure suite | `python3 tools/test_resource_pressure.py` | `PRESSURE_PASS=17/17`, exit 0 | PASS |
| Bench integrity | `python3 tools/test_bench_integrity.py` | `BENCHINT_PASS=53/53`, exit 0 | PASS |
| Bench gate | `python3 tools/test_bench_gate.py` | `BENCH_GATE_PASS=24/24`, exit 0 | PASS |
| Plane self-test | `python3 -I .../smoke_pressure.py --selftest-plane` | `PLANE_SELFTEST=4/4`, exit 0 | PASS |
| Live reading | `... --live` | plane GEX44; RAM 52515 MB; 29 processes; GREEN; n=1 | PASS (a probe, not a distribution) |
| Forced RED, both poles | `... --forced-red` | `SMOKE_PASS=7/7`, exit 0, real files unchanged | PASS |
| Old callers | a5_u6 13/13, arm preflight 23/23, gsd resources 17/17, gsd baseline 21/0 | all exit 0 | PASS |
| Reachability | `python3 modules/liveness/reachability.py --json` | exit 1, 56 offenders, unit names equal to `records/04-03-reach-final.json` | PASS (unchanged by name; debt pre-existing) |
| Git invocation | `python3 tools/test_git_invocation.py` | 6/7, V-GITINV-NO-GROWTH FAIL on the same 14 files as `04-01-baseline.txt` | PASS (unchanged; pre-existing) |
| Own poles, own fake /proc | `python3 -I /tmp/p4v_scratch/poles.py` | 14/14 as expected, count tree 2 + ambiguous 1 | PASS |
| Own mutants | see truth 1 and 2 | each caught by the owning gates | PASS |

## Probe Execution

No phase-declared `probe-*.sh`. SKIPPED. The red-then-green record files and the mutant records stand in as the phase's own falsification evidence, and I re-derived two mutants and the pole table myself.

## Requirements Coverage

| Requirement | Source | Description | Status | Evidence |
|-------------|--------|-------------|--------|----------|
| PERF-04 | 04-01, 04-02, 04-03 | host-pressure admission from both poles | SATISFIED on GEX44 | truths 1-3; laptop items UNJUDGED |

No orphaned requirement IDs mapped to Phase 4.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (modified files) | - | TBD / FIXME / XXX grep | none | empty |
| tools/resource_admission.py | 198 | `lstrip` of a literal U+FEFF (the injection scan flagged "invisible unicode") | Info | deliberate BOM strip in `parse_tasklist_csv`, not an injection |
| tools/resource_admission.py | 230-239 | Windows and macOS branches never run live | Warning | LAPTOP-ONLY, labelled in code and evidence |

Scope fences hold: `git diff --name-only 0a94118a..HEAD` lists only the six code/config files, STATE.md and the phase directory. `tools/gsd_mission.py`, `tools/verify_bench_all.py`, `vault/benchmarks/ledger.json` and ROADMAP.md are not in it.

## Human Verification Required

None blocking. Laptop evidence is listed as unknowns, not as items awaiting a human on this host (LP-07, LP-08 in 04-EVIDENCE.md section 8).

## Gaps Summary

No gaps. The phase delivers a reader, a classifier, ledger wiring and their gates, and I falsified each from the input side. What it does not deliver, and says so: laptop behaviour, a calibrated ceiling, launch-path admission by count, and any pressure awareness in `verify_bench_all`. The s9 red-team suite stays UNJUDGED for lack of a clean control run.

---

_Verified: 2026-11-23_
_Verifier: Claude (gsd-verifier)_
