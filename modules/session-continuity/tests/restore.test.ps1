# <module>/tests/restore.test.ps1
$ErrorActionPreference = 'Stop'
$tmp = Join-Path ([IO.Path]::GetTempPath()) ("lzres-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $tmp | Out-Null
$reg = Join-Path $tmp 'terminal_registry.json'
@{ version=4; rows=@(@{ slot='slot2'; session_id='SIDX'; cwd='C:/proj/Bar'; project_id='P'; ts='t'; pid=1 }) } |
  ConvertTo-Json -Depth 5 | Set-Content $reg -Encoding UTF8
$out = & "$PSScriptRoot/../restore.ps1" -RegRoot $tmp -Slot 'slot2' -DryRun
if ($out -notmatch 'claude --resume SIDX') { Write-Error "expected resume SIDX, got: $out"; exit 1 }
if ($out -notmatch 'C:/proj/Bar') { Write-Error "expected cwd in cmd"; exit 1 }
$null = & "$PSScriptRoot/../restore.ps1" -RegRoot $tmp -Slot 'slot9' -DryRun
if ($LASTEXITCODE -ne 0) { Write-Error "missing slot must not fail"; exit 1 }
Write-Host 'restore.test OK'
