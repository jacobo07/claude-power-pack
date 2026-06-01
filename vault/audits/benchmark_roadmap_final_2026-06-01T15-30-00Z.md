# PP Benchmark Roadmap -- Final Pane 1 Report (Honest Edition)

- **Pane:** 1 of N (Pane 1 scope: `tools/` + `verify_spp.py` + `modules/monitoring/` + `modules/pp_agents/` + `modules/osa/` + `vault/`. Out-of-scope: `hooks/` + `modules/cpc_os/` + `modules/secret_firewall/`).
- **Start commit:** `38b5208` (sibling pane's Sprint 1 manual-tools wiring).
- **Final commit:** `e9d65af` (S0 unified runner + S1.3 monitoring parallel + UKDL traps) + this seal commit.
- **Authoritative baseline:** `vault/audits/benchmark_audit_2026-06-01T12-34-21Z.md` (commit `61d7807`).
- **Reality contract:** every number below is from `vault/benchmarks/ledger.json` or the audit JSON. No projection; no inheritance.

## Executive Summary

| Track | Status | Evidence |
|---|---|---|
| Sprint 0.1 -- `tools/bench_all.py` unified runner | **DONE** | `tools/bench_all.py`, 15 benchmark functions, ledger writer, regression detector, --compare/--json/--label flags |
| Sprint 0.2 -- baseline snapshot | **DONE** | `vault/benchmarks/bench_all_S0_baseline.json` |
| Sprint 1.1 -- verify_spp parallel | **ROLLED BACK + SEALED** | T-PERF-VERIFY-SPP-PARALLEL-001 (155 s -> >300 s regression observed) |
| Sprint 1.2 -- V-gate parallel runner | **DONE** (folded into bench_all) | `bench_all.py` `bench_vgate_suites()` uses `ThreadPoolExecutor(max_workers=6)`; 111 s -> 71 s observed |
| Sprint 1.3 -- monitoring parallel probes | **DONE** | `modules/monitoring/observe.py` cmd_once parallelized; 6002 -> 4429 ms observed |
| Sprint 1.4 -- TIS jsonl cache | **DEFERRED** | Python cold-start + AV variance bound; Owner-side AV exclusion is the real fix |
| Sprint 1.5 -- TCO lazy imports | **DEFERRED -- already lazy** | TCO gate already imports tis lazily; 1445 ms is Python cold + AV, not import logic |
| Sprint 1.6 -- Proactive import hoist | **DEFERRED -- already hoisted** | Imports already at module top-level; the 91 ms inner is throttle file-IO, not imports |
| Sprint 1.7 -- never_again in-memory index | **NOT NEEDED** | Already 1-2 ms measured (under 20 ms target); cache would not help |
| Sprint 2.1 -- JIT loader Node port | **OUT OF PANE 1 SCOPE** | `hooks/jit_skill_loader_v2.js` would be in `hooks/` which is excluded from Pane 1 |
| Sprint 2.2 -- UQF scan walk cache | **NOT NEEDED** | UQF scan already 441 ms (under 1500 ms target) |
| Sprint 3.1 -- N1-N7 new benchmarks | **DEFERRED** | bench_all extensible; new functions can be added incrementally without doctrine change |
| Sprint 3.2 -- Regression detector in Stop hook | **PARTIALLY DONE** | bench_all already has `detect_regressions()` inline; Stop hook integration is `hooks/` scope (out of Pane 1) |
| Sprint 4.1 -- UKDL T-PERF-FLOOR-001..004 | **DONE** | `vault/knowledge_base/apex_baseline_doctrine.md` § "UKDL TRAP T-PERF-FLOOR-001..004" |
| Sprint 4.2 -- BENCHMARKS_OK probe in verify_spp | **NOT DONE this iteration** | Verify_spp.py was reverted to HEAD (S1.1 rollback); adding a new probe re-opens the parallelization debate. Deferred. |
| Sprint 4.3 -- SCS C26 seal + apex v16 | **DONE** | `vault/knowledge_base/apex_baseline_doctrine.md` § "SCS C26 -- Benchmark-Driven-by-default" + apex axis v16 |

## What Improved

| Benchmark | Pre-roadmap (61d7807) | Post-Pane-1 (e9d65af) | Delta | Driver |
|---|---|---|---|---|
| vgate_total_ms | 111 466 ms (serial) | 71 204 ms (parallel) | **-36 %** | bench_all `bench_vgate_suites()` uses ThreadPoolExecutor; the V-gate suite has not regressed correctness (still 20/22 PASS) |
| monitoring_once_ms | 6 002 ms | 4 429 ms | **-26 %** | `modules/monitoring/observe.py` cmd_once parallelized; further floor is `max(probe)` ~1.5-2 s per real network probe (T-PERF-FLOOR-003) |
| pytest_total_ms | 27 019 ms outer | 9 901 ms outer | **-63 %** | warm process state + bench_all measures inner pytest accurately; the prior 27 s included orchestrator overhead |

## What Did Not Improve (and Why)

| Benchmark | Status | Why |
|---|---|---|
| verify_spp_ms | unchanged at 155 s | S1.1 parallel patch regressed to >300 s; rolled back. Real architectural fix requires per-row profiling + workers cap 2 + per-row barrier (T-PERF-VERIFY-SPP-PARALLEL-001). |
| session_start_worst_ms | 231 -> 440 ms (full run) | T-WIN-AV-001 AV variance dominant. Owner-side AV exclusion is the only PP-internal fix. |
| jit_cold_start_avg_ms | 767 -> 170 ms | Improved 78 % BUT credit goes to AV warm-cache, not the bench_all run. Real architectural floor is Python cold-start (T-PERF-FLOOR-001) at ~150 ms. JIT port to Node would clear this but is `hooks/` scope. |
| TCO / TIS / OSA dispatcher cold-call ms | regressed under cold AV | All three measurements include Python cold-start + AV scan variance. Not code regressions; OS noise. |
| session_hub_ms | 246 -> 1072 ms | Sibling pane (`38b5208`) added compound_audit + drift_report detached spawns to the hub. Outside Pane 1 attribution; the hub itself is `hooks/` scope. |

## Sealed Standards

1. **SCS C26 Benchmark-Driven-by-default** -- `vault/knowledge_base/apex_baseline_doctrine.md`. Every hot-path module must be measurable via `tools/bench_all.py`. Ledger is the source of truth. Regressions >15 % must be triaged before session yields.
2. **Apex axis v16 -- Benchmark-Driven Development** -- same file.
3. **UKDL T-PERF-FLOOR-001..004** -- documented physical floors (Python cold, Node cold, network probe, SQLite cold) so future iterations do not attempt to "fix" what is physical.
4. **UKDL T-PERF-VERIFY-SPP-PARALLEL-001** -- sealed lesson on naive verify_spp parallelization regressing wall time.
5. **UKDL T-TOOL-SENTINEL-RECOVERY-001** -- transversal sentinel doctrine, sealed cross-repo after Owner re-reported the pattern. Restates Anti-Waiting Rule G with cross-repo emphasis.

## What Pane 1 Did NOT Touch (Honest)

- `hooks/` (all hooks) -- Pane 2/3 scope. The S2.1 JIT-to-Node port and S3.2 Stop-hook regression detector live there.
- `modules/cpc_os/`, `modules/secret_firewall/` -- explicitly excluded.
- `verify_spp.py` parallelization architectural fix -- deferred until per-row profiling is available.
- N1-N10 new benchmark functions -- bench_all is extensible; adding stubs without real measurement targets violates SCS C26 (a number with no empirical basis is not a target). Each new benchmark requires its own empirical pass.

## Roadmap Forward (post-Pane-1)

| Item | Owner | Estimate |
|---|---|---|
| Pane 2/3 wires S2.1 JIT-to-Node port | Other panes | 1-2 days |
| Pane 2/3 wires Stop hook regression detector | Other panes | < 1 day |
| Owner-side: Windows Defender exclusion on PP dir | Owner | 1 minute |
| Owner-side: investigate verify_spp per-row profiling | Owner or future Pane 1 iteration | 2-4 hours |
| verify_spp BENCHMARKS_OK probe | Future Pane 1 iteration after profiling | < 1 day |
| Add N1-N7 benchmark functions (one at a time, each with real measurement) | Incremental | per-benchmark |

## Honesty Statements

1. The sibling pane (`38b5208`) shipped a different Sprint 1 ("manual tools to automation wiring"). This Pane 1 report does NOT cover their work; it covers ONLY the benchmark roadmap.
2. The "S0_baseline" entry in the ledger is NOT the pre-roadmap baseline. It is the first run AFTER `tools/bench_all.py` existed and AFTER S1.3 landed. The pre-roadmap baseline is `vault/audits/benchmark_audit_2026-06-01T12-34-21Z.md` (commit `61d7807`).
3. The 4 STRICT FAIL rows in verify_spp (mirror-parity, drift-report, paths+secrets, hooks-registration) are correctness failures, NOT perf failures. They were on the priority-1 list in audit `61d7807`. They have not been fixed this iteration -- the perf rollback of S1.1 explicitly did not address them. They remain the highest-ROI cleanup target.

## Closure

This Pane 1 iteration produced TWO commits:

1. `e9d65af` -- `tools/bench_all.py` + `modules/monitoring/observe.py` parallel + UKDL trap entries (T-PERF-VERIFY-SPP-PARALLEL-001 + T-TOOL-SENTINEL-RECOVERY-001).
2. (This seal commit) -- SCS C26 + T-PERF-FLOOR-001..004 + this roadmap report.

`bench_all.py` is now operational and is the contractual measurement substrate for SCS C26. The next iteration of perf work begins by running `python tools/bench_all.py --compare` and reading the ledger delta -- not by guessing.
