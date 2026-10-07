#!/usr/bin/env python
"""attribute.py -- program spend per model call, coordinating panes included (A1-2 / A2-1, G3-G5). Zero model calls.

`turns.py --attribute ...` delegates here. Reads transcripts directly (the usage index is laptop-only and cannot see
a session that never wrote), so a planning pane that only reads cards and spawns agents is still counted.

processed = input + cache_creation + cache_read + output of one call, deduplicated by `<message.id>|<requestId>`.
A call is attributed to the program on exactly one basis, first match wins:
  write_span    between the first and the last Write/Edit/MultiEdit of a path under a program root, in its session
  lineage_cwd   the call ran with a cwd inside a program root
  lineage_card  the call Read a program card (G4: planning panes rarely write)
Subagent transcripts (`<session>/subagents/*.jsonl`) roll up into their parent session. Sessions named in
`--exclude-sid` (already counted by a ledger source) are skipped and listed. A text-only call outside every basis is
never guessed at: its share is reported under `unknown` (null is not zero).

  python turns.py --attribute --root DIR [--root DIR ...] [--card FILE ...] [--exclude-sid SID ...]
                  --projects-dir DIR [--since ISO] [--json OUT]
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

EDIT_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}


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


def session_of(path: Path, o: dict) -> str:
    parts = path.parts
    if "subagents" in parts:
        return parts[len(parts) - 1 - parts[::-1].index("subagents") - 1]
    return str(o.get("sessionId") or path.stem)


def read_calls(path: Path, roots, cards) -> list:
    """One entry per model call in one transcript, in file order, with the facts attribution needs."""
    calls, order = {}, []
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return []
    with fh:
        for raw in fh:
            try:
                o = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(o, dict) or o.get("type") != "assistant":
                continue
            m = o.get("message") if isinstance(o.get("message"), dict) else {}
            key = f"{m.get('id')}|{o.get('requestId')}"
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


def attribute(paths, roots, cards=(), exclude_sids=(), since=None, dedup=True) -> dict:
    """Pure over the given transcripts. `dedup` exists only so the test can drive the double-count branch."""
    roots = [_norm(r) for r in roots]
    cards = {_norm(c) for c in cards}
    exclude = set(exclude_sids)
    seen: set = set()
    by_sid: dict = {}
    dup = 0
    for p in sorted(Path(x) for x in paths):
        for c in read_calls(p, roots, cards):
            if dedup:
                if c["key"] in seen:
                    dup += 1
                    continue
                seen.add(c["key"])
            by_sid.setdefault(c["sid"], []).append(c)
    basis = {"write_span": 0, "lineage_cwd": 0, "lineage_card": 0}
    sessions, unknown_calls, no_usage, skipped = {}, 0, 0, []
    cutoff = since.timestamp() if since else None
    for sid, cs in sorted(by_sid.items()):
        if sid in exclude:
            skipped.append(sid)
            continue
        cs.sort(key=lambda c: str(c["ts"]))
        w = [i for i, c in enumerate(cs) if c["write"]]
        lo, hi = (w[0], w[-1]) if w else (None, None)
        row = {"calls": len(cs), "attributed_calls": 0, "processed": 0, "basis": dict.fromkeys(basis, 0)}
        for i, c in enumerate(cs):
            if cutoff is not None:
                try:
                    if datetime.fromisoformat(str(c["ts"]).replace("Z", "+00:00")).timestamp() < cutoff:
                        continue
                except ValueError:
                    pass
            b = ("write_span" if lo is not None and lo <= i <= hi else
                 "lineage_cwd" if c["cwd"] and _under(c["cwd"], roots) else
                 "lineage_card" if c["card"] else None)
            if b is None:
                if c["tools"] == 0:
                    unknown_calls += 1
                continue
            if c["processed"] is None:
                no_usage += 1
                continue
            basis[b] += c["processed"]
            row["basis"][b] += c["processed"]
            row["processed"] += c["processed"]
            row["attributed_calls"] += 1
        if row["attributed_calls"]:
            sessions[sid] = row
    unknown = []
    if unknown_calls:
        unknown.append(f"{unknown_calls} text-only calls outside every basis: share UNKNOWN, not counted")
    if no_usage:
        unknown.append(f"{no_usage} attributed calls carry no usage: cost UNKNOWN, not counted")
    return {"unit": "processed", "program_processed": sum(basis.values()), "by_basis": basis,
            "attributed_calls": sum(s["attributed_calls"] for s in sessions.values()), "sessions": sessions,
            "duplicates_dropped": dup, "excluded_sessions": skipped, "unknown": unknown}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--card", action="append", default=[])
    ap.add_argument("--exclude-sid", action="append", default=[])
    ap.add_argument("--projects-dir", required=True)
    ap.add_argument("--since")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    since = datetime.fromisoformat(a.since.replace("Z", "+00:00")) if a.since else None
    # a transcript last written before --since cannot hold a call at or after it: skip it unread
    paths = [str(p) for p in Path(a.projects_dir).rglob("*.jsonl")
             if since is None or p.stat().st_mtime >= since.timestamp()]
    res = attribute(paths, a.root, a.card, a.exclude_sid, since)
    blob = json.dumps(res, indent=1, sort_keys=True)
    if a.json:
        Path(a.json).write_text(blob, encoding="utf-8", newline="\n")
    print(blob)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
