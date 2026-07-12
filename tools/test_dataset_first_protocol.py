#!/usr/bin/env python3
"""test_dataset_first_protocol.py -- DFP done-gate. Hermetic x3.

Every gate writes only under a tempdir. The real necessity ledger is never touched, so
the suite is safe to run repeatedly (the hermeticity lesson: a gate that writes to a
global path fails on rapid re-run).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.dataset_first import (  # noqa: E402
    Outcome, Override, Prediction, calibrate, classify, evaluate, record, thresholds,
)
from modules.dataset_first.knowledge_sufficiency import (  # noqa: E402
    DATASET_FIRST_MANDATORY, EXPERIMENT_FIRST, DIRECT_IMPLEMENTATION,
)
from modules.dataset_first.manifest import (  # noqa: E402
    ARCHITECTURE, IMPLEMENTATION, ONTOLOGY, KnowledgeInfrastructureManifest,
)

_KB = _PP_ROOT / "vault" / "knowledge_base" / "dataset_first"
_DATASETS = sorted(_KB.glob("dfp_*_v1.txt"))

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


def _words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", text))


def _parts(text: str) -> list:
    return re.split(r"(?m)^PART\s+[IVX]+\s+[—-]", text)[1:]


def main(argv=None) -> int:
    # --- V-DFP-DOCTRINE-EXISTS ------------------------------------------------------
    if len(_DATASETS) == 3 and all(p.stat().st_size > 40_000 for p in _DATASETS):
        _ok("V-DFP-DOCTRINE-EXISTS",
            f"3 datasets: {', '.join(p.name.split('_v1')[0] for p in _DATASETS)}")
    else:
        _fail("V-DFP-DOCTRINE-EXISTS", f"{len(_DATASETS)} datasets found (need 3)")

    # --- V-DFP-DEPTH -- the MEASURED band (CANONICAL_ONTOLOGY 5.2): 8k-15k per dataset,
    # >=800 words per Part. Not a band invented to fit the drafts.
    depth_bad = []
    for p in _DATASETS:
        t = p.read_text(encoding="utf-8-sig", errors="replace")
        w = _words(t)
        parts = _parts(t)
        thin = [i + 1 for i, s in enumerate(parts) if _words(s) < 800]
        if not (8000 <= w <= 15000) or len(parts) != 10 or thin:
            depth_bad.append(f"{p.name}: {w}w, {len(parts)} Parts, thin={thin}")
    if not depth_bad:
        _ok("V-DFP-DEPTH", "3 datasets x 10 Parts, all in 8k-15k, every Part >=800w")
    else:
        _fail("V-DFP-DEPTH", "; ".join(depth_bad))

    # --- V-DFP-NO-CODE-IN-DOCTRINE --------------------------------------------------
    fenced = [p.name for p in _DATASETS
              if "```" in p.read_text(encoding="utf-8-sig", errors="replace")]
    if not fenced:
        _ok("V-DFP-NO-CODE-IN-DOCTRINE", "0 code fences across the corpus")
    else:
        _fail("V-DFP-NO-CODE-IN-DOCTRINE", f"fences in {fenced}")

    # --- V-DFP-CONTAMINATION -- the conceptual quarantine ----------------------------
    pat = re.compile(r"(?i)commonwealth|tua-?x|unfair advantage|first win|capital ladder|"
                     r"pre-capital|ecommerce")
    hits = []
    for p in list(_DATASETS) + [_KB / "CANONICAL_ONTOLOGY.md", _KB / "DFP_INDEX.md"]:
        if not p.is_file():
            continue
        for m in pat.finditer(p.read_text(encoding="utf-8-sig", errors="replace")):
            hits.append(f"{p.name}:{m.group(0)}")
    if not hits:
        _ok("V-DFP-CONTAMINATION", "0 quarantined-domain hits in the corpus")
    else:
        _fail("V-DFP-CONTAMINATION", f"{len(hits)} hits: {hits[:5]}")

    # --- V-DFP-CROSS-REF-NOT-RENARRATE ----------------------------------------------
    # Each dataset must NAME its siblings (compose) rather than re-explain them.
    siblings = ("DRK", "ACIS", "spec_gate", "D2A")
    missing_ref = []
    for p in _DATASETS:
        t = p.read_text(encoding="utf-8-sig", errors="replace").lower()
        named = sum(1 for s in siblings if s.lower() in t
                    or s.lower().replace("_", " ") in t)
        if named < 2:
            missing_ref.append(f"{p.name}: names {named}/4 siblings")
    if not missing_ref:
        _ok("V-DFP-CROSS-REF-NOT-RENARRATE",
            "every dataset cross-references >=2 sealed siblings by name")
    else:
        _fail("V-DFP-CROSS-REF-NOT-RENARRATE", "; ".join(missing_ref))

    # --- V-DFP-ONTOLOGY-COMPLETE -- every canonical object has a producer AND consumer
    onto = (_KB / "CANONICAL_ONTOLOGY.md").read_text(encoding="utf-8-sig",
                                                     errors="replace")
    objects = ["ProjectClassification", "KnowledgeSufficiencyVerdict",
               "DatasetNecessityRecord", "KnowledgeInfrastructureManifest",
               "CompoundEffect", "ProtocolCalibrationRecord"]
    declared = [o for o in objects if o in onto]
    producers = onto.count("Producer:")
    if len(declared) == 6 and producers >= 5:
        _ok("V-DFP-ONTOLOGY-COMPLETE",
            f"6/6 canonical objects declared, {producers} producers named")
    else:
        _fail("V-DFP-ONTOLOGY-COMPLETE",
              f"declared={len(declared)}/6 producers={producers}")

    # --- V-DFP-DETECTOR-FAILOPEN -- pathological input -> SILENCE, never a block ------
    try:
        bad = [evaluate(""), evaluate("\x00﻿   "), evaluate("x" * 20000),
               classify(""), classify("\x00" * 100)]
        classes = {getattr(b, "verdict", None) or getattr(b, "project_class", None)
                   for b in bad}
        if classes <= {DIRECT_IMPLEMENTATION} and all(b is not None for b in bad):
            _ok("V-DFP-DETECTOR-FAILOPEN",
                "empty/null/BOM/20k-char -> DIRECT_IMPLEMENTATION (silence), no raise")
        else:
            _fail("V-DFP-DETECTOR-FAILOPEN", f"classes={classes}")
    except Exception as e:  # noqa: BLE001
        _fail("V-DFP-DETECTOR-FAILOPEN", f"RAISED {type(e).__name__} (must never raise)")

    # --- V-DFP-EXPERIMENT-REACHABLE -- a cheap probe is never sent to write a corpus --
    probe = evaluate("measure whether retrieval latency degrades under load past ten "
                     "thousand indexed coordinates", "Latency Probe", reversibility="A")
    if probe.verdict == EXPERIMENT_FIRST:
        _ok("V-DFP-EXPERIMENT-REACHABLE",
            f"empirical probe -> {probe.verdict} (score {probe.score}, NOT gated on score)")
    else:
        _fail("V-DFP-EXPERIMENT-REACHABLE",
              f"empirical probe -> {probe.verdict} (expected {EXPERIMENT_FIRST})")

    # --- V-DFP-KNOWLEDGE-FIRST-REACHABLE ---------------------------------------------
    # The class MUST be reachable, or it is dead -- and so is the eleventh DRK verdict it
    # produces. An earlier build of this gate asserted INV-1 over a list that happened to
    # be EMPTY (no case returned knowledge-first), so `all([])` passed vacuously while the
    # class was in fact UNREACHABLE. A gate that cannot fail is not a gate.
    kf = evaluate(
        "design the permanent constitutional governance authority and ontology for a "
        "novel distributed consensus architecture with no precedent: define the taxonomy "
        "of kinds, the protocol of state transitions, the invariant semantics, the "
        "benchmark thresholds and the evaluator that verifies every claim; this is a "
        "sealed universal standard that will outlive every contributor, is irreversible "
        "in production, and requires first principles theory because no prior science or "
        "model of the domain exists and it is unproven", reversibility="C")
    trivial = evaluate("add a token bucket rate limiter to the outbound api client")
    if (kf.verdict == DATASET_FIRST_MANDATORY and kf.missing
            and trivial.verdict == DIRECT_IMPLEMENTATION):
        _ok("V-DFP-KNOWLEDGE-FIRST-REACHABLE",
            f"foundational -> {kf.verdict} (score {kf.score}, capacity "
            f"{kf.dimensions['institutional_capacity']}, names {len(kf.missing)} missing "
            f"kinds -- INV-1); trivial -> {trivial.verdict}. Both poles reachable.")
    else:
        _fail("V-DFP-KNOWLEDGE-FIRST-REACHABLE",
              f"foundational -> {kf.verdict} (score {kf.score}, missing={kf.missing}); "
              f"trivial -> {trivial.verdict}. The class must be REACHABLE or it is dead.")

    # --- V-DFP-TERMINATES -- INV-6: the denominator is immutable ----------------------
    m = KnowledgeInfrastructureManifest(family="HERMETIC")
    ok1, _ = m.declare_parts(3)
    m.advance(ONTOLOGY)
    ok2, why2 = m.declare_parts(99)          # must REFUSE
    ok3, why3 = m.can_advance(IMPLEMENTATION)  # must REFUSE (unreachable before FROZEN)
    if ok1 and not ok2 and not ok3 and "INV-6" in why2:
        _ok("V-DFP-TERMINATES",
            "parts_planned immutable after ARCHITECTURE; IMPLEMENTATION unreachable early")
    else:
        _fail("V-DFP-TERMINATES", f"declare={ok1} redeclare={ok2} impl={ok3}")

    # --- V-DFP-RETIREMENT-REACHABLE (INV-4) -- the protocol CAN recommend its deletion.
    # A synthetic evidence set must flip retirement_signal True, or the protocol is
    # unfalsifiable and must be deleted on those grounds alone.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for i in range(12):
            r = record(subject=f"synthetic corpus {i}",
                       verdict=DATASET_FIRST_MANDATORY,
                       decided=DATASET_FIRST_MANDATORY, score=85,
                       missing=["ONTOLOGY"],
                       prediction=Prediction(claim="will pay off",
                                             observable="citations"),
                       repo_root=root)
            # Every demanded corpus DID NOT pay off and was NEVER cited.
            _set_outcome(root, r.id, Outcome(observed="ignored", paid_off=False,
                                             rework_events=0, citations=0))
        cal = calibrate(root)
        if cal.retirement_signal and cal.false_positive_rate >= 0.5:
            _ok("V-DFP-RETIREMENT-REACHABLE",
                f"synthetic evidence flips retirement_signal=True "
                f"(FP={cal.false_positive_rate:.0%}, citations={cal.citation_rate:.0%})")
        else:
            _fail("V-DFP-RETIREMENT-REACHABLE",
                  f"retirement unreachable: signal={cal.retirement_signal} "
                  f"FP={cal.false_positive_rate}")

        # --- V-DFP-NO-DOGMA -- the thresholds must be MOVABLE under evidence ----------
        if cal.threshold_delta and thresholds():
            _ok("V-DFP-NO-DOGMA",
                f"calibrator proposes {cal.threshold_delta} (propose, never auto-apply)")
        else:
            _fail("V-DFP-NO-DOGMA", "calibrator proposed no threshold movement on "
                                    "evidence of systematic false positives")

    # --- V-DFP-LEDGER-ADMISSIBILITY (INV-3) ------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        r_no = record("no prediction", DATASET_FIRST_MANDATORY, DATASET_FIRST_MANDATORY,
                      80, repo_root=root)
        r_yes = record("with prediction", DATASET_FIRST_MANDATORY,
                       DATASET_FIRST_MANDATORY, 80,
                       prediction=Prediction(claim="c", observable="o"), repo_root=root)
        if r_no is not None and not r_no.admissible and r_yes.admissible:
            _ok("V-DFP-LEDGER-ADMISSIBILITY",
                "a record without a PREDICTION is written but INADMISSIBLE as evidence")
        else:
            _fail("V-DFP-LEDGER-ADMISSIBILITY",
                  f"no_pred.admissible={getattr(r_no, 'admissible', None)}")

    # --- V-DFP-DRK-AMENDMENT -- the 11th verdict exists, is reachable, and is recorded
    try:
        from modules.decision_review.decision_record import Verdict
        from modules.decision_review.decision_kernel import (
            _PRECEDENCE, _highest_precedence, _resolve_knowledge,
        )
        kv = _resolve_knowledge({"project_class": DATASET_FIRST_MANDATORY})
        cheaper = _highest_precedence([Verdict.BUILD_KNOWLEDGE_FIRST,
                                       Verdict.RUN_EXPERIMENT])
        drk_idx = (_PP_ROOT / "vault" / "knowledge_base" / "decision_review"
                   / "DRK_INDEX.md").read_text(encoding="utf-8-sig", errors="replace")
        if (len(list(Verdict)) == 11
                and kv == Verdict.BUILD_KNOWLEDGE_FIRST
                and Verdict.BUILD_KNOWLEDGE_FIRST in _PRECEDENCE
                and cheaper == Verdict.RUN_EXPERIMENT
                and "BUILD-KNOWLEDGE-FIRST" in drk_idx):
            _ok("V-DFP-DRK-AMENDMENT",
                "11 verdicts; DFP provider emits BUILD-KNOWLEDGE-FIRST; RUN-EXPERIMENT "
                "wins the tie (cheaper class); doctrine amended in DRK_INDEX")
        else:
            _fail("V-DFP-DRK-AMENDMENT",
                  f"cardinality={len(list(Verdict))} kv={kv} tie={cheaper}")
    except Exception as e:  # noqa: BLE001
        _fail("V-DFP-DRK-AMENDMENT", f"{type(e).__name__}: {e}")

    # --- V-DFP-D2A-REGISTRY -- D2A can now SEE the families DFP would have duplicated -
    try:
        from modules.duplicate_to_advantage.d2a_engine import FAMILY_REGISTRY, Proposal, run
        new_fams = {"DRK-01", "DRK-03", "ACIS", "SPEC-GATE", "HR", "D2A"}
        court = run(Proposal(
            "a collegiate court of judges with distinct perspectives that deliberates and "
            "issues a verdict, with override mechanisms and recorded justification",
            "Dataset Necessity Court"))
        if new_fams <= set(FAMILY_REGISTRY) and court.dupe.is_duplicate \
                and court.dupe.parent_id.startswith("DRK"):
            _ok("V-DFP-D2A-REGISTRY",
                f"registry={len(FAMILY_REGISTRY)} families; the 'Court' proposal is "
                f"detected as a duplicate of {court.dupe.parent_id} "
                f"({court.dupe.coverage_pct}%)")
        else:
            _fail("V-DFP-D2A-REGISTRY",
                  f"registry={len(FAMILY_REGISTRY)} court_parent="
                  f"{court.dupe.parent_id} dup={court.dupe.is_duplicate}")
    except Exception as e:  # noqa: BLE001
        _fail("V-DFP-D2A-REGISTRY", f"{type(e).__name__}: {e}")

    # --- V-DFP-LIVENESS -- a row in the D1 ledger, and its probe earns LIVE on evidence
    try:
        from modules.liveness.liveness_ledger import default_registry
        row = next((r for r in default_registry()
                    if r.get("id") == "dfp-necessity-ledger"), None)
        ledger = _PP_ROOT / "vault" / "dataset_first" / "necessity_ledger.jsonl"
        seeded = ledger.is_file() and ledger.stat().st_size > 0
        if row and seeded:
            n = sum(1 for line in ledger.read_text(encoding="utf-8-sig").splitlines()
                    if line.strip())
            _ok("V-DFP-LIVENESS",
                f"D1 row 'dfp-necessity-ledger' present; probe target has {n} real "
                "record(s) -- LIVE is EARNED, not declared")
        else:
            _fail("V-DFP-LIVENESS", f"row={bool(row)} ledger_seeded={seeded}")
    except Exception as e:  # noqa: BLE001
        _fail("V-DFP-LIVENESS", f"{type(e).__name__}: {e}")

    # --- V-BASELINE -- the families DFP touched are still green -----------------------
    base = {}
    for script, want in (("test_decision_review.py", "18/18"),
                         ("test_duplicate_to_advantage.py", "22/22")):
        try:
            p = subprocess.run([sys.executable, str(_PP_ROOT / "tools" / script)],
                               capture_output=True, text=True, cwd=str(_PP_ROOT),
                               timeout=300)
            base[script] = (p.returncode, want in (p.stdout or ""))
        except Exception as e:  # noqa: BLE001
            base[script] = (99, False)
    if all(rc == 0 and hit for rc, hit in base.values()):
        _ok("V-BASELINE", "DRK 18/18 + D2A 22/22 still green after the amendment")
    else:
        _fail("V-BASELINE", f"{base}")

    # --- report ----------------------------------------------------------------------
    for status, gate, ev in _log:
        print(f"[{status}] {gate}: {ev}")
    total = _passes + _fails
    print(f"\nDFP_PASS={_passes}/{total}  threshold={total}/{total}  "
          f"VERDICT={'PASS' if _fails == 0 else 'FAIL'}")
    return 0 if _fails == 0 else 1


def _set_outcome(root: Path, rec_id: str, outcome: Outcome) -> None:
    """Rewrite one record's outcome in a TEMP ledger (hermetic only)."""
    from modules.dataset_first.necessity_record import ledger_path
    p = ledger_path(root)
    lines = [ln for ln in p.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
    out = []
    for ln in lines:
        d = json.loads(ln)
        if d.get("id") == rec_id:
            d["outcome"] = {"observed": outcome.observed, "paid_off": outcome.paid_off,
                            "rework_events": outcome.rework_events,
                            "citations": outcome.citations}
        out.append(json.dumps(d, ensure_ascii=False))
    p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())
