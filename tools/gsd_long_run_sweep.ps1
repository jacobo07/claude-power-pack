#Requires -Version 5.1
# gsd_long_run_sweep.ps1 -- Task Scheduler entry (PP-GsdLongRun-Sweep, every 5 minutes, via
# wscript + tools/hidden_launch.vbs so nothing flashes on the desktop).
#
# Two stages: `gsd_mission.py supervise` (Ralph missions, the only live path) FIRST, then the
# retired v2 marker stage `gsd_long_run.py sweep`. Mission first because on 2026-09-27 the v2
# stage alone outlived the 5-minute schedule and supervise never got its turn (peer pane c2,
# fixed at the cause in 9f750fa).
#
# Pass contract (T7, 2026-09-28):
#  * ONE pass at a time. An exclusive handle on gsd-sweep.lease is held for the whole pass and
#    the OS drops it if this process dies; a pass that finds it held records `skipped`. The
#    Task Scheduler time limit kills wscript, never the python grandchild, so without this
#    passes overlapped (7 piled up, measured).
#  * Every stage is BOUNDED. On its deadline the stage's whole process tree is killed.
#  * Every pass writes gsd-sweep-heartbeat.json (ran / skipped, per-stage rc, seconds,
#    timed_out) whether or not anything acted, so an idle pass and a dead one differ.
#    The log below still records only passes that DID something.
# Overrides (tests only): CPP_SWEEP_PY, CPP_SWEEP_TOOLS_DIR, CPP_SWEEP_STATE_DIR,
#   CPP_SWEEP_MISSION_TIMEOUT_S, CPP_SWEEP_V2_TIMEOUT_S.
# Register:   see commands/cpp-gsd-long.md ("Sweep")
# Unregister: Unregister-ScheduledTask -TaskName PP-GsdLongRun-Sweep -Confirm:$false
$ErrorActionPreference = 'Stop'

function Get-Setting($name, $default) {
    $v = [Environment]::GetEnvironmentVariable($name)
    if ([string]::IsNullOrEmpty($v)) { return $default }
    return $v
}

$py       = Get-Setting 'CPP_SWEEP_PY' 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$tools    = Get-Setting 'CPP_SWEEP_TOOLS_DIR' $PSScriptRoot
$stateDir = Get-Setting 'CPP_SWEEP_STATE_DIR' (Join-Path $env:USERPROFILE '.claude\state')
$missionTimeout = [int](Get-Setting 'CPP_SWEEP_MISSION_TIMEOUT_S' '600')
$v2Timeout      = [int](Get-Setting 'CPP_SWEEP_V2_TIMEOUT_S' '240')
$log   = Join-Path $stateDir 'gsd-long-run-sweep.log'
$lease = Join-Path $stateDir 'gsd-sweep.lease'
$beat  = Join-Path $stateDir 'gsd-sweep-heartbeat.json'
$env:PYTHONIOENCODING = 'utf-8'
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Write-Beat($obj) {
    $tmp = "$beat.$PID.tmp"
    [System.IO.File]::WriteAllText($tmp, ($obj | ConvertTo-Json -Depth 5 -Compress), $utf8)
    Move-Item -LiteralPath $tmp -Destination $beat -Force
}

function Invoke-Stage($name, $argList, $timeoutS) {
    $out = Join-Path $stateDir "gsd-sweep-$name.$PID.out"
    $err = Join-Path $stateDir "gsd-sweep-$name.$PID.err"
    $t0 = [DateTime]::UtcNow
    $p = Start-Process -FilePath $py -ArgumentList $argList -WindowStyle Hidden -PassThru `
         -RedirectStandardOutput $out -RedirectStandardError $err
    # Touch the handle NOW: a PassThru process whose handle was never opened reports a null
    # ExitCode after it exits (measured: every stage read rc=null, success and crash alike).
    $null = $p.Handle
    $timedOut = -not $p.WaitForExit($timeoutS * 1000)
    if ($timedOut) {
        # The whole tree: gsd-tools / node / claude children included.
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
    return [pscustomobject]@{ name = $name; rc = $rc; timed_out = $timedOut; pid = $p.Id;
        secs = [math]::Round(([DateTime]::UtcNow - $t0).TotalSeconds, 1); text = $text.Trim() }
}

function Add-Log($prefix, $text) {
    if ($text -and $text -ne '[]') {
        $line = "{0} {1}{2}" -f [DateTime]::UtcNow.ToString('o'), $prefix, ($text -replace '\s+', ' ')
        [System.IO.File]::AppendAllText($log, $line + "`r`n", $utf8)
    }
}

New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
$started = [DateTime]::UtcNow.ToString('o')
try {
    $fs = [System.IO.File]::Open($lease, 'OpenOrCreate', 'ReadWrite', 'None')
} catch {
    # Never overwrite the holder's heartbeat: a `skipped` stamped over `running` every 5 minutes
    # hid a pass stuck past its bounds for ever (adversarial review F3, 2026-09-28).
    $skip = Join-Path $stateDir 'gsd-sweep-skip.json'
    $tmp = "$skip.$PID.tmp"
    [System.IO.File]::WriteAllText($tmp, (([ordered]@{ outcome = 'skipped';
        reason = 'another pass holds the lease'; at = $started; pid = $PID }) | ConvertTo-Json -Compress), $utf8)
    Move-Item -LiteralPath $tmp -Destination $skip -Force
    exit 0
}
try {
    Write-Beat ([ordered]@{ outcome = 'running'; started_at = $started; pid = $PID })
    $stages = @()
    $m = Invoke-Stage 'mission' @("`"$(Join-Path $tools 'gsd_mission.py')`"", 'supervise', '--actions-only') $missionTimeout
    Add-Log 'mission ' $m.text
    if ($m.timed_out) { Add-Log '' "SWEEP_STAGE_TIMEOUT stage=mission after ${missionTimeout}s; tree of pid $($m.pid) killed" }
    $stages += $m
    $v = Invoke-Stage 'v2' @("`"$(Join-Path $tools 'gsd_long_run.py')`"", 'sweep') $v2Timeout
    Add-Log '' $v.text
    if ($v.timed_out) { Add-Log '' "SWEEP_STAGE_TIMEOUT stage=v2 after ${v2Timeout}s; tree of pid $($v.pid) killed" }
    $stages += $v
    Write-Beat ([ordered]@{ outcome = 'ran'; started_at = $started;
        finished_at = [DateTime]::UtcNow.ToString('o'); pid = $PID;
        stages = @($stages | ForEach-Object { [ordered]@{ name = $_.name; rc = $_.rc;
            timed_out = $_.timed_out; secs = $_.secs } }) })
} finally {
    $fs.Dispose()
}
exit 0
