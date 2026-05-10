# install_csr_profile_hook.ps1 - wire $PROFILE.CurrentUserAllHosts (BL-0073).
#
# Patches the Owner's PS profile with a marker block that:
#   1. Dot-sources claude_smart_resume.ps1 (registers `csr` alias)
#   2. Runs lazarus_post_reboot_arm.py once per logon (bootid-sentinel gated)
#
# Why CurrentUserAllHosts (not bare $PROFILE):
#   $PROFILE = $PROFILE.CurrentUserCurrentHost which only covers ONE shell
#   (pwsh OR Windows PowerShell 5.1). CurrentUserAllHosts loads in BOTH —
#   matches Cursor's slot-profile spawning pwsh.exe AND any 5.1 shell the
#   Owner uses for legacy scripts. Audit gap #7.
#
# Idempotent: marker block "# >>> CSR-LAZARUS BEGIN" delimits the managed
# region; re-running updates contents in-place without duplication.
#
# Aborts on Restricted/AllSigned execution policy (Owner must relax first).
# Backup: $PROFILE.CurrentUserAllHosts.bak.<ISO> before any modification.

[CmdletBinding()]
param(
  [switch]$DryRun,
  [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$marker_begin = '# >>> CSR-LAZARUS BEGIN (managed by install_csr_profile_hook.ps1, BL-0073)'
$marker_end   = '# <<< CSR-LAZARUS END'

function Abort($msg) {
  Write-Error "[install-csr-hook] $msg"
  exit 1
}

# Pre-flight: execution policy
$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -in 'Restricted', 'AllSigned') {
  Abort @"
Execution policy is $policy in CurrentUser scope. Profile dot-source will be
blocked at every shell start. Run:
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
…then re-run this installer.
"@
}

$profile_path = $PROFILE.CurrentUserAllHosts
if (-not $profile_path) {
  Abort '$PROFILE.CurrentUserAllHosts is empty — running in a host that does not support profiles.'
}

# Build the managed block
$csr_path = Join-Path $env:USERPROFILE '.claude\skills\claude-power-pack\tools\claude_smart_resume.ps1'
$arm_path = Join-Path $env:USERPROFILE '.claude\skills\claude-power-pack\tools\lazarus_post_reboot_arm.py'

$block = @"
$marker_begin
# Dot-source smart-resume to register `csr` alias (Lazarus tier-1 dispatch).
# See modules/zero-crash/hooks/terminal-slot-recorder.js for the registry
# write path that this resolver consumes.
if (Test-Path -LiteralPath '$csr_path') {
  . '$csr_path'
}

# Run post-reboot arm once per logon (bootid-sentinel gated inside the script).
# Sanitizes terminal_registry.json, drops >24h heartbeats, cleans tmp orphans.
# Background + suppressed-output to avoid slowing shell start.
if (Test-Path -LiteralPath '$arm_path') {
  Start-Job -ScriptBlock {
    param(`$p) python `$p 2>&1 | Out-Null
  } -ArgumentList '$arm_path' | Out-Null
}
$marker_end
"@

# Read existing profile (or empty)
$existing = ''
if (Test-Path -LiteralPath $profile_path) {
  $existing = Get-Content -Raw -Encoding UTF8 -LiteralPath $profile_path
  if ($existing.Length -gt 0 -and [int][char]$existing[0] -eq 0xFEFF) {
    $existing = $existing.Substring(1) # strip BOM
  }
} else {
  $parent = Split-Path -Parent $profile_path
  if ($parent -and -not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
  }
}

$marker_re = [regex]::new(
  [regex]::Escape($marker_begin) + '.*?' + [regex]::Escape($marker_end),
  [System.Text.RegularExpressions.RegexOptions]::Singleline
)

if ($Uninstall) {
  if (-not $marker_re.IsMatch($existing)) {
    Write-Host "[install-csr-hook] no managed block in $profile_path; nothing to remove." -ForegroundColor Yellow
    return
  }
  $new_content = $marker_re.Replace($existing, '').Trim() + "`n"
  $action = 'UNINSTALL'
} elseif ($marker_re.IsMatch($existing)) {
  $new_content = $marker_re.Replace($existing, $block)
  $action = 'UPDATE'
} else {
  $new_content = ($existing.TrimEnd() + "`n`n" + $block + "`n").TrimStart()
  $action = 'INSTALL'
}

if ($DryRun) {
  Write-Host "[install-csr-hook DRY] action=$action  profile=$profile_path" -ForegroundColor Magenta
  Write-Host "--- new content ---" -ForegroundColor Magenta
  Write-Host $new_content
  return
}

# Backup
if (Test-Path -LiteralPath $profile_path) {
  $iso = (Get-Date).ToString('yyyy-MM-ddTHH-mm-ss')
  $backup = "$profile_path.bak.$iso"
  Copy-Item -LiteralPath $profile_path -Destination $backup -Force
  Write-Host "[install-csr-hook] backup: $backup" -ForegroundColor DarkGray
}

# Atomic write
$tmp = "$profile_path.tmp.$PID"
[System.IO.File]::WriteAllText($tmp, $new_content, (New-Object System.Text.UTF8Encoding($false)))
Move-Item -LiteralPath $tmp -Destination $profile_path -Force

Write-Host "[install-csr-hook] $action -> $profile_path" -ForegroundColor Green
Write-Host "[install-csr-hook] open a fresh shell; verify: " -NoNewline; Write-Host 'Get-Command csr' -ForegroundColor Yellow
Write-Host "[install-csr-hook] post-reboot arm runs as a Start-Job — check ~/.claude/lazarus/post_reboot_*.log after first logon."
