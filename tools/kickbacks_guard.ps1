<#
  kickbacks_guard.ps1 -- keep BOTH the Kickbacks ad AND the Claude Code context
  bar alive, AND notify the Owner the instant Kickbacks loses its session, so
  nothing disconnects silently and recovery is one click.

  Why this exists (empirical):
    * Bar loss (2026-06-23): Kickbacks owns ~/.vibe-ads/cli-prev-statusline.json
      (the chain capture its ad script reads to stack the gsd context-bar HUD
      under the ad) and periodically clears it on re-capture -> bar vanishes
      while the ad still shows. Audit: full-chain bar 0/30 with file absent,
      20/20 once restored.
    * Session loss (2026-06-24): the Kickbacks auth token lives in Cursor
      SecretStorage (state.vscdb rows secret://kickbacksai.kickbacks-ai/
      kickbacks.access + .refresh, DPAPI-encrypted). It SURVIVES Reload Window
      and Cursor restart -- /clear cannot touch it. "Sign in" therefore comes
      from SERVER-SIDE token expiry/revocation, which the PP cannot and must
      not auto-fix (re-auth needs the Owner; backing up the token = storing a
      credential on disk = forbidden). The safe mitigation is DETECT + NOTIFY:
      when signed out, Kickbacks stops refreshing ads, so cli-ad.json goes
      stale -- a credential-free signed-out proxy.

  Invariants (FAIL-OPEN -- any error -> exit 0, never breaks a working setup):
    INV-CHAIN   (always repaired, ~/.vibe-ads): chain file points at the gsd HUD
                with a cmd.exe-valid Windows path.
    INV-SETTINGS(detect; repair only with -RepairSettings): ~/.claude/settings.json
                statusLine stays the vibe-ads ad (so the ad earns).
    INV-AUTH    (detect + notify): if ads stop refreshing while Cursor is running
                (signed-out proxy), raise a Windows toast + a durable flag with
                the exact restore step, on state transition, throttled. Clears
                the flag on recovery. Never reads the credential value.
    INV-CANARY  (reap stale lock): delete a leftover ~/.vibe-ads/boot.canary that
                survived a canceled activation (age >= 15s, past Kickbacks' 5s
                settle window) so the next activation does NOT misread it as
                "prior activation didn't complete cleanly" -> skip-patch + bar
                blank. Pre-empts the patch-activation-failed + earnings-bar-hidden
                false positive at its shared root. Never touches Kickbacks code.
    INV-RENDER  (detect + notify) [PRIMARY earning-health signal]: the TRUE billing gate is
                the ad actually RENDERING. Elimination forensic (2026-07-06): a real gap had
                EVERY local signal green AND window-focus 100% green, yet no impressions --
                so billing is neither timer-while-serving nor focus-gated; it needs a render.
                The CLI ad is drawn by the statusline, which Claude Code re-invokes only on
                ACTIVITY, so idle panes (even focused) stop rendering -> ad stops -> billing
                pauses. gsd-statusline.js rewrites %TEMP%/claude-ctx-<sid>.json per render;
                the newest such mtime == the last moment any ad billed. When it is >=
                RenderStaleMinutes old while Cursor runs, advise the Owner to run a prompt.
                PP MUST NEVER fake a render (ad fraud). Fail-open: no bridge -> silence.
    INV-FOCUS   (detect + notify) [secondary]: focus loss is ONE reason renders can stop, but
                the 2026-07-06 gap proved focus is neither necessary nor sufficient (focus was
                green, billing still gapped). Kept as a contributing explainer; INV-RENDER is
                authoritative. Fires when Cursor is unfocused >= FocusLossMinutes while running.
                Fail-open: indeterminate foreground -> silence, never a false alarm.
    INV-AUTHSTREAK (detect + notify): a trailing run of failed auth.refresh (>= AuthFailStreak,
                last outcome still a failure) means the session is about to drop -> ads
                stop -> billing stops. Warn before the gap widens. Dormant when the last
                auth.refresh is ok. A DIFFERENT gap cause than focus; a defense-in-depth net.

  Usage:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/kickbacks_guard.ps1
    powershell ... tools/kickbacks_guard.ps1 -SelfTest
    powershell ... tools/kickbacks_guard.ps1 -RepairSettings          (Owner intent)
    powershell ... tools/kickbacks_guard.ps1 -SimulateSignedOut       (test notify path)
    powershell ... tools/kickbacks_guard.ps1 -SimulateUnfocused       (test focus advisory)
    powershell ... tools/kickbacks_guard.ps1 -SimulateAuthStreak      (test auth-streak advisory)
    powershell ... tools/kickbacks_guard.ps1 -SimulateRenderStale     (test render-stale advisory)
