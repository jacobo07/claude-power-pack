# Lazarus Shadow-Engine Global Enabler — MC-LAZ-14
#
# Adds `$env:LAZARUS_SHADOW_FOLDER='1'` to the user's PowerShell
# $PROFILE so that every new claude session born from that shell
# inherits the env var and the heartbeat hook activates the shadow
# engine for it. Idempotent: detects existing managed block and
# skips. Reversible via lazarus-disable-shadow-global.ps1.
#
# IMPORTANT: This does NOT affect already-running claude sessions
# (they captured their env at spawn time). It applies to NEW shells
# only. If you want to retrofit, close + reopen the terminal.
#
# ASCII-only — PS 5.1 reads scripts as ANSI; em-dashes break parser.

[CmdletBinding()]
param(
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$Marker = '# >>> LAZARUS_SHADOW_FOLDER (managed by lazarus-enable-shadow-global.ps1)'
$EndMarker = '# <<< LAZARUS_SHADOW_FOLDER'
$Block = @"
$Marker
`$env:LAZARUS_SHADOW_FOLDER = '1'
$EndMarker
"@

# $PROFILE points to the current host's profile; we want the
# all-hosts (CurrentUserAllHosts) profile for maximum coverage.
$ProfilePath = $PROFILE.CurrentUserAllHosts
Write-Output "[enable-shadow] target profile: $ProfilePath"

if (-not (Test-Path -LiteralPath $ProfilePath)) {
  if ($DryRun) {
    Write-Output "[enable-shadow] [DRY] would create $ProfilePath"
  } else {
    $dir = Split-Path -Parent $ProfilePath
    if (-not (Test-Path -LiteralPath $dir)) {
      New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    New-Item -ItemType File -Path $ProfilePath -Force | Out-Null
    Write-Output "[enable-shadow] created profile"
  }
}

$existing = if (Test-Path -LiteralPath $ProfilePath) {
  Get-Content -LiteralPath $ProfilePath -Raw -ErrorAction SilentlyContinue
} else { '' }

$profileAlreadyDone = $existing -and ($existing -match [regex]::Escape($Marker))

if ($profileAlreadyDone) {
  Write-Output "[enable-shadow] PowerShell profile: managed block already present (no-op)."
} elseif ($DryRun) {
  Write-Output "[enable-shadow] PowerShell profile: [DRY] would append managed block."
} else {
  # Append, preserve trailing newline behavior.
  $prefix = if ($existing -and -not $existing.EndsWith("`n")) { "`n" } else { '' }
  Add-Content -LiteralPath $ProfilePath -Value ($prefix + $Block) -Encoding UTF8
  Write-Output "[enable-shadow] PowerShell profile updated."
}

# MC-LAZ-17: also set HKCU\Environment so CMD-launched processes
# (e.g. autoresume.bat) inherit the var without needing the
# PowerShell profile. setx writes user-level persistent env; no
# admin required. Already-running shells do NOT pick this up; new
# processes do.
$envCmd = (Get-Command setx -ErrorAction SilentlyContinue)
if (-not $envCmd) {
  Write-Output "[enable-shadow] WARN: setx not on PATH; CMD shells will not inherit. Manual fallback: HKCU\Environment registry edit."
} else {
  $setxOut = & setx LAZARUS_SHADOW_FOLDER 1 2>&1
  if ($LASTEXITCODE -eq 0) {
    Write-Output "[enable-shadow] HKCU\Environment updated (setx) -- new CMD + PowerShell processes inherit env=1."
  } else {
    Write-Output "[enable-shadow] WARN: setx failed: $setxOut"
  }
}

# Verify via reg query (Zero-Stub gate per directive).
$regCheck = & reg query "HKCU\Environment" /v LAZARUS_SHADOW_FOLDER 2>&1
if ($regCheck -match 'LAZARUS_SHADOW_FOLDER\s+REG_SZ\s+1') {
  Write-Output "[enable-shadow] VERIFIED: reg query confirms LAZARUS_SHADOW_FOLDER=1 in HKCU\Environment."
} else {
  Write-Output "[enable-shadow] WARN: reg query did not confirm. Output: $regCheck"
}

Write-Output ""
Write-Output "[enable-shadow] enabled. Existing shells/processes are NOT affected."
Write-Output "[enable-shadow] Open a NEW shell to pick up the env var."
Write-Output "[enable-shadow] verify CMD:        cmd /c echo %LAZARUS_SHADOW_FOLDER%"
Write-Output "[enable-shadow] verify PowerShell: powershell -NoProfile -Command '`$env:LAZARUS_SHADOW_FOLDER'"
Write-Output "[enable-shadow] disable:           ./lazarus-disable-shadow-global.ps1"
