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


def g_roles(e):
    # WS-F: recovery spend has its own role under the programme's recovery reserve and is never productive
    # spend on a lease; refused-but-billed boundaries stay real cost and are reported apart.
    tga.declare("t8", 1000, lease_calls=1)
    exhaust("t8", "A8")
    for m in (1400, 1600):
        led("t8").renew("A8", m, 600, per_call=100)
    st = led("t8").status()
    check("V-ECON-REFUSED-BILLED-ROLE", st.get("refused_billed") == 400 and st["settled"] == 1600,
          f"settles of a tombstoned pane are real cost, reported apart: refused_billed {st.get('refused_billed')}")
    nr = led("t8").renew("R0", 0, 600, per_call=100, role="recovery")
    check("V-ECON-RECOVERY-NO-RESERVE", not nr["ok"] and "RECOVERY" in nr["reason"]
          and not any(r["op"] == "reserve" and r["sid"] == "R0" and r.get("kind") == "lease" for r in journal("t8")),
          f"no recovery reserve, no recovery lease: {nr['reason'][:60]}")

    l8 = led("t8")
    l8.set_programme(10_000, "test owner", inside_agent=False)
    ex0 = l8.programme_status()["executable"]
    so = l8.lease_open("succ-8", 2000, reserves={"recovery": 800})
    ex1 = l8.programme_status()["executable"]
    l1_before = led("t8")._gfold(led("t8")._read())["leases"][0]["used"]
    r1 = led("t8").renew("R8", 0, 200, per_call=100, role="recovery")
    r2 = led("t8").renew("R8", 300, 200, per_call=100, role="recovery")
    g = led("t8")._gfold(led("t8")._read())
    l1, l2 = g["leases"][0], g["leases"][-1]
    check("V-ECON-RECOVERY-OFF-LEASE", so["ok"] and r1["ok"] and r2["ok"] and l2["used"] == 0
          and l2.get("recovery_used", 0) >= 300 and l1["used"] == l1_before and g["used"] == 0,
          f"recovery spend: L1 {l1_before}->{l1['used']}, L2 productive {l2['used']}, "
          f"recovery {l2.get('recovery_used')}, admission used {g['used']}")
    ex2 = led("t8").programme_status()["executable"]
    check("V-ECON-RECOVERY-PREFUNDED", ex1 == ex2 and ex1 == ex0 - 800,
          f"spending a pre-funded recovery reserve does not shrink executable twice: {ex0} -> {ex1} -> {ex2}")
    import socket
    bp = ms.binding_path("R9")
    bp.parent.mkdir(parents=True, exist_ok=True)
    bp.write_text(json.dumps({"goal": "t8", "since_ts": "2000-01-01T00:00:00", "source": "explicit", "pid": 0,
                              "role": "recovery"}), encoding="utf-8")
    tw = ms.goal_renew("t8", "R9", 0, 100, socket.gethostname())
    rows = [r for r in journal("t8") if r["op"] == "reserve" and r["sid"] == "R9"]
    check("V-ECON-PY-TWIN-ROLE", tw["ok"] and rows and rows[-1].get("role") == "recovery",
          f"goal_renew takes the role from the session's binding record: {tw.get('reason', '')[:60]}")

    r3 = led("t8").renew("R8", 900, 200, per_call=100, role="recovery")
    g = led("t8")._gfold(led("t8")._read())
    check("V-ECON-RECOVERY-RESERVE-BOUND", not r3["ok"] and "RECOVERY_RESERVE_SPENT" in r3["reason"]
          and "R8" in g["tombs"] and not g["exhausted_now"],
          f"a spent recovery reserve fences the recovery pane, never the lease: {r3['reason'][:60]}")
    p = led("t8").renew("P8", 0, 600, per_call=100)
    check("V-ECON-RECOVERY-CONTROL", p["ok"] and not p["exhausted"], "a productive pane on the successor lease is still admitted")
    fx = led("t8").renew("P8", 50, 600, per_call=100, role="recovery")
    check("V-ECON-ROLE-FIXED", not fx["ok"] and "ROLE_FIXED" in fx["reason"],
          f"a session's role is fixed on a goal: {fx['reason'][:60]}")


