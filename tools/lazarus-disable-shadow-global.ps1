# Lazarus Shadow-Engine Global Disabler — MC-LAZ-14
#
# Removes the managed `$env:LAZARUS_SHADOW_FOLDER='1'` block from
# the user's PowerShell $PROFILE. Counterpart of
# lazarus-enable-shadow-global.ps1.
#
# Does NOT affect currently-running claude sessions (their env was
# captured at spawn time). For an immediate full disable: close all
# terminals, run this, then reopen.

[CmdletBinding()]
param(
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$Marker = '# >>> LAZARUS_SHADOW_FOLDER (managed by lazarus-enable-shadow-global.ps1)'
$EndMarker = '# <<< LAZARUS_SHADOW_FOLDER'
$ProfilePath = $PROFILE.CurrentUserAllHosts
Write-Output "[disable-shadow] target profile: $ProfilePath"

if (-not (Test-Path -LiteralPath $ProfilePath)) {
  Write-Output "[disable-shadow] no profile at $ProfilePath. Nothing to do."
  exit 0
}

$content = Get-Content -LiteralPath $ProfilePath -Raw -ErrorAction SilentlyContinue
if (-not $content) {
  Write-Output "[disable-shadow] profile is empty. Nothing to do."
  exit 0
}

$pattern = "(?ms)" + [regex]::Escape($Marker) + ".*?" + [regex]::Escape($EndMarker) + "(\r?\n)?"
if ($content -notmatch $pattern) {
  Write-Output "[disable-shadow] no managed block found. Already disabled."
  exit 0
}

$updated = [regex]::Replace($content, $pattern, '')

if ($DryRun) {
  Write-Output "[disable-shadow] [DRY] would remove managed block from $ProfilePath"
  exit 0
}

# Backup before mutating.
$backup = "$ProfilePath.bak.$(Get-Date -AsUTC -Format yyyyMMddTHHmmssfffZ)"
Copy-Item -LiteralPath $ProfilePath -Destination $backup -Force
Set-Content -LiteralPath $ProfilePath -Value $updated -Encoding UTF8 -NoNewline
Write-Output "[disable-shadow] PowerShell profile cleaned. Backup: $backup"

# MC-LAZ-17 reverse: remove from HKCU\Environment so CMD-launched
# processes also drop the var. reg delete is the counterpart of setx;
# no admin needed for HKCU.
$regOut = & reg delete "HKCU\Environment" /v LAZARUS_SHADOW_FOLDER /f 2>&1
if ($LASTEXITCODE -eq 0) {
  Write-Output "[disable-shadow] HKCU\Environment cleared (LAZARUS_SHADOW_FOLDER removed)."
} else {
  # Not necessarily an error -- value may have never been set.
  Write-Output "[disable-shadow] reg delete: $regOut"
}

Write-Output "[disable-shadow] disabled. Existing shells unaffected; open a NEW shell to drop the var."
