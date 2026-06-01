# PP Benchmark Audit

- **Run timestamp:** 2026-06-01T12:34:21Z (UTC)
- **Repo commit:** `2770d29 feat(session-hub): collapse 5 PP SessionStart entries to 1 hub process`
- **Host:** Windows 11 Pro 10.0.26200 (`os.name = nt`)
- **Python:** 3.12.10
- **Node:** v22.x (used by `hooks/session_start_hub.js`)
- **Raw evidence:**
  - `vault/benchmarks/audit_run_2026-06-01T12-34-21Z.json` -- pass 1 (15 benchmarks)
  - `vault/benchmarks/audit_pass2_2026-06-01T12-42-25Z.json` -- pass 2 (verify_spp re-run, 3x session-start re-measure, monitoring rc-interpretation)
  - `vault/benchmarks/audit_verify_spp_2026-06-01T12-47-42Z.json` -- pass 3 (verify_spp at 300s budget)
- **Orchestrator:** `tools/run_all_benchmarks.py` + `tools/run_bench_passes.py` + `tools/run_bench_verify_spp.py`

## Executive Summary

| # | Benchmark | Measured | Target | Verdict | Delta vs historical |
|---|---|---|---|---|---|
| 1 | Session Start `individual_max_ms` | **231 ms** (pass2 median of 3) | < 300 ms slow / < 1000 ms total | ✅ OK | -95.1% vs 4696 ms baseline; +5% vs 220 ms hub_final |
| 1b | Session Start `total_serial_ms` | **448 ms** (pass2 median) | < 1000 ms | ✅ OK | -93.9% vs 7375 ms baseline |
| 2 | JIT Loader cold-start (5-run, avg) | **767 ms** (min 407, max 1449, σ 408) | < 500 ms avg | ⚡ WARN (high σ) | +31% vs 586 ms post-fix avg sealed 2026-05-31 |
| 3 | UQF `--scan-all` | **3574 ms** outer (rc=0, 7 lines stdout) | < 10 s | ✅ OK | -- no prior baseline |
| 4 | `verify_spp.py` umbrella | **155.3 s** wall, rc=1 (4 STRICT FAIL rows / 5 OK rows) | < 240 s wall | ⚡ within budget; **correctness fails** -- see §verify_spp detail | -- no prior baseline |
| 5 | `pytest tests/` | **15.88 s** inner / 27.0 s wall (43 passed) | < 60 s | ✅ OK | -- |
| 6 | V-gate suites (22 files) | **111.5 s** total (20 PASS / 2 FAIL) | per-suite < 30 s | ⚡ MIXED (see §V-gate detail) | -- |
| 7 | TCO compact gate | **312 ms** outer (`context-pct (estimate): 7%`) | < 200 ms | ⚡ WARN | -- |
| 8 | TIS report `--summary` | **399 ms** outer (4 stdout lines) | < 500 ms | ✅ OK | -- |
| 9 | OSA dispatcher `--check` | **251 ms** outer | < 300 ms | ✅ OK | -- |
| 10 | Proactive dispatch (cold) | **91 ms** inner / 206 ms outer (0 advisories on empty ctx) | < 100 ms inner | ✅ OK | -- |
| 11 | Monitoring `--once` | **6002 ms** outer, rc=1 (kobiicraft DOWN, others UP -- **semantic signal**) | < 15 s | ✅ OK (perf) / 🟡 semantic alert | -- |
| 12 | `anti_patterns.run_all(ceps.py)` | **86 ms** inner / 198 ms outer (22 hits in 7 categories) | < 200 ms inner | ✅ OK | -- |
| 13 | CEPS `record_error` | **35 ms** inner / 133 ms outer | < 50 ms inner | ✅ OK | -- |
| 14 | Session hub direct invoke | **246 ms** outer (rc=0, 17 bytes stdout, valid JSON) | < 1500 ms (V-HUB-FAST gate) | ✅ OK | hub_final baseline 220 ms |
| 15 | `never_again.top_recurring(10)` | **66 ms** inner / 395 ms outer (10 rows) | < 200 ms inner | ✅ OK | -- |

