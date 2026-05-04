<#
.SYNOPSIS
  Installs a Windows Startup shortcut so ghost_input_driver.ps1 runs in -Live
  mode at every user logon.

.DESCRIPTION
  This script creates a `.lnk` in the user's Startup folder
  (`shell:startup`). It does NOT modify the registry, does NOT install a
  scheduled task, and does NOT touch any system-wide location. It is
  inert until the Owner runs it (the Owner is the user, not Claude).

  After install, the next time you log into Windows, ghost_input_driver
  runs hidden in the background in -Live mode and watches the
  context_snapshots.jsonl ledger for tier-2 advisories. When detected, it
  fires `/compact focus on <hint>{ENTER}` via SendKeys to the FOREGROUND
  window. Brittleness documented in
  vault/audits/ghost_driver_immunization.md (BL-0058).

  To uninstall: delete the shortcut from
  `[Environment]::GetFolderPath('Startup')`, OR run this script with
  -Uninstall.

.EXAMPLE
  pwsh tools/install_ghost_autostart.ps1
  pwsh tools/install_ghost_autostart.ps1 -Uninstall
  pwsh tools/install_ghost_autostart.ps1 -DryRun   # show what would happen
#>
[CmdletBinding()]
param(
  [switch]$Uninstall,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$startupDir = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupDir 'GhostInputDriver.lnk'
$driverPath = Join-Path $env:USERPROFILE '.claude\skills\claude-power-pack\tools\ghost_input_driver.ps1'

Write-Host "Startup folder:  $startupDir"
Write-Host "Shortcut target: $shortcutPath"
Write-Host "Driver script:   $driverPath"

if (-not (Test-Path $driverPath)) {
  Write-Error "Driver not found at $driverPath. Aborting."
  exit 2
}

if ($Uninstall) {
  if (Test-Path $shortcutPath) {
    if ($DryRun) {
      Write-Host "[DRY-RUN] would delete: $shortcutPath"
    } else {
      Remove-Item -Path $shortcutPath -Force
      Write-Host "Uninstalled: shortcut removed."
    }
  } else {
    Write-Host "Nothing to uninstall (shortcut not present)."
  }
  exit 0
}

if (Test-Path $shortcutPath) {
  Write-Host "Shortcut already exists. Re-creating to refresh target..."
  if (-not $DryRun) { Remove-Item -Path $shortcutPath -Force }
}

if ($DryRun) {
  Write-Host "[DRY-RUN] would create shortcut:"
  Write-Host "  TargetPath = pwsh.exe"
  Write-Host "  Arguments  = -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$driverPath`" -Live"
  Write-Host "  WorkDir    = $env:USERPROFILE"
  exit 0
}

$pwshExe = (Get-Command pwsh -ErrorAction SilentlyContinue).Path
if (-not $pwshExe) {
  Write-Warning "pwsh.exe not on PATH; falling back to powershell.exe."
  $pwshExe = (Get-Command powershell -ErrorAction Stop).Path
}

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pwshExe
$shortcut.Arguments  = "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$driverPath`" -Live"
$shortcut.WorkingDirectory = $env:USERPROFILE
$shortcut.Description = 'Ghost-Input Driver — auto-detect tier-2 context advisory and fire /compact via SendKeys (BL-0057)'
$shortcut.WindowStyle = 7  # 7 = Minimized
$shortcut.Save()

Write-Host ""
Write-Host "Installed. Next logon, ghost_input_driver will run hidden in -Live mode."
Write-Host "To stop it without uninstalling: kill the corresponding pwsh.exe process."
Write-Host "To uninstall: pwsh tools/install_ghost_autostart.ps1 -Uninstall"
