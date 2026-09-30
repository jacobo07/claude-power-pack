"""V-FCT gates for tools/fresh_context_tax.py on synthetic transcripts.
    python tools/test_fresh_context_tax.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fresh_context_tax as fct  # noqa: E402

passes = fails = 0


def gate(name, cond, evidence):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {name}: {evidence}")


def write(path: Path, rows: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def asst(ts, usage, content, model="claude-opus-5-5"):
    return {"type": "assistant", "timestamp": ts, "message": {"model": model, "usage": usage, "content": content}}


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        good = write(d / "good.jsonl", [
            {"type": "user", "timestamp": "2026-09-28T10:00:00Z", "message": {"content": "/gsd-autonomous --x"}},
            asst("2026-09-28T10:00:05Z", {"input_tokens": 10, "cache_creation_input_tokens": 180000,
                                          "cache_read_input_tokens": 0}, [{"type": "text", "text": "ok"}]),
            asst("2026-09-28T10:00:20Z", {"input_tokens": 5, "cache_creation_input_tokens": 500,
                                          "cache_read_input_tokens": 180010}, [{"type": "tool_use", "id": "t1"}]),
        ])
        refused = write(d / "refused.jsonl", [
            {"type": "user", "timestamp": "2026-09-28T10:00:00Z", "message": {"content": "/gsd-autonomous"}},
            asst("2026-09-28T10:00:01Z", {"input_tokens": 0, "output_tokens": 0},
                 [{"type": "text", "text": "You've hit your weekly limit · resets 8pm"}], model="<synthetic>"),
        ])
        paths = {"good": good, "refused": refused, "gone": None}
        find = paths.get

        g = fct.measure_session("good", 1_000_000, find=find)
        gate("V-FCT-MEASURED", g["state"] == "MEASURED" and g["bootstrap_tokens"] == 180010
             and g["tokens_at_first_action"] == 180515 and g["secs_to_first_action"] == 20.0,
             {k: g.get(k) for k in ("state", "bootstrap_tokens", "tokens_at_first_action", "secs_to_first_action")})
        r = fct.measure_session("refused", 1_000_000, find=find)
        gate("V-FCT-REFUSAL-IS-NOT-ZERO", r["state"] == "PROVIDER_REFUSED" and "bootstrap_tokens" not in r,
             r["state"] + " " + r.get("reason", "")[:40])
        n = fct.measure_session("gone", 1_000_000, find=find)
        gate("V-FCT-UNMEASURED", n["state"] == "UNMEASURED", n["reason"])
        gate("V-FCT-DAY", g.get("day") == "2026-09-28", g.get("day"))
        rows = [g, {"state": "MEASURED", "bootstrap_tokens": 100, "day": "2026-09-29"},
                {"state": "MEASURED", "bootstrap_tokens": 300, "day": "2026-09-29"},
                {"state": "MEASURED", "bootstrap_tokens": 50, "day": None}, r, n]
        bd = fct.by_day(rows)
        gate("V-FCT-BY-DAY", bd == {"2026-09-28": {"n": 1, "median": 180010, "min": 180010, "max": 180010},
                                    "2026-09-29": {"n": 2, "median": 200.0, "min": 100, "max": 300},
                                    "UNDATED": {"n": 1, "median": 50, "min": 50, "max": 50}}, bd)
    print(f"FCT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
