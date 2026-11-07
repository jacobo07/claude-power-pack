---
covers: [pgrep, pkill, self-match, wait-loop, mission-worker, stall]
tier: T2
status: APPROVED (Owner "go ahead", 2026-11-07, session 280f506f)
---
# Self-matching pgrep guard (PreToolUse Bash)

## Problem (measured 2026-11-07, S17 W2, GEX44)
The S17 worker waited with `until ! pgrep -f "llm_fix run --cohort list --fns evidence/.../w2_pilot_id" ...`.
Claude Code runs a Bash call as `bash -c "... eval '<command>'"`, so the wrapper shell's own command line holds
the pattern. pgrep excludes only itself, so it always found the wrapper. The loop could never end. llm_fix finished
at ~15:46Z; the worker sat idle until the coordinator killed both loops at 15:52Z. `pkill -f` with such a pattern
kills the caller's own shell.

## Behaviour
- On PreToolUse Bash: for every `pgrep`/`pkill` call that has `-f` (alone or combined: `-af`, `-fl`, ...), take
  its pattern. If the pattern compiles as a regex AND matches the command text itself: **deny**, naming the pattern
  and three safe forms: bracket the first char (`[l]lm_fix`), wait on a pid (`while kill -0 $PID`), or wait on a log
  sentinel line.
- Skip (allow): no `-f`; a pattern holding `$` or a backtick (resolved at runtime, not judgeable); a pattern that
  does not compile; a pattern that does not match the command.
- Fail open on every internal error (malformed stdin, other tools).

## Out of scope
The sweep's live-idle detection (separate debt). Laptop registration.

## Acceptance
- `node hooks/tests/test-self-match-pgrep-guard.js`: the S17 command is denied, `pkill -f` self-match is denied,
  the bracket form, the pid wait, a no-`-f` pgrep, a `$VAR` pattern and a non-Bash tool are allowed, and bad stdin
  fails open. Both poles are exercised.
- GEX44: registered in `~/.claude/settings.json` PreToolUse Bash, file in `~/agora/mission-hooks/`. A real-host smoke
  pipes the S17 shape through the installed file and gets a deny.

## Rollback
Remove the settings entry (backup `settings.json.bak-pgrep-<ts>`) and the file.
