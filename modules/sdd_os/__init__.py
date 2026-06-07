"""SDD-OS runtime -- BL-SDD-OS-001 (build-everything BLOQUE A).

Runtime generators on top of the Sprint 2 SDD-OS layer (spec_gate.
classify_tier + per-tier OQS + prd-tier templates).

Public API:
  * prd_generator: generate_prd, render_prd, PRD
"""
from .prd_generator import PRD, generate_prd, render_prd

__all__ = ["PRD", "generate_prd", "render_prd"]
