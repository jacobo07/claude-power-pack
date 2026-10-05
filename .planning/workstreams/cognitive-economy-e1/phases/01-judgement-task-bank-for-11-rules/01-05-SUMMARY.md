---
phase: 01-judgement-task-bank-for-11-rules
plan: 05
status: complete
completed: 2026-10-05
---
# 01-05 Summary: move, freeze-check, single freeze commit, BANK_FROZEN_AT

- `freeze_check(repo, bank_rel, frozen_file, expected_tasks=11)` + CLI `freeze-check` added to validate_bank.py
  (written by a subagent in e1, diff read by the orchestrator). Tests: E1BANK_PASS=30/30 (six
  V-E1BANK-FREEZE-* gates + V-E1BANK-FREEZE-RENAME).
- bank-draft/ moved to bank/ in the commit clone; `index --write` (11 tasks); `validate --log bank/VALIDATE.log`:
  PINS 13/13, 16 SHA256 lines, 11 OK lines in contract order, all with bank_in_tree=none,
  pin_copies_removed=rules/common/code-review.md,rules/python/testing.md, pin_rescan=0, worktree_removed=True;
  `VALIDATE-E1 11/11 base=78ba9e7414 pins=13/13`; 0 BAD lines. /home/kobii/e1-runs empty afterwards.
- Freeze commit `d68871742adefe392728370d82b69991a4437f79` (17 A under bank/, 15 D under bank-draft/).
  BANK_FROZEN_AT committed in `efab0084`. `freeze-check` -> FREEZE-CHECK OK d68871742a (in the clone and in e1).

Deviation found: the plan's verify `grep '^OK J-'` matches nothing (log lines read `OK  J-` with two spaces), so
its `test -z` clause was vacuous. Re-checked with `^OK +J-`: 11 lines, 0 without the exact pin scrub.
