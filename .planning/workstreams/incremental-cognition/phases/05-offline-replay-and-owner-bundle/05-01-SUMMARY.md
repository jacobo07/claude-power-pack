---
phase: 05-offline-replay-and-owner-bundle
plan: 01
subsystem: measurement-instrument
tags: [kme, pillar-L, offline-replay, upper-bound, stdlib, mutation-drill]

requires:
  - phase: 03-kme-corpus-measurements
    provides: kme_pillars run context (_prepare/_resolve/_match), EObserver, burden/residency arithmetic, cmd_signature
provides:
  - wiki/tools/kme_replay.py `rank`: three candidate experiments on one weighted denominator, ranked by upper bound
  - tools/test_kme_replay.py: 20 V-KMER-* gates and a 6-mutant drill
  - additive observer_factories keyword on kme_pillars _measure / _resolve
affects: [05-02 ranking contract and KME-G smoke, 05-03 wrapper R3 extension and laptop code sync, 05-04 bundle summary]

actuals:
  tokens: 18547
  tasks: 3
  commits: 3
plan_head_before: bfe4ee4ada6a8e2fa3ae22a3cce211bb4edeebc1
commits: 3

tech-stack:
  added: []
  patterns:
    - "import, never fork: identical_rereads is kp.EObserver itself, equality with `kme_pillars.py e` is a gate"
    - "UNMEASURED is a separate list with a reason and no number; a measured zero ranks"
    - "figures rounded at 6 decimals at the ranking boundary"

key-files:
  created:
    - wiki/tools/kme_replay.py
    - tools/test_kme_replay.py
  modified:
    - wiki/tools/kme_pillars.py

key-decisions:
  - "Separate module kme_replay.py instead of a rank subcommand in kme_pillars.py (its `all`, RULE_DENOMINATORS pin and bundle gate stay untouched)"
  - "late_rollover threshold is GROWTH above the thread's own floor, G = 100,000 default; 50k/100k/200k sensitivity beside, never deciding the rank"
  - "Ranked figures are rounded to 6 decimals; the E-equality gate compares to round(E hi, 6)"

requirements-completed: []   # IC-L addressed, NOT satisfied: only a ledger terminal satisfies it (needs the KME-L laptop run and the Owner's decision)

coverage:
  - id: D1
    description: "kme_replay.py rank scans once and ranks late_rollover, identical_rereads, unchanged_precondition_retries by upper bound on one named weighted denominator"
    requirement: IC-L
    verification:
      - kind: unit
        ref: "python3 tools/test_kme_replay.py (V-KMER-TRACER-E2E and the 19 other gates)"
        status: pass
    human_judgment: false
  - id: D2
    description: "A partly observed candidate is UNMEASURED with a reason and no number; a measured zero ranks"
    requirement: IC-L
    verification:
      - kind: unit
        ref: "V-KMER-ROLLOVER-INLINE-SIDECHAIN-UNMEASURED, V-KMER-RETRY-UNPAIRED-UNMEASURED, V-KMER-ROLLOVER-BELOW-THRESHOLD, drill M9"
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-10-04
status: complete
---

# Phase 5 Plan 01: Offline replay ranker core Summary

**`kme_replay.py rank` replays three experiments (late rollover at a growth-above-floor threshold, identical rereads as the Phase 3 E observer itself, unchanged-precondition retries) on one weighted denominator and ranks them by upper bound, never as a saving, with UNMEASURED kept out of the numbers.**

## Performance

- **Duration:** about 7 min wall clock (00:41 to 00:48 UTC, 2026-10-04)
- **Tasks:** 3 of 3 (1 tracer, 2 TDD auto)
- **Files:** 2 created, 1 modified (additive keyword only)

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | 6af1b5e5 | feat(incremental-cognition): L -- offline replay ranker tracer (three candidates, one denominator, upper bounds) |
| 2 | 3d657858 | feat(incremental-cognition): L -- late rollover policy replay and identical rereads (E) from both poles, drill M1 M2 M5 |
| 3 | 0e6a7af3 | feat(incremental-cognition): L -- unchanged-precondition retries (loose upper, strict beside), unpaired results UNMEASURED, drill 6/6 |

## Baseline (measured before the first edit)

- `timeout 300 python3 tools/test_kme_pillars.py`: `KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0`
- `timeout 600 python3 tools/test_kme_pillars.py --drill`: `DRILL killed=20/20`

After the work (re-run at Task 1 and Task 3): the same two lines, unchanged. `timeout 300 python3 tools/test_incremental_cognition_program.py --selftest` prints `ICP_SELFTEST=PASS`. Ledger `state.L` is `{}`; IC-L unticked.

## Gate output (final)

