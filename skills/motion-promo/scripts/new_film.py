#!/usr/bin/env python3
"""Build a film .html from a beat-sheet JSON plus the engine template.

The engine is 30 KB of drawing code that never changes between films. Only
the FILM block at the top does. This script swaps that one block, so making
a film costs a beat sheet, not a rewrite of the renderer.

Usage
    python new_film.py --spec beats.json --out meridian.html
    python new_film.py --spec beats.json --out f.html --template custom.html

The spec is exactly the FILM object:
    {
      "title":  "Meridian",
      "aspect": "9:16",
      "fps":    30,
      "brand":  { "hero": "#00D4FF", "accent": null },
      "beats": [
        { "shot": "grid-sweep", "dur": 2.6, "text": "Meetings nobody hates" }
      ]
    }

Exit codes: 0 built (warnings allowed), 2 the spec is not buildable.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = HERE.parent / "assets" / "film.template.html"

ASPECTS = {"9:16": (1080, 1920), "1:1": (1080, 1080), "16:9": (1920, 1080)}
HEX_RE = re.compile(r"^#?[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")

START = "const FILM = "
END = "/* ═══════════════════════ END FILM"


def known_shots(template_text: str) -> list[str]:
    """Read the shot names out of the engine itself, so this script can never
    drift from what the template can actually draw."""
    return sorted(set(re.findall(r'SHOTS\["([a-z-]+)"\]', template_text)))


def validate(spec: dict, shots: list[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    aspect = spec.get("aspect")
    if aspect not in ASPECTS:
        errors.append(f"aspect must be one of {list(ASPECTS)}, got {aspect!r}")

    fps = spec.get("fps", 30)
    if not isinstance(fps, int) or not (12 <= fps <= 60):
        errors.append(f"fps must be an integer from 12 to 60, got {fps!r}")

    brand = spec.get("brand") or {}
    for key in ("hero", "accent"):
        val = brand.get(key)
        if val is not None and not HEX_RE.match(str(val)):
            errors.append(f"brand.{key} must be a hex colour like #00D4FF, got {val!r}")
    if not brand.get("hero"):
        warnings.append("no brand.hero given — the film falls back to the house cyan")

    beats = spec.get("beats")
    if not isinstance(beats, list) or not beats:
        errors.append("beats must be a non-empty list")
        return errors, warnings

    total = 0.0
    for i, b in enumerate(beats):
        where = f"beat {i + 1}"
        if not isinstance(b, dict):
            errors.append(f"{where} is not an object")
            continue
        shot = b.get("shot")
        if shot not in shots:
            errors.append(f"{where}: unknown shot {shot!r}. Available: {', '.join(shots)}")
        dur = b.get("dur")
        if not isinstance(dur, (int, float)) or dur <= 0:
            errors.append(f"{where}: dur must be a positive number, got {dur!r}")
            continue
        total += float(dur)
        if dur < 1.2:
            warnings.append(f"{where} is {dur}s — under 1.2s a beat reads as a flicker")
        if dur > 6.0:
            warnings.append(f"{where} is {dur}s — over 6s a single idea starts to sit")
        if shot == "number-slam" and not b.get("value"):
            warnings.append(f"{where}: number-slam without a `value` falls back to `text`")
        words = len(str(b.get("text") or "").split())
        if words > 6:
            warnings.append(f"{where}: {words} words on screen — five or fewer reads better")

    if not 4 <= len(beats) <= 7:
        warnings.append(f"{len(beats)} beats — 4 to 7 is the range that holds together")
    if total < 12:
        warnings.append(f"{total:.1f}s total — under 12s a film feels rushed")
    if total > 45:
        warnings.append(f"{total:.1f}s total — over 45s needs a real narrative to justify itself")

    return errors, warnings


def build(spec: dict, template_text: str) -> str:
    i = template_text.find(START)
    j = template_text.find(END)
    if i < 0 or j < 0 or j <= i:
        raise ValueError(
            "the template has no recognisable FILM block "
            f"(looked for {START!r} then {END!r})"
        )
    block = "const FILM = " + json.dumps(spec, indent=2, ensure_ascii=False) + ";\n"
    return template_text[:i] + block + template_text[j:]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build a film .html from a beat-sheet JSON.")
    ap.add_argument("--spec", required=True, help="path to the beat-sheet JSON")
    ap.add_argument("--out", required=True, help="path to write the film .html")
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="engine template .html")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args(argv)

    tpl = Path(args.template)
    if not tpl.is_file():
        print(f"ERROR: no template at {tpl}", file=sys.stderr)
        return 2
    template_text = tpl.read_text(encoding="utf-8")

    spec_path = Path(args.spec)
    if not spec_path.is_file():
        print(f"ERROR: no spec at {spec_path}", file=sys.stderr)
        return 2
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: {spec_path} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    shots = known_shots(template_text)
    errors, warnings = validate(spec, shots)

    for w in warnings:
        print(f"warn     {w}")
    for e in errors:
        print(f"ERROR    {e}", file=sys.stderr)
    if errors or (args.strict and warnings):
        return 2

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(spec, template_text), encoding="utf-8")

    beats = spec["beats"]
    total = sum(float(b["dur"]) for b in beats)
    w, h = ASPECTS[spec["aspect"]]
    fps = spec.get("fps", 30)
    print(f"built    {out}")
    print(f"film     {spec.get('title', out.stem)}  {spec['aspect']}  {w}x{h} @ {fps}fps")
    print(f"length   {total:.2f}s  {round(total * fps)} frames  {len(beats)} beats")
    t = 0.0
    for i, b in enumerate(beats):
        line = str(b.get("text") or b.get("value") or "")
        print(f"  {i + 1}  {t:5.2f}s  {b['shot']:<12} {line[:44]}")
        t += float(b["dur"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
