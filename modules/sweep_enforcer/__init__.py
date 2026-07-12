"""Sweep Enforcer (P3) -- closes UKDL U-2 permanently.

A prevention rule is not sealable until it has survived a sweep across
every site matching its pattern. The enforcer runs the sweep itself; a
claimed list of patched sites is exactly the evidence that failed last
time.

    from modules.sweep_enforcer import SweepSpec, sweep, seal
    res = sweep(SweepSpec(site_pattern=..., fix_pattern=...), root)
    verdict = seal("U-27", "loaders skip _-prefixed keys", res)
"""
from .rule_sweep import (
    COLLAPSE_THRESHOLD,
    SealVerdict,
    Site,
    SweepResult,
    SweepSpec,
    Verdict,
    gate_rule_write,
    propose_collapse,
    seal,
    sweep,
)

__all__ = [
    "SweepSpec", "SweepResult", "Site", "Verdict", "SealVerdict",
    "sweep", "seal", "propose_collapse", "gate_rule_write",
    "COLLAPSE_THRESHOLD",
]
