#!/usr/bin/env python
"""V-AUTOPSY-* gates for modules/token-optimizer/token_autopsy.py (fixed 2026-09-27).

Measured before the fix, on real sessions: another pane's transcript analysed as "latest",
a headline total that omitted 56.8 M cache reads, a cost of -$746, every message counted
once per content-block line (485 M cache reads for a session that had 80 M), and one
session counted twice because it was recorded under two project folders."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "token_autopsy", ROOT / "modules" / "token-optimizer" / "token_autopsy.py")
ta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ta)

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def line(mid, cr, out=10, model="claude-opus-5-5"):
    return json.dumps({"type": "assistant", "timestamp": "2026-09-27T10:00:00Z", "message": {
        "id": mid, "model": model, "content": [],
        "usage": {"input_tokens": 1, "cache_creation_input_tokens": 100,
                  "cache_read_input_tokens": cr, "output_tokens": out}}})


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="autopsy-test-"))
    sid = "11111111-2222-4333-8444-555555555555"
    for folder in ("proj-a", "proj-b"):   # the same session recorded under two folders
        d = tmp / folder
        d.mkdir()
        # m1 is written as three lines (one per content block), as the harness does
        (d / f"{sid}.jsonl").write_text("\n".join(
            [line("m1", 1_000_000)] * 3 + [line("m2", 2_000_000)]), encoding="utf-8")
    other = tmp / "proj-c"
    other.mkdir()
    (other / "99999999-0000-4000-8000-000000000000.jsonl").write_text(line("x", 5), encoding="utf-8")
    os.utime(other / "99999999-0000-4000-8000-000000000000.jsonl")  # newest file on disk

    saved = os.environ.get("CLAUDE_CODE_SESSION_ID")
    os.environ["CLAUDE_CODE_SESSION_ID"] = sid
    try:
        picked = ta.find_session_logs(tmp, "latest")
        check("V-AUTOPSY-LATEST-IS-OWN-SESSION", [p.stem for p in picked] == [sid], str(picked))
        check("V-AUTOPSY-ONE-FILE-PER-SESSION",
              [p.stem for p in ta.find_session_logs(tmp, sid)] == [sid])
        os.environ.pop("CLAUDE_CODE_SESSION_ID")
        control = ta.find_session_logs(tmp, "latest")
        check("V-AUTOPSY-LATEST-FALLBACK-NEWEST",
              len(control) == 1 and control[0].stem.startswith("99999999"), str(control))
    finally:
        if saved is None:
            os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        else:
            os.environ["CLAUDE_CODE_SESSION_ID"] = saved

    s = ta.parse_session(tmp / "proj-a" / f"{sid}.jsonl")
    check("V-AUTOPSY-MESSAGE-COUNTED-ONCE", s["usage"]["cache_read_input_tokens"] == 3_000_000,
          str(s["usage"]))
    cost = ta.estimate_cost(s["usage"], "claude-opus-5-5")
    c = cost.get("claude-opus-5-5", {})
    # 3 M cache reads at $0.20 + 200 writes at $5.00 + 2 input at $4 + 20 output at $20, per M
    expected = 3.0 * 0.20 + 200 / 1e6 * 5.0 + 2 / 1e6 * 4.0 + 20 / 1e6 * 20.0
    check("V-AUTOPSY-COST-POSITIVE-AND-EXACT",
          bool(c) and c["total"] > 0 and abs(c["total"] - expected) < 1e-9, str(c))
    check("V-AUTOPSY-OPUS-5-5-NOT-OPUS-5", ta.get_pricing("claude-opus-5-5")["cache_read"] == 0.20)
    check("V-AUTOPSY-UNKNOWN-MODEL-UNPRICED", ta.estimate_cost(s["usage"], "claude-imaginary-9") == {})
    check("V-AUTOPSY-PRICES-FROM-CANONICAL-SOURCE", "anthropic_" in ta.PRICING_SOURCE, ta.PRICING_SOURCE)

    print(f"AUTOPSY_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
