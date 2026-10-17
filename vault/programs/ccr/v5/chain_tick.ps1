# Chain tick for programme ccr v5 Envelopes 0-3 (Task PP-CcrChain-Tick, every 10 min). ASCII only.
# Kill: CPP_GSDX_CHAIN=off, or Disable-ScheduledTask PP-CcrChain-Tick.
# Physical admission: no tick (so no new worker) while free RAM < 4 GB.
$env:PYTHONIOENCODING = 'utf-8'
$py    = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$tool  = 'C:\Users\User\.claude\skills\claude-power-pack\tools\gsdx_chain.py'
$chain = Join-Path $PSScriptRoot 'chain.json'
$log   = Join-Path $env:USERPROFILE '.claude\state\ccr-chain-tick.log'
$freeGb = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)
if ($freeGb -lt 4) { Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' ram_hold free_gb=' + $freeGb) -Encoding ASCII; exit 0 }
$out   = & $py $tool tick --chain $chain 2>&1 | Out-String
Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' rc=' + $LASTEXITCODE + ' free_gb=' + $freeGb + ' ' + $out.Trim()) -Encoding ASCII