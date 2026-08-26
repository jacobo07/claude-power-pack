#!/usr/bin/env python3
"""V-VERIF-* -- the input two sealed Hard Rules were starving for.

HR-CASCADE-001 (refuse a deploy when tests have not passed) and
HR-CASCADE-003 (pause a commit with no prior verification) are both
implemented: `_detect_deploy` and `_detect_commit` read `ctx["verified"]`.
A grep across modules/, tools/ and vault/ found ZERO producers of that
signal, so it defaulted to True at every call site and neither rule could
fire. Both read as enforcement and were inert.

The gates below assert the producer, the three-valued contract, and that
the detectors actually fire once fed -- which is the part that proves the
rules were starving rather than merely quiet.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

from modules.cascade_prevention import engine, verification_state as vs  # noqa: E402

EXPECTED_GATES = 7
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


def main() -> int:
    print("V-VERIF -- verification provenance for HR-CASCADE-001/003")

    tmp = Path(tempfile.mkdtemp(prefix="verif_"))
    saved = vs.STATE_PATH
    vs.STATE_PATH = tmp / "verification.json"
    try:
        # No record is NOT a failure. This is the whole safety property: a
        # blocking rule must never fire on the strength of its own ignorance.
        if vs.was_verified() is None:
            _ok("V-VERIF-UNKNOWN-IS-NOT-FALSE",
                "no record -> None, never False")
        else:
            _fail("V-VERIF-UNKNOWN-IS-NOT-FALSE",
                  f"empty state returned {vs.was_verified()!r}")

        vs.record_verification("suite", True, "51/51")
        if vs.was_verified() is True and vs.STATE_PATH.exists():
            _ok("V-VERIF-RECORDS-PASS", "a green run is recorded and read back")
        else:
            _fail("V-VERIF-RECORDS-PASS", f"got {vs.was_verified()!r}")

        vs.record_verification("suite", False, "3 rows failed")
        if vs.was_verified() is False:
            _ok("V-VERIF-RECORDS-FAIL", "a red run reads back as False")
        else:
            _fail("V-VERIF-RECORDS-FAIL", f"got {vs.was_verified()!r}")

        # An expired pass stops vouching, and must degrade to None rather
        # than to False -- reporting an aged-out pass as a failure would
        # invent a result nobody observed.
        vs.record_verification("suite", True, "old")
        data = json.loads(vs.STATE_PATH.read_text(encoding="utf-8"))
        data["last"]["ts"] = time.time() - (vs.DEFAULT_MAX_AGE_S + 60)
        vs.STATE_PATH.write_text(json.dumps(data), encoding="utf-8")
        if vs.was_verified() is None:
            _ok("V-VERIF-EXPIRY-IS-UNKNOWN",
                "an aged-out pass degrades to None, not False")
        else:
            _fail("V-VERIF-EXPIRY-IS-UNKNOWN", f"got {vs.was_verified()!r}")

        # THE STARVATION ITSELF. Fed a measured False, both detectors fire;
        # this is what could never happen before, and it is the difference
        # between "the rule is quiet" and "the rule cannot speak".
        commit_hits = engine.detect("commit",
                                    {"is_commit": True, "verified": False})
        deploy_hits = engine.detect("deploy",
                                    {"is_deploy": True, "tests_passed": False,
                                     "verified": False})
        if commit_hits and deploy_hits:
            _ok("V-VERIF-RULES-FIRE-WHEN-FED",
                f"HR-CASCADE-003 -> {commit_hits[0].severity.name}, "
                f"HR-CASCADE-001 -> {deploy_hits[0].severity.name}")
        else:
            _fail("V-VERIF-RULES-FIRE-WHEN-FED",
                  f"commit={commit_hits} deploy={deploy_hits}")

        # BOOKEND. Fed a measured True, the VERIFICATION-driven hits stop.
        #
        # Scoped deliberately. A first version asserted total silence and
        # failed, because _detect_deploy independently warns about a missing
        # rollback plan -- a separate contract that has nothing to do with
        # tests. The gate was wrong, not the code. Asserting "no hits at all"
        # would have pressured a correct warning into being deleted to make a
        # test green.
        quiet_c = engine.detect("commit", {"is_commit": True, "verified": True})
        quiet_d = engine.detect("deploy", {"is_deploy": True,
                                           "tests_passed": True,
                                           "verified": True,
                                           "has_rollback": True})
        test_driven = [h for h in quiet_c + quiet_d
                       if "test" in h.cascade_type.value
                       or "verif" in h.cascade_type.value]
        blockers = [h for h in quiet_c + quiet_d if h.should_block]
        if not test_driven and not blockers:
            _ok("V-VERIF-BOOKEND-VERIFIED-IS-SILENT",
                "a verified commit and deploy raise no test-driven hit and "
                f"no blocker (residual advisories: "
                f"{[h.cascade_type.value for h in quiet_c + quiet_d]})")
        else:
            _fail("V-VERIF-BOOKEND-VERIFIED-IS-SILENT",
                  f"test_driven={test_driven} blockers={blockers}")
    finally:
        vs.STATE_PATH = saved

    # The producer must be wired, or this is another starving consumer.
    src = (PP / "tools" / "verify_spp.py").read_text(encoding="utf-8-sig")
    if "record_verification(" in src:
        _ok("V-VERIF-PRODUCER-WIRED",
            "verify_spp records the verdict of every umbrella run")
    else:
        _fail("V-VERIF-PRODUCER-WIRED",
              "nothing writes verification state; the signal starves again")

    total = _passes + _fails
    print(f"VERIFICATION_PROVENANCE_PASS={_passes}/{total}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if total != EXPECTED_GATES:
        print(f"FAIL: {total} gates executed, {EXPECTED_GATES} declared")
        return 1
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
