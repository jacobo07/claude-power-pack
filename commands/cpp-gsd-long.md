---
name: cpp-gsd-long
description: Start a /gsd-autonomous run that survives context compactions — retunes GSD's context warnings, drops the autorun marker, then starts the run. Use for multi-hour unattended runs; plain /gsd-autonomous is right for anything that fits in one context.
argument-hint: "[--from <phase>] [--restore]"
---

# /cpp-gsd-long — unattended multi-cycle autonomous run

Specs: `vault/specs/gsd-autonomous-autocompact.md` (v1),
`vault/specs/autocompact-per-session-flags.md`, `vault/specs/gsd-long-run-v2.md` (v2).

A plain `/gsd-autonomous` halts at the first context wall: GSD says "wrap up"
at 35% remaining and "stop immediately" at 25%, while the Power Pack watchdog
compacts at 30% remaining — between the two. This command reorders those
events so a run can cross the wall and keep going.

## What it does

1. **Retunes GSD's fire-points** (gap A) so they sit below the compaction
   point instead of above it. The warnings stay on as a last-resort floor.
   The previous values are parked in `~/.claude/state/gsd-long-run-backups/`,
   not in `config.json` (gsd-tools warns on unknown keys).
2. **Drops the autorun marker** (gap C) — the record that says a run is in
   flight, which command re-enters it, and its **budget**. `context-watchdog.py`
   reads it and appends "do NOT stop; re-issue this command after compacting"
   to the tier-2 message, replacing GSD's "wrap up".
3. **Starts the run.**

Tier-2 rearm (gap B) needs no setup: the watchdog clears its own debounce
whenever the context drops below 45% used, so every crossing fires.

## Steps

**Open the session IN the project you want to run.** The resumed command
executes in the session's own directory; `--cwd` cannot move it, and arming
refuses when the two differ.

Run each from the project root, in order.

```powershell
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$pp = 'C:\Users\User\.claude\skills\claude-power-pack'

# 1. Lower GSD's context warnings below the compaction point.
& $py "$pp\tools\gsd_long_run_config.py" --apply --project .

# 2. Record the run. Prefer the bare command: it re-enters at the first
#    incomplete phase, so it stays correct as phases complete. PIN --from N when
#    the roadmap carries tracks owned by OTHER sessions -- "first incomplete
#    phase" is then somebody else's Phase 1, and every resume re-enters it.
#    --mission is REQUIRED: 3-8 distinctive terms of the Owner-approved mission.
#    --max-cycles / --max-hours are the budget (defaults 12 resumes / 24 h).
& $py "$pp\tools\gsd_autorun_marker.py" --write `
      --session $env:CLAUDE_CODE_SESSION_ID --command "/gsd-autonomous" --cwd . `
      --mission "<term1>,<term2>,<term3>" --max-cycles 12 --max-hours 24
```

```
# 3. START THE RUN. This is a step, not a footnote.
```

**Invoke `/gsd-autonomous` now** — the same command string you recorded in step 2,
`--from N` included if you pinned one.

> **Steps 1 and 2 start nothing.** They make a run *survive* a compaction; they do
> not launch one. Stopping here leaves compaction-survival configured for a run
> that never began, and `gsd_long_run.py status` reports that state exactly the way
> it reports a healthy run — so nothing will tell you.
>
> Measured 2026-09-19 across this estate's own ledger: **4 of 9 markers were armed
> with no evidence a run ever started**, three of them from different sessions. It
> is not carelessness. Every event that would distinguish "started" from
> "abandoned" — `crossing`, `resume_requested`, `resume_confirmed` — fires only at
> the **first compaction**, which can be hours away. Until then the two states are
> indistinguishable by construction, which is why three sessions passed unnoticed.
>
> `gsd_autorun_marker.py --write` now prints this instruction itself, at the moment
> of arming. That print is the mechanism; this paragraph is only its explanation.

Step 2 exits 2 with `REFUSED: <reason>` and arms nothing when:

| refusal | meaning | fix |
|---|---|---|
| `mission freshness STALE` | the active milestone describes another mission | `/gsd-new-milestone` for the right one; never weaken the terms. **If the root milestone is another track's, live work, do not replace it** — use a workstream (below) |
| `invalid workstream name` | `--workstream` is not `[A-Za-z0-9._-]+` | pick a plain name |
| `this session runs in X but --cwd is Y` | the session was opened in another project | open the session in Y |
| `GSD parses 0 phases` | ROADMAP.md headings are not GSD phases (e.g. `W0…W8`) | restructure as GSD phases |
| `could not ask GSD` | gsd-tools/node unavailable — not the same as 0 phases | fix the GSD install |
| `nothing to run` | every phase is already complete | nothing to do |
| `resume command must start with '/'` | free text cannot be re-issued | use a slash command |

### A second mission in a shared repo: `--workstream` (LIVE since 2026-09-23)

When the root `.planning/` milestone belongs to another session's track, run the new
mission as a GSD workstream instead of replacing that milestone:

> ⛔ **Never `workstream.create` in a repo still in flat mode.** Measured 2026-09-23: on a flat
> `.planning/` it *migrates* the root `ROADMAP.md`, `STATE.md`, `REQUIREMENTS.md` and `phases/`
> into `workstreams/default/` -- every other pane's milestone vanishes from the root (git: `D`
> on all of them). Create the directory by hand; `workstream.set` needs only that it exists.
> With the root left flat, a session with no pointer still sees the root milestone.

