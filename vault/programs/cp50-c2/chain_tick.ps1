# Chain tick for programme cp50-c2 (Task PP-Cp50ChainTick, every 10 min). ASCII only.
# Tool is the LIVE gsdx_chain.py. Kill: CPP_GSDX_CHAIN=off, or Disable-ScheduledTask PP-Cp50ChainTick.
$env:PYTHONIOENCODING = 'utf-8'
$py    = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$tool  = 'C:\Users\User\.claude\skills\claude-power-pack\tools\gsdx_chain.py'
$chain = Join-Path $PSScriptRoot 'chain.json'
$log   = Join-Path $env:USERPROFILE '.claude\state\cp50-chain-tick.log'
$out   = & $py $tool tick --chain $chain 2>&1 | Out-String
Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' rc=' + $LASTEXITCODE + ' ' + $out.Trim()) -Encoding ASCII

