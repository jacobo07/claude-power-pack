#!/usr/bin/env python3
"""V-XFC-* gates for vault/datasets/uwcp/external_failure_corpus.jsonl (UWCP assimilation X5).

Every external or local failure has a destination: a REGRESSION that names gates
existing in tools/test_*.py (stale-entry clause) with a valid evidence class, an
OWED slice, or an AVOIDED design decision with its reason. The red branch of the
validator is driven with synthetic entries, so a validator that stopped
validating cannot report a clean corpus.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.done_gate.strength_ladder import EVIDENCE_CLASSES  # noqa: E402

CORPUS = ROOT / "vault" / "datasets" / "uwcp" / "external_failure_corpus.jsonl"
REQUIRED = ("id", "source", "system", "symptom", "root_cause", "abstraction", "uwcp_exposure",
            "falsification", "status", "confidence")
STATUSES = ("REGRESSION", "OWED", "AVOIDED")
SLICE = re.compile(r"^(S\d+(-\d+[a-z]?)?|A\d+[a-z]?|X\d+)$")
MIN_ENTRIES = 20
passes = fails = 0


def check(gate, cond, good, bad):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {good}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {bad}")


def gate_ids() -> set[str]:
    ids = set()
    for f in (ROOT / "tools").glob("test_*.py"):
        if f.resolve() == Path(__file__).resolve():
            continue    # this file names synthetic gates; scanning it made them "exist"
        ids.update(re.findall(r'"(V-[A-Z0-9-]+)"', f.read_text(encoding="utf-8", errors="replace")))
    # gates whose names are built at runtime (the TLA gate derives them from cfg names)
    tla = ROOT / "tools" / "test_uwcp_tla.py"
    if tla.is_file():
        for cfg in re.findall(r'"(UWCP[\w]*)\.cfg"', tla.read_text(encoding="utf-8")):
            base = "V-TLA-" + cfg.upper().replace("_", "-")
            ids.update({base, base + "-MECHANISM"})
    return ids


def problems(entry: dict, known_gates: set[str]) -> list[str]:
    p = [f"missing {k}" for k in REQUIRED if not str(entry.get(k, "")).strip()]
    st = entry.get("status")
    if st not in STATUSES:
        return p + [f"status {st!r} not in {STATUSES}"]
    if st == "REGRESSION":
        regs = entry.get("regression") or []
        if not regs:
            p.append("REGRESSION with no gate")
        p += [f"gate {g} does not exist in tools/test_*.py" for g in regs if g not in known_gates]
        if entry.get("evidence_class") not in EVIDENCE_CLASSES:
            p.append(f"evidence_class {entry.get('evidence_class')!r} not a known class")
    if st == "OWED" and not SLICE.match(str(entry.get("owed_slice", ""))):
        p.append(f"OWED without a slice id (got {entry.get('owed_slice')!r})")
    if entry.get("owed_slice") and not SLICE.match(str(entry["owed_slice"])):
        p.append(f"owed_slice {entry['owed_slice']!r} is not a slice id")
    if st == "AVOIDED" and len(str(entry.get("reason", "")).strip()) < 20:
        p.append("AVOIDED without a reason someone can disagree with")
    return p


def main() -> int:
    known = gate_ids()
    lines = [ln for ln in CORPUS.read_text(encoding="utf-8").splitlines() if ln.strip()]
    entries, parse_err = [], []
    for i, ln in enumerate(lines, 1):
        try:
            entries.append(json.loads(ln))
        except ValueError as exc:
            parse_err.append(f"line {i}: {exc}")
    check("V-XFC-PARSES", not parse_err, f"{len(entries)} entries parse", f"{parse_err}")
    check("V-XFC-FLOOR", len(entries) >= MIN_ENTRIES, f"{len(entries)} >= {MIN_ENTRIES} entries",
          f"only {len(entries)}: the corpus may have lost entries")
    ids = [e.get("id") for e in entries]
    check("V-XFC-UNIQUE-IDS", len(ids) == len(set(ids)), "ids are unique", f"duplicates in {ids}")
    bad = {e.get("id"): problems(e, known) for e in entries}
    bad = {k: v for k, v in bad.items() if v}
    check("V-XFC-DESTINATION", not bad, "every entry has a valid destination", f"{bad}")
    counts = {s: sum(e.get("status") == s for e in entries) for s in STATUSES}
    check("V-XFC-MIX", counts["REGRESSION"] >= 1 and counts["OWED"] >= 1,
          f"status mix {counts}", f"{counts}")

    # red branch, synthetic entries (never a real one, so fixing the corpus cannot disarm it)
    base = {k: "x" * 25 for k in REQUIRED}
    synth = {
        "no-gate": {**base, "status": "REGRESSION", "regression": [], "evidence_class": "LOCAL_REALITY"},
        "stale-gate": {**base, "status": "REGRESSION", "regression": ["V-NOPE-NEVER"],
                       "evidence_class": "LOCAL_REALITY"},
        "bad-class": {**base, "status": "REGRESSION", "regression": sorted(known)[:1],
                      "evidence_class": "PROVEN"},
        "owed-no-slice": {**base, "status": "OWED"},
        "avoided-no-reason": {**base, "status": "AVOIDED", "reason": "because"},
        "bad-status": {**base, "status": "FIXED"},
        "missing-field": {k: v for k, v in {**base, "status": "OWED", "owed_slice": "A6"}.items()
                          if k != "root_cause"},
    }
    caught = {k: bool(problems(v, known)) for k, v in synth.items()}
    check("V-XFC-VALIDATOR-RED", all(caught.values()), f"all {len(synth)} malformed synthetic entries refused",
          f"not refused: {[k for k, v in caught.items() if not v]}")
    good = {**base, "status": "OWED", "owed_slice": "S1-8d"}
    check("V-XFC-VALIDATOR-GREEN", not problems(good, known), "a well-formed synthetic entry passes",
          f"{problems(good, known)}")
    print(f"XFC_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
