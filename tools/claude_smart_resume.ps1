# claude_smart_resume.ps1 — terminal-aware resume wrapper (BL-0044 v0.1, BL-0072 v0.2).
#
# v0.2 4-TIER DISPATCH (Lazarus v2):
#   Tier 1: $env:LAZARUS_TERMINAL_KEY is UUID v4  -> ~/.claude/lazarus/terminal_registry.json
#                                                    (Q&A Q3-b global registry, slot_id-keyed)
#   Tier 2: $env:LAZARUS_TERMINAL_KEY is slotN    -> ~/.claude/lazarus/<proj>/bindings.json
#                                                    (legacy MC-LAZ-G termkey)
#   Tier 3: cwd match                             -> vault/terminal_slots.json (existing BL-0044)
#   Tier 4: no match                              -> claude --continue
#
# LIVE-WINS (Q&A Q4-b): at any tier, if the resolved UUID has a fresh heartbeat
# (<60s) in ANOTHER pane, the current pane defers to the next tier (avoids
# .jsonl write conflict).
#
# Install (add to your PowerShell $PROFILE):
#   . "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\claude_smart_resume.ps1"
#
# CLI:
#   csr                          # smart-resume; aliases also for kclaude.ps1 callers
#   claude-smart-resume
#   csr -DryRun                  # show decision tree without executing claude

$script:CSR_HEARTBEAT_FRESH_S = 60

function Test-CSRHeartbeatFreshElsewhere {
  param([string]$Uuid, [int]$ExcludePid = 0)
  if (-not $Uuid) { return $false }
  $hbRoot = Join-Path $env:USERPROFILE '.claude\lazarus'
  if (-not (Test-Path -LiteralPath $hbRoot)) { return $false }
  foreach ($projDir in (Get-ChildItem -LiteralPath $hbRoot -Directory -ErrorAction SilentlyContinue)) {
    $hb = Join-Path $projDir.FullName "heartbeats\$Uuid.lock"
    if (Test-Path -LiteralPath $hb) {
      try {
        $st = Get-Item -LiteralPath $hb
        $age = ((Get-Date) - $st.LastWriteTime).TotalSeconds
        if ($age -lt $script:CSR_HEARTBEAT_FRESH_S) { return $true }
      } catch { }
    }
  }
  return $false
}

function Get-CSRRegistryEntry {
  param([string]$WorkspacePath, [string]$SlotId)
  $regPath = Join-Path $env:USERPROFILE '.claude\lazarus\terminal_registry.json'
  if (-not (Test-Path -LiteralPath $regPath)) { return $null }
  try {
    $raw = Get-Content -Raw -Encoding UTF8 $regPath
    if ($raw.Length -gt 0 -and [int][char]$raw[0] -eq 0xFEFF) { $raw = $raw.Substring(1) }
    $reg = $raw | ConvertFrom-Json
    if (-not $reg.entries) { return $null }
    foreach ($e in $reg.entries) {
      if ($e.slot_id -eq $SlotId -and $e.workspace_path -eq $WorkspacePath) { return $e }
    }
    # Fallback: slot_id-only match (workspace may have shifted)
    foreach ($e in $reg.entries) { if ($e.slot_id -eq $SlotId) { return $e } }
  } catch { }
  return $null
}

function Get-CSRBindingsEntry {
  param([string]$Cwd, [string]$SlotKey)
  $projectId = ($Cwd -replace '[^a-zA-Z0-9-]', '-')
  $bindings = Join-Path $env:USERPROFILE ".claude\lazarus\$projectId\bindings.json"
  if (-not (Test-Path -LiteralPath $bindings)) { return $null }
  try {
    $raw = Get-Content -Raw -Encoding UTF8 $bindings
    $b = $raw | ConvertFrom-Json
    if ($b.terminal_keys -and $b.terminal_keys.$SlotKey) { return [string]$b.terminal_keys.$SlotKey }
  } catch { }
  return $null
}

