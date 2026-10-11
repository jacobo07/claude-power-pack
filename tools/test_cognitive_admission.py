"""CDC C3 gates: model-call admission firewall at the Agent|Task spawn edge + launch edge capability rows.

Each deny branch is driven red (the hook denies) with a control in which the same shape is admitted, and a
mutation drill disables each predicate in a throwaway copy of the hook: its test must turn RED.
The hook logs through a detached writer; every read of the jsonl polls until the expected row exists.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
sys.path.insert(0, str(HERE))
import cognitive_admission as ca  # noqa: E402
import work_proof as wp  # noqa: E402

HOOK = PP / "hooks" / "cognitive_admission.js"
NODE = os.environ.get("NODE_BIN") or "node"
passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def run(state, sid, prompt, hook=HOOK, extra_env=None, cwd=None):
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(state))
    for k in ("CPP_COG_ADMISSION", "CPP_COG_ROUTE", "CPP_COG_UNIT", "CPP_GOAL"):
        env.pop(k, None)
    env.update(extra_env or {})
    ev = {"session_id": sid, "hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": str(cwd or state),
          "tool_input": {"prompt": prompt, "subagent_type": "general-purpose"}}
    p = subprocess.run([NODE, str(hook)], input=json.dumps(ev), capture_output=True, text=True, env=env, timeout=60)
    try:
        out = json.loads(p.stdout or "{}")
    except ValueError:
        out = {"_raw": p.stdout, "_err": p.stderr}
    d = out.get("hookSpecificOutput", {})
    return d.get("permissionDecision") == "deny", d.get("permissionDecisionReason", ""), out


def rows(state, n, timeout=15):
    """Await the detached writer: poll until n rows exist (or time out)."""
    p = Path(state) / "cognitive-admission.jsonl"
    end = time.time() + timeout
    while time.time() < end:
        if p.exists():
            r = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
            if len(r) >= n:
                return r
        time.sleep(0.1)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def mk_route(tmp, **kw):
    r = Path(tmp) / "route.json"
    r.write_text(json.dumps(kw), encoding="utf-8")
    return r


def bind_unit(state, sid, route, root=""):
    p = Path(state) / "cognitive-unit" / f"{sid}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"unit": "WU-T", "route": str(route), "root": str(root)}), encoding="utf-8")


def exhaust_goal(state, sid, goal="g1"):
    b = Path(state) / "goal-binding" / f"{sid}.json"
    b.parent.mkdir(parents=True, exist_ok=True)
    b.write_text(json.dumps({"goal": goal, "since_ts": "2000-01-01T00:00:00", "source": "explicit", "pid": 0}))
    j = Path(state) / "goal-budget" / goal / "spend.journal.jsonl"
    j.parent.mkdir(parents=True, exist_ok=True)
    j.write_text(json.dumps({"op": "exhausted", "lease": "L1"}) + "\n", encoding="utf-8")


def bind_open_goal(state, sid, goal="g2"):
    b = Path(state) / "goal-binding" / f"{sid}.json"
    b.parent.mkdir(parents=True, exist_ok=True)
    b.write_text(json.dumps({"goal": goal, "since_ts": "2000-01-01T00:00:00", "source": "explicit", "pid": 0}))
    j = Path(state) / "goal-budget" / goal / "spend.journal.jsonl"
    j.parent.mkdir(parents=True, exist_ok=True)
    j.write_text(json.dumps({"op": "cap", "value": 1000}) + "\n", encoding="utf-8")


def scenarios(hook, tag):
    """Drive every deny branch. Returns {branch: denied?} plus controls {branch: allowed?}."""
    res = {}
    with tempfile.TemporaryDirectory() as t:
        st = Path(t) / "state"
        st.mkdir()
        root = Path(t) / "root"
        (root / "vault" / "config").mkdir(parents=True)
        dep = root / "dep.txt"
        dep.write_text("v1", encoding="utf-8")
        wp.record_proof("c1", ["dep.txt"], root=root, ledger_path=root / "vault" / "config" / "claim-proofs.json")
        proof_route = mk_route(t, effect="BOUNDED_COGNITION", proof={"claim": "c1", "deps": ["dep.txt"]})
        # NO_WORK
        bind_unit(st, "s-nowork", proof_route, root)
        res["NO_WORK"] = run(st, "s-nowork", "p1", hook)[0]
        dep.write_text("v2", encoding="utf-8")          # fingerprint changed -> control admitted
        res["NO_WORK_ctl"] = not run(st, "s-nowork", "p1b", hook)[0]
        # EFFECT
        bind_unit(st, "s-eff", mk_route(t, effect="deterministic"), root)
        res["EFFECT"] = run(st, "s-eff", "p2", hook)[0]
        bind_unit(st, "s-eff2", mk_route(t, effect="DETERMINISTIC", deopt=["input changed"]), root)
        res["EFFECT_ctl"] = not run(st, "s-eff2", "p2", hook)[0]
        # LEASE
        exhaust_goal(st, "s-lease")
        res["LEASE"] = run(st, "s-lease", "p3", hook)[0]
        bind_open_goal(st, "s-lease2")
        res["LEASE_ctl"] = not run(st, "s-lease2", "p3", hook)[0]
        # DUPLICATE
        a = run(st, "s-dup", "Do   the thing", hook)[0]
        res["DUPLICATE"] = (not a) and run(st, "s-dup", "do the THING", hook)[0]
        res["DUPLICATE_ctl"] = not run(st, "s-dup", "another prompt", hook)[0]
        res["DUPLICATE_other_session"] = not run(st, "s-dup2", "do the thing", hook)[0]
        # unbound interactive: allow
        res["UNBOUND_allow"] = not run(st, "s-free", "anything", hook)[0]
        # kill switch
        res["KILL_SWITCH"] = not run(st, "s-eff", "p2", hook, {"CPP_COG_ADMISSION": "off"})[0]
        # garbage input fails open
        env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(st))
        p = subprocess.run([NODE, str(hook)], input="{not json", capture_output=True, text=True, env=env, timeout=60)
        res["FAIL_OPEN"] = p.returncode == 0 and "deny" not in p.stdout
        res["_rows"] = rows(st, 5)
    return res


def main():
    r = scenarios(HOOK, "live")
    for k in ("NO_WORK", "NO_WORK_ctl", "EFFECT", "EFFECT_ctl", "LEASE", "LEASE_ctl", "DUPLICATE", "DUPLICATE_ctl",
              "DUPLICATE_other_session", "UNBOUND_allow", "KILL_SWITCH", "FAIL_OPEN"):
        check(f"C3-{k}", r[k] is True, f"{k} -> {r[k]}")
    rw = r["_rows"]
    check("C3-ROWS", len(rw) >= 5 and all(x.get("cap_id") and "decision" in x and x.get("unit") for x in rw),
          f"{len(rw)} capability rows, fields {sorted(rw[0]) if rw else None}")
    check("C3-ROWS-deny", any(x["decision"] == "deny" and x["reason"].startswith("NO_WORK") for x in rw),
          "a deny row carries the reason")
    check("C3-HASH-parity", all(len(x["prompt_hash"] or "") == 16 for x in rw if x["prompt_hash"])
          and ca.prompt_hash("Do   the thing") == ca.prompt_hash("do the THING"), "python/JS normalisation")

    # single writer function used by both edges
    with tempfile.TemporaryDirectory() as t:
        os.environ["GSD_LONG_RUN_STATE_DIR"] = t
        row = ca.record(None, "m-x", "DETERMINISTIC", "route ADMISSIBLE", edge="launch")
        check("C3-LAUNCH-edge", bool(row) and rows(t, 1)[0]["edge"] == "launch", "launch-edge row via ca.record")
        src = (HERE / "gsd_mission.py").read_text(encoding="utf-8")
        check("C3-LAUNCH-wired", "cognitive_admission as _ca" in src and "_ca.record(" in src, "admit_route calls the writer")
        os.environ.pop("GSD_LONG_RUN_STATE_DIR")

    # fast path (no python spawn on the decision path; measured on the in-process decision)
    with tempfile.TemporaryDirectory() as t:
        code = ("const h=require(%s);const t=process.hrtime.bigint();"
                "for(let i=0;i<50;i++)h.decide({session_id:'s'+i,tool_input:{prompt:'p'+i},cwd:%s},Date.now());"
                "console.log(Number(process.hrtime.bigint()-t)/50e6)" % (json.dumps(str(HOOK)), json.dumps(t)))
        env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=t)
        ms = float(subprocess.run([NODE, "-e", code], capture_output=True, text=True, env=env, timeout=60).stdout.strip() or 9e9)
        check("C3-FAST", ms < 50, f"decide() {ms:.2f} ms/call (< 50)")

    # mutation drill: disable each predicate in a throwaway copy; its test must turn RED
    muts = {
        "NO_WORK": ("if (w) return", "if (false) return"),
        "EFFECT": ("NO_MODEL.has(effect) &&", "false &&"),
        "LEASE": ("bind.quarantine || gb.goalExhausted(bind.goal) || gb.sidTombstoned(bind.goal, sid)", "false"),
        "DUPLICATE": ("if (dupSeen(sid, h, now))", "if (false)"),
    }
    src = HOOK.read_text(encoding="utf-8")
    for branch, (a, b) in muts.items():
        if a not in src:
            check(f"C3-MUT-{branch}", False, "mutation anchor missing")
            continue
        mut = HOOK.with_name(f"cognitive_admission_mut_{branch}.js")
        mut.write_text(src.replace(a, b), encoding="utf-8")
        try:
            m = scenarios(mut, branch)
        finally:
            mut.unlink(missing_ok=True)
        check(f"C3-MUT-{branch}", m[branch] is False, f"with the {branch} predicate disabled the deny test is RED ({m[branch]})")
    print(f"\n{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
