# <module>/install-cursor-profiles.ps1
# Owner-applied. JSON5-safe regex block-insert (Cursor settings.json has // comments).
param(
  [string]$SettingsPath = (Join-Path $env:APPDATA 'Cursor\User\settings.json'),
  [int]$NumSlots = 4
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $SettingsPath)) { Write-Error "no $SettingsPath"; exit 1 }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item $SettingsPath "$SettingsPath.bak-$stamp"
$raw = Get-Content $SettingsPath -Raw

$restore = ((Join-Path $PSScriptRoot 'restore.ps1') -replace '\\','/')
$profiles = (1..$NumSlots | ForEach-Object {
@"
    "slot$_": {
      "source": "PowerShell",
      "args": ["-NoExit","-ExecutionPolicy","Bypass","-File","$restore"],
      "env": { "LAZARUS_TERMINAL_KEY": "slot$_" }
    }
"@ }) -join ",`n"

$block = @"
  // >>> LAZARUS-V4 BEGIN (managed - do not edit by hand)
  "terminal.integrated.enablePersistentSessions": true,
  "terminal.integrated.restoreTerminals": true,
  "terminal.integrated.profiles.windows": {
$profiles
  },
  // <<< LAZARUS-V4 END
"@

if ($raw -match '(?s)// >>> LAZARUS-V4 BEGIN.*?// <<< LAZARUS-V4 END\r?\n?') {
  $raw = [regex]::Replace($raw, '(?s)// >>> LAZARUS-V4 BEGIN.*?// <<< LAZARUS-V4 END\r?\n?', $block.TrimEnd() + "`n")
} else {
  $raw = $raw -replace '^\s*\{', "{`n$block"
}
Set-Content -Path $SettingsPath -Value $raw -Encoding UTF8 -NoNewline
Write-Host "Cursor profiles slot1..slot$NumSlots installed. Backup: $SettingsPath.bak-$stamp" -ForegroundColor Green
