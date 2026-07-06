<#
  cursor_apply_perf_flags.ps1 -- keep Cursor's launch shortcuts carrying the
  Chromium "do not throttle background renderers" flag(s), idempotently.

  Why this exists (empirical, 2026-07-06):
    Kickbacks stopped billing impressions for ~28 min (ledger 15:45->16:15)
    while Cursor was focused and actively used. Root cause: the extension-host
    background event-loop was SUSPENDED/throttled (debug.log dead-silent
    15:43->16:11:52, matching the gap edge-to-edge). During the suspension the
    extension's ad-cache refresh + impression accounting halted. The suspected
    host mechanism is Chromium timer/renderer throttling of an occluded ext-host
    renderer -- which --disable-background-timer-throttling (and its two siblings)
    is designed to prevent. argv.json only honours a fixed allowlist that does NOT
    include these switches, so the reliable carrier is the launch shortcut Arguments.

  What it does (idempotent, reversible):
    * Finds every Cursor.lnk (Start Menu, Start Menu subfolder, Taskbar pin,
      Desktop, Public Desktop) that points at Cursor.exe.
    * Backs each up ONCE to <lnk>.bak-preflag before the first change.
    * -Apply (default): ensures each $Flags switch is present in Arguments (adds
      only the missing ones -- running twice changes nothing).
    * -Revert: strips the $Flags switches from Arguments (leaves any others).

  Caveat: the flag only takes effect on a FULL Cursor restart (quit ALL windows,
  then relaunch from the shortcut). A single-instance re-launch onto a running
  Cursor just focuses it WITHOUT the flag. Cursor auto-updates may recreate the
  Start Menu shortcuts -- re-run this script after an update. Verify live with:
    Get-CimInstance Win32_Process -Filter "Name='Cursor.exe'" |
      Where-Object { $_.CommandLine -notmatch '--type=' } |
      Select-Object -ExpandProperty CommandLine

  Usage:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/cursor_apply_perf_flags.ps1
    powershell ... tools/cursor_apply_perf_flags.ps1 -Revert
    powershell ... tools/cursor_apply_perf_flags.ps1 -Flags "--disable-background-timer-throttling","--disable-renderer-backgrounding","--disable-backgrounding-occluded-windows"
#>
[CmdletBinding()]
param(
  [switch]$Revert,
  [string[]]$Flags = @("--disable-background-timer-throttling")
)
$ErrorActionPreference = "Continue"
$sh = New-Object -ComObject WScript.Shell
$roots = @(
  "$env:USERPROFILE\Desktop",
  "$env:PUBLIC\Desktop",
  "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
  "$env:ProgramData\Microsoft\Windows\Start Menu\Programs",
  "$env:APPDATA\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
)
$lnks = @()
foreach ($r in $roots) {
  if (Test-Path $r) {
    Get-ChildItem $r -Recurse -Filter "*.lnk" -ErrorAction SilentlyContinue | ForEach-Object {
      try {
        $t = $sh.CreateShortcut($_.FullName)
        if ($t.TargetPath -match 'Cursor\.exe$') { $lnks += $_.FullName }
      } catch {}
    }
  }
}
$lnks = $lnks | Sort-Object -Unique
if ($lnks.Count -eq 0) { Write-Output "No Cursor.lnk shortcuts found -- nothing to do."; exit 0 }

$changed = 0
foreach ($l in $lnks) {
  try {
    $bak = "$l.bak-preflag"
    if (-not (Test-Path $bak)) { Copy-Item -LiteralPath $l -Destination $bak -Force -ErrorAction SilentlyContinue }
    $s = $sh.CreateShortcut($l)
    # tokenize existing args, drop empties
    $args = @()
    if ($s.Arguments) { $args = $s.Arguments -split '\s+' | Where-Object { $_ -ne '' } }
    $before = ($args -join ' ')
    if ($Revert) {
      $args = $args | Where-Object { $Flags -notcontains $_ }
    } else {
      foreach ($f in $Flags) { if ($args -notcontains $f) { $args += $f } }
    }
    $after = ($args -join ' ')
    if ($after -ne $before) {
      $s.Arguments = $after
      $s.Save()
      $changed++
      Write-Output ("CHANGED: {0}`n         [{1}] -> [{2}]" -f $l, $before, $after)
    } else {
      Write-Output ("OK (no change): {0}  Args=[{1}]" -f (Split-Path $l -Leaf), $after)
    }
  } catch {
    Write-Output ("ERROR on {0}: {1}" -f $l, $_.Exception.Message)
  }
}
$verb = if ($Revert) { "reverted" } else { "applied" }
Write-Output ("DONE: {0} {1} on {2} shortcut(s); {3} changed. Restart Cursor fully for it to take effect." -f $verb, ($Flags -join ','), $lnks.Count, $changed)
exit 0
