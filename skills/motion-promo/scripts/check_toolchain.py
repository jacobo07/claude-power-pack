#!/usr/bin/env python3
"""Preflight for the motion-promo skill: can this machine actually render?

Checks the two things a render depends on and nothing else — a headless
Chromium that launches, and an ffmpeg that can encode H.264. Both are
pip-vendored, so neither needs a system install.

    python check_toolchain.py

Exit 0 = ready to render. Exit 1 = a named thing is missing, with the
command that fixes it.
"""
from __future__ import annotations

import subprocess
import sys

problems: list[tuple[str, str]] = []


def check_pillow() -> str:
    try:
        import PIL
    except ImportError:
        problems.append(("Pillow (contact sheets)", "pip install pillow"))
        return "MISSING"
    return f"OK  {getattr(PIL, '__version__', '?')}"


def check_ffmpeg() -> str:
    try:
        import imageio_ffmpeg
    except ImportError:
        problems.append(("imageio-ffmpeg (H.264 encoder)", "pip install imageio-ffmpeg"))
        return "MISSING"
    try:
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        problems.append(("imageio-ffmpeg binary", f"reinstall imageio-ffmpeg ({exc})"))
        return "MISSING"
    encoders = subprocess.run([exe, "-hide_banner", "-encoders"],
                              capture_output=True, text=True).stdout
    if "libx264" not in encoders:
        problems.append(("libx264 in ffmpeg", f"the ffmpeg at {exe} cannot encode H.264"))
        return "NO libx264"
    return f"OK  libx264  {exe}"


def check_chromium() -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        problems.append(("playwright", "pip install playwright && playwright install chromium"))
        return "MISSING"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            version = browser.version
            page = browser.new_page(viewport={"width": 64, "height": 64})
            page.set_content("<canvas id=c width=64 height=64></canvas>")
            shot = page.screenshot()
            browser.close()
    except Exception as exc:
        problems.append(("Chromium browser", f"playwright install chromium  ({exc})"))
        return "LAUNCH FAILED"
    return f"OK  Chromium {version}, screenshot {len(shot)} bytes"


def main() -> int:
    print("motion-promo toolchain")
    print("-" * 62)
    print(f"  ffmpeg    {check_ffmpeg()}")
    print(f"  chromium  {check_chromium()}")
    print(f"  pillow    {check_pillow()}")
    print("-" * 62)
    if problems:
        print(f"{len(problems)} thing(s) to fix before rendering:\n")
        for what, fix in problems:
            print(f"  {what}\n      {fix}")
        return 1
    print("ready to render")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
