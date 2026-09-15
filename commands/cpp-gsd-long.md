---
name: cpp-gsd-long
description: Start a /gsd-autonomous run that survives context compactions — retunes GSD's context warnings, drops the autorun marker, then starts the run. Use for multi-hour unattended runs; plain /gsd-autonomous is right for anything that fits in one context.
argument-hint: "[--from <phase>] [--restore]"
---

# /cpp-gsd-long — unattended multi-cycle autonomous run

Spec: `vault/specs/gsd-autonomous-autocompact.md`.

A plain `/gsd-autonomous` halts at the first context wall: GSD says "wrap up"
at 35% remaining and "stop immediately" at 25%, while the Power Pack watchdog
compacts at 30% remaining — between the two. This command reorders those
events so a run can cross the wall and keep going.

## What it does

1. **Retunes GSD's fire-points** (gap A) so they sit below the compaction
   point instead of above it. The warnings stay on as a last-resort floor.
2. **Drops the autorun marker** (gap C, partial) — the record that says a run
   is in flight and which command re-enters it. `context-watchdog.py` reads it
   and appends "do NOT stop; re-issue this command after compacting" to the
   tier-2 message, replacing GSD's "wrap up".
3. **Starts the run.**

Tier-2 rearm (gap B) needs no setup: the watchdog clears its own debounce
whenever the context drops below 45% used, so every crossing fires, not just
the first.

## Steps

Run each from the project root, in order.

```powershell
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$pp = 'C:\Users\User\.claude\skills\claude-power-pack'

# 1. Lower GSD's context warnings below the compaction point.
& $py "$pp\tools\gsd_long_run_config.py" --apply --project .

# 2. Record the run. Use the bare command, not --from N: it re-enters at the
#    first incomplete phase, so it stays correct as phases complete, while a
#    pinned N goes stale the moment phase N finishes.
& $py "$pp\tools\gsd_autorun_marker.py" --write `
      --session $env:CLAUDE_CODE_SESSION_ID --command "/gsd-autonomous" --cwd .
```

Then invoke `/gsd-autonomous` (add `--from <phase>` only when the caller asked
to start somewhere specific — the marker still holds the bare form).

The variable is `CLAUDE_CODE_SESSION_ID`. Verified 2026-09-15: it holds this
session's id, while `CLAUDE_SESSION_ID` — the name that reads as the obvious
one — is empty, so a marker written with it lands under an invalid id and the
watchdog silently never finds it.

**Do not fall back to "the newest `%TEMP%\claude-ctx-*.json`".** Measured on
this host: the newest of those belonged to a different pane, so that fallback
marks somebody else's session as running your autonomous job. If the variable
is empty, stop and establish the id — there is no safe guess with panes open.

## When the run ends

```powershell
& $py "$pp\tools\gsd_autorun_marker.py" --clear --session $env:CLAUDE_SESSION_ID
& $py "$pp\tools\gsd_long_run_config.py" --restore --project .
```

`--restore` puts back exactly what the project had, including keys that were
absent before. Leaving the marker in place is not harmful but it will keep
telling future compactions in this session to re-issue the run.

`/cpp-gsd-long --restore` performs only this cleanup block.

## What this does NOT do

**It is not keystroke-free.** After each compaction the agent emits the resume
command as a trailing line and you press Enter once — the same one-keystroke
dispatch the `/compact` line already uses. Automatic typing of the resume
command was designed and refused by the auto-mode classifier (`Tmux Self
Drive`), so it is not shipped; see the spec's Honest limits.

Expect roughly one keystroke per compaction cycle, not one per phase.

## Done-gate

`python tools/test_gsd_autocompact.py` — 19 V-GSDAC-* gates. The live
end-to-end crossing (two consecutive compactions, run continuing at phase N+1)
is Owner-run and is not claimable from that suite: driving tier 2 in a test
would dispatch a real compaction into the running session.
