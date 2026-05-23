# <module>/tests/install-cursor-profiles.test.ps1
$ErrorActionPreference = 'Stop'
$tmp = Join-Path ([IO.Path]::GetTempPath()) ("lzcur-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $tmp | Out-Null
$settings = Join-Path $tmp 'settings.json'
@'
{
  // user comment preserved
  "editor.fontSize": 13,
}
'@ | Set-Content $settings -Encoding UTF8
& "$PSScriptRoot/../install-cursor-profiles.ps1" -SettingsPath $settings -NumSlots 3
$raw = Get-Content $settings -Raw
if ($raw -notmatch '// user comment preserved') { Write-Error 'JSON5 comment destroyed'; exit 1 }
if ($raw -notmatch 'LAZARUS-V4 BEGIN') { Write-Error 'marker block missing'; exit 1 }
if ($raw -notmatch 'LAZARUS_TERMINAL_KEY') { Write-Error 'slot env missing'; exit 1 }
if ($raw -notmatch 'restoreTerminals') { Write-Error 'restoreTerminals not set'; exit 1 }
& "$PSScriptRoot/../install-cursor-profiles.ps1" -SettingsPath $settings -NumSlots 3
$n = ([regex]::Matches((Get-Content $settings -Raw), 'LAZARUS-V4 BEGIN')).Count
if ($n -ne 1) { Write-Error "block duplicated ($n)"; exit 1 }
Write-Host 'install-cursor-profiles.test OK'
