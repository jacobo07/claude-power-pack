#!/usr/bin/env python
"""V-VERDICT-* gates: one verdict contract between tools/route_admission.py (what it can emit) and
tools/gsd_mission.py (what may launch). WU-E4a.

Origin: E3G sat because the live sweep launched only "ADMISSIBLE" while the planner's WATCHED unit
was accepted by another build's launch sites. A verdict is now defined once (LAUNCHABLE_VERDICTS /
KNOWN_VERDICTS); a verdict this build does not know is refused by name, never silently treated as
"not admitted". Every refusal has a launching control. Hermetic: temp state before import, injected
runner, no real worker. Mutation drill: GSD_MISSION_DRILL_DIR holding a mutated copy of the tools.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="verdict-contract-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
os.environ.pop("CPP_ROUTE_ADMISSION", None)
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402
import route_admission as ra  # noqa: E402
import envelope_fixture  # noqa: E402
envelope_fixture.bound_missions(gm)
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
NOW = 1_800_000_000.0
ENV = {"target": 3_500_000, "warn": 4_500_000, "stop": 5_500_000, "calls": 25}
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


def route(calls: int) -> dict:
    return {"envelope": ENV, "workers": [{"name": "w", "profile": "top-level-worker", "calls": calls, "packet": 4000}]}


def verdict_of(calls: int) -> str:
    return ra.admit(route(calls), ra.load_floors(None))["verdict"]


# find a call count the REAL planner calls WATCHED (never a hand-picked constant)
watched_calls = next((n for n in range(5, 120) if verdict_of(n) == ra.WATCHED), None)
adm_calls = next((n for n in range(1, 120) if verdict_of(n) == ra.ADMISSIBLE), None)
check("V-VERDICT-FIXTURE", watched_calls is not None and adm_calls is not None,
      f"watched_calls={watched_calls} admissible_calls={adm_calls}")

check("V-VERDICT-CONSTANTS",
      tuple(ra.LAUNCHABLE_VERDICTS) == ("ADMISSIBLE", "WATCHED")
      and set(ra.KNOWN_VERDICTS) == {"ADMISSIBLE", "WATCHED", "DEFER", "RECOMPILE", "ESCALATE"},
      f"launchable={ra.LAUNCHABLE_VERDICTS} known={ra.KNOWN_VERDICTS}")
check("V-VERDICT-GSD-IMPORTS-CONSTANTS",
      gm.LAUNCHABLE_VERDICTS is ra.LAUNCHABLE_VERDICTS and gm.KNOWN_VERDICTS is ra.KNOWN_VERDICTS)

calls: list = []


def runner(argv, cwd):
    calls.append(argv)
    return SimpleNamespace(stdout=f"backgrounded · c0ffee{len(calls):02x} · {argv[3]}", stderr="", returncode=0)


def mission(mid: str) -> dict:
    gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING, epoch=1)
    gm.set_envelope(mid, wu_packet=write(f"{mid}-WU.md", f"# WU {mid}\n"), now=NOW)
    return gm.load(mid)


# --- WATCHED launches (the real planner's WATCHED, through the real admit/launch path)
if watched_calls is not None:
    mission("m-vw")
    rp = write("route-watched.json", route(watched_calls))
    rec = gm.admit_route("m-vw", rp, measure=lambda r: None, now=NOW)
    check("V-VERDICT-WATCHED-RECORDED", rec["admission"]["verdict"] == "WATCHED", rec["admission"]["verdict"])
    check("V-VERDICT-WATCHED-NOT-REFUSED", gm.admission_refusal(gm.load("m-vw")) is None)
    cur = gm.load("m-vw")
    out = gm.launch_worker("m-vw", expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                           runner=runner, now=NOW)
    after = gm.load("m-vw")
    check("V-VERDICT-WATCHED-LAUNCHES", out.get("ok") and after["admission"].get("consumed_epoch") is not None,
          f"ok={out.get('ok')} consumed={after['admission'].get('consumed_epoch')}")
    seen: list = []
    real_declare = ms.declare
    ms.declare = lambda sid, target, warn, stop, **kw: seen.append((sid, target, warn, stop))
    try:
        gm._declare_worker_envelope(after, "sid-watched")
    finally:
        ms.declare = real_declare
    check("V-VERDICT-WATCHED-ENVELOPE-APPLIED", len(seen) == 1 and seen[0][1:] == (ENV["target"], ENV["warn"], ENV["stop"]),
          str(seen))

# --- control: ADMISSIBLE still launches
if adm_calls is not None:
    mission("m-va")
    gm.admit_route("m-va", write("route-adm.json", route(adm_calls)), measure=lambda r: None, now=NOW)
    check("V-VERDICT-ADMISSIBLE-NOT-REFUSED", gm.admission_refusal(gm.load("m-va")) is None)


# --- refused verdicts, built on the real recorded admission so digests are valid
def with_verdict(mid: str, verdict: str) -> dict:
    rec = gm.load(mid)
    return {**rec, "admission": {**rec["admission"], "verdict": verdict}}


base = gm.load("m-va" if adm_calls is not None else "m-vw")
mid_base = base["mission_id"]
for v in ("ESCALATE", "RECOMPILE", "DEFER"):
    r = gm.admission_refusal(with_verdict(mid_base, v))
    check(f"V-VERDICT-{v}-REFUSED", r is not None and not r.startswith("verdict_unknown"), str(r)[:90])
r = gm.admission_refusal(with_verdict(mid_base, "BOGUS_VERDICT"))
check("V-VERDICT-UNKNOWN-NAMED",
      bool(r) and r.startswith("verdict_unknown:") and "BOGUS_VERDICT" in r and str(gm.CODE_ID) in r, str(r)[:140])
r_none = gm.admission_refusal({**base, "admission": {}})
check("V-VERDICT-NONE-NOT-UNKNOWN", r_none is not None and not r_none.startswith("verdict_unknown"), str(r_none)[:90])

# --- static: no literal ADMISSIBLE comparison left in gsd_mission's launch sites
src = Path(gm.__file__).read_text(encoding="utf-8")
lits = [i + 1 for i, ln in enumerate(src.splitlines())
        if re.search(r"""verdict["']?\)?\s*(not\s+)?(in|==|!=)\s*[\("']\s*["']?ADMISSIBLE""", ln)
        or re.search(r"""in\s*\(\s*["']ADMISSIBLE["']""", ln)]
check("V-VERDICT-NO-LITERAL-COMPARE", not lits, f"literal comparison lines={lits}")

print(f"VERDICT_CONTRACT_PASS={passes}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
