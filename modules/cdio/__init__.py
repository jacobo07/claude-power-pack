"""CDIO -- Chief Design Intelligence Officer (deterministic core).

A cross-cutting design-intelligence layer for the Power Pack. The datasets
(vault/knowledge_base/cdio/) are the criteria; this package is the reproducible
machinery: a pure Design Quality Score (scorer), a PM-03 bus bridge, and CO-12
telemetry. A CDIO score is a measurement, not an opinion
(T-DESIGN-OPINION-VS-CRITERIA-001).
"""
from modules.cdio.scorer import (  # noqa: F401
    Verdict, ScoreResult, score_review, contrast_ratio, check_contrast,
    check_tap_target, check_mobile_font, check_type_levels, check_line_measure,
    check_spacing_system, check_single_primary_cta,
    APPROVE_MIN, REVISE_MIN, SEVERITY_DEDUCTION,
)

__all__ = [
    "Verdict", "ScoreResult", "score_review", "contrast_ratio",
    "check_contrast", "check_tap_target", "check_mobile_font",
    "check_type_levels", "check_line_measure", "check_spacing_system",
    "check_single_primary_cta", "APPROVE_MIN", "REVISE_MIN", "SEVERITY_DEDUCTION",
]
