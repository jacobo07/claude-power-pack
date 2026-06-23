<#
  kickbacks_guard.ps1 -- keep BOTH the Kickbacks ad AND the Claude Code context
  bar alive, self-healing, so neither disconnects unless the Owner does it on
  purpose.

  Why this exists (empirical, 2026-06-23): Kickbacks owns
  ~/.vibe-ads/cli-prev-statusline.json -- the "chain capture" the ad script
  reads to stack the user's own status line (the gsd context-bar HUD) under the
  ad. Kickbacks periodically re-captures/clears that file (install, update,
  restart). Every time it clears it with no valid prior status line, the gsd
  chain -- and the context bar -- vanishes, while the ad keeps showing. Audit
  proved it: full-chain bar reliability was 0/30 with the file absent, 20/20
  once restored. So the bar "sometimes fails" because this Kickbacks-owned file
  keeps disappearing.

  This guard enforces two invariants and is FAIL-OPEN (any error -> exit 0,
  never removes a working chain):
    INV-CHAIN (always repaired -- ~/.vibe-ads, fully in scope):
        cli-prev-statusline.json MUST be { statusLine: { type: command,
        command: '"<node>" "<gsd>"' } } with a cmd.exe-valid Windows path.
        Rewritten whenever absent / MSYS-pathed / not pointing at the HUD.
    INV-SETTINGS (detected always; repaired only with -RepairSettings):
        ~/.claude/settings.json statusLine.command should point at the Kickbacks
        vibe-ads script (so the ad earns). Auto-mutating ~/.claude/settings.json
        from a background timer is risky, so by default we only WARN; pass
        -RepairSettings to restore it (backs up first).

  Run -SelfTest to execute the real chain with synthetic stdin and assert the
  bar renders.

  Usage:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/kickbacks_guard.ps1
    powershell ... tools/kickbacks_guard.ps1 -SelfTest
    powershell ... tools/kickbacks_guard.ps1 -RepairSettings   (Owner-intent)
#>
[CmdletBinding()]
param(
  [switch]$RepairSettings,
  [switch]$SelfTest,
  [string]$Node = "C:\Program Files\nodejs\node.exe",
  [string]$Gsd  = "C:\Users\User\.claude\hooks\gsd-statusline.js",
  [string]$Mjs  = "C:\Users\User\.vibe-ads\vibe-ads-statusline.mjs",
  [string]$ChainFile = "C:\Users\User\.vibe-ads\cli-prev-statusline.json",
  [string]$Settings  = "C:\Users\User\.claude\settings.json",
  [string]$AdCache   = "C:\Users\User\.vibe-ads\cli-ad.json",
  [string]$LogFile   = "C:\Users\User\.claude\state\kickbacks_guard.log"
)
$ErrorActionPreference = "Continue"   # fail-open: a guard must never break a working setup
$utf8 = New-Object System.Text.UTF8Encoding($false)
$healed = @()
$warns  = @()
$stamp  = (Get-Date).ToUniversalTime().ToString('o')

# --- INV-CHAIN: ~/.vibe-ads/cli-prev-statusline.json must point at the gsd HUD ---
try {
  if (Test-Path $Mjs) {                       # only meaningful when Kickbacks is installed
    $needsFix = $true
    if (Test-Path $ChainFile) {
      $cur = Get-Content $ChainFile -Raw -ErrorAction SilentlyContinue
      if ($cur -and ($cur -match 'gsd-statusline') -and ($cur -notmatch '/c/Program Files')) { $needsFix = $false }
    }
    if ($needsFix) {
      $cmd = '"{0}" "{1}"' -f $Node, $Gsd
      $obj = @{ statusLine = @{ type = "command"; command = $cmd } }
      $json = $obj | ConvertTo-Json -Compress -Depth 4
      [System.IO.File]::WriteAllText($ChainFile, $json, $utf8)
      $healed += "chain(restored gsd HUD)"
    }
  } else {
    $warns += "Kickbacks vibe-ads script absent -- nothing to chain"
  }
} catch { $warns += ("chain check error: " + $_.Exception.Message) }

