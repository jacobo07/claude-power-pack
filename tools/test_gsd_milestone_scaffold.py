"""V-GSDX-SCAFFOLD-* gates for tools/gsd_milestone_scaffold.py and its arm wiring (spec gsd-x-universal-mission.md).
The OK pole is judged by the REAL gsd-tools (`gsd_long_run.gsd_status`), never by a stub: a roadmap only counts if GSD
itself parses it. Temp dirs only; nothing under ~/.claude is written."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ["GSD_LONG_RUN_STATE_DIR"] = tempfile.mkdtemp(prefix="gsdx-scaffold-state-")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402
import gsd_milestone_scaffold as gms  # noqa: E402
import gsd_mission as gm  # noqa: E402

passes = fails = 0

PACKET = """# WU-T1 -- demo unit
Phases, in order:
Q1 Instrument: build the gate and its tests.
Q2 Baseline: measure the four cells.
Q3 Iterate toward ACCEPT with registered interventions.
Q2 Baseline again (duplicate label must not add a phase).
"""


def check(name, cond, detail=""):
    global passes, fails
    passes, fails = passes + bool(cond), fails + (not cond)
    print(f"{'PASS' if cond else 'FAIL'} {name} {detail}")


def tmpdir():
    return Path(tempfile.mkdtemp(prefix="gsdx-scaffold-"))


def main() -> int:
    os.environ.pop("CPP_GSD_X_AUTOSCAFFOLD", None)
    os.environ.pop("_TEST_GSD_STATUS", None)

    ph = gms.phases_from_packet(PACKET, fallback="Execute x")
    check("V-GSDX-SCAFFOLD-PHASES-FROM-PACKET", len(ph) == 3 and ph[0].startswith("Q1") and ph[2].startswith("Q3"), str(ph))
    check("V-GSDX-SCAFFOLD-FALLBACK-ONE-PHASE", gms.phases_from_packet("no phases here", "Execute p.md") == ["Execute p.md"])

    # real GSD: empty repo -> NO_PHASES -> scaffold -> GSD itself says OK with the packet's 3 phases
    d = tmpdir(); pk = d / "WU.md"; pk.write_text(PACKET, encoding="utf-8")
    raw_before = lr.gsd_status(str(d))
    check("V-GSDX-SCAFFOLD-ABSENT-ROADMAP-IS-NO-PHASES", gms.absent_roadmap(raw_before).get("outcome") == "NO_PHASES",
          f"raw {raw_before}")
    before = gms.absent_roadmap(raw_before)
    if before.get("outcome") == "UNAVAILABLE":
        print(f"GSDX_SCAFFOLD_INCONCLUSIVE gsd-tools unavailable: {before.get('reason')}")
        return 2
    check("V-GSDX-SCAFFOLD-PRECONDITION-NO-PHASES", before.get("outcome") == "NO_PHASES", str(before))
    res = gms.ensure(d, wu_packet=str(pk), command="/gsd-autonomous")
    after = lr.gsd_status(str(d))
    check("V-GSDX-SCAFFOLD-REAL-GSD-OK", res["action"] == "scaffolded" and after.get("outcome") == "OK"
          and after.get("phase_count") == 3, f"{res} {after}")
    # idempotent: an OK roadmap is never touched
    mtime = (d / ".planning" / "ROADMAP.md").stat().st_mtime_ns
    res2 = gms.ensure(d, wu_packet=str(pk))
    check("V-GSDX-SCAFFOLD-OK-UNTOUCHED", res2["action"] == "none"
          and (d / ".planning" / "ROADMAP.md").stat().st_mtime_ns == mtime, str(res2))

    # no packet: one fallback phase, still OK by real GSD
    d2 = tmpdir()
    res = gms.ensure(d2, command="python run.py")
    check("V-GSDX-SCAFFOLD-NO-PACKET-OK", res["action"] == "scaffolded" and lr.gsd_status(str(d2)).get("phase_count") == 1, str(res))

    # an existing unparseable roadmap is archived (moved, never deleted) and replaced
    d3 = tmpdir(); (d3 / ".planning").mkdir(); (d3 / ".planning" / "ROADMAP.md").write_text("# old\nnothing\n", encoding="utf-8")
    res = gms.ensure(d3, wu_packet=str(pk))
    arch = list((d3 / ".planning" / "milestones").glob("auto-archived-*/ROADMAP.md"))
    check("V-GSDX-SCAFFOLD-ARCHIVES-OLD", res["action"] == "scaffolded" and len(arch) == 1
          and arch[0].read_text(encoding="utf-8").startswith("# old"), str(res))

    # a verdict that never turns OK restores exactly what was there (injected reader: always NO_PHASES)
    d4 = tmpdir(); (d4 / ".planning").mkdir(); (d4 / ".planning" / "ROADMAP.md").write_text("# keep me\n", encoding="utf-8")
    res = gms.ensure(d4, wu_packet=str(pk), status_reader=lambda c, w: {"outcome": "NO_PHASES", "reason": "forced"})
    check("V-GSDX-SCAFFOLD-FAILED-RESTORES", res["action"] == "failed"
          and (d4 / ".planning" / "ROADMAP.md").read_text(encoding="utf-8") == "# keep me\n"
          and not (d4 / ".planning" / "STATE.md").exists(), str(res))

    # switches and guards
    os.environ["CPP_GSD_X_AUTOSCAFFOLD"] = "off"
    d5 = tmpdir()
    check("V-GSDX-SCAFFOLD-KILL-SWITCH", gms.ensure(d5)["action"] == "skipped" and not (d5 / ".planning").exists())
    os.environ.pop("CPP_GSD_X_AUTOSCAFFOLD")
    check("V-GSDX-SCAFFOLD-MISSING-CWD-SKIPS", gms.ensure(str(d5 / "nope"))["action"] == "skipped")
    check("V-GSDX-SCAFFOLD-UNAVAILABLE-NO-WRITE",
          gms.ensure(d5, status_reader=lambda c, w: {"outcome": "UNAVAILABLE"})["action"] == "none"
          and not (d5 / ".planning").exists())

    # wiring: arm_chain scaffolds BEFORE its preflight, so a repo with no milestone passes the gsd_status check
    d6 = tmpdir(); pk6 = d6 / "WU.md"; pk6.write_text(PACKET, encoding="utf-8")
    real, seen = gm.arm_preflight, {}

    def spy(cwd, *a, **k):
        seen["status"] = gms.absent_roadmap(lr.gsd_status(str(cwd))).get("outcome")
        return {"ok": False, "checks": [], "refusal": "spy: stop before create"}
    gm.arm_preflight = spy
    try:
        gm.arm_chain(str(d6), "/gsd-autonomous", wu_packet=str(pk6), token_estimate=1, route="r")
    finally:
        gm.arm_preflight = real
    check("V-GSDX-SCAFFOLD-ARM-CHAIN-WIRED", seen.get("status") == "OK", str(seen))

    # mutation drill: a scaffold that writes nothing must leave the wired preflight seeing NO_PHASES
    real_ensure, gms.ensure = gms.ensure, (lambda *a, **k: {"action": "none"})
    d7 = tmpdir(); seen.clear(); gm.arm_preflight = spy
    try:
        gm.arm_chain(str(d7), "/gsd-autonomous", wu_packet=str(pk6), token_estimate=1, route="r")
    finally:
        gm.arm_preflight, gms.ensure = real, real_ensure
    check("V-GSDX-SCAFFOLD-MUTANT-GOES-RED", seen.get("status") == "NO_PHASES", str(seen))

    print(f"GSDX_SCAFFOLD_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
