#!/usr/bin/env python3
"""measure_session_start.py -- empirical timing of ~/.claude/settings.json
SessionStart hooks.

Reports per-hook + total wall time. Used as the verify-and-iterate gate for
BL-LAG-001. Targets:
  - total wall (max of individual)         < 1000 ms
  - no individual hook > 300 ms (when sync)
  - PP-owned hooks must self-detach        < 100 ms

Owner can run any time:
    python tools/measure_session_start.py
    python tools/measure_session_start.py --json > timing.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
SLOW_INDIVIDUAL_MS = 300
TOTAL_TARGET_MS = 1000
PER_HOOK_TIMEOUT_S = 8


def _enumerate_hooks() -> list[str]:
    raw = SETTINGS_PATH.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    ss = data.get("hooks", {}).get("SessionStart", [])
    out: list[str] = []
    for entry in ss:
        for hh in entry.get("hooks", []):
            cmd = hh.get("command", "")
            if not cmd:
                continue
            # The "test -f <file> || exit" guards do not run a hook by
            # themselves; skip from the timing roll-up.
            if cmd.strip().startswith("test -f "):
                continue
            out.append(cmd)
    return out


def _time_one(cmd: str) -> tuple[float, int]:
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, shell=True,
            input="{}", capture_output=True, text=True,
            timeout=PER_HOOK_TIMEOUT_S,
        )
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        rc = -1
    return ((time.perf_counter() - t0) * 1000, rc)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--json", action="store_true",
                    help="Emit JSON payload on stdout instead of table.")
    args = ap.parse_args(argv)

    hooks = _enumerate_hooks()
    results = []
    for cmd in hooks:
        ms, rc = _time_one(cmd)
        results.append({"cmd": cmd, "ms": ms, "rc": rc})

    individual_max = max((r["ms"] for r in results), default=0.0)
    total_serial = sum(r["ms"] for r in results)
    slow = [r for r in results if r["ms"] > SLOW_INDIVIDUAL_MS]

    payload = {
        "settings_path": str(SETTINGS_PATH),
        "hook_count": len(results),
        "individual_max_ms": individual_max,
        "total_serial_ms": total_serial,
        "slow_individual_threshold_ms": SLOW_INDIVIDUAL_MS,
        "total_target_ms": TOTAL_TARGET_MS,
        "slow_hooks": [r["cmd"][:120] for r in slow],
        "results": results,
        "verdict": (
            "OK" if individual_max < TOTAL_TARGET_MS and not slow
            else ("WARN" if individual_max < TOTAL_TARGET_MS
                  else "FAIL")
        ),
    }

    if args.json:
        sys.stdout.write(json.dumps(payload, indent=2))
        return 0 if payload["verdict"] == "OK" else 1

    print("=" * 72)
    print("SessionStart timing measurement")
    print("=" * 72)
    print(f"Hooks    : {len(results)}")
    print(f"Settings : {SETTINGS_PATH}")
    print()
    for r in results:
        tag = ("SLOW" if r["ms"] > SLOW_INDIVIDUAL_MS
               else "warn" if r["ms"] > SLOW_INDIVIDUAL_MS / 2
               else "ok  ")
        print(f"  [{tag}] {r['ms']:7.1f} ms rc={r['rc']:<3}  {r['cmd'][:80]}")
    print()
    print(f"Individual max : {individual_max:.1f} ms "
          f"(target < {TOTAL_TARGET_MS})")
    print(f"Serial total   : {total_serial:.1f} ms")
    print(f"Slow hooks     : {len(slow)} (> {SLOW_INDIVIDUAL_MS} ms)")
    print(f"VERDICT        : {payload['verdict']}")
    print("=" * 72)
    return 0 if payload["verdict"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
