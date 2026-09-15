# orphan-dev-server-reaper.ps1
#
# SessionEnd + SessionStart hook (sealed 2026-05-22 after a 39-process
# / 3 GB RAM burn crashed the host mid-MC-IO-2800 iteration; extended
# 2026-05-22 evening after a 2nd host crash with 9 accumulated
# Notion-MCP bunx-cached respawns + 2 Playwright children = ~510 MB
# leak). Reaps node.exe processes that the dying session spawned
# but never properly stopped — Next.js dev servers via corepack pnpm,
# Playwright MCP children whose parent connection dropped, Turbopack
# helper fans, AND bunx-cached MCP-server respawns whose host process
# died without graceful SIGTERM propagation.
#
# Conservative pattern match: only kills processes whose command
# line clearly identifies them as dev-time orphans. Cursor's own
# nodes and claude-power-pack daemons are untouched.
#
# Notion-MCP rule: only the BUNX-CACHED temp-path variant is reaped
# (the leak pattern). A future cleaner global install of notion-mcp
# would have a different command-line shape and would NOT match.
#
# Idempotent. Logs to ~/.claude/cache/orphan-reaper.log so any drift
# is visible.

$ErrorActionPreference = 'SilentlyContinue'

$logDir = "$env:USERPROFILE\.claude\cache"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$log = "$logDir\orphan-reaper.log"

$ts = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'

# ---------------------------------------------------------------------------
# Electron husk reaper (sealed 2026-09-04, Orca X)
#
# The node.exe scan below cannot see this class at all: an Electron app's main
# process carries the APP's exe name, so `Name='node.exe'` is blind to it by
# construction. That aperture gap cost a hand-diagnosis when an `Orca X.exe`
# main process survived for days with no window, no renderer and no tray, and
# then blocked its own installer with "close the application manually" — there
# was nothing to close, so the instruction could not be followed.
#
# THE SIGNATURE, and why each clause is load-bearing:
#   1. not a child of a live process of the SAME app — Electron's renderer, GPU
#      and utility processes all carry the app's exe name and each has zero
#      children and no window of its own. Without this clause a healthy app's
#      renderer matches the husk shape exactly, and the rule eats the app it was
#      written to clean up after. Measured, not theorised: a live Orca showed one
#      main with 5 children and five children with 0 each.
#   2. zero child processes — a main process with a window ALWAYS has at least a
#      renderer child. A husk has none, which is the same thing as "no UI".
#   3. no main window handle — corroborates (2) from a different angle.
#   4. older than the grace period — a launching app is briefly childless while
#      main boots before the first window.
#
# A live app satisfies none of these as a root. The daemon (orca-terminal-daemon)
# is deliberately out of scope: it is designed to outlive the app and holds live
# PTY sessions.
#
# Run with -HuskSelfTest to drive the refusals, not just the catch; a rule whose
# refusal path nobody exercised is not a rule yet.
# ---------------------------------------------------------------------------

$huskExeNames = @('Orca X.exe', 'Orca.exe')
$huskMinAgeMinutes = 30

function Test-IsElectronHusk {
  param(
    [bool]$IsChildOfSameApp,
    [int]$ChildCount,
    [long]$MainWindowHandle,
    [double]$AgeMinutes,
    [int]$MinAgeMinutes = 30
  )
  if ($IsChildOfSameApp) { return $false }
  return ($ChildCount -eq 0) -and ($MainWindowHandle -eq 0) -and ($AgeMinutes -ge $MinAgeMinutes)
}

