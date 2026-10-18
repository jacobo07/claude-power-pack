"""V-MHF-* -- the multi_host_fabric family: B0 from verified origins, a violation goes red.

B0 was built from lines that exist in the Orca repo (AGENTS.md rules and the DWS row-59
live-run evidence). The subject for the green leg is that real repo; the red leg is a copy
whose evidence says the opposite. A missing subject is INVALID (exit 3), never a pass.

Run: python tools/test_tower_multi_host_fabric.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.tower import baselines as bl  # noqa: E402
from modules.tower import donegate as dg  # noqa: E402
from modules.tower import families as fm  # noqa: E402

FAMILY = "multi_host_fabric"
ORCA = r"C:\Users\User\Apps\orca-rb-live-wt"
EVIDENCE = os.path.join("docs", "dws", "live-2026-10-18-row-59-model-turn-evidence.md")
SUBJECT_FILES = ("AGENTS.md", EVIDENCE,
                 os.path.join("docs", "reference", "remote-wire-compatibility.md"),
                 os.path.join("docs", "reference", "detach-stop-cancel-effects.md"),
                 os.path.join("src", "main", "workspace-execution-consent.ts"))
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


def _verdicts(rep):
    return {v["entry_id"]: v["verdict"] for v in rep["entries"]}


def _copy_subject(dst, mutate_evidence=None):
    for rel in SUBJECT_FILES:
        out = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copyfile(os.path.join(ORCA, rel), out)
    if mutate_evidence:
        p = os.path.join(dst, EVIDENCE)
        with open(p, "r", encoding="utf-8") as fh:
            text = fh.read()
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(mutate_evidence(text))


def main() -> int:
    missing = [r for r in SUBJECT_FILES if not os.path.isfile(os.path.join(ORCA, r))]
    if missing:
        print("INVALID: subject files missing from the Orca repo: %s" % missing)
        return 3
    print("V-MHF gates")

    entries = bl.active_entries(FAMILY)
    _check("V-MHF-B0-EXISTS", bl.generations(FAMILY) == [0] and len(entries) == 6,
           "B0 only, %d active entries" % len(entries), "generations=%s" % bl.generations(FAMILY))
    bad = [e["id"] for e in entries if bl.verify_origin(e, window=0) != bl.VERIFIED]
    _check("V-MHF-ORIGINS-VERIFIED", not bad, "every cited quote is on its cited line", "drifted: %s" % bad)
    _check("V-MHF-ALL-CHECKABLE", all(e.get("check") for e in entries),
           "every entry carries a runnable check", "an entry has no check")

    green = dg.judge(FAMILY, ORCA)
    _check("V-MHF-REAL-REPO-GREEN",
           green["status"] == dg.JUDGED and not green["would_block"]
           and set(_verdicts(green).values()) == {dg.APPLIED_VERIFIED},
           "real Orca repo: %d/6 APPLIED_VERIFIED, would_block=False" % len(green["entries"]),
           "verdicts %s" % _verdicts(green))

    tmp = tempfile.mkdtemp(prefix="mhf_")
    try:
        ok_copy = os.path.join(tmp, "ok")
        _copy_subject(ok_copy)
        _check("V-MHF-COPY-STAYS-GREEN", not dg.judge(FAMILY, ok_copy)["would_block"],
               "an unmutated copy of the subject is green (the copy itself does not cause red)", "copy is red")

        red_copy = os.path.join(tmp, "red")
        _copy_subject(red_copy, lambda t: t.replace("SVC_HOME_RESTORED=True", "SVC_HOME_RESTORED=False"))
        red = dg.judge(FAMILY, red_copy)
        v = _verdicts(red)
        _check("V-MHF-VIOLATION-GOES-RED",
               red["would_block"] and v.get("multi_host_fabric-live-leg-restores-service-home") == dg.VIOLATED,
               "service home left unrestored -> VIOLATED on its own entry, would_block=True",
               "verdicts %s" % v)
        _check("V-MHF-VIOLATION-IS-ISOLATED",
               [k for k, x in v.items() if x == dg.VIOLATED] == ["multi_host_fabric-live-leg-restores-service-home"],
               "exactly one entry went red", "red set %s" % [k for k, x in v.items() if x != dg.APPLIED_VERIFIED])
        _check("V-MHF-VERDICT-STAMPED", red["judged_under"] == FAMILY + "/B0" and red["chain_ok"],
               "report stamped %s, chain OK" % red["judged_under"], "stamp %s chain %s" % (red["judged_under"], red["chain_ok"]))

        missing_rule = os.path.join(tmp, "norule")
        _copy_subject(missing_rule)
        os.remove(os.path.join(missing_rule, "docs", "reference", "remote-wire-compatibility.md"))
        mv = _verdicts(dg.judge(FAMILY, missing_rule))
        _check("V-MHF-MISSING-RULE-GOES-RED",
               mv.get("multi_host_fabric-mixed-version-peers-are-normal") == dg.VIOLATED,
               "a repo without the wire-compatibility note is VIOLATED", "verdicts %s" % mv)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ids = sorted(f.id for f in fm.load_families())
    _check("V-MHF-CONTROL-FAMILY-LOADS", FAMILY in ids, "family file is read: %s" % ids, "family not loaded: %s" % ids)
    hit = [m[0] for m in fm.classify_prompt("revisa el continue here entre el host remoto y el cliente")]
    miss = [m[0] for m in fm.classify_prompt("cambia el color del botón del hero")]
    _check("V-MHF-CONTROL-CLASSIFIES", FAMILY in hit and FAMILY not in miss,
           "a host-remoto prompt selects the family; a hero-colour prompt does not", "hit=%s miss=%s" % (hit, miss))
    _check("V-MHF-CONTROL-NO-FAMILY-NO-BASELINE", dg.judge("no_such_family", ORCA)["status"] == dg.NO_BASELINE,
           "an unknown family judges NO_BASELINE, so green above is the family's", "unknown family judged")

    print("\nMHF_PASS=%d/%d  threshold=%d/%d" % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
