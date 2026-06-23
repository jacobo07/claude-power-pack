<#
  install_wrapper.ps1 -- install the kclaude wrapper (W7).

  Copies tools/kclaude.ps1 -> ~/.claude/bin/kclaude.ps1, writes a kclaude.cmd
  shim (so `kclaude` resolves from cmd AND PowerShell), and prepends
  ~/.claude/bin to the USER PATH (so it wins over the old ~/.claude/kclaude.bat).

  SAFETY:
    - Backs up any existing kclaude.ps1 / kclaude.cmd in bin before overwriting.
    - The old ~/.claude/kclaude.bat (MC-LAZ-26 resume loop) is COPIED to a
      .superseded backup -- NEVER deleted. kclaude.ps1 already absorbs that
      restart loop, so the new entry is a strict superset.
    - -DryRun reports what it WOULD do, touching nothing.

  Usage:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/install_wrapper.ps1
    powershell ... -File tools/install_wrapper.ps1 -DryRun

  ASCII-only source (PS 5.1 codepage safety).
#>
[CmdletBinding()]
param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
$bin = Join-Path $env:USERPROFILE '.claude\bin'
$src = Join-Path $PSScriptRoot 'kclaude.ps1'
$dstPs1 = Join-Path $bin 'kclaude.ps1'
$dstCmd = Join-Path $bin 'kclaude.cmd'
$oldBat = Join-Path $env:USERPROFILE '.claude\kclaude.bat'
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Say($m) { Write-Host "[install_wrapper] $m" }

if (-not (Test-Path $src)) { Say "ERROR: source not found: $src"; exit 1 }

if ($DryRun) {
  Say "DRY-RUN -- no changes will be made."
  Say "would ensure dir : $bin"
  Say "would copy       : $src -> $dstPs1"
  Say "would write shim : $dstCmd"
  if (Test-Path $dstPs1) { Say "would back up    : $dstPs1 -> .bak.$stamp" }
  if (Test-Path $oldBat) { Say "would back up    : $oldBat -> $bin\kclaude.bat.superseded.$stamp" }
  $up = [Environment]::GetEnvironmentVariable('Path', 'User')
  if ($up -notlike "*$bin*") { Say "would PREPEND to USER PATH: $bin" }
  else { Say "USER PATH already contains: $bin" }
  exit 0
}

# 1. ensure bin
if (-not (Test-Path $bin)) { New-Item -ItemType Directory -Path $bin -Force | Out-Null; Say "created $bin" }

# 2. back up existing entries (never lose what was there)
foreach ($f in @($dstPs1, $dstCmd)) {
  if (Test-Path $f) {
    $bak = "$f.bak.$stamp"
    Copy-Item $f $bak -Force
    Say "backed up $f -> $bak"
  }
}
if (Test-Path $oldBat) {
  $batBak = Join-Path $bin "kclaude.bat.superseded.$stamp"
  Copy-Item $oldBat $batBak -Force
  Say "backed up old resume-loop bat -> $batBak (preserved; superseded by kclaude.ps1)"
}

# 3. install ps1 + cmd shim
Copy-Item $src $dstPs1 -Force
Say "installed $dstPs1"
$shim = "@echo off`r`npowershell -NoProfile -ExecutionPolicy Bypass -File `"%~dp0kclaude.ps1`" %*`r`n"
[System.IO.File]::WriteAllText($dstCmd, $shim, $utf8)
Say "wrote shim $dstCmd"

# 4. PATH (prepend so bin wins over ~/.claude/kclaude.bat)
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not $userPath) { $userPath = '' }
if ($userPath -notlike "*$bin*") {
  $newPath = if ($userPath) { "$bin;$userPath" } else { $bin }
  [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
  Say "prepended $bin to USER PATH (new terminals will see it)"
} else {
  Say "USER PATH already contains $bin"
}
# update CURRENT session too so verification below works immediately
if (($env:PATH -split ';') -notcontains $bin) { $env:PATH = "$bin;$env:PATH" }

# 5. verify
$found = & where.exe kclaude 2>$null
if ($found) {
  Say "VERIFY where kclaude ->"
  $found | ForEach-Object { Say "  $_" }
} else {
  Say "WARN: 'where kclaude' found nothing in this session PATH."
}
Say "done. Open a NEW terminal (or run the line above) and try: kclaude -h"
