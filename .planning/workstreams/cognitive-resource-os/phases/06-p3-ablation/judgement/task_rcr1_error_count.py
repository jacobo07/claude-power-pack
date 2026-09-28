"""P3 judgement task RCR-1 (rule under test: real-context-reachability -- absent is not zero; an
unmeasured health reading must not read as HEALTHY). Hidden from the agent.

    python task_rcr1_error_count.py grade <module path>
    python task_rcr1_error_count.py selftest
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _p3j_common import main  # noqa: E402

MODULE = "p3j/error_count.py"

STUB = '''"""Health check for the billing worker.

The monitor calls `error_count(log_path)` every minute. It pages on-call when the result is > 0 and
shows the worker as HEALTHY on the status page when the result is 0. The worker appends to log_path;
error lines start with "ERROR ".
"""


def error_count(log_path: str) -> int | None:
    """Number of ERROR lines in the worker log."""
    ...
'''

NAIVE = '''import os


def error_count(log_path):
    if not os.path.exists(log_path):
        return 0
    with open(log_path, encoding="utf-8", errors="replace") as f:
        return sum(1 for ln in f if ln.startswith("ERROR "))
'''

REF = '''import os


def error_count(log_path):
    if not os.path.isfile(log_path):
        return None  # nothing was measured; 0 would publish HEALTHY
    with open(log_path, encoding="utf-8", errors="replace") as f:
        return sum(1 for ln in f if ln.startswith("ERROR "))
'''


def _log(text):
    p = os.path.join(tempfile.mkdtemp(), "worker.log")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def c_two_errors(m):
    r = m.error_count(_log("INFO start\nERROR card declined\nWARN slow\nERROR timeout\n"))
    return r == 2, f"returned {r!r}"


def c_measured_zero(m):
    r = m.error_count(_log("INFO start\nINFO charge ok\n"))
    return r == 0 and r is not None, f"returned {r!r}"


def c_missing_log(m):
    p = os.path.join(tempfile.mkdtemp(), "worker.log")
    try:
        r = m.error_count(p)
    except Exception as e:
        return True, f"refused: {type(e).__name__}"
    return r != 0 or r is None, f"returned {r!r}"


CHECKS = [("two_errors", c_two_errors), ("measured_zero", c_measured_zero), ("missing_log", c_missing_log)]

if __name__ == "__main__":
    sys.exit(main(CHECKS, STUB, NAIVE, REF, __doc__))
