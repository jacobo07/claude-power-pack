"""resource_census.py -- Resource Residency Fabric P0 (plan vault/plans/resource-residency-fabric-20261120.md).

Measures who holds memory on this host, per process and per claude.exe session, with the three memory
counters kept apart (RR-01): WS = working set (psutil rss), private = PrivateUsage, commit = pagefile-charged
bytes (psutil pagefile). Host commit/limit come from GetPerformanceInfo (CommitTotal/CommitLimit x PageSize).

MCP attribution (RR-02): a process belongs to a server only through a signature built from the server's
configured command+args that cannot match unrelated processes. A bare command with no args (the playwright
defect: `mcp` + 0 args matched 751 unrelated processes), tokens that are all generic, a signature shorter
than MIN_SIG_CHARS, or a process matching two different servers -> UNKNOWN, never attributed. Descendants
(incl. conhost) of an attributed root inherit its server. Process identity is (pid, creation time): pid reuse
is defended by refusing a parent whose creation time is later than its child's.

Secrets: server configs carry keys in args/env. Tokens that look like credentials or that follow a flag are
dropped from signatures, and signatures are never written to a snapshot -- only counts and server names.

CLI:  snapshot [--out F]   |  diff A.json B.json   |  sessions [--snapshot F]
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import sys
import time

HOME = os.path.expanduser("~")
SCHEMA = 1
MIN_SIG_CHARS = 6
GENERIC = {"mcp", "run", "start", "serve", "server", "stdio", "exec", "dlx", "x", "npx", "node", "python",
           "python3", "uvx", "uv", "npm", "pnpm", "bunx", "cmd", "/c", "-y"}
NO_VALUE_FLAGS = {"-y", "--yes", "-q", "--quiet", "-s", "--silent", "-m", "-u", "--no-install", "--no-warnings"}
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def _norm(s: str) -> str:
    return s.replace("\\", "/").lower()


def _looks_secret(tok: str) -> bool:
    if "=" in tok and len(tok.split("=", 1)[1]) >= 12:
        return True
    if len(tok) >= 20 and not any(c in tok for c in "/\\@.:") and re.search(r"\d", tok) and re.search(r"[a-zA-Z]", tok):
        return True
    return False


def signature_tokens(command: str, args: list | None) -> list[str] | None:
    """Distinguishing tokens of a server's launch line, or None when no safe signature exists."""
    args = [a for a in (args or []) if isinstance(a, str)]
    cmd = _norm(command or "")
    toks: list[str] = []
    base = cmd.rsplit("/", 1)[-1]
    if "/" in cmd and base not in GENERIC and base.rsplit(".", 1)[0] not in GENERIC:
        toks.append(base)                              # a binary/script path IS a signature (ghost-mcp.exe)
    elif not args:
        return None                                   # bare command: the playwright defect
    prev_flag = False
    for a in args:
        if a.startswith("-"):
            # `--key VALUE`: the value is not a signature; but -y/-m style flags do not consume the package/module
            prev_flag = "=" not in a and a not in NO_VALUE_FLAGS
            continue
        if prev_flag:
            prev_flag = False
            continue
        n = _norm(a)
        if n in GENERIC or _looks_secret(a):
            continue
        toks.append(n)
    if not toks or sum(len(t) for t in toks) < MIN_SIG_CHARS:
        return None
    return toks


def build_signatures(servers: dict) -> tuple[dict, list]:
    """servers: name -> config. Returns ({name: tokens}, [names refused as UNKNOWN])."""
    sigs, refused = {}, []
    for name, cfg in (servers or {}).items():
        if not isinstance(cfg, dict) or cfg.get("type") in ("http", "sse") or "url" in cfg:
            continue                                   # remote: no local process to attribute
        t = signature_tokens(cfg.get("command", ""), cfg.get("args"))
        if t is None:
            refused.append(name)
        else:
            sigs[name] = t
    return sigs, refused


def match_server(cmdline: str, sigs: dict) -> str | None:
    """Server name when exactly one signature matches; None for no match or ambiguity."""
    n = _norm(cmdline or "")
    hits = [s for s, toks in sigs.items() if all(t in n for t in toks)]
    return hits[0] if len(hits) == 1 else None


