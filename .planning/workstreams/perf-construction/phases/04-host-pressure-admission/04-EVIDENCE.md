# Phase 4 Evidence: Host-pressure admission

Phase: 04-host-pressure-admission (requirement PERF-04)
Plane GEX44 (kobicraft-gex44, Linux, Python 3.12.3, stdlib only, no psutil). Date: 2026-11-23. Instrument HEAD for the live and forced-RED runs: the `# head:` line of both records is c4752b59, taken before the finished harness was committed; the harness text that produced them is the one committed in cadbbc81 together with the records, and tools/, modules/ and vault/ are identical at both. Evidence written on top of cadbbc81 and the final-gates commit.

Verdict: the three ROADMAP criteria are MET on GEX44, each cited to a record below. This is a verdict about the reader, the classifier, the ledger wiring and their gates on this host. It is not evidence about the laptop: the Owner's laptop case (28 claude.exe, 12 revived in one minute, 275-1563 MB free) is cited only as the motivation for the two poles; no laptop number was measured here and every laptop-judged item is LAPTOP-ONLY and UNJUDGED (section 8). Phase verification is a separate step.

Paths below are relative to `.planning/workstreams/perf-construction/phases/04-host-pressure-admission/` (written `PH`) unless they start with `tools/`, `modules/` or `vault/`.

## 1. Success criteria

| SC | Criterion | Command or test | Exit | Record | Verdict |
|----|-----------|-----------------|------|--------|---------|
| SC1 | resource_admission reads free RAM AND the live claude process count and returns RED below a declared floor (or above the declared ceiling), tested from both poles | `python3 tools/test_resource_pressure.py` (17 gates incl. both poles, unreadable is UNKNOWN never GREEN, five mutants rejected) and `python3 tools/resource_admission.py` | 0, PRESSURE_PASS=17/17; CLI exit 0 | `PH/records/04-01-T1.red.txt` (0/3), `04-01-T2.red.txt` (10/17), `04-01-T2.green.txt` (17/17), `04-01-mutants.txt`, `04-03-live.txt` | MET on GEX44 |
| SC2 | Every benchmark sample carries the host state; RED samples are INCONCLUSIVE for regression purposes | `python3 tools/test_bench_integrity.py` (53 gates) and the live smoke `PH/smoke_pressure.py --forced-red` through the shipped `bench_all.main` | 0, BENCHINT_PASS=53/53; SMOKE_PASS=7/7 | `PH/records/04-02-T1.red.txt` (32/44), `04-02-T2.red.txt` (48/53), `04-02-T2.green.txt` (53/53), `04-02-mutants.txt`, `04-03-forced-red.txt` | MET on GEX44 |
| SC3 | The laptop evidence is cited as the motivating case, LAPTOP-ONLY | no laptop number is measured or quoted as a result; LP-07 and LP-08 written with procedure and falsifier (section 8) | n/a | this file, section 8 | MET-WITH-UNKNOWNS: the laptop behaviour of the Windows and macOS parsers and of the ceiling is UNJUDGED |

Exactly one live run and one forced-RED run were recorded in `04-03-live.txt` and `04-03-forced-red.txt`; the forced-RED run was executed once more before recording during development (same result, 7/7, different RAM digits), and only the committed records are quoted here.

## 2. Gates and plan scope

| Plan | Commits | Files | Gate counts |
|------|---------|-------|-------------|
| 04-01 reader and classifier | 2cdf1a7d baselines, 784746d1 T1 red, cd6bed6e T1 green, 5c0e52a6 T2 red, 0a3bf103 T2 green, 971faea2 records | tools/resource_admission.py, tools/test_resource_pressure.py (new), vault/config/resource-floors.json (adds the `claude_process` key) | PRESSURE 3/3 after T1, 17/17 after T2; red 0/3 and 10/17 on pristine code |
| 04-02 ledger wiring | cea3f4bb baselines, c7df9889 T1 red, 81152927 T1 green, c17dafdf T2 red, e286d99d T2 green, 777e2572 records | tools/bench_all.py, tools/test_bench_integrity.py, tools/test_bench_gate.py | BENCHINT 41/41 to 53/53 (red 32/44 and 48/53 on pristine code), BENCH_GATE 23/23 to 24/24 (red 22/24) |
| 04-03 smoke and evidence | c4752b59 harness skeleton and plane self-test, cadbbc81 live and forced-RED records, then the final-gates, evidence and STATE.md commit(s) named in `04-03-SUMMARY.md` | PH/smoke_pressure.py, PH/records/04-03-*, PH/04-EVIDENCE.md, STATE.md | SMOKE 7/7; plane self-test 4/4; no production code |

