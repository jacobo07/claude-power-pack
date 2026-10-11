# Chain tick for programme autonomy-convergence (Task PP-AutonomyChain-Tick, every 10 min). ASCII only.
# Tool is the LIVE gsdx_chain.py (landed by S1). Kill: CPP_GSDX_CHAIN=off.
$env:PYTHONIOENCODING = 'utf-8'
$py    = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$live  = 'C:\Users\User\.claude\skills\claude-power-pack\tools\gsdx_chain.py'
$wtool = 'C:\Users\User\Apps\pp-ucda-wt\tools\gsdx_chain.py'
$tool  = if (Test-Path $wtool) { $wtool } elseif (Test-Path $live) { $live } else { 'C:\Users\User\Apps\pp-gsdx-factory-2\tools\gsdx_chain.py' }
$chain = Join-Path $PSScriptRoot 'chain.json'
$log   = Join-Path $env:USERPROFILE '.claude\state\autonomy-chain-tick.log'
$out   = & $py $tool tick --chain $chain 2>&1 | Out-String
Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' rc=' + $LASTEXITCODE + ' ' + $out.Trim()) -Encoding ASCII
