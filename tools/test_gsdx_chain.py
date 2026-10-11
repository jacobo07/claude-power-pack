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

# terminal missions of chain units with open holds are settled; live or foreign missions are not
d, p, chain = setup("settle")
term = dict(mission(d, "A", "COMPLETED"), owner={"session_id": "sid-A"})
live = dict(mission(d, "B", "RUNNING"), owner={"session_id": "sid-B"})
foreign = {"mission_id": "m-x", "cwd": str(d), "state": "HALTED", "wu_packet": {"path": str(d / "other.md")},
           "owner": {"session_id": "sid-X"}}
picked = gc.to_settle(chain, [term, live, foreign], {"sid-A", "sid-B", "sid-X"})
none_open = gc.to_settle(chain, [term], set())
check("V-CHAIN-SETTLES-TERMINAL", picked == ["sid-A"] and none_open == [], f"{picked} / {none_open}")

# a running mission -> nothing armed
d, p, _ = setup("running")
armed.clear()
r = gc.tick(p, state=lambda: ([mission(d, "A", "RUNNING")], 0), armer=arm)
check("V-CHAIN-ONE-WRITER", r["action"] == "running" and not armed, r["action"])

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

print(f"CHAIN_PASS={passes}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
