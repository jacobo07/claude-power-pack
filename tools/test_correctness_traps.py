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

EXPECTED_GATES = 10
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


_SELF_REJECT = re.compile(
    r"tool_?[Nn]ame[^\n]{0,40}?!==?\s*['\"](?P<only>\w+)['\"]")


def _code_refuses(command: str, surface: str = "PowerShell") -> bool:
    """Does the hook this command runs reject `surface` in its own source?

    Three of the five Bash-matched registrations here answer yes, which is
    why "widen the matcher" is not a uniform fix: for those, a wider
    matcher would advertise a coverage the code declines to provide.
    Unreadable source answers False -- an unknown must not be reported as
    a stronger claim than it is.
    """
    scripts = [tok.strip('"\'') for tok in command.split()
               if tok.strip('"\'').lower().endswith(".js")]
    if not scripts:
        return False
    path = Path(scripts[-1])
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(m.group("only") != surface for m in _SELF_REJECT.finditer(text))


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

    # --- recurrence four, replayed from this session's own transcript ---
    # Verbatim commands this session issued AFTER writing that a known trap
    # recurring is an institutionalisation failure. Prose has to be recalled
    # at the moment of writing a command; a pattern does not.
    replay = [
        "& $g -C $wt push origin 'frontier28/session-2026-08-26:main' 2>&1",
        "& $py 'tools\\normalize_paths.py' --check 2>&1 | Select-Object -Last 10",
        "& 'C:\\Program Files\\Git\\cmd\\git.exe' status 2>&1",
    ]
    caught = [c for c in replay
              if any("NativeCommandError" in w["trap"]
                     for w in trap_warnings(c))]
    if len(caught) == len(replay):
        _ok("V-TRAP-NATIVE-STDERR-CAUGHT",
            f"all {len(replay)} verbatim commands from this session are now "
            "flagged; the rule was prose-only through four recurrences")
    else:
        _fail("V-TRAP-NATIVE-STDERR-CAUGHT",
              f"only {len(caught)}/{len(replay)} replayed commands caught")

    # Negative controls. A note on a surface this busy earns its place by
    # what it stays silent about; 2>&1 is ordinary and CORRECT in Bash, and
    # this registry is checked against Bash commands too.
    silent = [
        "Get-ChildItem -Path . 2>&1",
        "ls -la 2>&1 | grep foo",
        "& $py 'tools\\x.py' 2>$null",
        "& $g -C $wt log -1 --format='%h'",
    ]
    noisy = [c for c in silent
             if any("NativeCommandError" in w["trap"]
                    for w in trap_warnings(c))]
    if not noisy:
        _ok("V-TRAP-NATIVE-STDERR-BOOKEND",
            "a cmdlet redirect, a Bash redirect, 2>$null and a plain native "
            "call all stay silent -- the pattern is native-exe AND 2>&1, "
            "never the redirect alone")
    else:
        _fail("V-TRAP-NATIVE-STDERR-BOOKEND", f"false positives on: {noisy}")

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
              f"matcher is {matcher!r}: the PreToolUse Bash chain never sees "
              "PowerShell, which is 75.5% of command traffic on this host "
              "(11126 of 14744, measured 2026-08-27 over 98 transcripts). "
              "HR-CASCADE-002 IS among the guards going blind: the chain's "
              "last entry is cascade_check_bash.js, the sole live "
              "enforcement of HR-CASCADE-001..005, and it accepts both "
              "surfaces in its own code. It is matcher-blind, not "
              "code-blind, so widening this one matcher restores it. "
              "OWNER ACTION: python tools/migrate_capture_surface.py "
              "--apply. See PR-WIDEN-PER-REGISTRATION-001.")

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
                    cmd = h.get("command", "").replace("\\", "/")
                    name = cmd.rstrip('"').split("/")[-1]
                    # CORRECTED 2026-08-27. This gate used to end with
                    # "widen each matcher". Measured against the code behind
                    # each one, that advice is right for ONE of the five:
                    # the rest reject the surface in their own source with
                    # `tool_name !== 'Bash'`, so a wider matcher would put a
                    # coverage claim in settings.json that the code refuses.
                    # Naming a gap is not the same as naming its fix.
                    gaps.append(f"{event}/{name}"
                                + ("" if not _code_refuses(cmd)
                                   else " [code also self-rejects]"))
        if not gaps:
            _ok("V-TRAP-SHELL-SURFACES-COVERED",
                "every Bash-matched registration also matches PowerShell")
        else:
            matcher_only = [g for g in gaps if "self-rejects" not in g]
            _fail("V-TRAP-SHELL-SURFACES-COVERED",
                  f"{len(gaps)} shell-facing registration(s) blind to "
                  f"PowerShell: {', '.join(sorted(gaps))}. Of these, "
                  f"{len(matcher_only)} would be fixed by widening the "
                  "matcher alone; the rest need a code change first, and "
                  "widening those would assert a coverage the hook refuses "
                  "to honour. OWNER ACTION: "
                  "python tools/migrate_capture_surface.py --apply, which "
                  "widens only the registrations whose code accepts the "
                  "surface. See PR-WIDEN-PER-REGISTRATION-001.")

    total = _passes + _fails
    print(f"CORRECTNESS_TRAPS_PASS={_passes}/{total}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if total != EXPECTED_GATES:
        print(f"FAIL: {total} gates executed, {EXPECTED_GATES} declared")
        return 1
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
