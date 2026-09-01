# register_compound_task.ps1 -- Owner-side registration for PP-Compound-Unattended.
#
# Why this is a script and not something the agent ran: registering a Windows
# Scheduled Task is an Owner-environment mutation, and the auto-mode classifier
# blocks it (HR-001: ship the PP-internal half, document the Owner-side step;
# never work around the denial). Everything else in the feature is already live;
# this is the one action that needs the Owner's own hands.
#
# Run:  powershell -ExecutionPolicy Bypass -File "<this file>"
# Undo: Unregister-ScheduledTask -TaskName 'PP-Compound-Unattended' -Confirm:$false
#
# Pattern copied verbatim from PP-Vault-Summarize, which runs clean (result=0)
# on this host: pythonw.exe (windowless -- no console flash, so no VBS shim is
# needed), Interactive logon, Limited runlevel. DisallowStartIfOnBatteries is
# left at its default of True on purpose: a headless agent session at 03:30 on
# battery is not something to start.

$ErrorActionPreference = 'Stop'

$py     = 'C:\Users\User\AppData\Local\Programs\Python\Python312\pythonw.exe'
$script = 'C:\Users\User\.claude\skills\claude-power-pack\tools\compound_unattended.py'
$name   = 'PP-Compound-Unattended'

if (-not (Test-Path $py))     { Write-Host "MISSING pythonw: $py";     exit 1 }
if (-not (Test-Path $script)) { Write-Host "MISSING driver:  $script"; exit 1 }

$action  = New-ScheduledTaskAction -Execute $py -Argument "`"$script`""
$trigger = New-ScheduledTaskTrigger -Daily -At 3:30am
$princ   = New-ScheduledTaskPrincipal -UserId $env:USERNAME `
                                      -LogonType Interactive -RunLevel Limited
$set     = New-ScheduledTaskSettingsSet -StartWhenAvailable `
                                        -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger `
    -Principal $princ -Settings $set -Force `
    -Description 'Unattended /cpp-compound: promotes recurring project learnings into global baseline rules. Spec vault/specs/cross-project-baseline.md' | Out-Null

$t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($t) {
    Write-Host "REGISTERED $name"
    Write-Host ("  state     = " + $t.State)
    Write-Host ("  exec      = " + $t.Actions[0].Execute)
    Write-Host ("  args      = " + $t.Actions[0].Arguments)
    Write-Host ("  trigger   = " + $t.Triggers[0].StartBoundary)
    Write-Host ("  onBattery = blocked (" + $t.Settings.DisallowStartIfOnBatteries + ")")
    Write-Host ""
    Write-Host "Verify without waiting for 03:30:"
    Write-Host "  Start-ScheduledTask -TaskName '$name'"
    Write-Host "  Get-Content `"$env:USERPROFILE\.claude\state\compound-unattended.log`" -Tail 5"
} else {
    Write-Host "REGISTRATION REPORTED SUCCESS BUT TASK NOT FOUND -- investigate"
    exit 1
}
