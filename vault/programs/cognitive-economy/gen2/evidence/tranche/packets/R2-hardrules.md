# Worker packet -- R2 HARD RULES mirror floor cut (tranche context-runtime-4)

Repo: C:\Users\User\.claude\skills\claude-power-pack (Windows). Use the PowerShell tool for every shell command;
git via `& 'C:\Program Files\Git\cmd\git.exe' -C <repo>`, python via
`& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Never Bash.

## Context
S1 measured the per-call floor and named the project CLAUDE.md HARD RULES mirror (~21,230 chars) as the next in-repo
controllable item. It is generated from `vault/hard_rules/HARD_RULES.md`, and it carries the stub entries HR-001..HR-007,
including the test entry HR-002 ("TEST CRITICAL bug for auto-propose pipeline ZZZ"). Owner decision: fix this at the
compiler source. Do NOT edit anything under ~/.claude outside this repo, and do NOT edit `~/.claude/CLAUDE.md`.

## Task
1. Find the compiler that writes the HARD RULES block into the project CLAUDE.md (search for the
   "HARD RULES (NON-NEGOTIABLE" heading and for writers of `vault/hard_rules/HARD_RULES.md`). Verify it exists
   before editing. Read `vault/plans/` or tests that pin its output, if any.
2. Remove the stub and test entries (HR-002 at minimum; HR-001, HR-003..HR-007 if they are auto-generated stubs
   without a real TRIGGER/STOP). Fix the source or the compiler's filter, never only the generated block, then
   regenerate the block with the compiler. Real rules (HR-SECRET-*, HR-CASCADE-*, HR-OUTPUT-*, HR-ONESHOT-*,
   HR-COST-*, HR-BACKLOG-*, HR-PREMISE-*, HR-SPEC-*, HR-CONTEXT-*, HR-STALLED-*, HR-NOVELTY-*) must stay.
3. Ship `tools/test_hard_rules_mirror.py` (V-HRM-* gates, exit 0 on pass): the regenerated block contains no
   HR-002 test entry; every real rule id above is still present; a fixture with a stub entry is filtered and a
   fixture with a real entry is kept (both poles).
4. Measure: CLAUDE.md chars before and after, and the mirror block chars before and after, each with the command.
   Report estimated tokens as chars/4 and label them estimates. Do NOT launch a live probe session (its spend would
   not be metered in this tranche); write `live probe: PENDING` in the receipt.

## Rules
- Pathspec commits only, never push, never touch files you did not change. End each message with
  `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
- Write `vault/programs/cognitive-economy/gen2/evidence/tranche/R2-receipt.md`: verdict (PASS / UNDECIDED / FAIL),
  which entries were removed and why, commands with exit codes, the measurements, and `COMMITS: <hash ...>`.
- Stop and write the receipt before your call budget runs out.
