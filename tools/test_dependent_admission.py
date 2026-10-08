#!/usr/bin/env python
"""V-DEP-* gates: a successor mission is admitted against its predecessor's METERED receipt
(tools/route_admission.py dependent_admission, wired in tools/gsd_mission.py admit_route), spec
expected-completion-admission.md unit E3, canaries 8 and 9.

Canary 8: predecessor metered over its target -> successor ESCALATE.
Canary 9: predecessor metered within target -> successor admitted on its own forecast.
Absent receipt -> ESCALATE (UNKNOWN), never admitted.

Hermetic like test_gsd_mission_admission.py: state in a temp dir BEFORE import, no real worker.
Mutation drills: the script re-runs itself with a mutated COPY of route_admission.py on sys.path
(CPP_DEP_DRILL_DIR); each canary must go red under its own mutant and the live module is never touched.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRILL = os.environ.get("CPP_DEP_DRILL_DIR")
TMP = tempfile.mkdtemp(prefix="dependent-admission-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
os.environ.pop("CPP_ROUTE_ADMISSION", None)
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
sys.path.insert(0, str(HERE))
if DRILL:
    sys.path.insert(0, DRILL)
import route_admission as ra  # noqa: E402  (first, so a drill copy wins the sys.modules slot gsd_mission reuses)
import gsd_mission as gm  # noqa: E402
import envelope_fixture  # noqa: E402
envelope_fixture.bound_missions(gm)
assert not DRILL or Path(ra.__file__).resolve().parent == Path(DRILL).resolve(), ra.__file__

gm.progress_fingerprint = lambda work_dir: None
FLOORS = str(HERE.parent / "vault" / "config" / "route-floors.json")
NOW = 1_800_000_000.0
ENV = {"target": 5_000_000, "warn": 6_000_000, "stop": 7_000_000, "calls": 40}
ROUTE = {"envelope": ENV, "workers": [{"name": "w0", "profile": "top-level-worker", "calls": 20, "packet": 4000}]}
SPENT = {"m-pred-over": 5_800_000, "m-pred-within": 4_000_000, "m-pred-zero": 0}
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def write(name: str, obj) -> str:
    p = Path(TMP) / name
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")
    return str(p)


def mission(mid: str, packet: bool, estimate: int | None = None) -> None:
    gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                  state=gm.RUNNING, epoch=1)
    if packet:
        gm.set_envelope(mid, wu_packet=write(f"{mid}-WU.md", f"# WU {mid}\n"), now=NOW)
    if estimate:
        gm.set_envelope(mid, token_estimate=estimate, now=NOW)


def metered(rec: dict):
    """The meter, by mission: only the predecessor's receipt has a number; the successor has spent nothing."""
    return SPENT.get(rec["mission_id"], 0 if rec["mission_id"].startswith("m-succ") else None)


def admit(mid: str, **kw) -> dict:
    return gm.admit_route(mid, write(f"{mid}-route.json", ROUTE), floors_path=FLOORS, now=NOW,
                          measure=kw.pop("measure", metered), **kw)["admission"]


def own() -> str:
    return ra.admit(ROUTE, ra.load_floors(FLOORS))["verdict"]


