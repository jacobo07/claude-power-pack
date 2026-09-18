#Requires -Version 5.1
# gsd_long_run_sweep.ps1 -- Task Scheduler entry for `gsd_long_run.py sweep`
# (spec vault/specs/gsd-long-run-v2.md, gaps 2 + 9). Runs every 5 minutes via
# wscript + tools/hidden_launch.vbs so nothing flashes on the desktop, and in the
# interactive session because a recovery may spawn the SendKeys daemon.
#
# Logs only when the sweep DID something, so an idle machine writes nothing.
# Register:   see commands/cpp-gsd-long.md ("Sweep")
# Unregister: Unregister-ScheduledTask -TaskName PP-GsdLongRun-Sweep -Confirm:$false
$ErrorActionPreference = 'SilentlyContinue'
$py   = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$tool = Join-Path $PSScriptRoot 'gsd_long_run.py'
$log  = Join-Path $env:USERPROFILE '.claude\state\gsd-long-run-sweep.log'
$env:PYTHONIOENCODING = 'utf-8'
$out = (& $py $tool sweep 2>&1 | Out-String).Trim()
if ($out -and $out -ne '[]') {
    Add-Content -LiteralPath $log -Value ("{0} {1}" -f [DateTime]::UtcNow.ToString('o'), ($out -replace '\s+', ' ')) -Encoding UTF8
}
exit 0
