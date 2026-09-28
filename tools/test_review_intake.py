"""V-RINTAKE-*: tools/review_intake.py + modules/code_review severity accounting.

Every INCOMPLETE path is driven, each verdict pole has its own case, and the approval control is
an EXPLICIT empty findings list -- the one reply that may approve with nothing found. The prose
reply that says "looks good" is the case that must never approve.
    python tools/test_review_intake.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import review_intake as ri  # noqa: E402
from modules import code_review as cr  # noqa: E402

passes = fails = 0


def check(gate: str, cond: bool, ev: object = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def f(i: str, sev: str) -> dict:
    return {"id": i, "severity": sev, "title": "t", "description": "d", "evidence": "tools/x.py:1"}


def run(reply) -> ri.Intake:
    return ri.intake(reply, "pp-code-reviewer", "claude-sonnet-5")


def main() -> int:
    print("verdict poles")
    check("V-RINTAKE-EXPLICIT-EMPTY-APPROVES", run('{"findings": []}').verdict == ri.APPROVE, "control")
    check("V-RINTAKE-LOW-APPROVES", run(json.dumps({"findings": [f("a", "low"), f("b", "info")]})).verdict == ri.APPROVE)
    check("V-RINTAKE-HIGH-WARNS", run(json.dumps({"findings": [f("a", "high")]})).verdict == ri.WARNING)
    check("V-RINTAKE-CRITICAL-BLOCKS", run(json.dumps({"findings": [f("a", "critical"), f("b", "high")]})).verdict == ri.BLOCK)
    fenced = "Review done.\n```json\n" + json.dumps({"findings": [f("a", "medium")]}) + "\n```\nThanks."
    check("V-RINTAKE-FENCED-READ", run(fenced).verdict == ri.APPROVE, run(fenced).counts)
    upper = "Done.\n```JSON\n" + json.dumps({"findings": [f("a", "high")]}) + "\n```"
    check("V-RINTAKE-FENCE-LABEL-ANY-CASE", run(upper).verdict == ri.WARNING, run(upper).reason)
    spaced = "Done.\n``` json\n" + json.dumps({"findings": [f("a", "low")]}) + "\n```"
    check("V-RINTAKE-FENCE-SPACED-LABEL", run(spaced).verdict == ri.APPROVE, run(spaced).reason)
    quoting = ("The config reads:\n```\n{\"retries\": 3}\n```\nVerdict:\n```json\n"
               + json.dumps({"findings": [f("a", "high")]}) + "\n```")
    check("V-RINTAKE-BARE-QUOTE-BESIDE-LABELLED", run(quoting).verdict == ri.WARNING, run(quoting).reason)
    two_bare = "```\n{\"findings\": []}\n```\n```\n{\"findings\": []}\n```"
    check("V-RINTAKE-TWO-BARE-STILL-AMBIGUOUS", run(two_bare).verdict == ri.INCOMPLETE, run(two_bare).reason)

    print("never an approval")
    for gate, reply, needle in [
        ("V-RINTAKE-EMPTY-REPLY", "", "empty reply"),
        ("V-RINTAKE-NONE-REPLY", None, "empty reply"),
        ("V-RINTAKE-PROSE-LOOKS-GOOD", "Looks good to me, no issues found.", "no parseable JSON"),
        ("V-RINTAKE-TWO-BLOCKS", "```json\n{\"findings\": []}\n```\n```json\n{\"findings\": []}\n```", "exactly one"),
        ("V-RINTAKE-EXTRA-KEY", '{"findings": [], "verdict": "APPROVE"}', "exactly the key"),
        ("V-RINTAKE-UNKNOWN-SEVERITY", json.dumps({"findings": [f("a", "major")]}), "severity is invalid"),
        ("V-RINTAKE-DUPLICATE-ID", json.dumps({"findings": [f("a", "low"), f("a", "low")]}), "unique"),
        ("V-RINTAKE-MISSING-FIELD", json.dumps({"findings": [{"id": "a", "severity": "low", "title": "t"}]}), "exactly"),
        # A real review (2026-09-28): json.loads keeps the LAST duplicate, so this was an APPROVE.
        ("V-RINTAKE-DUPLICATE-KEY-COLLAPSE", '{"findings": [' + json.dumps(f("a", "critical")) + '], "findings": []}',
         "duplicate key"),
        ("V-RINTAKE-DUPLICATE-SEVERITY", '{"findings": [{"id": "a", "severity": "critical", "title": "t", '
                                         '"description": "d", "evidence": "e", "severity": "low"}]}', "duplicate key"),
    ]:
        r = run(reply)
        check(gate, r.verdict == ri.INCOMPLETE and needle in r.reason, r.reason)
    saved = os.environ.get("CPP_NODE_EXE")
    os.environ["CPP_NODE_EXE"] = str(Path(tempfile.gettempdir()) / "no-node-here.exe")
    try:
        down = run('{"findings": []}')
    finally:
        if saved is None:
            os.environ.pop("CPP_NODE_EXE", None)
        else:
            os.environ["CPP_NODE_EXE"] = saved
    check("V-RINTAKE-BRIDGE-DOWN-INCOMPLETE", down.verdict == ri.INCOMPLETE and "bridge" in down.reason, down.reason)

    print("modules/code_review: an ungradable severity is not an absence")
    ok = {"line": 1, "failure_mode": "x", "surrounding_context": "y", "severity_defensible": True, "text": "real bug"}
    rv = cr.run_full_review([{**ok, "severity": "Major"}])
    check("V-RINTAKE-CR-UNRECOGNISED-INCOMPLETE", rv["verdict"] == "INCOMPLETE" and rv["unrecognised"] == 1, rv)
    rc = cr.run_full_review([{**ok, "severity": "LOW"}])
    check("V-RINTAKE-CR-CONTROL-APPROVE", rc["verdict"] == "APPROVE" and rc["unrecognised"] == 0, rc["verdict"])
    check("V-RINTAKE-CR-DERIVE-UNRECOGNISED", cr.derive_verdict([{"severity": "blocker"}]) == "INCOMPLETE"
          and cr.derive_verdict([{"severity": "high"}]) == "WARNING", "blocker -> INCOMPLETE, high -> WARNING")

    print("CLI exit codes")
    tmp = Path(tempfile.mkdtemp(prefix="rintake_t_"))
    try:
        p = tmp / "r.txt"
        codes = []
        for body in ('{"findings": []}', json.dumps({"findings": [f("a", "high")]}),
                     json.dumps({"findings": [f("a", "critical")]}), "nothing"):
            p.write_text(body, encoding="utf-8")
            codes.append(ri.main(["--reply", str(p), "--provider", "x", "--model", "y"]))
        codes.append(ri.main(["--reply", str(tmp / "missing.txt"), "--provider", "x", "--model", "y"]))
        check("V-RINTAKE-CLI-EXITS", codes == [0, 1, 4, 3, 3], codes)
    finally:
        for q in tmp.glob("*"):
            q.unlink()
        tmp.rmdir()
    total = passes + fails
    print(f"RINTAKE_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
