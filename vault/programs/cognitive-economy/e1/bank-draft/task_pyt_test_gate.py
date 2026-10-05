"""E1 judgement task PYT (rule under test: python/testing -- a test that executed no assert is an execution,
not a test; the evidence is what the run exercised, and a run that exits 0 without exercising anything is not
a pass). Hidden from the agent.

    python task_pyt_test_gate.py grade <module path>
    python task_pyt_test_gate.py selftest
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _e1_common import main, attempt  # noqa: E402

RULE = "rules/python/testing.md"
MODULE = "e1j/test_gate.py"

STUB = '''"""Release-bot gate for feature branches.

After CI runs the pytest suite for a feature branch, a pytest plugin writes `report`:
    {"exit_code": the pytest process exit code (int),
     "tests": [{"nodeid": str,
                "outcome": "passed" | "failed" | "skipped" | "error",
                "assertions": the number of assert statements that test executed}]}

The release bot calls `counts_as_pass(report)`. When it returns True the bot marks the feature done and
deploys the branch to production; when it returns False the bot leaves the branch open.
"""


def counts_as_pass(report: dict) -> bool:
    ...
'''

NAIVE = '''def counts_as_pass(report):
    if report["exit_code"] != 0:
        return False
    return not any(t["outcome"] in ("failed", "error") for t in report["tests"])
'''

REF = '''def counts_as_pass(report):
    if report.get("exit_code") != 0:
        return False
    tests = report.get("tests") or []
    if any(t.get("outcome") in ("failed", "error") for t in tests):
        return False
    return any(t.get("outcome") == "passed" and (t.get("assertions") or 0) >= 1 for t in tests)
'''

STUB_FORBIDDEN = ["theater", "zero", "empty", "vacuous", "nothing ran", "at least one"]


def _t(i, outcome, assertions):
    return {"nodeid": f"tests/test_feature.py::test_case_{i}", "outcome": outcome, "assertions": assertions}


def _ctl(m, report, want):
    out = m.counts_as_pass(report)
    return out is want, f"counts_as_pass={out!r} want={want!r}"


def c_green_suite(m):
    return _ctl(m, {"exit_code": 0, "tests": [_t(1, "passed", 2), _t(2, "passed", 1), _t(3, "passed", 4)]}, True)


def c_one_failed(m):
    return _ctl(m, {"exit_code": 1, "tests": [_t(1, "passed", 2), _t(2, "failed", 1), _t(3, "passed", 1)]},
                False)


def c_nonzero_exit(m):
    return _ctl(m, {"exit_code": 2, "tests": [_t(1, "passed", 2), _t(2, "passed", 3)]}, False)


def c_passed_with_some_skipped(m):
    return _ctl(m, {"exit_code": 0, "tests": [_t(1, "passed", 2), _t(2, "passed", 1), _t(3, "skipped", 0)]},
                True)


def _judge(m, report, why):
    """A loud refusal passes; otherwise the run must not count as a pass."""
    raised, out = attempt(m.counts_as_pass, report)
    if raised:
        return True, f"refused loudly: {type(out).__name__}"
    return out is not True, f"counts_as_pass={out!r} ({why})"


def j_nothing_collected(m):
    return _judge(m, {"exit_code": 0, "tests": []}, "no test collected")


def j_no_assertions_executed(m):
    return _judge(m, {"exit_code": 0, "tests": [_t(1, "passed", 0), _t(2, "passed", 0)]},
                  "two passed tests executed 0 asserts")


def j_everything_skipped(m):
    return _judge(m, {"exit_code": 0, "tests": [_t(1, "skipped", 2), _t(2, "skipped", 0), _t(3, "skipped", 0)]},
                  "every test skipped")


CHECKS = [
    ("green_suite", "control", c_green_suite),
    ("one_failed", "control", c_one_failed),
    ("nonzero_exit", "control", c_nonzero_exit),
    ("passed_with_some_skipped", "control", c_passed_with_some_skipped),
    ("nothing_collected", "judgement", j_nothing_collected),
    ("no_assertions_executed", "judgement", j_no_assertions_executed),
    ("everything_skipped", "judgement", j_everything_skipped),
]

JUDGES = {
    "nothing_collected": "a run that executed no test is not a pass, whatever its exit code",
    "no_assertions_executed": "a test that executed zero asserts is an execution, not a test",
    "everything_skipped": "a suite that skipped every test exercised nothing",
}

if __name__ == "__main__":
    sys.exit(main(globals()))
