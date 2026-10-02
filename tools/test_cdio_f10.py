#!/usr/bin/env python3
"""V-F10-* -- the CDIO-06 F10 "Calm Utility" family, enforced rather than described.

F10 was distilled 2026-09-14 from a seven-image reference bank (CDIO-06 sec.9).
This file pins the parts a dataset alone cannot hold: that the family is
DECLARABLE, that its font licence is real AND narrow, and above all that its
signature floor collision is REFUSABLE.

Every gate here drives BOTH branches. A family check that only ever asserts the
new family passes would stay green with the whole range widened to anything.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.cdio.scorer import (  # noqa: E402
    CONTRAST_BODY_MIN,
    FAMILIES_SANCTIONING_DEFAULT_FONTS,
    KNOWN_FAMILIES,
    check_family_declared,
    check_font_stack,
    contrast_ratio,
)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  OK   {gate}  {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}  {diagnostic}")


def gate_declarable() -> None:
    """F10 is a family the gate accepts, not prose in a dataset."""
    v = check_family_declared("F10")
    if v.status == "pass" and "F10" in v.observed:
        _ok("V-F10-DECLARABLE", f"check_family_declared('F10') -> {v.status}")
    else:
        _fail("V-F10-DECLARABLE", f"got {v.status}: {v.observed}")


def gate_boundary() -> None:
    """The range grew by one, so the off-by-one is the live risk.

    F11 must still be refused, AND the refusal must SAY F1..F10. A message that
    still reads "F1..F9" is a gate telling an operator to declare a family the
    gate would then reject -- the failure mode of every widened enum.
    """
    v = check_family_declared("F11")
    said_range = "F1..F10" in (v.observed or "") or "F1..F10" in (v.recommendation or "")
    if v.status == "fail" and v.severity == "critical" and said_range:
        _ok("V-F10-BOUNDARY", "F11 refused, message names F1..F10")
    else:
        _fail("V-F10-BOUNDARY",
              f"status={v.status} sev={v.severity} range_named={said_range} :: {v.observed}")

    if len(KNOWN_FAMILIES) == 10:
        _ok("V-F10-RANGE-SIZE", f"KNOWN_FAMILIES n={len(KNOWN_FAMILIES)}")
    else:
        _fail("V-F10-RANGE-SIZE", f"expected 10, got {len(KNOWN_FAMILIES)}")


def gate_font_licence() -> None:
    """F10 defers to the platform's own sans -- deliberately, and NARROWLY.

    Both branches, because the licence is only meaningful if it is scoped: the
    SAME stack that F10 may keep must still be refused for a family that has not
    earned it. A one-sided assertion here would pass with the licence granted to
    everyone, which is the exact way this check stops being a check.
    """
    system_stack = ["-apple-system", "system-ui", "sans-serif"]

    granted = check_font_stack(system_stack, "F10")
    if granted.status == "pass":
        _ok("V-F10-FONT-LICENCE-GRANTED", f"F10 keeps the platform stack ({granted.status})")
    else:
        _fail("V-F10-FONT-LICENCE-GRANTED", f"F10 was refused its own licence: {granted.observed}")

    refused = check_font_stack(system_stack, "F9")
    if refused.status == "fail":
        _ok("V-F10-FONT-LICENCE-SCOPED", "same stack still refused for F9")
    else:
        _fail("V-F10-FONT-LICENCE-SCOPED",
              "F9 was allowed a default-tier stack -- the licence is not scoped")

    if "F10" in FAMILIES_SANCTIONING_DEFAULT_FONTS and "F9" not in FAMILIES_SANCTIONING_DEFAULT_FONTS:
        _ok("V-F10-FONT-TABLE", f"sanctioning set = {sorted(FAMILIES_SANCTIONING_DEFAULT_FONTS)}")
    else:
        _fail("V-F10-FONT-TABLE", f"unexpected set {sorted(FAMILIES_SANCTIONING_DEFAULT_FONTS)}")


def gate_hero_floor() -> None:
    """THE FAMILY'S SIGNATURE COLLISION, made refusable (CDIO-06 sec.5 F10a).

    F10's characteristic gesture is the screen's primary fact in white on a large
    surface filled with the one saturated accent. Whether that clears the body
    floor is decided entirely by the accent's luminance -- and the friendly blues
    this family reaches for sit right on the line, failing while looking
    perfectly pleasant. Nothing about the declared family can detect this; only
    the ratio can.

    Both branches: the accent the family WANTS must fail, and the darkened accent
    that fixes it must pass. Without the second, a check that failed every colour
    would look like a working floor.
    """
    friendly = "#4a9eff"   # the blue the reference bank reaches for
    darkened = "#1d4ed8"   # the same hue, chosen against the contrast it must carry
    white = "#ffffff"

    r_bad = contrast_ratio(white, friendly)
    r_good = contrast_ratio(white, darkened)

    if r_bad < CONTRAST_BODY_MIN:
        _ok("V-F10-HERO-FLOOR-REFUSES", f"white on {friendly} = {r_bad}:1 < {CONTRAST_BODY_MIN}:1")
    else:
        _fail("V-F10-HERO-FLOOR-REFUSES",
              f"the family's own accent passed at {r_bad}:1 -- the trap is undetectable")

    if r_good >= CONTRAST_BODY_MIN:
        _ok("V-F10-HERO-FLOOR-ADMITS", f"white on {darkened} = {r_good}:1 >= {CONTRAST_BODY_MIN}:1")
    else:
        _fail("V-F10-HERO-FLOOR-ADMITS",
              f"the darkened accent also failed at {r_good}:1 -- check refuses everything")


def main() -> int:
    gate_declarable()
    gate_boundary()
    gate_font_licence()
    gate_hero_floor()
    total = _passes + _fails
    print(f"CDIO_F10_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
