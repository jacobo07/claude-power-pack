#!/usr/bin/env python
"""V-STEWARD-* gates (WU-S1): the mission steward settles, salvages and proposes -- deterministically,
once, and never arms. Hermetic: state + ledger in a temp dir BEFORE import, injected liveness/transcripts.
Mutation drill: GSD_MISSION_DRILL_DIR holding a mutated copy of tools/ files or modules/.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-steward-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CLAUDE_CONFIG_DIR"] = str(Path(TMP) / "claude")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
os.environ.pop("CLAUDECODE", None)
os.environ.pop("CPP_MISSION_STEWARD", None)
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402
import mission_steward as st  # noqa: E402
from modules.provider_routing.ledger import GoalLedger, SpendLedger  # noqa: E402

NOW = 1_800_000_000.0
passes = fails = 0
N = [0]


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def journal(goal):
    p = Path(TMP) / "goal-budget" / goal / "spend.jsonl"
    if not p.exists():
        cands = list((Path(TMP) / "goal-budget" / goal).glob("*.jsonl"))
        p = cands[0] if cands else p
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def ops(goal, op):
    return [r for r in journal(goal) if r["op"] == op]


def transcript(path: Path, refused_input=None):
    lines = [
        {"type": "assistant", "uuid": "u1", "message": {"id": "msg1", "model": "x", "usage": {
            "input_tokens": 1000, "output_tokens": 500},
            "content": [{"type": "tool_use", "id": "tu1", "name": "Write", "input": refused_input or {"a": 1}}]}},
        {"type": "user", "uuid": "u2", "message": {"content": [{
            "type": "tool_result", "tool_use_id": "tu1", "is_error": True,
            "content": "SESSION BUDGET BREAKER: stop reached"}]}},
        {"type": "assistant", "uuid": "u3", "message": {"id": "msg1", "model": "x", "usage": {
            "input_tokens": 1000, "output_tokens": 500}, "content": [{"type": "text", "text": "dup id"}]}},
        {"type": "assistant", "uuid": "u4", "message": {"id": "msg2", "model": "x", "usage": {
            "input_tokens": 2000, "output_tokens": 500}, "content": [{"type": "text", "text": "ok"}]}},
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    return 4000          # 1500 (deduped msg1) + 2500


def case(state=gm.HALTED, hold=False, receipt=False, refused_input=None, with_goal=True, cap=50_000_000):
    N[0] += 1
    n = N[0]
    tree = Path(TMP) / f"tree{n}"
    tree.mkdir()
    goal, sid, mid = f"g{n}", f"00000000-0000-4000-8000-{n:012d}", f"m-{n:012x}"
    pkt = tree / "WU-X.md"
    pkt.write_text(f"work_tree: {tree}\nreceipt: out/r.json\n\n# WU\n", encoding="utf-8")
    if receipt:
        (tree / "out").mkdir()
        (tree / "out" / "r.json").write_text("{}", encoding="utf-8")
    if with_goal:
        r = ms.goal_declare(goal, cap, "test", [str(tree)])
        assert r["ok"], r
    rec = gm.create(str(tree), "claude --resume x", mission_id=mid)
    changes = dict(state=state, wu_packet={"path": str(pkt), "sha256": "x"}, goal={"repo": "r", "unit": "u"},
                   owner={"session_id": sid, "kind": "background"}, admission={"at": NOW - 1000})
    if hold:
        changes["owner_hold"] = {"by": "test"}
    rec = gm.transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="test_setup",
                        now=NOW - 500, **changes)
    tp = Path(TMP) / "tx" / f"{sid}.jsonl"
    measured = transcript(tp, refused_input)
    led = ms._goal_ledger(goal) if with_goal else None
    if led:
        led.renew(sid, 0, 700_000)                                  # an open lease of the dead worker
        with led._lock:                                              # ... and a phantom `final` hold
            recs = led._read()
            led._append(recs, {"op": "reserve", "id": f"{goal}:{sid}:9", "sid": sid, "kind": "final",
                               "provider": goal, "amount": 150_000, "window": "goal", "base": 0})
    return dict(mid=mid, sid=sid, tree=tree, goal=goal, led=led, tp=tp, measured=measured, pkt=pkt)


def run(c, **kw):
    missions, _ = gm._scan()
    kw.setdefault("sessions", [])
    kw.setdefault("transcript_for", lambda s: c["tp"] if s == c["sid"] and c["tp"].exists() else None)
    kw.setdefault("ledger_for", ms._goal_ledger)
    now = kw.pop("now", NOW)
    return st.steward_pass(missions, now, pid_alive=lambda p: False, **kw)


def mine(rows, c):
    return [r for r in rows if r.get("mission_id") == c["mid"]]


# --- settle closes all (lease + final), used = measured; control: before the pass both are open
c = case()
g0 = c["led"].status()
stale = gm._scan()[0]                  # a pass that started before the first one finished
rows = run(c)
g1 = c["led"].status()
check("V-STEWARD-SETTLE-CLOSES-ALL", g0["open"] == 850_000 and g1["open"] == 0 and g1["used"] == c["measured"]
      and mine(rows, c) and mine(rows, c)[0]["action"] == "steward_settled", f"{g0['open']}->{g1['open']} used={g1['used']}")
# --- idempotent: second pass and a second direct call book nothing
n_j = len(journal(c["goal"]))
rec_seq = gm.load(c["mid"])["seq"]
rows2 = run(c)
c["led"].settle_stopped(c["sid"], c["measured"], "again")
check("V-STEWARD-SETTLE-IDEMPOTENT", len(journal(c["goal"])) == n_j and not mine(rows2, c), f"journal {n_j}")
check("V-STEWARD-DUP-PASS-ONE-EFFECT", gm.load(c["mid"])["seq"] == rec_seq and len(ops(c["goal"], "settle")) == 1,
      f"seq {rec_seq} settles={len(ops(c['goal'], 'settle'))}")
# --- salvage byte-exact
payload = {"file_path": "x.md", "content": "line1\nüñí\t\"q\" \\ end"}
cs = case(refused_input=payload)
run(cs)
sf = cs["tree"] / "vault" / "specs" / "salvage" / cs["mid"] / "tu1.json"
check("V-STEWARD-SALVAGE", sf.exists() and json.loads(sf.read_text(encoding="utf-8")) == payload)
part = Path(str(cs["tree"] / "out" / "r.json") + ".partial.json")
pj = json.loads(part.read_text(encoding="utf-8")) if part.exists() else {}
check("V-STEWARD-PARTIAL-RECEIPT", pj.get("model_calls") == 2 and pj.get("tool_calls") == 1
      and pj.get("tokens") == 4000 and not (cs["tree"] / "out" / "r.json").exists()
      and "## Residual" in Path(str(cs["pkt"]) + ".residual.md").read_text(encoding="utf-8"), str(pj)[:120])
# --- no transcript -> UNKNOWN, nothing settled
cn = case()
cn["tp"].unlink()
rown = mine(run(cn), cn)
check("V-STEWARD-NO-TRANSCRIPT-UNKNOWN", rown and rown[0]["action"] == "UNKNOWN" and not ops(cn["goal"], "settle")
      and cn["led"].status()["open"] == 850_000)
# --- live owner untouched; control: same case dead is acted on (above)
cl = case()
live = [{"sessionId": cl["sid"], "state": "running", "status": "busy"}]
rl = mine(run(cl, sessions=live), cl)
check("V-STEWARD-LIVE-OWNER-UNTOUCHED", not rl and not ops(cl["goal"], "settle") and "steward" not in gm.load(cl["mid"]))
# --- canonical receipt untouched
cr = case(receipt=True)
rr = mine(run(cr), cr)
check("V-STEWARD-CANONICAL-RECEIPT-UNTOUCHED", not rr and (cr["tree"] / "out" / "r.json").read_text() == "{}"
      and not Path(str(cr["tree"] / "out" / "r.json") + ".partial.json").exists() and not ops(cr["goal"], "settle"))
# --- restart midway: ledger settled, steward field empty (crash after the settle) -> completes once
cm = case()
cm["led"].settle_stopped(cm["sid"], cm["measured"], "pre")
run(cm)
done = (gm.load(cm["mid"]).get("steward") or {}).get("done")
check("V-STEWARD-RESTART-MIDWAY", done is True and len(ops(cm["goal"], "settle")) == 1
      and cm["led"].status()["open"] == 0, f"settles={len(ops(cm['goal'], 'settle'))}")
# --- never arms
before = len(gm._scan()[0])
files = {p.name for p in Path(TMP).glob("gsd-mission-*.json")}
run(case())
after = gm._scan()[0]
check("V-STEWARD-NEVER-ARMS", len(after) == before + 1 and all(m["state"] == gm.HALTED for m in after)
      and {p.name for p in Path(TMP).glob("gsd-mission-*.json")} - files == {f"gsd-mission-m-{N[0]:012x}.json"})
# --- hold not forgotten, forgotten once per 24h
ch = case(hold=True)
inc = gm.lr.state_dir() / "steward-incidents.jsonl"
rh = run(ch, now=NOW + 7200)
hold_rows = [r for r in rh if r.get("goal") == ch["goal"] and r["rule"] == "R2"]
cf = case()
rf = run(cf, now=NOW + 7200)
f_rows = [r for r in rf if r.get("goal") == cf["goal"] and r["rule"] == "R2"]
check("V-STEWARD-HOLD-NOT-FORGOTTEN", not hold_rows and f_rows, f"hold={len(hold_rows)} control={len(f_rows)}")
rf2 = run(cf, now=NOW + 7300)
rf3 = run(cf, now=NOW + 7200 + 25 * 3600)
lines = [json.loads(x) for x in inc.read_text(encoding="utf-8").splitlines()] if inc.exists() else []
n_cf = sum(1 for x in lines if x["goal"] == cf["goal"])
check("V-STEWARD-FORGOTTEN-ONCE-PER-24H", n_cf == 2 and not [r for r in rf2 if r.get("goal") == cf["goal"]]
      and [r for r in rf3 if r.get("goal") == cf["goal"]], f"incidents={n_cf}")
# --- kill switch
ck = case()
os.environ["CPP_MISSION_STEWARD"] = "off"
rk = run(ck)
os.environ.pop("CPP_MISSION_STEWARD")
check("V-STEWARD-KILL-SWITCH", rk == [] and not ops(ck["goal"], "settle") and "steward" not in gm.load(ck["mid"]))
# --- correct lowers; later settle watermarks from there; base fold ignores the op
cc = case()
cc["led"].settle_stopped(cc["sid"], 9_000_000, "big")
cc["led"].correct(cc["sid"], 1_000_000, "misattributed", "test")
s1 = cc["led"].status()["settled"]
cc["led"].settle_stopped(cc["sid"], 900_000, "lower than the corrected mark")
s2 = cc["led"].status()["settled"]
cc["led"].settle_stopped(cc["sid"], 1_200_000, "higher")
s3 = cc["led"].status()["settled"]
base_ok = True
try:
    SpendLedger(Path(TMP) / "goal-budget" / cc["goal"], caps={}, leak_after_s=60)._fold(
        SpendLedger(Path(TMP) / "goal-budget" / cc["goal"], caps={}, leak_after_s=60)._read())
except Exception as e:  # noqa: BLE001
    base_ok = False
check("V-STEWARD-CORRECT-LOWERS", (s1, s2, s3) == (1_000_000, 1_000_000, 1_200_000) and base_ok, f"{s1},{s2},{s3}")


def cli(*args, stdin=subprocess.DEVNULL):
    env = {**os.environ}
    return subprocess.run([sys.executable, str(HERE / "mission_spend.py"), *args], capture_output=True, text=True,
                          stdin=stdin, env=env, timeout=60)


p1 = cli("goal-correct", "--goal", cc["goal"], "--session", cc["sid"], "--measured", "5", "--reason", "x", "--owner")
p2 = cli("goal-correct", "--goal", cc["goal"], "--session", cc["sid"], "--measured", "5", "--reason", "x")
check("V-STEWARD-CORRECT-NEEDS-TTY", p1.returncode == 3 and p2.returncode == 3 and "TTY" in p1.stdout
      and cc["led"].status()["settled"] == 1_200_000, f"{p1.returncode}/{p2.returncode} {p1.stdout[:90]} {p1.stderr[-200:]}")
# --- CLI settle refuses blind; control: --measured settles
cb = case()
q1 = cli("goal-settle", "--goal", cb["goal"], "--session", cb["sid"])
blind_open = cb["led"].status()["open"]
q2 = cli("goal-settle", "--goal", cb["goal"], "--session", cb["sid"], "--measured", "1234")
check("V-STEWARD-CLI-SETTLE-REFUSES-BLIND", q1.returncode == 3 and blind_open == 850_000 and not ops(cb["goal"], "settle")[:0]
      and q2.returncode == 0 and cb["led"].status()["open"] == 0 and cb["led"].status()["used"] == 1234,
      f"rc={q1.returncode}/{q2.returncode} {q1.stdout[:80]}")
# --- supervise isolates a steward failure to one row
cx = case()
real = st.steward_pass
st.steward_pass = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
try:
    out = gm.supervise(now=NOW, sessions=[], pid_alive=lambda p: False)
finally:
    st.steward_pass = real
err = [r for r in out if r.get("action") == "steward_error"]
out_ok = gm.supervise(now=NOW, sessions=[], pid_alive=lambda p: False)
check("V-STEWARD-SUPERVISE-ERROR-ISOLATED", len(err) == 1 and "boom" in err[0]["error"]
      and not [r for r in out_ok if r.get("action") == "steward_error"], f"{len(err)} error rows")
# --- control: nothing qualifies -> zero effects
empty_before = len(journal(cx["goal"]))
cz = case(with_goal=False, state=gm.COMPLETED)
rz = [r for r in run(cz) if r.get("mission_id") == cz["mid"]]
check("V-STEWARD-CONTROL-NOTHING-QUALIFIES", not rz and "steward" not in gm.load(cz["mid"]))

print(f"STEWARD_PASS={passes}/{passes + fails}")
sys.exit(0 if not fails else 1)
