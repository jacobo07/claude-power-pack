#Requires -Version 5.1
# pending-keystrokes-daemon.ps1 - Zero-Command Plan, Component B.3 (sealed 2026-05-21).
#
# Source of truth: PP repo (claude-power-pack/hooks/).
# Deployment path: ~/.claude/hooks/pending-keystrokes-daemon.ps1
# Registration: spawned detached from Stop hook (or SessionStart) like
# auto-compact-sendkeys-daemon.ps1 - same single-flight + lock pattern.
#
# Purpose: generalized SendKeys dispatcher. Polls a directory of pending
# slash-command flags and types them into Cursor when it has focus. Does
# NOT replace auto-compact-sendkeys-daemon.ps1 - that one is dedicated to
# the /compact threshold flow with its own lifecycle; this is the
# arbitrary-command registry the Zero-Command plan B.3 calls for.
#
# Flag contract: any JSON file under ~/.claude/hooks/pending-keystrokes/
# with shape:
#     {
#       "uuid": "...",
#       "command_to_dispatch": "/speckit-spec",
#       "prompt": "...",                          # optional, appended as arg
#       "ttl_sec": 1800,                          # optional, default 600
#       "ts": <epoch>                             # required
#     }
# A `.disabled` marker in the same dir suspends ALL dispatch (Owner kill-switch).
#
# Cursor-focus discipline: never AppActivate, never steal focus. If Cursor
# is not the foreground window when the flag matures, the daemon keeps
# polling until TTL. Owner-cancel: delete or modify the flag file.
#
# Single-flight: PID-stamped lock file with stale-PID reclaim. Same pattern
# as auto-compact-sendkeys-daemon.ps1 - duplicate daemons cannot stack.

$ErrorActionPreference = 'SilentlyContinue'

$hooksDir   = Join-Path $env:USERPROFILE '.claude\hooks'
$queueDir   = Join-Path $hooksDir 'pending-keystrokes'
$disabledMk = Join-Path $queueDir '.disabled'
$lockFile   = Join-Path $hooksDir '.pending-keystrokes-daemon.lock'
$logFile    = Join-Path $hooksDir 'pending-keystrokes-daemon.log'

$ttlSec     = 180
$tickMs     = 500
$defaultFlagTtl = 600

