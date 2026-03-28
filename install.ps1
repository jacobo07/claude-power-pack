# Claude Power Pack v3.0 — Windows Installer
$ErrorActionPreference = "Stop"
$SkillDir = Join-Path $env:USERPROFILE ".claude\skills\claude-power-pack"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Claude Power Pack v3.0 Installer" -ForegroundColor Cyan
Write-Host "================================="
Write-Host ""
Write-Host "Step 1: Installing skill files..."
New-Item -ItemType Directory -Path "$SkillDir\modules" -Force | Out-Null
Copy-Item "$ScriptDir\SKILL.md" -Destination $SkillDir -Force
Copy-Item "$ScriptDir\modules\*" -Destination "$SkillDir\modules" -Recurse -Force
Write-Host "  OK: Installed to $SkillDir" -ForegroundColor Green
Write-Host ""
Write-Host "Step 2: Checking Python dependencies..."
$python = $null
if (Get-Command python -ErrorAction SilentlyContinue) { $python = "python" }
elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $python = "python3" }
if ($python) {
    try { & $python -m pip install httpx feedparser -q 2>$null; Write-Host "  OK" -ForegroundColor Green }
    catch { Write-Host "  WARN: pip failed" -ForegroundColor Yellow }
} else { Write-Host "  WARN: Python not found" -ForegroundColor Yellow }
Write-Host ""
$yn = Read-Host "Step 3: Setup autoresearch scheduler? [y/N]"
if ($yn -eq "y" -and $python) { & $python "$SkillDir\modules\autoresearch\setup_schedule.py" }
else { Write-Host "  Skipped." }
Write-Host ""
Write-Host "Done! Post-install:" -ForegroundColor Green
Write-Host "  1. Edit modules/autoresearch/config.json"
Write-Host "  2. Remove/throttle Stop hook in ~/.claude/settings.json"
Write-Host "  3. python modules/executionos-lite/migrate.py <executionos.md> --verify"
Write-Host "  4. Trigger 'deep optimize' in Claude Code"
