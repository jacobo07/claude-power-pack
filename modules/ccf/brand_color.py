"""Colour science and accessibility (BCAP2-07 / BI-20). Pure; contrast is computed, never claimed.

Role-based palette check: every (fg role, bg role) pair the caller declares is measured in WCAG 2.x relative-luminance
contrast per context (body text 4.5, large text/UI 3.0); a pair with no declared context is UNASSESSED, not passing.
delta_e76 is CIE76 on sRGB->Lab (a screening distance, labelled as such). No conversion/trust association is accepted.
"""
from __future__ import annotations

import re

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
THRESHOLD = {"body": 4.5, "large": 3.0, "ui": 3.0}


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _rgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def contrast(fg, bg):
    l = [0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b) for r, g, b in (_rgb(fg), _rgb(bg))]
    a, b = max(l), min(l)
    return round((a + 0.05) / (b + 0.05), 2)


def _lab(h):
    r, g, b = (_lin(v) for v in _rgb(h))
    x, y, z = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, 0.2126 * r + 0.7152 * g + 0.0722 * b, (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e76(a, b):
    return round(sum((p - q) ** 2 for p, q in zip(_lab(a), _lab(b))) ** 0.5, 2)


def check_palette(palette: dict, pairs: list) -> dict:
    """palette: role->#hex. pairs: [{fg, bg, context}]. Returns problems + per-pair rows."""
    problems, rows = [], []
    for role, v in palette.items():
        if not isinstance(v, str) or not _HEX.match(v):
            problems.append(f"role {role}: not #RRGGBB")
    for p in pairs:
        fg, bg, ctx = p.get("fg"), p.get("bg"), p.get("context")
        if fg not in palette or bg not in palette:
            problems.append(f"pair {fg}/{bg}: unknown role"); continue
        if ctx not in THRESHOLD:
            rows.append({"pair": [fg, bg], "status": "UNASSESSED", "why": f"context {ctx!r} not one of {sorted(THRESHOLD)}"}); continue
        r = contrast(palette[fg], palette[bg])
        ok = r >= THRESHOLD[ctx]
        rows.append({"pair": [fg, bg], "context": ctx, "ratio": r, "status": "PASS" if ok else "FAIL"})
        if not ok:
            problems.append(f"{fg}/{bg} {ctx}: {r} < {THRESHOLD[ctx]}")
    return {"problems": problems, "rows": rows, "profiles_needed": ["mono", "dark", "light"]}


def association_claim_ok(claim: dict) -> bool:
    """A colour->conversion/trust claim is accepted only with a measured source; bare assertion is refused."""
    return bool((claim or {}).get("evidence_source") and (claim or {}).get("measured") is True)
