<#
  hibernation_daemon.ps1 -- FASE A daemon tick (Owner-scheduled, ~every 5 min).

  One tick: scan live panes -> run the governor -> (dry) preview or (live) hibernate.
  DRY by default: pass -Mode live only after reviewing DRY output (STOP #1).
  Appends every tick to ~/.claude/cache/hibernation-daemon.log. Fail-open: any
  error aborts the tick, never a pane. ASCII-only (Task-Scheduler codepage safety).

  Register (DRY):
    $a = New-ScheduledTaskAction -Execute powershell.exe -Argument (
      '-NoProfile -ExecutionPolicy Bypass -File ' +
      '"%USERPROFILE%\.claude\skills\claude-power-pack\tools\hibernation_daemon.ps1" -Mode dry')
    Register-ScheduledTask PP-Hibernation -Action $a -Trigger (
      New-ScheduledTaskTrigger -Once -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Minutes 5))
  Flip to live: re-register with '-Mode live'.
#>
[CmdletBinding()]
param([ValidateSet('dry', 'live')] [string] $Mode = 'dry')

$ErrorActionPreference = 'Continue'   # fail-open: never abort a tick fatally

$pp = Join-Path $env:USERPROFILE '.claude\skills\claude-power-pack'
$scan = Join-Path $pp 'tools\scan_panes.ps1'
$runner = Join-Path $pp 'tools\run_hibernation.py'

$py = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
if (-not (Test-Path $py)) {
  $c = Get-Command python -ErrorAction SilentlyContinue
  if ($c) { $py = $c.Source }
}

$log = Join-Path $env:USERPROFILE '.claude\cache\hibernation-daemon.log'
$stamp = (Get-Date).ToUniversalTime().ToString('o')

try {
  if (-not (Test-Path $scan) -or -not (Test-Path $runner) -or -not (Test-Path $py)) {
    Add-Content $log "$stamp [$Mode] SKIP: missing scan/runner/python"
    return
  }
  $tmp = Join-Path $env:TEMP 'pp_hibernation_scan.json'
  $raw = & powershell -NoProfile -ExecutionPolicy Bypass -File $scan
  [System.IO.File]::WriteAllText($tmp, $raw, (New-Object System.Text.UTF8Encoding($false)))

  $argList = @($runner, '--from-scan', $tmp)
  if ($Mode -eq 'live') { $argList += '--live' }

  $env:PYTHONIOENCODING = 'utf-8'
  $out = & $py @argList
  $summary = ($out | Select-Object -Last 1)
  Add-Content $log "$stamp [$Mode] $summary"
} catch {
  Add-Content $log "$stamp [$Mode] ERROR (fail-open, no pane touched): $($_.Exception.Message)"
}
