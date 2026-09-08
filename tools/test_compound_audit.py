#!/usr/bin/env python3
"""Gates for compound_audit.py.

The thing being repaired was a health check that could not fail, so a test suite that
only drove green branches would reproduce the defect exactly. Every case here that
expects True has a twin that expects False on the same clause.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import compound_audit as ca  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL {gate}: {diagnostic}")


def _check(gate: str, got: tuple[bool, str], want_ok: bool, want_substr: str = "") -> None:
    ok, msg = got
    if ok != want_ok:
        _fail(gate, f"expected ok={want_ok}, got ok={ok} ({msg})")
        return
    if want_substr and want_substr.lower() not in msg.lower():
        _fail(gate, f"ok={ok} as expected but message lacks {want_substr!r}: {msg}")
        return
    _ok(gate, msg[:150])


def _state(projects: dict, last_run_global=None) -> dict:
    return {"schema_version": 1, "threshold": 5,
            "last_run_global": last_run_global, "projects": projects}


def _iso(days_ago: int) -> str:
    return (dt.datetime.now(dt.timezone.utc)
            - dt.timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")


def main() -> int:
    # --- consolidation-advances, both directions -----------------------------------
    _check("V-COMPOUND-STUCK-PROJECT-FAILS",
           ca.assert_consolidation_advances(
               _state({"proj-a": {"last_run_iso": _iso(1), "directive_count": ca.DEGRADE_AT}})),
           False, "past the")

    _check("V-COMPOUND-BELOW-THRESHOLD-PASSES",
           ca.assert_consolidation_advances(
               _state({"proj-a": {"last_run_iso": _iso(1),
                                  "directive_count": ca.DEGRADE_AT - 1}})),
           True, "no project past")

    # The distinction the pending marker got wrong, in both directions. Without both,
    # the cause sentence could be a constant string and stay green.
    _check("V-COMPOUND-NEVER-RAN-SAYS-NOBODY-RAN-IT",
           ca.assert_consolidation_advances(
               _state({"p": {"directive_count": 49}}, last_run_global=None)),
           False, "nobody ran it")

    _check("V-COMPOUND-RAN-ELSEWHERE-SAYS-STEP-7",
           ca.assert_consolidation_advances(
               _state({"p": {"directive_count": 49}}, last_run_global="2026-09-01T00:00:00Z")),
           False, "Step 7 is the right place")

    _check("V-COMPOUND-NO-PROJECTS-PASSES",
           ca.assert_consolidation_advances(_state({})), True, "no project past")

    _check("V-COMPOUND-UNREADABLE-STATE-IS-NOT-A-PASS",
           ca.assert_consolidation_advances({"schema_version": 1, "projects": "not-a-dict"}),
           False, "projects key")

    # --- marker-staleness, which previously could not fail at all -------------------
    _check("V-COMPOUND-STALE-CURSOR-FAILS",
           ca.assert_no_stale_markers(_state({"old": {"last_run_iso": _iso(400)}})),
           False, "older than")

    _check("V-COMPOUND-FRESH-CURSOR-PASSES",
           ca.assert_no_stale_markers(_state({"new": {"last_run_iso": _iso(2)}})),
           True, "within sliding window")

    # --- state-shape keeps its own job, and only its own -----------------------------
    _check("V-COMPOUND-SHAPE-IGNORES-LAST-RUN-GLOBAL",
           ca.assert_state_valid(_state({"p": {"last_run_iso": _iso(1)}}, last_run_global=None)),
           True, "last_run_global=never")

    _check("V-COMPOUND-SHAPE-REJECTS-BAD-SCHEMA",
           ca.assert_state_valid({"schema_version": 2, "threshold": 5, "projects": {}}),
           False, "schema_version")

    # --- POSITIVE CONTROL ------------------------------------------------------------
    # A detector that stopped detecting reports the same clean green as one that still
    # works. This drives the new check against the REAL state file on this machine and
    # requires the verdict to match what that file actually contains -- so the suite
    # cannot go green on a check that has been quietly disconnected from disk.
    real = ca._load_state()
    if real is None:
        _ok("V-COMPOUND-POSITIVE-CONTROL", "no state file on this host; nothing to control against")
    else:
        worst = max((int((i or {}).get("directive_count") or 0)
                     for i in real.get("projects", {}).values() if isinstance(i, dict)),
                    default=0)
        ok, msg = ca.assert_consolidation_advances()
        expected_ok = worst < ca.DEGRADE_AT
        if ok == expected_ok:
            _ok("V-COMPOUND-POSITIVE-CONTROL",
                f"real state: worst directive_count={worst}, threshold={ca.DEGRADE_AT}, "
                f"verdict ok={ok} -- consistent")
        else:
            _fail("V-COMPOUND-POSITIVE-CONTROL",
                  f"real state has worst directive_count={worst} against threshold "
                  f"{ca.DEGRADE_AT}, so ok should be {expected_ok}, but the check said {ok}: {msg}")

    total = _passes + _fails
    print(f"COMPOUND_AUDIT_TEST_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
