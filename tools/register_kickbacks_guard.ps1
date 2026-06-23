<#
  register_kickbacks_guard.ps1 -- install a Windows Scheduled Task that runs
  kickbacks_guard.ps1 every 2 minutes (and at logon), so the Kickbacks ad + the
  context bar self-heal without any manual action.

  A timer (not a Claude Code hook) is used on purpose: Kickbacks can clear the
  chain file mid-session, and a SessionStart hook would only heal at the next
  session start. A 2-minute timer caps any bar-gone window at ~2 min regardless
  of what Claude is doing.

  Idempotent: re-running replaces the task. Reversible: -Unregister removes it.
  Runs as the current user, hidden window, only when logged in. Does NOT need
  admin for a per-user task.

  Usage:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/register_kickbacks_guard.ps1
    powershell ... tools/register_kickbacks_guard.ps1 -Unregister
#>
[CmdletBinding()]
param(
  [string]$TaskName = "PP-KickbacksGuard",
  [int]$IntervalMinutes = 2,
  [switch]$Unregister
)
$ErrorActionPreference = "Stop"
$guard = Join-Path $PSScriptRoot "kickbacks_guard.ps1"

if ($Unregister) {
  try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop; Write-Output "Unregistered: $TaskName" }
  catch { Write-Output ("Task not present or could not unregister: " + $_.Exception.Message) }
  return
}

if (-not (Test-Path $guard)) { throw "guard script not found: $guard" }

$ps = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
$action = New-ScheduledTaskAction -Execute $ps `
  -Argument ('-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}"' -f $guard)

# trigger: at logon + repeat every N minutes, effectively forever
$tLogon = New-ScheduledTaskTrigger -AtLogOn
$tRepeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
  -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
  -RepetitionDuration (New-TimeSpan -Days 3650)

$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 2) -MultipleInstances IgnoreNew

# remove any prior version first (idempotent)
try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue } catch {}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger @($tLogon, $tRepeat) `
  -Principal $principal -Settings $settings `
  -Description "Self-heals the Kickbacks ad + Claude Code context-bar chain (kickbacks_guard.ps1) every $IntervalMinutes min." | Out-Null

$t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($t) { Write-Output ("Registered: $TaskName  state=" + $t.State + "  interval=" + $IntervalMinutes + "min") }
else { throw "registration verify failed" }
