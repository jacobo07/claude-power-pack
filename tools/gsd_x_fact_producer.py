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
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# The freshness primitive and the fact-state vocabulary have ONE owner, in the
# module that owns the document. This bootstrap is what makes that import
# reachable from a tool: without it `modules.` is not on the path, the import
# raises, and this file's 15 gates become a crash rather than a red -- an
# instrument failure wearing a regression's clothes.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.gsd_x.mission.obligation import (  # noqa: E402
    DECLARED, DERIVED, OBSERVED, UNKNOWN)
from modules.gsd_x.mission.structured_facts import (  # noqa: E402
    SCHEMA_V2, fingerprint, reconcile_document)

SCHEMA = SCHEMA_V2

# Re-exported under the names this file's own gate already calls by name:
# tools/test_gsd_x_fact_producer.py reads FP.SCHEMA, FP.UNKNOWN and
# FP.reconcile. `fingerprint` is an EMIT-time dependency here, not only a
# reconcile-time one -- it stamps every produced entry's `depends_on`.
_fingerprint = fingerprint
reconcile = reconcile_document

DEFAULT_MEMORY_LOG = Path.home() / ".claude" / "logs" / "host-memory-floor.json"
DEFAULT_STATE_DIR = Path.home() / ".claude" / "state"
# CEPS is this estate's own recorded failure history. It is the authoritative
# source for "has this environment MEASURED a failure mode", which is the
# question `op_failure_consequence` gates on.
DEFAULT_CEPS_LOG = Path(__file__).resolve().parents[1] / "vault" / "ceps" / "events.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


# ── producer: measured_failure_mode ──────────────────────────────────────────
def produce_measured_failure_mode(ceps_log: Path) -> Outcome:
    """OBSERVED from CEPS, this estate's own recorded failure history.

    THE FIRST GATING FACT ANY PRODUCER ON THIS HOST EMITS. Until now
    `V-FACTSV2-PRODUCER-REACH` measured, as a live fact, that no producible name
    was gating -- so the blindness and coverage machinery was correct and
    unreachable from the world, provable only against a constructed document.
    This is what makes it reachable, and it is what makes an UNPRODUCED verdict
    CLEARABLE rather than a deadlock.

    WHAT THE FACT MEANS, AND WHY A COUNT IS THE RIGHT EVIDENCE. The operator's
    own authority line is "the environment's own measurements", and the pattern
    it was written against is a failure with a MEASURED FREQUENCY -- not a
    hypothetical, and not a single incident. A `pattern_signature` seen twice or
    more is exactly that: the same failure, recorded independently, with a count.

    DELIBERATELY NOT MISSION-SCOPED, unlike `unattended_operation`. That fact
    asserts something about THIS root, so a marker from another pane would have
    been a cross-mission leak. This one asserts something about the ENVIRONMENT
    the mission runs in, and the environment is shared. The evidence names the
    window and the totals so a reader can disagree with that reading rather than
    having to infer it.

    An unparseable line is not evidence of absence: if nothing parsed, or if
    nothing recurred while some lines could not be read, the answer is UNKNOWN.
    """
    name = "measured_failure_mode"
    fp = _fingerprint(ceps_log)
    if not fp.get("readable"):
        return Outcome(name, None, UNKNOWN,
                       f"CEPS event log unreadable: {fp.get('why')}", [fp],
                       why="the authoritative source could not be read")

    counts: dict[str, int] = {}
    labels: dict[str, str] = {}
    parsed = unparseable = 0
    try:
        text = ceps_log.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        return Outcome(name, None, UNKNOWN, f"CEPS event log unreadable: {exc}", [fp],
                       why="the authoritative source could not be decoded")
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            unparseable += 1
            continue
        if not isinstance(row, dict):
            unparseable += 1
            continue
        sig = row.get("pattern_signature")
        if not isinstance(sig, str) or not sig:
            continue
        parsed += 1
        counts[sig] = counts.get(sig, 0) + 1
        labels.setdefault(sig, f"{row.get('category')}/{row.get('subsystem')}")

    if not parsed:
        return Outcome(name, None, UNKNOWN,
                       f"CEPS log carries no parseable event ({unparseable} bad line(s))",
                       [fp], why="the source exists but recorded nothing this can read")

    recurring = sorted(((n, s) for s, n in counts.items() if n >= 2), reverse=True)
    if not recurring:
        if unparseable:
            return Outcome(name, None, UNKNOWN,
                           f"no signature recurs among {parsed} event(s), but "
                           f"{unparseable} line(s) could not be read", [fp],
                           why="absence of a recurring failure is not established "
                               "while some events are unreadable")
        return Outcome(name, False, OBSERVED,
                       f"{parsed} CEPS event(s), no pattern_signature seen more than once",
                       [fp], why="no failure mode in this environment has a measured "
                                "frequency above one")

    top = "; ".join(f"{labels.get(s, s)} x{n}" for n, s in recurring[:3])
    ev = (f"{len(recurring)} recurring failure signature(s) across {parsed} CEPS "
          f"event(s) estate-wide; most frequent: {top}")
    return Outcome(name, True, OBSERVED, ev, [fp],
                   why="this environment has measured at least one failure mode "
                       "with a frequency above one")


PRODUCERS = ("bounded_local_capacity", "unattended_operation",
             "measured_failure_mode")


def produce_all(mission_root: Path, memory_log: Path, state_dir: Path,
                ceps_log: Path = DEFAULT_CEPS_LOG) -> list[Outcome]:
    out = []
    for fn in (lambda: produce_bounded_local_capacity(memory_log),
               lambda: produce_unattended_operation(state_dir, mission_root),
               lambda: produce_measured_failure_mode(ceps_log)):
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--emit", metavar="ROOT")
    ap.add_argument("--dry-run", metavar="ROOT")
    ap.add_argument("--reconcile", metavar="ROOT")
    ap.add_argument("--memory-log", default=str(DEFAULT_MEMORY_LOG))
    ap.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    ap.add_argument("--ceps-log", default=str(DEFAULT_CEPS_LOG))
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

    outcomes = produce_all(root_path, Path(args.memory_log), Path(args.state_dir),
                           Path(args.ceps_log))
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
