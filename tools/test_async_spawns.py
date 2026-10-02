#!/usr/bin/env python3
"""V-ASYNC-* gates: an async Agent's tool_result is its LAUNCH ack, never its return.

Measured 2026-10-03 on the live index (peer S3 audit): 1,184 of 1,452 recorded spawn
results were "Async agent launched successfully.", so c4 counted launches as RETURNED
and c8's Equivalents treated every async equivalent as finished at launch. Here the
ack is driven from both poles: it is LAUNCHED / ASYNC_RAN and never RETURNED, a real
answer stays RETURNED, and an async equivalent stays active until its subagent's last
call (or, with no subagent, for the NO_RESULT bound). Hermetic; no model call."""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import estate_shadow as es  # noqa: E402
import fanout_ledger as fl  # noqa: E402
import usage_index as ux  # noqa: E402

PASS = FAIL = 0
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()
SESS = "S1"
ACK = ("Async agent launched successfully. (This tool result is intended for the model; "
       "the agent's output arrives later as a task notification.)")


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def iso(h):
    return datetime.fromtimestamp(T0 + h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def asst(mid, h, spawns=(), prompt="same"):
    content = [{"type": "tool_use", "id": s, "name": "Agent",
                "input": {"subagent_type": "Explore", "prompt": prompt}} for s in spawns]
    return json.dumps({"type": "assistant", "timestamp": iso(h), "sessionId": SESS,
                       "requestId": "r" + mid,
                       "message": {"id": mid, "model": "claude-opus-5-5", "content": content,
                                   "usage": {"input_tokens": 1, "cache_read_input_tokens": 10,
                                             "cache_creation_input_tokens": 0,
                                             "output_tokens": 1}}}) + "\n"


def result(tuid, h, text, is_error=False):
    c = {"type": "tool_result", "tool_use_id": tuid, "content": text}
    if is_error:
        c["is_error"] = True
    return json.dumps({"type": "user", "timestamp": iso(h), "sessionId": SESS,
                       "message": {"role": "user", "content": [c]}}) + "\n"


def subagent(proj: Path, tuid: str, hours) -> None:
    d = proj / "C--p" / SESS / "subagents"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"agent-{tuid}.jsonl").write_text(
        "".join(asst(f"{tuid}-{i}", h) for i, h in enumerate(hours)), encoding="utf-8")
    (d / f"agent-{tuid}.meta.json").write_text(
        json.dumps({"agentType": "Explore", "toolUseId": tuid, "spawnDepth": 1}), encoding="utf-8")


def main() -> int:
    # -- pure classification, both poles ------------------------------------------
    ok("V-ASYNC-ACK-LINKED", fl.spawn_outcome(1.0, 0, ACK, True) == "ASYNC_RAN",
       "ack + subagent transcript -> ASYNC_RAN, not RETURNED")
    ok("V-ASYNC-ACK-UNLINKED", fl.spawn_outcome(1.0, 0, ACK, False) == "LAUNCHED",
       "ack, no subagent transcript -> LAUNCHED (nothing observed to run)")
    ok("V-ASYNC-ANSWER-STAYS", fl.spawn_outcome(1.0, 0, "found it", True) == "RETURNED",
       "control: a real answer is still RETURNED")
    ok("V-ASYNC-ERROR-NOT-ACK", fl.spawn_outcome(1.0, 1, ACK, False) == "FAILED_TO_START",
       "an ERROR result is never read as a launch ack")

    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / "projects"
        main_fp = proj / "C--p" / f"{SESS}.jsonl"
        main_fp.parent.mkdir(parents=True)
        main_fp.write_text(
            asst("m1", 1.0, spawns=("tuA",))                    # async, child calls 1.1 .. 3.0
            + result("tuA", 1.01, ACK)
            + asst("m2", 1.5, spawns=("tuB",), prompt="other")  # async, no child transcript
            + result("tuB", 1.51, ACK)
            + asst("m3", 1.6, spawns=("tuS",), prompt="sync")   # synchronous answer
            + result("tuS", 1.7, "the answer")
            + asst("m4", 2.0, spawns=("tuA2",))                 # equivalent of tuA, child running
            + result("tuA2", 2.01, ACK)
            + asst("m5", 1.8, spawns=("tuB2",), prompt="other") # equivalent of tuB within bound
            + asst("m6", 4.0, spawns=("tuA3",)),                # equivalent of tuA, child ended
            encoding="utf-8")
        subagent(proj, "tuA", (1.1, 2.0, 3.0))
        subagent(proj, "tuA2", (2.1,))
        con = ux.connect(Path(td) / "ix.sqlite")
        try:
            r = ux.refresh(con, proj, deadline_s=30)
            ok("V-ASYNC-REFRESH", r["status"] == "OK", json.dumps(r))
            got = {s["tool_use_id"]: s["outcome"] for s in fl.spawn_rows(con, 0, T0 + 99 * 3600)}
            ok("V-ASYNC-OUTCOMES", got.get("tuA") == "ASYNC_RAN" and got.get("tuB") == "LAUNCHED"
               and got.get("tuS") == "RETURNED", f"{got}")
            s = fl.summary(con, T0, T0 + 99 * 3600).get("spawn_outcomes", {})
            ok("V-ASYNC-SUMMARY", s.get("RETURNED") == 1 and s.get("ASYNC_RAN") == 2
               and s.get("LAUNCHED") == 1, f"summary: {s} (only tuS returned an answer)")
            last = fl.child_last_call(con)
            ok("V-ASYNC-CHILD-LAST", last.get("tuA") == T0 + 3.0 * 3600 and "tuB" not in last,
               f"tuA child last call {last.get('tuA')}; tuB has none")

            eq = es.Equivalents(con)
            h = con.execute("SELECT input_hash FROM spawns WHERE tool_use_id='tuA'").fetchone()[0]
            hb = con.execute("SELECT input_hash FROM spawns WHERE tool_use_id='tuB'").fetchone()[0]
            ok("V-ASYNC-EQ-RUNNING", eq.active(h, T0 + 2.0 * 3600, "tuA2") == 1,
               "at 2 h tuA's child is still calling: its equivalent is active "
               "(the ack at 1.01 h is not its end)")
            ok("V-ASYNC-EQ-ENDED", eq.active(h, T0 + 4.0 * 3600, "tuA3") == 0,
               "control: at 4 h tuA (last call 3 h) and tuA2 (last call 2.1 h) have ended")
            ok("V-ASYNC-EQ-NO-CHILD", eq.active(hb, T0 + 1.8 * 3600, "tuB2") == 1,
               "an ack with no subagent has no end: active within the NO_RESULT bound")
            after = T0 + 1.8 * 3600 + es.NO_RESULT_ACTIVE_S + 60   # past tuB AND tuB2's bound
            ok("V-ASYNC-EQ-NO-CHILD-BOUND", eq.active(hb, after, "tuX") == 0,
               "control: past the NO_RESULT bound an endless ack is no longer running "
               "(no end is not 'running forever')")
        finally:
            con.close()

    total = PASS + FAIL
    print(f"ASYNC_SPAWNS_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
