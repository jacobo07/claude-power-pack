---
phase: 02-kme-l-challenger
plan: 05
subsystem: kme-analytics
tags: [challenger, benchmark, strace, post-delta, canary, index-bytes, real-corpus, gex44]
requires:
  - phase: 02-kme-l-challenger
    provides: plan 02-04 evidence (certificate, read set 107 sessions / 369 files, unscoped control scan as the champion byte basis)
  - phase: 02-kme-l-challenger
    provides: plan 02-02 strace_io_sum.py run and kme_equivalence.py compare
provides:
  - "P-table-gex44.md: post-delta canary, N=5 cold/warm runs, 8-row comparison table with caption, machine-readable ## Data block, read-only proof"
affects: [02-06]
plan_head_before: b1023f3d7fc115c4f3622f7cce5238873b0b02ff
actuals:
  tokens: 11358     # chars/4 over the +/- lines of the evidence file (git diff b1023f3d..HEAD, 45431 chars)
  tasks: 3
  commits: 3        # measured: git rev-list --count b1023f3d..HEAD (the docs commit of this summary comes after)
tech-stack:
  added: []
  patterns:
    - "evidence file generated from the bench JSON by scratch scripts (gen_table_t1/t2/t3.py), never typed by hand"
    - "post-delta canary on a real copy with a realpath-guarded append script"
key-files:
  created:
    - vault/programs/incremental-cognition/gen2/evidence/P-table-gex44.md
  modified: []
key-decisions:
  - "Task 1 and Task 2 evidence were committed as partial states of P-table-gex44.md (the plan says do not commit yet); the plan's named commit subject is the Task 3 commit."
  - "The post-delta traced run was repeated with --trace-repeat 2 so that open_set_identical is true and the plan's Task 2 verify (which globs every JSON under bench/) can pass."
requirements-completed: []
duration: ~40 min
completed: 2026-10-07
status: complete
---

# Phase 2 Plan 05: Champion vs scoped vs challenger table on GEX44 Summary

**Median of 5 untraced repetitions of the 7-file query: scoped warm 56.976 s, scoped evicted-best-effort 58.523 s, challenger warm 29.581 s, challenger evicted-best-effort 37.529 s; traced raw bytes 6,120,339,068 (scoped, 995 files) against 3,298,099,868 (challenger, 369 files) plus 1,805,435,496 index bytes; a post-delta query on a scratch copy reads exactly the five appended sessions as stale and still equals the scoped run and the committed files (SAME 7/7 twice).**

## What was built

**Task 1 (tracer, commit e06dafa7).** Fresh `cp -a` of the six scoped directories into `/home/kobii/ao-scratch/p2/delta-root/` (3,160,520,417 bytes; inode of a copied file differs from its source, no symlinks, no hard links). Index `delta.sqlite` (979 files, one call), `population` EXACT (102 active sessions, plane gex44), `certify` CERTIFIED (selected 102, uncovered 16). `append_delta.py` (realpath guard, refusal shown for the real corpus path and for `delta-root/../x`) appended one post-freeze line (122 bytes) to five main transcripts: three sessions the index did not select, two it did. Challenger and scoped 7-file queries on the copy; path records `plan_taken index`, `deopt null`, `stale` equal to the five appended sessions.

**Task 2 (commit 9fb64b83).** Four configurations of N=5 untraced repetitions plus traced runs, all foreground under `timeout`: scoped warm, scoped evicted, challenger warm, challenger evicted (cold ones split 3 + 2, same label). Two traced repetitions per path with `open_set_identical` true. A fresh-out-dir equivalence check of the bench configuration itself: challenger and scoped each `KMEQ_VERDICT=SAME same=7/7` against the committed files.

**Task 3 (commit cd4b63cc).** `## Table` (8 rows, verbatim caption), `## Data` (JSON computed from the bench JSON), `## Read-only proof` (corpus manifest sha256 `29969e7d6ab1...` and index sha256 `6ddd159a914d...` equal before and after, mtime_ns equal, no sidecars).

## Verification observed

Task 1 automated check 1: `python3 -c '...'` printed `[]`, exit 0. Task 1 check 2: `python3 -I tools/kme_equivalence.py compare --candidate /home/kobii/ao-scratch/p2/delta-challenger --committed vault/programs/incremental-cognition/measurements` last line `KMEQ_VERDICT=SAME same=7/7`. The canary also printed `KMEQ_VERDICT=SAME same=7/7` against the scoped run on the copy.

Task 2 verify (after the repeat described below): `[] 3 True`, exit 0 (no configuration short of 5 walls, three traced results, all `open_set_identical` true).

Task 3 verify 1: `True True True`, exit 0 (Data block parsed, walls and raw bytes numeric, `index_bytes` present, caption present). Task 3 verify 2: `python3 -I tools/test_kme_challenger.py` -> `KMEC_PASS=21/21  threshold=21/21  skipped=0  inconclusive=0`, exit 0.

## Measured numbers (commands and JSON in P-table-gex44.md `## Runs`)

