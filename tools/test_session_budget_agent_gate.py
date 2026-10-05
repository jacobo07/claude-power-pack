"""V-SBGA-* gates: session_budget_guard denies an Agent spawn the envelope left cannot pay for.

Origin: Live QA W0 (m-8bbdf725cd52, 2026-10-05): four GSD subagents spent 41.8M inside a 4M envelope,
each re-reading an ~85k floor per call. The guard now charges a spawn its type's measured floor x
default_min_calls (vault/config/route-floors.json) against stop - processed. Every deny has an
allowed control. Driven through the STANDALONE stdin entry -- the path a `Agent|Task` registration
runs -- so the entry itself is under test, not only decide().
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
sys.path.insert(0, str(HERE))
import mission_spend as ms  # noqa: E402

# Mutation drill: SBGA_GUARD_DRILL = a mutated copy of the guard; it is pointed at the repo's table.
DRILL = os.environ.get("SBGA_GUARD_DRILL")
GUARD = Path(DRILL) if DRILL else PP / "hooks" / "session_budget_guard.js"
FLOORS_FILE = PP / "vault" / "config" / "route-floors.json"
FLOORS = json.loads(FLOORS_FILE.read_text(encoding="utf-8"))
NODE = shutil.which("node") or "node"
SID = "sbga-test-0001"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


class Box:
    def __init__(self, spent: int, stop: int = 1_000_000, declare: bool = True):
        self.root = Path(tempfile.mkdtemp(prefix="sbga_"))
        self.state = self.root / "state"
        self.state.mkdir()
        self.tx = self.root / "t.jsonl"
        self.tx.write_text(json.dumps({"type": "assistant", "timestamp": "2026-10-06T10:00:00Z", "message": {
            "id": "m1", "model": "claude-sonnet-5-5", "content": [{"type": "text", "text": "x"}],
            "usage": {"input_tokens": spent, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
                      "output_tokens": 0}}}) + "\n", encoding="utf-8")
        if declare:
            old = os.environ.get("GSD_LONG_RUN_STATE_DIR")
            os.environ["GSD_LONG_RUN_STATE_DIR"] = str(self.state)
            try:
                ms.declare(SID, target=stop // 2, warn=stop, stop=stop, noprogress_calls=10**6)
            finally:
                if old is None:
                    os.environ.pop("GSD_LONG_RUN_STATE_DIR")
                else:
                    os.environ["GSD_LONG_RUN_STATE_DIR"] = old

    def call(self, tool="Agent", tool_input=None, raw=None, **env):
        ev = {"session_id": SID, "hook_event_name": "PreToolUse", "tool_name": tool,
              "tool_input": tool_input if tool_input is not None else {}, "transcript_path": str(self.tx)}
        e = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(self.state))
        e.pop("CPP_SESSION_BUDGET", None)
        e.pop("CPP_ROUTE_FLOORS", None)          # the guard's own default path is what runs live
        if DRILL:
            e["CPP_ROUTE_FLOORS"] = str(FLOORS_FILE)
        e.update(env)
        p = subprocess.run([NODE, str(GUARD)], input=raw if raw is not None else json.dumps(ev),
                           capture_output=True, text=True, env=e, timeout=60)
        out = json.loads(p.stdout) if p.stdout.strip() else None
        return p.returncode, out


def kind(out):
    h = (out or {}).get("hookSpecificOutput") or {}
    if h.get("permissionDecision") == "deny":
        return "deny"
    return "advise" if h.get("additionalContext") else "allow"


def reason(out):
    return ((out or {}).get("hookSpecificOutput") or {}).get("permissionDecisionReason") or ""


def main() -> int:
    p = FLOORS["profiles"]
    k = FLOORS["default_min_calls"]
    # 800k of a 1M stop spent: 200k left
    b = Box(800_000)
    rc, out = b.call(tool_input={"subagent_type": "gsd-executor"})
    check("V-SBGA-EXECUTOR-DENIED", rc == 0 and kind(out) == "deny" and f"{p['gsd-executor']['floor']:,}" in reason(out),
          f"{p['gsd-executor']['floor']:,} x {k} = {p['gsd-executor']['floor'] * k:,} > 200,000: {reason(out)[:140]}")
    rc, out = b.call(tool_input={"subagent_type": "Explore"})
    check("V-SBGA-EXPLORE-CONTROL", kind(out) == "allow", f"{p['Explore']['floor'] * k:,} <= 200,000 -> {kind(out)}")
    rc, out = b.call(tool_input={})
    check("V-SBGA-DEFAULT-TYPE-IS-GENERAL", kind(out) == "deny" and "general-purpose" in reason(out), reason(out)[:120])
    rc, out = b.call(tool="Task", tool_input={"subagent_type": "gsd-planner"})
    check("V-SBGA-OLD-TOOL-NAME", kind(out) == "deny", "Task is judged like Agent (rename-proof)")
    rc, out = b.call(tool="Bash", tool_input={"command": "echo hi"})
    check("V-SBGA-NON-AGENT-CONTROL", kind(out) == "allow", f"same envelope, Bash -> {kind(out)}")

    top = max(v["floor"] for v in p.values())
    rc, out = b.call(tool_input={"subagent_type": "never-measured"})
    check("V-SBGA-UNMEASURED-CHARGED-MAX", kind(out) == "deny" and "unmeasured" in reason(out) and f"{top:,}" in reason(out),
          reason(out)[:140])
    roomy = Box(1_000_000 - top * k)          # exactly the highest floor x k left
    rc, out = roomy.call(tool_input={"subagent_type": "never-measured"})
    check("V-SBGA-UNMEASURED-CONTROL", kind(out) == "allow", f"{top * k:,} left -> {kind(out)}")
    rc, out = roomy.call(tool_input={"subagent_type": "never-measured"}, CPP_ROUTE_FLOORS=str(b.root / "nope.json"))
    check("V-SBGA-TABLE-UNREADABLE-ADVISES", kind(out) == "advise", "named, never a silent allow or a guessed deny")

    rc, out = Box(800_000, declare=False).call(tool_input={"subagent_type": "gsd-executor"})
    check("V-SBGA-NO-ENVELOPE-INERT", rc == 0 and out is None)
    rc, out = b.call(tool_input={"subagent_type": "gsd-executor"}, CPP_SESSION_BUDGET="off")
    check("V-SBGA-KILL-SWITCH", out is None)
    rc, out = b.call(raw="{not json")
    check("V-SBGA-ENTRY-FAILS-OPEN", rc == 0 and out is None, f"rc {rc}")

    # --- review F1: subagent spend lives in <transcript>/subagents/, never in the parent file ---------
    def usage_row(mid, n, model="claude-sonnet-5-5", ts="2026-10-06T10:01:00Z"):
        return json.dumps({"type": "assistant", "timestamp": ts, "message": {"id": mid, "model": model,
                           "usage": {"input_tokens": 0, "cache_creation_input_tokens": 0,
                                     "cache_read_input_tokens": n, "output_tokens": 0}}}) + "\n"

    ctl = Box(100_000)
    rc, out = ctl.call(tool_input={"subagent_type": "gsd-executor"})
    check("V-SBGA-SUB-CONTROL", kind(out) == "allow", "parent 100k, no subagents: 900k left -> allow")
    s = Box(100_000)
    sd = s.root / "t" / "subagents"
    sd.mkdir(parents=True)
    (sd / "agent-a.jsonl").write_text(usage_row("a1", 700_000) + usage_row("a1", 700_000)       # streamed dup
                                      + usage_row("syn", 999_999, model="<synthetic>"), encoding="utf-8")
    (sd / "agent-a.meta.json").write_text('{"agentType": "gsd-executor"}', encoding="utf-8")   # not a transcript
    rc, out = s.call(tool_input={"subagent_type": "gsd-executor"})
    st = json.loads((s.state / f"session-budget-{SID}.state.json").read_text(encoding="utf-8"))
    ref = ms._file_tokens(s.tx, None) + ms._file_tokens(sd / "agent-a.jsonl", None)
    check("V-SBGA-SUB-SPEND-COUNTED", kind(out) == "deny" and st["tokens"] == ref == 800_000 and st["sub_tokens"] == 700_000,
          f"js {st['tokens']:,} (sub {st.get('sub_tokens')}) py {ref:,}: {reason(out)[:90]}")
    with open(sd / "agent-a.jsonl", "a", encoding="utf-8") as fh:
        fh.write(usage_row("a2", 50_000))
    s.call(tool="Bash", tool_input={"command": "echo"})
    st2 = json.loads((s.state / f"session-budget-{SID}.state.json").read_text(encoding="utf-8"))
    check("V-SBGA-SUB-INCREMENTAL", st2["tokens"] == 850_000, f"{st2['tokens']:,} after +50k (no re-count)")
    (sd / "agent-b.jsonl").write_text(usage_row("b1", 200_000), encoding="utf-8")
    rc, out = s.call(tool="Bash", tool_input={"command": "echo"})
    check("V-SBGA-SUB-STOP-BREAKER", kind(out) == "deny" and "1,050,000" in reason(out),
          f"a second subagent pushes processed past stop for a NON-agent call: {reason(out)[:80]}")

    print(f"SBGA_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
