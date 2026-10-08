#!/usr/bin/env python3
"""V-SWEEPPY-* gates for tools/gsd_sweep_pass.py -- the T7 pass contract, portable twin.

Drives the REAL script against a fake tools dir and a temp state dir; nothing touches the live
estate. Mirrors test_gsd_sweep_pass.py (the .ps1 gates) and adds one the Linux host needs:
a process the stage launched into its OWN session (how `claude --bg` workers live, measured on
GEX44: SID == PID) survives the stage's deadline kill, while the stage's own grandchild dies.
Also closes the gap the port exists for: `gsd_mission.sweep_health` reads this heartbeat as OK.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "gsd_sweep_pass.py"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def pid_alive(pid: int) -> bool:
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    # a zombie still answers kill(0); read its state
    try:
        return Path(f"/proc/{pid}/stat").read_text().split(")")[-1].split()[0] != "Z"
    except OSError:
        return True


def wait_for(pred, secs=30):
    t0 = time.time()
    while time.time() - t0 < secs:
        try:
            if pred():
                return True
        except (OSError, ValueError):
            pass
        time.sleep(0.2)
    return False


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="sweep-pass-py-"))
    tools, state = root / "tools", root / "state"
    tools.mkdir()
    sess = "start_new_session=True" if os.name != "nt" else "creationflags=0x00000008"
    (tools / "gsd_mission.py").write_text(
        "import os, sys, subprocess\n"
        "if os.environ.get('FAKE_SPAWN_WORKER'):\n"
        f"    w = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(90)'], {sess},\n"
        "        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        f"    open(r'{root / 'worker.pid'}', 'w').write(str(w.pid))\n"
        "print('[{\"mission_id\": \"m-fake\", \"action\": \"relay\"}]')\n"
        "sys.exit(int(os.environ.get('FAKE_MISSION_RC', '0')))\n", encoding="utf-8")
    (tools / "gsd_long_run.py").write_text(
        "import subprocess, sys, time, os\n"
        "c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
        f"open(r'{root / 'grandchild.pid'}', 'w').write(str(c.pid))\n"
        "time.sleep(int(os.environ.get('FAKE_V2_SLEEP', '120')))\n", encoding="utf-8")
    env = {**os.environ, "CPP_SWEEP_PY": sys.executable, "CPP_SWEEP_TOOLS_DIR": str(tools),
           "CPP_SWEEP_STATE_DIR": str(state), "CPP_SWEEP_V2_TIMEOUT_S": "4",
           "CPP_SWEEP_MISSION_TIMEOUT_S": "30"}
    cmd = [sys.executable, str(SCRIPT)]
    beat = state / "gsd-sweep-heartbeat.json"

    def read_beat():
        return json.loads(beat.read_text(encoding="utf-8-sig"))

    # 1. bounded stage + tree kill; a worker in its own session survives
    r = subprocess.run(cmd, env={**env, "FAKE_SPAWN_WORKER": "1"}, capture_output=True, text=True, timeout=120)
    b = read_beat()
    st = {s["name"]: s for s in b.get("stages", [])}
    check("V-SWEEPPY-PASS-RAN", r.returncode == 0 and b.get("outcome") == "ran", f"rc={r.returncode} {b} {r.stderr[-300:]}")
    check("V-SWEEPPY-MISSION-FIRST-AND-OK", list(st) == ["mission", "v2"] and st["mission"]["rc"] == 0, str(b.get("stages")))
    check("V-SWEEPPY-STAGE-DEADLINE", st.get("v2", {}).get("timed_out") is True and st["v2"]["secs"] < 30, str(st.get("v2")))
    gpid = int((root / "grandchild.pid").read_text())
    check("V-SWEEPPY-TREE-REAPED", wait_for(lambda: not pid_alive(gpid), 5), f"grandchild {gpid}")
    wpid = int((root / "worker.pid").read_text())
    check("V-SWEEPPY-OWN-SESSION-WORKER-SURVIVES", pid_alive(wpid), f"worker {wpid}")
    try:
        os.kill(wpid, signal.SIGKILL if os.name != "nt" else signal.SIGTERM)
    except OSError:
        pass
    logtxt = (state / "gsd-long-run-sweep.log").read_text(encoding="utf-8")
    check("V-SWEEPPY-LOG-NAMES-TIMEOUT", "SWEEP_STAGE_TIMEOUT stage=v2" in logtxt and "m-fake" in logtxt, logtxt[-200:])

    # 1b. rc is real
    subprocess.run(cmd, env={**env, "FAKE_MISSION_RC": "3"}, capture_output=True, text=True, timeout=120)
    st3 = {s["name"]: s for s in read_beat().get("stages", [])}
    check("V-SWEEPPY-STAGE-RC-IS-REAL", st3.get("mission", {}).get("rc") == 3, str(st3.get("mission")))
    # 1b'. consecutive failed passes are counted (GEX44 2026-10-07: 264 rc=1 passes nobody saw); a clean pass resets
    s0 = read_beat().get("fail_streak") or 0
    subprocess.run(cmd + ["--stages", "mission"], env={**env, "FAKE_MISSION_RC": "3"}, capture_output=True,
                   text=True, timeout=60)
    check("V-SWEEPPY-FAIL-STREAK-COUNTS", s0 >= 1 and read_beat().get("fail_streak") == s0 + 1,
          f"{s0} -> {read_beat().get('fail_streak')}")
    subprocess.run(cmd + ["--stages", "mission"], env=env, capture_output=True, text=True, timeout=60)
    check("V-SWEEPPY-CONTROL-CLEAN-PASS-RESETS-STREAK", read_beat().get("fail_streak") == 0, str(read_beat()))

    # 1c. --stages mission runs only the mission stage (the GEX44 unit's form)
    subprocess.run(cmd + ["--stages", "mission"], env=env, capture_output=True, text=True, timeout=60)
    check("V-SWEEPPY-STAGES-SELECTABLE", [s["name"] for s in read_beat().get("stages", [])] == ["mission"], str(read_beat()))
    bad = subprocess.run(cmd + ["--stages", "v2,mission"], env=env, capture_output=True, text=True, timeout=60)
    check("V-SWEEPPY-MISSION-MUST-LEAD", bad.returncode != 0, f"rc={bad.returncode}")

    # 2. no overlap; the skip never overwrites the holder's beat
    env_slow = {**env, "CPP_SWEEP_V2_TIMEOUT_S": "10"}
    a = subprocess.Popen(cmd, env=env_slow, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_for(lambda: read_beat().get("outcome") == "running" and read_beat().get("pid") == a.pid)
    rb = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
    skip_f = state / "gsd-sweep-skip.json"
    sk = json.loads(skip_f.read_text(encoding="utf-8")) if skip_f.exists() else {}
    check("V-SWEEPPY-NO-OVERLAP-SKIPPED", rb.returncode == 0 and sk.get("outcome") == "skipped", str(sk)[:200])
    check("V-SWEEPPY-SKIP-KEEPS-HOLDER-BEAT", read_beat().get("outcome") == "running" and read_beat().get("pid") == a.pid)
    a.wait(timeout=120)
    check("V-SWEEPPY-HOLDER-FINISHES", read_beat().get("outcome") == "ran", str(read_beat())[:160])

    # 3. a hard-killed pass releases the lease
    a = subprocess.Popen(cmd, env=env_slow, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_for(lambda: read_beat().get("outcome") == "running" and read_beat().get("pid") == a.pid)
    a.kill()
    a.wait(timeout=30)
    subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
    check("V-SWEEPPY-KILLED-PASS-RELEASES-LEASE", read_beat().get("outcome") == "ran", str(read_beat())[:160])

    # 4. the consumer: status's sweep_health reads this heartbeat (the gap this port closes)
    sys.path.insert(0, str(HERE))
    os.environ["GSD_LONG_RUN_STATE_DIR"] = str(state)
    import gsd_mission
    beat.write_text(json.dumps({"outcome": "ran", "stages": [{"name": "mission", "rc": 0, "timed_out": False}]}), encoding="utf-8")
    h = gsd_mission.sweep_health()
    check("V-SWEEPPY-STATUS-READS-OK", h["verdict"] == "OK", str(h))
    beat.unlink()
    check("V-SWEEPPY-CONTROL-ABSENT-IS-NOT-OBSERVED", gsd_mission.sweep_health()["verdict"] == "NOT_OBSERVED")

    print(f"SWEEPPY_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
