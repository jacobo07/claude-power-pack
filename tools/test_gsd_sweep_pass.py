#!/usr/bin/env python
"""V-SWEEP-* gates for tools/gsd_long_run_sweep.ps1 -- the pass contract (T7, 2026-09-28).

Drives the REAL script under powershell.exe against a fake tools dir and a temp state dir, so
nothing here touches the live estate. What it proves:
  * a stage past its deadline is killed WITH its whole tree (a spawned grandchild dies too);
  * two passes never overlap: the second records `skipped`;
  * the lease is released by the OS when a pass is hard-killed (the next pass runs);
  * every pass leaves a heartbeat, including an idle one.
Measured origin: 7 `gsd_long_run.py sweep` passes had piled up (peer pane c2, 2026-09-27) --
the task time limit killed wscript, never the python grandchild -- and supervise starved.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PS1 = HERE / "gsd_long_run_sweep.ps1"
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def pid_alive(pid: int) -> bool:
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
    return str(pid) in out


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="sweep-pass-"))
    tools, state = root / "tools", root / "state"
    tools.mkdir()
    (tools / "gsd_mission.py").write_text(
        "import os, sys\n"
        "print('[{\"mission_id\": \"m-fake\", \"action\": \"relay\"}]')\n"
        "sys.exit(int(os.environ.get('FAKE_MISSION_RC', '0')))\n", encoding="utf-8")
    # v2 stage: spawns a grandchild that records its pid, then hangs. Its tree must die.
    (tools / "gsd_long_run.py").write_text(
        "import subprocess, sys, time, os\n"
        "c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
        f"open(r'{root / 'grandchild.pid'}', 'w').write(str(c.pid))\n"
        "time.sleep(int(os.environ.get('FAKE_V2_SLEEP', '120')))\n", encoding="utf-8")
    env = {**os.environ, "CPP_SWEEP_PY": sys.executable, "CPP_SWEEP_TOOLS_DIR": str(tools),
           "CPP_SWEEP_STATE_DIR": str(state), "CPP_SWEEP_V2_TIMEOUT_S": "4",
           "CPP_SWEEP_MISSION_TIMEOUT_S": "30"}
    cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
           "-File", str(PS1)]
    beat = state / "gsd-sweep-heartbeat.json"

    def read_beat():
        return json.loads(beat.read_text(encoding="utf-8-sig"))

    # 1. bounded stage + tree kill
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
    b = read_beat()
    st = {s["name"]: s for s in b.get("stages", [])}
    check("V-SWEEP-PASS-RAN", r.returncode == 0 and b.get("outcome") == "ran", f"rc={r.returncode} {b} {r.stderr[-300:]}")
    check("V-SWEEP-MISSION-STAGE-FIRST-AND-OK",
          list(st) == ["mission", "v2"] and st["mission"]["rc"] == 0, str(b.get("stages")))
    check("V-SWEEP-STAGE-DEADLINE", st.get("v2", {}).get("timed_out") is True
          and st["v2"]["secs"] < 30, str(st.get("v2")))
    gpid = int((root / "grandchild.pid").read_text())
    time.sleep(1)
    check("V-SWEEP-TREE-REAPED", not pid_alive(gpid), f"grandchild {gpid} alive={pid_alive(gpid)}")
    logtxt = (state / "gsd-long-run-sweep.log").read_text(encoding="utf-8")
    check("V-SWEEP-LOG-NAMES-TIMEOUT", "SWEEP_STAGE_TIMEOUT stage=v2" in logtxt and "m-fake" in logtxt,
          logtxt[-200:])

    # 1b. the exit code is REAL, not a constant: a failing stage reads as failing
    subprocess.run(cmd, env={**env, "FAKE_MISSION_RC": "3"}, capture_output=True, text=True, timeout=180)
    st3 = {s["name"]: s for s in read_beat().get("stages", [])}
    check("V-SWEEP-STAGE-RC-IS-REAL", st3.get("mission", {}).get("rc") == 3, str(st3.get("mission")))

    # 2. no overlap: B starts while A holds the lease
    env_slow = {**env, "CPP_SWEEP_V2_TIMEOUT_S": "15"}
    a = subprocess.Popen(cmd, env=env_slow, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 30:
        try:
            if read_beat().get("outcome") == "running" and read_beat().get("pid"):
                break
        except (OSError, ValueError):
            pass
        time.sleep(0.2)
    rb = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
    bb = read_beat()
    check("V-SWEEP-NO-OVERLAP-SKIPPED", rb.returncode == 0 and bb.get("outcome") == "skipped", str(bb)[:200])
    a.wait(timeout=180)
    check("V-SWEEP-HOLDER-FINISHES", read_beat().get("outcome") == "ran", str(read_beat())[:160])
    rc_ = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
    check("V-SWEEP-CONTROL-LEASE-FREED-AFTER-PASS", read_beat().get("outcome") == "ran")

    # 3. a hard-killed pass releases the lease
    a = subprocess.Popen(cmd, env=env_slow, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 30:
        try:
            if read_beat().get("outcome") == "running":
                break
        except (OSError, ValueError):
            pass
        time.sleep(0.2)
    subprocess.run(["taskkill", "/PID", str(a.pid), "/T", "/F"], capture_output=True)
    a.wait(timeout=30)
    subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
    check("V-SWEEP-KILLED-PASS-RELEASES-LEASE", read_beat().get("outcome") == "ran", str(read_beat())[:160])

    print(f"SWEEP_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
