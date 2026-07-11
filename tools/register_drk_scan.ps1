<#
  register_drk_scan.ps1 -- install a Windows Scheduled Task that runs the DRK
  proactive scanner once a day, writing vault/audits/drk_proactive_<date>.md and
  appending high-urgency findings to the OWNER_QUEUE.

  A daily out-of-band task (not a SessionStart hook, not a Stop hook) is used on
  purpose. The SessionStart hub is the most contended surface in the pack (JIT
  cards, AKOS injection, pane restore) and a scan there taxes every session start;
  the Stop chain already carries FD-07 and token_irr and a scan there taxes every
  turn. The scanner has nothing to say that is urgent within a session -- its
  findings are about systems that have been silent for days. So it runs where it
  costs the interactive flow exactly nothing.

  The scanner never blocks: it writes a report and, only for high-urgency
  findings, an OWNER_QUEUE row (idempotent by id, so a daily re-scan of an
  unfixed finding does not duplicate it).

  Idempotent: re-running replaces the task. Reversible: -Unregister removes it.
  Runs as the current user, hidden window, only when logged in. No admin needed.

  Usage:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/register_drk_scan.ps1
    powershell ... tools/register_drk_scan.ps1 -Unregister
    powershell ... tools/register_drk_scan.ps1 -At 08:30
#>
[CmdletBinding()]
param(
  [string]$TaskName = "PP-DRKScan",
  [string]$At = "09:00",
  [switch]$Unregister
)
$ErrorActionPreference = "Stop"

if ($Unregister) {
  try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop; Write-Output "Unregistered: $TaskName" }
  catch { Write-Output ("Task not present or could not unregister: " + $_.Exception.Message) }
  return
}

$repo = Split-Path -Parent $PSScriptRoot
$scanner = Join-Path $repo "modules\decision_review\proactive_scanner.py"
if (-not (Test-Path $scanner)) { throw "scanner not found: $scanner" }

# Resolve python: prefer the pinned interpreter, fall back to PATH.
$py = "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $py)) {
  $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
  if ($null -eq $cmd) { throw "python.exe not found (checked the pinned path and PATH)" }
  $py = $cmd.Source
}

$action = New-ScheduledTaskAction -Execute $py `
  -Argument '-m modules.decision_review.proactive_scanner --repo . --write --publish' `
  -WorkingDirectory $repo

$trigger = New-ScheduledTaskTrigger -Daily -At $At
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew

try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue } catch {}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
  -Principal $principal -Settings $settings `
  -Description "DRK proactive scanner: daily sweep for silent systems, dead knowledge, aged residuals and unrecorded architecture decisions. Writes vault/audits/drk_proactive_<date>.md; high-urgency findings go to the OWNER_QUEUE." | Out-Null

$t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($t) { Write-Output ("Registered: $TaskName  state=" + $t.State + "  daily at " + $At) }
else { throw "registration verify failed" }
