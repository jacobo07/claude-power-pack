# Transparent Process Hibernation -- FASE A (install + ops + FASE B spec)

Status: **built + tested 2026-07-03** | Owner-approved scope (STOP #1): Shell-Wrapper
mechanism, idle>15min + not-hot trigger, ship-patches-Owner-installs.

Frees RAM by killing idle `claude.exe` panes and transparently rehydrating them
on the next keystroke via the `kclaude` wrapper. **Measured baseline at build
time: 56 `claude.exe` = 12.2 GB working set (~217 MB WS / ~1 GB commit each).**

---

## 1. What this is (honest guarantee)

Per CO-10 guarantee levels, this is a **WRAPPER-tier** economy: the only tier that
can actually act on the process lifecycle. It never fires without the daemon, the
daemon never kills a pane it cannot prove is idle + rehydratable, and every failure
mode leaves the process **alive** (fail-open).

The active pane is protected **structurally**: it is never idle, so it can never
clear the `idle > 15 min` gate. Foreground/loop panes are kept for the same reason
(a live loop is never idle) plus explicit gates.

## 2. Shipped + tested (already in the repo, no install needed to inspect)

| File | Role |
|---|---|
| `modules/cognitive_os/process_governor.py` | `decide`/`plan`/`enrich_panes` -- picks idle, not-hot, anchored, wakeable panes. Pure core. |
| `modules/cognitive_os/hibernate_runner.py` | `hibernate_pane` -- CO-07 store+verify -> arm wake flag -> kill, rollback on kill fail. |
| `modules/cognitive_os/rehydration.py` | `verify_rehydration` -- G4 identity gate (restored sid == resumed sid, else FAILED). |
| `tools/scan_panes.ps1` | live `claude.exe` -> raw pane records (read-only, never kills). |
| `tools/run_hibernation.py` | orchestrator: scan -> enrich -> plan -> hibernate. **DRY by default.** |
| `tools/kclaude.ps1` | (edited) sid beacon + hibernation park-and-resume. |
| `tools/test_hibernation.py` | **21/21 V-gates**, hermetic. |

Verify anytime:
```
python tools\test_hibernation.py            # 21/21, exit 0
powershell -File tools\scan_panes.ps1 | ...  # live pane JSON
python tools\run_hibernation.py --from-scan <scan.json>   # DRY plan, no kills
```

## 3. Install steps (the "you install" half -- global ~/.claude files)

Auto-mode cannot write `~/.claude/` global config, so these are yours to apply.

### 3.1 Mirror the patched wrapper (activates the 15 powershell panes)
The live wrapper is `~/.claude/bin/kclaude.ps1`; the repo `tools/kclaude.ps1` is
canonical. Sync it:
```powershell
Copy-Item "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\kclaude.ps1" `
          "$env:USERPROFILE\.claude\bin\kclaude.ps1" -Force
```
New panes launched from `bin\kclaude.cmd` / the pwsh profile now write a sid beacon
and honor the hibernation wake flag. (Existing panes activate on their next launch.)

### 3.2 Converge the 37 `kclaude.bat` panes (recommended: repoint)
`bin\kclaude.cmd` is already a 2-line shim to `kclaude.ps1`. The cleanest coverage
is to launch via `bin\kclaude.cmd` everywhere. **Option A (least churn):** point your
Cursor "Command Prompt" profile / `doskey claude=` at `%USERPROFILE%\.claude\bin\
kclaude.cmd` instead of `kclaude.bat`.
**Option B (patch kclaude.bat to a thin delegator):** replace its body with
```bat
@echo off
call "%USERPROFILE%\.claude\bin\kclaude.cmd" %*
```
so its first launch runs through `kclaude.ps1` (which owns the park loop). After
either, confirm `/restart` still lands in-pane (kclaude.ps1 keeps the restart-flag
loop). `lazarus-shell-autoresume.bat` already prefers `bin\kclaude.cmd` -- no change.

### 3.3 Register the daemon (Scheduled Task, ~every 5 min)
```powershell
$pp = "$env:USERPROFILE\.claude\skills\claude-power-pack"
$act = New-ScheduledTaskAction -Execute "powershell.exe" -Argument (
  "-NoProfile -ExecutionPolicy Bypass -Command " +
  "`"& '$pp\tools\scan_panes.ps1' > `$env:TEMP\pp_scan.json; " +
  "& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' " +
  "'$pp\tools\run_hibernation.py' --from-scan `$env:TEMP\pp_scan.json --live`"")
$trg = New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "PP-Hibernation" -Action $act -Trigger $trg
```
**Start in DRY** (drop `--live`) for a day, read the plans it would execute, then
add `--live`. Tune the threshold with `--idle-min N`.

## 4. Verification (Owner-run, empirical)
1. Leave a wrapped pane idle >15 min. Confirm its `claude.exe` is gone
   (`Get-Process claude`) and RAM dropped (compare `WorkingSet64` sum before/after).
2. Press a key in that pane -> status line -> claude rehydrates via `--resume`.
3. `python tools\run_hibernation.py --from-scan <scan> ` (DRY) shows the plan.
4. Rehydration identity: `python -m modules.cognitive_os.rehydration --archive-id
   <id> --expect-sid <sid>` -> `RECOVERED`.

## 5. FASE B -- host-limited (NOT built; honest boundary)

These require Cursor/Windows internals the PP cannot reach; documented, not faked.

- **Wake keystroke delivered as the message.** Today the first keystroke is a WAKE
  (consumed by the wrapper's `ReadKey`); the Owner then types. ConPTY `CONIN$`
  injection into resumed claude is unreliable on this host
  (`feedback_restart_opens_new_terminal_not_in_place`). Needs a Cursor terminal API
  or a claude-side resume-with-initial-message flag.
- **Raw non-wrapped panes.** A `claude.exe` with no `kclaude` parent can be reaped
  for RAM but cannot self-rehydrate. FASE A **keeps** them (Owner chose no-reap).
- **Full live-frame visual continuity.** The terminal **scrollback persists** while
  claude is dead (the wrapper stays alive, so Cursor keeps the buffer) -- you still
  see prior conversation text. The live TUI frame is swapped for the status line
  until rehydrate. Exact live-frame preservation is a host/tmux-style suspend
  feature Cursor does not expose.
- **Rehydrate-under-5s timing gate.** A real wall-clock SLA needs a live claude
  launch to measure; asserted at runtime (step 4.2), not unit-faked (Reality
  Contract: no timing theater).

## 6. Known FASE A limitations (by design, fail-safe)
- A **new, never-resumed** session has no sid beacon yet -> governor **keeps** it
  (no-sid fail-safe). Coverage grows as panes are resumed/beaconed.
- **Foreground/loop** detection is not reliable per-process inside Cursor; the
  `idle>15min` + not-hot guards are the real protection (the active/looping pane is
  never idle). Documented degradation, not a silent gap.
