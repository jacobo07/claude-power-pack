<#
  kclaude.ps1 -- kclaude wrapper orchestrator (W6).

  Launch order (startup-blank fix, T-KCLAUDE-STARTUP-BLANK-001):
    1. prelaunch --mode fast   launch-critical only (W2 resume + W4 coord +
                               CO-08 gate + CO-00 advisory)         (<0.5s)
    2. cached advisories       printed instantly from the last refresh
    3. background refresh       prelaunch --mode advisories, detached (W1/W5)
    4. claude [args]           launch (foreground)
    5. W3 session naming        background, NON-blocking

  The slow advisory scan (W1 turn ~1.3s + W5 cost ~17-27s) is NEVER on the
  blocking path: it runs detached and writes a cache the NEXT launch reads.
  Fail-open ABSOLUTE: any error at any step and claude still launches.

  ASCII-only source (PS 5.1 / Task-Scheduler codepage safety).
#>
[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments = $true)] [string[]] $ClaudeArgs)

$ErrorActionPreference = 'Continue'   # fail-open: never abort the launch

# --- wrapper usage (kclaude --help / -h) -------------------------------------
if ($ClaudeArgs.Count -eq 1 -and ($ClaudeArgs[0] -in @('--help', '-h', '/?'))) {
  Write-Host "kclaude -- Claude Code launcher (Power Pack wrapper)"
  Write-Host ""
  Write-Host "  Pre-launch (fast): transcript-anchored auto-resume (W2), same-repo"
  Write-Host "  coordinator (W4), CO-08 hot-session cap; advisories (W1 context, W5"
  Write-Host "  cost/burn) print from a background-refreshed cache. Names new"
  Write-Host "  sessions in the background (W3)."
  Write-Host ""
  Write-Host "  Usage:  kclaude [claude args...]    all args pass through to claude"
  Write-Host "          cd <repo> ; kclaude          auto-resumes that repo's latest session"
  Write-Host "          kclaude -n | --new           force a NEW session (skip auto-resume)"
  Write-Host "          kclaude --resume <sid>       resume a specific session (honored as-is)"
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
$advCache = Join-Path $env:USERPROFILE ".claude\cache\kclaude_advisories.json"

# --- helper: fast (launch-critical) prelaunch decision, or $null -------------
function Get-FastDecision {
  $d = $null
  if ($py -and (Test-Path $pre)) {
    try {
      $env:PYTHONIOENCODING = 'utf-8'
      $raw = & $py $pre --cwd $cwd --mode fast 2>$null
      if ($raw) { $d = ($raw | ConvertFrom-Json) }
    } catch { $d = $null }
  }
  return $d
}

# --- helper: print cached advisories from the previous launch (fail-open) ----
function Show-CachedAdvisories {
  try {
    if (-not (Test-Path $advCache)) { return }
    $c = Get-Content $advCache -Raw -ErrorAction Stop | ConvertFrom-Json
    if (-not $c) { return }
    if ($c.cwd -and ($c.cwd -ne $cwd)) { return }   # advisories are per-cwd
    $ts = [datetime]::MinValue
    if ([datetime]::TryParse([string]$c.ts, [ref]$ts)) {
      if (((Get-Date).ToUniversalTime() - $ts.ToUniversalTime()).TotalHours -gt 6) { return }
    }
    foreach ($a in @($c.advisories)) { if ($a) { Write-Host $a -ForegroundColor Yellow } }
  } catch { }
}

# --- helper: detached background advisory refresh (non-blocking) -------------
function Start-AdvisoryRefresh {
  if ($py -and (Test-Path $pre)) {
    try {
      Start-Process -FilePath $py -WindowStyle Hidden `
        -ArgumentList @($pre, '--cwd', $cwd, '--mode', 'advisories') | Out-Null
    } catch { }
  }
}

# --- helper: timed key read (multiple-session pick; default on timeout) ------
function Read-HostTimed([int]$timeoutSec) {
  try {
    $sb = New-Object System.Text.StringBuilder
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) {
      if ([Console]::KeyAvailable) {
        $k = [Console]::ReadKey($true)
        if ($k.Key -eq 'Enter') { return $sb.ToString() }
        if ($k.Key -eq 'Escape') { return '__ESC__' }
        if ($k.KeyChar) { [void]$sb.Append($k.KeyChar); Write-Host -NoNewline $k.KeyChar }
      } else { Start-Sleep -Milliseconds 80 }
    }
    Write-Host ""
    return $sb.ToString()   # timeout -> empty -> default to most recent
  } catch { return '' }     # non-interactive / redirected input -> default
}

# --- passthrough arg inspection ----------------------------------------------
# Honor an explicit --resume/--continue (skip auto-resume); strip -n/--new.
$explicitResume = $false
$forceNew = $false
if ($ClaudeArgs) {
  $filtered = @()
  foreach ($a in $ClaudeArgs) {
    if ($a -in @('-n', '--new')) { $forceNew = $true; continue }
    if ($a -in @('--resume', '-r', '--continue', '-c') -or $a -like '--resume=*') {
      $explicitResume = $true
    }
    $filtered += $a
  }
  $ClaudeArgs = $filtered
}

# --- run FAST prelaunch (launch-critical) ------------------------------------
$decision = Get-FastDecision

# --- advisories: print cached (instant) + refresh in the background ----------
Show-CachedAdvisories
Start-AdvisoryRefresh

# --- decide resume vs new ----------------------------------------------------
$resumeArg = $null
$newSession = $true

if ($explicitResume) {
  # Owner passed --resume/--continue: pass it through verbatim, no auto-resume.
  $newSession = $false
} elseif ($forceNew) {
  # -n/--new: force a fresh session even when one is active (the escape hatch
  # that keeps "start new on an active repo" reachable after the F2 silent-resume).
  $newSession = $true
} elseif ($decision -and $decision.coord -and $decision.coord.active -and
          $decision.coord.source -eq 'multiple') {
  # MULTIPLE active sessions on this repo -> numbered list, 3s timed default.
  Write-Host $decision.coord.warning -ForegroundColor Cyan
  Write-Host "  [Enter=mas reciente | numero=elegir | n=nueva | 3s auto]" -ForegroundColor DarkGray
  $ans = Read-HostTimed 3
  if ($ans -eq '__ESC__' -or $ans -match '^[Nn]') {
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
    $resumeArg = $decision.coord.default_resume           # Enter / timeout -> most recent
    $newSession = $false
  }
} elseif ($decision -and $decision.coord -and $decision.coord.active) {
  # SINGLE active session -> SILENT auto-resume, no dialog (F2,
  # T-W4-DIALOG-SINGLE-SESSION-001). This is the base case and must be quiet.
  $resumeArg = $decision.coord.default_resume; $newSession = $false
} elseif ($decision -and $decision.resume -and $decision.resume.resume_arg) {
  # No recent "active" session, but a resumable transcript exists -> auto-resume.
  $resumeArg = $decision.resume.resume_arg; $newSession = $false
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

# --- CO-00 resume context advisory (rung-2) ----------------------------------
# A session must be OPENED to be /compact-ed, so resuming a near/over-ceiling
# session is WARNED, not blocked (an honest rung-2 advisory). Fail-open: silent.
if ($resumeArg -and $decision -and $decision.resume_gate -and $decision.resume_gate.advise) {
  Write-Host $decision.resume_gate.message -ForegroundColor Yellow
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
# this same terminal. On restart the fast CO gates RE-RUN (F3a,
# HR-RESTART-VIA-KCLAUDE-001) so CO-00/CO-08 stay active after every restart.
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
  # F3a: re-run the fast CO gates so the Cognitive OS is ACTIVE after restart.
  $rd = Get-FastDecision
  if ($rd -and $rd.resume_gate -and $rd.resume_gate.advise) {
    Write-Host $rd.resume_gate.message -ForegroundColor Yellow
  }
  Show-CachedAdvisories
  Start-AdvisoryRefresh
  if ($sid) {
    Write-Host "[kclaude] Restart detected. Relaunching --resume $sid (CO active)..." -ForegroundColor Green
    Start-Sleep -Seconds 1
    $launch = @('--resume', $sid)
  } else {
    Write-Host "[kclaude] Restart detected. Relaunching --continue (CO active)..." -ForegroundColor Green
    Start-Sleep -Seconds 1
    $launch = @('--continue')
  }
}
