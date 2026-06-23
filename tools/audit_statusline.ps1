<#
  audit_statusline.ps1 -- deep, empirical audit of the Claude Code context-bar
  status line under the Kickbacks chain.

  The bar reaches the terminal through a TWO-stage spawn:
     Claude Code  ->  vibe-ads-statusline.mjs  -(spawn shell:true)->  gsd-statusline.js
  with the session JSON forwarded on stdin across both hops. This tool measures
  how reliably the bar survives that chain, isolates gsd alone vs the full chain,
  and runs the static health checks (settings key, chain path, ad freshness).

  Pure measurement -- writes nothing, repairs nothing. Pair with kickbacks_guard.ps1
  for the repair side.

  Usage: powershell -NoProfile -ExecutionPolicy Bypass -File tools/audit_statusline.ps1 [-N 25]
#>
[CmdletBinding()]
param(
  [int]$N = 25,
  [string]$Node = "C:\Program Files\nodejs\node.exe",
  [string]$Gsd  = "C:\Users\User\.claude\hooks\gsd-statusline.js",
  [string]$Mjs  = "C:\Users\User\.vibe-ads\vibe-ads-statusline.mjs",
  [string]$ChainFile = "C:\Users\User\.vibe-ads\cli-prev-statusline.json"
)
$ErrorActionPreference = "Continue"

# --- synthetic session JSON (UTF-8 NO BOM; fed via cmd redirection, never a PS pipe) ---
$session = "audit-" + ([guid]::NewGuid().ToString())
$payload = @{
  model = @{ display_name = "Opus 4.8" }
  workspace = @{ current_dir = "C:\Users\User\.claude\skills\claude-power-pack" }
  session_id = $session
  context_window = @{ remaining_percentage = 62 }
} | ConvertTo-Json -Compress
$inFile = Join-Path $env:TEMP ("statusline_audit_" + $PID + ".json")
[System.IO.File]::WriteAllText($inFile, $payload, (New-Object System.Text.UTF8Encoding($false)))

function Invoke-Chain($exe, $script) {
  # run "<exe> <script> < <inFile>" through cmd so the no-BOM file is the stdin
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  $cmdline = '"{0}" "{1}" < "{2}"' -f $exe, $script, $inFile
  $out = cmd /c $cmdline | Out-String
  $sw.Stop()
  return [pscustomobject]@{ ms = $sw.ElapsedMilliseconds; out = $out }
}
function Has-Bar($s) { return ($s -match '\d+%') }  # the '<n>%' segment only renders on the remaining!=null path == bar present

Write-Output "===== STATIC HEALTH ====="
$set = Get-Content "C:\Users\User\.claude\settings.json" -Raw | ConvertFrom-Json
$slCmd = if ($set.statusLine) { $set.statusLine.command } else { "<none>" }
Write-Output ("settings.statusLine -> " + $slCmd)
Write-Output ("  points at vibe-ads (Kickbacks active) = " + ($slCmd -match 'vibe-ads-statusline'))
if (Test-Path $ChainFile) {
  $cur = Get-Content $ChainFile -Raw
  Write-Output ("chain file gsd=" + ($cur -match 'gsd-statusline') + "  MSYS_path=" + ($cur -match '/c/Program Files'))
} else { Write-Output "chain file ABSENT" }
$adCache = "C:\Users\User\.vibe-ads\cli-ad.json"
if (Test-Path $adCache) {
  try { $ad = Get-Content $adCache -Raw | ConvertFrom-Json; $ageMin = [math]::Round(((Get-Date).ToUniversalTime() - [datetimeoffset]::FromUnixTimeMilliseconds($ad.ts).UtcDateTime).TotalMinutes,1); Write-Output ("ad cache age=" + $ageMin + " min (fresh<10min => ad shows)") } catch { Write-Output "ad cache unparseable" }
} else { Write-Output "ad cache ABSENT (Kickbacks ad will not show)" }

Write-Output ""
Write-Output ("===== gsd ALONE x$N (HUD reliability, no chain) =====")
$g = @(1..$N | ForEach-Object { Invoke-Chain $Node $Gsd })
$gBar = @($g | Where-Object { Has-Bar $_.out }).Count
$gMs = @($g | ForEach-Object { $_.ms } | Sort-Object)
Write-Output ("bar present: $gBar/$N   p50=" + $gMs[[int]($N*0.5)] + "ms  p95=" + $gMs[[int]($N*0.95)] + "ms  max=" + $gMs[-1] + "ms")

Write-Output ""
Write-Output ("===== FULL CHAIN x$N (vibe-ads mjs -> gsd) =====")
$c = @(1..$N | ForEach-Object { Invoke-Chain $Node $Mjs })
$cBar = @($c | Where-Object { Has-Bar $_.out }).Count
$cAd  = @($c | Where-Object { $_.out -match 'ad' }).Count
$cMs = @($c | ForEach-Object { $_.ms } | Sort-Object)
Write-Output ("bar present: $cBar/$N   ad present: $cAd/$N   p50=" + $cMs[[int]($N*0.5)] + "ms  p95=" + $cMs[[int]($N*0.95)] + "ms  max=" + $cMs[-1] + "ms")

Write-Output ""
Write-Output "===== DIAGNOSIS ====="
$gRel = [math]::Round(100*$gBar/$N,1); $cRel = [math]::Round(100*$cBar/$N,1)
Write-Output ("gsd-alone reliability = $gRel%   full-chain reliability = $cRel%")
if ($cBar -lt $N) { Write-Output ("CHAIN DROPS BAR on " + ($N-$cBar) + "/$N runs -> the mjs->gsd hop is the loss surface (Mode B latency/stdin race)") }
if ($gBar -lt $N) { Write-Output ("gsd ALONE drops bar on " + ($N-$gBar) + "/$N -> HUD-internal (stdin timeout / parse), independent of Kickbacks") }
if ($cBar -eq $N -and $gBar -eq $N) { Write-Output "both 100% in this sample -> intermittency is load-dependent (Mode B under system pressure) or upstream-missing-field (Mode C)" }
try { [System.IO.File]::Delete($inFile) } catch {}
