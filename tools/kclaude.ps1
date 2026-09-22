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

# --- FD-00/FD-07 frontier-session marker (SCS C82 EXECUTION-mode) -------------
# kclaude launches Claude Code on the host default model, which is Opus (a
# frontier model) on this host -- so a kclaude session IS a frontier session by
# construction. Export PP_FRONTIER_SESSION so the FD-07 close-boundary flywheel (a
# Stop-chain child) knows to turn the distillation loop at this session's close;
# the launched claude and every hook child it spawns inherit this env var. A bare
# `claude` launch never sets it, so the flywheel is a silent no-op there. Purely
# advisory downstream (ASCII-only, PS 5.1 safe); nothing here can abort the launch.
$env:PP_FRONTIER_SESSION = '1'

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

# --- helper: paste-window step counter (T-KCLAUDE-PASTE-WINDOW-001) ----------
# When KCLAUDE_TRACE_FILE is set, every SYNCHRONOUS step that runs before
# `& claude` appends one line naming itself, and the launch appends `launch`.
# A count of steps is load-independent; a timing on this host is not (python's
# own floor measured 458-704 ms across three consecutive runs). The gate
# tools/test_kclaude_paste_window.py reads this trace. Trace mode is a PROBE:
# it also suppresses the detached spawns and the settings repair, so running
# the gate never writes the Owner's advisory cache or settings.json.
function Trace-Step([string] $Step) {
  if ($env:KCLAUDE_TRACE_FILE) {
    try { Add-Content -Path $env:KCLAUDE_TRACE_FILE -Value $Step -Encoding ASCII } catch { }
  }
}

