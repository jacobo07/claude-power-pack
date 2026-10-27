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


def g_raise(e):
    """Owner raise verb (vault/specs/econ-owner-raise.md): `subelo N` is answered before the model."""
    work = e.root / "w8"
    work.mkdir()
    tga.declare("t8", 1000, roots=[str(work)], lease_calls=1)
    exhaust("t8", "R8")
    bind("R8", "t8", "cwd")
    led("t8").set_programme(5000, "test owner", inside_agent=False)
    n0 = len(journal("t8"))
    why = lambda o: o.get("reason") or ""  # noqa: E731
    prose = admit(e, "R8", "please subelo 3k when you can", work)
    comma = admit(e, "R8", "subelo 1,5M", work)
    check("V-ECON-RAISE-WHOLE-MESSAGE",
          all("NOT sent to the model" in why(o) and "OWNER RAISE" not in why(o) for o in (prose, comma))
          and len(journal("t8")) == n0, "the verb inside a sentence, or with a comma decimal, is not the verb: ordinary block, ledger untouched")
    absurd = admit(e, "R8", "subelo 10000000M", work)
    check("V-ECON-RAISE-ARITHMETIC-GUARD", "REFUSED" in why(absurd) and len(journal("t8")) == n0,
          "10 trillion tokens trips only the arithmetic guard and writes nothing")
    work12 = e.root / "w12"
    work12.mkdir()
    tga.declare("t12", 1000, roots=[str(work12)], lease_calls=1)
    exhaust("t12", "R12")
    bind("R12", "t12", "cwd")
    led("t12").set_programme(5000, "test owner", inside_agent=False)
    huge = admit(e, "R12", "subelo 700000M", work12)                  # the old 200M ceiling would have refused this
    lo12 = [r for r in journal("t12") if r["op"] == "lease_open"]
    check("V-ECON-RAISE-UNBOUNDED", "OWNER RAISE APPLIED" in (huge.get("hookSpecificOutput") or {}).get("additionalContext", "")
          and len(lo12) == 1 and lo12[0]["cap"] == 700_000_000_000,
          f"700,000M is applied (cap {lo12[0]['cap'] if lo12 else 0:,}): no budget ceiling on the Owner's amount")
    work13 = e.root / "w13"
    work13.mkdir()
    tga.declare("t13", 1000, roots=[str(work13)], lease_calls=1)
    exhaust("t13", "X13")
    led("t13").set_programme(9000, "test owner", inside_agent=False)
    p13 = len(journal("t13"))
    away = admit(e, "N13", "subelo 3k", e.root / "nowhere")            # control: no record, cwd under no goal root
    check("V-ECON-RAISE-NEUTRAL-CONTROL", "NOT APPLIED" in why(away) and "recent goals" in why(away) and len(journal("t13")) == p13,
          "a pane with no goal and no goal root says so, names goals it can address, and writes nothing")
    by_cwd = admit(e, "N13", "subelo 3k", work13)                      # no binding record, cwd under the exhausted goal
    lo13 = [r for r in journal("t13") if r["op"] == "lease_open"]
    check("V-ECON-RAISE-NEUTRAL-CWD", by_cwd.get("decision") == "block" and "APPLIED" in why(by_cwd) and len(lo13) == 1
          and lo13[0]["cap"] == 3000, "an unrecorded pane quarantined by cwd raises the goal it works on, answered before the model")
    tga.declare("t14", 1000, lease_calls=1)
    exhaust("t14", "X14")
    led("t14").set_programme(9000, "test owner", inside_agent=False)
    p14 = len(journal("t14"))
    nogoal = admit(e, "N14", "subelo 3k nosuchgoal", e.root / "nowhere")
    check("V-ECON-RAISE-NAMED-UNKNOWN", "NOT APPLIED" in why(nogoal) and "not declared" in why(nogoal) and len(journal("t14")) == p14,
          "an undeclared goal name is refused and nothing is written")
    named = admit(e, "N14", "Súbelo 3k T14", e.root / "nowhere")      # accents and case ignored, any pane
    lo14 = [r for r in journal("t14") if r["op"] == "lease_open"]
    check("V-ECON-RAISE-NAMED-GOAL", "APPLIED" in why(named) and len(lo14) == 1 and lo14[0]["cap"] == 3000,
          "`subelo 3k t14` from a pane with no goal opens the successor lease on t14")
    check("V-ECON-RAISE-SUCCESS-NOT-ERROR-LABEL",
          "NOT AN ERROR" in why(named) and "NOT AN ERROR" not in why(nogoal) and "NOT AN ERROR" not in why(absurd),
          "a block-delivered success says it is not an error (the harness labels every pre-model answer 'blocked'); "
          "the refusals of the same verb do not carry that line")
    again14 = admit(e, "N14", "subelo 3k t14", e.root / "nowhere")
    lo14 = [r for r in journal("t14") if r["op"] == "lease_open"]
    check("V-ECON-RAISE-NAMED-SECOND-RAISE", len(lo14) == 2 and lo14[-1]["cap"] == 6000,
          "a second raise on an unspent lease carries its remainder (3,000 + 3,000); the idempotency key is per lease: "
          + why(again14)[:40])
    tga.declare("t9", 1000, lease_calls=1)
    exhaust("t9", "R9")
    bind("R9", "t9", "cwd")
    led("t9").set_programme(1100, "test owner", inside_agent=False)   # overdrawn: 1,200 spent, executable -100
    m0 = len(journal("t9"))
    small = admit(e, "R9", "subelo 100", work)
    check("V-ECON-RAISE-ENVELOPE", "AUTHORITY_REQUIRED" in why(small) and len(journal("t9")) == m0,
          "a raise whose successor does not fit the programme is refused and writes nothing")
    tga.declare("t15", 1000, lease_calls=1)
    exhaust("t15", "X15")                                             # L1 spent: 1,200 against cap 1,000
    led("t15").set_programme(1300, "test owner", inside_agent=False)  # holds 100, less than the spent cap
    live = admit(e, "N15", "subelo 3k t15", e.root / "nowhere")
    lo15 = [r for r in journal("t15") if r["op"] == "lease_open"]
    check("V-ECON-RAISE-SPENT-PROGRAMME", "APPLIED" in why(live) and "NOT APPLIED" not in why(live)
          and len(lo15) == 1 and lo15[0]["cap"] == 3000,
          "a spent lease and a nearly spent programme still take the raise: the successor holds N, not the spent "
          "cap + N (gsdx-factory-2 2026-10-22: 70M and 150M both refused 69,882,516 short): " + why(live)[:80])
    tga.declare("t16", 1000, lease_calls=1)
    exhaust("t16", "X16")
    led("t16").set_programme(1100, "test owner", inside_agent=False)  # overdrawn (this fixture: executable -200)
    over = admit(e, "N16", "subelo 3k t16", e.root / "nowhere")
    lo16 = [r for r in journal("t16") if r["op"] == "lease_open"]
    pr16 = [r for r in journal("t16") if r["op"] == "programme"][-1]
    cap16 = lo16[0]["cap"] if lo16 else None
    check("V-ECON-RAISE-OVERDRAWN-ABSORBS-DEFICIT", "APPLIED" in why(over) and "NOT APPLIED" not in why(over)
          and len(lo16) == 1 and cap16 == 2800 and pr16["value"] == 4100,
          "an overdrawn goal takes the raise: programme +3,000, the successor holds what is left after the deficit "
          f"(gsdx-factory-2 2026-10-23: 129M refused for any amount): cap {cap16}, programme {pr16['value']:,}")
    tga.declare("t17", 1000, lease_calls=1)
    exhaust("t17", "X17")
    led("t17").set_programme(9000, "test owner", inside_agent=False)
    uuid17 = "25a5410c-54d3-4e9b-a944-3d8089f069fe"
    cp17 = subprocess.run([sys.executable, str(HERE / "econ_plane.py"), "raise", "--goal", "t17", "--amount", "3000",
                           "--approval-uuid", uuid17], capture_output=True, text=True, timeout=60, env=os.environ.copy())
    pr17 = [r for r in journal("t17") if r["op"] == "programme"][-1]
    check("V-ECON-RAISE-APPROVAL-UUID", cp17.returncode == 0 and uuid17 in str(pr17.get("source")),
          f"the programme row of a raise carries the approving transcript entry uuid: exit {cp17.returncode}, source {pr17.get('source')!r}")
    tga.declare("t18", 1000, lease_calls=1)
    exhaust("t18", "X18")
    led("t18").set_programme(9000, "test owner", inside_agent=False)
    cp18 = subprocess.run([sys.executable, str(HERE / "econ_plane.py"), "raise", "--goal", "t18", "--amount", "3000"],
                          capture_output=True, text=True, timeout=60, env=os.environ.copy())
    pr18 = [r for r in journal("t18") if r["op"] == "programme"][-1]
    check("V-ECON-RAISE-APPROVAL-UUID-CONTROL", cp18.returncode == 0 and "approval" not in str(pr18.get("source")),
          f"control: with no uuid known the tag is the old one and no uuid is invented: {pr18.get('source')!r}")
    # Envelope-less goal (ccr-a2 2026-10-27): declared elsewhere, only spend here. Spec econ-raise-envelope-bootstrap.
    tga.declare("t19", 1000, lease_calls=1)
    exhaust("t19", "X19")
    g19 = led("t19")._gfold(led("t19")._read())
    floor19 = sum(g19["marks"].values()) + g19["open"]
    boot = admit(e, "N19", "subelo 3k t19", e.root / "nowhere")
    pr19 = [r for r in journal("t19") if r["op"] == "programme"]
    lo19 = [r for r in journal("t19") if r["op"] == "lease_open"]
    ex19 = led("t19").programme_status()["executable"]
    check("V-ECON-RAISE-BOOTSTRAP-ENVELOPE", "APPLIED" in why(boot) and "NOT APPLIED" not in why(boot)
          and len(pr19) == 1 and pr19[0]["value"] == floor19 + 3000 and len(lo19) == 1 and lo19[0]["cap"] == 3000
          and ex19 == 3000, f"typed raise on an envelope-less goal: programme {pr19[0]['value'] if pr19 else None} "
          f"(spent {floor19} + 3,000), lease cap {lo19[0]['cap'] if lo19 else None}, executable {ex19}: " + why(boot)[:80])
    tga.declare("t20", 1000, lease_calls=1)
    exhaust("t20", "X20")
    direct = led("t20").lease_open("agent-try", 3000, prev_lease=led("t20").lineage()["leases"][-1]["id"])
    check("V-ECON-RAISE-BOOTSTRAP-ONLY-VIA-OWNER-VERB",
          not direct["ok"] and not [r for r in journal("t20") if r["op"] in ("lease_open", "programme")],
          f"control: lease_open called directly on an envelope-less goal is still refused and writes nothing: {direct.get('reason')}")
    tga.declare("t21", 1000, lease_calls=1)
    exhaust("t21", "X21")
    g21 = led("t21")._gfold(led("t21")._read())
    floor21 = sum(g21["marks"].values()) + g21["open"]
    cur21 = g21["leases"][-1]["id"]                                 # a crash after the programme row, before the lease
    led("t21").set_programme(floor21 + 3000, f"owner-econ-raise:owner-raise:goal:t21:{cur21}:bootstrap", inside_agent=False)
    cp21 = subprocess.run([sys.executable, str(HERE / "econ_plane.py"), "raise", "--goal", "t21", "--amount", "3000"],
                          capture_output=True, text=True, timeout=60, env=os.environ.copy())
    pr21 = [r for r in journal("t21") if r["op"] == "programme"]
    lo21 = [r for r in journal("t21") if r["op"] == "lease_open"]
    check("V-ECON-RAISE-BOOTSTRAP-CRASH-REPLAY", cp21.returncode == 0 and len(pr21) == 1 and len(lo21) == 1
          and lo21[0]["cap"] == 3000, f"a raise replayed after a crash between its two writes adds no second programme row: "
          f"{len(pr21)} programme, {len(lo21)} lease_open, exit {cp21.returncode}")
    ok = admit(e, "R8", "Súbelo 3k", work)                       # accented spelling
    j = journal("t8")
    prog = [r for r in j if r["op"] == "programme"][-1]
    lo = [r for r in j if r["op"] == "lease_open"]
    ctx = (ok.get("hookSpecificOutput") or {}).get("additionalContext", "")
    check("V-ECON-RAISE-APPLIED", ok.get("decision") != "block" and "OWNER RAISE APPLIED" in ctx and "/kclear" in ctx
          and prog["value"] == 8000 and len(lo) == 1 and lo[0]["cap"] == 3000,
          f"programme 5,000 -> {prog['value']:,}; successor lease cap {lo[0]['cap'] if lo else None} (3,000 new; L1 fully spent); "
          f"{len(lo)} lease_open; message NOT blocked, carries the /kclear order")
    n1 = len(j)
    check("V-ECON-RAISE-PANE-UNFENCED", admit(e, "R8", "hello", work) == {},
          "after the raise the same pane's next message reaches the model")
    tx8 = e.root / "t8.jsonl"
    tx8.write_text(tga.row("m1", 100), encoding="utf-8")
    dec, _w = tga.run_guard(e, "R8", tx8, work, tool="Write", tool_input={"file_path": str(work / "x.py")})
    check("V-ECON-RAISE-GUARD-LIFTED", dec is None, "the PreToolUse guard no longer denies this pane's changes (goal_binding fold)")
    dec9, _w9 = tga.run_guard(e, "R9", tx8, work, tool="Write", tool_input={"file_path": str(work / "x.py")})
    check("V-ECON-RAISE-CONTROL-REFUSED-STAYS-FENCED", dec9 == "deny",
          "the pane whose raise was refused (envelope too small) is still fenced")
    n1 = len(journal("t8"))                                         # after the guard's own settle rows
    again = admit(e, "R8", "subelo 3k", work)
    check("V-ECON-RAISE-IDEMPOTENT", "not blocked" in why(again) and len(journal("t8")) == n1,
          "the same message once the pane is unfenced adds nothing")
    tga.declare("t11", 1000, lease_calls=1)
    exhaust("t11", "R11")
    bind("R11", "t11", "cwd")
    led("t11").set_programme(9000, "test owner", inside_agent=False)
    led("t11").lease_open("owner-raise:R11:L1", 4000)               # a successor an earlier build opened, fence left on
    n11 = len(journal("t11"))
    res = admit(e, "R11", "subelo 3k", work)
    check("V-ECON-RAISE-RESUME", "lifted" in (res.get("hookSpecificOutput") or {}).get("additionalContext", "")
          and len([r for r in journal("t11") if r["op"] == "programme"]) == 1 and len(journal("t11")) == n11 + 1,
          "a pane whose own successor already exists is unfenced with exactly one untomb row and no new money")
    bind("NEW8", "t8", "cwd")
    check("V-ECON-RAISE-SUCCESSOR-ADMITS", admit(e, "NEW8", "go", work) == {},
          "a fresh session binds to the new lease and its messages reach the model")
    tga.declare("t10", 10_000_000, lease_calls=1)
    bind("R10", "t10")
    led("t10").renew("R10", 0, 600, per_call=100)
    k0 = len(journal("t10"))
    free = admit(e, "R10", "subelo 3k", work)
    check("V-ECON-RAISE-CONTROL-NOT-BLOCKED", "not blocked" in why(free) and len(journal("t10")) == k0,
          "a session with room is told nothing was raised and the ledger is untouched")
    led("t8").renew("R8", 6000, 600, per_call=100)                    # crosses lease L2's cap: fenced again
    check("V-ECON-RAISE-REFENCES-ON-NEXT-CROSSING",
          "R8" in led("t8")._gfold(led("t8")._read())["tombs"], "a later crossing of the successor lease tombstones the pane again")


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
    for g in (g_ledger, g_guard, g_admission, g_detach, g_successor, g_raise, g_roles, g_wiring):
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
