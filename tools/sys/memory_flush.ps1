<#
.SYNOPSIS
    Memory Flush Orchestrator — Unified RAM cleanup via kill_zombies + priority manager.
.DESCRIPTION
    Orchestrates existing tools in sequence:
    1. kill_zombies.ps1 -Force (purge orphan processes)
    2. electron_priority_manager.ps1 -Once (rebalance Cursor priority + trim working sets)
    Reports before/after RAM and exits with health code.
.USAGE
    .\memory_flush.ps1              # full flush — kill zombies + rebalance priorities
    .\memory_flush.ps1 -CheckOnly   # report RAM status only, touch nothing
    .\memory_flush.ps1 -Verbose     # full flush with detailed output from each tool
#>

param(
    [switch]$CheckOnly,
    [switch]$Verbose,
    [double]$HealthyGB = 3.0,
    [double]$CriticalGB = 1.5
)

$toolsRoot = (Resolve-Path "$PSScriptRoot\..").Path

function Get-RamSnapshot {
    try {
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
        $totalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
        if ($totalGB -le 0) { throw "Invalid total memory" }
        $usedPercent = [math]::Round((1 - $freeGB / $totalGB) * 100, 1)
        return @{ FreeGB = $freeGB; TotalGB = $totalGB; UsedPercent = $usedPercent; Available = $true }
    } catch {
        Write-Host "  [WARN] WMI unavailable ($($_.Exception.Message)) - using Get-Process fallback" -ForegroundColor DarkYellow
        $totalUsedMB = (Get-Process | Measure-Object WorkingSet64 -Sum).Sum / 1MB
        return @{ FreeGB = 0; TotalGB = 0; UsedPercent = 0; Available = $false }
    }
}

function Get-TopConsumers {
    Get-Process | Group-Object Name | ForEach-Object {
        $sum = ($_.Group | Measure-Object WorkingSet64 -Sum).Sum
        [PSCustomObject]@{ Name = $_.Name; Count = $_.Count; MB = [math]::Round($sum / 1MB, 0) }
    } | Sort-Object MB -Descending | Select-Object -First 5
}

function Get-HealthCode {
    param([double]$FreeGB)
    if ($FreeGB -ge $HealthyGB) { return 0 }
    if ($FreeGB -ge $CriticalGB) { return 1 }
    return 2
}

function Get-StatusColor {
    param([int]$Code)
    switch ($Code) { 0 { 'Green' } 1 { 'Yellow' } 2 { 'Red' } }
}

function Get-StatusLabel {
    param([int]$Code)
    switch ($Code) { 0 { 'HEALTHY' } 1 { 'WARNING' } 2 { 'CRITICAL' } }
}

# --- Header ---
Write-Host "`n=== MEMORY FLUSH ORCHESTRATOR ===" -ForegroundColor Cyan
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "[$timestamp] Mode: $(if ($CheckOnly) { 'CHECK ONLY' } else { 'FULL FLUSH' })`n" -ForegroundColor Gray

# --- Before snapshot ---
$before = Get-RamSnapshot
$beforeCode = Get-HealthCode $before.FreeGB
if ($before.Available) {
    Write-Host "RAM: $($before.FreeGB)GB free / $($before.TotalGB)GB ($($before.UsedPercent)% used) [$(Get-StatusLabel $beforeCode)]" -ForegroundColor (Get-StatusColor $beforeCode)
} else {
    Write-Host "RAM: unknown (WMI unavailable) - proceeding with cleanup anyway" -ForegroundColor DarkYellow
}

# --- Top consumers ---
$top = Get-TopConsumers
Write-Host "`nTop consumers:" -ForegroundColor Gray
$top | ForEach-Object { Write-Host "  $($_.Name) ($($_.Count) procs): $($_.MB)MB" -ForegroundColor Gray }

if ($CheckOnly) {
    Write-Host "`n[CHECK ONLY] No actions taken." -ForegroundColor DarkGray
    exit (Get-HealthCode $before.FreeGB)
}

# --- Step 1: Kill zombies ---
Write-Host "`n--- Step 1: Kill Zombies ---" -ForegroundColor Yellow
$zombieScript = Join-Path $toolsRoot "kill_zombies.ps1"
if (Test-Path $zombieScript) {
    if ($Verbose) {
        & $zombieScript -Force
    } else {
        $output = & $zombieScript -Force 2>&1
        $killLine = $output | Select-String -Pattern "killed|No zombie|Found" | Select-Object -Last 1
        if ($killLine) { Write-Host "  $killLine" -ForegroundColor Gray }
    }
} else {
    Write-Host "  [SKIP] kill_zombies.ps1 not found at $zombieScript" -ForegroundColor DarkYellow
}

# --- Step 2: Electron priority rebalance ---
Write-Host "`n--- Step 2: Priority Rebalance ---" -ForegroundColor Yellow
$priorityScript = Join-Path $toolsRoot "electron_priority_manager.ps1"
if (Test-Path $priorityScript) {
    if ($Verbose) {
        & $priorityScript -Once
    } else {
        $output = & $priorityScript -Once 2>&1
        $trimLine = $output | Select-String -Pattern "Trimmed|No Cursor|Cursor:" | Select-Object -Last 1
        if ($trimLine) { Write-Host "  $trimLine" -ForegroundColor Gray }
    }
} else {
    Write-Host "  [SKIP] electron_priority_manager.ps1 not found at $priorityScript" -ForegroundColor DarkYellow
}

# --- Wait for process teardown ---
Start-Sleep -Seconds 2

# --- After snapshot ---
$after = Get-RamSnapshot
$afterCode = Get-HealthCode $after.FreeGB
$recoveredMB = [math]::Round(($after.FreeGB - $before.FreeGB) * 1024, 0)

Write-Host "`n=== RESULTS ===" -ForegroundColor Cyan
if ($before.Available) {
    Write-Host "Before: $($before.FreeGB)GB free ($($before.UsedPercent)% used)" -ForegroundColor Gray
} else {
    Write-Host "Before: unknown (WMI was unavailable)" -ForegroundColor DarkGray
}
if ($after.Available) {
    Write-Host "After:  $($after.FreeGB)GB free ($($after.UsedPercent)% used)" -ForegroundColor (Get-StatusColor $afterCode)
    if ($before.Available -and $recoveredMB -gt 0) {
        Write-Host "Recovered: ~${recoveredMB}MB" -ForegroundColor Green
    }
} else {
    Write-Host "After:  unknown (WMI still unavailable)" -ForegroundColor DarkYellow
}
Write-Host "Status: $(Get-StatusLabel $afterCode)" -ForegroundColor (Get-StatusColor $afterCode)

exit $afterCode