#>
[CmdletBinding()]
param(
  [switch]$RepairSettings,
  [switch]$SelfTest,
  [switch]$SimulateSignedOut,
  [switch]$SimulateVsixBlocked,
  [switch]$SimulateUnfocused,
  [switch]$SimulateAuthStreak,
  [switch]$SimulateRenderStale,
  [int]$AdStaleMinutes = 20,
  [int]$RenotifyMinutes = 30,
  [int]$FocusLossMinutes = 5,
  [int]$FocusRenotifyMinutes = 30,
  [int]$AuthFailStreak = 5,
  [int]$RenderStaleMinutes = 10,
  [string]$Node = "C:\Program Files\nodejs\node.exe",
  [string]$Gsd  = "C:\Users\User\.claude\hooks\gsd-statusline.js",
  [string]$Mjs  = "C:\Users\User\.vibe-ads\vibe-ads-statusline.mjs",
  [string]$ChainFile = "C:\Users\User\.vibe-ads\cli-prev-statusline.json",
  [string]$Settings  = "C:\Users\User\.claude\settings.json",
  [string]$AdCache   = "C:\Users\User\.vibe-ads\cli-ad.json",
  [string]$LogFile   = "C:\Users\User\.claude\state\kickbacks_guard.log",
  [string]$AuthState = "C:\Users\User\.claude\state\kickbacks_auth_state.json",
  [string]$SignInFlag= "C:\Users\User\.claude\state\kickbacks_signin_needed.flag",
  [string]$DebugLog  = "C:\Users\User\.vibe-ads\debug.log",
  [string]$VsixState = "C:\Users\User\.claude\state\kickbacks_vsix_state.json",
  [string]$FocusState= "C:\Users\User\.claude\state\kickbacks_focus_state.json",
  [string]$FocusFlag = "C:\Users\User\.claude\state\kickbacks_focus_lost.flag",
  [string]$AuthStreakState = "C:\Users\User\.claude\state\kickbacks_authstreak_state.json",
  [string]$RenderState = "C:\Users\User\.claude\state\kickbacks_render_state.json",
  [string]$RenderFlag  = "C:\Users\User\.claude\state\kickbacks_render_stale.flag"
)
$ErrorActionPreference = "Continue"   # fail-open: a guard must never break a working setup
$utf8 = New-Object System.Text.UTF8Encoding($false)
$healed = @()
$warns  = @()
$notes  = @()
$stamp  = (Get-Date).ToUniversalTime().ToString('o')

function Show-Toast($title, $msg) {
  try {
    $null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime]
    $null = [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType=WindowsRuntime]
    $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $t = $xml.GetElementsByTagName("text")
    $t.Item(0).AppendChild($xml.CreateTextNode($title)) | Out-Null
    $t.Item(1).AppendChild($xml.CreateTextNode($msg)) | Out-Null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    $appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
    return $true
  } catch { return $false }
}
function Test-CursorRunning { return [bool](Get-Process -Name "Cursor" -ErrorAction SilentlyContinue) }

# Foreground process name via Win32. Returns $null when INDETERMINATE (no
# foreground HWND / unresolvable pid -- e.g. locked screen, session race) so
# INV-FOCUS fails-open to SILENCE and can never raise a false "unfocused" alarm.
function Get-ForegroundProcName {
  try {
    Add-Type -Namespace KBGuard -Name Win -ErrorAction SilentlyContinue -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern System.IntPtr GetForegroundWindow();
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(System.IntPtr hWnd, out uint pid);
'@
    $h = [KBGuard.Win]::GetForegroundWindow()
    if ($h -eq [System.IntPtr]::Zero) { return $null }
    $procId = 0; [void][KBGuard.Win]::GetWindowThreadProcessId($h, [ref]$procId)
    if ($procId -eq 0) { return $null }
    $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if ($null -eq $p) { return $null }
    return $p.ProcessName
  } catch { return $null }
}

