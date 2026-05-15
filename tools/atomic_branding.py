#!/usr/bin/env python3
"""atomic_branding.py - brand prompt -> Tailwind + Framer-Motion tokens.

Absorbs the Figma "brand design system" loop: a brand-identity prompt
deterministically yields an extended `tailwind.config.js` (tonal palette
50..950, type scale, radius, shadow, spacing) plus a sibling
`motion-tokens.ts` of Framer-Motion variants.

Jobs/Woz hybrid gate (Q4, audit Gap #8 — MEASURABLE):
  * token count = tiktoken cl100k_base if importable, else
    ceil(len(text)/4) (the documented Anthropic heuristic). The method
    actually used is printed and written into the report.
  * threshold = 2500 tokens PER emitted component (file).
  * Signature Visual (the palette/theme — brand-defining): Jobs
    precedence — over budget is a WARN, emission proceeds.
  * Utility / scaffolding (motion tokens — internal plumbing): Woz
    ABSOLUTE veto — over budget is a hard FAIL (exit 5), no emission.

Deterministic: identical brand string -> identical bytes. No network,
no LLM. CLI:
  --brand "<identity prompt>"   required
  --out <dir>                   default ./brand_out
  --report                      print the Jobs/Woz token verdict JSON
"""
from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
import os
import re
import sys

TOKEN_LIMIT = 2500

# Named hue anchors (HSL hue degrees). Brand prompt is scanned for these;
# otherwise the hue is derived deterministically from the prompt hash.
HUES = {
    "red": 0, "rose": 345, "pink": 330, "fuchsia": 300, "purple": 280,
    "violet": 265, "indigo": 245, "blue": 220, "sky": 200, "cyan": 190,
    "teal": 175, "emerald": 160, "green": 145, "lime": 100, "yellow": 50,
    "amber": 40, "orange": 25, "slate": 215, "gray": 220, "stone": 30,
    "sovereign": 265, "kobii": 265, "apex": 245,
}

# Tailwind-like tonal ladder: (step, lightness%, saturation-scale).
LADDER = [
    (50, 0.97, 0.55), (100, 0.93, 0.62), (200, 0.86, 0.70),
    (300, 0.76, 0.78), (400, 0.66, 0.86), (500, 0.55, 1.00),
    (600, 0.46, 0.98), (700, 0.38, 0.92), (800, 0.30, 0.84),
    (900, 0.23, 0.74), (950, 0.15, 0.62),
]


def count_tokens(text: str) -> tuple[int, str]:
    try:
        import tiktoken  # type: ignore
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text)), "tiktoken/cl100k_base"
    except Exception:  # noqa: BLE001 - heuristic fallback is intentional
        return math.ceil(len(text) / 4), "heuristic ceil(len/4)"


def _hue_for(brand: str) -> tuple[int, str]:
    low = brand.lower()
    for name, deg in HUES.items():
        if re.search(rf"\b{name}\b", low):
            return deg, name
    m = re.search(r"#([0-9a-f]{6})", low)
    if m:
        r, g, b = (int(m.group(1)[i:i + 2], 16) / 255 for i in (0, 2, 4))
        h, _l, _s = colorsys.rgb_to_hls(r, g, b)
        return int(h * 360), f"#{m.group(1)}"
    h = int(hashlib.sha256(brand.encode("utf-8")).hexdigest(), 16) % 360
    return h, "derived"


