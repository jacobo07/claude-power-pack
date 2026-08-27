"""V-SURFACE-* -- the migration must widen one registration, not five.

The obvious reading of "five hooks carry a Bash matcher on a PowerShell
host" is that five matchers are wrong. Measured against the hooks' own
code, exactly one should change, and one of the other four must NOT:
`PreToolUse-Bash-chain` carries windows-bash-bridge-guard.js, which blocks
git/mix/gh/npm via Bash precisely to force them onto PowerShell. Widening
that entry would block the surface the doctrine redirects to.

These gates pin every disposition against the real installed hooks, so a
later bulk widen cannot pass review by looking tidy.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

import tools.capture_liveness as cl  # noqa: E402
import tools.migrate_capture_surface as ms  # noqa: E402

EXPECTED_GATES = 10
_passes: list[str] = []
_fails: list[str] = []

HOOKS = Path.home() / ".claude" / "hooks"
PPH = PP / "hooks"
ZC = PP / "modules" / "zero-crash" / "hooks"


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  FAIL {gate}: {diagnostic}")


def _settings(matcher: str, command: str) -> Path:
    blob = {"hooks": {"PostToolUse": [
        {"matcher": matcher, "hooks": [{"command": command}]}]}}
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(blob, handle)
    handle.close()
    return Path(handle.name)


def main() -> int:
    original = cl.SETTINGS
    bridge_cmd = "node C:/Users/User/.claude/skills/claude-power-pack/hooks/bug-hunter-ceps-bridge.js"

    # --- the plan against a NARROW registration --------------------------
    cl.SETTINGS = _settings("Bash", bridge_cmd)
    actions = ms.plan()
    if len(actions) == 1 and actions[0]["marker"] == "bug-hunter-ceps-bridge.js":
        _ok("V-SURFACE-PLAN-SCOPE", "exactly one registration is planned")
    else:
        _fail("V-SURFACE-PLAN-SCOPE",
              f"planned {[a['marker'] for a in actions]}; a bulk widen would "
              "have included the bash-bridge guard")

    if actions and actions[0]["add"] == ["PowerShell"]:
        _ok("V-SURFACE-PLAN-ADDS", "adds exactly PowerShell")
    else:
        _fail("V-SURFACE-PLAN-ADDS",
              f"add list is {actions[0]['add'] if actions else None}")

    # --- idempotence: the fixed state plans nothing ----------------------
    cl.SETTINGS = _settings("Bash|PowerShell", bridge_cmd)
    if ms.plan() == []:
        _ok("V-SURFACE-IDEMPOTENT",
            "a widened registration plans no further change")
    else:
        _fail("V-SURFACE-IDEMPOTENT", "the migration would run twice")

    # --- guard 3: code that refuses the surface, measured on real hooks --
    for name, path in (("bug-hunter-learning.js", HOOKS / "bug-hunter-learning.js"),
                       ("osa_deploy_detector.js", PPH / "osa_deploy_detector.js")):
        if not path.is_file():
            _fail(f"V-SURFACE-SELFREJECT-{name.split('.')[0].upper()}",
                  f"{path} absent -- disposition unverifiable")
            continue
        if ms.self_rejects(path, "PowerShell"):
            _ok(f"V-SURFACE-SELFREJECT-{name.split('.')[0].upper()}",
                f"{name} hard-rejects non-Bash in code; a wider matcher "
                "would buy nothing")
        else:
            _fail(f"V-SURFACE-SELFREJECT-{name.split('.')[0].upper()}",
                  f"{name} no longer self-rejects -- re-evaluate its "
                  "disposition, it may now be widenable")

    bridge_src = PPH / "bug-hunter-ceps-bridge.js"
    if not ms.self_rejects(bridge_src, "PowerShell"):
        _ok("V-SURFACE-BRIDGE-ACCEPTS",
            "the bridge does NOT self-reject PowerShell -- widening it works")
    else:
        _fail("V-SURFACE-BRIDGE-ACCEPTS",
              "the bridge refuses the surface the migration would add")

    # --- the KEEP dispositions, pinned -----------------------------------
    if "tty-restore.js" not in ms.CANDIDATES:
        _ok("V-SURFACE-KEEP-TTY",
            "tty-restore stays narrow: the focus-reporting leak is a Bash "
            "bridge artefact, not a PowerShell one")
    else:
        _fail("V-SURFACE-KEEP-TTY", "an intentionally narrow hook was enrolled")

    guard = HOOKS / "windows-bash-bridge-guard.js"
    if "hook-dispatcher.js" not in ms.CANDIDATES and guard.is_file():
        _ok("V-SURFACE-KEEP-BASH-CHAIN",
            "PreToolUse-Bash-chain stays narrow: it carries the guard that "
            "blocks git/npm via Bash to force them onto PowerShell")
    else:
        _fail("V-SURFACE-KEEP-BASH-CHAIN",
              "the chain that redirects TO PowerShell is enrolled for "
              "widening, or its guard has moved")

    # --- guard 1 is a real bound, not decoration -------------------------
    if len(ms.CANDIDATES) == 1:
        _ok("V-SURFACE-CANDIDATES-BOUNDED",
            f"allow-list holds exactly {sorted(ms.CANDIDATES)}")
    else:
        _fail("V-SURFACE-CANDIDATES-BOUNDED",
              f"allow-list grew to {sorted(ms.CANDIDATES)} -- each addition "
              "needs its own evidence")

    # --- a non-candidate is never planned, however narrow ----------------
    cl.SETTINGS = _settings("Bash", "node C:/x/tty-restore.js")
    if ms.plan() == []:
        _ok("V-SURFACE-NONCANDIDATE-IGNORED",
            "a narrow non-candidate is left alone")
    else:
        _fail("V-SURFACE-NONCANDIDATE-IGNORED", "the allow-list did not bound")

    cl.SETTINGS = original
    ran = len(_passes) + len(_fails)
    print(f"\nSURFACE_PASS={len(_passes)}/{ran}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if ran != EXPECTED_GATES:
        print(f"GATE COUNT MISMATCH: {ran} ran, {EXPECTED_GATES} expected")
        return 1
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
