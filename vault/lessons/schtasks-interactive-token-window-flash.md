# T-SPAWN-WINDOW-002 — Scheduled-Task InteractiveToken window flash

**Sealed:** 2026-06-30 (HungProcesses audit, Block A)
**Extends:** T-SPAWN-WINDOW-001 (which covered hook spawns + settings.json launchers only)

## Symptom

Owner sees `.exe` / `cmd.exe` windows flash open and interrupt the screen during
normal work. F0 (commit b144eba) and T-SPAWN-WINDOW-001 already fixed all PP hook
spawns and settings.json hook launchers — yet the flashes continued.

## Root cause (the new source)

A Windows **Scheduled Task** running `LogonType=InteractiveToken` executes in the
Owner's interactive session. If its action launcher is a **console-subsystem app**
or an **unhidden shell**, Windows allocates a visible console each fire:

- `python.exe <script>` — console subsystem → flashes a console window.
- `powershell.exe ... -File ...` without `-WindowStyle Hidden` → flashes a PS window.
- `cmd.exe /c ...` → flashes (cannot self-hide); `cmd /c "python ..."` double-flashes.

`audit_spawn_windows.py` did **not** cover Scheduled Tasks at all — only hook
spawns and settings.json. That was the coverage gap.

Empirical (2026-06-30): 7 of 8 PP tasks were flashing — 5 `python.exe`
(ClaudePP-SessionSnapshot, PP-Miner-V2, PP-Normalize-Paths, PP-Sovereign-Miner,
PP-Vault-Summarize) + 2 unhidden PowerShell (PP-Playwright-MCP-Watchdog,
pp-snapshot-writer). Only PP-KickbacksGuard was clean (`-WindowStyle Hidden`).

## Fix (Owner-approved mechanism: pythonw + Hidden flag)

- Python tasks → `pythonw.exe` (GUI subsystem, no console allocated). Applied via
  the `ScheduledTasks` PS module (preserves Arguments exactly, no `schtasks /TR`
  quoting): `Set-ScheduledTask -TaskName N -Action (New-ScheduledTaskAction
  -Execute pythonw.exe -Argument <orig args>)`.
- PowerShell tasks → prepend `-WindowStyle Hidden` to Arguments.
- Note: a hidden PowerShell parent does NOT reliably hide a `python.exe`/`.cmd`
  child (the child is console-subsystem and gets a fresh console). For console
  apps the only robust no-flash is the windowless binary (`pythonw.exe`) or
  `LogonType=S4U` (session 0). Owner chose pythonw to keep the interactive
  context for snapshot tasks.

## Reversibility

Originals: the 5 python tasks had `Execute=python.exe` (same Arguments); the 2 PS
tasks lacked the leading `-WindowStyle Hidden`. Revert = swap Execute back / strip
the flag via the same `Set-ScheduledTask` call.

## Gate (durable)

`python tools/audit_spawn_windows.py --schtasks` enumerates root Scheduled Tasks,
parses each Exec action's Command+Arguments, and flags flash launchers. HR-001
honest scoping: a flashing task whose launcher path contains `claude-power-pack`
or `\.claude\` is **OWNED → gated FAIL**; any other (OneDrive/NVIDIA/Opera, and
the Owner's other-project tasks) is **ADVISORY only**. Post-fix:
`schtask_owned_fails=0`.

## Remaining (advisory — NOT PP-owned, not auto-fixed)

These flash too but belong to other projects; fixing them needs each project's
rules (e.g. production CostaLuz). Surfaced for Owner decision:

- `\CostaLuz-Gate-R156` — `cmd.exe /c gate_autorun_R156.cmd`
- `\KobiiNetworkHealthDaemonV2` — `cmd.exe /c "python.exe ..."` (double-flash)
- `\KobiiCountdownRender` — `powershell.exe` without `-WindowStyle Hidden`
- `\LaptOps` — `powershell.exe` without `-WindowStyle Hidden`
