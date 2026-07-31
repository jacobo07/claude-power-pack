"""OSR -- Observed System Reconstruction.

The irreducible residue of the USIRC proposal (audit:
`vault/audits/usirc/`). Of ~160 chartered dataset slots and 89 audited
mechanisms, 77 already had an owner. Three did not, and they are here.

    OSR-1  model.py     a typed model of an EXTERNAL observed product
    OSR-2  compare.py   comparison of a build against a captured reference
    OSR-3  align.py     two-execution alignment for the earliest divergence
    OSR-L1 ordering.py  arrival at a state does not witness the order to it

What this package is NOT, per `vault/audits/usirc/BOUNDARY_CONTRACT.md`:
it acquires no evidence (crawl_os), stands up no graph (graphify), publishes
no fidelity number (DAIF-03 §1.7 holds the metric authority by Owner ruling),
investigates no cause (craif), promotes no finding to a rule (FD-03 routes,
rule_compiler places), and assigns no epistemic status (ACIS).
"""
from __future__ import annotations

from .align import align, craif_record
from .compare import (
    DIFF,
    MATCH,
    UNMEASURED,
    compare_geometry,
    compare_rasters,
    compare_timelines,
    instrument_report,
)
from .model import EDGE_KINDS, NODE_KINDS, ModelError, ObservedSystemModel
from .ordering import gate, verify_ordering

__all__ = [
    "ObservedSystemModel",
    "ModelError",
    "NODE_KINDS",
    "EDGE_KINDS",
    "compare_rasters",
    "compare_geometry",
    "compare_timelines",
    "instrument_report",
    "MATCH",
    "DIFF",
    "UNMEASURED",
    "align",
    "craif_record",
    "verify_ordering",
    "gate",
]