if ($args -contains '-HuskSelfTest') {
  $cases = @(
    @{ n = 'husk: root, no children, no window, old';   k = $false; c = 0; h = 0;   a = 600; want = $true  },
    @{ n = 'live main: has renderer children';          k = $false; c = 5; h = 0;   a = 600; want = $false },
    @{ n = 'live main: has a visible window';           k = $false; c = 0; h = 123; a = 600; want = $false },
    @{ n = 'young root: still booting its first window'; k = $false; c = 0; h = 0;  a = 2;   want = $false },
    @{ n = 'renderer child of a live main, hours old';  k = $true;  c = 0; h = 0;   a = 600; want = $false }
  )
  $fails = 0
  foreach ($c in $cases) {
    $got = Test-IsElectronHusk -IsChildOfSameApp $c.k -ChildCount $c.c -MainWindowHandle $c.h -AgeMinutes $c.a -MinAgeMinutes $huskMinAgeMinutes
    if ($got -ne $c.want) { $fails++; "FAIL $($c.n): got=$got want=$($c.want)" } else { "ok   $($c.n)" }
  }
  "HUSK_SELFTEST=$($cases.Count - $fails)/$($cases.Count)"
  exit ($(if ($fails -eq 0) { 0 } else { 1 }))
}

try {
  $now = Get-Date
  $huskProcessNames = @($huskExeNames | ForEach-Object { [System.IO.Path]::GetFileNameWithoutExtension($_) })
  $childCountByParent = @{}
  $parentOf = @{}
  foreach ($proc in (Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId)) {
    $procId = [int]$proc.ProcessId
    $parentId = if ($null -eq $proc.ParentProcessId) { 0 } else { [int]$proc.ParentProcessId }
    $parentOf[$procId] = $parentId
    $childCountByParent[$parentId] = 1 + ([int]$childCountByParent[$parentId])
  }
  $appProcesses = Get-Process -ErrorAction SilentlyContinue | Where-Object { $huskProcessNames -contains $_.ProcessName }
  $appProcessIds = @{}
  foreach ($appProcess in $appProcesses) { $appProcessIds[[int]$appProcess.Id] = $true }
  foreach ($candidate in $appProcesses) {
    $parentId = [int]$parentOf[[int]$candidate.Id]
    $isChildOfSameApp = [bool]$appProcessIds[$parentId]
    $ageMinutes = ($now - $candidate.StartTime).TotalMinutes
    $children = [int]$childCountByParent[[int]$candidate.Id]
    if (-not (Test-IsElectronHusk -IsChildOfSameApp $isChildOfSameApp -ChildCount $children -MainWindowHandle ([long]$candidate.MainWindowHandle) -AgeMinutes $ageMinutes -MinAgeMinutes $huskMinAgeMinutes)) {
      continue
    }
    $wsMB = [math]::Round($candidate.WorkingSet64 / 1MB)
    try {
      Stop-Process -Id $candidate.Id -Force -ErrorAction Stop
      Add-Content -Path $log -Value "[$ts] HUSK_REAPED $($candidate.ProcessName) pid=$($candidate.Id) age_min=$([math]::Round($ageMinutes)) ws_mb=$wsMB children=0"
    } catch {
      Add-Content -Path $log -Value "[$ts] HUSK_KILL_FAIL $($candidate.ProcessName) pid=$($candidate.Id): $($_.Exception.Message)"
    }
  }
} catch {
  Add-Content -Path $log -Value "[$ts] HUSK_SCAN_FAIL: $($_.Exception.Message)"
}

