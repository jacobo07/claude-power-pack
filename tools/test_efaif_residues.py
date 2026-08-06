#!/usr/bin/env python3
"""V-gates for the two EFAIF residues (vault/plans/efaif-corpus-2026-08-04.md).

R1 -- modules/craif/oier.py: the producer CRAIF Part XIII never had.
R2 -- modules/spec_gate/gate.py::check_reframing_gate: the trigger the
      lateral-thinking frames never had.

Hermetic by construction: every ledger path is a fresh tempfile, so the suite
never reads or writes vault/craif_registry/ and repeated runs cannot drift
(feedback_hermetic_test_global_writes_time_window -- a gate that writes a
global directory is non-hermetic and its second run measures its first).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.craif.oier import (  # noqa: E402
    EscapeClass, SurfacedBy, harvest_owner_queue, read, record)
from modules.spec_gate.gate import check_reframing_gate  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate}  --  {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}  --  {diagnostic}")


def _tmp() -> Path:
    fd, name = tempfile.mkstemp(suffix=".jsonl", prefix="oier_")
    import os
    os.close(fd)
    os.unlink(name)          # want the path, not the file
    return Path(name)


# --- R1: OIER producer --------------------------------------------------

def t_empty_is_unmeasured() -> None:
    r = read(_tmp())
    if r.rate is None and r.measurable is False:
        _ok("V-OIER-EMPTY-UNMEASURED",
            f"rate={r.rate} measurable={r.measurable}")
    else:
        _fail("V-OIER-EMPTY-UNMEASURED",
              f"empty ledger asserted rate={r.rate!r} measurable={r.measurable} "
              "-- an empty ledger must not report the best possible score")


def t_producer_writes() -> None:
    p = _tmp()
    wrote = record("D-1", SurfacedBy.SYSTEM, EscapeClass.DETECTOR_GAP,
                   detector="liveness", path=p)
    r = read(p)
    if wrote and r.denominator == 1 and r.system_surfaced == 1:
        _ok("V-OIER-PRODUCER-WRITES",
            f"append=True denominator={r.denominator} system={r.system_surfaced}")
    else:
        _fail("V-OIER-PRODUCER-WRITES",
              f"append={wrote} denominator={r.denominator} "
              f"system={r.system_surfaced}")


def t_detector_gap_counts() -> None:
    p = _tmp()
    record("D-1", SurfacedBy.OWNER, EscapeClass.DETECTOR_GAP, path=p)
    record("D-2", SurfacedBy.SYSTEM, EscapeClass.DETECTOR_GAP, path=p)
    r = read(p)
    if r.measurable and r.escapes == 1 and r.denominator == 2 and r.rate == 0.5:
        _ok("V-OIER-DETECTOR-GAP-COUNTS",
            f"rate={r.rate} escapes={r.escapes}/{r.denominator}")
    else:
        _fail("V-OIER-DETECTOR-GAP-COUNTS",
              f"rate={r.rate} escapes={r.escapes} denom={r.denominator}")


def t_authority_block_excluded() -> None:
    p = _tmp()
    record("D-1", SurfacedBy.OWNER, EscapeClass.DETECTOR_GAP, path=p)
    for i in range(9):
        record(f"OQ-{i}", SurfacedBy.OWNER, EscapeClass.AUTHORITY_BLOCK, path=p)
    r = read(p)
    # 9 authority blocks must not dilute the one real escape toward 0.1.
    if r.denominator == 1 and r.rate == 1.0 and r.excluded_authority_blocks == 9:
        _ok("V-OIER-AUTHORITY-EXCLUDED",
            f"rate={r.rate} denom={r.denominator} excluded=9")
    else:
        _fail("V-OIER-AUTHORITY-EXCLUDED",
              f"rate={r.rate} denom={r.denominator} "
              f"excluded={r.excluded_authority_blocks} -- a designed boundary "
              "leaked into the escape rate")


def t_unclassified_never_numerator() -> None:
    p = _tmp()
    record("D-1", SurfacedBy.OWNER, EscapeClass.UNCLASSIFIED, path=p)
    r = read(p)
    if r.escapes == 0 and r.denominator == 1 and r.rate == 0.0:
        _ok("V-OIER-UNCLASSIFIED-NOT-NUMERATOR",
            f"escapes={r.escapes} denom={r.denominator} unclassified={r.unclassified}")
    else:
        _fail("V-OIER-UNCLASSIFIED-NOT-NUMERATOR",
              f"escapes={r.escapes} denom={r.denominator} rate={r.rate}")


def t_harvest_idempotent() -> None:
    p = _tmp()
    qfd = Path(tempfile.mkstemp(suffix=".md", prefix="oq_")[1])
    qfd.write_text(
        "# OWNER_QUEUE\n\n"
        "## NEW (2026-08-03) -- activate the Session Delta Gate  [PENDING]\n\n"
        "body\n\n"
        "## NEW (2026-07-30) -- wire the beacon  [DONE]\n\nbody\n",
        encoding="utf-8")
    first = harvest_owner_queue(qfd, p)
    second = harvest_owner_queue(qfd, p)
    r = read(p)
    if first == 2 and second == 0 and r.denominator == 0:
        _ok("V-OIER-HARVEST-IDEMPOTENT",
            f"first={first} second={second} denom={r.denominator} (all blocks)")
    else:
        _fail("V-OIER-HARVEST-IDEMPOTENT",
              f"first={first} second={second} denom={r.denominator}")


def t_append_is_lf_only() -> None:
    p = _tmp()
    record("D-1", SurfacedBy.SYSTEM, EscapeClass.DETECTOR_GAP, path=p)
    record("D-2", SurfacedBy.SYSTEM, EscapeClass.DETECTOR_GAP, path=p)
    raw = p.read_bytes()
    lf = raw.count(bytes([10]))
    crlf = raw.count(bytes([13, 10]))
    if crlf == 0 and lf == 2:
        _ok("V-OIER-APPEND-LF-ONLY", f"{lf} LF, 0 CRLF")
    else:
        _fail("V-OIER-APPEND-LF-ONLY",
              f"crlf={crlf} lf={lf} -- Windows text-mode compounding")


# --- R2: reframing gate -------------------------------------------------

def t_reframe_fires() -> None:
    v = check_reframing_gate(
        "Build a new agent workflow module that generates weekly reports.")
    if v.applies and len(v.frames) == 5:
        _ok("V-REFRAME-FIRES", f"matched={v.matched!r} frames={len(v.frames)}")
    else:
        _fail("V-REFRAME-FIRES",
              f"applies={v.applies} matched={v.matched!r} -- a tier-2 build "
              "with no stated problem did not trip the gate")


def t_reframe_clears_on_problem() -> None:
    v = check_reframing_gate(
        "Build a new agent workflow module because the nightly report "
        "currently fails whenever the API times out.")
    if not v.applies:
        _ok("V-REFRAME-CLEARS-ON-PROBLEM", v.message[:70])
    else:
        _fail("V-REFRAME-CLEARS-ON-PROBLEM",
              "gate fired even though a problem was stated -- false alarm")


def t_reframe_tier_exempt() -> None:
    v = check_reframing_gate("Fix a typo in the README label.")
    if not v.applies:
        _ok("V-REFRAME-TIER-EXEMPT", v.message[:70])
    else:
        _fail("V-REFRAME-TIER-EXEMPT",
              "gate fired on micro work -- reframing a typo is theater")


def t_reframe_no_solution_signal() -> None:
    v = check_reframing_gate(
        "Which module owns the authorization schema for the billing API?")
    if not v.applies:
        _ok("V-REFRAME-NO-SOLUTION", v.message[:70])
    else:
        _fail("V-REFRAME-NO-SOLUTION",
              "gate fired on a question with no solution commitment")


def main() -> int:
    print("EFAIF residues -- R1 (OIER producer) + R2 (reframing gate)\n")
    print("R1 -- modules/craif/oier.py")
    t_empty_is_unmeasured()
    t_producer_writes()
    t_detector_gap_counts()
    t_authority_block_excluded()
    t_unclassified_never_numerator()
    t_harvest_idempotent()
    t_append_is_lf_only()
    print("\nR2 -- modules/spec_gate/gate.py::check_reframing_gate")
    t_reframe_fires()
    t_reframe_clears_on_problem()
    t_reframe_tier_exempt()
    t_reframe_no_solution_signal()
    total = _passes + _fails
    print(f"\nEFAIF_RESIDUES_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
