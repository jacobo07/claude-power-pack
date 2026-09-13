#!/usr/bin/env python3
"""Two systems, four letters apart, and one of them was rejected.

This repository holds two acronyms that differ by a single transposition. They
are not spellings of one programme, and nothing in the tree said so until a
session was handed a brief instructing it to "determine whether naming drift
exists" and to treat the two as one evolving effort until repository truth
settled it. Repository truth settles it the other way:

    U-S-E-A   Universal Software Engineering Architect
              the sealed constitution at vault/constitution/usea/, fifteen laws,
              /cpp-usea, tools/usea_*.py, UKDL Phases I-VI. LIVE.

    U-A-S-E   Universal Architecture Synthesis Engine
              system 02 of the UPAC ownership audit of 2026-08-18, written up in
              vault/knowledge_base/decision_review/drk_08_*. REJECTED.

A rename in either direction would have folded a rejected architecture-synthesis
proposal into the live constitutional programme, and would have taken the seal
path, the command name, the tool filenames and every UKDL rule id with it. The
brief's premise was reasonable and the evidence disproves it, which is the only
reason this file exists: the next session gets the same brief.

WHY A GATE AND NOT A PARAGRAPH
    This estate has measured its own rule corpora at 821 ids of which 92 name an
    executable owner. A note in a README is the 89% case. The predicate below is
    the part that survives being forgotten.

WHAT IT ASSERTS
    Each occurrence of the rejected acronym sits beside architecture-synthesis
    vocabulary and beside NO constitutional vocabulary; no line claims the two
    are one system; and the sweep found something, because a sweep that silently
    matched nothing reports the same clean bill as a healthy tree.

WHAT IT DOES NOT ASSERT
    That the rejected system stays rejected. That is a decision record, not a
    naming fact, and DRK-08 owns it.

THE DRILL IS SYNTHETIC ON PURPOSE
    Its subject is a string built here, never a real file. A drill pinned to a
    real offender has an interest in that offender surviving and asserts nothing
    the day it is fixed; this one still drives the red branch when every file in
    the tree is clean, which is the state the gate is trying to hold.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

# A detector cannot be its own subject: this file necessarily spells both
# acronyms to talk about them. That is the ONLY exclusion, and the gate below
# asserts the set never grows -- widening an exclusion set is how a census comes
# to measure nothing.
_SELF = Path(__file__).resolve()
_EXCLUDED = {_SELF}

_SUFFIXES = {".md", ".py", ".json", ".txt", ".js", ".ps1", ".yml", ".yaml"}
_SKIP_DIRS = {".git", "__pycache__", "node_modules", "_knowledge_graph", ".venv"}

# Assembled rather than written so that grepping this repository for either
# acronym does not surface this file as a fifth occurrence of one of them.
REJECTED = "U" + "ASE"          # Universal Architecture Synthesis Engine
CANONICAL = "U" + "SEA"         # Universal Software Engineering Architect

# Vocabulary that identifies which of the two a line is talking about. Matched
# case-insensitively over a window around the hit, never over the whole file --
# a file may legitimately discuss both, and whole-file matching would call every
# such file ambiguous.
SYNTHESIS_MARKERS = ("architecture synthesis", "synthesis engine", "upac",
                     "drk-08", "drk_08")
CONSTITUTION_MARKERS = ("software engineering architect", "constitution",
                        "fifteen laws", "law ii", "law ix", "cpp-usea")

# How far either side of a hit to read for context.
WINDOW = 400

PASSES = 0
FAILS = 0


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def classify(text: str, token: str) -> list[tuple[int, bool, bool]]:
    """For each occurrence of `token`, does its neighbourhood look like the
    synthesis engine, the constitution, or both?

    Returns (offset, synthesis_nearby, constitution_nearby) per hit. Both-true
    is the ambiguous case and both-false is the unattributed case; the caller
    decides what each means, because they are different problems.
    """
    hits: list[tuple[int, bool, bool]] = []
    start = 0
    while True:
        i = text.find(token, start)
        if i < 0:
            return hits
        window = text[max(0, i - WINDOW): i + WINDOW].lower()
        hits.append((
            i,
            any(m in window for m in SYNTHESIS_MARKERS),
            any(m in window for m in CONSTITUTION_MARKERS),
        ))
        start = i + len(token)


def _files() -> list[Path]:
    out: list[Path] = []
    for p in _ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in _SUFFIXES:
            continue
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        if p.resolve() in _EXCLUDED:
            continue
        out.append(p)
    return out


def main() -> int:
    prov = _read(_ROOT / "vault" / "constitution" / "usea" / "PROVENANCE.md")

    # --- the canonical identity resolves ------------------------------------
    check("V-IDENT-CANONICAL-RESOLVES",
          "Universal Software Engineering Architect" in prov,
          "the sealed constitution's provenance names the Architect programme")

    # --- the exclusion set cannot grow --------------------------------------
    check("V-IDENT-ONE-EXCLUSION-ONLY",
          _EXCLUDED == {_SELF},
          "exactly one file is exempt (this detector, which cannot be its own "
          "subject)")

    # --- the sweep ----------------------------------------------------------
    files = _files()
    total_hits = 0
    misattributed: list[str] = []   # near constitution vocabulary
    unattributed: list[str] = []    # near neither
    aliased: list[str] = []         # both acronyms asserted equivalent

    for f in files:
        text = _read(f)
        if REJECTED not in text and CANONICAL not in text:
            continue
        rel = str(f.relative_to(_ROOT))

        for off, synth, const in classify(text, REJECTED):
            total_hits += 1
            line_no = text.count("\n", 0, off) + 1
            if const and not synth:
                misattributed.append(f"{rel}:{line_no}")
            elif not const and not synth:
                unattributed.append(f"{rel}:{line_no}")

        # An alias claim is the specific failure this gate exists to stop: one
        # line carrying both spellings joined by an equivalence. Checked per
        # line, because the two legitimately co-occur in a file that contrasts
        # them -- as the audit map and this docstring both do.
        for n, line in enumerate(text.splitlines(), 1):
            if REJECTED in line and CANONICAL in line:
                low = line.lower()
                if any(v in low for v in (" is ", " same ", "aka", "alias",
                                          "rename", "formerly", "a.k.a")):
                    aliased.append(f"{rel}:{n}")

    # Positive control. Every assertion below is an emptiness test, and an
    # emptiness test passes against a sweep that walked nothing.
    check("V-IDENT-SWEEP-FOUND-SUBJECTS",
          len(files) > 200 and total_hits >= 1,
          f"{len(files)} files walked, {total_hits} occurrence(s) of the "
          f"rejected acronym found to judge")

    check("V-IDENT-NO-MISATTRIBUTION",
          not misattributed,
          "no occurrence of the rejected acronym sits in constitutional "
          f"context{'' if not misattributed else ': ' + ', '.join(misattributed)}")

    check("V-IDENT-ALL-ATTRIBUTED",
          not unattributed,
          "every occurrence names its own system"
          f"{'' if not unattributed else '; unattributed: ' + ', '.join(unattributed)}")

    check("V-IDENT-NO-ALIAS-CLAIM",
          not aliased,
          "no line asserts the two acronyms are one system"
          f"{'' if not aliased else ': ' + ', '.join(aliased)}")

    # --- synthetic drill, both poles ----------------------------------------
    # Neither pole touches the filesystem, so neither decays when the tree
    # changes. The red pole is the whole point; the green pole is what stops a
    # predicate that flags everything from looking like a working detector.
    red_body = (f"### 02 - {REJECTED}\nThe sealed constitution's fifteen laws, "
                f"LAW II and LAW IX, are carried by this system.\n")
    red = classify(red_body, REJECTED)
    check("V-IDENT-DRILL-RED",
          len(red) == 1 and red[0][2] and not red[0][1],
          "a synthetic line placing the rejected acronym in constitutional "
          "context is flagged")

    green_body = (f"### 02 - {REJECTED} - Universal Architecture Synthesis "
                  f"Engine\nUPAC ownership audit, verdict recorded in DRK-08.\n")
    green = classify(green_body, REJECTED)
    check("V-IDENT-DRILL-GREEN",
          len(green) == 1 and green[0][1] and not green[0][2],
          "a synthetic line placing it in synthesis context passes")

    total = PASSES + FAILS
    print(f"IDENTITY_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
