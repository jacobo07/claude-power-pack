"""Turn routing verdicts into the two artifacts a human can act on.

WHY TWO
-------
A routed corpus answers two different questions and they have different
readers. "What should the runner do next" is a queue. "What should I ask a
person for" is a request. Rendering both from one table keeps them consistent;
rendering them into one document would make both unusable.

THE MEASURE OF THE SECOND ONE
-----------------------------
Questions unlocked per request, not row count. The pending corpus asks 399
topics through five lenses, and the case-data lens collides with the same
declared boundary every time -- so the evidence those 399 questions are missing
is ONE dataset, described once. A file listing 399 questions would be the same
information at 399x the human cost, which is the failure mode this exists to
avoid.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass

from .routing import Lens, RouteClass

#: The segmentation the case-data template asks for, in the corpus's own words.
#: Stated here because it is the shared shape of every request the lens
#: generates -- one dataset cut these six ways answers all of them.
_CASE_AXES = "categoria, ticket, margen, canal, geografia, madurez de la marca"


@dataclass(frozen=True)
class EvidenceRequest:
    """One artifact to ask a human for, and everything it would unlock."""

    boundary_id: str
    boundary_text: str
    lens: Lens
    route_class: RouteClass
    prompts: int
    families: tuple[str, ...]
    sample_topics: tuple[str, ...]

    @property
    def leverage(self) -> int:
        """Questions resolved per request. The only number that matters here."""
        return self.prompts


def build_evidence_requests(rows, boundaries) -> list[EvidenceRequest]:
    """Collapse diverted verdicts into the few artifacts they actually need.

    Grouped by (boundary, lens): two questions that collide with the same
    declared limit through the same template are missing the same thing, and
    asking for it twice wastes the scarcest resource in the loop.
    """
    text_of = {b.boundary_id: b.scope_text for b in boundaries}
    buckets: dict[tuple, list] = collections.defaultdict(list)
    for r in rows:
        route_class = RouteClass(r["route_class"])
        if not route_class.diverts:
            continue
        buckets[(r["boundary_id"], r["lens"], r["route_class"])].append(r)

    requests = []
    for (boundary_id, lens, route_class), group in buckets.items():
        families = sorted({g["family"] for g in group})
        topics = sorted({g["topic"] for g in group if g["topic"]})
        requests.append(EvidenceRequest(
            boundary_id=boundary_id,
            boundary_text=text_of.get(boundary_id, "(boundary not in ledger)"),
            lens=Lens(lens),
            route_class=RouteClass(route_class),
            prompts=len(group),
            families=tuple(families),
            sample_topics=tuple(topics[:6]),
        ))
    return sorted(requests, key=lambda r: -r.leverage)


def render_evidence_pack(requests: list[EvidenceRequest]) -> str:
    """The document to take to a person. Density over completeness."""
    if not requests:
        return ("# Evidence requests\n\nNone. No routed question collides with "
                "a limit the source has declared, so nothing needs a human "
                "yet.\n")

    out = ["# Evidence requests",
           "",
           "Each block is ONE thing to ask for, and the number of pending "
           "questions it would unlock. Ordered by leverage.",
           ""]
    for i, req in enumerate(requests, 1):
        out += [
            f"## {i}. {req.lens.value} -- unlocks {req.leverage} questions",
            "",
            f"- **Route**: `{req.route_class.value}`",
            f"- **The source's own words**: \"{req.boundary_text.strip()}\"",
            f"- **Spans**: {len(req.families)} families, "
            f"{req.prompts} pending questions",
        ]
        if req.lens is Lens.REAL_CASES:
            out.append(f"- **What would answer all of them**: case outcomes "
                       f"segmented by {_CASE_AXES}. One dataset, cut six ways.")
        out += ["", "Families:", ""]
        out += [f"  - {f}" for f in req.families[:12]]
        if len(req.families) > 12:
            out.append(f"  - ... and {len(req.families) - 12} more")
        if req.sample_topics:
            out += ["", "Sample topics:", ""]
            out += [f"  - {t}" for t in req.sample_topics]
        out.append("")
    return "\n".join(out)


def render_queue(rows) -> str:
    """What the runner should do, and why -- one line per class, then detail."""
    by_class: dict = collections.Counter()
    by_lens_class: dict = collections.defaultdict(collections.Counter)
    unbacked = 0
    for r in rows:
        by_class[r["route_class"]] += 1
        by_lens_class[r["lens"]][r["route_class"]] += 1
        if not r["evidence_backed"]:
            unbacked += 1

    out = ["# Acquisition queue", "",
           f"{len(rows)} pending prompts routed. "
           f"{unbacked} carry a verdict from a lens with no measured evidence "
           f"and are therefore ranked, not diverted.", "",
           "| route | prompts | asks the source? |", "|---|---|---|"]
    for cls, n in by_class.most_common():
        asks = "no" if RouteClass(cls).diverts else "yes"
        if RouteClass(cls) is RouteClass.MULTI_SOURCE:
            asks = "yes, and also needs evidence elsewhere"
        out.append(f"| `{cls}` | {n} | {asks} |")

    out += ["", "## By lens", "", "| lens | " +
            " | ".join(sorted({c for m in by_lens_class.values() for c in m})) +
            " |"]
    classes = sorted({c for m in by_lens_class.values() for c in m})
    out.append("|---" * (len(classes) + 1) + "|")
    for lens, counts in sorted(by_lens_class.items(),
                               key=lambda kv: -sum(kv[1].values())):
        cells = " | ".join(str(counts.get(c, 0)) for c in classes)
        out.append(f"| {lens} | {cells} |")

    reasons: dict = {}
    for r in rows:
        reasons.setdefault((r["lens"], r["route_class"]), r["reason"])
    out += ["", "## Why", ""]
    for (lens, cls), reason in sorted(reasons.items()):
        out.append(f"- **{lens} -> `{cls}`**: {reason}")
    return "\n".join(out) + "\n"


__all__ = [
    "EvidenceRequest",
    "build_evidence_requests",
    "render_evidence_pack",
    "render_queue",
]
