---
covers: [pgrep, pkill, self-match, wait-loop, mission-worker, stall]
tier: T2
status: APPROVED (Owner, 2026-11-07)
---
# Self-matching pgrep guard (PreToolUse Bash)

## Problem (measured 2026-11-07, a long-running mission worker on a remote Linux host)
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
Detecting a worker that sits idle while its wait never ends (separate work).

## Registration
The hook does nothing until it is registered. Add it to `~/.claude/settings.json`:
```json
{"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
  {"type": "command", "command": "node /path/to/claude-power-pack/hooks/self_match_pgrep_guard.js"}]}]}}
```
Merge it into an existing `PreToolUse` list rather than replacing the list.

## Acceptance
- `node hooks/tests/test-self-match-pgrep-guard.js`: the stall command is denied, `pkill -f` self-match is denied,
  the bracket form, the pid wait, a no-`-f` pgrep, a `$VAR` pattern and a non-Bash tool are allowed, and bad stdin
  fails open. Both poles are exercised.
- On the host where it was first deployed, a real-host smoke piped the stall shape through the installed file and got
  a deny, and a real `claude -p` Bash call with that shape was denied.

## Rollback
Remove the settings entry (back up `settings.json` first) and the file.
