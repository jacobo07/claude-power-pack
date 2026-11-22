#Requires -Version 5.1
# auto-compact-sendkeys-daemon.ps1 -- sealed 2026-05-20 (Owner 1c, BL-0003 bypass)
# Per-session flags + window routing: 2026-09-18
#   (spec: skills/claude-power-pack/vault/specs/autocompact-per-session-flags.md)
#
# Out-of-band SendKeys dispatcher for the Tier-2 auto-compact flow. Spawned
# detached by context-watchdog at Tier 2 and by auto-compact-stop-launcher.ps1.
# Polls ~/.claude/hooks/ for:
#   auto-compact-trigger-<session>.flag : freshly dropped by the watchdog.
#   auto-compact-pending-<session>.flag : carried over while Cursor was not
#                                         the foreground window.
# The legacy single names (auto-compact-trigger.flag / -pending.flag) match
# the same globs, so an old watchdog keeps working.
#
# Behaviour:
#   - Cursor NOT foreground -> demote each trigger to its own pending file.
#     Nothing is ever discarded (the old single flag dropped the second run's
#     Enter, which stalled it).
#   - Cursor foreground, title "<root> - Cursor":
#       * a flag whose cwd leaf == <root>             -> Enter (oldest first)
#       * a flag whose project has ANOTHER open window -> wait for that window
#       * a flag whose project has no open window      -> Enter (legacy rule)
#   - At most one Enter per window until focus leaves it and comes back, so
#     two runs sharing one window never get two Enters in a row.
#   - TTL exit leaves pending files for the next spawn.
#
# Single-flight: PID-stamped lock; stale lock (dead PID) is reclaimed.
#
# Honest limits:
#   - SendKeys needs the interactive logon session.
#   - Never steals focus.
#   - Two runs in ONE Cursor window (two terminal tabs) cannot be told apart
#     from Win32; the focus-change rule limits misfire, it cannot route.
#
# Test seam (never set in production):
#   AC_DAEMON_DIR           flag/lock/log directory
#   AC_DAEMON_DRYRUN=1      log WOULD-SEND instead of SendKeys
#   AC_DAEMON_FAKE_FG       JSON {"name":..,"title":..,"hwnd":..} or a path to
#                           a file holding it (re-read every tick)
#   AC_DAEMON_FAKE_WINDOWS  JSON array of Cursor window titles, or a path
#   AC_DAEMON_TTL           seconds
#   AC_DAEMON_REFUSE_AFTER  seconds a mismatched flag waits before refusal
#   GSD_LONG_RUN_STATE_DIR  ledger directory
#
# Expect-line validation (2026-09-18, spec vault/specs/gsd-long-run-v2.md gap 3):
# a flag carrying `transcript` + `expect_line`/`expect_prefix` is dispatched only
# when the transcript's last assistant line matches; mismatched for longer than
# the refuse window it becomes auto-compact-refused-<sid>.flag + a ledger row.

$ErrorActionPreference = 'SilentlyContinue'

$hooksDir = if ($env:AC_DAEMON_DIR) { $env:AC_DAEMON_DIR } else { Join-Path $env:USERPROFILE '.claude\hooks' }
$lockFile = Join-Path $hooksDir '.auto-compact-daemon.lock'
$logFile  = Join-Path $hooksDir 'auto-compact-daemon.log'
$dryRun   = ($env:AC_DAEMON_DRYRUN -eq '1')

$ttlSec = 600
if ($env:AC_DAEMON_TTL) { $ttlSec = [int]$env:AC_DAEMON_TTL }
$tickMs = 500

function Acquire-Lock {
    if (Test-Path $lockFile) {
        try {
            $line = (Get-Content $lockFile -Raw -ErrorAction Stop).Trim()
            $oldPid = [int]($line -split '\|')[0]
            if (Get-Process -Id $oldPid -ErrorAction SilentlyContinue) {
                return $false
            }
        } catch {}
    }
    "$PID|$(Get-Date -Format o)" | Set-Content $lockFile -Encoding ASCII -Force
    return $true
}

function Log($msg) {
    try {
        "$([DateTime]::UtcNow.ToString('o')) [pid $PID] $msg" |
            Out-File -Append -FilePath $logFile -Encoding utf8
    } catch {}
}

function Read-Fake($value) {
    if (-not $value) { return $null }
    $raw = $value
    if (Test-Path -LiteralPath $value) { $raw = Get-Content -LiteralPath $value -Raw }
    try { return ($raw | ConvertFrom-Json) } catch { return $null }
}

# Title "<editor> - <root> - Cursor" or "<root> - Cursor" -> "<root>".
function Get-Root($title) {
    if (-not $title) { return '' }
    $t = $title -replace '\s+-\s+Cursor\s*$', ''
    $parts = $t -split '\s+-\s+'
    return $parts[-1].Trim().TrimStart([char]0x25CF).Trim()
}

if (-not (Acquire-Lock)) { exit 0 }

