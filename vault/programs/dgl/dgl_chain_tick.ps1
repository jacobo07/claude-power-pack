# One chain tick for programme dgl (Task PP-DglChain-Tick, every 15 min, via hidden_launch.vbs).
# ASCII only (PS 5.1 -File). Decision rows go to ~/.claude/state/gsdx-chain.jsonl (goal=dgl), written by the tool.
# Driver: gsdx_chain.py from Apps\pp-gsdx-factory-2 until W5 installs tools/goal_chain.py live and re-points this task.
# Kill switch: CPP_GSDX_CHAIN=off.
$ErrorActionPreference = 'Continue'
$env:PYTHONIOENCODING = 'utf-8'
$py    = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$tool  = 'C:\Users\User\.claude\skills\claude-power-pack\tools\gsdx_chain.py'
$chain = Join-Path $PSScriptRoot 'chain.json'
$log   = Join-Path $env:USERPROFILE '.claude\state\dgl-chain-tick.log'
$err   = Join-Path $env:TEMP 'dgl-chain-tick.err'
$out   = Join-Path $env:TEMP 'dgl-chain-tick.out'
$p = Start-Process -FilePath $py -ArgumentList "`"$tool`"", 'tick', '--chain', "`"$chain`"" -WorkingDirectory (Split-Path $tool -Parent) -NoNewWindow -Wait -PassThru -RedirectStandardError $err -RedirectStandardOutput $out
$tail = ''
if (Test-Path $err) { $tail = (Get-Content $err -Tail 3) -join ' | ' }
$row = ''
if (Test-Path $out) { $row = (Get-Content $out -Tail 1) }
Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' rc=' + $p.ExitCode + ' ' + $row + ' ' + $tail) -Encoding ASCII
# Bootstrap until W3/W5: a freshly armed unit gets a done_check bound to its receipt, so the supervisor completes it
# from the receipt instead of asking GSD (pp-dgl has no GSD phases -> NO_PHASES -> held for ever; W1b 2026-10-10).
try {
    $r = $row | ConvertFrom-Json
    $mid = $r.armed.mission_id
    if ($mid) {
        $c = Get-Content $chain -Raw | ConvertFrom-Json
        $unit = $c.units | Where-Object { $_.id -eq $r.unit } | Select-Object -First 1
        $att = & $py (Join-Path $PSScriptRoot 'unit_done.py') attach $mid $unit.receipt
        Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' done_check: ' + ($att -join ' ')) -Encoding ASCII
    }
} catch {
    Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' done_check attach failed: ' + $_.Exception.Message) -Encoding ASCII
}