```powershell
$n = (Get-Command node).Source; $gt = "$env:USERPROFILE\.claude\gsd-core\bin\gsd-tools.cjs"
New-Item -ItemType Directory -Force .planning\workstreams\<name>\phases   # NOT workstream.create -- see the warning above
& $n $gt query workstream.set <name> --raw --cwd .      # session-local: keyed by CLAUDE_CODE_SESSION_ID
# seed its STATE.md / ROADMAP.md (GSD phases) with the mission, then:
& $py "$pp\tools\gsd_autorun_marker.py" --write --session $env:CLAUDE_CODE_SESSION_ID `
      --command "/gsd-autonomous" --cwd . --mission "<terms>" --workstream <name>
```

The marker records `workstream`; mission freshness, the phase preflight, every resume
re-check and the sweep's finish test then read `.planning/workstreams/<name>/`, never the
root. A named workstream that does not exist is `UNREADABLE`, never a fallback to the root.
Gates: `V-MF-WS-*`, `V-MF-ARM-WS`, `V-MF-RESUME-WS` in `tools/test_gsd_mission_freshness.py`.

(Step 3 above is where you invoke it. Two cases call for `--from <phase>`: the
caller asked to start somewhere specific, **or** the roadmap holds tracks owned by
other sessions. In the second case the bare form is actively wrong — it re-enters
at the first incomplete phase across the whole roadmap, which is another session's
work, on every resume. Verify what the marker actually recorded:
`resume_command` in `~/.claude/state/gsd-autorun-<session-id>.json`.)

The variable is `CLAUDE_CODE_SESSION_ID` (`CLAUDE_SESSION_ID` is empty). Never
fall back to "the newest `%TEMP%\claude-ctx-*.json`" — it can belong to another
pane. If the variable is empty, stop and establish the id.

## What happens at each compaction

- **Crossing** (70% used): checkpoint, `/compact` line requested, ledger `crossing`.
- **Resume gate** (after the compaction): the run **halts** — marker cleared,
  ledger `halted`, the agent told to summarise and stop — when the budget is
  spent or the mission re-check is no longer FRESH. Otherwise the resume line
  is requested (ledger `resume_requested`, cycle counted). Under 1500 MB free
  RAM the agent first runs `gsd_long_run.py wait-ram` (bounded, 10 min).
- **Dispatch**: the daemon presses Enter only when the transcript's last
  assistant line is exactly the resume command (or starts with `/compact`);
  a line still wrong after 180 s is **refused**, never submitted.
- **Confirmation**: the watchdog records `resume_confirmed` when the transcript
  shows the command actually submitted.

## Is it working?

```powershell
& $py "$pp\tools\gsd_long_run.py" status                 # every armed run
& $py "$pp\tools\gsd_long_run.py" report --session <sid> # one run's verdict
```

`report` derives the verdict from `~/.claude/state/gsd-autorun-ledger.jsonl`:
**PROVEN** = at least 2 crossings, each followed by a confirmed resume ·
PARTIAL · UNPROVEN · NO_CROSSINGS.

## Sweep (every 5 minutes)

Task `PP-GsdLongRun-Sweep` (wscript + `tools/hidden_launch.vbs`, no window)
runs `tools/gsd_long_run_sweep.ps1` → `gsd_long_run.py sweep`:

- respawns the daemon when flags wait and no daemon is alive;
- **recovers** a run idle ≥ 20 min whose transcript ends on its resume line
  (or a `/compact` line) with nothing waiting: re-drops a validated flag;
- records other idle runs as `stalled` (once per transcript state);
- **finishes** runs whose milestone is complete and **reaps** markers whose
  transcript is gone or idle 48 h, then restores that project's config when
  no other marker uses it.

Actions are logged to `~/.claude/state/gsd-long-run-sweep.log` only when
something happened. Remove with
`Unregister-ScheduledTask -TaskName PP-GsdLongRun-Sweep -Confirm:$false`.

## When the run ends

The sweep cleans up on its own. To end a run by hand:

```powershell
& $py "$pp\tools\gsd_autorun_marker.py" --clear --session $env:CLAUDE_CODE_SESSION_ID
& $py "$pp\tools\gsd_long_run_config.py" --restore --project .
```

`--restore` puts back exactly what the project had, including keys that were
absent before. `/cpp-gsd-long --restore` performs only this cleanup block.

## Limits that remain

**Keystrokes.** Resumes still go through Enter, only while Cursor is the
foreground window. Each session drops its own flag and the daemon routes by
window title (`<project> - Cursor`): a flag is sent only while its own
project's window is in front; with no window for its project it goes to the
focused Cursor window; at most one Enter per window until focus leaves and
returns. **Run each long run in its own Cursor window** — two runs in one
window (two terminal tabs) cannot be told apart.

**Headless resume is deliberately not used.** `claude -p --resume <sid>` would
be a second process appending to the transcript the open pane owns — two
writers on one log with no lock.

**Live proof** of a multi-compaction run is produced by `report` on the next
real run; tests never dispatch a real compaction.

## Done-gate

```
python tools/test_gsd_autocompact.py        # V-GSDAC-*  (v1 loop)
python tools/test_autocompact_per_session.py # V-ACPS-*   (daemon routing + expect-line)
python tools/test_gsd_long_run.py            # V-GSDLR-*  (v2: preflight, gates, sweep, report)
```
