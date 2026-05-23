# Claude Power Pack — global installer (Windows PowerShell wrapper)
#
# Sibling of install.ps1 (per-project doctrine scaffolder; do NOT
# confuse with it — that one templates a per-project CLAUDE.md).
# This script installs / updates the Power Pack into ~/.claude/ for
# any user. Pure-Python logic lives in tools/install_global_core.py;
# this wrapper handles banner + env-scrub + invocation.
#
# Usage:
#   .\install-global.ps1               # apply
#   .\install-global.ps1 -DryRun       # preview every action; no mutation
#   .\install-global.ps1 -Settings <path>  # custom settings.json
#
# Doctrine (Lesson 2, 2026-05-19): this script NEVER writes into
# permissions.allow — it PRINTS the rules the Owner pastes. See
# vault/standards/feature-completion-standard.md.

[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$Settings
)

$ErrorActionPreference = 'Stop'

Write-Host "============================================================"
Write-Host "  Claude Power Pack -- install-global.ps1"
Write-Host "  Banner: PER-USER GLOBAL installer (NOT per-project!)"
Write-Host "  Sibling: install.ps1 (per-project CLAUDE.md scaffolder)"
Write-Host "============================================================"

# Locate the Python interpreter. Honor an explicit override; else find
# python.exe on PATH. Fail loud if missing — no silent degraded mode.
$python = $env:CLAUDE_PY_EXE
if (-not $python -or -not (Test-Path $python)) {
    $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source }
}
if (-not $python -or -not (Test-Path $python)) {
    Write-Error "Cannot find python.exe. Install Python 3.10+ or set CLAUDE_PY_EXE."
    exit 5
}

# Resolve the core script relative to THIS file (no hardcoded paths —
# gap 2 doctrine, paths must work for any user on any host).
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$core = Join-Path $here 'tools\install_global_core.py'
if (-not (Test-Path $core)) {
    Write-Error "install_global_core.py not found at $core"
    exit 5
}

# Env scrub (gap 4 / L3 cycle finding): the spawned Python invokes
# settings_merger.py which has classifier-sensitive paths. Strip
# parent-session markers so a nested-claude detection path does NOT
# misread the install.
$savedClaudeCode = $env:CLAUDECODE
$savedCcVars = @{}
foreach ($k in @($env.Keys)) {
    if ($null -eq $k) { continue }
    if ($k -eq 'CLAUDECODE' -or $k.StartsWith('CLAUDE_CODE_') -or
        $k -eq 'CLAUDE_PROJECT_DIR') {
        $savedCcVars[$k] = (Get-Item "env:$k").Value
        Remove-Item "env:$k" -ErrorAction SilentlyContinue
    }
}

$argv = @($core)
if ($DryRun) { $argv += '--dry-run' }
if ($Settings) { $argv += '--settings'; $argv += $Settings }

Write-Host "Invoking: $python $($argv -join ' ')"
Write-Host ""
& $python @argv
$rc = $LASTEXITCODE

# Restore env (best-effort — same shell session).
foreach ($k in $savedCcVars.Keys) {
    Set-Item "env:$k" $savedCcVars[$k]
}

if ($rc -ne 0) {
    Write-Host ""
    Write-Host "install-global.ps1: FAILED (exit $rc)" -ForegroundColor Red
    exit $rc
}
Write-Host ""
Write-Host "install-global.ps1: OK" -ForegroundColor Green
exit 0