`git diff --name-only 0a94118a..HEAD -- tools modules vault` (0a94118a is the 04-01 start) lists exactly: tools/bench_all.py, tools/resource_admission.py, tools/test_bench_gate.py, tools/test_bench_integrity.py, tools/test_resource_pressure.py, vault/config/resource-floors.json. tools/gsd_mission.py, tools/verify_bench_all.py and vault/benchmarks/ledger.json are not in that list. `git diff --stat f470597d..HEAD -- tools modules vault` is empty (record `04-03-final-gates.txt`, section `source_unchanged_since_04-02`).

## 3. Definitions

Claude process identity (tools/resource_admission.py `count_claude_procs`, Linux from /proc): a process counts when its comm equals `claude` or `claude.exe`, or its exe link ends `claude/versions/<name>` and `<name>` cut to the kernel's 15 characters equals comm. A semver-shaped comm whose exe link cannot be read goes to an `ambiguous` counter and is not counted. The command line is never read and nothing but counts leaves the reader (HR-SECRET-002). The count is of processes, not sessions, and it includes the reader's own session tree. An empty pid listing, a failed command, an unparseable output or an unsupported platform gives count None, never 0. The Windows (tasklist) and macOS (ps) parsers are pinned on fixture text and stub subprocess results only; their live behaviour is LAPTOP-ONLY and UNJUDGED.

Pressure classes (`pressure()`): RED when free RAM is below the declared floor (the single comparator `mb >= floor` admits, so strictly below is RED) or the claude count is strictly above the declared ceiling (a count equal to the ceiling is not RED, pinned by the M1 mutant), even if the other pole is unreadable. Otherwise UNKNOWN when a pole is unreadable. Otherwise GREEN. Reasons come out in the fixed order ram_below_floor, claude_count_over_ceiling, ram_unreadable, claude_count_unreadable. Nothing is killed or signalled.

host_state schema 2 (tools/bench_all.py, HOST_SCHEMA 2, thirteen fields): schema, host, os, cpu_count, available_mb, available_source, load1, claude_count, claude_count_source, claude_ceiling, ram_floor_mb, pressure, pressure_reasons. Schema-1 rule: an entry whose host_state is not schema 2 (legacy, or forged to claim GREEN) reads UNKNOWN pressure and has no host bucket, so it is never a baseline and never silently GREEN. An entry under RED or UNKNOWN is recorded and shown, never dropped; its `regressed` is None, `evidence_sufficient` is False with a reason naming the pressure, it does not enter later windows (counted as `under_pressure`), and `met_target` stays judged against the absolute target (D4-05 safest option).

Declared ceiling: `claude_process.ceiling` 40 in vault/config/resource-floors.json, status PROPOSED_UNCALIBRATED, basis and plane written next to it (section 6). Kill switch: `CPP_RESOURCE_ADMISSION=off` still short-circuits the RAM verdict and the opt-in count refusal (M5 mutant of 04-01). No automatic kill exists anywhere in the change (HR-STALLED-SESSION-ADVISORY-001).

## 4. Live smoke

Instrument for every number in this section: `PH/smoke_pressure.py` (stdlib, run with `python3 -I`) calling the shipped `tools/resource_admission.py` and `tools/bench_all.py` by file path. Plane GEX44, host kobicraft-gex44. Plane header: `plane_line()` is a pure function of (node, platform) with no override path; `records/04-03-plane-selftest.txt` shows PLANE_SELFTEST=4/4: (kobicraft-gex44, linux) prints the GEX44 line, and (kobicraft-gex44, win32), (some-other-node, linux) and (LAPTOP-OWNER, win32) each print `plane: UNVERIFIED`. The live modes exit 3 before any reading unless the line is the GEX44 one (D4-07 falsifier).

