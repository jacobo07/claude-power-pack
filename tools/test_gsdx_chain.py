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

# a failed arm (held PREPARED record) is surfaced, not read as running; control: a plain PREPARED one is running
d, p, _ = setup("refused")
held = dict(mission(d, "A", "PREPARED"), owner_hold={"reason": "arm-chain failed: MissionError: route RECOMPILE"})
r1 = gc.tick(p, state=lambda: ([held], 0), armer=arm)
r2 = gc.tick(p, state=lambda: ([mission(d, "A", "PREPARED")], 0), armer=arm)
check("V-CHAIN-ARM-REFUSED-SURFACED", r1["action"] == "arm_refused" and r2["action"] == "running",
      f"{r1['action']} / {r2['action']}")

# a running mission -> nothing armed
d, p, _ = setup("running")
armed.clear()
r = gc.tick(p, state=lambda: ([mission(d, "A", "RUNNING")], 0), armer=arm)
check("V-CHAIN-ONE-WRITER", r["action"] == "running" and not armed, r["action"])

# HALTED without receipt -> never re-armed
d, p, _ = setup("halted")
armed.clear()
r = gc.tick(p, state=lambda: ([mission(d, "A", "HALTED")], 0), armer=arm)
check("V-CHAIN-HALTED-NOT-REARMED", r["action"] == "stopped_without_done" and not armed, r["action"])

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
r2 = gc.tick(p, state=lambda: ([], 4_000_000), armer=arm)
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