```
KMER_PASS=20/20  threshold=20/20  skipped=0  inconclusive=0
PASS DRILL-CONTROL unmutated run: 19/19 gates green
KILLED M1 ... by V-KMER-ROLLOVER-FLOOR
KILLED M2 ... by V-KMER-ROLLOVER-SEGMENT
KILLED M3 ... by V-KMER-RETRY-INTERVENING-WRITE
KILLED M4 ... by V-KMER-RETRY-COMMAND-KEY
KILLED M5 ... by V-KMER-REREADS-EQUALS-E
KILLED M9 ... by V-KMER-RETRY-UNPAIRED-UNMEASURED, V-KMER-ROLLOVER-INLINE-SIDECHAIN-UNMEASURED
PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 19/19 gates green
DRILL killed=6/6
```

Tracer: identical_rereads 2200.0 > late_rollover 803.0 > unchanged_precondition_retries 225.0 on a 3,879.0 denominator, all three equal to the hand derivation in the plan (no difference to record).

## RED / first-run record

- **Task 1 RED** (before `wiki/tools/kme_replay.py` existed): `ModuleNotFoundError: No module named 'kme_replay'` at the import line of tools/test_kme_replay.py. The tracer then passed on its first run after the build.
- **Task 2 gates RED before the build** (Task 1 build had no synthetic skip, no inline-sidechain detection, no sensitivity): V-KMER-ROLLOVER-SYNTHETIC-SKIPPED (read 1,125.0), V-KMER-ROLLOVER-INLINE-SIDECHAIN-UNMEASURED (ranked instead of unranked), V-KMER-ROLLOVER-SENSITIVITY (KeyError sensitivity). **Passed on first run, red shown another way:** ROLLOVER-FLOOR (drill M1), ROLLOVER-SEGMENT (M2), REREADS-EQUALS-E (M5); ROLLOVER-POSITIVE / -BELOW-THRESHOLD form a pole pair on one fixture (803.0 vs 0.0 by threshold; an ad hoc run with G forced to 1 turned both red); ROLLOVER-SUBAGENT-THREAD (ad hoc: ignoring subagent files turned it red); REREADS-POSITIVE / -NEGATIVE are a pole pair (ad hoc: a classifier that calls everything identical turned NEGATIVE red).
- **Task 3 gates RED before the build** (Task 1 retry observer was loose-only with no epochs, no Agent handling, no after-error flag): V-KMER-RETRY-INTERVENING-BASH (strict 1 instead of 0), V-KMER-RETRY-EXCLUSIONS (agent_redispatches missing), V-KMER-RETRY-AFTER-ERROR (after_error missing). **Passed on first run:** INTERVENING-WRITE (drill M3), COMMAND-KEY (M4), UNPAIRED-UNMEASURED (M9, also pairing was already in the Task 1 observer), RETRY-POSITIVE and OUTPUT-SHARE (ad hoc: doubling the output share turned both red).

## Deviations from Plan

### Judgement calls (no rule trigger)

1. **Rounding at 6 decimals.** The ranking boundary rounds `upper_bound_weighted` and `weighted_denominator` to 6 decimals (float noise such as 2200.0000000000005 is not a measurement). The plan's "equals ... exactly" for V-KMER-REREADS-EQUALS-E is therefore "equal to `round(weighted_interval[1], 6)`"; the gate still separates it from `weighted_interval[0]` (4000.0 vs 1333.33) and drill M5 kills it.
2. **Commit trailer.** The attribution reminder in force for this run (`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`) was used, as the dispatch said, not the Opus line in the execution prompt.
3. **stdout token.** `vs_threshold=` prints `>=3%` / `<3%` (spaces removed) so the line stays one token per field; the file and JSON keep the plan's `">= 3 %"` / `"< 3 %"`.
4. **Unranked entries carry no details.** An UNMEASURED candidate's JSON entry holds only candidate, status, reason and observability: its details (which would include rollover sensitivity figures) are dropped so no number for it can leak.
5. **`terminal_ok` helper added** to kme_replay.py (05-03 lists it among the symbols it will import); it holds the terminal rule (primary + exact + committed frozen source + nothing unranked).

No Rule 1-4 deviations. No auth gates, no package installs.

## Known Stubs

None.

## Threat Flags

None. The ranker only reads transcripts and writes one measurement file through `kp.write_measurement` after `redact()`; commands appear only as `kp.cmd_signature` output, file content only as sha256 inside EObserver (never emitted).

## Notes for the next plans

- `kme_pillars.py` diff is exactly six lines (keyword on `_measure` / `_resolve` and the three measuring call sites plus the `obs =` line).
- 05-02 needs only the ranking-contract hardening and the KME-G smoke; the module already exposes `FRONT_KEYS`, `RULE_DENOMINATORS`, `INSTRUMENT`, `KMER_BODY_MARKER`, `terminal_ok` for 05-03.
- The loose retry class is a deliberate upper bound; strict is reported beside in `details`.

## Self-Check: PASSED

- FOUND: wiki/tools/kme_replay.py, tools/test_kme_replay.py, wiki/tools/kme_pillars.py (modified)
- FOUND commits: 6af1b5e5, 3d657858, 0e6a7af3 (git log on branch mission/incremental-cognition-run)
- `git rev-list --count bfe4ee4a..HEAD` = 3 before this SUMMARY commit
