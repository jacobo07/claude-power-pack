# Phase 2 Evidence: Benchmark integrity

Plane: GEX44 (host `kobicraft-gex44`, linux, 20 CPUs), unattended executors, 2026-11-22. Pre-fix base for every citation below: commit 39f59e28 (the head recorded in `records/02-01-T1.red.txt`); line numbers were re-read at that commit with `git show`. Nothing here was run on the laptop and nothing was pushed.

## 1. Scope, baseline and plane

Scope is exactly P01, P03, P04 and P06 (01-EVIDENCE.md: CONFIRMED_ACTIVE or PARTIALLY_FIXED) in the two existing owners `tools/bench_all.py` and `tools/verify_bench_all.py`; no new owner module. P07 is out of scope (section 3).

Baselines of the existing gates, taken before any edit (02-CONTEXT.md, HEAD 1ce2ef59): `tools/test_bench_gate.py` 13/13 exit 0; `tools/test_ram_optimization.py` 10/10 exit 0; `tools/test_git_invocation.py` 6/7 exit 1 with one failing gate, V-GITINV-NO-GROWTH, listing 14 unfrozen offenders, and V-GITINV-NO-STALE-EXEMPTION PASS.

The tracked ledger `vault/benchmarks/ledger.json` was never written: every gate and the live smoke use a temp ledger, and `git status --porcelain` lists nothing under `vault/`.

## 2. Defects fixed, with falsifying records

Every red record was taken with the owner file pristine (`# pristine: ...=yes`, re-verified with `record_run.py --verify ... --expect fail --pristine-required`) and exits 1; every green record exits 0.

| P-id | Pre-fix evidence (at commit 39f59e28) | Fix (functions, commits) | Red record, exit | Green record, exit |
|------|---------------------------------------|--------------------------|------------------|--------------------|
| P01 | `tools/bench_all.py:719` `rc = 0 if (not errors and not regressions) else 1`: an absolute `TARGETS` miss never changed rc; the per-benchmark tag looked up a benchmark name in a metric table and was always OK | `target_misses`, `_primary_tag`, `METRIC_OWNER`, host-scope RAM UNJUDGED, commit 729bf021 (RED) and commit 0ef7239f (GREEN); then `judge_metrics`, `verdicts_fail` and the verdict-derived rc, commit bd717662 (RED) and commit e92562d1 (GREEN) | `records/02-01-T3.red.txt` exit 1 (24/28); `records/02-03-T2.red.txt` exit 1 | `records/02-01-T3.green.txt` exit 0 (28/28); `records/02-03-T2.green.txt` exit 0 (41/41) |
| P03 | nine timed sites recorded elapsed ms whatever the exit code (`bench_pytest` at `tools/bench_all.py:169`); live witness: `pytest_total_ms: 19.9, pytest_rc: 1` against target 8000 because pytest is not installed. Gate side: a failed retry was dropped silently (`tools/verify_bench_all.py`) | bench side: `_sample_failure` classifier at all 15 sites, vgate aggregate, commit d76e8a9f (RED), commit 4e7b6d0d, commit b9611b73 (RED) and commit dcd6dfdc (GREEN); gate side: failed-retry accounting, commit e1bc38a8 (RED) and commit 1a2ba1fc (GREEN) | `records/02-01-T1.red.txt` exit 1; `records/02-01-T2.red.txt` exit 1 (5/21); `records/02-02-T2.red.txt` exit 1 | `records/02-01-T1.green.txt` exit 0; `records/02-01-T2.green.txt` exit 0 (21/21); `records/02-02-T2.green.txt` exit 0 |
| P04 | `tools/verify_bench_all.py:156` `best = min(vals)` alone confirmed an over-band metric; the only label was "min of N samples"; no percentile existed | `percentile`, `summarize`, labelled potential floor with p50, p95 and n (UNJUDGED below 3 valid samples), absolute-target notes inside the band, commit 31ea3e98 (RED), commit c54590c2, commit 891df83f (RED) and commit 5fb64d7f (GREEN) | `records/02-02-T1.red.txt` exit 1; `records/02-02-T3.red.txt` exit 1 | `records/02-02-T1.green.txt` exit 0; `records/02-02-T3.green.txt` exit 0 |
| P06 | `tools/bench_all.py:650` `prev_results = history[-1].get("results")` whatever its mode; entry written at `tools/bench_all.py:692` carried `quick` but no host state and `quick` was never used for matching | `HOST_SCHEMA`, `read_host_state`, `host_bucket`, `window_for`, `baseline_from_window`, `judge_metrics` (`MIN_WINDOW` 3, `WINDOW_N` 7), ledger_schema 2, `--compare` against the matched median; commit 00f6c7af (RED), commit 8893f2b8 (GREEN), commit bd717662 (RED) and commit e92562d1 (GREEN) | `records/02-03-T1.red.txt` exit 1 (both decoy gates FAIL); `records/02-03-T2.red.txt` exit 1 | `records/02-03-T1.green.txt` exit 0; `records/02-03-T2.green.txt` exit 0 |

