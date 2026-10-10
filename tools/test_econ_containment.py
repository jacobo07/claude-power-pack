"""V-ECON-* gates: economic failure containment (vault/plans/econ-containment-2026-10-10.md).

Origin: ctx-same-pane, 2026-10-10. Two panes bound by cwd to a 16M goal reached 18,072,474
used+reserved. The second pane bound itself 50 minutes after the cap was crossed; every Owner message
bought ~200K to be refused, the escape (cd, another shell) was refused by the same guard, and the
"one final reply per pane" re-armed after every settle. These gates drive the real ledger, the real
PreToolUse guard and the real UserPromptSubmit admission hook. Every refusal has a control in which
the same input fits and is admitted: a gate that refuses everything passes every refusal assertion.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PP))
import mission_spend as ms  # noqa: E402
import test_goal_budget_admission as tga  # noqa: E402
from modules.provider_routing.ledger import GoalLedger  # noqa: E402

ADMISSION = PP / "hooks" / "econ_admission.js"
NODE = tga.NODE

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def led(goal):
    return GoalLedger(ms.goal_root() / goal, goal)


def journal(goal):
    p = ms.goal_root() / goal / "spend.journal.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def bind(sid, goal, source="explicit"):
    p = ms.binding_path(sid)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"goal": goal, "since_ts": "2000-01-01T00:00:00", "source": source, "pid": 0}),
                 encoding="utf-8")


def admit(e, sid, prompt, cwd):
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(e.state))
    env.pop("CPP_ECON_ADMISSION", None)
    p = subprocess.run([NODE, str(ADMISSION)], input=json.dumps({"session_id": sid, "prompt": prompt, "cwd": str(cwd),
                       "hook_event_name": "UserPromptSubmit"}), capture_output=True, text=True, env=env, timeout=60)
    try:
        return json.loads(p.stdout or "{}")
    except ValueError:
        return {"_raw": p.stdout, "_err": p.stderr}


def exhaust(goal, sid, cap=1000):
    """Bind `sid`, lease once, then cross the cap: the first refusal."""
    led(goal).renew(sid, 0, 600, per_call=100)
    return led(goal).renew(sid, cap + 200, 600, per_call=100)


def g_ledger(e):
    tga.declare("t1", 1000, lease_calls=1)
    out = exhaust("t1", "A")
    j = journal("t1")
    tomb = [r for r in j if r["op"] == "tombstone" and r["sid"] == "A"]
    exh = [r for r in j if r["op"] == "exhausted"]
    check("V-ECON-TOMBSTONE-ON-REFUSAL", not out["ok"] and len(tomb) == 1 and len(exh) == 1 and out["exhausted"],
          f"first refusal writes tombstone {len(tomb)} + exhausted {len(exh)}: {out['reason'][:60]}")
    finals0 = [r for r in j if r["op"] == "reserve" and r.get("kind") == "final"]
    for m in (1400, 1600, 1800):                   # three more refused boundaries, each really billed
        r = led("t1").renew("A", m, 600, per_call=100)
    j = journal("t1")
    finals = [r for r in j if r["op"] == "reserve" and r.get("kind") == "final"]
    marks = led("t1")._gfold(led("t1")._read())["marks"]
    check("V-ECON-FINAL-ONCE", len(finals0) == 1 and len(finals) == 1 and r.get("tombstoned_sid"),
          f"final reserves before/after 3 more refusals: {len(finals0)}/{len(finals)} (re-arm was the amplifier)")
    check("V-ECON-REFUSED-BILLED-TRUTH", marks.get("A") == 1800,
          f"refused boundaries still settle at the measured truth: mark {marks.get('A')}")
    tga.declare("t1c", 100000, lease_calls=1)
    ctl = led("t1c").renew("A", 0, 600, per_call=100)
    check("V-ECON-LEDGER-CONTROL", ctl["ok"] and not ctl["exhausted"], "the same renew on a goal with room is admitted")


def g_guard(e):
    work, other = e.root / "w2", e.root / "o2"
    work.mkdir()
    other.mkdir()
    tga.declare("t2", 1000, roots=[str(work)], lease_calls=1)
    exhaust("t2", "OLD")
    tx = e.root / "t2.jsonl"
    tx.write_text(tga.row("m1", 100), encoding="utf-8")
    n0 = len(journal("t2"))

    dec, why = tga.run_guard(e, "NEW", tx, work, tool="Write", tool_input={"file_path": str(work / "x.py")})
    check("V-ECON-QUARANTINE-FENCE", dec == "deny" and "ECONOMIC FENCE (t2)" in why
          and not ms.binding_path("NEW").exists() and len(journal("t2")) == n0,
          f"a fresh pane in an exhausted goal's worktree: no bind, no renew, mutation fenced: {why[:70]}")
    dec, why = tga.run_guard(e, "NEW", tx, work, tool="Read", tool_input={"file_path": str(work / "x.py")})
    check("V-ECON-QUARANTINE-READ-FREE", dec is None and len(journal("t2")) == n0, "reads stay free and unbilled")
    dec, why = tga.run_guard(e, "NEW", tx, work, tool="Write", tool_input={"file_path": str(other / "y.py")})
    check("V-ECON-QUARANTINE-ELSEWHERE", dec is None, "a change outside the exhausted workspace is not fenced")

    w3 = e.root / "w3"
    w3.mkdir()
    tga.declare("t3", 10_000_000, roots=[str(w3)], lease_calls=1)
    dec, why = tga.run_guard(e, "FRESH", tx, w3, tool="Write", tool_input={"file_path": str(w3 / "x.py")})
    check("V-ECON-QUARANTINE-CONTROL", dec is None and (ms.read_binding("FRESH") or {}).get("goal") == "t3",
          "the same call in a goal with room binds and is admitted")

    bind("OLD", "t2", "cwd")
    cmd = f'python "{HERE / "econ_plane.py"}" status --session OLD'
    dec, why = tga.run_guard(e, "OLD", tx, work, tool="PowerShell", tool_input={"command": cmd})
    check("V-ECON-EGRESS-EXEMPT", dec is None, "status of a tombstoned session never needs the exhausted goal's authority")
    dec, why = tga.run_guard(e, "OLD", tx, work, tool="PowerShell", tool_input={"command": cmd + "; Remove-Item x"})
    check("V-ECON-EGRESS-ANCHORED", dec == "deny", "a chained command does not ride the exemption")
    dec, why = tga.run_guard(e, "OLD", tx, work, tool="Bash", tool_input={"command": "cd /c/elsewhere"})
    check("V-ECON-TOMBSTONED-GUARD", dec == "deny" and ("TOMBSTONED" in why or "FENCE" in why) and "econ detach" in why,
          f"an ordinary call from the tombstoned pane is refused and names the zero-cost exit: {why[:60]}")

    bind("CW", "t3")
    dec, why = tga.run_guard(e, "CW", tx, other, tool="Write", tool_input={"file_path": str(other / "z.py")})
    rec = ms.read_binding("CW")
    check("V-ECON-CWD-CANARY", rec["goal"] == "t3" and rec.get("gen", 1) == 1,
          "a session's economic identity does not follow its working directory")
    dec, why = tga.run_guard(e, "CW", tx, other, tool="Write",
                             tool_input={"file_path": str(e.state / "goal-binding" / "CW.g2.json")})
    check("V-ECON-BINDING-STATE-PROTECTED", dec == "deny", "a bound session cannot write its own binding generation")


def g_admission(e):
    work = e.root / "w4"
    work.mkdir()
    tga.declare("t4", 1000, roots=[str(work)], lease_calls=1)
    exhaust("t4", "T4")
    bind("T4", "t4", "cwd")
    n0 = len(journal("t4"))
    outs = [admit(e, "T4", f"please continue {i}", work) for i in range(5)]
    blocked = [o.get("decision") == "block" and "NOT sent to the model" in (o.get("reason") or "") for o in outs]
    check("V-ECON-PRE-MODEL-BLOCK", all(blocked) and len(journal("t4")) == n0,
          f"5 Owner messages to a tombstoned pane: blocked {sum(blocked)}/5 before the model, journal unchanged")
    st = admit(e, "T4", "econ status", work)
    check("V-ECON-STATUS-ZERO-MODEL", st.get("decision") == "block" and "used" in st.get("reason", "")
          and "TOMBSTONED" in st.get("reason", ""), st.get("reason", "")[:80].replace("\n", " | "))
    tga.declare("t5", 10_000_000, lease_calls=1)
    bind("T5", "t5")
    led("t5").renew("T5", 0, 600, per_call=100)
    check("V-ECON-ADMISSION-CONTROL", admit(e, "T5", "please continue", work) == {}, "a session with room passes untouched")
    check("V-ECON-ADMISSION-UNBOUND", admit(e, "NOBODY", "hello", work) == {}, "an unbound session passes untouched")


def g_detach(e):
    work, other = e.root / "w6", e.root / "o6"
    work.mkdir()
    other.mkdir()
    tga.declare("t6", 10_000_000, roots=[str(work)], lease_calls=1)
    bind("D6", "t6", "cwd")
    led("t6").renew("D6", 500, 600, per_call=100)
    out = admit(e, "D6", "econ detach", work)
    rec = ms.read_binding("D6")
    g = led("t6")._gfold(led("t6")._read())
    check("V-ECON-DETACH", out.get("decision") == "block" and "left goal t6" in out.get("reason", "")
          and rec["goal"] == "none" and rec["gen"] == 2 and rec["fenced"] == ["t6"] and "D6" in g["tombs"]
          and not any(r["hold"] for r in g["res"].values() if r["sid"] == "D6"),
          f"detach: gen {rec.get('gen')} goal {rec.get('goal')} fenced {rec.get('fenced')}, holds closed, tombstoned")
    tx = e.root / "t6.jsonl"
    tx.write_text(tga.row("m1", 100), encoding="utf-8")
    dec, why = tga.run_guard(e, "D6", tx, other, tool="Edit", tool_input={"file_path": str(work / "a.py")})
    check("V-ECON-NO-SESSION-LAUNDERING", dec == "deny" and "detached" in why,
          "a detached pane cannot keep changing the goal it left, even from another directory")
    dec, why = tga.run_guard(e, "D6", tx, other, tool="Edit", tool_input={"file_path": str(other / "a.py")})
    check("V-ECON-DETACH-CONTROL", dec is None, "the detached pane works freely outside the fenced workspace")
    first = ms.read_binding("D6")
    check("V-ECON-PY-TWIN-GENERATIONS", first["gen"] == 2 and ms.binding_path("D6").exists(),
          "generation 1 is never edited; the Python twin reads the highest generation")


def g_successor(e):
    work = e.root / "w7"
    work.mkdir()
    tga.declare("t7", 1000, roots=[str(work)], lease_calls=1)
    exhaust("t7", "OLD7")
    bind("OLD7", "t7", "cwd")
    check("V-ECON-PY-TWIN-QUARANTINE", (ms.resolve_binding({"cwd": str(work), "tool_name": "Write",
                                                            "tool_input": {"file_path": "x"}}, "Q7") or {}).get("quarantine"),
          "mission_spend.resolve_binding never binds to an exhausted goal either")
    l7 = led("t7")
    l7.set_programme(5000, "test owner", inside_agent=False)
    so = l7.lease_open("succ-1", 2000)
    tx = e.root / "t7.jsonl"
    tx.write_text(tga.row("m1", 100), encoding="utf-8")
    dec, why = tga.run_guard(e, "NEW7", tx, work, tool="Write", tool_input={"file_path": str(work / "x.py")})
    check("V-ECON-SUCCESSOR-ADMITS-NEW", so["ok"] and dec is None and (ms.read_binding("NEW7") or {}).get("goal") == "t7",
          "after a successor lease, a fresh session binds and works on the same goal (accounting follows lineage)")
    dec, why = tga.run_guard(e, "OLD7", tx, work, tool="Write", tool_input={"file_path": str(work / "x.py")})
    check("V-ECON-SUCCESSOR-FENCES-OLD", dec == "deny", "the tombstoned predecessor stays fenced in the successor lease")
    check("V-ECON-SUCCESSOR-ADMISSION", admit(e, "NEW7", "go", work) == {}, "the successor session's messages reach the model")


def main():
    for g in (g_ledger, g_guard, g_admission, g_detach, g_successor):
        e = tga.Env()
        try:
            g(e)
        except Exception as ex:  # noqa: BLE001 -- a crashed gate is a FAIL, never a skip
            check(f"V-ECON-CRASH-{g.__name__}", False, repr(ex))
        finally:
            e.close()
    print(f"ECON_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
