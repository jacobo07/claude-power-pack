#!/usr/bin/env python
"""attribute.py -- program spend per model call, coordinating panes included (A1-2 / A2-1, G3-G5). Zero model calls.

`turns.py --attribute ...` delegates here. Reads transcripts directly (the usage index is laptop-only and cannot see
a session that never wrote), so a planning pane that only reads cards and spawns agents is still counted.

processed = input + cache_creation + cache_read + output of one call, deduplicated by message.id (requestId when the
id is absent). Two separate questions, never mixed (M2):
  session total   every assistant record with usage, attributed or not. This is what a session SPENT.
  attribution     which part of it belongs to the program, first match wins:
    write_span    between the first and the last Write/Edit/MultiEdit of a path under a program root, in its session
    lineage_cwd   the call ran with a cwd inside a program root
    lineage_card  the call Read a program card (G4: planning panes rarely write)
  Attribution is a breakdown of the total and can never reduce it: calls outside every basis are the session's
  `unattributed` row, counted in the total and never in `program_processed`.
Subagent transcripts (`<session>/subagents/*.jsonl`) roll up into their parent session. Sessions named in
`--exclude-sid` (already counted by a ledger source) are skipped and listed.
Unparseable (torn) JSONL lines are counted and reported, never skipped silently (M4): they make a total a lower bound.

  python turns.py --attribute --root DIR [--root DIR ...] [--card FILE ...] [--exclude-sid SID ...]
                  --projects-dir DIR [--since ISO] [--until ISO] [--json OUT]
  python attribute.py --session SID [--session SID ...] --projects-dir DIR [--until ISO] [--host SID=HOST ...]
      session meter: finds SID in EVERY project dir, runs this counter AND the independent stage0/self_spend.py and
      returns AGREE only when both match to the token; DISAGREE / UNKNOWN / INCOMPLETE never carry a number.
      exit 0 all AGREE, 1 any DISAGREE, 2 any UNKNOWN, 3 any INCOMPLETE (torn lines).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

EDIT_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
SELF_SPEND = Path(__file__).resolve().parents[1] / "gen2" / "evidence" / "stage0" / "self_spend.py"


def processed(usage) -> int | None:
    """Sum of the four token fields, or None when the call carries no usage at all (never 0)."""
    if not isinstance(usage, dict):
        return None
    keys = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
    vals = [usage.get(k) for k in keys]
    if all(v is None for v in vals):
        return None
    return sum(v for v in vals if isinstance(v, int) and not isinstance(v, bool))


def _norm(p) -> str:
    return os.path.normcase(os.path.normpath(str(p)))


def _under(path, roots) -> bool:
    n = _norm(path)
    return any(n == r or n.startswith(r + os.sep) for r in roots)


def _ts(v):
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def session_of(path: Path, o: dict) -> str:
    parts = path.parts
    if "subagents" in parts:
        return parts[len(parts) - 1 - parts[::-1].index("subagents") - 1]
    return str(o.get("sessionId") or path.stem)


def find_session_files(sid: str, projects_dir) -> list:
    """M1: every transcript of `sid` under `projects_dir` and under EVERY directory directly below it, subagents
    included, deduplicated by real path. An empty list means the session is unknown here, never zero spend."""
    root = Path(projects_dir)
    found: dict = {}
    if not root.is_dir():
        return []
    for pdir in [root] + sorted(d for d in root.iterdir() if d.is_dir()):
        top = pdir / f"{sid}.jsonl"
        if top.is_file():
            found[os.path.realpath(top)] = top
        sub = pdir / sid
        if sub.is_dir():
            for f in sub.rglob("*.jsonl"):
                found[os.path.realpath(f)] = f
    return [found[k] for k in sorted(found)]


def read_calls(path: Path, roots, cards, stats=None) -> list:
    """One entry per model call in one transcript, in file order, with the facts attribution needs."""
    calls, order = {}, []
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        if stats is not None:
            stats.setdefault("unreadable", []).append(str(path))
        return []
    with fh:
        for n, raw in enumerate(fh):
            if not raw.strip():
                continue
            try:
                o = json.loads(raw)
            except ValueError:
                if stats is not None:
                    stats["torn_lines"] = stats.get("torn_lines", 0) + 1
                    stats.setdefault("torn_files", {}).setdefault(str(path), 0)
                    stats["torn_files"][str(path)] += 1
                continue
            if not isinstance(o, dict) or o.get("type") != "assistant":
                continue
            m = o.get("message") if isinstance(o.get("message"), dict) else {}
            key = str(m.get("id") or o.get("requestId") or f"{path}:{n}")
            c = calls.get(key)
            if c is None:
                c = calls[key] = {"key": key, "sid": session_of(path, o), "ts": o.get("timestamp"),
                                  "cwd": o.get("cwd"), "processed": processed(m.get("usage")),
                                  "write": False, "card": False, "tools": 0}
                order.append(key)
            elif c["processed"] is None:
                c["processed"] = processed(m.get("usage"))
            for blk in m.get("content") if isinstance(m.get("content"), list) else []:
                if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                    continue
                c["tools"] += 1
                inp = blk.get("input") if isinstance(blk.get("input"), dict) else {}
                name = blk.get("name")
                tgt = inp.get(EDIT_TOOLS[name]) if name in EDIT_TOOLS else (inp.get("file_path") if name == "Read" else None)
                if not tgt:
                    continue
                p = Path(str(tgt))
                if not p.is_absolute() and o.get("cwd"):
                    p = Path(o["cwd"]) / p
                if name in EDIT_TOOLS and _under(p, roots):
                    c["write"] = True
                if name == "Read" and _norm(p) in cards:
                    c["card"] = True
    return [calls[k] for k in order]


def attribute(paths, roots, cards=(), exclude_sids=(), since=None, dedup=True, until=None) -> dict:
    """Pure over the given transcripts. `dedup` exists only so the test can drive the double-count branch."""
    roots = [_norm(r) for r in roots]
    cards = {_norm(c) for c in cards}
    exclude = set(exclude_sids)
    seen: set = set()
    by_sid: dict = {}
    dup = 0
    stats: dict = {}
    for p in sorted(Path(x) for x in paths):
        for c in read_calls(p, roots, cards, stats):
            if dedup:
                if c["key"] in seen:
                    dup += 1
                    continue
                seen.add(c["key"])
            by_sid.setdefault(c["sid"], []).append(c)
    basis = {"write_span": 0, "lineage_cwd": 0, "lineage_card": 0}
    sessions, totals, unknown_calls, no_usage, skipped = {}, {}, 0, 0, []
    lo_cut = since.timestamp() if since else None
    hi_cut = until.timestamp() if until else None
    for sid, cs in sorted(by_sid.items()):
        if sid in exclude:
            skipped.append(sid)
            continue
        cs.sort(key=lambda c: str(c["ts"]))
        w = [i for i, c in enumerate(cs) if c["write"]]
        lo, hi = (w[0], w[-1]) if w else (None, None)
        row = {"calls": len(cs), "attributed_calls": 0, "processed": 0, "basis": dict.fromkeys(basis, 0)}
        tot = {"calls": 0, "processed": 0, "no_usage_calls": 0, "unattributed_calls": 0, "unattributed_processed": 0}
        for i, c in enumerate(cs):
            t = _ts(c["ts"])
            if t is not None and ((lo_cut is not None and t < lo_cut) or (hi_cut is not None and t > hi_cut)):
                continue
            if c["processed"] is None:
                tot["no_usage_calls"] += 1
            else:
                tot["calls"] += 1
                tot["processed"] += c["processed"]
            b = ("write_span" if lo is not None and lo <= i <= hi else
                 "lineage_cwd" if c["cwd"] and _under(c["cwd"], roots) else
                 "lineage_card" if c["card"] else None)
            if b is None:
                if c["tools"] == 0:
                    unknown_calls += 1
                if c["processed"] is not None:
                    tot["unattributed_calls"] += 1
                    tot["unattributed_processed"] += c["processed"]
                continue
            if c["processed"] is None:
                no_usage += 1
                continue
            basis[b] += c["processed"]
            row["basis"][b] += c["processed"]
            row["processed"] += c["processed"]
            row["attributed_calls"] += 1
        totals[sid] = tot
        if row["attributed_calls"]:
            sessions[sid] = row
    unknown = []
    if unknown_calls:
        unknown.append(f"{unknown_calls} text-only calls outside every basis: unattributed row of the session total, "
                       "never in program_processed")
    if no_usage:
        unknown.append(f"{no_usage} attributed calls carry no usage: cost UNKNOWN, not counted")
    if stats.get("torn_lines"):
        unknown.append(f"{stats['torn_lines']} torn JSONL lines unparsed: totals are a LOWER BOUND, the fragment is UNKNOWN")
    if stats.get("unreadable"):
        unknown.append(f"{len(stats['unreadable'])} transcripts unreadable: their spend is UNKNOWN")
    return {"unit": "processed", "program_processed": sum(basis.values()), "by_basis": basis,
            "attributed_calls": sum(s["attributed_calls"] for s in sessions.values()), "sessions": sessions,
            "session_totals": totals, "total_processed": sum(t["processed"] for t in totals.values()),
            "total_calls": sum(t["calls"] for t in totals.values()),
            "unattributed_processed": sum(t["unattributed_processed"] for t in totals.values()),
            "torn_lines": stats.get("torn_lines", 0), "torn_files": stats.get("torn_files", {}),
            "duplicates_dropped": dup, "excluded_sessions": skipped, "unknown": unknown}


def _second_counter(sid: str, projects_dir, until) -> dict | None:
    """The independent counter: stage0/self_spend.py run as its own process. Shares no parser with this module."""
    argv = [sys.executable, "-I", str(SELF_SPEND), "--session", sid, "--dir", str(projects_dir)]
    if until:
        argv += ["--until", until]
    p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"calls (\d+) processed ([\d,]+).* torn (\d+)", p.stdout)
    if not m:
        return None
    return {"calls": int(m.group(1)), "processed": int(m.group(2).replace(",", "")), "torn_lines": int(m.group(3))}


def meter_session(sid: str, projects_dir, until: str | None = None, host: str | None = None, second=_second_counter) -> dict:
    """M1+M3+M4+M5. A number is only ever returned under verdict AGREE (or INCOMPLETE, as a labelled lower bound)."""
    files = find_session_files(sid, projects_dir)
    if not files:
        where = f"on host {host}, no local transcript" if host else f"no transcript under {projects_dir}"
        return {"sid": sid, "verdict": "UNKNOWN", "host": host, "why": where}
    u = datetime.fromisoformat(until.replace("Z", "+00:00")) if until else None
    a = attribute(files, [], until=u)
    mine = {"calls": a["total_calls"], "processed": a["total_processed"], "torn_lines": a["torn_lines"]}
    other = second(sid, projects_dir, until)
    out = {"sid": sid, "files": len(files), "host": host, "counters": {"attribute": mine, "self_spend": other}}
    if other is None:
        out.update(verdict="UNKNOWN", why="second counter produced no reading")
    elif (mine["calls"], mine["processed"]) != (other["calls"], other["processed"]):
        out.update(verdict="DISAGREE", why="the two counters differ; no number is reported")
    elif mine["torn_lines"] or other["torn_lines"]:
        out.update(verdict="INCOMPLETE", lower_bound=mine, why=f"{max(mine['torn_lines'], other['torn_lines'])} torn lines")
    else:
        out.update(verdict="AGREE", calls=mine["calls"], processed=mine["processed"])
    return out


EXIT = {"AGREE": 0, "DISAGREE": 1, "UNKNOWN": 2, "INCOMPLETE": 3}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", default=[])
    ap.add_argument("--card", action="append", default=[])
    ap.add_argument("--exclude-sid", action="append", default=[])
    ap.add_argument("--projects-dir", required=True)
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--json")
    ap.add_argument("--session", action="append", default=[])
    ap.add_argument("--host", action="append", default=[], help="SID=HOST, a session known to live on another host")
    a = ap.parse_args(argv)
    if a.session:
        hosts = dict(h.split("=", 1) for h in a.host if "=" in h)
        rows = [meter_session(s, a.projects_dir, a.until, hosts.get(s)) for s in a.session]
        blob = json.dumps(rows, indent=1, sort_keys=True)
        if a.json:
            Path(a.json).write_text(blob, encoding="utf-8", newline="\n")
        print(blob)
        return max(EXIT[r["verdict"]] for r in rows)
    if not a.root:
        ap.error("--root is required unless --session is given")
    since = datetime.fromisoformat(a.since.replace("Z", "+00:00")) if a.since else None
    until = datetime.fromisoformat(a.until.replace("Z", "+00:00")) if a.until else None
    # a transcript last written before --since cannot hold a call at or after it: skip it unread
    paths = [str(p) for p in Path(a.projects_dir).rglob("*.jsonl")
             if since is None or p.stat().st_mtime >= since.timestamp()]
    res = attribute(paths, a.root, a.card, a.exclude_sid, since, until=until)
    blob = json.dumps(res, indent=1, sort_keys=True)
    if a.json:
        Path(a.json).write_text(blob, encoding="utf-8", newline="\n")
    print(blob)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