function Invoke-ClaudeSmartResume {
  [CmdletBinding()]
  param(
    [switch]$DryRun,
    [string[]]$ExtraArgs
  )

  $cwd = (Get-Location).Path
  $cwdNorm = $cwd -replace '\\', '/' -replace '/+$', ''
  $cwdNorm = [regex]::Replace($cwdNorm, '^([A-Z]):', { param($m) $m.Groups[1].Value.ToLower() + ':' })
  $key = $env:LAZARUS_TERMINAL_KEY
  $uuidRegex = '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
  $slotRegex = '^slot[1-9][0-9]*$'

  $resolved = $null
  $tier = 'none'

  # Tier 1: registry by UUID v4 slot_id (BL-0072) OR slotN (BL-0073)
  # BL-0073 fix: pass $cwdNorm (forward-slashed, lower-cased drive) — must
  # match terminal-slot-recorder.js normalizeCwd() output exactly. Passing raw
  # $cwd ('C:\…' form) silently broke registry lookups (audit gap #9).
  if ($key -and ($key -match $uuidRegex -or $key -match $slotRegex)) {
    $entry = Get-CSRRegistryEntry -WorkspacePath $cwdNorm -SlotId $key
    if ($entry -and $entry.uuid) {
      # BL-0073 fix (audit gap #3 lineage): if Tier-1 resolves a UUID whose
      # .jsonl is missing on disk, fall through instead of passing a ghost
      # UUID to `claude --resume` (which would yield "No conversation found").
      $jsonlPath  = Join-Path $env:USERPROFILE ".claude\projects\$(($cwdNorm -replace '[^a-zA-Z0-9-]','-'))\$($entry.uuid).jsonl"
      $jsonlLive  = "$jsonlPath.live"
      $jsonlExists = (Test-Path -LiteralPath $jsonlPath) -or (Test-Path -LiteralPath $jsonlLive)
      if (-not $jsonlExists) {
        Write-Host "[csr T1] uuid $($entry.uuid) has no .jsonl on disk; falling to T2/T3" -ForegroundColor DarkYellow
      } elseif (Test-CSRHeartbeatFreshElsewhere -Uuid $entry.uuid) {
        Write-Host "[csr T1] uuid $($entry.uuid) live in another pane; falling to T2/T3" -ForegroundColor DarkYellow
      } else {
        $resolved = $entry.uuid
        $tier = 'T1-registry'
      }
    }
  }

  # Tier 2: legacy bindings.json by slotN
  if (-not $resolved -and $key -and $key -match $slotRegex) {
    $sid = Get-CSRBindingsEntry -Cwd $cwd -SlotKey $key
    if ($sid) {
      if (Test-CSRHeartbeatFreshElsewhere -Uuid $sid) {
        Write-Host "[csr T2] slot $key uuid $sid live elsewhere; falling to T3" -ForegroundColor DarkYellow
      } else {
        $resolved = $sid
        $tier = 'T2-bindings'
      }
    }
  }

  # Tier 3: cwd-keyed terminal_slots.json (existing BL-0044)
  if (-not $resolved) {
    $slotsPath = Join-Path $env:USERPROFILE '.claude\skills\claude-power-pack\vault\terminal_slots.json'
    if (Test-Path -LiteralPath $slotsPath) {
      try {
        $raw = Get-Content -Raw -Encoding UTF8 $slotsPath
        if ($raw.Length -gt 0 -and [int][char]$raw[0] -eq 0xFEFF) { $raw = $raw.Substring(1) }
        $data = $raw | ConvertFrom-Json
        if ($data.slots -and $data.slots.PSObject.Properties.Name -contains $cwdNorm) {
          $sid = $data.slots.$cwdNorm.session_id
          if ($sid -and -not (Test-CSRHeartbeatFreshElsewhere -Uuid $sid)) {
            $resolved = $sid
            $tier = 'T3-cwd'
          }
        }
      } catch {
        Write-Warning "[csr] terminal_slots.json unreadable ($_)"
      }
    }
  }

  if ($DryRun) {
    Write-Host "[csr DRY] cwd=$cwdNorm key='$key' tier=$tier resolved=$resolved" -ForegroundColor Magenta
    return
  }

  if ($resolved) {
    Write-Host "[csr $tier] resuming $resolved" -ForegroundColor Cyan
    $kclaude = Join-Path $env:USERPROFILE '.claude\kclaude.ps1'
    if (Test-Path -LiteralPath $kclaude) {
      & $kclaude --resume $resolved @ExtraArgs
    } else {
      & claude --resume $resolved @ExtraArgs
    }
  } else {
    Write-Host "[csr T4] no match (key='$key' cwd=$cwdNorm); falling back to --continue" -ForegroundColor Yellow
    $kclaude = Join-Path $env:USERPROFILE '.claude\kclaude.ps1'
    if (Test-Path -LiteralPath $kclaude) {
      & $kclaude --continue @ExtraArgs
    } else {
      & claude --continue @ExtraArgs
    }
  }
}

Set-Alias -Name claude-smart-resume -Value Invoke-ClaudeSmartResume -Scope Global
Set-Alias -Name csr                 -Value Invoke-ClaudeSmartResume -Scope Global
