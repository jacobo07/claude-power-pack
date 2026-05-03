# claude_smart_resume.ps1 — terminal-aware resume wrapper (BL-0044 / MC-SYS-70).
#
# Reads vault/terminal_slots.json, finds the session_id last associated with
# the current cwd, and exec's `claude --resume <id>`. Falls back to
# `claude --continue` when no slot match is found.
#
# Install (add to your PowerShell $PROFILE):
#   . "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\claude_smart_resume.ps1"
#
# Then in any terminal:
#   csr                      # smart-resume the session bound to this cwd
#   claude-smart-resume      # full alias

function Invoke-ClaudeSmartResume {
  [CmdletBinding()]
  param([string[]]$ExtraArgs)

  $slotsPath = Join-Path $env:USERPROFILE '.claude\skills\claude-power-pack\vault\terminal_slots.json'
  $cwdNorm = (Get-Location).Path -replace '\\', '/' -replace '/+$', ''
  $cwdNorm = [regex]::Replace($cwdNorm, '^([A-Z]):', { param($m) $m.Groups[1].Value.ToLower() + ':' })

  $sessionId = $null
  if (Test-Path $slotsPath) {
    try {
      $raw = Get-Content -Raw -Encoding UTF8 $slotsPath
      if ($raw.Length -gt 0 -and [int][char]$raw[0] -eq 0xFEFF) { $raw = $raw.Substring(1) }
      $data = $raw | ConvertFrom-Json
      if ($data.slots -and $data.slots.PSObject.Properties.Name -contains $cwdNorm) {
        $sessionId = $data.slots.$cwdNorm.session_id
      }
    } catch {
      Write-Warning "claude-smart-resume: terminal_slots.json unreadable ($_); falling back to --continue"
    }
  }

  if ($sessionId) {
    Write-Host "[csr] resuming bound session $sessionId for cwd=$cwdNorm" -ForegroundColor Cyan
    & claude --resume $sessionId @ExtraArgs
  } else {
    Write-Host "[csr] no slot for cwd=$cwdNorm; falling back to --continue" -ForegroundColor Yellow
    & claude --continue @ExtraArgs
  }
}

Set-Alias -Name claude-smart-resume -Value Invoke-ClaudeSmartResume -Scope Global
Set-Alias -Name csr                 -Value Invoke-ClaudeSmartResume -Scope Global
