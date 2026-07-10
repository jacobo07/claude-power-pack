"""Meta-System Loop Runner (R-LOOP) -- run the seven in the corpus loop order.

The corpus's closed loop is MS-6 -> MS-2 -> MS-1 -> MS-0 -> MS-3 -> MS-4 -> MS-5
(finds-what's-missing -> compiles -> assembles -> makes-reproducible -> compounds
-> prices -> keeps-coherent). This runner interprets each in that order for the
current repo's noun-map, producing one execution plan per meta-system. There is
no fabricated ROI ranker: without a live value signal the honest default is the
corpus's own fixed order; a caller may restrict the set (`enabled`) or stop early
(`stop_after`).
"""

from __future__ import annotations

from pathlib import Path

from . import LOOP_ORDER
from .executor import ExecutionPlan, build_plan
from .noun_map import NounMap


def run_loop(nm: NounMap, corpus_root: str | Path, *,
             order: list[str] | None = None,
             stop_after: int | None = None,
             enabled: tuple[str, ...] | None = None) -> list[ExecutionPlan]:
    """Interpret each meta-system in loop order for the repo's noun-map.

    `enabled` (or the noun-map's own `enabled`) restricts the set; `stop_after`
    caps how many plans are produced (a loop may run all seven or stop after the
    first per the caller's config).
    """
    seq = order or LOOP_ORDER
    sel = enabled if enabled is not None else nm.enabled
    plans: list[ExecutionPlan] = []
    for ms in seq:
        if sel is not None and ms not in sel:
            continue
        plans.append(build_plan(ms, nm, corpus_root))
        if stop_after is not None and len(plans) >= stop_after:
            break
    return plans
