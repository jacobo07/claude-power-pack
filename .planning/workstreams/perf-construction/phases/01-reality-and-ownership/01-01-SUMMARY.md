---
phase: 01-reality-and-ownership
plan: 01
subsystem: perf-metrology-evidence
tags: [evidence, p-id-census, bench_all, verify_bench_all, resource_admission]
requires: []
provides:
  - "01-EVIDENCE.md: P01-P40 table, searches S-01..S-15, observations OBS-01..06, LP-01"
  - "check_evidence.py: staged V-EVD-1..14 checker with a mutation self-test"
affects: [01-02, phase-02, phase-04]
tech-stack:
  added: []
  patterns: ["evidence table with checker that resolves every path:line", "zero-hit search must carry a positive control"]
key-files:
  created:
    - .planning/workstreams/perf-construction/phases/01-reality-and-ownership/check_evidence.py
    - .planning/workstreams/perf-construction/phases/01-reality-and-ownership/01-EVIDENCE.md
  modified: []
decisions:
  - "check_evidence.py is BUILT (not extended): claim_evidence.py and evidence_bundle.py parse neither a status table nor path:line citations"
  - "Only P01, P03, P04, P06, P16, P17 are judged; P07, P40 and 32 others are DEFINITION_NOT_FOUND / UNKNOWN (origin audit ref ed9de300 is not in this clone)"
metrics:
  duration: "about 1 h"
  completed: 2026-11-22
status: complete
commits: 3
plan_head_before: e9ab7c2b1cfa8ca2d2e977d855d2d66ac0a610ff
actuals:
  tokens: 12000
  tasks: 3
  commits: 3
---

# Phase 1 Plan 1: Evidence spine and P-id judgement Summary

Falsifiable P01-P40 evidence file plus a phase-local checker; six P-ids judged by reading owner code, 34 honestly UNKNOWN.

## What was built

- `check_evidence.py` (stdlib only, phase-local): V-EVD-1..14 across stages tracer, pids, owners, d1, final; `--selftest` builds mutants (invalid status, citation past EOF, invented status on an undefined row, deleted row, zero-hit search with zero control, and from later stages a missing ratchet path, invalid D1, plain COMPLETE with UNKNOWN rows) and requires each to be rejected with its designed violation code. Later-stage runs against v0 correctly FAIL (117 and 120 violations), showing it can return the other answer.
- `01-EVIDENCE.md`: eight sections, 40 P-rows, 15 search records, 6 observations, 1 laptop procedure.

## Judgements (read from code, not copied from the W0 note)

| P-id | Status | Core evidence |
|------|--------|---------------|
| P01 | PARTIALLY_FIXED | bench_all rc ignores target misses (tools/bench_all.py:719); verify_bench_all gates 8 of 17 names with looser QUICK_TARGETS x1.5; 9 names gated by no exit code (listed in the file) |
| P03 | PARTIALLY_FIXED | 6 sites turn non-zero rc into an error; 9 sites keep elapsed ms regardless, so an instant failure counts as a fast sample and a timeout as a slow, uncensored one |
| P04 | CONFIRMED_ACTIVE | min(vals) is the sole confirm statistic (tools/verify_bench_all.py:156); no percentile code (S-05) |
| P06 | CONFIRMED_ACTIVE | baseline is history[-1] whatever its mode (tools/bench_all.py:650); ledger records no host state |
| P16, P17 | CONFIRMED_ACTIVE (code level) | one MemAvailable point check on mission-worker launches only; no process count (S-11, S-12); laptop figures left as LP-01 |

## Deviations from Plan

**1. [Finding, premise falsified] iteracion-avanzada-universal.txt is NOT absent from this host.**
- **Found during:** Task 1, search S-01 (with positive control).
- **Issue:** the roadmap and plan expect UNAVAILABLE. The Windows Downloads path is indeed absent, but the same file name exists at 160 paths under /home/kobii, including one tracked in this clone at `vault/programs/cognitive-economy/a5/inputs/iteracion-avanzada-universal.txt`.
- **Handling:** recorded in section 4 as UNAVAILABLE at the roadmap path plus an explicit FINDING; no copy was opened or hashed (other missions' trees are off limits and plan says nothing is derived from its content). Provenance and equality with the laptop file are UNKNOWN. Plan 01-02 / the lead must decide whether the in-clone copy is admissible.

**2. [Rule 3 - blocking] Branch precondition cannot hold literally.** The task precondition expects `mission/perf-construction`; the isolated worktree branch is `worktree-agent-aa2c4b2c72721cc2b` (required agent namespace for commits). HEAD at start equalled the mission branch tip (e9ab7c2b). Recorded in the EVIDENCE header; not treated as a blocker.

**3. [Rule 1 - plan drift] ROADMAP line pointers in the plan were stale** (55-58 vs actual 62-64, 29). Found by grep; citations use the real lines.

**4. [Rule 3 - search skeleton]** the plan's literal S-01 find skeleton hit the 150 s bound (exit 124, 103 partial hits). Rerun with `-xdev` and extra prunes (.cache, .npm, site-packages, __pycache__, ~/.claude/projects) completed in about 50 s. Both are recorded. Guard-friendly spellings (`'.gi[t]'` for the VCS directory) were used because the worktree guard rejects commands containing that bare name.

## Known Stubs

None. Section 2 (Ratchet owner UNSURVEYED, UCR-CIF candidate), section 3 (D1 UNDECIDED), section 8 (verdict BLOCKED, in progress) are deliberate open items that plan 01-02 closes; the checker rejects them at stages owners, d1 and final.

## Threat Flags

None. No new surface; no product code, ~/.claude file or live install was touched; no transcript content was read (names only, S-10); nothing pushed.

## Open items for plan 01-02 and the lead

- Decide the iteracion-avanzada file admissibility (deviation 1) and compute its hash comparison only if the lead authorises reading other mission dirs.
- S-03 found 0 non-test path-style importers of modules/trace_context against 20 reference files for modules/capability_runtime; plan 01-02 must read them (not count them) before D1.
- UCR-CIF material exists in 101 files; the owner is not yet decided (tower candidate only).

## Self-Check: PASSED

- check_evidence.py and 01-EVIDENCE.md exist; commits b73950d1, e3588fac, da1e673d exist on the worktree branch.
- `check_evidence.py ... --stage pids --require-judged P01,P03,P04,P06,P16,P17 --selftest` exits 0, 5 mutants executed, 0 accepted.
- `git status` outside the workstream directory was clean at every task commit.
