#!/usr/bin/env python3
"""Render one still per beat and montage them into a single contact sheet.

This is the composition check that happens before committing to a full
render: one image showing every beat at its midpoint, labelled, so the
framing and the colour travel can be judged in one look instead of ten.

Usage
    python contact_sheet.py film.html --out sheet.png
    python contact_sheet.py film.html --out sheet.png --cols 5 --tile 300
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Contact sheet of every beat in a film.")
    ap.add_argument("html", help="path to the film .html")
    ap.add_argument("--out", required=True, help="output .png")
    ap.add_argument("--cols", type=int, default=0, help="columns (default: auto)")
    ap.add_argument("--tile", type=int, default=340, help="tile width in px")
    ap.add_argument("--at", type=float, default=0.55,
                    help="where inside each beat to sample, 0..1 (default 0.55)")
    ap.add_argument("--timeout", type=int, default=60_000)
    args = ap.parse_args(argv)

    html = Path(args.html).resolve()
    if not html.is_file():
        print(f"ERROR: no such file: {html}", file=sys.stderr)
        return 2

    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("ERROR: Pillow is not installed. Run: pip install pillow", file=sys.stderr)
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright is not installed. Run: pip install playwright", file=sys.stderr)
        return 2

    shots: list[tuple[str, "Image.Image"]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--force-color-profile=srgb", "--disable-lcd-text",
                                           "--hide-scrollbars"])
        page = browser.new_page(viewport={"width": 800, "height": 600}, device_scale_factor=1)
        page.goto(html.as_uri() + "?capture=1", timeout=args.timeout)
        try:
            page.wait_for_function("window.__ready === true", timeout=args.timeout)
        except Exception as exc:
            browser.close()
            print(f"ERROR: {html.name} never became ready: {exc}", file=sys.stderr)
            return 2

        meta = page.evaluate("window.__meta")
        w, h, fps = int(meta["w"]), int(meta["h"]), int(meta["fps"])
        beats = meta.get("beats") or []
        if not beats:
            browser.close()
            print("ERROR: the film exposes no beats", file=sys.stderr)
            return 2

        page.set_viewport_size({"width": w, "height": h})
        clip = {"x": 0, "y": 0, "width": w, "height": h}
        for i, b in enumerate(beats):
            t = b["start"] + (b["end"] - b["start"]) * args.at
            fi = max(0, min(int(meta["frames"]) - 1, round(t * fps)))
            page.evaluate("i => window.__renderFrame(i)", fi)
            png = page.screenshot(clip=clip)
            shots.append((f"{i + 1}. {b['shot']}  {t:.1f}s", Image.open(io.BytesIO(png)).convert("RGB")))
            print(f"beat     {i + 1}/{len(beats)}  {b['shot']}  t={t:.2f}s")
            sys.stdout.flush()
        browser.close()

    n = len(shots)
    cols = args.cols or min(5, n)
    rows = (n + cols - 1) // cols
    tw = args.tile
    th = round(tw * h / w)
    label = 22
    pad = 8

    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + label + pad) + pad), (12, 12, 16))
    draw = ImageDraw.Draw(sheet)
    for k, (name, img) in enumerate(shots):
        cx = pad + (k % cols) * (tw + pad)
        cy = pad + (k // cols) * (th + label + pad)
        sheet.paste(img.resize((tw, th), Image.LANCZOS), (cx, cy))
        draw.text((cx + 2, cy + th + 5), name, fill=(190, 190, 205))

    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"wrote    {out}  ({cols}x{rows} tiles, {sheet.width}x{sheet.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
