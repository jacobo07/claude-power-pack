"""V-MHFP-* -- multi_host_fabric B1 was promoted through the ratchet, read back, and a demotion is refused.

Run: python tools/test_tower_mhf_promotion.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

_PP_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.tower import baselines as bl  # noqa: E402
from modules.tower import donegate as dg  # noqa: E402
from modules.tower import ratchet as rt  # noqa: E402

FAMILY = "multi_host_fabric"
ORCA = r"C:\Users\User\Apps\orca-rb-live-wt"
NEW = ("multi_host_fabric-live-leg-never-answers-bypass-consent",
       "multi_host_fabric-transfer-is-read-back-on-the-target")
_PASS = 0
_FAIL = 0


def _check(gate, cond, evidence, diagnostic):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-40s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-40s %s" % (gate, diagnostic))


def main() -> int:
    print("V-MHFP gates")
    gens = bl.generations(FAMILY)
    b1 = bl.load_generation(FAMILY, 1) if 1 in gens else {}
    ids = [e["id"] for e in b1.get("entries", [])]
    _check("V-MHFP-READ-BACK", gens == [0, 1] and all(n in ids for n in NEW) and len(ids) == 8,
           "B1 read from disk: %d entries, both promoted ids present" % len(ids), "gens=%s ids=%s" % (gens, ids))
    _check("V-MHFP-PROMOTED-BY-RATCHET", "promoted_by" in b1 and b1.get("reason", "").startswith("promote "),
           "record carries promoted_by + a promote reason", "no ratchet stamp: %s" % sorted(b1))
    rep = rt.verify_chain(FAMILY)
    _check("V-MHFP-CHAIN-OK", rep.ok and not rep.unanchored, "chain B0->B1 anchored, no regression",
           "report %s" % rep.as_dict())
    bad = [e["id"] for e in bl.active_entries(FAMILY) if bl.verify_origin(e, window=0) != bl.VERIFIED]
    _check("V-MHFP-ORIGINS-VERIFIED", not bad, "every active origin quote sits on its cited line", "drifted: %s" % bad)
    green = dg.judge(FAMILY, ORCA)
    verdicts = {v["entry_id"]: v["verdict"] for v in green["entries"]}
    _check("V-MHFP-REAL-REPO-GREEN",
           green["judged_under"] == FAMILY + "/B1" and not green["would_block"]
           and set(verdicts.values()) == {dg.APPLIED_VERIFIED} and len(verdicts) == 8,
           "real Orca repo judged under B1: 8/8 APPLIED_VERIFIED", "stamp %s verdicts %s" % (green["judged_under"], verdicts))

    tmp = tempfile.mkdtemp(prefix="mhfp_")
    try:
        root = os.path.join(tmp, "baselines")
        shutil.copytree(os.path.join(_PP_ROOT, "vault", "tower", "baselines"), root)
        # Control: a recorded revert on the copy is accepted, so the refusals below are the ratchet's.
        try:
            rt.revert(FAMILY, NEW[0], "", "someone", root=root)
            refused_blank = False
        except rt.RatchetRefusal:
            refused_blank = True
        _check("V-MHFP-REVERT-NEEDS-REASON", refused_blank, "a revert with no reason is refused", "blank reason accepted")
        try:
            rt.promote(FAMILY, [{"id": NEW[0], "requirement": "x", "why": "y", "origin": {}, "class": "D"}],
                       "dup", "someone", root=root)
            refused_dup = False
        except rt.RatchetRefusal:
            refused_dup = True
        _check("V-MHFP-REPROMOTE-REFUSED", refused_dup, "promoting an existing id is refused", "duplicate accepted")

        # Demotion attempt: a raw B2 that drops the entry to prose with no record.
        b1c = bl.load_generation(FAMILY, 1, root)
        weakened = [dict(e, check="") if e["id"] == NEW[1] else e for e in b1c["entries"]]
        bl.write_generation(FAMILY, weakened, "make the gate pass", root=root)
        kinds = [(r["id"], r["kind"]) for r in rt.verify_chain(FAMILY, root=root).regressions]
        _check("V-MHFP-DEMOTION-REFUSED", (NEW[1], rt.WEAKENED) in kinds,
               "an unrecorded drop to prose is WEAKENED on the chain", "regressions %s" % kinds)
        legit = rt.verify_chain(FAMILY)
        _check("V-MHFP-CONTROL-REAL-CHAIN-CLEAN", legit.ok, "the real chain stays clean while the copy is red",
               "real chain %s" % legit.as_dict())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\nMHFP_PASS=%d/%d  threshold=%d/%d" % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