# --- INV-CHAIN: ~/.vibe-ads/cli-prev-statusline.json must point at the gsd HUD ---
try {
  if (Test-Path $Mjs) {
    $needsFix = $true
    if (Test-Path $ChainFile) {
      $cur = Get-Content $ChainFile -Raw -ErrorAction SilentlyContinue
      if ($cur -and ($cur -match 'gsd-statusline') -and ($cur -notmatch '/c/Program Files')) { $needsFix = $false }
    }
    if ($needsFix) {
      $cmd = '"{0}" "{1}"' -f $Node, $Gsd
      $obj = @{ statusLine = @{ type = "command"; command = $cmd } }
      [System.IO.File]::WriteAllText($ChainFile, ($obj | ConvertTo-Json -Compress -Depth 4), $utf8)
      $healed += "chain(restored gsd HUD)"
    }
  } else { $warns += "Kickbacks vibe-ads script absent -- nothing to chain" }
} catch { $warns += ("chain check error: " + $_.Exception.Message) }

# --- INV-SETTINGS: ~/.claude/settings.json statusLine should be the vibe-ads ad ---
try {
  if ((Test-Path $Settings) -and (Test-Path $Mjs)) {
    $o = Get-Content $Settings -Raw | ConvertFrom-Json
    $slCmd = if ($o.statusLine) { [string]$o.statusLine.command } else { "" }
    if ($slCmd -notmatch 'vibe-ads-statusline') {
      if ($RepairSettings) {
        if ($slCmd -and ($slCmd -notmatch 'vibe-ads')) {
          $cap = @{ statusLine = @{ type = "command"; command = $slCmd } }
          [System.IO.File]::WriteAllText($ChainFile, ($cap | ConvertTo-Json -Compress -Depth 4), $utf8)
        }
        Copy-Item $Settings ($Settings + ".bak-guard") -Force -ErrorAction SilentlyContinue
        $want = 'node "C:\Users\User\.vibe-ads\vibe-ads-statusline.mjs"'
        if ($o.PSObject.Properties.Name -contains 'statusLine') { $o.statusLine = [pscustomobject]@{ type = "command"; command = $want } }
        else { $o | Add-Member -NotePropertyName statusLine -NotePropertyValue ([pscustomobject]@{ type = "command"; command = $want }) }
        [System.IO.File]::WriteAllText($Settings, ($o | ConvertTo-Json -Depth 20), $utf8)
        $healed += "settings(restored Kickbacks statusLine)"
      } else { $warns += "settings.statusLine NOT pointing at Kickbacks -- run with -RepairSettings (Owner intent)" }
    }
  }
} catch { $warns += ("settings check error: " + $_.Exception.Message) }

# --- INV-AUTH: detect signed-out (ad-refresh stalled while Cursor running) + notify ---
try {
  $cursorUp = Test-CursorRunning
  # earning proxy: cli-ad.json refreshed within AdStaleMinutes
  $earning = $false; $adAge = $null
  if (Test-Path $AdCache) {
    try { $ad = Get-Content $AdCache -Raw | ConvertFrom-Json
          $adAge = ((Get-Date).ToUniversalTime() - [datetimeoffset]::FromUnixTimeMilliseconds([int64]$ad.ts).UtcDateTime).TotalMinutes
          $earning = $adAge -le $AdStaleMinutes } catch {}
  }
  if ($SimulateSignedOut) { $cursorUp = $true; $earning = $false; $adAge = 999 }

  # only judge auth while Cursor is actually running (closed Cursor != signed out)
  if ($cursorUp) {
    $state = if ($earning) { "OK" } else { "SIGNED_OUT" }
  } else {
    $state = "CURSOR_CLOSED"   # indeterminate; do not alarm
  }

  # previous state + last-notify
  $prev = "OK"; $lastNotify = [datetime]"2000-01-01"
  if (Test-Path $AuthState) {
    try { $ps = Get-Content $AuthState -Raw | ConvertFrom-Json
          if ($ps.state) { $prev = $ps.state }
          if ($ps.lastNotify) { $lastNotify = [datetime]$ps.lastNotify } } catch {}
  }

  if ($state -eq "SIGNED_OUT") {
    $minsSince = ((Get-Date) - $lastNotify).TotalMinutes
    $transition = ($prev -ne "SIGNED_OUT")
    if ($transition -or ($minsSince -ge $RenotifyMinutes)) {
      $title = "Kickbacks session lost"
      $body  = "Restore in one click: Ctrl+Shift+P  ->  Kickbacks: Sign in"
      $shown = Show-Toast $title $body
      $flagText = "$stamp  Kickbacks appears SIGNED OUT (ads stopped refreshing; ad age=$adAge min).`r`nRestore: Command Palette (Ctrl+Shift+P) -> 'Kickbacks: Sign in'  (command id kickbacks.signIn).`r`nIf the bar/ad still misbehave after sign-in: 'Kickbacks: Restore Claude Code'."
      [System.IO.File]::WriteAllText($SignInFlag, $flagText, $utf8)
      $lastNotify = Get-Date
      $notes += ("AUTH: signed-out detected -> notified (toast=" + $shown + ", flag written)")
    } else {
      $notes += "AUTH: still signed-out (within renotify throttle)"
    }
  } elseif ($state -eq "OK") {
    if (Test-Path $SignInFlag) { try { [System.IO.File]::Delete($SignInFlag); $notes += "AUTH: recovered -> flag cleared" } catch {} }
  }
  [System.IO.File]::WriteAllText($AuthState, (@{ state = $state; lastNotify = $lastNotify.ToString('o'); adAgeMin = $adAge } | ConvertTo-Json -Compress), $utf8)
} catch { $warns += ("auth check error: " + $_.Exception.Message) }

