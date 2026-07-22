<#
.SYNOPSIS
  Scope 2 of vault/specs/cursor-window-session-restoration.md (ULTRA-PLAN,
  2026-07-22): captures the set of currently-open top-level Cursor windows,
  each resolved to a repo path, plus which one is focused.

  This is the producer that was missing per the plan's root-cause chain item
  3: pane_map.json's "live" flag is a per-Claude-session signal, not a
  "was a Cursor window open for this repo" signal. Nothing else in the repo
  records OS-level window topology.

.NOTES
  Repo-name -> path resolution is cross-referenced from pane_map.json (the
  existing source of truth for repo cwds), never invented. A window whose
  title doesn't match any known repo is still recorded (repoPath: $null)
  rather than silently dropped -- see docs/cursor-startup-and-reload.md
  precedent: over-inclusion is the correct error for a recovery net.

  Run on a short interval (Scheduled Task, see register_window_topology_task.ps1)
  so the last snapshot before any close -- graceful or not -- is always recent.
  Mirrors the existing pp-snapshot-writer / pane_map freshness pattern
  (SCS C79) rather than depending on an unreliable true close-hook.
#>

[CmdletBinding()]
param(
    [ValidateSet("run","start","stop","status")]
    [string]$Action = "run",
    [int]$IntervalMinutes = 2,
    [string]$PaneMapPath  = "$env:USERPROFILE\.claude\state\pane_map.json",
    [string]$OutPath      = "$env:USERPROFILE\.claude\state\window_topology.json",
    [string]$LastOpenPath = "$env:USERPROFILE\.claude\state\window_topology_last_open.json",
    [string]$QueuePath    = "$env:USERPROFILE\.claude\state\window_topology_reconcile_queue.json",
    [string]$ReconcileLog = "$env:USERPROFILE\.claude\state\window_topology_reconcile.log"
)

# Owner decision 2026-07-22 (post-crash, explicit approval in this session,
# task.allowAutomaticTasks flipped back "on" for it): reconciliation is
# PROGRESSIVE -- one missing repo opened per scheduled-task cycle (~every
# IntervalMinutes), never a big-bang reopen of every missing repo at once.
# Extends the existing pane-level wave-stagger precedent
# (T-FOLDEROPEN-STAMPEDE-001) to the window level.
function Write-ReconcileLog {
    param([string]$Msg)
    $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    "$ts $Msg" | Out-File -FilePath $ReconcileLog -Append -Encoding utf8
}

# start/stop/status manage a companion Scheduled Task, `pp-window-topology-writer`,
# mirroring the existing pp-snapshot-writer registration pattern (see
# tools/snapshot_auto_writer.ps1) -- a 2-minute cadence (vs that task's 15) because
# window topology (which repos have a window open, which is focused) changes on
# human timescales and the whole point is "the last snapshot before any close,
# graceful or not, is recent enough to trust" (SCS C79 freshness precedent).
$TaskName = "pp-window-topology-writer"
$ScriptPath = $PSCommandPath