Live reading, copied from `PH/records/04-03-live.txt` (sample size n=1: one reading, a probe of that moment, not a distribution):

| Field | Value |
|-------|-------|
| Free RAM | 52320.125 MB, source /proc/meminfo |
| Claude processes | 29, source proc:exe+comm, ambiguous 0 |
| Declared RAM floor | 3000 MB (default profile) |
| Declared ceiling | 40, status PROPOSED_UNCALIBRATED |
| Class | GREEN, reasons none |

Forced-RED run, copied from `PH/records/04-03-forced-red.txt`: everything against a temp ledger and two temp floors files (paths named once in the record); the real `vault/benchmarks/ledger.json` sha256 `cef10a592e567e06fa43529966061bc223600475526fa2f435741f11582e32f4` and `vault/config/resource-floors.json` sha256 `54a5f2af2c4d2a46151bc751000819aafcfa67d69e43e0b95fdf1ed884cfdc09` are equal at step 0 and step 7. The stub benchmark is `never_again` (target 20 ms); the real `read_host_state` and the real reader run unchanged. The control uses three seeded GREEN runs at 10.0, so the window is n=3 (the declared minimum).

| Step | Input | Key lines from the record | Claim |
|------|-------|---------------------------|-------|
| 2 control seed | 3 runs, stub 10.0, declared floors | pressure GREEN each; RAM 52423.52, 52423.03, 52414.28 MB; count 29, proc:exe+comm | SMOKE-LIVE-GREEN PASS |
| 3 control | stub 18.0 (within target, above 10 x 1.15) | `REGRESSION WINDOW: 3 matched entries ... under_pressure=0`; `REGRESSIONS (1)`; `never_again_ms: 10 -> 18 ms (+80%)`; `HOST PRESSURE: GREEN`; `bench_all exit rc=1` | SMOKE-CONTROL-REGRESSES PASS (regressed True) |
| 4 count pole | temp floors default 1, ceiling 1; stub 18.0 | pressure RED, reasons claude_count_over_ceiling only; regressed None, evidence_sufficient False, met_target True; `HOST PRESSURE: RED (claude_count_over_ceiling)`; `REGRESSION: INCONCLUSIVE -- host pressure RED ...`; rc=0; no REGRESSIONS block; ledger entries 5 | SMOKE-FORCED-RED-COUNT PASS |
| 5 RAM pole | temp floors default 1000000000 MB, ceiling 1000000; stub 18.0 | pressure RED, reasons ram_below_floor only; same verdicts; `under_pressure=1` in the window line; rc=0; ledger entries 6 | SMOKE-FORCED-RED-RAM PASS |
| 6 next GREEN | declared floors, stub 10.0 | `REGRESSION WINDOW: 4 matched entries ... under_pressure=2`; this run regressed False; `HOST PRESSURE: GREEN` | SMOKE-RED-EXCLUDED-FROM-WINDOW PASS |
| 0 and 7 | sha256 of the two real files | equal before and after | SMOKE-REAL-FILES-UNTOUCHED PASS |

Footer: `SMOKE_PASS=7/7  threshold=7/7`, exit 0. The same data (stub 18.0) regresses on a GREEN host and is INCONCLUSIVE on a RED host through each pole separately, the RED entries are kept in the ledger and left out of the next window, and no RED run printed a bare no-regressions text (the record has none). The live host was GREEN at the start, so the exit-5 branch (live host not GREEN, no control built) was not taken.

The planning-time probe of 9 processes by comm-exact match versus 25 by the exe rule was one sample (n=1) taken before the reader existed; no record of this phase holds that comparison, so it is a probe and not evidence. Other counts seen in this phase's records at healthy samples: 27 (04-01 SUMMARY), 31 (04-02 SUMMARY), 29 (this plan, five readings in two records); each is a single reading and the spread shows the count moves with whatever sessions are open.

## 5. Gates

