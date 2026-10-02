#Requires -Version 5.1
# goal_sweep.ps1 -- Task Scheduler entry (PP-GoalSweep, every 5 minutes, via wscript +
# tools/hidden_launch.vbs so nothing flashes). SPEC-GOAL-SWEEP-SCHEDULED.
#
# One stage: `gsd_x_goal.py sweep-all` -- every goal the store marks autonomous, gate epochs
# only (anything that spends an account is reported, never dispatched). Sibling of
# gsd_long_run_sweep.ps1 (PP-GsdLongRun-Sweep), whose pass contract this copies:
#  * ONE pass at a time: an exclusive handle on goal-sweep.lease for the whole pass; a pass
#    that finds it held records `skipped` in goal-sweep-skip.json and leaves the beat alone.
#  * The stage is BOUNDED; on its deadline the stage's whole process tree is killed.
#  * Every pass writes goal-sweep-pass.json (ran, rc, seconds, timed_out). The python side
#    writes gsd-x/sweep_heartbeat.json (what it saw and did). The log records only passes
#    that printed something (acted or refused).
# Overrides (tests only): CPP_SWEEP_PY, CPP_SWEEP_TOOLS_DIR, CPP_SWEEP_STATE_DIR,
#   CPP_GOAL_SWEEP_TIMEOUT_S.
# Unregister: Unregister-ScheduledTask -TaskName PP-GoalSweep -Confirm:$false
$ErrorActionPreference = 'Stop'

function Get-Setting($name, $default) {
    $v = [Environment]::GetEnvironmentVariable($name)
    if ([string]::IsNullOrEmpty($v)) { return $default }
    return $v
}

$py       = Get-Setting 'CPP_SWEEP_PY' 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$tools    = Get-Setting 'CPP_SWEEP_TOOLS_DIR' $PSScriptRoot
$stateDir = Get-Setting 'CPP_SWEEP_STATE_DIR' (Join-Path $env:USERPROFILE '.claude\state')
$timeoutS = [int](Get-Setting 'CPP_GOAL_SWEEP_TIMEOUT_S' '240')
$log   = Join-Path $stateDir 'goal-sweep.log'
$lease = Join-Path $stateDir 'goal-sweep.lease'
$pass  = Join-Path $stateDir 'goal-sweep-pass.json'
$env:PYTHONIOENCODING = 'utf-8'
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Write-Json($path, $obj) {
    $tmp = "$path.$PID.tmp"
    [System.IO.File]::WriteAllText($tmp, ($obj | ConvertTo-Json -Depth 5 -Compress), $utf8)
    Move-Item -LiteralPath $tmp -Destination $path -Force
}

New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
$started = [DateTime]::UtcNow.ToString('o')
try {
    $fs = [System.IO.File]::Open($lease, 'OpenOrCreate', 'ReadWrite', 'None')
} catch {
    Write-Json (Join-Path $stateDir 'goal-sweep-skip.json') ([ordered]@{ outcome = 'skipped';
        reason = 'another pass holds the lease'; at = $started; pid = $PID })
    exit 0
}
try {
    Write-Json $pass ([ordered]@{ outcome = 'running'; started_at = $started; pid = $PID })
    $out = Join-Path $stateDir "goal-sweep.$PID.out"
    $err = Join-Path $stateDir "goal-sweep.$PID.err"
    $t0 = [DateTime]::UtcNow
    $p = Start-Process -FilePath $py -WindowStyle Hidden -PassThru `
         -ArgumentList @("`"$(Join-Path $tools 'gsd_x_goal.py')`"", 'sweep-all') `
         -RedirectStandardOutput $out -RedirectStandardError $err
    $null = $p.Handle   # an unopened PassThru handle reports a null ExitCode
    $timedOut = -not $p.WaitForExit($timeoutS * 1000)
    if ($timedOut) {
        & taskkill.exe /PID $p.Id /T /F 2>&1 | Out-Null
        $p.WaitForExit(10000) | Out-Null
    }
    $text = ''
    foreach ($f in @($out, $err)) {
        if (Test-Path -LiteralPath $f) {
            $text += [System.IO.File]::ReadAllText($f, $utf8)
            Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue
        }
    }
    $rc = $null
    if (-not $timedOut) { $rc = $p.ExitCode }
    $text = $text.Trim()
    if ($timedOut) { $text = "SWEEP_STAGE_TIMEOUT after ${timeoutS}s; tree of pid $($p.Id) killed. $text" }
    if ($text) {
        $line = "{0} rc={1} {2}" -f [DateTime]::UtcNow.ToString('o'), $rc, ($text -replace '\s+', ' ')
        [System.IO.File]::AppendAllText($log, $line + "`r`n", $utf8)
    }
    Write-Json $pass ([ordered]@{ outcome = 'ran'; started_at = $started;
        finished_at = [DateTime]::UtcNow.ToString('o'); pid = $PID; rc = $rc;
        timed_out = $timedOut; secs = [math]::Round(([DateTime]::UtcNow - $t0).TotalSeconds, 1) })
} finally {
    $fs.Dispose()
}
exit 0
