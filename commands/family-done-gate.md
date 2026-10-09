---
name: family-done-gate
description: Judge a delivery against its family baseline (Tower S6 done-gate). Every active entry of the family's newest generation -- shown in the prompt or not -- gets APPLIED_VERIFIED, VIOLATED, DELEGATED, NOT_APPLICABLE or UNJUDGED against the subject repo. Report-only; run it before declaring a web_surface / kobiicraft_mode / persistent_state / wii_homebrew build done.
---

# /family-done-gate -- Family baseline done-gate

## When
The UserPromptSubmit hook printed a `Family baseline <family>/B<n>` block for this work, and the
work is about to be called done.

## Run
```
python ~/.claude/skills/claude-power-pack/tools/family_baseline.py judge <family> --repo <repo-root>
```
Declare an entry that does not fit with a reason: `--na <entry-id>="<reason>"` (an N/A with no
reason stays UNJUDGED). `--json` prints the full report.

## Reading it
- `VIOLATED` -- an evaluable check failed. Fix it or say why it does not apply.
- `UNJUDGED` -- prose check or instrument failure; never counted as applied. Judge it by hand and say so.
- Exit 1 = enforcement *would* have blocked. Nothing is refused: blocking is a separate Owner
  decision (spec `docs/superpowers/specs/2026-09-24-family-baselines-design.md` §7).
- Each report is stamped `<family>/B<n>` + generation SHA-256, the same stamp the prompt showed.