# ---------------------------------------------------------------------------
# Never-resumed child reaper (sealed 2026-09-13, KobiiCraft Core Files)
#
# The pattern scan below cannot see this class either, and for a sharper reason
# than the Electron husk: these processes have no distinguishing command line
# at all. They are ordinary hook children — the statusline, the live-snapshotter,
# the sentinel — that were CREATED and never RESUMED. The parent died between
# CreateProcess and ResumeThread, so the child sits in a single waiting thread
# forever: no CPU, no output, no exit code, no error, no log line.
#
# MEASURED 2026-09-13 on this host: 168 node.exe, ALL 168 parents dead, 148 of
# them gsd-statusline.js, 143 spawned that same day, oldest 74.6 hours, holding
# 573 MB of paged commit. The estate had no instrument that could see them —
# a process consuming zero CPU and producing zero bytes looks exactly like a
# process that exited cleanly.
#
# Note what this defeats: gsd-statusline.js carries its OWN guard against
# hanging on stdin (a 3s timer that calls process.exit). The guard is correct
# and unreachable, because the JS never runs. A guard inside a process cannot
# protect a process that never executed an instruction.
#
# THE SIGNATURE, and why each clause is load-bearing:
#   1. the command line points inside ~/.claude — it is ours to reap. Scope,
#      not safety; clause 3 is what makes it safe.
#   2. the parent no longer exists — nothing is waiting on it, so nothing can
#      be broken by its death.
#   3. kernel time + user time == 0 since creation — THE load-bearing clause.
#      A process that has never executed an instruction cannot be doing work,
#      cannot hold state, and has nothing to lose. This is also what separates
#      "never started" from "legitimately long": a real long-running task has
#      burned CPU. Without this clause the rule would eat healthy work, which
#      is strictly worse than the leak it was written to stop.
#   4. older than the grace period — a child spawned moments ago may simply not
#      have been scheduled yet. Without this, the rule races the live statusline.
#
# Run with -GhostSelfTest to drive the REFUSALS, not just the catch.
# ---------------------------------------------------------------------------

$ghostMinAgeSeconds = 120

# CPU time has THREE states here, not two, and collapsing the third into "zero"
# is how a safety check becomes a hazard. Measured 2026-09-13: of 16 node
# processes, 4 could not be read at all (gone between enumerations, or access
# denied). Unreadable is not evidence of anything — least of all that a process
# never ran — so it refuses.
function Test-IsNeverResumedChild {
  param(
    [bool]$IsOurs,
    [bool]$ParentAlive,
    [bool]$CpuKnown,
    [long]$CpuTicks,
    [double]$AgeSeconds,
    [int]$MinAgeSeconds = 120
  )
  if (-not $IsOurs) { return $false }
  if ($ParentAlive) { return $false }
  if (-not $CpuKnown) { return $false }
  if ($CpuTicks -ne 0) { return $false }
  return ($AgeSeconds -ge $MinAgeSeconds)
}

# ---------------------------------------------------------------------------
# Abandoned-hook reaper (sealed 2026-09-15)
#
# THE THIRD APERTURE GAP IN THIS FILE, and the same shape as the other two: the
# scan above cannot see this class BY CONSTRUCTION, because its load-bearing
# clause is `CpuTicks -eq 0` and its own self-test enshrines the refusal
# ("healthy long task: has burned CPU -> want = $false"). That clause is correct
# for its subject and structurally blind to this one: a hook that was spawned,
# RAN, breached its timeout and was orphaned has burned CPU by definition. It is
# exactly the population the other rule promises to spare.
#
# MEASURED 2026-09-15 on this host, which is what forced the rule:
#   node/python processes alive        65
#     orphaned (parent gone)           49     holding 271 MB
#     oldest orphan                    11/09  (4 days)
#   host free memory                   518 MB of 32,061 MB   (1.6 %)
#   hook-dispatcher timeout events     15,574 (28,508 log lines)
# spawnSync's timeout kills the DIRECT CHILD ONLY. Every one of those 15,574
# timeouts was an opportunity to strand a descendant, and the strandings
# accumulate into the RAM starvation that makes the next hook breach its budget.
# The timeout is not the protection here; unreaped, it is the engine.
#
# WHY KILLING THESE IS SAFE — a DIFFERENT argument from clause 3 above, not a
# loosening of it. Do not merge the two rules:
#   1. ours to reap — the command line points inside ~/.claude. Scope, not safety.
#   2. the parent is gone — and a hook's ENTIRE output contract is stdout read by
#      its parent. A hook whose parent is dead cannot deliver its result to
#      anybody, ever, whatever it computes next. It is not working; it is writing
#      to a closed pipe. THIS is the load-bearing clause, and it is stronger than
#      "never ran" because it does not care whether the process did work: the work
#      is undeliverable either way.
#   3. older than EVERY declared contract — the longest timeoutMs in CHAIN_MAP is
#      70 s and the longest harness budget is 120 s, so a floor of 300 s means the
#      process has outlived every bound it could have been running under by ~2.5x.
#      Derived from the declared budgets, not chosen for feel; if a budget ever
#      exceeds this floor, the floor is wrong and must move with it.
#   4. not a deliberate survivor — daemons, watchers and pane-restorers are DESIGNED
#      to outlive their parent. They are excluded by name, not by heuristic.
#
# On side effects, honestly: a hook killed here may have been mid-write. It was
# already 300 s past a contract its parent gave up on, and the dispatcher recorded
# ETIMEDOUT and moved on long ago — so the inconsistency already exists. Reaping
# does not create it, it stops it growing. That is the true claim, not a stronger one.
# ---------------------------------------------------------------------------

