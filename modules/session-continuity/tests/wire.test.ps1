# <module>/tests/wire.test.ps1
$ErrorActionPreference = 'Stop'
$tmp = Join-Path ([IO.Path]::GetTempPath()) ("lzwire-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $tmp | Out-Null
$sj = Join-Path $tmp 'settings.json'
'{ "hooks": { "SessionStart": [], "PreToolUse": [] } }' | Set-Content $sj -Encoding UTF8
& "$PSScriptRoot/../wire-claude-settings.ps1" -SettingsPath $sj
$j = Get-Content $sj -Raw | ConvertFrom-Json
# -Width 4096: Out-String wraps at console width by default, truncating the
# command payload before 'recorder.js' and causing a false negative. Widening
# the render is rendering-only; it does not weaken the wired/idempotent checks.
if (($j.hooks.SessionStart | Out-String -Width 4096) -notmatch 'recorder.js') { Write-Error 'recorder not wired'; exit 1 }
if (($j.hooks.PreToolUse  | Out-String -Width 4096) -notmatch 'governance-guard.js') { Write-Error 'guard not wired'; exit 1 }
& "$PSScriptRoot/../wire-claude-settings.ps1" -SettingsPath $sj
$j2 = Get-Content $sj -Raw | ConvertFrom-Json
$cnt = ($j2.hooks.SessionStart | Out-String -Width 4096 | Select-String 'recorder.js' -AllMatches).Matches.Count
if ($cnt -ne 1) { Write-Error "recorder wired $cnt times"; exit 1 }
Write-Host 'wire.test OK'
