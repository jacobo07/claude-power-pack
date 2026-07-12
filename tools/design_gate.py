#!/usr/bin/env python3
"""design_gate.py -- the anti-slop done-gate for any PP output with a visual surface.

This is an ENTRYPOINT, not an engine. Every verdict it emits is computed by
`modules.cdio.scorer` -- the same deterministic scorer the cdio-reviewer agent uses
and the same sealed verdict contract (PR-CDIO-REVIEW-GATE-001: APPROVE requires
score >= 80 AND zero critical). There is exactly one definition of "acceptable
design" in the Power Pack, and it does not live in this file.

What it adds on top of the scorer: it reads a project's DESIGN.md, extracts the
declared family, the font stack, and the palette, and feeds them to the CDIO-06
anti-slop checks. Before this, the Anti-Slop Kit could not FAIL anything.

FAIL-OPEN, ABSOLUTELY (design constraint): a gate that cannot read its artifact
returns SKIP and exit 0. A broken gate must never block real work -- it must only
ever be the reason a genuinely-slop surface is stopped, never the reason a good one
is. Every unreadable / missing / unparseable input is a SKIP with a stated reason,
never a BLOCK.

Usage:
    python tools/design_gate.py <path/to/DESIGN.md>
    python tools/design_gate.py <path/to/DESIGN.md> --json

Exit codes:
    0  APPROVE (score >= 80, zero critical) or SKIP (gate could not evaluate)
    1  REVISE  (majors to resolve)
    2  BLOCK   (a critical -- slop detected, or no family declared)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cdio.scorer import (  # noqa: E402
    check_design_md_exists,
    check_family_declared,
    check_font_stack,
    check_palette_cliche,
    score_review,
)

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}")
FONT_RE = re.compile(r"^\s*fontFamily:\s*(.+?)\s*$", re.MULTILINE)
FAMILY_RE = re.compile(r"^\s*aesthetic_family:\s*([A-Za-z0-9]+)", re.MULTILINE)
# The page ground: the token a surface actually sits on. `neutral` is the DESIGN.md
# convention for it; `background` and `bg` are accepted as common aliases.
GROUND_RE = re.compile(r"^\s*(?:neutral|background|bg):\s*\"?(#[0-9a-fA-F]{3,8})\"?",
                       re.MULTILINE)


class SkipGate(Exception):
    """Raised when the gate cannot evaluate. Always fail-open -> SKIP, exit 0."""


def _front_matter(text: str) -> str:
    """Return the YAML front-matter block, or the whole text if there is no fence.

    Deliberately tolerant: the point is to extract tokens, not to validate YAML. A
    malformed fence yields the whole document, and the regexes simply find less.
    """
    if text.lstrip().startswith("---"):
        parts = text.lstrip().split("---", 2)
        if len(parts) >= 3:
            return parts[1]
    return text


def parse_design_md(path: str) -> dict:
    """Extract (family, fonts, colors, ground) from a DESIGN.md. Raises SkipGate if
    the file cannot be read -- never a hard failure."""
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:   # -sig: strip a BOM
            text = fh.read()
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        # UnicodeDecodeError is NOT an OSError. Catching only OSError here let a
        # binary / mis-encoded artifact crash the gate instead of failing open --
        # a broken gate would then have blocked good work, which is the one thing
        # this gate must never do. Caught by V-DESIGN-FAIL-OPEN.
        raise SkipGate(f"cannot decode {path}: {exc}") from exc

    fm = _front_matter(text)

    family = ""
    m = FAMILY_RE.search(fm)
    if m:
        family = m.group(1).strip()

    fonts = []
    for raw in FONT_RE.findall(fm):
        # Strip inline comments and quotes: `Lora   # body serif` -> `Lora`
        name = raw.split("#", 1)[0].strip().strip("\"'")
        if name:
            fonts.append(name)

    colors = sorted(set(HEX_RE.findall(fm)))

    ground = None
    g = GROUND_RE.search(fm)
    if g:
        ground = g.group(1)

    return {"family": family, "fonts": fonts, "colors": colors, "ground": ground}


def design_gate(design_md_path: str) -> dict:
    """Run the CDIO-06 anti-slop checks against a DESIGN.md.

    Returns a dict with `verdict` in {APPROVE, REVISE, BLOCK, SKIP}. SKIP means the
    gate could not evaluate and is standing down -- it is never a failure verdict.
    """
    presence = check_design_md_exists(design_md_path)
    if presence.status == "fail":
        # No DESIGN.md at all is a REAL finding, not a gate malfunction: a visual
        # surface with no tokens is unreviewable by construction. It BLOCKs.
        result = score_review([presence])
        out = result.to_json()
        out["design_md"] = design_md_path
        return out

    try:
        parsed = parse_design_md(design_md_path)
    except SkipGate as exc:
        return {"verdict": "SKIP", "score": None, "reason": str(exc),
                "design_md": design_md_path, "is_done": True}

    verdicts = [
        presence,
        check_family_declared(parsed["family"]),
        check_font_stack(parsed["fonts"], parsed["family"]),
        check_palette_cliche(parsed["colors"], background=parsed["ground"]),
    ]

    result = score_review(verdicts)
    out = result.to_json()
    out["design_md"] = design_md_path
    out["parsed"] = parsed
    return out


def _render(out: dict) -> str:
    lines = [f"design_gate: {out['verdict']}  (score={out.get('score')})",
             f"  design.md: {out.get('design_md')}",
             f"  reason:    {out.get('reason')}"]
    for sev in ("critical", "major", "minor"):
        for f in out.get(sev, []) or []:
            lines.append(f"  [{sev.upper():8}] {f['criterion']}: {f['observed']}")
            if f.get("recommendation"):
                lines.append(f"             -> {f['recommendation']}")
    for f in out.get("passed", []) or []:
        lines.append(f"  [PASS    ] {f['criterion']}: {f['observed']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CDIO-06 anti-slop design gate")
    ap.add_argument("design_md", help="path to the project's DESIGN.md")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args(argv)

    try:
        out = design_gate(args.design_md)
    except Exception as exc:                      # noqa: BLE001 -- fail-open is the contract
        out = {"verdict": "SKIP", "score": None, "is_done": True,
               "reason": f"gate error, standing down (fail-open): {exc}",
               "design_md": args.design_md}

    print(json.dumps(out, indent=2, ensure_ascii=False) if args.json else _render(out))

    return {"APPROVE": 0, "SKIP": 0, "REVISE": 1, "BLOCK": 2}.get(out["verdict"], 0)


if __name__ == "__main__":
    raise SystemExit(main())
