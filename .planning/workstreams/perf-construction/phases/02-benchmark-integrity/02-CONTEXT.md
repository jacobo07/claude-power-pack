# Phase 2: Benchmark integrity - Context

**Gathered:** 2026-11-22 (unattended; no discuss step; decisions below are the planner's, recorded for traceability)
**Status:** Ready for planning
**Plane:** GEX44 (Linux, Python 3.12.3, stdlib only). Windows behaviour is LAPTOP-ONLY and is recorded as such, never asserted.

<domain>
## Phase Boundary

`tools/bench_all.py` and `tools/verify_bench_all.py` (the existing owners; EXTEND, no new owner) must stop reporting success they did not earn. Scope is exactly the P-ids Phase 1 judged CONFIRMED_ACTIVE or PARTIALLY_FIXED: **P01, P03, P04, P06** (01-EVIDENCE.md). Nothing else is in scope.

Requirement: PERF-02 (benchmark integrity defects fixed in owners with falsifying tests).

Evidence base (the research for this phase; research step skipped): `01-EVIDENCE.md`, `01-VERIFICATION.md`, `vault/audits/perf_campaign_w0_reality.md`, and the owner code read at HEAD 1ce2ef59.

Pre-fix facts the plans cite (all re-verified at HEAD 1ce2ef59):
- P01: `tools/bench_all.py:719` is `rc = 0 if (not errors and not regressions) else 1`; `at_target` is only counted. The gate `tools/verify_bench_all.py` judges 8 names against `QUICK_TARGETS x BAND(1.5)`, looser than the absolute `TARGETS` (ceps_record_ms 400 vs 25).
- P03: nine bench sites record elapsed ms whatever the exit code (uqf_scan, verify_spp, pytest, tco_gate, tis_report, osa_dispatcher, monitoring, session_hub_direct, vgate suites); six sites guard some failures (session_start, jit_cold_start, proactive_dispatch, anti_patterns, ceps_record, never_again). Live witness on this host: `bench_pytest()` returns `pytest_total_ms: 19.9, pytest_rc: 1` because pytest is not installed, a 19.9 ms "pass" against target 8000.
- P04: `verify_bench_all.py:153-158` `best = min(vals)` alone confirms; the only label is "min of N samples"; no percentiles.
- P06: baseline is `history[-1]` whatever its mode (`bench_all.py:649-650`); ledger entries (688-695) carry no host state; the `quick` flag is written and never used for matching.

Baseline of the existing gates, taken at HEAD 1ce2ef59 on this host before any edit:
- `python3 tools/test_bench_gate.py` -> `BENCH_GATE_PASS=13/13`, exit 0.
- `python3 tools/test_ram_optimization.py` -> `RAM_PASS=10/10`, exit 0.
- `python3 tools/test_git_invocation.py` -> `GIT_INVOCATION_PASS=6/7`, exit 1. The one failure, V-GITINV-NO-GROWTH, lists 14 pre-existing unfrozen offenders (none are this phase's files). This is the baseline, not a regression: the Phase 2 requirement is that the failing set does not change and V-GITINV-NO-STALE-EXEMPTION stays PASS (it requires `tools/bench_all.py` to REMAIN a bare-git offender).
</domain>

<decisions>
## Implementation Decisions (locked for the executors)

### P01 - exit contract
- **D-01:** The absolute-target exit lives in `bench_all.py`. `main` returns non-zero when an instrument errored, OR a primary metric (a key of `TARGETS`) has `met_target` False, OR a regression is True. `verify_bench_all` keeps its documented band contract (`BAND` 1.5 x `QUICK_TARGETS`), which four existing V-BENCH gates pin (for example tis_report 268 admitted); the gate only REPORTS absolute misses that sit inside the band, as an extra informational line, and its exit code is unchanged. Unselected benchmarks (for example everything outside `--quick`) produce no verdict and are never counted as met. `ram_footprint_mb` is exempt from `met_target` when `ram_scope` is not `"pp"` (a host-wide reading is unattributable, see the comment above `_PS_RAM`): `met_target` None, `evidence_sufficient` False, printed as UNJUDGED. The per-benchmark progress tag (OBS-01: always OK because `TARGETS.get(name)` looks up a benchmark name in a metric table) is fixed in the same plan because it is the console form of the same verdict.

### P04 - floor, p50, p95
- **D-02:** The gate's pass/fail stays floor-based (min). Existing gates pin it (a p50 of 1008 and 194 would break V-BENCH-RETRY-ABSORBS-NOISE). The floor gets its honest label ("potential floor: min of the valid samples; additive spawn noise can only raise a sample"), and p50 and p95 are computed and reported next to it, with an advisory `typical_within_band`. With fewer than 3 valid samples the typical verdict prints UNJUDGED (UNKNOWN is never PASS). Pure helpers `percentile` (linear interpolation, None on empty, never 0) and `summarize`.

### P03 - FAILED/TIMED_OUT is never fast
- **D-03 (bench_all side):** A per-benchmark `COMPLETED_RCS` table says which exit codes are verdicts rather than failures: session_start (0, 1) and monitoring (0, 1); every other benchmark and each vgate suite (0,). One shared classifier returns None or a reason: rc -1 is TIMED_OUT; rc -2 or -3 is FAILED (spawn); rc outside `COMPLETED_RCS` is FAILED; stderr containing "Traceback (most recent call last)" or "No module named" is CRASHED even when rc is in the set. A failed sample returns only `<name>_error` with the reason and the elapsed time, never a primary `_ms` value; `main` therefore records an error, exits 1, and the gate sees the metric MISSING. vgate: any FAILED/TIMED_OUT/CRASHED suite sets `vgate_error` and keeps the detail fields. This is a deliberate behaviour change (a verify_spp, pytest or vgate run with failures now errors instead of reporting a time); the SUMMARY of 02-01 documents it.
- **D-04 (gate side):** `sample()` is unchanged. The stop-on-failed-retry behaviour stays (the retry budget is 3 x 45 s inside a 150 s row), but a failed attempt is no longer invisible: the report states `attempted / valid / failed`, marks the confirmation UNCONFIRMED, and exit stays 1. `evaluate()` tolerates `None` entries among the retry samples (today a leading `None` makes it ignore every later sample). A pure `judge(attempts)` wraps `evaluate` and adds floor/p50/p95/n.

### P06 - host-state-matched window
- **D-05:** `HOST_SCHEMA = 1`. A never-raising `read_host_state()` records `{schema, host, os, cpu_count, available_mb, available_source, load1}` per ledger entry. `available_mb` comes from `tools/resource_admission.read_available_mb` (loaded by file path; no second /proc/meminfo parser); None when unreadable, never 0. `load1` is `os.getloadavg()[0]` or None. No `os.environ` capture. Process counting belongs to Phase 4 and is NOT added. A matching bucket is (host, os, cpu_count, memory bucket via `MEM_EDGES_MB = (1000, 3000, 8000)`, load-per-cpu bucket via `LOAD_EDGES = (0.5, 1.0)` or "na"). Entries without host_state, or with unreadable memory, never match. `window_for(history, quick, host_state, n)` requires the same `quick` flag AND the same bucket, takes the last `WINDOW_N = 7`, and returns the excluded counts (`no_host_state`, `other_mode`, `other_host_state`). `baseline_from_window` gives a per-metric median and n. `MIN_WINDOW = 3`: below it `regressed` is None and `evidence_sufficient` False. `detect_regressions(curr, prev)` keeps its signature and `REGRESSION_PCT` stays 1.15; it is fed the window medians restricted to sufficient metrics. The legacy `history[-1]` path is removed. `--compare` shows deltas against the matched baseline or says "no host-state-matched baseline". Legacy ledger entries (13 tracked, none with host_state) never match, so regression prints UNJUDGED until three matched entries accumulate; it is never silently "no regressions".

### Verdict model
- **D-06:** `judge_metrics` yields four verdicts per primary metric of every selected benchmark. `instrument_ran`: a numeric value, no `_error`, completed rc. `met_target`: value <= `TARGETS[metric]` when instrument_ran, else None. `regressed`: True/False/None from the matched window. `evidence_sufficient`: instrument_ran AND matched-window n >= `MIN_WINDOW`. Each carries a reason string, and `verdicts` is stored in the ledger entry and the `--json` output. Exit code: 1 on any instrument_ran False, met_target False or regressed True. Insufficient evidence alone does not force a non-zero exit but is always printed as UNJUDGED with its n.

### Process and test discipline
- **D-07:** Every fix task is test-first. The test file is written, run against pristine owner code, and its FAIL output recorded verbatim (header carries `git rev-parse --short HEAD` and a pristine check of the owner file); then the fix lands and the same command's PASS output is recorded. RED and GREEN are separate commits, each by pathspec. Tests are plain stdlib scripts in the repo's `_ok`/`_fail` style with an `EXPECTED_GATES` count; pytest is NOT installed on this host and must not be installed. New API is reached through `getattr` so a pre-fix run prints FAIL rather than crashing on import. Tests never touch the tracked `vault/benchmarks/ledger.json`: they patch `bench_all.LEDGER_PATH` to a temp file and patch `ALL_BENCHES`. Executors commit by pathspec (`git add -- <paths>`, `git commit -F <msgfile> -- <paths>`), never push.
- **D-08:** Wiring without a new owner or a `verify_spp.py` edit: `tools/test_bench_integrity.py` is run as a subprocess by one gate inside `tools/test_bench_gate.py`, which is already the verify_spp row "bench-gate" (30 s budget), so the suite must be pure and fast.
- **D-09:** `tools/bench_all.py` must keep its bare `git` call in `get_head_commit` and gain no new bare `git` call; `tools/test_bench_integrity.py` must call no `git` at all (V-GITINV-NO-STALE-EXEMPTION and V-GITINV-NO-GROWTH).
- **D-10:** `ram_footprint` keeps its function name `bench_ram_footprint` (imported by `tools/test_ram_optimization.py`).

### Claude's Discretion
Names of private helpers, exact message wording, and the internal layout of the temp-ledger fixtures are the executor's choice inside the contracts above.
</decisions>

<carried>
## Out of scope (recorded, not planned)

- **P07: BLOCKED-ON-ORIGIN-AUDIT.** The id is UNDEFINED on this host (the origin audit main@ed9de300 is absent from the clone). No task touches it. 33 other P-ids are UNKNOWN for the same reason; P16 and P17 belong to Phase 4.
- OBS-02 (a corrupt ledger silently disables regression detection; the write is not atomic), OBS-03 (the gate has a write side effect and ignores bench_all's rc), OBS-05 (two target tables), OBS-06 (no gated RAM figure on a Linux host), OBS-07 (stale wiki page). They are carried with their evidence in 01-EVIDENCE.md; none is a Phase 2 success criterion. OBS-04 (a metric that errored last run is exempt from regression) is resolved as a consequence of D-05, not as separate work.
- The RED host class and process counting (Phase 4).
- `verify_spp.py` row definitions and the `vault/benchmarks/ledger.json` content (the tracked ledger is never rewritten here).

## LAPTOP-ONLY / UNJUDGED
- **LP-03:** Windows host-state reading (`read_available_mb` through GlobalMemoryStatusEx, `os.getloadavg` absent on Windows so `load1` None, bucket stability) is not observable on this host. Procedure for the laptop: run `python tools/bench_all.py --quick --label lp03` twice back to back on an idle laptop and compare the `host_state` buckets of the two ledger entries. Falsifier: the two buckets differ on an idle machine (the buckets are then too narrow to ever build a window). Recorded in 02-EVIDENCE.md as UNJUDGED.

## Open question for the Owner (non-blocking)
- Should `verify_bench_all` itself FAIL on an absolute-target miss inside the band? That is a policy change to `BAND`/`QUICK_TARGETS`, which were calibrated on the laptop (T-WIN-AV-001 spawn variance). D-01 leaves the gate's exit untouched and reports the miss; bench_all's own exit now carries the absolute contract.
- Should a vgate suite that exits 1 (a real assertion failure, not a crash) make `vgate_total_ms` an instrument error (D-03 says yes: a failing suite exits early and shortens the total) or only increment `vgate_fails`?
</carried>

<canonical_refs>
## Canonical References
- `.planning/workstreams/perf-construction/ROADMAP.md` (Phase 2 success criteria), `REQUIREMENTS.md` (PERF-02), `STATE.md`
- `.planning/workstreams/perf-construction/phases/01-reality-and-ownership/01-EVIDENCE.md` (P-table, OBS-01..07), `01-VERIFICATION.md`
- `vault/audits/perf_campaign_w0_reality.md`
- `tools/bench_all.py`, `tools/verify_bench_all.py`, `tools/test_bench_gate.py`, `tools/resource_admission.py`, `tools/verify_spp.py` (rows benchmarks-ok line 600, bench-gate line 612), `tools/test_ram_optimization.py`, `tools/test_git_invocation.py`
</canonical_refs>

<deferred>
## Deferred Ideas
None added by this phase; carried items above keep their Phase 1 owners.
</deferred>
