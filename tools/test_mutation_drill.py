#!/usr/bin/env python
"""V-MD-* gates for tools/mutation_drill.py, on a SYNTHETIC subject so the drill represents the
class and cannot be fixed out from under its assertions. Every outcome is driven, and the
live subject's bytes are checked after every drill.

The CONTROL and LAYOUT cases (plan ccp-s15 C1) each pin one false verdict the harness used to
give: a gate already failing on the clean copy read KILLED, a misspelled gate read SURVIVED, a
test outside the subject's directory ran the LIVE subject (SURVIVED), and a test reading a repo
sibling crashed in the flat copy (UNJUDGED)."""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutation_drill as md  # noqa: E402

passes = fails = 0
SUBJ = "def f():\n    return 1  # anchor\n"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def gate_test(import_line: str, extra: str = "") -> str:
    """A suite with one gate V-S-ONE that passes iff subj.f() == 1."""
    return ("import sys\nfrom pathlib import Path\n" + import_line + extra +
            "import subj\nok = subj.f() == 1\nprint(('PASS' if ok else 'FAIL') + ' V-S-ONE')\n"
            "print(f'S_PASS={int(ok)}/1')\n")


def mini_repo(git_as_file: bool = False) -> tuple[Path, Path]:
    """repo/.git + modules/m/subj.py + tools/test_subj.py: the test is OUTSIDE the subject dir
    and reaches it through the repo layout, the way tools/* tests import modules/*."""
    repo = Path(tempfile.mkdtemp(prefix="md-repo-")) / "repo"
    (repo / "modules" / "m").mkdir(parents=True)
    (repo / "tools").mkdir()
    if git_as_file:                                    # a worktree's .git is a file
        (repo / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    else:
        (repo / ".git").mkdir()
    subj = repo / "modules" / "m" / "subj.py"
    subj.write_text(SUBJ, encoding="utf-8")
    test = repo / "tools" / "test_subj.py"
    test.write_text(gate_test("sys.path.insert(0, str(Path(__file__).resolve().parent.parent "
                              "/ 'modules' / 'm'))\n"), encoding="utf-8")
    return subj, test


def main() -> int:
    d = Path(tempfile.mkdtemp(prefix="md-subject-")) / "pkg"
    d.mkdir()
    subj, test = d / "subj.py", d / "test_subj.py"
    subj.write_text(SUBJ, encoding="utf-8")
    test.write_text(gate_test("sys.path.insert(0, str(Path(__file__).parent))\n"), encoding="utf-8")
    h = sha(subj)
    base = {"file": str(subj), "test": str(test), "gate": "V-S-ONE"}

    # Same-size mutant ("1" -> "2"): with bytecode written by the control run, a same-second
    # rewrite would load the stale .pyc and read SURVIVED.
    v, _ = md.drill({**base, "old": "return 1", "new": "return 2"})
    check("V-MD-KILLED", v == "KILLED", v)
    v, _ = md.drill({**base, "old": "# anchor", "new": "# renamed"})
    check("V-MD-SURVIVED-IS-NOT-KILLED", v == "SURVIVED", v)
    v, _ = md.drill({**base, "old": "return 1", "new": "return ("})
    check("V-MD-CRASH-IS-UNJUDGED", v == "UNJUDGED", v)
    v, why = md.drill({**base, "old": "not in the file", "new": "x"})
    check("V-MD-MISSING-ANCHOR-HARNESS", v == "HARNESS" and "0x" in why, why)
    check("V-MD-LIVE-SUBJECT-NEVER-WRITTEN", sha(subj) == h)

    # CONTROL: the clean copy must show the gate passing before any mutant counts.
    v, _ = md.drill({**base, "gate": "V-S-NOPE", "old": "return 1", "new": "return 2"})
    check("V-MD-CONTROL-MISSPELLED-GATE", v == "CONTROL_INVALID", f"{v} (was SURVIVED)")
    bad = d.parent / "bad"
    bad.mkdir()
    (bad / "subj.py").write_text(SUBJ.replace("return 1", "return 3"), encoding="utf-8")
    (bad / "test_subj.py").write_text(test.read_text(encoding="utf-8"), encoding="utf-8")
    v, _ = md.drill({"file": str(bad / "subj.py"), "test": str(bad / "test_subj.py"),
                     "gate": "V-S-ONE", "old": "return 3", "new": "return 4"})
    check("V-MD-CONTROL-GATE-ALREADY-FAILING", v == "CONTROL_INVALID", f"{v} (was KILLED)")
    v, _ = md.drill({**base, "old": "return 1", "new": "return ("})
    check("V-MD-CONTROL-CLEAN-STILL-JUDGES", v == "UNJUDGED", v)     # positive control

    # LAYOUT: a test outside the subject's dir must run against the MUTANT, not the live file.
    for gate, as_file in (("V-MD-OUTSIDE-TEST-REACHES-MUTANT", False),
                          ("V-MD-OUTSIDE-TEST-WORKTREE-GITFILE", True)):
        rs, rt = mini_repo(as_file)
        rh = sha(rs)
        v, why = md.drill({"file": str(rs), "test": str(rt), "gate": "V-S-ONE",
                           "old": "return 1", "new": "return 2"})
        check(gate, v == "KILLED" and sha(rs) == rh, f"{v} (was SURVIVED) {why[-120:]!r}")

    # LAYOUT: a test beside its subject that reads a repo sibling (tools/ reading modules/)
    # gets the sibling by default, without copy_dirs in the spec.
    rs, rt = mini_repo()
    side = rs.parents[2] / "tools" / "side.py"
    side.write_text(SUBJ, encoding="utf-8")
    (rs.parents[2] / "modules" / "data.txt").write_text("1\n", encoding="utf-8")
    beside = rs.parents[2] / "tools" / "test_side.py"
    beside.write_text(
        "import sys\nfrom pathlib import Path\nHERE = Path(__file__).resolve().parent\n"
        "sys.path.insert(0, str(HERE))\nimport side\n"
        "want = int((HERE.parent / 'modules' / 'data.txt').read_text())\n"
        "ok = side.f() == want\nprint(('PASS' if ok else 'FAIL') + ' V-S-ONE')\n"
        "print(f'S_PASS={int(ok)}/1')\n", encoding="utf-8")
    v, why = md.drill({"file": str(side), "test": str(beside), "gate": "V-S-ONE",
                       "old": "return 1", "new": "return 2"})
    check("V-MD-SIBLING-DIR-BY-DEFAULT", v == "KILLED", f"{v} (was UNJUDGED) {why[-120:]!r}")

    # Gate lines (audit ccp-s15-c1 G1/G2): every suite format in use, and never a prefix.
    shapes = {"PASS V-X ev": True, "  PASS V-X: ev": True, "[PASS] V-X: ev": True,
              "  V-X  PASS  ev": True, "PASS V-X-2 ev": False, "  V-X-2  PASS": False,
              "PASS XV-X": False, "BYPASS V-X": False}
    wrong = {s: want for s, want in shapes.items() if md.gate_line("V-X", "PASS", s) != want}
    check("V-MD-GATE-LINE-SHAPES", not wrong, f"mismatched: {wrong}")
    v, _ = md.drill({**base, "old": "# anchor", "new": "# anchor"})
    check("V-MD-NOOP-MUTATION-HARNESS", v == "HARNESS", v)

    # Detail (ACV C4): the indented FAIL lines the resolver/capability suites print must reach the
    # drill's detail. Detail never decides a verdict; it only has to show the failing line.
    out = "  FAIL V-X: ev\n[FAIL] V-Y: ev\n  V-Z  FAIL  ev\n  PASS V-W\nFAILED to parse\nprefixFAIL x\nX_PASS=1/4"
    got = md.detail_lines(out)
    check("V-MD-DETAIL-INDENTED-FAIL", got == ["  FAIL V-X: ev", "[FAIL] V-Y: ev", "  V-Z  FAIL  ev", "X_PASS=1/4"],
          got)

    print(f"MD_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
