<#
  build_pane_map.ps1 -- derive the resumable-pane recovery map from disk truth.

  Single source of truth for the PP Sessions extension and for manual recovery.
  Two-source verification per pane: session_snapshot.json (what panes exist) is
  cross-checked against the actual transcript .jsonl on disk (what is resumable).
  Never invents a session id; a sid with no transcript is classified STALE.

  Outputs:
    ~/.claude/state/pane_map.json   (machine-readable, read by the extension)
    ~/.claude/state/pane_map.md     (human-readable recovery map)

  Usage: powershell -ExecutionPolicy Bypass -File tools/build_pane_map.ps1
#>
[CmdletBinding()]
param(
  [string]$StateDir = (Join-Path $env:USERPROFILE ".claude\state"),
  [string]$ProjBase = (Join-Path $env:USERPROFILE ".claude\projects")
)
$ErrorActionPreference = "Stop"
$snapPath = Join-Path $StateDir "session_snapshot.json"
if (-not (Test-Path $snapPath)) { Write-Error "snapshot not found: $snapPath"; exit 1 }
$snap = Get-Content $snapPath -Raw -Encoding UTF8 | ConvertFrom-Json
$nowUtc = Get-Date

function Get-Topic($jsonl) {
  if (-not (Test-Path $jsonl)) { return "" }
  $lines = [System.IO.File]::ReadAllLines($jsonl, [System.Text.Encoding]::UTF8)
  $label = ""
  foreach ($ln in $lines) { try { $o = $ln | ConvertFrom-Json -EA Stop } catch { continue }
    if ($o.type -eq 'summary' -and $o.summary) { $label = $o.summary; break } }
  if (-not $label) {
    foreach ($ln in $lines) { try { $o = $ln | ConvertFrom-Json -EA Stop } catch { continue }
      if ($o.type -eq 'user' -and $o.message.role -eq 'user') {
        $c = $o.message.content
        if ($c -is [string]) { $t = $c } elseif ($c) { $t = ($c | Where-Object { $_.type -eq 'text' } | Select-Object -First 1).text }
        if ($t) { $t = ($t -replace '<[^>]+>', ' '); $label = ($t -replace '[^\x20-\x7E]', ' ' -replace '\s+', ' ').Trim(); if ($label.Length -gt 4) { break } } } }
  }
  if ($label.Length -gt 90) { $label = $label.Substring(0, 90) + '...' }
  return $label
}

$seen = @{}; $items = @()
foreach ($p in ($snap | Sort-Object pane)) {
  if (-not $p.session_id) { continue }                 # phantom: null sid, skipped
  if ($seen.ContainsKey($p.session_id)) { continue }    # registry dupes
  $seen[$p.session_id] = $true
  $enc = ($p.cwd -replace '[^a-zA-Z0-9]', '-')
  $jsonl = Join-Path (Join-Path $ProjBase $enc) "$($p.session_id).jsonl"
  $hasJ = Test-Path $jsonl
  $ts = ""
  if ($hasJ) {
    $ll = [System.IO.File]::ReadAllLines($jsonl, [System.Text.Encoding]::UTF8)
    $ts = $ll | ForEach-Object { try { ($_ | ConvertFrom-Json).timestamp } catch {} } | Where-Object { $_ } | Select-Object -Last 1
  }
  $age = if ($ts) { ($nowUtc - [datetime]$ts).TotalHours } else { 9999 }
  $status = if (-not $hasJ) { "STALE" } elseif ($age -gt 48) { "OLD" } else { "RESUMABLE" }
  $resume = if ($hasJ) { "claude --resume $($p.session_id)" } else { "claude" }
  $items += [ordered]@{
    repo = $p.repo; cwd = $p.cwd; sessionId = $p.session_id; topic = (Get-Topic $jsonl)
    lastActivity = $ts; status = $status; resumeCmd = $resume
    confidence = if ($hasJ) { "HIGH" } else { "LOW" }
  }
}

$counts = [ordered]@{
  resumable = ($items | Where-Object { $_.status -eq 'RESUMABLE' }).Count
  old       = ($items | Where-Object { $_.status -eq 'OLD' }).Count
  stale     = ($items | Where-Object { $_.status -eq 'STALE' }).Count
}
$payload = [ordered]@{ generatedAt = $nowUtc.ToString('o'); source = "session_snapshot.json + transcript-on-disk"; counts = $counts; panes = $items }

$utf8 = New-Object System.Text.UTF8Encoding($false)
$jsonOut = Join-Path $StateDir "pane_map.json"
[System.IO.File]::WriteAllText($jsonOut, ($payload | ConvertTo-Json -Depth 6), $utf8)

# Markdown view
$sb = New-Object System.Text.StringBuilder
function W($s) { [void]$sb.AppendLine($s) }
W "# PP PANE MAP -- Recovery Safety Net"
W ("Generated: " + $nowUtc.ToString('yyyy-MM-dd HH:mm') + " local | 2-source verified (snapshot + transcript-on-disk)")
W "If a Cursor reload loses a pane, paste the exact command below into a terminal in the right repo."
W ""
foreach ($grp in @(@('RESUMABLE', 'RESUMABLE -- active'), @('OLD', 'RESUMABLE -- old >48h'), @('STALE', 'STALE -- transcript lost, new chat'))) {
  $list = $items | Where-Object { $_.status -eq $grp[0] }
  W ("## {0} ({1})" -f $grp[1], $list.Count); W ""
  foreach ($it in $list) {
    W ("- **{0}** -- {1}" -f $it.repo, ($it.topic)); W ("  - last: {0} | session: ``{1}``" -f $it.lastActivity, $it.sessionId)
    W ("  - ``cd `"{0}`" ; {1}``" -f $it.cwd, $it.resumeCmd); W ""
  }
}
W "---"
W "RESUMABLE = exact sid + transcript on disk. STALE = sid recorded, transcript gone. Phantom null-sid panes are excluded by construction."
[System.IO.File]::WriteAllText((Join-Path $StateDir "pane_map.md"), $sb.ToString(), $utf8)

Write-Output ("pane_map.json + pane_map.md written | resumable={0} old={1} stale={2}" -f $counts.resumable, $counts.old, $counts.stale)