# --- INV-CANARY: reap a leftover boot.canary that survived a canceled activation ---
# Kickbacks writes ~/.vibe-ads/boot.canary at activation start and self-deletes it
# 5s later via an .unref()'d timer (dist/extension.js bootCanary, SETTLE_MS=5000).
# If Cursor reloads / cancels activation within those 5s, the unref'd timer is
# dropped and the canary survives. The NEXT activation within 90s (CANARY_STALE_MS)
# reads the stale canary as "prior activation didn't complete cleanly" -> calls
# suspendServing() -> servingVerdict()="freeze" -> canPatch()=false (patch skipped,
# warning toast shown) AND the green earnings status-bar item blanks. Reaping a
# canary older than the 5s settle window (it can no longer be a live in-flight
# activation -- real boots settle in <5s per boot.cycle.done timestamps) pre-empts
# that false positive on the next reload. File-only: never touches Kickbacks code.
try {
  $canary = Join-Path (Split-Path $ChainFile -Parent) "boot.canary"
  if (Test-Path $canary) {
    $canaryAge = ((Get-Date).ToUniversalTime() - (Get-Item $canary).LastWriteTimeUtc).TotalSeconds
    if ($canaryAge -ge 15) {
      [System.IO.File]::Delete($canary)
      $healed += ("canary(reaped stale boot.canary age=" + [int]$canaryAge + "s -> next activation patches clean)")
    } else {
      $notes += ("canary present but fresh (age=" + [int]$canaryAge + "s) -- possible in-flight activation, left intact")
    }
  }
} catch { $warns += ("canary check error: " + $_.Exception.Message) }

# --- INV-VSIX: advise (throttled 1x/day) if Kickbacks selfupdate is chronically blocked ---
# Kickbacks logs selfupdate.failed {reason:"vsix-url-blocked", consecutiveFails:N} when it
# cannot fetch the newer VSIX -> the extension stays stuck on an old version. Not an immediate
# earning bug, so advisory only: warn once/day when the most-recent consecutiveFails > 10.
# Fail-open: no log / parse error -> silence.
try {
  $vsixFails = 0
  if ($SimulateVsixBlocked) {
    $vsixFails = 99
  } elseif (Test-Path $DebugLog) {
    $tail = Get-Content $DebugLog -Tail 400 -ErrorAction SilentlyContinue
    for ($i = $tail.Count - 1; $i -ge 0; $i--) {
      $ln = $tail[$i]
      if (($ln -match 'selfupdate\.failed') -and ($ln -match 'vsix-url-blocked')) {
        if ($ln -match '"consecutiveFails":\s*(\d+)') { $vsixFails = [int]$Matches[1] }
        break
      }
    }
  }
  if ($vsixFails -gt 10) {
    $lastVsixNotify = [datetime]"2000-01-01"
    if (Test-Path $VsixState) {
      try { $vx = Get-Content $VsixState -Raw | ConvertFrom-Json
            if ($vx.lastNotify) { $lastVsixNotify = [datetime]$vx.lastNotify } } catch {}
    }
    $hrsSince = ((Get-Date) - $lastVsixNotify).TotalHours
    if ($SimulateVsixBlocked -or ($hrsSince -ge 24)) {
      $warns += ("Kickbacks no puede actualizarse (vsix-url-blocked, " + $vsixFails + " fallos consecutivos). Considerar reinstalar la extension manualmente desde kickbacks.ai")
      if (-not $SimulateVsixBlocked) {
        [System.IO.File]::WriteAllText($VsixState, (@{ lastNotify = (Get-Date).ToString('o'); consecutiveFails = $vsixFails } | ConvertTo-Json -Compress), $utf8)
      }
    } else {
      $notes += ("vsix-blocked present (fails=" + $vsixFails + ") -- within 24h renotify throttle")
    }
  }
} catch { $warns += ("vsix check error: " + $_.Exception.Message) }