$hookOrphanMinAgeSeconds = 300
$hookOrphanSurvivorRx = 'daemon|sendkeys|restore_panes|watcher|session-watcher|heartbeat-loop'

function Test-IsAbandonedHookOrphan {
  param(
    [bool]$IsOurs,
    [bool]$ParentAlive,
    [string]$CommandLine,
    [double]$AgeSeconds,
    [int]$MinAgeSeconds = 300
  )
  if (-not $IsOurs) { return $false }
  if ($ParentAlive) { return $false }
  if ([string]::IsNullOrWhiteSpace($CommandLine)) { return $false }
  # A deliberate survivor is excluded before anything else is considered.
  if ($CommandLine -match $hookOrphanSurvivorRx) { return $false }
  # Narrow to processes whose output contract is stdout-to-a-parent: hook scripts
  # and the PP tools the hook lanes invoke. A broad `.claude` match would sweep in
  # user-launched work that merely lives under the same root.
  $isHookShaped = ($CommandLine -match '\.claude[\\/](hooks|skills[\\/]claude-power-pack[\\/](hooks|tools|modules[\\/][^\\/]+[\\/]hooks))[\\/]')
  if (-not $isHookShaped) { return $false }
  return ($AgeSeconds -ge $MinAgeSeconds)
}

if ($args -contains '-GhostSelfTest') {
  $gcases = @(
    @{ n = 'ghost: ours, parent dead, never ran, old';     o = $true;  p = $false; k = $true;  c = 0;    a = 3600;  want = $true  },
    @{ n = 'healthy long task: has burned CPU';            o = $true;  p = $false; k = $true;  c = 5587; a = 84000; want = $false },
    @{ n = 'live child: parent still alive';               o = $true;  p = $true;  k = $true;  c = 0;    a = 3600;  want = $false },
    @{ n = 'young child: not scheduled yet';               o = $true;  p = $false; k = $true;  c = 0;    a = 5;     want = $false },
    @{ n = 'not ours: someone else''s idle node';          o = $false; p = $false; k = $true;  c = 0;    a = 3600;  want = $false },
    @{ n = 'cpu UNREADABLE: absent is not zero, refuse';   o = $true;  p = $false; k = $false; c = 0;    a = 3600;  want = $false }
  )

  # Abandoned-hook cases. The FIRST one is the whole point of the rule: it is the
  # process the table above deliberately refuses (burned CPU), and it must be
  # caught here. If these two tables ever agree on a case, one of them is wrong.
  $hookCmd = 'C:\Program Files\nodejs\node.exe C:/Users/User/.claude/hooks/lazarus-livesnap.js'
  $ppCmd   = 'python.exe C:\Users\User\.claude\skills\claude-power-pack\modules\zero-crash\hooks\context-watchdog.py'
  $hcases = @(
    @{ n = 'THE CLASS: ours, parent dead, burned CPU, old'; o = $true;  p = $false; c = $hookCmd;  a = 4000; want = $true  },
    @{ n = 'PP module hook orphan, old';                    o = $true;  p = $false; c = $ppCmd;    a = 900;  want = $true  },
    @{ n = 'parent still alive: it can still read stdout';  o = $true;  p = $true;  c = $hookCmd;  a = 4000; want = $false },
    @{ n = 'young: inside the longest declared budget';     o = $true;  p = $false; c = $hookCmd;  a = 90;   want = $false },
    @{ n = 'not hook-shaped: user work under .claude';      o = $true;  p = $false; c = 'node.exe C:/Users/User/.claude/mybuild.js'; a = 4000; want = $false },
    @{ n = 'deliberate survivor: daemon outlives parent';   o = $true;  p = $false; c = 'node.exe C:/Users/User/.claude/hooks/claude-daemon.js'; a = 9000; want = $false },
    @{ n = 'not ours';                                      o = $false; p = $false; c = $hookCmd;  a = 4000; want = $false },
    @{ n = 'no command line: cannot classify, refuse';      o = $true;  p = $false; c = '';        a = 4000; want = $false }
  )

  $gfails = 0
  foreach ($c in $gcases) {
    $got = Test-IsNeverResumedChild -IsOurs $c.o -ParentAlive $c.p -CpuKnown $c.k -CpuTicks $c.c -AgeSeconds $c.a -MinAgeSeconds $ghostMinAgeSeconds
    if ($got -ne $c.want) { $gfails++; "FAIL $($c.n): got=$got want=$($c.want)" } else { "ok   $($c.n)" }
  }
  foreach ($c in $hcases) {
    $got = Test-IsAbandonedHookOrphan -IsOurs $c.o -ParentAlive $c.p -CommandLine $c.c -AgeSeconds $c.a -MinAgeSeconds $hookOrphanMinAgeSeconds
    if ($got -ne $c.want) { $gfails++; "FAIL hook: $($c.n): got=$got want=$($c.want)" } else { "ok   hook: $($c.n)" }
  }
  # The two rules must DISAGREE on the class this commit exists for. If a change
  # ever makes the CPU rule catch it too, that rule has stopped sparing healthy
  # long-running work, and the regression surfaces here rather than in an incident.
  $ovCpu  = Test-IsNeverResumedChild -IsOurs $true -ParentAlive $false -CpuKnown $true -CpuTicks 5587 -AgeSeconds 4000 -MinAgeSeconds $ghostMinAgeSeconds
  $ovHook = Test-IsAbandonedHookOrphan -IsOurs $true -ParentAlive $false -CommandLine $hookCmd -AgeSeconds 4000 -MinAgeSeconds $hookOrphanMinAgeSeconds
  if ($ovCpu -or -not $ovHook) { $gfails++; "FAIL disjointness: cpu=$ovCpu hook=$ovHook (want cpu=False hook=True)" }
  else { "ok   disjointness: CPU rule spares burned-CPU work; this rule owns it" }
  $gcases = $gcases + $hcases + @(@{ n = 'disjointness' })
  "GHOST_SELFTEST=$($gcases.Count - $gfails)/$($gcases.Count)"
  exit ($(if ($gfails -eq 0) { 0 } else { 1 }))
}

