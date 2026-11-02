# GPF-L2 laptop results (2026-11-02, plane DESKTOP-PMT5BS8, claude --model haiku, interactive ConPTY, PP root, CCR canary enforce)

## Why GPF-L2 was not applied as written
GPF-L2 (LAPTOP_STEPS.md) copied the GEX44-derived `global-CLAUDE.diet.md` over the laptop's `~/.claude/CLAUDE.md`. The two
source files differ on 140 lines. The laptop has sections GEX44 lacks: Windows Execution, Background Process Hygiene, the
Windows host probe. Copying would have deleted them. 3 of the 5 rules it stubs do not exist on the laptop (already skills, see
`skill-rule-index.md`). Instead, the diet was recompiled from the laptop's own file: `diet/global-CLAUDE.laptop.diet.md`
(19,289 -> 7,930 B; original in `diet/global-CLAUDE.laptop.original.md`). The 2 laptop rules (`common/code-review.md`,
`python/testing.md`) become 2-line stubs pointing at `~/.claude/skills/claude-power-pack/rules/...`.
Out of scope: the repo `CLAUDE.md`. Its laptop working copy (23,197 B) carries another pane's uncommitted edit, so the worker's
9,724 B version (a46ae9a3, GEX44) must not be landed over it until that edit is committed.

## Floor (call-1, N=4/arm, CTCT then TCTC) -> gpf-l2-laptop.json
control 78,236 / 78,231 / 78,530 / 78,571 (spread 0.43%) | diet 71,723 / 72,007 / 72,008 / 72,053
**delta -6,444 tokens per call-1 (-8.2%), MEASURED.**

## Quality (l6 Work Unit, 3 pairs CTC / TCT) -> gpf-l2-quality.json
correct C 3/3, T 3/3; page faults 0; repairs 0. processed/task: C 402,793 / 401,956 / 407,291; T 348,467 / 407,769 / 347,817
(mean -35,996, noisy: one T run took 8 calls).

## Applied live 2026-11-02 16:07 local
Backup `~/.claude/backups/gpf-apply-20261102T160717/` (CLAUDE.md, rules/common/code-review.md, rules/python/testing.md); the
live files were hash-checked equal to the measured original first. Post-apply live probe: call-1 **72,059** (gpf-l2-post-apply.json).
Revert: copy those three backup files back over `~/.claude/`.

## Driver defects fixed (Error -> Immunity)
1. `l5_canary_driver.run` / `l6.run` read the pty with a blocking `read()`: once the pane went quiet, the deadline was never
   checked (a probe hung 12 min). Fixed in l5 with a reader thread. GPF quality_run uses the same pattern.
2. Both found the probe's transcript as "newest transcript with the same cwd". With another pane active in the PP root
   (09664f88), that measures someone else's session. Fixed: `run(arm, session_id=True)` passes `--session-id` and reads that
   transcript only.
3. `l6_quality_driver.py` imports `p3_canary`, which no longer exists (vanished temp worktree,
   T-LAPTOP-TEMP-WORKTREE-FILES-VANISH-001). GPF aliases it to l5 (same three functions).
