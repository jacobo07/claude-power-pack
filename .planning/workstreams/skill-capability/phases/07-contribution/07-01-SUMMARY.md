---
phase: 07-contribution
plan: 01
status: in-progress
---

# Phase 7 Plan 01: pillar E contribution verdict gate (running notes)

Written as the plan executes; finalized at the end.

## Task 1 (tracer) -- commit 6dd22c57

- `python3 tools/test_contribution_verdict.py --write-evidence` then default: CT_PASS=4/4, verdict NOT_SEPARABLE.
- Floor 3/4 (75 points), attained at (4,5), (4,6), (5,4), (6,4); equal k=5 floor 4/5; 45 allocations, 23 separate nothing.
- Committed effect 0 (authoritative), P stored 1 of 2.
- CE measurement one-off (`/tmp/ct_ce_check.py`, imports test_skill_capability_program then `ce._check_evidence`): `[]`.
- P3 dir unchanged (`git diff --quiet` rc 0).
## Task 2 (red drills) -- commit b8fdf436

RED run (`--drills`, before GRADES-AGREE / ROWS-PINNED / EVIDENCE-CURRENT existed): all 13 drills `<-- WRONG`;
the 11 row drills each `MISSING V-CT-GRADES-AGREE`, `grade-sources-disagree` read `all ok verdict NOT_SEPARABLE`
(the gap the clause closes), and both text drills `clause missing (name 'clause_rows_pinned_drill' / 'clause_evidence_current_drill' is not defined)`; rc 1.
Green after the clauses + commit: CT_PASS=8/8, verdict NOT_SEPARABLE, 13 drill sub-lines. Before the commit the same
run read `FAIL V-CT-EVIDENCE-CURRENT ... at HEAD differs` (the intended render -> commit -> gate order).
CLI red drills: `/tmp/ct-sep.jsonl` (P 5/5 vs N0 0/5) sep_rc=1, `FAIL V-CT-SEPARATION SEPARABLE ... (1 >= 3/4) ... P vs N0 1 (p=1/126)`,
`verdict: SEPARABLE`; `/tmp/ct-zero.jsonl` zero_rc=1, `INCONCLUSIVE V-CT-SOURCES control arm N0 UNMEASURED (0 measured rows)`,
`0/0` count 0.
<!-- gsd:write-continue -->
