#!/usr/bin/env python3
"""CDIO scorer -- the deterministic Design Quality Score engine.

Implements the CDIO-05 review pipeline's score formula VERBATIM, plus the
mechanically-computable design checks (WCAG contrast, spacing-system
conformance, type-level count, tap-target size, line measure). The score is a
pure function of the per-criterion verdicts: same verdicts -> same score, every
time. This is what makes a CDIO Design Quality Score a measurement and not the
reviewer's opinion (T-DESIGN-OPINION-VS-CRITERIA-001).

Two kinds of input feed the score:
  1. MECHANICAL verdicts -- produced here from raw values (a contrast ratio, a
     px size). Not subject to judgment.
  2. JUDGMENT verdicts -- produced by the cdio-reviewer agent against the
     dataset thresholds, but each MUST carry an `observed` value or it is
     dropped (CDIO-00 reality contract).

Score formula (CDIO-05 sec.4): start 100; per failing verdict subtract
critical=25, major=8, minor=2; clamp [0,100].
Verdict (CDIO-05 sec.5 / PR-CDIO-REVIEW-GATE-001):
  APPROVE  = score >= 80 AND zero critical
  REVISE   = 60 <= score <= 79 AND zero critical
  BLOCK    = score < 60 OR any critical (a critical forces BLOCK at any score)
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict

# --- CDIO-05 fixed constants (the contract; mirrored in CDIO-05 dataset) ----
SEVERITY_DEDUCTION = {"critical": 25, "major": 8, "minor": 2}
APPROVE_MIN = 80
REVISE_MIN = 60

# --- CDIO-01 mechanical thresholds (WCAG 2.1 AA + design-system rules) ------
CONTRAST_BODY_MIN = 4.5      # normal text
CONTRAST_LARGE_MIN = 3.0     # large text (>=24px, or >=18.66px bold) / UI
TAP_TARGET_MIN_PX = 44       # WCAG 2.5.5 minimum touch target
BODY_FONT_MOBILE_MIN_PX = 16
MEASURE_MAX_CHARS = 75       # CDIO-01 line-length ceiling
MEASURE_MIN_CHARS = 45       # CDIO-01 line-length floor
TYPE_LEVELS_MAX = 3          # CDIO-01 hierarchy ceiling
DEFAULT_SPACING_BASE = 8     # base grid unit; 4 also common


@dataclass
class Verdict:
    """One criterion verdict (CDIO-05 sec.2). A failing verdict with no
    `observed` value violates the reality contract and is rejected by the
    scorer (see is_valid)."""
    criterion: str
    dimension: str            # visual | ux | trust | conversion
    status: str               # pass | fail
    severity: str = ""        # critical | major | minor (only on fail)
    observed: str = ""        # the measured value / concrete instance
    recommendation: str = ""

    def is_valid(self) -> bool:
        if self.status == "pass":
            return bool(self.criterion)
        return (
            self.severity in SEVERITY_DEDUCTION
            and bool(self.observed.strip())
            and bool(self.criterion)
        )

    def to_json(self) -> dict:
        return asdict(self)


@dataclass
class ScoreResult:
    score: int
    verdict: str                       # APPROVE | REVISE | BLOCK
    reason: str
    critical: list = field(default_factory=list)
    major: list = field(default_factory=list)
    minor: list = field(default_factory=list)
    passed: list = field(default_factory=list)
    dropped: list = field(default_factory=list)  # invalid verdicts, reported

    @property
    def is_done(self) -> bool:
        """The PP completion gate: APPROVE only."""
        return self.verdict == "APPROVE"

    def to_json(self) -> dict:
        d = asdict(self)
        d["is_done"] = self.is_done
        return d


def _clamp(n: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, n))


def score_review(verdicts) -> ScoreResult:
    """Compute the Design Quality Score + verdict from criterion verdicts.

    Deterministic and pure: the same list of verdicts always returns the same
    ScoreResult. Invalid verdicts (fail with no observed value / bad severity)
    are dropped and reported in `dropped`, never silently counted.
    """
    critical, major, minor, passed, dropped = [], [], [], [], []

    for v in verdicts:
        if not isinstance(v, Verdict):
            v = Verdict(**v) if isinstance(v, dict) else None
        if v is None or not v.is_valid():
            dropped.append(v.to_json() if isinstance(v, Verdict) else repr(v))
            continue
        if v.status == "pass":
            passed.append(v.to_json())
        elif v.severity == "critical":
            critical.append(v.to_json())
        elif v.severity == "major":
            major.append(v.to_json())
        elif v.severity == "minor":
            minor.append(v.to_json())

    score = 100
    score -= SEVERITY_DEDUCTION["critical"] * len(critical)
    score -= SEVERITY_DEDUCTION["major"] * len(major)
    score -= SEVERITY_DEDUCTION["minor"] * len(minor)
    score = _clamp(score)

    if critical:
        verdict = "BLOCK"
        reason = f"{len(critical)} critical issue(s) -- floor not tradeable (CDIO-00 sec.4)"
    elif score < REVISE_MIN:
        verdict = "BLOCK"
        reason = f"score {score} < {REVISE_MIN}"
    elif score < APPROVE_MIN:
        verdict = "REVISE"
        reason = f"score {score} in [{REVISE_MIN},{APPROVE_MIN}) -- majors must be resolved"
    else:
        verdict = "APPROVE"
        reason = f"score {score} >= {APPROVE_MIN} and zero critical"

    return ScoreResult(score=score, verdict=verdict, reason=reason,
                       critical=critical, major=major, minor=minor,
                       passed=passed, dropped=dropped)


# --------------------------------------------------------------------------- #
# Mechanical checks -- real computations, not judgment. Each returns a Verdict.
# --------------------------------------------------------------------------- #
def _hex_to_rgb(h: str):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"bad hex color: {h!r}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rel_luminance(rgb) -> float:
    """WCAG 2.1 relative luminance from an sRGB triple (0-255)."""
    def chan(c):
        s = c / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """WCAG contrast ratio between two hex colors. Range 1.0 .. 21.0."""
    l1 = _rel_luminance(_hex_to_rgb(fg_hex))
    l2 = _rel_luminance(_hex_to_rgb(bg_hex))
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 2)


def check_contrast(fg_hex: str, bg_hex: str, *, large: bool = False,
                   criterion: str = "contrast") -> Verdict:
    """Contrast is an accessibility-floor check: a failure is CRITICAL."""
    ratio = contrast_ratio(fg_hex, bg_hex)
    minimum = CONTRAST_LARGE_MIN if large else CONTRAST_BODY_MIN
    label = "large/UI" if large else "body"
    if ratio >= minimum:
        return Verdict(criterion=f"{criterion}-{label}", dimension="visual",
                       status="pass", observed=f"{ratio}:1 >= {minimum}:1")
    return Verdict(
        criterion=f"{criterion}-{label}", dimension="visual", status="fail",
        severity="critical", observed=f"{ratio}:1 < {minimum}:1 ({fg_hex} on {bg_hex})",
        recommendation=f"raise contrast to >= {minimum}:1 (darken/lighten one color)")


def check_tap_target(size_px: float, *, criterion: str = "tap-target-size") -> Verdict:
    """Touch target below 44px is an accessibility-floor failure -> CRITICAL."""
    if size_px >= TAP_TARGET_MIN_PX:
        return Verdict(criterion=criterion, dimension="ux", status="pass",
                       observed=f"{size_px}px >= {TAP_TARGET_MIN_PX}px")
    return Verdict(criterion=criterion, dimension="ux", status="fail",
                   severity="critical", observed=f"{size_px}px < {TAP_TARGET_MIN_PX}px",
                   recommendation=f"enlarge touch target to >= {TAP_TARGET_MIN_PX}px")


def check_mobile_font(size_px: float, *, criterion: str = "mobile-body-font") -> Verdict:
    if size_px >= BODY_FONT_MOBILE_MIN_PX:
        return Verdict(criterion=criterion, dimension="visual", status="pass",
                       observed=f"{size_px}px >= {BODY_FONT_MOBILE_MIN_PX}px")
    return Verdict(criterion=criterion, dimension="visual", status="fail",
                   severity="major", observed=f"{size_px}px < {BODY_FONT_MOBILE_MIN_PX}px",
                   recommendation=f"set mobile body text >= {BODY_FONT_MOBILE_MIN_PX}px")


def check_type_levels(count: int, *, criterion: str = "type-levels") -> Verdict:
    if count <= TYPE_LEVELS_MAX:
        return Verdict(criterion=criterion, dimension="visual", status="pass",
                       observed=f"{count} levels <= {TYPE_LEVELS_MAX}")
    return Verdict(criterion=criterion, dimension="visual", status="fail",
                   severity="major", observed=f"{count} competing type levels > {TYPE_LEVELS_MAX}",
                   recommendation="collapse to at most 3 type levels per viewport")


def check_line_measure(chars: int, *, criterion: str = "line-measure") -> Verdict:
    if MEASURE_MIN_CHARS <= chars <= MEASURE_MAX_CHARS:
        return Verdict(criterion=criterion, dimension="visual", status="pass",
                       observed=f"{chars} chars in [{MEASURE_MIN_CHARS},{MEASURE_MAX_CHARS}]")
    return Verdict(criterion=criterion, dimension="visual", status="fail",
                   severity="minor", observed=f"{chars} chars outside [{MEASURE_MIN_CHARS},{MEASURE_MAX_CHARS}]",
                   recommendation="constrain measure with a max-width (~66ch optimum)")


def check_spacing_system(values, *, base: int = DEFAULT_SPACING_BASE,
                         criterion: str = "spacing-system") -> Verdict:
    """Every spacing value should be a multiple of the base grid unit. Off-system
    values are the 'cramping' anti-pattern (CDIO-01) -> MINOR."""
    off = [v for v in values if base and v % base != 0]
    if not off:
        return Verdict(criterion=criterion, dimension="visual", status="pass",
                       observed=f"all {len(values)} values multiples of {base}px")
    return Verdict(criterion=criterion, dimension="visual", status="fail",
                   severity="minor", observed=f"off-system: {off} (base {base}px)",
                   recommendation=f"snap spacing to multiples of {base}px")


def check_single_primary_cta(count: int, *, criterion: str = "single-primary-cta") -> Verdict:
    """Zero primary CTAs above the fold, or more than one competing primary, is a
    conversion + clarity failure. Zero -> critical (buried/absent action)."""
    if count == 1:
        return Verdict(criterion=criterion, dimension="conversion", status="pass",
                       observed="exactly 1 primary CTA")
    if count == 0:
        return Verdict(criterion=criterion, dimension="conversion", status="fail",
                       severity="critical", observed="0 primary CTAs above the fold",
                       recommendation="add one clear primary action above the fold")
    return Verdict(criterion=criterion, dimension="conversion", status="fail",
                   severity="major", observed=f"{count} competing primary CTAs",
                   recommendation="demote all but one CTA to secondary emphasis")