def collect_configs(home: str = HOME) -> dict:
    """Every MCP server config reachable by sessions: user scope, project scopes, ~/.claude/.mcp.json, plugins."""
    out: dict = {}

    def add(servers):
        for k, v in (servers or {}).items():
            if isinstance(v, dict) and ("command" in v or "url" in v):     # a server config, not a wrapper key
                out.setdefault(k, v)

    def load(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    cfg = load(os.path.join(home, ".claude.json"))
    add(cfg.get("mcpServers"))
    for pdata in (cfg.get("projects") or {}).values():
        add((pdata or {}).get("mcpServers"))
    add(load(os.path.join(home, ".claude", ".mcp.json")).get("mcpServers"))
    plug = os.path.join(home, ".claude", "plugins")
    for root, _d, files in os.walk(plug):
        if root.count(os.sep) - plug.count(os.sep) > 6:
            continue
        if ".mcp.json" in files:
            d = load(os.path.join(root, ".mcp.json"))
            add(d.get("mcpServers") or {k: v for k, v in d.items() if isinstance(v, dict)})
    # catalogued (demoted) servers: names only matter for attribution of stragglers
    return out


def build_snapshot(procs: list[dict], sigs: dict, host: dict, refused: list | None = None, now: float | None = None) -> dict:
    """Pure core. procs: [{pid, ppid, create, name, cmdline, ws, private, commit}] (bytes)."""
    by_pid = {p["pid"]: p for p in procs}

    def parent(p):
        q = by_pid.get(p.get("ppid"))
        return q if q and q["create"] <= p["create"] else None     # pid-reuse defence

    attributed: dict = {}                                             # pid -> server
    for p in procs:
        s = match_server(p.get("cmdline") or "", sigs)
        if s:
            attributed[p["pid"]] = s

    def server_of(p):
        seen, cur = 0, p
        while cur and seen < 64:
            if cur["pid"] in attributed:
                return attributed[cur["pid"]]
            cur, seen = parent(cur), seen + 1
        return None

    def session_of(p):
        seen, cur = 0, p
        while cur and seen < 64:
            if (cur.get("name") or "").lower() == "claude.exe":
                return cur
            cur, seen = parent(cur), seen + 1
        return None

    sessions: dict = {}
    for p in procs:
        if (p.get("name") or "").lower() == "claude.exe":
            m = UUID_RE.search(p.get("cmdline") or "")
            sessions[p["pid"]] = {"claude_pid": p["pid"], "create": p["create"],
                                  "session_id": m.group(0).lower() if m else None,
                                  "ws": p["ws"], "private": p["private"], "commit": p["commit"],
                                  "mcp": {}, "unattributed_descendants": 0}
    servers: dict = {}
    for p in procs:
        s = server_of(p)
        if s:
            a = servers.setdefault(s, {"procs": 0, "ws": 0, "private": 0, "commit": 0, "live_sessions": set()})
            a["procs"] += 1; a["ws"] += p["ws"]; a["private"] += p["private"]; a["commit"] += p["commit"]
        c = session_of(p)
        if c and p["pid"] != c["pid"]:
            sess = sessions[c["pid"]]
            if s:
                m = sess["mcp"].setdefault(s, {"procs": 0, "ws": 0, "private": 0, "commit": 0})
                m["procs"] += 1; m["ws"] += p["ws"]; m["private"] += p["private"]; m["commit"] += p["commit"]
                servers[s]["live_sessions"].add(c["pid"])
            else:
                sess["unattributed_descendants"] += 1
    for a in servers.values():
        a["live_sessions"] = len(a["live_sessions"])
    return {
        "schema": SCHEMA, "taken_at": now if now is not None else time.time(), "host": host,
        "counters": {"ws": "psutil rss (working set)", "private": "psutil memory_info.private (PrivateUsage)",
                     "commit": "psutil memory_info.pagefile (pagefile-charged)"},
        "process_count": len(procs),
        "claude_sessions": len(sessions),
        "sessions": sorted(sessions.values(), key=lambda s: s["claude_pid"]),
        "servers": servers,
        "signatures_refused_unknown": sorted(refused or []),
        "identities": sorted(f"{p['pid']}@{p['create']:.0f}" for p in procs
                             if p["pid"] in attributed or server_of(p)),
    }


def diff_snapshots(a: dict, b: dict) -> dict:
    ia, ib = set(a.get("identities", [])), set(b.get("identities", []))
    out = {"mcp_born": len(ib - ia), "mcp_died": len(ia - ib), "servers": {}, "host": {}}
    for s in sorted(set(a["servers"]) | set(b["servers"])):
        x = a["servers"].get(s, {}); y = b["servers"].get(s, {})
        out["servers"][s] = {k: y.get(k, 0) - x.get(k, 0) for k in ("procs", "ws", "private", "commit")}
    for k in ("commit_total", "commit_limit", "pagefile_total", "ram_free"):
        if k in a["host"] and k in b["host"]:
            out["host"][k] = b["host"][k] - a["host"][k]
    out["claude_sessions"] = b["claude_sessions"] - a["claude_sessions"]
    out["process_count"] = b["process_count"] - a["process_count"]
    return out


# ---- live collection (Windows) ----
class _PERF(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong)] + [(n, ctypes.c_size_t) for n in (
        "CommitTotal", "CommitLimit", "CommitPeak", "PhysicalTotal", "PhysicalAvailable", "SystemCache",
        "KernelTotal", "KernelPaged", "KernelNonpaged", "PageSize")] + [
        ("HandleCount", ctypes.c_ulong), ("ProcessCount", ctypes.c_ulong), ("ThreadCount", ctypes.c_ulong)]


