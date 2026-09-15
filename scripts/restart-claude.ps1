#Requires -Version 5.1
# ============================================================================
# /restart -- graceful in-pane restart via /exit injection (no SIGKILL).
#
# Sealed 2026-05-31 (REVISED): replaces the Stop-Process -Force kill with
# WriteConsoleInputW injection of "/exit\r" into the shared console input
# buffer. The Owner reported the older /restart did NOT kill the pane --
# claude exited gracefully via /exit, control fell back to the kclaude.bat
# wrapper, and the same session resumed. This restores that behavior.
#
# How it works (Win32 console architecture):
#   - claude.exe and any PowerShell tool subprocess SHARE the same console
#     (confirmed: GetConsoleProcessList returns BOTH PIDs).
#   - PowerShell's STDIN handle is a pipe (claude redirected it for tool
#     JSON-RPC) and is NOT the console input buffer.
#   - Opening "CONIN$" via CreateFileW yields a handle to the SHARED
#     console input buffer (mode 0x208 = ENABLE_EXTENDED_FLAGS |
#     ENABLE_VIRTUAL_TERMINAL_INPUT, verified live on this host).
#   - WriteConsoleInputW key events into CONIN$ are read by claude.exe's
#     input loop as if the Owner typed them.
#
# Sequence (zero-keystroke under kclaude.bat parent):
#   1. Capture CLAUDE_CODE_SESSION_ID.
#   2. Resolve claude.exe path (CLAUDE_CODE_EXECPATH / PATH / ~/.local/bin).
#   3. Walk PowerShell's parent chain to locate claude.exe PID
#      (for the kclaude.bat flag-file naming convention).
#   4. Write SID -> ~/.claude/lazarus/kclaude-restart-sid.txt.
#   5. Write flag -> %TEMP%\claude-restart-<claude-pid>.flag.
#   6. Copy clipboard fallback ("<claude.exe>" --resume "<uuid>").
#   7. INJECT "/exit\r" into the shared console input buffer.
#   8. Exit PowerShell. claude completes the tool turn, returns to its
#      input loop, reads "/exit" from the buffer, exits gracefully.
#   9. kclaude.bat detects the flag, runs claude --resume <sid> in the
#      SAME pane.
#
# Fallback path:
#   - When the CONIN$ injection cannot complete (missing console, write
#     failure), the script falls through to Stop-Process -Force (the
#     pre-2026-05-31-evening behavior) so the Owner is NEVER stuck with
#     a hung claude.exe. The fallback ALWAYS prints a yellow-tagged
#     warning so the regression is visible.
#
# Session Safety Contract sec.1: .jsonl is NEVER touched. claude.exe persists
# session events synchronously per turn -- /exit at a quiet moment is safe.
#
# ASCII-ONLY (BL-2026-05-24): loaded by powershell.exe 5.1 (ANSI codepage).
# The rule was declared in this header and broken two lines above it: a section
# sign sat here from the first revision. Under a non-ASCII OEM codepage PS 5.1
# mis-tokenizes such bytes, and the failure shows up as a phantom parse error
# somewhere else entirely. Declaring a constraint is not enforcing it -- the
# gate is the byte sweep in tools/test_restart_speed.py.
# ============================================================================

$ErrorActionPreference = "Stop"

# 1. Capture session id ------------------------------------------------------
$sessionId = $env:CLAUDE_CODE_SESSION_ID
if (-not $sessionId -or $sessionId -notmatch '^[0-9a-fA-F-]{36}$') {
    Write-Host "CLAUDE_CODE_SESSION_ID missing/invalid; kclaude will fall back to --continue." -ForegroundColor Yellow
    $sessionId = $null
}

# 2. Resolve claude.exe path -------------------------------------------------
$claudePath = $env:CLAUDE_CODE_EXECPATH
if (-not $claudePath -or -not (Test-Path $claudePath)) {
    $cmd = Get-Command claude.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        $claudePath = $cmd.Source
    } else {
        $candidate = Join-Path $env:USERPROFILE ".local\bin\claude.exe"
        if (Test-Path $candidate) { $claudePath = $candidate }
    }
}
if (-not $claudePath) {
    Write-Host "Cannot find claude.exe (CLAUDE_CODE_EXECPATH unset, not on PATH, not at ~/.local/bin)." -ForegroundColor Red
    exit 3
}

