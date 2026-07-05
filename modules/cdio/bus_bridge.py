#!/usr/bin/env python3
"""CDIO <-> PM-03 Findings Bus bridge.

A CDIO review reaches reusable conclusions ("the hero CTA contrast is 2.8:1,
fails AA"). This bridge publishes those conclusions to the existing PM-03
Findings Bus so another agent working the same repo consults them for zero new
model tokens instead of re-deriving the same defect (the Redundancy Tax).

CDIO does NOT invent its own store: it reuses modules.parallel_mesh.pm_03_bus
exactly as the mesh does. Topic convention: `design:<criterion>` so design
findings are namespaced and queryable. Fail-open ABSOLUTE: a bus write never
breaks a review.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.parallel_mesh import pm_03_bus  # noqa: E402

TOPIC_PREFIX = "design"


def _topic(criterion: str) -> str:
    return f"{TOPIC_PREFIX}:{criterion}"


def publish_findings(repo: str, score_result, *, sid: str = "",
                     state_dir=None) -> int:
    """Publish a review's failing findings (critical + major) to the bus.

    Minor polish issues are not published (they are not reusable-conclusion
    grade). Returns the count published. Fail-open -> 0.
    `score_result` is a ScoreResult (or its .to_json() dict).
    """
    try:
        data = score_result.to_json() if hasattr(score_result, "to_json") else dict(score_result)
        bus = pm_03_bus.FindingsBus(state_dir=state_dir)
        n = 0
        for finding in list(data.get("critical", [])) + list(data.get("major", [])):
            criterion = finding.get("criterion", "unknown")
            observed = finding.get("observed", "")
            severity = "critical" if finding in data.get("critical", []) else "major"
            claim = f"[{severity}] {observed}"
            if finding.get("recommendation"):
                claim += f" -- fix: {finding['recommendation']}"
            bus.publish(repo, _topic(criterion), claim,
                        evidence=finding.get("dimension", ""), sid=sid)
            n += 1
        return n
    except Exception:  # noqa: BLE001 -- fail-open: a bus write must never break a review
        return 0


def consult(repo: str, criterion: str, *, state_dir=None):
    """Before flagging a criterion, ask the bus whether it is already known.
    Returns (hit: bool, claim: str|None). Fail-open -> (False, None)."""
    try:
        bus = pm_03_bus.FindingsBus(state_dir=state_dir)
        f = bus.lookup(repo, _topic(criterion))
        return (f is not None, f.claim if f else None)
    except Exception:  # noqa: BLE001 -- fail-open
        return (False, None)


def known_design_findings(repo: str, *, state_dir=None) -> list:
    """All design findings on the bus for a repo (topic starts with 'design:').
    Used by telemetry to count antipatterns prevented by reuse. Fail-open -> []."""
    try:
        bus = pm_03_bus.FindingsBus(state_dir=state_dir)
        pref = f"{TOPIC_PREFIX}:"
        return [f for f in bus.load(repo) if f.topic.startswith(pref)]
    except Exception:  # noqa: BLE001 -- fail-open
        return []
