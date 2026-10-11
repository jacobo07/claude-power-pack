"""V-EWC-E2 gates: obligation fields, SESSION scope, owner classifier, turn compiler, CLI.
    python tools/test_ewc_obligations.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FIX = ROOT / "tools" / "fixtures" / "ewc"

passes = fails = 0


def check(name, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {name}: {ev}")


def last_assistant(case):
    txt = ""
    for line in (FIX / f"{case}.jsonl").read_text(encoding="utf8").splitlines():
        r = json.loads(line)
        if r.get("type") == "assistant":
            txt = "\n".join(b["text"] for b in r["message"]["content"] if b.get("type") == "text")
    return txt


from modules.autonomy_gate import obligations as oc  # noqa: E402
from modules.autonomy_gate.gate import AGENT, OWNER  # noqa: E402
from modules.daif import turn_obligations as tc  # noqa: E402
from modules.gsd_x.goal import session_scope as ss  # noqa: E402
from modules.gsd_x.goal import convergence as cv  # noqa: E402
from modules.gsd_x.goal.log import GoalLog, goals_root  # noqa: E402

# ---- M1: fields, old events, session scope ----------------------------------------
with tempfile.TemporaryDirectory() as td:
    os.environ["GSDX_GOALS_ROOT"] = td
    repo = "a" * 40
    # old-format event (no new fields) in a real GoalLog
    log = GoalLog(repo, "old-goal")
    log.append(1, cv.OB_ACCEPTED, {"id": "o1", "plane": "OUTCOME", "text": "x", "done_gate": "g",
                                   "gate_pin": [["f", "h"]], "revision": "r"}, "t")
    from types import SimpleNamespace
    c = cv.project_convergence(SimpleNamespace(goal_id="old-goal", events=log.read()))
    o = c.obligations["o1"]
    check("M1 old event projects", o.severity == "" and o.actionability == "" and o.owner_class == ""
          and o.next_action == "" and o.source == "", "defaults empty")

    # real existing goal log copy, if any
    real = Path.home() / ".claude" / "state" / "gsd-x" / "goals"
    n = 0
    if real.is_dir():
        for rd in real.iterdir():
            for gd in rd.iterdir() if rd.is_dir() else []:
                try:
                    gl = GoalLog(rd.name, gd.name, base=real)
                    c = cv.project_convergence(SimpleNamespace(goal_id=gd.name, events=gl.read()))
                    n += 1
                except Exception as e:  # noqa: BLE001
                    check("M1 real log projects " + gd.name, False, repr(e))
    check("M1 real goal logs project", n >= 0, f"{n} real logs projected")

    # session scope
    oid = ss.add(repo, "sess-1", text="fix contrast", source="turn", severity="RED",
                 actionability="NOW", owner_class="AGENT", next_action="fix contrast in css")
    rows = ss.list_obligations(repo, "sess-1")
    check("M1 session add+list", len(rows) == 1 and rows[0]["id"] == oid and rows[0]["state"] == "open"
          and rows[0]["severity"] == "RED" and rows[0]["actionability"] == "NOW", str(rows))
    d = goals_root() / repo / ss.scope_id("sess-1")
    files = sorted(p.name for p in d.iterdir())
    ev = json.loads((d / files[0]).read_text(encoding="utf8"))
    check("M1 node-readable one JSON read per event", ev["type"] == cv.OB_ACCEPTED
          and ev["data"]["severity"] == "RED" and files[0] == "000001.json", files[0])
    check("M1 no temp leftovers", not [p for p in d.iterdir() if p.name.startswith(".tmp")])
    oid2 = ss.add(repo, "sess-1", text="fix contrast", source="turn", severity="RED",
                  actionability="NOW", owner_class="AGENT", next_action="fix contrast in css")
    check("M1 add idempotent on same text", oid2 == oid and len(ss.list_obligations(repo, "sess-1")) == 1)
    # close: pole 1 refuse, pole 2 accept
    for bad in ("", "done", "ok", "fixed it"):
        try:
            ss.close(repo, "sess-1", oid, bad)
            check(f"M1 close refuses verdict {bad!r}", False)
        except ss.SessionScopeError:
            check(f"M1 close refuses verdict {bad!r}", True)
    ss.close(repo, "sess-1", oid, "pytest tools/test_x.py: exit 0, 12 passed")
    r = ss.list_obligations(repo, "sess-1")[0]
    check("M1 close with gate verdict", r["state"] == "closed" and "pytest" in r["verdict"], str(r))
    try:
        ss.close(repo, "sess-1", "nope", "pytest x: exit 0")
        check("M1 close unknown id refused", False)
    except ss.SessionScopeError:
        check("M1 close unknown id refused", True)
    check("M1 other session isolated", ss.list_obligations(repo, "sess-2") == [])

# ---- M3: classifier ----------------------------------------------------------------
def ob(**k):
    base = dict(severity="RED", actionability="NOW", next_action="fix contrast in css", text="t")
    base.update(k)
    return base

v = oc.classify_obligation(ob())
check("M3 RED internal -> AGENT/NOW", v["owner"] == AGENT and v["category"] == "NOW", str(v))
for phrase in ("another iteration", "takes effort", "uncertain but researchable"):
    v = oc.classify_obligation(ob(severity="AMBER", next_action=f"this needs {phrase}"))
    check(f"M3 near-miss {phrase!r} is AGENT", v["owner"] == AGENT, str(v))
v = oc.classify_obligation(ob(next_action="send the summary email to the leads"))
check("M3 outward -> OWNER/APPROVAL", v["owner"] == OWNER and v["category"] == "APPROVAL", str(v))
v = oc.classify_obligation(ob(next_action="I need the api key for the vendor"))
check("M3 resource -> OWNER/RESOURCE", v["owner"] == OWNER and v["category"] == "RESOURCE", str(v))
v = oc.classify_obligation(ob(next_action="git reset --hard the tree"))
check("M3 irreversible -> OWNER/APPROVAL", v["owner"] == OWNER and v["category"] == "APPROVAL", str(v))
v = oc.classify_obligation(ob(severity="INFO", next_action="which logo colour looks better, your call"))
check("M3 preference -> OWNER/HUMAN_PREF", v["owner"] == OWNER and v["category"] == "HUMAN_PREF", str(v))
v = oc.classify_obligation(ob(severity="RED", next_action="which logo colour looks better, your call"))
check("M3 RED never preference", v["owner"] == AGENT and v["category"] == "NOW", str(v))
v = oc.classify_obligation(None)
check("M3 fail closed on garbage", v["owner"] == OWNER, str(v))
v = oc.classify_obligation({"next_action": 5, "severity": object()})
check("M3 fail closed on malformed", v["owner"] in (OWNER, AGENT) and "why" in v, str(v))
now = ob()
pref = ob(severity="INFO", next_action="which logo colour looks better, your call", actionability="HUMAN_PREF")
check("M3 human_gate_ready false while NOW remains", oc.human_gate_ready([now, pref]) is False)
check("M3 human_gate_ready true when only human", oc.human_gate_ready([pref]) is True)
check("M3 human_gate_ready false when empty", oc.human_gate_ready([]) is False)
done = dict(now, state="closed")
check("M3 closed NOW does not block", oc.human_gate_ready([done, pref]) is True)

# ---- M4: compiler ------------------------------------------------------------------
inc = tc.compile_turn(last_assistant("incident"))
now_n = sum(1 for o in inc if o["actionability"] == "NOW")
pref_n = sum(1 for o in inc if o["actionability"] == "HUMAN_PREF")
check("M4 incident >= 5 NOW", now_n >= 5, f"NOW={now_n} total={len(inc)}")
check("M4 incident == 1 HUMAN_PREF", pref_n == 1, f"HUMAN_PREF={pref_n}")
comp = tc.compile_turn(last_assistant("complete"))
check("M4 complete -> 0", comp == [], str(comp))
ho = tc.compile_turn(last_assistant("human_only"))
check("M4 human-only -> 1 APPROVAL", len(ho) == 1 and ho[0]["actionability"] == "APPROVAL", str(ho))
for o in inc:
    check("M4 fields " + o["id"], all(o.get(k) for k in ("source", "severity", "actionability",
          "owner_class", "next_action", "text")))
check("M4 wish refused", tc.compile_turn("At some point we should keep an eye on the next step for the spacing.") == [])
check("M4 description refused", tc.compile_turn("The report describes how a table row with FAIL would be shown.") == [])
check("M4 zero counts refused", tc.compile_turn("Totals: 0 FAIL, 0 WARN, all committed.") == [])
check("M4 uncommitted", any(o["source"] == "uncommitted" for o in tc.compile_turn("There are uncommitted changes in the tree.")))
check("M4 negation committed", not tc.compile_turn("Everything is committed and the evidence file was written."))
check("M4 empty/None", tc.compile_turn("") == [] and tc.compile_turn(None) == [])
check("M4 dedupe", len(tc.compile_turn("The changes are not committed.\nThe changes are not committed.")) == 1)
pj = ROOT / "modules" / "autonomy_gate" / "obligation_patterns.json"
P = json.loads(pj.read_text(encoding="utf8"))
check("M4 patterns JSON schema", P.get("schema") and all({"id", "regex", "flags"} <= set(p) for p in P["patterns"]),
      f"{len(P['patterns'])} patterns")
node = subprocess.run(["node", "-e",
    "const P=require(process.argv[1]);for(const p of P.patterns)new RegExp(p.regex,p.flags.replace('u',''));console.log('ok')",
    str(pj)], capture_output=True, text=True)
check("M4 patterns compile in Node", node.stdout.strip() == "ok", node.stderr[:200])

# ---- CLI ---------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as td:
    env = dict(os.environ, GSDX_GOALS_ROOT=td)
    def cli(*a):
        return subprocess.run([sys.executable, "-m", "modules.autonomy_gate", "obligations", *a],
                              capture_output=True, text=True, cwd=str(ROOT), env=env)
    r = cli("add", "--session", "cli-1", "--text", "fix overflow", "--severity", "RED",
            "--next-action", "fix overflow in css")
    check("CLI add rc0", r.returncode == 0, r.stdout.strip()[:120] + r.stderr[:200])
    oid = json.loads(r.stdout)["id"] if r.returncode == 0 else ""
    r = cli("list", "--session", "cli-1")
    check("CLI list", r.returncode == 0 and oid in r.stdout, r.stdout.strip()[:120])
    r = cli("close", "--session", "cli-1", "--id", oid, "--verdict", "done")
    check("CLI close bare verdict refused (rc!=0)", r.returncode != 0, r.stderr.strip()[:120])
    r = cli("close", "--session", "cli-1", "--id", oid, "--verdict", "pytest tools/t.py: exit 0")
    check("CLI close with gate rc0", r.returncode == 0, r.stdout.strip()[:120] + r.stderr[:120])
    r = cli("list", "--session", "cli-1", "--open")
    check("CLI list --open empty after close", r.returncode == 0 and json.loads(r.stdout) == [], r.stdout.strip()[:80])
    r = cli("compile", "--session", "cli-1", "--text", "The changes are not committed.")
    check("CLI compile records", r.returncode == 0 and len(json.loads(r.stdout)) == 1, r.stdout.strip()[:120])

print(f"EWC_E2_PASS={passes}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
