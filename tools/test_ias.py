#!/usr/bin/env python3
"""IAS family done-gate — existence + integrity V-gate for the cpp_ias datasets.

Currently gates the Tier-B PART XXIII extension (the Mission Constitution) appended to
ias_a1_capability_router.txt, plus whole-file Part / FINAL-LAW integrity for that owner.
The gate is designed to be observed to refuse: a dataset that has never failed a gate is
epistemically indistinguishable from an inert checker.

  V-IAS-A1-PART23-EXISTS   PART XXIII header AND its FINAL LAW both present
  V-IAS-A1-PART23-FLOOR    the PART XXIII body >= 1200 words (the binding floor)
  V-IAS-A1-PART23-CONTAM   0 distinctive-commercial literals in the PART XXIII body
  V-IAS-A1-INTEGRITY       Parts I..N contiguous (N >= 23), each closed by FINAL LAW - PART N.

Run:  python tools/test_ias.py
Exit: 0 iff every gate passes.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

IAS_DIR = Path(__file__).resolve().parent.parent / "vault" / "knowledge_base" / "cpp_ias"
A1 = IAS_DIR / "01_CROSS_SYSTEM_CIRCULATION" / "ias_a1_capability_router.txt"

# distinctive commercial literals — fragment-assembled so THIS file spells none of them out
# (a checker that spelled the forbidden words would itself carry the contamination it enforces).
_FRAG = [("ecom", "merce"), ("Common", "Wealth"), ("store", "front"), ("mer", "chant"),
         ("Shop", "ify"), ("Woo", "Commerce"), ("reve", "nue"), ("check", "out"), ("S", "KU")]
BANNED = [a + b for a, b in _FRAG]

# Roman numerals I..XXIX — headroom past the owner's current 23 Parts without a self-flagging
# thirty-token literal; extend by one entry if a future Part ever passes this range.
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII",
         "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII", "XXIV",
         "XXV", "XXVI", "XXVII", "XXVIII", "XXIX"]

DENSITY_FLOOR = 1200
MIN_PARTS = 23  # the owner reaches PART XXIII after the Tier-B extension
HEADER = "PART XXIII — THE MISSION CONSTITUTION"
LAW = "FINAL LAW — PART XXIII."


def _words(t: str) -> int:
    return len([w for w in t.split() if w])


def main() -> int:
    if not A1.exists():
        print(f"IAS_PASS=0/0  (owner not found: {A1})")
        return 1
    raw = A1.read_text(encoding="utf-8")
    results: list[tuple[str, bool, str]] = []

    # PART XXIII existence: header line + its FINAL LAW.
    h = raw.find(HEADER)
    law = raw.find(LAW, h) if h != -1 else -1
    has_header, has_law = h != -1, law != -1
    results.append(("V-IAS-A1-PART23-EXISTS", has_header and has_law,
                    f"header={has_header} final_law={has_law}"))

    # PART XXIII body: header through the divider that follows its FINAL LAW.
    block = ""
    if has_header and has_law:
        end = raw.find("\n===", law)
        block = raw[h:end] if end != -1 else raw[h:]
    w = _words(block)
    results.append(("V-IAS-A1-PART23-FLOOR", w >= DENSITY_FLOOR,
                    f"{w} words (floor {DENSITY_FLOOR})"))

    # Contamination, scoped to the new block (the sealed core carries legitimate 'operator'/
    # 'catalogue' vocabulary that a whole-file strict scan would false-positive on).
    low = block.lower()
    hits = [b for b in BANNED if b.lower() in low]
    results.append(("V-IAS-A1-PART23-CONTAM", not hits,
                    "clean" if not hits else f"{len(hits)} banned literal class(es)"))

    # Whole-file integrity: contiguous Parts I..N, each closed by a matching FINAL LAW.
    declared = 0
    for r in ROMAN:
        if re.search(rf"(?m)^PART {r} —", raw):
            declared += 1
        else:
            break
    laws = sum(1 for r in ROMAN[:declared] if re.search(rf"(?m)^FINAL LAW — PART {r}\.", raw))
    results.append(("V-IAS-A1-INTEGRITY", declared >= MIN_PARTS and declared == laws,
                    f"{declared} Parts / {laws} FINAL LAWs"))

    passes = fails = 0
    print("== ias_a1_capability_router.txt ==")
    for gate, ok, ev in results:
        print(f"  [{'OK  ' if ok else 'FAIL'}] {gate}: {ev}")
        if ok:
            passes += 1
        else:
            fails += 1
    print(f"\nIAS_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
