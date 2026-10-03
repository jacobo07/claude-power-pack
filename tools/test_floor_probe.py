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

        # C4.1 detail: per-file instructions and named former other_attachments types.
        home = Path(td) / "home"
        g, rule, mem = (str(home / ".claude" / "CLAUDE.md"),
                        str(home / ".claude" / "rules" / "x.md"),
                        str(home / ".claude" / "projects" / "p" / "memory" / "MEMORY.md"))
        d = Path(td) / "detail.jsonl"
        d.write_text("".join(json.dumps(x) + "\n" for x in [
            {"type": "attachment", "attachment": {"type": "instructions", "files": [
                {"path": g, "content": "G" * 4000}, {"path": rule, "content": "R" * 2000},
                {"path": mem, "content": "M" * 500}]}},
            {"type": "attachment", "attachment": {"type": "agent_listing_delta", "addedTypes": ["a"] * 50}},
            {"type": "attachment", "attachment": {"type": "brand_new_kind", "content": "N" * 80}},
            {"type": "assistant", "message": {"model": "m", "usage": {"input_tokens": 9000}}},
        ]), encoding="utf-8")
        detail: dict = {}
        comp, _ = fp.startup_components(d, detail)
        fsum = sum(v for k, v in detail.items() if k.startswith("file:"))
        ok("V-FLOOR-DETAIL-FILES",
           len([k for k in detail if k.startswith("file:")]) == 3
           and 0 < fsum <= comp["instructions"] and detail[f"file:{g}"] > detail[f"file:{rule}"],
           f"3 files, sum {fsum} <= instructions {comp['instructions']}")
        ok("V-FLOOR-NAMED-TYPES",
           comp.get("agent_listing_delta", 0) > 0 and "type:agent_listing_delta" not in detail
           and detail.get("type:brand_new_kind", 0) > 0
           and comp["other_attachments"] == detail["type:brand_new_kind"],
           "agent listing is its own component; an unknown type stays in other and is named")
        cls = [fp.instruction_class(p, home) for p in (g, rule, mem, str(Path(td) / "repo" / "CLAUDE.md"))]
        ok("V-FLOOR-INSTR-CLASS",
           cls == ["GLOBAL_CLAUDE_MD", "GLOBAL_RULE", "MEMORY", "PROJECT_CONTEXT"], f"{cls}")

        rows = [{"calls": 10, "detail": detail}]
        ranked = [("instructions", 1000.0), ("environment", 500.0), ("hook_success", 400.0),
                  ("skill_listing", 300.0)]
        rd = fp.rank_detail(rows, 1.0, 10_000.0, ranked, home)
        names = [x["component"] for x in rd["controllable_ranked"]]
        ok("V-FLOOR-RANK-CONTROLLABLE", names == ["instructions", "skill_listing"]
           and rd["controllable_ranked"][0]["share"] == 0.1,
           f"{names}: PROVIDER and UNKNOWN never ranked as levers; share is of the whole floor")
        bc = rd["instructions_by_class"]
        ok("V-FLOOR-RANK-CLASSES", list(bc)[0] == "GLOBAL_CLAUDE_MD"
           and abs(sum(v["tokens"] for v in bc.values()) - fsum * 10) <= 3
           and rd["unmapped_attachment_types"][0]["type"] == "brand_new_kind",
           f"classes {list(bc)} sum to the per-file rent")

    total = PASS + FAIL
    print(f"FLOOR_PROBE_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
