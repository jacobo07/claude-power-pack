#!/usr/bin/env python3
"""V-BUDGETOBS gates: budget_monitor runway from observed programmatic usage."""
from __future__ import annotations

import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import budget_monitor as B  # noqa: E402

passes = fails = 0
PRICING = {"models": {"claude-opus-5-5": {"input": 4.0, "output": 20.0,
                                          "cache_write_5m": 5.0, "cache_write_1h": 8.0,
                                          "cache_read": 0.2}}}
CFG = {"tier": "pro", "monthly_usd": 20.0}


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  [PASS] {gate}: {ev}")
    else:
        fails += 1
        print(f"  [FAIL] {gate}: {ev}")


def session(path: Path, entrypoint: str, n: int, model="claude-opus-5-5", ts=None):
    ts = ts or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    lines = [json.dumps({"type": "user", "entrypoint": entrypoint, "message": {"content": "x"}})]
    for i in range(n):
        line = json.dumps({"type": "assistant", "timestamp": ts, "requestId": f"r{i}",
                           "message": {"id": f"{path.stem}{i}", "model": model,
                                       "usage": {"input_tokens": 1_000_000, "output_tokens": 0}}})
        lines += [line, line]  # streamed twice: must count once
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / "p"
        proj.mkdir()
        session(proj / "prog.jsonl", "sdk-cli", 3)       # 3 calls x $4 = $12
        session(proj / "chat.jsonl", "cli", 5)           # interactive: excluded
        old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).isoformat()
        session(proj / "old.jsonl", "sdk-cli", 4, ts=old.replace("+00:00", "Z"))

        ob = B._aggregate_observed(7, PRICING, project_dirs=[proj])
        check("V-BUDGETOBS-PROGRAMMATIC-ONLY",
              ob["calls"] == 3 and ob["interactive_calls_excluded"] == 5,
              f"calls={ob['calls']} interactive_excluded={ob['interactive_calls_excluded']}")
        check("V-BUDGETOBS-WINDOW", abs(ob["usd"] - 12.0) < 1e-9,
              f"usd={ob['usd']} (30-day-old sdk-cli calls outside the 7d window)")
        r = B._compute_runway(CFG, PRICING, ob)
        check("V-BUDGETOBS-RUNWAY", r["status"] == "ok" and r["source"] == "observed"
              and abs(r["daily_burn_usd"] - 12.0 / 7) < 1e-4,
              f"{r}")

        unp = Path(td) / "u"
        unp.mkdir()
        session(unp / "x.jsonl", "sdk-cli", 3, model="claude-future-9")
        r_u = B._compute_runway(CFG, PRICING, B._aggregate_observed(7, PRICING, [unp]))
        check("V-BUDGETOBS-UNPRICED-REFUSES", r_u["status"] == "unpriced-models"
              and r_u["runway_days"] is None, f"{r_u['status']}: {r_u.get('reason')}")

        chat_only = Path(td) / "c"
        chat_only.mkdir()
        session(chat_only / "c.jsonl", "cli", 3)
        r_z = B._compute_runway(CFG, PRICING, B._aggregate_observed(7, PRICING, [chat_only]))
        check("V-BUDGETOBS-MEASURED-ZERO", r_z["status"] == "zero-burn-in-window"
              and "sdk-cli" in r_z.get("reason", ""), f"{r_z}")

        r_m = B._compute_runway(CFG, PRICING, {"state": "UNMEASURED", "reason": "no transcripts dir"})
        check("V-BUDGETOBS-UNMEASURED", r_m["status"] == "UNMEASURED",
              f"{r_m}")
        check("V-BUDGETOBS-STATES-DISTINCT",
              len({r["status"], r_u["status"], r_z["status"], r_m["status"]}) == 4,
              "ok / unpriced-models / zero-burn-in-window / UNMEASURED")

    print(f"BUDGETOBS_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
