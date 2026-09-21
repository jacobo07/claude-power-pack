# V-SHARE-* : build_pane_map.ps1 must never deny a writer on a live transcript.
#
# WHY THIS EXISTS. Claude Code's /compact opens the session transcript for
# WRITING. Any reader holding it with FileShare.Read denies that open, and the
# user sees:
#   Error during compaction: EBUSY: resource busy or locked, open '...jsonl'
#
# Measured 2026-09-21 with Restart Manager: build_pane_map.ps1 was the NAMED
# holder denying writers in ~90 consecutive samples across 97 seconds, because
# two of its three transcript readers used [System.IO.File]::ReadLines -- which
# opens FileShare.Read AND is lazy, so a `break`/`return` out of the foreach
# abandoned an open handle until GC.
#
# The green control is not optional. "No denial observed" is what a working
# subject produces AND what a probe that cannot detect denial produces. So this
# first proves the probe CAN see a denial (by deliberately creating one), and
# only then trusts its silence about the subject.
#
#   0  both poles behaved
#   1  the subject denied a writer, or the control failed to detect a denial
#   2  HARNESS-FAILED -- no live transcript to measure against
#
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File tools\test_pane_map_share_mode.ps1

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$script = Join-Path $PSScriptRoot 'build_pane_map.ps1'

$projects = Join-Path $env:USERPROFILE '.claude\projects'
$tr = Get-ChildItem $projects -Recurse -Filter '*.jsonl' -File -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $tr) { Write-Output "HARNESS-FAILED: no transcript under $projects to measure against"; exit 2 }
if (-not (Test-Path $script)) { Write-Output "HARNESS-FAILED: $script not found"; exit 2 }

$f = $tr.FullName
$passes = 0; $fails = 0
function Ok($g, $e)  { $script:passes++; Write-Output "PASS ${g}: $e" }
function Bad($g, $e) { $script:fails++;  Write-Output "FAIL ${g}: $e" }

function Test-WriterDenied($path) {
  try { $s = [System.IO.File]::Open($path, 'Open', 'Write', 'ReadWrite'); $s.Close(); return $false }
  catch { return $true }
}

# ---- GREEN CONTROL: manufacture a denial, require the probe to see it --------
# A separate process holds the file exactly the way the old ReadLines did.
$holder = @"
`$fs = [System.IO.File]::Open('$f', 'Open', 'Read', 'Read')
Start-Sleep -Seconds 4
`$fs.Close()
"@
$hf = Join-Path $env:TEMP ("share-holder-{0}.ps1" -f $PID)
[System.IO.File]::WriteAllText($hf, $holder, (New-Object System.Text.UTF8Encoding($false)))
$hp = Start-Process powershell.exe -PassThru -WindowStyle Hidden `
        -ArgumentList '-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$hf
$seen = $false
for ($i = 0; $i -lt 60; $i++) {
  if (Test-WriterDenied $f) { $seen = $true; break }
  Start-Sleep -Milliseconds 100
}
if ($seen) {
  Ok 'V-SHARE-CONTROL-DETECTS-A-DENIAL' `
     "a FileShare.Read holder on $($tr.Name) is observed as writer-denied, so silence below is a measurement"
} else {
  Bad 'V-SHARE-CONTROL-DETECTS-A-DENIAL' `
      "a deliberate FileShare.Read holder was NOT observed -- the probe cannot see denials and proves nothing about the subject"
}
try { $hp.WaitForExit(8000) | Out-Null } catch {}
try { Remove-Item $hf -Force -Confirm:$false } catch {}

# Let the control's handle clear before measuring the subject.
for ($i = 0; $i -lt 100; $i++) { if (-not (Test-WriterDenied $f)) { break }; Start-Sleep -Milliseconds 100 }
if (Test-WriterDenied $f) {
  Write-Output "HARNESS-FAILED: the file is still writer-denied by something else; the subject cannot be measured cleanly"
  exit 2
}

# ---- SUBJECT: run build_pane_map repeatedly, sample throughout ---------------
$runs = 3
$procs = @()
for ($r = 0; $r -lt $runs; $r++) {
  $procs += Start-Process powershell.exe -PassThru -WindowStyle Hidden `
              -ArgumentList '-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$script
}
$denied = 0; $samples = 0
$deadline = (Get-Date).AddSeconds(45)
while ((Get-Date) -lt $deadline) {
  $alive = @($procs | Where-Object { -not $_.HasExited })
  $samples++
  if (Test-WriterDenied $f) { $denied++ }
  if ($alive.Count -eq 0 -and $samples -gt 20) { break }
  Start-Sleep -Milliseconds 50
}
foreach ($p in $procs) { try { $p.WaitForExit(5000) | Out-Null } catch {} }

if ($samples -lt 20) {
  Write-Output "HARNESS-FAILED: only $samples samples taken; the subject was not observed long enough"
  exit 2
}
if ($denied -eq 0) {
  Ok 'V-SHARE-PANE-MAP-NEVER-DENIES-A-WRITER' `
     "$runs concurrent build_pane_map.ps1 runs over $samples samples denied a writer 0 times on $($tr.Name)"
} else {
  Bad 'V-SHARE-PANE-MAP-NEVER-DENIES-A-WRITER' `
      "build_pane_map.ps1 denied a writer in $denied of $samples samples -- /compact will fail with EBUSY against this"
}

$total = $passes + $fails
Write-Output "SHARE_PASS=$passes/$total  threshold=$total/$total"
if ($fails -eq 0) { exit 0 } else { exit 1 }