SETTINGS = Path.home() / ".claude" / "settings.json"
DISPATCHERS = [PP / "hooks" / "hook-dispatcher.js", Path.home() / ".claude" / "hooks" / "hook-dispatcher.js"]


def ups_standalone_timeouts(settings: dict) -> list:
    """Timeouts (s) of UserPromptSubmit entries that run econ_admission.js DIRECTLY (not via a dispatcher)."""
    out = []
    for grp in ((settings.get("hooks") or {}).get("UserPromptSubmit") or []):
        for h in (grp.get("hooks") or []):
            line = " ".join([str(h.get("command", ""))] + [str(a) for a in (h.get("args") or [])])
            if "econ_admission.js" in line and "hook-dispatcher" not in line:
                out.append(h.get("timeout"))
    return out


def chain_has_admission(src: str) -> bool:
    """Is econ_admission.js a MEMBER of the dispatcher's UserPromptSubmit-chain (comments ignored)?"""
    head = "'UserPromptSubmit-chain': ["
    if head not in src:
        return False
    body = src.split(head, 1)[1].split("\n  ],", 1)[0]
    return any("econ_admission.js" in ln for ln in body.splitlines() if not ln.strip().startswith("//"))


def g_wiring(e):
    # Incident 5e764b5a (2026-10-10): in-chain, admission shared the dispatcher's 15 s harness timeout with
    # its cold start and the sequential critical lane; under RAM starvation the harness killed the chain
    # (19,283 / 18,768 ms) and a killed hook fails OPEN -- two Owner messages reached a tombstoned pane's
    # model. The gate must be its own entry with its own timeout, and must not also run in the chain.
    pos_settings = {"hooks": {"UserPromptSubmit": [{"hooks": [{"command": "node", "args": ["x/econ_admission.js"], "timeout": 30}]}]}}
    neg_settings = {"hooks": {"UserPromptSubmit": [{"hooks": [{"command": "node", "args": ["x/hook-dispatcher.js", "--event=UserPromptSubmit-chain"], "timeout": 15}]}]}}
    pos_chain = "'UserPromptSubmit-chain': [\n    // econ_admission.js note\n    { script: '../hooks/econ_admission.js' },\n  ],"
    neg_chain = "'UserPromptSubmit-chain': [\n    // econ_admission.js moved out\n    { script: './other.js' },\n  ],"
    check("V-ECON-WIRING-DETECTORS-CONTROL",
          ups_standalone_timeouts(pos_settings) == [30] and ups_standalone_timeouts(neg_settings) == []
          and chain_has_admission(pos_chain) and not chain_has_admission(neg_chain),
          "both detectors see the shape they look for and ignore dispatcher entries and comments")
    try:
        live = json.loads(SETTINGS.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as ex:
        live = None
        check("V-ECON-ADMISSION-STANDALONE", False, f"live settings.json unreadable: {ex!r}")
    if live is not None:
        t = ups_standalone_timeouts(live)
        check("V-ECON-ADMISSION-STANDALONE", len(t) == 1 and isinstance(t[0], (int, float)) and t[0] >= 20,
              f"direct UserPromptSubmit entries for econ_admission.js: timeouts {t} (need exactly one, >= 20 s)")
    for d in DISPATCHERS:
        src = d.read_text(encoding="utf-8") if d.exists() else None
        check(f"V-ECON-ADMISSION-NOT-IN-CHAIN[{d.parent.parent.name}]", src is not None and not chain_has_admission(src),
              f"{d}: " + ("missing" if src is None else "still a chain member (would run twice)" if chain_has_admission(src) else "not a chain member"))


def main():
    for g in (g_ledger, g_guard, g_admission, g_detach, g_successor, g_roles, g_wiring):
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
