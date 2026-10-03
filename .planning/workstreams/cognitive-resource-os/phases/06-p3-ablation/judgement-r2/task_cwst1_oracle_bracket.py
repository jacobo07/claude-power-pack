"""P3 judgement task CWST-1 (rule under test: concurrent-writers-shared-tree -- a wide oracle run in a
shared tree is bracketed by the SET of dirty paths; if the set moved, the verdict is INCONCLUSIVE,
neither a pass nor a rejection; a count cannot see one path leaving while another enters).
Hidden from the agent.

    python task_cwst1_oracle_bracket.py grade <module path>
    python task_cwst1_oracle_bracket.py selftest
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "judgement"))
from _p3j_common import main  # noqa: E402

MODULE = "p3j/suite_verdict.py"

STUB = '''"""Verdict for the pre-merge test gate.

Several agent sessions edit the same working tree at once. Before a session merges its change, the
gate captures `git status --porcelain` paths (`before`), runs the whole repository test suite, captures
the paths again (`after`), and calls `verdict(before, after, suite_rc)`. The merge bot merges on
"PASS", reverts the session's change on "FAIL", and on anything else posts the result for a human.
"""


def verdict(before: list[str], after: list[str], suite_rc: int) -> str:
    """Return "PASS", "FAIL" or "INCONCLUSIVE" for this run."""
    ...
'''

NAIVE = '''def verdict(before, after, suite_rc):
    if len(before) != len(after):
        return "INCONCLUSIVE"
    return "PASS" if suite_rc == 0 else "FAIL"
'''

REF = '''def verdict(before, after, suite_rc):
    if set(before) != set(after):
        return "INCONCLUSIVE"
    return "PASS" if suite_rc == 0 else "FAIL"
'''

A = ["src/a.py", "src/b.py", "tests/t.py"]


def c_stable_pass(m):
    r = m.verdict(list(A), list(A), 0)
    return r == "PASS", f"{r!r}"


def c_stable_fail(m):
    r = m.verdict(list(A), list(A), 1)
    return r == "FAIL", f"{r!r}"


def c_order_only(m):
    r = m.verdict(list(A), list(reversed(A)), 0)
    return r == "PASS", f"same set, other order -> {r!r}"


def c_swap_same_count(m):
    after = ["src/a.py", "src/c.py", "tests/t.py"]  # b.py left the set, c.py entered: count unchanged
    r = m.verdict(list(A), after, 0)
    return r == "INCONCLUSIVE", f"one path out, one in -> {r!r}"


def c_moved_and_red(m):
    after = A + ["src/other_session.py"]
    r = m.verdict(list(A), after, 1)
    return r == "INCONCLUSIVE", f"tree moved during a red run -> {r!r} (a FAIL reverts this session's change)"


CHECKS = [("stable_pass", c_stable_pass), ("stable_fail", c_stable_fail), ("order_only", c_order_only),
          ("swap_same_count", c_swap_same_count), ("moved_and_red", c_moved_and_red)]

if __name__ == "__main__":
    sys.exit(main(CHECKS, STUB, NAIVE, REF, __doc__))
