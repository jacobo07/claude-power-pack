"""V-APR2-* gates: machine seal, false-DONE refusal, residual classes (hermetic: injected runner, git, state)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsdx_chain as gc  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="apr-seal-test-"))
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
    chain = {"goal": "g", "root": str(d), "envelope": 40_000_000, "units": units, **extra}
    p = d / "chain.json"
    p.write_text(json.dumps(chain), encoding="utf-8")
    return d, p, chain


def mission(d, uid, state="COMPLETED", suffix="", n=1, **kw):
    return {"mission_id": f"m-{uid}{n}", "cwd": str(d), "state": state, "created_at": 1000 + n,
            "wu_packet": {"path": str(d / f"WU-{uid}.md") + suffix}, **kw}


class Runner:
    def __init__(self, rc=0, tail="", timeout=False):
        self.calls, self.rc, self.tail, self.timeout = 0, rc, tail, timeout

    def __call__(self, argv, cwd, timeout):
        self.calls += 1
        return (-1, "gate timeout") if self.timeout else (self.rc, self.tail)


def git(commits=("c1",), head="H1"):
    def g(*a):
        return head if a[0] == "rev-parse" else "\n".join(commits)
    return g


armed = []
arm = lambda chain, u: armed.append((u["id"], u["route"])) or {"ok": True, "mission_id": "m-new"}  # noqa: E731


def tick(p, ms, runner, g=None, **kw):
    armed.clear()
    return gc.tick(p, state=lambda: (ms, 0), armer=arm, **({"gate_runner": runner, "git": g or git()} | kw))


# 1. E2-shaped: receipt without Status, commit present, gate passes -> sealed, successor armed
d, p, _ = setup("e2")
(d / "R-A.md").write_text("# A receipt\nall done, no status line\n", encoding="utf-8")
r = tick(p, [mission(d, "A")], Runner())
seal = gc._jload(str(d / "R-A.md") + ".seal.json") or {}
check("V-APR2-E2-SEAL-ARMS", r["action"] == "arm" and r["unit"] == "B" and seal.get("verdict") == "DONE"
      and seal.get("sealed_by") == "gsdx_chain.finalize" and seal.get("receipt_sha256") and seal.get("commits"), json.dumps(r)[:140])
check("V-APR2-RECEIPT-BYTES-UNTOUCHED", (d / "R-A.md").read_text(encoding="utf-8") == "# A receipt\nall done, no status line\n")

# 2. false DONE: Status DONE, gate exits 1 -> no successor, refusal on disk, class FALSE_DONE
d, p, _ = setup("fd")
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
r = tick(p, [mission(d, "A")], Runner(1, "boom"))
ref = gc._jload(str(d / "R-A.md") + ".refusal.json") or {}
check("V-APR2-FALSE-DONE-REFUSED", ref.get("verdict") == "FALSE_DONE" and not armed and r["action"] != "arm"
      and r.get("unit") == "A", json.dumps(r)[:160])

# 3. deadlock: FALSE_DONE has no steward; residual must arm (max_residuals 1) from the finalizer-written packet
d, p, _ = setup("fd-res", max_residuals=1, route_ladder=[])
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
r = tick(p, [mission(d, "A")], Runner(1, "boom"))
resf = Path(str(d / "WU-A.md") + ".residual.md")
txt = resf.read_text(encoding="utf-8") if resf.exists() else ""
check("V-APR2-FALSE-DONE-NO-STEWARD-DEADLOCK", r["action"] == "arm" and r.get("class") == "FALSE_DONE" and r.get("receipt") == "FALSE_DONE"
      and "## Residual" in txt and "m-A1" in txt and "boom" in txt and "refusal.json" in txt and "# packet A" in txt
      and armed and armed[0][0] == "A", json.dumps(r)[:200])

# 4. controls: DONE + passing gate arms successor; no seal/refusal written
d, p, _ = setup("ok")
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
r = tick(p, [mission(d, "A")], Runner())
check("V-APR2-DONE-PASSING-ARMS", r["action"] == "arm" and r["unit"] == "B"
      and not Path(str(d / "R-A.md") + ".refusal.json").exists(), r["action"])

# 5. no acceptance anywhere: behaviour unchanged, runner never called
d, p, _ = setup("none", acceptance=False)
(d / "R-A.md").write_text("# A\nno status\n", encoding="utf-8")
run = Runner()
r = tick(p, [mission(d, "A")], run)
check("V-APR2-NO-ACCEPTANCE-UNCHANGED", r["action"] == "stopped_without_done" and run.calls == 0 and not armed, r["action"])

# 6. cache: unchanged (receipt sha, HEAD) -> gates not re-run; new HEAD -> re-run
d, p, _ = setup("cache")
(d / "R-A.md").write_text("# A\nno status\n", encoding="utf-8")
run = Runner()
tick(p, [mission(d, "A")], run)
tick(p, [mission(d, "A")], run)
tick(p, [mission(d, "A")], run)
check("V-APR2-CACHE-NO-RERUN", run.calls == 1, f"calls={run.calls}")
tick(p, [mission(d, "A")], run, git(head="H2"))
check("V-APR2-CACHE-NEW-HEAD-RERUNS", run.calls == 2, f"calls={run.calls}")
d, p, _ = setup("cache-fail")
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
run = Runner(1, "x")
tick(p, [mission(d, "A")], run)
tick(p, [mission(d, "A")], run)
check("V-APR2-CACHE-REFUSAL-NO-RERUN", run.calls == 1, f"calls={run.calls}")

# 7. timeout -> refusal with reason, not a crash
d, p, _ = setup("timeout")
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
r = tick(p, [mission(d, "A")], Runner(timeout=True))
ref = gc._jload(str(d / "R-A.md") + ".refusal.json") or {}
check("V-APR2-GATE-TIMEOUT-REFUSES", ref.get("reason") == "gate timeout" and not armed, json.dumps(r)[:120])

# 8. require_commit: gates pass but no commit -> not sealed
d, p, _ = setup("nocommit")
(d / "R-A.md").write_text("# A\nno status\n", encoding="utf-8")
r = tick(p, [mission(d, "A")], Runner(), git(commits=()))
check("V-APR2-REQUIRE-COMMIT", not Path(str(d / "R-A.md") + ".seal.json").exists() and not armed, r["action"])

# 9. repeated fingerprint: first residual climbs, the same failure on the top rung -> human_gate
lad = lambda d: [str(d / "r1.json"), str(d / "r2.json")]  # noqa: E731
d, p, ch = setup("hg", max_residuals=3)
for n in (1, 2):
    (d / f"r{n}.json").write_text(json.dumps({"envelope": {"target": 1}}), encoding="utf-8")
ch["route_ladder"] = lad(d)
ch["units"][0]["route"] = ch["route_ladder"][0]
p.write_text(json.dumps(ch), encoding="utf-8")
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
r = tick(p, [mission(d, "A")], Runner(1, "same"), git(head="H1"))
(d / "R-A.md").write_text("# A\nStatus: DONE\nattempt 2\n", encoding="utf-8")
ms = [mission(d, "A"), mission(d, "A", suffix=".residual.md", n=2)]
r2 = tick(p, ms, Runner(1, "same"), git(head="H2"))
check("V-APR2-REPEAT-FP-HUMAN-GATE", r["action"] == "arm" and r["route"] == ch["route_ladder"][1]
      and r2["action"] == "human_gate" and r2["why"] == "same failure on every rung" and r2["evidence"] and not armed, json.dumps(r2)[:200])
# positive control: a DIFFERENT failure the second time is not a human gate
(d / "R-A.md").write_text("# A\nStatus: DONE\nattempt 3\n", encoding="utf-8")
ms = [mission(d, "A"), mission(d, "A", suffix=".residual.md", n=2), mission(d, "A", suffix=".residual.md", n=3)]
r3 = tick(p, ms, Runner(1, "different"), git(head="H3"))
check("V-APR2-DIFFERENT-FP-NOT-GATE", r3["action"] != "human_gate", r3["action"])

# 10. residual classes
d, p, _ = setup("cls", acceptance=False, max_residuals=1)
rc = lambda r: r.get("class")  # noqa: E731
(d / "R-A.md").write_text("# A\nno status\n", encoding="utf-8")
c1 = tick(p, [mission(d, "A")], None)
(d / "R-A.md").unlink()
c2 = tick(p, [mission(d, "A")], None)
c3 = tick(p, [mission(d, "A", "HALTED")], None)
check("V-APR2-CLASSES", (rc(c1), rc(c2), rc(c3)) == ("UNCLOSED_RECEIPT", "NO_RECEIPT", "WORKER_STOPPED"), f"{rc(c1)},{rc(c2)},{rc(c3)}")

# 11. try_seal for APR-3
d, p, _ = setup("tryseal")
(d / "R-A.md").write_text("# A\nno status\n", encoding="utf-8")
r = gc.try_seal(d / "WU-A.md", missions=[mission(d, "A", "HALTED")], runner=Runner(), git=git())
check("V-APR2-TRY-SEAL", r["sealed"] is True and Path(r["seal"]).exists(), json.dumps(r)[:120])
d, p, _ = setup("tryseal-fail")
(d / "R-A.md").write_text("# A\nno status\n", encoding="utf-8")
r = gc.try_seal(d / "WU-A.md", missions=[mission(d, "A", "HALTED")], runner=Runner(1, "no"), git=git())
check("V-APR2-TRY-SEAL-FAILS-CLOSED", r["sealed"] is False, json.dumps(r)[:120])

# 12. real subprocess runner: timeout is awaited (no leak) and a real passing gate passes
rc0, _t = gc._run_gate([sys.executable, "-c", "exit(0)"], str(TMP), 30)
rct, tt = gc._run_gate([sys.executable, "-c", "import time; time.sleep(30)"], str(TMP), 1)
check("V-APR2-REAL-RUNNER", rc0 == 0 and rct == -1 and tt == "gate timeout", f"{rc0},{rct},{tt}")

# REVIEW-APR: an acceptance block with no gates/files/require_commit must not seal (empty contract proves nothing)
d, p, ch = setup("empty")
ch["units"][0]["acceptance"] = {"cwd": str(d)}
p.write_text(json.dumps(ch), encoding="utf-8")
(d / "R-A.md").write_text("# A\nall done, no status line\n", encoding="utf-8")
r = tick(p, [mission(d, "A")], Runner(0))
check("V-APR2-EMPTYACC", r["action"] != "arm" and not (d / "R-A.md.seal.json").exists(), r["action"])

# 15. accepted DONE is sticky across HEAD moves: a later unit's commit must not re-judge it (ewc E3/E4 timeout refusal)
d, p, _ = setup("sticky")
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
run = Runner()
tick(p, [mission(d, "A")], run)
late = Runner(timeout=True)
r = tick(p, [mission(d, "A")], late, git(head="H2"))
check("V-APR2-ACCEPTED-DONE-STICKY", late.calls == 0 and r["action"] == "arm" and r["unit"] == "B"
      and not Path(str(d / "R-A.md") + ".refusal.json").exists(), f"calls={late.calls} {r['action']}")
# control: the receipt changes -> the evidence no longer belongs to it, so the gates run again
(d / "R-A.md").write_text("# A\nStatus: DONE\nedited\n", encoding="utf-8")
tick(p, [mission(d, "A")], late, git(head="H2"))
check("V-APR2-ACCEPTED-DONE-RECEIPT-EDIT-RERUNS", late.calls == 1
      and (gc._jload(str(d / "R-A.md") + ".refusal.json") or {}).get("reason") == "gate timeout", f"calls={late.calls}")
# control: a FAILED done claim still re-runs on a new HEAD (a fix commit must be able to clear it)
d, p, _ = setup("sticky-fail")
(d / "R-A.md").write_text("# A\nStatus: DONE\n", encoding="utf-8")
run = Runner(1, "x")
tick(p, [mission(d, "A")], run)
tick(p, [mission(d, "A")], run, git(head="H2"))
check("V-APR2-FAILED-DONE-NEW-HEAD-RERUNS", run.calls == 2, f"calls={run.calls}")

print(f"{passes} pass / {fails} fail")
sys.exit(1 if fails else 0)
