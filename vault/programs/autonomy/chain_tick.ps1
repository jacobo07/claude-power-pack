# Chain tick for programme autonomy-convergence (Task PP-AutonomyChain-Tick, every 10 min). ASCII only.
# Tool is the LIVE gsdx_chain.py (landed by S1). Kill: CPP_GSDX_CHAIN=off.
$env:PYTHONIOENCODING = 'utf-8'
$py    = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$live  = 'C:\Users\User\.claude\skills\claude-power-pack\tools\chain_registry.py'
$wtool = 'C:\Users\User\Apps\pp-ucda-wt\tools\chain_registry.py'
$tool  = if (Test-Path $wtool) { $wtool } elseif (Test-Path $live) { $live } else { $wtool }
$reg   = Join-Path $PSScriptRoot '..\chains.json'   # registry: a new programme = one entry, no new task
$log   = Join-Path $env:USERPROFILE '.claude\state\autonomy-chain-tick.log'
$out   = & $py $tool tick --registry $reg 2>&1 | Out-String
Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' rc=' + $LASTEXITCODE + ' ' + $out.Trim()) -Encoding ASCII

