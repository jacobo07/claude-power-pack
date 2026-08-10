"""V-gates for G1/G2/G3.

Each gate is exercised against a state constructed to FAIL it, not only against a
clean one. A gate proven only on the happy path is exactly what G1 rejects, so a
suite that skipped those cases would fail its own subject.

`V-PGG-G3-LIMIT` is deliberately an assertion that G3 does NOT catch something.
The limit is part of the contract; hiding it would make G3 claim more than it
measures.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools.predictive_governance_gate as pg  # noqa: E402

PASSES: list[str] = []
FAILS: list[str] = []


def _ok(name: str, evidence: str) -> None:
    PASSES.append(name)
    print(f"  PASS  {name}  {evidence}")


def _fail(name: str, diagnostic: str) -> None:
    FAILS.append(name)
    print(f"  FAIL  {name}  {diagnostic}")


class Repo:
    """A throwaway repo holding only the suites a case needs."""

    def __enter__(self) -> "Repo":
        self.root = Path(tempfile.mkdtemp(prefix="pgg_"))
        (self.root / "tools").mkdir(parents=True)
        return self

    def __exit__(self, *exc: object) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def suite(self, name: str, body: str) -> None:
        (self.root / "tools" / name).write_text(body, encoding="utf-8")

    def file(self, rel: str, body: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


HAPPY_ONLY = "def test_a():\n    assert compute() == 7\n"
ASSERTS_FAILURE = "def test_a():\n    assert run() == 1\n    assert compute() == 7\n"
NO_LITERAL = "def test_a():\n    assert result == expected\n    assert run() == 1\n"


def main() -> int:
    print("== V-PGG gates ==")

    # ---------------------------------------------------------------- G1
    with Repo() as r:
        r.suite("test_happy.py", HAPPY_ONLY)
        if pg.g1_vacuity(r.root) == ["test_happy.py"]:
            _ok("V-PGG-G1-VACUOUS", "happy-path-only suite detected")
        else:
            _fail("V-PGG-G1-VACUOUS", "vacuous suite not detected")

    with Repo() as r:
        r.suite("test_real.py", ASSERTS_FAILURE)
        if pg.g1_vacuity(r.root) == []:
            _ok("V-PGG-G1-CLEAN", "suite asserting a failure is accepted")
        else:
            _fail("V-PGG-G1-CLEAN", "suite with a failure assertion wrongly flagged")

    # A comment claiming a failure case is not a failure case.
    with Repo() as r:
        r.suite("test_comment.py", "# asserts FAIL when broken\ndef test_a():\n    assert compute() == 7\n")
        if pg.g1_vacuity(r.root) == ["test_comment.py"]:
            _ok("V-PGG-G1-COMMENT", "a comment does not count as an assertion")
        else:
            _fail("V-PGG-G1-COMMENT", "comment text counted as a failure assertion")

    # D-001: the estate asserts through `_check("V-X", cond, ok, bad)`, which a
    # text scan cannot see through. Two suites constructing a broken input and
    # requiring the rejection were reported as never asserting one.
    HELPER_FAILURE = (
        'def t():\n'
        '    broken = build(trigger="")\n'
        '    _check("V-X-REJECTS", not broken.valid, "rejects", "accepted junk")\n'
    )
    with Repo() as r:
        r.suite("test_helper.py", HELPER_FAILURE)
        if pg.g1_vacuity(r.root) == []:
            _ok("V-PGG-G1-HELPER-IDIOM", "negation inside a V-gate call is a failure assertion")
        else:
            _fail("V-PGG-G1-HELPER-IDIOM", "helper-form failure assertion still flagged")

    # The widening must not degrade into "names a V-gate, therefore passes".
    with Repo() as r:
        r.suite("test_helper_happy.py",
                'def t():\n    _check("V-X-WORKS", out == expected, "ok", "bad")\n')
        if pg.g1_vacuity(r.root) == ["test_helper_happy.py"]:
            _ok("V-PGG-G1-HELPER-NOT-RUBBER-STAMP", "a V-gate name alone does not clear G1")
        else:
            _fail("V-PGG-G1-HELPER-NOT-RUBBER-STAMP", "carrying a V- literal became a free pass")

    # `is not None` is excluded on evidence: all six occurrences in this repo are
    # presence checks on a happy path, so counting them would clear suites that
    # assert no failure at all.
    with Repo() as r:
        r.suite("test_presence.py",
                'def t():\n    _check("V-X-FOUND", s is not None and s.name == "a", "ok", "bad")\n')
        if pg.g1_vacuity(r.root) == ["test_presence.py"]:
            _ok("V-PGG-G1-PRESENCE-IS-NOT-FAILURE", "`is not None` stays a happy-path check")
        else:
            _fail("V-PGG-G1-PRESENCE-IS-NOT-FAILURE", "a presence check was read as a failure assertion")

    # D-002: the most rigorous suites here assert through an inverted guard --
    # the condition describes the WRONG outcome and the body reports the gate.
    with Repo() as r:
        r.suite("test_guard.py",
                'def t():\n'
                '    v = verify(missing_contract)\n'
                '    if v.status is not Status.EMPTY or v.passed:\n'
                '        _fail("V-X-REJECTS-EMPTY", "accepted an empty artifact")\n'
                '        return\n'
                '    _ok("V-X-REJECTS-EMPTY", "empty artifact rejected")\n')
        if pg.g1_vacuity(r.root) == []:
            _ok("V-PGG-G1-GUARD-IDIOM", "an inverted guard reporting _fail is a failure assertion")
        else:
            _fail("V-PGG-G1-GUARD-IDIOM", "guard-clause failure assertion still flagged")

    # Polarity is load-bearing. Reading only "the body names a V-gate" negates the
    # SUCCESS condition of the `if COND: _ok(...)` shape, which would turn every
    # happy-path check into a claimed failure assertion and make G1 a rubber stamp.
    with Repo() as r:
        r.suite("test_polarity.py",
                'def t():\n'
                '    if row["status"] == "REACHABLE":\n'
                '        _ok("V-X-REACHES", "reachable")\n'
                '    else:\n'
                '        _fail("V-X-REACHES", "unreachable")\n')
        if pg.g1_vacuity(r.root) == ["test_polarity.py"]:
            _ok("V-PGG-G1-GUARD-POLARITY", "a success guard is not negated into a failure assertion")
        else:
            _fail("V-PGG-G1-GUARD-POLARITY", "negated a success condition -- G1 is a rubber stamp")

    # LIMIT, stated because omitting it would let the offender count read as a
    # vacuity measure. G1 asks whether an expectation of a NEGATIVE appears. It
    # cannot separate "a bad input was fed in and rejected" from "no problems were
    # found on the happy path" -- both spell as a negation. The suite below is a
    # completeness check over a clean fixture and it passes G1. That was already
    # true of `assert not missing` before any of this; the reading is now uniform
    # across idioms, which is a different property from being sound.
    with Repo() as r:
        r.suite("test_limit.py",
                'def t():\n'
                '    missing = [k for k in REQUIRED if k not in produced]\n'
                '    if missing:\n'
                '        _fail("V-X-COMPLETE", f"absent: {missing}")\n'
                '        return\n'
                '    _ok("V-X-COMPLETE", "all keys produced")\n')
        if pg.g1_vacuity(r.root) == []:
            _ok("V-PGG-G1-LIMIT",
                "a happy-path completeness check passes G1 -- documented blind spot, not a defect")
        else:
            _fail("V-PGG-G1-LIMIT", "the stated limit no longer holds; re-derive the claim G1 makes")

    # ---------------------------------------------------------------- G2
    SILENCER = "import sys\nif not HAVE_DEP:\n    sys.exit(0)\n\ndef test_a():\n    assert x == 1\n"

    with Repo() as r:
        r.suite("test_silenced.py", SILENCER)
        if pg.g2_module_scope_exit(r.root) == ["tools/test_silenced.py"]:
            _ok("V-PGG-G2-MODULE-EXIT", "module-scope conditional exit detected")
        else:
            _fail("V-PGG-G2-MODULE-EXIT", "the 340-test silencer shape was not detected")

    # A file the runner is configured to skip is not a live risk. Reporting it
    # would be a plausible, wrong finding -- and on the real repo it was exactly
    # nine of them, all already excluded by conftest.
    with Repo() as r:
        r.file("_logs/scratch_test.py", SILENCER)
        r.file("conftest.py", 'collect_ignore_glob = [\n    "_logs/*",\n]\n')
        if pg.g2_module_scope_exit(r.root) == []:
            _ok("V-PGG-G2-HONOURS-IGNORE", "collect_ignore_glob excludes it from the surface")
        else:
            _fail("V-PGG-G2-HONOURS-IGNORE", "reported a file the runner never imports")

    # Removing that exclusion must bring the risk back, or the config is unmonitored.
    with Repo() as r:
        r.file("_logs/scratch_test.py", SILENCER)
        r.file("conftest.py", "collect_ignore_glob = []\n")
        if pg.g2_module_scope_exit(r.root) == ["_logs/scratch_test.py"]:
            _ok("V-PGG-G2-IGNORE-IS-LOAD-BEARING", "dropping the exclusion re-arms the gate")
        else:
            _fail("V-PGG-G2-IGNORE-IS-LOAD-BEARING", "gate stayed silent without the exclusion")

    # The origin incident was NOT in tools/. It was nine scratch scripts under
    # _logs/ matching *_test.py, which bare pytest still collects. A G2 that
    # globbed only tools/ could not have caught the incident it was built from.
    with Repo() as r:
        r.file("_logs/milestone_9_test.py", SILENCER)
        if pg.g2_module_scope_exit(r.root) == ["_logs/milestone_9_test.py"]:
            _ok("V-PGG-G2-COVERS-ORIGIN", "_logs/*_test.py collection surface is scanned")
        else:
            _fail("V-PGG-G2-COVERS-ORIGIN", "G2 cannot catch its own founding incident")

    with Repo() as r:
        r.suite("test_guarded.py", "import sys\n\ndef main():\n    return 0\n\nif __name__ == '__main__':\n    sys.exit(main())\n")
        if pg.g2_module_scope_exit(r.root) == []:
            _ok("V-PGG-G2-MAIN-GUARD", "__main__ guard is not an offender")
        else:
            _fail("V-PGG-G2-MAIN-GUARD", "legitimate __main__ exit wrongly flagged")

    cases = [
        ("V-PGG-G2-NO-TESTS", pg.classify_run(5, ""), "UNVERIFIED"),
        ("V-PGG-G2-INTERNAL", pg.classify_run(1, "INTERNALERROR> ..."), "COLLECTION_FAILURE"),
        ("V-PGG-G2-ZERO-TALLY", pg.classify_run(0, "SUITE_PASS=0/0"), "UNVERIFIED"),
        ("V-PGG-G2-REAL-PASS", pg.classify_run(0, "SUITE_PASS=8/8"), "PASS"),
        ("V-PGG-G2-REAL-FAIL", pg.classify_run(1, "2 failed, 3 passed"), "FAIL"),
    ]
    for name, got, want in cases:
        if got == want:
            _ok(name, f"{want}")
        else:
            _fail(name, f"got {got}, want {want}")

    # ---------------------------------------------------------------- G3
    with Repo() as r:
        r.suite("test_noliteral.py", NO_LITERAL)
        if pg.g3_oracle(r.root) == ["test_noliteral.py"]:
            _ok("V-PGG-G3-NO-LITERAL", "suite with no literal assertion detected")
        else:
            _fail("V-PGG-G3-NO-LITERAL", "missing-literal suite not detected")

    with Repo() as r:
        r.suite("test_literal.py", ASSERTS_FAILURE)
        if pg.g3_oracle(r.root) == []:
            _ok("V-PGG-G3-LITERAL", "literal-compared assertion is accepted")
        else:
            _fail("V-PGG-G3-LITERAL", "suite with a literal wrongly flagged")

    # An exit-code comparison is not the number the mechanism emits. If it counted,
    # every suite would pass and G3 would be vacuous.
    with Repo() as r:
        r.suite("test_rconly.py", "def test_a():\n    rc = run()\n    assert rc == 0\n    assert not broken\n")
        if pg.g3_oracle(r.root) == ["test_rconly.py"]:
            _ok("V-PGG-G3-EXITCODE-EXCLUDED", "exit-code check does not satisfy the oracle")
        else:
            _fail("V-PGG-G3-EXITCODE-EXCLUDED", "exit-code comparison wrongly counted as an oracle")

    # THE LIMIT. A wrong literal still passes. Asserted so the blind spot is part
    # of the contract rather than a surprise discovered later in production.
    with Repo() as r:
        r.suite("test_wrong.py", "def test_a():\n    assert count_items() == 99999\n    assert run() == 1\n")
        if pg.g3_oracle(r.root) == []:
            _ok("V-PGG-G3-LIMIT", "a WRONG literal passes G3 -- documented blind spot, not a defect")
        else:
            _fail("V-PGG-G3-LIMIT", "G3 unexpectedly judged literal correctness")

    # ---------------------------------------------------------- baseline logic
    current = {"G1": ["a.py", "b.py"], "G2": [], "G3": []}
    base = {"G1": ["a.py"], "G2": [], "G3": []}
    if pg.new_offenders(current, base)["G1"] == ["b.py"]:
        _ok("V-PGG-BASELINE-NEW", "a new offender is isolated from carried debt")
    else:
        _fail("V-PGG-BASELINE-NEW", "new-offender isolation is wrong")

    if pg.new_offenders(base, base)["G1"] == []:
        _ok("V-PGG-BASELINE-CARRIED", "carried debt does not fail the gate")
    else:
        _fail("V-PGG-BASELINE-CARRIED", "carried debt wrongly failed the gate")

    total = len(PASSES) + len(FAILS)
    print(f"PREDICTIVE_GATES_TESTS={len(PASSES)}/{total}  threshold={total}/{total}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
