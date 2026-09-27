#!/usr/bin/env python3
"""V-MHV-* -- a mutation drill must prove its own mutation happened.

ORIGIN. GSD X N7 measured that `test_gsd_x_mutation.py`'s v1 drill had never
produced a valid verdict on this host: `core.autocrlf` is true, so a file clean
from checkout is CRLF while a dirty one keeps its writer's LF, and anchors
written with `\\n` matched 0x. The drill exited as HARNESS -- which says nothing
about the subject -- while the surrounding regression line still quoted an
earned mutation count. N7 fixed ITS TWO drills and nobody swept the class.

Swept 2026-09-27: 2 of 12 harnesses proved application. The other ten are this
file's subject.

WHAT THIS GATE ASSERTS. For every harness that actually mutates a file:

  APPLIED   it establishes the anchor was found before writing (count == 1,
            `not in text`, or an original/mutated comparison). Without this a
            zero-application run is indistinguishable from a clean one.
  HARNESS   it has an instrument-failure class distinct from a subject verdict.
            A drill that cannot say "I could not judge this" will eventually
            say PASS about nothing.
  RESTORE   it verifies the restore reproduced the original bytes.

EOL, CONTROL and REASON are reported but NOT enforced: a drill whose anchors are
single-line may legitimately need no line-ending translation, and enforcing an
unmutated control on every harness is ceremony this file has not earned evidence
for. Reporting them keeps them visible without charging a tax.

NOT A DRILL. A file matching the glob that never writes a subject file is not a
mutation harness -- it is infrastructure or the harness's own test. It is
excluded BY MEASUREMENT (no write+restore pair), never by a hand-kept skip list,
and the exclusions are printed so an exclusion nobody agrees with is arguable.

THE INVENTORY SHRINKS ONLY. `KNOWN_WEAK` freezes today's offenders so this gate
is green on arrival and a NEW weak harness fails it. An entry that has since
been fixed also fails, as a stale entry -- otherwise the list becomes a
permanent excuse and the ratchet stops turning.

THE DRILL IS SYNTHETIC. The red branch is driven against a throwaway harness
this file writes, not against whichever real harness is broken today. A drill
pinned to a real defect has an interest in that defect surviving, and it decays
the moment someone fixes it. The green half is shipped beside it, or a detector
that flagged everything would pass the red branch and look like it works.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools"

# The floor exists because a glob that silently stops matching reports the same
# clean bill as an estate with no weak harnesses. Measured 12 on 2026-09-27.
POPULATION_FLOOR = 8

# Verified by reading the file: tools/test_gsd_x_facts_v2_mutation.py carries
# every property this gate detects. If the detector cannot see all three
# enforced ones there, the detector is blind and every NO below is worthless.
POSITIVE_CONTROL = "test_gsd_x_facts_v2_mutation.py"

# Frozen 2026-09-27 BY THIS GATE'S OWN MEASUREMENT. Shrink only.
#
# The first version of this set was seeded from a looser text sweep and was
# wrong three ways at once -- it omitted four real drills and named one file
# that is not a drill at all. All three clauses below caught it on the first
# run, which is the only reason the list is right now. An inventory derived
# from a different instrument than the one that checks it is not an inventory;
# it is a second opinion that nothing reconciles.
#
# `test_gsd_x_manifest_reachability_mutation.py` is deliberately ABSENT: it
# mutates a scratch COPY through GSDX_REACH_MANIFEST and never writes the
# tracked file, so it has no write+restore pair on a subject and is excluded
# by measurement rather than by opinion.
KNOWN_WEAK = {
    "mutation_probe.py",
    "mutation_ratchet.py",
    "test_gsd_x_goal_mutation.py",
    "test_gsd_x_goal_mutation_safety.py",
    "test_gsd_x_mission_mutation.py",
    "test_gsd_x_mutation.py",
    "test_gsd_x_reconstruction_mutation.py",
    "test_mutation_probe.py",
    "test_mutation_ratchet.py",
}

# --- detectors ---------------------------------------------------------------
# Each is a list of alternatives; a property holds if ANY matches. Calibrated
# against the positive control rather than invented, and the control asserts
# that calibration still holds.

_MUTATES = (r"\.write_bytes\(", r"\.write_text\(", r"writeFileSync\(")
_RESTORES = (r"finally\s*:", r"restore", r"original")
_APPLIED = (
    r"\.count\([^)]*\)\s*(?:!=|==|<|>)",   # count(anchor) != 1
    r"anchor\s+found",                      # the message that names it
    r"\bnot\s+in\s+(?:text|src|body|source)\b",
    r"original\s*==\s*mutated",
    r"\bif\s+mutated\s*==\s*original\b",
)
_HARNESS = (r"HARNESS",)
_RESTORE_PROOF = (r"sha256", r"_sha\(", r"hashlib")
_EOL = (r'replace\("\\\\n"', r"autocrlf", r'"\\r\\n"\s+if')
_CONTROL = (r"\bCONTROL\b", r"unmutated")
_REASON = (r"must in failed", r"wrong reason", r"intended reason")


def _any(text: str, pats) -> bool:
    return any(re.search(p, text) for p in pats)


def classify(text: str) -> dict:
    return {
        "mutates": _any(text, _MUTATES) and _any(text, _RESTORES),
        "applied": _any(text, _APPLIED),
        "harness": _any(text, _HARNESS),
        "restore": _any(text, _RESTORE_PROOF),
        "eol": _any(text, _EOL),
        "control": _any(text, _CONTROL),
        "reason": _any(text, _REASON),
    }


ENFORCED = ("applied", "harness", "restore")


def is_weak(c: dict) -> bool:
    return not all(c[k] for k in ENFORCED)


def harnesses() -> list[Path]:
    return sorted(p for p in TOOLS.iterdir()
                  if p.is_file() and "mutation" in p.name
                  and p.suffix in (".py", ".js")
                  and p.name != Path(__file__).name)


# --- reporting ---------------------------------------------------------------
_pass = 0
_fail = 0


def ok(gate: str, evidence: str) -> None:
    global _pass
    _pass += 1
    print(f"  PASS {gate}: {evidence}")


def bad(gate: str, evidence: str) -> None:
    global _fail
    _fail += 1
    print(f"  FAIL {gate}: {evidence}")


def harness_failed(why: str) -> int:
    """The instrument could not judge. Never a subject verdict."""
    print(f"\nHARNESS-FAILED: {why}")
    print("MHV_PASS=0/0  threshold=HARNESS")
    return 2


# --- synthetic drill ----------------------------------------------------------
# Represents the CLASS, so it keeps working on the day the last real offender is
# fixed. A red subject with no applied-proof, and a green one with it.

_SYNTH_WEAK = '''
import hashlib
from pathlib import Path
p = Path("subject.py")
original = p.read_bytes()
try:
    p.write_bytes(original.replace(b"a", b"b"))
finally:
    p.write_bytes(original)
print(hashlib.sha256(original).hexdigest())
'''

_SYNTH_STRONG = '''
import hashlib
from pathlib import Path
p = Path("subject.py")
original = p.read_bytes()
text = original.decode("utf-8")
if text.count("anchor") != 1:
    print("HARNESS-FAILED: anchor found %dx" % text.count("anchor"))
    raise SystemExit(2)
try:
    p.write_bytes(text.replace("anchor", "moved").encode("utf-8"))
finally:
    p.write_bytes(original)
print(hashlib.sha256(original).hexdigest())
'''


def synthetic_drill() -> bool:
    """Drive both poles against a subject this file owns and deletes."""
    with tempfile.TemporaryDirectory() as d:
        weak = Path(d) / "test_synth_weak_mutation.py"
        strong = Path(d) / "test_synth_strong_mutation.py"
        weak.write_text(_SYNTH_WEAK, encoding="utf-8")
        strong.write_text(_SYNTH_STRONG, encoding="utf-8")
        cw = classify(weak.read_text(encoding="utf-8"))
        cs = classify(strong.read_text(encoding="utf-8"))

    red_ok = cw["mutates"] and is_weak(cw)
    green_ok = cs["mutates"] and not is_weak(cs)
    if red_ok:
        ok("V-MHV-DRILL-RED", "a synthetic harness with no applied-proof is flagged weak")
    else:
        bad("V-MHV-DRILL-RED",
            f"synthetic weak harness was not flagged (mutates={cw['mutates']}, {cw})")
    if green_ok:
        ok("V-MHV-DRILL-GREEN",
           "a synthetic harness WITH applied-proof is not flagged -- the detector "
           "is not simply flagging everything")
    else:
        bad("V-MHV-DRILL-GREEN",
            f"synthetic strong harness was flagged anyway ({cs})")
    return red_ok and green_ok


def main() -> int:
    found = harnesses()
    if len(found) < POPULATION_FLOOR:
        return harness_failed(
            f"found {len(found)} mutation harnesses under {TOOLS}, expected at least "
            f"{POPULATION_FLOOR}. The glob may have stopped matching; a sweep that "
            "found nothing must not read as a clean estate.")
    ok("V-MHV-POPULATION",
       f"{len(found)} harnesses discovered structurally (floor {POPULATION_FLOOR})")

    texts = {p.name: p.read_text(encoding="utf-8", errors="replace") for p in found}

    if POSITIVE_CONTROL not in texts:
        return harness_failed(
            f"positive control {POSITIVE_CONTROL} is not in the population; the "
            "detector cannot be calibrated and every verdict below is unfounded.")
    pc = classify(texts[POSITIVE_CONTROL])
    missing = [k for k in ENFORCED + ("eol", "control", "reason") if not pc[k]]
    if missing:
        return harness_failed(
            f"positive control {POSITIVE_CONTROL} did not light up {missing}. It was "
            "verified by reading to carry all of them, so the DETECTOR is blind and "
            "a NO from it means nothing.")
    ok("V-MHV-POSITIVE-CONTROL",
       f"{POSITIVE_CONTROL} lights every property -- the detector can see them")

    if not synthetic_drill():
        return harness_failed("the synthetic drill did not drive both poles")

    graded = {n: classify(t) for n, t in texts.items()}
    drills = {n: c for n, c in graded.items() if c["mutates"]}
    not_drills = sorted(n for n, c in graded.items() if not c["mutates"])
    if not_drills:
        print(f"  NOT-A-DRILL (never writes+restores a subject, excluded by "
              f"measurement): {', '.join(not_drills)}")
    if not drills:
        return harness_failed("no file in the population actually mutates a subject; "
                              "the `mutates` detector has probably gone blind.")

    weak_now = {n for n, c in drills.items() if is_weak(c)}
    strong_now = sorted(set(drills) - weak_now)

    print(f"\n  drills={len(drills)}  proving-application={len(strong_now)}  "
          f"weak={len(weak_now)}")
    for n in sorted(drills):
        c = drills[n]
        flags = "".join(k[0].upper() if c[k] else "-" for k in
                        ("applied", "harness", "restore", "eol", "control", "reason"))
        print(f"    {'WEAK  ' if n in weak_now else 'STRONG'} {flags}  {n}")

    new_weak = sorted(weak_now - KNOWN_WEAK)
    if new_weak:
        bad("V-MHV-NO-NEW-WEAK",
            "harness(es) added or regressed without proving their own mutation "
            f"applied: {new_weak}. A drill that cannot show the anchor matched "
            "reports a count it did not earn.")
    else:
        ok("V-MHV-NO-NEW-WEAK",
           f"no weak harness outside the frozen inventory of {len(KNOWN_WEAK)}")

    stale = sorted(KNOWN_WEAK - weak_now)
    if stale:
        bad("V-MHV-NO-STALE-INVENTORY",
            f"{stale} now prove their mutation applied but are still frozen as weak. "
            "Remove them from KNOWN_WEAK -- an inventory that outlives its debts "
            "becomes a permanent excuse.")
    else:
        ok("V-MHV-NO-STALE-INVENTORY",
           "every frozen entry is still a genuine current offender")

    absent = sorted(KNOWN_WEAK - set(drills))
    if absent:
        bad("V-MHV-INVENTORY-SUBJECTS-EXIST",
            f"{absent} are frozen as weak but are not drills in the population "
            "(renamed or deleted). The inventory is describing subjects that are "
            "no longer there.")
    else:
        ok("V-MHV-INVENTORY-SUBJECTS-EXIST",
           "every frozen entry names a harness that still exists and still mutates")

    print(f"\nMHV_PASS={_pass}/{_pass + _fail}  "
          f"threshold={_pass + _fail}/{_pass + _fail}")
    return 0 if _fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