# --- INV-RENDER: statusline render staleness = the TRUE earning gate (2026-07-06 v5) ---
# Elimination forensic: during a real billing gap (2026-07-06 15:45+) EVERY local signal
# was green -- auth ok, vsix low, signedIn:true, killed:false, hasAd:true THE WHOLE TIME,
# and window-focus was 100% green on the dashboard. Billing still gapped. Therefore billing
# is NOT timer-based-while-serving and NOT focus-gated -- it requires the ad to actually
# RENDER/DISPLAY. The CLI ad is drawn by the statusline, which Claude Code only re-invokes
# on ACTIVITY (a turn running / spinner ticking); idle panes (even focused) stop rendering
# -> the ad stops displaying -> impressions pause. Proof: gsd-statusline.js rewrites
# %TEMP%/claude-ctx-<sid>.json on every render, and the newest such mtime went sparse at
# EXACTLY 15:45 -- the same instant the dashboard Activity Ledger's last row landed. So the
# newest bridge mtime across live sessions == the last moment any ad could have billed.
# PP must NEVER fake a render to inflate impressions (ad fraud) -- the only honest move is to
# make the earning-pause VISIBLE so the Owner can run a prompt to resume. Fail-open: no bridge
# files / error -> silence. Only UUID-named session bridges count (excludes guard-selftest/test).
try {
  if (Test-CursorRunning) {
    $tmpDir = [System.IO.Path]::GetTempPath()
    $bridges = @(Get-ChildItem $tmpDir -Filter "claude-ctx-*.json" -ErrorAction SilentlyContinue |
                 Where-Object { $_.Name -match '^claude-ctx-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-' })
    if ($bridges.Count -eq 0) {
      $notes += "RENDER: no session bridge files -- indeterminate, skipped"
    } else {
      $newest = $bridges | Sort-Object LastWriteTime -Descending | Select-Object -First 1
      $renderAge = if ($SimulateRenderStale) { 999 } else { ((Get-Date) - $newest.LastWriteTime).TotalMinutes }
      $rLastNotify = [datetime]"2000-01-01"; $rPrevStale = $false
      if (Test-Path $RenderState) {
        try { $rs = Get-Content $RenderState -Raw | ConvertFrom-Json
              if ($rs.lastNotify) { $rLastNotify = [datetime]$rs.lastNotify }
              if ($null -ne $rs.stale) { $rPrevStale = [bool]$rs.stale } } catch {}
      }
      $stale = $renderAge -ge $RenderStaleMinutes
      if ($stale) {
        $minsSince = ((Get-Date) - $rLastNotify).TotalMinutes
        if ((-not $rPrevStale) -or ($minsSince -ge $RenotifyMinutes)) {
          $body = ("Sin render del statusline en {0} min -> Kickbacks no acumula impresiones (Claude Code inactivo, aunque Cursor tenga foco). Ejecuta un prompt para reanudar el billing." -f [int]$renderAge)
          $shown = Show-Toast "Kickbacks no esta cobrando" $body
          [System.IO.File]::WriteAllText($RenderFlag, ("$stamp  " + $body), $utf8)
          $rLastNotify = Get-Date
          $notes += ("RENDER: stale " + [int]$renderAge + "min -> notified (toast=" + $shown + ", flag written)")
        } else { $notes += ("RENDER: still stale (" + [int]$renderAge + "min, within renotify throttle)") }
      } else {
        if (Test-Path $RenderFlag) { try { [System.IO.File]::Delete($RenderFlag); $notes += "RENDER: fresh again -> flag cleared" } catch {} }
        $notes += ("RENDER: fresh (" + [int]$renderAge + "min old) -- ad displaying, billing eligible")
      }
      [System.IO.File]::WriteAllText($RenderState, (@{ renderAgeMin = [math]::Round($renderAge,1); stale = $stale; lastNotify = $rLastNotify.ToString('o'); newest = $newest.Name } | ConvertTo-Json -Compress), $utf8)
    }
  }
} catch { $warns += ("render check error: " + $_.Exception.Message) }

