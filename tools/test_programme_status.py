"""WU-S4 tests. Run: python tools/test_programme_status.py (prints PROGRAMME_STATUS_PASS=n/m). Hermetic, no live state."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import programme_status as ps  # noqa: E402

PASS = FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    PASS, FAIL = PASS + bool(ok), FAIL + (not ok)
    print(("PASS " if ok else "FAIL ") + name + (" " + str(detail) if detail else ""))


T = Path(tempfile.mkdtemp(prefix="pstatus-"))
(T / "route.json").write_text(json.dumps({"envelope": {"target": 3000000}}))


def mk(n=3, done=0):
    units = []
    for i in range(n):
        u = {"id": f"U{i}", "packet": str(T / f"WU-U{i}.md"), "route": str(T / "route.json"),
             "receipt": str(T / f"WU-U{i}-receipt.md"), "after": f"U{i-1}" if i else None}
        units.append(u)
        Path(u["packet"]).write_text("x")
        if i < done:
            Path(u["receipt"]).write_text("# r\nStatus: DONE\n")
        else:
            Path(u["receipt"]).unlink(missing_ok=True)
    c = T / "chain.json"
    c.write_text(json.dumps({"goal": "g", "root": str(T), "envelope": 10_000_000, "units": units}))
    return c, units


SP = {"settled": 100, "reserved": 5, "unknown": 0, "available": 9_999_895, "telemetry_ok": True}
c, units = mk(3, 1)
st = ps.project(c, missions=[], goal_used=0, spend=SP, head="abc1234")
check("armable at U1", st["state"] == "armable" and st["current_unit"] == "U1", st["action"])
check("last verified U0", st["last_verified_transition"]["unit"] == "U0")
check("forecast from route", st["forecast_next_unit"] == 3000000)
check("debt counts pending", st["debt"]["units_pending"] == 2)
check("handoff rendered", st["handoff"].startswith("HANDOFF") and "unit: U1" in st["handoff"] and "settled=100" in st["handoff"])
check("no material event when armable", ps.material_event(st) is None)

run = [{"mission_id": "m1", "state": "RUNNING", "cwd": str(T), "wu_packet": {"path": units[1]["packet"]}}]
st = ps.project(c, missions=run, goal_used=0, spend=SP, head="h")
check("running + worker named", st["state"] == "running" and st["worker"] == "m1:RUNNING", st["worker"])

held = [{"mission_id": "m2", "state": "PREPARED", "cwd": str(T), "wu_packet": {"path": units[1]["packet"]},
         "owner_hold": {"reason": "owner parked"}}]
st = ps.project(c, missions=held, goal_used=0, spend=SP, head="h")
check("held = blocked + authority edge", st["state"] == "blocked" and ps.material_event(st) == "authority_edge", st["action"])
check("blocker carries reason", "owner parked" in (st["blocker"] or ""))

st = ps.project(c, missions=[], goal_used=9_000_000, spend=SP, head="h")
check("envelope refusal is an authority edge", st["action"] == "refuse_envelope" and ps.material_event(st) == "authority_edge")

Path(units[1]["receipt"]).write_text("# r\nStatus: BLOCKED_HUMAN\n")
st = ps.project(c, missions=[], goal_used=0, spend=SP, head="h")
check("BLOCKED_HUMAN receipt -> blocked", st["state"] == "blocked" and ps.material_event(st) == "blocked", st["blocker"])

c, units = mk(3, 3)
st = ps.project(c, missions=[], goal_used=0, spend=SP, head="h")
check("all done -> done + programme_done", st["state"] == "done" and ps.material_event(st) == "programme_done")

# UNKNOWN is not zero
st = ps.project(c, missions=None, goal_used=None, spend={"settled": ps.UNKNOWN, "reserved": ps.UNKNOWN, "unknown": ps.UNKNOWN,
                                                          "available": ps.UNKNOWN, "telemetry_ok": False}, head="h") \
    if False else None
c, units = mk(3, 1)
orig = ps._load_missions
ps._load_missions = lambda goal: (None, None)
st = ps.project(c, spend=SP, head="h")
ps._load_missions = orig
check("unreadable live state = UNKNOWN, not armable", st["state"] == ps.UNKNOWN and st["worker"] == ps.UNKNOWN, st["state"])
st = ps.project(c, missions=[], goal_used=0, spend={"settled": ps.UNKNOWN, "reserved": ps.UNKNOWN, "unknown": ps.UNKNOWN,
                                                     "available": ps.UNKNOWN, "telemetry_ok": False}, head="h")
check("UNKNOWN spend rendered as UNKNOWN + authority edge", "settled=UNKNOWN" in st["handoff"] and ps.material_event(st) == "authority_edge")

# notify once
c, units = mk(3, 3)
done = ps.project(c, missions=[], goal_used=0, spend=SP, head="h")
sp = T / "notified.json"
sp.unlink(missing_ok=True)
m1, m2 = ps.notify(done, sp), ps.notify(done, sp)
check("notify fires once per event", m1 and m1.startswith("programme_done") and m2 is None, (m1, m2))
c, units = mk(3, 1)
quiet = ps.project(c, missions=[], goal_used=0, spend=SP, head="h")
check("no notification when nothing material", ps.notify(quiet, T / "n2.json") is None)

# large fake history must not change output size
def size(nhist):
    cc, uu = mk(3, 1)
    hist = [{"mission_id": f"old{i}", "state": "COMPLETED", "cwd": str(T), "wu_packet": {"path": units[0]["packet"]}}
            for i in range(nhist)]
    big = dict(SP)
    return len(json.dumps(ps.project(cc, missions=hist, goal_used=0, spend=big, head="h")))
check("output size independent of history", size(5) == size(5000), (size(5), size(5000)))

# mutation drill: an unclipped blocker would grow with history text -> clip is the guard
c, units = mk(3, 1)
long = [{"mission_id": "m3", "state": "PREPARED", "cwd": str(T), "wu_packet": {"path": units[1]["packet"]},
         "owner_hold": {"reason": "x" * 100000}}]
st = ps.project(c, missions=long, goal_used=0, spend=SP, head="h")
check("long free text is clipped", len(json.dumps(st)) < 3000, len(json.dumps(st)))

print(f"PROGRAMME_STATUS_PASS={PASS}/{PASS + FAIL}")
sys.exit(1 if FAIL else 0)