# --- INV-SETTINGS: ~/.claude/settings.json statusLine should be the vibe-ads ad ---
try {
  if (Test-Path $Settings) {
    $o = Get-Content $Settings -Raw | ConvertFrom-Json
    $slCmd = if ($o.statusLine) { [string]$o.statusLine.command } else { "" }
    $kickbacksActive = $slCmd -match 'vibe-ads-statusline'
    if (Test-Path $Mjs) {
      if (-not $kickbacksActive) {
        if ($RepairSettings) {
          # If a real, non-vibe status line is currently set, preserve it as the
          # chain capture so the user's own HUD keeps rendering below the ad.
          if ($slCmd -and ($slCmd -notmatch 'vibe-ads')) {
            $cap = @{ statusLine = @{ type = "command"; command = $slCmd } }
            [System.IO.File]::WriteAllText($ChainFile, ($cap | ConvertTo-Json -Compress -Depth 4), $utf8)
          }
          Copy-Item $Settings ($Settings + ".bak-guard") -Force -ErrorAction SilentlyContinue
          $want = 'node "C:\Users\User\.vibe-ads\vibe-ads-statusline.mjs"'
          if ($o.PSObject.Properties.Name -contains 'statusLine') {
            $o.statusLine = [pscustomobject]@{ type = "command"; command = $want }
          } else {
            $o | Add-Member -NotePropertyName statusLine -NotePropertyValue ([pscustomobject]@{ type = "command"; command = $want })
          }
          [System.IO.File]::WriteAllText($Settings, ($o | ConvertTo-Json -Depth 20), $utf8)
          $healed += "settings(restored Kickbacks statusLine)"
        } else {
          $warns += "settings.statusLine NOT pointing at Kickbacks -- run with -RepairSettings to restore (Owner intent)"
        }
      }
    }
  }
} catch { $warns += ("settings check error: " + $_.Exception.Message) }

# --- INV-AD: report Kickbacks ad freshness (cannot manufacture ads -- detect only) ---
try {
  if (Test-Path $AdCache) {
    $ad = Get-Content $AdCache -Raw | ConvertFrom-Json
    if ($ad.ts) {
      $ageMin = ((Get-Date).ToUniversalTime() - [datetimeoffset]::FromUnixTimeMilliseconds([int64]$ad.ts).UtcDateTime).TotalMinutes
      if ($ageMin -gt 60) { $warns += ("ad cache stale " + [math]::Round($ageMin) + " min -- Kickbacks refresher may be down (ad will stop showing)") }
    }
  }
} catch { $warns += ("ad cache check error: " + $_.Exception.Message) }

# --- optional self-test: run the real chain, assert the bar ---
$selfTestResult = ""
if ($SelfTest) {
  try {
    $session = "guard-selftest-" + ([guid]::NewGuid().ToString())
    $payload = @{ model = @{ display_name = "Opus 4.8" }; workspace = @{ current_dir = "C:\Users\User" }; session_id = $session; context_window = @{ remaining_percentage = 62 } } | ConvertTo-Json -Compress
    $inFile = Join-Path $env:TEMP ("kbguard_selftest_" + $PID + ".json")
    [System.IO.File]::WriteAllText($inFile, $payload, $utf8)
    $cmdline = '"{0}" "{1}" < "{2}"' -f $Node, $Mjs, $inFile
    $out = cmd /c $cmdline | Out-String
    $hasBar = $out -match '\d+%'
    $hasAd  = $out -match 'ad'
    $selfTestResult = "selftest bar=$hasBar ad=$hasAd"
    if (-not $hasBar) { $warns += "SELFTEST: bar did NOT render through the chain" }
    try { [System.IO.File]::Delete($inFile) } catch {}
  } catch { $warns += ("selftest error: " + $_.Exception.Message) }
}

# --- log (append, capped) + report ---
try {
  $line = "$stamp healed=[" + ($healed -join '; ') + "] warns=[" + ($warns -join '; ') + "] $selfTestResult"
  $dir = Split-Path $LogFile -Parent
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  Add-Content -Path $LogFile -Value $line -Encoding UTF8
  $all = Get-Content $LogFile -ErrorAction SilentlyContinue
  if ($all.Count -gt 200) { $all[-200..-1] | Set-Content -Path $LogFile -Encoding UTF8 }
} catch {}

if ($healed.Count) { Write-Output ("HEALED: " + ($healed -join '; ')) } else { Write-Output "OK: invariants already satisfied (no change)" }
foreach ($w in $warns) { Write-Output ("WARN: " + $w) }
if ($selfTestResult) { Write-Output $selfTestResult }
exit 0
