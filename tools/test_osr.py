#!/usr/bin/env python3
"""test_osr.py -- done-gate for OSR (Observed System Reconstruction).

V-OSR-* gates, hermetic: no network, no subprocess, no writes outside a
tempdir, byte-identical across repeated runs. Every gate exercises a real code
path -- the PNG fixtures below are encoded here and decoded by the module under
test, so the raster instrument is proven end to end rather than described.

Run: python tools/test_osr.py [--json]
"""
from __future__ import annotations

import json
import struct
import sys
import tempfile
import zlib
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.osr import (  # noqa: E402
    DIFF,
    MATCH,
    UNMEASURED,
    ModelError,
    ObservedSystemModel,
    align,
    compare_geometry,
    compare_rasters,
    compare_timelines,
    craif_record,
    gate,
    instrument_report,
    verify_ordering,
)

_PASSES: list[str] = []
_FAILS: list[str] = []


def _ok(name: str, evidence: str) -> None:
    _PASSES.append(name)
    print(f"  PASS {name} -- {evidence}")


def _fail(name: str, diagnostic: str) -> None:
    _FAILS.append(name)
    print(f"  FAIL {name} -- {diagnostic}")


# ------------------------------------------------------------- PNG fixtures

def _write_png(path: Path, width: int, height: int, pixels: list[tuple[int, int, int]]) -> None:
    """Minimal 8-bit truecolour PNG encoder -- test fixture generation only."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0
        for x in range(width):
            raw.extend(pixels[y * width + x])

    def chunk(tag: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body))
            + tag
            + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw)))
        + chunk(b"IEND", b"")
    )


# ------------------------------------------------------------ OSR-1 (model)

def gate_model_ontology() -> None:
    m = ObservedSystemModel("reference-app", version="2026.07")
    m.add_node("app", "product", status="observed", evidence=["ev-1"])
    m.add_node("compose", "surface", status="observed", evidence=["ev-2"])
    m.add_edge("app", "contains", "compose")
    if len(m.nodes) == 2 and len(m.edges) == 1:
        _ok("V-OSR-MODEL-BUILD", "2 nodes + 1 edge accepted with evidence refs")
    else:
        _fail("V-OSR-MODEL-BUILD", f"got {len(m.nodes)} nodes / {len(m.edges)} edges")

    try:
        m.add_node("bogus", "not_a_kind")
        _fail("V-OSR-MODEL-KIND", "an unknown node kind was accepted")
    except ModelError:
        _ok("V-OSR-MODEL-KIND", "unknown node kind rejected")

    try:
        m.add_edge("app", "contains", "ghost")
        _fail("V-OSR-MODEL-EDGE", "an edge to a missing node was accepted")
    except ModelError:
        _ok("V-OSR-MODEL-EDGE", "edge to a non-existent node rejected")


def gate_model_no_autopromotion() -> None:
    m = ObservedSystemModel("reference-app")
    m.add_node("sidebar_persists", "hypothesis", status="hypothesized")
    try:
        m.promote("sidebar_persists", "observed")
        _fail("V-OSR-NO-AUTOPROMOTION", "status rose with no new evidence")
    except ModelError:
        _ok("V-OSR-NO-AUTOPROMOTION", "hypothesized -> observed refused without evidence")

    m.promote("sidebar_persists", "observed", evidence=["ev-9"])
    if m.node("sidebar_persists")["status"] == "observed":
        _ok("V-OSR-PROMOTION-WITH-EVIDENCE", "status rose once an evidence ref was supplied")
    else:
        _fail("V-OSR-PROMOTION-WITH-EVIDENCE", "promotion with evidence did not take effect")

    try:
        ObservedSystemModel("x").add_node("n", "state", status="measured")
        _fail("V-OSR-EVIDENCE-REQUIRED", "a reality claim was accepted with no evidence")
    except ModelError:
        _ok("V-OSR-EVIDENCE-REQUIRED", "status 'measured' rejected without an evidence ref")


def gate_model_structural_gaps() -> None:
    m = ObservedSystemModel("reference-app")
    m.add_node("loading", "state", status="observed", evidence=["ev-1"])
    m.add_node("ready", "state", status="observed", evidence=["ev-2"])
    m.add_node("upload_fails", "failure_mode", status="observed", evidence=["ev-3"])
    m.add_edge("loading", "transitions_to", "ready")
    gaps = {g["gap"] for g in m.structural_gaps()}
    expected = {"state_with_entry_and_no_exit", "failure_mode_with_no_recovery_path"}
    if expected <= gaps:
        _ok("V-OSR-STRUCTURAL-GAPS", f"detected {sorted(expected)}")
    else:
        _fail("V-OSR-STRUCTURAL-GAPS", f"expected {sorted(expected)}, got {sorted(gaps)}")

    coverage = m.coverage()
    if coverage.get("state", {}).get("observed") == 2:
        _ok("V-OSR-COVERAGE-ABSOLUTE", "coverage reports counts per cell, not a ratio")
    else:
        _fail("V-OSR-COVERAGE-ABSOLUTE", f"unexpected coverage table {coverage}")


def gate_model_roundtrip(tmp: Path) -> None:
    m = ObservedSystemModel("reference-app", version="2026.07")
    m.add_node("app", "product", status="verified", evidence=["ev-1", "ev-2"])
    m.add_node("send", "action", status="observed", evidence=["ev-3"])
    m.add_edge("app", "contains", "send")
    path = m.save(tmp / "model.json")
    back = ObservedSystemModel.load(path)
    if back.to_dict() == m.to_dict():
        _ok("V-OSR-MODEL-ROUNDTRIP", "save/load is byte-equivalent and revalidates")
    else:
        _fail("V-OSR-MODEL-ROUNDTRIP", "reloaded model differs from the original")

    types = m.graphify_types()
    if all(t.startswith("osr.") for t in types["node_types"] + types["edge_types"]):
        _ok("V-OSR-GRAPHIFY-NAMESPACE", f"{len(types['node_types'])} node types, all osr-prefixed")
    else:
        _fail("V-OSR-GRAPHIFY-NAMESPACE", "a type escaped the osr. namespace")


# ---------------------------------------------------------- OSR-2 (compare)

def gate_raster_instrument(tmp: Path) -> None:
    black = [(0, 0, 0)] * 64
    ref = tmp / "ref.png"
    same = tmp / "same.png"
    moved = tmp / "moved.png"
    small = tmp / "small.png"
    _write_png(ref, 8, 8, black)
    _write_png(same, 8, 8, black)
    changed = list(black)
    changed[27] = (255, 0, 0)
    _write_png(moved, 8, 8, changed)
    _write_png(small, 4, 4, [(0, 0, 0)] * 16)

    identical = compare_rasters(ref, same)
    if identical["verdict"] == MATCH and identical["observations"]["differing_pixels"] == 0:
        _ok("V-OSR-RASTER-MATCH", "identical PNGs decoded and matched, 0 differing pixels")
    else:
        _fail("V-OSR-RASTER-MATCH", f"got {identical}")

    differs = compare_rasters(ref, moved)
    obs = differs.get("observations", {})
    if differs["verdict"] == DIFF and obs.get("differing_pixels") == 1 and obs.get("region_count") == 1:
        _ok("V-OSR-RASTER-DIFF", "one changed pixel located in exactly one region")
    else:
        _fail("V-OSR-RASTER-DIFF", f"got {differs}")

    dims = compare_rasters(ref, small)
    if dims["verdict"] == DIFF and "dimension_mismatch" in dims["observations"]:
        _ok("V-OSR-RASTER-DIMENSIONS", "size mismatch reported without a pixel scan")
    else:
        _fail("V-OSR-RASTER-DIMENSIONS", f"got {dims}")

    absent = compare_rasters(tmp / "does-not-exist.png", ref)
    if absent["verdict"] == UNMEASURED:
        _ok("V-OSR-RASTER-UNMEASURED", "missing artifact yields UNMEASURED, never a quiet pass")
    else:
        _fail("V-OSR-RASTER-UNMEASURED", f"got {absent['verdict']}")


def gate_geometry_and_temporal() -> None:
    ref_boxes = [
        {"id": "composer", "x": 0, "y": 100, "w": 200, "h": 40},
        {"id": "send", "x": 210, "y": 100, "w": 40, "h": 40},
    ]
    build_boxes = [
        {"id": "composer", "x": 0, "y": 100, "w": 200, "h": 40},
        {"id": "send", "x": 260, "y": 100, "w": 40, "h": 40},
    ]
    geo = compare_geometry(ref_boxes, build_boxes)
    moved_ids = [m["id"] for m in geo["observations"]["moved"]]
    if geo["verdict"] == DIFF and moved_ids == ["send"]:
        _ok("V-OSR-GEOMETRY-MOVED", "a 50px displacement on one element detected")
    else:
        _fail("V-OSR-GEOMETRY-MOVED", f"got {geo}")

    missing = compare_geometry(ref_boxes, build_boxes[:1])
    if missing["observations"]["missing_in_build"] == ["send"]:
        _ok("V-OSR-GEOMETRY-MISSING", "an element absent from the build named explicitly")
    else:
        _fail("V-OSR-GEOMETRY-MISSING", f"got {missing['observations']}")

    ref_tl = [
        {"name": "skeleton", "start_ms": 0, "end_ms": 120},
        {"name": "stream", "start_ms": 120, "end_ms": 900},
    ]
    build_tl = [
        {"name": "stream", "start_ms": 0, "end_ms": 780},
        {"name": "skeleton", "start_ms": 780, "end_ms": 900},
    ]
    temporal = compare_timelines(ref_tl, build_tl)
    if temporal["verdict"] == DIFF and temporal["observations"]["order_changed"]:
        _ok("V-OSR-TEMPORAL-ORDER", "reordered phases detected even though both phases exist")
    else:
        _fail("V-OSR-TEMPORAL-ORDER", f"got {temporal}")

    report = instrument_report([
        {"instrument": "geometry", "verdict": MATCH},
        {"instrument": "temporal", "verdict": UNMEASURED},
    ])
    if report["verdict"] == UNMEASURED:
        _ok("V-OSR-CONJUNCTION", "MATCH + UNMEASURED aggregates to UNMEASURED, never averaged")
    else:
        _fail("V-OSR-CONJUNCTION", f"aggregate was {report['verdict']}")


# ------------------------------------------------------------ OSR-3 (align)

def gate_alignment() -> None:
    reference = [
        {"event_id": "r1", "kind": "boot.manifest_loaded", "layer": "internal", "payload": {"n": 12}},
        {"event_id": "r2", "kind": "boot.tool_registry", "layer": "internal", "payload": {"n": 7}},
        {"event_id": "r3", "kind": "ui.render", "layer": "observable", "payload": {"view": "hub"}},
        {"event_id": "r4", "kind": "ui.click", "layer": "observable", "payload": {"target": "send"}},
    ]
    build = [
        {"event_id": "b1", "kind": "boot.manifest_loaded", "layer": "internal", "payload": {"n": 12}},
        {"event_id": "b2", "kind": "boot.tool_registry", "layer": "internal", "payload": {"n": 3}},
        {"event_id": "b3", "kind": "ui.render", "layer": "observable", "payload": {"view": "hub"}},
        {"event_id": "b4", "kind": "ui.click", "layer": "observable", "payload": {"target": "none"}},
    ]
    result = align(reference, build)
    t1 = result["t1_internal"]
    t2 = result["t2_observable"]
    if result["verdict"] == "DIVERGED" and t1 and t1["reference_index"] == 1:
        _ok("V-OSR-ALIGN-T1", "earliest INTERNAL divergence located at index 1")
    else:
        _fail("V-OSR-ALIGN-T1", f"t1={t1}")

    if t2 and t2["reference_index"] == 3 and result["causal_distance"] == 2:
        _ok("V-OSR-CAUSAL-DISTANCE", "symptom at 3, cause at 1, distance 2 -- the whole point")
    else:
        _fail("V-OSR-CAUSAL-DISTANCE", f"t2={t2} distance={result['causal_distance']}")

    volatile = align(
        [{"event_id": "r1", "kind": "k", "layer": "internal", "payload": {"ts": 1, "v": "a"}}],
        [{"event_id": "b1", "kind": "k", "layer": "internal", "payload": {"ts": 999, "v": "a"}}],
    )
    if volatile["verdict"] == "ALIGNED":
        _ok("V-OSR-ALIGN-VOLATILE", "a differing timestamp is not treated as a divergence")
    else:
        _fail("V-OSR-ALIGN-VOLATILE", f"got {volatile['verdict']}")

    missing = align(reference, [reference[0], reference[2], reference[3]])
    kinds = {d["divergence"] for d in missing["divergences"]}
    if "MISSING_IN_BUILD" in kinds:
        _ok("V-OSR-ALIGN-MISSING", "an event absent from the build classified as MISSING_IN_BUILD")
    else:
        _fail("V-OSR-ALIGN-MISSING", f"classifications were {sorted(kinds)}")

    record = craif_record(result, mission="regression-hunt")
    if record["consumer"] == "craif" and record["investigate_from"] == 1:
        _ok("V-OSR-CRAIF-HANDOFF", "handoff names craif and points at the cause, not the symptom")
    else:
        _fail("V-OSR-CRAIF-HANDOFF", f"got {record}")

    empty = align([], [])
    if empty["verdict"] == "UNMEASURED":
        _ok("V-OSR-ALIGN-UNMEASURED", "empty traces report UNMEASURED")
    else:
        _fail("V-OSR-ALIGN-UNMEASURED", f"got {empty['verdict']}")


# -------------------------------------------------------- OSR-L1 (ordering)

def gate_ordering_law() -> None:
    required = ["mount_resources", "init_managers", "load_save_data"]

    good = verify_ordering(required, required + ["hub"], terminal="hub")
    if gate(good):
        _ok("V-OSR-L1-SATISFIED", "prerequisites in order before the terminal state")
    else:
        _fail("V-OSR-L1-SATISFIED", f"got {good}")

    skipped = verify_ordering(required, ["mount_resources", "init_managers", "hub"], terminal="hub")
    if skipped["verdict"] == "MISSING_PREREQUISITE" and not gate(skipped):
        _ok("V-OSR-L1-MISSING", "a skipped prerequisite fails even though the hub was reached")
    else:
        _fail("V-OSR-L1-MISSING", f"got {skipped}")

    late = verify_ordering(required, ["mount_resources", "init_managers", "hub", "load_save_data"],
                           terminal="hub")
    if late["verdict"] == "AFTER_TERMINAL" and late["after_terminal"] == ["load_save_data"]:
        _ok("V-OSR-L1-AFTER-TERMINAL", "arrival before a prerequisite is named, not excused")
    else:
        _fail("V-OSR-L1-AFTER-TERMINAL", f"got {late}")

    swapped = verify_ordering(required, ["init_managers", "mount_resources", "load_save_data", "hub"],
                              terminal="hub")
    if swapped["verdict"] == "OUT_OF_ORDER":
        _ok("V-OSR-L1-ORDER", "an inverted pair detected although every step occurred")
    else:
        _fail("V-OSR-L1-ORDER", f"got {swapped}")

    unmeasured = verify_ordering([], ["hub"], terminal="hub")
    if unmeasured["verdict"] == "UNMEASURED" and not gate(unmeasured):
        _ok("V-OSR-L1-UNMEASURED", "no declared sequence is UNMEASURED and fails the gate")
    else:
        _fail("V-OSR-L1-UNMEASURED", f"got {unmeasured}")

    derived = verify_ordering(required, ["hub"], terminal="hub")
    if derived["verdict"] == "MISSING_PREREQUISITE":
        _ok("V-OSR-L1-ARRIVAL-IS-NOT-PROOF", "reaching the terminal state alone does not pass")
    else:
        _fail("V-OSR-L1-ARRIVAL-IS-NOT-PROOF", f"got {derived}")


# ------------------------------------------------------------------- driver

def main() -> int:
    as_json = "--json" in sys.argv
    with tempfile.TemporaryDirectory(prefix="osr_gate_") as td:
        tmp = Path(td)
        print("OSR done-gate")
        print("-- OSR-1 model")
        gate_model_ontology()
        gate_model_no_autopromotion()
        gate_model_structural_gaps()
        gate_model_roundtrip(tmp)
        print("-- OSR-2 comparison instruments")
        gate_raster_instrument(tmp)
        gate_geometry_and_temporal()
        print("-- OSR-3 alignment")
        gate_alignment()
        print("-- OSR-L1 ordering law")
        gate_ordering_law()

    total = len(_PASSES) + len(_FAILS)
    if as_json:
        print(json.dumps({"passed": _PASSES, "failed": _FAILS, "total": total}, indent=2))
    print(f"OSR_PASS={len(_PASSES)}/{total}  threshold={total}/{total}")
    return 0 if not _FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
