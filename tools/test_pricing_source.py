#!/usr/bin/env python3
"""V-PRICESRC gates for tools/pricing_source.py and the current pricing file."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pricing_source as P  # noqa: E402

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  [PASS] {gate}: {ev}")
    else:
        fails += 1
        print(f"  [FAIL] {gate}: {ev}")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        for name in ("anthropic_2026-05.json", "anthropic_2026-09.json",
                     "anthropic_2025-12.json", "anthropic_latest.json",
                     "anthropic_2027-01.json.bak"):
            (d / name).write_text("{}", encoding="utf-8")
        got = P.current_pricing_path(d).name
        check("V-PRICESRC-NEWEST", got == "anthropic_2026-09.json",
              f"picked {got} (undated / .bak names ignored)")

        empty = d / "empty"
        empty.mkdir()
        try:
            P.current_pricing_path(empty)
            check("V-PRICESRC-NONE-RAISES", False, "returned instead of raising")
        except FileNotFoundError:
            check("V-PRICESRC-NONE-RAISES", True, "FileNotFoundError on empty dir")
        miss = P.pricing_path_or_missing(empty)
        check("V-PRICESRC-MISSING-PATH", not miss.exists(),
              f"{miss.name} does not exist, so the consumer's is_file() branch fires")

    cur = P.current_pricing_path()
    data = json.loads(cur.read_text(encoding="utf-8"))
    o47 = data["models"].get("claude-opus-4-7", {})
    # The 2026-05 file priced this id at the Opus 4/4.1 rate of $15/$75.
    check("V-PRICESRC-OPUS47-NOT-OPUS4-RATE",
          o47.get("input") == 5.0 and o47.get("output") == 25.0,
          f"{cur.name}: claude-opus-4-7 = {o47.get('input')}/{o47.get('output')}")
    bad = [m for m, p in data["models"].items()
           if abs(p["cache_write_5m"] - 1.25 * p["input"]) > 1e-9
           or abs(p["cache_write_1h"] - 2.0 * p["input"]) > 1e-9]
    check("V-PRICESRC-WRITE-MULTIPLIERS", not bad,
          f"5m=1.25x, 1h=2x input for every model; offenders={bad}")

    print(f"PRICESRC_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
