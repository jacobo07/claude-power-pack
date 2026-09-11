"""V-UNMEASURED-* -- a row that was TAKEN is not a row that FAILED.

The founding incident of this surface: an 82-row sweep was killed by the OS at
2181 MB free of 32061 MB, and nothing in the estate could say the run had been
killed rather than failed. `_row` already classified a TIMEOUT as "not a
verdict" and had no name at all for a process the kernel removed -- so the one
death that actually happened was the one that read as a defect.

Every subject here is SYNTHETIC and built inside the test. The killed case does
not simulate a kill: it calls TerminateProcess on itself with STATUS_NO_MEMORY,
which is the exact shape an OOM death has on this platform. A drill that faked
the exit code would be asserting about its own fixture.

Both directions are driven. The must-not-fire half is the half that matters: a
classifier that called everything "killed" would satisfy every positive case
here and would have erased the distinction it exists to draw.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.verify_spp import _row, _terminated_by_os  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [OK  ] {gate:<32s} {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate:<32s} {diagnostic}")


# --- the classifier, in isolation ------------------------------------------

def test_taken_codes_are_recognised() -> None:
    taken = {
        -9: "POSIX SIGKILL",
        -1: "TerminateProcess",
        0xC0000017: "STATUS_NO_MEMORY (the OOM shape)",
        0xC00000FD: "STATUS_STACK_OVERFLOW",
    }
    missed = [why for rc, why in taken.items() if not _terminated_by_os(rc)]
    if missed:
        _fail("V-UNMEASURED-TAKEN", f"not recognised: {missed}")
    else:
        _ok("V-UNMEASURED-TAKEN", f"{len(taken)} teardown shapes recognised")


def test_honest_exit_codes_are_not_kills() -> None:
    """THE HALF THAT MATTERS. A verifier returning 1 has judged its subject."""
    honest = {
        0: "clean pass",
        1: "ordinary gate failure",
        2: "argparse / usage error",
        124: "the timeout code this file already owned",
        127: "binary missing",
    }
    wrong = [why for rc, why in honest.items() if _terminated_by_os(rc)]
    if wrong:
        _fail("V-UNMEASURED-HONEST", f"misread as kills: {wrong}")
    else:
        _ok("V-UNMEASURED-HONEST", f"{len(honest)} real exit codes left alone")


# --- a row that is genuinely removed by the OS ------------------------------

# Produces the EXACT observable an OOM death produces -- a process whose exit
# status is STATUS_NO_MEMORY -- which is all `_row` can ever see. It does not
# claim the kernel chose to do it; the classifier reads exit codes, so the exit
# code is the thing that must be real.
#
# The first draft called TerminateProcess through ctypes with no argtypes. The
# exit code 0xC0000017 does not fit the default c_int, the call silently did
# nothing, the child ran to completion and exited 0 -- and the drill went RED.
# That is an instrument failure caught by its own assertion rather than a
# fixture that passed for the wrong reason, which is the whole argument for
# asserting on the classification instead of on "the process is gone".
_SUICIDE = """
import sys
print("about to be taken")
sys.stdout.flush()
if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.ExitProcess.argtypes = [ctypes.c_uint]
    kernel32.ExitProcess.restype = None
    kernel32.ExitProcess(ctypes.c_uint(0xC0000017))
else:
    import os, signal
    os.kill(os.getpid(), signal.SIGKILL)
raise SystemExit("fixture failed to terminate -- the drill proves nothing")
"""

_HONEST_FAILURE = """
print("GATE_PROBE = 3/7")
raise SystemExit(1)
"""


def _row_for(body: str, name: str, td: str) -> dict:
    p = Path(td) / f"{name}.py"
    p.write_text(body, encoding="utf-8")
    return _row(name, [sys.executable, str(p)], cwd=Path(td), budget=30)


def test_a_killed_row_is_unmeasured() -> None:
    with tempfile.TemporaryDirectory() as td:
        r = _row_for(_SUICIDE, "taken", td)
    if r.get("killed") and "not a verdict" in r["summary"]:
        _ok("V-UNMEASURED-KILLED",
            f"rc={r['rc']} classified killed, summary says not a verdict")
    else:
        _fail("V-UNMEASURED-KILLED",
              f"rc={r['rc']} killed={r.get('killed')} summary={r['summary']!r}")


def test_an_honest_failure_is_still_a_failure() -> None:
    """NEGATIVE CONTROL. Without it, marking every non-zero row 'killed' would
    pass the case above and silently convert every real defect into a shrug."""
    with tempfile.TemporaryDirectory() as td:
        r = _row_for(_HONEST_FAILURE, "honest", td)
    if r["rc"] == 1 and not r.get("killed"):
        _ok("V-UNMEASURED-CONTROL", "rc=1 stayed a failure, not a kill")
    else:
        _fail("V-UNMEASURED-CONTROL",
              f"rc={r['rc']} killed={r.get('killed')} -- a real defect was excused")


def test_a_passing_row_is_not_disturbed() -> None:
    with tempfile.TemporaryDirectory() as td:
        r = _row_for("print('PROBE = 6/6')\n", "clean", td)
    if r["rc"] == 0 and not r.get("killed") and "6/6" in r["summary"]:
        _ok("V-UNMEASURED-CLEAN", "rc=0 untouched, summary preserved")
    else:
        _fail("V-UNMEASURED-CLEAN", f"rc={r['rc']} summary={r['summary']!r}")


def test_a_timeout_is_still_distinguishable_from_a_kill() -> None:
    """Same epistemic status, different causes. Collapsing them would lose the
    only signal that says whether to raise a budget or free memory."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "slow.py"
        p.write_text("import time; time.sleep(30)\n", encoding="utf-8")
        r = _row("slow", [sys.executable, str(p)], cwd=Path(td), budget=2)
    if r.get("timed_out") and not r.get("killed") and r["rc"] == 124:
        _ok("V-UNMEASURED-TIMEOUT", "timeout kept its own class and rc=124")
    else:
        _fail("V-UNMEASURED-TIMEOUT",
              f"rc={r['rc']} timed_out={r.get('timed_out')} killed={r.get('killed')}")


def main() -> int:
    print("=" * 70)
    print("test_verify_spp_unmeasured -- V-UNMEASURED-* (synthetic subjects)")
    print("=" * 70)
    for fn in (
        test_taken_codes_are_recognised,
        test_honest_exit_codes_are_not_kills,
        test_a_killed_row_is_unmeasured,
        test_an_honest_failure_is_still_a_failure,
        test_a_passing_row_is_not_disturbed,
        test_a_timeout_is_still_distinguishable_from_a_kill,
    ):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            # An instrument that crashed judged nothing. Report it as the
            # instrument failing, outranking any subject finding in this run.
            _fail(fn.__name__, f"INSTRUMENT FAILED: {type(exc).__name__}: {exc}")
    total = _passes + _fails
    print("=" * 70)
    print(f"UNMEASURED_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
