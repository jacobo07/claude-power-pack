# cursor_snapshot_purge_on_close.ps1 -- backlog D42 (Owner 2026-11-16).
# Waits until NO Cursor.exe is running, then deletes Cursor's regenerable git
# snapshot packs (snapshots\codebases + snapshots\stores) and logs the measured
# free-space delta. One-shot: exits after one purge, or after -MaxHours.
# Single instance via a named mutex. Never touches snapshots\state or \roots,
# never touches ~/.claude (session transcripts).
# -Loop: run forever (Scheduled Task at logon), purging once per Cursor close.
# Must NOT be started from a Cursor terminal: Cursor kills its process tree on
# close (observed 2026-11-18, the first watcher died without logging).
# While Cursor is open: a Windows toast when C: free < -WarnGB, once per
# crossing; re-armed when free > -RearmGB (Owner 2026-11-18, option 4).
# -TestToast: show one toast and exit (to verify the notification is visible).
param([int]$PollSeconds = 30, [int]$MaxHours = 168, [switch]$DryRun, [switch]$Loop,
      [double]$WarnGB = 15, [double]$RearmGB = 20, [switch]$TestToast)
if ($Loop) { $MaxHours = 24 * 365 * 10 }

$ErrorActionPreference = 'Stop'
$log  = Join-Path $env:LOCALAPPDATA 'cursor-snapshot-purge.log'
$root = Join-Path $env:APPDATA 'Cursor\snapshots'
function Log($m) { Add-Content -LiteralPath $log -Value ("{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $m) -Encoding ASCII }

function Send-Toast([string]$title, [string]$body) {
    try {
        [void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
        [void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]
        $esc = { param($s) [Security.SecurityElement]::Escape($s) }
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml("<toast scenario='reminder'><visual><binding template='ToastGeneric'><text>$(& $esc $title)</text><text>$(& $esc $body)</text></binding></visual><actions><action content='OK' arguments='ok' activationType='system'/></actions></toast>")
        $appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show([Windows.UI.Notifications.ToastNotification]::new($xml))
        Log "toast shown: $title"
    } catch {
        Log ("TOAST FAILED " + $_.Exception.Message)
    }
}

if ($TestToast) {
    Send-Toast ("Prueba: disco C: {0:N1} GB libres" -f ((Get-PSDrive C).Free / 1GB)) "Si ves esto, el aviso de poco espacio funciona."
    exit 0
}

$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Global\CursorSnapshotPurgeOnClose', [ref]$created)
if (-not $created) { Log "another watcher already running; exit"; exit 0 }

try {
    Log "watcher start pid=$PID dry=$DryRun loop=$Loop warn<$WarnGB rearm>$RearmGB"
    $deadline = (Get-Date).AddHours($MaxHours)
    $warned = $false
    while ((Get-Date) -lt $deadline) {
        if (-not (Get-Process -Name Cursor -ErrorAction SilentlyContinue)) {
            Start-Sleep -Seconds 10   # debounce: a restart briefly shows zero processes
            if (Get-Process -Name Cursor -ErrorAction SilentlyContinue) { continue }
            $t0 = (Get-PSDrive C).Free
            foreach ($sub in 'codebases', 'stores') {
                $p = Join-Path $root $sub
                if (-not (Test-Path -LiteralPath $p)) { Log "absent $p"; continue }
                # re-check right before each effect (destructive-state-authorization)
                if (Get-Process -Name Cursor -ErrorAction SilentlyContinue) { Log "Cursor reappeared; abort before $sub"; break }
                $b = (Get-PSDrive C).Free
                if ($DryRun) { Log "DRYRUN would delete $p"; continue }
                # empty the folder but keep it: codebases carries a deny-write ACL (D42, 2026-11-18)
                # that must survive the purge, or Cursor recreates the folder without it.
                try { Get-ChildItem -LiteralPath $p -Force | Remove-Item -Recurse -Force -Confirm:$false; $st = 'OK' }
                catch { $st = 'PARTIAL: ' + $_.Exception.Message }
                Log ("{0} {1} delta={2:N2} GB" -f $st, $p, (((Get-PSDrive C).Free - $b) / 1GB))
            }
            Log ("purge done total_delta={0:N2} GB free_now={1:N2} GB" -f (((Get-PSDrive C).Free - $t0) / 1GB), ((Get-PSDrive C).Free / 1GB))
            $warned = $false
            if (-not $Loop) { exit 0 }
            # Loop mode: one purge per close event -- wait for Cursor to come back first.
            while (-not (Get-Process -Name Cursor -ErrorAction SilentlyContinue)) { Start-Sleep -Seconds $PollSeconds }
            Log "Cursor reopened; armed for next close"
            continue
        }
        # Low-disk warning while Cursor is open: once per crossing (hysteresis).
        $freeGB = (Get-PSDrive C).Free / 1GB
        if ($freeGB -lt $WarnGB -and -not $warned) {
            $warned = $true
            Log ("LOW DISK {0:N1} GB < {1} GB" -f $freeGB, $WarnGB)
            Send-Toast ("Disco C: casi lleno ({0:N1} GB libres)" -f $freeGB) "Cursor esta llenando sus snapshots. Cierralo 1 minuto y se limpiaran solos."
        } elseif ($warned -and $freeGB -gt $RearmGB) {
            $warned = $false
            Log ("disk recovered {0:N1} GB; warning re-armed" -f $freeGB)
        }
        Start-Sleep -Seconds $PollSeconds
    }
    Log "deadline reached without Cursor closing; exit"
} catch {
    Log ("ERROR " + $_.Exception.Message)
    exit 1
} finally {
    $mutex.ReleaseMutex(); $mutex.Dispose()
}
