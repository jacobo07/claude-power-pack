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
import os
import re
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

import tools.capture_liveness as cl  # noqa: E402

EXPECTED_GATES = 22
_TEMPS: list[str] = []
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
    _TEMPS.append(handle.name)
    return handle.name


def _multi(entries: list) -> Path:
    """settings.json with entries as (event, matcher, command) triples."""
    hooks: dict = {}
    for event, matcher, command in entries:
        hooks.setdefault(event, []).append(
            {"matcher": matcher, "hooks": [{"command": command}]})
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8")
    json.dump({"hooks": hooks}, handle)
    handle.close()
    _TEMPS.append(handle.name)
    return Path(handle.name)


def _hook_src(surfaces: str) -> str:
    """A stand-in hook source declaring a COMMAND_TOOLS set."""
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".js", delete=False, encoding="utf-8")
    handle.write("'use strict';\nconst COMMAND_TOOLS = new Set([%s]);\n"
                 % surfaces)
    handle.close()
    _TEMPS.append(handle.name)
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
    # This gate used to accept NARROW *or* COVERED, which is every outcome
    # it can name -- it could not fail for the defect it is about. It now
    # asserts the measurement is internally COHERENT, which can.
    declared, matched = set(live["declared"] or []), set(live["matched"] or [])
    coherent = (
        (live["state"] == "NARROW"
         and live["uncovered"] and declared > matched)
        or (live["state"] == "COVERED"
            and not live["uncovered"]
            and (matched == {"*"} or declared <= matched)))
    if coherent:
        _ok("V-COVERAGE-LIVE-MEASURED",
            f"live bridge coverage is {live['state']} and self-consistent: "
            f"declares {live['declared']}, matches {live['matched']}, "
            f"uncovered {live['uncovered']}")
    else:
        _fail("V-COVERAGE-LIVE-MEASURED",
              f"incoherent: state={live['state']} declared={live['declared']} "
              f"matched={live['matched']} uncovered={live['uncovered']}")

    # --- the address half: a store must belong to its own checkout -------
    # These two hardcoded the installed path, so a copy running from a git
    # worktree wrote into the installed corpus while the test beside it
    # snapshotted and restored a file nobody had written -- and passed its
    # own byte-identical-restore gate while doing it.
    import tools.ceps as ceps
    # `ceps.PP_ROOT == PP` was true by construction -- both are parents[1]
    # of a file in the same tools/ dir, so it asserted arithmetic. What
    # matters is that the SOURCE no longer derives the store from $HOME and
    # that every write path lands under this checkout.
    ceps_src = (PP / "tools" / "ceps.py").read_text(
        encoding="utf-8", errors="replace")
    home_rooted = re.search(
        r"PP_ROOT\s*=\s*HOME\s*/|PP_ROOT\s*=\s*Path\.home\(\)", ceps_src)
    writes = [ceps.EVENTS_PATH, ceps.DB_PATH, ceps.REJECTIONS_PATH,
              ceps.DRAFTS_DIR, ceps.LESSONS_PATH, ceps.UKDL_PATH]
    stray = [w for w in writes if PP not in Path(w).resolve().parents]
    if not home_rooted and not stray:
        _ok("V-COVERAGE-STORE-ADDRESS",
            f"no $HOME-rooted store in ceps.py and all {len(writes)} write "
            f"paths resolve under {PP.name}")
    else:
        _fail("V-COVERAGE-STORE-ADDRESS",
              f"home_rooted={bool(home_rooted)} stray={[str(x) for x in stray]}"
              " -- a worktree run would write the installed corpus")

    bridge_text = (PP / "hooks" / "bug-hunter-ceps-bridge.js").read_text(
        encoding="utf-8", errors="replace")
    # A substring pin on one backslash spelling would pass a forward-slash
    # hardcoded path. Assert the ASSIGNMENT instead: PP_PATH must not be a
    # drive-letter literal, in either spelling.
    hardcoded = re.search(r"PP_PATH\s*=\s*['\"][A-Za-z]:", bridge_text)
    if "__dirname" in bridge_text and not hardcoded:
        _ok("V-COVERAGE-HOOK-ADDRESS",
            "the bridge derives PP_PATH from __dirname; no absolute-path "
            "assignment in either slash spelling")
    else:
        _fail("V-COVERAGE-HOOK-ADDRESS",
              f"hardcoded={bool(hardcoded)} -- a worktree copy would write "
              "to the installed store")

    # --- HIGH-1: coverage is per EVENT ----------------------------------
    # Stop/SessionStart/UserPromptSubmit entries carry no matcher at all.
    # Unioned across events, one of those made the PostToolUse surface read
    # COVERED while it was Bash-only -- the exact false-healthy verdict
    # this file exists to abolish, restored silently.
    cl.SETTINGS = _multi([
        ("PostToolUse", "Bash", "node probe.js"),
        ("Stop", None, "node probe.js"),
    ])
    scoped = cl.coverage_of(dict(_spec(both), event="PostToolUse"))
    if scoped["state"] == "NARROW" and scoped["uncovered"] == ["PowerShell"]:
        _ok("V-COVERAGE-EVENT-SCOPED",
            "a matcher-less Stop entry does not make the PostToolUse "
            "surface read as covered")
    else:
        _fail("V-COVERAGE-EVENT-SCOPED",
              f"cross-event leak: {scoped} -- one event's universality "
              "masked another's narrowness")

    if cl.registration_surfaces("probe.js", "Stop") is None:
        _ok("V-COVERAGE-EVENT-SCOPED-BOOKEND",
            "the matcher-less Stop entry is still universal in ITS event")
    else:
        _fail("V-COVERAGE-EVENT-SCOPED-BOOKEND",
              "event scoping broke the universal case it must preserve")

    # --- MEDIUM-3: a historical declaration in a comment ----------------
    commented = tempfile.NamedTemporaryFile(
        "w", suffix=".js", delete=False, encoding="utf-8")
    commented.write(
        "// historical: COMMAND_TOOLS = new Set(['Bash']) before the repair\n"
        "const COMMAND_TOOLS = new Set(['Bash', 'PowerShell']);\n")
    commented.close()
    if cl.declared_surfaces(Path(commented.name)) == {"Bash", "PowerShell"}:
        _ok("V-COVERAGE-COMMENT-IGNORED",
            "a pre-repair declaration quoted in a comment does not narrow "
            "the declared set")
    else:
        _fail("V-COVERAGE-COMMENT-IGNORED",
              f"read {cl.declared_surfaces(Path(commented.name))} -- a "
              "narrower declared set makes `declared - matched` empty and "
              "reports COVERED")

    spread = _hook_src("...BASE, 'Bash'")
    if cl.declared_surfaces(Path(spread)) is None:
        _ok("V-COVERAGE-NONLITERAL-UNVERIFIABLE",
            "a spread declaration is UNVERIFIABLE, not the literal fragment")
    else:
        _fail("V-COVERAGE-NONLITERAL-UNVERIFIABLE",
              f"read {cl.declared_surfaces(Path(spread))} from a spread")

    # --- LOW-9: matchers are regexes ------------------------------------
    cl.SETTINGS = Path(_settings(".*", "node probe.js"))
    if cl.registration_surfaces("probe.js") is None:
        _ok("V-COVERAGE-REGEX-UNIVERSAL",
            "'.*' reads as universal, not as a tool literally named '.*'")
    else:
        _fail("V-COVERAGE-REGEX-UNIVERSAL",
              "a regex wildcard read as NARROW; the migration would append "
              "|PowerShell to a pattern that already matched everything")

    # --- MEDIUM-5: one foreign row must not satisfy the outage check ----
    sink = tempfile.NamedTemporaryFile(
        "w", suffix=".jsonl", delete=False, encoding="utf-8")
    sink.write(json.dumps({"ts": "2999-01-01T00:00:00Z", "origin": "direct"})
               + "\n")
    sink.close()
    cutoff = cl._now() - cl.timedelta(days=7)
    if cl.count_since(Path(sink.name), cutoff, origin="hook") == 0:
        _ok("V-COVERAGE-RECORDS-ORIGIN-FILTERED",
            "a row written by another caller does not count as this "
            "producer's record; fires-without-records can still trip")
    else:
        _fail("V-COVERAGE-RECORDS-ORIGIN-FILTERED",
              "one foreign row satisfies the 63-fires/0-records check")

    for leftover in _TEMPS + [commented.name, sink.name]:
        try:
            os.unlink(leftover)
        except OSError:
            pass
    ran = len(_passes) + len(_fails)
    print(f"\nCOVERAGE_PASS={len(_passes)}/{ran}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if ran != EXPECTED_GATES:
        print(f"GATE COUNT MISMATCH: {ran} ran, {EXPECTED_GATES} expected")
        return 1
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
