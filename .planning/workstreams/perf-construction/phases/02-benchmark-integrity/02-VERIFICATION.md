---
phase: 02-benchmark-integrity
verified: 2026-11-22T21:10:00Z
status: passed
verdict: passed_with_unknowns  # GSD routes only passed|gaps_found|human_needed; unknowns below stay open
score: 4/4 roadmap success criteria verified for the code paths (P01, P03, P04, P06); P07 not addressed (BLOCKED-ON-ORIGIN-AUDIT)
verified_head: 62102855
behavior_unverified: 0
gaps: []
unknowns:
  - "P07 has no definition on this host (origin audit ed9de300 absent); BLOCKED-ON-ORIGIN-AUDIT, no work done, NOT a pass"
  - "LP-03: Windows host-state reading and bucket stability are laptop-only and unobserved (UNJUDGED)"
  - "Live regression verdicts on this host are UNJUDGED: fewer than 3 host-state-matched ledger entries exist; the window logic is proven only by temp-ledger gates"
  - "tools/verify_bench_all.py and tools/verify_spp.py were NOT run live by this verification (they append to the tracked ledger); the gate side is verified by temp-ledger gates and mutation only"
  - "Owner question 1 open: verify_bench_all still exits 0 on an absolute-target miss that stays inside the 1.5x band (reported as BENCHMARKS_NOTE only)"
  - "Owner question 2 open: a vgate suite exiting 1 makes vgate_total_ms an instrument error (implemented per D-03) vs only incrementing vgate_fails"
human_verification: []
---

# Phase 2: Benchmark integrity - Verification Report

**Phase goal:** bench_all / verify_bench_all cannot report success they did not earn.
**Plane:** GEX44 (linux, python3 stdlib). Code reading, the two named test suites, and throw-away mutation copies in /tmp (git archive of HEAD, deleted afterwards). `verify_bench_all` and `verify_spp` were not run; the tracked ledger `vault/benchmarks/ledger.json` was not touched (`git status --short vault` is empty).
**Re-verification:** No, initial verification.
**Status: passed_with_unknowns.** The four roadmap success criteria are met on evidence I re-observed. The phase does not cover P07, does not make the gate fail on an in-band absolute miss (policy question left to the Owner), and leaves live regression verdicts and laptop behaviour UNJUDGED. None of those is counted as a pass.

## Observable Truths (ROADMAP Phase 2 success criteria)

| # | Truth | Status | Evidence (re-observed, not taken from SUMMARY) |
|---|-------|--------|-----------------------------------------------|
| 1 | Four verdicts per metric (instrument_ran, met_target, regressed, evidence_sufficient); a FAILED or TIMED_OUT sample never counts as fast (P03); non-zero exit on a missed absolute target (P01) | VERIFIED | `tools/bench_all.py`: `judge_metrics` (848) emits the four verdicts per primary metric with a reason each and `None` for unknown; `verdicts_fail` (918) forces failure on `instrument_ran False`, `met_target False` or `regressed True`; `main` ends `rc = 1 if (errors or verdicts_fail(verdicts)) else 0` (1282). `_sample_failure` (143) classifies TIMED_OUT / FAILED / CRASHED against a per-benchmark `COMPLETED_RCS` table; there are 17 `_run(` references and 17 `_sample_failure(` references (definition plus 16 call sites, one per `bench_*` function at 191-642). `pytest` rc 1 is now an error, not 19.9 ms. I ran `python3 tools/test_bench_integrity.py`: `BENCHINT_PASS=41/41`, exit 0. |
| 2 | verify_bench_all keeps `min` as a labelled potential floor and adds p50/p95 (P04); regression compares against a host-state-matched window (P06) | VERIFIED | `tools/verify_bench_all.py`: `percentile` (168), `summarize` (183, floor/p50/p95/max/n), `FLOOR_LABEL` "potential floor (min of N valid samples ...)" printed in the verdict line; `judge` (284) accounts every attempt and sets `evidence_sufficient`. `tools/bench_all.py`: `host_bucket` (1022), `window_for` (1051: same quick flag AND same host bucket, last `WINDOW_N`=7, never falls back to the previous entry), `baseline_from_window` (1076: errored entries contribute nothing, host-scope RAM is not a baseline), `MIN_WINDOW`=3 below which regression is `None` (UNJUDGED) rather than "no regressions". Ledger entry carries `ledger_schema`, `host_state`, `verdicts`. `python3 tools/test_bench_gate.py`: `BENCH_GATE_PASS=23/23`, exit 0. |
| 3 | Each fix has a test that FAILS on the pre-fix code and passes after, recorded verbatim | VERIFIED | `records/*.red.txt` / `*.green.txt` pairs exist in the phase dir, and the test commits precede the fix commits in `git log` (d76e8a9f RED -> 4e7b6d0d, b9611b73 -> dcd6dfdc, 729bf021 -> 0ef7239f, e1bc38a8 -> 1a2ba1fc, 31ea3e98 -> c54590c2, 891df83f -> 5fb64d7f, 00f6c7af -> 8893f2b8, bd717662 -> e92562d1). I did not rely on the records: I ran my own mutations on a copy of HEAD, see the mutation table. |
| 4 | Existing gates of the touched owners still pass | VERIFIED (baseline kept) | `test_bench_gate.py` 23/23 (baseline 13/13, grown by new gates), `test_ram_optimization.py` `RAM_PASS=10/10` (baseline 10/10), `test_git_invocation.py` `GIT_INVOCATION_PASS=6/7` exit 1: only V-GITINV-NO-GROWTH fails with 14 unfrozen offenders, none in `tools/bench_all.py` or `tools/verify_bench_all.py`; this equals the pre-phase baseline recorded in 02-EVIDENCE.md section 1 (6/7, same failing gate). Pre-existing failure, not a regression. |

