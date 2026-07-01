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

# --- passthrough arg inspection ----------------------------------------------
# Honor an explicit --resume/--continue; strip -n/--new (now a no-op -- a bare
# terminal-profile launch already opens a NEW session by default).
$explicitResume = $false
if ($ClaudeArgs) {
  $filtered = @()
  foreach ($a in $ClaudeArgs) {
    if ($a -in @('-n', '--new')) { continue }             # no-op: new is default
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
# T-KCLAUDE-LAUNCH-CONTEXT-001: a terminal-profile / bare launch ALWAYS opens a
# NEW session (parity with the native Claude button). Auto-resume happens ONLY
# on an explicit --resume/--continue -- from the Owner, from the "Last session"
# lazarus route, from the /restart clipboard, or from the restart loop below.
# The coordinator + advisories are informational only; they never auto-resume.
$resumeArg = $null
if ($explicitResume) {
  $newSession = $false                 # honor explicit resume, pass through
} else {
  $newSession = $true                  # bare launch -> a fresh session
}

# --- CO-08 hot-session cap (ADVISORY on a bare launch) -----------------------
# "Gates active, but never auto-resume": the CO-08 cap still EVALUATES and WARNS
# when hot-session pressure is high, but a terminal-profile launch always
# proceeds with the new session -- it never blocks or force-resumes (that would
# re-introduce landing in a prior session, the exact BUG A). An explicit
# --resume never reaches here (newSession is false). Fail-open: silent when the
# gate is missing or proceed.
if ($newSession -and $decision -and $decision.gate -and $decision.gate.verdict -eq 'refuse') {
  $hot = $decision.gate.hot_count; $cap = $decision.gate.cap
  Write-Host ("PP CO-08: $hot hot session(s) on this repo (soft cap $cap) -- opening a new one anyway.") -ForegroundColor Yellow
  Write-Host "  Tip: /compact or close an idle session to relieve token pressure." -ForegroundColor DarkGray
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
