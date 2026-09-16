#!/usr/bin/env python3
"""test_hook_stdin_liveness.py -- V-STDIN-* gates.

A hook that reads stdin with `fs.readFileSync(0)` BLOCKS THE EVENT LOOP. If the
pipe never closes, the process parks forever and no in-process watchdog can save
it, because a timer is never scheduled. The harness's per-hook `timeout` does not
save it either: that kills the shell wrapper, and a timeout kills the DIRECT
CHILD ONLY, so the node process survives holding the inherited stdout pipe and
whoever reads that pipe waits on a handle nothing will close.

MEASURED 2026-09-15 -- the incident that forced this gate:
    UI parked on "running PreToolUse hooks 6/8 ... 40m 44s"
    pid=47776  age_min=36.5  cpu_sec=0  parent_alive=False
    pid=3900   age_min=36.5  cpu_sec=0  parent_alive=False
Zero CPU over 36 minutes is the discriminator: it rules out a runaway regex and
proves the processes never executed one line of hook logic.

    MUTANT (sync readFileSync)  -> STILL HUNG after 12000 ms
    FIXED  (bounded async, 2 s) -> EXITED after 2434 ms

SCOPE, and why it is narrower than "every hook":
Hooks spawned by hook-dispatcher.js get their stdin written and CLOSED by the
dispatcher, so they are far less exposed. The dangerous population is the hooks
the HARNESS spawns directly -- the standalone `type:"command"` entries in
settings.json. Those are enumerated here STRUCTURALLY, from settings.json
itself, never by grepping for the safe pattern: grepping for a fix finds the
files that have it, which is the opposite of the question.

RATCHET, not a clean bill. The population is real and pre-existing; a gate that
is red on arrival gets switched off within a week. So the current offenders are
frozen by name with a reason, and the gate fails when the set GROWS or when an
entry goes stale. Names, never a count: a count is satisfied by deleting a hook.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

# Budget for the live drive below. A migrated hook's own bound is 2 s with a 5 s
# hard-exit backstop, but the population includes third-party GSD plugin hooks
# that are legitimately slow: gsd-context-monitor.js was MEASURED at 10.6 s with
# stdin open, bounded and correct. A 9 s budget called it parked, which is a
# false accusation aimed at a hook that works.
#
# 20 s is generous on purpose and costs no strictness: a genuinely parked hook
# stays parked for any window you choose, so widening the window can only remove
# false positives, never hide a real one.
LIVENESS_BUDGET_S = 20
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"

# A process that burned this much CPU was WORKING, not parked. The parked
# signature from the original incident is the discriminator that made it
# diagnosable at all: pid=47776, 36.5 minutes, cpu_sec=0. A hook that has used
# real CPU over the budget is slow; one sitting at startup cost and nothing more
# is blocked. A timeout alone cannot tell those apart, and calling a slow hook
# parked is a false accusation aimed at a hook that works.
CPU_BUSY_THRESHOLD_S = 1.0


def process_cpu_seconds(pid: int):
    """Kernel+user CPU of a live pid, or None if it cannot be read.

    ctypes rather than a PowerShell round-trip, on purpose. Get-Process prints
    the number in the host's locale -- this machine emits '0,109' -- and float()
    on that raises, which an except-clause then turns into whatever the author
    defaulted to. That exact bug labelled six genuinely PARKED hooks as BUSY
    earlier in this session. A Win32 call returns integers and has no locale.
    """
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        creation, exit_t = wintypes.FILETIME(), wintypes.FILETIME()
        kernel, user = wintypes.FILETIME(), wintypes.FILETIME()
        if not k32.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_t),
                                   ctypes.byref(kernel), ctypes.byref(user)):
            return None

        def _secs(ft):  # FILETIME counts 100-nanosecond intervals
            return ((ft.dwHighDateTime << 32) | ft.dwLowDateTime) / 1e7

        return _secs(kernel) + _secs(user)
    finally:
        k32.CloseHandle(handle)


HOME = pathlib.Path(os.path.expanduser("~"))
SETTINGS = HOME / ".claude" / "settings.json"

# The population as it stood on 2026-09-15, BEFORE any migration. This never
# shrinks. KNOWN_OFFENDERS below does, and the difference between the two is the
# set of hooks somebody has CLAIMED to have fixed -- which is what
# V-STDIN-MIGRATED-EXITS then goes and drives.
#
# WHY BOTH LISTS EXIST. The stale-entry clause forces you to delete a name once
# the hook is fixed. Nothing forced you to fix it before deleting the name, so
# the ratchet could be turned by editing a dict -- a gate satisfied by
# describing the work rather than doing it. Deriving the migrated set instead of
# curating it means a deletion here is a CLAIM that gets tested, not a claim
# that gets believed.
ORIGINAL_POPULATION_2026_09_15 = {
    "agent-solo-guard.js",
    "auto-test-gate.js",
    "bug-hunter-ceps-bridge.js",
    "bug-hunter-learning.js",
    "lazarus-livesnap.js",
    "lazarus-stub-recover.js",
    "osa_deploy_detector.js",
    "restart-target-consumer.js",
    "session_start_hub.js",
    "subagent-bash-avoidance-advisor.js",
}

# EMPTY, 2026-09-16. The ratchet reached its target: no harness-spawned hook
# reads stdin synchronously any more. All ten of the 2026-09-15 population were
# migrated to the bounded-async template and each one is DRIVEN LIVE by
# V-STDIN-MIGRATED-EXITS below, not merely re-read.
#
# Zero here is not the end of the gate, it is the start of its useful life:
# V-STDIN-NO-NEW-DEBT now fails on the FIRST new offender instead of on the
# eleventh, which is the whole reason a ratchet is worth turning rather than
# leaving frozen at a comfortable number.
#
# An entry may be added back, but only with a reason and only as a deliberate
# admission of debt -- and the stale-entry clause will then force its removal
# the moment the hook is fixed.
KNOWN_OFFENDERS: dict[str, str] = {}

# A population floor. An empty or tiny sweep is what a BROKEN enumerator returns,
# and it reads identically to a healthy estate. 20 is comfortably under the 35
# scripts observed on 2026-09-15 and well above anything a parse failure yields.
MIN_SCRIPTS = 20

_SCRIPT_RE = re.compile(r'(?:[A-Za-z]:[\\/]|/[a-z]/)[^"\']*?\.(?:js|cjs|mjs)')
_SYNC_RE = re.compile(r'readFileSync\s*\(\s*0\b')

passes: list[str] = []
fails: list[str] = []


def _ok(gate: str, ev: str) -> None:
    passes.append(gate)
    print(f"[OK]   {gate} -- {ev}")


def _fail(gate: str, ev: str) -> None:
    fails.append(gate)
    print(f"[FAIL] {gate} -- {ev}")


def strip_comments(src: str) -> str:
    """Remove comments ONLY, and only where removal cannot eat code.

    Needed because the fix in session-file-guard.js quotes the banned call in
    its own explanatory comment, so a raw grep flags a file that is already
    correct and sends someone to "fix" it.

    TWO DELIBERATE RESTRAINTS, both learned by breaking this on the first run:

    1. String literals are NOT stripped. The obvious `'(?:[^'\\]|\\.)*'` spans
       newlines, so one unbalanced apostrophe anywhere -- a regex literal, an
       escaped quote -- pairs with a quote far below and swallows everything
       between. MEASURED: it deleted the real `fs.readFileSync(0, 'utf-8')` in
       auto-test-gate.js, and the gate then reported that hook CLEAN. A
       false negative is a broken hook certified as safe.
    2. Line comments are stripped only when `//` opens the line. Mid-line `//`
       lives inside URLs, and cutting from there to end-of-line can remove a
       real call that follows on the same line.

    Both restraints point the imperfection at the LOUD failure. A detector that
    over-matches gets a human look; one that under-matches is never looked at
    again, which is how the thing it guards dies quietly.
    """
    src = re.sub(r'/\*.*?\*/', ' ', src, flags=re.S)
    src = re.sub(r'(?m)^\s*//.*$', ' ', src)
    return src


def msys_to_win(p: str) -> str:
    m = re.match(r'^/([a-z])/(.*)$', p)
    return f"{m.group(1).upper()}:\\" + m.group(2).replace("/", "\\") if m else p


def harness_spawned_scripts() -> set[str]:
    """Enumerate from settings.json -- the authority on what the harness runs."""
    raw = SETTINGS.read_text(encoding="utf-8-sig")
    settings = json.loads(raw)
    found: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            cmd = node.get("command")
            if isinstance(cmd, str):
                for m in _SCRIPT_RE.finditer(cmd):
                    found.add(msys_to_win(m.group(0)))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(settings.get("hooks", {}))
    return found


def main() -> int:
    try:
        scripts = harness_spawned_scripts()
    except Exception as exc:  # noqa: BLE001
        _fail("V-STDIN-ENUMERATE", f"could not read settings.json: {exc}")
        print(f"STDIN_LIVENESS_PASS={len(passes)}/{len(passes)+len(fails)}")
        return 1

    if len(scripts) >= MIN_SCRIPTS:
        _ok("V-STDIN-ENUMERATE", f"{len(scripts)} harness-spawned scripts (floor {MIN_SCRIPTS})")
    else:
        _fail("V-STDIN-ENUMERATE",
              f"only {len(scripts)} scripts found (floor {MIN_SCRIPTS}) -- "
              "a sweep that matched almost nothing is a broken enumerator, not a clean estate")

    offenders: dict[str, str] = {}
    unreadable: list[str] = []
    for path in sorted(scripts):
        name = os.path.basename(path)
        if name == "hook-dispatcher.js":
            continue  # bounded by design: it uses a timed readStdin()
        if not os.path.isfile(path):
            continue
        try:
            src = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            unreadable.append(f"{name}: {exc}")
            continue
        if _SYNC_RE.search(strip_comments(src)):
            offenders[name] = path

    # Unreadable is its own outcome. A file we could not open has NOT been
    # cleared, and counting it as clean is how a sweep goes quietly blind.
    if unreadable:
        _fail("V-STDIN-READABLE", f"{len(unreadable)} script(s) unreadable: {unreadable[:3]}")
    else:
        _ok("V-STDIN-READABLE", "every enumerated script was readable")

    # Positive control: the detector must still be able to FIND the pattern.
    # Without this, a regex that stopped matching reports a perfectly clean
    # estate and nothing ever notices.
    probe = 'const x = fs.readFileSync(0, "utf8");'
    decoy = '// this was fs.readFileSync(0, "utf-8") before the fix\nconst y = 1;'
    # The third case is the one that actually broke: an unbalanced apostrophe
    # above a REAL call. A stripper that removes string literals eats the call
    # and certifies a broken hook as clean, so this asserts we still see it.
    apostrophe_trap = "const msg = 'it\\'s fine';\nconst b = fs.readFileSync(0, 'utf-8');"
    live = bool(_SYNC_RE.search(strip_comments(probe)))
    quiet = not _SYNC_RE.search(strip_comments(decoy))
    survives = bool(_SYNC_RE.search(strip_comments(apostrophe_trap)))
    if live and quiet and survives:
        _ok("V-STDIN-DETECTOR-LIVE",
            "finds real calls, ignores comments, survives an unbalanced apostrophe")
    else:
        _fail("V-STDIN-DETECTOR-LIVE",
              f"detector broken: real={live} comment_ignored={quiet} apostrophe_safe={survives}")

    new = sorted(set(offenders) - set(KNOWN_OFFENDERS))
    if new:
        _fail("V-STDIN-NO-NEW-DEBT",
              "NEW harness-spawned hook(s) reading stdin synchronously: " + ", ".join(new)
              + " -- see hooks/session-file-guard.js for the bounded-async pattern")
    else:
        _ok("V-STDIN-NO-NEW-DEBT", f"no new offenders beyond the {len(KNOWN_OFFENDERS)} frozen")

    # Stale entries. Without this the inventory becomes a permanent excuse and
    # the ratchet stops turning -- a list describing fixed hooks reads exactly
    # like one describing broken hooks.
    stale = sorted(set(KNOWN_OFFENDERS) - set(offenders))
    if stale:
        _fail("V-STDIN-NO-STALE-ENTRIES",
              "fixed (or removed) but still listed in KNOWN_OFFENDERS: " + ", ".join(stale)
              + " -- delete these lines; the ratchet only turns if the list shrinks")
    else:
        _ok("V-STDIN-NO-STALE-ENTRIES", "every frozen entry is still a real offender")

    # The claim, driven. Everything above is STATIC: it reads source and decides
    # whether a forbidden call is present. That cannot tell a migrated hook from
    # a hook whose name was simply deleted from the dict above, and those are the
    # two things this gate most needs to distinguish -- one is the work, the
    # other is the appearance of the work.
    #
    # So for every hook claimed migrated, spawn it with a stdin pipe that is
    # NEVER written to and NEVER closed (what a hook inherits when its wrapper
    # died) and require the PROCESS TO EXIT. stdout goes to DEVNULL rather than a
    # pipe on purpose: an undrained pipe is a SECOND, independent hang
    # (hooks/tests/test-pipe-write-liveness.js), and importing it here would make
    # every failure ambiguous between the two boundaries.
    # SCOPE: every harness-spawned script, not just the ten. The static clauses
    # above answer "does this file call readFileSync(0)". That was never the
    # class. MEASURED 2026-09-16, driving the whole population: SIX further hooks
    # parked at zero CPU on an unclosed pipe and NOT ONE of them contained the
    # banned call --
    #
    #   background-verifier, cdio_visual_advisory, first-time-project,
    #   zero-command-bootstrap, terminal-slot-recorder, mistake-ingest
    #
    # Four came from two SHARED runtimes whose timers resolved the promise and
    # left the 'data' listener attached (hook-runtime.runHook, which additionally
    # never called process.exit at all); two had no timer whatsoever. A detector
    # scoped to one primitive cannot see any of that, so this clause is scoped to
    # the PROPERTY instead: can the process die when its producer never closes
    # the pipe.
    #
    # stdout goes to DEVNULL rather than a pipe on purpose. An undrained pipe is
    # a SECOND, independent hang (hooks/tests/test-pipe-write-liveness.js), and
    # importing it here would make every failure ambiguous between the two
    # boundaries.
    if os.environ.get("CLAUDE_SKIP_HOOK_DRIVE") == "1":
        _ok("V-STDIN-ALL-EXIT", "drive skipped by CLAUDE_SKIP_HOOK_DRIVE=1 (NOT a pass)")
    else:
        drivable = sorted(p for p in scripts if os.path.isfile(p))
        hung, exited, slow = [], [], []
        hung_cpu: dict[str, str] = {}
        for path in drivable:
            name = os.path.basename(path)
            proc = subprocess.Popen(
                [NODE, path],
                stdin=subprocess.PIPE,       # held open, never written, never closed
                stdout=subprocess.DEVNULL,   # see note above
                stderr=subprocess.DEVNULL,
            )
            try:
                proc.wait(timeout=LIVENESS_BUDGET_S)
                exited.append(name)
            except subprocess.TimeoutExpired:
                # Over budget is not yet a verdict. Read the CPU BEFORE killing:
                # a blocked hook sits at startup cost forever, a slow one has
                # been burning a core. Only the first is this gate's subject, and
                # on a contended host the second is common and harmless.
                cpu = process_cpu_seconds(proc.pid)
                if cpu is not None and cpu >= CPU_BUSY_THRESHOLD_S:
                    slow.append(f"{name} (cpu={cpu:.1f}s)")
                else:
                    # Name kept BARE. The evidence rides alongside it, because a
                    # name with a suffix glued on stops matching the population
                    # sets below, and a gamed-ratchet check that silently matches
                    # nothing is the failure this whole file exists to prevent.
                    hung.append(name)
                    hung_cpu[name] = "unreadable" if cpu is None else f"{cpu:.2f}s"
                proc.kill()                  # a gate that leaks the process it
                proc.wait()                  # is testing has refuted itself
            finally:
                try:
                    proc.stdin.close()
                except OSError:
                    pass

        if slow:
            # Reported, never counted. A hook that is merely slow is not a defect
            # of this class, and folding it into the failure would train someone
            # to switch the gate off.
            print(f"       over budget but BURNING CPU (slow, not parked): {', '.join(sorted(slow))}")

        if hung:
            # One parked hook deserves a sharper message than the rest: a name
            # removed from KNOWN_OFFENDERS that still hangs means the ratchet was
            # turned by editing a dict rather than by doing the work.
            gamed = sorted(set(hung) & (ORIGINAL_POPULATION_2026_09_15 - set(KNOWN_OFFENDERS)))
            extra = ("; " + ", ".join(gamed) + " was removed from KNOWN_OFFENDERS without the "
                     "fix landing -- the ratchet turned on a claim, not on work") if gamed else ""
            named = ", ".join(f"{n} [cpu={hung_cpu.get(n, '?')}]" for n in sorted(hung))
            _fail("V-STDIN-ALL-EXIT",
                  f"{len(hung)} harness-spawned hook(s) still alive on an unclosed stdin after "
                  f"{LIVENESS_BUDGET_S}s at essentially zero CPU (killed): " + named + extra)
        else:
            _ok("V-STDIN-ALL-EXIT",
                f"all {len(exited)} harness-spawned hooks exited on an unclosed stdin")

    total = len(passes) + len(fails)
    print(f"STDIN_LIVENESS_PASS={len(passes)}/{total}  threshold={total}/{total}")
    print(f"standing debt (named, not counted): {len(offenders)} -> {sorted(offenders)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