| Stage | Record | a5_u6 | arm preflight | bench integrity | bench gate | resource pressure | gsd resources | gsd baseline | git invocation | reachability |
|-------|--------|-------|---------------|-----------------|------------|-------------------|---------------|--------------|----------------|--------------|
| baseline (04-01) | `04-01-baseline.txt` | 13/13 | 23/23 | 41/41 | 23/23 | (not yet existing) | 17/17 | 21 passed | exit 1, 6/7 | 56 offenders |
| after 04-01 | `04-01-gates-after.txt`, `04-01-reach-after.json` | 13/13 | 23/23 | 41/41 | 23/23 | 17/17 | 17/17 | 21 passed | exit 1, 6/7 | 56, names identical |
| after 04-02 | `04-02-gates-after.txt`, `04-02-reach-after.json` | 13/13 | 23/23 | 53/53 | 24/24 | 17/17 | 17/17 | 21 passed | exit 1, 6/7 | 56, names identical |
| final (04-03) | `04-03-final-gates.txt`, `04-03-reach-final.json` | 13/13 | 23/23 | 53/53 | 24/24 | 17/17 | 17/17 | 21 passed | exit 1, 6/7 | 56, names identical |

Comparison of the final run with `04-02-gates-after.txt`: every exit code and counter is equal. The only textual difference is the random temp directory name printed by three V-RES-CLI-* lines (gsd-mission-res-test-8cse5bkg versus gsd-mission-res-test-qs26seop). The tools/test_git_invocation.py output (V-GITINV-NO-GROWTH FAIL, 14 unfrozen offender files, 2 frozen sites) is equal line for line. The 56 reachability offender names are identical to `04-02-reach-after.json` (checked by sorted list equality in the recording script); passed stays false, as before the phase. These pre-existing failures are not mine and are not claimed fixed.

Red and mutant records, all under `PH/records/`: `04-01-T1.red.txt` (PRESSURE 0/3, pristine tools/resource_admission.py), `04-01-T2.red.txt` (10/17, pristine module and json), `04-01-mutants.txt` (M1 ceiling comparator, M2 RAM pole off, M3 unreadable becomes zero, M4 empty listing counted as zero, M5 kill switch off), `04-02-T1.red.txt` (BENCHINT 32/44, pristine tools/bench_all.py), `04-02-T2.red.txt` (48/53, pristine), `04-02-T2.gate.red.txt` (BENCH_GATE 22/24), `04-02-mutants.txt` (M1 RED not INCONCLUSIVE, M2 pressure not passed, M3 window not excluding, M4 schema-1 rule off, M5 suspect line off). The 04-02 SUMMARY states which Task 2 gates passed already at Task 1 code and are pins rather than red-then-green gates.

tools/test_s9_redteam.py: not re-run by 04-03 (814 s wall in its last run; source unchanged since 04-02, empty `git diff --stat`). The 04-02 footer is `S9RT_PASS=111/114  threshold=114/114  wall=814s (limit 540s)` with three FAILs: V-S9RT-REPORT-REPRODUCES, V-S9RT-DRILL-M-REPORT-DRIFT, V-S9RT-DRILL-CONTROL-NOOP-FIRES. Caveat (UNJUDGED): the first was already failing in the 04-01 baseline run, which timed out at 900 s after 66 PASS and that one FAIL; the other two name the first as their own cause. No clean control run was possible, so "these three also appear without this phase's changes" is inferred from the suite's own messages, not shown by a pristine run.

## 6. Declared numbers

RAM floors: unchanged by this phase (default 3000 MB; slim-t1 and slim-t2 1500; top-level-worker 3000), asserted by V-PRESS-DECLARED-CEILING-FILE and V-PRESS-OLD-CALLERS-UNCHANGED.

