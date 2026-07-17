<#
.SYNOPSIS
Snapshot Auto-Writer -- PP BL-CPCOS-AUTOWRITER-001 (2026-06-06)

.DESCRIPTION
Keeps the crash-restore artifacts fresh in the background so a crash at any
hour self-restores on the next Cursor open with ZERO Owner action. Each cycle:

  1. Regenerates ~/.claude/state/session_snapshot.json from the live CPC-OS
     pane registry (python -m modules.cpc_os.snapshot).
  2. Writes a .vscode/tasks.json into every repo in the snapshot so Cursor
     auto-runs `claude --resume <id>` per pane on folder open
     (python modules/cpc_os/vscode_autorun.py).

It does NOT open Cursor windows. restore_panes.ps1 -AutoRun is the INTERACTIVE
crash-recovery entry point (it reopens windows); a 15-minute background task
must only WRITE the tasks.json, never spawn windows -- so this composes the
vscode_autorun generator directly (the same merge-not-clobber, backup-first,
idempotent-skip unit restore_panes.ps1 -AutoRun uses).

Distinct from the daily \ClaudePP-SessionSnapshot task: that one zips
~/.claude/projects/ for disaster recovery (Layer 3). This one refreshes the
pane manifest + tasks.json for crash RESTORE. No overlap.

ASCII-ONLY (BL-2026-05-24): loaded by Task Scheduler -> powershell.exe 5.1
which uses the system ANSI codepage, NOT UTF-8. Keep this file 7-bit ASCII.

.PARAMETER Action
  start   -> register the task (every IntervalMinutes) + one immediate cycle
  stop    -> unregister the task
  status  -> show task state + snapshot age + repos with tasks.json
  run     -> a single cycle (invoked by Task Scheduler)

.PARAMETER IntervalMinutes
  Refresh cadence (default 15).

.EXAMPLE
  powershell -File tools\snapshot_auto_writer.ps1 -Action start
  powershell -File tools\snapshot_auto_writer.ps1 -Action status
  powershell -File tools\snapshot_auto_writer.ps1 -Action stop

.NOTES
  RunLevel = Limited (no UAC). Touches only user-owned files. Reversible via
  -Action stop.
#>
param(
    [ValidateSet("start","stop","status","run")]
    [string]$Action = "status",
    [int]$IntervalMinutes = 15
)

$TaskName = "pp-snapshot-writer"
$ScriptPath = $PSCommandPath
$PPRoot = Split-Path (Split-Path $ScriptPath -Parent) -Parent
$AutorunScript = Join-Path $PPRoot "modules\cpc_os\vscode_autorun.py"
$SnapshotJson = Join-Path $HOME ".claude\state\session_snapshot.json"
$LogFile = "$env:TEMP\pp-snapshot-writer.log"

function Write-Log($msg) {
    $ts = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    "$ts $msg" | Out-File -FilePath $LogFile -Append -Encoding ascii
}

function Resolve-PythonExe {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $fallback = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
    if (Test-Path $fallback) { return $fallback }
    return $null
}

function Invoke-Cycle {
    $py = Resolve-PythonExe
    if (-not $py) {
        Write-Log "[ERROR] python not found -- cannot run cycle"
        Write-Host "[ERROR] python not found"
        return 1
    }
    Push-Location $PPRoot
    try {
        # 1. Refresh the pane manifest from the registry. snapshot.py uses
        #    relative imports, so import it (single import -- avoids the
        #    `python -m` runpy double-import RuntimeWarning) and call it. cwd is
        #    PPRoot (Push-Location above) so `modules` resolves on sys.path.
        $env:PYTHONIOENCODING = 'utf-8'
        & $py -c "from modules.cpc_os.snapshot import generate_snapshot; print('snapshot:', generate_snapshot())" 2>&1 | ForEach-Object { Write-Log "[snap] $_" }
        $snapRc = $LASTEXITCODE
        # 2. Write .vscode/tasks.json per repo. PREFER the corrected pane_map.json
        #    (all repos, all panes -- refreshed by the PP-PaneMapUpdate task) over
        #    the legacy session_snapshot.json (which under-records repos+sids and,
        #    without --no-truncate, capped each repo to its live tab count -> the
        #    "1 pane per repo" + "only works in PP" automatic-path regressions).
        #    --pane-map implies no truncation, so every resumable pane of every
        #    repo becomes its own folderOpen task (the tasks.json Cursor auto-runs
        #    on a reboot -> shutdown restores like a restart). Fail-open: if the
        #    pane_map is missing, fall back to the legacy snapshot path so a cycle
        #    never writes nothing. No Cursor windows; idempotent-skip unchanged.
        #    --tiers OPEN-NOW,ACTIVE scopes the ALWAYS-ON folderOpen file to panes
        #    that were actually open, NOT 7 days of RECENT-tier history. Without it,
        #    allowAutomaticTasks:on would auto-launch every historical pane on open
        #    (PP measured 33 -> 4). Interactive full crash-restore stays in
        #    restore_panes.ps1 -AutoRun (no --tiers). T-REVIVAL-NOTRUNCATE-AUTORUN-HAZARD-001.
        $PaneMapJson = Join-Path $HOME ".claude\state\pane_map.json"
        if (Test-Path $PaneMapJson) {
            & $py $AutorunScript --pane-map $PaneMapJson --tiers OPEN-NOW,ACTIVE 2>&1 | ForEach-Object { Write-Log "[autorun] $_" }
            $genRc = $LASTEXITCODE
            Write-Log "[CYCLE] source=pane_map snapshot_rc=$snapRc autorun_rc=$genRc"
        } else {
            & $py $AutorunScript --snapshot $SnapshotJson 2>&1 | ForEach-Object { Write-Log "[autorun] $_" }
            $genRc = $LASTEXITCODE
            Write-Log "[CYCLE] source=snapshot(fallback) snapshot_rc=$snapRc autorun_rc=$genRc"
        }
        Write-Host "OK: cycle complete (snapshot_rc=$snapRc autorun_rc=$genRc)"
        return 0
    } finally {
        Pop-Location
    }
}