# 3. Find claude.exe PID in parent chain (needed for flag-file naming + fallback)
# SPEED (measured 2026-09-15). The chain walk below used one CIM query PER HOP,
# and a single Win32_Process query costs ~719 ms on this host -- about 1.4 s
# spent rediscovering a number the environment already hands us. claude.exe
# exports CLAUDE_PID into every tool subprocess; this session measured
# CLAUDE_PID=10104 and the independent topology walk resolved the same pid.
#
# The env var is trusted only after it is CORROBORATED: the pid must still be
# alive and still be named claude.exe. A recycled pid is the one way this could
# be wrong, and that check costs a few milliseconds.
#
# The fallback no longer walks hop by hop either. ONE bulk query (~465 ms) plus
# an in-memory walk (~37 ms) beats a single targeted hop, because the cost here
# is per-QUERY, not per-row.
function Get-ClaudePid {
    $envPid = 0
    if ([int]::TryParse([string]$env:CLAUDE_PID, [ref]$envPid) -and $envPid -gt 0) {
        $p = Get-Process -Id $envPid -ErrorAction SilentlyContinue
        if ($p -and $p.ProcessName -ieq 'claude') { return $envPid }
    }
    $all = Get-CimInstance Win32_Process -Property ProcessId,ParentProcessId,Name -ErrorAction SilentlyContinue
    if (-not $all) { return $null }
    $map = @{}
    foreach ($p in $all) { $map[[int]$p.ProcessId] = $p }
    $cur = $map[[int]$PID]
    $depth = 0
    while ($cur -and $depth -lt 12) {
        $parent = $map[[int]$cur.ParentProcessId]
        if (-not $parent) { return $null }
        if ($parent.Name -ieq 'claude.exe') { return [int]$parent.ProcessId }
        $cur = $parent
        $depth++
    }
    return $null
}
$claudePid = Get-ClaudePid

# 3b. Find the kclaude wrapper (the pane) that owns this claude.exe.
# Sealed 2026-09-15 (HR-RESTART-PANE-KEYED-001). The handshake used to be keyed
# globally -- one sid file for the whole host, and a flag consumed by the glob
# claude-restart-*.flag with Select-Object -First 1. With N panes open that is a
# race with two observed outcomes, and the Owner hit both in Orca X (5 of the 19
# live panes): another pane eats your flag, your loop finds none and exits to the
# bare shell ("me manda al cmd"); or the single global sid slot is overwritten or
# deleted, so the pane relaunches without --resume ("sin devolverme a donde
# estaba"). Evidence at diagnosis time: three session ids each claimed by two
# different wrappers, and a stale global sid file holding an InfinityOps session.
# The wrapper pid is the right key and the estate already uses it for the pane
# beacon (kclaude-pane-<wrapperpid>.sid) and the hibernate flag
# (claude-hibernate-<wrapperpid>.flag). Restart was the only global outlier.
function Get-WrapperPid {
    param([int]$ClaudeProcessId)
    if (-not $ClaudeProcessId) { return $null }
    $c = Get-CimInstance Win32_Process -Filter "ProcessId=$ClaudeProcessId" -ErrorAction SilentlyContinue
    if (-not $c -or -not $c.ParentProcessId) { return $null }
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$($c.ParentProcessId)" -ErrorAction SilentlyContinue
    if (-not $p) { return $null }
    if ($p.Name -inotmatch '^(powershell|pwsh)\.exe$') { return $null }
    # A PowerShell parent is not by itself the wrapper -- read its command line
    # and require kclaude.ps1. Measured 2026-09-15 over 48 live claude.exe: the
    # command-line probe agreed with the process topology 35/35, while the pane
    # beacon (the first probe tried here) was absent for 29 of those 35 -- the
    # beacon is only written once the wrapper knows a session id, so a freshly
    # opened pane has the loop and no beacon. Probing by beacon would have
    # refused /restart on 29 panes where it works today.
    if ([string]$p.CommandLine -imatch 'kclaude\.ps1') { return $p.ProcessId }
    return $null
}
$wrapperPid = Get-WrapperPid -ClaudeProcessId $claudePid

