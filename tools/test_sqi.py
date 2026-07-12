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

    # Handed to the guardian gates so the reconciliation is paid for exactly once.
    return rep


def check_guardian(rep) -> None:
    """SQI-02 Part XII. The engines MEASURE; the guardian is the only one that can REFUSE.

    Every gate here writes only inside a temp directory. A guardian gate that touched the real
    vault/audits/sqi_baseline.json would ratchet it as a side effect of being run, and the suite
    would stop being hermetic on its own second execution.
    """
    import copy
    import json as _json
    import os
    import subprocess
    import tempfile

    try:
        from modules.sqi import baseline_guardian as G
    except ImportError as exc:
        _fail("V-GUARDIAN-IMPORT", f"the guardian does not import: {exc}")
        return

    ENV = "gate-env-key"

    def _write(tmp, snap, name="b.json"):
        p = Path(tmp) / name
        G.save_baseline(p, snap)
        return p

    with tempfile.TemporaryDirectory() as td:
        base = G.snapshot(rep, ENV)
        root = next(iter(base["roots"]), None)
        if root is None:
            _fail("V-GUARDIAN-FIRST-RUN", "no OK invocation; nothing to baseline")
            return

        # --- first run: no baseline on disk -> CREATED, and it exists afterwards ---
        p = Path(td) / "fresh.json"
        v = G.check(rep, ENV, repo=REPO, baseline_path=p)
        if v.verdict == G.CREATED and not v.failing and p.is_file():
            _ok("V-GUARDIAN-FIRST-RUN",
                f"{v.verdict}; baseline written: "
                f"{base['roots'][root]['executed_cases']} executed, "
                f"{base['authored_count']} authored, env={ENV}")
        else:
            _fail("V-GUARDIAN-FIRST-RUN", f"{v.verdict} failing={v.failing} exists={p.is_file()}")

        # --- stable -> PASS, no ratchet ---
        p = _write(td, base, "stable.json")
        v = G.check(rep, ENV, repo=REPO, baseline_path=p)
        if v.verdict == G.PASS and not v.failing and not v.updated:
            _ok("V-GUARDIAN-PASSES-STABLE", f"{v.verdict}; nothing fell, nothing ratcheted")
        else:
            _fail("V-GUARDIAN-PASSES-STABLE",
                  f"{v.verdict} failing={v.failing} updated={v.updated}")

        # --- a silent decrease FAILS THE BUILD, and names what vanished ---
        snap = copy.deepcopy(base)
        snap["roots"][root]["executed_cases"] += 1
        p = _write(td, snap, "drop.json")
        v = G.check(rep, ENV, repo=REPO, baseline_path=p)
        if v.verdict == G.REGRESSED and v.failing and not v.updated:
            r = v.regressions[0]
            _ok("V-GUARDIAN-DETECTS-REGRESSION",
                f"{v.verdict}; {r.gate}@{r.root}: {r.baseline} -> {r.observed}; "
                f"a decrease never auto-updates the baseline (12.7)")
        else:
            _fail("V-GUARDIAN-DETECTS-REGRESSION",
                  f"{v.verdict} failing={v.failing} updated={v.updated}")

        # --- an increase is free, and it ratchets ---
        snap = copy.deepcopy(base)
        observed = base["roots"][root]["executed_cases"]
        snap["roots"][root]["executed_cases"] = observed - 1
        p = _write(td, snap, "grew.json")
        v = G.check(rep, ENV, repo=REPO, baseline_path=p)
        after = _json.loads(p.read_text(encoding="utf-8"))["roots"][root]["executed_cases"]
        if v.verdict == G.PASS and v.updated and after == observed:
            _ok("V-GUARDIAN-UPDATES-BASELINE",
                f"{v.verdict}; baseline ratcheted {observed - 1} -> {after}")
        else:
            _fail("V-GUARDIAN-UPDATES-BASELINE",
                  f"{v.verdict} updated={v.updated} baseline_now={after} expected={observed}")

        # --- THE DELETION ATTACK (18.2). Deleting the orphans takes reach to 100% and never
        # touches the executed count. A ratio-gated guardian celebrates. This one must refuse.
        attacked = copy.deepcopy(rep)
        reached = set(attacked.reached_files)
        attacked.authored_files = sorted(reached)
        attacked.authored_count = len(reached)
        attacked.orphaned_files, attacked.orphaned_count = [], 0
        attacked.test_file_reach = 1.0
        p = _write(td, base, "attack.json")
        v = G.check(attacked, ENV, repo=REPO, baseline_path=p)
        authored_regs = [r for r in v.regressions if r.gate == "authored"]
        if v.verdict == G.REGRESSED and v.failing and authored_regs:
            _ok("V-GUARDIAN-BLOCKS-DELETION-ATTACK",
                f"{v.verdict}; reach forged to 100% by deleting "
                f"{len(authored_regs[0].lost_identities)} authored files -> REFUSED on the "
                f"absolute ({authored_regs[0].baseline} -> {authored_regs[0].observed}). "
                f"A ratio can be improved by shrinking its denominator; an absolute cannot (8.2)")
        else:
            _fail("V-GUARDIAN-BLOCKS-DELETION-ATTACK",
                  f"the deletion attack bought a green: {v.verdict} failing={v.failing}")

        # --- a cross-environment comparison is not a comparison (12.4) ---
        p = _write(td, G.snapshot(rep, "host-a"), "env.json")
        v = G.check(rep, "host-b", repo=REPO, baseline_path=p)
        if v.verdict == G.ENV_MISMATCH and not v.failing and not v.regressions:
            _ok("V-GUARDIAN-ENV-MISMATCH",
                f"{v.verdict}; two measurements of two different systems -- the guardian "
                f"refuses to raise an alarm it cannot substantiate")
        else:
            _fail("V-GUARDIAN-ENV-MISMATCH", f"{v.verdict} failing={v.failing}")

        # --- corrupt baseline -> UNKNOWN. Never a false PASS. ---
        p = Path(td) / "corrupt.json"
        p.write_text("{ not json", encoding="utf-8")
        v = G.check(rep, ENV, repo=REPO, baseline_path=p)
        if v.verdict == G.UNKNOWN and v.verdict != G.PASS and v.error:
            _ok("V-GUARDIAN-FAILOPEN-CORRUPT",
                f"{v.verdict}; a disarmed guard reports UNKNOWN, never success")
        else:
            _fail("V-GUARDIAN-FAILOPEN-CORRUPT", f"{v.verdict} error={v.error}")

        # --- END TO END: the runner must actually EXIT NON-ZERO on a regression. Everything
        # above tests the library; this tests the gate. Both the baseline and the audit dir are
        # redirected into the temp tree, so the repository's real artifacts are untouched.
        # env_key=None so the subprocess -- which computes the REAL host env hash -- compares
        # rather than short-circuiting on ENVIRONMENT_MISMATCH. A baseline recorded under a
        # synthetic key would make the runner correctly refuse to compare, and the gate would be
        # asserting nothing.
        snap = G.snapshot(rep, None)
        snap["roots"][root]["executed_cases"] += 5
        pipe_base = _write(td, snap, "pipeline.json")
        env = dict(os.environ)
        env["SQI_BASELINE_PATH"] = str(pipe_base)
        env["SQI_AUDIT_DIR"] = str(Path(td) / "audits")
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "run_sqi.py"), "--quiet"],
            cwd=str(REPO), capture_output=True, text=True, timeout=600,
            env=env, errors="replace",
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        wrote = (Path(td) / "audits").is_dir()
        if proc.returncode != 0 and G.REGRESSED in out and wrote:
            _ok("V-GUARDIAN-IN-PIPELINE",
                f"run_sqi.py exit={proc.returncode} on a regression; report still written. "
                f"Measuring became gating.")
        else:
            _fail("V-GUARDIAN-IN-PIPELINE",
                  f"exit={proc.returncode} regressed_in_output={G.REGRESSED in out} "
                  f"report_written={wrote}")

    # --- the guardian is inside the surface it audits (5.10) ---
    guarded = [
        p for p in rep.reached_files
        if "baseline_guardian" in (REPO / p).read_text(encoding="utf-8-sig", errors="replace")
    ]
    if guarded:
        _ok("V-GUARDIAN-SELF-REACH",
            f"the guardian is exercised by {guarded} -- a control that has never been observed "
            f"to refuse is indistinguishable from one that is not connected (17.10)")
    else:
        _fail("V-GUARDIAN-SELF-REACH",
              "no test reached by a canonical invocation exercises the guardian")