# --- helper: fast (launch-critical) prelaunch decision, or $null -------------
# $SidArg (when known: the resume target) lets prelaunch recall this pane's own
# declared PM-02 scope so the CO-08 gate is intent-aware after a restart.
function Get-FastDecision {
  param([string] $SidArg)
  $d = $null
  if ($py -and (Test-Path $pre)) {
    try {
      Trace-Step 'sync:prelaunch-fast'
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
  if ($env:KCLAUDE_TRACE_FILE) { return }   # probe mode: never write the Owner's cache
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

# --- PASTE WINDOW: nothing blocking before `& claude` on a bare pane ----------
# T-KCLAUDE-PASTE-WINDOW-001 (2026-09-22). Symptom: pasting a prompt into a NEW
# pane did not work. Root cause: every millisecond this script spends before
# `& claude` is time in which the pane is NOT Claude. Claude's prompt box, and
# the bracketed-paste mode that lets a multi-line paste arrive as ONE paste, do
# not exist yet, so a paste landing here goes to a console with no reader for
# it -- it is lost, or its newlines arrive as Enter keys. Measured before this
# fix (median of 3, host at ~8 GB free): prelaunch --mode fast 1145 ms plus the
# hook-registry check 1081 ms = ~2.2 s of synchronous Python, on top of the
# interpreter floor of ~650 ms each. Claude's own SessionStart chain (~4.7 s)
# is NOT part of the window: it delays SUBMISSION, the prompt box accepts a
# paste while it runs.
#
# The rule this encodes, and the gate that holds it (tools/test_kclaude_paste_
# window.py): on a bare pane NOTHING synchronous runs before `& claude` except
# what the launch itself consumes. Anything informational is detached or
# served from a cache. A new blocking step must justify itself against that
# gate, not against its own runtime in isolation.
#
# The fast prelaunch returns nothing launch-critical for a bare pane: scope
# recall needs a sid (a bare pane has none) and --scope is exported above
# already; the resume gate is keyed on $resumeArg, which a bare pane never has;
# the CO-08 warning never blocked anything and now rides the cached advisories
# (prelaunch.run_advisories); and the namer's "which sessions existed before"
# list is read from disk below in ~6 ms, BEFORE launch, so it cannot race the
# new transcript. Resume and --scope panes keep the synchronous decision,
# because there it is load-bearing.
$barePane = (-not $explicitResume) -and (-not $scopeFlag) -and (-not $initSid)
if ($barePane) {
  $decision = $null
} else {
  $decision = Get-FastDecision $initSid
  Set-LaunchScopeEnv $decision
}

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
      if ($decision -and $decision.known_sids) {
        $known = ($decision.known_sids -join ',')
      } else {
        # Bare pane: the sessions that exist BEFORE this launch are exactly the
        # transcripts already on disk for this cwd. Same directory encoding as
        # auto_resumer._encode_cwd; read here, pre-launch, so the new session's
        # own transcript cannot be in it. Newest 400 only, to stay well under
        # the 32K command-line limit (the largest project measured held 115).
        try {
          $projDir = Join-Path $env:USERPROFILE ('.claude\projects\' + ($cwd -replace '[^a-zA-Z0-9]', '-'))
          if (Test-Path $projDir) {
            $known = (@(Get-ChildItem $projDir -Filter *.jsonl -File -ErrorAction Stop |
              Sort-Object LastWriteTime -Descending | Select-Object -First 400 |
              ForEach-Object { $_.BaseName }) -join ',')
          }
        } catch { $known = "" }
      }
      if ($env:KCLAUDE_TRACE_FILE) {
        # Probe mode: report what the namer WOULD receive instead of spawning it.
        Trace-Step ('known:' + @($known -split ',' | Where-Object { $_ }).Count)
      } else {
        Start-Process -FilePath $py -WindowStyle Hidden `
          -ArgumentList @($namer, '--cwd', $cwd, '--known', $known) | Out-Null
      }
    } elseif ($resumeArg -match 'resume\s+(\S+)') {
      Start-Process -FilePath $py -WindowStyle Hidden `
        -ArgumentList @($namer, '--cwd', $cwd, '--resume-sid', $matches[1]) | Out-Null
    }
  } catch { }
}

# --- dead-screen guard: conhost --headless hook wrappers ---------------------
# T-CONHOST-HOOK-REINFECTION-001. Orca X re-registers 11 hook entries across 11
# events, each wrapped as `conhost.exe --headless cmd.exe /d /c <hook>`. conhost
# allocates a pseudoconsole whose output does NOT return through the parent pipe:
# it goes straight to the ATTACHED TERMINAL carrying ESC[2J (erase display) and
# ESC[H (home). On PreToolUse with matcher '*' that wipes the Owner's screen on
# EVERY tool call in EVERY repository -- the exact shape of "me pasa en todos mis
# repos" -- and discards the wrapped hook's stdout.
#
# A one-time repair does not hold: the installer reinstates on its next launch
# (measured 2026-09-11 -- removed 21:37, back by 22:27). So it is re-applied at
# launch, the one moment independent of the installer's cadence. The full
# rationale, the byte measurements and the unwrap-never-delete contract live in
# the guard file; it is ONE definition, dot-sourced, so the gate drives exactly
# the code that ships here.
#
# Fail-open: a missing or broken guard file leaves Repair-HookWrappers undefined
# and the call site below tolerates that. A screen-clear guard must never be the
# reason a launch fails.
$wrapGuard = Join-Path $env:USERPROFILE '.claude\bin\repair-hook-wrappers.ps1'
if (Test-Path $wrapGuard) { try { . $wrapGuard } catch { } }

# --- launch claude, with /restart loop (supersedes kclaude.bat) --------------
# Absorbs the MC-LAZ-26 resume loop: when /restart drops a flag, relaunch the
# SAME session (--resume <sid> from the lazarus SID file, else --continue) in
# this same terminal. On restart the fast CO gates RE-RUN (F3a,
# HR-RESTART-VIA-KCLAUDE-001) so CO-00/CO-08 stay active after every restart.
$flagPattern = Join-Path $env:TEMP 'claude-restart-*.flag'
$sidFile = Join-Path $env:USERPROFILE '.claude\lazarus\kclaude-restart-sid.txt'
# Pane-keyed handshake (HR-RESTART-PANE-KEYED-001, 2026-09-15). restart-claude.ps1
# writes claude-restart-w<wrapperpid>.flag and kclaude-restart-sid-w<wrapperpid>.txt
# for the pane that owns the exiting claude.exe; the un-suffixed names are the
# legacy global pair, kept so a pane running an older in-memory loop still works.
$flagPaneFile = Join-Path $env:TEMP ("claude-restart-w{0}.flag" -f $PID)
$sidFilePane = Join-Path $env:USERPROFILE ".claude\lazarus\kclaude-restart-sid-w$PID.txt"
# Purge OUR OWN stale flag only. The old line purged the whole glob, so launching
# any pane destroyed every other pane's pending restart flag -- open Cursor with
# 19 panes and whichever was mid-restart lost its handshake and fell to the shell.
Remove-Item $flagPaneFile -Force -ErrorAction SilentlyContinue

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

  # Dead-screen guard: re-strip the conhost wrappers the installer may have
  # reinstated since the last launch. Inside the loop on purpose -- a /restart or
  # a hibernate-rehydrate is a fresh config read and deserves the same clean
  # registry as a cold launch. Guarded on the command existing: if the dot-source
  # above failed, this is a silent no-op rather than a CommandNotFound error.
  # Probe mode skips it: a gate run must never rewrite the live settings.json.
  # Its own gate is tools/test_kclaude_conhost_repair.py. Measured 17 ms on a
  # clean registry, so it is not part of the paste-window cost.
  if ((-not $env:KCLAUDE_TRACE_FILE) -and (Get-Command Repair-HookWrappers -ErrorAction SilentlyContinue)) {
    try { [void](Repair-HookWrappers) } catch { }
  }

  # Hook-registration integrity (incident 2026-09-16 20:02 -> 2026-09-18 13:55).
  # A settings rewrite dropped --event= from all six dispatcher registrations and
  # every hook-based health check went dark WITH the substrate it was meant to
  # watch. This check runs OUTSIDE that substrate, at the moment that decides a
  # session's config generation. DETECT ONLY: it never rewrites settings.json --
  # repair needs a known-good source and a human-visible decision. Fail-open for
  # the launch itself; loud on screen when the registry is invalid. The receipt
  # line records which settings bytes this pane launched on (config generation).
  try {
    $hrTool = Join-Path $env:USERPROFILE '.claude\skills\claude-power-pack\tools\test_hook_registration_integrity.py'
    $hrPy = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
    $hrSettings = Join-Path $env:USERPROFILE '.claude\settings.json'
    if ((Test-Path $hrTool) -and (Test-Path $hrPy) -and (Test-Path $hrSettings)) {
      $hrGen = (Get-FileHash $hrSettings -Algorithm SHA256).Hash.Substring(0, 16)
      $hrState = if ($env:CLAUDE_STATE_DIR) { $env:CLAUDE_STATE_DIR } else { Join-Path $env:USERPROFILE '.claude\state' }
      # CONTENT-ADDRESSED VERDICT CACHE (T-KCLAUDE-PASTE-WINDOW-001). This check
      # cost ~1.1 s of the paste window on EVERY launch, and its verdict is a pure
      # function of four inputs: the settings bytes, the dispatcher source whose
      # exports it loads, the checker's own source, and whether each dispatcher
      # target named in settings exists. Same four -> same verdict, so a VALID
      # verdict is reused when, and only when, all four match; any change re-runs
      # the checker synchronously, which is exactly the launch after a rewrite --
      # the case the check exists for. Only VALID is cached: INVALID and
      # UNJUDGEABLE always re-run, so a broken registry is never silenced by a
      # cache hit. The receipt says `cached` so the generations ledger stays
      # honest about which launches were judged live.
      $hrKey = $null
      try {
        $hrDisp = Join-Path $env:USERPROFILE '.claude\skills\claude-power-pack\hooks\hook-dispatcher.js'
        $hrText = [IO.File]::ReadAllText($hrSettings)
        $hrTargets = @([regex]::Matches($hrText, '"([^"]*hook-dispatcher\.js)"') |
          ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique |
          ForEach-Object { $p = $_ -replace '^~', $env:USERPROFILE; '{0}={1}' -f $_, [int](Test-Path $p) })
        $hrKey = @(
          $hrGen,
          (Get-FileHash $hrDisp -Algorithm SHA256).Hash.Substring(0, 16),
          (Get-FileHash $hrTool -Algorithm SHA256).Hash.Substring(0, 16),
          ($hrTargets -join ';')
        ) -join '|'
      } catch { $hrKey = $null }
      $hrCache = Join-Path $hrState 'hook-registry-verdict-cache.json'
      $hrCached = $false
      if ($hrKey) {
        try {
          $hc = Get-Content $hrCache -Raw -ErrorAction Stop | ConvertFrom-Json
          if ($hc.verdict -eq 'VALID' -and $hc.key -eq $hrKey) { $hrCached = $true }
        } catch { }
      }
      if ($hrCached) {
        $hrOut = ''; $hrRc = 0
      } else {
        Trace-Step 'sync:hook-registry'
        $env:PYTHONIOENCODING = 'utf-8'
        $hrOut = & $hrPy $hrTool --live-only 2>&1 | Out-String
        $hrRc = $LASTEXITCODE
        if ($hrRc -eq 0 -and $hrKey) {
          try {
            $hcBody = '{{"key":"{0}","verdict":"VALID","ts":"{1}"}}' -f ($hrKey -replace '\\', '\\' -replace '"', '\"'), (Get-Date).ToString('o')
            [IO.File]::WriteAllText($hrCache, $hcBody, (New-Object Text.UTF8Encoding($false)))
          } catch { }
        }
      }
      $hrVerdict = if ($hrRc -eq 0) { 'VALID' } elseif ($hrRc -eq 1) { 'INVALID' } else { 'UNJUDGEABLE' }
      $hrLine = '{{"ts":"{0}","pane_pid":{1},"settings_sha16":"{2}","verdict":"{3}","cached":{4}}}' -f (Get-Date).ToString('o'), $PID, $hrGen, $hrVerdict, $(if ($hrCached) { 'true' } else { 'false' })
      Add-Content -Path (Join-Path $hrState 'session-config-generations.jsonl') -Value $hrLine -Encoding ASCII
      if ($hrRc -eq 1) {
        Write-Host ''
        Write-Host '!!! POWER PACK HOOK REGISTRY INVALID -- security/Stop/prompt hooks may NOT run in this session !!!' -ForegroundColor Red
        ($hrOut -split "`n") | Where-Object { $_ -match '^FAIL' } | ForEach-Object { Write-Host ('    ' + $_.Trim()) -ForegroundColor Red }
        Write-Host '    Re-check: python tools/test_hook_registration_integrity.py --live' -ForegroundColor Red
        Write-Host ''
      } elseif ($hrRc -ne 0) {
        Write-Host ('[kclaude] hook registry could not be judged (rc=' + $hrRc + ')') -ForegroundColor Yellow
      }
    }
  } catch { }

  Trace-Step 'launch'
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

  # Our own flag first. Only fall back to the global glob when this pane has no
  # pane-keyed flag AND no other pane could have claimed one -- i.e. the flag was
  # written by an older restart-claude.ps1 that did not key by wrapper.
  $flag = $null
  $flagWasMine = $false
  if (Test-Path $flagPaneFile) {
    $flag = Get-Item $flagPaneFile -ErrorAction SilentlyContinue
    $flagWasMine = $true
  } else {
    $legacy = Get-ChildItem $flagPattern -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -notmatch '^claude-restart-w\d+\.flag$' } |
      Select-Object -First 1
    $flag = $legacy
  }
  if (-not $flag) {
    Remove-Item (Join-Path $env:TEMP ("kclaude-pane-{0}.sid" -f $PID)) `
      -Force -ErrorAction SilentlyContinue
    exit $code
  }
  Remove-Item $flag.FullName -Force -ErrorAction SilentlyContinue
  # Read the pane-keyed sid when the flag was ours; only a pane-keyed flag proves
  # the sid belongs to THIS pane. Falling back to the global slot on our own flag
  # is how a pane used to resume another pane's session.
  $sid = $null
  $sidSource = if ($flagWasMine) { $sidFilePane } else { $sidFile }
  if (Test-Path $sidSource) {
    $sid = (Get-Content $sidSource -Raw -ErrorAction SilentlyContinue)
    if ($sid) { $sid = $sid.Trim() }
    Remove-Item $sidSource -Force -ErrorAction SilentlyContinue
  }
  if ($flagWasMine -and -not $sid -and (Test-Path $sidFile)) {
    # Our flag, but no pane-keyed sid: an older restart-claude.ps1 wrote only the
    # global slot. Better to resume the one session recorded than to relaunch bare.
    $sid = (Get-Content $sidFile -Raw -ErrorAction SilentlyContinue)
    if ($sid) { $sid = $sid.Trim() }
    Remove-Item $sidFile -Force -ErrorAction SilentlyContinue
  }
  # Deliberately do NOT delete the global sid file here. After a pane-keyed read
  # it may already hold a DIFFERENT pane's pending sid, and deleting it is how a
  # pane makes its neighbour relaunch bare -- the bug this change exists to end.
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
