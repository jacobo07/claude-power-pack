#!/usr/bin/env python3
"""Render a motion-promo film HTML to PNG stills and/or an H.264 MP4.

The film HTML is deterministic: every pixel is a pure function of the frame
index. This script drives it one frame at a time through headless Chromium
and pipes the PNGs straight into ffmpeg, so what you scrub in the browser and
what lands in the MP4 are the same picture.

Usage
    python render_film.py film.html --out film.mp4
    python render_film.py film.html --stills 5 --stills-dir ./preview
    python render_film.py film.html --out cut.mp4 --range 90:210

Toolchain (both already vendored by pip, nothing to install globally):
    playwright        headless Chromium
    imageio-ffmpeg    static ffmpeg with libx264
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def _err(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"ERROR: {msg}", file=sys.stderr, flush=True)
    raise SystemExit(2)


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
    except ImportError:
        _err("imageio-ffmpeg is not installed. Run: pip install imageio-ffmpeg")
    return imageio_ffmpeg.get_ffmpeg_exe()


def has_libx264(exe: str) -> bool:
    out = subprocess.run([exe, "-hide_banner", "-encoders"],
                         capture_output=True, text=True).stdout
    return "libx264" in out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Render a motion-promo film to MP4 / stills.")
    p.add_argument("html", help="path to the film .html")
    p.add_argument("--out", help="output .mp4 path (omit to render stills only)")
    p.add_argument("--stills", type=int, default=0,
                   help="also write N evenly spaced preview PNGs")
    p.add_argument("--stills-dir", default=None,
                   help="where the preview PNGs go (default: alongside the html)")
    p.add_argument("--range", dest="rng", default=None,
                   help="frame range A:B, inclusive of A and exclusive of B")
    p.add_argument("--crf", type=int, default=17, help="x264 quality, lower is better (default 17)")
    p.add_argument("--preset", default="slow", help="x264 preset (default slow)")
    p.add_argument("--fps", type=int, default=0, help="override the film's own fps")
    p.add_argument("--scale", type=float, default=1.0,
                   help="render scale, e.g. 0.5 for a fast rough cut")
    p.add_argument("--timeout", type=int, default=60_000, help="page load timeout in ms")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    html = Path(args.html).resolve()
    if not html.is_file():
        _err(f"no such file: {html}")

    if not args.out and not args.stills:
        _err("nothing to do: pass --out for an MP4, --stills N for previews, or both")

    exe = None
    if args.out:
        exe = ffmpeg_exe()
        if not has_libx264(exe):
            _err(f"the ffmpeg at {exe} was built without libx264; cannot encode H.264")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _err("playwright is not installed. Run: pip install playwright && playwright install chromium")

    started = time.time()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=[
            "--force-color-profile=srgb",
            "--disable-lcd-text",
            "--hide-scrollbars",
            "--disable-gpu-vsync",
        ])
        page = browser.new_page(viewport={"width": 800, "height": 600}, device_scale_factor=1)
        page.goto(html.as_uri() + "?capture=1", timeout=args.timeout)

        try:
            page.wait_for_function("window.__ready === true", timeout=args.timeout)
        except Exception as exc:
            browser.close()
            _err(f"{html.name} did not initialise as a motion-promo film "
                 f"(window.__ready never became true): {exc}")

        meta = page.evaluate("window.__meta")
        if not isinstance(meta, dict) or "frames" not in meta:
            browser.close()
            _err(f"{html.name} exposes no window.__meta; it is not a motion-promo film")

        w, h = int(meta["w"]), int(meta["h"])
        fps = int(args.fps or meta["fps"])
        total = int(meta["frames"])

        scale = max(0.05, min(1.0, args.scale))
        # H.264 needs even dimensions on yuv420p.
        out_w = max(2, (int(round(w * scale)) // 2) * 2)
        out_h = max(2, (int(round(h * scale)) // 2) * 2)

        first, last = 0, total
        if args.rng:
            try:
                a, b = args.rng.split(":")
                first, last = int(a), int(b)
            except ValueError:
                browser.close()
                _err(f"--range wants A:B, got {args.rng!r}")
            first = max(0, first)
            last = min(total, last)
            if last <= first:
                browser.close()
                _err(f"--range {args.rng} is empty (film has {total} frames)")

        page.set_viewport_size({"width": w, "height": h})
        clip = {"x": 0, "y": 0, "width": w, "height": h}

        beats = meta.get("beats") or []
        print(f"film     {meta.get('title', html.stem)}  {meta.get('aspect','?')}  {w}x{h} @ {fps}fps")
        print(f"length   {meta.get('duration', 0):.2f}s  {total} frames  {len(beats)} beats")
        if scale != 1.0:
            print(f"scale    {scale:g}  ->  {out_w}x{out_h}")
        if (first, last) != (0, total):
            print(f"range    frames {first}..{last - 1}")
        sys.stdout.flush()

        # ---- stills ---------------------------------------------------
        if args.stills > 0:
            sdir = Path(args.stills_dir) if args.stills_dir else html.parent / f"{html.stem}_stills"
            sdir.mkdir(parents=True, exist_ok=True)
            n = args.stills
            picks = [first + round(k * (last - 1 - first) / max(1, n - 1)) for k in range(n)]
            for k, fi in enumerate(picks):
                page.evaluate("i => window.__renderFrame(i)", fi)
                dest = sdir / f"still_{k:02d}_f{fi:05d}.png"
                page.screenshot(path=str(dest), clip=clip)
                print(f"still    {dest.name}  (frame {fi}, t={fi/fps:.2f}s)")
            sys.stdout.flush()

        # ---- video ----------------------------------------------------
        if args.out:
            out = Path(args.out).resolve()
            out.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                exe, "-y", "-loglevel", "error",
                "-f", "image2pipe", "-vcodec", "png", "-r", str(fps), "-i", "-",
                "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
                "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            ]
            if (out_w, out_h) != (w, h):
                cmd += ["-vf", f"scale={out_w}:{out_h}:flags=lanczos"]
            cmd += ["-r", str(fps), str(out)]

            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            count = last - first
            t0 = time.time()
            broke = None
            try:
                for n, fi in enumerate(range(first, last)):
                    page.evaluate("i => window.__renderFrame(i)", fi)
                    png = page.screenshot(clip=clip)
                    proc.stdin.write(png)
                    if n % 30 == 0 or n == count - 1:
                        done = n + 1
                        rate = done / max(1e-6, time.time() - t0)
                        eta = (count - done) / max(1e-6, rate)
                        print(f"frame    {done}/{count}  {rate:.1f} fps  eta {eta:5.1f}s")
                        sys.stdout.flush()
            except BrokenPipeError as exc:
                broke = exc
            finally:
                try:
                    proc.stdin.close()
                except (BrokenPipeError, OSError) as exc:
                    print(f"note     closing the ffmpeg pipe raised {exc!r}", file=sys.stderr)
                stderr = proc.stderr.read().decode("utf-8", "replace")
                rc = proc.wait()

            if broke is not None or rc != 0:
                browser.close()
                _err(f"ffmpeg exited {rc}. stderr:\n{stderr.strip() or '(empty)'}")

            size = out.stat().st_size
            print(f"wrote    {out}  ({size/1_000_000:.2f} MB)")

        browser.close()

    print(f"done     {time.time() - started:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
