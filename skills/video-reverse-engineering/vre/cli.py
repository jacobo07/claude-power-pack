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
    t.add_argument("--ocr-stride", type=int, default=1, help="OCR every Nth frame (slow OCR); timing is then N-frame")
    t.add_argument("--no-text", action="store_true")
    t.add_argument("--no-layers", action="store_true")
    t.add_argument("--no-flow", action="store_true")
    t.add_argument("--sam2", help="SAM 2 checkpoint (.pt); without it the model-free colour follower runs")
    g = sub.add_parser("generate", help="spec + brand + copy -> Remotion composition (TSX)")
    g.add_argument("spec_dir")
    g.add_argument("--brand", help="brand JSON {font, light:{...}, dark:{...}}")
    g.add_argument("--copy", help="copy JSON {element id: text}; the reference's text is never used")
    g.add_argument("--out", required=True)
    g.add_argument("--strict", action="store_true", help="fail when a text slot has no copy")
    o = sub.add_parser("oneshot", help="analyze -> track -> generate -> render -> judge -> fix, 2-5 rounds")
    o.add_argument("video")
    o.add_argument("--out", required=True)
    o.add_argument("--project", required=True, help="Remotion project dir with node_modules (scratch copy is rendered)")
    o.add_argument("--tolerances", required=True, help="frozen tolerances JSON from vre.judge.freeze; never defaulted")
    o.add_argument("--brand")
    o.add_argument("--copy")
    o.add_argument("--rounds", type=int, default=3)
    o.add_argument("--scale", type=float, default=1.0, help="Remotion render scale")
    o.add_argument("--reference-spec", help="spec dir of an already tracked reference (reused, not re-measured)")
    o.add_argument("--ocr-stride", type=int, default=1)
    o.add_argument("--sam2", help="SAM 2 checkpoint for layer tracking of reference and candidates")
    o.add_argument("--rebrand", action="store_true", help="new brand/copy: judge moves and layout, skip pixels")
    sub.add_parser("deps", help="optional engines, licences and their state")
    args = ap.parse_args(argv)
    if args.cmd == "deps":
        from .deps import status

        for row in status():
            print(f"{row['name']:<20} {row['state']:<12} {row.get('licence', row.get('reason', ''))}")
        return 0
    if args.cmd == "generate":
        from .generate import generate

        rep = generate(args.spec_dir, args.out, brand=args.brand, copy=args.copy, strict=args.strict)
        print(f"{rep['shots']} shots, {rep['rows']} rows, unfilled text slots "
              f"{len(rep['unfilled_text'])} -> {args.out}")
        return 0
    if args.cmd == "oneshot":
        from pathlib import Path

        from .layers import default_provider
        from .oneshot import oneshot, remotion_renderer, side_by_side

        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        rep = oneshot(args.video, args.out, brand=args.brand, copy_file=args.copy, tolerances=args.tolerances,
                      renderer=remotion_renderer(args.project, out, scale=args.scale), rounds=args.rounds,
                      provider=default_provider(args.sam2), rebrand=args.rebrand,
                      ocr_stride=args.ocr_stride, reference_spec=args.reference_spec)
        last = out / f"round{rep['rounds_run']}" / "candidate.mp4"
        side_by_side(args.video, str(last), str(out / "side_by_side.mp4"))
        print(f"{rep['final_level']} after {rep['rounds_run']}/{rep['cap']} rounds, critical {rep['critical_failures']}"
              f" -> {out}/delta_report.json, side_by_side.mp4")
        return 0 if rep["final_level"] != "FAIL" else 2
    if args.cmd == "track":
        from .track import track

        from .layers import default_provider

        tt = track(args.spec_dir, video=args.video, width=args.width, text_on=not args.no_text,
                   ocr_stride=args.ocr_stride, layers_on=not args.no_layers, flow_on=not args.no_flow,
                   provider=default_provider(args.sam2) if not args.no_layers else None)
        print(f"text: {tt.get('engine')} {tt.get('status')}, {len(tt.get('tracks', []))} tracks -> "
              f"{args.spec_dir}/spec.json")
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
