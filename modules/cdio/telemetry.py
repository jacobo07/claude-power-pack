#!/usr/bin/env python3
"""CDIO telemetry -- CDIO's impact, measured on the CO-12 substrate.

CDIO holds itself to the standard it enforces: its own value is a measurement,
not a claim. Every review records a signal to the SAME CO-12 sink the rest of
the cognitive OS uses (modules.cognitive_os.co_12_telemetry), and the readiness
reader aggregates real data:

  design_reviews_count     -- how many reviews actually ran
  avg_design_quality_score -- mean Design Quality Score over recorded reviews
  critical_issues_caught   -- total critical findings caught across reviews
  antipatterns_prevented   -- distinct design findings on the PM-03 bus (a bus
                              hit is a defect another agent did not re-derive)

Honest (CO-12 reality contract): with no reviews recorded, the counts are 0 and
the average is `None` (unknown) -- never a faked score. Fail-open ABSOLUTE.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.cognitive_os import co_12_telemetry as co12  # noqa: E402
from modules.cdio import bus_bridge  # noqa: E402

SIGNAL_KIND = "cdio_review"


def record_review(repo: str, score_result, *, sid: str = "", state_dir=None,
                  now=None) -> bool:
    """Record one CDIO review as a CO-12 signal. `score_result` is a ScoreResult
    or its dict. Fail-open -> False."""
    try:
        data = score_result.to_json() if hasattr(score_result, "to_json") else dict(score_result)
        payload = {
            "repo": repo,
            "sid": sid,
            "score": int(data.get("score", 0)),
            "verdict": str(data.get("verdict", "")),
            "critical": len(data.get("critical", [])),
            "major": len(data.get("major", [])),
            "minor": len(data.get("minor", [])),
        }
        return co12.record_signal(SIGNAL_KIND, payload, state_dir=state_dir, now=now)
    except Exception:  # noqa: BLE001 -- fail-open
        return False


def cdio_readiness(repo: str | None = None, *, state_dir=None,
                   bus_state_dir=None) -> dict:
    """Aggregate CDIO's recorded impact. Honest zeros/None when no data.
    Fail-open -> a benign all-zero/unknown dict."""
    try:
        sigs = [s for s in co12.load_signals(state_dir=state_dir)
                if s.get("kind") == SIGNAL_KIND]
        if repo:
            sigs = [s for s in sigs if s.get("repo") == repo]

        count = len(sigs)
        scores = [int(s.get("score", 0)) for s in sigs if "score" in s]
        avg = round(sum(scores) / len(scores), 1) if scores else None
        criticals = sum(int(s.get("critical", 0)) for s in sigs)

        prevented = 0
        if repo:
            prevented = len(bus_bridge.known_design_findings(repo, state_dir=bus_state_dir))

        return {
            "design_reviews_count": count,
            "avg_design_quality_score": avg,
            "critical_issues_caught": criticals,
            "antipatterns_prevented": prevented,
            "measured": count > 0,
        }
    except Exception:  # noqa: BLE001 -- fail-open
        return {"design_reviews_count": 0, "avg_design_quality_score": None,
                "critical_issues_caught": 0, "antipatterns_prevented": 0,
                "measured": False}
