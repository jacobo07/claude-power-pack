#!/usr/bin/env python
"""Gate for tools/a3_pane_autopsy.py. Each V-A3AUTOPSY gate is driven GREEN on a synthetic
transcript and RED against a deliberately wrong variant/expectation, so a gate that cannot
fail is caught. Exit 0 only when every gate shows both poles."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a3_pane_autopsy as A  # noqa: E402

FAILS = []


def gate(name: str, green: bool, red_detects: bool):
    ok = green and red_detects
    print(f"{'PASS' if ok else 'FAIL'} {name} green={green} red_detected={red_detects}")
    if not ok:
        FAILS.append(name)


def asst(mid, rid, inp, cw, cr, out, tools=()):
    content = [{"type": "tool_use", "id": t[0], "name": t[1], "input": t[2]} for t in tools]
    return {"type": "assistant", "requestId": rid, "message": {
        "id": mid, "usage": {"input_tokens": inp, "cache_creation_input_tokens": cw,
                             "cache_read_input_tokens": cr, "output_tokens": out}, "content": content}}


def result(tid, chars):
    return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "content": "x" * chars}]}}


def build(tmp: Path) -> Path:
    d = tmp / "proj"
    d.mkdir()
    p = d / "abcd1234-0000.jsonl"
    rows = [
        asst("m1", "r1", 10, 1000, 9000, 50, [("t1", "Read", {"file_path": "a.py"})]),     # ctx 10010
        result("t1", 400),
        asst("m2", "r2", 10, 100, 11000, 60, [("t2", "Read", {"file_path": "a.py"})]),     # ctx 11110, repeat read
        result("t2", 800),
        asst("m3", "r3", 10, 100, 13000, 70, [("t3", "Bash", {"command": "ls"}), ("t4", "Agent", {})]),  # ctx 13110
        result("t3", 4000),
        asst("m3", "r3", 10, 100, 13000, 75, [("t3", "Bash", {"command": "ls"}), ("t4", "Agent", {})]),  # streamed dup
        asst("m4", "r4", 10, 100, 15000, 80, [("t5", "Edit", {"file_path": "b.py"})]),     # ctx 15110
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        p = build(tmp)
        r = A.analyze(p)
        raw = A.analyze(p, dedup=False)
        # dedup: 4 unique calls, the streamed duplicate counted once; without dedup it is 5
        gate("V-A3AUTOPSY-DEDUP", r["calls"] == 4 and r["split"]["output"] == 50 + 60 + 75 + 80, raw["calls"] == 5)
        # floor = first call context
        gate("V-A3AUTOPSY-FLOOR", r["floor"] == 10010, r["floor"] != 11110)
        # split: total = floor x calls + growth + output, exactly
        s = r["split"]
        ctx = [10010, 11110, 13110, 15110]
        gate("V-A3AUTOPSY-SPLIT", s["floor_x_calls"] + s["growth_above_floor"] + s["output"] == r["processed"]
             and s["growth_above_floor"] == sum(ctx) - 4 * 10010,
             s["growth_above_floor"] != 0 and s["floor_x_calls"] + s["growth_above_floor"] != r["processed"])
        # growth slope positive and equal to the least-squares value
        gate("V-A3AUTOPSY-SLOPE", abs(r["slope_per_call"] - A.slope(ctx)) < 0.1 and r["slope_per_call"] > 0,
             A.slope([5, 5, 5, 5]) == 0)
        # repeated read: second Read of a.py is the only repeat; its result is 800/4 = 200 tokens
        gate("V-A3AUTOPSY-REPEATREAD", r["repeated_reads"] == {"count": 1, "tokens_est": 200},
             A.analyze(p)["repeated_reads"]["count"] != 0 and A.slope([1]) is None)
        # effect / deliberation: m1, m2 are Read-only (no effect); m3 Bash, m4 Edit are effects
        gate("V-A3AUTOPSY-EFFECT", r["no_effect_calls"] == 2 and r["effect_calls"] == 2, r["no_effect_calls"] != 0)
        # Agent spawn counted once despite the streamed duplicate; no subagent dir -> UNKNOWN (None), never 0
        gate("V-A3AUTOPSY-SPAWN-UNKNOWN", r["agent_spawns"] == 1 and r["subagent_processed"] is None,
             r["subagent_processed"] != 0)
        # tool_result share by tool sums to ~1
        gate("V-A3AUTOPSY-SHARE", abs(sum(r["tool_result_share"].values()) - 1) < 0.01
             and r["tool_result_share"]["Bash"] > r["tool_result_share"]["Read"], True)
        # counterfactual labelled ESTIMATED and uses the measured floor
        cf = r["counterfactual_est"]
        gate("V-A3AUTOPSY-CF", cf["label"] == "ESTIMATED" and cf["floor"] == 95695
             and cf["processed"] == 2 * 95695 + 75 + 80, cf["processed"] != r["processed"])
        # missing transcript is UNKNOWN, found one is OK
        miss = A.run(["deadbeef"], tmp)["deadbeef"]
        found = A.run(["abcd1234"], tmp)["abcd1234"]
        gate("V-A3AUTOPSY-UNKNOWN", miss["status"] == "UNKNOWN" and "calls" not in miss, found["status"] == "OK")
    print(f"A3AUTOPSY_PASS={10 - len(FAILS)}/10")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
