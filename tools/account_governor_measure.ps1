# Hourly account-governor measurement (CCN-3, Owner Q2 = enforce 85%).
# Run by task PP-AccountGovernor-Measure via wscript + hidden_launch.vbs (no window).
# 1. measures this laptop's API-equivalent spend since the weekly reset;
# 2. pulls GEX44's own measurement (same account) so the lower bound covers both hosts.
# A failed pull leaves the previous gex44.json; a file measured on another window is
# excluded by account_governor.status (stale_hosts), never summed.
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$tools = Split-Path -Parent $MyInvocation.MyCommand.Path
$state = Join-Path $env:USERPROFILE '.claude\state'
$hosts = Join-Path $state 'account-governor-hosts'
$log = Join-Path $state 'account-governor-measure.log'
New-Item -ItemType Directory -Force $hosts | Out-Null
Add-Content -Path $log -Value ("--- " + [DateTime]::UtcNow.ToString('o'))
# Native output goes through Out-String + Add-Content: PS 5.1 `*>>` writes UTF-16 into this ANSI log.
& $py (Join-Path $tools 'account_governor.py') measure --host laptop 2>&1 | Out-String | Add-Content -Path $log
Add-Content -Path $log -Value ("laptop rc=" + $LASTEXITCODE)
$scp = Join-Path $env:SystemRoot 'System32\OpenSSH\scp.exe'
$key = Join-Path $env:USERPROFILE '.ssh\kobicraft_gex44'
$part = Join-Path $hosts 'gex44.json.part'
& $scp -q -i $key -o BatchMode=yes -o ConnectTimeout=20 'gex44:.claude/state/account-governor-hosts/gex44.json' $part 2>&1 | Out-String | Add-Content -Path $log
if ($LASTEXITCODE -eq 0) {
    Move-Item -Force $part (Join-Path $hosts 'gex44.json')
    Add-Content -Path $log -Value 'gex44 pulled'
} else {
    Add-Content -Path $log -Value ("gex44 pull failed rc=" + $LASTEXITCODE)
}
# 3. pushes this laptop's measurement to GEX44, so its arm/topup governor sees the whole account.
# Uploaded as .part and renamed there: a half-written file would read as a missing host, never as a low one.
$ssh = Join-Path $env:SystemRoot 'System32\OpenSSH\ssh.exe'
$remote = '.claude/state/account-governor-hosts/laptop.json'
& $scp -q -i $key -o BatchMode=yes -o ConnectTimeout=20 (Join-Path $hosts 'laptop.json') ("gex44:" + $remote + ".part") 2>&1 | Out-String | Add-Content -Path $log
if ($LASTEXITCODE -eq 0) {
    & $ssh -i $key -o BatchMode=yes -o ConnectTimeout=20 gex44 ("mv -f " + $remote + ".part " + $remote) 2>&1 | Out-String | Add-Content -Path $log
}
Add-Content -Path $log -Value ("laptop push rc=" + $LASTEXITCODE)
