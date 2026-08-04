#!/usr/bin/env python3
"""stop1_queue.py -- the STOP #1 transition producer (UCEIMR G1).

A STOP #1 is the estate's blocking decision point: a plan writes
`status: STOP #1` to its front matter and waits for the Owner. Nothing ever
wrote the other side of that transition. The field only ever moved in one
direction, so the queue could only grow -- the sealed
`feedback_status_field_nobody_can_transition` pattern, at portfolio tier.

Measured 2026-08-04: **15** plan files carry an open STOP #1, the oldest nine
days old. The count being tracked in conversation was five. Nobody was lying;
the number was being remembered rather than derived, which is
`feedback_hand_curated_audit_measures_memory`.

This module supplies the missing half:

  scan()      discover every open STOP #1 from disk, never from a list
  resolve()   write the transition -- the ONLY producer of a terminal status
  gate()      PR-STOP1-PORTFOLIO-001: report the open queue before another
              STOP #1 is opened

Transitions are Owner-authored: `resolve()` demands a terminal status and a
reason, and refuses to invent either. It edits ONE front-matter key and leaves
the rest of the document byte-identical -- a resolver that rewrites the plan it
resolves would destroy the evidence the decision rests on.

Stdlib-only. Fail-open on scan, fail-closed on resolve.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = _PP_ROOT / "vault" / "plans"

OPEN_MARKER = "STOP #1"
# Terminal statuses. A STOP #1 leaves the queue by being decided, superseded or
# abandoned -- never by being edited into silence.
RESOLVED = "RESOLVED"
ARCHIVED = "ARCHIVED"
SUPERSEDED = "SUPERSEDED"
TERMINAL = (RESOLVED, ARCHIVED, SUPERSEDED)

_MAX_HEAD_BYTES = 8000
_FM_LINE = re.compile(r"^(?P<key>[a-z_]+):[ \t]*(?P<val>.*)$", re.I)


@dataclass
class Stop1Entry:
    path: str
    title: str
    status: str
    date: str
    age_days: int = -1          # -1 == undatable, never silently 0
    verdict: str = ""

    @property
    def undated(self) -> bool:
        return self.age_days < 0


@dataclass
class QueueReport:
    entries: list = field(default_factory=list)
    scanned: int = 0
    undated: int = 0

    @property
    def open_count(self) -> int:
        return len(self.entries)

    @property
    def oldest(self):
        dated = [e for e in self.entries if not e.undated]
        return max(dated, key=lambda e: e.age_days) if dated else None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = {}
    for line in parts[1].split("\n"):
        m = _FM_LINE.match(line)
        if m:
            fm.setdefault(m.group("key").lower(), m.group("val").strip())
    return fm


def scan(plans_dir=None, now=None) -> QueueReport:
    """Every open STOP #1, discovered from disk.

    `PR-COVERAGE-BY-CONSTRUCTION-001`: the denominator is what exists, never a
    curated register. A plan absent from someone's memory is still in the queue.
    Fail-open -> an empty report, never a raise.
    """
    rep = QueueReport()
    base = Path(plans_dir) if plans_dir is not None else PLANS_DIR
    try:
        paths = sorted(base.glob("*.md"))
    except OSError:
        return rep
    ref = now or _now()
    for p in paths:
        try:
            if p.stat().st_size > 4_000_000:
                continue
            head = p.read_text(encoding="utf-8-sig",
                               errors="replace")[:_MAX_HEAD_BYTES]
        except OSError:
            continue
        fm = _front_matter(head)
        if not fm:
            continue
        rep.scanned += 1
        status = fm.get("status", "")
        if OPEN_MARKER not in status:
            continue
        if any(t in status.upper() for t in TERMINAL):
            continue                      # decided in place; not open
        age = -1
        try:
            when = datetime.fromisoformat(fm.get("date", "").strip())
            age = (ref - when.replace(tzinfo=timezone.utc)).days
        except (ValueError, TypeError):
            rep.undated += 1
        rep.entries.append(Stop1Entry(
            path=str(p), title=fm.get("title", p.stem), status=status.strip(),
            date=fm.get("date", ""), age_days=age,
            verdict=fm.get("verdict", "")))
    rep.entries.sort(key=lambda e: (-e.age_days, e.path))
    return rep


def resolve(path, status: str, reason: str, *, now=None) -> str:
    """Write the transition. The ONLY producer of a terminal STOP #1 status.

    Fail-CLOSED: refuses a non-terminal status, an empty reason, a file with no
    front matter, and a plan that is not actually open. Rewrites exactly one
    `status:` line and appends a resolution record; the body is untouched.
    """
    if status not in TERMINAL:
        raise ValueError(
            f"{status!r} is not terminal -- use one of {', '.join(TERMINAL)}")
    if not str(reason).strip():
        raise ValueError(
            "a transition requires a reason -- an unexplained resolution is "
            "how a queue becomes untrustworthy")
    p = Path(path)
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    fm = _front_matter(text)
    if not fm:
        raise ValueError(f"{p.name}: no front matter to transition")
    if OPEN_MARKER not in fm.get("status", ""):
        raise ValueError(
            f"{p.name}: status is {fm.get('status', '')!r}, not an open STOP #1")

    stamp = (now or _now()).strftime("%Y-%m-%d")
    old = fm["status"]
    lines, done = text.split("\n"), False
    for i, line in enumerate(lines[:60]):
        m = _FM_LINE.match(line)
        if m and m.group("key").lower() == "status" and not done:
            lines[i] = f"status: {status} ({stamp}) -- was: {old}"
            done = True
            break
    if not done:
        raise ValueError(f"{p.name}: status line not found in front matter")
    body = "\n".join(lines)
    body += (f"\n\n## Resolution ({stamp})\n\n**{status}.** {reason.strip()}\n")
    tmp = p.with_suffix(".md.tmp")
    tmp.write_text(body, encoding="utf-8")
    tmp.replace(p)
    return str(p)


def gate(plans_dir=None, threshold: int = 3, now=None) -> tuple:
    """PR-STOP1-PORTFOLIO-001. (ok, report, message).

    Advisory by design -- it reports, it does not block. A gate that refused to
    open a STOP #1 would stop the audit work that produces the estate's best
    evidence. What it refuses is the *silence*: opening the next one without
    seeing the queue.
    """
    rep = scan(plans_dir, now)
    if rep.open_count <= threshold:
        return True, rep, (f"{rep.open_count} open STOP #1 of {rep.scanned} "
                           f"plan(s) -- at or under the {threshold} threshold")
    oldest = rep.oldest
    tail = (f"; oldest {oldest.age_days}d ({Path(oldest.path).name})"
            if oldest else "")
    return False, rep, (
        f"{rep.open_count} open STOP #1 of {rep.scanned} plan(s), threshold "
        f"{threshold}{tail}. A queue with no transition producer only grows -- "
        "resolve or archive before opening another")


def render(rep: QueueReport, message: str = "") -> str:
    lines = [message] if message else []
    for e in rep.entries:
        age = f"{e.age_days}d" if not e.undated else "undated"
        lines.append(f"  [{age:>7}] {Path(e.path).name}")
        lines.append(f"            {e.title[:88]}")
    if rep.undated:
        lines.append(f"  ({rep.undated} entr(ies) carry no parsable date -- "
                     "reported as undated, never as age 0)")
    return "\n".join(lines) if lines else "no open STOP #1"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="STOP #1 queue (UCEIMR G1)")
    ap.add_argument("--plans-dir", default=None)
    ap.add_argument("--threshold", type=int, default=3)
    ap.add_argument("--resolve", default="", metavar="PLAN_PATH")
    ap.add_argument("--status", default=RESOLVED, choices=list(TERMINAL))
    ap.add_argument("--reason", default="")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 when the open queue exceeds the threshold")
    args = ap.parse_args(argv)

    if args.resolve:
        try:
            out = resolve(args.resolve, args.status, args.reason)
        except (ValueError, OSError) as e:
            print(f"REFUSED: {e}")
            return 1
        print(f"{args.status}: {out}")
        return 0

    ok, rep, msg = gate(args.plans_dir, args.threshold)
    print(render(rep, msg))
    return 0 if ok or not args.strict else 1


__all__ = [
    "Stop1Entry", "QueueReport", "OPEN_MARKER", "TERMINAL", "RESOLVED",
    "ARCHIVED", "SUPERSEDED", "scan", "resolve", "gate", "render",
]

if __name__ == "__main__":
    raise SystemExit(main())
