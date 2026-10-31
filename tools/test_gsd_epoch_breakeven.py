"""V-EPOCH-BE gates: rollover breakeven is advisory, never rotates, never turns missing input into ROTATE.
    python tools/test_gsd_epoch_breakeven.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_epoch as ge  # noqa: E402

passes = fails = 0


def gate(name, cond, evidence):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {name}: {evidence}")


def main() -> int:
    big = dict(successor_floor=60_000, bootstrap_tokens=150_000)
    r = ge.breakeven_advisory(230_000, 40, at_boundary=True, **big)
    gate("V-EPOCH-BE-ROTATE", r["verdict"] == "ROTATE_ADVISED" and r["saving_tokens"] == 40 * 170_000 - 150_000,
         r)
    gate("V-EPOCH-BE-BREAKEVEN-CALLS", r["breakeven_calls"] == 1, r["breakeven_calls"])
    r = ge.breakeven_advisory(230_000, 40, at_boundary=False, **big)
    gate("V-EPOCH-BE-HOLD-NO-BOUNDARY", r["verdict"] == "HOLD_UNTIL_BOUNDARY", r["verdict"])
    r = ge.breakeven_advisory(230_000, 0, at_boundary=True, **big)
    gate("V-EPOCH-BE-CONTINUE-NEAR-END", r["verdict"] == "CONTINUE", r["verdict"])
    r = ge.breakeven_advisory(70_000, 5, at_boundary=True, successor_floor=60_000, bootstrap_tokens=150_000)
    gate("V-EPOCH-BE-CONTINUE-SMALL-CTX", r["verdict"] == "CONTINUE" and r["breakeven_calls"] == 15, r)
    r = ge.breakeven_advisory(50_000, 99, at_boundary=True, **big)
    gate("V-EPOCH-BE-NO-GAIN", r["verdict"] == "CONTINUE" and r["breakeven_calls"] is None, r)
    r = ge.breakeven_advisory(None, 40, at_boundary=True, **big)
    gate("V-EPOCH-BE-UNMEASURED", r["verdict"] == "UNMEASURED" and "context_tokens" in r["missing"], r)
    r = ge.breakeven_advisory(230_000, 40, at_boundary=True, page_in_tokens=10_000_000, **big)
    gate("V-EPOCH-BE-PAGEIN-FLIPS", r["verdict"] == "CONTINUE", r["verdict"])
    gate("V-EPOCH-BE-ADVISORY", all(ge.breakeven_advisory(1, 1, successor_floor=1, bootstrap_tokens=1,
                                                         at_boundary=b)["advisory_only"] for b in (0, 1)), "flag")
    print(f"EPOCH_BE_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
