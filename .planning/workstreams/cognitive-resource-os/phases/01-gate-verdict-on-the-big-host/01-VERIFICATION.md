---
phase: 01-gate-verdict-on-the-big-host
verified: 2026-09-30T12:00:00Z
status: passed
score: 4/4 must-haves verified
supersedes: "01-verification-history-2026-09-28.md (status gaps_found, kept unchanged as the record of that run)"
gaps: []
---

# Phase 1: Gate verdict on the big host -- Verification Report (re-verified 2026-09-30)

The 2026-09-28 report found one gap: the full pytest suite never ran (01-02 Task 1 answered rejected, no Owner
reachable). The Owner approved the install on 2026-09-30 and 01-02 was re-run on GEX44. This report checks the
four ROADMAP Phase 1 success criteria against EVIDENCE.md as committed in `81bc0de`.

| # | Criterion | Status | Evidence (EVIDENCE.md) |
|---|-----------|--------|------------------------|
| 1 | Workstream gates recorded verbatim on GEX44 | VERIFIED | section 1: 25/25, 5/5, 7/7, 9/9, gates_verdict PASS (unchanged since 2026-09-28) |
| 2 | Full suite under a <=1800 s bound, bracketed by sorted dirty sets, PASS / FAIL / INCONCLUSIVE | VERIFIED | 2c: suite_rc 0, `194 passed, 4 skipped in 2.98s`, suite_wall_s 3.2; 2b: suite_moved_lines 0; suite_verdict PASS |
| 3 | Every failure classified | VERIFIED (vacuous) | section 3: failure set empty, class_counts all 0 |
| 4 | Commands, exit codes and verdicts on record | VERIFIED | 2a-2d and 4: install rc, pin re-check 3/3, venv file provenance 110/110, tco TCO_PASS=14/14, phase_verdict PASS |

All automated checks in 01-02-PLAN.md Tasks 2 and 3 were run on GEX44 and exit 0.

## Recorded caveat (not a gap)
The run is at HEAD `016c19f`, not the plan's base `784e446`: `016c19f` makes tests/test_cascade_populator.py skip
without esprima, and without it collection aborts on this host. EVIDENCE section 4 records this deviation. CRO-01's
PASS is therefore a statement about `016c19f`.
