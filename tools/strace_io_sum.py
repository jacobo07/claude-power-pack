#!/usr/bin/env python3
"""strace open-set summer and query runner (incremental-cognition phase 2, plan 02-02).

Exposure is the set of files a process actually opened, not the selector's intention. This turns an
`strace -f -y -e trace=openat,read,pread64,readv,preadv` log into the columns of the KME-L comparison table:
raw bytes read, distinct corpus files opened, unique bytes by (st_dev, st_ino), cross-project bytes, forbidden
(client-confidential) bytes and opens, and the whole-corpus index bytes as a separate column.

    strace_io_sum.py sum LOG [LOG ...] --corpus-root R [--scope-regex RX] [--forbid-regex RX]
                     [--index-path P ...] [--list-opened]
    strace_io_sum.py run --label L --repeat N [--trace-repeat K] [--trace-dir D] [--evict PATH ...]
                     [--ok-exit C ...] --step 'ARGV' [--step 'ARGV' ...] --corpus-root R [sum options]

Output is one JSON object. It prints paths and numbers only, never file content. An empty or unparsable log is
UNMEASURED (exit 3), never a zero. Exit codes: 0 ok, 1 a run failed, 2 usage, 3 UNMEASURED, 4 strace missing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter

STRACE_EVENTS = "openat,read,pread64,readv,preadv"
READ_SYSCALLS = frozenset({"read", "pread64", "readv", "preadv"})
OPEN_SYSCALLS = frozenset({"open", "openat", "openat2"})
DEFAULT_FORBID = r"(?i)costaluz"
INDEX_SIBLINGS = ("", "-wal", "-shm", "-journal")
CACHE_LABEL = "evicted best-effort, residency not measured"

_RE_RESUMED = re.compile(r"^(?:(\d+)\s+)?<\.\.\. ([a-z0-9_]+) resumed>")
_RE_START = re.compile(r"^(?:(\d+)\s+)?([a-z0-9_]+)\(")
_RE_UNFINISHED = re.compile(r"<unfinished \.\.\.>\s*$")
_RE_RET = re.compile(r"^.*\)\s+=\s+(-?\d+|\?)(?:<(.*)>)?(?:\s+.*)?$")
_RE_FDPATH = re.compile(r"\((\d+)<(.*?)>(?:,|\))")
_RE_IGNORED = re.compile(r"^(?:\d+\s+)?(?:---|\+\+\+)")


def parse_syscalls(lines):
    """Yield (name, path, ret) for every completed openat/read-family call, pairing unfinished/resumed by PID.

    `path` is the fd annotation of a read, or the return annotation of an open. Lines that are not a recognised
    syscall are counted in the second value returned by the generator's owner via `Parse.unparsed`.
    """
    st = Parse()
    pending = {}
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip() or _RE_IGNORED.match(line):
            continue
        m = _RE_RESUMED.match(line)
        if m:
            pid, name = m.group(1) or "0", m.group(2)
            prev = pending.pop(pid, None)
            r = _RE_RET.match(line)
            if prev is None or prev[0] != name or r is None or r.group(1) == "?":
                st.unparsed += 1
                continue
            st.calls.append((name, prev[1] if name in READ_SYSCALLS else r.group(2), int(r.group(1))))
            continue
        m = _RE_START.match(line)
        if not m:
            st.unparsed += 1
            continue
        pid, name = m.group(1) or "0", m.group(2)
        if name not in READ_SYSCALLS and name not in OPEN_SYSCALLS:
            st.unparsed += 1
            continue
        fd = _RE_FDPATH.search(line) if name in READ_SYSCALLS else None
        if _RE_UNFINISHED.search(line):
            pending[pid] = (name, fd.group(2) if fd else None)
            continue
        r = _RE_RET.match(line)
        if r is None or r.group(1) == "?":
            st.unparsed += 1
            continue
        if name in READ_SYSCALLS:
            if fd is None:
                st.unparsed += 1
                continue
            st.calls.append((name, fd.group(2), int(r.group(1))))
        else:
            st.calls.append((name, r.group(2), int(r.group(1))))
    st.unparsed += len(pending)
    return st


class Parse:
    def __init__(self):
        self.calls = []
        self.unparsed = 0


def unique_key(path):
    """Identity of a file for the unique-bytes column: (st_dev, st_ino). Raises OSError when it no longer stats."""
    s = os.stat(path)
    return (s.st_dev, s.st_ino), s.st_size


def finalize_verdict(syscalls_parsed):
    """MEASURED only when at least one syscall was parsed; an empty or unreadable log is UNMEASURED."""
    return "MEASURED" if syscalls_parsed > 0 else "UNMEASURED"


def _roots(corpus_root):
    r = corpus_root.rstrip("/") or "/"
    out = {r}
    with_real = os.path.realpath(r)
    out.add(with_real)
    return sorted(out, key=len, reverse=True)


def _project_of(path, roots):
    for r in roots:
        if path.startswith(r + "/"):
            rel = path[len(r) + 1:]
            return rel.split("/", 1)[0] if rel else None
    return None


def summarize(logs, corpus_root, scope_regex=None, forbid_regex=None, index_paths=(), list_opened=False):
    """Sum one or more strace logs (the steps of one query) into the table columns."""
    forbid = re.compile(forbid_regex if forbid_regex is not None else DEFAULT_FORBID)
    scope = re.compile(scope_regex) if scope_regex else None
    roots = _roots(corpus_root)
    index_set = set()
    for p in index_paths:
        for base in {p, os.path.realpath(p)}:
            for sib in INDEX_SIBLINGS:
                index_set.add(base + sib)

    calls, unparsed = [], 0
    for lp in logs:
        with open(lp, "r", errors="replace") as fh:
            parsed = parse_syscalls(fh)
        calls.extend(parsed.calls)
        unparsed += parsed.unparsed

    raw_bytes = index_bytes = other_bytes = forbidden_bytes = cross_bytes = 0
    forbidden_opens = 0
    by_project = {}
    opened = set()
    per_path = Counter()
    for name, path, ret in calls:
        if name in OPEN_SYSCALLS:
            if ret < 0 or not path:
                continue
            if forbid.search(path):
                forbidden_opens += 1
            if path.endswith(".jsonl") and _project_of(path, roots) is not None:
                opened.add(path)
            continue
        if ret <= 0 or path is None:
            continue
        per_path[path] += ret
        if forbid.search(path):
            forbidden_bytes += ret
        if path in index_set:
            index_bytes += ret
            continue
        proj = _project_of(path, roots)
        if proj is not None and path.endswith(".jsonl"):
            raw_bytes += ret
            slot = by_project.setdefault(proj, {"bytes": 0, "files": set()})
            slot["bytes"] += ret
            slot["files"].add(path)
            if scope is not None and not scope.search(proj):
                cross_bytes += ret
        else:
            other_bytes += ret

    keys, unstattable, unique_bytes = {}, [], 0
    for p in sorted(opened):
        try:
            key, size = unique_key(p)
        except OSError:
            unstattable.append(p)
            continue
        if key not in keys:
            keys[key] = size
            unique_bytes += size

    parsed_n = len(calls)
    out = {
        "verdict": finalize_verdict(parsed_n),
        "syscalls_parsed": parsed_n,
        "lines_unparsed": unparsed,
        "corpus_root": corpus_root,
        "raw_bytes": raw_bytes,
        "raw_files_opened": len(opened),
        "unique_bytes": unique_bytes,
        "unstattable": unstattable,
        "cross_project_bytes": (cross_bytes if scope is not None else None),
        "forbidden_bytes": forbidden_bytes,
        "forbidden_opens": forbidden_opens,
        "index_bytes": index_bytes,
        "other_bytes": other_bytes,
        "by_project": {k: {"bytes": v["bytes"], "files": len(v["files"])} for k, v in sorted(by_project.items())},
        "open_set_sha256": hashlib.sha256("\n".join(sorted(opened)).encode()).hexdigest(),
    }
    if out["verdict"] == "UNMEASURED":
        # an unmeasured log must not read as zero: every column is null, not 0
        for k in ("raw_bytes", "raw_files_opened", "unique_bytes", "forbidden_bytes", "forbidden_opens",
                  "index_bytes", "other_bytes"):
            out[k] = None
        out["cross_project_bytes"] = None
    if list_opened:
        out["opened_paths"] = sorted(opened)
    out["_opened"] = opened
    return out


def public(summary):
    return {k: v for k, v in summary.items() if not k.startswith("_")}


# --------------------------------------------------------------------------- run
def evict(paths):
    """Best-effort page-cache eviction: open each regular file read-only and posix_fadvise DONTNEED. No byte is read."""
    ok = fail = 0
    for top in paths:
        files = []
        if os.path.isdir(top):
            for d, _dirs, fns in os.walk(top):
                files.extend(os.path.join(d, f) for f in fns)
        else:
            files.append(top)
        for f in files:
            try:
                fd = os.open(f, os.O_RDONLY)
            except OSError:
                fail += 1
                continue
            try:
                os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                ok += 1
            except OSError:
                fail += 1
            finally:
                os.close(fd)
    return ok, fail


def _run_step(argv, out_dir, tag, wrap=None):
    cmd = (wrap or []) + argv
    if out_dir:
        so = open(os.path.join(out_dir, tag + ".stdout"), "wb")
        se = open(os.path.join(out_dir, tag + ".stderr"), "wb")
    else:
        so = se = subprocess.DEVNULL
    t0 = time.monotonic()
    try:
        rc = subprocess.run(cmd, stdout=so, stderr=se, stdin=subprocess.DEVNULL).returncode
    except OSError as exc:
        rc = 127
        if out_dir:
            se.write(f"{exc.__class__.__name__}: {exc}\n".encode())
    wall = time.monotonic() - t0
    if out_dir:
        so.close()
        se.close()
    return rc, wall


def run_query(args, out_dir):
    steps = [shlex.split(s) for s in args.step]
    ok_exit = set(args.ok_exit) if args.ok_exit else {0}
    cache = {"mode": "not evicted (page cache as found)"}
    ev_ok = ev_fail = ev_reps = 0

    def maybe_evict():
        nonlocal ev_ok, ev_fail, ev_reps
        if args.evict:
            o, f = evict(args.evict)
            ev_ok += o
            ev_fail += f
            ev_reps += 1

    wall_runs, failed = [], []
    for i in range(args.repeat):
        maybe_evict()
        walls, bad = [], None
        for j, argv in enumerate(steps):
            rc, w = _run_step(argv, out_dir, f"{args.label}-w{i}-s{j}")
            walls.append(round(w, 6))
            if rc not in ok_exit:
                bad = {"run": i, "step": j, "exit": rc}
                break
        total = round(sum(walls), 6)
        wall_runs.append({"run": i, "wall_s": total, "step_walls_s": walls, "failed": bad is not None})
        if bad:
            failed.append(bad)
    good = [r["wall_s"] for r in wall_runs if not r["failed"]]
    median = round(statistics.median(good), 6) if good else None

    traced, sets, t_failed = [], [], []
    for i in range(args.trace_repeat):
        maybe_evict()
        logs, bad = [], None
        for j, argv in enumerate(steps):
            log = os.path.join(out_dir, f"{args.label}-r{i}-s{j}.strace")
            logs.append(log)
            rc, _w = _run_step(argv, out_dir, f"{args.label}-t{i}-s{j}",
                               wrap=[STRACE, "-f", "-y", "-e", f"trace={STRACE_EVENTS}", "-o", log])
            if rc not in ok_exit:
                bad = {"trace_run": i, "step": j, "exit": rc}
                break
        if bad:
            t_failed.append(bad)
            traced.append({"run": i, "failed": True, "step": bad["step"], "exit": bad["exit"]})
            continue
        s = summarize(logs, args.corpus_root, args.scope_regex, args.forbid_regex, args.index_path or ())
        entry = public(s)
        entry["run"] = i
        entry["failed"] = False
        entry["logs"] = logs
        traced.append(entry)
        if s["verdict"] == "MEASURED":
            sets.append(s["_opened"])
    ident = None
    if len(sets) >= 2 and len(sets) == args.trace_repeat:
        ident = all(x == sets[0] for x in sets[1:])
    if args.evict:
        cache = {"mode": CACHE_LABEL, "evicted": ev_ok, "failed": ev_fail, "repetitions_evicted": ev_reps}
    return {
        "label": args.label,
        "steps": args.step,
        "n": args.repeat,
        "wall_runs": wall_runs,
        "wall_median_s": median,
        "failed": failed + t_failed,
        "traced": traced,
        "open_set_identical": ident,
        "cache": cache,
        "trace_dir": out_dir,
    }


# --------------------------------------------------------------------------- cli
def _common(p):
    p.add_argument("--corpus-root", required=True)
    p.add_argument("--scope-regex", default=None)
    p.add_argument("--forbid-regex", default=None)
    p.add_argument("--index-path", action="append", default=None)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="strace_io_sum.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    sp = sub.add_parser("sum", help="summarise strace logs")
    sp.add_argument("logs", nargs="+")
    _common(sp)
    sp.add_argument("--list-opened", action="store_true")
    sp.add_argument("--json", action="store_true", help="accepted for symmetry; output is always JSON")
    rp = sub.add_parser("run", help="run a query untraced for wall and traced for bytes")
    rp.add_argument("--label", required=True)
    rp.add_argument("--repeat", type=int, required=True)
    rp.add_argument("--trace-repeat", type=int, default=0)
    rp.add_argument("--trace-dir", default=None)
    rp.add_argument("--evict", action="append", default=None)
    rp.add_argument("--ok-exit", type=int, action="append", default=None)
    rp.add_argument("--step", action="append", required=True)
    _common(rp)
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code not in (0, None) else 0
    if args.cmd is None:
        ap.print_usage(sys.stderr)
        return 2
    if args.cmd == "sum":
        for lp in args.logs:
            if not os.path.exists(lp):
                print(f"strace_io_sum: log not found: {lp}", file=sys.stderr)
                return 2
        s = summarize(args.logs, args.corpus_root, args.scope_regex, args.forbid_regex,
                      args.index_path or (), args.list_opened)
        print(json.dumps(public(s), indent=1))
        return 3 if s["verdict"] == "UNMEASURED" else 0
    if args.repeat < 0 or args.trace_repeat < 0 or (args.repeat == 0 and args.trace_repeat == 0):
        print("strace_io_sum: need --repeat or --trace-repeat above 0", file=sys.stderr)
        return 2
    if args.trace_repeat > 0 and not (shutil.which("strace") or os.path.exists(STRACE)):
        print("strace_io_sum: strace not found", file=sys.stderr)
        return 4
    out_dir = args.trace_dir or tempfile.mkdtemp(prefix="strace-io-")
    os.makedirs(out_dir, exist_ok=True)
    res = run_query(args, out_dir)
    print(json.dumps(res, indent=1))
    if any(t.get("verdict") == "UNMEASURED" for t in res["traced"]):
        return 3
    return 1 if res["failed"] else 0


STRACE = shutil.which("strace") or "/usr/bin/strace"

if __name__ == "__main__":
    sys.exit(main())
