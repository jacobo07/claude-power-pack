# Phase 6 - Inheritance map (plan 06-01, PERF-06)

Plane: GEX44 (Linux, Python 3.12, stdlib only). Every verdict below is quoted from a recorded run; none is the planner's expectation.
Instrument: `inherit_check.py` (phase-local, `python3 -I`, registered nowhere). Its own selftest ends `INHERIT_SELFTEST=9/9` and includes a mutant control that proves the count rule can fail (`records/06-01-T1.selftest.txt`).

Records:
- `records/06-01-T1.selftest.txt`, `records/06-01-T1.tracer.txt` - checker controls and the one-row tracer.
- `records/06-01-T2.manifest.txt` - the standing gates of Phases 2-5 against their recorded counts.
- `records/06-01-T3.matrix.txt` - the mutant matrix (verified by `inherit_check.py matrix --verify-record`).

## 1. Manifest: what the standing gates say today (06-01-T2.manifest.txt, one run, no retry)

Footer: `INHERIT_JUDGED=14/15 judged`, `INHERIT_PASS=14/14`, `SKIPPED=1`, `NOT_JUDGED=0`. Ledger and floors sha256 SAME before and after.

| Row | Verdict | Observed vs recorded |
|-----|---------|----------------------|
| a5_u6 | PASS | 13/13 |
| arm_preflight | PASS | 23/23 |
| bench_integrity | PASS | 53/53 |
| bench_gate | PASS | 24/24 |
| resource_pressure | PASS | 17/17 |
| gsd_mission_resources | PASS | 17/17 |
| gsd_mission_baseline | PASS | `21 passed, 0 failed` |
| metrology | PASS | 38/38 |
| critical_path | PASS | 134/134 |
| hook_boundary | PASS | 7/7 (fresh temp HOME; the duplicate-invocation sub-check stays UNEVALUATED, LAPTOP-ONLY LP-12) |
| git_invocation | BASELINE_MATCH | 6/7, equal to the recorded pre-existing debt; not a pass |
| hooks_unchanged | PASS | empty `git diff --stat 4fa606d7 -- hooks/` |
| reachability | BASELINE_MATCH | 56 offenders, names equal `05-01-reach-pre.txt` by unit; pre-existing debt |
| phase6_tree_clean | PASS | empty porcelain for tools, modules, hooks, vault/config |
| s9_redteam | SKIPPED_BY_POLICY | 814 s; last recorded 111/114; UNJUDGED, no clean control run exists (Phase 4 caveat) |

Reading: 14 of 15 rows were judged and none failed. The two BASELINE_MATCH rows are pre-existing debt unchanged by name, not fixed. The skipped s9 red-team is not a pass and nothing here says it is.

## 2. Mutant matrix: which proofs a standing gate defends (06-01-T3.matrix.txt)

Method: `git archive HEAD` of the source trees into a scratch directory under the system temp directory; the unmutated control passed the standing gate and all four owning suites first (`CONTROL_RESULT PASS`); each target occurred exactly once and each mutant compiled; the scratch copy was removed. Standing gate = `tools/test_bench_gate.py` (the `bench-gate` row of `tools/verify_spp.py`).

F2 note: the plan's five archive paths were not enough for a passing control (the first matrix run had a failing control and five NOT_DISCRIMINATING verdicts; it was not committed and the saved record is the corrected run, which prints the added paths on its `ADDED_PATHS` line). Added read-only inputs: `hooks`, `tests`, `vault/specs`, and the Phase 5 inventory baseline JSON. No mutant is written to any of them except the five owner files.

| Mutant | Owner (phase) | Condition inverted | Standing gate | Owning suite | Verdict |
|--------|---------------|--------------------|---------------|--------------|---------|
| MX1 | `tools/bench_all.py` (4, pressure judge) | `elif pressure is not None and pressure[0] != PRESSURE_GREEN:` -> `elif False:` | exit 1, `V-BENCH-INTEGRITY-SUITE-WIRED` | exit 1, `V-BENCHINT-RED-RUN-INCONCLUSIVE` | ENFORCED |
| MX2 | `tools/resource_admission.py` (4, reader) | `count > ceiling` -> `count >= ceiling` | exit 1, `V-BENCH-PRESSURE-SUITE-WIRED` | exit 1, `V-PRESS-TRACER-COUNT-OVER-IS-RED` | ENFORCED |
| MX3 | `tools/bench_all.py` (2, integrity) | `or v.get("met_target") is False` removed from `verdicts_fail` | exit 1, `V-BENCH-INTEGRITY-SUITE-WIRED` | exit 1, `V-BENCHINT-EXIT-FROM-VERDICTS` | ENFORCED |
| MX4 | `modules/capability_runtime/construction_metrology.py` (3) | `FAILED` dropped from `CENSORED_STATES` | exit 0 | exit 1, `V-METRO-CONTRACT-MATCHES-CODE` | OWN_SUITE_ONLY |
| MX5 | `tools/hook_critical_path_audit.py` (5) | `if b.get(flag) and not c.get(flag):` -> `... and c.get(flag):` (FLAG_WEAKENED) | exit 0 | exit 1, `V-CRIT-GUARD-CONTROL-IDENTICAL` | OWN_SUITE_ONLY |