def check_weakening(rep) -> None:
    """SQI-02 Part XV. The guardian gates COUNTS; these gate the CONTENT of what survives.

    Deletion is loud: it lowers a count, and a lowered count fails a build. Weakening lowers
    NOTHING -- the file is present, the case is collected, the case passes, and the protection is
    gone. It is the perfect attack on a count-based instrument, and the guardian is a count-based
    instrument.

    Every gate writes only inside a temp tree, for the same reason the guardian's do: a gate that
    ratcheted the repository's real weakening baseline as a side effect of being run would stop
    being hermetic on its own second execution.
    """
    import json as _json
    import os
    import subprocess
    import tempfile

    try:
        from modules.sqi import weakening_detectors as WD
        from modules.sqi import weakening_baseline as WB
    except ImportError as exc:
        _fail("V-WEAKENING-IMPORT", f"the weakening detectors do not import: {exc}")
        return

    class _Rep:
        def __init__(self, files, commit="gate"):
            self.authored_files = list(files)
            self.commit = commit

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # --- Gate A: a removed assertion FAILS THE BUILD. Nothing else in SQI can see this. ---
        f = tmp / "test_a.py"
        f.write_text("def test_a():\n    assert 1\n    assert 2\n    assert 3\n", encoding="utf-8")
        r = _Rep(["test_a.py"])
        p = tmp / "wb.json"
        WB.check(r, repo=tmp, baseline_path=p)
        f.write_text("def test_a():\n    assert 1\n    assert 2\n", encoding="utf-8")
        v = WB.check(r, repo=tmp, baseline_path=p)
        if v.verdict == WB.WEAKENED and v.failing and not v.updated:
            w = v.weakenings[0]
            _ok("V-ASSERT-COUNT-DETECTS-REMOVAL",
                f"{v.verdict}; {w.gate}@{w.path}: {w.baseline} -> {w.observed}. The file is "
                f"present, the case is collected, the case passes -- and it asserts one thing "
                f"less. A test with zero assertions is not a test; it is an execution (15.2)")
        else:
            _fail("V-ASSERT-COUNT-DETECTS-REMOVAL",
                  f"a removed assertion bought a green: {v.verdict} failing={v.failing}")

        # --- an added assertion is free, and it RATCHETS: removing it tomorrow fails. ---
        f.write_text(
            "def test_a():\n    assert 1\n    assert 2\n    assert 3\n    assert 4\n",
            encoding="utf-8",
        )
        v = WB.check(r, repo=tmp, baseline_path=p)
        now = _json.loads(p.read_text(encoding="utf-8"))["files"]["test_a.py"]["assertions"]
        if v.verdict == WB.PASS and not v.failing and now == 4:
            _ok("V-ASSERT-COUNT-PASSES-ADDITION",
                f"{v.verdict}; baseline ratcheted 2 -> {now}. An increase requires nothing (12.2)")
        else:
            _fail("V-ASSERT-COUNT-PASSES-ADDITION",
                  f"{v.verdict} failing={v.failing} baseline_now={now}")

        # --- Gate B: over-mocking as a DELTA, never a ratio. The inline plan specified
        # `mocks / assertions > threshold`; a ratio falls when its denominator rises, and the
        # cheapest way to raise an assertion count is `assert x is not None` -- weakening 15.8.
        # A ratio gate is quieted by the exact attack Part XV exists to catch.
        g = tmp / "test_m.py"
        g.write_text("def test_a(monkeypatch):\n    m = Mock()\n    assert m\n", encoding="utf-8")
        rm = _Rep(["test_m.py"])
        pm = tmp / "wm.json"
        WB.check(rm, repo=tmp, baseline_path=pm)
        g.write_text(
            "def test_a(monkeypatch):\n"
            "    m = Mock()\n"
            "    m2 = MagicMock()\n"
            "    m3 = create_autospec(object)\n"
            "    monkeypatch.setattr('x', 'y')\n"
            "    assert m\n",
            encoding="utf-8",
        )
        v = WB.check(rm, repo=tmp, baseline_path=pm)
        mock_regs = [w for w in v.weakenings if w.gate == "mocks"]
        if v.verdict == WB.WEAKENED and v.failing and mock_regs:
            _ok("V-MOCK-DELTA-ALARM",
                f"{v.verdict}; mocks {mock_regs[0].baseline} -> {mock_regs[0].observed}. Mocked "
                f"collaborators rose while the assertion count did not: the test moved away from "
                f"reality without moving away from green (15.6). Gated as a DELTA on two "
                f"absolutes -- a mocks/assertions RATIO would be quieted by adding a tautological "
                f"assertion, which is weakening 15.8")
        else:
            _fail("V-MOCK-DELTA-ALARM", f"over-mocking bought a green: {v.verdict}")

        # --- Gate C: the content moved, the arithmetic held. REVIEW, never a build failure:
        # 15.3/15.4 are explicit that this is "a candidate list for review rather than a verdict".
        h = tmp / "test_c.py"
        h.write_text(
            "def test_a():\n    payload = {'a': 1, 'b': 2, 'c': 3}\n    assert payload\n",
            encoding="utf-8",
        )
        rc = _Rep(["test_c.py"])
        pc = tmp / "wc.json"
        WB.check(rc, repo=tmp, baseline_path=pc)
        h.write_text("def test_a():\n    payload = {'a': 1}\n    assert payload\n", encoding="utf-8")
        v = WB.check(rc, repo=tmp, baseline_path=pc)
        content = [w for w in v.reviews if w.gate == "content"]
        if v.verdict == WB.REVIEW and not v.failing and content:
            _ok("V-CONTENT-HASH-DETECTS-CHANGE",
                f"{v.verdict}; {content[0].baseline} -> {content[0].observed}. The fixture "
                f"shrank and every count held -- the signature of the unreal fixture (15.4) and "
                f"of the same-name rewrite (15.9), invisible to any instrument storing numbers")
        else:
            _fail("V-CONTENT-HASH-DETECTS-CHANGE", f"{v.verdict} reviews={len(v.reviews)}")

        # --- 15.8: the tautological assertion, the endpoint of every other weakening and the one
        # NO count reveals. Two tests, one unit, one assertion each, both green, both covered.
        # Break the return value: exactly one notices.
        (tmp / "unit.py").write_text("def value():\n    return 42\n", encoding="utf-8")
        (tmp / "test_strong.py").write_text(
            "from unit import value\ndef test_strong():\n    assert value() == 42\n",
            encoding="utf-8",
        )
        (tmp / "test_tauto.py").write_text(
            "from unit import value\ndef test_tauto():\n    value()\n    assert True\n",
            encoding="utf-8",
        )
        probe = WD.mutation_probe(
            tmp, invocation="pytest .", targets=["unit.py"],
            test_files=["test_strong.py", "test_tauto.py"], allow_dirty=True, timeout=300,
        )
        intact = (tmp / "unit.py").read_text(encoding="utf-8") == "def value():\n    return 42\n"
        m = probe.mutants[0] if probe.mutants else None
        if m and m.killed_by and m.survived_by and intact:
            _ok("V-MUTATION-PROBE-FINDS-TAUTOLOGY",
                f"killed_by={m.killed_by} survived_by={m.survived_by}; the surviving test stayed "
                f"green through a broken return value -- it is asserting nothing about the value "
                f"it claims to protect (15.8). Source restored byte-identical after the probe")
        else:
            _fail("V-MUTATION-PROBE-FINDS-TAUTOLOGY",
                  f"mutants={len(probe.mutants)} error={probe.error} restored={intact}")

        # --- fail-open, on both legs. Neither may produce a PASS. ---
        bad = tmp / "test_bad.py"
        bad.write_text("def test_a(:\n  syntax error\n", encoding="utf-8")
        rec = WD.scan_file(tmp, bad)
        pu = tmp / "corrupt.json"
        pu.write_text("{ not json", encoding="utf-8")
        v = WB.check(_Rep(["test_bad.py"]), repo=tmp, baseline_path=pu)
        if rec.assertions is None and rec.error and v.verdict == WB.UNKNOWN and not v.failing:
            _ok("V-WEAKENING-FAILOPEN-UNKNOWN",
                f"unparseable file -> assertions=None (not 0: a zero could never fall, and would "
                f"manufacture a weakening event out of a syntax error); corrupt baseline -> "
                f"{v.verdict}, never a false PASS")
        else:
            _fail("V-WEAKENING-FAILOPEN-UNKNOWN",
                  f"assertions={rec.assertions} verdict={v.verdict} failing={v.failing}")

        # --- END TO END: run_sqi.py must EXIT NON-ZERO on a weakening. Everything above tests
        # the library; this tests the GATE. The forged baseline claims one real file had one more
        # assertion than it does, so the live scan reads as a removal. Baselines and the audit
        # dir are redirected into the temp tree; the repository's artifacts are untouched.
        records = WD.scan(REPO, rep.authored_files)
        victim = next(
            (k for k, r in records.items() if (r.get("assertions") or 0) > 0), None
        )
        if victim is None:
            _fail("V-WEAKENING-PIPELINE-BLOCKS", "no file with a positive assertion count to forge")
        else:
            forged = WB.snapshot(records, rep.commit, None)
            forged["files"][victim] = dict(records[victim])
            forged["files"][victim]["assertions"] = records[victim]["assertions"] + 1
            wb_path = tmp / "pipeline_weak.json"
            WB.save_baseline(wb_path, forged)

            env = dict(os.environ)
            env["SQI_WEAKENING_BASELINE_PATH"] = str(wb_path)
            env["SQI_BASELINE_PATH"] = str(tmp / "pipeline_guard.json")
            env["SQI_AUDIT_DIR"] = str(tmp / "audits")
            env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.run(
                [sys.executable, str(REPO / "tools" / "run_sqi.py"), "--quiet"],
                cwd=str(REPO), capture_output=True, text=True, timeout=900,
                env=env, errors="replace",
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode != 0 and WB.WEAKENED in out:
                _ok("V-WEAKENING-PIPELINE-BLOCKS",
                    f"run_sqi.py exit={proc.returncode} on a removed assertion in {victim}. "
                    f"The count of executed cases never moved -- the guardian saw nothing. "
                    f"Measuring the CONTENT became gating")
            else:
                _fail("V-WEAKENING-PIPELINE-BLOCKS",
                      f"a removed assertion bought a green build: exit={proc.returncode} "
                      f"weakened_in_output={WB.WEAKENED in out}")

    # --- the detectors are inside the surface they audit (5.10) ---
    reached = [
        p for p in rep.reached_files
        if "weakening" in (REPO / p).read_text(encoding="utf-8-sig", errors="replace")
    ]
    if reached:
        _ok("V-WEAKENING-SELF-REACH",
            f"the weakening detectors are exercised by {reached} -- a control that has never "
            f"been observed to refuse is indistinguishable from one that is not connected (17.10)")
    else:
        _fail("V-WEAKENING-SELF-REACH",
              "no test reached by a canonical invocation exercises the weakening detectors")


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
    rep = check_engines()
    if rep is not None:
        check_guardian(rep)
        check_weakening(rep)

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