try {
  $gnow = Get-Date
  $ghostKilled = 0
  $ghostCommit = 0
  $ghostSeen = 0
  $ghostHookKilled = 0

  # ONE WMI query for the whole process table — it yields both the node command
  # lines AND the live-PID set the parent check needs. The first version of this
  # scan asked WMI once PER PROCESS for thread times and measured 17,781 ms over
  # only 16 processes (~3 min over the 168 found on this host) against its own
  # 10 s hook budget: it would have been killed on every fire and done nothing at
  # all, forever, silently. That is precisely the defect its sibling detector
  # (hooks/tests/test-stop-chain-budget.js) was written to catch, and it nearly
  # shipped inside the fix for it.
  #
  # Process.TotalProcessorTime answers the same question in 189 ms — 94x cheaper
  # — and was cross-checked against the WMI sum over a live population: 12/12
  # agreement on "is it zero", zero disagreements.
  $gAllProcs = Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, Name, CommandLine
  $gLive = @{}
  foreach ($ap in $gAllProcs) { $gLive[[int]$ap.ProcessId] = $true }

  # Aperture: python.exe added 2026-09-15. The census that forced the abandoned-hook
  # rule found orphaned `python.exe ... tools/audit_cache.py` alongside the node ones,
  # and a scan filtered to node.exe is blind to half its own subject. Enumerating by
  # `Name='node.exe'` ALONE is the same construction error the husk block above
  # documents: the filter, not the predicate, is what made the class invisible.
  $gByPid = @{}
  foreach ($pr in (Get-Process node, python, python3.12 -ErrorAction SilentlyContinue)) { $gByPid[[int]$pr.Id] = $pr }

  foreach ($gp in ($gAllProcs | Where-Object { $_.Name -eq 'node.exe' -or $_.Name -like 'python*.exe' })) {
    $ghostSeen++

    $gcmd = if ($gp.CommandLine) { $gp.CommandLine } else { '' }
    $gIsOurs = $gcmd -match '\.claude[\\/]'
    if (-not $gIsOurs) { continue }

    $gParentAlive = [bool]$gLive[[int]$gp.ParentProcessId]
    if ($gParentAlive) { continue }

    $gproc = $gByPid[[int]$gp.ProcessId]
    if (-not $gproc) { continue }

    # Three states, not two: measured-zero, measured-nonzero, UNREADABLE.
    # 4 of 16 processes could not be read at all on this host, and an
    # unreadable CPU time is not evidence that a process never ran.
    $gCpuKnown = $false
    $gTicks = 0
    try { $gTicks = [int64]$gproc.TotalProcessorTime.Ticks; $gCpuKnown = $true } catch { $gCpuKnown = $false }

    $gAge = 0
    try { if ($gproc.StartTime) { $gAge = ($gnow - $gproc.StartTime).TotalSeconds } } catch { $gAge = 0 }

    # TWO rules, disjoint by construction, each with its own safety argument:
    #   never-resumed  -> burned no CPU, so it has nothing to lose
    #   abandoned-hook -> burned CPU, but its parent is gone, so whatever it
    #                     produces can never be delivered to anybody
    # Either makes a process reapable. The reason is recorded so the log says
    # WHICH rule fired — a rule that silently stops firing is the failure mode
    # this file has already been bitten by twice.
    $gReason = $null
    if (Test-IsNeverResumedChild -IsOurs $gIsOurs -ParentAlive $gParentAlive -CpuKnown $gCpuKnown -CpuTicks $gTicks -AgeSeconds $gAge -MinAgeSeconds $ghostMinAgeSeconds) {
      $gReason = 'never-resumed'
    } elseif (Test-IsAbandonedHookOrphan -IsOurs $gIsOurs -ParentAlive $gParentAlive -CommandLine $gcmd -AgeSeconds $gAge -MinAgeSeconds $hookOrphanMinAgeSeconds) {
      $gReason = 'abandoned-hook'
      $ghostHookKilled++
    }
    if (-not $gReason) { continue }

    $gCommitMB = [math]::Round($gproc.PagedMemorySize64 / 1MB, 1)
    try {
      Stop-Process -Id $gp.ProcessId -Force -ErrorAction Stop
      $ghostKilled++
      # Counted HERE, on the kill, never at the decision above: a Stop-Process that
      # threw is a process still running, and a count built from what we INTENDED
      # would report it as reaped. Report what the authority did, not what we asked.
      if ($gReason -eq 'abandoned-hook') { $ghostHookKilled++ }
      $ghostCommit += $gCommitMB
    } catch {
      Add-Content -Path $log -Value "[$ts] GHOST_KILL_FAIL pid=$($gp.ProcessId) rule=${gReason}: $($_.Exception.Message)"
    }
  }
  if ($ghostKilled -gt 0) {
    # Per-rule counts, not a total. A total cannot distinguish "the new rule is
    # working" from "the old rule is doing all of it and the new one is dead" —
    # and a rule that silently stops firing is how this file lost a class twice.
    $gNeverResumed = $ghostKilled - $ghostHookKilled
    Add-Content -Path $log -Value "[$ts] GHOST_REAPED $ghostKilled |never_resumed=$gNeverResumed |abandoned_hook=$ghostHookKilled |commit_mb=$([math]::Round($ghostCommit)) |scanned=$ghostSeen"
  } else {
    # A floor on the population: a scan that saw nothing at all is not a clean
    # bill, it is a broken enumerator, and the two read identically otherwise.
    Add-Content -Path $log -Value "[$ts] GHOST_CLEAN scanned=$ghostSeen"
  }
} catch {
  Add-Content -Path $log -Value "[$ts] GHOST_SCAN_FAIL: $($_.Exception.Message)"
}


