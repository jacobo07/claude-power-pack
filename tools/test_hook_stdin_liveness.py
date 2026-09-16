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
# hard-exit backstop, so 9 s is comfortably past both. Generous on purpose: a
# hook that is genuinely hung stays hung for any window, so a wide one costs no
# strictness -- while a narrow one turns a contended host into a false accusation.
LIVENESS_BUDGET_S = 9
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"

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

# Frozen 2026-09-15. Each entry is a hook the HARNESS spawns directly that still
# reads stdin synchronously. Fixing one means DELETING its line here -- the
# stale-entry check below makes that mandatory rather than optional.
KNOWN_OFFENDERS = {
    "auto-test-gate.js": "PostToolUse; lower blast radius, still harness-spawned. "
                         "Nearly dropped from this list by a stripper bug that ate its "
                         "real call -- the stale-entry clause is what surfaced it",
    "bug-hunter-learning.js": "advisory; safe to fix late",
    "lazarus-stub-recover.js": "SessionStart; a stall here delays session open",
    "session_start_hub.js": "SessionStart hub; measured 7374 ms with NO declared budget",
}

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
    claimed = sorted(ORIGINAL_POPULATION_2026_09_15 - set(KNOWN_OFFENDERS))
    if not claimed:
        _ok("V-STDIN-MIGRATED-EXITS", "nothing claimed migrated yet -- nothing to drive")
    else:
        by_name = {os.path.basename(p): p for p in scripts}
        hung, missing, exited = [], [], []
        for name in claimed:
            path = by_name.get(name)
            if not path or not os.path.isfile(path):
                missing.append(name)
                continue
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
                hung.append(name)
                proc.kill()                  # a gate that leaks the process it
                proc.wait()                  # is testing has refuted itself
            finally:
                try:
                    proc.stdin.close()
                except OSError:
                    pass

        if hung:
            _fail("V-STDIN-MIGRATED-EXITS",
                  "claimed migrated but STILL HANGS on an unclosed stdin: " + ", ".join(hung)
                  + f" (killed after {LIVENESS_BUDGET_S}s) -- the name was removed from "
                  "KNOWN_OFFENDERS without the fix landing, which is the ratchet being "
                  "turned by editing a dict")
        elif missing:
            _fail("V-STDIN-MIGRATED-EXITS",
                  "claimed migrated but not found among harness-spawned scripts: "
                  + ", ".join(missing) + " -- a hook that settings.json no longer names was "
                  "not fixed, it was unregistered; say which one it was")
        else:
            _ok("V-STDIN-MIGRATED-EXITS",
                f"{len(exited)} migrated hook(s) exited on an unclosed stdin: "
                + ", ".join(exited))

    total = len(passes) + len(fails)
    print(f"STDIN_LIVENESS_PASS={len(passes)}/{total}  threshold={total}/{total}")
    print(f"standing debt (named, not counted): {len(offenders)} -> {sorted(offenders)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
