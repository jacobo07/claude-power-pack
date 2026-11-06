"""V-ANL-*: `arm --no-launch` runs the GSD milestone check (spec vault/specs/arm-no-launch-milestone.md).

Origin 2026-11-06 (GEX44, S16 m-29dd612ed825): the mission was armed --no-launch for the sweep to launch, and the ledger
has NO arm-preflight row for it -- neither the milestone scaffold nor the GSD check ran, so the worker would have met
an archived milestone. A hand `ensure --command` then built a 1-phase roadmap from the prose command. Hermetic: GSD is
a fake that answers from the fixture's ROADMAP.md; `--drills` mutates the module and expects red.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TMP = Path(tempfile.mkdtemp(prefix="gsd-anl-test-"))
os.environ["GSD_LONG_RUN_STATE_DIR"] = str(TMP / "state")
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(TMP / "state" / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = str(TMP / "state")
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(TMP / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(TMP / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
os.environ["CPP_RESOURCE_ADMISSION"] = "off"   # host RAM is not what these gates measure
os.environ.pop("CPP_GSD_X_AUTOSCAFFOLD", None)
os.environ.pop("CPP_GSD_X_OPTOUT", None)
(TMP / "state" / "sessions").mkdir(parents=True)
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
sys.path.insert(1, str(HERE))
import gsd_mission as gm  # noqa: E402
import gsd_long_run as lr  # noqa: E402


def fake_gsd_status(cwd, workstream=None, **_kw):
    road = Path(cwd) / ".planning" / "ROADMAP.md"
    if not road.is_file():
        return {"outcome": "UNAVAILABLE", "reason": "gsd-tools rc=1: Error: No ROADMAP.md found."}
    n = len(re.findall(r"(?m)^- \[ \] \*\*Phase \d+", road.read_text(encoding="utf-8")))
    return {"outcome": "OK", "reason": f"{n} open phases"} if n else {"outcome": "NO_PHASES", "reason": "0 phases"}


lr.gsd_status = fake_gsd_status
NOW = 1_800_000_000.0
PHASES = "# S99 phases\n\nW0 Reality and baseline\nW1 Frozen cohorts\nW2 Comparative experiments\n"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {'' if cond else ':: ' + str(ev)[:300]}")


def repo(name):
    d = TMP / name
    (d / ".planning").mkdir(parents=True)
    (d / ".planning" / "STATE.md").write_text("# State (archived milestone)\n", encoding="utf-8")
    return d


def phases_file():
    p = TMP / "S99-PHASES.md"
    p.write_text(PHASES, encoding="utf-8")
    return p


def preflight_rows(cwd):
    return [e for e in lr.ledger_events() if e.get("event") == "arm_preflight" and e.get("cwd") == str(cwd)]


def open_phases(cwd):
    return fake_gsd_status(str(cwd)).get("reason")


def main() -> int:
    # 1. --no-launch with a phases file: the milestone is scaffolded from it (3 phases, not 1) and the check is ledgered.
    d = repo("r-scaffold")
    rec = gm.arm(str(d), "Execute Generation S99 (prose command)", launch=False, now=NOW,
                 milestone_from=str(phases_file()))["mission"]
    check("V-ANL-NOLAUNCH-SCAFFOLDS", (d / ".planning" / "ROADMAP.md").is_file() and bool(preflight_rows(d)),
          [p.name for p in (d / ".planning").iterdir()])
    check("V-ANL-PHASES-FROM-FILE", open_phases(d) == "3 open phases", open_phases(d))
    check("V-ANL-MILESTONE-FROM-NOT-PACKET", not rec.get("wu_packet") and rec["state"] == gm.PREPARED, rec.get("wu_packet"))

    # 2. Scaffold off, no milestone: --no-launch is told (warn, ledgered), a launching arm is still refused.
    os.environ["CPP_GSD_X_AUTOSCAFFOLD"] = "off"
    try:
        d2 = repo("r-warn")
        try:
            gm.arm(str(d2), "Execute something", launch=False, now=NOW)
            refused = None
        except gm.MissionError as exc:
            refused = str(exc)
        rows = preflight_rows(d2)
        check("V-ANL-NOLAUNCH-WARNS", refused is None and bool(rows)
              and ["gsd_status", "warn"] in [list(c) for c in rows[-1]["checks"]],
              refused or (rows[-1:] if rows else "no arm_preflight row"))
        d3 = repo("r-refuse")
        try:
            gm.arm(str(d3), "Execute something", launch=True, now=NOW)
            check("V-ANL-LAUNCH-STILL-REFUSES", False, "a launching arm with no milestone was accepted")
        except gm.MissionError as exc:
            check("V-ANL-LAUNCH-STILL-REFUSES", "NO_PHASES" in str(exc), str(exc))
    finally:
        os.environ.pop("CPP_GSD_X_AUTOSCAFFOLD", None)

    # 3. A caller that already preflighted (arm_chain) does not run it twice.
    d4 = repo("r-once")
    gm.arm(str(d4), "Execute something", launch=False, now=NOW, preflighted=True)
    check("V-ANL-PREFLIGHTED-SKIPS", not preflight_rows(d4) and not (d4 / ".planning" / "ROADMAP.md").exists())

    # 3b. Review MEDIUM: a mission worker arming --no-launch does not get its .planning rewritten (check still runs).
    gm.create(str(TMP), "/gsd-autonomous", mission_id="m-anl-parent", now=NOW)
    gm.transition("m-anl-parent", expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                  state=gm.RUNNING, epoch=1, owner={"session_id": "anl-worker-sid", "pid": 1, "kind": "background"})
    d6 = repo("r-worker")
    prev = os.environ.get("CLAUDE_CODE_SESSION_ID")
    os.environ["CLAUDE_CODE_SESSION_ID"] = "anl-worker-sid"
    try:
        gm.arm(str(d6), "Execute sub-unit", launch=False, now=NOW, milestone_from=str(phases_file()))
        wrefused = None
    except gm.MissionError as exc:
        wrefused = str(exc)
    finally:
        if prev is None:
            os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        else:
            os.environ["CLAUDE_CODE_SESSION_ID"] = prev
    check("V-ANL-WORKER-PLANNING-UNTOUCHED", wrefused is None and not (d6 / ".planning" / "ROADMAP.md").exists()
          and (d6 / ".planning" / "STATE.md").is_file() and bool(preflight_rows(d6)),
          wrefused or [p.name for p in (d6 / ".planning").iterdir()])

    # 4. CLI: --milestone-from reaches the scaffold.
    d5 = repo("r-cli")
    rc = gm._cli(["arm", "--cwd", str(d5), "--command", "Execute Generation S99", "--no-launch",
                  "--milestone-from", str(phases_file())])
    check("V-ANL-CLI-MILESTONE-FROM", rc == 0 and open_phases(d5) == "3 open phases", (rc, open_phases(d5)))

    print(f"ARM_NO_LAUNCH_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


DRILLS = [
    ("no-launch skips the check again", "    if not preflighted:\n", "    if launch and not preflighted:\n",
     "V-ANL-NOLAUNCH-SCAFFOLDS"),
    ("phases file not passed", "wu_packet=milestone_from or kw.get(\"wu_packet\"))",
     "wu_packet=kw.get(\"wu_packet\"))", "V-ANL-PHASES-FROM-FILE"),
    ("no-launch refuses instead of warning", "launch=launch, gsd_refuse=launch,", "launch=launch, gsd_refuse=True,",
     "V-ANL-NOLAUNCH-WARNS"),
    ("preflighted ignored", "    if not preflighted:\n", "    if True:\n", "V-ANL-PREFLIGHTED-SKIPS"),
    ("worker scaffold guard removed",
     "if arm_preflight_on() and not worker_why:", "if arm_preflight_on():", "V-ANL-WORKER-PLANNING-UNTOUCHED"),
]


def drills() -> int:
    src = (HERE / "gsd_mission.py").read_text(encoding="utf-8")
    bad = 0
    for name, needle, repl, gate in DRILLS:
        if src.count(needle) != 1:
            print(f"DRILL-FAIL {name}: needle found {src.count(needle)} times, not once")
            bad += 1
            continue
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "gsd_mission.py").write_text(src.replace(needle, repl, 1), encoding="utf-8")
            r = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve())], capture_output=True, text=True,
                               env={**os.environ, "GSD_MISSION_DRILL_DIR": td}, timeout=300)
            red = r.returncode != 0 and f"FAIL {gate}" in r.stdout
            print(f"{'DRILL-PASS' if red else 'DRILL-FAIL'} {name}: {gate} {'red' if red else 'stayed green'}")
            bad += 0 if red else 1
    print(f"ARM_NO_LAUNCH_DRILLS={len(DRILLS) - bad}/{len(DRILLS)}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(drills() if "--drills" in sys.argv else main())