| Configuration | Wall median s (n=5) | Walls (s) | Raw bytes (traced) | Raw files | Index bytes |
|---|---|---|---|---|---|
| scoped all+rank, warm | 56.976 | 56.976 57.181 57.927 56.416 56.063 | 6,120,339,068 | 995 | 0 |
| scoped all+rank, evicted best-effort, residency not measured | 58.523 | 58.176 58.523 59.526 58.672 57.989 | 6,120,339,068 | 995 | 0 |
| challenger all+rank, warm | 29.581 | 29.581 29.400 29.548 29.732 29.966 | 3,298,099,868 | 369 | 1,805,435,496 |
| challenger all+rank, evicted best-effort, residency not measured | 37.529 | 37.929 37.297 37.451 37.529 37.783 | 3,298,099,868 | 369 | 1,805,435,496 |
| challenger post-delta (scratch copy) | 28.759 | 28.731 28.759 28.860 28.927 28.637 | 3,301,460,730 | 372 | 519,078,504 (six-directory delta index) |

Unique bytes: scoped 3,055,976,146; challenger 1,648,220,948; post-delta 1,649,876,803. Cross-project bytes and CostaLuz bytes 0 on every measured row. Post-delta read set: 110 sessions / 372 files = 102 selected + 5 no-first-timestamp + 3 newly stale non-selected. Champion Run 5 byte columns are derived from 10 x the 02-04 unscoped single scan (raw 109,088,283,520; unique 9,934,971,549); Run 6 byte columns are UNMEASURED (cited wall 24 s and 177 s, rchar 2.83 GB and 19.47 GB). Every challenger path record of the bench (warm, cold, traced, post-delta): `plan_taken index`, `deopt null`.

## Deviations from Plan

**1. [Process] Tasks 1 and 2 were committed as partial states of the evidence file.** The plan says "Do not commit yet" for Task 1 and commits only in Task 3; the orchestrator's instruction (commit each task as soon as its verify passes) took precedence. The Task 3 commit carries the plan's subject line. The file held a continuation sentinel between commits; the final commit has none.

**2. [Rule 3 - blocking, plan interplay] Post-delta traced run repeated with `--trace-repeat 2`.** Task 1 step 5 asks for `--trace-repeat 1`, and Task 2's verify requires every traced JSON under `bench/` to have `open_set_identical` true, which a single repetition cannot show (it is null). I re-ran the post-delta traced step with two repetitions into `strace2/` (result identical: raw 3,301,460,730, 372 files, index 519,078,504; open sets identical) and overwrote the JSON; the evidence says so.

**3. [Design] Post-delta read set is 110 sessions, not "selected plus three".** Same refinement as 02-04: the 5 no-first-timestamp sessions are read raw by design, so the set is 102 + 5 + 3. The canary still shows exactly five stale sessions equal to the five appended ones, and the output SAME 7/7 on both comparisons.

**4. [Plan text] Table has 8 rows, not 9.** The plan's acceptance text says nine; its own row list (Run 5; Run 6 population; Run 6 seven runs; scoped cold and warm; challenger cold and warm; challenger post-delta) is eight. All listed rows are present.

**5. [Instrument note] Cold rows are barely slower than warm for the scoped path (58.5 vs 57.0 s)** on this NVMe host. The eviction is `posix_fadvise(DONTNEED)` of 6,948 files plus the index, residency not measured; the rows are labelled accordingly and no cold claim is made. The challenger shows a larger gap (37.5 vs 29.6 s). Reported as measured.

**6. [Instrument note] Repeated bench out-dirs make `compare` report `MISSING reason=ambiguous`** (the tool writes suffixed files rather than overwrite). Equivalence of the bench configuration was therefore checked with one fresh out-dir per plan (both SAME 7/7), recorded in `## Runs`.

**7. [Scratch retained]** The scratch copy `/home/kobii/ao-scratch/p2/delta-root/` (3.16 GB), `delta.sqlite`, certificates, strace logs and bench JSON were not deleted; they stay outside the repo and no corpus file was touched.

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat model. T-02-21: realpath guard plus refusal demonstration, manifest before/after equal. T-02-22: forced `--plan challenger`, every path record plan_taken index. T-02-23: walls from untraced repetitions only, index bytes in their own column, Data block computed. T-02-24: logs and copies stay in scratch.

## Notes for plan 02-06

- Read the numbers from `## Data` in `vault/programs/incremental-cognition/gen2/evidence/P-table-gex44.md` (`json.loads` of the fence under the heading): `scoped.warm.wall_median_s` 56.975624, `challenger.warm.wall_median_s` 29.580848, `scoped.raw_bytes` 6,120,339,068, `challenger.raw_bytes` 3,298,099,868, `challenger.index_bytes` 1,805,435,496. `raw_bytes` and `index_bytes` are two processes (`all`, `rank`).
- The decision is 02-06's. Index bytes are not folded into raw bytes anywhere; the post-delta row uses a six-directory index and is not comparable on that column.
- Requirement status: `requirements mark-complete` was not run (unattended instruction); AO-07, AO-09 and AOP-P stay as they are.

## Self-Check: PASSED

- FOUND: vault/programs/incremental-cognition/gen2/evidence/P-table-gex44.md (sections Post-delta canary, Runs, Table, Data, Read-only proof)
- FOUND commits: e06dafa7 (Task 1), 9fb64b83 (Task 2), cd4b63cc (Task 3)
