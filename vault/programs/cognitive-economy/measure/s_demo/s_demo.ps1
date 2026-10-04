$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
$wt = 'C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\cognitive-economy'
$base = 'C:\Users\User\.claude\jobs\f12cbb46\tmp\s_demo'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$intents = [ordered]@{
    'port'          = "Port Angry Birds Star Wars II from the Android APK to the Nintendo Wii: extract the asset corpus, reimplement the runtime natively, and ship a boot.dol that runs on real hardware."
    'faithful-port' = "Port Angry Birds Star Wars II from the Android APK to the Nintendo Wii as a faithful port: gameplay must be identical to the original, which still runs on the phone."
    'cosmetic'      = "Fix a typo in the README heading."
}
foreach ($case in $intents.Keys) {
    $root = Join-Path $base $case
    New-Item -ItemType Directory -Force $root | Out-Null
    Copy-Item 'C:\Users\User\Desktop\Cursor Projects\Wii Projects\ABSW2-Wii\README.md' (Join-Path $root 'README.md') -Force
    [IO.File]::WriteAllText((Join-Path $root 'INTENT.txt'), $intents[$case], $utf8)
    "=== case: $case ==="
    "intent: $($intents[$case])"
    & $py (Join-Path $wt 'tools\gsd_x_mission.py') derive $root
    "rc=$LASTEXITCODE"
}
