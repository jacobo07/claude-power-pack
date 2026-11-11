#!/usr/bin/env python3
"""Gate for the Ascension Autopilot (V-AP-*). Runs against a scratch HOME/STATE_DIR with fake mission records; never
touches real missions (gm/judge/plan are stubbed). Ends with a mutation drill: each guard disabled must turn tests red."""
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
tmp = Path(tempfile.mkdtemp(prefix="ap-test-"))
os.environ.update(AP_HOME=str(tmp / "home"), AP_STATE_DIR=str(tmp / "state"), AP_OWNER_TS="2026-11-11T00:00:00.000Z")
(tmp / "home").mkdir()
(tmp / "state").mkdir()


def load():
    spec = importlib.util.spec_from_file_location("ap", HERE / "autopilot.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


GOOD = ["Phase 1: K1 freeze cohort (cap 3M): commit pool before draw; gate tools/test_k1.py with planted mutants",
        "Phase 2: K2 run (cap 10M): unchanged certify path; gate tools/test_k2.py",
        "Phase 3: K3 checkpoint (cap 2M): re-run gates, checkpoint file, CHECKPOINT_COMPLETE"]
PROFILE_OK = ["Phase 1: P1 new additive profile (cap 5M): independent target oracle on original DOL bytes; frozen pilot "
              "committed before the draw; pre/post controls; A2 negatives; historical receipts byte-identical; separate counters",
              "Phase 2: P2 checkpoint (cap 2M): gates"]
results = []


def check(name, cond):
    results.append((name, bool(cond)))


def run_all(ap):
    results.clear()
    check("V-AP-POLICY-ADMITS-GOOD", ap.policy_check(GOOD, "") == [])
    check("V-AP-POLICY-ADMITS-PROFILE-WITH-ALL-CONDITIONS", ap.policy_check(PROFILE_OK, "") == [])
    for label, line in [("push", "then git push the branch"), ("merge", "merge the 582 into the headline counter"),
                        ("revoke", "revoke contradicted certificates"), ("R2", "open R2 for the ctx"),
                        ("H2", "rebuild H2"), ("certifier", "modify certify.py to admit arm choice"),
                        ("canon", "change the canonical ctx headers"), ("paid", "use paid API for speed"),
                        ("budget", "raise the budget to 40M")]:
        bad = GOOD[:2] + [GOOD[2] + "; " + line]
        check(f"V-AP-POLICY-REFUSES-{label.upper()}", ap.policy_check(bad, "") != [])
    for cond in ["oracle", "DOL", "frozen pilot", "controls", "A2 negatives", "receipts byte-identical", "separate counters"]:
        line = PROFILE_OK[0].replace(cond, "zzz") if cond != "frozen pilot" else PROFILE_OK[0].replace("frozen pilot", "pilot")
        if cond == "A2 negatives":
            line = PROFILE_OK[0].replace("A2 negatives", "zzz")
        check(f"V-AP-PROFILE-NEEDS-{cond.upper().replace(' ', '-')}", ap.policy_check([line, PROFILE_OK[1]], "") != [])
    check("V-AP-POLICY-REFUSES-OVER-GEN-CAP", ap.policy_check(
        ["Phase 1: a (cap 20M): x", "Phase 2: b (cap 6M): y"], "") != [])
    check("V-AP-POLICY-REFUSES-NO-CAP", ap.policy_check(["Phase 1: a: x", "Phase 2: b (cap 1M): y"], "") != [])
    check("V-AP-POLICY-REFUSES-ONE-PHASE", ap.policy_check(["Phase 1: a (cap 1M): x"], "") != [])
    check("V-AP-POLICY-REFUSES-FRESH-OVER-1M", ap.policy_check(
        ["Phase 1: a (cap 3M): fresh 2M model pilot", "Phase 2: b (cap 1M): y"], "") != [])
    check("V-AP-POLICY-REFUSES-COMMAND-PUSH", ap.policy_check(GOOD, "and push when done") != [])
    now = 1794400000.0  # 2026-11-11
    day = [{"ts": now, "tokens": 60_000_000}]
    check("V-AP-BUDGET-DAY-REFUSES", ap.budget_admits(day, now, 25_000_000) is not None)
    check("V-AP-BUDGET-DAY-ADMITS", ap.budget_admits(day, now, 20_000_000) is None)
    check("V-AP-BUDGET-NEXT-DAY-ADMITS", ap.budget_admits(day, now + 86400, 25_000_000) is None)
    many = [{"ts": now - 86400 * k, "tokens": 79_000_000} for k in range(1, 6)]  # 395M on earlier days
    check("V-AP-BUDGET-TOTAL-REFUSES", ap.budget_admits(many, now, 25_000_000) is not None)
    check("V-AP-BUDGET-WALL-REFUSES", ap.budget_admits([], 1796083200.0, 1) is not None)  # 2026-12-01
    check("V-AP-LASTJSON", ap.last_json('blah {"a": {"b": 1}} more {"verdict": "AGREE", "x": [1, {"y": 2}]}')
          == {"verdict": "AGREE", "x": [1, {"y": 2}]})
    # lane transitions with stubs
    lanes = [{"name": "L", "letter": "K", "cwd": str(tmp / "cwd"), "product": str(tmp / "cwd"), "packet_dir": "v",
              "mission": "m-aaaaaaaaaaaa"}]
    (tmp / "cwd").mkdir(exist_ok=True)
    rec = {"mission_id": "m-aaaaaaaaaaaa", "state": "RUNNING", "owner_hold": {"kind": "checkpoint", "set_at": 1,
           "evidence": str(tmp / "ck.md")}}
    (tmp / "state" / "gsd-mission-m-aaaaaaaaaaaa.json").write_text(json.dumps(rec))
    calls = []
    ap.gm = lambda *a, **k: (calls.append(a) or (0, '"mission_id": "m-bbbbbbbbbbbb"'))
    ap.sh = lambda cmd, **k: (0, "")
    ap.mission_spend = lambda m: 1
    ap.write_packet = lambda lane, name, p: Path(lane["cwd"]) / "v" / f"{name}.md"

    def fresh_state():
        for f in ("state.json", "ledger.jsonl", "owner_queue.md", "digest.md", "autopilot.log"):
            (tmp / "home" / f).unlink(missing_ok=True)
        calls.clear()
    fresh_state()
    ap.judge = lambda *a: {"verdict": "DISAGREE", "notes": "x", "_tokens": 5}
    st = {}
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-DISAGREE-PARKS", st["lanes"]["L"]["status"] == "PARKED" and not any(c[0] == "arm" for c in calls))
    fresh_state()
    ap.judge = lambda *a: {"verdict": "AGREE", "new_canonical_certs": 0, "validated_capability": False, "_tokens": 5}
    ap.plan = lambda *a: {"title": "t", "facts": [], "phases": GOOD, "_tokens": 7}
    st = {}
    for k in range(3):
        st.setdefault("lanes", {}).setdefault("L", {})["judged_for"] = None
        st["lanes"]["L"]["status"] = "WAITING"
        rec["owner_hold"]["set_at"] = k + 10
        rec["state"] = "RUNNING"
        (tmp / "state" / "gsd-mission-m-aaaaaaaaaaaa.json").write_text(json.dumps(rec))
        st["lanes"]["L"]["mission"] = "m-aaaaaaaaaaaa"
        ap.lane_tick(st, lanes[0], False)
    check("V-AP-THREE-BLANK-STOPS", st["lanes"]["L"]["status"] == "STOPPED")
    fresh_state()
    ap.judge = lambda *a: {"verdict": "AGREE", "new_canonical_certs": 3, "validated_capability": False, "_tokens": 5}
    st = {}
    rec["owner_hold"]["set_at"] = 99
    (tmp / "state" / "gsd-mission-m-aaaaaaaaaaaa.json").write_text(json.dumps(rec))
    ap.lane_tick(st, lanes[0], False)
    acts = [c[0] for c in calls]
    check("V-AP-ARM-SEQUENCE", acts[:3] == ["close", "arm", "authority"] and st["lanes"]["L"]["status"] == "RUNNING"
          and st["lanes"]["L"]["mission"] == "m-bbbbbbbbbbbb")
    auth = [c for c in calls if c[0] == "authority"][0]
    check("V-AP-AUTHORITY-IS-PHASE-CAPS", auth[auth.index("--tokens") + 1] == str(15_000_000))
    check("V-AP-OWNER-TURN-PASSED", "--owner-turn" in auth)
    fresh_state()
    ap.plan = lambda *a: {"title": "t", "facts": [], "phases": GOOD[:2] + [GOOD[2] + " then git push"], "_tokens": 7}
    st = {}
    rec["owner_hold"]["set_at"] = 100
    (tmp / "state" / "gsd-mission-m-aaaaaaaaaaaa.json").write_text(json.dumps(rec))
    ap.lane_tick(st, lanes[0], False)
    check("V-AP-POLICY-BLOCKS-ARM", st["lanes"]["L"]["status"] == "PARKED" and not any(c[0] in ("close", "arm") for c in calls))
    fresh_state()
    (tmp / "home" / "OFF").write_text("")
    (tmp / "home" / "lanes.json").write_text(json.dumps(lanes))
    ap.judge = lambda *a: (_ for _ in ()).throw(AssertionError("judge must not run when OFF"))
    ok = True
    try:
        ap.main(["x", "tick"])
    except AssertionError:
        ok = False
    check("V-AP-KILL-SWITCH", ok and not calls)
    (tmp / "home" / "OFF").unlink()
    return [n for n, ok in results if not ok]


fails = run_all(load())
for n, ok in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"{len(results) - len(fails)}/{len(results)}")
# mutation drill: disabling each guard must make the suite fail
drill = {"policy_off": lambda m: setattr(m, "policy_check", lambda *a: []),
         "budget_off": lambda m: setattr(m, "budget_admits", lambda *a, **k: None),
         "blank_off": lambda m: setattr(m, "BLANK_STOP", 99),
         "profile_off": lambda m: setattr(m, "PROFILE_CONDITIONS", {})}
survivors = []
for name, mut in drill.items():
    m = load()
    mut(m)
    if not run_all(m):
        survivors.append(name)
print("MUTANTS SURVIVED:", survivors or "none")
ok = not fails and not survivors
print("AUTOPILOT_GATE_PASS" if ok else "AUTOPILOT_GATE_FAIL")
sys.exit(0 if ok else 1)
