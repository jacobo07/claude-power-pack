"""V-APR7-* gates: closing the woz VETO + pp-code-reviewer findings on APR-2..4 (hermetic; real processes for the lock)."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsdx_chain as gc  # noqa: E402
import gsd_mission as gm  # noqa: E402

TOOLS = Path(__file__).resolve().parent
TMP = Path(tempfile.mkdtemp(prefix="apr7-test-"))
os.environ["CPP_GSDX_CHAIN_STATE"] = str(TMP / "state")
passes = fails = 0


def check(gate, ok, detail=""):
    global passes, fails
    passes, fails = passes + bool(ok), fails + (not ok)
    print(f"{'PASS' if ok else 'FAIL'} {gate} {detail}")


def setup(name, acceptance=True, **extra):
    d = TMP / name
    d.mkdir()
    route = d / "route.json"
    route.write_text(json.dumps({"envelope": {"target": 1_000_000}}), encoding="utf-8")
    units = []
    for uid in ("A", "B"):
        u = {"id": uid, "packet": str(d / f"WU-{uid}.md"), "route": str(route), "receipt": str(d / f"R-{uid}.md"),
             "after": "A" if uid == "B" else None, "wait": []}
        if uid == "A" and acceptance:
            u["acceptance"] = {"gates": [["python", "-c", "exit(0)"]], "require_commit": True}
        units.append(u)
    (d / "WU-A.md").write_text("# packet A\n", encoding="utf-8")
    chain = {"goal": "g-" + name, "root": str(d), "envelope": 40_000_000, "units": units, **extra}
    p = d / "chain.json"
    p.write_text(json.dumps(chain), encoding="utf-8")
    return d, p, chain


def mission(d, uid, state="COMPLETED", suffix="", n=1, **kw):
    return {"mission_id": f"m-{uid}{n}", "cwd": str(d), "state": state, "created_at": 1000 + n,
            "wu_packet": {"path": str(d / f"WU-{uid}.md") + suffix}, **kw}


class Runner:
    def __init__(self, rc=0, tail=""):
        self.calls, self.rc, self.tail = 0, rc, tail

    def __call__(self, argv, cwd, timeout):
        self.calls += 1
        return (self.rc, self.tail)


def git(commits=("c1",), head="H1"):
    return lambda *a: head if a[0] == "rev-parse" else "\n".join(commits)


armed, alerts = [], []
arm = lambda chain, u: armed.append((u["id"], u["packet"])) or {"ok": True, "mission_id": "m-new"}  # noqa: E731


def tick(p, ms, runner=None, g=None, state=None, **kw):
    armed.clear()
    alerts.clear()
    return gc.tick(p, state=state or (lambda: (ms, 0)), armer=arm, alerter=alerts.append,
                   **({"gate_runner": runner or Runner(), "git": g or git()} | kw))


# 1. dup-arm on the residual path: a base-packet mission appears between decide and _arm
d, p, _ = setup("dup", acceptance=False, max_residuals=1, route_ladder=[])
(d / "R-A.md").write_text("# A\nno status\n", encoding="utf-8")
Path(str(d / "WU-A.md") + ".residual.md").write_text("# res m-A1\n", encoding="utf-8")
ms0 = [mission(d, "A", steward={"done": True})]
calls = []


def racing_state():
    calls.append(1)
    return (ms0 if len(calls) == 1 else ms0 + [mission(d, "A", "RUNNING", n=2)]), 0


r = tick(p, None, state=racing_state)
check("V-APR7-DUP-ARM-BASE-PACKET", r["action"] == "running" and not armed and len(calls) >= 2, json.dumps(r)[:200])

# 2. atomic fact writer: a crash at the rename leaves the old fact intact
f = d / "fact.json"
gc._wr(f, {"v": 1})
real = os.replace
os.replace = lambda *a: (_ for _ in ()).throw(OSError("boom"))
try:
    gc._wr(f, {"v": 2})
except OSError:
    pass
finally:
    os.replace = real
check("V-APR7-ATOMIC-WR", json.loads(f.read_text(encoding="utf-8")) == {"v": 1})

# 3. one lock: two real processes finalize the same unit -> the gates run once, one seal
pd = TMP / "programs"
d3 = pd / "lock"
d3.mkdir(parents=True)
cnt = d3 / "count.txt"
chain3 = {"goal": "g-lock", "root": str(d3), "envelope": 40_000_000, "units": [
    {"id": "A", "packet": str(d3 / "WU-A.md"), "route": str(d3 / "route.json"), "receipt": str(d3 / "R-A.md"), "after": None,
     "wait": [], "acceptance": {"gates": [[sys.executable, "-c",
                                          f"import time;open(r'{cnt}','a').write('x');time.sleep(2)"]], "timeout_s": 30}}]}
(d3 / "chain.json").write_text(json.dumps(chain3), encoding="utf-8")
(d3 / "WU-A.md").write_text("# A\n", encoding="utf-8")
(d3 / "R-A.md").write_text("# A\nno status\n", encoding="utf-8")
code = (f"import sys,json;sys.path.insert(0,r'{TOOLS}');import gsdx_chain as g;"
        f"print(json.dumps(g.try_seal(r'{d3 / 'WU-A.md'}', missions=[], programs_dir=r'{pd}')))")
procs = [subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True, env=os.environ.copy()) for _ in (0, 1)]
outs = [json.loads(pr.communicate(timeout=120)[0].strip().splitlines()[-1]) for pr in procs]
check("V-APR7-ONE-LOCK-TWO-PROCS", len(cnt.read_text()) == 1 and sum(o.get("result") == "sealed" for o in outs) == 1
      and all(o["sealed"] for o in outs), f"runs={len(cnt.read_text())} {outs}")

# 4. seal scope: explicit PARTIAL with passing gates is the worker's verdict
d, p, _ = setup("partial")
(d / "R-A.md").write_text("# A\nStatus: PARTIAL\n", encoding="utf-8")
r = tick(p, [mission(d, "A")])
r2 = gc.try_seal(d / "WU-A.md", missions=[mission(d, "A", "HALTED")], runner=Runner(), git=git(), programs_dir=TMP)
check("V-APR7-PARTIAL-NO-SEAL", not (d / "R-A.md.seal.json").exists() and r["action"] != "arm" and r2["sealed"] is False,
      f"{r['action']} {r2}")
d, p, _ = setup("unreadable")
(d / "R-A.md").write_text("# A\nno status\n", encoding="utf-8")
r2 = gc.try_seal(d / "WU-A.md", missions=[mission(d, "A", "HALTED")], runner=Runner(), git=git(), programs_dir=TMP)
check("V-APR7-UNREADABLE-STILL-SEALS", r2["sealed"] is True, str(r2))

# 5. one fingerprint per attempt (receipt), not per HEAD
d, p, _ = setup("fp")
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
for h in ("H1", "H2", "H3"):
    tick(p, [mission(d, "A")], Runner(1, "same"), git(head=h))
fps = (gc._jload(str(d / "R-A.md") + ".refusal.json") or {}).get("fingerprints") or []
check("V-APR7-FP-PER-ATTEMPT", len(fps) == 1, f"fps={len(fps)}")

# 6. infra is not FALSE_DONE
d, p, _ = setup("infra", max_residuals=2)
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
r = tick(p, [mission(d, "A")], Runner(-1, "gate could not start: [WinError 2]"))
check("V-APR7-INFRA-NO-VERDICT", r["action"] == "gate_infra" and not armed and not (d / "R-A.md.refusal.json").exists()
      and not (d / "R-A.md.seal.json").exists() and not Path(str(d / "WU-A.md") + ".residual.md").exists(), json.dumps(r)[:200])
check("V-APR7-INFRA-ALERTS", len(alerts) >= 1, str(alerts)[:120])
r = tick(p, [mission(d, "A")], Runner(0), git())
check("V-APR7-INFRA-RECOVERS", r["action"] == "arm" and r["unit"] == "B", json.dumps(r)[:160])

# 7. human gate purity
for acc in (False, True):
    d, p, _ = setup(f"human{acc}", acceptance=acc, max_residuals=2, route_ladder=[])
    (d / "R-A.md").write_text("# A\nStatus: BLOCKED_HUMAN\n", encoding="utf-8")
    r = tick(p, [mission(d, "A")])
    check(f"V-APR7-HUMAN-GATE-{acc}", r["action"] == "human_gate" and not armed, json.dumps(r)[:160])
    (d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
    r = tick(p, [mission(d, "A")])
    check(f"V-APR7-HUMAN-RESOLVED-ADVANCES-{acc}", r["action"] == "arm" and r["unit"] == "B", json.dumps(r)[:160])
d, p, _ = setup("exhausted", acceptance=False, max_residuals=1, route_ladder=[])
(d / "R-A.md").write_text("# A\nno status\n", encoding="utf-8")
ms = [mission(d, "A"), mission(d, "A", suffix=".residual.md", n=2)]
r = tick(p, ms)
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
r2 = tick(p, ms)
check("V-APR7-EXHAUSTED-REJUDGED", r["action"] == "residual_exhausted" and r2["action"] == "arm" and r2["unit"] == "B", f"{r['action']} {r2['action']}")

# 8. one owner rule: try_seal finds its chain only through discover_chains
d, p, _ = setup("owner")
(d / "R-A.md").write_text("# A\nno status\n", encoding="utf-8")
empty = TMP / "emptyprograms"
empty.mkdir()
r = gc.try_seal(d / "WU-A.md", missions=[], runner=Runner(), git=git(), programs_dir=empty)
check("V-APR7-ONE-OWNER-RULE", r["sealed"] is False and "not found" in r.get("reason", ""), str(r))

# 9. stale refusal is rewritten even when the gate cache is current; wait_finalizer is silent-class
d, p, _ = setup("stale")
rc = d / "R-A.md"
rc.write_text("# A\nStatus: DONE\n", encoding="utf-8")
gc._wr(str(rc) + ".gate.json", {"sha": gc._sha(rc), "head": "H1", "passed": False, "reason": "gate failed", "commits": ["c1"],
                                "gates": [{"argv": ["x"], "rc": 1, "tail": "t"}]})
gc._wr(str(rc) + ".refusal.json", {"receipt_sha256": "old", "head": "H0", "fingerprints": ["f0"]})
tick(p, [mission(d, "A")], Runner(1, "t"))
check("V-APR7-STALE-REFUSAL-REWRITTEN", (gc._jload(str(rc) + ".refusal.json") or {}).get("receipt_sha256") == gc._sha(rc))
check("V-APR7-WAIT-FINALIZER-SILENT", "wait_finalizer" in gc.SILENT and "gate_infra" in gc.SILENT)

# 9b. A8: a residual packet's receipt is located through the chain unit, judged by receipt_judge
d, p, _ = setup("a8")
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
rec = {"wu_packet": {"path": str(d / "WU-A.md.residual.md")}}
check("V-APR7-A8-RESIDUAL-RECEIPT-VIA-CHAIN", gm._receipt_present(rec, programs_dir=TMP) is True)
(d / "WU-Z.md").write_text("x", encoding="utf-8")
(d / "WU-Z-receipt.md").write_text("# Z\nStatus: DONE\n", encoding="utf-8")
rec = {"wu_packet": {"path": str(d / "WU-Z.md.residual.md")}}
check("V-APR7-A8-RESIDUAL-STEM-FALLBACK", gm._receipt_present(rec, programs_dir=TMP) is True)
rec = {"wu_packet": {"path": str(d / "WU-Q.md.residual.md")}}
check("V-APR7-A8-NO-RECEIPT-STILL-FALSE", gm._receipt_present(rec, programs_dir=TMP) is False)

print(f"{passes} pass / {fails} fail")
sys.exit(1 if fails else 0)
