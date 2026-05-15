# <module>/restore.ps1 — auto-run by each slotN Cursor profile.
param(
  [string]$RegRoot = (Join-Path $env:USERPROFILE '.claude\lazarus'),
  [string]$Slot = $env:LAZARUS_TERMINAL_KEY,
  [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$reg = Join-Path $RegRoot 'terminal_registry.json'
if (-not $Slot -or -not (Test-Path $reg)) { Write-Host "[session-continuity] no registry/slot - clean start"; exit 0 }
try { $rows = (Get-Content $reg -Raw | ConvertFrom-Json).rows } catch { Write-Host "[session-continuity] registry unreadable - clean start"; exit 0 }
$row = $rows | Where-Object { $_.slot -eq $Slot } | Select-Object -First 1
if (-not $row -or -not $row.session_id) { Write-Host "[session-continuity] slot $Slot had no chat - clean start"; exit 0 }
$cmd = "cd `"$($row.cwd)`"; claude --resume $($row.session_id)"
if ($DryRun) { Write-Output $cmd; exit 0 }
Write-Host "[session-continuity] reviving $Slot -> $($row.session_id)" -ForegroundColor Yellow
Set-Location $row.cwd
& claude --resume $row.session_id