# Only a kclaude wrapper has the loop that relaunches claude after this script
# kills it. Measured 2026-09-15: panes come in two shapes on this host --
#   Cursor:  claude.exe <- powershell.exe (kclaude.ps1) <- cmd.exe <- Cursor.exe
#   Orca X:  claude.exe <- cmd.exe <- orca-terminal-daemon.exe
# The second has no wrapper and therefore no loop, so killing claude there drops
# the Owner at the cmd.exe prompt that was its parent all along. That is the
# reported "me manda al cmd unicamente sin devolverme a donde estaba" -- not a
# metaphor, the literal parent process.
$hasResumeLoop = [bool]$wrapperPid

# 4. Write the SID for the wrapper loop to consume on its next iteration ------
# Pane-keyed file is authoritative. The legacy global file is still written so a
# wrapper already running an OLDER in-memory copy of kclaude.ps1 keeps working
# exactly as before -- this change must not break the 19 panes open right now,
# which only pick up the new loop when they are next relaunched.
$lazarusDir = Join-Path $env:USERPROFILE ".claude\lazarus"
if (-not (Test-Path $lazarusDir)) { New-Item -ItemType Directory -Path $lazarusDir -Force | Out-Null }
$sidFile = Join-Path $lazarusDir "kclaude-restart-sid.txt"
$sidFilePane = if ($wrapperPid) { Join-Path $lazarusDir "kclaude-restart-sid-w$wrapperPid.txt" } else { $null }
if ($sessionId) {
    Set-Content -Path $sidFile -Value $sessionId -Encoding ASCII -NoNewline
    if ($sidFilePane) { Set-Content -Path $sidFilePane -Value $sessionId -Encoding ASCII -NoNewline }
} else {
    if (Test-Path $sidFile) { Remove-Item $sidFile -Force -ErrorAction SilentlyContinue }
    if ($sidFilePane -and (Test-Path $sidFilePane)) { Remove-Item $sidFilePane -Force -ErrorAction SilentlyContinue }
}

# 5. Write the flag the wrapper loop watches --------------------------------
# Both names match the legacy glob claude-restart-*.flag on purpose, so an old
# in-memory loop still sees a flag; a new loop matches its own pane exactly.
$flagName = if ($claudePid) { "claude-restart-$claudePid.flag" } else { "claude-restart-restart.flag" }
$flagFile = Join-Path $env:TEMP $flagName
Set-Content -Path $flagFile -Value '' -Encoding ASCII
if ($wrapperPid) {
    $flagFilePane = Join-Path $env:TEMP "claude-restart-w$wrapperPid.flag"
    Set-Content -Path $flagFilePane -Value '' -Encoding ASCII
    Write-Host ("  pane: wrapper PID {0} (flag + sid keyed to this pane)" -f $wrapperPid) -ForegroundColor DarkGray
} else {
    Write-Host "  pane: wrapper not identified; falling back to the global handshake." -ForegroundColor Yellow
}

# 5b. Write universal-fallback marker for restart_resume.js (BL-RESTART-001) -
# kclaude.bat handles the actual --resume <uuid> when it is the pane parent.
# This marker provides a CONTEXTUAL HINT (additionalContext) to any new
# session that lands in the same cwd within 5 min, even if kclaude.bat
# isn't the parent (PowerShell / Git Bash / VPS profiles).
$stateDir = Join-Path $env:USERPROFILE ".claude\state"
if (-not (Test-Path $stateDir)) { New-Item -ItemType Directory -Path $stateDir -Force | Out-Null }
$markerFile = Join-Path $stateDir "restart_pending.json"
$nowIso = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$cwd = (Get-Location).Path
# SPEED: spawning git for this cost 564 ms measured. The branch name is one
# line of .git/HEAD ("ref: refs/heads/<name>") and this field is descriptive
# metadata on a marker, not a decision input -- worth ~5 ms, not half a second.
# A detached HEAD has no ref: line, which correctly degrades to 'unknown'.
$branch = try {
    $headFile = Join-Path $cwd '.git\HEAD'
    if (Test-Path $headFile) {
        $h = [System.IO.File]::ReadAllText($headFile).Trim()
        if ($h -match '^ref:\s*refs/heads/(.+)$') { $Matches[1] } else { 'unknown' }
    } else { 'unknown' }
} catch { 'unknown' }
$markerObj = [pscustomobject]@{
    session_id  = $sessionId
    cwd         = $cwd
    branch      = $branch
    timestamp   = $nowIso
    session_note = "Session restarted via /restart. The kclaude.bat MC-LAZ-26 wrapper (if parent of this pane) ran claude --resume on the prior session id."
}
$markerJson = $markerObj | ConvertTo-Json -Compress
# PowerShell 5.1 `Set-Content -Encoding UTF8` writes a BOM that some JSON
# readers (Node JSON.parse, Python json.load without utf-8-sig) reject.
# Use .NET WriteAllText with UTF8Encoding($false) to emit UTF-8 WITHOUT BOM.
[System.IO.File]::WriteAllText(
    $markerFile,
    $markerJson,
    [System.Text.UTF8Encoding]::new($false))

