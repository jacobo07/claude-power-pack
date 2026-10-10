# One chain tick for programme gsdx-factory (Task PP-GsdxChain-Tick, every 15 min, via hidden_launch.vbs).
# ASCII only (PS 5.1 -File). The decision row goes to ~/.claude/state/gsdx-chain.jsonl (written by the tool);
# this wrapper records only the exit code and any stderr. Kill switch: CPP_GSDX_CHAIN=off.
$ErrorActionPreference = 'Continue'
$env:PYTHONIOENCODING = 'utf-8'
$py   = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$tool = Join-Path $PSScriptRoot 'gsdx_chain.py'
$log  = Join-Path $env:USERPROFILE '.claude\state\gsdx-chain-tick.log'
$err  = Join-Path $env:TEMP 'gsdx-chain-tick.err'
$p = Start-Process -FilePath $py -ArgumentList "`"$tool`"", 'tick' -WorkingDirectory (Split-Path $PSScriptRoot) -NoNewWindow -Wait -PassThru -RedirectStandardError $err -RedirectStandardOutput (Join-Path $env:TEMP 'gsdx-chain-tick.out')
$tail = ''
if (Test-Path $err) { $tail = (Get-Content $err -Tail 3) -join ' | ' }
Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' rc=' + $p.ExitCode + ' ' + $tail) -Encoding ASCII
