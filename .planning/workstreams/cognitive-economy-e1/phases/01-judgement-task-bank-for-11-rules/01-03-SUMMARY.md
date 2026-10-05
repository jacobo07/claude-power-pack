---
phase: 01-judgement-task-bank-for-11-rules
plan: 03
status: complete
completed: 2026-10-05
---
# 01-03 Summary: cpc, slai, pert judgement tasks

Built: `task_cpc_compact_row.py` (capability-preserving-compaction), `task_slai_pane_sleep.py`
(state-lifetime-and-incarnation), `task_pert_freed_memory.py` (post-effect-resource-truth). Written by a subagent
in /tmp (harness refused its writes under the shared checkout path), placed in bank-draft by the orchestrator.

Review (pp-code-reviewer, WARNING 1 HIGH / 3 MEDIUM), all fixed and re-verified by the orchestrator:
- cpc HIGH: the stub made the rule-following answer (never delete in the same PR) fail controls. Stub now says
  this PR keeps the old row and delete_old schedules a separate follow-up PR after re-pinning; no-loss controls
  assert `lost == []`. Rule-following mutant cpc_never_delete now 9/9.
- cpc: new judgements `count_badge_removed`, `gating_condition_changed` (cpc_badge_vanish 3/5).
- slai: new judgement `stale_unsent_stamp_ignored` (slai_no_pid 2/3); JUDGES reworded to what each check tests.
- pert: new judgement `failed_but_gone_not_credited` (pert_requested_set 2/3).

Verify: selftests SELFTEST OK; `validate --only J-cpc_compact_row,J-slai_pane_sleep,J-pert_freed_memory` ->
VALIDATE-E1 3/3 base=78ba9e7414 pins=13/13.