**Score:** 4/4 criteria verified; 0 present-but-behavior-unverified truths.

## Mutation checks I ran (could the instrument have returned the other answer?)

Each mutation was applied to a fresh `git archive HEAD` copy under /tmp and the suite re-run there. Each one is detected.

| Mutation | Result | Failing gates (excerpt) |
|----------|--------|------------------------|
| A. `rc` ignores verdicts (`rc = 1 if errors else 0`) | exit 1 | V-BENCHINT-EXIT-FROM-VERDICTS, V-BENCHINT-REAL-REGRESSION-NOT-MASKED, V-BENCHINT-ABS-MISS-EXITS-NONZERO, V-BENCHINT-RAM-HOST-SCOPE-UNJUDGED |
| B. `_sample_failure` never flags (always None) | exit 1 | V-BENCHINT-PYTEST-FAILED-NOT-FAST (`pytest_total_ms=0.0` recorded for a failed subprocess), V-BENCHINT-SITE-session_start / jit_cold_start / uqf_scan / verify_spp / pytest and the remaining per-site gates |
| C. `window_for` ignores the host bucket / mode | `BENCHINT_PASS=39/41`, exit 1 | V-BENCHINT-WINDOW-FILTERS, V-BENCHINT-COMPARE-MATCHED |
| D. `verify_bench_all` drops the UNCONFIRMED line for a failed retry | `BENCH_GATE_PASS=22/23` | V-BENCH-MAIN-FAILED-RETRY-UNCONFIRMED |

Not mutated by me (taken from the phase's own red records, which show pristine-file runs exiting 1): P04 floor label / p50 / p95 and the in-band absolute-target note. They are covered by passing gates but I did not independently falsify them.

## Key links

| From | To | Via | Status |
|------|----|-----|--------|
| `tools/bench_all.py:main` | `judge_metrics` / `verdicts_fail` | exit derived from verdicts | WIRED (line 1282, mutation A shows it load-bearing) |
| every `bench_*` | `_sample_failure` | classifier before any numeric is stored | WIRED (16 sites; mutation B) |
| `main` | `window_for` -> `baseline_from_window` -> `regression_baseline` -> `detect_regressions` | matched window feeds regression and `--compare` | WIRED (mutation C) |
| `tools/test_bench_gate.py` | `tools/test_bench_integrity.py` | V-BENCH-INTEGRITY-SUITE-WIRED (row bench-gate of verify_spp) | WIRED; the gate has a negative control (exit-1, partial-count and silent scripts rejected). No RED run exists by design; I did not mutate this gate. |

## Requirements coverage

| Requirement | Status | Note |
|-------------|--------|------|
| PERF-02 (benchmark integrity defects fixed in owners with falsifying tests) | SATISFIED for P01, P03, P04, P06 | P07 is named in the roadmap goal but UNDEFINED on this host (Phase 1: UNKNOWN, origin audit ed9de300 absent); carried as BLOCKED-ON-ORIGIN-AUDIT, not claimed. No orphaned Phase 2 requirements. |

## Anti-patterns and integrity checks

- Debt-marker scan (TBD / FIXME / XXX / TODO) over lines added to `tools/bench_all.py` and `tools/verify_bench_all.py` since 1ce2ef59: none.
- Scope: files changed since the Phase 1 base outside `.planning` are exactly `tools/bench_all.py`, `tools/verify_bench_all.py`, `tools/test_bench_gate.py`, `tools/test_bench_integrity.py`; no new owner module, matching "EXTEND, no new owner".
- Tracked ledger untouched; no live `verify_bench_all` / `verify_spp` execution.
- Live smoke (`live_smoke.py`, temp ledger) is recorded in 02-EVIDENCE.md section 5 with before/after files; I did not re-run it.

## Unknowns and risks (WARNING, none blocking)

1. **P07 undefined (BLOCKED-ON-ORIGIN-AUDIT).** Named in the phase goal; no work performed and none could be honest. Closing needs the origin audit (main at ed9de300), laptop-side.
2. **The gate still exits 0 on an in-band absolute-target miss.** `verify_bench_all` judges 8 names against `QUICK_TARGETS x BAND (1.5)`; a metric between the absolute target and the band is printed as `BENCHMARKS_NOTE`, and the run prints `BENCHMARKS_OK`. `bench_all` itself now fails on the miss (P01), but the gate that `verify_spp` calls does not. This is a laptop-calibrated policy (Owner question 1), so I did not record it as a gap, but "verify_bench_all cannot report success it did not earn" holds only with that caveat.
3. **`evidence_sufficient` is computed by `judge` but does not change `verify_bench_all`'s exit** (only the UNCONFIRMED line is printed). A healthy single-sample exit 0 is the unchanged path.
4. **Live regression is UNJUDGED on this host** until three matched entries exist; matched-window behaviour rests on temp-ledger gates.
5. **LP-03 laptop-only:** Windows `read_available_mb`, `load1 None`, bucket stability. The procedure is written in 02-EVIDENCE.md section 6.
6. **Self-authored instrument.** `test_bench_integrity.py` (1161 lines) was written by the phase it judges. Mitigated by my mutations A-D, which it caught each time, but the suite is not independently audited. The git-invocation gate still fails on 14 pre-existing, unrelated offenders.
7. Cosmetic: the console verdict line prints `(n=K)` twice when the reason already contains the count (recorded by the phase, unfixed).

---

_Verified: 2026-11-22T21:10:00Z_
_Verifier: Claude (gsd-verifier)_
