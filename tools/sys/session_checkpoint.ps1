<#
.SYNOPSIS
    Session Checkpoint — Persist git + RAM state across context resets.
.DESCRIPTION
    Captures current git state (branch, commit, dirty files), RAM status,
    and top consumers into a checkpoint file. Designed to pair with /kclear
    for full session handoff.
.USAGE
    .\session_checkpoint.ps1                        # create checkpoint with "manual" label
    .\session_checkpoint.ps1 "pre-refactor"         # create with custom label
    .\session_checkpoint.ps1 -List                  # show existing checkpoints
    .\session_checkpoint.ps1 -Flush                 # checkpoint + RAM flush if needed
    .\session_checkpoint.ps1 -MaxCheckpoints 10     # keep more history
#>

param(
    [Parameter(Position = 0)]
    [string]$Label = "manual",
    [int]$MaxCheckpoints = 5,
    [switch]$List,
    [switch]$Flush
)

$checkpointDir = Join-Path $env:USERPROFILE ".claude\sessions\checkpoints"
if (-not (Test-Path $checkpointDir)) {
    New-Item -ItemType Directory -Path $checkpointDir -Force | Out-Null
}

# --- List mode ---
if ($List) {
    $files = Get-ChildItem -Path $checkpointDir -Filter "checkpoint_*.md" -ErrorAction SilentlyContinue | Sort-Object Name -Descending
    if (-not $files -or $files.Count -eq 0) {
        Write-Host "No checkpoints found." -ForegroundColor Gray
        exit 0
    }

    Write-Host "`n=== SESSION CHECKPOINTS ===" -ForegroundColor Cyan
    Write-Host "Directory: $checkpointDir`n" -ForegroundColor Gray

    foreach ($f in $files) {
        $content = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
        $branchMatch = [regex]::Match($content, '\*\*Branch:\*\* (.+)')
        $ramMatch = [regex]::Match($content, '\*\*Free RAM:\*\* (.+)')
        $branch = if ($branchMatch.Success) { $branchMatch.Groups[1].Value } else { "?" }
        $ram = if ($ramMatch.Success) { $ramMatch.Groups[1].Value } else { "?" }

        $age = (Get-Date) - $f.LastWriteTime
        $ageStr = if ($age.TotalHours -lt 1) { "$([math]::Round($age.TotalMinutes))m ago" }
                  elseif ($age.TotalDays -lt 1) { "$([math]::Round($age.TotalHours, 1))h ago" }
                  else { "$([math]::Round($age.TotalDays, 1))d ago" }

        Write-Host "  $($f.BaseName)" -ForegroundColor White -NoNewline
        Write-Host " | $branch | RAM: $ram | $ageStr" -ForegroundColor Gray
    }
    Write-Host ""
    exit 0
}

# --- Capture state ---
Write-Host "`n=== SESSION CHECKPOINT ===" -ForegroundColor Cyan

# Git state (graceful if not in a repo)
$branch = git rev-parse --abbrev-ref HEAD 2>$null
if (-not $branch) { $branch = "(no git repo)" }

$lastCommit = git log --oneline -1 2>$null
if (-not $lastCommit) { $lastCommit = "(no commits)" }

$modifiedFiles = @(git status --porcelain 2>$null)
$modifiedCount = $modifiedFiles.Count

# System state
try {
    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
    $freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    $totalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    if ($totalGB -le 0) { throw "Invalid total memory" }
    $usedPercent = [math]::Round((1 - $freeGB / $totalGB) * 100, 1)
} catch {
    Write-Host "  [WARN] WMI unavailable - RAM data will show as unknown" -ForegroundColor DarkYellow
    $freeGB = -1
    $totalGB = -1
    $usedPercent = -1
}

$cursorInstances = @(Get-Process -Name Cursor -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero }).Count

$topConsumers = Get-Process | Group-Object Name | ForEach-Object {
    $sum = ($_.Group | Measure-Object WorkingSet64 -Sum).Sum
    [PSCustomObject]@{ Name = $_.Name; Count = $_.Count; MB = [math]::Round($sum / 1MB, 0) }
} | Sort-Object MB -Descending | Select-Object -First 5

# Timestamp and filename
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$safeLabel = $Label -replace '[^a-zA-Z0-9_-]', '_'
$fileName = "checkpoint_${timestamp}_${safeLabel}.md"
$filePath = Join-Path $checkpointDir $fileName

# Build checkpoint content
$cwd = (Get-Location).Path
$modifiedList = if ($modifiedCount -gt 0) {
    ($modifiedFiles | ForEach-Object { "  - ``$_``" }) -join "`n"
} else {
    "  (clean working tree)"
}

$topTable = ($topConsumers | ForEach-Object { "| $($_.Name) | $($_.Count) | $($_.MB)MB |" }) -join "`n"

$content = @"
# Session Checkpoint: $Label
**Created:** $timestamp
**CWD:** ``$cwd``

## Git State
- **Branch:** $branch
- **Last commit:** $lastCommit
- **Modified files:** $modifiedCount
$modifiedList

## System State
- **Free RAM:** $(if ($freeGB -ge 0) { "${freeGB}GB / ${totalGB}GB ($usedPercent% used)" } else { "unknown (WMI unavailable)" })
- **Cursor instances:** $cursorInstances

### Top Consumers
| Process | Count | Memory |
|---------|-------|--------|
$topTable

## Resume Instructions
1. ``cd $cwd``
2. ``git status`` to verify state matches above
3. Review $modifiedCount modified file(s)
4. Check RAM: ``.\tools\sys\memory_flush.ps1 -CheckOnly``
"@

$content | Out-File -FilePath $filePath -Encoding utf8
Write-Host "Checkpoint saved: $fileName" -ForegroundColor Green
$ramLabel = if ($freeGB -ge 0) { "$($freeGB)GB free" } else { "unknown" }
Write-Host "  Branch: $branch | Files: $modifiedCount | RAM: $ramLabel" -ForegroundColor Gray

# --- Auto-prune ---
$allCheckpoints = Get-ChildItem -Path $checkpointDir -Filter "checkpoint_*.md" | Sort-Object Name -Descending
if ($allCheckpoints.Count -gt $MaxCheckpoints) {
    $toDelete = $allCheckpoints | Select-Object -Skip $MaxCheckpoints
    foreach ($old in $toDelete) {
        Remove-Item $old.FullName -Force
        Write-Host "  Pruned: $($old.Name)" -ForegroundColor DarkGray
    }
}

# --- Flush mode ---
if ($Flush) {
    $flushScript = Join-Path $PSScriptRoot "memory_flush.ps1"
    if ($freeGB -lt 3.0 -and $freeGB -ge 0) {
        Write-Host "`nRAM below 3GB - running memory flush..." -ForegroundColor Yellow
        if (Test-Path $flushScript) {
            & $flushScript
        } else {
            Write-Host "  [SKIP] memory_flush.ps1 not found at $flushScript" -ForegroundColor DarkYellow
        }
    } else {
        Write-Host "`nRAM healthy ($($freeGB)GB free) - flush skipped." -ForegroundColor Green
    }
}

Write-Host ""
