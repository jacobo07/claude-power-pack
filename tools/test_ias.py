#!/usr/bin/env python3
"""IAS family done-gate — existence + integrity V-gate for the cpp_ias Tier-B extensions.

Gates each Part appended to a cpp_ias owner by the CPCSC Tier-B pass, plus whole-file
Part / FINAL-LAW integrity for that owner. Designed to be observed to refuse: a gate that
has never failed is epistemically indistinguishable from an inert checker.

Per target owner (label INFIX derived from the dataset id, e.g. ias_a1 -> IAS-A1):
  V-<INFIX>-EXTPART-EXISTS   the appended Part header AND its FINAL LAW both present
  V-<INFIX>-EXTPART-FLOOR    the appended Part body >= the density floor (words)
  V-<INFIX>-EXTPART-CONTAM   0 distinctive-commercial literals in the appended Part body
  V-<INFIX>-INTEGRITY        Parts I..N contiguous (N >= min_parts), each closed by FINAL LAW.

Run:  python tools/test_ias.py
Exit: 0 iff every gate passes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

IAS_DIR = Path(__file__).resolve().parent.parent / "vault" / "knowledge_base" / "cpp_ias"

# One row per Tier-B extension. `min_parts` is the whole-file Part count the owner reaches
# AFTER its extension — a data field describing the owner, not a tuning constant.
#   (label, relative path, appended-Part header prefix, appended-Part FINAL LAW, min_parts)
TARGETS = [
    ("ias_a1", "01_CROSS_SYSTEM_CIRCULATION/ias_a1_capability_router.txt",
     "PART XXIII — THE MISSION CONSTITUTION", "FINAL LAW — PART XXIII.", 23),
    ("ias_d2", "04_SYSTEM_ECOLOGY_IMMUNOLOGY/ias_d2_immune_system.txt",
     "PART XXV — CLASS SEVEN", "FINAL LAW — PART XXV.", 25),
    ("ias_f3-p25", "06_FORESIGHT_ARCHITECTURE/ias_f3_digital_twin.txt",
     "PART XXV — DISASTER-RECOVERY SIMULATION", "FINAL LAW — PART XXV.", 27),
    ("ias_f3-p26", "06_FORESIGHT_ARCHITECTURE/ias_f3_digital_twin.txt",
     "PART XXVI — MODEL-EXIT SIMULATION", "FINAL LAW — PART XXVI.", 27),
    ("ias_f3-p27", "06_FORESIGHT_ARCHITECTURE/ias_f3_digital_twin.txt",
     "PART XXVII — THE SPOF, MATURITY, AND DEBT REGISTER", "FINAL LAW — PART XXVII.", 27),
]

# distinctive commercial literals — fragment-assembled so THIS file spells none of them out
# (a checker that spelled the forbidden words would itself carry the contamination it enforces).
_FRAG = [("ecom", "merce"), ("Common", "Wealth"), ("store", "front"), ("mer", "chant"),
         ("Shop", "ify"), ("Woo", "Commerce"), ("reve", "nue"), ("check", "out"), ("S", "KU")]
BANNED = [a + b for a, b in _FRAG]

# Roman numerals I..XXIX — headroom past the current owners' Part counts without a
# self-flagging thirty-token literal; extend by one entry if a future Part passes this range.
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII",
         "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII", "XXIV",
         "XXV", "XXVI", "XXVII", "XXVIII", "XXIX"]

DENSITY_FLOOR = 1200


def _words(t: str) -> int:
    return len([w for w in t.split() if w])


def _infix(label: str) -> str:
    return label.upper().replace("_", "-")


def check(label: str, rel: str, header: str, law: str, min_parts: int
          ) -> list[tuple[str, bool, str]]:
    path = IAS_DIR / rel
    infix = _infix(label)
    if not path.exists():
        return [(f"V-{infix}-EXTPART-EXISTS", False, f"owner not found: {path}")]
    raw = path.read_text(encoding="utf-8")
    out: list[tuple[str, bool, str]] = []

    # Appended-Part existence: header line + its FINAL LAW.
    h = raw.find(header)
    lw = raw.find(law, h) if h != -1 else -1
    has_header, has_law = h != -1, lw != -1
    out.append((f"V-{infix}-EXTPART-EXISTS", has_header and has_law,
                f"header={has_header} final_law={has_law}"))

    # Appended-Part body: header through the divider that follows its FINAL LAW.
    block = ""
    if has_header and has_law:
        end = raw.find("\n===", lw)
        block = raw[h:end] if end != -1 else raw[h:]
    w = _words(block)
    out.append((f"V-{infix}-EXTPART-FLOOR", w >= DENSITY_FLOOR, f"{w} words (floor {DENSITY_FLOOR})"))

    # Contamination, scoped to the appended block (sealed cores carry legitimate vocabulary a
    # whole-file strict scan would false-positive on).
    low = block.lower()
    hits = [b for b in BANNED if b.lower() in low]
    out.append((f"V-{infix}-EXTPART-CONTAM", not hits,
                "clean" if not hits else f"{len(hits)} banned literal class(es)"))

    # Whole-file integrity: contiguous Parts I..N, each closed by a matching FINAL LAW.
    declared = 0
    for r in ROMAN:
        if re.search(rf"(?m)^PART {r} —", raw):
            declared += 1
        else:
            break
    laws = sum(1 for r in ROMAN[:declared] if re.search(rf"(?m)^FINAL LAW — PART {r}\.", raw))
    out.append((f"V-{infix}-INTEGRITY", declared >= min_parts and declared == laws,
                f"{declared} Parts / {laws} FINAL LAWs (min {min_parts})"))
    return out


def main() -> int:
    passes = fails = 0
    for label, rel, header, law, min_parts in TARGETS:
        print(f"== {label} ==")
        for gate, ok, ev in check(label, rel, header, law, min_parts):
            print(f"  [{'OK  ' if ok else 'FAIL'}] {gate}: {ev}")
            if ok:
                passes += 1
            else:
                fails += 1
    print(f"\nIAS_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
