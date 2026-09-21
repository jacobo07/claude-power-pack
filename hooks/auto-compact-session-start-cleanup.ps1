#Requires -Version 5.1
# auto-compact-session-start-cleanup.ps1 -- SessionStart entry (Owner PASO 3).
# Cleans flags older than 30 minutes (stale carry-over from a dead session)
# AND removes a daemon lock whose PID is no longer alive. Non-stale flags
# remain so a new daemon spawn can still consume them.
# 2026-09-18: flags are per session, so this runs on OTHER sessions' flags
# too; 30 min (was 10) keeps a flag that is legitimately waiting for its
# window to be focused from being reaped by an unrelated session start.
$ErrorActionPreference = 'SilentlyContinue'
$hooks = Join-Path $env:USERPROFILE '.claude\hooks'
$stale = (Get-Date).AddMinutes(-30)
Get-ChildItem -LiteralPath $hooks -File |
    Where-Object { ($_.Name -like 'auto-compact-trigger*.flag' -or $_.Name -like 'auto-compact-pending*.flag') -and $_.LastWriteTime -lt $stale } |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue }
$lock = Join-Path $hooks '.auto-compact-daemon.lock'
if (Test-Path $lock) {
    try {
        $oldPid = [int]((Get-Content $lock -Raw).Trim() -split '\|')[0]
        if (-not (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
            Remove-Item $lock -Force -ErrorAction SilentlyContinue
        }
    } catch { Remove-Item $lock -Force -ErrorAction SilentlyContinue }
}
exit 0
