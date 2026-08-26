#!/usr/bin/env python3
"""V-DEC-* -- a settled decision stops being a decision.

The decision registry was write-only for decision-making: review_decision()
appended and never read back, and Registry.next_id() derives a fresh id
from the line count, so re-submitting a byte-identical decision produced a
NEW record rather than a match. The system could not notice it had already
answered.

The gates below assert the property that matters and, just as hard, the
property that must NOT hold: a decision whose EVIDENCE moved is a different
decision wearing the same words, and must be re-reasoned.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

from modules.decision_review.decision_kernel import review_decision  # noqa: E402
from modules.decision_review.decision_record import (  # noqa: E402
    DecisionObject, Evidence, EvidenceType, Registry)
from modules.decision_review import recurrence  # noqa: E402

EXPECTED_GATES = 8
_passes = 0
_fails = 0


def _ok(g: str, e: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {g}: {e}")


def _fail(g: str, d: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {g}: {d}")


def _obj(statement="Adopt X as the cache module for the deploy pipeline",
         chosen="X", claim="X is faster", ident="DEC-T1"):
    """An IN-SCOPE decision.

    The first fixture was classified L0 and wrote no record, so two gates
    passed against an empty registry -- a green suite proving nothing.
    Stage 1 admits a decision that crosses a consequence threshold, so this
    statement deliberately touches several blast surfaces (module, deploy,
    pipeline, data store).
    """
    return DecisionObject(
        id=ident,
        statement=statement,
        problem="the deploy pipeline needs a data store for its cache",
        options=["X", "Z"],
        chosen=chosen,
        rationale="because the measured numbers favour it",
        evidence=[Evidence(type=EvidenceType.OBSERVED_EVIDENCE, claim=claim,
                           source="bench.json", observable="p95_ms")],
        predicted_consequences=["latency drops"],
        is_build_decision=True,
    )


def main() -> int:
    print("V-DEC -- decision recurrence")

    # Fingerprint covers inputs, and only inputs.
    a, b = _obj(), _obj(ident="DEC-T2")
    if recurrence.fingerprint(a) == recurrence.fingerprint(b):
        _ok("V-DEC-FINGERPRINT-IGNORES-ID",
            "same inputs, different id -> same fingerprint")
    else:
        _fail("V-DEC-FINGERPRINT-IGNORES-ID", "id leaked into the digest")

    moved = _obj(claim="X is SLOWER after the regression")
    if recurrence.fingerprint(a) != recurrence.fingerprint(moved):
        _ok("V-DEC-FINGERPRINT-TRACKS-EVIDENCE",
            "changed evidence claim -> different fingerprint")
    else:
        _fail("V-DEC-FINGERPRINT-TRACKS-EVIDENCE",
              "evidence change did not move the digest")

    other = _obj(chosen="Z")
    if recurrence.fingerprint(a) != recurrence.fingerprint(other):
        _ok("V-DEC-FINGERPRINT-TRACKS-CHOICE",
            "a different chosen option -> different fingerprint")
    else:
        _fail("V-DEC-FINGERPRINT-TRACKS-CHOICE", "choice not covered")

    tmp = Path(tempfile.mkdtemp(prefix="dec_"))
    try:
        reg = Registry(tmp / "records.jsonl")

        # Empty registry: no precedent, and certainly no crash.
        if recurrence.find_precedent(a, reg) is None:
            _ok("V-DEC-EMPTY-REGISTRY-NO-PRECEDENT",
                "nothing recorded -> None")
        else:
            _fail("V-DEC-EMPTY-REGISTRY-NO-PRECEDENT", "invented a precedent")

        first = review_decision(_obj(), registry=reg, ts="2026-08-26T10:00:00Z")
        rows = reg.load()
        if rows and rows[-1].get("fingerprint"):
            _ok("V-DEC-RECORD-CARRIES-FINGERPRINT",
                f"written record stamps {rows[-1]['fingerprint']}")
        else:
            _fail("V-DEC-RECORD-CARRIES-FINGERPRINT",
                  "no fingerprint on the record; precedent can never match")

        # THE CAPABILITY. The identical decision, resubmitted, is answered
        # from the prior verdict instead of re-reasoned.
        again = review_decision(_obj(ident="DEC-T9"), registry=reg,
                                ts="2026-08-26T11:00:00Z")
        reused = "DEC-PRECEDENT-REUSED" in (again.guards_fired or [])
        if reused and again.verdict == first.verdict:
            _ok("V-DEC-REPEAT-IS-REUSED",
                f"identical decision -> {again.verdict.value} from precedent, "
                "nine stages not re-run")
        else:
            _fail("V-DEC-REPEAT-IS-REUSED",
                  f"guards={again.guards_fired} verdict={again.verdict} "
                  f"first={first.verdict}")

        # No new record: reuse must not grow the registry, or the cache
        # inflates the very history it reads.
        # Guarded against passing on an empty registry: with zero records
        # "unchanged" is trivially true and the gate would assert nothing.
        if not rows:
            _fail("V-DEC-REUSE-WRITES-NOTHING",
                  "registry is empty, so this gate cannot distinguish reuse "
                  "from a decision that was never recorded")
        elif len(reg.load()) == len(rows):
            _ok("V-DEC-REUSE-WRITES-NOTHING",
                f"registry stayed at {len(rows)} record(s) across the reuse")
        else:
            _fail("V-DEC-REUSE-WRITES-NOTHING",
                  f"{len(rows)} -> {len(reg.load())}")

        # BOOKEND, and the one that protects correctness: evidence moved,
        # so this is a DIFFERENT decision and must be reasoned afresh.
        changed = review_decision(_obj(claim="X is SLOWER after the regression",
                                       ident="DEC-T10"),
                                  registry=reg, ts="2026-08-26T12:00:00Z")
        if "DEC-PRECEDENT-REUSED" not in (changed.guards_fired or []):
            _ok("V-DEC-BOOKEND-MOVED-EVIDENCE-REASONS",
                "changed evidence is re-reasoned, not served from cache")
        else:
            _fail("V-DEC-BOOKEND-MOVED-EVIDENCE-REASONS",
                  "served a stale verdict for changed evidence")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = _passes + _fails
    print(f"DECISION_RECURRENCE_PASS={_passes}/{total}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if total != EXPECTED_GATES:
        print(f"FAIL: {total} gates executed, {EXPECTED_GATES} declared")
        return 1
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
