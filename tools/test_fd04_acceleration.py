#!/usr/bin/env python3
"""V-gate for epistemic acceleration (SEIP-EXT-M2).

The load-bearing property is V-ACCEL-STALL-BEATS-TREND. The live ledger's interior
points are tightly spaced -- an unguarded cadence trend would report ACCELERATING for a
proving loop that has not run in three weeks. True about the window, false about the
institution. Staleness must short-circuit the trend, never lose to it.

    python tools/test_fd04_acceleration.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.fable_distillation import fd_04_acceleration as A   # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_REPO = "unit-test-repo"


def _write(d: Path, rows: list) -> None:
    from modules.fable_distillation.fd_04_prover import _proofs_path
    p = _proofs_path(_REPO, d)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


def _rec(offset_s: int, fp: str, target: str = "deterministic") -> dict:
    return {"fingerprint": fp, "verdict": "PROVEN", "achieved_target": target,
            "ts": (_T0 + timedelta(seconds=offset_s)).isoformat()}


def main() -> int:
    print("EPISTEMIC ACCELERATION V-GATE (SEIP-EXT-M2)")

    # --- staleness outranks a flattering interior -------------------------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        # Eight proofs, each closer together than the last: a textbook ACCELERATING
        # interior. But the ledger then goes quiet for a year.
        rows, t = [], 0
        for i, gap in enumerate([8000, 7000, 6000, 5000, 4000, 3000, 2000]):
            rows.append(_rec(t, f"fp{i}"))
            t += gap
        rows.append(_rec(t, "fp7"))
        _write(d, rows)
        r = A.measure(_REPO, d, now=_T0 + timedelta(days=400))
        if r["verdict"] == A.STALLED:
            _ok("V-ACCEL-STALL-BEATS-TREND",
                f"{r['proofs']} proofs with a monotonically tightening interval still "
                f"return STALLED after {r['days_since_last']:.0f} quiet days -- the "
                "flattering reading does not win by default")
        else:
            _fail("V-ACCEL-STALL-BEATS-TREND", f"got {r['verdict']}: {r['reason']}")

        # Same ledger, read while still warm -> the trend is allowed to speak.
        r = A.measure(_REPO, d, now=_T0 + timedelta(seconds=t + 100))
        if r["verdict"] == A.ACCELERATING and r["mean_gap_seconds_late"] < \
                r["mean_gap_seconds_early"]:
            _ok("V-ACCEL-TREND-WHEN-WARM",
                f"a live ledger reports ACCELERATING: mean interval "
                f"{r['mean_gap_seconds_early']:.0f}s -> {r['mean_gap_seconds_late']:.0f}s")
        else:
            _fail("V-ACCEL-TREND-WHEN-WARM", f"got {r['verdict']}: {r['reason']}")

    # --- a decelerating ledger is named as such ------------------------------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        rows, t = [], 0
        for i, gap in enumerate([1000, 2000, 3000, 4000, 5000, 6000, 7000]):
            rows.append(_rec(t, f"fp{i}"))
            t += gap
        rows.append(_rec(t, "fp7"))
        _write(d, rows)
        r = A.measure(_REPO, d, now=_T0 + timedelta(seconds=t + 100))
        if r["verdict"] == A.DECELERATING:
            _ok("V-ACCEL-DECELERATING",
                "a widening interval is reported as DECELERATING, so the metric can "
                "return bad news about its own institution")
        else:
            _fail("V-ACCEL-DECELERATING", f"got {r['verdict']}")

    # --- one observation per claim cannot show a claim getting cheaper ---------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _write(d, [_rec(i * 1000, f"fp{i}") for i in range(8)])
        r = A.measure(_REPO, d, now=_T0 + timedelta(seconds=9000))
        cd = r["cost_descent"]
        if cd["verdict"] == A.UNMEASURABLE and cd["repeated_claims"] == 0:
            _ok("V-ACCEL-NO-DESCENT-FROM-SINGLE-POINT",
                "8 claims each proven once yield UNMEASURABLE cost descent, not FLAT "
                "-- a trend needs more than one observation per subject")
        else:
            _fail("V-ACCEL-NO-DESCENT-FROM-SINGLE-POINT", f"got {cd}")

    # --- a genuine descent is detected -------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        rows = [_rec(i * 1000, f"fp{i}") for i in range(6)]
        rows += [_rec(7000, "cheap", "mid-model"), _rec(8000, "cheap", "deterministic")]
        _write(d, rows)
        cd = A.measure(_REPO, d, now=_T0 + timedelta(seconds=9000))["cost_descent"]
        if cd["verdict"] == A.ACCELERATING and cd["descended"] == 1:
            _ok("V-ACCEL-DESCENT-DETECTED",
                "a claim re-proven mid-model -> deterministic is counted as one "
                "descent on the cost ladder")
        else:
            _fail("V-ACCEL-DESCENT-DETECTED", f"got {cd}")

    # --- thin and absent ledgers ---------------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _write(d, [_rec(0, "a"), _rec(100, "b")])
        r = A.measure(_REPO, d, now=_T0 + timedelta(seconds=200))
        if r["verdict"] == A.UNMEASURABLE and str(A.MIN_PROOFS_FOR_TREND) in r["reason"]:
            _ok("V-ACCEL-THIN-IS-UNMEASURABLE",
                f"2 proofs is below the floor of {A.MIN_PROOFS_FOR_TREND} and the "
                "reason names it")
        else:
            _fail("V-ACCEL-THIN-IS-UNMEASURABLE", f"got {r['verdict']}")

    try:
        r = A.measure("no-such-repo-xyz", Path(tempfile.gettempdir()) / "nope-xyz")
        if r["verdict"] == A.UNMEASURABLE and r["proofs"] == 0:
            _ok("V-ACCEL-FAILOPEN",
                "an absent ledger is UNMEASURABLE with zero counts, not an exception")
        else:
            _fail("V-ACCEL-FAILOPEN", f"got {r}")
    except Exception as e:                                   # noqa: BLE001
        _fail("V-ACCEL-FAILOPEN", f"raised {type(e).__name__}: {e}")

    # --- the live ledger -------------------------------------------------------------------
    live = A.measure()
    if live["verdict"] in (A.STALLED, A.UNMEASURABLE, A.ACCELERATING,
                           A.DECELERATING, A.FLAT):
        _ok("V-ACCEL-LIVE",
            f"live FD-04 ledger: {live['proofs']} proofs / {live['claims']} claims, "
            f"span {live['span_days']}d, quiet {live['days_since_last']}d -> "
            f"{live['verdict']}")
    else:
        _fail("V-ACCEL-LIVE", f"unexpected verdict {live['verdict']}")

    total = _passes + _fails
    print(f"\nACCELERATION_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
