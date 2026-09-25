---
name: cpp-gsd-long
description: Start a multi-hour unattended /gsd-autonomous run as a Ralph MISSION — at every context wall a FRESH background session continues the work (no compaction). Words like "autocompact" or "compact" in the request do not change this. Plain /gsd-autonomous is right for anything that fits in one context.
argument-hint: "[--from <phase>] [--max-cycles N] [--max-hours H]"
---

# /cpp-gsd-long — unattended multi-cycle autonomous run

## Routing — read this first, it is not optional

**This command always arms a Ralph mission** (section below). That holds even when the request
says "autocompact", "compact", "compactar", "/compact", "clear", "survive compactions" or "use
autocompact". The Owner decided (2026-09-24) that those words mean "keep going past the
context wall", and on this estate that means a fresh session: the relay IS the automatic
`/clear`, because the successor starts with an empty context and a rehydration card.

- **Ralph is the only path (Owner decision 2026-09-25).** The v2 compact-and-resume path is
  retired for live runs: `gsd_autorun_marker.py --write` refuses against the real state
  directory with or without `--legacy-compact`, and no phrase unlocks it. Do not run
  `gsd_long_run_config.py --apply` either.
- Do **not** invoke `/gsd-autonomous` in THIS session after arming. The mission's background
  worker runs it; a second copy here would put two writers on one roadmap.
- The worker's native `--autocompact 600k` stays on as a safety net only.
- **A pane opened before a change to this file may still hold the old text.** If a run in an
  older window wrote a `gsd-autorun-<sid>.json` marker and no `gsd-mission-*.json` record, it
  was armed the retired way: arm it again from a fresh window.

Specs: `vault/specs/mission-continuity.md` (v3, the only live path). Historical:
`vault/specs/gsd-autonomous-autocompact.md` (v1), `vault/specs/gsd-long-run-v2.md` (v2).

## Default: Ralph mission (fresh session at every wall) — v3

**Owner decision 2026-09-23:** a long run continues in a **new session** at its context wall
instead of compacting — a fresh process frees the RAM a long-lived one accumulates (one
worker measured at ~660 MB working set). The mission, not the session, owns the work.

```powershell
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$pp = 'C:\Users\User\.claude\skills\claude-power-pack'
# from the project root (it must be a TRUSTED workspace -- `claude --bg` refuses otherwise):
& $py "$pp\tools\gsd_mission.py" arm --cwd . --command "/gsd-autonomous" --max-cycles 12 --max-hours 24
& $py "$pp\tools\gsd_mission.py" status
```

`arm` creates the mission record (`~/.claude/state/gsd-mission-<id>.json`) and launches worker 1
as `claude --bg`. From then on nothing needs the pane that armed it:

| step | who | evidence |
|---|---|---|
| worker starts | host (`claude --bg`) | the id the host prints for THIS launch |
| `LAUNCHING → RUNNING` | the worker's own SessionStart (hub), or the host listing that id | ledger `worker_acked` / `worker_adopted` |
| wall (40 % used) | judged MID-TURN on every tool call (`hooks/mission_wall.js`, PostToolUse) and again at Stop: finish + commit the step, end with `HANDOFF NOTE:` | `mission-wall-<sid>-e<N>.flag`, ledger `handoff_asked` |
| relay | sweep (every 5 min, out of band): GSD still has work → stop the worker, **wait for its pid**, launch the next | ledger `launch_claimed` / `launched` |
| rehydration | the supervisor renders the card at relay time (≤ 8 KB: reconcile-first, HEAD, dirty paths, the predecessor's note labelled as a claim) and passes it with `--append-system-prompt` — no hook in between | mission record `card` |
| end | GSD `ALL_COMPLETE` → `COMPLETED`; budget → `HALTED`; permission prompt → `BLOCKED` (surfaced, never replaced) | ledger |

A crashed **busy** worker is restarted by the host itself (measured) and is never replaced
by the mission — replacing it put two writers on the same work. The mission replaces only a
worker the host reports stopped/done while GSD still has work.

**A finished worker whose process lingers** (host says `done`, `claude.exe` still alive —
measured 12 h on 2026-09-25, blocking every relay) is terminated by the supervisor, but only
when its command line carries that worker's exact `--session-id`. A reused or unreadable pid
keeps the relay held, and the sweep log says which.

**Permission mode of workers** — `auto` by default (Owner decision 2026-09-24, pinned in
`arm --permission-mode` so a settings change cannot alter it). `acceptEdits` cannot run git
through PowerShell here, so a GSD run in that mode parks on a permission prompt (surfaced as
`BLOCKED`). A `BLOCKED` mission waits for you: answer the worker's prompt and the next sweep
resumes it.

**If the run moves into a git worktree** (`/gsd-autonomous` may enter one), the supervisor
follows it: the predecessor's transcript names the directory, GSD is asked there, and the
successor's card says `WORK TREE: … enter it first`. Launches stay in the trusted cwd.

## Is it working?

```powershell
& $py "$pp\tools\gsd_mission.py" status
Get-Content "$env:USERPROFILE\.claude\state\gsd-long-run-sweep.log" -Tail 20
```

`status` shows each mission's state, owner liveness and the supervisor's next action. A
`replace` that repeats pass after pass with a `stop:` or `held:` reason is a stuck relay; the
reason names what holds it.

## Sweep (every 5 minutes)

Task `PP-GsdLongRun-Sweep` (wscript + `tools/hidden_launch.vbs`, no window) runs
`tools/gsd_long_run_sweep.ps1`, which supervises every mission. Execution limit: **15 minutes**,
`MultipleInstances IgnoreNew`. One relay pass can spend ~90 s asking the host, up to 240 s
asking GSD (measured 67.5 s at 1.4 GB free; `SUPERVISE_GSD_TIMEOUT_S`), up to 90 s waiting for
the predecessor's pid and up to 180 s launching. When (re)registering:
`$t=Get-ScheduledTask -TaskName PP-GsdLongRun-Sweep; $t.Settings.ExecutionTimeLimit='PT15M'; Set-ScheduledTask -InputObject $t`.

## Retired: v2 compact-and-resume (removed from live use 2026-09-25)

The v2 path typed `/compact` and the resume command into the pane that ran the work. It
depended on a keystroke daemon, the owning terminal's extension and the pane's last line all
agreeing, and every refused request left the run parked with a full context and nothing to
relay it. Its code and tests remain (`tools/test_gsd_long_run.py`, `tools/test_gsd_autocompact.py`)
so the retired machinery stays honest, but it cannot arm a live run.

## Done-gate

```
python tools/test_gsd_mission.py            # V-MC-*    (Ralph: arm, relay, stop, linger)
python tools/test_cpp_gsd_long_routing.py   # V-ROUTE-* (Ralph is the only live path)
```
