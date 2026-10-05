---
phase: 01-judgement-task-bank-for-11-rules
status: passed
verified: 2026-10-05
---
# Phase 1 Verification

| # | Success criterion | Evidence | Status |
|---|---|---|---|
| 1 | Every task's judgement checks test the decision its rule governs; rule named in the index | bank/index.json maps 11 task ids to their rule files with JUDGES per check; three adversarial reviews (01-02/03/04) plus the 01-01 review drove 20 mutants: each wrong-per-rule solution now fails >= 1 judgement check, the rule-following cpc mutant passes 9/9 | PASS |
| 2 | No-model validation: selftests OK, naive fails ONLY judgement checks; log committed | bank/VALIDATE.log at d6887174: every selftest_rc=0 (selftest enforces naive fails >=1 judgement and 0 control), VALIDATE-E1 11/11 base=78ba9e7414 pins=13/13 | PASS |
| 3 | No grader reachable from a session's working tree, proven by listing | every OK line: tree_files=4306 bank_in_tree=none module_absent_at_base=True; BASE 78ba9e74 has no bank or plan paths (jbase refuses otherwise) | PASS (limit below) |
| 4 | Bank frozen by one commit recorded in BANK_FROZEN_AT | BANK_FROZEN_AT = d68871742a...; `git log --no-renames --diff-filter=A -- .../e1/bank` prints only it; freeze-check OK | PASS |

Limit carried to Phase 4 (accepted risk T-01-04 in 01-01-PLAN): a run worktree shares the repo's object store, so
`git log --all` / `git show <ref>:<path>` from inside a run tree can reach the bank. The Phase 4 report must audit
the transcripts for such access (as P3 REPORT R2 did).
