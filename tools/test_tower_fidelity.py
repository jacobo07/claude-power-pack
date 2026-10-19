"""V-GMF-* -- the game_mod_fidelity family and its evidence gate (modules/tower/evidence).

The discriminating subject is the real audit of the 42 TB captures: nine rows are
UNVERIFIED, four FAIL_VISUAL, one PARTIAL, one without a run. Every refusal has a
control in which the evidence exists and the claim is admitted, so a gate that
refuses everything cannot pass.

Run: python tools/test_tower_fidelity.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
for p in (_PP_ROOT, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from modules.tower import baselines as bl  # noqa: E402
from modules.tower import evidence as ev  # noqa: E402

TRACKER = os.path.join(_PP_ROOT, "vault", "tower", "sources", "ttb-fidelity-v3",
                       "TTB_Run_Audit_Tracker_v3.csv")
FAMILY = "game_mod_fidelity"
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


def _refused(rec, claimed, source="evidence"):
    try:
        ev.validate_claim(rec, claimed, source)
    except ev.ClaimRefused as exc:
        return str(exc)
    return None


FULL = {"unit": "X", "run": "tbl-1", "shots": 3, "assessment": "UNVERIFIED", "video": "YES",
        "wii_hardware": "YES", "hardware_logs": "YES", "owner_approved": "YES",
        "owner_decision_file": "fidelity/decisions/X.md"}


def main():
    with open(TRACKER, encoding="utf-8") as fh:
        recs = ev.parse_tracker(fh.read())
    by = {r["unit"]: r for r in recs}
    summ = ev.summarize(recs)

    _check("V-GMF-TRACKER-ROWS", len(recs) == 15, "15 audited units parsed",
           "rows=%d" % len(recs))
    top = {s for s in summ["per_unit"].values()}
    _check("V-GMF-NOTHING-ABOVE-STILLS", top <= {ev.DOLPHIN_LOAD, ev.FAIL, ev.NO_EVIDENCE},
           "counts=%s" % summ["counts"], "a real row claims above stills: %s" % top)
    _check("V-GMF-FAIL-VISUAL-KEPT",
           all(summ["per_unit"][u] == ev.FAIL for u in ("F2A", "F3A", "F3B", "F3C")),
           "F2A F3A F3B F3C stay FAIL", "per_unit=%s" % summ["per_unit"])
    _check("V-GMF-NO-RUN-NO-EVIDENCE", summ["per_unit"]["F6C"] == ev.NO_EVIDENCE,
           "F6C has no run -> NO_EVIDENCE", "F6C=%s" % summ["per_unit"]["F6C"])

    for state in (ev.PASS, ev.WII_TESTED, ev.OWNER_APPROVED, ev.DOLPHIN_BEHAVIOR):
        why = _refused(by["F4B"], state)
        _check("V-GMF-REFUSE-%s" % state, why is not None, "F4B refused: %s" % (why or "")[:70],
               "F4B was allowed to claim %s on stills" % state)
    _check("V-GMF-CONTROL-STILLS-ADMITTED", _refused(by["F4B"], ev.DOLPHIN_LOAD) is None,
           "F4B may claim DOLPHIN_LOAD", "the control refused a supported claim")

    why = _refused(by["F4B"], ev.DOLPHIN_LOAD, source="probe_outcome")
    _check("V-GMF-PROBE-LETTER-NOT-EVIDENCE", why is not None and "probe outcome" in why,
           "supported claim still refused when sourced from the letter", "letter accepted: %s" % why)

    _check("V-GMF-CONTROL-FULL-PASS", _refused(FULL, ev.PASS) is None and ev.top_state(FULL) == ev.PASS,
           "video + hardware + logs + decision file -> PASS", "full evidence refused")
    nolog = dict(FULL, hardware_logs="NO")
    _check("V-GMF-HW-NEEDS-LOGS", _refused(nolog, ev.WII_TESTED) is not None
           and _refused(nolog, ev.PASS) is not None, "hardware without logs: no WII_TESTED, no PASS",
           "hardware alone was accepted")
    novid = dict(FULL, video="NO")
    _check("V-GMF-STILLS-ARE-NOT-BEHAVIOUR", ev.allowed(novid) == {ev.NO_EVIDENCE, ev.DOLPHIN_LOAD},
           "no video caps at DOLPHIN_LOAD even with hardware flags", "allowed=%s" % sorted(ev.allowed(novid)))
    nofile = dict(FULL, owner_decision_file="")
    _check("V-GMF-APPROVAL-IS-A-FILE", _refused(nofile, ev.OWNER_APPROVED) is not None,
           "'YES' without a decision file is not approval", "approval accepted with no record")
    nohw = dict(FULL, wii_hardware="NO")
    _check("V-GMF-DOLPHIN-APPROVAL-NOT-PASS",
           _refused(nohw, ev.OWNER_APPROVED) is None and _refused(nohw, ev.PASS) is not None,
           "Owner approval in Dolphin is real but is not PASS", "approval promoted to PASS")
    failing = dict(FULL, assessment="FAIL_VISUAL")
    _check("V-GMF-MORE-CAPTURES-NO-PASS", ev.allowed(failing) == {ev.FAIL},
           "a failing audit stays FAIL with full evidence", "allowed=%s" % sorted(ev.allowed(failing)))
    _check("V-GMF-UNKNOWN-STATE", _refused(FULL, "SHIPPED") is not None, "unknown state refused",
           "unknown state accepted")

    entries = bl.active_entries(FAMILY)
    bad = [e["id"] for e in entries if bl.verify_origin(e) != bl.VERIFIED]
    _check("V-GMF-B0-CITATIONS", len(entries) == 7 and not bad, "7 entries, every citation re-read VERIFIED",
           "entries=%d unverified=%s" % (len(entries), bad))

    gate = os.path.join(_HERE, "family_baseline.py")
    with tempfile.TemporaryDirectory() as empty, tempfile.TemporaryDirectory() as full:
        for rel, body in (("fidelity/measurements/run_audit_tracker.csv",
                           "Unit,Run,Shots,Assessment,Why,Wii hardware tested?\nF1,r,3,PARTIAL,x,NO\n"),
                          ("fidelity/references/refs.sha256", "abc  ref.png\n"),
                          ("fidelity/contracts/jacobo.json", "{}\n"),
                          ("fidelity/decisions/OWNER.md", "d\n"),
                          ("fidelity/captures/dolphin-native/a.png", "x"),
                          ("tools/test_fidelity_planes.py", "pass\n")):
            path = os.path.join(full, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(body)
        red = subprocess.run([sys.executable, "-I", gate, "judge", FAMILY, "--repo", empty],
                             capture_output=True, text=True)
        green = subprocess.run([sys.executable, "-I", gate, "judge", FAMILY, "--repo", full],
                               capture_output=True, text=True)
    _check("V-GMF-JUDGE-RED-ON-EMPTY", red.returncode == 1 and "VIOLATED" in red.stdout,
           "an empty repo would be blocked", "rc=%s out=%s" % (red.returncode, red.stdout[-200:]))
    _check("V-GMF-JUDGE-GREEN-WITH-STRUCTURE", green.returncode == 0 and "VIOLATED" not in green.stdout,
           "a repo with the structure is not blocked", "rc=%s out=%s" % (green.returncode, green.stdout[-300:]))

    from modules.tower import families as fam  # noqa: E402
    _check("V-GMF-ACTIVATES-BY-PROMPT",
           fam.classify_prompt("compare the kitten capture with a 1:1 fidelity gate")[0][0] == FAMILY
           and fam.classify_prompt("fix the css padding on the pricing page") == [],
           "a fidelity prompt selects the family; an unrelated one selects nothing",
           "prompt classification wrong")
    with tempfile.TemporaryDirectory() as proj, tempfile.TemporaryDirectory() as other:
        os.makedirs(os.path.join(proj, ".planning"))
        with open(os.path.join(proj, ".planning", "PROJECT.md"), "w", encoding="utf-8") as fh:
            fh.write("# The Two Builders\n")
        hit = FAMILY in fam.repo_families(proj)
        miss = FAMILY not in fam.repo_families(other)
    _check("V-GMF-ACTIVATES-BY-REPO", hit and miss,
           "a repo marker selects the family without copying it; an empty repo does not",
           "hit=%s miss=%s" % (hit, miss))

    print("GMF_PASS=%d/%d  threshold=%d/%d" % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
