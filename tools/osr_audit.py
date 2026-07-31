#!/usr/bin/env python3
"""osr_audit.py -- the live surface for OSR (Observed System Reconstruction).

Every OSR mechanism is reachable from here, and this file is named by
`commands/cpp-osr.md`, which is a seed surface for `modules/liveness/
reachability.py`. That chain is the point: CLASE 0 -- "module built but not
auto-activated" -- is this estate's single most-recurring error, and a
reconstruction runtime that shipped unreachable would be an expensive instance
of the failure it exists to detect.

Usage
  python tools/osr_audit.py --types
  python tools/osr_audit.py --model vault/osr/models/<target>.json
  python tools/osr_audit.py --compare-raster REF.png BUILD.png
  python tools/osr_audit.py --compare-geometry REF.json BUILD.json
  python tools/osr_audit.py --compare-timeline REF.json BUILD.json
  python tools/osr_audit.py --align REF.jsonl BUILD.jsonl --mission NAME
  python tools/osr_audit.py --verify-order REQUIRED.json OBSERVED.json [--terminal S]

Add --json for machine-readable output on any subcommand.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.osr import (  # noqa: E402
    ObservedSystemModel,
    align,
    compare_geometry,
    compare_rasters,
    compare_timelines,
    craif_record,
    gate,
    verify_ordering,
)
from modules.osr.compare import DIFF, UNMEASURED  # noqa: E402


def _read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _read_jsonl(path: str) -> list[dict]:
    out = []
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _emit(payload: dict, as_json: bool, headline: str) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(headline)
        print(json.dumps(payload, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="OSR -- Observed System Reconstruction")
    ap.add_argument("--types", action="store_true", help="print the graphify type vocabulary")
    ap.add_argument("--model", metavar="PATH", help="load a model and report coverage and gaps")
    ap.add_argument("--compare-raster", nargs=2, metavar=("REF", "BUILD"))
    ap.add_argument("--compare-geometry", nargs=2, metavar=("REF", "BUILD"))
    ap.add_argument("--compare-timeline", nargs=2, metavar=("REF", "BUILD"))
    ap.add_argument("--align", nargs=2, metavar=("REF", "BUILD"))
    ap.add_argument("--verify-order", nargs=2, metavar=("REQUIRED", "OBSERVED"))
    ap.add_argument("--terminal", help="terminal state name for --verify-order")
    ap.add_argument("--mission", default="unnamed", help="mission label for --align")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    if args.types:
        types = ObservedSystemModel("probe").graphify_types()
        _emit(types, args.as_json, "OSR type vocabulary for the graphify indexer:")
        return 0

    if args.model:
        model = ObservedSystemModel.load(args.model)
        payload = {
            "target": model.target,
            "version": model.version,
            "node_count": len(model.nodes),
            "edge_count": len(model.edges),
            "coverage": model.coverage(),
            "structural_gaps": model.structural_gaps(),
            "unresolved": [n["id"] for n in model.unresolved()],
        }
        _emit(payload, args.as_json, f"OSR-1 model report for {model.target}:")
        return 1 if payload["structural_gaps"] else 0

    if args.compare_raster:
        result = compare_rasters(*args.compare_raster)
        _emit(result, args.as_json, "OSR-2 raster instrument:")
        return _verdict_exit(result["verdict"])

    if args.compare_geometry:
        ref, build = (_read_json(p) for p in args.compare_geometry)
        result = compare_geometry(ref, build)
        _emit(result, args.as_json, "OSR-2 geometry instrument:")
        return _verdict_exit(result["verdict"])

    if args.compare_timeline:
        ref, build = (_read_json(p) for p in args.compare_timeline)
        result = compare_timelines(ref, build)
        _emit(result, args.as_json, "OSR-2 temporal instrument:")
        return _verdict_exit(result["verdict"])

    if args.align:
        ref, build = (_read_jsonl(p) for p in args.align)
        alignment = align(ref, build)
        payload = {"alignment": alignment, "craif_input": craif_record(alignment, args.mission)}
        _emit(payload, args.as_json, "OSR-3 alignment:")
        return 1 if alignment["verdict"] == "DIVERGED" else 0

    if args.verify_order:
        required, observed = (_read_json(p) for p in args.verify_order)
        result = verify_ordering(required, observed, terminal=args.terminal)
        _emit(result, args.as_json, "OSR-L1 ordering gate:")
        return 0 if gate(result) else 1

    ap.print_help()
    return 0


def _verdict_exit(verdict: str) -> int:
    """DIFF and UNMEASURED both exit non-zero.

    An unmeasured dimension is a failed dimension. A gate that exits 0 because
    nothing could be measured is the quiet pass this estate has sealed as a
    defect four separate times.
    """
    return 1 if verdict in (DIFF, UNMEASURED) else 0


if __name__ == "__main__":
    raise SystemExit(main())