# --- INV-FOCUS: sustained Cursor focus loss (impressions bill ONLY while focused) ---
# ROOT CAUSE (2026-07-06 forensic): billing gaps occurred while the extension was
# 100% healthy locally (auth ok, killed:false, hasAd:true, vsix fails low). The ad
# renderer (vibe-ads-statusline.mjs) is a PURE renderer -- no impression report -- so
# accounting lives entirely in the closed extension + backend, which bills only while
# the Cursor window is FOREGROUND ("100% billed while focused"). PP has no focus
# telemetry, so prior forensics (all local, all green) never saw this. PP CANNOT force
# focus (Host-limited); the only honest mitigation is DETECT + NOTIFY -- turn the
# invisible suppression into a visible advisory. Fail-open: indeterminate foreground or
# any error -> silence, never a false alarm. Anchor is a KNOWN-focused sample, so the
# first unfocused sample cannot fire (no anchor in the past yet).
try {
  if (Test-CursorRunning) {
    $fgName = if ($SimulateUnfocused) { "Brave" } else { Get-ForegroundProcName }
    if ($null -eq $fgName) {
      $notes += "FOCUS: foreground indeterminate -- skipped (no false positive)"
    } else {
      $focused = ($fgName -ieq "Cursor")
      $nowUtc = (Get-Date).ToUniversalTime()
      $lastFocused = $nowUtc; $lastFNotify = [datetime]"2000-01-01"; $prevFocused = $true
      if (Test-Path $FocusState) {
        try { $fs = Get-Content $FocusState -Raw | ConvertFrom-Json
              if ($fs.lastFocusedUtc) { $lastFocused = [datetime]$fs.lastFocusedUtc }
              if ($fs.lastNotify)     { $lastFNotify = [datetime]$fs.lastNotify }
              if ($null -ne $fs.focused) { $prevFocused = [bool]$fs.focused } } catch {}
      }
      if ($focused) {
        $lastFocused = $nowUtc
        if (Test-Path $FocusFlag) { try { [System.IO.File]::Delete($FocusFlag); $notes += "FOCUS: regained -> flag cleared" } catch {} }
        $notes += "FOCUS: Cursor foreground -- billing eligible"
      } else {
        $minsUnfocused = if ($SimulateUnfocused) { 999 } else { ($nowUtc - $lastFocused).TotalMinutes }
        if ($minsUnfocused -ge $FocusLossMinutes) {
          $minsSince = ((Get-Date) - $lastFNotify).TotalMinutes
          if ($prevFocused -or ($minsSince -ge $FocusRenotifyMinutes)) {
            $body = ("Cursor sin foco {0} min (primer plano: {1}) -> Kickbacks no cobra impresiones. Vuelve a Cursor para reanudar el billing." -f [int]$minsUnfocused, $fgName)
            $shown = Show-Toast "Kickbacks no esta cobrando" $body
            [System.IO.File]::WriteAllText($FocusFlag, ("$stamp  " + $body), $utf8)
            $lastFNotify = Get-Date
            $notes += ("FOCUS: unfocused " + [int]$minsUnfocused + "min -> notified (toast=" + $shown + ", flag written)")
          } else { $notes += "FOCUS: still unfocused (within renotify throttle)" }
        } else { $notes += ("FOCUS: unfocused " + [int]$minsUnfocused + "min (< " + $FocusLossMinutes + "min threshold, not yet billing-relevant)") }
      }
      [System.IO.File]::WriteAllText($FocusState, (@{ lastFocusedUtc = $lastFocused.ToString('o'); lastNotify = $lastFNotify.ToString('o'); focused = $focused; fg = $fgName } | ConvertTo-Json -Compress), $utf8)
    }
  } else { $notes += "FOCUS: Cursor not running -- indeterminate, skipped" }
} catch { $warns += ("focus check error: " + $_.Exception.Message) }

