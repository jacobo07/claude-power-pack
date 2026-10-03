#!/usr/bin/env python
"""Skill invocations from transcripts -- what was actually CALLED, never what was mentioned.

Two observable channels (PLAN-SKILL-RESIDENCY C1, audit G'8/G'9):
  model  assistant tool_use name == "Skill"  -> input.skill        (deduped by tool_use id)
  typed  user row, STRING content, not isMeta, carrying <command-name>/X</command-name> in either
         order with <command-message>, X an installed skill/command  (deduped by row uuid)
Never counted: skill listings, hook output, pointers, tool inputs that mention a name, the isMeta
expansion that follows a typed command (turnCompanion) or a Skill call (sourceToolUseID), built-ins
(/clear, /compact). List-form user rows that carry a command tag are reported as `unknown_rows`
(an aperture, not a zero). Subagent transcripts (<session>/subagents/*.jsonl) join their parent by
the FILE's session id, never by a row's session_id field.

Row-time bounds (optional): count_file(since=, until=) and scan(bound_rows=True) keep only candidate rows whose
`timestamp` lies in [since, until] (epoch seconds). A candidate row with no parseable timestamp (a timezone-naive one
included) is counted in
`untimed_rows` and on no channel: an aperture, never an invocation and never a zero. Unbounded output is unchanged.

Not observable here at all: bodies a hook injects (SessionStart, JIT), doctrine cards. Those deliver
a capability with no invocation event, so "no observed invocation" never means "never delivered".

    python tools/skill_invocations.py [--days 7] [--root ~/.claude/projects]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from collections import Counter
from pathlib import Path

TAG = re.compile(r"<command-name>\s*/([\w:.-]+)\s*</command-name>")
MSG = re.compile(r"<command-message>")


def installed_names(home: Path | None = None) -> set[str]:
    """Skill dirs and command files under ~/.claude; nested command dirs give `dir:stem`."""
    home = home or Path.home() / ".claude"
    out: set[str] = set()
    sk = home / "skills"
    if sk.is_dir():
        out.update(p.name for p in sk.iterdir() if p.is_dir())
    cm = home / "commands"
    if cm.is_dir():
        for p in cm.rglob("*.md"):
            rel = p.relative_to(cm).with_suffix("")
            out.add(":".join(rel.parts))
    return out


def typed_name(content: str, installed: set[str]) -> str | None:
    """The command a STRING user row invoked, or None. Both tag orders; built-ins excluded."""
    m = TAG.search(content)
    if not m or not MSG.search(content):
        return None
    name = m.group(1)
    return name if (name in installed or ":" in name) else None


def session_of(path: Path) -> str:
    """Main transcript: its stem. Subagent transcript: the session dir above `subagents/`."""
    if path.parent.name == "subagents":
        return path.parent.parent.name
    return path.stem


def row_epoch(d: dict) -> float | None:
    """The row's ISO `timestamp` as epoch seconds, or None when missing or unparseable. A timezone-naive
    timestamp (no `Z` or offset, or a date only) is unparseable here: reading it as host-local time would
    bound the same row differently on two hosts."""
    ts = d.get("timestamp") if isinstance(d, dict) else None
    if not isinstance(ts, str):
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt.timestamp()


def count_file(path: Path, installed: set[str], seen: set | None = None,
               since: float | None = None, until: float | None = None) -> dict:
    seen = seen if seen is not None else set()
    model, typed, unknown, untimed = Counter(), Counter(), 0, 0
    bounded = since is not None or until is not None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"Skill"' not in line and "command-name" not in line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if bounded:
                ep = row_epoch(d)
                if ep is None:
                    untimed += 1
                    continue
                if (since is not None and ep < since) or (until is not None and ep > until):
                    continue
            m = d.get("message") or {}
            if d.get("type") == "assistant":
                for b in m.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill":
                        key = ("t", b.get("id"))
                        if b.get("id") and key in seen:
                            continue
                        seen.add(key)
                        model[(b.get("input") or {}).get("skill") or "?"] += 1
            elif d.get("type") == "user" and not d.get("isMeta"):
                c = m.get("content")
                if isinstance(c, str):
                    name = typed_name(c, installed)
                    if name:
                        key = ("u", d.get("uuid"))
                        if d.get("uuid") and key in seen:
                            continue
                        seen.add(key)
                        typed[name] += 1
                elif isinstance(c, list) and any(isinstance(b, dict) and TAG.search(str(b.get("text", "")))
                                                 for b in c):
                    unknown += 1
    return {"session": session_of(path), "model": model, "typed": typed, "unknown_rows": unknown,
            "untimed_rows": untimed}


def scan(root: Path, days: float, installed: set[str], now: float | None = None,
         bound_rows: bool = False) -> dict:
    now_eff = now or time.time()
    cut = now_eff - days * 86400
    model, typed, unknown, files, sessions, untimed = Counter(), Counter(), 0, 0, set(), 0
    seen: set = set()
    for f in root.rglob("*.jsonl"):
        try:
            if f.stat().st_mtime < cut:
                continue
        except OSError:
            continue
        files += 1
        r = (count_file(f, installed, seen, since=cut, until=now_eff) if bound_rows
             else count_file(f, installed, seen))
        model.update(r["model"]); typed.update(r["typed"]); unknown += r["unknown_rows"]
        untimed += r["untimed_rows"]
        if r["model"] or r["typed"]:
            sessions.add(r["session"])
    return {"files": files, "sessions_with_calls": len(sessions), "model": model, "typed": typed,
            "unknown_rows": unknown, "untimed_rows": untimed}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float, default=7)
    ap.add_argument("--root", default=str(Path.home() / ".claude" / "projects"))
    a = ap.parse_args(argv)
    r = scan(Path(os.path.expanduser(a.root)), a.days, installed_names())
    names = set(r["model"]) | set(r["typed"])
    print(f"window {a.days:g} d; files {r['files']}; model Skill calls {sum(r['model'].values())}; "
          f"typed {sum(r['typed'].values())}; list-form command rows (UNKNOWN) {r['unknown_rows']}")
    for n in sorted(names, key=lambda n: -(r["model"][n] + r["typed"][n])):
        print(f"  {r['model'][n]:5d} {r['typed'][n]:5d}  {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
