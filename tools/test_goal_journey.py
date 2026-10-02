#!/usr/bin/env python3
"""V-JRNY-* gates: one compact Goal journey per root (plan s13 c8b).

A mission root (session title m-<id>-eN) joins to the goal epoch whose event names
that mission under `bind_mission`, read through the goal spine's own verified
reader; anything else is UNBOUND, with the reason. Receipts are counted from a
receipts file. The record stays compact: it is a summary, never a transcript.
Hermetic (GSDX_GOALS_ROOT points at a temp store); no model call."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import root_progress as rp  # noqa: E402
import usage_index as ux  # noqa: E402
from modules.gsd_x.goal import log as gl  # noqa: E402

PASS = FAIL = 0
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def iso(h):
    return datetime.fromtimestamp(T0 + h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def session(title, pid, h, sess):
    head = json.dumps({"type": "custom-title", "customTitle": title}) + "\n" if title else ""
    return (head + json.dumps({"type": "user", "promptId": pid, "timestamp": iso(h),
                               "sessionId": sess, "origin": {"kind": "task-notification"}}) + "\n"
            + json.dumps({"type": "assistant", "timestamp": iso(h + 0.01), "sessionId": sess,
                          "requestId": "r" + pid,
                          "message": {"id": "m" + pid, "model": "claude-opus-5-5", "content": [],
                                      "usage": {"input_tokens": 1, "cache_read_input_tokens": 10,
                                                "cache_creation_input_tokens": 0,
                                                "output_tokens": 1}}}) + "\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        os.environ[gl.ENV_ROOT] = str(Path(td) / "goals")
        log = gl.GoalLog("abcdef1", "g-test")
        log.append(1, "goal.created", {"title": "t"}, "test")
        log.append(2, "epoch.dispatching", {"spec": {"bind_mission": "m-aaaa11112222"}}, "test")
        proj = Path(td) / "projects" / "C--p"
        proj.mkdir(parents=True)
        (proj / "A.jsonl").write_text(session("m-aaaa11112222-e3", "PA", 1.0, "A"), encoding="utf-8")
        (proj / "B.jsonl").write_text(session("m-bbbb33334444-e1", "PB", 2.0, "B"), encoding="utf-8")
        (proj / "C.jsonl").write_text(session(None, "PC", 3.0, "C"), encoding="utf-8")
        rec = Path(td) / "receipts.jsonl"
        rec.write_text("".join(json.dumps({"subject": {"root_prompt": p}, "verdict": v}) + "\n"
                               for p, v in (("PA", "ALLOW"), ("PA", "WOULD_DEFER"), ("PB", "ALLOW"))),
                       encoding="utf-8")
        con = ux.connect(Path(td) / "ix.sqlite")
        try:
            ux.refresh(con, proj.parent, deadline_s=30)
            a = rp.journey(con, "PA", str(rec))
            ok("V-JRNY-BOUND", isinstance(a["goal"], list) and a["goal"][0]["goal_id"] == "g-test"
               and a["goal_join"]["epoch"] == 3, f"PA goal={a['goal']} join={a['goal_join']}")
            b = rp.journey(con, "PB", str(rec))
            ok("V-JRNY-UNBOUND-MISSION", b["goal"] == "UNBOUND" and b["goal_join"]["mission"]
               == "m-bbbb33334444", f"PB goal={b['goal']} join={b['goal_join']}")
            c = rp.journey(con, "PC")
            ok("V-JRNY-NOT-MISSION", c["goal"] == "UNBOUND"
               and c["goal_join"]["reason"] == "not a mission root", f"PC join={c['goal_join']}")
            ok("V-JRNY-RECEIPTS", a["policy_receipts"] == {"ALLOW": 1, "WOULD_DEFER": 1}
               and c["policy_receipts"] == "NOT_REQUESTED", f"PA receipts={a['policy_receipts']}")
            ok("V-JRNY-SHAPE-PROGRESS", a["shape"]["area"] == 1 and a["progress"]["state"] == "UNSETTLED",
               f"shape={a['shape']} progress={a['progress']}")
            size = len(json.dumps(a))
            ok("V-JRNY-COMPACT", size < 2048 and a["meta_overhead"]["model_calls"] == 0,
               f"{size} bytes, model_calls={a['meta_overhead']['model_calls']}")
            ok("V-JRNY-UNKNOWN", rp.journey(con, "nope")["status"] == "UNKNOWN_PROMPT", "unknown root")
        finally:
            con.close()
            os.environ.pop(gl.ENV_ROOT, None)

    total = PASS + FAIL
    print(f"GOAL_JOURNEY_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
