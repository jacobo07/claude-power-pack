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
        $leaf = ''; $sid = ''; $tr = ''; $eLine = ''; $ePrefix = ''
        try {
            $p = Get-Content -LiteralPath $f.FullName -Raw | ConvertFrom-Json
            if ($p.cwd) { $leaf = Split-Path -Leaf ([string]$p.cwd).TrimEnd('\', '/') }
            if ($p.session_id) { $sid = [string]$p.session_id }
            if ($p.transcript) { $tr = [string]$p.transcript }
            if ($p.expect_line) { $eLine = [string]$p.expect_line }
            if ($p.expect_prefix) { $ePrefix = [string]$p.expect_prefix }
        } catch {}
        $out += [pscustomobject]@{ file = $f; leaf = $leaf; isTrigger = ($f.Name -like 'auto-compact-trigger*');
                                   sid = $sid; transcript = $tr; expectLine = $eLine; expectPrefix = $ePrefix }
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
function Get-ExpectState($fl) {
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

function Refuse-Flag($fl) {
    $dest = Join-Path $hooksDir ($fl.file.Name -replace '^auto-compact-(trigger|pending)', 'auto-compact-refused')
    try { Move-Item -LiteralPath $fl.file.FullName -Destination $dest -Force -ErrorAction Stop } catch {}
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
    $script:inbox[$key] = @{ sid = $fl.sid; id = $id; state = 'pending'; at = Get-Date; line = $line }
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

        $ack = $null
        $ackP = Join-Path $inboxDir "$($e.sid).ack.json"
        if (Test-Path -LiteralPath $ackP) { try { $ack = Get-Content -LiteralPath $ackP -Raw | ConvertFrom-Json } catch {} }
        if ($ack -and [string]$ack.id -eq $e.id) {
            $st = [string]$ack.status
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
                Log "SENT via=extension sid=$($e.sid) terminal=[$($ack.terminal)] window=[$($ack.window_cwd)] enters=$ent arg_tail=[$at]"
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
                Write-LedgerRow $e.sid 'compact_dispatched' "terminal inbox delivered via extension; terminal=[$($ack.terminal)] enters=$ent"
                foreach ($fl in $mine) { Remove-Item -LiteralPath $fl.file.FullName -Force -ErrorAction SilentlyContinue }
                continue
            }
            if ($st -eq 'refused') {
                $e.state = 'refused'
                Log "inbox: REFUSED by extension sid=$($e.sid) reason=$($ack.reason)"
                foreach ($fl in $mine) {
                    $dest = Join-Path $hooksDir ($fl.file.Name -replace '^auto-compact-(trigger|pending)', 'auto-compact-refused')
                    try { Move-Item -LiteralPath $fl.file.FullName -Destination $dest -Force -ErrorAction Stop } catch {}
                }
                Write-LedgerRow $e.sid 'refused' "terminal inbox refused: $($ack.reason)"
                continue
            }
            if ($st -eq 'deferred' -and $e.state -ne 'deferred') {
                $e.state = 'deferred'
                Log "inbox: deferred by extension sid=$($e.sid) reason=$($ack.reason)"
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
                if ((Get-ExpectState $fl).state -eq 'refuse') { Refuse-Flag $fl }
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
            if ($st.state -eq 'refuse') { Refuse-Flag $fl }
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
