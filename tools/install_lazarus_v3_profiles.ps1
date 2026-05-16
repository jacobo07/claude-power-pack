# install_lazarus_v3_profiles.ps1 — Cursor terminal profile installer (BL-0073).
#
# Patches Cursor's User\settings.json to register 4 PowerShell terminal profiles
# (slot1..slot4), each injecting LAZARUS_TERMINAL_KEY=<slotN> into the env. This
# is the activation key for terminal-slot-recorder.js writeRegistryEntry() (which
# requires $env:LAZARUS_TERMINAL_KEY to populate ~/.claude/lazarus/terminal_registry.json).
#
# Why regex block-insert instead of ConvertFrom-Json:
#   Cursor settings.json is JSON5 — line comments (//) and trailing commas are
#   valid. PowerShell ConvertFrom-Json silently strips comments and may fail
#   on trailing commas; round-tripping ConvertTo-Json then writing back destroys
#   the user's annotations. Audit gap #4 — this is the safe approach.
#
# Why abort on user/machine LAZARUS_TERMINAL_KEY:
#   A system-wide setx would shadow the per-profile env value, silently
#   collapsing all 4 panes into one slot. Audit gap #6.
#
# Idempotent: re-running detects the marker block "// >>> LAZARUS-V3 BEGIN" and
# updates the slot definitions without duplicating them.
#
# Backup: writes settings.json.bak.<ISO> before any modification.

[CmdletBinding()]
param(
  [string]$SettingsPath = (Join-Path $env:APPDATA 'Cursor\User\settings.json'),
  [int]$NumSlots = 4,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$marker_begin = '// >>> LAZARUS-V3 BEGIN (managed by install_lazarus_v3_profiles.ps1)'
$marker_end   = '// <<< LAZARUS-V3 END'

function Abort($msg) {
  Write-Error "[install-v3] $msg"
  exit 1
}

# Pre-flight: shadowing env-var check (audit gap #6)
$shadow_user    = [Environment]::GetEnvironmentVariable('LAZARUS_TERMINAL_KEY', 'User')
$shadow_machine = [Environment]::GetEnvironmentVariable('LAZARUS_TERMINAL_KEY', 'Machine')
if ($shadow_user -or $shadow_machine) {
  Abort @"
LAZARUS_TERMINAL_KEY is set at User=$shadow_user / Machine=$shadow_machine.
This shadows the per-profile env value Cursor injects, collapsing all 4 panes
into one slot. Run:
  [Environment]::SetEnvironmentVariable('LAZARUS_TERMINAL_KEY', `$null, 'User')
  [Environment]::SetEnvironmentVariable('LAZARUS_TERMINAL_KEY', `$null, 'Machine')
…then re-run this installer.
"@
}

if (-not (Test-Path -LiteralPath $SettingsPath)) {
  Abort "Cursor settings.json not found at $SettingsPath. Pass -SettingsPath if your install differs."
}

# Read raw text — preserve comments + trailing commas
$raw = Get-Content -Raw -Encoding UTF8 -LiteralPath $SettingsPath
if ($raw.Length -gt 0 -and [int][char]$raw[0] -eq 0xFEFF) {
  $raw = $raw.Substring(1) # strip BOM (BL-0036)
}

# Build the marker block with N slot profiles
$slot_lines = @()
for ($i = 1; $i -le $NumSlots; $i++) {
  $slot_lines += @"
    "slot$i (pwsh)": {
      "path": "pwsh.exe",
      "args": ["-NoLogo"],
      "icon": "terminal-powershell",
      "env": { "LAZARUS_TERMINAL_KEY": "slot$i" }
    },
"@
}
$slot_block = ($slot_lines -join "`n")
$lazarus_block = @"
$marker_begin
"terminal.integrated.profiles.windows": {
$slot_block
},
"terminal.integrated.defaultProfile.windows": "slot1 (pwsh)",
$marker_end
"@

# Detect existing marker block
$marker_re = [regex]::new(
  [regex]::Escape($marker_begin) + '.*?' + [regex]::Escape($marker_end),
  [System.Text.RegularExpressions.RegexOptions]::Singleline
)

if ($marker_re.IsMatch($raw)) {
  $new_raw = $marker_re.Replace($raw, $lazarus_block)
  $action = 'UPDATE'
} else {
  # Insert just before the trailing closing brace
  $closing_brace_re = [regex]::new('\}\s*$')
  if (-not $closing_brace_re.IsMatch($raw)) {
    Abort "Could not locate trailing '}' in $SettingsPath — file may be corrupt."
  }
  $insertion = "`n  $lazarus_block`n}"
  $new_raw = $closing_brace_re.Replace($raw, $insertion, 1)
  $action = 'INSERT'
}

if ($DryRun) {
  Write-Host "[install-v3 DRY] action=$action would write to $SettingsPath" -ForegroundColor Magenta
  Write-Host "--- new block ---" -ForegroundColor Magenta
  Write-Host $lazarus_block
  return
}

# Backup
$iso = (Get-Date).ToString('yyyy-MM-ddTHH-mm-ss')
$backup = "$SettingsPath.bak.$iso"
Copy-Item -LiteralPath $SettingsPath -Destination $backup -Force
Write-Host "[install-v3] backup: $backup" -ForegroundColor DarkGray

# Atomic write: temp + rename
$tmp = "$SettingsPath.tmp.$PID"
[System.IO.File]::WriteAllText($tmp, $new_raw, (New-Object System.Text.UTF8Encoding($false)))
Move-Item -LiteralPath $tmp -Destination $SettingsPath -Force

Write-Host "[install-v3] $action $NumSlots slot profiles -> $SettingsPath" -ForegroundColor Green
Write-Host "[install-v3] reload Cursor (Cmd-Shift-P -> 'Developer: Reload Window') to activate." -ForegroundColor Cyan
Write-Host "[install-v3] verify: open a new pane via 'Terminal: Select Default Profile' -> 'slot1 (pwsh)'" -ForegroundColor Cyan
Write-Host "[install-v3] then in pane: " -NoNewline; Write-Host '`$env:LAZARUS_TERMINAL_KEY' -ForegroundColor Yellow -NoNewline; Write-Host '  -> should print "slot1"'
