---
phase: 06-consume-owners-and-close
plan: 04
subsystem: testing
tags: [pillar-n, ledger, reviews, deltas, done-gate, closeout, python]
status: complete

requires:
  - phase: 06-consume-owners-and-close
    provides: ukdl-candidates.md, reviews/ukdl.md, reviews/cbr.md, tools/test_ic_closeout.py with eight gates (plan 06-03)
provides:
  - "ledger reviews.ukdl / reviews.cbr pinned as {file, sha256}"
  - "ledger deltas: 8 product and 9 intelligence entries covering phases 1-6"
  - "tools/test_ic_closeout.py: V-ICN-LEDGER-REVIEWS-PINNED, V-ICN-LEDGER-DELTAS, V-ICN-LEDGER-DELTAS-COVER-PHASES; drill M7-M12 (12/12)"
  - "evidence/N.md: done-gate output verbatim, Status OPEN"
affects: []

actuals:
  tokens: 40000     # chars/4 over the realized diff (~38 KB test code, ~25 KB ledger entries, ~13 KB N.md, minor bundle insert)
  tasks: 3
  commits: 3        # MEASURED: git rev-list --count d31c33dc..HEAD at SUMMARY write
plan_head_before: d31c33dc3a95ff3770d0f4714d779271557e262d
commits: 3

key-files:
  created: [vault/programs/incremental-cognition/evidence/N.md]
  modified: [tools/test_ic_closeout.py, vault/programs/incremental-cognition/ledger.json, vault/programs/incremental-cognition/owner-bundle.md]

key-decisions:
  - "N is addressed, NOT satisfied: no state.N or any other state.<P>, frozen untouched, IC-N not ticked, requirements.mark-complete not called"
  - "a program commit needs BOTH a program or phase-number subject AND a program-owned path (PROGRAM_PATHS); either half alone admits foreign commits"
  - "phase 6 deltas cite ukdl-candidates.md and 06-03-SUMMARY.md, not the two review files, so a recorded promotion re-pins one place (the ledger reviews)"

requirements-completed: []   # IC-N addressed here, not satisfied (promotion is the Owner's; --final fails on the open pillars)

duration: 100min
completed: 2026-10-04
---

# Phase 6 Plan 04: ledger reviews and deltas, done-gate record Summary

**The program ledger now pins both reviews by sha256 and carries 8 product and 9 intelligence deltas for phases 1-6, three gated V-ICN-LEDGER checks (drill 12/12) keep them honest, and `--final` fails on the fourteen open pillars and on nothing else; evidence/N.md records that output verbatim with Status OPEN.**

## Accomplishments

- Task 1 (tracer): `reviews_problems`, `delta_problems`, `program_commit_problem` and the gates V-ICN-LEDGER-REVIEWS-PINNED / V-ICN-LEDGER-DELTAS were written first and run RED (`ICN_PASS=8/10`: reviews null, deltas empty). The ledger edit then replaced exactly the two original lines; `--final` lost its four L8 lines. The gate's failure message names the review file and its current LF sha256. One continuation paragraph was inserted under the bundle's `[N]` item telling the Owner to re-pin `reviews.<key>.sha256` after recording a promotion (5 lines added, 0 removed, no new item).
- Task 2: V-ICN-LEDGER-DELTAS-COVER-PHASES discovers shipped phases from disk and was run RED (`ICN_PASS=10/11`: phases 1, 3, 4, 5, 6 without deltas), then the full set was written; drill M7-M12 added.
- Task 3: evidence/N.md with the frozen rule, review counts, the ledger reviews and deltas, `--status` / `--final` / `--pillar N` verbatim with exit codes, baseline / vault / institutional GC disposition, liveness, eight LF sha256 values, Product / Intelligence Delta, named debts, `## Status: OPEN`.

## Task Commits

| Task | Commit | Subject |
| ---- | ------ | ------- |
| 1 (tracer) | 229bc006782ba4f237779701128dcfc99e309d0c | docs(incremental-cognition): N -- ledger reviews pinned and first deltas; ledger gates (the done-gate's L8 clause satisfied, every pillar still open) |
| 2 | 1a1ad30e0439c10b92bb7cb1af403deec6a894c9 | docs(incremental-cognition): N -- product and intelligence deltas for every shipped phase (1-6), coverage gate, ledger drill |
| 3 | b9645df1c801c14c26f640e52adf3be36f3f3e30 | docs(incremental-cognition): N -- closeout evidence (reviews and deltas set, --final fails on the 14 open pillars only, Status OPEN) |

## Done-gate result (measured, GEX44, 2026-10-04)

- Before (plan base `d31c33dc`): `--final` exit 1, 14 `FAIL L3`, 4 `FAIL L8`, `CEP_VERDICT=FAIL failures=18`, `ICP_VERDICT=FAIL failures=1`.
- After: `--final` exit 1, 14 `FAIL L3 <P>: no terminal disposition` (A to N), 0 `FAIL L8`, `CEP_VERDICT=FAIL failures=14`, `FAIL CE clauses failed (rc 1)`, `ICP_VERDICT=FAIL failures=1`; first line `INCONCLUSIVE V-ICP-REAL-OWNER-READ: fa9ae2ed / 21671d6c not in this clone`. Recorded verbatim in evidence/N.md (every non-empty line of a fresh run is present).
- `--status` exit 0, `"violations": []`, `"closed": []`; `--selftest` `ICP_SELFTEST=PASS`; `--pillar N` exit 1 `FAIL L3 N: no terminal disposition`.
- `test_ic_closeout.py` `ICN_PASS=11/11`; `--drill` `DRILL killed=12/12` with both control lines PASS; `KMER_PASS=45/45`; `ICR2_PASS=14/14` (drill 6/6); `KMEP_PASS=89/89`; `FLOOR_PASS=67/67`.
- Ledger diff over the plan removes exactly the two original lines; every `state.<P>` is `{}`. Owner bundle `git diff --numstat`: `5 0` (insert only); `grep -c '^+- \*\*\['` 0.
- Own commits touching protected paths: `own 3 touching protected []`; phase-own commits touching the liveness surface: `phase-own 16 touching liveness paths []`.

## Deviations from Plan

None - plan executed as written. One mechanical note: the closeout gate imports `test_cognitive_economy_program` (for `ce.TERMINALS`) the way the program wrapper does; the coverage helper and gate were added in Task 2 (after the Task 1 commit) so Task 2 had its own RED run, as the plan orders them.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- evidence/N.md, 06-04-SUMMARY.md, the ledger and tools/test_ic_closeout.py exist; commits 229bc006, 1a1ad30e and b9645df1 are in `git log`.
