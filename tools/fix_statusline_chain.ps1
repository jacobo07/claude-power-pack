<#
  fix_statusline_chain.ps1 -- keep the Claude Code context bar visible under Kickbacks.

  Kickbacks.ai replaces the Claude Code `statusLine` with its own ad line, then
  CHAINS the user's prior statusLine below the ad -- it reads the command from
  C:\Users\User\.vibe-ads\cli-prev-statusline.json and runs it via spawn(shell:true)
  (cmd.exe). The captured command used an MSYS / Git-Bash path
  ("/c/Program Files/nodejs/node.exe ...") which cmd.exe cannot resolve, so the
  chained statusline (the gsd HUD that draws the context bar) silently failed --
  the bar vanished while the ad still showed.

  This writes a cmd.exe-valid chain command so the ad AND the context bar both
  render. Idempotent and safe to re-run; run it again if a Kickbacks update ever
  re-captures the broken path.

  Usage: powershell -NoProfile -ExecutionPolicy Bypass -File tools/fix_statusline_chain.ps1
#>
[CmdletBinding()]
param(
  [string]$ChainFile = (Join-Path $env:USERPROFILE ".vibe-ads\cli-prev-statusline.json"),
  [string]$NodeExe = "C:\Program Files\nodejs\node.exe",
  [string]$Hud = (Join-Path $env:USERPROFILE ".claude\hooks\gsd-statusline.js")
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path (Split-Path $ChainFile -Parent))) {
  Write-Output "Kickbacks .vibe-ads dir absent -- nothing to chain. (Is Kickbacks installed?)"
  exit 0
}
if (-not (Test-Path $Hud)) { Write-Warning "HUD not found: $Hud (chain will still be written)" }

$needsFix = $true
if (Test-Path $ChainFile) {
  $cur = Get-Content $ChainFile -Raw
  # already good if it points at the HUD with a Windows path and no MSYS prefix
  if ($cur -match 'gsd-statusline' -and $cur -notmatch '/c/Program Files') { $needsFix = $false }
  Copy-Item $ChainFile ($ChainFile + ".bak") -Force
}

if ($needsFix) {
  $cmd = '"{0}" "{1}"' -f $NodeExe, $Hud
  $obj = @{ statusLine = @{ type = "command"; command = $cmd } }
  $json = $obj | ConvertTo-Json -Compress -Depth 4
  [System.IO.File]::WriteAllText($ChainFile, $json, (New-Object System.Text.UTF8Encoding($false)))
  Write-Output "FIXED chain -> $cmd"
} else {
  Write-Output "Chain already valid (Windows path -> HUD); no change."
}
