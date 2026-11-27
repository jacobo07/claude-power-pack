# One-shot A3/A4 re-measure for SPEC-HOOK-CHAIN-THREAD-RUNNER (scheduled task PP-PerfRemeasure-20261203).
# Read-only over the transcripts. Writes AFTER_* next to BEFORE_* in this folder and a one-line DONE marker.
$ErrorActionPreference = 'Continue'
$d    = Split-Path -Parent $MyInvocation.MyCommand.Path
$wt   = 'C:\Users\User\Apps\pp-perf-wt'
$py   = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$root = Join-Path $env:USERPROFILE '.claude\projects'
$since = '2026-11-26T13:52:00Z'                       # first minute after the live deploy (13:51:57Z)
$until = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
& $py (Join-Path $d 'turn_decomp2.py') $root 15 400 $since $until *> (Join-Path $d 'AFTER_turn_decomp.txt')
& $py (Join-Path $d 'hook_cost.py')    $root 15 400 $since $until *> (Join-Path $d 'AFTER_hook_cost.txt')
Push-Location $wt
# LP-05 re-run, same flags as the 2026-11-24 baseline record (LP-05-laptop-distribution.txt)
& $py tools\construction_metrology_report.py --root $root --max-files 200 --max-bytes 200000000 --seed 0 *> (Join-Path $d 'AFTER_LP05.txt')
Pop-Location
Add-Content -Path (Join-Path $d 'DONE.txt') -Value ("ran {0} window {1} -> {2}" -f (Get-Date -Format s), $since, $until)
# Owner reminder (backlog D46): a Windows toast once the AFTER files exist
& (Join-Path $d 'notify.ps1') 'Re-medida de velocidad lista' 'Pídele a Claude la comparación antes/después (backlog D46).'
