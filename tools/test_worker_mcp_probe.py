#!/usr/bin/env python
"""V-MCPP-* gates for tools/worker_mcp_probe.py: the predeclared rule, driven from every pole, plus the
result parser. No model call -- the live probe is run by hand (it spends tokens)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worker_mcp_probe as p  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def ok(tokens):
    return {"ok": True, "tokens": tokens}


def main() -> int:
    v, why = p.decide([ok(98321)] * 3, [ok(90967)] * 3)
    check("V-MCPP-MEASURED-SAVING-APPLIES", v == "APPLY", why)
    v, why = p.decide([ok(100_000)] * 3, [ok(96_000)] * 3)
    check("V-MCPP-CONTROL-SMALL-SAVING-KEEPS", v == "KEEP", why)
    v, _ = p.decide([ok(100_000)] * 3, [ok(95_000)] * 3)
    check("V-MCPP-THRESHOLD-INCLUSIVE", v == "APPLY", "exactly 5% applies, as the .sh rule says")
    v, _ = p.decide([ok(98321), {"ok": False}, ok(98321)], [ok(90967)] * 3)
    check("V-MCPP-DEFAULT-FAILURE-UNJUDGED", v == "UNJUDGED")
    v, _ = p.decide([ok(98321)] * 3, [ok(90967), {"ok": False}, ok(90967)])
    check("V-MCPP-NOMCP-FAILURE-KEEPS", v == "KEEP")
    check("V-MCPP-NO-RUNS-UNJUDGED", p.decide([], [])[0] == "UNJUDGED")
    good = json.dumps({"result": "OK", "is_error": False,
                       "usage": {"input_tokens": 2, "cache_creation_input_tokens": 80898, "cache_read_input_tokens": 17421}})
    r = p.parse_run(good)
    check("V-MCPP-PARSE-SUMS-INPUT-AND-CACHE", r["ok"] and r["tokens"] == 98321, str(r))
    check("V-MCPP-PARSE-NOT-OK-ANSWER", not p.parse_run(json.dumps({"result": "Sure!", "usage": {}}))["ok"])
    check("V-MCPP-PARSE-ERROR-RESULT", not p.parse_run(json.dumps({"result": "OK", "is_error": True}))["ok"])
    check("V-MCPP-PARSE-UNREADABLE", not p.parse_run("not json", "boom")["ok"])
    print(f"MCPP_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
