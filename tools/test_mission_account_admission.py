#!/usr/bin/env python
"""V-BAMR-ADMIT gates: every model-spending mission launch passes the account governor (BAMR P3, 2026-11-20).

Two launch paths exist and both are covered: gsd_mission.launch_worker (arm, relay, rotation, replacement,
quota/top-up wake, closeout) and gsd_epoch.continue_worker (same-session `--resume` wake). Hermetic: the
governor reads the suite's own state directory; each refusal has an admitting control, and the static gate
fails if a new launch site appears outside the two gated functions.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="bamr-admit-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
os.environ["CPP_RESOURCE_ADMISSION"] = "off"   # RAM floor: covered by test_a5_u6
os.environ.pop("CPP_MISSION_ACCOUNT_ADMISSION", None)
os.environ.pop("CPP_GOVERNOR_UNKNOWN", None)
os.environ.pop("CPP_MISSION_RENEW", None)
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import gsd_mission as gm  # noqa: E402
import gsd_epoch as ge  # noqa: E402
import gsd_long_run as lr  # noqa: E402
import account_governor as ag  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
gm.effective_workdir = lambda sid, cwd, ws=None: None
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


def write(name, obj):
    p = Path(TMP) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), encoding="utf-8")


def quota(seven=None, five=None, age=30.0):
    """Plant the governor's picture in the suite's state dir. seven=None -> no official reading at all."""
    for n in ("quota-reading.json", "account-governor.json"):
        (Path(TMP) / n).unlink(missing_ok=True)
    if seven is None:
        return
    rl = {"seven_day": {"used_percentage": seven, "resets_at": time.time() + 86400}}
    if five is not None:
        rl["five_hour"] = {"used_percentage": five, "resets_at": time.time() + 3600}
    write("quota-reading.json", {"captured_at": time.time() - age, "source": "harness_statusline", "rate_limits": rl})


def mission(mid):
    gm.create(TMP, "/gsd-autonomous --ws wsx", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING, epoch=1)


def launch(mid):
    cur = gm.load(mid)
    return gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="t", runner=runner, now=NOW)


def events(name, mid=None):
    p = lr.ledger_path()
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []
    return [r for r in rows if r.get("event") == name and (mid is None or r.get("mission_id") == mid)]


def main() -> int:
    # 1. unknown quota (no official reading, no estimate) refuses before the claim: no epoch, no spawn
    quota(None)
    mission("m-unk")
    n0 = len(calls)
    r = launch("m-unk")
    after = gm.load("m-unk")
    check("V-BAMR-ADMIT-UNKNOWN-REFUSES", not r["ok"] and r.get("account_refused") and len(calls) == n0
          and after["epoch"] == 1 and after["state"] == gm.RUNNING and events("launch_refused_account", "m-unk"),
          f"why={r.get('why', '')[:90]!r} epoch={after['epoch']} spawned={len(calls) - n0}")

    # 2. control: a fresh official reading under the reserves admits the same launch
    quota(19)
    r = launch("m-unk")
    check("V-BAMR-ADMIT-OFFICIAL-ADMITS", r["ok"] and len(calls) == n0 + 1, f"ok={r['ok']} spawned={len(calls) - n0}")

    # 3. weekly reserve and 4. 5-hour reserve refuse
    for gate, seven, five in (("V-BAMR-ADMIT-WEEKLY-RESERVE", 86, None), ("V-BAMR-ADMIT-5H-RESERVE", 10, 81)):
        quota(seven, five)
        mid = "m-" + gate[-10:].lower().replace("-", "")
        mission(mid)
        n = len(calls)
        r = launch(mid)
        check(gate, not r["ok"] and len(calls) == n and "REFUSE" in r["why"], r["why"][:100])

    # 5. a stale official reading (window just reset, nobody has rendered since) is unknown, not "fresh window"
    quota(1, age=3600)
    mission("m-stale")
    n = len(calls)
    r = launch("m-stale")
    check("V-BAMR-ADMIT-RESET-NOT-AUTHORITY", not r["ok"] and len(calls) == n and "UNKNOWN" in r["why"],
          "1%% read an hour ago is no licence to spend: " + r["why"][:80])

    # 6. a governor fault is an unknown quota: refused, never an allowance
    quota(19)
    real_check = ag.check
    ag.check = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("planted"))
    try:
        mission("m-fault")
        n = len(calls)
        r = launch("m-fault")
    finally:
        ag.check = real_check
    check("V-BAMR-ADMIT-FAULT-REFUSES", not r["ok"] and len(calls) == n and "fault" in r["why"], r["why"][:90])

    # 7. deterministic work is never blocked by an unknown quota (it spends none)
    quota(None)
    mission("m-det")
    real_ds, real_rd = gm.deterministic_script, gm._run_deterministic
    gm.deterministic_script = lambda rec: {"script": "planted"}
    gm._run_deterministic = lambda rec, det, now, run=None: {"ok": True, "deterministic": True}
    try:
        r = launch("m-det")
    finally:
        gm.deterministic_script, gm._run_deterministic = real_ds, real_rd
    check("V-BAMR-ADMIT-DETERMINISTIC-RUNS", r.get("deterministic") and not events("launch_refused_account", "m-det"),
          f"det={r.get('deterministic')}")

    # 8. kill switch restores the pre-BAMR launch under unknown quota
    os.environ["CPP_MISSION_ACCOUNT_ADMISSION"] = "off"
    try:
        mission("m-ks")
        n = len(calls)
        r = launch("m-ks")
    finally:
        os.environ.pop("CPP_MISSION_ACCOUNT_ADMISSION", None)
    check("V-BAMR-ADMIT-KILL-SWITCH", r["ok"] and len(calls) == n + 1, f"ok={r['ok']}")

    # 9. same-session continuation (gsd_epoch.continue_worker) is gated too, before its claim
    quota(None)
    mission("m-cont")
    gm.transition("m-cont", expect_epoch=1, expect_state=gm.RUNNING, event="t_owner", now=NOW,
                  owner={"session_id": "abcdef12-0000-0000-0000-000000000000"})
    rec = gm.load("m-cont")
    seen = []
    r = ge.continue_worker("m-cont", rec, prompt="go", decision={"reason": "t"},
                           runner=lambda argv, cwd: seen.append(argv), now=NOW)
    after = gm.load("m-cont")
    check("V-BAMR-ADMIT-CONTINUATION-REFUSES", not r["ok"] and r.get("account_refused") and not seen
          and after["state"] == gm.RUNNING and events("continue_refused_account", "m-cont"),
          f"state={after['state']} woke={len(seen)}")
    quota(19)
    r = ge.continue_worker("m-cont", gm.load("m-cont"), prompt="go", decision={"reason": "t"},
                           runner=lambda argv, cwd: seen.append(argv) or SimpleNamespace(
                               stdout="resumed abcdef12", stderr="", returncode=0), now=NOW)
    check("V-BAMR-ADMIT-CONTINUATION-ADMITS", r["ok"] and len(seen) == 1 and "--resume" in seen[0], f"ok={r['ok']}")

    # 10. static: the only places that start a claude worker are the two gated functions, and the gate sits
    #     after the deterministic/done-gate closes and before the claim in launch_worker
    src = (TOOLS / "gsd_mission.py").read_text(encoding="utf-8")
    lw = src[src.index("def launch_worker("):src.index("\ndef ", src.index("def launch_worker(") + 10)]
    i_gate, i_det, i_claim = lw.find("account_refusal(rec"), lw.find("try_done_gate_close(rec"), lw.find("epoch = expect_epoch + 1")
    spawn_sites = [m.start() for m in re.finditer(r"worker_argv\(rec, prompt\)|_launch_slim\(rec, prompt", src)]
    in_lw = all(src.index("def launch_worker(") < s < src.index("def launch_worker(") + len(lw) for s in spawn_sites)
    esrc = (TOOLS / "gsd_epoch.py").read_text(encoding="utf-8")
    cw = esrc[esrc.index("def continue_worker("):esrc.index("\ndef ", esrc.index("def continue_worker(") + 10)]
    resume_sites = [m.start() for m in re.finditer(r"resume_argv\(", esrc)]
    check("V-BAMR-ADMIT-SINGLE-GATE", 0 < i_det < i_gate < i_claim and in_lw and len(spawn_sites) == 2
          and cw.find("account_refusal(rec") < cw.find("gm.transition(") and len(resume_sites) == 2,
          f"order det<gate<claim={0 < i_det < i_gate < i_claim} spawns_in_launch_worker={in_lw} ({len(spawn_sites)}) "
          f"resume_argv defs+calls={len(resume_sites)}")

    print(f"BAMR_ADMIT_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
