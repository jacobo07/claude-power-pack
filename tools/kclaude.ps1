<#
  kclaude.ps1 -- kclaude wrapper orchestrator (W6).

  Pre-launch intelligence, then launch claude, then name the session:
    1. W1 turn-guard      context-pressure advisory   (<=1.0s)
    2. W4 coordinator     same-repo active-pane check  (<=0.5s)
    3. W5 cost gate        daily burn / compaction      (<=0.5s)
    4. W2 auto-resume     transcript-anchored resume   (<=1.0s)
    5. claude [args]      launch (foreground)
    6. W3 session naming  background, NON-blocking

  Steps 1-4 run in ONE python process (modules/wrapper/prelaunch.py) with
  per-feature timeouts running concurrently -> total overhead < 2s. Fail-open
  ABSOLUTE: any error at any step and claude still launches.

  ASCII-only source (PS 5.1 / Task-Scheduler codepage safety).
#>
[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments = $true)] [string[]] $ClaudeArgs)

$ErrorActionPreference = 'Continue'   # fail-open: never abort the launch

# --- wrapper usage (kclaude --help / -h) -------------------------------------
if ($ClaudeArgs.Count -eq 1 -and ($ClaudeArgs[0] -in @('--help', '-h', '/?'))) {
  Write-Host "kclaude -- Claude Code launcher (Power Pack wrapper)"
  Write-Host ""
  Write-Host "  Pre-launch: context-pressure advisory (W1), same-repo coordinator (W4),"
  Write-Host "  cost/compaction gate (W5), transcript-anchored auto-resume (W2);"
  Write-Host "  names new sessions in the background (W3)."
  Write-Host ""
  Write-Host "  Usage:  kclaude [claude args...]    all args pass through to claude"
  Write-Host "          cd <repo> ; kclaude          auto-resumes that repo's latest session"
  Write-Host "          kclaude -h                   this help"
  Write-Host ""
  Write-Host "  Fail-open: if any pre-launch feature errors, claude launches anyway."
  return
}

$cwd = (Get-Location).Path

# --- resolve python (host install, then PATH) --------------------------------
$py = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
if (-not (Test-Path $py)) {
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  $py = if ($cmd) { $cmd.Source } else { $null }
}
$ppRoot = Join-Path $env:USERPROFILE ".claude\skills\claude-power-pack"
$pre = Join-Path $ppRoot "modules\wrapper\prelaunch.py"
$namer = Join-Path $ppRoot "modules\wrapper\session_namer.py"

# --- run prelaunch (W1+W4+W5+W2 in one process); fail-open to null -----------
$decision = $null
if ($py -and (Test-Path $pre)) {
  try {
    $env:PYTHONIOENCODING = 'utf-8'
    $raw = & $py $pre --cwd $cwd 2>$null
    if ($raw) { $decision = ($raw | ConvertFrom-Json) }
  } catch { $decision = $null }
}

# --- advisories (W1 + W5) ----------------------------------------------------
if ($decision -and $decision.advisories) {
  foreach ($a in $decision.advisories) {
    if ($a) { Write-Host $a -ForegroundColor Yellow }
  }
}

# --- decide resume vs new ----------------------------------------------------
$resumeArg = $null
$newSession = $true
if ($decision -and $decision.coord -and $decision.coord.active) {
  Write-Host $decision.coord.warning -ForegroundColor Cyan
  $ans = Read-Host
  if ($ans -match '^[Nn]') {
    $newSession = $true                                   # explicit new
  } elseif ($ans -match '^\d+$' -and $decision.coord.candidates) {
    $i = [int]$ans - 1
    $cands = @($decision.coord.candidates)
    if ($i -ge 0 -and $i -lt $cands.Count) {
      $resumeArg = "--resume " + $cands[$i]; $newSession = $false
    } else {
      $resumeArg = $decision.coord.default_resume; $newSession = $false
    }
  } else {
    $resumeArg = $decision.coord.default_resume           # default S
    $newSession = $false
  }
} elseif ($decision -and $decision.resume -and $decision.resume.resume_arg) {
  $resumeArg = $decision.resume.resume_arg                # auto-resume, no prompt
  $newSession = $false
}

