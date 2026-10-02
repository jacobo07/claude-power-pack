#!/usr/bin/env python3
"""V-FLOOR-* gates for tools/floor_probe.py (C4.0). Hermetic, no model call.

The fit is driven from both poles: synthetic transcripts generated from a KNOWN
tokens-per-char rate and known per-type hidden floors must be recovered, and data with
no within-type variation must come back UNMEASURED rather than as a number."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import floor_probe as fp  # noqa: E402

PASS = FAIL = 0


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def main() -> int:
    rate, hidden = 0.3, {"gsd-executor": 20000, "Explore": 9000}
    rows = []
    for t, base in hidden.items():
        for chars in (40000, 90000, 150000, 200000):
            rows.append({"type": t, "chars": chars, "ctx": round(rate * chars + base)})
    f = fp.fit(rows)
    ok("V-FLOOR-FIT-RECOVERS", abs(f["rate"] - rate) < 1e-3
       and all(abs(f["intercepts"][t] - b) < 5 for t, b in hidden.items()),
       f"rate={f['rate']:.4f} intercepts={ {k: round(v) for k, v in f['intercepts'].items()} }")
    flat = [{"type": "x", "chars": 100, "ctx": 50}, {"type": "x", "chars": 100, "ctx": 60}]
    ok("V-FLOOR-NO-VARIATION-UNMEASURED", fp.fit(flat).get("rate") is None,
       "identical chars within every type -> no rate, never a guessed one")

    with tempfile.TemporaryDirectory() as td:
        t = Path(td) / "agent.jsonl"
        lines = [
            {"type": "user", "message": {"role": "user", "content": "do the task"}},
            {"type": "attachment", "attachment": {"type": "instructions", "content": "R" * 1000}},
            {"type": "attachment", "attachment": {"type": "skill_listing", "content": "S" * 300}},
            {"type": "attachment", "attachment": {"type": "hook_thing", "content": "H" * 50}},
            {"type": "assistant", "message": {"model": "claude-opus-5-5", "usage": {
                "input_tokens": 3, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 700}}},
            {"type": "attachment", "attachment": {"type": "instructions", "content": "LATE" * 999}},
        ]
        t.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        comp, ctx = fp.startup_components(t)
        ok("V-FLOOR-COMPONENTS", ctx == 703 and comp["instructions"] > 1000
           and comp["skill_listing"] > 300 and comp["other_attachments"] > 50
           and comp["opening_message"] > 0 and comp["instructions"] < 2000,
           f"ctx={ctx} comp={comp} (lines after the first call are not startup)")
        s = Path(td) / "synthetic_only.jsonl"
        s.write_text(json.dumps({"type": "assistant", "message": {
            "model": "<synthetic>", "usage": {"output_tokens": 0}}}) + "\n", encoding="utf-8")
        ok("V-FLOOR-SYNTHETIC-SKIPPED", fp.startup_components(s) is None,
           "a refused (synthetic) first row is not a startup measurement")

    total = PASS + FAIL
    print(f"FLOOR_PROBE_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