def host_counters() -> dict:
    pi = _PERF(); pi.cb = ctypes.sizeof(pi)
    if not ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(pi), pi.cb):
        return {}
    ps = pi.PageSize
    import psutil
    return {"commit_total": pi.CommitTotal * ps, "commit_limit": pi.CommitLimit * ps,
            "ram_free": pi.PhysicalAvailable * ps, "ram_total": pi.PhysicalTotal * ps,
            "pagefile_total": psutil.swap_memory().total,
            "source": "GetPerformanceInfo (CommitTotal/CommitLimit x PageSize); psutil.swap_memory"}


def live_processes() -> list[dict]:
    import psutil
    out = []
    for p in psutil.process_iter(["pid", "ppid", "name", "create_time", "cmdline", "memory_info"]):
        i = p.info
        mi = i.get("memory_info")
        if mi is None:
            continue                                   # access denied: counted nowhere, never attributed
        out.append({"pid": i["pid"], "ppid": i["ppid"], "name": i["name"] or "", "create": i["create_time"] or 0.0,
                    "cmdline": " ".join(i["cmdline"] or []), "ws": mi.rss,
                    "private": getattr(mi, "private", 0), "commit": getattr(mi, "pagefile", 0)})
    return out


def take_snapshot() -> dict:
    sigs, refused = build_signatures(collect_configs())
    return build_snapshot(live_processes(), sigs, host_counters(), refused)


def _gb(n) -> str:
    return f"{n / 2**30:.2f} GB"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot"); s.add_argument("--out")
    d = sub.add_parser("diff"); d.add_argument("a"); d.add_argument("b")
    q = sub.add_parser("sessions"); q.add_argument("--snapshot")
    a = ap.parse_args(argv)
    if a.cmd == "snapshot":
        snap = take_snapshot()
        text = json.dumps(snap, indent=2)
        if a.out:
            os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
            open(a.out, "w", encoding="utf-8", newline="\n").write(text)
        h = snap["host"]
        print(f"commit {_gb(h.get('commit_total', 0))} / limit {_gb(h.get('commit_limit', 0))}; "
              f"pagefile {_gb(h.get('pagefile_total', 0))}; claude.exe x{snap['claude_sessions']}; "
              f"procs {snap['process_count']}; refused-UNKNOWN {snap['signatures_refused_unknown']}")
        for n, v in sorted(snap["servers"].items(), key=lambda kv: -kv[1]["private"]):
            print(f"  {n}: x{v['procs']} private {_gb(v['private'])} ws {_gb(v['ws'])} commit {_gb(v['commit'])} sessions {v['live_sessions']}")
        return 0
    if a.cmd == "diff":
        print(json.dumps(diff_snapshots(json.load(open(a.a)), json.load(open(a.b))), indent=2))
        return 0
    snap = json.load(open(a.snapshot)) if a.snapshot else take_snapshot()
    for se in snap["sessions"]:
        print(f"claude {se['claude_pid']} id={se['session_id']} private {_gb(se['private'])} "
              f"mcp_servers={len(se['mcp'])} mcp_procs={sum(m['procs'] for m in se['mcp'].values())} "
              f"unattributed_desc={se['unattributed_descendants']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