# 6. Populate clipboard fallback (for panes NOT under the kclaude wrapper) ----
# HR-RESTART-VIA-KCLAUDE-001: relaunch via kclaude.ps1 so the Cognitive OS
# (CO-00 / CO-08) is active after a restart, even for a pane that was started
# with bare claude. Fail-open: bare claude if the wrapper is not on disk.
# Prefer the live launcher (bin, what the Cursor kClaude profile runs); fall
# back to the repo copy; else bare claude.
$kclaudeBin  = Join-Path $env:USERPROFILE ".claude\bin\kclaude.ps1"
$kclaudeRepo = Join-Path $env:USERPROFILE ".claude\skills\claude-power-pack\tools\kclaude.ps1"
$kclaudePs1 = if (Test-Path $kclaudeBin) { $kclaudeBin } elseif (Test-Path $kclaudeRepo) { $kclaudeRepo } else { $null }
$viaKclaude = [bool]$kclaudePs1
if ($sessionId) {
    if ($viaKclaude) {
        $resumeCmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $kclaudePs1 + '" --resume "' + $sessionId + '"'
    } else {
        $resumeCmd = '"' + $claudePath + '" --resume "' + $sessionId + '"'
    }
    $modeLabel = "--resume <this session>"
} else {
    if ($viaKclaude) {
        $resumeCmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $kclaudePs1 + '" --continue'
    } else {
        $resumeCmd = '"' + $claudePath + '" --continue'
    }
    $modeLabel = "--continue"
}
Set-Clipboard -Value $resumeCmd

Write-Host ""
Write-Host "Resume queued for the kclaude wrapper:" -ForegroundColor Cyan
Write-Host "  flag: $flagFile" -ForegroundColor DarkGray
Write-Host "  sid:  $sidFile" -ForegroundColor DarkGray
if ($viaKclaude) {
    Write-Host "Clipboard fallback (Ctrl+V + Enter if pane is NOT under kclaude) -- via kclaude wrapper:" -ForegroundColor Cyan
} else {
    Write-Host "[kclaude] wrapper not found; clipboard uses bare claude (fail-open)." -ForegroundColor Yellow
    Write-Host "Clipboard fallback (Ctrl+V + Enter if pane is NOT under kclaude):" -ForegroundColor Cyan
}
Write-Host "  $resumeCmd" -ForegroundColor White

if (-not $claudePid) {
    Write-Host ""
    Write-Host "Could not locate claude.exe in PowerShell's parent chain." -ForegroundColor Yellow
    Write-Host "Type /exit yourself; kclaude auto-resumes (if wrapping) or paste from clipboard." -ForegroundColor Yellow
    exit 0
}

# Dry-run guard (testing only): if PP_RESTART_DRY_RUN=1, exercise the full
# code path EXCEPT the actual /exit injection + fallback kill. Used to
# validate the script does not regress without ending the session.
if ($env:PP_RESTART_DRY_RUN -eq "1") {
    Write-Host ""
    Write-Host "[DRY RUN] PP_RESTART_DRY_RUN=1 -- skipping injection + fallback." -ForegroundColor Magenta
    Write-Host "[DRY RUN]   would inject '/exit<CR>' into CONIN`$ of console shared with PID $claudePid." -ForegroundColor Magenta
    Write-Host "[DRY RUN]   would NOT call Stop-Process -Force." -ForegroundColor Magenta
    Write-Host "[DRY RUN]   SID + flag + clipboard machinery already executed (real)." -ForegroundColor Magenta
    exit 0
}

