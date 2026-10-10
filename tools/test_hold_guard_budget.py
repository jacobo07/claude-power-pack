"""EVC U5 gate: a hold writes the guard budget for the live worker, and the REAL guard then denies
that worker's next tool call (canary drill, isolated GSD_LONG_RUN_STATE_DIR, no live state touched)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TMP = tempfile.mkdtemp(prefix="holdguard_")
STATE = Path(TMP) / "state"
STATE.mkdir()
os.environ["GSD_LONG_RUN_STATE_DIR"] = str(STATE)
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

GUARD = HERE.parent / "hooks" / "session_budget_guard.js"
NODE = shutil.which("node") or "node"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(("PASS " if cond else "FAIL ") + gate + (f": {ev}" if ev else ""))


RUNNER = ("const g=require(process.argv[1]);let r='';process.stdin.on('data',d=>r+=d).on('end',()=>"
          "{process.stdout.write(JSON.stringify(g.decide(JSON.parse(r))));});")


def call(sid, tx):
    ev = {"session_id": sid, "tool_name": "Bash", "tool_input": {"command": "echo hi"}, "transcript_path": str(tx)}
    p = subprocess.run([NODE, "-e", RUNNER, str(GUARD)], input=json.dumps(ev), capture_output=True, text=True,
                       env=dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(STATE)), timeout=60)
    if p.returncode != 0:
        return "CRASH " + p.stderr[-200:]
    out = json.loads(p.stdout)
    h = (out or {}).get("hookSpecificOutput") or {} if not isinstance(out, str) else {}
    return "deny" if h.get("permissionDecision") == "deny" else ("allow" if out is None else "other")


def tx_with(path, n_msgs):
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n_msgs):
            fh.write(json.dumps({"type": "assistant", "timestamp": "2026-10-10T10:00:00.000Z", "uuid": f"u{i}",
                                 "message": {"id": f"m{i}", "model": "claude-opus-5-5",
                                             "content": [{"type": "tool_use", "name": "Read", "input": {}}],
                                             "usage": {"input_tokens": 50000, "cache_creation_input_tokens": 0,
                                                       "cache_read_input_tokens": 0, "output_tokens": 10}}}) + "\n")


def main():
    sid = "hold-worker-0001"
    tx = Path(TMP) / "t.jsonl"
    tx_with(tx, 3)
    # CONTROL: no budget file -> the worker is not touched
    check("V-HOLDGUARD-CONTROL-NO-FILE-ALLOWS", call(sid, tx) == "allow")
    # the hold-side writer, driven by a record whose owner is the worker
    rec = {"mission_id": "m-hold-canary", "owner": {"session_id": sid}}
    done = gm.hold_guard_budget(rec, "canary")
    check("V-HOLDGUARD-WRITES-FILE", done == [sid] and ms.budget_path(sid).is_file(), str(done))
    d = json.loads(ms.budget_path(sid).read_text(encoding="utf-8"))
    check("V-HOLDGUARD-STOP-1-AND-MARKED", d["stop"] == 1 and d.get("hold") is True, str(d))
    check("V-HOLDGUARD-REAL-GUARD-DENIES-NEXT-CALL", call(sid, tx) == "deny", call(sid, tx))
    # RED branch: a worker the hold did not name stays allowed
    other = "hold-other-0002"
    check("V-HOLDGUARD-UNNAMED-SESSION-ALLOWED", call(other, tx) == "allow")
    # RED branch: an invalid sid is reported, never raised
    bad = gm.hold_guard_budget({"mission_id": "m-x", "owner": {"session_id": "bad sid!"}}, "r")
    check("V-HOLDGUARD-BAD-SID-REPORTED-NOT-RAISED", bad and bad[0].startswith("FAIL:"), str(bad))
    print(f"HOLDGUARD_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
