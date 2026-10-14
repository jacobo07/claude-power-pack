#!/usr/bin/env python3
"""Compare the canonical environment of two planes (05-2-03, N17/N19).

  --vector                      hash of a fixed body (platform independent: both legs must print the same)
  --live [--deps pkg:x ...]     JSON of THIS plane: plane id, canonical body, environment hash
  --compare a.json b.json       EQUIVALENT | DRIFT <fields>   (exit 0 / 1)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.gsd_x.goal import proof as pf      # noqa: E402
from modules.gsd_x.goal import trust            # noqa: E402

VECTOR_BODY = {"v": 2, "runtime": {"impl": "CPython", "version": "3.12.0"},
               "platform": {"system": "Plane", "machine": "m0"}, "deps": {"pkg:a": "1"}}


def vector() -> str:
    return "env2:" + hashlib.sha256(pf._canonical(VECTOR_BODY)).hexdigest()


def live(deps) -> dict:
    return {"plane": trust.plane_id(), "body": trust.canonical_env_body(deps),
            "environment": trust.environment_canonical(deps)}


def compare(a: dict, b: dict) -> list:
    """Fields that differ between two `--live` outputs; the plane id itself is expected to differ."""
    drift = []
    for part in ("runtime", "platform"):
        if a["body"].get(part) != b["body"].get(part):
            drift.append(part)
    for dep in sorted(set(a["body"]["deps"]) | set(b["body"]["deps"])):
        if a["body"]["deps"].get(dep) != b["body"]["deps"].get(dep):
            drift.append(dep)
    return drift


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vector", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--deps", nargs="*", default=[])
    ap.add_argument("--compare", nargs=2, metavar=("A", "B"))
    ns = ap.parse_args(argv)
    if ns.vector:
        print(vector())
        return 0
    if ns.live:
        print(json.dumps(live(ns.deps), sort_keys=True))
        return 0
    if ns.compare:
        a, b = (json.loads(Path(p).read_text(encoding="utf-8-sig")) for p in ns.compare)
        drift = compare(a, b)
        print("DRIFT " + ", ".join(drift) if drift else "EQUIVALENT")
        return 1 if drift else 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
