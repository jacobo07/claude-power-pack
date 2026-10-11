"""V-REG-* gates for tools/chain_registry.py + gsdx_chain parked/held/continuation (hermetic, zero model)."""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chain_registry as cr  # noqa: E402
import gsdx_chain as gc  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="chain-reg-test-"))
passes = fails = 0
MUTANT = os.environ.get("REG_MUTANT", "")


def check(gate, ok, detail=""):
    global passes, fails
    passes, fails = passes + bool(ok), fails + (not ok)
    print(f"{'PASS' if ok else 'FAIL'} {gate} {detail}")


if MUTANT == "no-parked":      # mutation drill: parked guard removed
    gc.is_parked = lambda m: False


def setup(name, **extra):
    d = TMP / name
    d.mkdir()
    route = d / "route.json"
    route.write_text(json.dumps({"envelope": {"target": 1_000_000}}), encoding="utf-8")
    units = [{"id": u, "packet": str(d / f"WU-{u}.md"), "route": str(route), "receipt": str(d / f"R-{u}.json"),
              "after": "A" if u == "B" else None} for u in ("A", "B")]
    p = d / "chain.json"
    p.write_text(json.dumps({"goal": name, "root": str(d), "envelope": 40_000_000, "units": units, **extra}), encoding="utf-8")
    return d, p


def mission(d, uid, state, **kw):
    return {"mission_id": f"m-{d.name}-{uid}", "cwd": str(d), "state": state, "wu_packet": {"path": str(d / f"WU-{uid}.md")}, **kw}


def reg(entries):
    p = TMP / f"reg{len(list(TMP.glob('reg*')))}.json"
    p.write_text(json.dumps({"chains": entries}), encoding="utf-8")
    return p


armed = []
arm = lambda chain, u: armed.append((chain["goal"], u["id"])) or {"ok": True, "mission_id": "m-new"}  # noqa: E731
kw = dict(state=lambda: ([], 0), armer=arm, discover_default=False)

# two-unit chain relays with zero model: A armed, A done -> B armed, via the registry
d, p = setup("relay")
r1 = cr.tick_all(reg([{"name": "relay", "chain": str(p)}]), **kw)
(d / "R-A.json").write_text(json.dumps({"status": "DONE"}), encoding="utf-8")
r2 = cr.tick_all(reg([{"name": "relay", "chain": str(p)}]), **kw)
check("V-REG-TWO-UNIT-RELAY", r1[0]["unit"] == "A" and r2[0]["unit"] == "B" and armed == [("relay", "A"), ("relay", "B")],
      str(armed))

# N programmes in one tick; one broken chain does not stop the others
armed.clear()
d1, p1 = setup("n1")
d2, p2 = setup("n2")
rows = cr.tick_all(reg([{"name": "n1", "chain": str(p1)}, {"name": "bad", "chain": str(TMP / "missing.json")},
                        {"name": "n2", "chain": str(p2)}]), **kw)
check("V-REG-N-CHAINS-ISOLATED", [r["action"] for r in rows] == ["arm", "error", "arm"] and len(armed) == 2,
      str([r["action"] for r in rows]))

# parked chain (enabled=false in chain.json) and disabled registry entry arm nothing
armed.clear()
d3, p3 = setup("parkedchain", enabled=False)
d4, p4 = setup("disabledentry")
rows = cr.tick_all(reg([{"name": "pc", "chain": str(p3)}, {"name": "de", "chain": str(p4), "enabled": False}]), **kw)
check("V-REG-PARKED-ARMS-NOTHING", [r["action"] for r in rows] == ["parked", "parked"] and not armed, str(rows))

# the shipped Sidecar queue chain is parked and arms nothing
sc = Path(__file__).resolve().parents[1] / "vault" / "programs" / "sidecar-liveqa" / "chain.json"
sj = json.loads(sc.read_text(encoding="utf-8"))
row = gc.tick(sc, state=lambda: ([], 0), armer=arm)
check("V-REG-SIDECAR-PARKED", row["action"] == "parked" and sj["enabled"] is False and not armed
      and [u["id"] for u in sj["units"]] == ["B-P3", "B-P4", "B-park", "A-experiments"], row["action"])