$src = @"
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Diagnostics;
public static class AcFg {
    public delegate bool EnumProc(IntPtr h, IntPtr l);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc p, IntPtr l);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    static string ProcName(IntPtr h) {
        uint pid; GetWindowThreadProcessId(h, out pid);
        try { return Process.GetProcessById((int)pid).ProcessName; } catch { return ""; }
    }
    static string Title(IntPtr h) { var sb = new StringBuilder(512); GetWindowText(h, sb, 512); return sb.ToString(); }
    public static string[] Fg() {
        IntPtr h = GetForegroundWindow();
        if (h == IntPtr.Zero) return new string[] { "", "", "0" };
        return new string[] { ProcName(h), Title(h), h.ToInt64().ToString() };
    }
    public static string[] CursorTitles() {
        var r = new List<string>();
        EnumWindows((h, l) => {
            if (IsWindowVisible(h) && ProcName(h) == "Cursor") { var t = Title(h); if (t.Length > 0) r.Add(t); }
            return true;
        }, IntPtr.Zero);
        return r.ToArray();
    }
}
// Orca provider (2026-11-17). Orca stamps ORCA_TERMINAL_HANDLE on every PTY it spawns, so the
// handle in claude.exe's OWN environment block names its pane; a pid match is impossible because
// Orca's terminal records carry no PTY pid. x64 targets only: anything else returns null.
public static class AcProcEnv {
    [StructLayout(LayoutKind.Sequential)] struct Pbi { public IntPtr R1; public IntPtr Peb; public IntPtr R2a; public IntPtr R2b; public IntPtr Pid; public IntPtr R3; }
    [DllImport("ntdll.dll")] static extern int NtQueryInformationProcess(IntPtr h, int c, ref Pbi p, int l, out int r);
    [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(int a, bool i, int pid);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll")] static extern bool IsWow64Process(IntPtr h, out bool w);
    [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, IntPtr n, out IntPtr r);
    static byte[] Read(IntPtr h, IntPtr a, int n) {
        var b = new byte[n]; IntPtr r;
        if (!ReadProcessMemory(h, a, b, (IntPtr)n, out r) || (long)r != n) return null;
        return b;
    }
    public static string Get(int pid, string name) {
        if (IntPtr.Size != 8) return null;
        IntPtr h = OpenProcess(0x0400 | 0x0010, false, pid);
        if (h == IntPtr.Zero) return null;
        try {
            bool wow; if (!IsWow64Process(h, out wow) || wow) return null;
            var p = new Pbi(); int rl;
            if (NtQueryInformationProcess(h, 0, ref p, Marshal.SizeOf(p), out rl) != 0) return null;
            var pp = Read(h, IntPtr.Add(p.Peb, 0x20), 8); if (pp == null) return null;
            IntPtr par = (IntPtr)BitConverter.ToInt64(pp, 0);
            var ep = Read(h, IntPtr.Add(par, 0x80), 8); var sz = Read(h, IntPtr.Add(par, 0x3F0), 8);
            if (ep == null || sz == null) return null;
            long size = BitConverter.ToInt64(sz, 0);
            if (size <= 0 || size > 4194304) return null;
            var blk = Read(h, (IntPtr)BitConverter.ToInt64(ep, 0), (int)size); if (blk == null) return null;
            string pre = name + "=";
            foreach (var kv in Encoding.Unicode.GetString(blk).Split('\0'))
                if (kv.StartsWith(pre, StringComparison.OrdinalIgnoreCase)) return kv.Substring(pre.Length);
            return null;
        } finally { CloseHandle(h); }
    }
}
// Same quoting as Orca's native CLI launcher (OrcaCliLauncher.cs), so a typed line with quotes or
// spaces reaches the CLI byte-identical; PowerShell 5.1's native-arg passing does not escape `"`.
public static class AcOrcaCli {
    static string Q(string v) {
        bool need = v.Length == 0;
        for (int i = 0; i < v.Length && !need; i++) need = v[i] == '"' || Char.IsWhiteSpace(v[i]);
        if (!need) return v;
        var sb = new StringBuilder("\""); int bs = 0;
        foreach (char ch in v) {
            if (ch == '\\') { bs++; continue; }
            if (ch == '"') { sb.Append('\\', bs * 2 + 1); sb.Append('"'); } else { sb.Append('\\', bs); sb.Append(ch); }
            bs = 0;
        }
        sb.Append('\\', bs * 2); sb.Append('"'); return sb.ToString();
    }
    // Returns { exitCode, stdout }; exitCode -1 = timed out (killed) or could not start.
    public static string[] Run(string exe, string[] args, int timeoutMs) {
        var psi = new ProcessStartInfo(exe);
        var parts = new List<string>(); foreach (var a in args) parts.Add(Q(a));
        psi.Arguments = String.Join(" ", parts.ToArray());
        psi.UseShellExecute = false; psi.RedirectStandardOutput = true; psi.RedirectStandardError = true;
        psi.CreateNoWindow = true; psi.StandardOutputEncoding = Encoding.UTF8;
        psi.EnvironmentVariables["ELECTRON_RUN_AS_NODE"] = "1";
        psi.EnvironmentVariables["ORCA_WINDOWS_PACKAGED_CLI_LAUNCHER"] = "1";
        psi.EnvironmentVariables["ORCA_CLI_COMMAND"] = "orca";
        psi.EnvironmentVariables.Remove("NODE_OPTIONS");
        try {
            using (var p = Process.Start(psi)) {
                var so = p.StandardOutput.ReadToEndAsync(); p.StandardError.ReadToEndAsync();
                if (!p.WaitForExit(timeoutMs)) {
                    try { p.Kill(); } catch (InvalidOperationException) { return new string[] { "-1", "exited during kill" }; }
                    return new string[] { "-1", "timeout" };
                }
                return new string[] { p.ExitCode.ToString(), so.Result };
            }
        } catch (Exception e) { return new string[] { "-1", e.Message }; }
    }
}
"@
try { Add-Type -TypeDefinition $src -ErrorAction Stop } catch {
    Log "Add-Type failed: $($_.Exception.Message)"
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
    exit 2
}
if (-not $dryRun) {
    try { Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop } catch {
        Log "Forms load failed: $($_.Exception.Message)"
        Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
        exit 3
    }
}

function Get-Foreground {
    $fake = Read-Fake $env:AC_DAEMON_FAKE_FG
    if ($fake) { return @{ name = [string]$fake.name; title = [string]$fake.title; hwnd = [string]$fake.hwnd } }
    $f = [AcFg]::Fg()
    return @{ name = $f[0]; title = $f[1]; hwnd = $f[2] }
}

function Get-OpenRoots {
    $fake = Read-Fake $env:AC_DAEMON_FAKE_WINDOWS
    $titles = if ($fake) { @($fake) } else { @([AcFg]::CursorTitles()) }
    return @($titles | ForEach-Object { Get-Root $_ } | Where-Object { $_ })
}

function Get-Flags {
    $out = @()
    foreach ($f in @(Get-ChildItem -LiteralPath $hooksDir -File -ErrorAction SilentlyContinue |
                     Where-Object { $_.Name -like 'auto-compact-trigger*.flag' -or $_.Name -like 'auto-compact-pending*.flag' } |
                     Sort-Object LastWriteTime)) {
        $leaf = ''; $sid = ''; $tr = ''; $eLine = ''; $ePrefix = ''; $fLine = ''
        try {
            $p = Get-Content -LiteralPath $f.FullName -Raw | ConvertFrom-Json
            if ($p.cwd) { $leaf = Split-Path -Leaf ([string]$p.cwd).TrimEnd('\', '/') }
            if ($p.session_id) { $sid = [string]$p.session_id }
            if ($p.transcript) { $tr = [string]$p.transcript }
            if ($p.expect_line) { $eLine = [string]$p.expect_line }
            if ($p.expect_prefix) { $ePrefix = [string]$p.expect_prefix }
            if ($p.fresh_line) { $fLine = [string]$p.fresh_line }
        } catch {}
        $out += [pscustomobject]@{ file = $f; leaf = $leaf; isTrigger = ($f.Name -like 'auto-compact-trigger*');
                                   sid = $sid; transcript = $tr; expectLine = $eLine; expectPrefix = $ePrefix;
                                   freshLine = $fLine }
    }
    return $out
}

# Gap 3 (spec gsd-long-run-v2.md): Enter submits whatever the input box holds.
# A flag that names what it expects is only dispatched when the transcript's
# last assistant line IS that; anything else waits, then is refused.
$refuseAfter = 180
if ($env:AC_DAEMON_REFUSE_AFTER) { $refuseAfter = [int]$env:AC_DAEMON_REFUSE_AFTER }

function Get-LastAssistantLine($path) {
    try {
        $fs = [IO.File]::Open($path, 'Open', 'Read', 'ReadWrite')
        try {
            $len = $fs.Length
            $start = [Math]::Max([long]0, $len - 262144)
            [void]$fs.Seek($start, 'Begin')
            $buf = New-Object byte[] ($len - $start)
            $n = $fs.Read($buf, 0, $buf.Length)
        } finally { $fs.Close() }
        $lines = [Text.Encoding]::UTF8.GetString($buf, 0, $n) -split "`n"
        for ($i = $lines.Count - 1; $i -ge 0; $i--) {
            $l = $lines[$i].Trim()
            if (-not $l -or -not $l.Contains('"assistant"')) { continue }
            try { $o = $l | ConvertFrom-Json } catch { continue }
            if ($o.type -ne 'assistant') { continue }
            $parts = @()
            $c = $o.message.content
            if ($c -is [string]) { $parts += $c } else { foreach ($b in $c) { if ($b.type -eq 'text') { $parts += [string]$b.text } } }
            $ls = @(($parts -join "`n") -split "`r?`n" | Where-Object { $_.Trim() })
            if ($ls.Count -eq 0) { return '' }
            return $ls[-1].Trim().Trim([char]96).Trim()
        }
        return $null
    } catch { return $null }
}

# Returns @{ state; line }. `line` is the validated command on 'ok': the daemon
# TYPES it before Enter. Measured 2026-09-18 (session fa6961b6): a bare Enter
# landed on an empty input box and submitted nothing -- the agent's trailing line
# lives in the transcript, never in the prompt box, so Enter alone cannot run it.
# Fresh-session lines (2026-09-29). After a rollover /clear the successor's prompt is
# empty and no assistant line exists to validate, so the expect-line rule cannot apply.
# A `fresh_line` flag is typed only while the session has had NO assistant turn: the
# moment one exists, typing would land inside work somebody started. Only /kresume is
# representable, bare or as `/kresume focus on <one line>` (Owner 2026-09-29, like
# /compact). The focus text comes from a capsule and is typed into a terminal, so this
# shape check is the authority, not the hub: no control or line-separator character
# (a newline would submit early and put the rest in a second prompt), first char not a
# space, at most 200 chars. \z, never $: in .NET `$` also matches before a final "\n".
$freshPattern = '^/kresume( focus on [^\s\u0000-\u001f\u007f-\u009f\u2028\u2029][^\u0000-\u001f\u007f-\u009f\u2028\u2029]{0,199})?\z'

# 'fresh' (file absent, or no assistant row) | 'used' | 'unknown' (unreadable).
function Get-TranscriptTurnState($path) {
    if (-not $path) { return 'unknown' }
    if (-not (Test-Path -LiteralPath $path)) { return 'fresh' }
    try {
        $fs = [IO.File]::Open($path, 'Open', 'Read', 'ReadWrite')
        try {
            if ($fs.Length -gt 1048576) { return 'used' }
            $buf = New-Object byte[] ($fs.Length)
            $n = $fs.Read($buf, 0, $buf.Length)
        } finally { $fs.Close() }
        foreach ($l in ([Text.Encoding]::UTF8.GetString($buf, 0, $n) -split "`n")) {
            if (-not $l.Contains('"assistant"')) { continue }
            try { $o = $l.Trim() | ConvertFrom-Json } catch { continue }
            if ($o.type -eq 'assistant') { return 'used' }
        }
        return 'fresh'
    } catch { return 'unknown' }
}

function Get-ExpectState($fl) {
    if ($fl.freshLine) {
        if ($fl.freshLine -cnotmatch $freshPattern) {
            return @{ state = 'refuse'; line = ''; why = "fresh_line [$($fl.freshLine)] is not an allowed /kresume form" }
        }
        $ts = Get-TranscriptTurnState $fl.transcript
        if ($ts -eq 'fresh') { return @{ state = 'ok'; line = $fl.freshLine } }
        if ($ts -eq 'used') { return @{ state = 'refuse'; line = ''; why = 'the session already had a turn; not typing into it' } }
        if (((Get-Date) - $fl.file.LastWriteTime).TotalSeconds -gt $refuseAfter) {
            return @{ state = 'refuse'; line = ''; why = 'transcript unreadable for the whole wait' }
        }
        return @{ state = 'wait'; line = '' }
    }
    if (-not $fl.transcript -or (-not $fl.expectLine -and -not $fl.expectPrefix)) { return @{ state = 'nocheck'; line = '' } }
    $last = Get-LastAssistantLine $fl.transcript
    if ($null -ne $last) {
        if ($fl.expectLine -and $last -ceq $fl.expectLine) { return @{ state = 'ok'; line = $last } }
        if ($fl.expectPrefix -and $last.StartsWith($fl.expectPrefix)) { return @{ state = 'ok'; line = $last } }
    }
    if (((Get-Date) - $fl.file.LastWriteTime).TotalSeconds -gt $refuseAfter) { return @{ state = 'refuse'; line = '' } }
    return @{ state = 'wait'; line = '' }
}

# SendKeys reserves + ^ % ~ ( ) { } [ ]; each is sent literally inside braces.
function ConvertTo-SendKeysLiteral([string]$text) {
    $sb = New-Object Text.StringBuilder
    foreach ($ch in $text.ToCharArray()) {
        if ('+^%~(){}[]'.IndexOf($ch) -ge 0) { [void]$sb.Append('{').Append($ch).Append('}') }
        else { [void]$sb.Append($ch) }
    }
    return $sb.ToString()
}

function Write-LedgerRow($sid, $event, $detail) {
    try {
        $dir = if ($env:GSD_LONG_RUN_STATE_DIR) { $env:GSD_LONG_RUN_STATE_DIR } else { Join-Path $env:USERPROFILE '.claude\state' }
        $row = @{ ts = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss+00:00'); session_id = $sid; event = $event; detail = $detail } | ConvertTo-Json -Compress
        [IO.File]::AppendAllText((Join-Path $dir 'gsd-autorun-ledger.jsonl'), $row + "`n", (New-Object Text.UTF8Encoding($false)))
    } catch {}
}

function Refuse-Flag($fl, $why) {
    $dest = Join-Path $hooksDir ($fl.file.Name -replace '^auto-compact-(trigger|pending)', 'auto-compact-refused')
    try { Move-Item -LiteralPath $fl.file.FullName -Destination $dest -Force -ErrorAction Stop } catch {}
    if ($fl.freshLine) {
        Log "REFUSED flag=$($fl.file.Name) fresh_line=[$($fl.freshLine)] -- $why"
        Write-LedgerRow $fl.sid 'refused' "fresh_line [$($fl.freshLine)] not typed: $why"
        return
    }
    $want = if ($fl.expectLine) { $fl.expectLine } else { "$($fl.expectPrefix)..." }
    Log "REFUSED flag=$($fl.file.Name) expected=[$want] -- last assistant line never matched"
    Write-LedgerRow $fl.sid 'refused' "expected [$want]; last assistant line never matched within ${refuseAfter}s"
}

# Exact-target continuation (2026-09-18, spec
# skills/claude-power-pack/vault/specs/exact-target-continuation.md, C4).
# Foreground is presentation, not identity: on 2026-09-18 this daemon typed
# /d1-continue and /absw2-continue into Cursor windows that did not own those
# sessions. By DEFAULT only the exact path (terminal inbox) may type; a flag no
# exact provider accepted is REFUSED and ledgered. The old foreground SendKeys
# path runs only with CPP_LEGACY_FOREGROUND_SENDKEYS=1 (manual-class opt-in).
$legacyForeground = ($env:CPP_LEGACY_FOREGROUND_SENDKEYS -eq '1')

function Refuse-NoExact($fl, $why) {
    $dest = Join-Path $hooksDir ($fl.file.Name -replace '^auto-compact-(trigger|pending)', 'auto-compact-refused')
    try { Move-Item -LiteralPath $fl.file.FullName -Destination $dest -Force -ErrorAction Stop } catch {}
    Log "REFUSED flag=$($fl.file.Name) -- $why; foreground fallback disabled"
    Write-LedgerRow $fl.sid 'refused' "no exact-session delivery: $why; foreground fallback disabled (CPP_LEGACY_FOREGROUND_SENDKEYS=1 allows it)"
}

function Send-Enter($flag, $why) {
    # A validated line is typed, then Enter; a flag with no expectation keeps the
    # legacy bare Enter. Honest limit: text the user already typed into that box
    # is not visible from Win32, so the command would be appended to it.
    $keys = '~'; $typed = ''
    if ($flag.typeLine) { $typed = [string]$flag.typeLine; $keys = (ConvertTo-SendKeysLiteral $typed) + '~' }
    $what = if ($typed) { " typed=[$typed] keys=[$keys]" } else { ' typed=[]' }
    if ($dryRun) {
        Log "WOULD-SEND flag=$($flag.file.Name) leaf=$($flag.leaf) why=$why$what"
    } else {
        [System.Windows.Forms.SendKeys]::SendWait($keys)
        Log "SENT flag=$($flag.file.Name) leaf=$($flag.leaf) why=$why$what"
        # Its own event, never merged with the extension path. This is the
        # FOREGROUND send: it reaches whichever window has focus, which on
        # 2026-09-18 was a session that had not asked for anything. A delivery
        # whose target is presentation rather than identity is the one most worth
        # a durable record, and it was the one with none. Merging the two names
        # would leave the ledger unable to say which path typed.
        Write-LedgerRow $flag.sid 'foreground_dispatched' "legacy foreground SendKeys typed into the FOCUSED window (CPP_LEGACY_FOREGROUND_SENDKEYS=1); why=$why"
    }
    Remove-Item -LiteralPath $flag.file.FullName -Force -ErrorAction SilentlyContinue
}

# --- Terminal inbox (2026-09-18): type into the session's OWN terminal ----------
# SendKeys reaches only the foreground window. The PP Sessions extension (>= 0.4.0)
# running in the Cursor window that hosts the session types with terminal.sendText,
# no focus needed. This daemon resolves session -> claude.exe (procStart-checked)
# -> ancestor pids and writes <sid>.req.json; the extension answers <sid>.ack.json
# with sent | deferred | refused (rules in extension/src/terminal_inbox.js).
# No answer within $ackFirstSec = no extension listening -> foreground fallback.
$inboxDir    = if ($env:AC_INBOX_DIR) { $env:AC_INBOX_DIR } else { Join-Path $env:USERPROFILE '.claude\state\terminal-inbox' }
$sessionsDir = if ($env:AC_SESSIONS_DIR) { $env:AC_SESSIONS_DIR } else { Join-Path $env:USERPROFILE '.claude\sessions' }
$ackFirstSec = 10
if ($env:AC_ACK_FIRST) { $ackFirstSec = [int]$env:AC_ACK_FIRST }
# Staleness budget for a request the owner has ACCEPTED but cannot act on yet.
# It is NOT the silence budget -- that is $ackFirstSec above, and it stays at 10 s.
#
# MEASURED 2026-09-19 (session 37cfb187, the first live /cpp-gsd-long crossing):
#   22:39:47.82  REQUESTED  typed=[/compact focus on ...]
#   22:39:47.87  deferred by extension  reason=status-busy   <- owner answered in 50 ms
#   22:40:48.15  REFUSED    by extension  reason=expired     <- 60.3 s later
# The extension only types into a session whose status is exactly "idle"
# (terminal_inbox.js). A session is busy until its turn finishes, and the turn
# that emits the line finishes by running the Stop chain -- 11 hooks with a
# 300 s ceiling in settings.json, measured at 82 s on this host. So at 60 s the
# deadline was SHORTER THAN THE LATENCY OF THE STATE IT WAITS FOR, and no
# crossing could ever be delivered. That is why every armed run here reads
# UNPROVEN: not a routing bug, a unit mismatch between two numbers on one host.
#
# 300 s covers the Stop chain's own ceiling. Raising it is only safe because
# Poll-Inbox now WITHDRAWS the request as soon as the transcript stops ending on
# the line we asked to be typed -- staleness is bounded by the transcript, not
# by this clock (a clock can only ever guess at it).
$inboxTtlMs = 300000
if ($env:AC_INBOX_TTL) { $inboxTtlMs = [int]$env:AC_INBOX_TTL }
$inbox = @{}   # "<sid>|<flag mtime ticks>" -> @{ sid; id; state; at }

function Resolve-Session($sid) {
    if (-not $sid) { return $null }
    foreach ($f in @(Get-ChildItem -LiteralPath $sessionsDir -Filter '*.json' -File -ErrorAction SilentlyContinue)) {
        try { $s = Get-Content -LiteralPath $f.FullName -Raw | ConvertFrom-Json } catch { continue }
        if ([string]$s.sessionId -cne $sid) { continue }
        $p = Get-CimInstance Win32_Process -Filter "ProcessId=$([int]$s.pid)" -ErrorAction SilentlyContinue
        if (-not $p) { continue }
        $ft = $p.CreationDate.ToFileTimeUtc()
        $rec = [long]0
        # CIM drops the last FILETIME digit; a reused pid differs by far more than 10.
        if (-not [long]::TryParse([string]$s.procStart, [ref]$rec) -or [Math]::Abs($rec - $ft) -ge 10) { continue }
        $chain = @(); $cur = $p
        for ($i = 0; $i -lt 12 -and $cur; $i++) {
            $chain += [int]$cur.ProcessId
            $cur = Get-CimInstance Win32_Process -Filter "ProcessId=$([int]$cur.ParentProcessId)" -ErrorAction SilentlyContinue
        }
        return @{ pid = [int]$s.pid; procStart = [string]$ft; ancestors = $chain }
    }
    return $null
}

function Request-Inbox($fl, $line, $key) {
    $s = Resolve-Session $fl.sid
    if (-not $s) {
        Log "inbox: session $($fl.sid) not resolvable (no live claude.exe with matching procStart); foreground fallback"
        $script:inbox[$key] = @{ sid = $fl.sid; id = ''; state = 'fallback'; at = Get-Date }
        return
    }
    $id = [guid]::NewGuid().ToString('N')
    $req = [ordered]@{ id = $id; session_id = $fl.sid; text = $line; claude_pid = $s.pid; proc_start = $s.procStart;
                       ancestors = @($s.ancestors); created_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds(); ttl_ms = $inboxTtlMs }
    [void](New-Item -ItemType Directory -Force -Path $inboxDir)
    Remove-Item -LiteralPath (Join-Path $inboxDir "$($fl.sid).ack.json") -Force -ErrorAction SilentlyContinue
    $p = Join-Path $inboxDir "$($fl.sid).req.json"; $tmp = "$p.$PID.tmp"
    [IO.File]::WriteAllText($tmp, ($req | ConvertTo-Json -Compress), (New-Object Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $tmp -Destination $p -Force
    Log "REQUESTED flag=$($fl.file.Name) sid=$($fl.sid) pid=$($s.pid) ancestors=$($s.ancestors.Count) typed=[$line]"
    # `line` is kept so Poll-Inbox can re-verify the transcript still ends on the
    # exact text we asked to be typed, and withdraw the request when it does not.
    $script:inbox[$key] = @{ sid = $fl.sid; id = $id; state = 'pending'; at = Get-Date; line = $line;
                             pid = $s.pid; procStart = $s.procStart }
}

# --- Orca provider (2026-11-17) --------------------------------------------------
# Sessions hosted in an Orca X pane have no extension to answer, so every request was
# refused after $ackFirstSec. The daemon answers for them itself: the pane is the
# ORCA_TERMINAL_HANDLE in claude.exe's own environment, confirmed live (and on the same
# tab) by `orca terminal list`, and typed with `orca terminal send` -- no focus involved.
# It writes the same ack the extension writes, so Poll-Inbox's single path records it.
# No handle in the environment = not an Orca pane: the request is left to the extension.
$orcaOff = ($env:AC_ORCA_PROVIDER -eq 'off')
$orcaApp = if ($env:AC_ORCA_APP) { $env:AC_ORCA_APP } else {
    $d = Join-Path $env:LOCALAPPDATA 'Programs\orca'
    @('Orca X.exe', 'Orca.exe') | ForEach-Object { Join-Path $d $_ } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
$orcaCliJs = if ($env:AC_ORCA_CLI_JS) { $env:AC_ORCA_CLI_JS } elseif ($orcaApp) {
    Join-Path (Split-Path -Parent $orcaApp) 'resources\app.asar.unpacked\out\cli\index.js'
} else { '' }
$orcaEnterDelayMs = 250   # text and Enter apart, as the extension does (ENTER_DELAY_MS)

function Invoke-OrcaCli([string[]]$cliArgs) {
    $r = [AcOrcaCli]::Run($orcaApp, (@($orcaCliJs) + $cliArgs), 30000)
    if ($r[0] -eq '-1') { return @{ ok = $false; why = "cli-did-not-finish($($r[1]))" } }
    try { $j = $r[1] | ConvertFrom-Json } catch { return @{ ok = $false; why = "cli-output-unparseable(exit=$($r[0]))" } }
    if (-not $j.ok) { return @{ ok = $false; why = "cli-error($([string]$j.error.code))" } }
    return @{ ok = $true; result = $j.result }
}

function Write-InboxAck($e, $fields) {
    $ack = [ordered]@{ id = $e.id; session_id = $e.sid; provider = 'orca'; at_ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() }
    foreach ($k in $fields.Keys) { $ack[$k] = $fields[$k] }
    $p = Join-Path $inboxDir "$($e.sid).ack.json"; $tmp = "$p.$PID.tmp"
    [IO.File]::WriteAllText($tmp, ($ack | ConvertTo-Json -Compress), (New-Object Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $tmp -Destination $p -Force
}

function Get-OrcaSessionStatus($e) {
    $f = Join-Path $sessionsDir "$($e.pid).json"
    try { $s = Get-Content -LiteralPath $f -Raw | ConvertFrom-Json } catch { return @{ ok = $false; why = 'session-unreadable' } }
    if ([string]$s.sessionId -cne $e.sid) { return @{ ok = $false; why = 'session-mismatch' } }
    $rec = [long]0; $want = [long]0
    if (-not [long]::TryParse([string]$s.procStart, [ref]$rec) -or -not [long]::TryParse([string]$e.procStart, [ref]$want) -or
        [Math]::Abs($rec - $want) -ge 10) { return @{ ok = $false; why = 'proc-start-mismatch' } }
    return @{ ok = $true; status = [string]$s.status }
}

function Send-OrcaLine($handle, $line) {
    $first = Invoke-OrcaCli @('terminal', 'send', '--terminal', $handle, '--text', $line, '--enter', '--json')
    if (-not $first.ok) { return @{ ok = $false; why = "orca-send-failed:$($first.why)" } }
    if (-not $first.result.send.accepted) { return @{ ok = $false; why = 'orca-send-not-accepted' } }
    # The slash-command popup eats the first Enter; Enter on an empty prompt is a no-op (extension.js).
    Start-Sleep -Milliseconds $orcaEnterDelayMs
    $enters = 1
    if ((Invoke-OrcaCli @('terminal', 'send', '--terminal', $handle, '--enter', '--json')).ok) { $enters = 2 }
    $tail = ''
    if ($line -cmatch '^/compact\s+') {
        $tail = ($line -creplace '^/compact\s+', '').Trim()
        Start-Sleep -Milliseconds $orcaEnterDelayMs
        if ((Invoke-OrcaCli @('terminal', 'send', '--terminal', $handle, '--text', $tail, '--enter', '--json')).ok) { $enters++ }
    }
    return @{ ok = $true; enters = $enters; tail = $tail }
}

function Invoke-OrcaProvider($e) {
    if ($e.orca -eq 'none' -or $e.orca -eq 'done' -or -not $e.pid) { return }
    # Dry-run suites may be launched from an Orca pane: without an injected CLI they never reach Orca.
    if ($dryRun -and -not $env:AC_ORCA_APP) { $e.orca = 'none'; return }
    if ($null -eq $e.orca) {
        $h = [AcProcEnv]::Get([int]$e.pid, 'ORCA_TERMINAL_HANDLE')
        if (-not $h) { $e.orca = 'none'; return }
        $e.orca = @{ handle = $h; tab = [AcProcEnv]::Get([int]$e.pid, 'ORCA_TAB_ID') }
        Log "inbox: sid=$($e.sid) runs in Orca pane handle=$h tab=$($e.orca.tab)"
    }
    if ($e.orcaNext -and (Get-Date) -lt $e.orcaNext) { return }
    $e.orcaNext = (Get-Date).AddSeconds(2)
    $handle = $e.orca.handle
    $refuse = { param($why) $e.orca = 'done'; Write-InboxAck $e @{ status = 'refused'; reason = $why; terminal = "orca:$handle" } }

    if (-not $orcaApp -or -not (Test-Path -LiteralPath $orcaCliJs)) { & $refuse 'orca-cli-not-found'; return }
    $line = [string]$e.line
    if ($line.Length -eq 0 -or $line.Length -gt 512 -or $line -match '[\u0000-\u001f\u007f]') { & $refuse 'invalid-text'; return }
    $st = Get-OrcaSessionStatus $e
    # Claude Code rewrites this file constantly; a torn read is retried next tick, bounded by Poll-Inbox's limit.
    if (-not $st.ok -and $st.why -eq 'session-unreadable') { return }
    if (-not $st.ok) { & $refuse $st.why; return }
    if ($st.status -ne 'idle') {
        if ($e.state -ne 'deferred') { Write-InboxAck $e @{ status = 'deferred'; reason = "status-$($st.status)"; terminal = "orca:$handle" } }
        return
    }
    $list = Invoke-OrcaCli @('terminal', 'list', '--json')
    if (-not $list.ok) { & $refuse "orca-unreachable:$($list.why)"; return }
    $t = @($list.result.terminals | Where-Object { [string]$_.handle -ceq $handle })
    if ($t.Count -ne 1) { & $refuse 'orca-handle-not-live'; return }
    if ($e.orca.tab -and [string]$t[0].tabId -cne $e.orca.tab) { & $refuse 'orca-tab-mismatch'; return }
    if (-not $t[0].connected -or -not $t[0].writable) { & $refuse 'orca-terminal-not-writable'; return }

    $e.orca = 'done'
    $sent = Send-OrcaLine $handle $line
    if (-not $sent.ok) { Write-InboxAck $e @{ status = 'refused'; reason = $sent.why; terminal = "orca:$handle" }; return }
    Write-InboxAck $e @{ status = 'sent'; terminal = "orca:$handle"; enters = $sent.enters;
                         arg_tail = $(if ($sent.tail) { $sent.tail } else { $null }) }
}

function Poll-Inbox($flags) {
    foreach ($key in @($script:inbox.Keys)) {
        $e = $script:inbox[$key]
        if ($e.state -ne 'pending' -and $e.state -ne 'deferred') { continue }
        $mine = @($flags | Where-Object { "$($_.sid)|$($_.file.LastWriteTime.Ticks)" -eq $key })

        # Staleness is a property of the TRANSCRIPT, not of a clock. The request
        # says "type this line into the session whose last assistant line IS this
        # line"; the moment that stops being true the request describes a session
        # that has moved on, and typing it would submit into a turn nobody asked
        # for. Withdrawing here is what lets $inboxTtlMs be long enough to outlast
        # the Stop chain without widening the window in which a stale line could
        # land. A request nobody is deferring yet is withdrawn on the same rule.
        if ($mine.Count -gt 0 -and $e.line) {
            $now = Get-ExpectState $mine[0]
            if ($now.state -ne 'ok' -or $now.line -cne $e.line) {
                $e.state = 'withdrawn'
                Remove-Item -LiteralPath (Join-Path $inboxDir "$($e.sid).req.json") -Force -ErrorAction SilentlyContinue
                Log "inbox: WITHDRAWN sid=$($e.sid) -- last assistant line no longer the requested one (now state=$($now.state))"
                Write-LedgerRow $e.sid 'withdrawn' "terminal inbox withdrawn: transcript moved on before the owner went idle"
                continue
            }
        }

        if (-not $orcaOff) { Invoke-OrcaProvider $e }

        $ack = $null
        $ackP = Join-Path $inboxDir "$($e.sid).ack.json"
        if (Test-Path -LiteralPath $ackP) { try { $ack = Get-Content -LiteralPath $ackP -Raw | ConvertFrom-Json } catch {} }
        if ($ack -and [string]$ack.id -eq $e.id) {
            $st = [string]$ack.status
            $via = if ($ack.provider) { [string]$ack.provider } else { 'extension' }
            if ($st -eq 'sent') {
                $e.state = 'sent'
                # enters/arg_tail come from the ack the extension just wrote, and
                # from nowhere else: a second source could disagree with what was
                # actually typed, which is the whole thing this line exists to
                # witness. `<none>` when the field is absent -- an older extension
                # that does not report them must not read as "sent 0 Enters".
                #
                # WHY (2026-09-21). The /compact argument tail is submitted by a
                # build we do not own, so no unit test can say whether the popup
                # still eats the first Enter. The ack knows, and the ack file is
                # consumed the moment delivery completes (`flags left=0`), so the
                # 18:24 crossing could not answer the question afterwards. One
                # line per crossing, in a log that outlives the flag, is what
                # turns "no test says so" into a record that does.
                $ent = if ($null -ne $ack.enters) { [string]$ack.enters } else { '<none>' }
                $at = if ($ack.arg_tail) { [string]$ack.arg_tail } else { '<none>' }
                Log "SENT via=$via sid=$($e.sid) terminal=[$($ack.terminal)] window=[$($ack.window_cwd)] enters=$ent arg_tail=[$at]"
                # The ledger row is not a duplicate of the log line. Every FAILURE
                # path here ledgers (refused x2, withdrawn) and this success path
                # did not, so the ledger was structurally incapable of showing a
                # compact that worked: it could only ever answer "never delivered".
                # Measured 2026-09-23 -- a query for compact outcomes returned 26
                # requests and 0 deliveries and was believed, while this daemon's
                # own log held two SENT rows from the same day. A zero bounded by
                # the instrument's vocabulary is UNKNOWN, not evidence.
                # The event name mirrors resume_dispatched deliberately: one query
                # over the ledger must see both kinds, or the next reader repeats
                # the same wrong conclusion.
                Write-LedgerRow $e.sid 'compact_dispatched' "terminal inbox delivered via ${via}; terminal=[$($ack.terminal)] enters=$ent"
                foreach ($fl in $mine) { Remove-Item -LiteralPath $fl.file.FullName -Force -ErrorAction SilentlyContinue }
                continue
            }
            if ($st -eq 'refused') {
                $e.state = 'refused'
                Log "inbox: REFUSED by $via sid=$($e.sid) reason=$($ack.reason)"
                foreach ($fl in $mine) {
                    $dest = Join-Path $hooksDir ($fl.file.Name -replace '^auto-compact-(trigger|pending)', 'auto-compact-refused')
                    try { Move-Item -LiteralPath $fl.file.FullName -Destination $dest -Force -ErrorAction Stop } catch {}
                }
                Write-LedgerRow $e.sid 'refused' "terminal inbox refused: $($ack.reason)"
                continue
            }
            if ($st -eq 'deferred' -and $e.state -ne 'deferred') {
                $e.state = 'deferred'
                Log "inbox: deferred by $via sid=$($e.sid) reason=$($ack.reason)"
            }
        }
        $age = ((Get-Date) - $e.at).TotalSeconds
        $limit = if ($e.state -eq 'deferred') { $inboxTtlMs / 1000 + 10 } else { $ackFirstSec }
        if ($age -gt $limit) {
            $e.state = 'fallback'
            Remove-Item -LiteralPath (Join-Path $inboxDir "$($e.sid).req.json") -Force -ErrorAction SilentlyContinue
            Log "inbox: no extension answer in ${limit}s sid=$($e.sid); foreground fallback"
        }
    }
}

Log "daemon start ttl=${ttlSec}s tick=${tickMs}ms dry=$dryRun"
$deadline = (Get-Date).AddSeconds($ttlSec)
$blockedHwnd = ''

try {
    while ((Get-Date) -lt $deadline) {
        $flags = @(Get-Flags)
        if ($flags.Count -eq 0) { break }

        # Extension path first -- it does not care which window is in front.
        foreach ($fl in $flags) {
            if (-not $fl.sid) { continue }
            $key = "$($fl.sid)|$($fl.file.LastWriteTime.Ticks)"
            if ($inbox.ContainsKey($key)) { continue }
            $st = Get-ExpectState $fl
            if ($st.state -eq 'ok' -and $st.line) { Request-Inbox $fl $st.line $key }
        }
        Poll-Inbox $flags
        # Only flags nobody in the inbox is handling reach the foreground path.
        $flags = @($flags | Where-Object {
            $k = "$($_.sid)|$($_.file.LastWriteTime.Ticks)"
            (-not $_.sid) -or (-not $inbox.ContainsKey($k)) -or ($inbox[$k].state -eq 'fallback')
        } | Where-Object { Test-Path -LiteralPath $_.file.FullName })
        if ($flags.Count -eq 0) { Start-Sleep -Milliseconds $tickMs; continue }

        # Default (no opt-in): nothing below this point may type. A flag the
        # inbox gave up on, or one with no session id at all, is refused; a flag
        # still waiting for its expected line keeps waiting (stale -> refused).
        if (-not $legacyForeground) {
            foreach ($fl in $flags) {
                $k = "$($fl.sid)|$($fl.file.LastWriteTime.Ticks)"
                if (-not $fl.sid) { Refuse-NoExact $fl 'flag carries no session id' ; continue }
                if ($inbox.ContainsKey($k) -and $inbox[$k].state -eq 'fallback') {
                    Refuse-NoExact $fl 'no terminal-inbox provider answered or the session is not resolvable'
                    continue
                }
                $st = Get-ExpectState $fl
                if ($st.state -eq 'refuse') { Refuse-Flag $fl $st.why }
            }
            Start-Sleep -Milliseconds $tickMs
            continue
        }

        $fg = Get-Foreground
        if ($blockedHwnd -and $fg.hwnd -ne $blockedHwnd) { $blockedHwnd = '' }

        if ($fg.name -ine 'Cursor') {
            foreach ($fl in $flags | Where-Object { $_.isTrigger }) {
                $dest = Join-Path $hooksDir ($fl.file.Name -replace '^auto-compact-trigger', 'auto-compact-pending')
                try {
                    Move-Item -LiteralPath $fl.file.FullName -Destination $dest -Force -ErrorAction Stop
                    Log "trigger -> pending $($fl.file.Name) (fg=$($fg.name))"
                } catch { Log "demote failed $($fl.file.Name): $($_.Exception.Message)" }
            }
            Start-Sleep -Milliseconds $tickMs
            continue
        }

        if ($blockedHwnd) { Start-Sleep -Milliseconds $tickMs; continue }

        $ready = @()
        foreach ($fl in $flags) {
            $st = Get-ExpectState $fl
            if ($st.state -eq 'refuse') { Refuse-Flag $fl $st.why }
            elseif ($st.state -ne 'wait') {
                $fl | Add-Member -NotePropertyName typeLine -NotePropertyValue $st.line -Force
                $ready += $fl
            }
        }

        $root  = Get-Root $fg.title
        $roots = Get-OpenRoots
        $pick = $null; $why = ''
        $own = @($ready | Where-Object { $_.leaf -and $_.leaf -ieq $root })
        if ($own.Count -gt 0) {
            $pick = $own[0]; $why = 'title-match'
        }
        # The former `no-own-window` rule (type a flag whose project has no open
        # Cursor window into WHATEVER window is focused) is gone, even under the
        # legacy opt-in: it is the rule that sent /d1-continue for an Orca-hosted
        # session into a Cursor pane on 2026-09-18. Such a flag waits, then is
        # refused by the expect-line timeout.

        if ($pick) {
            try {
                Send-Enter $pick $why
                $blockedHwnd = $fg.hwnd
            } catch { Log "SendKeys failed: $($_.Exception.Message)" }
        }
        Start-Sleep -Milliseconds $tickMs
    }
} finally {
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
    $left = @(Get-Flags).Count
    Log "daemon exit; flags left=$left"
}
exit 0
