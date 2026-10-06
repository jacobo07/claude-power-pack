"""V-SBT-* gates: the session breaker meters the whole TREE (Gen3 T3 S2, 2026-10-05).

Origin: the TOK-18 Gen3 T2 canary passed its 42M cap while hooks/session_budget_guard.js read only
the parent transcript -- subagent transcripts (<sid>/subagents/agent-*.jsonl) carry the parent's
session id and were never summed (gen3_t2/T2-0.5-guard-subagent.md). Every gate below is one the
pre-T3 guard gets wrong, except the controls, which pin that nothing else moved.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_session_budget_guard import Box, GUARD, NODE, SID, U, kind, row  # noqa: E402

RUNNER = r"""
const g = require(process.argv[1]);
let raw = ''; process.stdin.on('data', d => raw += d).on('end', () => {
  const ev = JSON.parse(raw); const opts = JSON.parse(process.argv[2] || '{}');
  process.stdout.write(JSON.stringify({ out: g.decide(ev, opts) }));
});
"""

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate}: {ev}")


class Tree(Box):
    def __init__(self):
        super().__init__()
        self.kids = self.root / "t" / "subagents"
        self.kids.mkdir(parents=True)

    def child(self, name, text, age_s=0):
        p = self.kids / name
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(text)
        if age_s:
            t = time.time() - age_s
            os.utime(p, (t, t))
        return p

    def ask(self, tx=None, dispatch=False):
        ev = {"session_id": SID, "tool_name": "Agent" if dispatch else "Bash",
              "tool_input": {} if dispatch else {"command": "echo hi"}, "transcript_path": str(tx or self.tx)}
        p = subprocess.run([NODE, "-e", RUNNER, str(GUARD), json.dumps({"dispatch": dispatch})],
                           input=json.dumps(ev), capture_output=True, text=True, env=self.env(), timeout=60)
        if p.returncode != 0:
            return "CRASH:" + p.stderr[-300:], None
        out = json.loads(p.stdout)["out"]
        reason = ((out or {}).get("hookSpecificOutput") or {}).get("permissionDecisionReason", "")
        return kind(out), reason


def main():
    # V-SBT-TREE: the parent's call is judged on parent + child (pre-T3: 100, allow)
    t = Tree(); t.declare(); t.append(row("p1", U(100)))
    t.child("agent-a.jsonl", row("c1", U(2950)), age_s=600)
    k, _ = t.ask()
    s = t.st()
    check("V-SBT-TREE", k == "deny" and s["tokens"] == 3050, f"parent 100 + child 2950 > stop 3000 -> {k}, tokens {s['tokens']}")

    # V-SBT-CHILD-PATH: an event naming the CHILD transcript resolves to the same tree
    t = Tree(); t.declare(); t.append(row("p1", U(100)))
    kid = t.child("agent-a.jsonl", row("c1", U(400)))
    k, _ = t.ask(tx=kid)
    s = t.st()
    check("V-SBT-CHILD-PATH", s["tokens"] == 500 and s["caller"] == "agent-a.jsonl" and s["caller_tokens"] == 400,
          f"tokens {s['tokens']}, caller {s['caller']}, caller_tokens {s['caller_tokens']} -> {k}")

    # V-SBT-RESERVE: a RUNNING child's context is reserved before the parent's next call; a stale one is not
    t = Tree(); t.declare(); t.append(row("p1", U(1000)))
    t.child("agent-a.jsonl", row("c1", U(10, 0, 1490)))
    running, why = t.ask()
    t2 = Tree(); t2.declare(); t2.append(row("p1", U(1000)))
    t2.child("agent-a.jsonl", row("c1", U(10, 0, 1490)), age_s=600)
    stale, _ = t2.ask()
    check("V-SBT-RESERVE", running == "deny" and "reserve 1,500 for 1 running" in why and stale == "advise",
          f"2500 spent + 1500 in flight -> {running}; same child idle -> {stale}")

    # V-SBT-PER-CHILD: a child over its own envelope is stopped; the parent is not
    t = Tree(); t.declare(per_child_stop=500); t.append(row("p1", U(100)))
    kid = t.child("agent-a.jsonl", row("c1", U(600)), age_s=600)
    k_child, why = t.ask(tx=kid)
    k_parent, _ = t.ask()
    check("V-SBT-PER-CHILD", k_child == "deny" and "CHILD ENVELOPE" in why and k_parent == "allow",
          f"child 600 > 500 -> {k_child}; parent call -> {k_parent}")

    # V-SBT-DISPATCH: Agent dispatch holds the new child's reserve (parent kill switch)
    t = Tree(); t.declare(child_reserve=1500); t.append(row("p1", U(1000)))
    ok, _ = t.ask(dispatch=True)
    t.append(row("p2", U(600)))
    no, why = t.ask(dispatch=True)
    plain, _ = t.ask()
    check("V-SBT-DISPATCH", ok == "allow" and no == "deny" and "being dispatched" in why and plain == "allow",
          f"1000+1500 -> {ok}; 1600+1500 -> {no}; same spend, ordinary call -> {plain}")

    # V-SBT-CONTROL: no children -> identical to the legacy single-file meter
    t = Tree(); t.declare(); t.append(row("p1", U(500, o=1)))
    k, _ = t.ask()
    s = t.st()
    check("V-SBT-CONTROL", k == "allow" and s["tokens"] == 501 and s["reserve"] == 0 and s["caller"] == "root",
          f"{k}, tokens {s['tokens']}, reserve {s['reserve']}, caller {s['caller']}")

    print(f"SBT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
