<#
.SYNOPSIS
    Electron Priority Manager — Boosts foreground Cursor, deprioritizes background instances.
.DESCRIPTION
    Detects the active Cursor window and promotes its process tree to AboveNormal priority.
    All background Cursor instances are set to BelowNormal and their working sets are trimmed
    to release pageable RAM back to the OS. Runs on a configurable polling loop.

    Integrates with claude-watchdog.ps1 thresholds — if free RAM < CriticalGB, aggressively
    trims ALL Cursor instances including foreground.
.USAGE
    .\electron_priority_manager.ps1                  # run with 30s interval
    .\electron_priority_manager.ps1 -IntervalSec 15  # custom interval
    .\electron_priority_manager.ps1 -Once             # single pass, no loop
    .\electron_priority_manager.ps1 -DryRun           # show what would happen
#>

param(
    [int]$IntervalSec = 30,
    [double]$CriticalGB = 2.0,
    [switch]$Once,
    [switch]$DryRun
)

# --- Win32 API for foreground window detection ---
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    [DllImport("psapi.dll")]
    public static extern bool EmptyWorkingSet(IntPtr hProcess);
}
"@

function Get-ForegroundPid {
    $hwnd = [Win32]::GetForegroundWindow()
    $fgProcessId = 0
    [Win32]::GetWindowThreadProcessId($hwnd, [ref]$fgProcessId) | Out-Null
    return $fgProcessId
}

function Get-CursorProcessGroups {
    # Get all Cursor processes
    $allCursor = Get-Process -Name Cursor -ErrorAction SilentlyContinue
    if (-not $allCursor) { return $null }

    # Find the foreground PID
    $fgPid = Get-ForegroundPid

    # Check if foreground window belongs to Cursor
    $fgCursor = $allCursor | Where-Object { $_.Id -eq $fgPid }

    # If foreground isn't Cursor, find the Cursor process with a MainWindowHandle
    if (-not $fgCursor) {
        $fgCursor = $allCursor | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero } | Select-Object -First 1
    }

    $fgId = if ($fgCursor) { $fgCursor.Id } else { 0 }

    # Group: foreground instance vs background instances
    # Cursor spawns child processes (GPU, renderer, utility) — we identify by MainWindowHandle
    $mainInstances = $allCursor | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero }

    return @{
        All = $allCursor
        ForegroundPid = $fgId
        MainInstances = $mainInstances
    }
}

function Get-FreeMemoryGB {
    $os = Get-CimInstance Win32_OperatingSystem
    return [math]::Round($os.FreePhysicalMemory / 1MB, 2)
}

function Invoke-PriorityPass {
    $groups = Get-CursorProcessGroups
    if (-not $groups) {
        Write-Host "  No Cursor processes found." -ForegroundColor DarkGray
        return
    }

    $freeGB = Get-FreeMemoryGB
    $isCritical = $freeGB -lt $CriticalGB
    $timestamp = Get-Date -Format "HH:mm:ss"
    $totalProcs = $groups.All.Count
    $fgPid = $groups.ForegroundPid

    Write-Host "[$timestamp] Cursor: $totalProcs procs | FG PID: $fgPid | Free RAM: ${freeGB}GB$(if ($isCritical) { ' [CRITICAL]' })" -ForegroundColor $(if ($isCritical) { 'Red' } else { 'Cyan' })

    $trimmedMB = 0

    foreach ($proc in $groups.All) {
        $isForeground = ($proc.Id -eq $fgPid)
        $targetPriority = if ($isForeground -and -not $isCritical) { 'AboveNormal' } else { 'BelowNormal' }
        $shouldTrim = (-not $isForeground) -or $isCritical
        $wsMB = [math]::Round($proc.WorkingSet64 / 1MB, 0)

        try {
            if ($DryRun) {
                if ($proc.PriorityClass -ne $targetPriority) {
                    Write-Host "  [DRY] PID $($proc.Id): $($proc.PriorityClass) -> $targetPriority $(if ($shouldTrim) { '+ trim' }) (${wsMB}MB)" -ForegroundColor DarkGray
                }
            } else {
                # Set priority
                if ($proc.PriorityClass -ne $targetPriority) {
                    $proc.PriorityClass = $targetPriority
                }

                # Trim working set for background instances (or all if critical)
                if ($shouldTrim -and $wsMB -gt 50) {
                    $handle = $proc.Handle
                    if ($handle) {
                        [Win32]::EmptyWorkingSet($handle) | Out-Null
                        $trimmedMB += $wsMB
                    }
                }
            }
        } catch {
            # Access denied for system-level Cursor processes (expected for PID 0, GPU process, etc.)
            if (-not $DryRun) {
                Write-Verbose "  Skipped PID $($proc.Id): access denied (system process)"
            }
        }
    }

    if ($trimmedMB -gt 0 -and -not $DryRun) {
        Write-Host "  Trimmed ~${trimmedMB}MB from background working sets" -ForegroundColor Yellow
    }
}

# --- Main ---
Write-Host "`n=== ELECTRON PRIORITY MANAGER ===" -ForegroundColor Cyan
Write-Host "Interval: ${IntervalSec}s | Critical threshold: ${CriticalGB}GB | Mode: $(if ($DryRun) { 'DRY RUN' } elseif ($Once) { 'SINGLE PASS' } else { 'LOOP' })" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop.`n" -ForegroundColor DarkGray

if ($Once) {
    Invoke-PriorityPass
} else {
    while ($true) {
        Invoke-PriorityPass
        Start-Sleep -Seconds $IntervalSec
    }
}