# --- CO-08 hot-session cap (rung-3 block; ONLY for a genuinely NEW pane) ------
# Resuming consumes no new slot, so the cap fires only when a new pane would be
# opened. No bypass flag (CO-00 II.4 / CO-08 III.4): the only paths past a
# refusal are SATISFACTION -- resume the existing session, or free a slot and
# retry. Fail-open: a missing/proceed gate never blocks.
if ($newSession -and $decision -and $decision.gate -and $decision.gate.verdict -eq 'refuse') {
  Write-Host ""
  Write-Host "PP CO-08: hot-session cap reached -- opening a NEW pane is refused." -ForegroundColor Red
  foreach ($r in $decision.gate.reasons) { Write-Host ("  - " + $r) -ForegroundColor Red }
  Write-Host "Satisfy (no bypass -- only these make it fit):" -ForegroundColor Yellow
  foreach ($s in $decision.gate.satisfy) { Write-Host ("  > " + $s) -ForegroundColor Yellow }
  $rt = $null
  if ($decision.coord -and $decision.coord.default_resume) { $rt = $decision.coord.default_resume }
  elseif ($decision.resume -and $decision.resume.resume_arg) { $rt = $decision.resume.resume_arg }
  if ($rt) {
    Write-Host ("Resume the existing session instead? [S/n]  (" + $rt + ")") -ForegroundColor Cyan
    $capAns = Read-Host
    if ($capAns -match '^[Nn]') {
      Write-Host "[kclaude] Cap not satisfied -- launch declined. Free a slot, then retry." -ForegroundColor Red
      exit 9
    }
    $resumeArg = $rt; $newSession = $false
  } else {
    Write-Host "[kclaude] Cap not satisfied -- launch declined. Free a slot (/compact or close the longest hot session), then retry." -ForegroundColor Red
    exit 9
  }
}

# --- W3 session naming (background, non-blocking) ----------------------------
if ($py -and (Test-Path $namer)) {
  try {
    if ($newSession) {
      $known = ""
      if ($decision -and $decision.known_sids) { $known = ($decision.known_sids -join ',') }
      Start-Process -FilePath $py -WindowStyle Hidden `
        -ArgumentList @($namer, '--cwd', $cwd, '--known', $known) | Out-Null
    } elseif ($resumeArg -match 'resume\s+(\S+)') {
      Start-Process -FilePath $py -WindowStyle Hidden `
        -ArgumentList @($namer, '--cwd', $cwd, '--resume-sid', $matches[1]) | Out-Null
    }
  } catch { }
}

# --- launch claude, with /restart loop (supersedes kclaude.bat) --------------
# Absorbs the MC-LAZ-26 resume loop: when /restart drops a flag, relaunch the
# SAME session (--resume <sid> from the lazarus SID file, else --continue) in
# this same terminal. Pre-launch intelligence (above) ran ONCE; restarts skip it.
$flagPattern = Join-Path $env:TEMP 'claude-restart-*.flag'
$sidFile = Join-Path $env:USERPROFILE '.claude\lazarus\kclaude-restart-sid.txt'
Remove-Item $flagPattern -Force -ErrorAction SilentlyContinue   # purge stale flags

$launch = @()
if ($resumeArg) { $launch += ($resumeArg -split '\s+') }
if ($ClaudeArgs) { $launch += $ClaudeArgs }

while ($true) {
  & claude @launch
  $code = $LASTEXITCODE
  $flag = Get-ChildItem $flagPattern -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $flag) { exit $code }
  Remove-Item $flag.FullName -Force -ErrorAction SilentlyContinue
  $sid = $null
  if (Test-Path $sidFile) {
    $sid = (Get-Content $sidFile -Raw -ErrorAction SilentlyContinue)
    if ($sid) { $sid = $sid.Trim() }
    Remove-Item $sidFile -Force -ErrorAction SilentlyContinue
  }
  Write-Host ""
  if ($sid) {
    Write-Host "[kclaude] Restart detected. Relaunching with --resume $sid..." -ForegroundColor Green
    Start-Sleep -Seconds 1
    $launch = @('--resume', $sid)
  } else {
    Write-Host "[kclaude] Restart detected. Relaunching with --continue..." -ForegroundColor Green
    Start-Sleep -Seconds 1
    $launch = @('--continue')
  }
}
