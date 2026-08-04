"""duplicate_to_advantage -- the D2A Engine (SCS C85).

The PP's immune-and-evolution system for ARCHITECTURE PROPOSALS. Where
`frontier_intelligence.evolution_engine` scans the EXISTING knowledge_base
retrospectively and proposes health mutations, the D2A Engine runs PROSPECTIVELY:
given a not-yet-built proposal, it detects duplication in three axes, maps the
capability gap around the parent, generates vertical + horizontal reinforcement
candidates, scores the portfolio on 16 dimensions, and emits a minimal BUILD
CONTRACT under a 10-rule anti-inflation gate.

Root law (PR-DUPLICATE-TO-ADVANTAGE-001): ninguna duplicidad termina en rechazo.
Toda duplicidad se convierte en busqueda estructurada de la mejor capacidad
adyacente. Propose-never-build, Owner-gated, fail-open ABSOLUTE.
"""
from .d2a_engine import (
    Proposal,
    DupeVerdict,
    GapMap,
    Candidate,
    BuildContract,
    D2AVerdict,
    run,
    OPERATIONS,
    ANTI_INFLATION_RULES,
    GAP_DIMENSIONS,
    PORTFOLIO_DIMENSIONS,
    FamilyItemVerdict,
    FamilySizingReport,
    run_family,
    render_family,
    ExpansionCandidate,
    ExpansionPlan,
    Stop1Menu,
    load_config,
    compute_expansion,
    build_stop1_menu,
    render_stop1_menu,
)

__all__ = [
    "Proposal", "DupeVerdict", "GapMap", "Candidate", "BuildContract",
    "D2AVerdict", "run", "OPERATIONS", "ANTI_INFLATION_RULES",
    "GAP_DIMENSIONS", "PORTFOLIO_DIMENSIONS",
    "FamilyItemVerdict", "FamilySizingReport", "run_family", "render_family",
    # STOP #1 expansion option (PR-D2A-EXPANSION-001)
    "ExpansionCandidate", "ExpansionPlan", "Stop1Menu", "load_config",
    "compute_expansion", "build_stop1_menu", "render_stop1_menu",
]
