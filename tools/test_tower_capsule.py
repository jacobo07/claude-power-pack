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

from modules.tower import capsule as tc  # noqa: E402

# The module under test, for the G-4 source assertion below. Derived, never a
# second literal: if the implementation moves again this follows it.
_MODULE_SRC = os.path.abspath(tc.__file__)

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
    real_institutional = tc._deposits_institutional
    try:
        tc._state_dir = lambda: tmp                      # hermetic
        tc._repo_key = lambda path=None: "SYNTHETIC-REPO"
        # The estate's OWN ledgers must be isolated too. Cross-repo inheritance
        # made produce() read every ledger under ~/.claude/state, so without
        # this the real 215 deposits leak in and EMPTY_BY_EVIDENCE becomes
        # unreachable -- which is exactly how this gate went 13/15 the moment
        # inheritance landed. A hermetic test is hermetic about ALL its inputs,
        # and a new input silently un-isolates it.
        tc._deposits_institutional = lambda exclude_key=None: ([], 0)

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
               tc.evidence_tokens("/synthetic") == ["tower_baseline", tc.FAMILY_TOKEN],
               "tokens=%s" % tc.evidence_tokens("/synthetic"),
               "an in-family AVAILABLE capsule must contribute the universal "
               "AND the family token, got %s" % tc.evidence_tokens("/synthetic"))
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

        # --- OUT OF THE FAMILY STILL INHERITS THE UNIVERSAL LAYER -----------
        # INVERTED 2026-09-24 (C2). This case used to assert that an
        # out-of-family repo's WHOLE capsule was NOT_APPLICABLE -- which is how
        # CavEX inherited nothing. Spec §12.4: the Tower is universal ancestry
        # ABOVE the family baselines. Not-applicable now lives in family_layer.
        tc._family_of = lambda path: (False, "no markers")
        tc._deposits_for = lambda key: [
            {"delta_class": "NEW", "destination": "hard_rule",
             "portability_proven": False, "claim": "never truncate before serializing"}]
        cap_na = tc.produce("/synthetic")
        _check("V-TOWER-NOT-APPLICABLE",
               cap_na["family_layer"]["state"] == tc.NOT_APPLICABLE
               and cap_na["state"] == tc.AVAILABLE
               and os.path.exists(tc.capsule_path("/synthetic")),
               "family_layer=NOT_APPLICABLE, universal=AVAILABLE, capsule written",
               "out-of-family must be NOT_APPLICABLE in the family layer only, "
               "got state=%s family=%s" % (cap_na["state"], cap_na.get("family_layer")))
        _check("V-TOWER-NOT-APPLICABLE-NO-TOKENS",
               tc.evidence_tokens("/synthetic") == ["tower_baseline"],
               "tokens=['tower_baseline'] -- universal yes, family token no",
               "out-of-family must carry the universal token and never the "
               "family one, got %s" % tc.evidence_tokens("/synthetic"))

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
        # The UNIVERSAL producer broken -> the capsule says so.
        def _boom(*a, **k):
            raise RuntimeError("ledger read exploded")
        tc._deposits_institutional = _boom
        cap_fail = tc.produce("/synthetic")
        tc._deposits_institutional = lambda exclude_key=None: ([], 0)
        _check("V-TOWER-PRODUCER-FAILURE",
               cap_fail["state"] == tc.PRODUCER_FAILURE
               and cap_fail["state"] != tc.EMPTY_BY_EVIDENCE,
               "state=PRODUCER_FAILURE, distinct from EMPTY_BY_EVIDENCE",
               "a broken producer must not read as an empty baseline")
        # The FAMILY scanner broken -> only the family layer says so; the
        # universal inheritance must survive it.
        tc._family_of = _boom
        cap_ff = tc.produce("/synthetic")
        _check("V-TOWER-FAMILY-FAILURE-ISOLATED",
               cap_ff["family_layer"]["state"] == tc.PRODUCER_FAILURE
               and cap_ff["state"] == tc.AVAILABLE,
               "family_layer=PRODUCER_FAILURE, universal still AVAILABLE",
               "a broken family scanner must not cost the universal layer, got "
               "state=%s family=%s" % (cap_ff["state"], cap_ff.get("family_layer")))

        # --- G-4: the capsule must never touch the gating fields ------------
        with open(_MODULE_SRC, "r", encoding="utf-8") as fh:
            src = fh.read()
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

        # --- G-5: one repo, one key, whatever directory you stand in --------
        # Spec §11.b.9. The real repo_key is restored for this case: mocking it
        # would make the assertion about the mock. repo_identity exists BECAUSE
        # slugging the cwd created a second identity with an empty ledger the
        # moment anyone cd'd into a subdirectory, and a worktree's `.git` is a
        # FILE, which this tree has seven of.
        tc._repo_key = real_repo_key
        root_key = tc._repo_key(_PP_ROOT)
        sub = os.path.join(_PP_ROOT, "modules", "tower")
        sub_key = tc._repo_key(sub)
        rel_key = tc._repo_key(os.path.relpath(sub, os.getcwd())) if os.path.isdir(sub) else None
        _check("V-TOWER-G5-SUBDIR-SAME-KEY", root_key == sub_key and bool(root_key),
               "root and modules/tower both -> %s" % root_key,
               "subdirectory resolved to a DIFFERENT identity: %s vs %s"
               % (root_key, sub_key))
        _check("V-TOWER-G5-RELATIVE-SAME-KEY", rel_key == root_key,
               "a RELATIVE path resolves to the same key",
               "relative path gave %s, absolute gave %s -- this is the silent "
               "UNKNOWN measured on the first probe of the wired path"
               % (rel_key, root_key))

        print()
        print("TOWER_CAPSULE_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
        return 0 if _FAIL == 0 else 1
    finally:
        tc._state_dir = real_state_dir
        tc._repo_key = real_repo_key
        tc._family_of = real_family
        tc._deposits_for = real_deposits
        tc._deposits_institutional = real_institutional
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
