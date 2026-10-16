"""V-PNG-*: planning_gate.decide, every pole. Origin: M2 (2026-10-16) planned a TB-DISC-PROBE with a full
planner/checker/replanner loop (29.9M, zero execution) although P22-P24 had executed the same work class."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planning_gate as pg  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = passes + bool(cond), fails + (not cond)
    print(("PASS " if cond else "FAIL ") + gate + ("" if cond else f" :: {ev}"))


def main():
    # Arrange: a repo with a harness file and a capsule pinned to its sha.
    repo = Path(tempfile.mkdtemp())
    (repo / "runner.sh").write_bytes(b"echo run\n")
    cap = {"work_class": "TB-DISC-PROBE", "max_unknowns": 3,
           "planning_budget_tokens": {"DIRECT_TEMPLATE": 0, "DELTA_PLAN": 1_000_000},
           "closed_obligations": [{"id": "hud-portraits", "proof": "P24 tbl-20261016-110219"}],
           "invalidators": [{"path": "runner.sh", "sha256": hashlib.sha256(b"echo run\n").hexdigest()}]}
    (repo / "cap.json").write_text(json.dumps(cap))
    base = {"work_class": "TB-DISC-PROBE", "capsule": "cap.json", "reversible": True, "blast_radius": "low",
            "unknowns": ["loose .scp honoured", "PlayerUsingForce fires"], "claims": ["front-camera", "force-spawn"]}
    d = lambda **kw: pg.decide({**base, **kw}, repo)  # noqa: E731

    # Act / Assert
    r = d()
    check("V-PNG-MATURE-NO-FULL-PLAN", r["mode"] == "DELTA_PLAN" and not r["planner_agent_admitted"]
          and r["planning_authority_tokens"] == 1_000_000, str(r))
    check("V-PNG-NO-UNKNOWNS-DIRECT", d(unknowns=[])["mode"] == "DIRECT_TEMPLATE")
    check("V-PNG-NOVEL-ADMITS-PLANNER", d(unknowns=list("abcd"))["mode"] == "BOUNDED_PLAN"
          and d(unknowns=list("abcd"))["planner_agent_admitted"])
    check("V-PNG-IRREVERSIBLE-FULL", d(reversible=False)["mode"] == "FULL_PLAN")
    check("V-PNG-HIGH-BLAST-FULL", d(blast_radius="high")["mode"] == "FULL_PLAN")
    u = dict(base)
    u.pop("reversible")
    check("V-PNG-UNKNOWN-RISK-OWNER", pg.decide(u, repo)["mode"] == "OWNER")
    check("V-PNG-NO-CAPSULE-BOUNDED", d(capsule=None)["mode"] == "BOUNDED_PLAN")
    check("V-PNG-WRONG-CLASS-BOUNDED", d(work_class="KSR-SEAM")["mode"] == "BOUNDED_PLAN")
    r = d(claims=["front-camera", "hud-portraits"])
    check("V-PNG-CLOSED-OBLIGATION-REFUSED", r["refused_claims"] == [{"claim": "hud-portraits",
          "closed_by": "P24 tbl-20261016-110219"}], str(r["refused_claims"]))
    check("V-PNG-CONTROL-OPEN-CLAIMS-PASS", d()["refused_claims"] == [])
    (repo / "runner.sh").write_bytes(b"echo changed harness\n")       # the precedent's harness moved
    r = d()
    check("V-PNG-INVALIDATED-PRECEDENT-BOUNDED", r["mode"] == "BOUNDED_PLAN" and r["invalidated_by"] == ["runner.sh changed"],
          str(r))
    (repo / "cap.json").write_text("{not json")
    check("V-PNG-UNREADABLE-CAPSULE-NOT-VALID", d()["mode"] == "BOUNDED_PLAN")

    # Arm-time admission (gsd_mission.planning_admission + the real CLI), on a fresh valid capsule.
    import os
    import subprocess
    state = tempfile.mkdtemp()
    env = {**os.environ, "GSD_LONG_RUN_STATE_DIR": state, "GSD_LONG_RUN_SESSIONS_DIR": state,
           "GSD_AUTORUN_MARKER_DIR": state, "CPP_CLAUDE_JOBS_DIR": state}
    os.environ.update({k: v for k, v in env.items() if k != "PATH"})
    import gsd_mission as gm
    (repo / "runner.sh").write_bytes(b"echo run\n")
    (repo / "cap.json").write_text(json.dumps(cap))
    (repo / "unit.json").write_text(json.dumps(base))
    unit = str(repo / "unit.json")
    a = gm.planning_admission("/gsd-autonomous", str(repo), unit, None)
    check("V-PNG-ARM-GSD-REFUSED-ON-DELTA", not a["admitted"] and a["gate"] == "DELTA_PLAN", str(a)[:200])
    check("V-PNG-ARM-COMPILED-ADMITTED", gm.planning_admission("/tb-p25 run packet", str(repo), unit, None)["admitted"])
    check("V-PNG-ARM-OVERRIDE-ADMITTED", gm.planning_admission("/gsd-autonomous", str(repo), unit, "new arch")["admitted"])
    check("V-PNG-ARM-NO-UNIT-UNASSESSED", gm.planning_admission("/gsd-autonomous", str(repo), None, None)
          == {"admitted": True, "gate": "UNASSESSED"})
    p = subprocess.run([sys.executable, str(Path(gm.__file__)), "arm", "--cwd", str(repo), "--command", "/gsd-autonomous",
                        "--work-unit", unit, "--no-launch"], capture_output=True, text=True, env=env, timeout=120)
    made = list(Path(state).glob("gsd-mission-m-*.json"))
    check("V-PNG-CLI-ARM-REFUSED-NOTHING-ARMED", p.returncode == 4 and "REFUSED: planning gate DELTA_PLAN" in p.stdout
          and not made, f"rc={p.returncode} out={p.stdout[-200:]} err={p.stderr[-300:]} made={made}")
    print(f"PNG_PASS={passes}/{passes + fails}  threshold=17/17")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
