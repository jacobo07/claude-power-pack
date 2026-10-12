"""census.py -- PRR Memory Census: read-only process-tree attribution of physical memory.

Answers "where does the RAM of the Claude estate live" per logical session, without
touching any process. Pure classification (`classify`) is separated from the sampler
(`sample`) so the attribution rules are testable on synthetic process tables.

Metrics are Windows-truthful: `private_mb` is private bytes (commit charged to the
process), `wset_mb` is the resident working set. They differ a lot under pressure
(2026-10-12 laptop: 28.2 GB private vs 9.4 GB working set), so both are reported and
neither is summed into the other.

Parent identity: a parent edge counts only when the parent exists in the SAME snapshot
and was created no later than the child. A recycled PID (parent newer than child) is a
dead parent. Orphans are reported as CANDIDATES only; this module never terminates.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import socket
import sys
import time
from dataclasses import asdict, dataclass

PLANE_LAPTOP = "windows-laptop" if sys.platform == "win32" else f"{sys.platform}-{socket.gethostname()}"

_ROLE_NAMES = {"claude.exe": "claude", "claude": "claude"}
_JS_HOSTS = {"node.exe", "node", "bun.exe", "bun"}
_SHELLS = {"powershell.exe", "pwsh.exe", "pwsh"}


@dataclass(frozen=True)
class Proc:
    pid: int
    ppid: int
    name: str
    created: float
    cmdline: str = ""
    private_mb: float | None = None
    wset_mb: float | None = None


def _norm(cmd: str) -> str:
    return cmd.replace("\\", "/").lower()


def role_of(p: Proc, parent: Proc | None) -> str:
    name = p.name.lower()
    cmd = _norm(p.cmdline)
    if _ROLE_NAMES.get(name) == "claude":
        if parent is not None and _ROLE_NAMES.get(parent.name.lower()) == "claude":
            return "claude_helper"
        return "claude_main"
    if name in _JS_HOSTS:
        if ".planning/config.json" in cmd:
            return "gsd_probe"
        if "/.claude/hooks/" in cmd:
            return "hook"
        if "mcp" in cmd:
            return "mcp"
        return "js_other"
    if name in _SHELLS and "kclaude" in cmd:
        return "kclaude_wrapper"
    return "other"


def _valid_parent(p: Proc, by_pid: dict) -> Proc | None:
    par = by_pid.get(p.ppid)
    if par is None or par.pid == p.pid or par.created > p.created:
        return None
    return par


def _pearson(xs: list, ys: list) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def classify(procs: list, *, now: float, available_mb: float | None = None,
             total_mb: float | None = None, plane: str = PLANE_LAPTOP) -> dict:
    by_pid = {p.pid: p for p in procs}
    parent = {p.pid: _valid_parent(p, by_pid) for p in procs}
    role = {p.pid: role_of(p, parent[p.pid]) for p in procs}
    children: dict = {}
    for p in procs:
        par = parent[p.pid]
        if par is not None:
            children.setdefault(par.pid, []).append(p)

    def descendants(pid: int) -> list:
        out, stack = [], list(children.get(pid, []))
        while stack:
            c = stack.pop()
            out.append(c)
            stack.extend(children.get(c.pid, []))
        return out

    def wrapper_of(p: Proc) -> int | None:
        cur = parent[p.pid]
        while cur is not None:
            if role[cur.pid] == "kclaude_wrapper":
                return cur.pid
            cur = parent[cur.pid]
        return None

    sessions = []
    for p in procs:
        if role[p.pid] != "claude_main":
            continue
        by_role: dict = {}
        for d in descendants(p.pid):
            r = role[d.pid]
            agg = by_role.setdefault(r, {"count": 0, "private_mb": 0.0, "wset_mb": 0.0})
            agg["count"] += 1
            agg["private_mb"] += d.private_mb or 0.0
            agg["wset_mb"] += d.wset_mb or 0.0
        sessions.append({
            "pid": p.pid,
            "age_h": round((now - p.created) / 3600.0, 2),
            "private_mb": p.private_mb,
            "wset_mb": p.wset_mb,
            "descendants": by_role,
            "tree_private_mb": round((p.private_mb or 0.0) + sum(a["private_mb"] for a in by_role.values()), 1),
            "kclaude_wrapper": wrapper_of(p),
        })
    sessions.sort(key=lambda s: -(s["tree_private_mb"]))

    totals: dict = {}
    for p in procs:
        r = role[p.pid]
        if r == "other":
            continue
        agg = totals.setdefault(r, {"count": 0, "private_mb": 0.0, "wset_mb": 0.0})
        agg["count"] += 1
        agg["private_mb"] = round(agg["private_mb"] + (p.private_mb or 0.0), 1)
        agg["wset_mb"] = round(agg["wset_mb"] + (p.wset_mb or 0.0), 1)

    orphans = [
        {"pid": p.pid, "role": role[p.pid], "ppid": p.ppid, "private_mb": p.private_mb,
         "age_h": round((now - p.created) / 3600.0, 2)}
        for p in procs
        if role[p.pid] in {"gsd_probe", "hook", "mcp", "js_other", "claude_helper"} and parent[p.pid] is None
    ]

    mains = [s for s in sessions if s["private_mb"] is not None]
    return {
        "plane": plane,
        "sampled_at": now,
        "host": {"available_mb": available_mb, "total_mb": total_mb},
        "totals_by_role": totals,
        "sessions": sessions,
        "orphan_candidates": orphans,
        "age_private_pearson": _pearson([s["age_h"] for s in mains], [s["private_mb"] for s in mains]),
        "age_private_note": "cross-sectional over live main sessions; not a within-session growth curve",
    }


def sample() -> tuple:
    import psutil

    want_mem = set(_ROLE_NAMES) | _JS_HOSTS
    want_cmd = _JS_HOSTS | _SHELLS
    procs = []
    for ph in psutil.process_iter(["pid", "ppid", "name", "create_time"]):
        info = ph.info
        name = (info.get("name") or "").lower()
        if info.get("create_time") is None:
            continue
        private = wset = None
        cmd = ""
        try:
            if name in want_mem:
                m = ph.memory_info()
                private = round(getattr(m, "private", m.vms) / 2**20, 1)
                wset = round(getattr(m, "wset", m.rss) / 2**20, 1)
            if name in want_cmd:
                cmd = " ".join(ph.cmdline())
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess) as exc:
            cmd = cmd or f"<unreadable:{type(exc).__name__}>"
        procs.append(Proc(info["pid"], info.get("ppid") or 0, name, info["create_time"], cmd, private, wset))
    vm = psutil.virtual_memory()
    return procs, vm.available / 2**20, vm.total / 2**20


def run(plane: str | None = None) -> dict:
    procs, avail, total = sample()
    return classify(procs, now=time.time(), available_mb=round(avail), total_mb=round(total),
                    plane=plane or PLANE_LAPTOP)


def summary(rep: dict) -> str:
    lines = [f"plane={rep['plane']} available={rep['host']['available_mb']} MB / {rep['host']['total_mb']} MB"]
    for r, a in sorted(rep["totals_by_role"].items(), key=lambda kv: -kv[1]["private_mb"]):
        lines.append(f"  {r:16s} n={a['count']:4d} private={a['private_mb']:9.1f} MB wset={a['wset_mb']:9.1f} MB")
    lines.append(f"  sessions={len(rep['sessions'])} orphan_candidates={len(rep['orphan_candidates'])} "
                 f"age~private r={rep['age_private_pearson'] if rep['age_private_pearson'] is None else round(rep['age_private_pearson'], 2)}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PRR read-only memory census")
    ap.add_argument("--json", action="store_true", help="print the full report as JSON")
    ap.add_argument("--plane", default=None)
    args = ap.parse_args(argv)
    rep = run(args.plane)
    print(json.dumps(rep, indent=1) if args.json else summary(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
