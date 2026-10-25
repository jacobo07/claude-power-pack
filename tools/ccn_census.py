#!/usr/bin/env python3
"""CCN census: does running sessions concurrently cost more than running them in turn?

Deterministic, READ-ONLY measurement over the Claude Code transcript estate
(`~/.claude/projects/<project>/<session>.jsonl`). Works on Linux and on Windows paths.

  dup       cross-session duplicate tool calls (same normalized key, distinct sessions, <= 1800 s)
  stampede  first-call cache write/read: concurrent start (<= 300 s after another) vs isolated
  hot-idle  live claude processes joined to their transcript, with idle minutes, size, free RAM
  all       the three above; with --check, exit 1 when a CI threshold is breached

Plan of record: vault/plans/ccn-concurrency-neutrality-2026-10-24.md (sections A10, A12, B61).
Idle time is taken from the transcript's own last record timestamp, never from file mtime
(HR-PANE-MAP-FRESHNESS-001): a batch rewrite of mtimes would forge liveness.
"""
import argparse
import bisect
import calendar
import collections
import glob
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import time

WINDOW_S = 1800            # duplicate window between two sessions
CONCURRENT_S = 300         # "started right after another session"
DUP_MAX_PCT = 3.0          # CI: duplicates above this share of calls fail
STAMPEDE_MAX_RATIO = 1.10  # CI: concurrent write above isolated write x this fails
MIN_EVENTS = 50            # below this the dup check is UNMEASURED, not green
MIN_FIRST_CALLS = 10       # per arm, below this the stampede check is UNMEASURED
TAIL_BYTES = 256 * 1024
# Roles that can hold a conversation. A "spare" is a pooled worker that may or may not be claimed;
# it is joined by cwd only, so it can never be reported as joined by id.
JOINABLE = ("session", "spare")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
TEST_CMD_RE = re.compile(r"test_|pytest|git (log|status|diff)|status|census|gsd_mission")


def default_roots():
    return [os.path.join(os.path.expanduser("~"), ".claude", "projects")]


def parse_ts(ts):
    """ISO-8601 'YYYY-MM-DDTHH:MM:SS[.fff]Z' -> UTC epoch seconds, or None."""
    if not isinstance(ts, str) or len(ts) < 19:
        return None
    try:
        return calendar.timegm(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return None


def main_transcripts(roots, cut):
    """Main-session transcripts (one directory level under a project) touched since `cut`.
    mtime is only a scope prefilter here; every measurement uses record timestamps."""
    for root in roots:
        for path in glob.glob(os.path.join(root, "*", "*.jsonl")):
            try:
                if os.path.getmtime(path) < cut:
                    continue
            except OSError:
                continue
            yield os.path.basename(path)[:-6], path


def records(path):
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return
    with fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict):
                yield rec


# ---------------------------------------------------------------- dup

def tool_key(name, inp):
    """Normalized key for a tool call, or None when the call is not a comparable read/proof."""
    inp = inp or {}
    if name == "Read":
        return "Read:%s:%s:%s" % (str(inp.get("file_path", "")).lower().replace("\\", "/"),
                                  inp.get("offset"), inp.get("limit"))
    if name == "Grep":
        return "Grep:%s|%s" % (inp.get("pattern"), str(inp.get("path", "")).lower())
    if name == "Glob":
        return "Glob:%s|%s" % (inp.get("pattern"), str(inp.get("path", "")).lower())
    if name in ("PowerShell", "Bash"):
        cmd = " ".join(str(inp.get("command", "")).split())
        if not TEST_CMD_RE.search(cmd):
            return None
        return "%s:%s" % (name, cmd[:300])
    if name in ("Agent", "Task"):
        return "Agent:%s|%s" % (inp.get("subagent_type"), inp.get("description"))
    return None


