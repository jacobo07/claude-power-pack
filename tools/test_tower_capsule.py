"""V-TOWER-* -- the capsule's states must be DISTINGUISHABLE, not merely present.

G-3 (09_G3_DECISION.md) is only closed if a consumer can tell these apart:
legitimately empty, never produced, stale, not applicable, producer broken.
Before this, all five were "no output" -- the same observable -- which is why
O4 was infalsifiable.

The load-bearing case is V-TOWER-EMPTY-IS-NOT-UNKNOWN. Everything else can pass
while that one fails, and if it fails the whole design is back where it started.

Run: python tools/test_tower_capsule.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
for p in (_PP_ROOT, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import tower_capsule as tc  # noqa: E402

_PASS = 0
_FAIL = 0


def _ok(gate: str, evidence: str) -> None:
    global _PASS
    _PASS += 1
    print("  PASS %-34s %s" % (gate, evidence))


def _fail(gate: str, diagnostic: str) -> None:
    global _FAIL
    _FAIL += 1
    print("  FAIL %-34s %s" % (gate, diagnostic))


def _check(gate: str, cond: bool, evidence: str, diagnostic: str) -> None:
    _ok(gate, evidence) if cond else _fail(gate, diagnostic)


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="tower_capsule_gate_")
    real_state_dir = tc._state_dir
    real_repo_key = tc._repo_key
    real_family = tc._family_of
    real_deposits = tc._deposits_for
    try:
        tc._state_dir = lambda: tmp                      # hermetic
        tc._repo_key = lambda path=None: "SYNTHETIC-REPO"

        print("V-TOWER gates")

        # --- AVAILABLE: in family, deposits present -------------------------
        tc._family_of = lambda path: (True, "migrations_dir")
        tc._deposits_for = lambda key: [
            {"delta_class": "NEW", "destination": "hard_rule",
             "portability_proven": False},
            {"delta_class": "STRONGER", "destination": "benchmark",
             "portability_proven": False},
        ]
        cap = tc.produce("/synthetic")
        _check("V-TOWER-AVAILABLE", cap["state"] == tc.AVAILABLE,
               "state=%s entries=%s" % (cap["state"], cap.get("entries")),
               "expected AVAILABLE, got %s" % cap["state"])
        _check("V-TOWER-AVAILABLE-TOKENS",
               tc.evidence_tokens("/synthetic") == ["tower_baseline"],
               "tokens=%s" % tc.evidence_tokens("/synthetic"),
               "AVAILABLE must contribute its evidence token")
        _check("V-TOWER-VERIFIED-NOT-CLAIMED", cap.get("verified_entries") == 0,
               "verified_entries=0 while FD-07 writes portability_proven=False",
               "the `verified` clause must not be claimed from unproven deposits")

        # --- EMPTY_BY_EVIDENCE: in family, nothing promoted -----------------
        tc._deposits_for = lambda key: []
        cap_empty = tc.produce("/synthetic")
        _check("V-TOWER-EMPTY-BY-EVIDENCE",
               cap_empty["state"] == tc.EMPTY_BY_EVIDENCE,
               "state=%s" % cap_empty["state"],
               "expected EMPTY_BY_EVIDENCE, got %s" % cap_empty["state"])

        # --- THE LOAD-BEARING ONE -------------------------------------------
        read_empty = tc.read("/synthetic")
        os.remove(tc.capsule_path("/synthetic"))
        read_absent = tc.read("/synthetic")
        _check("V-TOWER-EMPTY-IS-NOT-UNKNOWN",
               read_empty["state"] == tc.EMPTY_BY_EVIDENCE
               and read_absent["state"] == tc.UNKNOWN
               and read_empty["state"] != read_absent["state"],
               "empty=%s absent=%s -- distinguishable"
               % (read_empty["state"], read_absent["state"]),
               "a capsule that is legitimately empty and one that was never "
               "produced must not read alike")

        # --- UNKNOWN is SAID, never silence ---------------------------------
        _check("V-TOWER-UNKNOWN-IS-SPOKEN",
               bool(read_absent.get("reason")) and read_absent["evidence_tokens"] == [],
               "reason=%r tokens=[]" % read_absent["reason"],
               "absence must carry a reason, not an empty return")

        # --- NOT_APPLICABLE still produces a capsule ------------------------
        tc._family_of = lambda path: (False, "no markers")
        cap_na = tc.produce("/synthetic")
        _check("V-TOWER-NOT-APPLICABLE",
               cap_na["state"] == tc.NOT_APPLICABLE
               and os.path.exists(tc.capsule_path("/synthetic")),
               "state=NOT_APPLICABLE and a capsule was still written",
               "out-of-family must STATE not-applicable, not stay silent")
        _check("V-TOWER-NOT-APPLICABLE-NO-TOKENS",
               tc.evidence_tokens("/synthetic") == [],
               "tokens=[] for NOT_APPLICABLE",
               "a non-applicable capsule must contribute no evidence")

        # --- STALE: produced, but past its contract -------------------------
        tc._family_of = lambda path: (True, "migrations_dir")
        tc._deposits_for = lambda key: [
            {"delta_class": "NEW", "destination": "hard_rule",
             "portability_proven": False}]
        tc.produce("/synthetic")
        p = tc.capsule_path("/synthetic")
        with open(p, "r", encoding="utf-8") as fh:
            aged = json.load(fh)
        aged["produced_at"] = time.time() - (tc.FRESH_SECONDS + 60)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(aged, fh)
        read_stale = tc.read("/synthetic")
        _check("V-TOWER-STALE", read_stale["state"] == tc.STALE,
               "state=STALE (%s)" % read_stale.get("reason"),
               "expected STALE, got %s" % read_stale["state"])
        _check("V-TOWER-STALE-DROPS-TOKENS",
               tc.evidence_tokens("/synthetic") == [],
               "stale evidence contributes nothing",
               "stale evidence must not reach MissionContext")

        # --- PRODUCER_FAILURE is its own state ------------------------------
        def _boom(path):
            raise RuntimeError("scanner exploded")
        tc._family_of = _boom
        cap_fail = tc.produce("/synthetic")
        _check("V-TOWER-PRODUCER-FAILURE",
               cap_fail["state"] == tc.PRODUCER_FAILURE
               and cap_fail["state"] != tc.EMPTY_BY_EVIDENCE,
               "state=PRODUCER_FAILURE, distinct from EMPTY_BY_EVIDENCE",
               "a broken producer must not read as an empty baseline")

        # --- G-4: the capsule must never touch the gating fields ------------
        src = open(os.path.join(_HERE, "tower_capsule.py"), "r",
                   encoding="utf-8").read()
        emits_gates = ('"held_scopes"' in src or "'held_scopes'" in src
                       or '"resolved_owners"' in src or "'resolved_owners'" in src)
        _check("V-TOWER-G4-EVIDENCE-ONLY", not emits_gates,
               "module emits no held_scopes / resolved_owners key",
               "G-4: a partial value in those fields INVERTS applicability")

        # --- atomic write leaves no debris ----------------------------------
        tc._family_of = lambda path: (True, "migrations_dir")
        tc.produce("/synthetic")
        leftovers = [f for f in os.listdir(tmp) if f.endswith(".tmp")]
        _check("V-TOWER-ATOMIC", not leftovers,
               "no .tmp debris after produce()",
               "found %s" % leftovers)

        print()
        print("TOWER_CAPSULE_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
        return 0 if _FAIL == 0 else 1
    finally:
        tc._state_dir = real_state_dir
        tc._repo_key = real_repo_key
        tc._family_of = real_family
        tc._deposits_for = real_deposits
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
