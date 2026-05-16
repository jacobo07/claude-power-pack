# Lazarus Panic Restore — MC-LAZ-06c
#
# Emergency cleanup if the Shadow-Folder Engine daemon dies (or some
# other process dies) leaving sessions' .jsonl files renamed with the
# .live-shadow-<ownerSid> suffix. Walks ~/.claude/projects/ and renames
# every shadow back to its original path.
#
# Conflict policy: if the original .jsonl already exists at the target
# path (e.g. another owner already restored), the shadow is parked
# under <name>.conflict.<iso-ts>.jsonl rather than overwriting — never
# destroy data, surface for human decision.
#
# Idempotent: safe to re-run. Returns exit 0 on success (including
# "nothing to do"), exit 1 on hard failure (e.g. filesystem error).
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass `
#       -File ~/.claude/skills/claude-power-pack/tools/lazarus-panic-restore.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass `
#       -File ...lazarus-panic-restore.ps1 -ProjectId C--Users-kobig-...
#   powershell -NoProfile -ExecutionPolicy Bypass `
#       -File ...lazarus-panic-restore.ps1 -DryRun
#
# Env: no env vars required. Bypasses the LAZARUS_SHADOW_FOLDER kill-
# switch on purpose — panic-restore must work even if the engine
# itself is disabled, otherwise the user is stuck with renamed files.
#
# This file is intentionally ASCII-only (PS 5.1 reads scripts as ANSI
# without a UTF-8 BOM; multi-byte glyphs become parse errors).

[CmdletBinding()]
param(
  [string]$ProjectId = "",
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$ProjectsDir = Join-Path $HOME ".claude\projects"
if (-not (Test-Path -LiteralPath $ProjectsDir)) {
  Write-Output "[panic-restore] no projects dir at $ProjectsDir; nothing to do"
  exit 0
}

# Suffix the engine writes: <sid>.jsonl.live-shadow-<ownerSid>
$SuffixPattern = '\.jsonl\.live-shadow-(.+)$'

function Get-ProjectsToScan {
  if ($ProjectId) {
    $p = Join-Path $ProjectsDir $ProjectId
    if (Test-Path -LiteralPath $p) { return ,(Get-Item -LiteralPath $p) }
    return @()
  }
  return Get-ChildItem -LiteralPath $ProjectsDir -Directory -ErrorAction SilentlyContinue
}

$totalRestored = 0
$totalParked = 0
$totalSkipped = 0

foreach ($proj in Get-ProjectsToScan) {
  $shadows = Get-ChildItem -LiteralPath $proj.FullName -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match $SuffixPattern }
  if (-not $shadows) { continue }

  Write-Output ("[panic-restore] project: {0} ({1} shadow(s))" -f $proj.Name, @($shadows).Count)
  foreach ($f in $shadows) {
    if ($f.Name -notmatch $SuffixPattern) { continue }
    # The leading part before .jsonl.live-shadow- is the original sid
    $cut = $f.Name.IndexOf('.jsonl.live-shadow-')
    if ($cut -lt 0) { $totalSkipped++; continue }
    $sid = $f.Name.Substring(0, $cut)
    $ownerSid = $Matches[1]
    $target = Join-Path $proj.FullName ("{0}.jsonl" -f $sid)

    if (Test-Path -LiteralPath $target) {
      $ts = (Get-Date -AsUTC).ToString("yyyy-MM-ddTHH-mm-ss-fffZ")
      $parked = "{0}.conflict.{1}" -f $target, $ts
      if ($DryRun) {
        Write-Output ("  [DRY] would PARK {0} -> {1}" -f $f.Name, (Split-Path $parked -Leaf))
      } else {
        try {
          Rename-Item -LiteralPath $f.FullName -NewName (Split-Path $parked -Leaf) -Force
          Write-Output ("  PARKED  sid={0} owner={1} -> {2} (target existed)" -f $sid, $ownerSid, (Split-Path $parked -Leaf))
          $totalParked++
        } catch {
          Write-Output ("  ERROR  park failed for {0}: {1}" -f $f.Name, $_.Exception.Message)
          $totalSkipped++
        }
      }
      continue
    }

    if ($DryRun) {
      Write-Output ("  [DRY] would RESTORE {0} -> {1}.jsonl" -f $f.Name, $sid)
    } else {
      try {
        Rename-Item -LiteralPath $f.FullName -NewName ("{0}.jsonl" -f $sid) -Force
        Write-Output ("  RESTORE sid={0} owner={1}" -f $sid, $ownerSid)
        $totalRestored++
      } catch {
        Write-Output ("  ERROR  rename failed for {0}: {1}" -f $f.Name, $_.Exception.Message)
        $totalSkipped++
      }
    }
  }
}

Write-Output ""
if ($DryRun) {
  Write-Output ("[panic-restore] DRY RUN -- no files mutated.")
} else {
  Write-Output ("[panic-restore] restored: {0}  parked: {1}  skipped: {2}" -f $totalRestored, $totalParked, $totalSkipped)
}
exit 0
