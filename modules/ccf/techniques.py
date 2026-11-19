"""Logo technique taxonomy as typed hypotheses (BCAP2-07 / BI-10).

METHOD ONLY. The 12 technique names are verified against the pinned upstream taxonomy
(moayadMoatamed/Marker-AI @ d14340c3, references/techniques.md; licence conflict open, so no upstream
prose is copied: the definitions and `needs` below are CPP's own wording).

A technique is a HYPOTHESIS about a concept, never a quality score. `check_hypothesis` accepts one
only when it names a registered technique, a concrete brand-specific observation, and a recipe whose
steps each carry a geometric operation. A self-rating (LLM or otherwise) is carried through as
`self_rating` and is never counted as measured originality.
"""
from __future__ import annotations

TECHNIQUES = {
    "negative_space_letterform": "a shape is read in the gap between or inside letters",
    "negative_space_silhouette": "figure-ground reversal where the empty area reads as a second subject",
    "letterform_modification": "a letter is cut, extended or bent so it carries a second reading",
    "letterform_as_symbol": "one letter is the whole mark and its construction carries the idea",
    "symbol_fusion": "two symbols merge into one mark, each still recognisable",
    "geometric_construction": "the mark is built on stated geometric relations that express the brand value",
    "gestalt_closure": "edges are withheld so the viewer completes the shape",
    "gestalt_continuity": "a directed line leads the eye and the path means something",
    "numeric_or_lexical_embedding": "a number or word is discoverable inside the mark",
    "cultural_or_etymological_mark": "the name's origin or cultural context is encoded visually",
    "ambigram_or_palindrome": "the mark holds under rotation or reflection and symmetry is the idea",
    "monogram_construction": "two or more initials are joined into one unit",
}
GEOMETRIC_OPS = ("align", "offset", "intersect", "subtract", "union", "mirror", "rotate", "scale",
                 "tangent", "grid", "extend", "truncate", "curve", "split", "stack", "trace")
TAXONOMY_PIN = {"repo": "moayadMoatamed/Marker-AI", "sha": "d14340c372730899950419dd9c0dd34b31116d6c",
                "path": "references/techniques.md", "licence_status": "CONFLICT (LICENSE Apache-2.0 vs README MIT)"}


def check_hypothesis(h) -> list:
    """Return a list of problems (empty = acceptable as a hypothesis). Never repairs, never scores."""
    h = h or {}
    out = []
    t = h.get("technique")
    if t not in TECHNIQUES:
        out.append(f"technique '{t}' is not in the registered taxonomy")
    obs = str(h.get("brand_observation") or "").strip()
    if len(obs.split()) < 4:
        out.append("brand_observation must be a concrete brand-specific observation (>= 4 words)")
    steps = h.get("recipe") or []
    if not isinstance(steps, list) or not steps:
        out.append("recipe missing: a construction recipe with geometric steps is required")
    else:
        for i, s in enumerate(steps):
            text = str(s or "").lower()
            if not any(op in text.split() or op in text for op in GEOMETRIC_OPS):
                out.append(f"recipe step {i + 1} has no geometric operation ({', '.join(GEOMETRIC_OPS[:6])}, ...)")
    return out


def summarize(hypotheses) -> dict:
    """Per-hypothesis problems plus honest accounting. `self_rating` is echoed as UNVERIFIED and
    `measured_originality` is always None: only an instrument (e.g. the trademark scan) may set it."""
    rows = []
    for h in hypotheses or []:
        rows.append({"id": h.get("id", "?"), "technique": h.get("technique"), "problems": check_hypothesis(h),
                     "self_rating": h.get("self_rating"), "self_rating_status": "UNVERIFIED" if h.get("self_rating") is not None else "ABSENT",
                     "measured_originality": None})
    return {"rows": rows, "accepted": [r["id"] for r in rows if not r["problems"]], "pin": TAXONOMY_PIN}