if ($Action -eq "start") {
    $actionObj = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument ("-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$ScriptPath`" -Action run")
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
        -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 2) `
        -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $TaskName -Action $actionObj -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Write-Output "OK: $TaskName installed (every ${IntervalMinutes}min)"
    & $ScriptPath -Action run
    return
}
if ($Action -eq "stop") {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Output "OK: $TaskName removed"
    return
}
if ($Action -eq "status") {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $t) { Write-Output "NOT INSTALLED"; return }
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Output "State=$($t.State) LastRunTime=$($info.LastRunTime) LastResult=$($info.LastTaskResult) NextRunTime=$($info.NextRunTime)"
    return
}
# else: Action -eq "run" falls through to the capture logic below.

Add-Type -Namespace PPWin -Name Native -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
[DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
[DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr hWnd);
[DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
'@ -ErrorAction SilentlyContinue

function Get-RepoLookup {
    param([string]$Path)
    $lookup = @{}
    if (-not (Test-Path $Path)) { return $lookup }
    try {
        $map = Get-Content $Path -Raw | ConvertFrom-Json
    } catch {
        return $lookup
    }
    foreach ($pane in $map.panes) {
        if ($pane.repo -and -not $lookup.ContainsKey($pane.repo)) {
            $lookup[$pane.repo] = $pane.cwd
        }
    }
    return $lookup
}

function Resolve-RepoFromTitle {
    param([string]$Title, [hashtable]$Lookup)
    # Cursor window titles are "<workspace-name> - Cursor" for a repo window,
    # bare "Cursor" for the welcome screen, "Cursor Agents" for the native
    # agents surface (no PP-owned repo mapping exists for that one).
    $name = $Title -replace '\s*-\s*Cursor\s*$', ''
    $name = $name.Trim()
    if ($name -eq '' -or $Title -eq 'Cursor') {
        return [pscustomobject]@{ repoName = $null; repoPath = $null; kind = 'welcome' }
    }
    if ($Title -eq 'Cursor Agents') {
        return [pscustomobject]@{ repoName = $null; repoPath = $null; kind = 'cursor-agents-native' }
    }
    if ($Lookup.ContainsKey($name)) {
        return [pscustomobject]@{ repoName = $name; repoPath = $Lookup[$name]; kind = 'repo' }
    }
    # Known but unmapped title -- record it, never invent a path.
    return [pscustomobject]@{ repoName = $name; repoPath = $null; kind = 'unmapped' }
}

function Get-CursorTopLevelWindows {
    # EnumWindows + GetWindowThreadProcessId, NOT Get-Process.MainWindowTitle.
    # Empirically verified 2026-07-22 (live crash recovery, this same session):
    # MainWindowTitle returns exactly ONE window per process even when Cursor
    # owns 6 top-level windows under one PID -- silently hiding 5 of 6. A
    # topology producer that under-counts windows is worse than none: it reads
    # as "restored" when it is not.
    $cursorPids = @(Get-Process -Name 'cursor' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
    if (-not $cursorPids -or $cursorPids.Count -eq 0) { return @() }
    $fg = [PPWin.Native]::GetForegroundWindow()
    $fgPid = 0
    if ($fg -ne [IntPtr]::Zero) { $tmp = 0; [void][PPWin.Native]::GetWindowThreadProcessId($fg, [ref]$tmp); $fgPid = $tmp }

    $found = New-Object System.Collections.Generic.List[object]
    $seenTitles = New-Object System.Collections.Generic.HashSet[string]
    $cb = {
        param($hWnd, $lParam)
        if ([PPWin.Native]::IsWindowVisible($hWnd)) {
            $len = [PPWin.Native]::GetWindowTextLength($hWnd)
            if ($len -gt 0) {
                $sb = New-Object System.Text.StringBuilder ($len + 1)
                [void][PPWin.Native]::GetWindowText($hWnd, $sb, $sb.Capacity)
                $title = $sb.ToString()
                $procId = 0
                [void][PPWin.Native]::GetWindowThreadProcessId($hWnd, [ref]$procId)
                if (($cursorPids -contains $procId) -and $seenTitles.Add($title)) {
                    $found.Add([pscustomobject]@{ pid = $procId; title = $title; hwnd = $hWnd })
                }
            }
        }
        return $true
    }
    [void][PPWin.Native]::EnumWindows($cb, [IntPtr]::Zero)
    return @($found | ForEach-Object {
        [pscustomobject]@{ pid = $_.pid; title = $_.title; focused = ($_.hwnd -eq $fg) }
    })
}

$repoLookup = Get-RepoLookup -Path $PaneMapPath
$rawWindows = Get-CursorTopLevelWindows
$windows = @($rawWindows | ForEach-Object {
    $resolved = Resolve-RepoFromTitle -Title $_.title -Lookup $repoLookup
    [pscustomobject]@{
        pid      = $_.pid
        title    = $_.title
        repoName = $resolved.repoName
        repoPath = $resolved.repoPath
        kind     = $resolved.kind
        focused  = $_.focused
    }
})

$prevWindowCount = -1
if (Test-Path $OutPath) {
    try { $prevWindowCount = (Get-Content $OutPath -Raw | ConvertFrom-Json).windowCount } catch { $prevWindowCount = -1 }
}
$currentCount = @($windows).Count
$currentRepoPaths = @($windows | Where-Object { $_.repoPath } | Select-Object -ExpandProperty repoPath -Unique)

# ---- Enqueue: only on a genuine 0 -> N transition (true cold start), and
# only if no reconciliation is already in progress (queue file absent/empty).
# Scoped deliberately to the unambiguous case: a repo-set SHRINKING while
# other windows stay open (user deliberately closed one window) is NOT
# reconciled -- indistinguishable from "user didn't want it back" without a
# real close-event signal, and forcing it back would be its own phantom-
# window bug. Documented limitation, not a silent gap.
$queueIsEmpty = -not (Test-Path $QueuePath) -or (@(Get-Content $QueuePath -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json -ErrorAction SilentlyContinue) | Where-Object { $_ }).Count -eq 0
if ($prevWindowCount -eq 0 -and $currentCount -gt 0 -and $queueIsEmpty -and (Test-Path $LastOpenPath)) {
    try {
        $lastOpen = Get-Content $LastOpenPath -Raw | ConvertFrom-Json
        $lastOpenRepoPaths = @($lastOpen.windows | Where-Object { $_.repoPath } | Select-Object -ExpandProperty repoPath -Unique)
        $missing = @($lastOpenRepoPaths | Where-Object { $currentRepoPaths -notcontains $_ })
        if ($missing.Count -gt 0) {
            $missing | ConvertTo-Json -Depth 3 | Set-Content -Path $QueuePath -Encoding utf8
            Write-ReconcileLog "[ENQUEUE] cold-start transition. Queued $($missing.Count) missing repo(s) for progressive reopen: $($missing -join '; ')"
        }
    } catch {
        Write-ReconcileLog "[ERROR] enqueue failed: $($_.Exception.Message)"
    }
}

# ---- Dequeue: pop exactly ONE repo per cycle, never the whole queue at
# once (Owner decision: progressive, not big-bang).
if (Test-Path $QueuePath) {
    try {
        $queue = @(Get-Content $QueuePath -Raw | ConvertFrom-Json)
        if ($queue.Count -gt 0) {
            $next = $queue[0]
            $rest = @($queue | Select-Object -Skip 1)
            if ($currentRepoPaths -contains $next) {
                # Already open (e.g. the Owner opened it manually meanwhile) --
                # skip launching, just drop it from the queue.
                Write-ReconcileLog "[SKIP] $next already open; removing from queue."
            } else {
                $restoreScript = Join-Path (Split-Path $ScriptPath -Parent) 'restore_panes.ps1'
                if (Test-Path $restoreScript) {
                    $argStr = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$restoreScript`" -AutoRun -OnlyRepoCwds `"$next`""
                    Start-Process -FilePath 'powershell.exe' -ArgumentList $argStr -WindowStyle Hidden
                    Write-ReconcileLog "[REOPEN] launched restore_panes.ps1 for: $next ($($rest.Count) remaining in queue)"
                } else {
                    Write-ReconcileLog "[ERROR] restore_panes.ps1 not found at $restoreScript -- cannot act on: $next"
                }
            }
            if ($rest.Count -eq 0) {
                # An empty array piped through ConvertTo-Json sends ZERO
                # objects downstream -- Set-Content then receives no input
                # and silently leaves the file's PREVIOUS (non-empty)
                # content in place. That stale content would permanently
                # read as "queue not empty" and block all future
                # reconciliation. Delete the file explicitly instead.
                Remove-Item -Path $QueuePath -ErrorAction SilentlyContinue
                Write-ReconcileLog "[DONE] reconciliation queue drained."
            } else {
                $rest | ConvertTo-Json -Depth 3 | Set-Content -Path $QueuePath -Encoding utf8
            }
        }
    } catch {
        Write-ReconcileLog "[ERROR] dequeue failed: $($_.Exception.Message)"
    }
}

# ---- Update the "last known fully open" reference. Monotonic non-
# decreasing rule: only overwrite when the current known-repo count is >=
# the reference's, so a still-partial post-reconcile state (fewer repos
# than the reference, until later cycles finish the queue) never clobbers
# the very reference reconciliation is restoring from.
$shouldUpdateLastOpen = $true
if ($currentCount -eq 0) {
    $shouldUpdateLastOpen = $false
} elseif (Test-Path $LastOpenPath) {
    try {
        $lastOpen = Get-Content $LastOpenPath -Raw | ConvertFrom-Json
        $lastOpenRepoCount = @($lastOpen.windows | Where-Object { $_.repoPath } | Select-Object -ExpandProperty repoPath -Unique).Count
        if ($currentRepoPaths.Count -lt $lastOpenRepoCount) { $shouldUpdateLastOpen = $false }
    } catch { $shouldUpdateLastOpen = $true }
}

$snapshot = [pscustomobject]@{
    capturedAt  = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')
    windowCount = $currentCount
    windows     = $windows
}
$snapshot | ConvertTo-Json -Depth 6 | Set-Content -Path $OutPath -Encoding utf8
if ($shouldUpdateLastOpen) { $snapshot | ConvertTo-Json -Depth 6 | Set-Content -Path $LastOpenPath -Encoding utf8 }

Write-Output "Captured $currentCount window(s) (prev=$prevWindowCount) -> $OutPath"
