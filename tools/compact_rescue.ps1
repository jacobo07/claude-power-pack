<#
.SYNOPSIS
Compact 95% Hang Rescue -- PP BL-COMPACT-001.
Owner-triggered escape when /compact freezes at 95%.

.DESCRIPTION
1. Finds the most-likely-stuck claude.exe parent process
2. Checks .jsonl recency (abort if session looks active)
3. Saves session ID for --resume
4. Kills claude.exe cleanly
5. Signals kclaude.bat/restart infra to resume on next launch

WHAT IS LOST: the compact summary being generated.
WHAT IS KEPT: every transcript turn pre-compact (.jsonl is
              append-only; each turn persisted before compact).

.PARAMETER DryRun
Report only -- do NOT kill anything.

.PARAMETER IdleThresholdSeconds
Seconds .jsonl must be idle before rescue proceeds (default 120).

.NOTES
ASCII-only per PP doctrine (PowerShell 5.1 ANSI codepage trap).
Fail-open by design: if guards say "looks active", rescue aborts.
#>
param(
    [switch]$DryRun,
    [int]$IdleThresholdSeconds = 120
)

$ErrorActionPreference = 'Continue'
$LogFile = "$env:TEMP\pp-compact-rescue.log"
$StateDir = "$env:USERPROFILE\.claude\state"
$ClaudeDir = "$env:USERPROFILE\.claude"

function Write-Log {
    param([string]$msg, [string]$Level = 'INFO')
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $line = "$ts [$Level] $msg"
    try {
        Add-Content -Path $LogFile -Value $line -Encoding ASCII -ErrorAction SilentlyContinue
    } catch {}
    Write-Host $line
}

Write-Log "Compact Rescue start (DryRun=$DryRun, threshold=${IdleThresholdSeconds}s)"

# --- Step 1: find claude.exe processes -----------------------------------
$claudeProcs = Get-Process -Name 'claude' -ErrorAction SilentlyContinue
if (-not $claudeProcs) {
    Write-Log "No claude.exe processes found" 'WARN'
    Write-Host "[OK] No claude.exe running. Nothing to rescue."
    exit 0
}
Write-Log ("Found {0} claude process(es)" -f @($claudeProcs).Count)

# --- Step 2: identify most-likely stuck process --------------------------
# Heuristic: highest WorkingSet (RSS) -- biggest in-memory transcript
# correlates with post-compact hang probability per repro doc.
$target = $claudeProcs | Sort-Object WorkingSet64 -Descending | Select-Object -First 1
$rss_mb = [math]::Round($target.WorkingSet64 / 1MB, 1)
Write-Log "Target PID=$($target.Id) RSS=${rss_mb}MB"

