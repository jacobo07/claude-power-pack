"""vre command line. Run from the skill directory: `python -m vre <command> ...`."""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="vre", description="video reverse engineering")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="probe, shots, palette, audio -> spec.json + REVERSE.md")
    a.add_argument("video")
    a.add_argument("--out", required=True)
    a.add_argument("--width", type=int, default=144)
    a.add_argument("--brand", help="brand roles JSON {light:{...}, dark:{...}}")
    a.add_argument("--no-words", action="store_true")
    a.add_argument("--no-beats", action="store_true")
    t = sub.add_parser("track", help="fill spec.json rows from the video (text tracks)")
    t.add_argument("spec_dir")
    t.add_argument("--video", help="override the video path stored in the spec")
    t.add_argument("--width", type=int, default=360)
    sub.add_parser("deps", help="optional engines, licences and their state")
    args = ap.parse_args(argv)
    if args.cmd == "deps":
        from .deps import status

        for row in status():
            print(f"{row['name']:<20} {row['state']:<12} {row.get('licence', row.get('reason', ''))}")
        return 0
    if args.cmd == "track":
        from .track import track

        tt = track(args.spec_dir, video=args.video, width=args.width)
        print(f"text: {tt['engine']} {tt['status']}, {len(tt['tracks'])} tracks -> {args.spec_dir}/spec.json")
        return 0
    from .pipeline import analyze

    brand = json.load(open(args.brand, encoding="utf-8")) if args.brand else None
    spec = analyze(args.video, args.out, width=args.width, words=not args.no_words, beats=not args.no_beats,
                   brand=brand)
    src = spec["source"]
    print(f"{src['width']}x{src['height']} @ {src['fps_exact']}, {src['decoded_frames']} frames, "
          f"{len(spec['shots'])} shots, {len(spec['cuts'])} cuts -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
