<#
.SYNOPSIS
  BL-0057 — Ghost-Input Driver: detects context-watchdog tier-2 advisory
  and (in LIVE mode) sends keystrokes to active window to auto-fire /compact.

.DESCRIPTION
  Watches ~/.claude/skills/claude-power-pack/vault/sleepy/context_snapshots.jsonl
  for new rows where tier=advisory. When detected, extracts the cwd from the
  row, reads the latest progress.md tail to derive a task hint, and sends:

      /compact focus on <task hint>{ENTER}

  via System.Windows.Forms.SendKeys.SendWait to whatever window has FOREGROUND
  focus.

  THIS IS BRITTLE BY DESIGN. Architectural limitations documented in
  vault/audits/lpa_auto_compact_infeasibility.md (BL-0056):
    - SendKeys hits whatever has focus. If you Alt-Tab away mid-detection,
      keystrokes land in the wrong window.
    - Cursor's chat input must have focus when the keystrokes fire.
    - No verification that Cursor consumed the keystrokes — fire-and-forget.
    - Multiple Cursor windows/panes increase misfire risk (Owner has 5+
      concurrent slots per memory reference_cursor_state_vscdb).

  Mode flags:
    -DryRun (default): logs detections to ghost_driver.log, never sends keys.
    -Live:             fires keystrokes for real. USE WITH CAUTION.

.EXAMPLE
  pwsh tools/ghost_input_driver.ps1
  pwsh tools/ghost_input_driver.ps1 -Live
#>
[CmdletBinding()]
param(
  [switch]$Live = $false,
  [int]$PollIntervalMs = 2000,
  [int]$FocusGraceMs = 1500
)

$ErrorActionPreference = 'Stop'
$LedgerPath = Join-Path $env:USERPROFILE '.claude\skills\claude-power-pack\vault\sleepy\context_snapshots.jsonl'
$LogPath = Join-Path $env:USERPROFILE '.claude\skills\claude-power-pack\vault\audits\ghost_driver.log'
$NewLogDir = Split-Path $LogPath -Parent
if (-not (Test-Path $NewLogDir)) { New-Item -ItemType Directory -Force -Path $NewLogDir | Out-Null }

function Write-DriverLog {
  param([string]$Level, [string]$Message)
  $iso = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  $line = "$iso [$Level] $Message"
  Add-Content -Path $LogPath -Value $line -Encoding utf8
  Write-Host $line
}

function Get-TaskHint {
  param([string]$Cwd)
  $candidates = @(
    (Join-Path $Cwd 'vault\progress.md'),
    (Join-Path $Cwd '.claude\progress.md')
  )
  foreach ($p in $candidates) {
    if (Test-Path $p) {
      $tail = Get-Content $p -Tail 6 -Encoding utf8 -ErrorAction SilentlyContinue
      $sessionLine = $tail | Where-Object { $_ -match '^## .* — session ' } | Select-Object -Last 1
      if ($sessionLine) {
        $m = [regex]::Match($sessionLine, 'session (\S+)')
        if ($m.Success) { return "context pressure session $($m.Groups[1].Value)" }
      }
    }
  }
  return 'context pressure resume'
}

function Send-CompactKeystroke {
  param([string]$TaskHint, [bool]$IsLive)
  $cmd = "/compact focus on $TaskHint"
  if (-not $IsLive) {
    Write-DriverLog 'DRYRUN' "would send: '$cmd' + ENTER (skipped, -Live not set)"
    return
  }
  Write-DriverLog 'LIVE' "firing in ${FocusGraceMs}ms: '$cmd'"
  Start-Sleep -Milliseconds $FocusGraceMs
  Add-Type -AssemblyName System.Windows.Forms
  $escaped = $cmd.Replace('+','{+}').Replace('^','{^}').Replace('%','{%}').Replace('~','{~}').Replace('(','{(}').Replace(')','{)}').Replace('{','{{}').Replace('}','{}}')
  [System.Windows.Forms.SendKeys]::SendWait($escaped)
  Start-Sleep -Milliseconds 250
  [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
  Write-DriverLog 'LIVE' "keystrokes dispatched"
}

function Read-NewAdvisoryRows {
  param([long]$LastByteOffset)
  if (-not (Test-Path $LedgerPath)) { return @{ rows = @(); newOffset = 0 } }
  $fs = [System.IO.File]::Open($LedgerPath, 'Open', 'Read', 'ReadWrite')
  try {
    $size = $fs.Length
    if ($size -le $LastByteOffset) { return @{ rows = @(); newOffset = $size } }
    $fs.Seek($LastByteOffset, 'Begin') | Out-Null
    $sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::UTF8)
    $rows = @()
    while (-not $sr.EndOfStream) {
      $line = $sr.ReadLine()
      if (-not $line) { continue }
      try {
        $row = $line | ConvertFrom-Json
        if ($row.tier -eq 'advisory') { $rows += $row }
      } catch { }
    }
    return @{ rows = $rows; newOffset = $size }
  } finally { $fs.Close() }
}

Write-DriverLog 'BOOT' "ghost-driver starting | live=$Live | poll=${PollIntervalMs}ms | ledger=$LedgerPath"
$offset = if (Test-Path $LedgerPath) { (Get-Item $LedgerPath).Length } else { 0 }
Write-DriverLog 'BOOT' "starting at byte offset $offset (only NEW advisories will trigger)"

while ($true) {
  try {
    $result = Read-NewAdvisoryRows -LastByteOffset $offset
    foreach ($row in $result.rows) {
      Write-DriverLog 'DETECT' "tier-2 advisory | session=$($row.session_id) | used=$($row.used_pct)% | cwd=$($row.cwd)"
      $hint = Get-TaskHint -Cwd $row.cwd
      Send-CompactKeystroke -TaskHint $hint -IsLive $Live
    }
    $offset = $result.newOffset
  } catch {
    Write-DriverLog 'ERROR' $_.Exception.Message
  }
  Start-Sleep -Milliseconds $PollIntervalMs
}