switch ($Action) {
    "start" {
        Write-Log "[START] Installing $TaskName (every ${IntervalMinutes}min)"
        if (-not (Test-Path $AutorunScript)) {
            Write-Host "ERROR: generator not found at $AutorunScript" -ForegroundColor Red
            Write-Log "[ERROR] generator missing: $AutorunScript"
            exit 1
        }
        try {
            $actionObj = New-ScheduledTaskAction `
                -Execute "powershell.exe" `
                -Argument ("-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$ScriptPath`" -Action run") `
                -WorkingDirectory $PPRoot

            $trigger = New-ScheduledTaskTrigger `
                -Once -At (Get-Date).AddMinutes(1) `
                -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)

            $settings = New-ScheduledTaskSettingsSet `
                -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
                -MultipleInstances IgnoreNew `
                -AllowStartIfOnBatteries `
                -DontStopIfGoingOnBatteries `
                -StartWhenAvailable

            $principal = New-ScheduledTaskPrincipal `
                -UserId "$env:USERDOMAIN\$env:USERNAME" `
                -LogonType Interactive `
                -RunLevel Limited

            Register-ScheduledTask `
                -TaskName $TaskName `
                -Action $actionObj `
                -Trigger $trigger `
                -Settings $settings `
                -Principal $principal `
                -Force | Out-Null

            Write-Log "[OK] Task registered"
            Write-Host "OK: Snapshot Auto-Writer installed"
            Write-Host "    Task:     $TaskName"
            Write-Host "    Interval: every $IntervalMinutes minutes"
            Write-Host "    Log:      $LogFile"
            Write-Host "    Running one cycle now..."
            Invoke-Cycle | Out-Null
        } catch {
            Write-Log "[ERROR] Register-ScheduledTask failed: $($_.Exception.Message)"
            Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
            exit 2
        }
    }

    "stop" {
        try {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
            Write-Log "[STOP] Task removed"
            Write-Host "OK: Snapshot Auto-Writer removed"
        } catch {
            Write-Host "Task not found or could not be removed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    "status" {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
            $lastRun = if ($info) { $info.LastRunTime } else { "never" }
            $lastResult = if ($info) { $info.LastTaskResult } else { "n/a" }
            Write-Host "OK: Snapshot Auto-Writer ACTIVE"
            Write-Host "    State:       $($task.State)"
            Write-Host "    Last run:    $lastRun"
            Write-Host "    Last result: $lastResult"
        } else {
            Write-Host "WARN: Snapshot Auto-Writer NOT installed"
            Write-Host "    Install: powershell -File tools\snapshot_auto_writer.ps1 -Action start"
        }
        if (Test-Path $SnapshotJson) {
            $age = [int]((Get-Date) - (Get-Item $SnapshotJson).LastWriteTime).TotalMinutes
            Write-Host "    Snapshot:    $age min old"
            try {
                $panes = Get-Content -Raw $SnapshotJson | ConvertFrom-Json
                $repos = $panes | Group-Object cwd
                $withTasks = 0
                foreach ($r in $repos) {
                    if (Test-Path (Join-Path $r.Name '.vscode\tasks.json')) { $withTasks++ }
                }
                Write-Host "    Repos:       $withTasks/$($repos.Count) have .vscode/tasks.json"
            } catch { }
        } else {
            Write-Host "    Snapshot:    MISSING"
        }
    }

    "run" {
        Write-Log "[RUN] cycle starting"
        Invoke-Cycle | Out-Null
    }
}

exit 0