# 7. INJECT "/exit\r" into the shared console input buffer -------------------
#
# OFF BY DEFAULT since 2026-09-15, opt in with PP_RESTART_TRY_EXIT=1.
#
# Section 8 below has documented since 2026-07-01 that this injection does NOT
# reach claude.exe under Cursor's ConPTY: WriteConsoleInputW writes the legacy
# console input buffer while claude (Node/Ink) reads the ConPTY VT stream, so
# "/exit" is never consumed and the watchdog is what actually ends the process.
#
# The cost of that dead path was not free. Add-Type compiles this C# through
# csc.exe on every invocation -- measured 865 ms warm and 1745 ms cold on this
# host -- plus the 250 ms settle below, on the Owner's critical path, to attempt
# something the file itself says will not work here. Keeping a capability that
# only fires where it works is right; paying for it where it cannot is not.
#
# The graceful path is still reachable for terminals with a real console
# (Windows Terminal, conhost), where it remains the nicer exit.
$injected = $false
if ($env:PP_RESTART_TRY_EXIT -ne '1') {
    Write-Host "  graceful /exit skipped (ConPTY does not deliver it); watchdog will end the process." -ForegroundColor DarkGray
}
if ($env:PP_RESTART_TRY_EXIT -eq '1') {
try {
    # Build the P/Invoke surface once per invocation.
    Add-Type -Name RestartConIn -Namespace PPClaude -MemberDefinition @'
[StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
public struct KEY_EVENT_RECORD {
    public int bKeyDown;
    public short wRepeatCount;
    public short wVirtualKeyCode;
    public short wVirtualScanCode;
    public char UnicodeChar;
    public int dwControlKeyState;
}

[StructLayout(LayoutKind.Explicit, CharSet=CharSet.Unicode)]
public struct INPUT_RECORD {
    [FieldOffset(0)] public short EventType;
    [FieldOffset(4)] public KEY_EVENT_RECORD KeyEvent;
}

[DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
public static extern System.IntPtr CreateFileW(
    string n, int a, int s,
    System.IntPtr sa, int cd, int fa, System.IntPtr t);

[DllImport("kernel32.dll")]
public static extern bool CloseHandle(System.IntPtr h);

[DllImport("kernel32.dll")]
public static extern bool FlushConsoleInputBuffer(System.IntPtr h);

[DllImport("kernel32.dll", CharSet=CharSet.Unicode)]
public static extern bool WriteConsoleInputW(
    System.IntPtr h, [In] INPUT_RECORD[] b, int n, out int w);

public static int InjectText(System.IntPtr hCon, string text) {
    var list = new System.Collections.Generic.List<INPUT_RECORD>();
    foreach (char c in text) {
        short vk = (short)char.ToUpper(c);
        if (c == '\r') vk = 0x0D;
        if (c == '\n') vk = 0x0D;
        var kd = new KEY_EVENT_RECORD();
        kd.bKeyDown = 1;
        kd.wRepeatCount = 1;
        kd.wVirtualKeyCode = vk;
        kd.wVirtualScanCode = 0;
        kd.UnicodeChar = c;
        kd.dwControlKeyState = 0;
        var ku = kd;
        ku.bKeyDown = 0;
        var rd = new INPUT_RECORD();
        rd.EventType = 1;
        rd.KeyEvent = kd;
        var ru = new INPUT_RECORD();
        ru.EventType = 1;
        ru.KeyEvent = ku;
        list.Add(rd);
        list.Add(ru);
    }
    var arr = list.ToArray();
    int written;
    if (!WriteConsoleInputW(hCon, arr, arr.Length, out written)) return -1;
    return written;
}
'@

    $GENERIC_READ  = [int]-2147483648  # 0x80000000 as signed int
    $GENERIC_WRITE = 0x40000000
    $SHARE_RW = 3
    $OPEN_EXISTING = 3

    $hCon = [PPClaude.RestartConIn]::CreateFileW(
        "CONIN`$",
        ($GENERIC_READ -bor $GENERIC_WRITE),
        $SHARE_RW,
        [System.IntPtr]::Zero,
        $OPEN_EXISTING,
        0,
        [System.IntPtr]::Zero)

    if ($hCon.ToInt64() -ne -1) {
        Write-Host ""
        Write-Host ("Injecting /exit into claude.exe PID={0} ({1}) ..." `
                    -f $claudePid, $modeLabel) -ForegroundColor Cyan
        # Brief settle: let the tool result reach claude first so /exit
        # lands as the NEXT user input (not racing with the current
        # turn's stdin handling).
        Start-Sleep -Milliseconds 250
        $written = [PPClaude.RestartConIn]::InjectText($hCon, "/exit`r")
        [PPClaude.RestartConIn]::CloseHandle($hCon) | Out-Null
        if ($written -gt 0) {
            $injected = $true
            Write-Host ("  injected $written key events. claude will exit; " +
                        "kclaude.bat resumes the session.") -ForegroundColor Green
        } else {
            Write-Host "  WriteConsoleInputW returned 0 events; falling back to force-kill." -ForegroundColor Yellow
        }
    } else {
        Write-Host ""
        Write-Host "Could not open CONIN`$ (no shared console)." -ForegroundColor Yellow
        Write-Host "Falling back to force-kill (older behavior)." -ForegroundColor Yellow
    }
} catch {
    Write-Host ""
    Write-Host "Injection path threw: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "Falling back to force-kill." -ForegroundColor Yellow
}
}  # end PP_RESTART_TRY_EXIT opt-in

# 8. GUARANTEED EXIT (2026-07-01 fix) -----------------------------------------
# Root cause of "/restart does not work": under Cursor's ConPTY terminal the
# CONIN$ injection does NOT reach claude.exe. WriteConsoleInputW writes to the
# legacy console input buffer, but claude (Node/Ink) reads the ConPTY VT byte
# stream, so the injected "/exit" is never consumed and the session never
# restarts. And because $written -gt 0 was treated as success, the force-kill
# fallback never fired -- claude stayed alive with the flag unconsumed.
#
# Fix: ALWAYS arm a detached, hidden watchdog that force-kills claude after a
# short grace window IF it is still alive. Graceful /exit still wins where the
# terminal supports it (the watchdog then finds claude already gone and no-ops);
# otherwise the watchdog guarantees the restart. Session Safety Contract 1: the
# .jsonl is persisted per turn, so a force-kill at this idle prompt loses no
# conversation state (this is the historically-working behavior).
# GUARD (HR-RESTART-NO-LOOP-NO-KILL-001, 2026-09-15): never kill claude when
# nothing is going to bring it back. The watchdog below used to arm
# unconditionally, so in a pane with no resume loop /restart was a pure kill: the
# session ended and the Owner landed at the parent shell. A restart whose second
# half does not exist is not a restart, and destroying the session to discover
# that is the wrong order. Refuse, keep the session alive, and hand over the
# exact command -- it is already on the clipboard.
if (-not $hasResumeLoop) {
    Write-Host ""
    Write-Host "  /restart CANCELLED -- this pane has no kclaude resume loop." -ForegroundColor Yellow
    Write-Host "  Killing claude here would drop you at the parent shell with no way back," -ForegroundColor Yellow
    Write-Host "  so the session has been left running and untouched." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  To restart by hand, paste the command already on your clipboard:" -ForegroundColor Cyan
    Write-Host ("    {0}" -f $resumeCmd) -ForegroundColor White
    Write-Host ""
    Write-Host "  To get in-pane /restart in this terminal, launch claude through the" -ForegroundColor DarkGray
    Write-Host "  wrapper instead:  kclaude" -ForegroundColor DarkGray
    if (Test-Path $flagFile) { Remove-Item $flagFile -Force -ErrorAction SilentlyContinue }
    if ($wrapperPid) {
        $pf = Join-Path $env:TEMP "claude-restart-w$wrapperPid.flag"
        if (Test-Path $pf) { Remove-Item $pf -Force -ErrorAction SilentlyContinue }
    }
    exit 0
}

$graceMs = 2500
$watchCmd = "Start-Sleep -Milliseconds $graceMs; try { Get-Process -Id $claudePid -ErrorAction Stop | Out-Null; Stop-Process -Id $claudePid -Force -ErrorAction SilentlyContinue } catch { }"
try {
    Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -ArgumentList @(
        '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-Command', $watchCmd) | Out-Null
    Write-Host ("  restart guaranteed: watchdog force-kills PID {0} in {1} ms if /exit did not take." -f $claudePid, $graceMs) -ForegroundColor DarkCyan
} catch {
    Write-Host "  watchdog spawn failed; killing inline as last resort." -ForegroundColor Yellow
    Start-Sleep -Milliseconds $graceMs
    Stop-Process -Id $claudePid -Force -ErrorAction SilentlyContinue
}

exit 0
