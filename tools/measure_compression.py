#!/usr/bin/env python3
"""measure_compression.py — Apollo-retrofit compression gate.

"Compression is measured, not declared." Computes the REAL cl100k token
delta between the full SKILL.md and the summary-tier extraction for the
highest-priority trigger modules, and asserts a structural invariant:
the summary MUST still contain, verbatim, every high-signal anchor of
that module's TASK_PROFILE (Apollo SKILL.md guides have no executable
done-gate — the structural-anchor check is the honest substitute).

PASS gate (exit 0): every measured module reaches >= MIN_REDUCTION token
reduction AND retains all its include[] anchors verbatim. Any miss ->
exit 2 with the offending module(s) named. Numbers are computed live;
nothing is hardcoded.

Usage: python tools/measure_compression.py [--min 0.30]
"""
from __future__ import annotations
import argparse
import importlib.util
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = PP_ROOT / "vendor" / "apollo" / "upstream"
LOADER = PP_ROOT / "tools" / "jit_skill_loader.py"

# S+ (2026-05-18): measure EVERY trigger-matrix module, derived live from
# the loader's TRIGGERS (never hardcoded — auto-tracks the matrix). The
# constant below is only a fail-safe if TRIGGERS cannot be imported.
TARGETS_FALLBACK = ["apollo-client", "graphql-operations", "graphql-schema"]
MIN_REDUCTION = 0.30


def _load():
    spec = importlib.util.spec_from_file_location("jsl", LOADER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=float, default=MIN_REDUCTION)
    a = ap.parse_args()
    jsl = _load()
    tok = jsl._tok

    targets = sorted({m for t in getattr(jsl, "TRIGGERS", [])
                      for m in t[2]}) or TARGETS_FALLBACK

    print(f"=== Apollo-retrofit compression gate (min reduction "
          f">= {a.min:.0%}, tokenizer=cl100k, {len(targets)} modules) ===")
    failures: list[str] = []
    for mod in targets:
        skill = UPSTREAM / mod / "SKILL.md"
        if not skill.is_file():
            print(f"  [MISS] {mod}: SKILL.md absent")
            failures.append(f"{mod}:absent")
            continue
        body = skill.read_text(encoding="utf-8")
        full = jsl._render(mod, body, "full")
        summ = jsl._render(mod, body, "summary")
        tf, ts = tok(full), tok(summ)
        red = 1.0 - (ts / tf) if tf else 0.0

        prof = jsl.TASK_PROFILES.get(mod, {})
        anchors = prof.get("include") or []
        missing = [h for h in anchors if h not in summ]

        ok_red = red >= a.min
        ok_struct = not missing
        tag = "OK" if (ok_red and ok_struct) else "FAIL"
        print(f"  [{tag}] {mod}: full={tf}t summary={ts}t "
              f"reduction={red:.1%} | anchors {len(anchors)-len(missing)}"
              f"/{len(anchors)} verbatim")
        if not ok_red:
            failures.append(f"{mod}:reduction {red:.1%}<{a.min:.0%}")
        if not ok_struct:
            failures.append(f"{mod}:anchors-missing {missing}")

    if failures:
        print("COMPRESSION_GATE FAIL:", " | ".join(failures))
        return 2
    print("COMPRESSION_GATE OK — all targets compressed & structurally "
          "intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
