#!/usr/bin/env python3
"""V-RESTART-* -- the properties that keep /restart fast, and legible to PS 5.1.

Origin (2026-09-15, measured on this host). /restart took roughly 5.1-6.2 s
before it did anything the Owner could see. The breakdown:

    powershell -NoProfile cold start          697 ms
    CIM parent-chain walk, one query per hop ~1400 ms
    Get-WrapperPid, two more CIM queries      900 ms
    git branch --show-current                 564 ms
    Add-Type P/Invoke via csc.exe        865-1745 ms
    Start-Sleep settle                        250 ms

Three of those were avoidable and two were being paid for nothing:

  * claude.exe already exports CLAUDE_PID into every tool subprocess, so the
    chain walk rediscovered a number that was sitting in the environment.
  * the branch name is one line of .git/HEAD, not a process spawn.
  * the CONIN$ injection the Add-Type block exists for does NOT reach claude
    under Cursor's ConPTY -- the script has said so in a comment since
    2026-07-01, right above the watchdog that actually ends the process. The
    compile was on the critical path to attempt something known not to work
    in this terminal.

These gates are STATIC. A wall-clock assertion would be a coin flip on a busy
host -- this session measured the same dry run at 2870, 5335 and 3580 ms with
no code change in between -- so what is pinned here is the SHAPE that produced
the speed, not a duration. Timing belongs in a report, not in a gate that has
to stay green on a loaded laptop.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT = Path.home() / ".claude" / "scripts" / "restart-claude.ps1"

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate}  {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}  {diagnostic}")


def main() -> int:
    print("== V-RESTART speed/legibility gates ==")

    if not SCRIPT.exists():
        _fail("V-RESTART-SCRIPT-EXISTS", f"{SCRIPT} absent")
        print(f"RESTART_SPEED_PASS={_passes}/{_passes + _fails}")
        return 1
    _ok("V-RESTART-SCRIPT-EXISTS", str(SCRIPT))

    raw = SCRIPT.read_bytes()
    text = raw.decode("utf-8", errors="replace")

    # ---- V-RESTART-ASCII-ONLY ---------------------------------------------
    # The file's own header declares ASCII-ONLY (BL-2026-05-24) and carried a
    # section sign four lines above that declaration from its first revision.
    # PS 5.1 reads a .ps1 in the ANSI/OEM codepage, and a stray high byte
    # mis-tokenizes as a parse error reported somewhere else entirely.
    offenders = [(i, b) for i, b in enumerate(raw) if b > 127]
    if not offenders:
        _ok("V-RESTART-ASCII-ONLY", f"{len(raw)} bytes, all < 0x80")
    else:
        where = ", ".join(f"offset {i} (0x{b:02X})" for i, b in offenders[:5])
        _fail("V-RESTART-ASCII-ONLY", f"{len(offenders)} high bytes: {where}")

    # ---- V-RESTART-ASCII-SWEEP-CAN-FAIL -----------------------------------
    # Positive control. A sweep that matched nothing would report the same
    # clean bill as a healthy file, so prove the predicate detects a high byte.
    probe = "# Session Safety Contract §1".encode("utf-8")
    if [b for b in probe if b > 127]:
        _ok("V-RESTART-ASCII-SWEEP-CAN-FAIL", "predicate flags a synthetic high byte")
    else:
        _fail("V-RESTART-ASCII-SWEEP-CAN-FAIL", "the sweep cannot see a high byte at all")

    # ---- V-RESTART-USES-ENV-PID -------------------------------------------
    if "CLAUDE_PID" in text:
        _ok("V-RESTART-USES-ENV-PID", "claude pid read from the environment")
    else:
        _fail("V-RESTART-USES-ENV-PID",
              "no CLAUDE_PID -- the chain walk is back, ~1.4 s per invocation")

    # ---- V-RESTART-ENV-PID-CORROBORATED -----------------------------------
    # Trusting the env var blindly would act on a recycled pid. The fast path
    # is only sound because it re-checks the process is alive and is claude.
    # Anchor on the CODE spelling ($env:CLAUDE_PID), not the bare token. The
    # first version searched for "CLAUDE_PID" and landed in the comment block
    # that explains the change, so its 400-char window held prose and the gate
    # reported a missing guard that was present ten lines below. An aperture
    # defect in the instrument reads exactly like a defect in the subject.
    m = re.search(r"\$env:CLAUDE_PID.{0,400}", text, re.S)
    window = m.group(0) if m else ""
    if "Get-Process" in window and "claude" in window:
        _ok("V-RESTART-ENV-PID-CORROBORATED", "pid checked alive and named before use")
    else:
        _fail("V-RESTART-ENV-PID-CORROBORATED",
              "env pid used without corroboration -- a recycled pid would be killed")

    # ---- V-RESTART-NO-PER-HOP-CIM -----------------------------------------
    # The fallback must not go back to one query per hop: a single query costs
    # ~515 ms here, a bulk query ~465 ms for every process on the box.
    per_hop = re.search(r'while\s*\(\s*\$cur[^}]{0,400}Get-CimInstance', text, re.S)
    if not per_hop:
        _ok("V-RESTART-NO-PER-HOP-CIM", "no CIM query inside the walk loop")
    else:
        _fail("V-RESTART-NO-PER-HOP-CIM", "a CIM query is back inside the parent-chain loop")

    # ---- V-RESTART-NO-GIT-SPAWN -------------------------------------------
    if "branch --show-current" not in text:
        _ok("V-RESTART-NO-GIT-SPAWN", "branch read from .git/HEAD, not a process spawn")
    else:
        _fail("V-RESTART-NO-GIT-SPAWN", "git is spawned again for a descriptive field (564 ms)")

    # ---- V-RESTART-ADDTYPE-GATED ------------------------------------------
    # Add-Type must not be on the default path: csc.exe costs 865-1745 ms to
    # compile a mechanism this terminal does not deliver.
    # SECOND aperture defect in this file, and mutation caught it where reading
    # did not. The first version asked "does the TOKEN PP_RESTART_TRY_EXIT
    # appear before Add-Type" -- and that token also appears in the comment
    # block explaining the gate, so replacing the real guard with `if ($true)`
    # left the prose standing and the check passed. Ask instead whether the
    # guard EXPRESSION sits immediately above the compile: search backwards
    # from Add-Type over a bounded window, so nothing written ABOUT the
    # mechanism can stand in for the mechanism.
    # THIRD instance of the same mistake in one file, each caught by a control
    # rather than by reading it back: `find("Add-Type")` matched the sentence
    # above that SAYS "Add-Type compiles this C# through csc.exe", which sits
    # before the guard, so the clean file failed its own gate. Match the
    # INVOCATION (`Add-Type -Name`), which no prose here spells.
    inv = re.search(r"Add-Type\s+-Name", text)
    idx_add = inv.start() if inv else -1
    if idx_add < 0:
        _ok("V-RESTART-ADDTYPE-GATED", "no Add-Type invocation in the script at all")
    else:
        back = text[max(0, idx_add - 1200):idx_add]
        if re.search(r"\$env:PP_RESTART_TRY_EXIT\s+-eq\s+'1'", back):
            _ok("V-RESTART-ADDTYPE-GATED", "the guard expression stands above the compile")
        else:
            _fail("V-RESTART-ADDTYPE-GATED",
                  "no live opt-in guard above Add-Type -- csc.exe runs on every "
                  "/restart (865-1745 ms) for a path ConPTY does not deliver")

    # ---- V-RESTART-KEEPS-THE-KILL-GUARD -----------------------------------
    # The speed work must not have eaten the 2026-09-15 guard that refuses to
    # kill a pane with nothing to bring it back. Faster is not better if it
    # ends the session.
    # FOURTH instance of this file's own recurring mistake, and the one that
    # mattered most: asking whether the NAMES `hasResumeLoop` and `CANCELLED`
    # appear is satisfied by the assignment and by the dead branch's own text,
    # so replacing the branch with `if ($false)` left both in place and the
    # gate reported the safety property intact while /restart had become a
    # pure kill. Presence of a name is not liveness of a branch -- assert the
    # BRANCH, and require the refusal to sit inside it.
    m_guard = re.search(r"if\s*\(\s*-not\s+\$hasResumeLoop\s*\)\s*\{(.{0,1500}?)\n\}",
                        text, re.S)
    if m_guard and "CANCELLED" in m_guard.group(1) and "exit 0" in m_guard.group(1):
        _ok("V-RESTART-KEEPS-THE-KILL-GUARD",
            "the no-loop branch is live and returns before the kill")
    else:
        _fail("V-RESTART-KEEPS-THE-KILL-GUARD",
              "no live `-not $hasResumeLoop` branch that refuses and exits -- "
              "/restart would kill a pane with nothing to bring it back")

    total = _passes + _fails
    print(f"RESTART_SPEED_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
