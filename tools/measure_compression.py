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


def _rtk_probe(tok) -> dict:
    """Honest RTK half of the unified ledger.

    RTK compresses command OUTPUT, not the command string (`rtk rewrite
    <cmd>` returns `rtk <cmd>` — a wrapper). The real saving is therefore
    tok(raw stdout) - tok(rtk-wrapped stdout) on a fixed, safe, read-only
    sample (`git log --stat -50` — the canonical CLAUDE.md benchmark;
    deterministic for a fixed HEAD => reproducible within a run).
    Binary absent / any error -> saved=0 with the true reason. Never
    fabricates a number.
    """
    import os
    import subprocess
    rtk = os.environ.get("RTK_BIN") or str(
        Path(os.path.expanduser("~")) / ".claude" / "bin" / "rtk.exe")
    if not Path(rtk).is_file():
        return {"saved": 0, "present": False, "status": "binary-absent "
                "(hook fail-open: output passes through uncompressed)"}
    cmd = ["git", "log", "--stat", "-50"]
    try:
        raw = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=15, cwd=str(PP_ROOT))
        wrapped = subprocess.run([rtk] + cmd, capture_output=True,
                                 text=True, timeout=15, cwd=str(PP_ROOT))
        raw_t = tok(raw.stdout or "")
        rtk_t = tok(wrapped.stdout or "")
        if raw_t <= 0 or not (wrapped.stdout or "").strip():
            return {"saved": 0, "present": True, "status":
                    "binary-present but sample produced no comparable "
                    "output (saved=0, not fabricated)"}
        saved = max(0, raw_t - rtk_t)
        pct = (saved / raw_t) if raw_t else 0.0
        return {"saved": saved, "present": True, "status":
                f"binary-present | `git log --stat -50` OUTPUT "
                f"raw={raw_t}t -> rtk={rtk_t}t ({pct:.1%} compressed)"}
    except Exception as exc:
        return {"saved": 0, "present": False, "status":
                f"probe-error {type(exc).__name__} "
                "(fail-open: zero real compression counted)"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=float, default=MIN_REDUCTION)
    ap.add_argument("--coordinated", action="store_true",
                    help="also print the unified RTK+JIT token ledger")
    a = ap.parse_args()
    jsl = _load()
    tok = jsl._tok
    jit_saved = 0
    jit_full = 0

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
        jit_saved += (tf - ts)
        jit_full += tf

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

    if a.coordinated:
        rtk = _rtk_probe(tok)
        total = jit_saved + rtk["saved"]
        print("--- UNIFIED RTK+JIT TOKEN LEDGER (one system, measured) ---")
        print(f"  JIT input-side : -{jit_saved}t saved across {len(targets)}"
              f" modules (of {jit_full}t full)")
        print(f"  RTK output-side: -{rtk['saved']}t  [{rtk['status']}]")
        print(f"  COORDINATED_TOTAL_SAVED={total}t  "
              f"rtk_active={rtk['present']}")

    if failures:
        print("COMPRESSION_GATE FAIL:", " | ".join(failures))
        return 2
    print("COMPRESSION_GATE OK — all targets compressed & structurally "
          "intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
