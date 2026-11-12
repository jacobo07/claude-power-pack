param([Parameter(Mandatory=$true)][string]$EngineDir, [Parameter(Mandatory=$true)][string]$OutRoot,
      [int]$LockWaitMaxS = 14400, [int]$LockPollS = 30, [int]$MaxLockRetries = 3)
# DRX yield experiment: 3 arms x 3 missions x 3 reps, arm order rotated (Latin square) per mission+rep.
# v2 (2026-11-11): lock-aware. The deep_research lock is shared by every caller of the module; a run that
# meets a held lock never ran, so it is infrastructure loss, not data (PREREGISTRATION rule 6). Before each
# run we wait (bounded) while a LIVE pid holds the lock; a run that still lost the race is set aside under
# a *_lockheld_N name, logged as infra, and retried. The run's result is never seen before that decision.
$ErrorActionPreference = "Continue"
$env:CLAUDEPP_DEEPRESEARCH_MAX_QUERIES = "12"
$env:CLAUDEPP_DEEPRESEARCH_TIMEOUT_S = "2400"
$lockPath = "C:\Users\User\.claude\skills\claude-power-pack\vault\research\.deep-research.lock"
$ctx = "A technical lead deciding engineering and research direction; they act on measured results, named studies and concrete numbers."
$missions = @(
  "What did the Chinchilla paper (Hoffmann et al. 2022) find about the compute-optimal ratio of training tokens to model parameters, and which later results challenged or refined that ratio?",
  "How much does HTTP/3 (QUIC) reduce page load time or latency compared with HTTP/2, especially on lossy mobile networks, according to measured studies?",
  "What is the measured effect of SQLite WAL mode on concurrent read and write throughput compared with the rollback journal mode?"
)
$arms = @(
  @{ name = "A_t120_c25k"; t = "120"; c = "25000" },
  @{ name = "B_t240_c25k"; t = "240"; c = "25000" },
  @{ name = "C_t120_c12k"; t = "120"; c = "12000" }
)
New-Item -ItemType Directory -Force $OutRoot | Out-Null
$prog = Join-Path $OutRoot "progress.txt"
function Log([string]$msg) { "$(Get-Date -Format s) $msg" | Out-File -Append -Encoding utf8 $prog }

function Get-LiveLockHolder {
  if (-not (Test-Path $lockPath)) { return 0 }
  $txt = Get-Content $lockPath -Raw -ErrorAction SilentlyContinue
  if ($txt -match 'pid=(\d+)') {
    $p = [int]$Matches[1]
    if (Get-Process -Id $p -ErrorAction SilentlyContinue) { return $p }
  }
  return 0   # missing pid or dead holder: the engine reclaims an orphan lock itself
}

function Wait-LockFree {
  $t0 = Get-Date
  $holder = Get-LiveLockHolder
  if ($holder -ne 0) { Log "WAIT lock held by live pid=$holder" }
  while ($holder -ne 0) {
    if (((Get-Date) - $t0).TotalSeconds -ge $LockWaitMaxS) { return $false }
    Start-Sleep -Seconds $LockPollS
    $holder = Get-LiveLockHolder
  }
  if (((Get-Date) - $t0).TotalSeconds -ge 1) { Log "LOCK_FREE after $([int]((Get-Date) - $t0).TotalSeconds)s" }
  return $true
}

# v3 (2026-11-11): resume. A cell whose LAST progress line is a real run (rc=0) is done and is not re-run;
# cells lost to infrastructure (engine never started) are run now. The run order is unchanged.
$done = @{}
if (Test-Path $prog) {
  foreach ($line in Get-Content $prog) {
    if ($line -match ' INFRA ') { continue }
    if ($line -match 'arm=(\S+) mission=(\d) rep=(\d) rc=(-?\d+)') { $done["$($Matches[1])|$($Matches[2])|$($Matches[3])"] = ($Matches[4] -eq '0') }
  }
}
for ($rep = 1; $rep -le 3; $rep++) {
  for ($m = 0; $m -lt 3; $m++) {
    for ($k = 0; $k -lt 3; $k++) {
      $arm = $arms[($k + $m + $rep) % 3]
      $env:CLAUDEPP_RESEARCH_LLM_TIMEOUT_S = $arm.t
      $env:CLAUDEPP_RESEARCH_MAX_CHARS = $arm.c
      $dir = Join-Path $OutRoot "$($arm.name)\m$($m + 1)_rep$rep"
      if ($done["$($arm.name)|$($m + 1)|$rep"]) { continue }
      $attempt = 0
      while ($true) {
        if (-not (Wait-LockFree)) {
          Log "ABORT lock held by a live pid for >${LockWaitMaxS}s before arm=$($arm.name) mission=$($m + 1) rep=$rep"
          exit 2
        }
        New-Item -ItemType Directory -Force $dir | Out-Null
        $t0 = Get-Date
        python "$EngineDir\deep_research.py" --prompt $missions[$m] --depth 2 --breadth 3 --operator-context $ctx --out $dir 2>&1 | Out-File -Encoding utf8 "$dir\run.log"
        $rc = $LASTEXITCODE
        $secs = [int]((Get-Date) - $t0).TotalSeconds
        # The engine writes the lock refusal into the report .md ("# deep_research locked"), not run.log
        # (verified on yield_INVALID_lock_2003\A_t120_c25k\m1_rep1). Scan every file in the run dir.
        # Count matches: piped -Quiet emits one False per non-matching file and [bool]@($false,$false) is True.
        $lockHeld = @(Get-ChildItem $dir -File -ErrorAction SilentlyContinue | Select-String -Pattern '^# deep_research locked' -ErrorAction SilentlyContinue).Count -gt 0
        if ($lockHeld) {
          $attempt++
          $aside = "${dir}_lockheld_$attempt"
          Move-Item $dir $aside
          Log "INFRA lock_held arm=$($arm.name) mission=$($m + 1) rep=$rep rc=$rc secs=$secs set_aside=$aside"
          if ($attempt -ge $MaxLockRetries) { Log "ABORT $MaxLockRetries lock-held attempts in a row"; exit 3 }
          continue
        }
        # Infra fast-fail: non-zero exit within 15 s and no report .md = the engine never ran (2026-11-11 21:40:
        # research_quality.py vanished from the frozen copy; 23 cells burned in 7 s). Not data: set aside, stop.
        $hasReport = @(Get-ChildItem $dir -Filter *.md -File -ErrorAction SilentlyContinue).Count -gt 0
        if ($rc -ne 0 -and $secs -lt 15 -and -not $hasReport) {
          Move-Item $dir "${dir}_infra_fastfail"
          Log "INFRA fastfail arm=$($arm.name) mission=$($m + 1) rep=$rep rc=$rc secs=$secs set_aside=${dir}_infra_fastfail"
          Log "ABORT engine failed to start; fix the engine and relaunch (completed cells are skipped)"
          exit 4
        }
        Log "arm=$($arm.name) mission=$($m + 1) rep=$rep rc=$rc secs=$secs"
        break
      }
    }
  }
}
"ALL_DONE" | Out-File -Append -Encoding utf8 $prog