Claude process ceiling: 40, status PROPOSED_UNCALIBRATED. Reasoning, as written in the file's `basis`: the only host with a reading is GEX44, 25 processes by the exe rule at one healthy sample with 51 GB available (n=1, a probe); later single readings in this phase's records were 27, 29 and 31 (not in the `basis` text); 40 sits above all of them so the count pole cannot call the measured healthy host RED; the laptop's starvation is already caught by the RAM pole, so the laptop case explains why a count pole exists and does not set its value; a ceiling too high only under-reports, a ceiling too low would turn regression judging off on a healthy host, so the conservative direction was taken. This is a PROPOSAL. GEX44 numbers do not calibrate the laptop (D4-03). Only a record path written into `basis` (LP-08) may change the status. The headroom is thin (29 versus 40 in the committed records) because the count includes every open claude process on this shared host, including the sessions of this mission; if the count pole fires on GEX44 the entry is recorded as RED and excluded, which is the safe direction.

## 7. D4-01..D4-10 trace

| Decision | Satisfied by | Records | Notes |
|----------|--------------|---------|-------|
| D4-01 extend, count reader, None never 0, no psutil | cd6bed6e, 0a3bf103 | `04-01-T1.green.txt`, `04-01-T2.green.txt`, `04-01-mutants.txt` (M3, M4) | tools/resource_admission.py extended; no new module; stdlib only |
| D4-02 RED additive, old verdicts and callers stay, kill switch, no auto-kill | 0a3bf103 | V-PRESS-OLD-CALLERS-UNCHANGED in `04-01-T2.green.txt`; M5; `04-03-final-gates.txt` (a5_u6, arm preflight, gsd tests equal) | Implemented differently from the text: the count refusal exists as an opt-in `count_reader` parameter that no launch path passes (safest option; OWNER DECISION NEEDED (4)). The old RAM behaviour is byte-for-byte what existing callers see |
| D4-03 declared numbers with a source; ceiling a PROPOSAL; GEX44 does not calibrate laptop | 0a3bf103 | vault/config/resource-floors.json `claude_process`; section 6 | status PROPOSED_UNCALIBRATED; OWNER DECISION NEEDED (3) |
| D4-04 both poles and mutation records | 784746d1, 5c0e52a6, c7df9889, c17dafdf | the red, green and mutant records listed in section 5 | each red record taken on pristine code (`# pristine:` lines) |
| D4-05 host_state carries count and class, schema bump, RED INCONCLUSIVE, excluded from windows, met_target judged | 81152927, e286d99d | `04-02-T1.green.txt`, `04-02-T2.green.txt`, `04-03-forced-red.txt` | Implemented beyond the text: UNKNOWN pressure is also INCONCLUSIVE and excluded (safest: never judge on an unmeasured host; OWNER DECISION NEEDED (5)); the schema bump restarts windows (OWNER DECISION NEEDED (6)) |
| D4-06 SLOW-HOST-SUSPECT versus component finding, no new verdict key | e286d99d | V-BENCHINT-PRESSURE-LINES-RENDER and M5 in `04-02-mutants.txt` | UNKNOWN host prints UNATTRIBUTABLE; no new verdict key added |
| D4-07 live smoke naming plane, forced-RED with temp floors and temp ledger, LP-07 with falsifier | c4752b59, cadbbc81 | `04-03-plane-selftest.txt`, `04-03-live.txt`, `04-03-forced-red.txt` | section 4 and section 8 |
| D4-08 baselines first and kept green, new tests wired, offender sets by name | 2cdf1a7d, cea3f4bb, e286d99d (V-BENCH-PRESSURE-SUITE-WIRED with its negative control) | `04-01-baseline.txt`, `04-02-baseline.txt`, `04-03-final-gates.txt`, reach json files | section 5 |
| D4-09 scope fences | wave-disjoint file lists | `git diff --name-only 0a94118a..HEAD -- tools modules vault` (section 2) | tools/gsd_mission.py and tools/verify_bench_all.py untouched |
| D4-10 evidence, hygiene, SUMMARY per plan, OWNER DECISION NEEDED lines | 04-01, 04-02, 04-03 SUMMARY files; this file; STATE.md Phase 4 section | the SUMMARY files | commits by explicit pathspec, nothing pushed; commit message files were kept outside the shared git directory because the worktree guard refused writes there (recorded as a deviation in each SUMMARY) |

## 8. LAPTOP-ONLY items

Both items are UNJUDGED until the laptop supplies the records. No laptop number appears in this file as a measurement.

