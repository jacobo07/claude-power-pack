# A hook wrapped in a console allocator writes to the terminal, not to you

**Measured 2026-09-11** (claude-power-pack, Owner report: "me pasa en todos mis
repos"). Sealed as `T-CONHOST-HEADLESS-TERMINAL-LEAK-001`.

## The symptom, and the three wrong suspects

The terminal blanks mid-session and the agent appears hung. It happens in every
repository, under every kind of task. Three explanations were reached for first,
over months, and all three are consistent with the symptom:

- the MSYS2 Bash bridge freezing (a real, separately-documented failure);
- the `[Tool result missing due to internal error]` multiplex clip;
- a dead-screen closer the Stop guard failed to enumerate.

All three were wrong here, and each one is expensive to chase. The actual cause
was not in the agent at all.

## The measurement

Two lines settle it, and neither needs a hypothesis:

```
conhost.exe --headless cmd.exe /d /c "echo hi"   ->  0 bytes captured
cmd.exe /d /c "echo hi"                          ->  4 bytes ("hi\r\n")
```

`conhost --headless` allocates a pseudoconsole. Its output does not travel back
through the parent's stdout pipe; it is written **directly to the attached
terminal**, out of band. That write carries the console init/teardown sequences
`ESC[?25l`, `ESC[2J`, `ESC[H`, `ESC]0;<title>`. `ESC[2J` erases the display,
`ESC[H` homes the cursor.

A third-party installer had registered such a wrapper in the **global**
`~/.claude/settings.json` across **11 events**, several with `matcher: "*"` —
including `PreToolUse`, which fires on every tool call in every repository.

## Two damages, and the quiet one is worse

1. **The screen is cleared** on every registered event. Visible, and misread as
   the agent hanging.
2. **The wrapped hook's output is discarded.** Invisible. The integration
   believes it is reporting; nothing receives it. A hook that returns 0 bytes is
   indistinguishable from a hook that had nothing to say.

## The rule

> **Before diagnosing an agent, read what the host runs around it.** A hook is
> code you did not write executing on every event you did not choose, and a
> wrapper in a hook command is a second process whose output destination is not
> the one the contract implies.

Check for a console allocator standing between the hook registration and the
real command: `conhost`, `cmd /c start`, `wt`, `powershell -WindowStyle`. The
byte comparison above is the instrument; it costs two commands and it cannot
return the wrong answer.

Repair by promoting the wrapped argv into the hook command itself. A console
child of an already-console process inherits the console: no window is created
and nothing flashes, which is the only thing the allocator was buying.

## DON'T

- **Don't assume a wrapper is transparent because the wrapped command is
  correct.** The wrapper decides where output goes, and "nowhere you can read"
  is one of its options.
- **Don't treat a 0-byte hook result as "the hook had nothing to report".**
  Distinguish *ran and said nothing* from *ran and the output went elsewhere*;
  they are the same value and different facts.
- **Don't repair this by deleting the integration.** The wrapper is the defect,
  not the hook. Unwrapping keeps the third-party feature and fixes both damages.
- **Don't hand-edit eleven blocks of a global JSON config.** Deterministic tool,
  backup first, idempotent, driven against synthetic fixtures — a hand edit that
  corrupts `settings.json` takes every hook in the estate down with it.

## Instrument

`tools/fix_conhost_hook_leak.py` — `--apply` unwraps, backs up first, and is a
no-op on a second run. Drills: `tools/test_conhost_hook_leak.py`, 9/9, both
directions, synthetic subjects so the drill outlives the defect.
