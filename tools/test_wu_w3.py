"""WU-W3 done-gate: calls_unit + model-call counter (by message.id) + breaker deny on the intended unit.

Fixture: a recorded-shape transcript where ONE model message (id m1) is written as 3 rows (one per
content block, the real transcript shape): 3 tool_use blocks but 1 model call; plus m2 (1 tool) and
m3 (text only). Truth: tool_calls=5, model_calls=3.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_session_budget_guard as T  # noqa: E402
import mission_spend as ms  # noqa: E402

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
    else:
        fails += 1
    print(("PASS " if cond else "FAIL ") + f"{gate}: {ev}")


def fixture(box):
    u = T.U(10, 0, 0, 5)
    box.append(T.row("m1", u, tools=[("Read", {"file_path": "a"})]))
    box.append(T.row("m1", u, tools=[("Read", {"file_path": "b"})]))
    box.append(T.row("m1", u, tools=[("Read", {"file_path": "c"})]))
    box.append(T.row("m2", u, tools=[("Grep", {"pattern": "x"})]))
    box.append(T.row("m3", u))
    box.append(T.row("m2", u, tools=[("Glob", {"pattern": "y"})]))


def main():
    # reference counter (python)
    b = T.Box()
    fixture(b)
    ref = ms.session_tokens(b.tx)
    check("W3-REF-COUNTS", ref.get("calls") == 5 and ref.get("model_calls") == 3, str(ref))

    # declare: calls_unit recorded, default tool, unknown refused
    p = b.declare(calls_estimate=4)
    rec = json.loads(Path(p).read_text(encoding="utf-8"))
    check("W3-UNIT-DEFAULT", rec.get("calls_unit") == "tool", str(rec.get("calls_unit")))
    try:
        b.declare(calls_estimate=4, calls_unit="bogus")
        check("W3-UNIT-UNKNOWN-REFUSED", False, "declare accepted bogus")
    except ValueError:
        check("W3-UNIT-UNKNOWN-REFUSED", True, "ValueError")

    # guard counters match the transcript
    b.call()
    st = b.st()
    check("W3-GUARD-COUNTS", st.get("calls") == 5 and st.get("model_calls") == 3,
          f"calls={st.get('calls')} model_calls={st.get('model_calls')}")

    # breaker, unit=tool: 5 > 1.0 x 4 -> deny ; unit=model: 3 <= 4 -> not deny
    b.declare(calls_estimate=4, call_ratio=1.0, calls_unit="tool", noprogress_calls=999)
    k_tool = T.kind(b.call()["out"])
    check("W3-DENY-TOOL-UNIT", k_tool == "deny", k_tool)
    b2 = T.Box()
    fixture(b2)
    b2.declare(calls_estimate=4, call_ratio=1.0, calls_unit="model", noprogress_calls=999)
    k_model = T.kind(b2.call()["out"])
    check("W3-ALLOW-MODEL-UNIT", k_model != "deny", k_model)
    # model unit denies when model calls exceed: estimate 2 -> 3 > 2
    b3 = T.Box()
    fixture(b3)
    b3.declare(calls_estimate=2, call_ratio=1.0, calls_unit="model", noprogress_calls=999)
    out = b3.call()["out"]
    reason = json.dumps(out)
    check("W3-DENY-MODEL-UNIT", T.kind(out) == "deny" and "model calls" in reason, reason[:160])
    # deny message names the unit on the tool pole
    check("W3-DENY-NAMES-UNIT", "tool calls" in json.dumps(b.call()["out"]), "tool calls named")

    # unknown unit in a hand-edited budget is not free: deny
    b4 = T.Box()
    fixture(b4)
    pth = b4.declare(calls_estimate=100, noprogress_calls=999)
    d = json.loads(Path(pth).read_text(encoding="utf-8"))
    d["calls_unit"] = "weird"
    Path(pth).write_text(json.dumps(d), encoding="utf-8")
    check("W3-UNKNOWN-UNIT-DENIES", T.kind(b4.call()["out"]) == "deny", "deny")

    print(f"{passes} pass / {fails} fail")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