def collect_tool_events(roots, hours, now):
    cut = now - hours * 3600
    events = []   # (key, sid, t, result_bytes, tool)
    sessions = set()
    for sid, path in main_transcripts(roots, cut):
        pending = {}
        for rec in records(path):
            t = parse_ts(rec.get("timestamp"))
            if t is None or t < cut:
                continue
            content = (rec.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                kind = block.get("type")
                if kind == "tool_use":
                    key = tool_key(block.get("name"), block.get("input"))
                    if key is not None:
                        pending[block.get("id")] = (key, t, block.get("name"))
                elif kind == "tool_result" and block.get("tool_use_id") in pending:
                    key, t0, name = pending.pop(block["tool_use_id"])
                    body = block.get("content")
                    size = len(json.dumps(body)) if body is not None else 0
                    events.append((key, sid, t0, size, name))
                    sessions.add(sid)
    return events, sessions


def dup_scan(roots, hours=168.0, now=None, window_s=WINDOW_S):
    """A call is a duplicate when ANOTHER session ran the same key within `window_s` before it
    (or at the same instant)."""
    now = time.time() if now is None else now
    events, sessions = collect_tool_events(roots, hours, now)
    by_key = collections.defaultdict(list)
    for ev in events:
        by_key[ev[0]].append(ev)
    dup_calls = dup_bytes = 0
    per_tool = collections.Counter()
    per_tool_bytes = collections.Counter()
    shared = []
    for key, group in by_key.items():
        sids = {e[1] for e in group}
        if len(sids) < 2:
            continue
        group.sort(key=lambda e: e[2])
        times = [e[2] for e in group]
        for e in group:
            lo = bisect.bisect_left(times, e[2] - window_s)
            hi = bisect.bisect_right(times, e[2])
            if any(p[1] != e[1] for p in group[lo:hi]):
                dup_calls += 1
                dup_bytes += e[3]
                per_tool[e[4]] += 1
                per_tool_bytes[e[4]] += e[3]
        shared.append({"bytes": sum(e[3] for e in group), "calls": len(group),
                       "sessions": len(sids), "key": key[:110]})
    total_bytes = sum(e[3] for e in events)
    shared.sort(key=lambda r: r["bytes"], reverse=True)
    return {
        "window_h": hours, "window_s": window_s,
        "sessions_with_tools": len(sessions), "tool_events": len(events),
        "result_bytes": total_bytes,
        "dup_calls": dup_calls, "dup_calls_pct": round(100.0 * dup_calls / len(events), 3) if events else None,
        "dup_bytes": dup_bytes, "dup_bytes_pct": round(100.0 * dup_bytes / total_bytes, 3) if total_bytes else None,
        "per_tool": {n: {"calls": per_tool[n], "bytes": per_tool_bytes[n]} for n in per_tool},
        "top_shared": shared[:12],
    }


# ---------------------------------------------------------------- stampede

def first_call_rows(roots, days, now):
    """One row per main session: the first assistant record carrying usage."""
    cut = now - days * 86400
    rows = []   # (t, cache_write, cache_read)
    for _sid, path in main_transcripts(roots, cut):
        for rec in records(path):
            usage = (rec.get("message") or {}).get("usage")
            t = parse_ts(rec.get("timestamp"))
            if rec.get("type") != "assistant" or not usage or t is None:
                continue
            if t >= cut:
                rows.append((t, usage.get("cache_creation_input_tokens", 0) or 0,
                             usage.get("cache_read_input_tokens", 0) or 0))
            break
    rows.sort()
    return rows


def _arm(rows):
    writes = [r[0] for r in rows]
    reads = [r[1] for r in rows]
    if not rows:
        return {"n": 0, "write_median": None, "write_mean": None, "read_median": None, "read_mean": None}
    return {"n": len(rows), "write_median": statistics.median(writes), "write_mean": round(statistics.mean(writes)),
            "read_median": statistics.median(reads), "read_mean": round(statistics.mean(reads))}


def stampede_scan(roots, days=7.0, now=None, concurrent_s=CONCURRENT_S):
    now = time.time() if now is None else now
    rows = first_call_rows(roots, days, now)
    times = [r[0] for r in rows]
    concurrent, isolated = [], []
    for i, (t, w, r) in enumerate(rows):
        lo = bisect.bisect_left(times, t - concurrent_s)
        near = any(times[j] < t for j in range(lo, i))
        (concurrent if near else isolated).append((w, r))
    total_w = sum(r[1] for r in rows)
    total_r = sum(r[2] for r in rows)
    return {
        "window_d": days, "concurrent_s": concurrent_s, "first_calls": len(rows),
        "concurrent": _arm(concurrent), "isolated": _arm(isolated),
        "first_call_write_total": total_w, "first_call_read_total": total_r,
        "read_share_pct": round(100.0 * total_r / (total_w + total_r), 2) if total_w + total_r else None,
    }


# ---------------------------------------------------------------- hot-idle

def encode_cwd(cwd):
    """Claude Code's project directory name for a cwd."""
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def argv_session_id(argv):
    """Session id from --session-id / --resume / -r (value may be a transcript path), else None."""
    for i, tok in enumerate(argv):
        val = None
        if tok in ("--session-id", "--resume", "-r") and i + 1 < len(argv):
            val = argv[i + 1]
        elif tok.startswith("--session-id=") or tok.startswith("--resume="):
            val = tok.split("=", 1)[1]
        if val:
            base = os.path.basename(val.replace("\\", "/"))
            if base.endswith(".jsonl"):
                base = base[:-6]
            if UUID_RE.match(base):
                return base.lower()
    return None


def is_claude_argv(argv):
    if not argv:
        return False
    exe = argv[0].replace("\\", "/")
    base = exe.rsplit("/", 1)[-1].lower()
    return base in ("claude", "claude.exe") or "/claude/versions/" in exe


def classify_role(argv):
    if "bg-pty-host" in argv:
        return "pty-host"
    if len(argv) > 1 and argv[1] == "daemon":
        return "daemon"
    if "bg-spare" in argv:
        return "spare"
    return "session"


def proc_record(pid, ppid, argv, cwd, rss_mb):
    return {"pid": pid, "ppid": ppid, "role": classify_role(argv), "argv": " ".join(argv)[:240],
            "cwd": cwd, "rss_mb": rss_mb, "session_id": argv_session_id(argv)}


def procs_linux(proc_root="/proc"):
    out = []
    for name in os.listdir(proc_root):
        if not name.isdigit():
            continue
        base = os.path.join(proc_root, name)
        try:
            with open(os.path.join(base, "cmdline"), "rb") as fh:
                argv = [a for a in fh.read().decode("utf-8", "replace").split("\0") if a]
            if argv and " " in argv[0]:
                argv = argv[0].split() + argv[1:]   # a rewritten process title fuses argv[0] with its first argument
            if not is_claude_argv(argv):
                continue
            cwd = os.readlink(os.path.join(base, "cwd"))
            rss_kb = 0
            ppid = 0
            with open(os.path.join(base, "status"), encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if line.startswith("VmRSS:"):
                        rss_kb = int(line.split()[1])
                    elif line.startswith("PPid:"):
                        ppid = int(line.split()[1])
        except (OSError, ValueError):
            continue   # process exited between listdir and read, or not ours to read
        out.append(proc_record(int(name), ppid, argv, cwd, round(rss_kb / 1024.0, 1)))
    return out


def split_windows_cmdline(cmdline):
    """Minimal CommandLineToArgvW: whitespace separated, double quotes group."""
    return [m[0] or m[1] for m in re.findall(r'"([^"]*)"|(\S+)', cmdline or "")]


def procs_from_cim_json(text):
    """Parse `Get-CimInstance Win32_Process ... | ConvertTo-Json`; CIM has no cwd, so cwd is None."""
    if not text.strip():
        return []
    data = json.loads(text)
    if isinstance(data, dict):
        data = [data]
    out = []
    for row in data:
        argv = split_windows_cmdline(row.get("CommandLine") or "")
        if not is_claude_argv(argv):
            continue
        out.append(proc_record(int(row.get("ProcessId", 0)), int(row.get("ParentProcessId", 0)), argv, None,
                               round((row.get("WorkingSetSize") or 0) / 1048576.0, 1)))
    return out


def procs_windows():
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='claude.exe'\" | "
          "Select-Object ProcessId,ParentProcessId,CommandLine,WorkingSetSize | ConvertTo-Json")
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        raise RuntimeError("CIM query failed: " + res.stderr.strip()[:200])
    return procs_from_cim_json(res.stdout)


def list_claude_procs():
    return procs_windows() if platform.system() == "Windows" else procs_linux()


def free_ram_mb():
    """Available RAM in MB, or None when it cannot be read (unknown is not zero)."""
    try:
        if platform.system() == "Windows":
            ps = "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=60)
            return round(int(res.stdout.strip()) / 1024.0) if res.returncode == 0 else None
        with open("/proc/meminfo", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return round(int(line.split()[1]) / 1024.0)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return None


def last_activity(path):
    """Epoch of the last timestamped record, read from the file tail; None when unreadable."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - TAIL_BYTES))
            tail = fh.read().decode("utf-8", "replace")
    except OSError:
        return None
    for line in reversed(tail.splitlines()):
        try:
            t = parse_ts(json.loads(line).get("timestamp"))
        except (ValueError, AttributeError):
            continue
        if t is not None:
            return t
    return None


def find_by_id(roots, sid):
    for root in roots:
        hits = glob.glob(os.path.join(root, "*", sid + ".jsonl"))
        if hits:
            return hits[0]
    return None


def newest_in_cwd(roots, cwd):
    best = None
    for root in roots:
        for path in glob.glob(os.path.join(root, encode_cwd(cwd), "*.jsonl")):
            try:
                m = os.path.getmtime(path)
            except OSError:
                continue
            if best is None or m > best[0]:
                best = (m, path)
    return best[1] if best else None


_AUTO = object()


def hot_idle_scan(roots, now=None, procs=None, free_mb=_AUTO):
    """Join live claude processes to transcripts. `procs`/`free_mb` are injectable for fixtures."""
    now = time.time() if now is None else now
    procs = list_claude_procs() if procs is None else procs
    free_mb = free_ram_mb() if free_mb is _AUTO else free_mb   # None = injected "unreadable"
    cwd_users = collections.Counter(p["cwd"] for p in procs if p["role"] in JOINABLE and not p["session_id"] and p["cwd"])
    rows = []
    for p in procs:
        row = dict(p, joined_by=None, transcript=None, transcript_mb=None, idle_min=None, state="UNKNOWN")
        if p["role"] in JOINABLE:
            path, how = None, None
            if p["session_id"]:
                path, how = find_by_id(roots, p["session_id"]), "id"
            if path is None and not p["session_id"] and p["cwd"]:
                path, how = newest_in_cwd(roots, p["cwd"]), "cwd"
                row["cwd_sharers"] = cwd_users[p["cwd"]]
            if path:
                t = last_activity(path)
                row["joined_by"], row["transcript"] = how, path
                row["transcript_mb"] = round(os.path.getsize(path) / 1048576.0, 2)
                if t is not None:
                    row["idle_min"] = round(max(0.0, now - t) / 60.0, 1)
                    row["state"] = "JOINED"
        rows.append(row)
    sessions = [r for r in rows if r["role"] in JOINABLE]
    return {
        "processes": len(rows), "sessions": len(sessions),
        "by_role": dict(collections.Counter(r["role"] for r in rows)),
        "joined_by_id": sum(1 for r in sessions if r["joined_by"] == "id" and r["state"] == "JOINED"),
        "joined_by_cwd": sum(1 for r in sessions if r["joined_by"] == "cwd" and r["state"] == "JOINED"),
        "unjoined": sum(1 for r in sessions if r["state"] != "JOINED"),
        "rss_mb_total": round(sum(r["rss_mb"] for r in rows), 1), "free_ram_mb": free_mb,
        "rows": sorted(rows, key=lambda r: (r["idle_min"] is None, -(r["idle_min"] or 0))),
    }


# ---------------------------------------------------------------- advisory (read-only)

ADVISE_IDLE_MIN = 720      # a joined session idle this long (12 h) is listed
ADVISORY_PATH = os.path.expanduser("~/.claude/state/ccn-hot-idle.json")


def release_path(row):
    """The existing safe way to release one session. Text only: nothing here ever acts."""
    if row["role"] == "spare":
        return "pooled spare worker: no per-session release; the pool owner reclaims it"
    cwd = (row.get("cwd") or "").replace("\\", "/")
    if "/missions/" in cwd:
        return "mission worker: `python tools/gsd_mission.py hold --stop <mission id>` (ids: `gsd_mission.py list`)"
    return "pane: the Owner closes this terminal/pane; nothing is killed automatically"


def advise(scan, min_idle=ADVISE_IDLE_MIN):
    """Rank idle joined sessions (idle desc, then working set); UNKNOWN ones are reported, never ranked."""
    idle, unknown = [], []
    for r in scan["rows"]:
        if r["role"] not in JOINABLE:
            continue
        if r["state"] != "JOINED":
            unknown.append({"pid": r["pid"], "role": r["role"], "state": "UNKNOWN", "rss_mb": r["rss_mb"]})
        elif r["idle_min"] >= min_idle:
            idle.append({"pid": r["pid"], "role": r["role"], "idle_hours": round(r["idle_min"] / 60.0, 1),
                         "working_set_mb": round(r["rss_mb"] + (r["transcript_mb"] or 0), 1),
                         "confidence": "HIGH" if r["joined_by"] == "id" else "LOW (joined by cwd)",
                         "release": release_path(r)})
    idle.sort(key=lambda x: (-x["idle_hours"], -x["working_set_mb"]))
    return {"min_idle_min": min_idle, "idle": idle, "unknown": unknown, "free_ram_mb": scan["free_ram_mb"],
            "note": "advisory only (HR-STALLED-SESSION-ADVISORY-001): never kills, holds or releases"}


def write_advisory(adv, path=ADVISORY_PATH):
    """Atomic write so a status surface never reads a half-written file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dict(adv, written_at=time.time()), f, indent=1)
    os.replace(tmp, path)


def fmt_advice(adv):
    lines = ["idle >= %d min: %d listed, %d UNKNOWN (free_ram_mb=%s)" %
             (adv["min_idle_min"], len(adv["idle"]), len(adv["unknown"]), adv["free_ram_mb"])]
    for a in adv["idle"]:
        lines.append("  pid=%s %s idle=%sh ws=%sMB [%s] -> %s" % (a["pid"], a["role"], a["idle_hours"], a["working_set_mb"],
                                                                 a["confidence"], a["release"]))
    for u in adv["unknown"]:
        lines.append("  pid=%s %s UNKNOWN (no transcript joined; not counted as idle)" % (u["pid"], u["role"]))
    return "\n".join(lines)


# ---------------------------------------------------------------- check / CLI

def check_thresholds(dup, stamp):
    """Per-gate verdicts: OK / BREACH / UNMEASURED. UNMEASURED never reads as green."""
    out = {}
    if dup["tool_events"] < MIN_EVENTS:
        out["dup"] = {"verdict": "UNMEASURED", "reason": "tool_events %d < %d" % (dup["tool_events"], MIN_EVENTS)}
    else:
        pct = dup["dup_calls_pct"]
        out["dup"] = {"verdict": "BREACH" if pct > DUP_MAX_PCT else "OK", "value_pct": pct, "limit_pct": DUP_MAX_PCT}
    c, i = stamp["concurrent"], stamp["isolated"]
    if c["n"] < MIN_FIRST_CALLS or i["n"] < MIN_FIRST_CALLS:
        out["stampede"] = {"verdict": "UNMEASURED", "reason": "arms n=%d/%d < %d" % (c["n"], i["n"], MIN_FIRST_CALLS)}
    else:
        ratio = c["write_median"] / i["write_median"] if i["write_median"] else None
        if ratio is None:
            out["stampede"] = {"verdict": "UNMEASURED", "reason": "isolated median write is 0"}
        else:
            out["stampede"] = {"verdict": "BREACH" if ratio > STAMPEDE_MAX_RATIO else "OK",
                               "ratio": round(ratio, 4), "limit": STAMPEDE_MAX_RATIO}
    return out


def fmt_dup(r):
    lines = ["window_h=%s sessions_with_tools=%d tool_events=%d result_bytes=%d" %
             (r["window_h"], r["sessions_with_tools"], r["tool_events"], r["result_bytes"]),
             "cross-session duplicates (<= %ds): calls=%d (%s%%) bytes=%d (%s%%)" %
             (r["window_s"], r["dup_calls"], r["dup_calls_pct"], r["dup_bytes"], r["dup_bytes_pct"])]
    for n, v in r["per_tool"].items():
        lines.append("  %s: %d calls, %d bytes" % (n, v["calls"], v["bytes"]))
    for t in r["top_shared"]:
        lines.append("  top bytes=%d calls=%d sessions=%d %s" % (t["bytes"], t["calls"], t["sessions"], t["key"]))
    return "\n".join(lines)


def fmt_stampede(r):
    c, i = r["concurrent"], r["isolated"]
    return "\n".join([
        "first call, launched <= %ds after another session:" % r["concurrent_s"],
        "  cache_write n=%d median=%s mean=%s | cache_read median=%s mean=%s" % (c["n"], c["write_median"], c["write_mean"], c["read_median"], c["read_mean"]),
        "first call, isolated start:",
        "  cache_write n=%d median=%s mean=%s | cache_read median=%s mean=%s" % (i["n"], i["write_median"], i["write_mean"], i["read_median"], i["read_mean"]),
        "all first calls: write=%d read=%d read_share=%s%%" % (r["first_call_write_total"], r["first_call_read_total"], r["read_share_pct"])])


def fmt_hot_idle(r):
    lines = ["processes=%d sessions=%d roles=%s joined_by_id=%d joined_by_cwd=%d unjoined=%d rss_mb_total=%s free_ram_mb=%s" %
             (r["processes"], r["sessions"], r["by_role"], r["joined_by_id"], r["joined_by_cwd"], r["unjoined"], r["rss_mb_total"], r["free_ram_mb"])]
    for row in r["rows"]:
        if row["role"] not in JOINABLE:
            continue
        lines.append("  pid=%s role=%s rss_mb=%s idle_min=%s transcript_mb=%s joined_by=%s %s" %
                     (row["pid"], row["role"], row["rss_mb"], row["idle_min"], row["transcript_mb"], row["joined_by"], row["state"]))
    return "\n".join(lines)


def build_parser():
    ap = argparse.ArgumentParser(prog="ccn_census", description=__doc__.split("\n")[0])
    ap.add_argument("--root", action="append", help="projects directory (repeatable); default ~/.claude/projects")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dup")
    d.add_argument("--hours", type=float, default=168.0)
    s = sub.add_parser("stampede")
    s.add_argument("--days", type=float, default=7.0)
    h = sub.add_parser("hot-idle")
    h.add_argument("--advise", action="store_true", help="rank idle sessions and print the safe release path (never acts)")
    h.add_argument("--min-idle-min", type=float, default=ADVISE_IDLE_MIN)
    h.add_argument("--state-file", default=ADVISORY_PATH, help="where --advise writes its JSON")
    a = sub.add_parser("all")
    a.add_argument("--hours", type=float, default=168.0)
    a.add_argument("--days", type=float, default=7.0)
    a.add_argument("--check", action="store_true", help="exit 1 on BREACH")
    a.add_argument("--strict", action="store_true", help="with --check, exit 2 when a gate is UNMEASURED")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    roots = args.root or default_roots()
    if args.cmd == "dup":
        res = dup_scan(roots, args.hours)
        print(json.dumps(res, indent=1) if args.json else fmt_dup(res))
    elif args.cmd == "stampede":
        res = stampede_scan(roots, args.days)
        print(json.dumps(res, indent=1) if args.json else fmt_stampede(res))
    elif args.cmd == "hot-idle":
        res = hot_idle_scan(roots)
        if args.advise:
            adv = advise(res, args.min_idle_min)
            write_advisory(adv, args.state_file)
            print(json.dumps(adv, indent=1) if args.json else fmt_advice(adv))
        else:
            print(json.dumps(res, indent=1) if args.json else fmt_hot_idle(res))
    else:
        dup = dup_scan(roots, args.hours)
        stamp = stampede_scan(roots, args.days)
        hot = hot_idle_scan(roots)
        verdicts = check_thresholds(dup, stamp)
        res = {"dup": dup, "stampede": stamp, "hot_idle": hot, "check": verdicts}
        if args.json:
            print(json.dumps(res, indent=1))
        else:
            print("== dup ==\n" + fmt_dup(dup) + "\n== stampede ==\n" + fmt_stampede(stamp) +
                  "\n== hot-idle ==\n" + fmt_hot_idle(hot) + "\n== check ==\n" + json.dumps(verdicts))
        if args.check:
            if any(v["verdict"] == "BREACH" for v in verdicts.values()):
                return 1
            if args.strict and any(v["verdict"] == "UNMEASURED" for v in verdicts.values()):
                return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
