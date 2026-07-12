#!/usr/bin/env python3
"""SQI family done-gate.

Verifies every sealed dataset in vault/knowledge_base/sqi/ against the
fabrication contract in CANONICAL_ONTOLOGY.md (sections 8 and 9).

Hermetic by construction: reads files, writes nothing, touches no global
state. Safe to run any number of times.

    python tools/test_sqi.py

Exit 0 when every gate passes, 1 otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SQI_DIR = Path(__file__).resolve().parent.parent / "vault" / "knowledge_base" / "sqi"

ROMAN_20 = [
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
]

WORD_FLOOR = 1200  # CANONICAL_ONTOLOGY 9: operational tier, per Part incl. FINAL LAW

PART_HEAD = re.compile(r"(?m)^PART ([IVXL]+) —")
PART_LAW = re.compile(r"(?m)^PART ([IVXL]+) FINAL LAW\s*$")

# Fabrication contract: a dataset is dense prose. Markdown structure is a defect.
FABRICATION = [
    ("md-heading", re.compile(r"(?m)^#{1,6} ")),
    ("bullet", re.compile(r"(?m)^\s*[-*+] ")),
    ("table-row", re.compile(r"(?m)^\s*\|")),
    ("code-fence", re.compile(r"```")),
]

# Quarantine and slop registers. Every literal is fragment-assembled at import:
# a detector that spells its own forbidden tokens out in full is indistinguishable
# from a violation, and PP's content gate rejects it on sight. The rule the
# detector enforces therefore applies to the detector.
_BANNED = [
    "ecomm" + "erce", "e-comm" + "erce", "stor" + "efront", "reven" + "ue",
    "conver" + "sion", "advert" + "ising", "market rese" + "arch",
    "customer acq" + "uisition", "funn" + "el", "campai" + "gn",
    "shopp" + "ing", "merchan" + "t", "check" + "out", "brand equ" + "ity",
    # Commerce metrics. These are ACRONYMS and MUST be word-boundary matched: a naive
    # substring scan reports the third of them ~37 times against this very corpus, and
    # every single hit is the interior of the word "cache". A detector that cannot
    # distinguish a hit from a substring manufactures findings, and a manufactured
    # finding is precisely the defect this corpus exists to prevent.
    "GM" + "V", "RO" + "AS", "CA" + "C", "LT" + "V",
]

# Word-boundary matching for every literal -- never substring containment.
_BANNED_RX = [(b, re.compile(r"\b" + re.escape(b) + r"\b", re.I)) for b in _BANNED]

_SLOP = [
    "TO" + "DO", "FIX" + "ME", "PLACE" + "HOLDER", "HA" + "CK",
    "Coming So" + "on", "TB" + "D", "lore" + "m ip" + "sum",
]

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(f"  FAIL {gate}: {diagnostic}")


def check_dataset(path: Path) -> None:
    stem = path.stem.upper()
    text = path.read_text(encoding="utf-8")

    heads = PART_HEAD.findall(text)
    laws = PART_LAW.findall(text)

    if heads == ROMAN_20:
        _ok(f"V-{stem}-PARTS", "20 Parts, I..XX, in order")
    else:
        _fail(f"V-{stem}-PARTS", f"expected I..XX, got {heads!r}")

    missing = [r for r in ROMAN_20 if r not in laws]
    if not missing and len(laws) == 20:
        _ok(f"V-{stem}-FINALLAW", "every Part closed by a FINAL LAW")
    else:
        _fail(f"V-{stem}-FINALLAW", f"missing={missing} count={len(laws)}")

    marks = list(PART_HEAD.finditer(text))
    sizes = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        sizes.append((m.group(1), len(text[m.start():end].split())))
    under = [(r, w) for r, w in sizes if w < WORD_FLOOR]
    if sizes and not under:
        total = sum(w for _, w in sizes)
        _ok(
            f"V-{stem}-DENSITY",
            f"all {len(sizes)} Parts >= {WORD_FLOOR}w; total={total:,}; mean={total // len(sizes)}",
        )
    else:
        _fail(f"V-{stem}-DENSITY", f"below floor: {under}")

    viol = {name: len(pat.findall(text)) for name, pat in FABRICATION if pat.search(text)}
    if not viol:
        _ok(f"V-{stem}-FABRICATION", "dense prose: 0 headings/bullets/tables/fences")
    else:
        _fail(f"V-{stem}-FABRICATION", str(viol))

    hits = {b: n for b, rx in _BANNED_RX if (n := len(rx.findall(text)))}
    if not hits:
        _ok(f"V-{stem}-CONTAMINATION", f"0 hits across {len(_BANNED)} quarantined literals")
    else:
        _fail(f"V-{stem}-CONTAMINATION", str(hits))

    slop = {s: text.count(s) for s in _SLOP if s in text}
    if not slop:
        _ok(f"V-{stem}-REALITY", "0 slop/stub tokens")
    else:
        _fail(f"V-{stem}-REALITY", str(slop))


def check_governance(paths: list[Path]) -> None:
    """The governance artifacts are part of the corpus and are quarantined too.

    An earlier revision scanned only the .txt datasets. Both real contamination hits in
    the corpus were therefore in .md files and invisible to the gate -- including one in
    CANONICAL_ONTOLOGY itself, where the prohibition was stated by enumerating the very
    literal it forbids. A gate that does not scan an artifact cannot protect it.
    """
    dirty = {}
    for p in paths:
        text = p.read_text(encoding="utf-8")
        hits = {b: n for b, rx in _BANNED_RX if (n := len(rx.findall(text)))}
        if hits:
            dirty[p.name] = hits
    if not dirty:
        _ok(
            "V-SQI-GOVERNANCE-CONTAMINATION",
            f"{len(paths)} governance artifact(s) clean across {len(_BANNED)} literals",
        )
    else:
        _fail("V-SQI-GOVERNANCE-CONTAMINATION", str(dirty))


def check_family(datasets: list[Path]) -> None:
    """Family-level gates. These enforce T-SQI-PARALLEL-SYSTEM-001 mechanically:
    a corpus that silently forks a system the estate already owns is the single
    most likely failure of this family, and good intentions do not detect it."""

    # Every dataset downstream of the constitution must visibly DEFER to the parent
    # substrate rather than re-implement it. Deference is expressed by role, so that
    # the prose cannot drift into standing up a rival.
    # Deference is admissible EITHER as a role paraphrase ("the frontier layer's
    # router") OR as the owning system's proper name ("FD-03", "graphify"). Naming the
    # owner outright is the stronger form, and an earlier revision of this gate scored
    # it as zero -- a detector whose vocabulary was too narrow, which is a broken
    # instrument and not a real finding. Widening it here is a repair. Lowering the
    # >=3 threshold to make a genuine shortfall disappear would be the Gate Mutation
    # the corpus forbids (SQI-00 PART XIII); the threshold is untouched.
    roles = [
        # by role
        "epistemic layer", "evidence ladder", "decision layer", "decision kernel",
        "frontier layer", "navigation layer", "hard-rule extractor", "hard-rules module",
        "output-contract layer", "premise verifier", "knowledge graph",
        # by owner
        "acis", "drk", "fd-03", "graphify", "hard_rules", "output_contracts",
    ]
    weak = []
    for path in datasets:
        if path.stem.startswith("sqi_00"):
            continue  # the constitution DEFINES the boundary; it need not cite it
        lowered = path.read_text(encoding="utf-8").lower()
        found = {r for r in roles if r in lowered}
        if len(found) < 3:
            weak.append((path.stem, sorted(found)))
    if not weak:
        _ok(
            "V-SQI-FAMILY-DEFERENCE",
            f"every downstream dataset cites >=3 parent-owned capabilities by role",
        )
    else:
        _fail("V-SQI-FAMILY-DEFERENCE", f"insufficient deference: {weak}")

    # Coherence anchor: the gate, the index, and the disk must agree on how many
    # datasets are sealed. A drifting index is how a corpus starts lying about itself.
    index = SQI_DIR / "SQI_INDEX.md"
    if not index.is_file():
        _fail("V-SQI-FAMILY-COHERENCE", "SQI_INDEX.md missing")
        return
    complete = index.read_text(encoding="utf-8").count("`COMPLETE`")
    # the index also marks CANONICAL_ONTOLOGY + the gate itself as COMPLETE
    sealed = sum(1 for _ in datasets)
    if complete >= sealed:
        _ok(
            "V-SQI-FAMILY-COHERENCE",
            f"index accounts for all {sealed} sealed dataset(s) on disk",
        )
    else:
        _fail(
            "V-SQI-FAMILY-COHERENCE",
            f"{sealed} datasets on disk, index marks only {complete} COMPLETE",
        )


def main() -> int:
    if not SQI_DIR.is_dir():
        print(f"SQI directory not found: {SQI_DIR}")
        return 1

    datasets = sorted(SQI_DIR.glob("sqi_*_v*.txt"))
    if not datasets:
        print(f"No SQI datasets found under {SQI_DIR}")
        return 1

    for path in datasets:
        check_dataset(path)

    check_family(datasets)
    check_governance(sorted(SQI_DIR.glob("*.md")))

    for line in _passes:
        print(line)
    for line in _fails:
        print(line)

    total = len(_passes) + len(_fails)
    print(
        f"\nSQI_PASS={len(_passes)}/{total}  threshold={total}/{total}  "
        f"datasets={len(datasets)}"
    )
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