# held / parked mission is never read as running; control: plain PREPARED is running
d5, p5 = setup("held")
held = mission(d5, "A", "PREPARED", owner_hold={"reason": "owner hold: stage-A"})
r_h = gc.tick(p5, state=lambda: ([held], 0), armer=arm)
r_p = gc.tick(p5, state=lambda: ([mission(d5, "A", "PREPARED")], 0), armer=arm)
r_s = gc.tick(p5, state=lambda: ([mission(d5, "A", "PARKED")], 0), armer=arm)
check("V-REG-HELD-NOT-RUNNING", r_h["action"] == "held" and r_p["action"] == "running" and r_s["action"] == "held",
      f"{r_h['action']}/{r_p['action']}/{r_s['action']}")

# continuation insertion: Sb inserted after S1, successor re-pointed, then relay runs S1 -> S1b -> S2
armed.clear()
d6, p6 = setup("cont")
c = json.loads(p6.read_text(encoding="utf-8"))
c["units"].append({"id": "C", "packet": str(d6 / "WU-C.md"), "route": c["units"][0]["route"], "receipt": str(d6 / "R-C.json"), "after": "B"})
p6.write_text(json.dumps(c), encoding="utf-8")
gc.insert_continuation(p6, "A", {"id": "Ab", "packet": str(d6 / "WU-Ab.md"), "route": c["units"][0]["route"], "receipt": str(d6 / "R-Ab.json")})
c2 = json.loads(p6.read_text(encoding="utf-8"))
order = [(u["id"], u["after"]) for u in c2["units"]]
(d6 / "R-A.json").write_text(json.dumps({"status": "DONE"}), encoding="utf-8")
a1 = gc.tick(p6, state=lambda: ([mission(d6, "A", "COMPLETED")], 0), armer=arm)["unit"]
(d6 / "R-Ab.json").write_text(json.dumps({"status": "DONE"}), encoding="utf-8")
a2 = gc.tick(p6, state=lambda: ([mission(d6, "A", "COMPLETED"), mission(d6, "Ab", "COMPLETED")], 0), armer=arm)["unit"]
bad = False
try:
    gc.insert_continuation(p6, "A", {"id": "Ab"})
except ValueError:
    bad = True
check("V-REG-CONTINUATION-INSERT", order == [("A", None), ("Ab", "A"), ("B", "Ab"), ("C", "B")] and a1 == "Ab" and a2 == "B" and bad,
      f"{order} {a1} {a2}")

# kill switch still honoured through the registry
os.environ["CPP_GSDX_CHAIN"] = "off"
armed.clear()
rows = cr.tick_all(reg([{"name": "k", "chain": str(p1)}]), **kw)
os.environ.pop("CPP_GSDX_CHAIN")
check("V-REG-KILL-SWITCH", rows[0]["action"] == "off" and not armed, rows[0]["action"])

# the shipped registry parses and the live entries are the only enabled ones
shipped = json.loads((Path(__file__).resolve().parents[1] / "vault" / "programs" / "chains.json").read_text(encoding="utf-8"))
en = [e["name"] for e in shipped["chains"] if e.get("enabled", True)]
check("V-REG-SHIPPED-REGISTRY", en == ["autonomy-convergence", "xdomain-canary"], str(en))

# default-on: an unlisted programmes/<x>/chain.json is ticked with no registry entry; only an explicit off parks it
dd = TMP / "disc"
(dd / "p_on").mkdir(parents=True); (dd / "p_off").mkdir(); (dd / "p_park").mkdir()
for n, extra in (("p_on", {}), ("p_off", {"enabled": False}), ("p_park", {"parked": True})):
    (dd / n / "chain.json").write_text(json.dumps({"goal": n, **extra}), encoding="utf-8")
(dd / "chains.json").write_text(json.dumps({"chains": []}), encoding="utf-8")
found = {e["name"]: e["enabled"] for e in cr.discover(dd / "chains.json", [])}
if MUTANT == "no-default-on":
    found = {}
check("V-REG-DEFAULT-ON", found == {"p_on": True, "p_off": False, "p_park": False}, str(found))
listed = [{"name": "x", "chain": str(dd / "p_on" / "chain.json"), "enabled": False}]
check("V-REG-DEFAULT-ON-NO-DUP", "p_on" not in {e["name"] for e in cr.discover(dd / "chains.json", listed)}, "listed entry wins")

print(f"REG_PASS={passes}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
