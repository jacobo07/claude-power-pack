# Chain tick for programme evc wave 2 (Task PP-EvcChain-Tick, every 10 min). ASCII only.
# Tool is the LIVE gsdx_chain.py. Kill: CPP_GSDX_CHAIN=off, or Disable-ScheduledTask PP-EvcChain-Tick.
$env:PYTHONIOENCODING = 'utf-8'
$py    = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$tool  = 'C:\Users\User\.claude\skills\claude-power-pack\tools\gsdx_chain.py'
$chain = Join-Path $PSScriptRoot 'chain.json'
$log   = Join-Path $env:USERPROFILE '.claude\state\evc-chain-tick.log'
$out   = & $py $tool tick --chain $chain 2>&1 | Out-String
Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' rc=' + $LASTEXITCODE + ' ' + $out.Trim()) -Encoding ASCII
