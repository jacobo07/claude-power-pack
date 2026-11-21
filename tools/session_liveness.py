"""session_liveness.py -- Resource Residency P5: session liveness classifier, SHADOW REPORT ONLY.

Classifies each claude.exe session ACTIVE / IDLE / UNKNOWN from several independent signals. It never stops, signals or
modifies anything (HR-STALLED-SESSION-ADVISORY-001). Rules:
  * IDLE needs POSITIVE evidence on every axis: two CPU samples with ~no delta, no live non-MCP child, a bg-job state that
    is not working, and a transcript that is stale. One missing or contradicting signal => UNKNOWN (protected).
  * Any single strong live signal (CPU delta, busy child, working job, fresh transcript) => ACTIVE.
  * UNKNOWN is protected: it is never a hibernation candidate.
Kill switch: CPP_SESSION_HIBERNATION=off makes the report say candidates are disabled (it never acts either way).
Usage: python tools/session_liveness.py report [--interval 5] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

HOME = os.path.expanduser("~")
CPU_ACTIVE_S = 0.5          # cpu-seconds consumed between samples that proves life
TRANSCRIPT_FRESH_S = 120.0  # transcript written this recently => alive
TRANSCRIPT_STALE_S = 900.0  # older than this is the only age that supports IDLE
ACTIVE, IDLE, UNKNOWN = "ACTIVE", "IDLE", "UNKNOWN"
MCP_HINT = re.compile(r"mcp|modelcontext|fastmcp|playwright|context7|\\plugins\\cache\\", re.I)


def classify(s: dict) -> tuple[str, str]:
    """s: cpu_delta_s (float|None), busy_children (int|None), job_state (str|None), transcript_age_s (float|None),
    protected (bool). Returns (state, reason)."""
    if s.get("protected"):
        return UNKNOWN, "protected: mission/bg-job lease"
    cpu, kids, job, age = s.get("cpu_delta_s"), s.get("busy_children"), s.get("job_state"), s.get("transcript_age_s")
    if cpu is not None and cpu >= CPU_ACTIVE_S:
        return ACTIVE, f"cpu +{cpu:.2f}s between samples"
    if kids:
        return ACTIVE, f"{kids} busy non-MCP child process(es)"
    if job in ("working", "running", "starting"):
        return ACTIVE, f"bg job state={job}"
    if age is not None and age < TRANSCRIPT_FRESH_S:
        return ACTIVE, f"transcript written {age:.0f}s ago"
    missing = [k for k, v in (("cpu", cpu), ("children", kids), ("transcript", age)) if v is None]
    if missing:
        return UNKNOWN, "missing signal: " + ",".join(missing)
    if age < TRANSCRIPT_STALE_S:
        return UNKNOWN, f"transcript {age:.0f}s old: between fresh and stale"
    if job not in (None, "idle", "done", "completed", "stopped"):
        return UNKNOWN, f"unrecognised job state {job!r}"
    return IDLE, f"cpu +{cpu:.2f}s, no busy child, transcript {age:.0f}s old"


def _jobs() -> dict:
    out, base = {}, os.path.join(HOME, ".claude", "jobs")
    try:
        names = os.listdir(base)
    except OSError:
        return out
    for n in names:
        try:
            with open(os.path.join(base, n, "state.json"), encoding="utf-8-sig") as f:
                d = json.load(f)
            if d.get("sessionId"):
                out[d["sessionId"]] = d
        except (OSError, ValueError):
            continue
    return out


def _transcript_age(sid: str, now: float):
    base = os.path.join(HOME, ".claude", "projects")
    best = None
    try:
        for proj in os.listdir(base):
            p = os.path.join(base, proj, sid + ".jsonl")
            if os.path.exists(p):
                m = os.path.getmtime(p)
                best = m if best is None or m > best else best
    except OSError:
        return None
    return None if best is None else now - best


def sample(interval: float) -> list[dict]:
    import psutil
    def snap():
        d = {}
        for p in psutil.process_iter(["pid", "name", "cmdline", "cpu_times", "memory_info", "create_time"]):
            i = p.info
            if (i["name"] or "").lower() == "claude.exe" and i["cpu_times"] and i["memory_info"]:
                d[i["pid"]] = (i, p)
        return d
    a = snap()
    kid_a = {}
    for pid, (_, p) in a.items():
        try:
            kid_a[pid] = {c.pid: sum(c.cpu_times()[:2]) for c in p.children(recursive=True)}
        except psutil.Error:
            kid_a[pid] = None
    time.sleep(interval)
    b, jobs, now, rows = snap(), _jobs(), time.time(), []
    for pid, (i, p) in b.items():
        if pid not in a:
            continue
        cmd = " ".join(i["cmdline"] or [])
        m = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", cmd)
        sid = m.group(0) if m else None          # session id only when the command line names it; never guessed
        cpu = sum(i["cpu_times"][:2]) - sum(a[pid][0]["cpu_times"][:2])
        busy = None
        if kid_a.get(pid) is not None:
            busy = 0
            try:
                for c in p.children(recursive=True):
                    prev = kid_a[pid].get(c.pid)
                    if prev is not None and not MCP_HINT.search(" ".join(c.cmdline() or [])) \
                            and sum(c.cpu_times()[:2]) - prev >= CPU_ACTIVE_S:
                        busy += 1
            except psutil.Error:
                busy = None
        job = jobs.get(sid) if sid else None
        rows.append({"pid": pid, "session": sid, "private_mb": round(i["memory_info"].private / 1048576, 1)
                     if hasattr(i["memory_info"], "private") else None,
                     "cpu_delta_s": cpu, "busy_children": busy,
                     "job_state": (job or {}).get("state"),
                     "transcript_age_s": _transcript_age(sid, now) if sid else None,
                     "protected": bool(job) and (job.get("state") not in (None, "idle", "done", "completed", "stopped"))})
    for r in rows:
        r["state"], r["reason"] = classify(r)
    return rows


def report(rows: list[dict]) -> dict:
    off = os.environ.get("CPP_SESSION_HIBERNATION", "").lower() == "off"
    counts = {k: sum(1 for r in rows if r["state"] == k) for k in (ACTIVE, IDLE, UNKNOWN)}
    idle_mb = sum(r["private_mb"] or 0 for r in rows if r["state"] == IDLE)
    return {"mode": "shadow", "kill_switch_off": off, "counts": counts, "idle_private_mb": round(idle_mb, 1),
            "note": "report only; nothing is stopped. UNKNOWN is protected.", "sessions": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report")
    r.add_argument("--interval", type=float, default=5.0)
    r.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rep = report(sample(a.interval))
    if a.json:
        print(json.dumps(rep, indent=1))
    else:
        print(f"shadow: {rep['counts']}  idle-private={rep['idle_private_mb']} MB (nothing stopped)")
        for s in sorted(rep["sessions"], key=lambda x: x["state"]):
            print(f"  {s['pid']:>6} {s['state']:<8} {s['private_mb']} MB  {s['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