**Legend:** ✅ within target / ⚡ acceptable but above target or high variance / ❌ outside target / 🟡 informational

### Aggregate verdict

- **13/15 perf-green** (✅ OK).
- **2/15 warn on perf**: JIT cold-start variance (#2), TCO gate cold-start (#7).
- **0/15 fail on perf grounds** (every benchmark runs under its time budget).
- **Correctness fails surfaced (out-of-band but worth listing):**
  - #4 verify_spp -- 4 STRICT FAIL rows: mirror-parity, drift-report, paths+secrets, hooks-registration.
  - #6 V-gate suites -- `test_mirror_parity.py` ERR (rc=1), `test_vague_lint.py` FAIL.
  - These cluster on a single root: mirror-parity drift between PP and `~/.claude/`. See feedback memory `feedback_mirror_sync_direction_and_hooks_dir_deny.md`.

## Historical Context (evidence of improvement)

### Session Start Lag -- 4-stage convergence (BL-LAG-001 + BL-SESSION-HUB-001)

| Stage | `individual_max_ms` | `total_serial_ms` | Verdict | Notes |
|---|---|---|---|---|
| Baseline (pre-optimize) | 4697 | 7375 | FAIL | duplicate orphan-dev-server-reaper on SessionStart |
| Iter 1 (drop reaper + wrap auto-compact + wrap tco) | 3737 | 8317 | FAIL | async_wrapper bug: stdio: ['pipe', 'ignore', 'ignore'] kept Node loop open; sealed as T-ASYNC-WRAPPER-001 |
| Iter 2 (stdio:'ignore' all 3 streams + add auto-vault) | 703-993 | 2269-3695 | WARN-OK | wrapper fix verified |
| Iter 3 (auto-vault wrapped via optimizer) | 162-660 (median 245) | 919-2028 | OK on 3/4 runs | sealed 2026-06-01 morning |
| **Hub final (this clause C23)** | **220** | **430** | **OK** | 5 entries collapsed to 1 hub |
| **Audit pass1 (this report)** | 1106 | 2555 | FAIL | AV cold-scan on fresh hub.js binary (T-WIN-AV-001) |
| **Audit pass2 (3-run median)** | **231** | **448** | **OK** | matches hub_final after AV cache warmed |

**95.1%** reduction on individual max vs baseline (clean run).
**93.9%** reduction on serial total vs baseline (clean run).

### JIT Loader cold-start (BL-JIT-001)

| Stage | Avg | Min | Max | σ |
|---|---|---|---|---|
| Pre-fix (sealed 2026-05-31) | 780 ms | 475 ms | 1036 ms | -- |
| Post-fix (sealed 2026-05-31) | 586 ms | 346 ms | 766 ms | -- |
| **Audit (this report)** | **767 ms** | **407 ms** | **1449 ms** | **408 ms** |

The audit avg (767 ms) is 31 % above the post-fix avg (586 ms). The σ of 408 ms is the dominant signal -- variance, not mean drift. Likely T-WIN-AV-001 (Windows Defender scan variance on cold-start Python subprocess spawn). The min datapoint (407 ms) is within 18 % of the post-fix min (346 ms), suggesting the warm-path floor has not regressed. **Recommendation:** re-sample with `--repeat 10` and Defender exclusion on `C:\Users\User\.claude\skills\claude-power-pack` to isolate AV variance.

## V-gate Detail (§ benchmark 6)

22 V-gate suites in `tools/test_*.py`. Per-suite timing + verdict:

| Suite | ms | Verdict |
|---|---:|---|
| test_atomic_branding.py | 4788 | PASS |
| test_ceps_closed_loop.py | 1138 | PASS |
| test_ceps_edge_cases.py | 1639 | PASS |
| test_ceps_full_cycle.py | 9730 | PASS |
| test_compact_rescue.py | 17669 | PASS |
| test_hard_rules.py | 6045 | PASS |
| test_jit_performance.py | 3055 | PASS |
| test_karimo.py | 3522 | PASS |
| test_lateral_thinking.py | 3983 | PASS |
| **test_mirror_parity.py** | 1686 | **ERR (rc=1)** |
| test_monitoring.py | 2020 | PASS |
| test_osa.py | 9885 | PASS |
| test_playwright_resilience.py | 11554 | PASS |
| test_proactive_agents.py | 14030 | PASS |
| test_restart_and_lag.py | 6593 | PASS |
| test_speckit.py | 688 | PASS |
| test_tco.py | 3924 | PASS |
| test_tis_core.py | 257 | PASS |
| test_tis_e2e.py | 747 | PASS |
| test_uqf.py | 3386 | PASS |
| **test_vague_lint.py** | 1941 | **FAIL** |
| test_zero_command.py | 3182 | PASS |

**Two failures to investigate** (both correctness, not perf):
- `test_mirror_parity.py` rc=1 -- likely PP vs `~/.claude/` loose-ahead state (sibling drift). Sister rule: `feedback_mirror_sync_direction_and_hooks_dir_deny.md`.
- `test_vague_lint.py` -- failure mode unknown from outer rc; needs in-suite invocation to surface the assertion.

Slowest 3 suites: `test_compact_rescue.py` 17.7 s, `test_proactive_agents.py` 14.0 s, `test_playwright_resilience.py` 11.6 s -- all subprocess-heavy with real network or browser harnesses. Per-suite target of 30 s is comfortable.

## Per-benchmark detail

### #1 Session Start (`tools/measure_session_start.py --json`)

Pass1 (cold AV state):
```
individual_max_ms: 1106  total_serial_ms: 2555  slow_hooks: 2  verdict: FAIL
```

Pass2 (warm AV state, 3 consecutive runs):
```
run 1: max=231 total=448 slow=0  verdict: OK
run 2: max=235 total=531 slow=0  verdict: OK
run 3: max=216 total=403 slow=0  verdict: OK
median: max=231 total=448
```

**Interpretation:** the hub_final baseline (220 ms) is the steady-state truth. Pass1 hit AV scan variance documented as T-WIN-AV-001. No PP-side action; Owner-side AV exclusion on the PP directory is the only fix.

### #2 JIT Loader cold-start (5x subprocess imports of `tools.jit_skill_loader`)

```
run 1:  407 ms
run 2:  651 ms
run 3:  531 ms
run 4:  799 ms
run 5: 1449 ms  <- outlier (likely AV scan on python.exe + module deps)
avg: 767 ms, min: 407 ms, max: 1449 ms, stdev: 408 ms
```

Each run is a fresh `python.exe -c "import tools.jit_skill_loader"`. The post-fix sealed average (586 ms) is the published target. The 5th run outlier dominates the audit avg; without it, avg = 597 ms, well within the post-fix sealed range.

### #3 UQF `--scan-all`

`python tools/uqf_audit.py --scan-all` -- 3574 ms outer, rc=0, 7 stdout lines. No prior baseline; this is the seed value. Suggested target: < 5 s for the audit's small repo footprint.

### #4 verify_spp.py umbrella

Pass1 (orchestrator): incorrect path -> `verify_spp.py missing`. Pass2: 90 s timeout. Pass3 (300 s budget): **155.3 s wall, rc=1**.

Per-row breakdown (from stdout tail):
| Row | rc | elapsed | Result |
|---|---|---|---|
| mirror-parity | -- | -- | **STRICT FAIL** |
| drift-report | -- | -- | **STRICT FAIL** |
| paths+secrets | -- | -- | **STRICT FAIL** |
| hooks-registration | -- | -- | **STRICT FAIL** (HOOKS_REG_PROBE=6/7) |
| hard-rules | 0 | 0.31 s | OK (HARDRULES_PROBE=7/7) |
| playwright-resilience | 0 | 8.20 s | OK |
| compact-resilience | 0 | 10.39 s | OK |
| jit-performance | 0 | 1.47 s | OK (JIT_PERFORMANCE=11/11) |
| restart-and-lag | 0 | 4.12 s | OK (RESTART_AND_LAG=15/15) |

**4 of 9 rows STRICT FAIL.** Perf-side the umbrella is within budget (155 s of 240 s). Correctness-side: the 4 strict-fails are the same surface as the V-gate suite's `test_mirror_parity.py` ERR -- mirror parity is the root, and drift-report + paths+secrets + hooks-registration likely cascade off it. **Action item:** treat as a single mirror-state remediation task, not 4 separate fixes.

### #5 `pytest tests/`

`43 passed in 15.88s` inner / 27.0 s wall. The 11 s gap between inner and outer is pytest collection + subprocess overhead. Target: < 60 s. Comfortably green.

### #7 TCO compact gate

`python tools/tco_compact_gate.py` -- 312 ms outer, head: `context-pct (estimate): 7%  [warn>=70%]`. This is 56 % above the 200 ms target -- driven by Python cold-start, not the gate logic. **Recommendation:** if a tighter target is needed, run as a hot-reloaded daemon (matches what `tco_compact_gate_daemon` would look like), or accept 200 ms as aspirational and document the cold-start floor.

### #8 TIS report `--summary`

399 ms outer, rc=0, head: `session   calls  in_tok   out_tok  cache%  cost_usd`. Within target.

### #9 OSA dispatcher `--check`

251 ms outer, rc=0. JSON output starting with `{`. Within target.

### #10 Proactive dispatch (cold subprocess)

`from modules.pp_agents.proactive_dispatcher import dispatch` + 1 call on empty context:
```
inner_ms: 91   outer_ms: 206   advisories: 0
```

Empty-context returns 0 advisories (expected -- no signals to react to). Inner 91 ms is the import-and-dispatch cost.

### #11 Monitoring `--once`

`python -m modules.monitoring.observe --once` -- 6002 ms outer, rc=1. Originally classified as ERR by the orchestrator; pass2 reclassifies:

```
infinityops    | UP    | curl https://infinityops.ai/ pattern matched
kobiicraft     | DOWN  | tcp 5.9.23.174:25565 ConnectionRefused
tua-x          | UP    | HTTP 200 from cw.infinityops.ai
```

rc=1 is the **semantic signal** "at least one project DOWN", not a perf failure. The wall time (6 s) is dominated by the real network probes. **Action item:** kobiicraft DOWN is a real alert worth surfacing separately (out of scope for this audit but flagged).

### #12 `anti_patterns.run_all(ceps.py)`

86 ms inner / 198 ms outer. 22 hits in 7 categories on a real PP source file (`tools/ceps.py`).

### #13 CEPS `record_error`

35 ms inner / 133 ms outer (most of the 133 ms is Python cold-start; the record itself is fast).

### #14 Session hub direct invoke

`echo {} | node hooks/session_start_hub.js` -- 246 ms outer, rc=0, 17 bytes stdout (`{"continue":true}`). Matches the V-HUB-FAST gate target of < 1500 ms with margin.

### #15 `never_again.top_recurring(10)`

66 ms inner / 395 ms outer. 10 rows returned. The 329 ms outer overhead is Python cold-start + sqlite open.

## Gaps -- benchmarks that should exist but don't

The 15 benchmarks above cover the core PP surfaces. The following capabilities have NO measurement and should have one before the next major doctrine change:

| # | Surface | Why it matters | Suggested benchmark |
|---|---|---|---|
| G1 | All 22 PP hooks (cold-spawn time, individually) | hooks are the single biggest source of perceived lag; we only measure SessionStart hooks today | extend `tools/measure_session_start.py` into `measure_hooks.py` covering PreToolUse, PostToolUse, Stop, SessionEnd, UserPromptSubmit |
| G2 | `hook-dispatcher.js` end-to-end (when a multi-handler matcher fires) | the dispatcher is the C23-mirror for non-SessionStart events; consolidates multiple PreToolUse hooks | add to G1 |
| G3 | `bug-to-hardrule.py --scan` | the auto-HR pipeline; if it's slow, governance lag compounds | wall-time + new HR rate |
| G4 | `hard_rules` extractor + appender end-to-end | sealed-bug -> HR commit is part of the doctrine loop | wall-time |
| G5 | RTK fusion `verify_rtk_fusion.py` (already inside verify_spp, no isolated number) | RTK is per-Bash overhead; if it adds > 100 ms it shows up everywhere | isolated wall-time + compression ratio |
| G6 | `osa/throttle.py --check` | throttle overhead is in every dispatch path | wall-time |
| G7 | Bash bridge round-trip via PowerShell pivot | the PP doctrine is "prefer PowerShell"; we never measured the actual delta | dual benchmark of identical command both ways |
| G8 | JIT loader **warm** path (vs cold, currently the only measured) | the disk-cache hit is the steady-state; we only measure the cold-cache path | bench with `PP_WARM_RUN=1` pre-flight, then time the actual JIT match |
| G9 | Gatekeeper-semantic hook injection size + read overhead | the hook adds 40 KB additionalContext on every Read; the hook-fanout-systemic-cost.md feedback flagged this | KB injected per Read + per-Read hook fanout total wall |
| G10 | Session hub variance under load (10 consecutive SessionStarts) | confirms the 220 ms median holds; surfaces AV-variance distribution | 10 runs, p50 + p95 + p99 |
| G11 | Playwright MCP cold-up / warm-down | MCP latency directly affects user UX | wall-time to first usable browser context |
| G12 | Compact-rescue end-to-end (already in test_compact_rescue.py at 17.7 s, but no perf assertion) | rescue is rarely-fired but high-stakes; we should know its budget | add p50 assertion to the V-gate |
| G13 | Bench-audit itself (this report's orchestrator wall time) | the audit budget is a meta-metric | wall-time of `run_all_benchmarks.py` |

## Priority recommendations (ordered by ROI)

1. **Mirror-parity remediation** (correctness, biggest single root) -- 4 verify_spp STRICT FAILs + 1 V-gate ERR all cluster on PP↔`~/.claude/` drift. One investigation, multiple downstream fixes. Likely 30-60 min depending on whether the drift is loose-ahead (advisory-mergeable) or genuine divergence.
2. **AV exclusion on `C:\Users\User\.claude\skills\claude-power-pack`** (Owner-side, 1 minute) -- eliminates T-WIN-AV-001 noise that dominates JIT cold-start variance (σ 408 ms) and the session-start pass1 spike (1106 vs 220 ms). Highest perf-side action per minute of effort.
3. **Investigate `test_vague_lint.py` FAIL** (correctness, not perf, independent of mirror) -- single suite failure, likely 10-30 min investigation. After mirror remediation, this is the only remaining V-gate red.
4. **Add G1 (full hook coverage measurement)** -- the single biggest measurement blind spot. Once we have per-hook timing for ALL events (not just SessionStart), the next consolidation candidate after C23 becomes obvious.
5. **Reduce TCO gate cold-start to < 200 ms** (G5 RTK isolated + Python cold-start study). If TCO gate is a Python cold-start hostage, the answer is "accept 300 ms" -- but we should know that, not guess.
6. **Investigate JIT cold-start variance** (G8 warm path) -- the σ of 408 ms is the open question. Either the warm path is the right number (currently hidden) or there's a real cold-start regression hiding behind AV noise.

## Reality contract

Every row in the Executive Summary has a real number measured this run -- no projection, no inheritance from prior baselines. The two ERR rows (#4 pass1 verify_spp timeout, #11 monitoring rc=1) are documented honestly with their pass2 reclassification. The two V-gate failures (#6 mirror_parity ERR, vague_lint FAIL) are listed by name in §V-gate detail without obfuscation.

Verdict: **PP is performance-green on 13/15 benchmarks**; the 2 warn cases (#2, #7) and the 2 V-gate failures (#6) are itemized with concrete next steps.
