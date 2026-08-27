"""SPEC-KACQ-006 acceptance: an evidence request is ONE artifact, not one per lens.

The defect this pins was found by running the real pack, not by reading the
code: six "requests" were emitted against a single declared boundary, and four
of them were the SAME question (family 37, "exception queues") seen through
four templates. The lens decides HOW a question was asked; it never changes
WHAT artifact would answer it. Keying the buckets on lens therefore split one
dataset into six near-identical asks -- the exact 399x-human-cost failure that
queues.py's own module docstring exists to forbid.

Fixture rows mirror the live corpus shape (399 topics x 5 templates against one
boundary), scaled down so the arithmetic is checkable by eye.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_PP = Path(__file__).resolve().parents[1]
if str(_PP) not in sys.path:
    sys.path.insert(0, str(_PP))

from modules.knowledge_acquisition.queues import (  # noqa: E402
    build_evidence_requests, render_evidence_pack,
)
from modules.knowledge_acquisition.routing import Lens, RouteClass  # noqa: E402

DIVERTS = RouteClass.MULTI_SOURCE.value
ASKS_ONLY = RouteClass.EVA_HIGH_VALUE.value

CAPITAL_LIMIT = "No tengo un numero exacto de capital total disponible."
ACCESS_LIMIT = "No tengo acceso a los dashboards de cliente."


@dataclass(frozen=True)
class _Boundary:
    """Only the two attributes build_evidence_requests reads (mock at the boundary)."""

    boundary_id: str
    scope_text: str


def _row(lens, *, boundary="b-capital", route_class=DIVERTS,
         family="37. Operations", topic="exception queues"):
    return {"lens": lens, "boundary_id": boundary, "route_class": route_class,
            "family": family, "topic": topic}


def test_one_boundary_asked_through_five_lenses_is_one_request():
    # Arrange -- the live shape: one topic, one boundary, five templates.
    rows = [_row(lens.value) for lens in (
        Lens.REAL_CASES, Lens.FREEFORM, Lens.INTERNAL_PATTERNS,
        Lens.THRESHOLD, Lens.EXPERIMENT)]

    # Act
    reqs = build_evidence_requests(
        rows, [_Boundary("b-capital", CAPITAL_LIMIT)])

    # Assert -- ONE artifact, and it accounts for every prompt.
    assert len(reqs) == 1, "lens must not split one artifact into several"
    assert reqs[0].leverage == 5
    assert reqs[0].boundary_text == CAPITAL_LIMIT
    assert dict(reqs[0].lenses) == {
        Lens.REAL_CASES.value: 1, Lens.FREEFORM.value: 1,
        Lens.INTERNAL_PATTERNS.value: 1, Lens.THRESHOLD.value: 1,
        Lens.EXPERIMENT.value: 1,
    }


def test_lens_breakdown_sums_to_leverage():
    # Arrange -- uneven distribution, mirroring 396/9/1/1/1/1 in the real pack.
    rows = ([_row(Lens.REAL_CASES.value)] * 6
            + [_row(Lens.FREEFORM.value)] * 3
            + [_row(Lens.THRESHOLD.value)])

    # Act
    reqs = build_evidence_requests(rows, [_Boundary("b-capital", CAPITAL_LIMIT)])

    # Assert
    assert len(reqs) == 1
    assert sum(n for _, n in reqs[0].lenses) == reqs[0].leverage == 10
    # Descending, so the dominant lens is the headline.
    assert reqs[0].lenses[0] == (Lens.REAL_CASES.value, 6)


def test_distinct_boundaries_stay_distinct():
    """Collapsing by boundary must not over-collapse across boundaries."""
    # Arrange
    rows = [_row(Lens.REAL_CASES.value, boundary="b-capital"),
            _row(Lens.REAL_CASES.value, boundary="b-access")]

    # Act
    reqs = build_evidence_requests(rows, [
        _Boundary("b-capital", CAPITAL_LIMIT), _Boundary("b-access", ACCESS_LIMIT)])

    # Assert -- two real artifacts, because two different things are missing.
    assert len(reqs) == 2
    assert {r.boundary_id for r in reqs} == {"b-capital", "b-access"}


def test_non_diverting_routes_request_nothing():
    # Arrange -- questions the source can answer alone need no human artifact.
    rows = [_row(Lens.THRESHOLD.value, route_class=ASKS_ONLY),
            _row(Lens.PITFALLS.value, route_class=ASKS_ONLY)]

    # Act
    reqs = build_evidence_requests(rows, [_Boundary("b-capital", CAPITAL_LIMIT)])

    # Assert
    assert reqs == []


def test_rendered_pack_shows_one_block_with_the_lens_breakdown():
    # Arrange
    rows = ([_row(Lens.REAL_CASES.value, family="01. Frontier")] * 4
            + [_row(Lens.FREEFORM.value, family="02. Sourcing")])

    # Act
    pack = render_evidence_pack(
        build_evidence_requests(rows, [_Boundary("b-capital", CAPITAL_LIMIT)]))

    # Assert -- exactly one numbered block, with the breakdown inside it.
    assert pack.count("## ") == 1, "one artifact must render as one block"
    assert "unlocks 5 questions" in pack
    assert "Asked through:" in pack
    assert f"  - {Lens.REAL_CASES.value}: 4" in pack
    assert f"  - {Lens.FREEFORM.value}: 1" in pack
    # The REAL_CASES guidance fires on presence in the breakdown, not on a key.
    assert "One dataset, cut six ways." in pack


def test_empty_input_says_nothing_is_needed():
    # Arrange / Act
    pack = render_evidence_pack([])

    # Assert -- the honest empty state, not a blank document.
    assert "None." in pack
    assert "nothing needs a human" in pack
