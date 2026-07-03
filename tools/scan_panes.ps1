<#
  scan_panes.ps1 -- FASE A Transparent Process Hibernation: live pane collector.

  Emits a JSON array of raw pane records (one per live claude.exe) on stdout, the
  input the Resource Governor (process_governor.enrich_panes + plan) consumes:

    [{ pid, wrapper_pid, ws_mb, wrapper_kind, sid, cwd, is_foreground, is_loop }]

  wrapper_kind: how the pane was launched, which decides whether it can rehydrate
    ps1  -> parent is powershell running kclaude.ps1 (wakeable; the flag key is the
            parent pid = the $PID kclaude.ps1 uses to write its wake flag)
    bat  -> parent cmd running kclaude.bat            (wakeable after the bat patch)
    cmd  -> parent running bin\kclaude.cmd             (delegates to kclaude.ps1)
    none -> no kclaude wrapper                         (governor keeps it: no reap)

  sid/cwd come from the pane's own beacon (%TEMP%\kclaude-pane-<wrapperpid>.sid),
  written by kclaude.ps1. No beacon -> null sid -> the governor KEEPS the pane
  (no-sid fail-safe). Read-only + fail-open: this NEVER kills anything.

  ASCII-only (PS 5.1 / Task-Scheduler codepage safety).
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'SilentlyContinue'

function Get-WrapperKind([string]$cmdline, [string]$pname) {
  if (-not $cmdline) { return 'none' }
  if ($cmdline -match 'kclaude\.ps1') { return 'ps1' }
  if ($cmdline -match 'kclaude\.cmd') { return 'cmd' }
  if ($cmdline -match 'kclaude\.bat') { return 'bat' }
  return 'none'
}

$temp = $env:TEMP
$out = @()

$claude = Get-CimInstance Win32_Process -Filter "Name='claude.exe'" -ErrorAction SilentlyContinue
foreach ($c in $claude) {
  $wrapperPid = [int]$c.ParentProcessId
  $parent = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $wrapperPid) -ErrorAction SilentlyContinue
  $kind = 'none'
  if ($parent) { $kind = Get-WrapperKind $parent.CommandLine $parent.Name }

  # Working set (MB) from the live process object.
  $wsMb = 0.0
  try { $wsMb = [math]::Round(([int64]$c.WorkingSetSize) / 1MB, 1) } catch { }

  # sid/cwd from the pane beacon keyed by the wrapper pid.
  $sid = $null; $cwd = $null
  $beacon = Join-Path $temp ("kclaude-pane-{0}.sid" -f $wrapperPid)
  if (Test-Path $beacon) {
    try {
      $b = Get-Content $beacon -Raw -Encoding UTF8 | ConvertFrom-Json
      $sid = $b.sid; $cwd = $b.cwd
    } catch { }
  }

  $out += [pscustomobject]@{
    pid           = [int]$c.ProcessId
    wrapper_pid   = $wrapperPid
    ws_mb         = $wsMb
    wrapper_kind  = $kind
    sid           = $sid
    cwd           = $cwd
    # Foreground/loop detection is not reliable at the process level inside
    # Cursor (many panes share one window); the governor's idle>threshold +
    # not-hot guards are the real protection for the active/looping pane, which
    # is never idle. Emitted false; documented degradation.
    is_foreground = $false
    is_loop       = $false
  }
}

# Always emit a JSON array (even for 0/1 element) so python json.loads is happy.
if ($out.Count -eq 0) {
  Write-Output '[]'
} else {
  Write-Output ('[' + (($out | ForEach-Object { $_ | ConvertTo-Json -Compress }) -join ',') + ']')
}
