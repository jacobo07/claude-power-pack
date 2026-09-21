#Requires -Version 5.1
# auto-compact-stop-launcher.ps1 -- Stop hook entry (Owner PASO 3, 2026-05-20).
# If any trigger or pending flag exists (per-session names since 2026-09-18,
# legacy single names still matched), spawn the SendKeys daemon detached.
# The daemon enforces its own single-flight; duplicate spawn is harmless.
$ErrorActionPreference = 'SilentlyContinue'
$hooks = Join-Path $env:USERPROFILE '.claude\hooks'
$daemon = Join-Path $hooks 'auto-compact-sendkeys-daemon.ps1'
$any = Get-ChildItem -LiteralPath $hooks -File |
    Where-Object { $_.Name -like 'auto-compact-trigger*.flag' -or $_.Name -like 'auto-compact-pending*.flag' } |
    Select-Object -First 1
if ($any) {
    if (Test-Path $daemon) {
        Start-Process -FilePath 'powershell.exe' `
            -ArgumentList @('-NoProfile','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',$daemon) `
            -WindowStyle Hidden | Out-Null
    }
}
exit 0
