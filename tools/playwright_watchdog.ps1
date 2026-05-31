<#
.SYNOPSIS
Playwright MCP Watchdog -- PP BL-PLAYWRIGHT-001 (Option A sealed 2026-05-31)

.DESCRIPTION
Auto-installs a Windows Task Scheduler task that invokes
playwright_stale_killer.ps1 periodically. The killer removes stale
@playwright/mcp node processes; the Claude Code plugin loader then
spawns fresh ones with a clean transport on the next Playwright use.

ASCII-ONLY (BL-2026-05-24): loaded by Task Scheduler -> powershell.exe 5.1
which uses the system ANSI codepage, NOT UTF-8. Non-ASCII bytes mis-parse
and produce phantom 'missing brace' errors. Keep this file 7-bit ASCII.

.PARAMETER Action
  start   -> register task + initial run
  stop    -> unregister task
  status  -> show task state + count of playwright procs
  run     -> single cycle (invoked by Task Scheduler)

.PARAMETER IntervalMinutes
Watchdog cadence (default 8). Must be < IdleThresholdMinutes for the
killer to fire before the transport actually disconnects.

.PARAMETER IdleThresholdMinutes
Passed through to the killer (default 10).

.EXAMPLE
powershell -File tools\playwright_watchdog.ps1 -Action start
powershell -File tools\playwright_watchdog.ps1 -Action status
powershell -File tools\playwright_watchdog.ps1 -Action stop

.NOTES
RunLevel = Limited (no UAC elevation required). The watchdog only kills
processes owned by the current user (the node playwright procs the plugin
loader spawned), so no admin rights are needed.
#>
param(
    [ValidateSet("start","stop","status","run")]
    [string]$Action = "status",
    [int]$IntervalMinutes = 8,
    [int]$IdleThresholdMinutes = 10
)

$TaskName = "PP-Playwright-MCP-Watchdog"
$ScriptPath = $PSCommandPath
$PPRoot = Split-Path (Split-Path $ScriptPath -Parent) -Parent
$KillerScript = Join-Path $PPRoot "tools\playwright_stale_killer.ps1"
$LogFile = "$env:TEMP\pp-playwright-watchdog.log"

function Write-Log($msg) {
    $ts = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    "$ts $msg" | Out-File -FilePath $LogFile -Append -Encoding ascii
}

function Count-PlaywrightProcs {
    $procs = Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and (
                $_.CommandLine -like "*@playwright/mcp*" -or
                $_.CommandLine -like "*playwright*cli.js*"
            )
        }
    if ($procs) { return @($procs).Count } else { return 0 }
}

switch ($Action) {
    "start" {
        Write-Log "[START] Installing watchdog task: $TaskName (every ${IntervalMinutes}min, threshold ${IdleThresholdMinutes}min)"

        if (-not (Test-Path $KillerScript)) {
            Write-Host "ERROR: killer script not found at $KillerScript" -ForegroundColor Red
            Write-Log "[ERROR] killer script missing: $KillerScript"
            exit 1
        }

        try {
            $actionObj = New-ScheduledTaskAction `
                -Execute "powershell.exe" `
                -Argument ("-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$ScriptPath`" -Action run -IdleThresholdMinutes $IdleThresholdMinutes")

            $trigger = New-ScheduledTaskTrigger `
                -Once -At (Get-Date).AddMinutes(1) `
                -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)

            $settings = New-ScheduledTaskSettingsSet `
                -ExecutionTimeLimit (New-TimeSpan -Minutes 2) `
                -MultipleInstances IgnoreNew `
                -AllowStartIfOnBatteries `
                -DontStopIfGoingOnBatteries

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
            Write-Host "OK: Playwright MCP Watchdog installed"
            Write-Host "    Task: $TaskName"
            Write-Host "    Interval: every $IntervalMinutes minutes"
            Write-Host "    Threshold: kills procs idle >= $IdleThresholdMinutes min"
            Write-Host "    Log: $LogFile"
        } catch {
            Write-Log "[ERROR] Register-ScheduledTask failed: $($_.Exception.Message)"
            Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
            exit 2
        }
    }

    "stop" {
        try {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
            Write-Log "[STOP] Watchdog task removed"
            Write-Host "OK: Playwright MCP Watchdog removed"
        } catch {
            Write-Host "Task not found or could not be removed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    "status" {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        $procCount = Count-PlaywrightProcs
        if ($task) {
            $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
            $lastRun = if ($info) { $info.LastRunTime } else { "never" }
            $lastResult = if ($info) { $info.LastTaskResult } else { "n/a" }
            Write-Host "OK: Watchdog ACTIVE"
            Write-Host "    State:        $($task.State)"
            Write-Host "    Last run:     $lastRun"
            Write-Host "    Last result:  $lastResult"
            Write-Host "    Procs alive:  $procCount playwright node processes"
            Write-Host "    Log:          $LogFile"
        } else {
            Write-Host "WARN: Watchdog NOT installed"
            Write-Host "    Procs alive:  $procCount playwright node processes"
            Write-Host "    Install:      powershell -File tools\playwright_watchdog.ps1 -Action start"
        }
    }

    "run" {
        Write-Log "[RUN] Watchdog cycle starting"
        if (-not (Test-Path $KillerScript)) {
            Write-Log "[ERROR] Killer script not found: $KillerScript"
            exit 1
        }
        try {
            & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
                -File $KillerScript -IdleThresholdMinutes $IdleThresholdMinutes
            Write-Log "[RUN] Cycle complete, killer exit=$LASTEXITCODE"
        } catch {
            Write-Log "[ERROR] Killer invocation failed: $($_.Exception.Message)"
        }
    }
}

exit 0
