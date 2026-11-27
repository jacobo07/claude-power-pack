---
phase: 05-critical-path-audit
plan: 03
subsystem: hook-critical-path-audit
tags: [before-after-judge, plane-gate, sampler, laptop-procedure, evidence]
requires:
  - phase: 05-critical-path-audit plans 05-01, 05-02
    provides: inventory, class table, guard, boundary records
provides:
  - ab-judge subcommand (pure ab_verdict, closed verdicts, refuses GEX44 and SHAPE_ONLY input)
  - collect subcommand (per-sample fresh HOME, process-group kill, schema-2 host state)
  - 05-EVIDENCE.md with LP-09 to LP-12 as procedure and falsifier
affects: [phase 6, laptop evidence runs LP-09..LP-12]
tech-stack:
  added: []
  patterns: [owners imported not redefined, censored samples counted per arm, plane gate before judgment]
key-files:
  created:
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/05-EVIDENCE.md
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-03-suite.txt
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-03-collector-smoke.txt
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-03-final-gates.txt
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-03-reach-final.txt
  modified:
    - tools/hook_critical_path_audit.py
    - tools/test_hook_critical_path.py
decisions:
  - GEX44 host recognised by literal name and a gex44 substring, not by reading the name through bench_all
  - single strict host bucket per judgment; censoring counted over all plane-matching samples
  - --work-preserved absent means UNKNOWN
  - SHAPE_ONLY files are never judged
metrics:
  duration: one session, unattended
  completed: 2026-11-23
status: complete
requirements: [PERF-05]
commits: 4
plan_head_before: 4fa606d727afb03a10831a63a48738f3783a5fdb
actuals:
  tokens: 16000   # chars/4 over the changed tool, suite and evidence text; approximate, not a harness count
  tasks: 3
  commits: 4      # git rev-list --count 4fa606d727afb03a10831a63a48738f3783a5fdb..HEAD, measured before this docs commit
---

# Phase 5 Plan 03: Before/after judge, sampler and evidence Summary

A pure before/after judge that refuses any GEX44 number as laptop evidence, a sampler that on GEX44 can only prove its own mechanics, and a phase evidence file that writes the laptop measurement as an executable, falsifiable procedure (LP-09 to LP-12) without containing a single timing of a real hook chain.

## What was built

- **Task 1 (afff74cb)**: `ab-judge` and `ab_verdict` in `tools/hook_critical_path_audit.py`. Closed verdict set B_FASTER, B_SLOWER, NO_DIFFERENCE_DETECTED, INCONCLUSIVE, UNKNOWN. J5: both p50 and p95 must beat the A to A-replicate noise. Minimum 7 MEASURED samples per arm (PROPOSED, uncalibrated). Owners are imported, not redefined: `tools/bench_all.py` (host state, pressure, bucket, window), `tools/verify_bench_all.percentile`, `construction_metrology` states. An owner import failure is BLOCKED (exit 2), not a silent fallback. TIMED_OUT, UNOBSERVED and FAILED samples are counted per arm and an asymmetry is INCONCLUSIVE. 52 gates (V-CRIT-AB-*) including the plane CLI gates.
- **Task 2 (aa124969, ae6fd9d9)**: `collect`: one chain through a given dispatcher file, fresh HOME per sample, unique session id never stored, list argv, per-sample timeout with process-group kill. Any dispatcher that is not the running user's live install is labelled SHAPE_ONLY, prints no timing, and `ab-judge` refuses it. 23 decoy-dispatcher gates (V-CRIT-COLLECT-*). Shape smoke on GEX44: 3 MEASURED samples, `records/05-03-collector-smoke.txt`.
- **Task 3 (304b781b)**: `05-EVIDENCE.md` (nine sections), the final gate records, and this summary. EVIDENCE_OK printed.

Suite: `CRITPATH_PASS=134/134` (`records/05-03-suite.txt`, GEX44, about 44 s).

## Final gates (GEX44, `records/05-03-final-gates.txt`)

a5_u6 13/13, arm preflight 23/23, bench integrity 53/53, bench gate 24/24, resource pressure 17/17, gsd_mission resources 17/17, gsd_mission baseline 21 passed 0 failed, critical path 134/134, git-invocation 6/7 (exit 1). Compared with `04-03-final-gates.txt`: every counter equal; the git-invocation 6/7 and its 14 NEW offenders are the Phase 4 state, not caused by this plan. Reachability: 56 offenders before and after, names unchanged. `git diff --stat 4fa606d7 -- hooks/ vault/ tools/measure_hook_event.py tools/measure_session_start.py tools/test_hook_boundary.py` is empty. `tools/test_s9_redteam.py` was not re-run (814 s in Phase 4; its caveat stands in STATE.md).

## Deviations from Plan

**1. [Rule 1 - Bug] Plan said refuse the host name read via bench_all.** On the laptop that would refuse the laptop itself. Resolved with literal and `gex44` substring detection of the GEX44 name plus an explicit `--laptop-host` that every sample must match. Commit afff74cb.

**2. [Rule 1 - Bug] Gate V-CRIT-COLLECT-SHAPE-ONLY-JUDGE-REFUSES-SCOPE failed (131/132).** The test assumed the file's own host name reached the scope rule; on GEX44 that name is refused earlier. Split into an own-host refusal gate, a scope gate on a copy relabelled to a laptop-style host, and a LIVE_DISPATCHER control. Commit aa124969.

**3. [Rule 1 - Bug] Timeout-kill gate flaked under load.** The first final-gate run exited 1 (load near 118, node start-up outran a 600 ms timeout, pid file never written). The gate now retries up to three times at 3000 ms and judges only once the decoy has started; a decoy that never starts still fails. Commit ae6fd9d9. The gate run was repeated and passed.

**4. [Process note] Task 1 commit carries Task 2 code.** `afff74cb` already contains the collect code, which was gated only in Task 2. Not rewritten (history already recorded).

**5. [Process] The final-gates script rewrites the home prefix** in captured output so the committed record has 0 absolute home paths (T-05-15). The first run had 3.

## Auth gates

None.

## Threat Flags

None. The collector executes the dispatcher path it is given; documented as trusted input only, fresh empty HOME, per-sample timeout, list argv, no shell (T-05-14).

## Known Stubs

None.

## Unknowns carried

No wall time of a real hook chain exists on any plane. The 54.9 s figure is a laptop-era comment claim. The laptop `settings.json` registration is unseen. The sample minimum of 7 and the noise rule are proposed, uncalibrated. All laptop items are LAPTOP-ONLY / UNJUDGED until records come back.

## Self-Check

## Self-Check: PASSED

All created and modified files exist (evidence, four 05-03 records, tool, suite, this summary). Commits afff74cb, aa124969, ae6fd9d9 and 304b781b are on the branch.
