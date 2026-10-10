# The ONE chain tick (Task PP-ChainRegistry-Tick, every 10 min) replacing PP-GsdxChain-Tick, PP-DglChain-Tick and
# PP-AutonomyChain-Tick. ASCII only (PS 5.1 -File). Rows go to ~/.claude/state/chain-registry.jsonl (written by the tool).
# Kill switch: CPP_GSDX_CHAIN=off. Registering the task is an Owner/landing step (see WU-S3-receipt).
$ErrorActionPreference = 'Continue'
$env:PYTHONIOENCODING = 'utf-8'
$py   = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$tool = Join-Path $PSScriptRoot 'chain_registry.py'
$log  = Join-Path $env:USERPROFILE '.claude\state\chain-registry-tick.log'
$err  = Join-Path $env:TEMP 'chain-registry-tick.err'
$out  = Join-Path $env:TEMP 'chain-registry-tick.out'
$p = Start-Process -FilePath $py -ArgumentList "`"$tool`"", 'tick' -WorkingDirectory (Split-Path $PSScriptRoot) -NoNewWindow -Wait -PassThru -RedirectStandardError $err -RedirectStandardOutput $out
$tail = ''
if (Test-Path $err) { $tail = (Get-Content $err -Tail 3) -join ' | ' }
Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' rc=' + $p.ExitCode + ' ' + $tail) -Encoding ASCII
