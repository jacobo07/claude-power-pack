#!/usr/bin/env python3
"""DAIF family done-gate — V-gate runner for the Duplicate-to-Advantage Institutional Fabric.

Reproducible, hermetic. Verifies every authored DAIF dataset against the inherited SQI
fabrication contract (see vault/knowledge_base/d2a_fabric/DAIF_INDEX.md):

  V-DAIF-PARTS        every dataset opens Part I..N in order, each closed by a FINAL LAW
  V-DAIF-FINALLAW     Part count == FINAL LAW count (no Part left unclosed)
  V-DAIF-DENSITY      every Part >= 1200 words (the binding floor; target 1350-1500)
  V-DAIF-FABRICATION  0 markdown headings, 0 code fences, 0 bullet lists inside a dataset
  V-DAIF-CONTAMINATION 0 hits across the quarantined commercial literals (fragment-assembled here)
  V-DAIF-NONDUP       the dataset references at least one existing parent system by name

Run:  python tools/test_daif.py           (all DAIF datasets found on disk)
Exit: 0 iff every gate passes for every dataset; non-zero on any refusal.

The gate is designed to be *observed to refuse*: a dataset that has never failed a gate is
epistemically indistinguishable from an inert checker (SQI-00 Part XX). Density and contamination
have both fired during authoring (Part I landed at 1073w and was raised; 'catalogued'/'stored'
substrings were caught) — this runner is the durable form of those checks.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent.parent / "vault" / "knowledge_base" / "d2a_fabric"

# Quarantined commercial literals — fragment-assembled so THIS file carries zero spelled-out hits
# (a checker that spells the forbidden words would itself fail the contamination scan it enforces).
_FRAG = [
    ("ecom", "merce"), ("Shop", "ify"), ("Woo", "Commerce"), ("Str", "ipe"),
    ("Common", "Wealth"), ("CW", " Ops"), ("S", "KU"), ("mer", "chant"),
    ("reve", "nue"), ("cata", "log"), ("store", "front"), ("oper", "ator"),
    ("stor", "e"), ("sh", "op"),
]
BANNED = [a + b for a, b in _FRAG]

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
         "XXI", "XXII", "XXIII", "XXIV", "XXV"]

# At least one of these named parents must appear — DAIF composes, never re-narrates in a vacuum.
PARENTS = ["D2A", "SQI", "DRK", "FD", "ACIS", "CO-", "GK", "PM", "one_shot",
           "owner_queue", "liveness", "UKDL", "graphify", "hard_rules"]

DENSITY_FLOOR = 1200


def _words(text: str) -> int:
    return len(text.split())


def check_dataset(path: Path) -> tuple[list[tuple[str, bool, str]], int, int]:
    raw = path.read_text(encoding="utf-8")
    results: list[tuple[str, bool, str]] = []

    # Discover how many Parts this dataset declares (contiguous from I).
    declared = 0
    for r in ROMAN:
        if re.search(rf"(?m)^PART {r} —", raw) or re.search(rf"(?m)^PART {r} \-", raw):
            declared += 1
        else:
            break

    final_laws = len(re.findall(r"(?m)^PART [IVXLC]+ FINAL LAW\.", raw))
    results.append(("V-DAIF-FINALLAW", declared > 0 and declared == final_laws,
                    f"{declared} Parts / {final_laws} FINAL LAWs"))

    # Density per Part.
    short = []
    for r in ROMAN[:declared]:
        m = re.search(rf"(?s)PART {r} [—\-].*?PART {r} FINAL LAW\.", raw)
        w = _words(m.group(0)) if m else 0
        if w < DENSITY_FLOOR:
            short.append(f"{r}={w}")
    results.append(("V-DAIF-DENSITY", not short,
                    "all Parts >= 1200w" if not short else "under floor: " + ", ".join(short)))
    results.append(("V-DAIF-PARTS", declared > 0, f"{declared} Parts declared in order"))

    fences = raw.count("```")
    headings = len(re.findall(r"(?m)^#{1,6}\s", raw))
    bullets = len(re.findall(r"(?m)^\s*[-*]\s", raw))
    results.append(("V-DAIF-FABRICATION", fences == 0 and headings == 0 and bullets == 0,
                    f"fences={fences} headings={headings} bullets={bullets}"))

    low = raw.lower()
    hits = [b for b in BANNED if b.lower() in low]
    results.append(("V-DAIF-CONTAMINATION", not hits,
                    "clean" if not hits else f"{len(hits)} banned literal class(es) present"))

    refs = [p for p in PARENTS if p in raw]
    results.append(("V-DAIF-NONDUP", len(refs) > 0,
                    f"references {len(refs)} parent system(s)"))

    return results, declared, final_laws


def main() -> int:
    datasets = sorted(DATASET_DIR.glob("daif_*_v1.txt"))
    if not datasets:
        print("DAIF_PASS=0/0  (no daif_*_v1.txt datasets found yet)")
        return 0

    passes = fails = 0
    for ds in datasets:
        results, declared, _ = check_dataset(ds)
        print(f"\n== {ds.name}  ({declared} Parts) ==")
        for gate, ok, ev in results:
            tag = "OK  " if ok else "FAIL"
            print(f"  [{tag}] {gate}: {ev}")
            if ok:
                passes += 1
            else:
                fails += 1

    print(f"\nDAIF_PASS={passes}/{passes + fails}  datasets={len(datasets)}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
