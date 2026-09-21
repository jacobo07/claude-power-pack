"""V-PW-* : the PROVEN verdict measures CURRENT capability, not lifetime purity.

I proposed this rule change while it happened to unblock my own milestone, which
is the worst possible provenance for a loosened gate. So the load-bearing gates
here are the ones that still say NO, and one gate asserts the change is not a
no-op -- a "fix" that leaves the predicate equivalent would otherwise ship as a
comment with a green suite behind it.

Hermetic: `ledger_events` is replaced with synthetic event lists, so nothing
under ~/.claude is read and these cannot decay when a real ledger moves on.

  0  every case landed on its verdict
  1  a case produced the wrong verdict
  2  HARNESS-FAILED -- the module could not be loaded or driven

Usage:  python tools/test_proven_window.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

passes = fails = 0


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {evidence}")


def _fail(gate: str, evidence: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {evidence}")


def _load():
    spec = importlib.util.spec_from_file_location("_lr_pw", REPO / "tools" / "gsd_long_run.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_lr_pw"] = mod
    spec.loader.exec_module(mod)
    return mod


def _events(pattern: str) -> list[dict]:
    """'X.X' -> two crossings, neither confirmed. 'C' confirms the crossing before it.

    e.g. 'X XC XC' (spaces ignored) = crossing, crossing+confirm, crossing+confirm.
    """
    out: list[dict] = []
    n = 0
    for ch in pattern.replace(" ", ""):
        if ch == "X":
            n += 1
            out.append({"event": "crossing", "ts": f"2026-09-2{n}T00:00:00+00:00"})
        elif ch == "C":
            out.append({"event": "resume_confirmed", "ts": f"2026-09-2{n}T01:00:00+00:00"})
    return out


def _old_verdict(cycles: list[dict]) -> str:
    """The predicate as it stood before 2026-09-21, for the no-op control."""
    confirmed = sum(1 for c in cycles if c["confirmed"])
    if len(cycles) >= 2 and confirmed == len(cycles):
        return "PROVEN"
    return "PARTIAL" if confirmed else ("UNPROVEN" if cycles else "NO_CROSSINGS")


CASES = [
    # gate,                              pattern,      expect,        why this case exists
    ("V-PW-TWO-CLEAN-IS-PROVEN", "XC XC", "PROVEN",
     "the plain success: two crossings, both confirmed"),
    ("V-PW-EARLY-FAILURE-IS-FORGIVEN", "X XC XC", "PROVEN",
     "THE CHANGE: one early miss no longer bars the session forever"),
    ("V-PW-REGRESSION-REVOKES-PROVEN", "XC XC X", "PARTIAL",
     "THE REFUSAL: a fresh missed crossing drops it back, so PROVEN is not a "
     "badge once earned"),
    ("V-PW-OLD-SUCCESS-CANNOT-BE-BANKED", "XC X X", "PARTIAL",
     "two recent misses are not offset by an older confirmation"),
    ("V-PW-ONE-CROSSING-IS-NOT-ENOUGH", "XC", "PARTIAL",
     "the window still demands TWO; a single confirmation never proves "
     "continuation"),
    ("V-PW-NONE-CONFIRMED-IS-UNPROVEN", "X X", "UNPROVEN",
     "crossings with no confirmation at all"),
    ("V-PW-NO-CROSSINGS-IS-ITS-OWN-ANSWER", "", "NO_CROSSINGS",
     "nothing happened is not a failure of the transport"),
]


def main() -> int:
    try:
        lr = _load()
    except Exception as exc:                                   # noqa: BLE001
        print(f"HARNESS-FAILED: cannot load gsd_long_run: {exc!r}")
        return 2
    if not hasattr(lr, "PROVEN_WINDOW"):
        print("HARNESS-FAILED: gsd_long_run exposes no PROVEN_WINDOW")
        return 2

    real = lr.ledger_events
    try:
        for gate, pattern, expect, why in CASES:
            lr.ledger_events = lambda _sid, _p=pattern: _events(_p)
            got = lr.report("syn")
            if got["verdict"] == expect:
                _ok(gate, f"{pattern or '(no events)'!r} -> {expect} -- {why}")
            else:
                _fail(gate, f"{pattern or '(no events)'!r} -> {got['verdict']}, expected "
                            f"{expect} -- {why}")

        # The change must CHANGE something. Without this, a report() whose
        # predicate was left untouched passes every case above that the old rule
        # also passed, and the only failing case would be the one I wrote the
        # change for -- which is indistinguishable from a bug.
        lr.ledger_events = lambda _sid: _events("X XC XC")
        got = lr.report("syn")
        old = _old_verdict(got["cycles"])
        if old == "PARTIAL" and got["verdict"] == "PROVEN":
            _ok("V-PW-CHANGE-IS-NOT-A-NO-OP",
                "on 'X XC XC' the old predicate says PARTIAL and the new one says "
                "PROVEN -- the rule genuinely moved, and this is the ONLY shape it "
                "moved for")
        else:
            _fail("V-PW-CHANGE-IS-NOT-A-NO-OP",
                  f"old={old} new={got['verdict']} -- the predicate did not move as "
                  "documented")

        # Narrowing the VERDICT must not narrow the EVIDENCE. A reader has to be
        # able to see the history the window is stepping over, or the gate has
        # quietly deleted the thing that made it arguable.
        lr.ledger_events = lambda _sid: _events("X XC X X X X XC")
        got = lr.report("syn")
        if got["crossings"] == 7 and got["confirmed"] == 2:
            _ok("V-PW-EVIDENCE-STAYS-WHOLE",
                "a 7-crossing / 2-confirmed history still reports crossings=7 "
                "confirmed=2 beside the verdict; only the verdict uses the window")
        else:
            _fail("V-PW-EVIDENCE-STAYS-WHOLE",
                  f"crossings={got['crossings']} confirmed={got['confirmed']} -- the "
                  "window leaked into the evidence")

        # And that same real-world shape must NOT come out PROVEN: its last two
        # crossings are X then XC, so the window is not clean.
        if got["verdict"] == "PARTIAL":
            _ok("V-PW-REAL-SHAPE-STILL-REFUSED",
                "the actual 37cfb187 shape (7 crossings, 2 confirmed, last two not "
                "both confirmed) stays PARTIAL -- the change did not hand this "
                "milestone a free pass")
        else:
            _fail("V-PW-REAL-SHAPE-STILL-REFUSED",
                  f"the 37cfb187 shape now reads {got['verdict']} -- the rule change "
                  "rubber-stamped the very session that motivated it")
    finally:
        lr.ledger_events = real

    total = passes + fails
    print(f"PW_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
