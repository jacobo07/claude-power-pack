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

  CO-08 scope-gate (PM-02, SCS C77): a pane's declared scope reaches the gate
  automatically. --scope declares a fresh pane in one flag; on resume the pane's
  own prior intent is recalled by prelaunch (--sid) and re-exported, so a scope
  declared once survives restarts. No declaration -> nothing exported ->
  SAME_REPO_CAP failsafe unchanged.

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
  Write-Host "          kclaude --scope <a,b>        declare this pane's CO-08 scope (PM-02)"
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
# $SidArg (when known: the resume target) lets prelaunch recall this pane's own
# declared PM-02 scope so the CO-08 gate is intent-aware after a restart.
function Get-FastDecision {
  param([string] $SidArg)
  $d = $null
  if ($py -and (Test-Path $pre)) {
    try {
      $env:PYTHONIOENCODING = 'utf-8'
      $fastArgs = @($pre, '--cwd', $cwd, '--mode', 'fast')
      if ($SidArg) { $fastArgs += @('--sid', $SidArg) }
      $raw = & $py @fastArgs 2>$null
      if ($raw) { $d = ($raw | ConvertFrom-Json) }
    } catch { $d = $null }
  }
  return $d
}

# --- helper: export the CO-08 scope prelaunch resolved into the launch env ----
# prelaunch echoes the scope it applied (from a --scope env or a recalled intent)
# as launch_scope/launch_sid; propagate them so the launched claude inherits the
# pane's active scope. Fail-open: absent fields -> no change (SAME_REPO_CAP).
function Set-LaunchScopeEnv($decision) {
  if ($decision -and $decision.launch_scope) {
    $env:PP_PANE_SCOPE = [string]$decision.launch_scope
  }
  if ($decision -and $decision.launch_sid) {
    $env:PP_PANE_SID = [string]$decision.launch_sid
  }
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

# --- helper: beacon this pane's session id for the Resource Governor ----------
# FASE A hibernation (process_governor): the governor maps a live claude.exe ->
# its session by reading %TEMP%\kclaude-pane-<wrapperpid>.sid. Without a beacon
# the pane has no resolvable sid and the governor KEEPS it (no-sid fail-safe), so
# this is best-effort and fail-open; it never blocks the launch.
function Write-PaneSidBeacon($sid) {
  if (-not $sid) { return }
  try {
    $b = Join-Path $env:TEMP ("kclaude-pane-{0}.sid" -f $PID)
    $o = [pscustomobject]@{ sid = $sid; cwd = $cwd; pid = $PID;
      ts = (Get-Date).ToUniversalTime().ToString('o') }
    ($o | ConvertTo-Json -Compress) | Set-Content -Path $b -Encoding UTF8 -NoNewline
  } catch { }
}

# --- passthrough arg inspection ----------------------------------------------
# Honor an explicit --resume/--continue; strip -n/--new (now a no-op -- a bare
# terminal-profile launch already opens a NEW session by default). Capture a
# --scope <tokens> flag (kclaude-only; never passed to claude) as this pane's
# CO-08 scope declaration.
$explicitResume = $false
$scopeFlag = $null
if ($ClaudeArgs) {
  $filtered = @()
  for ($i = 0; $i -lt $ClaudeArgs.Count; $i++) {
    $a = $ClaudeArgs[$i]
    if ($a -in @('-n', '--new')) { continue }             # no-op: new is default
    if ($a -eq '--scope') {
      if (($i + 1) -lt $ClaudeArgs.Count) { $scopeFlag = $ClaudeArgs[$i + 1]; $i++ }
      continue
    }
    if ($a -like '--scope=*') { $scopeFlag = $a.Substring(8); continue }
    if ($a -in @('--resume', '-r', '--continue', '-c') -or $a -like '--resume=*') {
      $explicitResume = $true
    }
    $filtered += $a
  }
  $ClaudeArgs = $filtered
}

# CO-08 scope-gate (PM-02, SCS C77): a --scope flag declares this pane's intent
# for a NEW pane in one command -- the only honest scope source for a cold pane
# (only the Owner knows what a fresh pane will touch). Exported BEFORE the fast
# prelaunch so the CO-08 gate is scope-aware THIS launch. Fail-open: no flag ->
# nothing exported -> SAME_REPO_CAP failsafe.
if ($scopeFlag) { $env:PP_PANE_SCOPE = $scopeFlag }

# --- resolve the initial resume sid (for CO-08 scope recall on resume) --------
# On an explicit --resume <sid> the pane's previously-declared intent (if any) is
# recalled from the PM-02 registry by prelaunch (--sid) and re-applied, so a
# scope declared once survives restarts. A fresh pane has no sid here -> nothing
# recalled (only a --scope flag can scope a cold pane).
$initSid = $null
for ($i = 0; $i -lt $ClaudeArgs.Count; $i++) {
  if (($ClaudeArgs[$i] -in @('--resume', '-r')) -and (($i + 1) -lt $ClaudeArgs.Count)) {
    $initSid = $ClaudeArgs[$i + 1]
  } elseif ($ClaudeArgs[$i] -like '--resume=*') {
    $initSid = $ClaudeArgs[$i].Substring(9)
  }
}

# --- run FAST prelaunch (launch-critical) ------------------------------------
$decision = Get-FastDecision $initSid
Set-LaunchScopeEnv $decision

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
  # FASE A: beacon our session id (when known) so the Resource Governor can map
  # this pane's claude.exe -> its session for hibernation. Covers every relaunch
  # (initial resume, /restart, hibernate rehydrate). A new never-resumed session
  # has no sid here and is left alone (governor no-sid keep).
  $paneSid = $null
  for ($i = 0; $i -lt $launch.Count; $i++) {
    if (($launch[$i] -in @('--resume', '-r')) -and (($i + 1) -lt $launch.Count)) {
      $paneSid = $launch[$i + 1]
    }
  }
  Write-PaneSidBeacon $paneSid

  & claude @launch
  $code = $LASTEXITCODE

  # FASE A: HIBERNATION WAKE. The Resource Governor may have killed THIS pane to
  # reclaim RAM, arming a wake flag keyed by our own pid. Park at a status line
  # and rehydrate --resume on the first keystroke. Honest limit: the keystroke is
  # a WAKE, not a message -- ConPTY stdin cannot deliver it into resumed claude,
  # so the Owner presses any key, then types. The terminal scrollback stays intact.
  $hibFlag = Join-Path $env:TEMP ("claude-hibernate-{0}.flag" -f $PID)
  if (Test-Path $hibFlag) {
    $hsid = $null; $hcwd = $null; $hts = $null
    try {
      $hj = Get-Content $hibFlag -Raw -ErrorAction Stop | ConvertFrom-Json
      $hsid = $hj.sid; $hcwd = $hj.cwd; $hts = $hj.ts
    } catch { }
    $label = if ($hcwd) { Split-Path $hcwd -Leaf } else { 'session' }
    Write-Host ""
    Write-Host ("  [*] '$label' hibernated to free RAM. Press any key to continue.") -ForegroundColor Cyan
    Write-Host ("      Conversation preserved -- rehydrates via --resume. Idle since $hts.") -ForegroundColor DarkGray
    try { [void][System.Console]::ReadKey($true) } catch { }
    Remove-Item $hibFlag -Force -ErrorAction SilentlyContinue
    Write-Host "  [~] Rehydrating session..." -ForegroundColor Green
    if ($hsid) { $launch = @('--resume', $hsid) } else { $launch = @('--continue') }
    # Re-run the fast CO gates so the Cognitive OS is active after rehydrate; pass
    # the sid so this pane's declared CO-08 scope is recalled + re-exported.
    $rdH = Get-FastDecision $hsid
    Set-LaunchScopeEnv $rdH
    Show-CachedAdvisories
    Start-AdvisoryRefresh
    continue
  }

  $flag = Get-ChildItem $flagPattern -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $flag) {
    Remove-Item (Join-Path $env:TEMP ("kclaude-pane-{0}.sid" -f $PID)) `
      -Force -ErrorAction SilentlyContinue
    exit $code
  }
  Remove-Item $flag.FullName -Force -ErrorAction SilentlyContinue
  $sid = $null
  if (Test-Path $sidFile) {
    $sid = (Get-Content $sidFile -Raw -ErrorAction SilentlyContinue)
    if ($sid) { $sid = $sid.Trim() }
    Remove-Item $sidFile -Force -ErrorAction SilentlyContinue
  }
  Write-Host ""
  # F3a: re-run the fast CO gates so the Cognitive OS is ACTIVE after restart;
  # pass the sid so the pane's declared CO-08 scope is recalled + re-exported.
  $rd = Get-FastDecision $sid
  if ($rd -and $rd.resume_gate -and $rd.resume_gate.advise) {
    Write-Host $rd.resume_gate.message -ForegroundColor Yellow
  }
  Set-LaunchScopeEnv $rd
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
