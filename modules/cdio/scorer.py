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

import os
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
TINT_FILL_OPACITY_MIN = 0.10 # a fill above this opacity reads as a competing tint (VQ-4)
MAX_TINT_FILLS_PER_CARD = 2  # CDIO-01 system-tint discipline: max competing fills per card


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


def check_color_discipline(fill_opacities, *, threshold: float = TINT_FILL_OPACITY_MIN,
                           max_fills: int = MAX_TINT_FILLS_PER_CARD,
                           criterion: str = "color-discipline") -> Verdict:
    """VQ-4 System-Tint Discipline, made mechanically refusable.

    Counts the tint FILLS whose opacity exceeds `threshold` within a SINGLE card /
    container. Outline chips (transparent background) and text-only tints are 0-fill
    and correctly do not count. More than `max_fills` competing fills is the
    color-noise anti-pattern (T-DESIGN-MORE-COLORS-MORE-INFORMATION-001): colour is
    processed pre-attentively, so when everything is filled the eye cannot find the
    dominant datum -- a colour chart, not an information system. -> MAJOR.

    The VQ-4 semantic-colour exemption is for a *hue* being reused as a state signal
    (a red left-border echoing a red status), NOT for stacking N filled tint surfaces
    in one card. This check measures FILLS, so it does not fire on hue repetition
    across outline/border/text elements -- only on genuine competing fills.

    `fill_opacities`: the fill opacities (0..1) of the tinted, non-transparent
    surfaces in ONE card. Example -- the fixed /ai-ops/tasks card is [0.12]
    (StatusBadge pill only) -> PASS; the pre-fix card was [0.12, 0.12, 0.12]
    (pill + two specificity-bugged "outline" chips rendered as fills) -> FAIL.
    """
    active = [round(float(o), 3) for o in (fill_opacities or [])
              if isinstance(o, (int, float)) and float(o) > threshold]
    pct = int(round(threshold * 100))
    if len(active) <= max_fills:
        return Verdict(criterion=criterion, dimension="visual", status="pass",
                       observed=f"{len(active)} tint fill(s) >{pct}% opacity <= {max_fills}/card")
    return Verdict(
        criterion=criterion, dimension="visual", status="fail", severity="major",
        observed=f"{len(active)} tint fills >{pct}% opacity in one card > {max_fills}: {active}",
        recommendation=f"reduce to <= {max_fills} competing tint fills; subordinate the rest to "
                       "outline (transparent) or text-only, leaving one dominant fill = the most "
                       "urgent datum")


# --------------------------------------------------------------------------- #
# CDIO-06 anti-slop checks -- the GENERATIVE axis, enforced mechanically.
#
# Before these, the Anti-Slop Kit lived in two prose files and zero executable
# lines: the PP could not FAIL an output for visual slop, so the rule was a
# preference, not a gate. These four checks make it refusable.
#
# The load-bearing nuance (CDIO-06 sec.1): a default is not slop; a default
# WITHOUT A DECLARED INTENT is slop. Three of the nine families use Inter
# deliberately and for stated reasons, so check_font_stack does not blanket-fail
# a default-tier font -- it fails one whose declared family does not sanction it.
# --------------------------------------------------------------------------- #

# Families that deliberately sanction a default-tier font (CDIO-06 sec.1):
#   F1 Editorial Minimalism (Inter -- restraint is the point)
#   F4 Data-Dense Pro       (Inter -- for its tabular numerals)
#   F6 Playful Color        (Inter -- paired against a characterful display face)
KNOWN_FAMILIES = {f"F{i}" for i in range(1, 10)}
FAMILIES_SANCTIONING_DEFAULT_FONTS = {"F1", "F4", "F6"}

DEFAULT_TIER_FONTS = {
    "inter", "roboto", "arial", "helvetica", "helvetica neue", "system-ui",
    "-apple-system", "blinkmacsystemfont", "segoe ui", "sans-serif", "serif",
}

# The teal fingerprint (CDIO-06 sec.4) -- a specific machine-default tell.
CLICHE_ACCENTS = {"#16d5e6"}

# Purple-family hue window, in degrees. The clichéd gradient the Anti-Slop Kit
# names explicitly is a purple accent over a near-white or near-black ground.
PURPLE_HUE_MIN = 255
PURPLE_HUE_MAX = 300
CLICHE_SATURATION_MIN = 0.35   # below this it is a grey, not a purple
GROUND_LIGHT_MIN = 0.85        # relative luminance of a "white" ground
GROUND_DARK_MAX = 0.10         # relative luminance of a "black" ground


def _hue_sat(hex_color: str):
    """Return (hue_degrees, saturation) for a hex color. HSV-style saturation."""
    r, g, b = (c / 255.0 for c in _hex_to_rgb(hex_color))
    hi, lo = max(r, g, b), min(r, g, b)
    delta = hi - lo
    sat = 0.0 if hi == 0 else delta / hi
    if delta == 0:
        hue = 0.0
    elif hi == r:
        hue = 60 * (((g - b) / delta) % 6)
    elif hi == g:
        hue = 60 * (((b - r) / delta) + 2)
    else:
        hue = 60 * (((r - g) / delta) + 4)
    return hue, sat