# Patterns that identify long-lived dev orphans we control. KEEP
# this list TIGHT — false positives kill legitimate user processes.
#
# SCOPE NOTE (BL-REAPER-DEV-ONLY-2026-05-23): the previous broad pattern
# `node_modules\next\dist` matched BOTH `next dev` AND `next start`,
# killing legitimate production servers on every SessionStart fire.
# Reaper docstring + intent is "Next.js DEV servers". Tightened to
# only the dev/turbopack code paths. Production `next start` survives.
$patterns = @(
  'next/dist/cli/next-dev',
  'next.*dev.*--port',
  'turbopack-cli',
  '@playwright[\\/]mcp',
  'playwright[\\/]cli\.js',
  '@playwright[\\/]mcp[\\/]cli\.js',
  'corepack.*playwright',
  'corepack.*next',
  'node_modules\\next\\dist\\bin\\next.*\bdev\b',
  'node_modules\\next\\dist\\compiled\\.*turbopack',
  'phx\.server',
  # 2026-05-22 evening extension — bunx-cached Notion-MCP respawns.
  # Scope-tight: only matches the AppData\Local\Temp\bunx-<digits>-@notionhq
  # path that the leak pattern exhibits. A fresh global install of
  # notion-mcp-server (e.g. via npm i -g) would NOT match this regex.
  'bunx-\d+-@notionhq.*notion-mcp-server',
  '\\@notionhq\\notion-mcp-server@latest\\'
)
$rx = ($patterns | ForEach-Object { "($_)" }) -join '|'

$victims = @()
try {
  $procs = Get-CimInstance Win32_Process -Filter "Name='node.exe'"
  foreach ($p in $procs) {
    if ($null -eq $p.CommandLine) { continue }
    if ($p.CommandLine -match $rx) {
      $victims += $p
    }
  }
} catch {
  Add-Content -Path $log -Value "[$ts] ENUMERATE_FAIL: $($_.Exception.Message)"
  return
}

if ($victims.Count -eq 0) {
  Add-Content -Path $log -Value "[$ts] CLEAN no_orphans"
  return
}

$killed = 0
foreach ($v in $victims) {
  try {
    Stop-Process -Id $v.ProcessId -Force -ErrorAction Stop
    $killed++
  } catch {
    # ignore — process may have died between enumerate + stop
  }
}

$freeMB = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024, 0)
Add-Content -Path $log -Value "[$ts] REAPED $killed/$($victims.Count) orphans |free_after=${freeMB}MB"

# Rotate log if larger than 256 KB.
if ((Get-Item $log -ErrorAction SilentlyContinue).Length -gt 262144) {
  $bak = "$log.1"
  if (Test-Path $bak) { Remove-Item $bak -Force }
  Move-Item -Path $log -Destination $bak -Force
}
