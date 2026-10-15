#!/usr/bin/env python
"""A5-U6 gates: resource admission refuses a launch on low or unknown RAM. Hermetic; each refusal has an admitting control."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="a5-u6-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
os.environ.pop("CPP_RESOURCE_ADMISSION", None)
os.environ.pop("CPP_MISSION_RENEW", None)
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import gsd_mission as gm  # noqa: E402
import gsd_long_run as lr  # noqa: E402
import resource_admission as ra  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
NOW = 1_800_000_000.0
passes = fails = 0
calls: list = []


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def runner(argv, cwd):
    calls.append(argv)
    return SimpleNamespace(stdout=f"backgrounded · c0ffee{len(calls):02x} · {argv[3]}", stderr="", returncode=0)


def reader(mb):
    return lambda: {"available_mb": mb, "source": "planted"}


def mission(mid):
    gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING, epoch=1)


def launch(mid, rd):
    cur = gm.load(mid)
    return gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t",
                            runner=runner, now=NOW, mem_reader=rd)


def ledger_events(name):
    p = lr.ledger_path()
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []
    return [r for r in rows if r.get("event") == name]


def mutant_verdict():
    src = (TOOLS / "resource_admission.py").read_text(encoding="utf-8")
    assert "mb >= floor" in src
    d = Path(tempfile.mkdtemp(prefix="a5-u6-mut-"))
    (d / "resource_admission_mut.py").write_text(src.replace("mb >= floor", "mb < floor"), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("resource_admission_mut", d / "resource_admission_mut.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    low, ok, unk = ra.verdict({"available_mb": 500}, "top-level-worker"), ra.verdict({"available_mb": 8000}, "top-level-worker"), ra.verdict({"available_mb": None}, "top-level-worker")
    check("U6-LOW-REFUSES", low["verdict"] == ra.REFUSE_LOW_MEMORY and low["floor_mb"] == 3000, str(low))
    check("U6-ADEQUATE-ADMITS-CONTROL", ok["verdict"] == ra.ADMIT)
    check("U6-UNKNOWN-REFUSES", unk["verdict"] == ra.UNKNOWN_REFUSE and unk["available_mb"] is None, str(unk))
    check("U6-UNREADABLE-SHAPES-REFUSE", all(ra.verdict(r, "slim-t1")["verdict"] == ra.UNKNOWN_REFUSE
          for r in (None, {}, {"available_mb": "x"}, {"available_mb": float("nan")}, {"available_mb": True})))
    check("U6-FLOORS", [ra.floor_mb(p) for p in ("slim-t1", "slim-t2", "top-level-worker", "zzz")] == [1500, 1500, 3000, 3000])
    check("U6-SLIM-FLOOR-BOUNDARY", ra.verdict({"available_mb": 1500}, "slim-t2")["verdict"] == ra.ADMIT
          and ra.verdict({"available_mb": 1499}, "slim-t2")["verdict"] == ra.REFUSE_LOW_MEMORY)
    real = ra.read_available_mb()
    check("U6-REAL-READER", real["available_mb"] is None or real["available_mb"] > 0, str(real))

    mission("m-low")
    n, ep = len(calls), gm.load("m-low")["epoch"]
    res = launch("m-low", reader(500))
    rows = ledger_events("launch_refused_resources")
    check("U6-LAUNCH-LOW-SPAWNS-NOTHING", res["ok"] is False and len(calls) == n and gm.load("m-low")["epoch"] == ep
          and gm.load("m-low")["state"] == gm.RUNNING and len(rows) == 1 and rows[0]["reading"]["available_mb"] == 500, str(res.get("why")))
    res = launch("m-low", lambda: {"available_mb": None})
    check("U6-LAUNCH-UNKNOWN-SPAWNS-NOTHING", res["ok"] is False and len(calls) == n and "UNKNOWN_REFUSE" in res["why"])
    def boom():
        raise OSError("no meminfo")
    res = launch("m-low", boom)
    check("U6-LAUNCH-READER-RAISES-REFUSES", res["ok"] is False and len(calls) == n)
    res = launch("m-low", reader(9000))
    check("U6-LAUNCH-ADEQUATE-ADMITS-CONTROL", res["ok"] is True and len(calls) == n + 1 and gm.load("m-low")["epoch"] == ep + 1, str(res.get("why")))

    mission("m-off")
    os.environ["CPP_RESOURCE_ADMISSION"] = "off"
    n = len(calls)
    res = launch("m-off", reader(1))
    os.environ.pop("CPP_RESOURCE_ADMISSION")
    check("U6-KILL-SWITCH", res["ok"] is True and len(calls) == n + 1)

    mut = mutant_verdict()
    check("U6-MUTANT-INVERTED-COMPARATOR-RED",
          mut.verdict({"available_mb": 500}, "top-level-worker")["verdict"] == ra.ADMIT
          and mut.verdict({"available_mb": 8000}, "top-level-worker")["verdict"] != ra.ADMIT,
          "mutant admits low / refuses adequate: the gates above would fail")
    print(f"A5_U6_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