def _hex(h_deg: int, light: float, sat: float) -> str:
    r, g, b = colorsys.hls_to_rgb((h_deg % 360) / 360.0, light,
                                  min(1.0, 0.62 * sat + 0.20))
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def _slug(brand: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", brand.lower()).strip("-")
    return s[:32] or "brand"


def gen_tailwind(brand: str) -> str:
    hue, src = _hue_for(brand)
    slug = _slug(brand)
    scale = {str(step): _hex(hue, lt, sa) for step, lt, sa in LADDER}
    accent = (hue + 150) % 360
    accent_scale = {str(step): _hex(accent, lt, sa) for step, lt, sa in LADDER}
    cfg = {
        "brand": {"prompt": brand, "hue": hue, "hue_source": src},
        "primary": scale,
        "accent": accent_scale,
    }
    body = json.dumps(cfg, indent=2)
    return (
        f"// atomic_branding.py — deterministic from brand: {brand!r}\n"
        f"// hue={hue} ({src})  slug={slug}\n"
        "/** @type {import('tailwindcss').Config} */\n"
        "module.exports = {\n"
        "  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],\n"
        "  theme: {\n"
        "    extend: {\n"
        f"      colors: {{ primary: {json.dumps(scale, indent=8)},\n"
        f"                accent: {json.dumps(accent_scale, indent=8)} }},\n"
        "      borderRadius: { xl: '0.875rem', '2xl': '1.25rem',\n"
        "                      '3xl': '1.75rem' },\n"
        "      fontFamily: { sans: ['Inter var', 'system-ui', "
        "'sans-serif'],\n"
        "                    mono: ['JetBrains Mono', 'monospace'] },\n"
        "      fontSize: { '2xs': '0.6875rem', '3xl': '2rem',\n"
        "                  '4xl': '2.5rem', '5xl': '3.25rem' },\n"
        "      boxShadow: { 'brand': '0 10px 30px -10px " +
        scale['500'] + "55',\n"
        "                   'brand-lg': '0 20px 50px -12px " +
        scale['600'] + "66' },\n"
        "      spacing: { '18': '4.5rem', '22': '5.5rem', "
        "'30': '7.5rem' },\n"
        "    },\n"
        "  },\n"
        "  plugins: [],\n"
        f"}};\n// canonical: {body[:0]}"
        f"sha256={hashlib.sha256(body.encode()).hexdigest()[:16]}\n"
    )


def gen_motion(brand: str) -> str:
    hue, _src = _hue_for(brand)
    dur = 0.18 + (hue % 7) * 0.01  # deterministic, brand-tied micro-timing
    return (
        f"// atomic_branding.py — Framer-Motion tokens for {brand!r}\n"
        "import type { Variants, Transition } from 'framer-motion';\n\n"
        f"export const spring: Transition = "
        "{ type: 'spring', stiffness: 320, damping: 30 };\n"
        f"export const ease: Transition = "
        f"{{ duration: {dur:.3f}, ease: [0.22, 1, 0.36, 1] }};\n\n"
        "export const fade: Variants = {\n"
        "  hidden: { opacity: 0 },\n"
        "  show: { opacity: 1, transition: ease },\n"
        "};\n\n"
        "export const slideUp: Variants = {\n"
        "  hidden: { opacity: 0, y: 16 },\n"
        "  show: { opacity: 1, y: 0, transition: spring },\n"
        "};\n\n"
        "export const scaleIn: Variants = {\n"
        "  hidden: { opacity: 0, scale: 0.96 },\n"
        "  show: { opacity: 1, scale: 1, transition: spring },\n"
        "};\n\n"
        "export const staggerParent: Variants = {\n"
        "  hidden: {},\n"
        "  show: { transition: { staggerChildren: 0.06,\n"
        "                        delayChildren: 0.04 } },\n"
        "};\n"
    )


def _atomic_write(path: str, data: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(data)
    os.replace(tmp, path)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="brand -> tailwind+motion")
    ap.add_argument("--brand", required=True)
    ap.add_argument("--out", default=os.path.join(os.getcwd(), "brand_out"))
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)

    tw = gen_tailwind(a.brand)
    mo = gen_motion(a.brand)

    # Jobs/Woz hybrid gate — measurable.
    tw_tok, method = count_tokens(tw)
    mo_tok, _ = count_tokens(mo)
    components = [
        {"file": "tailwind.config.js", "kind": "signature-visual",
         "owner": "Jobs", "tokens": tw_tok, "limit": TOKEN_LIMIT,
         "over": tw_tok > TOKEN_LIMIT,
         "verdict": "WARN" if tw_tok > TOKEN_LIMIT else "PASS"},
        {"file": "motion-tokens.ts", "kind": "utility-scaffolding",
         "owner": "Woz", "tokens": mo_tok, "limit": TOKEN_LIMIT,
         "over": mo_tok > TOKEN_LIMIT,
         "verdict": "VETO" if mo_tok > TOKEN_LIMIT else "PASS"},
    ]
    report = {"brand": a.brand, "token_method": method,
              "threshold": TOKEN_LIMIT, "components": components}

    woz_veto = any(c["owner"] == "Woz" and c["over"] for c in components)
    if woz_veto:
        print(json.dumps(report, indent=2))
        print("WOZ ABSOLUTE VETO: utility component exceeds "
              f"{TOKEN_LIMIT} tokens — emission blocked.", file=sys.stderr)
        return 5

    twp = os.path.join(a.out, "tailwind.config.js")
    mop = os.path.join(a.out, "motion-tokens.ts")
    _atomic_write(twp, tw)
    _atomic_write(mop, mo)
    _atomic_write(os.path.join(a.out, "brand-report.json"),
                  json.dumps(report, indent=2) + "\n")

    if a.report:
        print(json.dumps(report, indent=2))
    else:
        print(f"tailwind.config.js -> {twp}  ({tw_tok} tok, {method})")
        print(f"motion-tokens.ts   -> {mop}  ({mo_tok} tok)")
        for c in components:
            print(f"  [{c['verdict']}] {c['file']} "
                  f"({c['owner']} owns, {c['tokens']}/{TOKEN_LIMIT})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
