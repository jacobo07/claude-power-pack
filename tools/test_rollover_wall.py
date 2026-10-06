"""V-RWALL-* gates: the interactive rollover wall is judged MID-TURN, not only at Stop.

Measured 2026-09-29, session f8ea8727 (CostaLuz pane): the last turn that ENDED closed at
381k tokens (~38 %). The Owner answered `y` at 16:09:36 and the next turn ran for 3+ hours
in auto mode with agents, growing to 688k (~69 %), and never reached Stop before it was
interrupted. context-watchdog.py is a Stop hook, so the 45 % wall was never judged: no
/kclear, no /clear, no /kresume, and zero ledger rows for the session.

hooks/rollover_wall.js is the interactive twin of mission_wall.js: an in-process member of
the dispatcher's PostToolUse-default lane that reads the same metrics bridge and the same
thresholds as the watchdog and, past the wall, returns decision:"block" so the model is told
mid-turn to finish the step in hand and END the turn -- the Stop that follows runs the
normal rollover chain. Re-asked every REASK_STEP_PCT points, like mission_wall (a single
notice was ignored for 3.5 h there).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
HOOK = Path(os.environ.get("RWALL_TEST_HOOK") or PP / "hooks" / "rollover_wall.js")
WATCHDOG = PP / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"
DISPATCHERS = [PP / "hooks" / "hook-dispatcher.js", Path.home() / ".claude" / "hooks" / "hook-dispatcher.js"]

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


class Box:
    """One isolated world: temp dir for the metrics bridge, state dir for flags/markers."""

    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="rwall_"))
        self.tmp = self.root / "tmp"
        self.state = self.root / "state"
        self.tmp.mkdir()
        self.state.mkdir()

    def env(self, **extra):
        e = dict(os.environ, TEMP=str(self.tmp), TMP=str(self.tmp),
                 GSD_LONG_RUN_STATE_DIR=str(self.state), GSD_AUTORUN_MARKER_DIR=str(self.state))
        e.pop("CPP_ROLLOVER_ACTIVE", None)
        e.pop("CTXWD_TEST_THRESHOLDS", None)
        e.update(extra)
        return e

    def used(self, sid, pct):
        (self.tmp / f"claude-ctx-{sid}.json").write_text(
            json.dumps({"session_id": sid, "used_pct": pct, "remaining_percentage": 100 - pct}), encoding="utf-8")

    def decide(self, sid="sess-1", **extra):
        js = ("const h=require(process.argv[1]);"
              "process.stdout.write(JSON.stringify(h.decide({session_id:process.argv[2],"
              "hook_event_name:'PostToolUse',tool_name:'Edit'})||null));")
        r = subprocess.run(["node", "-e", js, str(HOOK), sid], env=self.env(**extra),
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print(f"HARNESS-FAILED: hook did not run rc={r.returncode} err={r.stderr[-300:]!r}")
            sys.exit(2)
        return json.loads(r.stdout or "null")


def reason(out):
    return (out or {}).get("reason", "") if isinstance(out, dict) else ""


def main() -> int:
    # --- the wall, from both poles --------------------------------------------------
    b = Box()
    b.used("sess-1", 44)
    check("V-RWALL-BELOW-SILENT", b.decide() is None, "44 % < 45 %")

    b.used("sess-1", 46)
    out = b.decide()
    check("V-RWALL-AT-WALL-BLOCKS",
          isinstance(out, dict) and out.get("decision") == "block"
          and "CONTEXT WALL" in reason(out) and "46%" in reason(out)
          and "END this turn" in reason(out) and "/compact" in reason(out)
          # 2026-10-06: the notice must ask the model to seal (/kclear) itself; without it
          # the Stop finds no capsule and the rollover strands.
          and 'skill: "kclear"' in reason(out) and "invoke the kclear skill NOW" in reason(out),
          f"out={out}")

    check("V-RWALL-ONCE-PER-CROSSING", b.decide() is None, "same 46 % again -> silent")

    b.used("sess-1", 48)
    check("V-RWALL-NO-REASK-BELOW-STEP", b.decide() is None, "48 % is < 46+3")

    b.used("sess-1", 49)
    out = b.decide()
    check("V-RWALL-REASKS-PAST-STEP", "NOTICE 2" in reason(out), f"reason={reason(out)[:120]!r}")

    # A fresh context (after /clear the same pane is a new session id, but a /compact keeps
    # it): below the rearm floor the crossing is forgotten, and the next one notices again.
    b.used("sess-1", 29)
    check("V-RWALL-REARM-SILENT", b.decide() is None, "29 % < rearm 30 %")
    b.used("sess-1", 46)
    out = b.decide()
    check("V-RWALL-REARMED-NOTICES-AGAIN",
          "CONTEXT WALL" in reason(out) and "NOTICE" not in reason(out), f"reason={reason(out)[:120]!r}")

    # --- who it must leave alone ------------------------------------------------------
    b = Box()
    b.used("sess-m", 60)
    (b.state / "gsd-autorun-sess-m.json").write_text(json.dumps({"mission_id": "m-1", "epoch": 1}), encoding="utf-8")
    check("V-RWALL-MISSION-LEFT-TO-MISSION-WALL", b.decide("sess-m") is None, "mission marker present")

    b = Box()
    b.used("sess-1", 60)
    check("V-RWALL-KILL-SWITCH", b.decide(CPP_ROLLOVER_ACTIVE="0") is None, "CPP_ROLLOVER_ACTIVE=0")

    b = Box()
    check("V-RWALL-NO-METRICS-SILENT", b.decide() is None, "no bridge file")

    b = Box()
    b.used("../../x", 60)
    check("V-RWALL-BAD-SID-SILENT", b.decide("../../x") is None, "path-like session id")

    # --- the same wall as the watchdog --------------------------------------------------
    b = Box()
    b.used("sess-1", 50)
    (b.state / "ctxwd-thresholds-sess-1.json").write_text(
        json.dumps({"snapshot": 55, "advisory": 60, "rearm": 35}), encoding="utf-8")
    check("V-RWALL-SESSION-THRESHOLDS-HONOURED", b.decide() is None, "advisory 60 from the session file")

    b = Box()
    b.used("sess-1", 50)
    (b.state / "ctxwd-thresholds-sess-1.json").write_text(
        json.dumps({"snapshot": 55, "advisory": 60, "rearm": 10}), encoding="utf-8")
    check("V-RWALL-INVALID-THRESHOLDS-FALL-BACK", "CONTEXT WALL" in reason(b.decide()),
          "rearm 10 < floor 28 is refused, as in valid_thresholds()")

    b = Box()
    b.used("sess-1", 38)
    check("V-RWALL-ENV-THRESHOLDS", "CONTEXT WALL" in reason(b.decide(CTXWD_TEST_THRESHOLDS="31,36,30")),
          "CTXWD_TEST_THRESHOLDS=31,36,30")

    src = WATCHDOG.read_text(encoding="utf-8")
    want = {k: int(re.search(rf"^{k} = (\d+)", src, re.M).group(1))
            for k in ("THRESHOLD_ADVISORY_PCT", "THRESHOLD_REARM_PCT", "REARM_FLOOR_PCT")}
    got = json.loads(subprocess.run(
        ["node", "-e", "const h=require(process.argv[1]);process.stdout.write(JSON.stringify("
         "{THRESHOLD_ADVISORY_PCT:h.ADVISORY_PCT,THRESHOLD_REARM_PCT:h.REARM_PCT,REARM_FLOOR_PCT:h.REARM_FLOOR_PCT}))",
         str(HOOK)], capture_output=True, text=True, timeout=60).stdout or "{}")
    check("V-RWALL-CONSTANTS-MATCH-WATCHDOG", got == want, f"hook={got} watchdog={want}")

    # --- wired, and reachable through the real dispatcher ------------------------------------
    for d in DISPATCHERS:
        text = d.read_text(encoding="utf-8") if d.exists() else ""
        lane = text[text.find("'PostToolUse-default': ["):]
        lane = lane[:lane.find("],")]
        check(f"V-RWALL-REGISTERED ({d.parent.name}/{d.name})",
              "'../skills/claude-power-pack/hooks/rollover_wall.js'" in lane, f"lane_len={len(lane)}")

    b = Box()
    b.used("sess-e2e", 47)
    payload = json.dumps({"session_id": "sess-e2e", "hook_event_name": "PostToolUse", "tool_name": "Edit",
                          "tool_input": {}, "tool_response": {}, "cwd": str(b.root)})
    live = DISPATCHERS[1]
    r = subprocess.run(["node", str(live), "--event=PostToolUse-default"], input=payload,
                       env=b.env(CLAUDE_STATE_DIR=str(b.state)), capture_output=True, text=True, timeout=120)
    check("V-RWALL-E2E-LIVE-DISPATCHER", "CONTEXT WALL" in (r.stdout or "") and "47%" in (r.stdout or ""),
          f"rc={r.returncode} out={(r.stdout or '')[:200]!r} err={(r.stderr or '')[-160:]!r}")

    total = passes + fails
    print(f"RWALL_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
