<#
.SYNOPSIS
  CPC-OS Crash Restore -- reopen every repo as a Cursor window and restore ALL
  its panes (not just one) in the correct order, each resuming its EXACT session.

.DESCRIPTION
  Source of truth = ~/.claude/state/pane_map.json (built from disk transcripts by
  build_pane_map.ps1: complete, LIVE-flagged, most-recent-first). The legacy
  session_snapshot.json UNDER-records (only the live-registry sids), which made a
  prior version restore ~1 pane per repo. We now drive from the pane_map so EVERY
  RESUMABLE/LIVE pane of a repo is restored.

  Per repo (one Cursor window restores all its terminal tabs):
    * open the window once (`cursor <cwd>`), with a pause between repos so N
      windows do not race Cursor's startup;
    * with -AutoRun, write a .vscode/tasks.json holding ONE folderOpen task PER
      pane (via vscode_autorun.py --no-truncate) so each pane resumes in its own
      dedicated terminal through the kclaude wrapper (Cognitive OS active);
    * print, per repo, every `kclaude --resume <id>` line as the deterministic
      manual fallback.

  Ordering: LIVE panes first, then recent (RESUMABLE), most-recent-first within
  each group. If ~/.claude/state/tab_order.json exists it takes priority (maps a
  cwd to an ordered list of session_ids). Fail-open: a repo that fails to open is
  logged and skipped; the rest still restore.

  Runs from ANY terminal; Claude Code need not be open. All paths are absolute.

.PARAMETER DryRun
  Print the full restore plan (repos, pane counts, order) without opening Cursor
  or writing any tasks.json.

.PARAMETER AutoRun
  Also write per-repo .vscode/tasks.json so Cursor AUTO-RUNS `kclaude --resume`
  per pane on folder open (needs "task.allowAutomaticTasks":"on" in Cursor
  settings to fire without a click). Non-destructive: merges + backs up.

.PARAMETER PaneMapPath
  Override the pane_map.json path (default ~/.claude/state/pane_map.json).

.PARAMETER SnapshotPath
  Legacy session_snapshot.json path. Used only with -FromSnapshot or when the
  pane_map is missing/empty (fallback).

.PARAMETER FromSnapshot
  Force the legacy snapshot source instead of the pane_map.

.PARAMETER OpenDelayMs
  Pause (ms) between opening each repo window (race guard). Default 500.

.PARAMETER LargeRepoPanes / LargeRepoDelayMs
  A repo with more than LargeRepoPanes panes waits LargeRepoDelayMs instead of
  OpenDelayMs before the NEXT open (heavier repos need more settle time).

.NOTES
  ASCII-only by design (PowerShell 5.1 -File mis-parses non-ASCII under the ANSI
  codepage). No em-dashes, no emoji, no box-drawing characters.
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$AutoRun,
    [string]$PaneMapPath  = (Join-Path $HOME '.claude\state\pane_map.json'),
    [string]$SnapshotPath = (Join-Path $HOME '.claude\state\session_snapshot.json'),
    [switch]$FromSnapshot,
    [switch]$LiveOnly,          # restore only panes flagged LIVE ("where they were" at crash)
    [int]$OpenDelayMs = 500,
    [int]$LargeRepoPanes = 5,
    [int]$LargeRepoDelayMs = 1200,
    [switch]$TierOrder,         # open repos by TIER_ORDER priority instead of pane_map recency
    [int]$WaveSize = 5,         # panes launched per wave inside a repo (-AutoRun); 0 = no stagger
    [int]$WaveIntervalS = 8,    # seconds between waves (-AutoRun); 0 = no stagger
    [string[]]$OnlyRepoCwds = @()   # restrict to these repo cwds only (reconciliation: reopen
                                     # ONLY what's confirmed missing, never a repo already open --
                                     # see vault/specs/cursor-window-session-restoration.md Scope 3)
)

