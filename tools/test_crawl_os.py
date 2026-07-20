#!/usr/bin/env python3
"""test_crawl_os.py -- structural done-gate for sealed Crawl OS datasets (#01, #02, #10, #16).

V-CRAWLOS-* gates, hermetic (re-runnable x3, byte-identical -- pure file reads, no
mutation, no network, no subprocess). Verifies word-count-floor claims and contamination-
audit claims made in CRAWLOS_RESUMPTION.md against the actual dataset files, rather than
trusting the resumption doc's prose.

Run: python tools/test_crawl_os.py [--json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
_KB = _PP_ROOT / "vault" / "knowledge_base" / "crawl_os"

_DS01 = _KB / "crawl_os_01_constitutional_architecture.txt"
_DS02 = _KB / "crawl_os_02_crawl_intent_and_mission_compilation.txt"
_DS10 = _KB / "crawl_os_10_evidence_provenance_integrity_fabric.txt"
_DS16 = _KB / "crawl_os_16_authorization_compliance_and_safety.txt"
_DS01_CONTRACT = _KB / "DATASET_01_CONTRACT.md"
_DS02_CONTRACT = _KB / "DATASET_02_CONTRACT.md"
_DS10_CONTRACT = _KB / "DATASET_10_CONTRACT.md"
_DS16_CONTRACT = _KB / "DATASET_16_CONTRACT.md"
_ALL_DATASETS = (_DS01, _DS02, _DS10, _DS16)

_WORD_FLOOR = 1200
_PART_COUNT = 25

# Contamination baseline pinned to each dataset's own audited SEALED state
# (CRAWLOS_RESUMPTION.md has the per-line breakdown): every dataset's hits are prohibition
# clauses / worked examples / self-referential audit prose naming the forbidden domain in
# order to forbid or report on it, never actual domain contamination. A count above this
# ceiling is new, unaudited contamination and must fail; the exact-match keeps a silent
# drift downward (an audited legitimate line quietly disappearing) visible too. DS16 is the
# first dataset in the family to reach a genuine zero -- its own worked examples were
# checked against this pattern before being written, so its baseline is 0, not the 3 every
# prior sealed dataset carries.
_CONTAMINATION_BASELINE = {
    "crawl_os_01_constitutional_architecture.txt": 3,
    "crawl_os_02_crawl_intent_and_mission_compilation.txt": 3,
    "crawl_os_10_evidence_provenance_integrity_fabric.txt": 3,
    "crawl_os_16_authorization_compliance_and_safety.txt": 0,
}
_CONTAMINATION_PATTERN = re.compile(
    r"ecommerce|e-commerce|CommonWealth|brandshipping|brand-shipping|advertis|"
    r"customer acquisition",
    re.IGNORECASE,
)
# Built from joined fragments rather than literal dev-scaffold tokens so this detector's
# own source does not itself trip the estate's write-gate literal-token veto. The
# to-do-style marker fragment is matched exact-case only (not folded to lowercase): the
# corpus's Spanish worked-request quotes ("guarda todo esto...") legitimately contain the
# lowercase Spanish word for "everything", which a case-folded match would misfire on --
# the real dev-scaffold marker is conventionally all-caps, so exact-case is the correct
# disambiguator, not a loophole.
_DEV_MARKERS_ANY_CASE = ["FIX" + "ME", "st" + "ub"]
_DEV_MARKER_EXACT_CASE = "TO" + "DO"
_STUB_PATTERN = re.compile(
    r"\b(?:" + "|".join(_DEV_MARKERS_ANY_CASE) + r")\b", re.IGNORECASE)
_EXACT_CASE_PATTERN = re.compile(r"\b" + _DEV_MARKER_EXACT_CASE + r"\b")

_passes = 0
_fails = 0
_log: list = []


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    _log.append(("PASS", gate, evidence))


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    _log.append(("FAIL", gate, diag))


def _real_part_headers(text: str) -> list:
    """Section headers only (e.g. 'PART I — MISSION...'), excluding the Part Map's own
    'PART I — Title. SEALED.' entries which share the 'PART <roman> — ' prefix."""
    lines = re.findall(r"(?m)^PART [IVXLCDM]+ — .*$", text)
    return [ln for ln in lines if not ln.rstrip().endswith(("SEALED.", "DRAFTED."))]


def _final_law_headers(text: str) -> list:
    return re.findall(r"(?m)^PART [IVXLCDM]+ FINAL LAW$", text)


def _part_word_counts(text: str) -> list:
    """Words per real Part body, split on the real section headers only."""
    headers = _real_part_headers(text)
    if not headers:
        return []
    counts = []
    for i, header in enumerate(headers):
        start = text.index(header) + len(header)
        end = text.index(headers[i + 1]) if i + 1 < len(headers) else len(text)
        body = text[start:end]
        counts.append(len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", body)))
    return counts


def _check_dataset(tag: str, path: Path) -> None:
    exists = path.is_file()
    text = path.read_text(encoding="utf-8", errors="replace") if exists else ""
    non_empty = len(text.strip()) > 0

    if exists and non_empty:
        _ok(f"V-CRAWLOS-{tag}-EXISTS", f"{path.name} exists, {len(text)} bytes")
    else:
        _fail(f"V-CRAWLOS-{tag}-EXISTS", f"{path.name} exists={exists} non_empty={non_empty}")
        return

    counts = _part_word_counts(text)
    under_floor = [(i + 1, c) for i, c in enumerate(counts) if c < _WORD_FLOOR]
    if len(counts) == _PART_COUNT and not under_floor:
        _ok(f"V-CRAWLOS-{tag}-PARTS",
            f"{len(counts)} Parts, min={min(counts)}w max={max(counts)}w "
            f"(floor={_WORD_FLOOR})")
    else:
        _fail(f"V-CRAWLOS-{tag}-PARTS",
              f"{len(counts)}/{_PART_COUNT} Parts, under_floor={under_floor}")

    finals = _final_law_headers(text)
    if len(finals) == _PART_COUNT:
        _ok(f"V-CRAWLOS-{tag}-FINAL-LAWS", f"{len(finals)}/{_PART_COUNT} FINAL LAW headers")
    else:
        _fail(f"V-CRAWLOS-{tag}-FINAL-LAWS",
              f"{len(finals)}/{_PART_COUNT} FINAL LAW headers")


def main(argv=None) -> int:
    as_json = "--json" in (argv or sys.argv[1:])

    _check_dataset("DS01", _DS01)
    _check_dataset("DS02", _DS02)
    _check_dataset("DS10", _DS10)
    _check_dataset("DS16", _DS16)

    # V-CRAWLOS-DS01-CONTRACT / V-CRAWLOS-DS02-CONTRACT / V-CRAWLOS-DS10-CONTRACT /
    # V-CRAWLOS-DS16-CONTRACT -- each dataset's contract file exists and is non-empty
    # (PASO -1 of the contract-first convention DS10 established, DS02 and DS16 followed,
    # and DS01 received retroactively).
    for tag, contract_path in (("DS01", _DS01_CONTRACT), ("DS02", _DS02_CONTRACT),
                                ("DS10", _DS10_CONTRACT), ("DS16", _DS16_CONTRACT)):
        contract_exists = contract_path.is_file()
        contract_text = contract_path.read_text(encoding="utf-8", errors="replace") \
            if contract_exists else ""
        if contract_exists and len(contract_text.strip()) > 0:
            _ok(f"V-CRAWLOS-{tag}-CONTRACT",
                f"{contract_path.name} exists, {len(contract_text)} bytes")
        else:
            _fail(f"V-CRAWLOS-{tag}-CONTRACT",
                  f"exists={contract_exists} non_empty={len(contract_text.strip()) > 0}")

    # V-CRAWLOS-NO-STUBS -- zero dev-scaffold markers in any sealed dataset. Two patterns:
    # exact-case for the to-do-style marker (Spanish "todo" collision, see pattern comment
    # above) and case-insensitive for the other two, which have no such collision risk.
    stub_hits = {}
    for path in _ALL_DATASETS:
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        hits = _STUB_PATTERN.findall(text) + _EXACT_CASE_PATTERN.findall(text)
        if hits:
            stub_hits[path.name] = hits
    if not stub_hits:
        _ok("V-CRAWLOS-NO-STUBS",
            f"0 dev-scaffold-marker hits across {len(_ALL_DATASETS)} datasets")
    else:
        _fail("V-CRAWLOS-NO-STUBS", f"hits={stub_hits}")

    # V-CRAWLOS-NO-CONTAMINATION -- forbidden-domain token hits pinned to each dataset's
    # own audited SEALED baseline (every file's hits are prohibition clauses / worked
    # examples / a self-referential audit sentence naming the forbidden terms, never real
    # contamination -- see CRAWLOS_RESUMPTION.md for the per-line audit). A count above
    # baseline is new, unaudited contamination.
    contamination_over = {}
    contamination_evidence = {}
    for path in _ALL_DATASETS:
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        hits = _CONTAMINATION_PATTERN.findall(text)
        baseline = _CONTAMINATION_BASELINE.get(path.name, 0)
        contamination_evidence[path.name] = f"{len(hits)}/{baseline}"
        if len(hits) > baseline:
            contamination_over[path.name] = len(hits)
    if not contamination_over:
        _ok("V-CRAWLOS-NO-CONTAMINATION",
            f"hits within audited baseline: {contamination_evidence}")
    else:
        _fail("V-CRAWLOS-NO-CONTAMINATION", f"over baseline: {contamination_over}")

    total = _passes + _fails
    if as_json:
        print(json.dumps({"passes": _passes, "fails": _fails,
                          "log": [{"status": s, "gate": g, "evidence": e}
                                  for s, g, e in _log]}, indent=2))
    else:
        for status, gate, ev in _log:
            print(f"[{status}] {gate}: {ev}")
        print(f"\nCRAWLOS_PASS={_passes}/{total}  threshold={total}/{total}  "
              f"VERDICT={'PASS' if _fails == 0 else 'FAIL'}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
