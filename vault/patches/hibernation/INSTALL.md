# Hibernation — Owner-side activation runbook (INSTALL)

Everything an agent in auto-mode **cannot** do (HR-001: no writes to `~/.claude/`
global config, no Scheduled-Task registration, no killing live panes). Run these
yourself. Wrapper-convergence detail lives in [`README.md`](./README.md); this file
is the scannable command runbook + the daemon activation the README does not cover.

Paths assume `$cl = "$env:USERPROFILE\.claude"` and
`$pp = "$cl\skills\claude-power-pack"`.

---

## 1. Wrapper convergence (1 line per launcher)

| Launcher (count 2026-07-03) | Install command | Reverts with |
|---|---|---|
| `bin\kclaude.ps1` (ps1=23) | `Copy-Item "$pp\tools\kclaude.ps1" "$cl\bin\kclaude.ps1" -Force` | `$cl\bin\kclaude.ps1.bak-prehibernation-20260703` |
| `bin\kclaude.cmd` shim | `Copy-Item "$cl\bin\kclaude.cmd" "$cl\bin\kclaude.cmd.bak" -Force; Copy-Item "$pp\vault\patches\hibernation\kclaude.cmd" "$cl\bin\kclaude.cmd" -Force` | `Copy-Item "$cl\bin\kclaude.cmd.bak" "$cl\bin\kclaude.cmd" -Force` |
| `kclaude.bat` (bat=33) | `Copy-Item "$cl\kclaude.bat" "$cl\kclaude.bat.bak" -Force; Copy-Item "$pp\vault\patches\hibernation\kclaude.bat" "$cl\kclaude.bat" -Force` | `Copy-Item "$cl\kclaude.bat.bak" "$cl\kclaude.bat" -Force` |
| `lazarus-shell-autoresume.bat` (other=3) | **no patch** — converges automatically once `kclaude.bat` delegates to `bin\kclaude.cmd` | n/a |

Verify convergence (after relaunching a couple of panes):
```powershell
(Get-FileHash "$pp\tools\kclaude.ps1").Hash -eq (Get-FileHash "$cl\bin\kclaude.ps1").Hash  # True
Get-ChildItem "$env:TEMP\kclaude-pane-*.sid"   # beacons appear for resumed panes
```

---

## 2. Daemon — register the Scheduled Task in **DRY** first

DRY = the daemon prints the plan it *would* execute and touches nothing (no flags,
no kills). Run it as DRY for a day, read the plans, then promote to LIVE.

```powershell
$py = "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
# DRY: note there is NO --live flag here.
$cmd = "& '$pp\tools\scan_panes.ps1' > `$env:TEMP\pp_scan.json; " +
       "& '$py' '$pp\tools\run_hibernation.py' --from-scan `$env:TEMP\pp_scan.json"
$act = New-ScheduledTaskAction -Execute "powershell.exe" `
       -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$cmd`""
$trg = New-ScheduledTaskTrigger -Once -At (Get-Date) `
       -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "PP-Hibernation" -Action $act -Trigger $trg
```

Preview what it decides, on demand (safe, no kills), and read the loop-boundedness
advisories it surfaces:
```powershell
& "$pp\tools\scan_panes.ps1" > $env:TEMP\pp_scan.json
& $py "$pp\tools\run_hibernation.py" --from-scan $env:TEMP\pp_scan.json
#  -> "# loop-boundedness advisories (N)" lists stalled/unbounded panes (advisory only)
```

---

## 3. Promote DRY → LIVE (only after reading a day of DRY plans)

LIVE adds `--live`, so the daemon actually hibernates idle, not-hot, wakeable,
anchored panes. Re-register the same task with the `--live` flag appended:
```powershell
$cmd = "& '$pp\tools\scan_panes.ps1' > `$env:TEMP\pp_scan.json; " +
       "& '$py' '$pp\tools\run_hibernation.py' --from-scan `$env:TEMP\pp_scan.json --live"
$act = New-ScheduledTaskAction -Execute "powershell.exe" `
       -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$cmd`""
Set-ScheduledTask -TaskName "PP-Hibernation" -Action $act
```
Tune the threshold with `--idle-min N` (default 15). The active pane is protected
structurally (never idle → never clears the gate).

---

## 4. Empirical verification (the Reality Contract — measured, not estimated)

The RAM-freed and rehydrate-under-5s gates are runtime-asserted here (no unit
theater — `tools/test_hibernation.py` covers the mockable logic, 28/28 ×3):

```powershell
# baseline BEFORE hibernation:
$p = Get-Process claude; ($p | Measure-Object WorkingSet64 -Sum).Sum/1GB
# leave a wrapped pane idle >15min, let the daemon fire (or run §2 preview then --live once)
# baseline AFTER: the delta is the REAL RAM freed
$p2 = Get-Process claude; ($p2 | Measure-Object WorkingSet64 -Sum).Sum/1GB
```
1. Confirm the hibernated pane's `claude.exe` is gone (`Get-Process claude`).
2. Press a key in that pane → status line → claude rehydrates via `--resume` (<5s).
3. Identity gate: `& $py -m modules.cognitive_os.rehydration --archive-id <id> --expect-sid <sid>` → `RECOVERED`.

---

## 5. Kill switch / rollback

```powershell
Disable-ScheduledTask -TaskName "PP-Hibernation"     # stop the daemon (keeps the task)
Unregister-ScheduledTask -TaskName "PP-Hibernation" -Confirm:$false   # remove it entirely
```
Every wrapper file above has a `.bak`; revert with the "Reverts with" column in §1.
Fail-open by construction: if the daemon errors, every process stays alive.
