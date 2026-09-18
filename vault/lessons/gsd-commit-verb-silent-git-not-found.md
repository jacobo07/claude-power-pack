# GSD's commit verb reports success-shaped failure when git is off PATH

**Measured** 2026-09-19, claude-power-pack, during the first live `/cpp-gsd-long` run.

## What happened

The autonomous workflow commits each artifact through GSD's own verb:

```
node gsd-core/bin/gsd-tools.cjs query commit "docs(01): ..." --files "<path>"
```

On this host that returned **exit 0** with:

```json
{ "committed": false, "hash": null, "reason": "staging_failed",
  "error": "git: not found" }
```

Prepending `C:\Program Files\Git\cmd` to `PATH` for the call turned the same
command into `{"committed": true, "hash": "72fc059"}`.

## Why it matters more than it looks

This is the estate's already-documented PATH gap
(`vault/lessons/powershell-git-path-gap.md`: git is not on PowerShell's
`-NonInteractive` PATH here) arriving through a **third party's** code, and it
lands in the worst possible shape:

- **The process exits 0.** A caller that checks the exit code sees success.
- **The failure is a JSON field**, not a stream anyone watches. An autonomous
  run that commits a dozen artifacts would report nothing wrong while landing
  none of them.
- **It affects spawned agents, not just the orchestrator.** `gsd-planner` and
  `gsd-executor` run their own shells and call the same verb. Prepending PATH
  in the orchestrator's call does not reach them, and the env of an
  already-running `claude.exe` cannot be changed from inside it, so `setx`
  fixes only future sessions.

The general shape: **a wrapper that turns a missing dependency into a return
value inherits none of the caller's error handling.** Exit codes compose; JSON
fields do not.

## What to do

- Prepend `C:\Program Files\Git\cmd` to `PATH` in every `gsd-tools.cjs`
  invocation that may commit.
- After any GSD step that was supposed to commit, **verify the commit exists**
  (`git log -1 --format=%h%x20%s` via the absolute git path) rather than
  trusting the step returned.
- Do not read `exit=0` from a tool that reports its own outcome in a payload.
  Parse the payload.

## Not established

Whether other `gsd-tools` verbs that shell out (archive, cleanup, transition)
degrade the same way. Only `query commit` was measured.
