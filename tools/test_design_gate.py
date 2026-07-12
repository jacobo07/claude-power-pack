#!/usr/bin/env python3
"""Done-gate for the CDIO-06 anti-slop design gate (V-DESIGN-*).

The gate must be OBSERVED REFUSING. A gate that has never been seen emitting FAIL is
a preference, not a gate (feedback_zero_cannot_fall). So the suite proves BOTH poles
are reachable: slop BLOCKs, and a real, characterful design system APPROVEs.

It also pins the load-bearing nuance: a default-tier font is NOT slop when the
declared family sanctions it (F1/F4/F6). If that case failed, this would be a blanket
font ban, which is a different -- and wrong -- product.

Run:  python tools/test_design_gate.py
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cdio.scorer import (  # noqa: E402
    check_family_declared,
    check_font_stack,
    check_palette_cliche,
)
from tools.design_gate import design_gate, parse_design_md  # noqa: E402

PASSES = 0
FAILS = 0


def _ok(gate: str, evidence: str) -> None:
    global PASSES
    PASSES += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global FAILS
    FAILS += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _write(tmpdir: str, name: str, body: str) -> str:
    path = os.path.join(tmpdir, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return path


SLOP = """---
name: SlopProject
colors:
  accent: "#8b5cf6"
  neutral: "#ffffff"
typography:
  h1:
    fontFamily: Roboto
  body-md:
    fontFamily: Inter
---
A surface with no declared family, an inherited font stack, and a purple accent
on a white ground.
"""

SANCTIONED = """---
name: SanctionedProject
aesthetic_family: F1
colors:
  accent: "#5e6ad2"
  neutral: "#ffffff"
typography:
  body-md:
    fontFamily: Inter
---
Editorial Minimalism. Inter is the deliberate choice here, not the default.
"""

REPO_TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "modules", "design-md", "DESIGN.md.template",
)


def main() -> int:
    print("V-DESIGN gates (CDIO-06 anti-slop)")

    with tempfile.TemporaryDirectory() as tmp:
        # --- V-DESIGN-SLOP-BLOCKS: the gate must be observed REFUSING ----------
        slop_path = _write(tmp, "SLOP.md", SLOP)
        out = design_gate(slop_path)
        crit = {f["criterion"] for f in out.get("critical", [])}
        if out["verdict"] == "BLOCK" and "aesthetic-family-declared" in crit \
                and "font-stack-intent" in crit and "palette-cliche" in crit:
            _ok("V-DESIGN-SLOP-BLOCKS",
                f"verdict=BLOCK score={out['score']} criticals={sorted(crit)}")
        else:
            _fail("V-DESIGN-SLOP-BLOCKS",
                  f"expected BLOCK with 3 criticals, got {out['verdict']} "
                  f"score={out['score']} criticals={sorted(crit)}")

        # --- V-DESIGN-SANCTIONED-FONT-PASSES: the nuance, not a blanket ban ----
        sanc_path = _write(tmp, "SANCTIONED.md", SANCTIONED)
        out = design_gate(sanc_path)
        font = next((f for f in out.get("passed", [])
                     if f["criterion"] == "font-stack-intent"), None)
        if out["verdict"] == "APPROVE" and font:
            _ok("V-DESIGN-SANCTIONED-FONT-PASSES",
                f"F1 + Inter -> APPROVE ({font['observed']})")
        else:
            _fail("V-DESIGN-SANCTIONED-FONT-PASSES",
                  f"F1 + Inter should APPROVE (family sanctions the default); "
                  f"got {out['verdict']} score={out['score']}")

        # --- V-DESIGN-FAIL-OPEN: a gate that cannot read must never block ------
        missing = os.path.join(tmp, "no-such-dir", "DESIGN.md")
        out = design_gate(missing)
        if out["verdict"] == "BLOCK" and out["score"] == 75:
            _ok("V-DESIGN-NO-DESIGN-MD-BLOCKS",
                "absent DESIGN.md is a real finding (critical), not a gate error")
        else:
            _fail("V-DESIGN-NO-DESIGN-MD-BLOCKS",
                  f"expected BLOCK on absent DESIGN.md, got {out['verdict']}")

        # A path that exists but is unreadable as text -> SKIP, exit-0, never BLOCK.
        binpath = os.path.join(tmp, "BINARY.md")
        with open(binpath, "wb") as fh:
            fh.write(b"\xff\xfe\x00\x00\x80\x81\x82")
        out = design_gate(binpath)
        if out["verdict"] == "SKIP" and out.get("is_done") is True:
            _ok("V-DESIGN-FAIL-OPEN", f"unreadable artifact -> SKIP ({out['reason'][:48]}...)")
        else:
            _fail("V-DESIGN-FAIL-OPEN",
                  f"a gate that cannot read must SKIP, not {out['verdict']}")

    # --- V-DESIGN-TEMPLATE-CLEAN: the PP's own canonical template must PASS ----
    out = design_gate(REPO_TEMPLATE)
    if out["verdict"] == "APPROVE":
        _ok("V-DESIGN-TEMPLATE-CLEAN",
            f"DESIGN.md.template APPROVE score={out['score']} "
            f"family={out['parsed']['family']} fonts={out['parsed']['fonts']}")
    else:
        _fail("V-DESIGN-TEMPLATE-CLEAN",
              f"the PP's own canonical template must clear its own gate; got "
              f"{out['verdict']} score={out['score']} "
              f"criticals={[f['criterion'] for f in out.get('critical', [])]}")

    # --- V-DESIGN-UNIT: the checks in isolation -------------------------------
    if check_family_declared("").status == "fail" \
            and check_family_declared("F3").status == "pass" \
            and check_family_declared("F99").status == "fail":
        _ok("V-DESIGN-UNIT-FAMILY", "absent + unknown fail; F3 passes")
    else:
        _fail("V-DESIGN-UNIT-FAMILY", "family check does not discriminate")

    if check_font_stack(["Inter"], "F3").status == "fail" \
            and check_font_stack(["Inter"], "F1").status == "pass" \
            and check_font_stack(["Lora", "Inter"], "F3").status == "pass":
        _ok("V-DESIGN-UNIT-FONT",
            "default-only fails unsanctioned family; passes F1; passes when paired")
    else:
        _fail("V-DESIGN-UNIT-FONT", "font check does not discriminate")

    # Cream (#f4f3ee) has a relative luminance of ~0.90 -- it IS a near-white ground,
    # so a purple accent on cream is the same cliché as purple on white and must also
    # fail. The discriminator is the HUE, not the warmth of the ground: terracotta on
    # cream passes, purple on cream does not. A mid-tone ground (#5a5a5a) is neither
    # near-white nor near-black, so the clichéd-gradient rule does not reach it.
    if check_palette_cliche(["#8b5cf6"], background="#ffffff").status == "fail" \
            and check_palette_cliche(["#8b5cf6"], background="#f4f3ee").status == "fail" \
            and check_palette_cliche(["#8b5cf6"], background="#5a5a5a").status == "pass" \
            and check_palette_cliche(["#16d5e6"]).status == "fail" \
            and check_palette_cliche(["#c96442"], background="#f4f3ee").status == "pass":
        _ok("V-DESIGN-UNIT-PALETTE",
            "purple fails on white AND on cream (both near-white); passes on a mid-tone "
            "ground; teal fingerprint fails; terracotta on cream passes")
    else:
        _fail("V-DESIGN-UNIT-PALETTE", "palette check does not discriminate")

    total = PASSES + FAILS
    print(f"\nDESIGN_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