Footer: `MATRIX: ENFORCED=3 OWN_SUITE_ONLY=2 SURVIVED_ALL=0 NOT_DISCRIMINATING=0`.

Consequences, per verdict:
- **Phase 2 and Phase 4 (MX1, MX2, MX3): inherited by a standing gate.** If the fix is lost, the `bench-gate` row of `tools/verify_spp.py` fails, because that row runs `test_bench_integrity.py` and `test_resource_pressure.py` and rejects a non-green suite (and its own decoys prove it can reject).
- **Phase 3 and Phase 5 (MX4, MX5): inherited only by a command someone must run.** If the censoring set or the FLAG_WEAKENED rule is broken, the standing gate stays green; only `tools/test_construction_metrology.py` and `tools/test_hook_critical_path.py` (run with `-I`) fail, and nothing standing runs them. This matches the planner's expectation in 06-CONTEXT F6, but it is recorded here from the run, not assumed.
- **No mutant survived all suites**: no test gap was found among these five. Five mutants, one per owner, is a spot check; it does not prove every condition in those owners is defended.

## 3. Whether anything runs the standing gate on a schedule

One grep (list argv, file names only) over `hooks/`, `scripts/`, `tools/` and the install scripts: `hooks/` 0 files, `scripts/` 0 files (it holds only `restart-claude.ps1`), `tools/` 33 files mention `verify_spp.py` (verifiers, test fixtures and standards-append scripts). The two files that mention both `verify_spp` and cron text (`tools/verify_monitoring.py`, `tools/_glob_standards_append.py`) are a probe and a documentation append; the probe asserts `--daemon` only prints crontab and Task Scheduler instructions and never installs a job. **No scheduler found in the repo. UNKNOWN whether the laptop or any cron runs `verify_spp.py`.** "Inherited by the standing gate" therefore means "fails when someone runs the `bench-gate` row", not "runs automatically".

## 4. What this does not show

- Whether anything runs the `bench-gate` row on a schedule (section 3: UNKNOWN).
- Every laptop behaviour. This is GEX44 only; zero items here are laptop-judged. The laptop-only items (LP-xx) are untouched by this plan.
- Wall-clock effect of the fixes on creation speed: not measured here.
- Whether the other manifest suites (`a5_u6`, `arm_preflight`, `gsd_mission_*`, `hook_boundary`) are defended by a standing gate: no mutants were planted in their owners.
- The s9 red-team (111/114) remains UNJUDGED.
- Timing evidence is n=1 per suite per session and varies with host load (see the decision below).

## 5. OWNER DECISION NEEDED (11): wire the Phase 3 and Phase 5 suites into a standing gate?

The matrix shows two proofs (Phase 3 censoring, Phase 5 FLAG_WEAKENED) that no standing gate defends. Wiring `test_construction_metrology.py` and `test_hook_critical_path.py` into `tools/test_bench_gate.py` would put them inside the `bench-gate` row, whose budget is 30 s. Measured suite costs: planning session `test_bench_gate.py` 1.8 s, `test_construction_metrology.py` 10.4 s, `test_hook_critical_path.py` about 34 s (Phase 5 record); this plan's manifest run (one run each, a different load) read 0.8 s, 3.3 s and 10.0 s. The two sets of readings disagree by a factor of three, so whether the 34 s suite fits inside 30 s is not settled by either set; with the planning-session numbers it does not.

Pick (unattended, reversible): leave unwired; the two suites are rows in the manifest and are in the HANDOFF re-run command. Reversal: add a `V-BENCH-<NAME>-SUITE-WIRED` gate with a negative control, as Phases 2 and 4 did, after the Owner decides the budget.
