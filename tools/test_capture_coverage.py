"""V-COVERAGE-* -- registration presence is not registration coverage.

`capture_liveness.py` asked whether a producer's hook name appears anywhere
in settings.json. For `bug-hunter-ceps-bridge` it does, and the producer was
still blind to 75.5% of its subject: the entry carrying that name matched
`Bash`, while the hook's own source declares `Bash` AND `PowerShell` and host
doctrine routes python, pytest, git, npm, node, mix and gh through PowerShell.
Every prior rule in that gate reported healthy.

Every "rejects X" gate below is paired with an "admits Y" bookend. A detector
that can only say NO is indistinguishable from a broken one, and this file
exists because a check that could only say YES was indistinguishable from a
working one.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

import tools.capture_liveness as cl  # noqa: E402

EXPECTED_GATES = 14
_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  FAIL {gate}: {diagnostic}")


def _settings(matcher, command: str) -> str:
    """A minimal settings.json carrying one registration."""
    blob = {"hooks": {"PostToolUse": [
        {"matcher": matcher, "hooks": [{"command": command}]}]}}
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(blob, handle)
    handle.close()
    return handle.name


def _hook_src(surfaces: str) -> str:
    """A stand-in hook source declaring a COMMAND_TOOLS set."""
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".js", delete=False, encoding="utf-8")
    handle.write("'use strict';\nconst COMMAND_TOOLS = new Set([%s]);\n"
                 % surfaces)
    handle.close()
    return handle.name


def _spec(source: str | None, marker: str = "probe.js") -> dict:
    return {"hook_source": Path(source) if source else None,
            "hook_marker": marker}


def main() -> int:
    original = cl.SETTINGS

    # --- declared surfaces are DISCOVERED from source, never tabulated ---
    real = PP / "hooks" / "bug-hunter-ceps-bridge.js"
    got = cl.declared_surfaces(real)
    if got == {"Bash", "PowerShell"}:
        _ok("V-COVERAGE-DECLARED-FROM-SOURCE",
            f"the real bridge declares {sorted(got)}, read from its own code")
    else:
        _fail("V-COVERAGE-DECLARED-FROM-SOURCE",
              f"parsed {got}; a table would have said what someone remembered")

    if cl.declared_surfaces(Path(_hook_src(""))) is None:
        _ok("V-COVERAGE-DECLARED-EMPTY-IS-UNKNOWN",
            "an empty Set reads as undeterminable, not as zero surfaces")
    else:
        _fail("V-COVERAGE-DECLARED-EMPTY-IS-UNKNOWN", "empty parsed as a value")

    if cl.declared_surfaces(Path(_hook_src("")).with_suffix(".missing")) is None:
        _ok("V-COVERAGE-DECLARED-ABSENT", "an absent source is undeterminable")
    else:
        _fail("V-COVERAGE-DECLARED-ABSENT", "a missing file produced surfaces")

    # --- matcher parsing ------------------------------------------------
    cl.SETTINGS = Path(_settings("Bash", "node probe.js"))
    if cl.registration_surfaces("probe.js") == {"Bash"}:
        _ok("V-COVERAGE-MATCHER-SINGLE", "matcher 'Bash' matches exactly Bash")
    else:
        _fail("V-COVERAGE-MATCHER-SINGLE", "single matcher misparsed")

    cl.SETTINGS = Path(_settings("Bash|PowerShell", "node probe.js"))
    if cl.registration_surfaces("probe.js") == {"Bash", "PowerShell"}:
        _ok("V-COVERAGE-MATCHER-ALTERNATION",
            "an alternation is split into both surfaces")
    else:
        _fail("V-COVERAGE-MATCHER-ALTERNATION", "alternation misparsed")

    cl.SETTINGS = Path(_settings("*", "node probe.js"))
    if cl.registration_surfaces("probe.js") is None:
        _ok("V-COVERAGE-MATCHER-UNIVERSAL",
            "'*' is universal, distinct from an empty surface set")
    else:
        _fail("V-COVERAGE-MATCHER-UNIVERSAL", "wildcard not treated as universal")

    cl.SETTINGS = Path(_settings("Bash", "node somethingelse.js"))
    if cl.registration_surfaces("probe.js") == set():
        _ok("V-COVERAGE-MATCHER-ABSENT",
            "an unregistered marker matches nothing -- empty, not universal")
    else:
        _fail("V-COVERAGE-MATCHER-ABSENT", "absent marker did not read as empty")

    # --- THE BUG, replayed ----------------------------------------------
    both = _hook_src("'Bash', 'PowerShell'")
    cl.SETTINGS = Path(_settings("Bash", "node probe.js"))
    narrow = cl.coverage_of(_spec(both))
    if narrow["state"] == "NARROW" and narrow["uncovered"] == ["PowerShell"]:
        _ok("V-COVERAGE-NARROW-REJECTED",
            "declares Bash+PowerShell, matches Bash -> NARROW, names PowerShell")
    else:
        _fail("V-COVERAGE-NARROW-REJECTED",
              f"the exact production defect was admitted: {narrow}")

    # --- bookend: the fix must actually read as fixed --------------------
    cl.SETTINGS = Path(_settings("Bash|PowerShell", "node probe.js"))
    wide = cl.coverage_of(_spec(both))
    if wide["state"] == "COVERED" and not wide["uncovered"]:
        _ok("V-COVERAGE-WIDE-ADMITTED",
            "widening the matcher flips the verdict to COVERED")
    else:
        _fail("V-COVERAGE-WIDE-ADMITTED",
              f"a correct registration still failed: {wide} -- the gate can "
              "only say NO")

    cl.SETTINGS = Path(_settings("*", "node probe.js"))
    if cl.coverage_of(_spec(both))["state"] == "COVERED":
        _ok("V-COVERAGE-UNIVERSAL-ADMITTED",
            "a universal registration covers every declared surface")
    else:
        _fail("V-COVERAGE-UNIVERSAL-ADMITTED", "universal read as narrow")

    # --- unknown must not resolve to fine --------------------------------
    cl.SETTINGS = Path(_settings("Bash", "node probe.js"))
    blind = cl.coverage_of(_spec(_hook_src("")))
    if blind["state"] == "UNVERIFIABLE":
        _ok("V-COVERAGE-UNKNOWN-NOT-PASS",
            "an unreadable declaration is UNVERIFIABLE, never COVERED")
    else:
        _fail("V-COVERAGE-UNKNOWN-NOT-PASS",
              f"unknown coverage resolved to {blind['state']}")

    if cl.coverage_of(_spec(None))["state"] == "NOT-APPLICABLE":
        _ok("V-COVERAGE-NO-CONTRACT-SILENT",
            "a producer claiming no surface contract is not judged on one")
    else:
        _fail("V-COVERAGE-NO-CONTRACT-SILENT", "a contract was invented")

    cl.SETTINGS = Path(_settings("Bash", "node unrelated.js"))
    gone = cl.coverage_of(_spec(both))
    if gone["state"] == "UNREGISTERED":
        _ok("V-COVERAGE-UNREGISTERED-DISTINCT",
            "absent from settings.json reads as UNREGISTERED, not NARROW -- "
            "widening an entry that does not exist fixes nothing")
    else:
        _fail("V-COVERAGE-UNREGISTERED-DISTINCT",
              f"an unregistered hook reported {gone['state']}")

    # --- the live finding, pinned ----------------------------------------
    cl.SETTINGS = original
    live = cl.coverage_of(
        next(p for p in cl.PRODUCERS if p["name"] == "bug-hunter-ceps-bridge"))
    if live["state"] in ("NARROW", "COVERED"):
        _ok("V-COVERAGE-LIVE-MEASURED",
            f"live bridge coverage is {live['state']}: declares "
            f"{live['declared']}, matches {live['matched']}")
    else:
        _fail("V-COVERAGE-LIVE-MEASURED",
              f"live coverage is {live['state']} -- the installed hook's "
              "surface declaration could not be read at all")

    ran = len(_passes) + len(_fails)
    print(f"\nCOVERAGE_PASS={len(_passes)}/{ran}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if ran != EXPECTED_GATES:
        print(f"GATE COUNT MISMATCH: {ran} ran, {EXPECTED_GATES} expected")
        return 1
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
