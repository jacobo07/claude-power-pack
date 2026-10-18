#!/usr/bin/env python3
"""V-gates for the node-manifest consumer (UWCP S4-22 consume half).

Positive control is a manifest the Orca producer really emitted (docs/dws/phase-5-node-manifest.json
in the Orca repo); every refusal is asserted by its reason code, not by the absence of a view.

    python tools/test_gsd_x_goal_node.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import node as nd  # noqa: E402

REAL = ROOT / "tools" / "fixtures" / "orca_node_manifest_real.json"
DAY = 86_400_000
passes: list[str] = []
fails: list[str] = []


def check(gate: str, ok: bool, good: str, bad: str = "") -> None:
    (passes if ok else fails).append(gate)
    print(f"{'PASS' if ok else 'FAIL'} {gate}: {good if ok else bad}")


def refuses(doc, now, bound, code):
    try:
        nd.read_node_manifest(doc, now, bound)
    except nd.NodeManifestError as exc:
        return exc.code == code, exc.code
    return False, "accepted"


def main() -> int:
    if not REAL.exists():
        print("NOT_RUN V-NODE-REAL-MANIFEST: producer manifest missing")
        return 1
    real = json.loads(REAL.read_text(encoding="utf-8"))
    obs = real["observed_at"]
    view = nd.read_node_manifest(real, obs + 1000, 5 * 60_000)
    check("V-NODE-REAL-MANIFEST", view.address == real["node"]["address"] and bool(view.measured or view.unknown),
          f"{view.address} measured={sorted(view.measured)} unknown={sorted(view.unknown)}")
    check("V-NODE-FROM-TEXT-AND-PATH",
          nd.read_node_manifest(REAL.read_text(encoding="utf-8"), obs, 60_000).address == view.address
          and nd.read_node_manifest(str(REAL), obs, 60_000).address == view.address, "JSON text and path read the same view")

    ok, got = refuses(real, obs + 10 * 60_000, 5 * 60_000, "stale_manifest")
    check("V-NODE-STALE-MANIFEST", ok, "older than the bound is refused", got)
    ok, got = refuses(real, obs - 10 * 60_000, 5 * 60_000, "from_future")
    check("V-NODE-FROM-FUTURE", ok, "observed_at ahead of now beyond skew is refused", got)

    first = next((n for n in nd.MEASUREMENTS if real["measurements"][n]["status"] == "measured"), None)
    check("V-NODE-HAS-MEASURED", first is not None, f"fixture has a measured entry ({first})", "no measured entry to age")
    if first:
        m = real["measurements"][first]
        late = m["measured_at"] + m["max_age_ms"] + 1
        wide = copy.deepcopy(real)
        wide["observed_at"] = late
        ok, got = refuses(wide, late, DAY, "stale_measurement")
        check("V-NODE-STALE-MEASUREMENT", ok, "a measurement past its own max_age_ms is refused though the manifest is fresh", got)
        edge = copy.deepcopy(real)
        edge["observed_at"] = m["measured_at"] + m["max_age_ms"]
        try:
            nd.read_node_manifest(edge, m["measured_at"] + m["max_age_ms"], DAY)
            edge_ok = True
        except nd.NodeManifestError as exc:
            edge_ok = exc.code != "stale_measurement"
        check("V-NODE-MEASUREMENT-BOUNDARY", edge_ok, "exactly max_age_ms is fresh", "boundary refused")

    for gate, mutate in {
        "V-NODE-BAD-SCHEMA": lambda d: d.__setitem__("schema", "orca.node-manifest/2"),
        "V-NODE-EXTRA-FIELD": lambda d: d.__setitem__("surprise", 1),
        "V-NODE-NO-ADDRESS": lambda d: d["node"].__setitem__("address", ""),
        "V-NODE-MISSING-MEASUREMENT": lambda d: d["measurements"].pop("vram"),
        "V-NODE-BOOL-TIME": lambda d: d.__setitem__("observed_at", True),
    }.items():
        bad = copy.deepcopy(real)
        mutate(bad)
        ok, got = refuses(bad, obs, 60_000, "malformed")
        check(gate, ok, "refused as malformed", got)
    ok, got = refuses("{not json", obs, 60_000, "malformed")
    check("V-NODE-NOT-JSON", ok, "non-JSON refused", got)
    ok, got = refuses(str(REAL) + ".absent", obs, 60_000, "unreadable")
    check("V-NODE-UNREADABLE", ok, "absent path refused", got)

    unk = copy.deepcopy(real)
    unk["measurements"]["vram"] = {"status": "unknown", "reason": "no gpu probe"}
    uv = nd.read_node_manifest(unk, obs, 60_000)
    check("V-NODE-UNKNOWN-STAYS-UNKNOWN", "vram" in uv.unknown and "vram" not in uv.measured,
          "an unknown measurement is carried as unknown with its reason, not a number")

    # known_heads (S4-22 AC-4): Orca never emits it today, so the present case is the real manifest plus the field.
    def heads_of(v):
        return getattr(v, "known_heads", "FIELD-MISSING")   # a view without the field fails a gate, not the run

    check("V-NODE-KNOWN-HEADS-ABSENT-IS-UNKNOWN", "known_heads" not in real and heads_of(view) is None,
          "absent known_heads reads as None (unknown), not as an empty set", repr(heads_of(view)))
    with_heads = copy.deepcopy(real)
    with_heads["known_heads"] = ["1c44413db14ca811", "3266e1a41790ab35"]
    hv = nd.read_node_manifest(with_heads, obs, 60_000)
    check("V-NODE-KNOWN-HEADS-PRESENT", heads_of(hv) == ("1c44413db14ca811", "3266e1a41790ab35"),
          "present known_heads are exposed in order", repr(heads_of(hv)))
    dup = copy.deepcopy(real)
    dup["known_heads"] = ["abc", "abc"]
    try:
        dup_ok = heads_of(nd.read_node_manifest(dup, obs, 60_000)) == ("abc", "abc")
    except nd.NodeManifestError as exc:
        dup_ok = False
        print(f"  duplicate heads refused: {exc.code}")
    check("V-NODE-KNOWN-HEADS-DUPLICATES-ACCEPTED", dup_ok, "duplicates pass, as the producer schema allows")
    for gate, heads in {
        "V-NODE-KNOWN-HEADS-EMPTY": [],
        "V-NODE-KNOWN-HEADS-NULL": None,
        "V-NODE-KNOWN-HEADS-NOT-LIST": "abc123",
        "V-NODE-KNOWN-HEADS-EMPTY-ENTRY": ["abc123", ""],
        "V-NODE-KNOWN-HEADS-NON-STRING": ["abc123", 7],
    }.items():
        bad = copy.deepcopy(with_heads)
        bad["known_heads"] = heads
        ok, got = refuses(bad, obs, 60_000, "malformed")
        check(gate, ok, f"known_heads={heads!r} refused as malformed", got)

    print(f"\nGSDX_NODE_PASS={len(passes)}/{len(passes) + len(fails)}  threshold={len(passes) + len(fails)}/{len(passes) + len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
