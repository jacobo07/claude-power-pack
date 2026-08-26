"""V-BENCH-* -- the benchmark gate must measure what it says it measures.

The probe's docstring promised a 1.5x band for T-WIN-AV-001 spawn
variance and the code compared against the raw target, then printed
"over 1.5x target". It was stricter than its contract AND misreported
the threshold it used, so four benchmarks inside the band were named as
failures while the one benchmark genuinely 2.4x over target sat in the
same list, indistinguishable.

These gates assert against RECONSTRUCTIONS of that bug: the live tree no
longer contains it, so a test that only exercised the current code would
pass for the wrong reason. Every "rejects X" gate is paired with an
"admits Y" bookend -- a gate that can only say NO is indistinguishable
from a gate that is broken.
"""
from __future__ import annotations

import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from tools.verify_bench_all import (  # noqa: E402
    BAND, QUICK_TARGETS, evaluate,
)

EXPECTED_GATES = 10
_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  FAIL {gate}: {diagnostic}")


def full(**over):
    """A results dict with every quick benchmark comfortably passing."""
    r = {n: t * 0.5 for n, t in QUICK_TARGETS.items()}
    r.update(over)
    return r


def main() -> int:
    # --- the band exists and is the documented number --------------------
    if BAND == 1.5:
        _ok("V-BENCH-BAND-VALUE", f"BAND={BAND}, the documented allowance")
    else:
        _fail("V-BENCH-BAND-VALUE", f"BAND={BAND}, expected 1.5")

    # --- THE BUG: raw-target comparison ---------------------------------
    # 268 vs target 225 was reported as a failure. 1.5x225 = 337.5, so it
    # was inside the band the probe claimed to use. This is the exact
    # observed false positive, replayed.
    _m, over = evaluate(full(tis_report_ms=268))
    if not over:
        _ok("V-BENCH-BAND-APPLIED",
            "tis_report_ms=268 (target 225, band 337) admitted")
    else:
        _fail("V-BENCH-BAND-APPLIED",
              f"268 rejected against a 337 band: {over}")

    # tco_gate_ms=357 was the other reported 'pre-existing drift'.
    _m, over = evaluate(full(tco_gate_ms=357))
    if not over:
        _ok("V-BENCH-BAND-APPLIED-2",
            "tco_gate_ms=357 (target 270, band 405) admitted")
    else:
        _fail("V-BENCH-BAND-APPLIED-2", f"357 rejected: {over}")

    # --- bookend: over the band still fails ------------------------------
    _m, over = evaluate(full(session_hub_ms=1301))
    if "session_hub_ms" in over:
        _ok("V-BENCH-OVER-BAND-REJECTED",
            "session_hub_ms=1301 (band 450) rejected -- the real one")
    else:
        _fail("V-BENCH-OVER-BAND-REJECTED",
              "a 4.3x-target value was admitted; the gate cannot say NO")

    # --- boundary: exactly at the band is not over -----------------------
    at_band = QUICK_TARGETS["never_again_ms"] * BAND
    _m, over = evaluate(full(never_again_ms=at_band))
    if not over:
        _ok("V-BENCH-BAND-BOUNDARY", f"exactly {at_band:.0f} is admitted")
    else:
        _fail("V-BENCH-BAND-BOUNDARY", f"{at_band:.0f} rejected at boundary")

    # --- missing must not read as OK -------------------------------------
    partial = full()
    partial.pop("session_hub_ms")
    missing, _o = evaluate(partial)
    if missing == ["session_hub_ms"]:
        _ok("V-BENCH-MISSING-IS-FAILURE",
            "an unreported benchmark is named, not skipped")
    else:
        _fail("V-BENCH-MISSING-IS-FAILURE",
              f"missing={missing}; a broken probe would make this greener")

    # bookend: nothing missing when everything reports
    missing, _o = evaluate(full())
    if missing == []:
        _ok("V-BENCH-MISSING-BOOKEND", "a complete sample reports no gaps")
    else:
        _fail("V-BENCH-MISSING-BOOKEND", f"false gaps: {missing}")

    # --- retry semantics -------------------------------------------------
    # Variance: first sample over band, second inside -> absorbed.
    _m, over = evaluate(full(osa_dispatcher_ms=1008),
                        full(osa_dispatcher_ms=194))
    if not over:
        _ok("V-BENCH-RETRY-ABSORBS-NOISE",
            "1008 then 194 -> min 194 admitted (measured spread was 418%)")
    else:
        _fail("V-BENCH-RETRY-ABSORBS-NOISE", f"noise not absorbed: {over}")

    # A real regression reproduces and must survive the retry.
    _m, over = evaluate(full(session_hub_ms=1359),
                        full(session_hub_ms=734))
    if "session_hub_ms" in over and over["session_hub_ms"] == 734:
        _ok("V-BENCH-RETRY-KEEPS-REAL",
            "1359 then 734 -> min 734 still over band 450")
    else:
        _fail("V-BENCH-RETRY-KEEPS-REAL",
              f"a reproducing 2.4x regression escaped: {over}")

    # The retry must not be able to INVENT a pass by picking the max.
    _m, over = evaluate(full(session_hub_ms=734),
                        full(session_hub_ms=1359))
    if over.get("session_hub_ms") == 734:
        _ok("V-BENCH-RETRY-ORDER-FREE",
            "sample order does not change the verdict")
    else:
        _fail("V-BENCH-RETRY-ORDER-FREE",
              f"verdict depends on which sample came first: {over}")

    ran = len(_passes) + len(_fails)
    print(f"\nBENCH_GATE_PASS={len(_passes)}/{ran}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if ran != EXPECTED_GATES:
        # A skipped assertion must fail the suite, not shrink its
        # denominator. This repo has been bitten by a printed threshold
        # that did not match the gates that actually ran.
        print(f"GATE COUNT MISMATCH: {ran} ran, {EXPECTED_GATES} expected")
        return 1
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