# -TierOrder priority. Lower tier opens first. A repo not listed here lands in
# TIER_DEFAULT, after every named tier. Matching is a case-insensitive substring
# test against the repo's cwd, so a nested path (e.g. the KobiiCraft workspace)
# still resolves. Within a tier the pane_map's own order (LIVE first, then
# most-recent-first) is preserved -- the tier is a partition, not a re-sort.
# An ARRAY of tier records, never an [ordered] hashtable keyed by int: in
# PowerShell an integer indexer on an OrderedDictionary selects BY POSITION, not
# by key, so $TIER_ORDER[1] silently returned the SECOND tier. That shifted the
# whole map and dropped claude-power-pack (tier 1) into TIER_DEFAULT -- caught by
# the -DryRun gate, which is exactly what it is for. No indexer, no trap.
$TIER_ORDER = @(
    @{ Tier = 1; Match = @('claude-power-pack') },
    @{ Tier = 2; Match = @('TUA-X', 'InfinityOps') },
    @{ Tier = 3; Match = @('KobiiCraft', 'KobiiSports') },
    @{ Tier = 4; Match = @('Jacobo', 'AKOS', 'GEO-audit') }
)
$TIER_DEFAULT = 99

function Get-RepoTier {
    param([string]$Cwd)
    if (-not $Cwd) { return $TIER_DEFAULT }
    $lc = $Cwd.ToLower()
    foreach ($t in $TIER_ORDER) {
        foreach ($needle in $t.Match) {
            if ($lc.Contains($needle.ToLower())) { return [int]$t.Tier }
        }
    }
    return $TIER_DEFAULT
}

$ErrorActionPreference = 'Stop'

function Resolve-CursorExe {
    $cmd = Get-Command cursor -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $fallback = Join-Path $env:LOCALAPPDATA 'Programs\cursor\resources\app\bin\cursor.cmd'
    if (Test-Path $fallback) { return $fallback }
    return $null
}

function Resolve-PythonExe {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $fallback = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
    if (Test-Path $fallback) { return $fallback }
    return $null
}

# Kclaude wrapper for the printed manual commands (the tasks.json already routes
# through kclaude.bat via vscode_autorun). Prefer the smart bin\kclaude.cmd.
function Resolve-KclaudeLabel { return 'kclaude' }

# ----------------------------------------------------------------------------
# Load panes from the pane_map (complete source). Returns snapshot-schema records
# {cwd, session_id, resume, resume_kind, live, status, lastActivity} ordered
# LIVE-first then most-recent-first within each repo. tab_order.json overrides.
# ----------------------------------------------------------------------------
function Get-PanesFromPaneMap {
    param([string]$MapPath)
    if (-not (Test-Path $MapPath)) { return @() }
    $raw = Get-Content -Raw -Path $MapPath -Encoding UTF8
    $map = $raw | ConvertFrom-Json
    $panes = @($map.panes | Where-Object { $_.status -eq 'RESUMABLE' -or $_.live })
    if (-not $panes -or $panes.Count -eq 0) { return @() }

    # Ordering authority is build_pane_map.ps1: the pane_map is emitted
    # most-recent-first and ALREADY incorporates tab_order.json when the PP
    # Sessions extension has written it (join by 8-hex sid prefix). So we do NOT
    # re-parse tab_order here (its schema is owned upstream) -- we PRESERVE the
    # pane_map's per-repo order and only float LIVE panes to the top as a stable
    # partition (LIVE first, recent after; original order kept within each).
    $records = @()
    $repoSeen = @{}
    foreach ($p in $panes) { if (-not $repoSeen.ContainsKey($p.cwd)) { $repoSeen[$p.cwd] = $true } }
    foreach ($cwd in $repoSeen.Keys) {
        $grp = @($panes | Where-Object { $_.cwd -eq $cwd })
        $ordered = @(@($grp | Where-Object { $_.live }) + @($grp | Where-Object { -not $_.live }))
        foreach ($p in $ordered) {
            $records += [pscustomobject]@{
                cwd          = $p.cwd
                session_id   = $p.sessionId
                resume       = "claude --resume $($p.sessionId)"  # parsed by vscode_autorun; task launches via kclaude
                resume_kind  = 'exact'
                live         = [bool]$p.live
                status       = $p.status
                lastActivity = $p.lastActivity
                topic        = $p.topic   # pane_map label -> vscode_autorun task label -> terminal tab name
                repo         = $p.repo
            }
        }
    }
    return $records
}

# ----------------------------------------------------------------------------
Write-Host 'CPC-OS Crash Restore -- ALL panes per repo'

