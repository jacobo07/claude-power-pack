---
phase: 01-judgement-task-bank-for-11-rules
plan: 04
status: complete
completed: 2026-10-05
---
# 01-04 Summary: det, pyt, cr judgement tasks

Built: `task_det_exit_all.py` (durable-exit-transaction), `task_pyt_test_gate.py` (python/testing),
`task_cr_review_verdict.py` (common/code-review). Written by a subagent in /tmp (harness refused its writes under
the shared checkout path), placed in bank-draft by the orchestrator.

Review (pp-code-reviewer, APPROVE with 2 MEDIUM + 2 LOW coverage gaps), all fixed, each proven by a mutant that
scored full marks before and fails a judgement check after:
- cr `critical_without_proof` now covers every partial-proof combination (mutant cr_scenario_only: judgement 3/4).
- cr new judgement check `high_without_proof` (mutant cr_high_unproven: judgement 3/4).
- pyt `everything_skipped` fixture now has a skipped test that executed asserts (mutant pyt_sum_asserts: 2/3).
- det nothing-released checks also require a refusal (raise or "refused") (mutant det_lie_exited: 1/3).

Verify: each selftest SELFTEST OK; `validate --only J-det_exit_all,J-pyt_test_gate,J-cr_review_verdict` ->
VALIDATE-E1 3/3 base=78ba9e7414 pins=13/13, bank_in_tree=none.
