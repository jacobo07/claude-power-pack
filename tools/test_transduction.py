#!/usr/bin/env python3
"""test_transduction.py -- V-gates for CPCSC Tier-B B4 (the seam DFP FREEZE
-> IAS-C1 FUNDED).

Verifies the transduction that converts a real DFP `KnowledgeInfrastructure
Manifest` reaching FROZEN into a PROPOSED-track `FundingCandidate` -- the
exact artifact shape IAS-C1's own doctrine names for that lifecycle stage
(Part XV 15.2). The core discipline under test: the module never grants a
FUNDED verdict (board ratification is IAS-C1's own gate, not this
module's), the DFP-02 VIII.3 orthogonality caveat rides on every
candidate regardless of ACIS level, and every malformed or premature
input degrades to an honest None rather than a fabricated candidate.

  V-DT-FROZEN-REQUIRED        a manifest short of FROZEN -> None
  V-DT-TRANSDUCE-SHAPE        a real FROZEN manifest -> a well-formed candidate
  V-DT-EPISTEMIC-CAVEAT-ALWAYS  the VIII.3 caveat rides every candidate verbatim
  V-DT-ACIS-UNASSESSED-DEFAULT  no acis_level given -> "unassessed", never a guess
  V-DT-ACIS-LEVEL-COMPOSED    a supplied ACIS level round-trips via epistemic_algebra
  V-DT-NO-CERTIFICATION-DENIED  a tampered FROZEN-but-uncertified manifest -> None
  V-DT-FAIL-OPEN               None / malformed manifest and candidate never raise
  V-DT-FILE-CANDIDATE-OWNER-QUEUE  files idempotently into a real owner_queue
  V-DT-DETERMINISTIC          identical manifest -> identical candidate on re-run

Hermetic: owner_queue filing writes to a fresh tempdir state_dir -- no
global writes, identical on re-run (run x3). V-<DOMAIN>-<NAME>;
DT_VERDICT line for the done-gate grep.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.dataset_first import transduction as TR  # noqa: E402
from modules.dataset_first.manifest import (  # noqa: E402
    AUTHORING, CERTIFIED, FROZEN, ONTOLOGY, QA, REVIEW,
    Certification, KnowledgeInfrastructureManifest,
)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


def _frozen_manifest(family: str = "test_family") -> KnowledgeInfrastructureManifest:
    """Drive a real manifest through the actual gate chain to FROZEN --
    exercising the real API, not hand-constructed state."""
    m = KnowledgeInfrastructureManifest(family=family)
    m.declare_parts(1)
    m.advance(ONTOLOGY)
    m.advance(AUTHORING)
    m.seal_part(900)
    m.advance(REVIEW)
    m.advance(QA)
    m.advance(CERTIFIED)
    m.certification = Certification(
        governs="test scope", does_not_govern="everything else",
        at="2026-07-26T00:00:00Z")
    m.advance(FROZEN)
    m.frozen_at = "2026-07-26T12:00:00Z"
    return m


def test_frozen_required() -> None:
    # Arrange -- a manifest still at ARCHITECTURE.
    m = KnowledgeInfrastructureManifest(family="not_yet")
    # Act
    r = TR.transduce(m)
    # Assert
    if r is None:
        _ok("V-DT-FROZEN-REQUIRED", "ARCHITECTURE-stage manifest -> None")
    else:
        _fail("V-DT-FROZEN-REQUIRED", f"expected None, got {r}")


def test_transduce_shape() -> None:
    # Arrange
    m = _frozen_manifest()
    # Act
    c = TR.transduce(m)
    # Assert
    ok = (c is not None and c.family == "test_family" and c.governs == "test scope"
          and c.does_not_govern == "everything else"
          and c.frozen_at == "2026-07-26T12:00:00Z"
          and c.fingerprint.startswith("fc:"))
    if ok:
        _ok("V-DT-TRANSDUCE-SHAPE", f"well-formed candidate: {c}")
    else:
        _fail("V-DT-TRANSDUCE-SHAPE", f"shape mismatch: {c}")


def test_epistemic_caveat_always() -> None:
    # Arrange
    m = _frozen_manifest()
    # Act -- one with an ACIS level, one without.
    c1 = TR.transduce(m)
    c2 = TR.transduce(m, acis_level="E5")
    # Assert -- the VIII.3 caveat rides both, unconditionally.
    if (c1.epistemic_caveat == TR.EPISTEMIC_CAVEAT
            and c2.epistemic_caveat == TR.EPISTEMIC_CAVEAT):
        _ok("V-DT-EPISTEMIC-CAVEAT-ALWAYS", "VIII.3 caveat present regardless of ACIS input")
    else:
        _fail("V-DT-EPISTEMIC-CAVEAT-ALWAYS", f"caveat missing/altered: {c1}/{c2}")


def test_acis_unassessed_default() -> None:
    # Arrange / Act
    c = TR.transduce(_frozen_manifest())
    # Assert
    if c is not None and c.acis_level == "unassessed":
        _ok("V-DT-ACIS-UNASSESSED-DEFAULT", "no acis_level given -> 'unassessed'")
    else:
        _fail("V-DT-ACIS-UNASSESSED-DEFAULT", f"expected 'unassessed', got {c}")


def test_acis_level_composed() -> None:
    # Arrange / Act -- composes decision_review.epistemic_algebra.acis_rank.
    c = TR.transduce(_frozen_manifest(), acis_level="E4")
    # Assert
    if c is not None and c.acis_level == "E4":
        _ok("V-DT-ACIS-LEVEL-COMPOSED", "supplied 'E4' round-trips via epistemic_algebra")
    else:
        _fail("V-DT-ACIS-LEVEL-COMPOSED", f"expected E4, got {c}")


def test_no_certification_denied() -> None:
    # Arrange -- a tampered manifest: FROZEN stage, no certification recorded.
    # The real advance() gate forbids reaching this state; this proves the
    # module's own defensive check catches it anyway (a loaded/corrupted manifest).
    m = KnowledgeInfrastructureManifest(family="tampered")
    m.stage = FROZEN
    m.certification = None
    # Act
    r = TR.transduce(m)
    # Assert
    if r is None:
        _ok("V-DT-NO-CERTIFICATION-DENIED", "FROZEN-but-uncertified manifest -> None")
    else:
        _fail("V-DT-NO-CERTIFICATION-DENIED", f"expected None, got {r}")


def test_fail_open() -> None:
    # Arrange / Act
    r1 = TR.transduce(None)
    r2 = TR.transduce("not a manifest")
    r3 = TR.file_candidate(None)
    r4 = TR.file_candidate("not a candidate")
    # Assert
    if r1 is None and r2 is None and r3 is None and r4 is None:
        _ok("V-DT-FAIL-OPEN", "malformed manifest/candidate inputs never raise")
    else:
        _fail("V-DT-FAIL-OPEN", f"expected all None, got {r1}/{r2}/{r3}/{r4}")


def test_file_candidate_owner_queue() -> None:
    # Arrange
    with tempfile.TemporaryDirectory() as d:
        from modules.owner_queue.owner_queue import load as oq_load
        c = TR.transduce(_frozen_manifest())
        # Act -- file it twice; idempotent by fingerprint.
        rid1 = TR.file_candidate(c, state_dir=d)
        rid2 = TR.file_candidate(c, state_dir=d)
        rows = oq_load(d)
        # Assert
        if rid1 == rid2 == c.fingerprint and len(rows) == 1:
            _ok("V-DT-FILE-CANDIDATE-OWNER-QUEUE",
                f"filed once at {rid1}, re-file did not duplicate ({len(rows)} row)")
        else:
            _fail("V-DT-FILE-CANDIDATE-OWNER-QUEUE",
                  f"rid1={rid1} rid2={rid2} fp={c.fingerprint} rows={len(rows)}")


def test_deterministic() -> None:
    # Arrange
    m = _frozen_manifest()
    # Act -- two independent calls.
    c1, c2 = TR.transduce(m), TR.transduce(m)
    # Assert
    if c1 == c2 and c1 is not None:
        _ok("V-DT-DETERMINISTIC", f"identical candidate across runs: fp={c1.fingerprint}")
    else:
        _fail("V-DT-DETERMINISTIC", f"nondeterministic: {c1} != {c2}")


def main() -> int:
    print("== transduction (CPCSC Tier-B B4, DFP FREEZE -> IAS-C1 FUNDED) ==")
    for t in (test_frozen_required, test_transduce_shape, test_epistemic_caveat_always,
              test_acis_unassessed_default, test_acis_level_composed,
              test_no_certification_denied, test_fail_open,
              test_file_candidate_owner_queue, test_deterministic):
        t()
    total = _passes + _fails
    print(f"\nDT_PASS={_passes}/{total}  threshold={total}/{total}")
    print(f"DT_VERDICT={'PASS' if _fails == 0 else 'FAIL'}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
