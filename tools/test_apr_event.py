"""V-APR3-* gates: tick lock, idempotent arm, event path, status, bounded silence, reforecast (hermetic)."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsdx_chain as gc  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="apr-event-test-"))
os.environ.setdefault("CPP_GSDX_CHAIN_STATE", str(TMP / "state"))
passes = fails = 0


def check(gate, ok, detail=""):
    global passes, fails
    passes, fails = passes + bool(ok), fails + (not ok)
    print(f"{'PASS' if ok else 'FAIL'} {gate} {detail}")


def setup(name, n=2, targets=(1_000_000,) * 4, **extra):
    d = TMP / name
    d.mkdir()
    units = []
    for i, uid in enumerate("ABCD"[:n]):
        route = d / f"route-{uid}.json"
        route.write_text(json.dumps({"envelope": {"target": targets[i]}}), encoding="utf-8")
        units.append({"id": uid, "packet": str(d / f"WU-{uid}.md"), "route": str(route), "receipt": str(d / f"R-{uid}.md"),
                      "after": "ABCD"[i - 1] if i else None, "wait": []})
        (d / f"WU-{uid}.md").write_text("# p\n", encoding="utf-8")
    chain = {"goal": "g" + name, "root": str(d), "envelope": 40_000_000, "units": units, **extra}
    p = d / "chain.json"
    p.write_text(json.dumps(chain), encoding="utf-8")
    return d, p, chain


def mission(d, uid, state="RUNNING", suffix="", n=1, **kw):
    return {"mission_id": f"m-{uid}{n}", "cwd": str(d), "state": state, "created_at": 1000 + n,
            "wu_packet": {"path": str(d / f"WU-{uid}.md") + suffix}, **kw}


# ---- child process for the race (a real second process, a real slow armer) --------------------------------------
if len(sys.argv) > 2 and sys.argv[1] == "child":
    chain_path, store, lock_s = Path(sys.argv[2]), Path(sys.argv[3]), float(sys.argv[4])

    def st():
        return (json.loads(store.read_text()) if store.exists() else []), 0

    def slow_arm(chain, u):
        time.sleep(1.5)
        ms = st()[0] + [{"mission_id": f"m-{os.getpid()}", "cwd": chain["root"], "state": "RUNNING", "created_at": 1,
                         "wu_packet": {"path": u["packet"]}}]
        store.write_text(json.dumps(ms))
        return {"ok": True}
    r = gc.tick(chain_path, state=st, armer=slow_arm, lock_s=lock_s)
    print(json.dumps({"action": r["action"]}))
    sys.exit(0)


def race(name, lock_s):
    d, p, _ = setup(name, 1)
    store = d / "missions.json"
    procs = [subprocess.Popen([sys.executable, "-I", __file__, "child", str(p), str(store), str(lock_s)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"}) for _ in range(2)]
    outs = [pr.communicate(timeout=60)[0] for pr in procs]       # awaited: no child outlives the test
    acts = sorted(json.loads(o.strip().splitlines()[-1])["action"] for o in outs if o.strip())
    return acts, len(json.loads(store.read_text()))


acts, n = race("race-skip", 0.3)
check("V-APR3-LOCK-ONE-ARM-SKIP", n == 1 and acts == ["arm", "skipped_locked"], f"{acts} missions={n}")
acts, n = race("race-wait", 20)
check("V-APR3-LOCK-ONE-ARM-WAIT", n == 1 and acts == ["arm", "running"], f"{acts} missions={n}")

# ---- idempotent arm -----------------------------------------------------------------------------------------------
d, p, _ = setup("idem")
store = []
calls = []


def st():
    return list(store), 0


def good_arm(chain, u):
    calls.append(u["packet"])
    store.append(mission(d, u["id"], suffix=u["packet"][len(str(d / f"WU-{u['id']}.md")):]))
    return {"ok": True}


r1 = gc.tick(p, state=st, armer=good_arm, trigger="event")
r2 = gc.tick(p, state=st, armer=good_arm, trigger="watchdog")
check("V-APR3-EVENT-PLUS-WATCHDOG-ONE-ARM", len(calls) == 1 and r1["action"] == "arm" and r2["action"] == "running"
      and r1["trigger"] == "event" and r2["trigger"] == "watchdog", f"{r1['action']} {r2['action']}")

d, p, _ = setup("crash")
store, calls = [], []


def crash_arm(chain, u):
    good_arm(chain, u)
    raise RuntimeError("died after arm-chain returned")


r1 = gc.tick(p, state=st, armer=crash_arm)
r2 = gc.tick(p, state=st, armer=good_arm)
check("V-APR3-CRASH-AFTER-ARM-NO-DOUBLE", len(calls) == 1 and r1["armed"].get("raised") and r2["action"] == "running",
      f"{r1['action']} {r2['action']}")

# a live residual mission carries the unit's packet: a normal arm must refuse (re-read under lock)
d, p, _ = setup("resid")
live = [mission(d, "A", suffix=".residual.md")]
calls = []
stale = iter([([], 0), (live, 0)])        # decide sees a stale empty world; the re-read under the lock sees the residual
r = gc.tick(p, state=lambda: next(stale), armer=good_arm)
check("V-APR3-RESIDUAL-AND-FINALIZER-NO-DOUBLE", not calls and r["action"] == "running", json.dumps(r)[:120])

# ---- event path ----------------------------------------------------------------------------------------------------
import gsd_mission as gm  # noqa: E402

pdir = TMP / "programs"
(pdir / "one").mkdir(parents=True)
(pdir / "bad").mkdir()
d, p, chain = setup("evt")
(pdir / "one" / "chain.json").write_text(json.dumps(chain), encoding="utf-8")
(pdir / "bad" / "chain.json").write_text("{not json", encoding="utf-8")
ticks = []
tk = lambda cp, **kw: ticks.append((str(cp), kw)) or {"action": "running", "unit": "A", "trigger": kw["trigger"]}  # noqa: E731
pk = chain["units"][0]["packet"]
before = {"m1": ("RUNNING", pk)}
os.environ.pop("CPP_GSDX_CHAIN_EVENT", None)
t0 = time.perf_counter()
rows = gc.tick_for_packet(pk, programs_dir=pdir, ticker=tk)
dt = (time.perf_counter() - t0) * 1000
check("V-APR3-EVENT-DISCOVERS-AND-TICKS", len(ticks) == 1 and ticks[0][1]["trigger"] == "event"
      and any(r["action"] == "event_error" and "bad" in r["chain"] for r in rows), f"{[r['action'] for r in rows]}")
rows = gm.event_chain_ticks(before, {"m1": ("COMPLETED", pk)}, ticker=lambda q: gc.tick_for_packet(q, programs_dir=pdir, ticker=tk))
check("V-APR3-COMPLETED-TRANSITION-TICKS-ONCE", sum(1 for _ in ticks) == 2 and rows[0]["action"] == "chain_event", f"{rows[:2]}")
n0 = len(ticks)
gm.event_chain_ticks({"m1": ("COMPLETED", pk)}, {"m1": ("COMPLETED", pk)}, ticker=lambda q: gc.tick_for_packet(q, programs_dir=pdir, ticker=tk))
check("V-APR3-NO-TRANSITION-NO-TICK", len(ticks) == n0)
os.environ["CPP_GSDX_CHAIN_EVENT"] = "off"
rows = gm.event_chain_ticks(before, {"m1": ("HALTED", pk)}, ticker=lambda q: gc.tick_for_packet(q, programs_dir=pdir, ticker=tk))
check("V-APR3-KILL-SWITCH-NO-TICK", len(ticks) == n0 and rows == [])
os.environ.pop("CPP_GSDX_CHAIN_EVENT")
rows = gm.event_chain_ticks(before, {"m1": ("HALTED", pk)}, ticker=lambda q: 1 / 0)
check("V-APR3-EVENT-FAIL-ISOLATED", rows and rows[0]["status"] == "ERROR")
# real tick (injected state) through the event path: latency
store = []
calls = []
t0 = time.perf_counter()
rows = gc.tick_for_packet(pk, programs_dir=pdir, state=st, armer=good_arm)
lat = (time.perf_counter() - t0) * 1000
check("V-APR3-EVENT-LATENCY-MEASURED", lat < 5000 and any(r.get("trigger") == "event" for r in rows), f"{lat:.0f} ms")

# ---- seal before renew ---------------------------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))


class Runner:
    def __init__(self, rc):
        self.rc = rc

    def __call__(self, argv, cwd, timeout):
        return self.rc, "tail"


def gitf(*a):
    return "H1" if a[0] == "rev-parse" else "c1"


def seal_setup(name, rc):
    d, p, chain = setup(name)
    chain["units"][0]["acceptance"] = {"gates": [["x"]], "require_commit": True}
    p.write_text(json.dumps(chain), encoding="utf-8")
    (d / "R-A.md").write_text("# A\nall done, no status line\n", encoding="utf-8")
    gm._chain_try_seal = lambda pkt: gc.try_seal(pkt, missions=[], runner=Runner(rc), git=gitf)
    return d, {"mission_id": "m", "wu_packet": {"path": chain["units"][0]["packet"]}}


# the receipt path rule of gsd_mission is <stem>-receipt.md, so mirror it
d, p, chain = setup("seal-ok")
chain["units"][0]["receipt"] = str(d / "WU-A-receipt.md")
chain["units"][0]["acceptance"] = {"gates": [["x"]], "require_commit": True}
p.write_text(json.dumps(chain), encoding="utf-8")
(d / "WU-A-receipt.md").write_text("# A\nall done, no status line\n", encoding="utf-8")
rec = {"mission_id": "m", "wu_packet": {"path": chain["units"][0]["packet"]}}
gm._chain_try_seal = lambda pkt: gc.try_seal(pkt, missions=[], runner=Runner(0), git=gitf)
row = {}
gm.halt_continue(rec, str(d), "", None, row, time.time())
check("V-APR3-SEAL-BEFORE-RENEW-EVIDENCE-PASSES", row.get("renewal") == "not renewed: sealed by finalizer"
      and "renewed_as" not in row and (d / "WU-A-receipt.md.seal.json").exists(), json.dumps(row)[:140])
d, p, chain = setup("seal-bad")
chain["units"][0]["receipt"] = str(d / "WU-A-receipt.md")
chain["units"][0]["acceptance"] = {"gates": [["x"]], "require_commit": True}
p.write_text(json.dumps(chain), encoding="utf-8")
(d / "WU-A-receipt.md").write_text("# A\nall done, no status line\n", encoding="utf-8")
rec = {"mission_id": "m", "wu_packet": {"path": chain["units"][0]["packet"]}}
gm._chain_try_seal = lambda pkt: gc.try_seal(pkt, missions=[], runner=Runner(1), git=gitf)
row = {}
went_on = not gm._seal_instead_of_renew(rec, row)
check("V-APR3-SEAL-BEFORE-RENEW-EVIDENCE-FAILS-RENEWS", went_on and not (d / "WU-A-receipt.md.seal.json").exists(),
      json.dumps(row)[:140])
gm._chain_try_seal = lambda pkt: 1 / 0
row = {}
check("V-APR3-SEAL-RAISES-RENEWS-AS-TODAY", not gm._seal_instead_of_renew(rec, row) and "seal_attempt" in row)

# ---- bounded silence -----------------------------------------------------------------------------------------------
chain = {"goal": "s", "silence_s": 1800, "wait_timeout_s": 21600}
hist = [{"action": "human_gate", "unit": "A", "at": 1000 + 600 * i} for i in range(5)]
row = {"action": "human_gate", "unit": "A"}
check("V-APR3-SILENT-PAST-WINDOW-ALERTS", gc.silence_check(chain, row, hist, 1000 + 3000))
check("V-APR3-WITHIN-WINDOW-QUIET", not gc.silence_check(chain, row, hist, 1000 + 1000))
check("V-APR3-ONE-ALERT-PER-KEY", not gc.silence_check(chain, row, hist[:-1] + [{**hist[-1], "alerted": True}], 1000 + 3000))
check("V-APR3-RUNNING-NEVER-SILENT", not gc.silence_check(chain, {"action": "running", "unit": "A"},
                                                          [{"action": "running", "unit": "A", "at": 1}], 10**7))
w = [{"action": "wait_event", "unit": "A", "at": 1000}]
check("V-APR3-WAIT-EVENT-TIMES-OUT", gc.silence_check(chain, {"action": "wait_event", "unit": "A"}, w, 1000 + 21601)
      and not gc.silence_check(chain, {"action": "wait_event", "unit": "A"}, w, 1000 + 21000))
d, p, c = setup("silent", silence_s=10)
alerts = []
(d / "R-A.md").write_text("Status: BLOCKED_HUMAN\n", encoding="utf-8")
r = gc.tick(p, state=lambda: ([mission(d, "A", "HALTED")], 0), history=[{"action": "stopped_without_done", "unit": "A", "at": 1}],
            alerter=alerts.append, now=1000)
check("V-APR3-TICK-WRITES-ALERT-AND-MARKS-ROW", r["action"] in gc.SILENT and r.get("alerted") and len(alerts) == 1, r["action"])

# ---- reforecast ----------------------------------------------------------------------------------------------------
# overspent first unit: A target 1M measured 3M -> overrun 3.0; B,C,D 1M each -> forecast 9M > envelope left
d, p, c = setup("fc-over", n=4, envelope=10_000_000)
(d / "R-A.md").write_text("Status: DONE\n", encoding="utf-8")
r = gc.tick(p, state=lambda: ([], 3_000_000), armer=good_arm, measured={"A": 3_000_000}, ledger=None)
check("V-APR3-OVERSPENT-PAUSES", r["action"] == "pause_budget" and r["overrun"] == 3.0 and r["forecast"] == 9_000_000, json.dumps(r)[:200])
calls = []
r = gc.tick(p, state=lambda: ([], 1_000_000), armer=good_arm, measured={"A": 900_000})
check("V-APR3-CHEAP-FIRST-ARMS", r["action"] == "arm" and r["overrun"] == 1.0 and r["forecast"] == 3_000_000
      and r["forecast_basis"] == "measured" and len(calls) == 1, json.dumps(r)[:200])
r = gc.tick(p, state=lambda: ([], 0), armer=good_arm, measured={})
check("V-APR3-UNMEASURED-IS-SAID", r["forecast_basis"] == "unmeasured" and r["overrun"] == 1.0, r.get("forecast_basis"))

# ---- status ---------------------------------------------------------------------------------------------------------
d, p, c = setup("stat")
(d / "R-A.md").write_text("Status: DONE\n", encoding="utf-8")
ms = [mission(d, "B", "RUNNING", owner={"session_id": "own-sid-1"})]
s = gc.status(p, state=lambda: (ms, 2_000_000), history=[{"action": "arm", "unit": "B", "at": 5000, "trigger": "event"}],
              measured={"A": 1_500_000}, open_sids={"own-sid-1": 5, "stranger-sid": 7}, git=lambda *a: "6000", now=7000)
print(json.dumps(s, indent=1))
check("V-APR3-STATUS-SHAPE", s["current_unit"] == "B" and s["decision"] == "running" and s["units"][0]["done"]
      and s["last_progress_at"] >= 6000 and s["last_action"]["age_s"] == 2000 and s["envelope"]["overrun"] == 1.5
      and s["envelope"]["remaining"] == 38_000_000 and s["next_expected_event"], "")
check("V-APR3-FOREIGN-BINDINGS", [b["sid"] for b in s["foreign_bindings"]] == ["stranger"], str(s["foreign_bindings"]))

print(f"{passes} pass / {fails} fail")
sys.exit(1 if fails else 0)