Wiring (D-08): commit 07caeb3a adds V-BENCH-INTEGRITY-SUITE-WIRED to `tools/test_bench_gate.py` (23 gates), which `verify_spp` already runs as row bench-gate; the gate runs `tools/test_bench_integrity.py` and carries a negative control (a script that exits 1 after printing `BENCHINT_PASS=3/3`, one printing `2/3` and one silent script are all rejected). Record: `records/02-03-T3.wiring.txt` exit 0. No RED run exists for this gate by design; its falsifier is the negative control inside it. The whole `test_bench_gate.py` run takes 0.4 s, inside the 30 s row budget.

Gate counts in `tools/test_bench_integrity.py`: 28 after plan 02-01, 34 after the P06 tracer, 41 after the four-verdict task.

## 3. P07

| P07 | BLOCKED-ON-ORIGIN-AUDIT | No work performed. The id is UNDEFINED on this host: the origin audit (main@ed9de300) is absent from the clone and no source describes P07 (01-EVIDENCE.md searches S-06 to S-10). Not treated as a fact and not planned. | - | - |

## 4. Existing gates (this plan's final run)

Record: `records/02-03-T3.gates.txt`. Run from the worktree at HEAD 07caeb3a.

| Command | Result | Exit | Baseline |
|---------|--------|------|----------|
| `python3 tools/test_bench_integrity.py` | BENCHINT_PASS=41/41 | 0 | new in this phase |
| `python3 tools/test_bench_gate.py` | BENCH_GATE_PASS=23/23 | 0 | 13/13 (22 after plan 02-02, 23 after the wiring gate) |
| `python3 tools/test_ram_optimization.py` | RAM_PASS=10/10 | 0 | 10/10 |
| `python3 tools/test_git_invocation.py` | GIT_INVOCATION_PASS=6/7; only V-GITINV-NO-GROWTH fails with the same 14 offenders; V-GITINV-NO-STALE-EXEMPTION OK; `[frozen] tools/bench_all.py` still present (bare `git` call kept, line 1148) | 1 | 6/7 exit 1, same failing set |

`tools/verify_bench_all.py` and `tools/verify_spp.py` were deliberately NOT run live: both append to the tracked ledger by running bench_all. Their behaviour is covered by the temp-ledger gates above.

## 5. Live smoke on this host (temp ledger, tracked ledger untouched)

Fixture: `live_smoke.py` (stdlib, `python3 -I`); runs `main` twice on the three real benchmarks pytest, uqf_scan and proactive_dispatch against a temp ledger and refuses to run if the temp path equals the tracked one.