$panes = @()
$sourceLabel = ''
$snapForAutoRun = $null

if (-not $FromSnapshot) {
    $panes = @(Get-PanesFromPaneMap -MapPath $PaneMapPath)
    if ($panes.Count -gt 0) { $sourceLabel = "pane_map ($PaneMapPath)" }
}
if ($panes.Count -eq 0) {
    # fallback: legacy snapshot
    Write-Host ("Reading snapshot: {0}" -f $SnapshotPath)
    if (-not (Test-Path $SnapshotPath)) {
        Write-Host ''
        Write-Host '[ERROR] No pane_map and no snapshot found. Run build_pane_map.ps1 first.'
        exit 1
    }
    try {
        $panes = @(Get-Content -Raw -Path $SnapshotPath | ConvertFrom-Json)
    } catch {
        Write-Host ('[ERROR] Snapshot is not valid JSON: {0}' -f $_.Exception.Message)
        exit 1
    }
    $sourceLabel = "snapshot ($SnapshotPath)"
}

if (-not $panes -or $panes.Count -eq 0) {
    Write-Host '[INFO] No panes to restore.'
    exit 0
}
Write-Host ("Source: {0}" -f $sourceLabel)

# -LiveOnly: restore only the panes that were OPEN at crash time (LIVE flag).
if ($LiveOnly) {
    $panes = @($panes | Where-Object { $_.live })
    Write-Host ("LiveOnly: {0} LIVE pane(s) selected." -f $panes.Count)
    if ($panes.Count -eq 0) { Write-Host '[INFO] No LIVE panes to restore.'; exit 0 }
}

