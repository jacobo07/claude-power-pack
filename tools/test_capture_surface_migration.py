"""V-SURFACE-* -- widen the registrations the CODE is ready for, not all five.

Five hooks carry a `Bash` matcher on a host whose doctrine routes python,
pytest, git, npm, node, mix and gh through PowerShell. The tempting fix is
to widen five matchers. Measured against the code behind each one, TWO
should change and three should not: two hooks reject non-Bash in their own
source, so a wider matcher would advertise a coverage the code declines to
honour, and one is narrow on purpose.

An earlier revision of this file asserted the opposite for the chain --
that widening `PreToolUse-Bash-chain` would BLOCK the surface the doctrine
redirects to, because it carries windows-bash-bridge-guard.js. Wrong twice:
that guard self-rejects non-Bash at its first line, and the chain's LAST
entry is cascade_check_bash.js, the sole live enforcement of
HR-CASCADE-001..005, which accepts both surfaces in code. The reading that
produced the error stopped before the end of the chain definition. The
disposition RULE was sound; the evidence behind one row was not.

These gates pin every disposition against the real installed hooks, so
neither a bulk widen nor a confident half-read can pass review.
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

    # CORRECTED. This gate used to assert the chain must stay narrow,
    # because it carries the guard that blocks git/npm via Bash. That guard
    # self-rejects non-Bash at its first line, so widening cannot affect it
    # -- and the chain's LAST entry is cascade_check_bash.js, the only live
    # enforcement of HR-CASCADE-001..005, which accepts both surfaces in
    # code and is inert on PowerShell solely because of this matcher.
    cascade = PP / "hooks" / "cascade_check_bash.js"
    accepts_both = cascade.is_file() and "'PowerShell'" in cascade.read_text(
        encoding="utf-8", errors="replace")
    if "PreToolUse-Bash-chain" in ms.CANDIDATES and accepts_both:
        _ok("V-SURFACE-WIDEN-BASH-CHAIN",
            "the chain is enrolled: cascade_check_bash.js accepts both "
            "surfaces in code, so HR-CASCADE-002 is matcher-blind, not "
            "code-blind")
    else:
        _fail("V-SURFACE-WIDEN-BASH-CHAIN",
              f"chain enrolled={'PreToolUse-Bash-chain' in ms.CANDIDATES}, "
              f"cascade guard accepts PowerShell={accepts_both} -- if the "
              "guard stopped accepting it, widening no longer suffices")

    # --- guard 1 is a real bound, not decoration -------------------------
    if len(ms.CANDIDATES) == 2:
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
