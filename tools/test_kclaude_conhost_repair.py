"""V-KCLAUDE-REPAIR-* -- the launch-time dead-screen guard actually fires.

SUBJECT: ~/.claude/bin/repair-hook-wrappers.ps1 (the function) and
         ~/.claude/bin/kclaude.ps1 (the wiring that makes it reachable).

WHY THIS FILE EXISTS
--------------------
tools/test_conhost_hook_leak.py proves the PYTHON fixer unwraps correctly, on
synthetic fixtures, and that is right. tools/check_live_hook_wrappers.py proves
the LIVE registry is clean right now. Neither answers the question this one
does: **is the repair reached at launch**, so that a registry the installer
re-infects tomorrow is clean again before claude reads it.

That question is the one the estate keeps getting wrong. On 2026-09-13 the
repair was very nearly wired into C:\\Users\\User\\.claude\\kclaude.bat -- a
stale twin that launches nothing. The live chain, measured from the process
table, is:

    Cursor.exe -> cmd /K .claude\\bin\\kclaude.cmd
               -> powershell -NoProfile -File .claude\\bin\\kclaude.ps1
               -> claude.exe

A guard in the wrong launcher is indistinguishable from a guard that works,
until the screen goes blank again. So ORDERING inside the real kclaude.ps1 is
asserted here as a first-class gate, not left to inspection.

WHAT IS DRIVEN
--------------
The RED branch runs the REAL PowerShell function against an infected fixture and
requires it to come back clean. A test that re-implemented the unwrap in python
would pass while the shipped function was broken.

Controls, because an empty result is also what a broken harness produces:
  * POSCTRL   the fixture really was infected before the run (else RED is vacuous)
  * NEGCTRL   a CLEAN fixture is left byte-identical and reports no repair
  * PRESERVES the Orca hook is still registered afterwards (unwrap, never delete)
  * FAILOPEN  an absent path returns false rather than throwing

Exit 0 = all gates pass. Exit 1 = a gate failed. Exit 3 = the harness could not
run (PowerShell missing, subject files absent) -- NOT a pass, and not a defect
in the subject either.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
GUARD = HOME / ".claude" / "bin" / "repair-hook-wrappers.ps1"
KCLAUDE = HOME / ".claude" / "bin" / "kclaude.ps1"

PASSES: list[str] = []
FAILS: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    PASSES.append(gate)
    print(f"  [OK  ] {gate:<34s} {evidence}")


def _fail(gate: str, diag: str) -> None:
    FAILS.append(gate)
    print(f"  [FAIL] {gate:<34s} {diag}")


def _ps(script: str) -> subprocess.CompletedProcess:
    """Run a PowerShell snippet from a UTF-8 (no BOM) temp file.

    Never pipe a here-string to powershell -Command on this host: the BOM leaks
    into the first statement. A temp file with explicit encoding is the shape
    that does not fail.
    """
    fd, tmp = tempfile.mkstemp(suffix=".ps1", prefix="vkcr_")
    os.close(fd)
    Path(tmp).write_text(script, encoding="utf-8")
    try:
        return subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-File", tmp],
            capture_output=True, text=True, timeout=120,
        )
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


# --- fixtures ---------------------------------------------------------------

WRAPPED_ENTRY = {
    "type": "command",
    "command": "C:\\WINDOWS\\System32\\conhost.exe",
    "args": ["--headless", "C:\\WINDOWS\\System32\\cmd.exe", "/d", "/c",
             "%USERPROFILE%\\.orca\\agent-hooks\\claude-hook.cmd"],
    "timeout": 10,
}

CLEAN_ENTRY = {
    "type": "command",
    "command": "\"/c/Program Files/nodejs/node.exe\" \"C:/Users/User/.claude/hooks/x.js\"",
    "timeout": 5,
}


def _infected_settings() -> dict:
    return {
        "model": "opus[1m]",
        "hooks": {
            "PreToolUse": [{"matcher": "*", "hooks": [dict(WRAPPED_ENTRY)]}],
            "Stop": [{"hooks": [dict(CLEAN_ENTRY), dict(WRAPPED_ENTRY)]}],
        },
    }


def _clean_settings() -> dict:
    return {"model": "opus[1m]",
            "hooks": {"Stop": [{"hooks": [dict(CLEAN_ENTRY)]}]}}


def _count_wrapped(data: dict) -> int:
    n = 0
    for matchers in data.get("hooks", {}).values():
        for m in matchers:
            for e in m.get("hooks", []):
                if (isinstance(e, dict)
                        and str(e.get("command", "")).lower().endswith("conhost.exe")
                        and isinstance(e.get("args"), list)
                        and e["args"][:1] == ["--headless"]):
                    n += 1
    return n


def _drive(settings_path: Path) -> tuple[bool, str]:
    """Dot-source the SHIPPED guard and call the SHIPPED function."""
    script = (
        f". '{GUARD}'\n"
        f"$r = Repair-HookWrappers -SettingsPath '{settings_path}'\n"
        "if ($r) { Write-Output 'REPAIRED' } else { Write-Output 'NOOP' }\n"
    )
    cp = _ps(script)
    return ("REPAIRED" in cp.stdout), (cp.stdout + cp.stderr).strip()


# --- gates ------------------------------------------------------------------

def gate_syntax() -> None:
    for label, path in (("KCLAUDE", KCLAUDE), ("GUARD", GUARD)):
        script = (
            "$e = $null\n"
            f"[void][System.Management.Automation.Language.Parser]::ParseFile('{path}', [ref]$null, [ref]$e)\n"
            "if ($e -and $e.Count -gt 0) { $e | ForEach-Object { Write-Output $_.Message }; exit 1 }\n"
            "Write-Output 'PARSE_OK'\n"
        )
        cp = _ps(script)
        if "PARSE_OK" in cp.stdout:
            _ok(f"V-KCLAUDE-REPAIR-SYNTAX-{label}", f"{path.name} parses under PS 5.1")
        else:
            _fail(f"V-KCLAUDE-REPAIR-SYNTAX-{label}",
                  f"{path.name} has parse errors: {(cp.stdout + cp.stderr).strip()[:300]}")


def gate_wiring() -> None:
    """Reachability: the call must exist AND precede the launch."""
    src = KCLAUDE.read_text(encoding="utf-8-sig")

    # MEASURED 2026-09-13: the first version of this clause tested
    # `"repair-hook-wrappers.ps1" in src`, and a mutation that DELETED the
    # dot-source still passed it -- because the surviving line above assigns
    # that same filename to $wrapGuard. A filename mention is not an
    # invocation, and a check that a comment can satisfy could only ever
    # return one answer. Assert the dot-source OPERATOR against the variable
    # the launcher actually sources.
    dot_op = re.search(r"(?m)^\s*(?:if\b.*)?\.\s+\$wrapGuard\b", src) is not None
    assigns = re.search(r"\$wrapGuard\s*=.*repair-hook-wrappers\.ps1", src) is not None

    call_i = src.find("Repair-HookWrappers -ErrorAction SilentlyContinue")
    if call_i < 0:
        call_i = src.find("Repair-HookWrappers)")
    launch_i = src.find("& claude @launch")

    if dot_op and assigns:
        _ok("V-KCLAUDE-REPAIR-DOTSOURCED",
            "kclaude.ps1 dot-sources $wrapGuard, and $wrapGuard is the guard file")
    else:
        _fail("V-KCLAUDE-REPAIR-DOTSOURCED",
              f"dot_source_operator={dot_op} assigns_guard_path={assigns} "
              "-- a filename mention is not an invocation")

    if call_i >= 0 and launch_i >= 0 and call_i < launch_i:
        _ok("V-KCLAUDE-REPAIR-WIRED",
            f"call at char {call_i} precedes '& claude @launch' at {launch_i}")
    else:
        _fail("V-KCLAUDE-REPAIR-WIRED",
              f"call={call_i} launch={launch_i} -- guard does not precede the launch")

    # No second definition: two copies drift, and the gate would then be driving
    # a function the launcher does not use.
    if "function Repair-HookWrappers" not in src:
        _ok("V-KCLAUDE-REPAIR-SINGLE-DEF", "kclaude.ps1 holds no rival definition")
    else:
        _fail("V-KCLAUDE-REPAIR-SINGLE-DEF",
              "kclaude.ps1 defines its own Repair-HookWrappers -- two copies will drift")


def gate_red_branch(tmpdir: Path) -> None:
    """The load-bearing one: drive the REAL function against a real infection."""
    p = tmpdir / "infected.json"
    p.write_text(json.dumps(_infected_settings(), indent=2), encoding="utf-8")

    before = _count_wrapped(json.loads(p.read_text(encoding="utf-8-sig")))
    if before == 2:
        _ok("V-KCLAUDE-REPAIR-POSCTRL", f"fixture genuinely infected ({before} wrapped)")
    else:
        _fail("V-KCLAUDE-REPAIR-POSCTRL",
              f"fixture should hold 2 wrapped entries, holds {before} -- RED would be vacuous")
        return

    repaired, out = _drive(p)
    after_raw = p.read_text(encoding="utf-8-sig")
    after = _count_wrapped(json.loads(after_raw))

    if repaired and after == 0:
        _ok("V-KCLAUDE-REPAIR-RED", f"{before} wrapped -> 0 via the shipped function")
    else:
        _fail("V-KCLAUDE-REPAIR-RED",
              f"reported={repaired} wrapped_after={after} out={out[:200]}")

    # Unwrap, never delete: the Orca hook must still be registered afterwards.
    if "claude-hook.cmd" in after_raw and "cmd.exe" in after_raw:
        _ok("V-KCLAUDE-REPAIR-PRESERVES", "Orca hook still registered after unwrap")
    else:
        _fail("V-KCLAUDE-REPAIR-PRESERVES",
              "the repair DELETED the integration instead of unwrapping it")


def gate_bom(tmpdir: Path) -> None:
    """A BOM is ordinary on Windows; plain utf-8 chokes on it."""
    p = tmpdir / "infected_bom.json"
    p.write_text(json.dumps(_infected_settings(), indent=2), encoding="utf-8-sig")
    repaired, out = _drive(p)
    after = _count_wrapped(json.loads(p.read_text(encoding="utf-8-sig")))
    if repaired and after == 0:
        _ok("V-KCLAUDE-REPAIR-BOM", "BOM-prefixed registry repaired")
    else:
        _fail("V-KCLAUDE-REPAIR-BOM", f"reported={repaired} after={after} out={out[:200]}")


def gate_neg_control(tmpdir: Path) -> None:
    """Without a negative control, 'refuses everything' passes every RED case."""
    p = tmpdir / "clean.json"
    p.write_text(json.dumps(_clean_settings(), indent=2), encoding="utf-8")
    original = p.read_bytes()

    repaired, out = _drive(p)
    if not repaired and p.read_bytes() == original:
        _ok("V-KCLAUDE-REPAIR-NEGCTRL", "clean registry untouched, no repair reported")
    else:
        _fail("V-KCLAUDE-REPAIR-NEGCTRL",
              f"clean registry was modified or a repair was claimed (reported={repaired}) {out[:160]}")


def gate_fail_open(tmpdir: Path) -> None:
    missing = tmpdir / "does-not-exist.json"
    repaired, out = _drive(missing)
    if not repaired and "Exception" not in out and "not recognized" not in out:
        _ok("V-KCLAUDE-REPAIR-FAILOPEN", "absent registry -> false, no throw")
    else:
        _fail("V-KCLAUDE-REPAIR-FAILOPEN", f"reported={repaired} out={out[:200]}")


def main() -> int:
    print("=" * 72)
    print("test_kclaude_conhost_repair -- V-KCLAUDE-REPAIR")
    print(f"  guard   : {GUARD}")
    print(f"  launcher: {KCLAUDE}")

    for path in (GUARD, KCLAUDE):
        if not path.is_file():
            print(f"  [??  ] harness cannot run -- missing subject: {path}")
            print("KCLAUDE_REPAIR=UNKNOWN")
            return 3
    if os.name != "nt":
        print("  [??  ] harness cannot run -- PowerShell subject is Windows-only")
        print("KCLAUDE_REPAIR=UNKNOWN")
        return 3

    with tempfile.TemporaryDirectory(prefix="vkcr_") as td:
        tmpdir = Path(td)
        gate_syntax()
        gate_wiring()
        gate_red_branch(tmpdir)
        gate_bom(tmpdir)
        gate_neg_control(tmpdir)
        gate_fail_open(tmpdir)

    total = len(PASSES) + len(FAILS)
    print()
    print(f"KCLAUDE_REPAIR_PASS={len(PASSES)}/{total}  threshold={total}/{total}")
    if FAILS:
        print("FAILED: " + ", ".join(FAILS))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
