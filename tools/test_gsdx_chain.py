"""V-CHAIN-* gates for tools/gsdx_chain.py (hermetic: temp files, injected state and armer)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsdx_chain as gc  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="gsdx-chain-test-"))
passes = fails = 0


def check(gate, ok, detail=""):
    global passes, fails
    passes, fails = passes + bool(ok), fails + (not ok)
    print(f"{'PASS' if ok else 'FAIL'} {gate} {detail}")


def setup(name, envelope=40_000_000):
    d = TMP / name
    d.mkdir()
    route = d / "route.json"
    route.write_text(json.dumps({"envelope": {"target": 1_000_000}}), encoding="utf-8")
    units = []
    for uid in ("A", "B"):
        units.append({"id": uid, "packet": str(d / f"WU-{uid}.md"), "route": str(route),
                      "receipt": str(d / f"R-{uid}.json"), "after": "A" if uid == "B" else None, "wait": []})
    chain = {"goal": "g", "root": str(d), "envelope": envelope, "units": units}
    p = d / "chain.json"
    p.write_text(json.dumps(chain), encoding="utf-8")
    return d, p, chain


def mission(d, uid, state):
    return {"mission_id": f"m-{uid}", "cwd": str(d), "state": state, "wu_packet": {"path": str(d / f"WU-{uid}.md")}}


armed = []
arm = lambda chain, u: armed.append(u["id"]) or {"ok": True, "mission_id": "m-new"}  # noqa: E731

# first unit, nothing running -> arms A
d, p, _ = setup("first")
r = gc.tick(p, state=lambda: ([], 0), armer=arm)
check("V-CHAIN-ARMS-FIRST", r["action"] == "arm" and r["unit"] == "A" and armed == ["A"], json.dumps(r)[:120])

# A done -> arms B; control: A PARTIAL -> waits, nothing armed
d, p, _ = setup("next")
(d / "R-A.json").write_text(json.dumps({"status": "DONE"}), encoding="utf-8")
armed.clear()
r = gc.tick(p, state=lambda: ([mission(d, "A", "COMPLETED")], 0), armer=arm)
check("V-CHAIN-ARMS-SUCCESSOR-ON-DONE", r["action"] == "arm" and r["unit"] == "B" and armed == ["B"], r["action"])
(d / "R-A.json").write_text(json.dumps({"status": "PARTIAL"}), encoding="utf-8")
armed.clear()
r = gc.tick(p, state=lambda: ([mission(d, "A", "COMPLETED")], 0), armer=arm)
check("V-CHAIN-PARTIAL-NOT-ARMED", r["action"] == "stopped_without_done" and not armed, r["action"])

# a named extra status is accepted only for the unit that lists it
d, p, chain = setup("accept")
(d / "R-A.json").write_text(json.dumps({"status": "DONE_WITH_LIMITS"}), encoding="utf-8")
armed.clear()
r1 = gc.tick(p, state=lambda: ([mission(d, "A", "COMPLETED")], 0), armer=arm)
chain["units"][0]["accept"] = ["DONE", "DONE_WITH_LIMITS"]
p.write_text(json.dumps(chain), encoding="utf-8")
r2 = gc.tick(p, state=lambda: ([mission(d, "A", "COMPLETED")], 0), armer=arm)
check("V-CHAIN-ACCEPT-IS-PER-UNIT", r1["action"] == "stopped_without_done" and r2["action"] == "arm"
      and r2["unit"] == "B" and armed == ["B"], f"{r1['action']} -> {r2['action']}")

# DONE_WITH_LIMITS is accepted by default only with gate_rc 0 AND named limits; each missing proof still stops
d, p, _ = setup("limits")
cases = {
    "proven": ({"status": "DONE_WITH_LIMITS", "gate_rc": 0, "limits": ["probes are structural"]}, "arm"),
    "no-limits": ({"status": "DONE_WITH_LIMITS", "gate_rc": 0, "limits": []}, "stopped_without_done"),
    "blank-limits": ({"status": "DONE_WITH_LIMITS", "gate_rc": 0, "limits": [" "]}, "stopped_without_done"),
    "gate-failed": ({"status": "DONE_WITH_LIMITS", "gate_rc": 1, "limits": ["x"]}, "stopped_without_done"),
    "no-gate": ({"status": "DONE_WITH_LIMITS", "limits": ["x"]}, "stopped_without_done"),
    "partial": ({"status": "PARTIAL", "gate_rc": 0, "limits": ["x"]}, "stopped_without_done"),
}
got = {}
for name, (rec, _want) in cases.items():
    (d / "R-A.json").write_text(json.dumps(rec), encoding="utf-8")
    armed.clear()
    got[name] = gc.tick(p, state=lambda: ([mission(d, "A", "COMPLETED")], 0), armer=arm)["action"]
(d / "R-A.json").write_text("Status: DONE_WITH_LIMITS\ngate_rc: 0\nlimits: x\n", encoding="utf-8")
got["markdown"] = gc.tick(p, state=lambda: ([mission(d, "A", "COMPLETED")], 0), armer=arm)["action"]
want = {k: v[1] for k, v in cases.items()} | {"markdown": "stopped_without_done"}
check("V-CHAIN-LIMITS-DEFAULT", got == want, json.dumps({k: v for k, v in got.items() if v != want[k]}) if got != want else "all 7 poles")

# a failed arm (held PREPARED record) is surfaced, not read as running; control: a plain PREPARED one is running
d, p, _ = setup("refused")
held = dict(mission(d, "A", "PREPARED"), owner_hold={"reason": "arm-chain failed: MissionError: route RECOMPILE"})
r1 = gc.tick(p, state=lambda: ([held], 0), armer=arm)
r2 = gc.tick(p, state=lambda: ([mission(d, "A", "PREPARED")], 0), armer=arm)
check("V-CHAIN-ARM-REFUSED-SURFACED", r1["action"] == "arm_refused" and r2["action"] == "running",
      f"{r1['action']} / {r2['action']}")

# a refused arm whose route file changed since the refusal was repaired: the stub is history (not arm_refused, not
# a duplicate); control: the same stub with the route unchanged is still surfaced (gsdx-factory-2 r1 RECOMPILE)
import hashlib  # noqa: E402
d, p, chain = setup("repaired")
rt = Path(chain["units"][0]["route"])
stub = dict(mission(d, "A", "PREPARED"), owner_hold={"reason": "arm-chain failed: MissionError: route RECOMPILE"},
            admission={"verdict": "RECOMPILE", "route_path": str(rt),
                       "route_file_sha256": hashlib.sha256(rt.read_bytes()).hexdigest()})
armed.clear()
r1 = gc.tick(p, state=lambda: ([stub], 0), armer=arm)
rt.write_text(json.dumps({"envelope": {"target": 900_000}}), encoding="utf-8")
r2 = gc.tick(p, state=lambda: ([stub], 0), armer=arm)
check("V-CHAIN-REPAIRED-REFUSAL-RETRIES", r1["action"] == "arm_refused" and r2["action"] == "arm" and armed == ["A"],
      f"{r1['action']} / {r2['action']}")

# terminal missions of chain units with open holds are settled; live or foreign missions are not
d, p, chain = setup("settle")
term = dict(mission(d, "A", "COMPLETED"), owner={"session_id": "sid-A"})
live = dict(mission(d, "B", "RUNNING"), owner={"session_id": "sid-B"})
foreign = {"mission_id": "m-x", "cwd": str(d), "state": "HALTED", "wu_packet": {"path": str(d / "other.md")},
           "owner": {"session_id": "sid-X"}}
picked = gc.to_settle(chain, [term, live, foreign], {"sid-A", "sid-B", "sid-X"})
none_open = gc.to_settle(chain, [term], set())
check("V-CHAIN-SETTLES-TERMINAL", picked == ["sid-A"] and none_open == [], f"{picked} / {none_open}")
# a COMPLETED unit worker the ledger never booked (armed outside the goal's roots: no reservation) is settled;
# controls: one already booked is not, and a HALTED one stays the steward's
halted = dict(mission(d, "B", "HALTED"), owner={"session_id": "sid-C"})
unb = gc.to_settle(chain, [term, halted], set(), booked=set())
bk = gc.to_settle(chain, [term], set(), booked={"sid-A"})
check("V-CHAIN-SETTLES-UNBOOKED-COMPLETED", unb == ["sid-A"] and bk == [], f"{unb} / {bk}")
# a HALTED worker whose unit receipt is closed (closed after it stopped) is not the steward's: the chain books it;
# controls: same with the receipt PARTIAL stays the steward's, and an already-booked one is not settled again
(d / "R-B.json").write_text(json.dumps({"status": "DONE"}), encoding="utf-8")
hc = gc.to_settle(chain, [halted], set(), booked=set())
hb = gc.to_settle(chain, [halted], set(), booked={"sid-C"})
(d / "R-B.json").write_text(json.dumps({"status": "PARTIAL"}), encoding="utf-8")
hp = gc.to_settle(chain, [halted], set(), booked=set())
check("V-CHAIN-SETTLES-HALTED-CLOSED-RECEIPT", hc == ["sid-C"] and hb == [] and hp == [], f"{hc} / {hb} / {hp}")
# a unit's RESIDUAL mission (packet + .residual.md) is the unit's: held or never booked, it is settled
# (H012's residual m-23f5b6aef501 ran on WU-H012.md.residual.md and the base-packet match never saw it)
res = {"mission_id": "m-Ar", "cwd": str(d), "state": "COMPLETED", "owner": {"session_id": "sid-R"},
       "wu_packet": {"path": str(d / "WU-A.md") + gc.RESIDUAL}}
check("V-CHAIN-SETTLES-RESIDUAL-WORKER", gc.to_settle(chain, [res], {"sid-R"}) == ["sid-R"]
      and gc.to_settle(chain, [res], set(), booked=set()) == ["sid-R"],
      f"{gc.to_settle(chain, [res], {'sid-R'})} / {gc.to_settle(chain, [res], set(), booked=set())}")

# a receipt inside a MAIN git checkout is unwritable by a background worker (harness bgIsolation; gsdx-factory-2 U1
# burned 2.13M and could not write WU-U1-receipt.md): refuse the arm. Controls: the same root as a linked worktree
# (.git is a file) arms, and so does a receipt outside any checkout (every other fixture here)
d, p, chain = setup("bg-receipt")
(d / ".git").mkdir()
armed.clear()
rm = gc.tick(p, state=lambda: ([], 0), armer=arm)
am = list(armed)
(d / ".git").rmdir()
(d / ".git").write_text("gitdir: elsewhere", encoding="utf-8")
armed.clear()
rw = gc.tick(p, state=lambda: ([], 0), armer=arm)
check("V-CHAIN-REFUSES-MAIN-CHECKOUT-RECEIPT", rm["action"] == "receipt_unwritable" and am == []
      and rw["action"] == "arm" and armed == ["A"], f"{rm['action']} {am} / {rw['action']} {armed}")

# a running mission -> nothing armed
d, p, _ = setup("running")
armed.clear()
r = gc.tick(p, state=lambda: ([mission(d, "A", "RUNNING")], 0), armer=arm)
check("V-CHAIN-ONE-WRITER", r["action"] == "running" and not armed, r["action"])

# a foreign mission PARKED in the same root (PREPARED + Owner hold) writes nothing: it does not block the arm;
# control: a foreign RUNNING one does (gsdx-factory-2 2026-10-25: a held ctx-rent-obs record blocked H012's residual)
d, p, _ = setup("parked-foreign")
parked = {"mission_id": "m-p", "cwd": str(d), "state": "PREPARED", "wu_packet": {"path": str(d / "other.md")},
          "owner_hold": {"reason": "Owner: run it on GEX44 instead"}}
busy = {"mission_id": "m-b", "cwd": str(d), "state": "RUNNING", "wu_packet": {"path": str(d / "other.md")}}
armed.clear()
r1 = gc.tick(p, state=lambda: ([parked], 0), armer=arm)
r2 = gc.tick(p, state=lambda: ([busy], 0), armer=arm)
check("V-CHAIN-PARKED-FOREIGN-NOT-WRITER", r1["action"] == "arm" and r2["action"] == "wait_writer" and armed == ["A"],
      f"{r1['action']} / {r2['action']}")

# envelope_base: a chain's envelope is measured from the goal spend at its approval, not the goal's lifetime
# (gsdx-factory-2 gen-2: 26.5M envelope against 336M of gen-1 lifetime spend -> refuse_envelope forever)
d, p, chain = setup("base", envelope=26_500_000)
armed.clear()
r1 = gc.tick(p, state=lambda: ([], 336_000_000), armer=arm)
chain["envelope_base"] = 330_000_000
p.write_text(json.dumps(chain), encoding="utf-8")
r2 = gc.tick(p, state=lambda: ([], 336_000_000), armer=arm)
check("V-CHAIN-ENVELOPE-BASE", r1["action"] == "refuse_envelope" and r2["action"] == "arm" and armed == ["A"],
      f"{r1['action']} / {r2['action']}")
# status reports the same base-relative spend the tick decides on (it showed used 341M / remaining -315M)
st = gc.status(p, state=lambda: ([], 336_000_000), history=[], measured={}, open_sids={}, git=lambda *a: "")
check("V-CHAIN-STATUS-ENVELOPE-BASE", st["envelope"]["used"] == 6_000_000 and st["envelope"]["remaining"] == 20_500_000
      and st["decision"] != "refuse_envelope", f"{st['envelope']} {st['decision']}")

# HALTED without receipt, no max_residuals -> never re-armed (the default keeps the old behaviour)
d, p, _ = setup("halted")
armed.clear()
r = gc.tick(p, state=lambda: ([mission(d, "A", "HALTED")], 0), armer=arm)
check("V-CHAIN-HALTED-NOT-REARMED", r["action"] == "stopped_without_done" and not armed, r["action"])

# bounded residual re-arm: steward residual for the LATEST stopped mission -> arm it one rung up; cap -> Owner
d, p, chain = setup("residual")
rungs = []
for name, tgt in (("S", 1_000_000), ("M", 2_000_000), ("L", 3_000_000)):
    rp = d / f"route-{name}.json"
    rp.write_text(json.dumps({"envelope": {"target": tgt}}), encoding="utf-8")
    rungs.append(str(rp))
chain["route_ladder"] = rungs
chain["units"][0]["route"] = rungs[1]
chain["max_residuals"] = 2
p.write_text(json.dumps(chain), encoding="utf-8")
res = Path(chain["units"][0]["packet"] + ".residual.md")
got_units = []
arm_u = lambda chain, u: got_units.append(u) or {"ok": True}  # noqa: E731


def stopped(mid, created, packet=None, steward=True):
    m = dict(mission(d, "A", "HALTED"), mission_id=mid, created_at=created)
    if packet:
        m["wu_packet"] = {"path": packet}
    if steward:
        m["steward"] = {"done": True}
    return m


m1, m2 = stopped("m-1", 1), stopped("m-2", 2)
r_none = gc.tick(p, state=lambda: ([m1, m2], 0), armer=arm_u)                    # no residual written yet
res.write_text("# WU\n## Residual\nWritten by the steward for stopped mission m-1.\n", encoding="utf-8")
r_stale = gc.tick(p, state=lambda: ([m1, m2], 0), armer=arm_u)                   # residual is for m-1, not m-2
r_unsettled = gc.tick(p, state=lambda: ([m1, stopped("m-2", 2, steward=False)], 0), armer=arm_u)
check("V-CHAIN-RESIDUAL-WAITS-STEWARD", [r_none["action"], r_stale["action"], r_unsettled["action"]] == ["wait_steward"] * 3
      and not got_units, f"{r_none['action']}/{r_stale['action']}/{r_unsettled['action']}")
res.write_text("# WU\n## Residual\nWritten by the steward for stopped mission m-2.\n", encoding="utf-8")
r1 = gc.tick(p, state=lambda: ([m1, m2], 0), armer=arm_u)
u1 = got_units[0] if got_units else {}
check("V-CHAIN-RESIDUAL-ARMS-ONE-RUNG-UP", r1["action"] == "arm" and r1["residual"] == 1 and r1["need"] == 3_000_000
      and u1.get("packet") == str(res) and u1.get("route") == rungs[2] and u1.get("succession") == "A:r1",
      json.dumps({k: r1.get(k) for k in ("action", "residual", "need")}))
r_run = gc.tick(p, state=lambda: ([m1, m2, dict(stopped("m-3", 3, str(res)), state="RUNNING")], 0), armer=arm_u)
check("V-CHAIN-RESIDUAL-RUNNING", r_run["action"] == "running" and len(got_units) == 1, r_run["action"])
m3, m4 = stopped("m-3", 3, str(res)), stopped("m-4", 4, str(res))
res.write_text("# WU\n## Residual\nWritten by the steward for stopped mission m-3.\n", encoding="utf-8")
r2 = gc.tick(p, state=lambda: ([m1, m2, m3], 0), armer=arm_u)
res.write_text("# WU\n## Residual\nWritten by the steward for stopped mission m-4.\n", encoding="utf-8")
r_cap = gc.tick(p, state=lambda: ([m1, m2, m3, m4], 0), armer=arm_u)
check("V-CHAIN-RESIDUAL-BOUNDED", r2["action"] == "arm" and r2["residual"] == 2 and r2["route"] == rungs[2]
      and r_cap["action"] == "residual_exhausted" and len(got_units) == 2, f"{r2['action']} -> {r_cap['action']}")
# TRF W1 2026-10-11: m-a2577 renewed m-5d84 inside its lineage and was counted as residual 2 -> exhausted after one arm
m3r = dict(stopped("m-3r", 3.5, str(res)), renewed_from="m-3")
res.write_text("# WU\n## Residual\nWritten by the steward for stopped mission m-3r.\n", encoding="utf-8")
r_renew = gc.tick(p, state=lambda: ([m1, m2, m3, m3r], 0), armer=arm_u)
check("V-CHAIN-RESIDUAL-RENEWAL-NOT-COUNTED", r_renew["action"] == "arm" and r_renew["residual"] == 2
      and r_renew["after_mission"] == "m-3r", json.dumps({k: r_renew.get(k) for k in ("action", "residual", "residuals")}))
res.write_text("# WU\n## Residual\nWritten by the steward for stopped mission m-3.\n", encoding="utf-8")
r_env =gc.tick(p, state=lambda: ([m1, m2, m3], 39_000_001), armer=arm_u)
check("V-CHAIN-RESIDUAL-ENVELOPE", r_env["action"] == "refuse_envelope" and len(got_units) == 3, r_env["action"])

# wait event missing -> waits; created -> arms
d, p, chain = setup("event")
chain["units"][0]["wait"] = [str(d / "INST2-receipt.md")]
p.write_text(json.dumps(chain), encoding="utf-8")
armed.clear()
r1 = gc.tick(p, state=lambda: ([], 0), armer=arm)
(d / "INST2-receipt.md").write_text("Status: DONE", encoding="utf-8")
r2 = gc.tick(p, state=lambda: ([], 0), armer=arm)
check("V-CHAIN-WAITS-EVENT", r1["action"] == "wait_event" and r2["action"] == "arm" and armed == ["A"],
      f"{r1['action']} -> {r2['action']}")

# envelope: used + need > envelope -> refuse; control at the boundary arms
d, p, _ = setup("envelope", envelope=5_000_000)
armed.clear()
r1 = gc.tick(p, state=lambda: ([], 4_000_001), armer=arm)
r2 = gc.tick(p, state=lambda: ([], 3_000_000), armer=arm)
check("V-CHAIN-ENVELOPE", r1["action"] == "refuse_envelope" and r2["action"] == "arm" and armed == ["A"],
      f"{r1['action']} / {r2['action']}")

# all done -> complete; kill switch -> off
d, p, _ = setup("complete")
for uid in "AB":
    (d / f"R-{uid}.json").write_text(json.dumps({"status": "DONE"}), encoding="utf-8")
r = gc.tick(p, state=lambda: ([], 0), armer=arm)
import os  # noqa: E402
os.environ["CPP_GSDX_CHAIN"] = "off"
r_off = gc.tick(p, state=lambda: ([], 0), armer=arm)
os.environ.pop("CPP_GSDX_CHAIN")
check("V-CHAIN-COMPLETE-AND-KILL", r["action"] == "complete" and r_off["action"] == "off", f"{r['action']}/{r_off['action']}")

# receipt status parser: markdown and json
(TMP / "r.md").write_text("# x\nStatus: **DONE** (code)\n", encoding="utf-8")
check("V-CHAIN-RECEIPT-PARSE", gc.receipt_status(TMP / "r.md") == "DONE"
      and gc.receipt_status(TMP / "absent.json") is None, gc.receipt_status(TMP / "r.md"))

# ---- D1c: deterministic-first gate (chain_pre) -------------------------------------------------------------------
import chain_pre as cp  # noqa: E402
import os  # noqa: E402
import time  # noqa: E402
PYQ = '"' + sys.executable + '"'


def packet(d, uid, front):
    (d / f"WU-{uid}.md").write_text(front + "\n# WU\nbody\n", encoding="utf-8")


def fm(cls, cmds, extra=""):
    return "---\nclass: " + cls + "\n" + extra + "pre:\n" + "".join(f"  - {c}\n" for c in cmds) + "---"


def pyc(code):
    return f'{PYQ} -c "{code}"'


def own_receipt(d, p, name):
    chain = json.loads(p.read_text(encoding="utf-8"))
    chain["units"][0]["receipt"] = str(d / name)
    p.write_text(json.dumps(chain), encoding="utf-8")


# control: no front matter -> unchanged decision, no .pre.json
d, p, _ = setup("pre-none")
packet(d, "A", "# plain")
armed.clear()
r = gc.tick(p, state=lambda: ([], 0), armer=arm)
check("V-PRE-ABSENT-UNCHANGED", r["action"] == "arm" and armed == ["A"] and not cp.pre_path(d / "WU-A.md").exists(), r["action"])

# pre rc 0 -> arm, results recorded; rc 3 -> pre_failed, no arm
d, p, _ = setup("pre-ok")
packet(d, "A", fm("MODEL", [pyc("print(7)")]))
armed.clear()
r = gc.tick(p, state=lambda: ([], 0), armer=arm)
pj = cp.pre_path(d / "WU-A.md")
rec = json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else {}
check("V-PRE-OK-THEN-ARM", r["action"] == "arm" and armed == ["A"] and rec.get("rc") == 0 and "7" in rec.get("tail", "")
      and r.get("pre_json") == str(pj), r["action"])
d, p, _ = setup("pre-fail")
packet(d, "A", fm("MODEL", [pyc("import sys; sys.exit(3)")]))
armed.clear()
r = gc.tick(p, state=lambda: ([], 0), armer=arm)
check("V-PRE-FAIL-NO-ARM", r["action"] == "pre_failed" and r.get("rc") == 3 and not armed, r["action"])

# DETERMINISTIC: pre writes a DONE receipt -> closed without arm; control: MODEL class with the same pre arms
d, p, _ = setup("pre-det")
own_receipt(d, p, "R-A.md")
rcp = (d / "R-A.md").as_posix()
packet(d, "A", fm("DETERMINISTIC", [pyc(f"open('{rcp}','w').write('Status: DONE')")]))
armed.clear()
r = gc.tick(p, state=lambda: ([], 0), armer=arm)
check("V-PRE-DETERMINISTIC-CLOSES", r["action"] == "closed_deterministic" and not armed, r["action"])
d, p, _ = setup("pre-model")
own_receipt(d, p, "R-A.md")
rcp = (d / "R-A.md").as_posix()
packet(d, "A", fm("MODEL", [pyc(f"open('{rcp}','w').write('Status: DONE')")]))
armed.clear()
r = gc.tick(p, state=lambda: ([], 0), armer=arm)
check("V-PRE-MODEL-STILL-ARMS", r["action"] == "arm" and armed == ["A"], r["action"])

# once per sha: the second tick does not rerun; an edited packet reruns
d, p, _ = setup("pre-once")
cnt = (d / "count.txt").as_posix()
cmd = pyc(f"open('{cnt}','a').write('x')")
packet(d, "A", fm("MODEL", [cmd]))
gc.tick(p, state=lambda: ([], 0), armer=arm)
gc.tick(p, state=lambda: ([], 0), armer=arm)
cf = d / "count.txt"
n1 = len(cf.read_text()) if cf.exists() else 0
packet(d, "A", fm("MODEL", [cmd], "note: edited\n"))
gc.tick(p, state=lambda: ([], 0), armer=arm)
n2 = len(cf.read_text()) if cf.exists() else 0
check("V-PRE-ONCE-PER-SHA", n1 == 1 and n2 == 2, f"{n1}/{n2}")

# timeout honoured (rc 124 -> pre_failed) and capped at 900
d, p, _ = setup("pre-timeout")
packet(d, "A", fm("MODEL", [pyc("import time; time.sleep(30)")], "pre_timeout_s: 1\n"))
armed.clear()
t0 = time.time()
r = gc.tick(p, state=lambda: ([], 0), armer=arm)
check("V-PRE-TIMEOUT", r["action"] == "pre_failed" and r.get("rc") == 124 and not armed and time.time() - t0 < 20, r["action"])
check("V-PRE-TIMEOUT-CAPPED", cp.timeout_s({"pre_timeout_s": "5000"}) == 900 and cp.timeout_s({}) == 600, "")

# kill switch: the pre never runs, the unit arms as before
d, p, _ = setup("pre-kill")
packet(d, "A", fm("MODEL", [pyc("import sys; sys.exit(3)")]))
os.environ["CPP_CHAIN_PRE"] = "off"
armed.clear()
r = gc.tick(p, state=lambda: ([], 0), armer=arm)
os.environ.pop("CPP_CHAIN_PRE")
check("V-PRE-KILL-SWITCH", r["action"] == "arm" and armed == ["A"] and not cp.pre_path(d / "WU-A.md").exists(), r["action"])

# DETERMINISTIC_USED_MODEL typed failure (and its three controls)
check("V-PRE-USED-MODEL", cp.used_model("Status: DONE\n", "DETERMINISTIC", 3) == "DETERMINISTIC_USED_MODEL"
      and cp.used_model("Status: DONE\nUNKNOWN: x\n", "DETERMINISTIC", 3) is None
      and cp.used_model("Status: DONE\n", "DETERMINISTIC", 0) is None
      and cp.used_model("Status: DONE\n", "MODEL", 3) is None, "")

# P1P2-shaped regression: DETERMINISTIC unit, pre writes the receipt, no worker; the successor then arms
d, p, _ = setup("p1p2")
own_receipt(d, p, "R-A.md")
rcp = (d / "R-A.md").as_posix()
packet(d, "A", fm("DETERMINISTIC", [pyc(f"open('{rcp}','w').write('Status: DONE factor ran')")]))
armed.clear()
r1 = gc.tick(p, state=lambda: ([], 0), armer=arm)
r2 = gc.tick(p, state=lambda: ([], 0), armer=arm)
check("V-PRE-P1P2-NO-WORKER", r1["action"] == "closed_deterministic" and r2["action"] == "arm" and r2["unit"] == "B"
      and armed == ["B"], f"{r1['action']} -> {r2['action']}")


# Worker model: _arm passes --model from the unit or the chain (unattended arms otherwise launch on the host
# default); absent stays absent (control).
_seen = []
route_m = TMP / "route-m.json"
route_m.write_text(json.dumps({"envelope": {"target": 1}}), encoding="utf-8")
_real_run = gc.subprocess.run
gc.subprocess.run = lambda cmd, **kw: _seen.append(cmd) or type("P", (), {"stdout": '{"ok": true}', "stderr": "", "returncode": 0})()
try:
    gc._arm({"root": str(TMP), "model": "sonnet"}, {"packet": "x", "route": str(route_m)})
    gc._arm({"root": str(TMP)}, {"packet": "x", "route": str(route_m), "model": "haiku"})
    gc._arm({"root": str(TMP)}, {"packet": "x", "route": str(route_m)})
finally:
    gc.subprocess.run = _real_run
_m = [c[c.index("--model") + 1] if "--model" in c else None for c in _seen]
check("V-CHAIN-ARM-MODEL", _m == ["sonnet", "haiku", None], str(_m))

# a refused arm changes no mission, so no event re-ticks its chain: the sweep retries it (gsdx-factory-2 H3 residual
# 2026-10-25, refused at 2,537 MB free). Controls: too recent, an arm that succeeded, a held arm, and a newer row of
# another checkout's chain under the same goal (a unit this chain does not own) must not hide the refusal.
_pd = TMP / "retry-programs"
for _name in ("refused", "recent", "okarm", "held"):
    (_pd / _name).mkdir(parents=True, exist_ok=True)
    (_pd / _name / "chain.json").write_text(json.dumps({"goal": f"g-{_name}", "units": [{"id": "U"}]}), encoding="utf-8")
_T = 10_000.0
_hist = [{"goal": "g-refused", "unit": "U", "action": "arm", "at": _T - 300, "armed": {"ok": False, "why": "low memory"}},
         {"goal": "g-refused", "unit": "OTHER", "action": "complete", "at": _T - 100},
         {"goal": "g-recent", "unit": "U", "action": "arm", "at": _T - 60, "armed": {"ok": False}},
         {"goal": "g-okarm", "unit": "U", "action": "arm", "at": _T - 300, "armed": {"ok": True}},
         {"goal": "g-held", "unit": "U", "action": "arm", "at": _T - 300, "armed": {"ok": False, "held": True}}]
_ticked = []
_rr = gc.retry_refused_arms(programs_dir=_pd, now=_T, history=_hist,
                            ticker=lambda cp, trigger: _ticked.append((Path(cp).parent.name, trigger)) or {"action": "arm"})
check("V-CHAIN-RETRY-REFUSED-ARM", _ticked == [("refused", "retry")] and len(_rr) == 1, f"{_ticked} {_rr}")

print(f"CHAIN_PASS={passes}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
