# <module>/wire-claude-settings.ps1 — Owner-applied. In-process JSON validate, backup.
param([string]$SettingsPath = (Join-Path $env:USERPROFILE '.claude\settings.json'))
$ErrorActionPreference = 'Stop'
$node = '"/c/Program Files/nodejs/node.exe"'
$mod  = ((Join-Path $PSScriptRoot '.') -replace '\\','/')
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item $SettingsPath "$SettingsPath.bak-$stamp"
$j = Get-Content $SettingsPath -Raw | ConvertFrom-Json
function Ensure($arr, $cmd) {
  # @(...) wrapper forces an array even when one element survives the filter,
  # otherwise the pipeline yields a scalar PSObject and `+` throws op_Addition
  # on the second (idempotent) run.
  $list = @(@($arr) | Where-Object { $_ })
  # Exact structural compare on the deserialized object: matching against
  # ConvertTo-Json is unreliable because embedded quotes are backslash-escaped
  # in the JSON form but not in [regex]::Escape($cmd), so it never re-detects
  # an already-wired hook and duplicates it on every run.
  foreach ($entry in $list) {
    foreach ($h in @($entry.hooks)) {
      if ($h -and $h.command -eq $cmd) { return ,$list }
    }
  }
  return ,($list + @([pscustomobject]@{ hooks = @([pscustomobject]@{ type='command'; command=$cmd; timeout=5 }) }))
}
if (-not $j.hooks) { $j | Add-Member hooks ([pscustomobject]@{}) }
if (-not $j.hooks.SessionStart) { $j.hooks | Add-Member SessionStart @() -Force }
if (-not $j.hooks.PreToolUse)   { $j.hooks | Add-Member PreToolUse  @() -Force }
$j.hooks.SessionStart = Ensure $j.hooks.SessionStart "$node `"$mod/recorder.js`""
$j.hooks.PreToolUse   = Ensure $j.hooks.PreToolUse   "$node `"$mod/governance-guard.js`""
$out = $j | ConvertTo-Json -Depth 12
$null = $out | ConvertFrom-Json
Set-Content -Path $SettingsPath -Value $out -Encoding UTF8 -NoNewline
Write-Host "Wired recorder+guard. Backup: $SettingsPath.bak-$stamp" -ForegroundColor Green
