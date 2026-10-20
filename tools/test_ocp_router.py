"""V-OCP-ROUTER-* gates: the pre-budget Owner router (OCP Phase 3).

Drives the real hook (node hooks/econ_admission.js -> tools/ocp_router.py -> owner_router) against real
GoalLedger journals in an isolated state dir. Every refusal has a control in which the fact exists and the
claim is admitted. Phase 3 never applies: each case also asserts the journals are byte-identical after.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PP))
import mission_spend as ms  # noqa: E402
import test_goal_budget_admission as tga  # noqa: E402
import test_econ_containment as tec  # noqa: E402
from modules.provider_routing import capital_grammar as cg  # noqa: E402
from modules.provider_routing import owner_router as orr  # noqa: E402
from modules.provider_routing.ledger import GoalLedger  # noqa: E402

ADMISSION = PP / "hooks" / "econ_admission.js"
passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def run(e, sid, prompt, cwd=None, event="UserPromptSubmit", **env_over):
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(e.state), PYTHON_BIN=sys.executable)
    for k in ("CPP_ECON_ADMISSION", "CPP_OCP_ROUTER"):
        env.pop(k, None)
    env.update(env_over)
    p = subprocess.run([tga.NODE, str(ADMISSION)], capture_output=True, text=True, env=env, timeout=60,
                       input=json.dumps({"session_id": sid, "prompt": prompt, "cwd": str(cwd or e.root),
                                         "hook_event_name": event}))
    try:
        return json.loads(p.stdout or "{}")
    except ValueError:
        return {"_raw": p.stdout, "_err": p.stderr}


def boundary(goal):
    """An open authority boundary: a programme too small for the successor lease it asked for."""
    tga.declare(goal, 1000, lease_calls=1)
    led = GoalLedger(ms.goal_root() / goal, goal)
    led.set_programme(5_000_000, "test")
    led.lease_open(f"{goal}-s2", 90_000_000)


def journals():
    root = ms.goal_root()
    return {p.parent.name: p.read_bytes() for p in sorted(root.glob("*/spend.journal.jsonl"))} if root.exists() else {}


def reason(o):
    return o.get("reason", "") if o.get("decision") == "block" else ""


def g_tracer(e):
    boundary("ga")
    j0 = journals()
    o = run(e, "S1", "subelo por 70M")
    r = reason(o)
    check("V-OCP-ROUTER-ADD", "ga" in r and "70,000,000" in r and "NOT APPLIED" in r and "ADD" in r,
          r[:110].replace("\n", " | "))
    check("V-OCP-ROUTER-ADD-JOURNAL-UNCHANGED", journals() == j0, "ledger journal bytes identical after ADD")
    off = run(e, "S1", "subelo por 70M", CPP_OCP_ROUTER="off")
    check("V-OCP-ROUTER-KILL-SWITCH", off == {}, f"CPP_OCP_ROUTER=off gives the legacy path: {str(off)[:40]}")


def g_ops(e):
    boundary("ga")
    j0 = journals()
    s = reason(run(e, "S2", "subelo a 102M"))
    check("V-OCP-ROUTER-SET", "SET total 102,000,000" in s and "ga" in s, s[:90].replace("\n", " | "))
    check("V-OCP-ROUTER-ADD-NE-SET", "ADD" not in s and "SET" in s, "SET is not rendered as ADD")
    st = reason(run(e, "S2", "stop"))
    check("V-OCP-ROUTER-STOP", "STOP" in st and "ga" in st, st[:90].replace("\n", " | "))
    ke = reason(run(e, "S2", "keep"))
    check("V-OCP-ROUTER-KEEP", "KEEP" in ke and "ga" in ke, ke[:90].replace("\n", " | "))
    amb = reason(run(e, "S2", "70M"))
    check("V-OCP-ROUTER-AMBIGUOUS-AMOUNT", "add or set" in amb and "subelo por 70000000" in amb and "subelo a 70000000" in amb,
          amb[:110].replace("\n", " | "))
    inv = reason(run(e, "S2", "subelo por 1.5"))
    check("V-OCP-ROUTER-INVALID", "not understood" in inv and "NOT" not in inv.replace("Nothing applied", ""),
          inv[:90].replace("\n", " | "))
    check("V-OCP-ROUTER-OPS-JOURNAL-UNCHANGED", journals() == j0, "no case wrote a ledger row")


def g_targets(e):
    boundary("ga")
    boundary("gb")
    two = reason(run(e, "S3", "subelo por 70M"))
    check("V-OCP-ROUTER-AMBIGUOUS-TARGET", "2 goals" in two and "ga" in two and "gb" in two
          and "NOT APPLIED" not in two, two[:110].replace("\n", " | "))
    ex = reason(run(e, "S3", "modify gb to 102M"))
    check("V-OCP-ROUTER-EXPLICIT-GOAL-WINS", "gb" in ex and "102,000,000" in ex and "ga" not in ex,
          ex[:90].replace("\n", " | "))
    ghost = reason(run(e, "S3", "modify nope to 102M"))
    check("V-OCP-ROUTER-UNKNOWN-GOAL", "does not exist" in ghost, ghost[:90].replace("\n", " | "))
    # cwd and the session binding never select: bind S4 to gc (no boundary) and run from a gb-rooted cwd
    tga.declare("gc", 100000, lease_calls=1)
    tec.bind("S4", "gc")
    work = e.root / "wb"
    work.mkdir()
    three = reason(run(e, "S4", "subelo por 70M", cwd=work))
    check("V-OCP-ROUTER-CWD-NEVER-SELECTS", "gc" not in three and "2 goals" in three,
          "a bound pane and a cwd did not pick a target: " + three[:70].replace("\n", " | "))


def g_zero_boundary(e):
    tga.declare("gz", 1000000, lease_calls=1)
    add = reason(run(e, "S5", "subelo por 70M"))
    check("V-OCP-ROUTER-NO-BOUNDARY-CLARIFIES", "no goal is waiting" in add, add[:90].replace("\n", " | "))
    bare = run(e, "S5", "stop")
    check("V-OCP-ROUTER-BARE-STOP-IS-CHAT", bare == {}, f"bare stop with no boundary falls through: {str(bare)[:40]}")
    boundary("gq")
    ctl = reason(run(e, "S5", "stop"))
    check("V-OCP-ROUTER-BARE-STOP-CONTROL", "STOP" in ctl and "gq" in ctl, "the same word with one boundary is control")


def g_fence(e):
    work = e.root / "w9"
    work.mkdir()
    tga.declare("t9", 1000, roots=[str(work)], lease_calls=1)
    tec.exhaust("t9", "T9")
    tec.bind("T9", "t9", "cwd")
    on = run(e, "T9", "econ status", cwd=work)
    off = run(e, "T9", "econ status", cwd=work, CPP_OCP_ROUTER="off")
    check("V-OCP-ROUTER-STATUS-ZERO-HEADROOM", "ECONOMIC STATUS" in reason(on) and "0 model tokens" in reason(on)
          and on == off, "econ status at an exhausted lease is byte-identical with the router off")
    ctl = run(e, "NOBODY", "econ status", cwd=work)
    ctl_off = run(e, "NOBODY", "econ status", cwd=work, CPP_OCP_ROUTER="off")
    check("V-OCP-ROUTER-STATUS-CONTROL", ctl == ctl_off and "NEUTRAL" in reason(ctl) and "EXHAUSTED" not in reason(ctl),
          "an unbound session answers NEUTRAL, identically with the router off")
    chat = run(e, "T9", "fix issue 42", cwd=work)
    chat_off = run(e, "T9", "fix issue 42", cwd=work, CPP_OCP_ROUTER="off")
    check("V-OCP-ROUTER-RANDOM-CHAT-FALLS-THROUGH", chat == chat_off and "NOT sent to the model" in reason(chat),
          "digit-bearing chat at zero headroom is blocked by the old fence, identically")
    tga.declare("troom", 10_000_000, lease_calls=1)
    tec.bind("T10", "troom")
    GoalLedger(ms.goal_root() / "troom", "troom").renew("T10", 0, 600, per_call=100)
    check("V-OCP-ROUTER-CHAT-WITH-ROOM", run(e, "T10", "fix issue 42") == {}, "positive headroom: {}")
    sentinel = run(e, "T10", "hello there", PYTHON_BIN=str(e.root / "no_such_python"))
    check("V-OCP-ROUTER-NO-SPAWN-FOR-CHAT", sentinel == {}, "chat without digit/keyword never spawns Python")
    miss = run(e, "T9", "subelo por 70M", cwd=work, PYTHON_BIN=str(e.root / "no_such_python"))
    check("V-OCP-ROUTER-FAIL-OPEN-NEVER-WEAKENS-FENCE", "NOT sent to the model" in reason(miss),
          "missing interpreter: the zero-headroom block TEXT still comes from decide()")


def g_principal(e):
    boundary("ga")
    j0 = journals()
    bad = run(e, "S6", "subelo por 70M", event="PostToolUse")
    check("V-OCP-ROUTER-PRINCIPAL-UNKNOWN-NEVER-APPLIED", bad == {} and journals() == j0,
          "a non-UserPromptSubmit event is NOT_CONTROL")
    r = orr.route("subelo por 70M", "bad sid!", {"hook_event_name": "UserPromptSubmit"}, ms.goal_root())
    check("V-OCP-ROUTER-BAD-SID", r["outcome"] == orr.NOT_CONTROL and r["principal"] == "unknown" and not r["applied"],
          "invalid session id => unknown principal")
    ok = orr.route("subelo por 70M", "S6", {"hook_event_name": "UserPromptSubmit"}, ms.goal_root())
    check("V-OCP-ROUTER-PRINCIPAL-CONTROL", ok["outcome"] == orr.TYPED and ok["principal"] == "owner",
          "the same input from a UserPromptSubmit is control")


def prefilter_pass(p: str) -> bool:
    return len(p) <= 160 and "\n" not in p and bool(re.search(r"\d|\b(?:keep|mantener|stop|para|cierra|revoke)\b", p, re.I))


def g_static(e):
    samples = sorted(cg._KEEP | cg._STOP) + ["subelo por 70M", "subelo a 102M", "modify g to 5M", "revoke g",
                                              "add 2m", "sube 3000", "set to 4M", "70M"]
    miss = [s for s in samples if cg.parse_intent(s) is not None and not prefilter_pass(s)]
    check("V-OCP-ROUTER-PREFILTER-COVERS-GRAMMAR", not miss, f"{len(samples)} grammar positives pass the prefilter; missed {miss}")
    js = ADMISSION.read_text(encoding="utf-8")
    check("V-OCP-ROUTER-PREFILTER-MATCHES-JS", all(w in js for w in ("keep|mantener|stop|para|cierra|revoke", "160")),
          "the test mirrors the JS prefilter constants")
    src = "\n".join((PP / f).read_text(encoding="utf-8") for f in
                    ("modules/provider_routing/owner_router.py", "tools/ocp_router.py"))
    bad = re.findall(r"anthropic|requests|urllib|socket", src)
    check("V-OCP-ROUTER-NO-MODEL-NO-NETWORK", not bad, f"no model/network imports: {bad}")
    check("V-OCP-ROUTER-NO-WRITES", not re.search(r"\.(?:renew|declare_cap|set_programme|lease_open|_append)\(", src),
          "the router calls no ledger mutator")


def main():
    for g in (g_tracer, g_ops, g_targets, g_zero_boundary, g_fence, g_principal, g_static):
        e = tga.Env()
        try:
            g(e)
        except Exception as ex:  # noqa: BLE001 -- a crashed gate is a FAIL, never a skip
            check(f"V-OCP-ROUTER-CRASH-{g.__name__}", False, repr(ex))
        finally:
            e.close()
    print(f"OCP_ROUTER_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