# --- INV-AUTHSTREAK: a TRAILING run of failed auth.refresh (session at risk of dropping) ---
# Secondary net for a DIFFERENT future gap cause than focus: if the token refresh loop
# starts failing repeatedly and the last outcome is still a failure, the session is about
# to drop -> ads stop -> billing stops. Warn BEFORE the gap widens. Counts only the
# CURRENT trailing streak (resets the instant an ok:true appears). Fail-open: no/garbled
# log -> silence. Today this is dormant by design (last auth.refresh ok:true -> streak 0).
try {
  $streak = 0
  if ($SimulateAuthStreak) {
    $streak = 99
  } elseif (Test-Path $DebugLog) {
    $tail = Get-Content $DebugLog -Tail 80 -ErrorAction SilentlyContinue
    for ($i = $tail.Count - 1; $i -ge 0; $i--) {
      $ln = $tail[$i]
      if ($ln -match 'auth\.refresh') {
        if ($ln -match '"ok":true') { break }
        elseif ($ln -match '"ok":false') { $streak++ }
      }
    }
  }
  if ($streak -ge $AuthFailStreak) {
    $lastASNotify = [datetime]"2000-01-01"
    if (Test-Path $AuthStreakState) {
      try { $as = Get-Content $AuthStreakState -Raw | ConvertFrom-Json
            if ($as.lastNotify) { $lastASNotify = [datetime]$as.lastNotify } } catch {}
    }
    if ($SimulateAuthStreak -or (((Get-Date) - $lastASNotify).TotalMinutes -ge $RenotifyMinutes)) {
      $warns += ("Kickbacks auth.refresh fallando (" + $streak + " seguidos) -- si persiste perderas la sesion y el billing. Ctrl+Shift+P -> 'Kickbacks: Sign in' si se detiene.")
      if (-not $SimulateAuthStreak) {
        [System.IO.File]::WriteAllText($AuthStreakState, (@{ lastNotify = (Get-Date).ToString('o'); streak = $streak } | ConvertTo-Json -Compress), $utf8)
      }
    } else { $notes += ("AUTHSTREAK: present (streak=" + $streak + ") -- within renotify throttle") }
  }
} catch { $warns += ("authstreak check error: " + $_.Exception.Message) }

# --- optional self-test: run the real chain, assert the bar ---
$selfTestResult = ""
if ($SelfTest) {
  try {
    $session = "guard-selftest-" + ([guid]::NewGuid().ToString())
    $payload = @{ model = @{ display_name = "Opus 4.8" }; workspace = @{ current_dir = "C:\Users\User" }; session_id = $session; context_window = @{ remaining_percentage = 62 } } | ConvertTo-Json -Compress
    $inFile = Join-Path $env:TEMP ("kbguard_selftest_" + $PID + ".json")
    [System.IO.File]::WriteAllText($inFile, $payload, $utf8)
    $cmdline = '"{0}" "{1}" < "{2}"' -f $Node, $Mjs, $inFile
    $out = cmd /c $cmdline | Out-String
    $hasBar = $out -match '\d+%'; $hasAd = $out -match 'ad'
    $selfTestResult = "selftest bar=$hasBar ad=$hasAd"
    if (-not $hasBar) { $warns += "SELFTEST: bar did NOT render through the chain" }
    try { [System.IO.File]::Delete($inFile) } catch {}
  } catch { $warns += ("selftest error: " + $_.Exception.Message) }
}

# --- log (append, capped) + report ---
try {
  $line = "$stamp healed=[" + ($healed -join '; ') + "] warns=[" + ($warns -join '; ') + "] notes=[" + ($notes -join '; ') + "] $selfTestResult"
  $dir = Split-Path $LogFile -Parent
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  Add-Content -Path $LogFile -Value $line -Encoding UTF8
  $all = Get-Content $LogFile -ErrorAction SilentlyContinue
  if ($all.Count -gt 200) { $all[-200..-1] | Set-Content -Path $LogFile -Encoding UTF8 }
} catch {}

if ($healed.Count) { Write-Output ("HEALED: " + ($healed -join '; ')) } else { Write-Output "OK: invariants already satisfied (no change)" }
foreach ($w in $warns) { Write-Output ("WARN: " + $w) }
foreach ($n in $notes) { Write-Output ($n) }
if ($selfTestResult) { Write-Output $selfTestResult }
exit 0