function Log($msg) {
    try {
        $line = "$([DateTime]::UtcNow.ToString('o')) [pid $PID] $msg"
        Out-File -Append -FilePath $logFile -Encoding utf8 -InputObject $line
    } catch {
        # Final fallback: stderr. Demonstrable not silent (Woz #1).
        try { [Console]::Error.WriteLine("pending-keystrokes log fail: $($_.Exception.Message)") } catch { <# I/O fully closed #> }
    }
}

function Acquire-Lock {
    if (Test-Path $lockFile) {
        try {
            $line = (Get-Content $lockFile -Raw -ErrorAction Stop).Trim()
            $oldPid = [int]($line -split '\|')[0]
            if (Get-Process -Id $oldPid -ErrorAction SilentlyContinue) {
                return $false
            }
            Log "reclaiming stale lock pid=$oldPid"
        } catch {
            Log "lock read failed: $($_.Exception.Message); reclaiming"
        }
    }
    try {
        "$PID|$(Get-Date -Format o)" | Set-Content $lockFile -Encoding ASCII -Force -ErrorAction Stop
        return $true
    } catch {
        Log "lock write failed: $($_.Exception.Message)"
        return $false
    }
}

# Hoist Add-Type calls out of the per-tick path (code-review efficiency-#1).
# After first load .NET caches the type, but PS 5.1 still re-validates the
# source string on each call (~ms per call × 2 Hz × 180 s TTL = wasted work).
try {
    Add-Type -Namespace W -Name K -MemberDefinition @"
[System.Runtime.InteropServices.DllImport("user32.dll")]
public static extern System.IntPtr GetForegroundWindow();
[System.Runtime.InteropServices.DllImport("user32.dll")]
public static extern uint GetWindowThreadProcessId(System.IntPtr hWnd, out uint pid);
"@ -ErrorAction Stop
} catch {
    # Type may already exist if Add-Type ran in a prior daemon spawn in
    # this PS session. That's OK; the [W.K] type is reusable.
}
try {
    Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
} catch {
    # Same: idempotent assembly load; ignore "already loaded".
}

function Get-CursorForegroundPid {
    try {
        $hwnd = [W.K]::GetForegroundWindow()
        if ($hwnd -eq [IntPtr]::Zero) { return 0 }
        $pidOut = 0
        [void][W.K]::GetWindowThreadProcessId($hwnd, [ref]$pidOut)
        return [int]$pidOut
    } catch {
        Log "GetForegroundWindow failed: $($_.Exception.Message)"
        return 0
    }
}

function Is-CursorFocused {
    $fgPid = Get-CursorForegroundPid
    if ($fgPid -le 0) { return $false }
    try {
        $proc = Get-Process -Id $fgPid -ErrorAction Stop
        $name = $proc.ProcessName.ToLowerInvariant()
        return ($name -eq 'cursor' -or $name -eq 'code')
    } catch {
        return $false
    }
}

function Dispatch-Flag($flagPath) {
    try {
        $raw = Get-Content $flagPath -Raw -ErrorAction Stop
        # ConvertFrom-Json on PS 5.1 returns PSCustomObject; properties dotted.
        $obj = $raw | ConvertFrom-Json -ErrorAction Stop
    } catch {
        Log "flag parse failed $flagPath : $($_.Exception.Message); deleting"
        Remove-Item $flagPath -Force -ErrorAction SilentlyContinue
        return
    }

    $cmd = [string]$obj.command_to_dispatch
    if ([string]::IsNullOrWhiteSpace($cmd)) {
        Log "flag missing command_to_dispatch $flagPath; deleting"
        Remove-Item $flagPath -Force -ErrorAction SilentlyContinue
        return
    }
    $ttl = if ($obj.ttl_sec) { [int]$obj.ttl_sec } else { $defaultFlagTtl }
    $ts  = if ($obj.ts)      { [double]$obj.ts }    else { 0.0 }
    $ageSec = if ($ts -gt 0) { ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) - $ts } else { 0 }
    if ($ageSec -gt $ttl) {
        Log "flag expired age=${ageSec}s ttl=${ttl}s $flagPath; deleting"
        Remove-Item $flagPath -Force -ErrorAction SilentlyContinue
        return
    }

    # Build the text: command + (optional) verbatim prompt arg inside quotes.
    $arg = if ($obj.prompt) { ' "' + ($obj.prompt -replace '"', '\"') + '"' } else { '' }
    $text = "$cmd$arg"

    try {
        [System.Windows.Forms.SendKeys]::SendWait($text)
        Start-Sleep -Milliseconds 60
        [System.Windows.Forms.SendKeys]::SendWait('~')   # Enter
        Log "dispatched $cmd uuid=$($obj.uuid) flag=$flagPath"
    } catch {
        Log "SendKeys failed $flagPath : $($_.Exception.Message)"
        return
    }

    Remove-Item $flagPath -Force -ErrorAction SilentlyContinue
}

# Entry point
if (-not (Acquire-Lock)) { exit 0 }
if (-not (Test-Path $queueDir)) {
    try { New-Item -ItemType Directory -Path $queueDir -Force | Out-Null } catch { Log "queueDir mkdir failed: $($_.Exception.Message)"; exit 0 }
}

$start = Get-Date
Log "daemon start ttl=${ttlSec}s queue=$queueDir"

try {
    while (((Get-Date) - $start).TotalSeconds -lt $ttlSec) {
        if (Test-Path $disabledMk) {
            Start-Sleep -Milliseconds $tickMs
            continue
        }
        $flags = @(Get-ChildItem $queueDir -Filter '*.flag' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc)
        if ($flags.Count -gt 0 -and (Is-CursorFocused)) {
            foreach ($f in $flags) {
                Dispatch-Flag $f.FullName
                Start-Sleep -Milliseconds 250  # space dispatches so Cursor renders
            }
        }
        Start-Sleep -Milliseconds $tickMs
    }
    Log "daemon TTL exit"
} finally {
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
}
