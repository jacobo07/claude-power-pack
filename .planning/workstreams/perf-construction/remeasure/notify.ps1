param([string]$Title, [string]$Body)
# Windows toast via WinRT (PS 5.1, no module). Failure is logged, never fatal.
$log = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) 'DONE.txt'
try {
    [void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
    [void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]
    $esc = { param($s) [System.Security.SecurityElement]::Escape($s) }
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml("<toast scenario='reminder'><visual><binding template='ToastGeneric'><text>$(& $esc $Title)</text><text>$(& $esc $Body)</text></binding></visual><actions><action content='OK' arguments='ok' activationType='system'/></actions></toast>")
    $appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show([Windows.UI.Notifications.ToastNotification]::new($xml))
    Add-Content -Path $log -Value ("toast shown {0}" -f (Get-Date -Format s))
} catch {
    Add-Content -Path $log -Value ("toast FAILED {0}: {1}" -f (Get-Date -Format s), $_.Exception.Message)
}
