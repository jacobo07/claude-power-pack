"""WU-S7 tests + mutation drill. Run: python tools/test_autonomy_gates.py  (AUTONOMY_GATES_PASS=n/m)."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import autonomy_gates as ag  # noqa: E402

P = F = 0


def check(name, ok):
    global P, F
    P, F = P + bool(ok), F + (not ok)
    print(("PASS " if ok else "FAIL ") + name)


T = Path(tempfile.mkdtemp(prefix="ag-"))
(T / "p.md").write_text("x")
(T / "r.json").write_text("{}")
(T / "test_good.py").write_text("")
OKSP = {"settled": 10, "reserved": 5, "unknown": 0, "telemetry_ok": True}
GOOD = {"running": [{"id": "m", "heartbeat": 95}], "now": 100, "max_age_s": 60, "active_goals_for_root": 1,
        "size_small_history": 500, "size_large_history": 500,
        "units": [{"id": "U", "packet": str(T / "p.md"), "route": str(T / "r.json"), "receipt": "x"}],
        "guard_modules": ["good"], "tools_dir": str(T), "spend": OKSP, "cap": 100, "action": "running",
        "status_spend": OKSP, "ledger_spend": dict(OKSP)}
v = lambda s, name: next(r["verdict"] for r in ag.run_all(s)["results"] if r["gate"] == name)

check("all green on good state", ag.run_all(GOOD)["green"])
RED = {  # gate -> mutation of GOOD that must turn exactly that gate FAIL
    "duration": {"running": [{"id": "m", "heartbeat": 1}]},
    "goal_count": {"active_goals_for_root": 2},
    "history": {"size_large_history": 9000},
    "capability": {"units": [{"id": "U", "packet": str(T / "nope.md"), "route": str(T / "r.json"), "receipt": "x"}]},
    "test_estate": {"guard_modules": ["good", "untested"]},
    "observability": {"spend": dict(OKSP, settled="UNKNOWN")},
    "wait": {"action": "stopped_without_done"},
    "control": {"cap": 5},
    "spend_agreement": {"status_spend": dict(OKSP, settled="UNKNOWN"), "ledger_spend": dict(OKSP, settled=5996557)},
}
for gate, mut in RED.items():
    s = dict(GOOD, **mut)
    check(f"red:{gate}", v(s, gate) == "FAIL")
    check(f"missing-input-not-pass:{gate}", all(r["verdict"] != "PASS" for r in ag.run_all({})["results"]))
check("spend agreement detects differing numbers",
      v(dict(GOOD, status_spend=dict(OKSP, settled=1)), "spend_agreement") == "FAIL")
check("wait: waiting without event fails", v(dict(GOOD, action="wait_event"), "wait") == "FAIL")
check("wait: waiting with event passes", v(dict(GOOD, action="wait_event", wait_event="receipt"), "wait") == "PASS")
c = ag.reflex_coverage()
check("reflex coverage is a number with every class covered", c["covered"] == c["total"] and c["total"] >= 8)
check("reflex coverage drops when evidence is missing", ag.reflex_coverage(tools_dir=T, tests_dir=T)["covered"] == 0)

# mutation drill: neutering every gate to PASS must break the red checks above (proves the checks bite)
orig = list(ag.GATES)
ag.GATES[:] = [lambda s, n=g.__name__: {"gate": n[2:], "verdict": "PASS", "why": ""} for g in orig]
bitten = sum(v(dict(GOOD, **m), g) == "PASS" for g, m in RED.items())
ag.GATES[:] = orig
check("mutation drill: neutered gates let every red state through", bitten == len(RED))
print(f"AUTONOMY_GATES_PASS={P}/{P + F}")
sys.exit(1 if F else 0)
