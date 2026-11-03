"""Search plan: orders operator families by the CAUSE of the current residual (causal_diff classes) and by a prior over past successes.
A plan is a list of operator names; the search expands them in order. Negative Search Memory (if given) removes operators already refuted
for this (function, residual class)."""
from .operators import OPS

FAMILY_BY_CLASS = {
    "ORDER": ["order", "layout", "temps", "control", "style", "strength"],
    "REG_ALLOC": ["layout", "temps", "order", "style", "control", "strength"],
    "CONST": ["strength", "order", "style", "temps", "layout", "control"],
    "RELOC": ["order", "style", "control", "temps", "layout", "strength"],
    "FRAME": ["layout", "temps", "style", "order", "control", "strength"],
    "OPCODE": ["strength", "control", "order", "style", "temps", "layout"],
    "MISSING": ["control", "temps", "order", "style", "layout", "strength"],
    "EXTRA": ["temps", "control", "style", "order", "layout", "strength"],
}


def plan(primary_class, prior=None, nsm=None, fn=None):
    fams = FAMILY_BY_CLASS.get(primary_class, list(FAMILY_BY_CLASS["OPCODE"]))
    rank = {f: i for i, f in enumerate(fams)}
    names = sorted(OPS, key=lambda n: (rank.get(OPS[n].family, 99) - 3 * (prior or {}).get(n, 0), n))
    if nsm is not None and fn is not None:
        names = [n for n in names if not nsm.refuted_operator(fn, primary_class, n)]
    return names