def _is_purple(hex_color: str) -> bool:
    try:
        hue, sat = _hue_sat(hex_color)
    except ValueError:
        return False
    return PURPLE_HUE_MIN <= hue <= PURPLE_HUE_MAX and sat >= CLICHE_SATURATION_MIN


def check_family_declared(family, *, criterion: str = "aesthetic-family-declared") -> Verdict:
    """A surface with no declared aesthetic family cannot be reviewed, only reacted
    to. Absent or unknown -> CRITICAL (forces BLOCK at any score). This is what makes
    PR-DESIGN-FAMILY-BEFORE-BUILD-001 enforceable rather than aspirational."""
    fam = str(family or "").strip().upper()
    if fam in KNOWN_FAMILIES:
        return Verdict(criterion=criterion, dimension="visual", status="pass",
                       observed=f"aesthetic_family={fam} (CDIO-06)")
    if not fam:
        return Verdict(
            criterion=criterion, dimension="visual", status="fail", severity="critical",
            observed="aesthetic_family absent from DESIGN.md front-matter",
            recommendation="run the CDIO-06 sec.2 three-question picker; declare one of F1..F9")
    return Verdict(
        criterion=criterion, dimension="visual", status="fail", severity="critical",
        observed=f"aesthetic_family={fam!r} is not one of F1..F9",
        recommendation="declare a known CDIO-06 family (F1..F9)")


def check_font_stack(fonts, family, *, criterion: str = "font-stack-intent") -> Verdict:
    """Fail a default-tier font stack UNLESS the declared family sanctions it.

    `fonts` is the set of font families the surface actually uses. A stack whose
    non-default fonts are empty -- every font in it is default-tier -- was inherited,
    not chosen. That is the slop condition.
    """
    names = [str(f).strip().lower() for f in (fonts or []) if str(f).strip()]
    if not names:
        return Verdict(criterion=criterion, dimension="visual", status="fail",
                       severity="major", observed="no font families declared",
                       recommendation="declare the typography stack in DESIGN.md")

    fam = str(family or "").strip().upper()
    defaults = sorted({n for n in names if n in DEFAULT_TIER_FONTS})
    chosen = sorted({n for n in names if n not in DEFAULT_TIER_FONTS})

    if chosen:
        return Verdict(criterion=criterion, dimension="visual", status="pass",
                       observed=f"characterful font(s) present: {chosen}")
    if fam in FAMILIES_SANCTIONING_DEFAULT_FONTS:
        return Verdict(
            criterion=criterion, dimension="visual", status="pass",
            observed=f"default-tier stack {defaults} sanctioned by declared family {fam}")
    return Verdict(
        criterion=criterion, dimension="visual", status="fail", severity="critical",
        observed=f"every font is default-tier {defaults}; declared family "
                 f"{fam or '(none)'} does not sanction a default stack",
        recommendation="choose a typeface for the brand story (CDIO-06); a framework's "
                       "inherited font is not a typographic decision")


def check_palette_cliche(colors, *, background=None,
                         criterion: str = "palette-cliche") -> Verdict:
    """Fail the clichéd palettes the Anti-Slop Kit names: a purple-family accent over
    a near-white or near-black ground, and the teal `#16d5e6` fingerprint."""
    vals = [str(c).strip() for c in (colors or []) if str(c).strip()]
    hits = []

    for c in vals:
        if c.lower() in CLICHE_ACCENTS:
            hits.append(f"{c} (teal default fingerprint, CDIO-06 sec.4)")

    if background:
        try:
            ground = _rel_luminance(_hex_to_rgb(str(background)))
        except ValueError:
            ground = None
        if ground is not None and (ground >= GROUND_LIGHT_MIN or ground <= GROUND_DARK_MAX):
            tone = "white" if ground >= GROUND_LIGHT_MIN else "black"
            for c in vals:
                if _is_purple(c):
                    hits.append(f"{c} (purple accent on a near-{tone} ground)")

    if not hits:
        return Verdict(criterion=criterion, dimension="visual", status="pass",
                       observed=f"{len(vals)} color(s), no clichéd palette detected")
    return Verdict(
        criterion=criterion, dimension="visual", status="fail", severity="critical",
        observed="; ".join(hits),
        recommendation="ground the palette in the product narrative (CDIO-06 sec.4); "
                       "declare a brand-specific accent in DESIGN.md first")


def check_design_md_exists(path, *, criterion: str = "design-md-present") -> Verdict:
    """A visual surface built with no DESIGN.md is built with no tokens, and every
    token it invents is an unreviewable one-off. CRITICAL."""
    p = str(path or "")
    if p and os.path.isfile(p):
        return Verdict(criterion=criterion, dimension="visual", status="pass",
                       observed=f"DESIGN.md present at {p}")
    return Verdict(
        criterion=criterion, dimension="visual", status="fail", severity="critical",
        observed=f"no DESIGN.md at {p or '(no path given)'}",
        recommendation="create DESIGN.md from modules/design-md/DESIGN.md.template and "
                       "declare an aesthetic_family before building the surface")
