<#
.SYNOPSIS
  CPC-OS Crash Restore -- reopen every repo from the session snapshot as a
  Cursor window and print the exact `claude --resume <id>` line per pane.

.DESCRIPTION
  Reads ~/.claude/state/session_snapshot.json (written by
  modules/cpc_os/snapshot.py), dedups the panes by repo, and for each
  distinct repo runs `cursor <path>` so Cursor reopens the window and
  restores its own terminal panes. Then prints, per repo, the exact
  resume command(s) to paste into each restored terminal so the EXACT
  conversation comes back -- not just the cwd.

  Runs from ANY terminal; Claude Code does NOT need to be open. The
  snapshot path is absolute, so the script works from any cwd (e.g. C:\).

.PARAMETER DryRun
  Print what would be opened without launching Cursor. Use to preview.

.PARAMETER SnapshotPath
  Override the snapshot json path (default: ~/.claude/state/session_snapshot.json).

.NOTES
  ASCII-only by design (PowerShell 5.1 -File mis-parses non-ASCII under the
  ANSI codepage). No em-dashes, no emoji, no box-drawing characters.
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$SnapshotPath = (Join-Path $HOME '.claude\state\session_snapshot.json')
)

$ErrorActionPreference = 'Stop'

function Resolve-CursorExe {
    $cmd = Get-Command cursor -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $fallback = Join-Path $env:LOCALAPPDATA 'Programs\cursor\resources\app\bin\cursor.cmd'
    if (Test-Path $fallback) { return $fallback }
    return $null
}

Write-Host 'CPC-OS Crash Restore'
Write-Host ("Reading snapshot: {0}" -f $SnapshotPath)

if (-not (Test-Path $SnapshotPath)) {
    Write-Host ''
    Write-Host '[ERROR] Snapshot not found. Open Claude Code once to generate it,'
    Write-Host '        or run: python modules/cpc_os/snapshot.py'
    exit 1
}

try {
    $panes = Get-Content -Raw -Path $SnapshotPath | ConvertFrom-Json
} catch {
    Write-Host ('[ERROR] Snapshot is not valid JSON: {0}' -f $_.Exception.Message)
    exit 1
}

if (-not $panes -or $panes.Count -eq 0) {
    Write-Host '[INFO] Snapshot has no panes. Nothing to restore.'
    exit 0
}

# Dedup by cwd -> distinct repos (the real restore unit; a repo reopens ONE
# Cursor window that restores all its panes).
$repos = $panes | Group-Object -Property cwd
$total = $repos.Count
Write-Host ("Found {0} pane(s) across {1} repo(s)." -f $panes.Count, $total)
Write-Host ''

$cursorExe = Resolve-CursorExe
if (-not $cursorExe) {
    Write-Host '[WARN] cursor CLI not found -- cannot auto-open windows.'
    Write-Host '       Resume commands below still let you restore manually.'
    Write-Host ''
}

Write-Host ("Restoring {0} repo(s)..." -f $total)
$i = 0
foreach ($repo in $repos) {
    $i++
    $cwd = $repo.Name
    $name = Split-Path $cwd -Leaf
    if ($DryRun) {
        Write-Host ("[{0}/{1}] {2} -> [dry-run] would open: cursor `"{3}`"" -f $i, $total, $name, $cwd)
    } elseif ($cursorExe) {
        Write-Host ("[{0}/{1}] {2} -> opening Cursor window..." -f $i, $total, $name)
        try {
            & $cursorExe $cwd | Out-Null
        } catch {
            Write-Host ("        [WARN] cursor failed: {0}" -f $_.Exception.Message)
        }
    } else {
        Write-Host ("[{0}/{1}] {2} -> (cursor unavailable; see resume below)" -f $i, $total, $name)
    }
}

Write-Host ''
Write-Host 'Per-pane resume (paste into each restored terminal):'
Write-Host ''
foreach ($repo in $repos) {
    $cwd = $repo.Name
    $name = Split-Path $cwd -Leaf
    Write-Host ("  {0}  ({1})" -f $name, $cwd)
    # Distinct resume commands for this repo (repo-latest panes share one;
    # exact panes each carry their own captured session_id).
    $seen = @{}
    foreach ($p in $repo.Group) {
        $key = $p.resume
        if ($seen.ContainsKey($key)) { continue }
        $seen[$key] = $true
        $kind = $p.resume_kind
        Write-Host ("    {0}    [{1}]" -f $p.resume, $kind)
    }
    Write-Host ''
}

Write-Host '[OK] Done. Cierra esta ventana / Close this window.'
exit 0
