"""Production Reality evidence gate for fidelity work (family game_mod_fidelity).

A run's evidence decides which states it may claim. Nothing here approves
anything: `allowed` computes the set of claimable states from observed facts and
`validate_claim` refuses a claim outside it.

States and what each needs (a state never implies the one above it):

  NO_EVIDENCE       always claimable
  DOLPHIN_LOAD      stills from Dolphin: the content loads, nothing more
  DOLPHIN_BEHAVIOR  a continuous video from Dolphin (a still cannot show behaviour)
  WII_TESTED        DOLPHIN_BEHAVIOR plus physical-console evidence AND logs
  OWNER_APPROVED    a recorded Owner decision (a file) on top of DOLPHIN_BEHAVIOR;
                    this is visual approval, not console proof
  PASS              WII_TESTED and OWNER_APPROVED together

OWNER_APPROVED and WII_TESTED are deliberately incomparable: approval in Dolphin
is a real state and it is not the console.

A row the independent audit already read as a failure (FAIL, FAIL_VISUAL) claims
nothing above FAIL: more captures of a failing result do not turn it into a pass.
The probe's own outcome letter is never an input. It answers "did the causal
question get answered", not "does it look like the reference"; a claim whose
source is the letter is refused by name.
"""
from __future__ import annotations

import csv
import io

NO_EVIDENCE = "NO_EVIDENCE"
DOLPHIN_LOAD = "DOLPHIN_LOAD"
DOLPHIN_BEHAVIOR = "DOLPHIN_BEHAVIOR"
WII_TESTED = "WII_TESTED"
OWNER_APPROVED = "OWNER_APPROVED"
PASS = "PASS"
FAIL = "FAIL"

STATES = (NO_EVIDENCE, DOLPHIN_LOAD, DOLPHIN_BEHAVIOR, WII_TESTED, OWNER_APPROVED, PASS)
FAILING = ("FAIL", "FAIL_VISUAL")


class ClaimRefused(ValueError):
    """A claimed state the evidence does not support; nothing was recorded."""


def _yes(v) -> bool:
    return str(v or "").strip().upper() in ("YES", "TRUE", "1", "Y")


def allowed(rec: dict) -> frozenset:
    """States `rec` may claim. Keys read: assessment, run, shots, video, wii_hardware,
    hardware_logs, owner_approved, owner_decision_file."""
    if str(rec.get("assessment", "")).strip().upper() in FAILING:
        return frozenset({FAIL})
    ok = {NO_EVIDENCE}
    if int(rec.get("shots") or 0) < 1 or str(rec.get("run", "")).upper() in ("", "NO_RUN"):
        return frozenset(ok)
    ok.add(DOLPHIN_LOAD)
    if not _yes(rec.get("video")):
        return frozenset(ok)
    ok.add(DOLPHIN_BEHAVIOR)
    tested = _yes(rec.get("wii_hardware")) and _yes(rec.get("hardware_logs"))
    approved = _yes(rec.get("owner_approved")) and bool(str(rec.get("owner_decision_file") or "").strip())
    if tested:
        ok.add(WII_TESTED)
    if approved:
        ok.add(OWNER_APPROVED)
    if tested and approved:
        ok.add(PASS)
    return frozenset(ok)


def top_state(rec: dict) -> str:
    """The strongest state in `allowed(rec)`, for reporting (PASS > both > one > Dolphin)."""
    a = allowed(rec)
    for s in (PASS, WII_TESTED, OWNER_APPROVED, DOLPHIN_BEHAVIOR, DOLPHIN_LOAD, NO_EVIDENCE, FAIL):
        if s in a:
            return s
    return NO_EVIDENCE


def validate_claim(rec: dict, claimed: str, source: str = "evidence") -> str:
    """Return `claimed` if the evidence supports it, else raise ClaimRefused."""
    if claimed not in STATES + (FAIL,):
        raise ClaimRefused("unknown state %r" % claimed)
    if source != "evidence":
        raise ClaimRefused("a claim from %r is not evidence (a probe outcome answers the causal "
                           "question, not the fidelity one)" % source)
    if claimed not in allowed(rec):
        raise ClaimRefused("%s claims %s but its evidence supports only %s"
                           % (rec.get("unit"), claimed, sorted(allowed(rec))))
    return claimed


def parse_tracker(text: str) -> list:
    """Rows of a TTB_Run_Audit_Tracker CSV as records `allowed` understands.

    The tracker records stills only, so `video` and `hardware_logs` are NO here: a
    still is not behaviour, and the tracker's hardware column is read as written.
    """
    out = []
    for row in csv.DictReader(io.StringIO(text.lstrip("﻿"))):
        out.append({
            "unit": row.get("Unit"), "run": row.get("Run"), "shots": row.get("Shots") or 0,
            "assessment": row.get("Assessment"),
            "wii_hardware": row.get("Wii hardware tested?"),
            "owner_approved": row.get("Owner approved?"),
            "video": "NO", "hardware_logs": "NO", "owner_decision_file": "",
        })
    return out


def summarize(records: list) -> dict:
    """unit -> top state, plus a count per state."""
    per = {r["unit"]: top_state(r) for r in records}
    counts: dict = {}
    for v in per.values():
        counts[v] = counts.get(v, 0) + 1
    return {"per_unit": per, "counts": counts}