# --- Step 3: .jsonl recency guard ----------------------------------------
$jsonlFiles = @()
try {
    $jsonlFiles = Get-ChildItem -Path $ClaudeDir -Recurse -Filter '*.jsonl' `
        -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-1) } |
        Sort-Object LastWriteTime -Descending
} catch {
    Write-Log "jsonl scan error: $($_.Exception.Message)" 'WARN'
}

$idleSeconds = -1
$newestJsonl = $null
if ($jsonlFiles -and @($jsonlFiles).Count -gt 0) {
    $newestJsonl = $jsonlFiles[0]
    $idleSeconds = [int]((Get-Date) - $newestJsonl.LastWriteTime).TotalSeconds
    Write-Log "Newest .jsonl: $($newestJsonl.Name) idle=${idleSeconds}s"

    if ($idleSeconds -lt $IdleThresholdSeconds) {
        Write-Log "Session looks ACTIVE (idle ${idleSeconds}s < ${IdleThresholdSeconds}s) -- aborting" 'WARN'
        Write-Host ""
        Write-Host "[ABORT] Session looks active -- .jsonl written ${idleSeconds}s ago."
        Write-Host "        Wait $($IdleThresholdSeconds - $idleSeconds)s more, or override with:"
        Write-Host "        powershell -File tools\compact_rescue.ps1 -IdleThresholdSeconds 0"
        exit 1
    }
    Write-Log "Session idle for ${idleSeconds}s -- proceeding"
} else {
    Write-Log "No recent .jsonl in last hour -- proceeding (assumed stuck)" 'WARN'
}

# --- Step 4: capture sessionId for --resume ------------------------------
$sessionId = $env:CLAUDE_CODE_SESSION_ID
if (-not $sessionId -and $newestJsonl) {
    try {
        $firstLine = Get-Content -Path $newestJsonl.FullName -TotalCount 1 -ErrorAction SilentlyContinue
        if ($firstLine) {
            $parsed = $firstLine | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($parsed -and $parsed.sessionId) {
                $sessionId = $parsed.sessionId
            }
        }
    } catch {
        Write-Log "sessionId extract from jsonl failed: $($_.Exception.Message)" 'WARN'
    }
}
if ($sessionId) {
    Write-Log "Session ID captured: $sessionId"
} else {
    Write-Log "Session ID NOT captured (env+jsonl miss) -- manual --resume may be needed" 'WARN'
}

# --- Step 5: build rescue info object ------------------------------------
$rescueInfo = [ordered]@{
    timestamp       = (Get-Date).ToUniversalTime().ToString("o")
    target_pid      = $target.Id
    rss_mb          = $rss_mb
    session_id      = $sessionId
    cwd             = (Get-Location).Path
    rescue_reason   = "compact_95_hang"
    idle_seconds    = $idleSeconds
    jsonl_newest    = if ($newestJsonl) { $newestJsonl.FullName } else { $null }
}

if ($DryRun) {
    Write-Host ""
    Write-Host "=== DRY RUN -- no process killed ==="
    Write-Host (($rescueInfo | ConvertTo-Json -Depth 3))
    Write-Log "DRY RUN complete -- would kill PID=$($target.Id)"
    exit 0
}

# --- Step 6: write marker files ------------------------------------------
try {
    New-Item -ItemType Directory -Force -Path $StateDir -ErrorAction SilentlyContinue | Out-Null
} catch {
    Write-Log "state dir create failed: $($_.Exception.Message)" 'WARN'
}
try {
    ($rescueInfo | ConvertTo-Json -Depth 3) |
        Set-Content -Path "$StateDir\restart_pending.json" -Encoding UTF8
    Write-Log "Wrote $StateDir\restart_pending.json"
} catch {
    Write-Log "restart_pending.json write failed: $($_.Exception.Message)" 'WARN'
}
if ($sessionId) {
    try {
        $sessionId | Set-Content -Path "$StateDir\kclaude-restart-sid.txt" -Encoding ASCII
        Write-Log "Wrote $StateDir\kclaude-restart-sid.txt"
    } catch {
        Write-Log "sid file write failed: $($_.Exception.Message)" 'WARN'
    }
}

# --- Step 7: kill the stuck claude.exe -----------------------------------
Write-Log "Killing PID=$($target.Id) RSS=${rss_mb}MB" 'WARN'
try {
    Stop-Process -Id $target.Id -Force -ErrorAction Stop
    Write-Log "Process killed cleanly"
} catch {
    Write-Log "Stop-Process failed: $($_.Exception.Message)" 'ERROR'
    Write-Host ""
    Write-Host "[ERROR] Failed to kill PID=$($target.Id). Check permissions."
    exit 2
}

Write-Host ""
Write-Host "[DONE] Compact rescue executed"
Write-Host "       Killed: claude.exe PID=$($target.Id) (RSS=${rss_mb}MB)"
if ($sessionId) {
    Write-Host "       Session saved -- kclaude.bat will auto-resume on relaunch"
    Write-Host "       Manual command: claude --resume $sessionId"
} else {
    Write-Host "       Session ID not captured -- use 'claude --resume' picker"
}
Write-Host ""
Write-Host "NOTE: The compact summary was lost (mid-generation)."
Write-Host "      Your transcript is preserved (.jsonl is append-only)."
Write-Host "      Re-run /compact on the resumed session if needed."
exit 0