# Dedup by cwd -> distinct repos, preserving first-seen (already LIVE-first) order.
$repoOrder = @()
$repoPanes = [ordered]@{}
foreach ($p in $panes) {
    $cwd = $p.cwd
    if (-not $cwd) { continue }
    if (-not $repoPanes.Contains($cwd)) { $repoPanes[$cwd] = @(); $repoOrder += $cwd }
    $repoPanes[$cwd] += $p
}
if ($OnlyRepoCwds -and $OnlyRepoCwds.Count -gt 0) {
    $wanted = @($OnlyRepoCwds | ForEach-Object { $_.TrimEnd('\').ToLower() })
    $before = $repoOrder.Count
    $repoOrder = @($repoOrder | Where-Object { $wanted -contains $_.TrimEnd('\').ToLower() })
    Write-Host ("OnlyRepoCwds: restricted {0} -> {1} repo(s)." -f $before, $repoOrder.Count)
    if ($repoOrder.Count -eq 0) { Write-Host '[INFO] No matching repos in OnlyRepoCwds.'; exit 0 }
}
if ($TierOrder) {
    # Stable partition by tier: PowerShell's Sort-Object is stable, so repos
    # inside one tier keep their pane_map order (LIVE-first, most-recent-first).
    $repoOrder = @($repoOrder | Sort-Object { Get-RepoTier $_ })
    Write-Host 'TierOrder: repos open by priority tier (1=claude-power-pack first).'
    foreach ($c in $repoOrder) {
        Write-Host ("    [tier {0}] {1}" -f (Get-RepoTier $c), (Split-Path $c -Leaf))
    }
    Write-Host ''
}

$total = $repoOrder.Count
Write-Host ("Found {0} pane(s) across {1} repo(s)." -f $panes.Count, $total)
Write-Host ''

$cursorExe = Resolve-CursorExe
if (-not $cursorExe -and -not $DryRun) {
    Write-Host '[WARN] cursor CLI not found -- cannot auto-open windows.'
    Write-Host '       Resume commands below still let you restore manually.'
    Write-Host ''
}

# -AutoRun: write per-repo tasks.json (one task PER pane, kclaude) BEFORE opening.
# Non-destructive; --no-truncate so ALL panes become tasks (no tab-count cap).
if ($AutoRun) {
    $pythonExe = Resolve-PythonExe
    if (-not $pythonExe) {
        Write-Host '[WARN] python not found -- cannot write auto-run tasks.json; manual fallback below.'
        Write-Host ''
        $AutoRun = $false
    } else {
        # Write the pane_map-derived records to a temp snapshot for vscode_autorun.
        $snapForAutoRun = Join-Path $env:TEMP ("cpc_restore_autorun_{0}.json" -f $PID)
        $arr = @($panes | ForEach-Object { [ordered]@{ cwd = $_.cwd; session_id = $_.session_id; resume = $_.resume; resume_kind = $_.resume_kind; topic = $_.topic; repo = $_.repo } })
        $utf8 = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($snapForAutoRun, ($arr | ConvertTo-Json -Depth 5), $utf8)

        $autorunScript = Join-Path $PSScriptRoot '..\modules\cpc_os\vscode_autorun.py'
        Write-Host 'Auto-run: writing .vscode/tasks.json per repo (ALL panes, kclaude --resume on folder open)...'
        $genArgs = @($autorunScript, '--snapshot', $snapForAutoRun, '--no-truncate',
                     '--wave-size', $WaveSize, '--wave-interval', $WaveIntervalS)
        if ($DryRun) { $genArgs += '--dry-run' }
        Write-Host ("        (wave stagger: {0} pane(s) every {1}s within each repo)" -f $WaveSize, $WaveIntervalS)
        try { & $pythonExe @genArgs } catch { Write-Host ("        [WARN] tasks.json generation failed: {0}" -f $_.Exception.Message) }
        Write-Host ''
    }
}

Write-Host ("Restoring {0} repo(s)..." -f $total)
$i = 0
foreach ($cwd in $repoOrder) {
    $i++
    $name = Split-Path $cwd -Leaf
    $grp = @($repoPanes[$cwd])
    if ($DryRun) {
        Write-Host ("[{0}/{1}] {2} -> [dry-run] would open ({3} pane(s)):" -f $i, $total, $name, $grp.Count)
        foreach ($p in $grp) {
            $tag = if ($p.live) { 'LIVE  ' } else { 'recent' }
            Write-Host ("        [{0}] {1}" -f $tag, $p.session_id)
        }
    } elseif ($cursorExe) {
        Write-Host ("[{0}/{1}] {2} -> opening Cursor window ({3} pane(s))..." -f $i, $total, $name, $grp.Count)
        try {
            & $cursorExe $cwd | Out-Null
        } catch {
            # fail-open: log and continue with the next repo
            Write-Host ("        [WARN] cursor failed for {0}: {1} -- continuing" -f $name, $_.Exception.Message)
        }
    } else {
        Write-Host ("[{0}/{1}] {2} -> (cursor unavailable; see resume below)" -f $i, $total, $name)
    }
    # pause between repo opens so N windows do not race Cursor startup
    if (-not $DryRun -and $i -lt $total) {
        $delay = if ($grp.Count -gt $LargeRepoPanes) { $LargeRepoDelayMs } else { $OpenDelayMs }
        Start-Sleep -Milliseconds $delay
    }
}

Write-Host ''
if ($AutoRun) {
    Write-Host 'Auto-run armed (one dedicated terminal per pane). If Cursor does not'
    Write-Host 'auto-start them, set "task.allowAutomaticTasks":"on" or paste the lines below:'
} else {
    Write-Host 'Per-pane resume (paste into each restored terminal), LIVE first:'
}
Write-Host ''
$kc = Resolve-KclaudeLabel
foreach ($cwd in $repoOrder) {
    $name = Split-Path $cwd -Leaf
    $grp = @($repoPanes[$cwd])
    $liveN = @($grp | Where-Object { $_.live }).Count
    Write-Host ("  {0}  ({1} pane(s), {2} LIVE)  {3}" -f $name, $grp.Count, $liveN, $cwd)
    $seen = @{}
    foreach ($p in $grp) {
        if ($seen.ContainsKey($p.session_id)) { continue }
        $seen[$p.session_id] = $true
        $tag = if ($p.live) { 'LIVE  ' } else { 'recent' }
        Write-Host ("    [{0}] {1} --resume {2}" -f $tag, $kc, $p.session_id)
    }
    Write-Host ''
}

if ($snapForAutoRun -and (Test-Path $snapForAutoRun) -and -not $DryRun) {
    Remove-Item $snapForAutoRun -ErrorAction SilentlyContinue
}

Write-Host '[OK] Done.'
exit 0