LP-07 (reader on the laptop). Procedure: from a checkout containing these commits, run `python tools/resource_admission.py` with the laptop floors file at three moments (idle, the Owner's usual session set, immediately after a revival burst). Save the JSON of each run into a file whose header is the output's own `host` and `os` keys. Cross-check the count once against the Task Manager claude.exe row count at the same moment. Falsifier: any laptop record whose `os` is linux or whose `host` is kobicraft-gex44; any GEX44 number filed as a laptop number; or a record whose count source is an unreadable one while its class is GREEN (an unreadable pole must read UNKNOWN or RED, never GREEN). Also falsified if the tasklist count and the Task Manager row count differ by more than the ambiguous counter explains.

LP-08 (ceiling calibration). Procedure: on the laptop take at least ten `tools/bench_all.py --quick` runs spread across low and high claude counts, each into a ledger entry carrying its host_state, and compare same-bucket timings. Falsifier: if timings at counts above the proposed 40 are not slower than at counts below 10 beyond run-to-run spread, the count is not a timing predictor on the laptop and the ceiling must stay advisory (OWNER DECISION NEEDED (3) option d). Only a record path written into the json `basis` may change the status from PROPOSED_UNCALIBRATED.

Also laptop-only: the Windows tasklist and macOS ps count parsers (fixture-tested here, never run on those hosts), and whether the laptop's RAM floors suit its workload.

## 9. P-ids and open debt

P16 and P17 (admission does not govern total host consumption; combined sentence in the source): the reader and the classifier exist and are tested from both poles, and bench_all uses them. The launch-admission path in tools/gsd_mission.py still judges RAM only because no caller passes `count_reader`, so the launch-path half stays PARTIALLY_FIXED and is an OWNER DECISION (4). The laptop figures behind P16 and P17 stay LP-01 and LP-07, UNJUDGED.

P06 (regression compared the previous run, not a host-state-matched window): completed for the ledger. Phase 2 made the window host-state-matched; Phase 4 adds the missing cause, so a slow host (RED or UNKNOWN pressure) is separated from a slow component (GREEN host, `COMPONENT FINDING`), and a starved host's run is INCONCLUSIVE and out of later windows.

Not done by design: tools/verify_bench_all.py is unedited and does not read host pressure (OWNER DECISION (7)); ROADMAP.md, the ROOT milestone, tools/gsd_mission.py and the live power-pack install are untouched; no benchmark of the real nine was run by the harness and the real ledger was never opened for writing; tools/test_s9_redteam.py was not re-run (section 5 caveat).

Carried debt, pre-existing and unchanged by name: 56 reachability offenders, tools/test_git_invocation.py 6/7 (14 unfrozen offender files), tools/test_s9_redteam.py 111/114.

OWNER DECISION NEEDED lines, copied from `.planning/workstreams/perf-construction/STATE.md` (Phase 4 section; (1) and (2) are the Phase 2 lines in the same file):

- (3) The claude process ceiling is 40, PROPOSED_UNCALIBRATED. Options: keep 40, lower it, raise it, or switch the count pole off. Pick: keep 40. Reversal: edit `claude_process.ceiling` in vault/config/resource-floors.json; calibrate through LP-08.
- (4) The count refusal (REFUSE_HIGH_PROCESS_COUNT) is opt-in through `count_reader` and no launch path passes it. Pick: leave unwired. Reversal: pass `count_reader=rsa.read_claude_process_count` at the two `rsa.refusal(` calls in tools/gsd_mission.py (plus the preflight call) after LP-07 and LP-08 give laptop evidence.
- (5) UNKNOWN pressure is treated like RED for regression purposes. Pick: yes. Reversal: narrow `judge_metrics` and `window_for` in tools/bench_all.py to RED only.
- (6) The HOST_SCHEMA bump restarts regression windows (first three same-bucket runs print UNJUDGED). Pick: accept.
- (7) tools/verify_bench_all.py does not read host pressure. Pick: leave. Reversal: make its sample carry the entry's pressure and print SLOW-HOST-SUSPECT.

Also recorded in STATE.md: Owner decision D2 raised the authority ceiling to 215,000,000, and the tools/test_s9_redteam.py caveat of section 5.
