#!/usr/bin/env python
"""Produce FACTS.json from authoritative sources instead of from a human.

WHY THIS EXISTS. `modules/gsd_x/mission/structured_facts.py` says it in its own
docstring: declaring facts moved the vocabulary ceiling off a regex and onto
"whoever writes the file", and until a producer exists "a declared fact is
exactly as good as its declarer". No FACTS.json has ever existed on this host,
so the surface is consumable and unfed. This is the first producer.

WHAT IT REFUSES TO DO. It does not become a hand-maintained shadow database. A
fact it cannot derive is not invented and not defaulted -- it is reported
UNKNOWN, by name, with the reason.

THE FOUR STATES, AND WHY ABSENCE IS THREE DIFFERENT THINGS.

    OBSERVED   measured directly from an authoritative runtime source
    DERIVED    computed deterministically from authoritative evidence
    DECLARED   a human asserted it; nothing here can establish it
    UNKNOWN    the evidence to decide does not exist

The consumer's model is "a fact present in facts[] HOLDS". That makes absence
ambiguous in exactly the dangerous direction, because three different worlds
collapse into it: the fact was measured and does NOT hold · the fact could not
be measured · nobody asked. Only the first is safe to act on. So this producer
emits all three explicitly -- `facts[]`, `not_held[]`, `unknown[]` -- and a
consumer that derives obligations while `unknown[]` is non-empty is deriving
under acknowledged blindness and must say so.

FRESHNESS IS DEPENDENCY-DRIVEN, NOT A TTL. Each produced fact records the exact
sources it was computed from, with size + mtime + sha256. `--reconcile` re-reads
those and answers FRESH / STALE / UNKNOWN per fact. A change to an unrelated
file does not invalidate anything; a change to a source does. There is no clock
in the decision.

Usage:
  python tools/gsd_x_fact_producer.py --emit <mission-root>   write FACTS.json
  python tools/gsd_x_fact_producer.py --dry-run               print, write nothing
  python tools/gsd_x_fact_producer.py --reconcile <root>      freshness verdict
  (--state-dir / --memory-log override the sources, for tests)

Exit: 0 ok | 1 STALE or a refusal | 2 instrument failure
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "gsdx-facts/2"

OBSERVED = "OBSERVED"
DERIVED = "DERIVED"
DECLARED = "DECLARED"
UNKNOWN = "UNKNOWN"

DEFAULT_MEMORY_LOG = Path.home() / ".claude" / "logs" / "host-memory-floor.json"
DEFAULT_STATE_DIR = Path.home() / ".claude" / "state"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fingerprint(path: Path) -> dict:
    """Identity of a source, by CONTENT and not only by timestamp.

    mtime alone is a proxy: a file rewritten with identical bytes moves it, and
    a restored file can move it backwards. The hash is what decides; mtime is
    kept because it is what a human reads when asking 'when did this change'."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        return {"path": str(path), "readable": False, "why": str(exc)}
    st = path.stat()
    return {
        "path": str(path),
        "readable": True,
        "bytes": len(data),
        "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(timespec="seconds"),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


class Outcome:
    """One producer's answer. `holds` is tri-state: True / False / None(UNKNOWN)."""

    def __init__(self, name, holds, state, evidence, sources, why=""):
        self.name = name
        self.holds = holds
        self.state = state
        self.evidence = evidence
        self.sources = sources
        self.why = why

    def as_fact(self) -> dict:
        return {
            "name": self.name,
            "evidence": self.evidence,
            "state": self.state,
            "produced_at": _now(),
            "depends_on": self.sources,
        }

    def as_note(self) -> dict:
        return {
            "name": self.name,
            "state": self.state,
            "why": self.why or self.evidence,
            "depends_on": self.sources,
        }


# ── producer: bounded_local_capacity ─────────────────────────────────────────
def produce_bounded_local_capacity(memory_log: Path) -> Outcome:
    """OBSERVED from host-memory-floor.js's own readings.

    That hook is the estate's existing owner of host-memory visibility (N5 rule
    10) and it already writes every reading. Nothing new measures the host here;
    this reads what the owner recorded. The newest reading decides, because the
    host is documented to drift within minutes (N5 rule 11), so an average over
    the file would describe a host that no longer exists.
    """
    name = "bounded_local_capacity"
    fp = _fingerprint(memory_log)
    if not fp.get("readable"):
        return Outcome(name, None, UNKNOWN,
                       f"host memory log unreadable: {fp.get('why')}", [fp],
                       why="the authoritative source could not be read")
    try:
        doc = json.loads(memory_log.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return Outcome(name, None, UNKNOWN, f"host memory log unparseable: {exc}", [fp],
                       why="the authoritative source is not valid JSON")

    recent = doc.get("recent")
    if not isinstance(recent, list) or not recent:
        return Outcome(name, None, UNKNOWN, "host memory log carries no readings", [fp],
                       why="the source exists but has recorded nothing")

    last = recent[-1]
    level = last.get("level")
    free = last.get("freeMB")
    total = last.get("totalMB")
    iso = last.get("iso")
    if level not in ("OK", "WARN", "CRITICAL") or not isinstance(free, (int, float)):
        return Outcome(name, None, UNKNOWN, f"unrecognised reading shape: {last!r}", [fp],
                       why="the source's newest entry does not carry a level and a free figure")

    holds = level in ("WARN", "CRITICAL")
    ev = (f"host-memory-floor recorded {free} MB free of {total} MB at {iso} -> {level} "
          f"(readings={doc.get('readings')}, byLevel={doc.get('byLevel')})")
    return Outcome(name, holds, OBSERVED, ev, [fp],
                   why=("capacity is constrained" if holds
                        else f"capacity is NOT constrained at this reading ({level})"))


# ── producer: unattended_operation ───────────────────────────────────────────
def produce_unattended_operation(state_dir: Path, mission_root: Path) -> Outcome:
    """DERIVED from the long-run markers this estate already writes.

    A marker is the record that a run is in flight without a human at the pane,
    which is precisely what the fact asserts. Scoped to THIS mission root: an
    unattended run in another project says nothing about this one, and a fact
    that answered 'yes' because some other pane is running would be a
    cross-mission leak wearing the costume of a measurement.
    """
    name = "unattended_operation"
    if not state_dir.is_dir():
        fp = {"path": str(state_dir), "readable": False, "why": "not a directory"}
        return Outcome(name, None, UNKNOWN, f"state dir absent: {state_dir}", [fp],
                       why="the authoritative source directory does not exist")

    try:
        markers = sorted(state_dir.glob("gsd-autorun-*.json"))
    except OSError as exc:
        fp = {"path": str(state_dir), "readable": False, "why": str(exc)}
        return Outcome(name, None, UNKNOWN, f"state dir unreadable: {exc}", [fp],
                       why="the authoritative source directory could not be listed")

    try:
        want = mission_root.resolve()
    except OSError:
        want = mission_root

    sources, live, unparseable = [], [], 0
    for m in markers:
        try:
            doc = json.loads(m.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            unparseable += 1
            continue
        cwd = doc.get("cwd")
        if not isinstance(cwd, str):
            continue
        try:
            same = Path(cwd).resolve() == want
        except OSError:
            same = False
        if not same:
            continue
        sources.append(_fingerprint(m))
        cycles = doc.get("cycles")
        max_cycles = doc.get("max_cycles")
        spent = (isinstance(cycles, int) and isinstance(max_cycles, int)
                 and cycles >= max_cycles)
        if not spent:
            live.append({"session": doc.get("session_id"), "command": doc.get("resume_command"),
                         "cycles": cycles, "max_cycles": max_cycles})

    # An unparseable marker is not evidence of absence. If NOTHING matched and
    # something could not be read, the honest answer is that we do not know.
    if not sources and unparseable:
        return Outcome(name, None, UNKNOWN,
                       f"{unparseable} marker(s) unreadable and none matched this root",
                       [{"path": str(state_dir), "readable": True, "unparseable": unparseable}],
                       why="markers exist that could not be parsed, so absence is not established")

    if live:
        ev = (f"{len(live)} armed long-run marker(s) for this root in {state_dir}: "
              + "; ".join(f"{l['command']} cycle {l['cycles']}/{l['max_cycles']}" for l in live))
        return Outcome(name, True, DERIVED, ev, sources, why="a run is in flight for this root")

    ev = (f"no armed long-run marker for this root among {len(markers)} marker(s) in {state_dir}"
          + (f"; {len(sources)} matched this root but are budget-spent" if sources else ""))
    return Outcome(name, False, DERIVED, ev, sources or [_fingerprint(state_dir / ".")],
                   why="no run is in flight for this root")


PRODUCERS = ("bounded_local_capacity", "unattended_operation")


def produce_all(mission_root: Path, memory_log: Path, state_dir: Path) -> list[Outcome]:
    out = []
    for fn in (lambda: produce_bounded_local_capacity(memory_log),
               lambda: produce_unattended_operation(state_dir, mission_root)):
        try:
            out.append(fn())
        except Exception as exc:  # one producer must not silence the others
            out.append(Outcome("<producer>", None, UNKNOWN, f"producer raised: {exc}", [],
                               why="instrument failure inside a producer"))
    return out


def build_document(outcomes: list[Outcome], mission_root: Path) -> dict:
    return {
        "schema": SCHEMA,
        "provenance": (
            "Produced mechanically by tools/gsd_x_fact_producer.py from authoritative "
            "sources on this host. Not hand-authored. Each fact names the exact sources "
            "it was computed from; re-check with --reconcile."
        ),
        "generated_at": _now(),
        "mission_root": str(mission_root),
        "facts": [o.as_fact() for o in outcomes if o.holds is True],
        "not_held": [o.as_note() for o in outcomes if o.holds is False],
        "unknown": [o.as_note() for o in outcomes if o.holds is None],
    }


def reconcile(doc_path: Path) -> tuple[str, list[dict]]:
    """Re-read each fact's declared sources. FRESH / STALE / UNKNOWN per fact.

    STALE means a source this fact was computed from has changed content since.
    UNKNOWN means a source can no longer be read at all -- which is NOT the same
    as the fact having changed, and must not be reported as if it were."""
    try:
        doc = json.loads(doc_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return "INSTRUMENT", [{"why": f"{doc_path}: {exc}"}]

    rows = []
    for entry in list(doc.get("facts", [])) + list(doc.get("not_held", [])) + list(doc.get("unknown", [])):
        verdict = "FRESH"
        moved = []
        for dep in entry.get("depends_on", []) or []:
            path = Path(dep.get("path", ""))
            now = _fingerprint(path)
            if not now.get("readable") or not dep.get("readable"):
                verdict = "UNKNOWN"
                moved.append({"path": str(path), "why": "source no longer readable"})
                continue
            if now.get("sha256") != dep.get("sha256"):
                if verdict != "UNKNOWN":
                    verdict = "STALE"
                moved.append({"path": str(path), "was": dep.get("sha256", "")[:12],
                              "now": now.get("sha256", "")[:12]})
        rows.append({"name": entry.get("name"), "verdict": verdict, "moved": moved})

    if not rows:
        return "UNKNOWN", rows
    if any(r["verdict"] == "UNKNOWN" for r in rows):
        return "UNKNOWN", rows
    if any(r["verdict"] == "STALE" for r in rows):
        return "STALE", rows
    return "FRESH", rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--emit", metavar="ROOT")
    ap.add_argument("--dry-run", metavar="ROOT")
    ap.add_argument("--reconcile", metavar="ROOT")
    ap.add_argument("--memory-log", default=str(DEFAULT_MEMORY_LOG))
    ap.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.reconcile:
        verdict, rows = reconcile(Path(args.reconcile) / "FACTS.json")
        if args.json:
            print(json.dumps({"verdict": verdict, "facts": rows}, indent=2))
        else:
            for r in rows:
                extra = ("  " + json.dumps(r["moved"])) if r["moved"] else ""
                print(f"{r['verdict']:<8} {r.get('name')}{extra}")
            print(f"RECONCILE={verdict}")
        return {"FRESH": 0, "STALE": 1, "UNKNOWN": 1, "INSTRUMENT": 2}[verdict]

    root = args.emit or args.dry_run
    if not root:
        ap.error("one of --emit / --dry-run / --reconcile is required")
    root_path = Path(root)
    if not root_path.is_dir():
        print(f"INSTRUMENT: mission root is not a directory: {root_path}", file=sys.stderr)
        return 2

    outcomes = produce_all(root_path, Path(args.memory_log), Path(args.state_dir))
    doc = build_document(outcomes, root_path)

    if args.emit:
        target = root_path / "FACTS.json"
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, target)
        print(f"wrote {target}")

    if args.json:
        print(json.dumps(doc, indent=2))
    else:
        for f in doc["facts"]:
            print(f"HOLDS    {f['name']:<24} [{f['state']}] {f['evidence'][:110]}")
        for n in doc["not_held"]:
            print(f"NOT-HELD {n['name']:<24} [{n['state']}] {n['why'][:110]}")
        for u in doc["unknown"]:
            print(f"UNKNOWN  {u['name']:<24} [{u['state']}] {u['why'][:110]}")
        print(f"FACTS={len(doc['facts'])} NOT_HELD={len(doc['not_held'])} "
              f"UNKNOWN={len(doc['unknown'])}")
        if doc["unknown"]:
            print("A derivation run against this document is deriving under acknowledged "
                  "blindness: UNKNOWN is not false.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