- Before (pre-fix code from commit 39f59e28), `records/02-03-T3.smoke-before.txt`: pytest "completed" in 16 to 25 ms tagged `[OK]` although `pytest_rc` is 1 (the module is not installed), `AT TARGET: 3/3`, exit 0 on both calls, entry without `host_state` or verdicts. That is the P03 and P06 defect on the real host.
- After (working tree), `records/02-03-T3.smoke-after.txt`: pytest is `ERROR` ("No module named pytest"), exit 1 on both calls; the second entry carries `ledger_schema` 2, `host_state` (host kobicraft-gex44, 20 CPUs, 53089 MB available from /proc/meminfo, load1 13.5) and four verdicts per metric: pytest `instrument_ran` False, uqf_scan and proactive_dispatch `met_target` True with `regressed` None and `evidence_sufficient` False (n=1 matched value, fewer than 3), printed as UNJUDGED. The second call matched exactly one entry (the first call's), which confirms the matching rule on live data.

## 6. LAPTOP-ONLY items

LP-03 (UNJUDGED): Windows host-state reading (`read_available_mb` through GlobalMemoryStatusEx, `load1` None because `os.getloadavg` does not exist on Windows, bucket stability) is not observable on this host. Procedure for the laptop: run `python tools/bench_all.py --quick --label lp03` twice back to back on an idle laptop and compare the `host_state` buckets of the two ledger entries. Falsifier: the two buckets differ on an idle machine (the buckets are then too narrow to ever build a window). No claim is made about the laptop.

## 7. Carried observations and open Owner questions

- OBS-01 (per-benchmark tag always OK): fixed in plan 02-01 (`_primary_tag`).
- OBS-04 (a metric that errored last run was exempt from regression): resolved as a consequence of the window rule; an entry whose benchmark errored contributes nothing to the median (gate V-BENCHINT-ERRORED-ENTRY-EXCLUDED-FROM-WINDOW).
- OBS-02 (a corrupt ledger silently disables regression detection, non-atomic write), OBS-03 (the gate has a write side effect and ignores bench_all's rc), OBS-05 (two target tables), OBS-06 (no gated RAM figure on a Linux host), OBS-07 (stale wiki page): unchanged and owned elsewhere.
- Cosmetic, unfixed: the console verdict line prints `(n=K)` twice when the reason already contains the count.
- Open Owner question 1: should `verify_bench_all` itself FAIL on an absolute-target miss inside the band? A policy change to `BAND` and `QUICK_TARGETS` (laptop-calibrated); the gate currently only reports such misses.
- Open Owner question 2: should a vgate suite that exits 1 make `vgate_total_ms` an instrument error (implemented, per D-03) or only increment `vgate_fails`?

## 8. Verdict

ROADMAP Phase 2 success criteria:

1. Four verdicts per metric; a FAILED or TIMED_OUT sample never counts as fast (P03); non-zero exit on an absolute-target miss (P01): MET for the code paths, proven by `records/02-01-T3.green.txt`, `records/02-03-T2.green.txt` and the live smoke. Caveat kept visible: on this host regression verdicts are UNJUDGED until three host-state-matched entries exist; they are proven only by temp-ledger gates, not by live history.
2. `min` kept as a labelled potential floor with p50 and p95 (P04); regression compares against a host-state-matched window (P06): MET, `records/02-02-T1.green.txt` and `records/02-03-T1.green.txt`. Laptop behaviour of the window is UNJUDGED (LP-03).
3. Each fix has a test that fails on the pre-fix code and passes after, recorded verbatim: MET, six red records from plans 02-01 and 02-02 and two from this plan, all verified with `--pristine-required`; the wiring gate is covered by its negative control instead of a red run.
4. Existing gates of the touched owners still pass: MET against the baselines in section 4 (the 6/7 git-invocation result is the unchanged baseline, not a regression).

Not established: P07 (BLOCKED-ON-ORIGIN-AUDIT), LP-03 (UNJUDGED), live regression verdicts on this host (UNJUDGED, n below 3), both Owner questions.
