#!/usr/bin/env python3
"""gsd_sweep_pass.py -- the sweep pass contract (T7) as a portable Python entry point.

Twin of tools/gsd_long_run_sweep.ps1 for hosts without PowerShell (GEX44's systemd timer
`agora-mission-sweep`). Measured origin, 2026-09-28: the GEX44 unit ran
`gsd_mission.py supervise --actions-only` directly, so none of T7 existed there -- no lease,
no stage deadline, no heartbeat -- and `gsd_mission.py status` reported
`SWEEP NOT_OBSERVED` on a supervisor that was in fact firing every 5 minutes.

Contract (same as the .ps1, same files, so `sweep_health` reads either):
  * ONE pass at a time: an exclusive kernel lock on gsd-sweep.lease for the whole pass, released
    by the OS if this process dies. A pass that finds it held writes gsd-sweep-skip.json and
    NEVER touches the holder's heartbeat (review F3).
  * Mission stage first. Every stage is bounded; on its deadline the stage's whole process
    group is killed. Workers a stage launches are not in that group: `claude --bg` hands them to
    its daemon, each in its own session (measured on GEX44: SID == PID), so a deadline kill
    cannot reach a worker.
  * Every pass writes gsd-sweep-heartbeat.json (running -> ran, per-stage rc / secs / timed_out).
  * The log records only passes that DID something.

Usage:  gsd_sweep_pass.py [--stages mission,v2]
Overrides (tests only): CPP_SWEEP_PY, CPP_SWEEP_TOOLS_DIR, CPP_SWEEP_STATE_DIR,
  CPP_SWEEP_MISSION_TIMEOUT_S, CPP_SWEEP_V2_TIMEOUT_S.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

STAGES = {
    "mission": ("gsd_mission.py", ["supervise", "--actions-only"], "CPP_SWEEP_MISSION_TIMEOUT_S", 600),
    "v2": ("gsd_long_run.py", ["sweep"], "CPP_SWEEP_V2_TIMEOUT_S", 240),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, obj: dict) -> None:
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


def _lock(fh) -> bool:
    """Non-blocking exclusive lock; False when another live pass holds it."""
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _kill_tree(p: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run_stage(name: str, py: str, tools: Path, timeout_s: int) -> dict:
    script, args, _, _ = STAGES[name]
    t0 = time.time()
    kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" \
        else {"start_new_session": True}
    # Output goes to temp files, not pipes: a worker that inherits a pipe would hold it open
    # and turn communicate() into a wait on the worker's whole life.
    with tempfile.TemporaryFile() as out:
        p = subprocess.Popen([py, str(tools / script), *args], stdout=out, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONIOENCODING": "utf-8"}, **kw)
        timed_out = False
        try:
            rc = p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_tree(p)
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
            rc = None
        out.seek(0)
        text = out.read().decode("utf-8", "replace").strip()
    return {"name": name, "rc": rc, "timed_out": timed_out, "pid": p.pid,
            "secs": round(time.time() - t0, 1), "text": text}


def _log(log: Path, prefix: str, text: str) -> None:
    if text and text != "[]":
        flat = re.sub(r"\s+", " ", text)
        with log.open("a", encoding="utf-8") as f:
            f.write(f"{_now()} {prefix}{flat}\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stages", default="mission,v2",
                    help="comma list, run in order; mission must come first when present")
    a = ap.parse_args(argv)
    stages = [s for s in a.stages.split(",") if s]
    unknown = [s for s in stages if s not in STAGES]
    if unknown or not stages:
        ap.error(f"unknown or empty stages: {unknown or stages}")
    if "mission" in stages and stages[0] != "mission":
        ap.error("mission must be the first stage (v2 once starved supervise, 2026-09-27)")

    here = Path(__file__).resolve().parent
    py = os.environ.get("CPP_SWEEP_PY") or sys.executable
    tools = Path(os.environ.get("CPP_SWEEP_TOOLS_DIR") or here)
    state = Path(os.environ.get("CPP_SWEEP_STATE_DIR") or (Path.home() / ".claude" / "state"))
    state.mkdir(parents=True, exist_ok=True)
    beat, log = state / "gsd-sweep-heartbeat.json", state / "gsd-long-run-sweep.log"
    started = _now()

    fh = open(state / "gsd-sweep.lease", "a+b")
    try:
        if not _lock(fh):
            _write_json(state / "gsd-sweep-skip.json", {"outcome": "skipped",
                        "reason": "another pass holds the lease", "at": started, "pid": os.getpid()})
            return 0
        _write_json(beat, {"outcome": "running", "started_at": started, "pid": os.getpid()})
        done = []
        for name in stages:
            _, _, env_key, default = STAGES[name]
            timeout_s = int(os.environ.get(env_key) or default)
            r = run_stage(name, py, tools, timeout_s)
            _log(log, "mission " if name == "mission" else "", r["text"])
            if r["timed_out"]:
                _log(log, "", f"SWEEP_STAGE_TIMEOUT stage={name} after {timeout_s}s; "
                              f"tree of pid {r['pid']} killed")
            done.append({k: r[k] for k in ("name", "rc", "timed_out", "secs")})
        _write_json(beat, {"outcome": "ran", "started_at": started, "finished_at": _now(),
                           "pid": os.getpid(), "stages": done})
    finally:
        fh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