def main() -> int:
    # 0. the pure judge, both poles
    over = ra.dependent_admission(5_800_000, 5_000_000)
    within = ra.dependent_admission(4_000_000, 5_000_000)
    absent = ra.dependent_admission(None, 5_000_000)
    check("V-DEP-PURE-OVER", over["verdict"] == ra.ESCALATE, str(over))
    check("V-DEP-PURE-WITHIN", within["verdict"] is None and "own forecast" in within["reason"], str(within))
    check("V-DEP-PURE-ABSENT-IS-UNKNOWN", absent["verdict"] == ra.ESCALATE and absent["basis"] == "unmeasured", str(absent))
    zero = ra.dependent_admission(0, 5_000_000)
    check("V-DEP-PURE-ZERO-IS-A-MEASUREMENT", zero["verdict"] is None and zero["basis"].startswith("measured"), str(zero))
    check("V-DEP-PURE-NO-TARGET", ra.dependent_admission(1, None)["verdict"] == ra.ESCALATE)

    # 1. the control: the route alone is admissible, so a refusal below is the receipt's doing
    check("V-DEP-CONTROL-OWN-FORECAST-ADMISSIBLE", own() == ra.ADMISSIBLE, own())
    mission("m-succ-none", True)
    plain = admit("m-succ-none")
    check("V-DEP-NO-DEPENDENCY-UNCHANGED", plain["verdict"] == ra.ADMISSIBLE and "dependent" not in plain, str(plain["verdict"]))

    # 2. canary 8: predecessor metered over its target -> successor ESCALATE
    mission("m-pred-over", False, estimate=5_000_000)
    mission("m-succ-8", True)
    c8 = admit("m-succ-8", depends_on="m-pred-over")
    check("V-DEP-CANARY-8", c8["verdict"] == ra.ESCALATE and c8["dependent"]["spent"] == 5_800_000
          and "metered 5,800,000" in c8["reasons"][0], str(c8["reasons"][:1]))
    check("V-DEP-CANARY-8-NOT-LAUNCHABLE", gm.admission_refusal(gm.load("m-succ-8")) is not None)

    # 3. canary 9: predecessor within target -> admitted on its own forecast
    mission("m-pred-within", False, estimate=5_000_000)
    mission("m-succ-9", True)
    c9 = admit("m-succ-9", depends_on="m-pred-within")
    check("V-DEP-CANARY-9", c9["verdict"] == ra.ADMISSIBLE and c9["dependent"]["spent"] == 4_000_000, str(c9["verdict"]))
    check("V-DEP-CANARY-9-LAUNCHABLE", gm.admission_refusal(gm.load("m-succ-9")) is None)

    # 4. absent receipt -> UNKNOWN, never admitted (no such predecessor, and one the meter cannot read)
    mission("m-succ-ghost", True)
    ghost = admit("m-succ-ghost", depends_on="m-no-such-pred")
    check("V-DEP-ABSENT-PREDECESSOR-ESCALATES", ghost["verdict"] == ra.ESCALATE and ghost["dependent"]["basis"] == "unmeasured",
          str(ghost["reasons"][:1]))
    mission("m-pred-unread", False, estimate=5_000_000)
    mission("m-succ-unread", True)
    unread = admit("m-succ-unread", depends_on="m-pred-unread")
    check("V-DEP-UNMETERED-PREDECESSOR-ESCALATES", unread["verdict"] == ra.ESCALATE, str(unread["reasons"][:1]))

    # 5. the estimate is not the receipt: a predecessor that declared 5M but metered 5.8M is over
    check("V-DEP-ESTIMATE-IS-NOT-SPEND", gm.load("m-pred-over")["token_estimate"] == 5_000_000
          and c8["dependent"]["spent"] > gm.load("m-pred-over")["token_estimate"])

    # 6. a recorded depends_on is honoured without the kwarg
    mission("m-succ-rec", True)
    gm.transition("m-succ-rec", expect_epoch=1, expect_state=gm.RUNNING, event="t_dep", now=NOW, depends_on="m-pred-over")
    rec8 = admit("m-succ-rec")
    check("V-DEP-RECORDED-DEPENDENCY", rec8["verdict"] == ra.ESCALATE, str(rec8["verdict"]))

    print(f"DEPENDENT_ADMISSION_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


MUTANTS = [
    ("canary 8 (over target admitted)", "V-DEP-CANARY-8",
     "if pred_spent > pred_target:", "if pred_spent > pred_target * 1000:"),
    ("canary 9 (within target refused)", "V-DEP-CANARY-9",
     '    return {"verdict": None, "basis": "measured:mission_spend"',
     '    return {"verdict": ESCALATE, "basis": "measured:mission_spend"'),
    ("absent receipt read as zero", "V-DEP-UNMETERED-PREDECESSOR-ESCALATES",
     "if pred_spent is None or not _ok(pred_target):",
     "pred_spent = 0 if pred_spent is None else pred_spent\n    if not _ok(pred_target):"),
]


def drills() -> int:
    src = (HERE / "route_admission.py").read_text(encoding="utf-8")
    bad = 0
    for label, gate, old, new in MUTANTS:
        if src.count(old) != 1:
            print(f"FAIL V-DEP-DRILL-ANCHOR {label}: anchor found {src.count(old)} times")
            bad += 1
            continue
        d = Path(tempfile.mkdtemp(prefix="dep-drill-"))
        (d / "route_admission.py").write_text(src.replace(old, new), encoding="utf-8")
        r = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve())], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300, env={**os.environ, "CPP_DEP_DRILL_DIR": str(d)})
        red = f"FAIL {gate} " in r.stdout and r.returncode != 0
        print(f"{'PASS' if red else 'FAIL'} V-DEP-DRILL {label}: {gate} goes red under the mutant")
        bad += not red
    return bad


if __name__ == "__main__":
    rc = main()
    if rc == 0 and not DRILL:
        rc = 1 if drills() else 0
    raise SystemExit(rc)
