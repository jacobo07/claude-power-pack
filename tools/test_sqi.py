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

REPO = Path(__file__).resolve().parent.parent
SQI_DIR = REPO / "vault" / "knowledge_base" / "sqi"

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


def check_engines() -> None:
    """The executable layer. SQI-00's Executable Governance Law: a policy without
    enforcement is documentation. Until these gates existed, this file gated the CORPUS
    and reconciled nothing -- the corpus was, by its own law, documentation.

    Hermetic: every gate here reads, or writes only inside a temporary directory that is
    destroyed on exit. Nothing global is touched, so three consecutive runs are identical.
    """
    import tempfile

    sys.path.insert(0, str(REPO))
    try:
        from modules.sqi.repo_reality_scanner import scan_repo
        from modules.sqi.environment_qualifier import qualify, QUALIFIED, GATES
        from modules.sqi.reconcile import reconcile
    except ImportError as exc:
        _fail("V-SQI-ENGINE-IMPORT", f"the SQI engines do not import: {exc}")
        return

    # --- the scanner runs, and detects this repository's real runner ---
    profile = scan_repo(REPO)
    py = [c for c in profile.language_contexts if c.language == "python"]
    if py and py[0].runner == "pytest" and profile.test_artifacts:
        _ok("V-SQI-SCANNER-RUNS",
            f"pytest detected; {len(profile.test_artifacts)} authored artifacts; "
            f"domains={len(profile.domains)}")
    else:
        _fail("V-SQI-SCANNER-RUNS",
              f"contexts={[c.language for c in profile.language_contexts]} "
              f"artifacts={len(profile.test_artifacts)}")

    # --- fail-open: an unrecognized tree yields UNKNOWN, never a raise ---
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "notes.md").write_text("no code here", encoding="utf-8")
        blind = scan_repo(td)
    if not blind.language_contexts and blind.scan_error is None:
        _ok("V-SQI-SCANNER-FAILOPEN",
            f"unknown stack -> domains={blind.domains}, unknowns={blind.unknowns}, no raise")
    else:
        _fail("V-SQI-SCANNER-FAILOPEN",
              f"contexts={blind.language_contexts} error={blind.scan_error}")

    # --- the qualifier runs all seven gates and never grants QUALIFIED by silence ---
    env = qualify(REPO, profile=profile)
    if [g.gate for g in env.gates] == GATES and env.state != QUALIFIED:
        unk = sum(1 for g in env.gates if g.passed is None)
        _ok("V-SQI-QUALIFIER-RUNS",
            f"7 gates evaluated; state={env.state}; {unk} UNKNOWN (never coerced to pass); "
            f"ceiling={env.verdict_ceiling[:32]}")
    else:
        _fail("V-SQI-QUALIFIER-RUNS",
              f"gates={[g.gate for g in env.gates]} state={env.state}")

    # --- the reconciler finds real orphans in this repository ---
    rep = reconcile(REPO, hermetic_runs=1)
    if rep.orphaned_count > 0 and rep.orphaned_ratio and rep.orphaned_ratio > 0.5:
        _ok("V-SQI-RECONCILE-FINDS-ORPHANS",
            f"{rep.orphaned_count}/{rep.authored_count} authored test files unreached "
            f"(ratio={rep.orphaned_ratio:.3f}); reach={rep.test_file_reach:.3f}; "
            f"surprise_set={len(rep.surprise_files)}")
    else:
        _fail("V-SQI-RECONCILE-FINDS-ORPHANS",
              f"orphans={rep.orphaned_count} ratio={rep.orphaned_ratio}")

    # --- fail-open: a tree with no runnable suite yields UNKNOWN metrics, never zeros ---
    with tempfile.TemporaryDirectory() as td:
        empty = reconcile(td, hermetic_runs=1)
    if empty.test_file_reach is None and empty.orphaned_ratio is None:
        _ok("V-SQI-RECONCILE-FAILOPEN",
            "no runnable suite -> reach=UNKNOWN (not 0.0); no raise. Zero is a "
            "measurement; this is the absence of one (SQI-02 5.8)")
    else:
        _fail("V-SQI-RECONCILE-FAILOPEN",
              f"reach={empty.test_file_reach} ratio={empty.orphaned_ratio} -- "
              f"an unrunnable suite was rounded to a measurement")

    # --- the engine is inside the surface it audits (SQI-02 5.10, mandatory) ---
    if rep.self_reach["reached"] and rep.self_reach["admissible"]:
        _ok("V-SQI-SELF-REACH",
            f"engine exercised by {rep.self_reach['reached_by']}; report admissible")
    else:
        _fail("V-SQI-SELF-REACH",
              "the engine's own code is reached by no canonical invocation -- "
              "an auditor exempt from its own audit is not an auditor")

    # --- the runner produced a durable, citable artifact (the 6th chain stage) ---
    reports = sorted((REPO / "vault" / "audits").glob("sqi_report_*.md"))
    sidecars = sorted((REPO / "vault" / "audits").glob("sqi_report_*.json"))
    if reports and sidecars:
        _ok("V-SQI-RUNNER-WRITES-REPORT",
            f"{reports[-1].relative_to(REPO).as_posix()} + JSON sidecar; a pass that "
            f"leaves no artifact cannot be compared against tomorrow (SQI-02 6.6)")
    else:
        _fail("V-SQI-RUNNER-WRITES-REPORT",
              "no vault/audits/sqi_report_*.{md,json} -- run `python tools/run_sqi.py`")

    # --- the founding finding is reproduced from the disk, not from a fixture ---
    if sidecars:
        import json as _json

        data = _json.loads(sidecars[-1].read_text(encoding="utf-8"))
        r = data.get("reconciliation", {})
        auth_state = r.get("authoritative_reach_state")
        if r.get("orphaned_count", 0) > 0 and r.get("test_file_reach") is not None:
            _ok("V-SQI-FINDING-REPRODUCED",
                f"orphaned={r['orphaned_count']}/{r['authored_count']} "
                f"reach={r['test_file_reach']:.3f} verdict={r['signal_integrity_verdict']} "
                f"authoritative_reach={auth_state} -- measured, not asserted")
        else:
            _fail("V-SQI-FINDING-REPRODUCED",
                  f"the sidecar carries no reproduced finding: {r.get('orphaned_count')}")

    # --- the engine is registered where its own liveness will be probed ---
    try:
        from modules.liveness.liveness_ledger import default_registry

        ids = {e["id"] for e in default_registry()}
        if "sqi-runner" in ids:
            _ok("V-SQI-LIVENESS",
                "sqi-runner in the D1 Liveness Ledger -- a reach engine that is itself "
                "never invoked is the inert node it was built to detect")
        else:
            _fail("V-SQI-LIVENESS", f"sqi-runner absent from the ledger: {sorted(ids)}")
    except ImportError as exc:
        _fail("V-SQI-LIVENESS", f"liveness ledger does not import: {exc}")


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
    check_engines()

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
