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

if ($existing -and $existing -match [regex]::Escape($Marker)) {
  Write-Output "[enable-shadow] already enabled (managed block found in profile). No-op."
  exit 0
}

if ($DryRun) {
  Write-Output "[enable-shadow] [DRY] would append managed block to $ProfilePath"
  Write-Output "----- block -----"
  Write-Output $Block
  Write-Output "-----------------"
  exit 0
}

# Append, preserve trailing newline behavior.
$prefix = if ($existing -and -not $existing.EndsWith("`n")) { "`n" } else { '' }
Add-Content -LiteralPath $ProfilePath -Value ($prefix + $Block) -Encoding UTF8
Write-Output "[enable-shadow] enabled. Open a NEW PowerShell to pick up the env var."
Write-Output "[enable-shadow] verify: `$env:LAZARUS_SHADOW_FOLDER (should print '1')"
Write-Output "[enable-shadow] disable: ./lazarus-disable-shadow-global.ps1"
