#!/usr/bin/env python3
"""V-gate for predictive cascade detection (SEIP-EXT-D3).

The load-bearing property is V-PRED-WINDOW-MUST-DISCRIMINATE. A co-occurrence window
wider than the entire recorded span pairs every event with every other, so it imposes no
ordering at all -- the sealed `feedback_constant_factors_rank_nothing` shape. A detector
built on that fires always, and firing always is indistinguishable from not detecting.

    python tools/test_cascade_predictive.py
"""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.cascade_prevention import engine, predictive as P   # noqa: E402
from modules.cascade_prevention.types import CascadeHit, CascadeSeverity, CascadeType  # noqa: E402,E501

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


def _ev(offset_s: int, category: str) -> dict:
    return {"ts": _T0 + timedelta(seconds=offset_s), "category": category, "id": "x"}


def _spread(pairs: int = 3) -> list:
    """A store where A genuinely precedes B, spread over hours so a 300s window
    discriminates and each transition is a separate episode."""
    out = []
    for i in range(pairs):
        base = i * 7200
        out += [_ev(base, "alpha"), _ev(base + 60, "beta")]
    out.append(_ev(pairs * 7200 + 100_000, "gamma"))     # widen the span
    return sorted(out, key=lambda r: r["ts"])


def main() -> int:
    print("PREDICTIVE CASCADE V-GATE (SEIP-EXT-D3)")

    # --- the constant-factor trap ------------------------------------------------
    burst = [_ev(0, "a"), _ev(1, "b"), _ev(1, "c")]
    q = P.substrate_quality(burst, window_s=300)
    if q["verdict"] == P.SUBSTRATE_DEGENERATE and q["window_discriminates"] is False:
        _ok("V-PRED-WINDOW-MUST-DISCRIMINATE",
            f"a 300s window over a {q['span_seconds']:g}s span is refused -- it pairs "
            "every event with every other and so ranks nothing")
    else:
        _fail("V-PRED-WINDOW-MUST-DISCRIMINATE", f"got {q}")

    p = P.predict("a", burst)
    if p["verdict"] == P.UNMEASURABLE and p["prior"] is None:
        _ok("V-PRED-NO-PRIOR-FROM-DEGENERATE",
            "a degenerate store yields UNMEASURABLE with prior=None, never a number "
            "carrying the authority of measurement without the content")
    else:
        _fail("V-PRED-NO-PRIOR-FROM-DEGENERATE", f"got {p['verdict']} / {p['prior']}")

    # --- a real chain -------------------------------------------------------------
    good = _spread(3)
    q = P.substrate_quality(good, window_s=300)
    p = P.predict("alpha", good)
    if q["verdict"] == P.SUBSTRATE_OK and p["verdict"] == P.PREDICTED \
            and p["predicts"] == "beta" and p["prior"] == 1.0:
        _ok("V-PRED-REAL-CHAIN",
            f"3 spread-out alpha->beta episodes yield PREDICTED beta, prior 1.0, "
            f"basis {p['basis']!r}")
    else:
        _fail("V-PRED-REAL-CHAIN", f"substrate={q['verdict']} predict={p}")

    # --- one sighting is an anecdote ------------------------------------------------
    thin = _spread(1)
    p = P.predict("alpha", thin)
    if p["verdict"] in (P.NOT_PREDICTED, P.UNMEASURABLE) and p["prior"] is None:
        _ok("V-PRED-ONE-SIGHTING-INSUFFICIENT",
            f"a single alpha->beta transition does not predict ({p['verdict']}); "
            f"{P.MIN_COOCCURRENCE} is the floor for a pattern")
    else:
        _fail("V-PRED-ONE-SIGHTING-INSUFFICIENT", f"got {p['verdict']} {p['prior']}")

    # --- the session detector is no longer a stub -------------------------------------
    hits = engine.detect("session", {"last_error_category": "alpha", "events": good})
    if len(hits) == 1 and hits[0].cascade_type == CascadeType.PREDICTED_SUCCESSOR \
            and hits[0].is_predictive and hits[0].severity == CascadeSeverity.C3:
        _ok("V-PRED-SESSION-DETECTOR-WIRED",
            "engine.detect('session') now returns a predictive C3 hit; it returned [] "
            "unconditionally before, so its silence meant nothing")
    else:
        _fail("V-PRED-SESSION-DETECTOR-WIRED", f"got {hits}")

    silent = engine.detect("session", {"last_error_category": "a", "events": burst})
    if silent == []:
        _ok("V-PRED-SILENT-ON-DEGENERATE",
            "a degenerate store still produces no hit -- the prediction is advisory "
            "and must never be manufactured to justify the surface")
    else:
        _fail("V-PRED-SILENT-ON-DEGENERATE", f"got {silent}")

    # --- a hit without evidence is not predictive --------------------------------------
    plain = CascadeHit(cascade_type=CascadeType.SCOPE_CREEP,
                       severity=CascadeSeverity.C3, surface="task", reason="r")
    if plain.is_predictive is False and plain.prior is None \
            and plain.should_warn is True:
        _ok("V-PRED-BACKWARD-COMPATIBLE",
            "the existing 4-field construction still works, still warns, and is not "
            "predictive -- None means unmeasured, never no-risk")
    else:
        _fail("V-PRED-BACKWARD-COMPATIBLE", f"got {plain}")

    # --- fail-open ----------------------------------------------------------------------
    try:
        missing = P.load_events(Path(tempfile.gettempdir()) / "no-such-ceps-xyz.jsonl")
        q = P.substrate_quality(missing)
        if missing == [] and q["verdict"] == P.SUBSTRATE_ABSENT:
            _ok("V-PRED-FAILOPEN",
                "an absent store is SUBSTRATE_ABSENT, not an exception")
        else:
            _fail("V-PRED-FAILOPEN", f"got {q['verdict']}")
    except Exception as e:                                   # noqa: BLE001
        _fail("V-PRED-FAILOPEN", f"raised {type(e).__name__}: {e}")

    # --- the live store -------------------------------------------------------------------
    live = P.substrate_quality()
    if live["verdict"] == P.SUBSTRATE_DEGENERATE and live["pairs_at_threshold"] == 0:
        _ok("V-PRED-LIVE-SUBSTRATE-NAMED",
            f"live CEPS store: {live['events']} events, "
            f"{live['distinct_timestamps']} distinct timestamps, span "
            f"{live['span_seconds']:g}s -- degeneracy is now NAMED rather than "
            f"showing up as silence")
    elif live["verdict"] == P.SUBSTRATE_OK:
        _ok("V-PRED-LIVE-SUBSTRATE-NAMED",
            f"live store now supports inference: {live['pairs_at_threshold']} pair(s) "
            f"at threshold -- the gate tracks reality rather than pinning it")
    else:
        _fail("V-PRED-LIVE-SUBSTRATE-NAMED", f"unexpected: {live}")

    total = _passes + _fails
    print(f"\nPREDICTIVE_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


def test_all_gates() -> None:
    """pytest entry point -- see test_governance_minimality for the rationale.

    An authored V-gate that the canonical invocation cannot execute inflates the
    denominator and protects nothing.
    """
    assert main() == 0


if __name__ == "__main__":
    raise SystemExit(main())
