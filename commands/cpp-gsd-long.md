---
name: cpp-gsd-long
description: Start a multi-hour unattended /gsd-autonomous run as a Ralph MISSION — a turn that ends continues in the SAME background session; at the context wall a FRESH session continues the work (no compaction). Words like "autocompact" or "compact" in the request do not change this. Plain /gsd-autonomous is right for anything that fits in one context.
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
| turn end (no wall) | sweep: GSD still has work, the context is under 300k tokens and no background child of the worker is pending → stop it, then wake the **SAME session** (`claude --bg --resume <sid>`, no other flag — a flag makes the host start a copy). Same context epoch; counted by the no-progress halt and by `--max-cycles`. Off: `CPP_MISSION_CONTINUATION=off` | ledger `turn_continued`, `launch_cause` `TURN_CONTINUATION`/`resume` |
| context rotation | the wall was crossed this epoch (flag or `handoff_*` row), or the ended turn left ≥ 300k tokens resident → stop the worker, **wait for its pid**, launch a FRESH one | ledger `launch_claimed` / `launched`, `launch_cause` `CONTEXT_ROTATION`/`fresh` with `trigger` |
| background child pending | a `run_in_background` command or async agent the worker (or its subagent) launched has not reported, or its result is unconsumed → nothing is stopped (held up to 30 min) | ledger `relay_held` |
| rehydration | the supervisor renders the card at relay time (≤ 8 KB: reconcile-first, HEAD, dirty paths, the predecessor's note labelled as a claim) and passes it with `--append-system-prompt` — no hook in between | mission record `card` |
| end | GSD `ALL_COMPLETE` → `COMPLETED`, **also when it lands on the last budgeted turn** (GSD is asked before any budget halt); budget → `HALTED`; **3 consecutive epochs with no commit or work-tree change → `HALTED no_progress`, never renewed**; permission prompt → `BLOCKED` (surfaced, never replaced) | ledger |

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

**Capsule rotation (opt-in, `arm --rollover-protocol capsule-v2`)** — status: LIVE in code
(`tools/test_gsd_mission_capsule_v2.py`), not yet run on a real mission (T8 held). A fresh worker
then starts only after its predecessor's capsule is sealed and judged SAFE_TO_FORGET; the outgoing
worker is not stopped otherwise, and a mission whose capsule cannot be sealed even from durable state
goes `BLOCKED`. The successor launches with MCP stripped and cannot edit, write or run a mutating
command until it certifies (`tools/mission_capsule.py resume|certify --mission <m>`, named on its
card); 30 min without certifying parks the mission `BLOCKED`. Needs `--permission-mode auto` or
`bypassPermissions`. Omit the flag and the mission rotates exactly as before. Kill switch: the file
`~/.claude/state/rollover/capsule-v2.off` or `CPP_CAPSULE_ROLLOVER=off` (v2 missions then rotate the
legacy way). Spec: `vault/specs/mission-capsule-rollover.md`.

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
`MultipleInstances IgnoreNew`. The task limit kills wscript, never the python it started, so the
script enforces its own pass contract (2026-09-28): **one pass at a time** (a lease the OS drops
if the pass dies; an overlapping pass records `skipped`), missions **first** then the retired v2
marker stage, each stage **bounded** (600 s / 240 s) with its whole process tree killed on the
deadline, and a heartbeat on **every** pass — `~/.claude/state/gsd-sweep-heartbeat.json`
(`ran`/`skipped`/`running`, per-stage rc, seconds, timed_out). A heartbeat older than ~10 min
means the sweep is not running; the log alone cannot tell you that, it records only passes that
acted. Gate: `python tools/test_gsd_sweep_pass.py` (V-SWEEP-*). One relay pass can spend ~90 s asking the host, up to 240 s
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
python tools/test_gsd_epoch.py              # V-EPOCH-* (turn continuation vs context rotation, child hold)
python tools/gsd_epoch.py census            # fresh sessions BY CAUSE, continuations, compactions
python tools/gsd_epoch.py epochs --mission <id>   # one row per context epoch of a mission
python tools/test_cpp_gsd_long_routing.py   # V-ROUTE-* (Ralph is the only live path)
```
