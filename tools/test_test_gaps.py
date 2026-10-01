"""V-TG-* gates for tools/test_gaps.py (spec: vault/specs/test-gaps.md).

Builds a throwaway git project in a temp dir, so the diff parsing, the coverage contexts and the
mutation runs are all the real ones. Every "nothing reported" gate is paired with a gate on the
same fixture where something must be reported.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_gaps  # noqa: E402

passes = 0
fails = 0

V0 = "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    return x\n\n\ndef unused(a):\n    return a * 2\n"
V1 = ("def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n"
      "    return x\n\n\ndef unused(a):\n    return a * 2\n")
WEAK = ("from pkg.calc import clamp\n\n\ndef test_low():\n    assert clamp(-5, 0, 10) == 0\n\n\n"
        "def test_mid():\n    assert clamp(5, 0, 10) >= 0\n")
STRONG = WEAK.replace("assert clamp(5, 0, 10) >= 0", "assert clamp(5, 0, 10) == 5")
MARKER = ("import os\n\n\ndef test_marker():\n    with open(os.environ['TG_MARKER'], 'a') as f:\n"
          "        f.write('x')\n")


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {diag}")


def check(gate: str, cond: bool, evidence: str) -> None:
    (_ok if cond else _fail)(gate, evidence)


def git(repo: Path, *args: str) -> None:
    subprocess.run([test_gaps._git(), "-C", str(repo), "-c", "user.name=tg", "-c",
                    "user.email=tg@example.invalid", *args], check=True, capture_output=True)


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            h.update(p.relative_to(root).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def write(root: Path, rel: str, text: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(text, encoding="utf-8")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="tg-test-"))
    repo = tmp / "proj"
    marker = tmp / "marker.txt"
    os.environ["TG_MARKER"] = str(marker)
    try:
        # Arrange: committed v0 without the `hi` branch, working tree adds lines 4-5.
        write(repo, "pkg/__init__.py", "")
        write(repo, "pkg/calc.py", V0)
        write(repo, "tests/test_calc.py", WEAK)
        write(repo, "tests/test_marker.py", MARKER)
        git(repo, "init", "-q")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "v0")
        write(repo, "pkg/calc.py", V1)

        # Act
        before = tree_hash(repo)
        res = test_gaps.analyse(repo)
        after = tree_hash(repo)

        # Assert
        check("V-TG-DIFF-LINES", res["changed"] == {"pkg/calc.py": 2}, str(res["changed"]))
        check("V-TG-MEASURED", res["verdict"] == "MEASURED", f"{res['verdict']} {res.get('reason', '')}")
        check("V-TG-UNCOVERED", res["uncovered"] == {"pkg/calc.py": [5]}, str(res["uncovered"]))
        surv = res["survived"]
        check("V-TG-SURVIVOR-NAMED",
              len(surv) == 1 and surv[0]["line"] == 4 and surv[0]["mutation"] == "Gt -> LtE"
              and surv[0]["tests"] == ["tests/test_calc.py::test_mid"], str(surv))
        check("V-TG-UNCHANGED-LINES-IGNORED",
              all(r["line"] in (4, 5) for r in res["killed"] + surv), str(res["killed"] + surv))
        # The marker test runs in the baseline only. If mutants re-ran the whole suite it would
        # have run again for the line-4 mutant.
        runs = len(marker.read_text()) if marker.exists() else 0
        check("V-TG-ONLY-COVERING-TESTS-RERUN", runs == 1, f"marker test ran {runs}x")
        check("V-TG-PROJECT-UNTOUCHED", before == after, "tree hash identical before/after")

        # Control: a test that pins the value kills the same mutant.
        write(repo, "tests/test_calc.py", STRONG)
        res = test_gaps.analyse(repo)
        check("V-TG-STRONG-TEST-KILLS", res["survived"] == [] and len(res["killed"]) == 1
              and res["killed"][0]["line"] == 4, f"killed={res['killed']} survived={res['survived']}")
        check("V-TG-TESTS-NOT-MUTATED", "tests/test_calc.py" not in res["changed"], str(res["changed"]))

        # A CLI exercised only through `python -m pkg` in a subprocess. Measured on a real
        # project (2026-10-01): without subprocess coverage every such line read UNCOVERED and
        # produced no mutant at all. Line 8 must be covered, and its mutant judged by the whole
        # suite (no single test context exists inside the child process).
        write(repo, "pkg/cli.py", "import sys\n\nfrom pkg.calc import clamp\n\n\ndef main(argv):\n"
                                  "    n = int(argv[0])\n"
                                  "    print('big' if clamp(n, 0, 100) > 3 else 'small')\n")
        write(repo, "pkg/__main__.py", "import sys\n\nfrom pkg.cli import main\n\nmain(sys.argv[1:])\n")
        write(repo, "tests/test_cli_sub.py",
              "import subprocess\nimport sys\n\n\ndef test_cli_big():\n"
              "    out = subprocess.run([sys.executable, '-m', 'pkg', '5'], capture_output=True,\n"
              "                         text=True).stdout\n    assert out.strip() == 'big'\n")
        res = test_gaps.analyse(repo)
        cli_unc = res["uncovered"].get("pkg/cli.py", [])
        check("V-TG-SUBPROCESS-LINES-COVERED", res["verdict"] == "MEASURED" and 8 not in cli_unc
              and 7 not in cli_unc, f"{res['verdict']} uncovered cli.py={cli_unc}")
        sub_killed = [r for r in res["killed"] if r["file"] == "pkg/cli.py" and r["line"] == 8
                      and r["mutation"] == "Gt -> LtE"]
        check("V-TG-SUBPROCESS-MUTANT-WHOLE-SUITE", len(sub_killed) == 1 and sub_killed[0]["tests"] == [],
              f"line-8 rows={sub_killed} all cli rows={[r for r in res['killed'] + res['survived'] if r['file'] == 'pkg/cli.py']}")

        # A red baseline makes nothing measurable.
        write(repo, "tests/test_red.py", "def test_red():\n    assert False\n")
        res = test_gaps.analyse(repo)
        check("V-TG-RED-BASELINE-UNMEASURABLE",
              res["verdict"] == "UNMEASURABLE" and not res["killed"] and not res["survived"],
              f"{res['verdict']}: {res.get('reason', '')}")
        (repo / "tests/test_red.py").unlink()

        # Nothing changed -> NO_CHANGES, not a clean bill.
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "v1")
        res = test_gaps.analyse(repo)
        check("V-TG-NO-CHANGES", res["verdict"] == "NO_CHANGES", res["verdict"])

        # Exit codes through the CLI: measured -> 0, unmeasurable -> 2.
        cli = [sys.executable, str(Path(test_gaps.__file__)), "--repo", str(repo)]
        code0 = subprocess.run(cli + ["--files", "pkg/calc.py"], capture_output=True).returncode
        write(repo, "tests/test_red.py", "def test_red():\n    assert False\n")
        code2 = subprocess.run(cli + ["--files", "pkg/calc.py"], capture_output=True).returncode
        check("V-TG-EXIT-CODES", (code0, code2) == (0, 2), f"measured={code0} unmeasurable={code2}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"TG_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
