#!/usr/bin/env python
"""Drive every branch of the fact producer, including the three kinds of absence.

WHY THESE CASES. The producer's whole reason to exist is that a consumer reading
`facts[]` treats absence as "does not hold", and three different worlds collapse
into that absence: measured-and-false, could-not-measure, and never-asked. A
suite that only checks the happy path would pass against a producer that answers
UNKNOWN by omitting the fact -- which is the exact defect.

So every producer is driven at BOTH poles, and each is additionally driven into
UNKNOWN with the source removed and with the source corrupted. A pole that can
only ever come back one way is not evidence.

Fixtures are synthetic and per-PID: this host runs dozens of concurrent sessions,
and a shared fixture path produces an unattributable failure in exactly one.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gsd_x_fact_producer as FP  # noqa: E402

_pass = 0
_fail = 0


def _ok(gate, evidence):
    global _pass
    _pass += 1
    print(f"  PASS {gate}: {evidence}")


def _no(gate, why):
    global _fail
    _fail += 1
    print(f"  FAIL {gate}: {why}")


def _memlog(path: Path, level: str, free: int = 900):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "readings": 3,
        "byLevel": {level: 3},
        "lastIso": "2026-09-23T00:00:00.000Z",
        "recent": [{"iso": "2026-09-23T00:00:00.000Z", "sid": "x",
                    "freeMB": free, "totalMB": 32061, "pct": 2.8, "level": level}],
    }), encoding="utf-8")


def _marker(state_dir: Path, name: str, cwd: Path, cycles=1, max_cycles=24):
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / f"gsd-autorun-{name}.json").write_text(json.dumps({
        "session_id": name, "resume_command": "/gsd-autonomous", "cwd": str(cwd),
        "cycles": cycles, "max_cycles": max_cycles, "schema_version": 2,
    }), encoding="utf-8")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix=f"gsdxfp-{os.getpid()}-"))
    try:
        root = tmp / "mission"
        root.mkdir()
        other = tmp / "other-mission"
        other.mkdir()
        log = tmp / "mem.json"
        state = tmp / "state"
        state.mkdir()

        # ── bounded_local_capacity ───────────────────────────────────────────
        _memlog(log, "CRITICAL", free=400)
        o = FP.produce_bounded_local_capacity(log)
        if o.holds is True and o.state == FP.OBSERVED:
            _ok("V-GSDXFP-CAPACITY-HOLDS", f"CRITICAL reading -> holds, {o.state}")
        else:
            _no("V-GSDXFP-CAPACITY-HOLDS", f"got holds={o.holds} state={o.state}")

        _memlog(log, "OK", free=20000)
        o = FP.produce_bounded_local_capacity(log)
        if o.holds is False and o.state == FP.OBSERVED:
            _ok("V-GSDXFP-CAPACITY-NOT-HELD",
                "OK reading -> measured FALSE, not omitted and not UNKNOWN")
        else:
            _no("V-GSDXFP-CAPACITY-NOT-HELD", f"got holds={o.holds} state={o.state}")

        o = FP.produce_bounded_local_capacity(tmp / "no-such-log.json")
        if o.holds is None and o.state == FP.UNKNOWN:
            _ok("V-GSDXFP-CAPACITY-UNKNOWN-ABSENT",
                "missing source -> UNKNOWN, never False")
        else:
            _no("V-GSDXFP-CAPACITY-UNKNOWN-ABSENT",
                f"absence collapsed to holds={o.holds}")

        bad = tmp / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        o = FP.produce_bounded_local_capacity(bad)
        if o.holds is None and o.state == FP.UNKNOWN:
            _ok("V-GSDXFP-CAPACITY-UNKNOWN-CORRUPT", "unparseable source -> UNKNOWN")
        else:
            _no("V-GSDXFP-CAPACITY-UNKNOWN-CORRUPT", f"got holds={o.holds}")

        # ── unattended_operation ─────────────────────────────────────────────
        _marker(state, "aaa", root, cycles=1, max_cycles=24)
        o = FP.produce_unattended_operation(state, root)
        if o.holds is True and o.state == FP.DERIVED:
            _ok("V-GSDXFP-UNATTENDED-HOLDS", "armed marker for this root -> holds")
        else:
            _no("V-GSDXFP-UNATTENDED-HOLDS", f"got holds={o.holds} ({o.evidence})")

        # The one that matters: another project's run must not answer for ours.
        shutil.rmtree(state)
        _marker(state, "bbb", other, cycles=1, max_cycles=24)
        o = FP.produce_unattended_operation(state, root)
        if o.holds is False:
            _ok("V-GSDXFP-UNATTENDED-SCOPED",
                "a marker for ANOTHER root does not make this root unattended")
        else:
            _no("V-GSDXFP-UNATTENDED-SCOPED",
                f"cross-mission leak: holds={o.holds} ({o.evidence})")

        shutil.rmtree(state)
        _marker(state, "ccc", root, cycles=24, max_cycles=24)
        o = FP.produce_unattended_operation(state, root)
        if o.holds is False:
            _ok("V-GSDXFP-UNATTENDED-BUDGET-SPENT", "a spent marker is not a live run")
        else:
            _no("V-GSDXFP-UNATTENDED-BUDGET-SPENT", f"got holds={o.holds}")

        # An unreadable marker is not evidence of absence.
        shutil.rmtree(state)
        state.mkdir()
        (state / "gsd-autorun-ddd.json").write_text("{broken", encoding="utf-8")
        o = FP.produce_unattended_operation(state, root)
        if o.holds is None and o.state == FP.UNKNOWN:
            _ok("V-GSDXFP-UNATTENDED-UNKNOWN-UNPARSEABLE",
                "an unparseable marker with no match -> UNKNOWN, not False")
        else:
            _no("V-GSDXFP-UNATTENDED-UNKNOWN-UNPARSEABLE", f"got holds={o.holds}")

        o = FP.produce_unattended_operation(tmp / "no-such-state", root)
        if o.holds is None and o.state == FP.UNKNOWN:
            _ok("V-GSDXFP-UNATTENDED-UNKNOWN-ABSENT", "missing state dir -> UNKNOWN")
        else:
            _no("V-GSDXFP-UNATTENDED-UNKNOWN-ABSENT", f"got holds={o.holds}")

        # ── document shape: the three buckets are all present ────────────────
        shutil.rmtree(state)
        _marker(state, "eee", root)
        _memlog(log, "OK", free=20000)
        doc = FP.build_document(
            FP.produce_all(root, log, state), root)
        names = {f["name"] for f in doc["facts"]}
        not_held = {n["name"] for n in doc["not_held"]}
        if (doc["schema"] == FP.SCHEMA
                and "unattended_operation" in names
                and "bounded_local_capacity" in not_held):
            _ok("V-GSDXFP-DOC-THREE-BUCKETS",
                "held / not_held / unknown are separate keys, not one absence")
        else:
            _no("V-GSDXFP-DOC-THREE-BUCKETS", json.dumps(doc)[:200])

        # ── freshness: FRESH / STALE / UNKNOWN, dependency-driven ────────────
        rc = FP.main(["--emit", str(root), "--memory-log", str(log),
                      "--state-dir", str(state)])
        if rc == 0 and (root / "FACTS.json").is_file():
            _ok("V-GSDXFP-EMIT", "FACTS.json written atomically")
        else:
            _no("V-GSDXFP-EMIT", f"emit rc={rc}")

        verdict, rows = FP.reconcile(root / "FACTS.json")
        if verdict == "FRESH":
            _ok("V-GSDXFP-FRESH", "unchanged sources -> FRESH")
        else:
            _no("V-GSDXFP-FRESH", f"got {verdict}: {rows}")

        # Touching an UNRELATED file must not invalidate anything.
        (tmp / "unrelated.txt").write_text("noise", encoding="utf-8")
        verdict, _ = FP.reconcile(root / "FACTS.json")
        if verdict == "FRESH":
            _ok("V-GSDXFP-UNRELATED-CHANGE-IS-NOT-DRIFT",
                "an unrelated file changing leaves the facts FRESH")
        else:
            _no("V-GSDXFP-UNRELATED-CHANGE-IS-NOT-DRIFT", f"got {verdict}")

        # Changing a SOURCE must.
        _memlog(log, "CRITICAL", free=100)
        verdict, rows = FP.reconcile(root / "FACTS.json")
        moved = [r for r in rows if r["moved"]]
        if verdict == "STALE" and moved:
            _ok("V-GSDXFP-STALE", f"source content changed -> STALE, naming {moved[0]['name']}")
        else:
            _no("V-GSDXFP-STALE", f"got {verdict}: {rows}")

        # Removing a source is UNKNOWN, not STALE: we cannot say it changed.
        log.unlink()
        verdict, _ = FP.reconcile(root / "FACTS.json")
        if verdict == "UNKNOWN":
            _ok("V-GSDXFP-UNREADABLE-IS-NOT-STALE",
                "a source that vanished -> UNKNOWN, distinct from STALE")
        else:
            _no("V-GSDXFP-UNREADABLE-IS-NOT-STALE", f"got {verdict}")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = _pass + _fail
    print(f"GSDX_FACTPROD_PASS={_pass}/{total}  threshold={total}/{total}")
    return 0 if _fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
