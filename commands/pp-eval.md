---
name: pp-eval
description: PP Self-Eval -- show whether Power Pack's layers (always-loaded context, hooks, skills) are measured to help, hurt or make no difference, from the automatic nightly ablation runs. Status, report, and manual harvest/night controls.
---

# /pp-eval -- is Power Pack measured to help?

Spec: `vault/specs/pp-self-eval.md`. Runs by itself: the Windows scheduled task `PP-SelfEval`
starts `tools/pp_eval.py night` at 03:30. You do not need to run anything for it to work.

## What to run

Default (no argument): print the report.

```
python ~/.claude/skills/claude-power-pack/tools/pp_eval.py report
```

- `status`   bank size, last night (including why it skipped), verdicts, last quota reading
- `harvest`  mine and validate more tasks now (no model calls)
- `night --dry-run`  show what tonight would run, without running it
- `install` / `uninstall`  the scheduled task

## Reading a verdict

- `NO_LOSS` -- removing the layer changed no task outcome on >= 4 tasks that can fail. A proposal
  lands in the Owner queue; nothing is changed automatically.
- `HARM` -- a task failed WITH the layer and passed without it, 2 of 2. Also queued.
- `LOSS` -- the layer is measured to help. Report only.
- `INSUFFICIENT` -- not enough pairs, or the tasks never fail (ceiling). Not evidence either way.

A night that did not run says why (quota ceiling, you were active, low RAM, lock) in
`~/.claude/state/pp-eval/nights.jsonl`. State lives in `~/.claude/state/pp-eval/`.
