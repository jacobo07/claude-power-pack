<#
.SYNOPSIS
    Zombie Process Slayer — Finds and kills orphan processes draining RAM.
.DESCRIPTION
    Detects zombie Python, Node, and Claude CLI processes that are:
    - Python with no command line (bare interpreter)
    - Python running known heavy scripts (anvil, crash_analyzer, block scanning)
    - Node processes not parented by Cursor or Claude desktop app
    - Claude CLI processes disconnected from any terminal
.USAGE
    .\kill_zombies.ps1              # interactive — shows candidates, asks before killing
    .\kill_zombies.ps1 -Force       # auto-kill without confirmation
    .\kill_zombies.ps1 -DryRun      # show candidates only, kill nothing
#>

param(
    [switch]$Force,
    [switch]$DryRun
)

$zombies = @()
$totalMB = 0

Write-Host "`n=== ZOMBIE PROCESS SLAYER ===" -ForegroundColor Cyan
Write-Host "Scanning for orphan processes...`n" -ForegroundColor Gray

# --- Python Zombies ---
$pythonProcs = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -or $_.Name -eq 'python3.exe' }
foreach ($p in $pythonProcs) {
    $cmd = if ($p.CommandLine) { $p.CommandLine } else { "(no command line)" }
    $mb = [math]::Round($p.WorkingSet64 / 1MB, 0)
    $isZombie = $false
    $reason = ""

    # Bare python with no script
    if (-not $p.CommandLine -or $p.CommandLine -match '^"?[^"]*python[^"]*"?\s*$') {
        $isZombie = $true
        $reason = "Bare Python interpreter (no script)"
    }
    # Known heavy scripts from previous sessions
    elseif ($p.CommandLine -match 'anvil|crash_analyzer|block_scan|region.*mca|stadium_inspect') {
        $isZombie = $true
        $reason = "Known heavy analysis script (orphan)"
    }
    # Any python using >500MB (Thin Client Doctrine threshold)
    elseif ($mb -gt 500) {
        $isZombie = $true
        $reason = "Exceeds 500MB Thin Client threshold (${mb}MB)"
    }

    if ($isZombie) {
        $zombies += [PSCustomObject]@{
            PID = $p.ProcessId
            Name = $p.Name
            MB = $mb
            Reason = $reason
            Cmd = $cmd.Substring(0, [math]::Min(100, $cmd.Length))
        }
    }
}

# --- Node.js Orphans ---
$nodeProcs = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' }
$cursorPids = (Get-Process -Name Cursor -ErrorAction SilentlyContinue).Id
$claudeDesktopPids = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'claude.exe' -and $_.ExecutablePath -match 'AnthropicClaude'
} | Select-Object -ExpandProperty ProcessId

$validParents = @($cursorPids + $claudeDesktopPids) | Where-Object { $_ }

foreach ($n in $nodeProcs) {
    $mb = [math]::Round($n.WorkingSet64 / 1MB, 0)

    # Skip small node processes (<50MB)
    if ($mb -lt 50) { continue }

    # Check if parented by Cursor or Claude Desktop
    $parentChain = @()
    $currentPid = $n.ParentProcessId
    $depth = 0
    $hasValidParent = $false

    while ($currentPid -and $depth -lt 10) {
        if ($validParents -contains $currentPid) {
            $hasValidParent = $true
            break
        }
        $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$currentPid" -ErrorAction SilentlyContinue
        if (-not $parent) { break }
        $currentPid = $parent.ParentProcessId
        $depth++
    }

    if (-not $hasValidParent -and $mb -gt 100) {
        $cmd = if ($n.CommandLine) { $n.CommandLine.Substring(0, [math]::Min(100, $n.CommandLine.Length)) } else { "(no cmdline)" }
        $zombies += [PSCustomObject]@{
            PID = $n.ProcessId
            Name = $n.Name
            MB = $mb
            Reason = "Orphan node (no Cursor/Claude parent, ${mb}MB)"
            Cmd = $cmd
        }
    }
}

# --- Report ---
if ($zombies.Count -eq 0) {
    Write-Host "No zombie processes found. System is clean." -ForegroundColor Green
    $mem = Get-CimInstance Win32_OperatingSystem
    $freeGB = [math]::Round($mem.FreePhysicalMemory / 1MB, 1)
    Write-Host "Current free RAM: ${freeGB}GB" -ForegroundColor Gray
    exit 0
}

Write-Host "Found $($zombies.Count) zombie process(es):`n" -ForegroundColor Yellow
$zombies | Format-Table PID, Name, MB, Reason -AutoSize
$totalMB = ($zombies | Measure-Object MB -Sum).Sum

Write-Host "Total recoverable RAM: ~${totalMB}MB`n" -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "[DRY RUN] No processes killed." -ForegroundColor DarkGray
    exit 0
}

# --- Kill ---
if (-not $Force) {
    $confirm = Read-Host "Kill these $($zombies.Count) processes? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Host "Aborted." -ForegroundColor Gray
        exit 0
    }
}

$killed = 0
foreach ($z in $zombies) {
    try {
        Stop-Process -Id $z.PID -Force -ErrorAction Stop
        Write-Host "  Killed PID $($z.PID) ($($z.Name), $($z.MB)MB)" -ForegroundColor Red
        $killed++
    } catch {
        Write-Host "  Failed to kill PID $($z.PID): $_" -ForegroundColor DarkRed
    }
}

Start-Sleep -Seconds 2
$memAfter = Get-CimInstance Win32_OperatingSystem
$freeAfter = [math]::Round($memAfter.FreePhysicalMemory / 1MB, 1)
Write-Host "`n$killed/$($zombies.Count) processes killed. Free RAM now: ${freeAfter}GB" -ForegroundColor Green
