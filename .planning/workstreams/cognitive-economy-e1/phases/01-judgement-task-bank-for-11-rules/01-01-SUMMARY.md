---
phase: 01-judgement-task-bank-for-11-rules
plan: 01
status: complete
completed: 2026-10-05
---
# 01-01 Summary: driver, validator, tests, gceg + eaat tasks

Built (bank-draft/): `_e1_common.py` (grade/selftest driver), `validate_bank.py` (POSIX validator: fresh BASE
worktree under /home/kobii/e1-runs, pin-copy scrub, stub grade, leak listing, index builder), `test_validate_bank.py`,
`task_gceg_product_page.py` (generated-content-needs-an-evidence-gate), `task_eaat_session_launch.py`
(effect-authority-across-transports).

Verification (worker epoch 2, in the commit clone):
- `task_gceg_product_page.py selftest` -> SELFTEST OK; `task_eaat_session_launch.py selftest` -> SELFTEST OK
- `test_validate_bank.py` -> E1BANK_PASS=23/23
- `validate_bank.py validate` -> VALIDATE-E1 2/2 base=78ba9e7414 pins=13/13 (bank_in_tree=none, worktree_removed=True)

Code review (pp-code-reviewer, WARNING 1H/1M/1L) -- all three fixed before commit:
- HIGH eaat `retry_over_other_transport` accepted "refused": now requires "attached" (or a raise). A
  requester-keyed solution now scores judgement 1/2 (was 2/2).
- MEDIUM gceg `delivery_bullet_without_fact` passed when every bullet was dropped: now also requires the
  descriptive bullet to survive. The drop-all mutant now fails it.
- LOW `jgrade` raised on a 300 s grade timeout: now returns a failed result (rc 124, "grade timeout").
Known limit (not fixed, arguable from the stub text): an eaat solution that ignores op_id and attaches every
same-worktree request scores 6/6; it never starts a second process, which is what the JUDGES text claims.

Deviation: commits are made in the clone `.claude/worktrees/e1-commitclone` (STATE.md decision COMMIT PLANE).
