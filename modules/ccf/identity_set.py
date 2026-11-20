"""Cohesive identity sets (BCAP2-07 / BI-11).

One decision system spanning logo, font and palette. `validate_set` returns problems (empty = valid):
2-4 explicit comparison axes, a conceptual rationale, a measured contrast ratio (WCAG, computed here,
not claimed), a typography test record, and a category-default challenge. In KEEP/REFRESH mode the
original logo/palette/font must be preserved: a changed original is refused (no unwanted redesign).
"""
from __future__ import annotations

MODES = ("NEW", "KEEP", "REFRESH")


def _lum(hexc: str) -> float:
    c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(fg: str, bg: str) -> float:
    a, b = sorted((_lum(fg), _lum(bg)), reverse=True)
    return round((a + 0.05) / (b + 0.05), 2)


def validate_set(s: dict, mode: str = "NEW", original: dict = None) -> list:
    p = []
    if mode not in MODES:
        return [f"mode must be one of {MODES}"]
    axes = s.get("comparison_axes") or []
    if not 2 <= len(axes) <= 4:
        p.append(f"comparison_axes needs 2-4 entries, got {len(axes)}")
    if not (s.get("rationale") or "").strip():
        p.append("missing conceptual rationale")
    if not (s.get("category_default_challenge") or "").strip():
        p.append("missing category-default challenge")
    pal = s.get("palette") or {}
    fg, bg = pal.get("text"), pal.get("surface")
    try:
        ratio = contrast(fg, bg)
        if ratio < 4.5:
            p.append(f"text/surface contrast {ratio} < 4.5")
    except Exception:
        p.append("palette needs #RRGGBB text and surface to compute contrast")
    if not (s.get("typography_test") or {}).get("observed"):
        p.append("typography test has no observation")
    if mode in ("KEEP", "REFRESH"):
        if not original:
            p.append(f"{mode} requires the original logo/palette/font")
        else:
            keys = ("logo", "font") if mode == "REFRESH" else ("logo", "font", "palette")
            for k in keys:
                if s.get(k) != original.get(k):
                    p.append(f"{mode} must preserve original {k}")
    return p
