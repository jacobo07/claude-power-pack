# lifecycle_install_apply.ps1 -- apply a staged lifecycle install patch to the LIVE checkout by index.
# Deterministic closeout for plan v3 S1 (Owner "A" 2026-10-09). ASCII only (PS 5.1 -File).
# Preserves foreign uncommitted edits in the live working tree: they are saved as a patch, the
# install is committed from the index, and the foreign edits are re-applied on top. Any failure
# before the commit leaves live untouched; a red suite after the commit reverts it.
param(
  [Parameter(Mandatory=$true)][string]$Patch,
  [Parameter(Mandatory=$true)][string]$Sha256,
  [Parameter(Mandatory=$true)][string]$MsgFile,
  [Parameter(Mandatory=$true)][string]$LogDir,
  [string]$Live = 'C:\Users\User\.claude\skills\claude-power-pack',
  [switch]$DryRun
)
# Continue, not Stop: PS 5.1 turns any native stderr line (git checkout prints "Updated N paths") into a
# terminating error under Stop, which would abort AFTER the commit. Failures are checked by exit code instead.
$ErrorActionPreference = 'Continue'
$git = 'C:\Program Files\Git\cmd\git.exe'
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
function Say($m) { Write-Output ("[install] " + $m) }
function Git { $out = & $git -C $Live @args 2>&1; if ($LASTEXITCODE -ne 0) { throw ("git " + ($args -join ' ') + " failed: " + ($out -join ' ')) }; $out }

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Patch).Hash
if ($actual -ne $Sha256.ToUpper()) { throw "patch sha256 $actual != expected $Sha256" }
Say "patch sha256 verified"

$staged = & $git -C $Live diff --cached --name-only
if ($staged) { throw ("live index is not empty, refusing: " + ($staged -join ', ')) }

$files = @(& $git -C $Live apply --numstat $Patch | ForEach-Object { ($_ -split "`t")[2] })
Say ("install set: " + ($files -join ', '))
Git apply --check --cached $Patch | Out-Null
Say "patch applies cleanly to live HEAD"

# Save foreign uncommitted edits on the install set, byte for byte.
$foreign = Join-Path $LogDir 'foreign-uncommitted.patch'
& $git -C $Live diff --binary "--output=$foreign" -- $files
if (-not (Test-Path -LiteralPath $foreign)) { New-Item -ItemType File -Path $foreign | Out-Null }
$foreignBytes = (Get-Item -LiteralPath $foreign).Length
$foreignFiles = @(& $git -C $Live diff --name-only -- $files)
$backup = Join-Path $LogDir 'live-working-backup'
New-Item -ItemType Directory -Force -Path $backup | Out-Null
foreach ($f in $files) { $src = Join-Path $Live $f; if (Test-Path -LiteralPath $src) { $dst = Join-Path $backup ($f -replace '[\\/]', '__'); Copy-Item -LiteralPath $src -Destination $dst -Force } }
Say "foreign edits saved ($foreignBytes bytes), working files backed up to $backup"
if ($DryRun) { Say "dry run: stopping before any live mutation"; exit 0 }

$before = (Git rev-parse HEAD) -join ''
Git apply --cached $Patch | Out-Null
Git commit -q -F $MsgFile | Out-Null
$after = (Git rev-parse HEAD) -join ''
Say "committed $after (was $before)"

# Working tree = committed install + foreign edits.
foreach ($f in $files) { Git checkout -- $f | Out-Null }
if ($foreignBytes -gt 0) {
  & $git -C $Live apply --3way $foreign 2>&1 | Out-File -Encoding utf8 (Join-Path $LogDir 'foreign-reapply.log')
  if ($LASTEXITCODE -ne 0) {
    foreach ($f in $foreignFiles) { $b = Join-Path $backup ($f -replace '[\\/]', '__'); if (Test-Path -LiteralPath $b) { Copy-Item -LiteralPath $b -Destination (Join-Path $Live $f) -Force } }
    Say ("FOREIGN REAPPLY FAILED: " + ($foreignFiles -join ', ') + " restored to their pre-install working copy; the rest run the install. See foreign-reapply.log")
    exit 3
  }
  & $git -C $Live reset -q -- $files
  Say "foreign edits re-applied on top"
}

$suites = @('test_process_lifecycle.py','test_halt_continues.py','test_gsd_mission.py','test_gsd_mission_admission.py')
$red = @()
foreach ($s in $suites) {
  $log = Join-Path $LogDir ($s + '.log')
  $p = Start-Process -FilePath $py -ArgumentList (Join-Path $Live ('tools\' + $s)) -WorkingDirectory $Live -NoNewWindow -Wait -PassThru -RedirectStandardOutput $log -RedirectStandardError ($log + '.err')
  $line = (Select-String -LiteralPath $log -Pattern '_PASS=' | Select-Object -Last 1).Line
  Say ("$s rc=" + $p.ExitCode + " " + $line)
  if ($p.ExitCode -ne 0) { $red += $s }
}
$h = @{}; foreach ($f in $files) { $h[$f] = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Live $f)).Hash }
$h | ConvertTo-Json | Set-Content -Encoding ascii (Join-Path $LogDir 'live-sha256.json')
if ($red.Count -gt 0) { Say ("RED: " + ($red -join ', ') + " -- compare with baselines before reverting (LIFE 5/1 and MC 224/225 are pre-existing)"); exit 2 }
Say "GREEN"
exit 0
