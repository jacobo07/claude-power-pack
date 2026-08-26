#!/usr/bin/env python3
"""V-TRAP-* -- knowledge that reaches the moment of use.

Every pattern here is already written down in CLAUDE.md or the vault, and
every one has still been re-issued by an agent that had read it. That is a
knowledge-EXECUTION failure, not a knowledge gap: prose must be recalled at
the instant a command is composed, and recall is exactly what fails under
context pressure. A pattern does not have to be remembered.

The suite also pins the coverage gap that makes half of this inert, so it
cannot quietly become a TODO.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

from modules.cascade_prevention.dangerous_cmds import (  # noqa: E402
    is_dangerous, trap_warnings)

HOOK = PP / "hooks" / "cascade_check_bash.js"
SETTINGS = Path.home() / ".claude" / "settings.json"

EXPECTED_GATES = 8
_passes = 0
_fails = 0


def _ok(g: str, e: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {g}: {e}")


def _fail(g: str, d: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {g}: {d}")


def main() -> int:
    print("V-TRAP -- correctness traps reach the command that trips them")

    # The exact shape that put a BOM in commit 9e69d11's subject line --
    # and then again in 86139cf, four days later, in the very commit whose
    # message recorded me reintroducing a different documented trap.
    #
    # RECURRENCE 2, and the sharpest evidence in this file for why the
    # coverage gap below is not cosmetic. At the moment 86139cf was
    # composed, this registry ALREADY held the pattern and ALREADY named
    # the correct fix. It matched the command that was about to run. It
    # never executed, because the chain carrying it is registered on the
    # matcher `Bash` and the command went through the PowerShell tool --
    # the tool this host's doctrine REQUIRES for git and python.
    #
    # Knowledge in executable form is still not protection if it is
    # attached to a surface where the command is never composed.
    hit = trap_warnings("Set-Content -Path x.txt -Value $b -Encoding utf8")
    if hit and "BOM" in hit[0]["trap"]:
        _ok("V-TRAP-BOM-CAUGHT", hit[0]["fix"][:58])
    else:
        _fail("V-TRAP-BOM-CAUGHT", f"got {hit}")

    # BOOKEND. The correct form must stay silent, or the trap is noise.
    if not trap_warnings(
            "[System.IO.File]::WriteAllText($p,$s,"
            "(New-Object System.Text.UTF8Encoding($false)))"):
        _ok("V-TRAP-BOOKEND-CORRECT-FORM-SILENT",
            "WriteAllText with UTF8Encoding($false) -> no warning")
    else:
        _fail("V-TRAP-BOOKEND-CORRECT-FORM-SILENT", "flagged the FIX")

    # Bare git in PowerShell; and the absolute-path form must not warn.
    bare = trap_warnings("git status --short")
    absolute = trap_warnings(r"& 'C:\Program Files\Git\cmd\git.exe' status")
    if bare and not absolute:
        _ok("V-TRAP-BARE-GIT", "bare git warns, absolute-path git does not")
    else:
        _fail("V-TRAP-BARE-GIT", f"bare={bool(bare)} absolute={bool(absolute)}")

    # Observed in THIS session: a truncating pipe reported exit -1 for a
    # script that exited 0.
    if trap_warnings("python tools/x.py | Select-Object -First 5"):
        _ok("V-TRAP-TRUNCATING-PIPE",
            "Select-Object -First on a native exe warns about $LASTEXITCODE")
    else:
        _fail("V-TRAP-TRUNCATING-PIPE", "not caught")

    # Severities stay separate. A correctness note must never read as a
    # destructive block, or the block stops meaning anything.
    trap_cmd = "Set-Content x -Encoding utf8"
    if not is_dangerous(trap_cmd) and trap_warnings(trap_cmd):
        _ok("V-TRAP-ADVISORY-NOT-BLOCK",
            "a correctness trap warns and does not enter the block registry")
    else:
        _fail("V-TRAP-ADVISORY-NOT-BLOCK",
              "a correctness trap leaked into the destructive registry")

    # The hook must accept PowerShell, or every PowerShell pattern in the
    # registry is unreachable by construction.
    src = HOOK.read_text(encoding="utf-8-sig")
    if re.search(r"\['Bash',\s*'PowerShell'\]", src):
        _ok("V-TRAP-HOOK-ACCEPTS-POWERSHELL",
            "cascade_check_bash.js checks both command surfaces")
    else:
        _fail("V-TRAP-HOOK-ACCEPTS-POWERSHELL",
              "the gate still accepts Bash only, so `Remove-Item -Recurse "
              "-Force` in the dangerous registry can never fire")

    # THE COVERAGE GAP, NAMED. The chain matcher is Owner-owned config this
    # repo cannot edit. Reported as a measured fact either way so it can
    # never decay into a silent TODO -- and it flips to PASS by itself the
    # moment the Owner widens the matcher.
    try:
        raw = SETTINGS.read_text(encoding="utf-8-sig")
        entry = re.search(
            r'"matcher"\s*:\s*"([^"]*)"(?:(?!"matcher").)*?'
            r'PreToolUse-Bash-chain', raw, re.S)
        matcher = entry.group(1) if entry else None
    except OSError as exc:
        matcher = None
        print(f"  (settings.json unreadable: {exc})")

    if matcher is None:
        _fail("V-TRAP-CHAIN-MATCHER-COVERS-POWERSHELL",
              "could not read the PreToolUse-Bash-chain matcher from "
              f"{SETTINGS} -- coverage is UNKNOWN, which is not the same "
              "as covered")
    elif "PowerShell" in matcher:
        _ok("V-TRAP-CHAIN-MATCHER-COVERS-POWERSHELL",
            f"matcher {matcher!r} routes PowerShell into the chain")
    else:
        _fail("V-TRAP-CHAIN-MATCHER-COVERS-POWERSHELL",
              f"matcher is {matcher!r}: the whole PreToolUse Bash chain, "
              "HR-CASCADE-002 included, never sees PowerShell. OWNER ACTION: "
              'change it to "Bash|PowerShell" in ~/.claude/settings.json -- '
              "the shape two sibling matchers in that file already use. This "
              "repo cannot edit Owner-owned config.")

    # THE SAME GAP, DISCOVERED RATHER THAN NAMED. The check above knows one
    # registration by name, so it can only ever find the one instance
    # someone remembered. Sweeping every shell-facing registration in the
    # config found FIVE, and the most consequential is not the chain at all:
    # `bug-hunter-ceps-bridge.js`, the CEPS producer, is registered
    # PostToolUse on `Bash`. Measured over the whole event store: 70 of 79
    # events are `bash:*`, ZERO come from a PowerShell surface, and the
    # store has never recorded a single failure from git, pytest, npm, node,
    # gh, mix or pnpm -- every one of which this host's doctrine requires be
    # run through PowerShell. The corpus describes the matcher, not the
    # estate. See T-CORPUS-DESCRIBES-ITS-INSTRUMENT-001.
    try:
        cfg = json.loads(SETTINGS.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        cfg = None
        print(f"  (settings.json unreadable: {exc})")

    if cfg is None:
        _fail("V-TRAP-SHELL-SURFACES-COVERED",
              "settings.json unreadable -- coverage UNKNOWN, which is not "
              "the same as covered")
    else:
        gaps = []
        for event, entries in (cfg.get("hooks") or {}).items():
            for m in entries:
                mt = str(m.get("matcher") or "")
                # Only registrations that CLAIM the shell surface: a
                # matcher naming Bash is asserting it inspects commands.
                if not re.fullmatch(r"[\w|]*Bash[\w|]*", mt):
                    continue
                if "PowerShell" in mt:
                    continue
                for h in m.get("hooks", []):
                    name = (h.get("command", "").replace("\\", "/")
                            .rstrip('"').split("/")[-1])
                    gaps.append(f"{event}/{name}")
        if not gaps:
            _ok("V-TRAP-SHELL-SURFACES-COVERED",
                "every Bash-matched registration also matches PowerShell")
        else:
            _fail("V-TRAP-SHELL-SURFACES-COVERED",
                  f"{len(gaps)} shell-facing registration(s) blind to "
                  f"PowerShell: {', '.join(sorted(gaps))}. OWNER ACTION: "
                  'widen each matcher to "Bash|PowerShell". The CEPS '
                  "producer among them is why the event store has zero "
                  "git/pytest/npm failures in its entire history.")

    total = _passes + _fails
    print(f"CORRECTNESS_TRAPS_PASS={_passes}/{total}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if total != EXPECTED_GATES:
        print(f"FAIL: {total} gates executed, {EXPECTED_GATES} declared")
        return 1
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
