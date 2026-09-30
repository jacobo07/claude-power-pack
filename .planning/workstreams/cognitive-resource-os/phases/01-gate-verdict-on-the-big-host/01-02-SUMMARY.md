---
phase: 01-gate-verdict-on-the-big-host
plan: 02
subsystem: testing
requires:
  - phase: 01-gate-verdict-on-the-big-host (plan 01)
    provides: "EVIDENCE.md sections 0-1: gates_verdict PASS, host python3 has no pytest"
provides:
  - "EVIDENCE.md 2a-2d: approved hash-checked pytest venv, bracketed full-suite run (PASS), test_tco corroboration (14/14)"
  - "EVIDENCE.md 3: no failures to classify"
  - "EVIDENCE.md 4: CRO-01 phase_verdict PASS, with a recorded deviation (suite ran at 016c19f, not 784e446)"
affects: ["phase 5 (push 016c19f; restate V-BASELINE-INTACT GEX44 = PASS in RESUMPTION/UKDL)"]
key-files:
  created: []
  modified:
    - .planning/workstreams/cognitive-resource-os/phases/01-gate-verdict-on-the-big-host/EVIDENCE.md
requirements-completed: [CRO-01]
completed: 2026-09-30
status: complete
supersedes: "the 2026-09-28 rejection-branch summary of this plan (commit eab20dc), kept in git history"
---

# Phase 01 Plan 02: Full pytest suite on GEX44 -- PASS

**Owner approved the pinned pytest 9.1.1 / pluggy 1.6.0 / iniconfig 2.3.0 install on 2026-09-30. The full suite ran
once under `timeout 1800` from the worktree root: rc 0, `194 passed, 4 skipped in 2.98s`, wall 3.2 s, zero moved
lines in the dirty-set bracket. tools/test_tco.py: TCO_PASS=14/14 with V-BASELINE-INTACT PASS. With gates_verdict
PASS (01-01), CRO-01 phase_verdict is PASS.**

## What ran
- Task 1: answered `approved` by the Owner (relayed by a laptop session over ssh; the 2026-09-28 rejection was an
  availability default, not a decision on the packages).
- Task 2: pins re-verified against the PyPI JSON API (3/3 sha256 match); venv with `--system-site-packages`;
  `pip install --require-hashes --no-deps --only-binary :all:` rc 0; bracketed suite run; test_tco run, bracketed.
- Task 3: failure set empty, so no classification and no 784e446 scratch worktree; `git worktree list` = 2 entries.

## Deviations
- **The venv already existed.** Commit 016c19f (2026-09-28 22:20) records an earlier pytest 9.1.1 run in this venv
  that aborted at collection (INTERNALERROR, rc 3, esprima absent), with no approval or install recorded in
  EVIDENCE.md. pip therefore installed nothing new. The installed files were verified against freshly
  hash-checked wheels file by file: 110/110 match (EVIDENCE 2a).
- **Not measured at 784e446.** `git diff --name-only 784e446 HEAD -- . ':(exclude).planning'` lists two owned
  Phase 5 docs and tests/test_cascade_populator.py (016c19f, peer-owned, makes the module skip without esprima).
  Without that change collection aborts on this host, so the PASS is about HEAD 016c19f. 016c19f is local-only.

## Verification
All automated checks in 01-02-PLAN.md Tasks 2 and 3 exit 0 (suite verdict recompute, pytest --version, tco lines
verbatim, failure table, phase-verdict composition, worktree count). Acceptance greps all at expected counts;
secret-shape grep 0; redactor leaves the file unchanged. The only check that does not hold is the 784e446 source
diff, recorded above and in EVIDENCE section 4.

## Next
Phase 5 follow-up: push 016c19f with the branch and restate V-BASELINE-INTACT (GEX44) = PASS at 016c19f in
RESUMPTION and UKDL. 01-VERIFICATION.md (2026-09-28, gaps_found) predates this run and needs a fresh verify pass.
