#!/usr/bin/env python3
"""transduction.py -- CPCSC Tier-B B4: the seam DFP FREEZE -> IAS-C1 FUNDED.

DFP's `manifest.py` is a real, executable eight-stage lifecycle
(ARCHITECTURE..FROZEN..IMPLEMENTATION) that ends at FROZEN -- "the entry
gate to the only stage from which implementation is reachable" (DFP-02
Part VIII 8.5). `cpp_ias`'s IAS-C1 (Capability Portfolio) is a seven-state
capability-funding lifecycle (PROPOSED -> FUNDED -> TESTING -> RESOLVED,
Part XV) that names "Investment Thesis" as one of its own concepts, with
DFP as an explicit parent (IAS-C1's own overlap table: "Investment Thesis
(closest parents DFP, D2A; verdict SUBENGINE -> IAS-C1)"). IAS-C1 has no
executable of its own -- it is doctrine, like DAIF-01, deliberately never
built as a pipeline -- and nothing converts a DFP FREEZE event into the
input IAS-C1's own doctrine says a PROPOSED-track candidate needs: "a
D2A-5 birth score and an owner_queue entry" (IAS-C1 Part XV 15.2). A
corpus can reach FROZEN and simply sit there; nothing transduces it into
a fundable candidate.

This module is that transduction, and it is narrow by design: it never
grants FUNDED. IAS-C1 Part XV 15.3 is explicit that PROPOSED-to-FUNDED
"requires board ratification" -- a decision, DRK's authority, never a
module's. `transduce()` produces the PROPOSED-track candidate only, the
exact shape IAS-C1 already describes for that stage; `file_candidate()`
optionally records it as a real owner_queue entry, mirroring the
established `decision_review/proactive_scanner.py` -> `owner_queue`
adapter pattern for a distinct source (a FROZEN corpus, not a decision
scan).

The one caveat this module refuses to drop: DFP-02 Part VIII 8.3 states
in its own doctrine that "certification and epistemic level are orthogonal
axes... the certificate must say so on its face" -- a FROZEN corpus is
process-compliant, never thereby proven. `transduce()` accepts an optional
ACIS level (composing `decision_review.epistemic_algebra.acis_rank`, the
CPCSC B2 join, rather than re-deriving a parallel scale) and always
carries the orthogonality caveat verbatim on the candidate, so a FUNDED
review reads FROZEN and epistemic strength as the two separate signals
DFP's own doctrine insists they are.

Fail-open ABSOLUTE: a non-FROZEN or malformed manifest returns None from
`transduce()` -- an honest absence, never a fabricated candidate.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .manifest import FROZEN, KnowledgeInfrastructureManifest

# DFP-02 Part VIII 8.3, verbatim in spirit: certification never asserts
# doctrinal truth, only process compliance. Carried on every candidate so a
# FUNDED review can never mistake FROZEN for proven.
EPISTEMIC_CAVEAT = (
    "DFP-02 VIII.3: certification and epistemic level are orthogonal axes -- "
    "FROZEN asserts the corpus was built to its declared standard, reviewed, "
    "and mechanically verified; it asserts nothing about whether the doctrine "
    "inside it is true."
)

_UNASSESSED = "unassessed"

# Matches the "uu:"/12-hex convention already established by
# frontier_intelligence/unknown_unknown_generator.py's fingerprints.
_FP_HEX_LEN = 12


@dataclass(frozen=True)
class FundingCandidate:
    family: str
    governs: str
    does_not_govern: str
    frozen_at: str
    acis_level: str
    epistemic_caveat: str
    fingerprint: str


def _fingerprint(family: str, frozen_at: str) -> str:
    h = hashlib.sha256(f"{family}|{frozen_at}".encode("utf-8")).hexdigest()[:_FP_HEX_LEN]
    return f"fc:{h}"


def transduce(manifest: "KnowledgeInfrastructureManifest", *, acis_level=None):
    """A FROZEN manifest -> a PROPOSED-track `FundingCandidate` for IAS-C1's
    (doctrine-only) board process. Never returns a FUNDED state -- board
    ratification is IAS-C1's own gate (Part XV 15.3), not this module's.

    `acis_level` is read from the caller, never derived here (ACIS's own
    discipline: level is read, never set) -- pass a value from
    `decision_review.epistemic_algebra` / `fable_distillation.epistemic_ladder`
    when one exists for the corpus's underlying claims; omit it honestly
    when none has been assessed.

    Fail-open -> None: not-yet-FROZEN, no certification recorded, or a
    malformed manifest all degrade to an honest absence.
    """
    try:
        if manifest is None or getattr(manifest, "stage", None) != FROZEN:
            return None
        cert = getattr(manifest, "certification", None)
        if cert is None:
            return None
        frozen_at = getattr(manifest, "frozen_at", None) or ""
        family = getattr(manifest, "family", "") or ""
        if not family:
            return None
        level = _UNASSESSED
        if acis_level is not None:
            try:
                from modules.decision_review.epistemic_algebra import acis_rank
                r = acis_rank(acis_level)
                level = f"E{r}"
            except Exception:  # noqa: BLE001 -- fail-open per sub-check
                level = _UNASSESSED
        return FundingCandidate(
            family=family,
            governs=getattr(cert, "governs", "") or "",
            does_not_govern=getattr(cert, "does_not_govern", "") or "",
            frozen_at=frozen_at,
            acis_level=level,
            epistemic_caveat=EPISTEMIC_CAVEAT,
            fingerprint=_fingerprint(family, frozen_at),
        )
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return None


def file_candidate(candidate: "FundingCandidate", *, state_dir=None):
    """Record a `FundingCandidate` as a real owner_queue entry -- IAS-C1 Part
    XV 15.2's "owner_queue entry" half of the PROPOSED-stage artifact pair.
    Idempotent (owner_queue's own contract): re-filing the same candidate
    never duplicates.

    Fail-open -> None: owner_queue unavailable or a malformed candidate
    never raises, never fabricates a row id.
    """
    try:
        if candidate is None:
            return None
        from modules.owner_queue.owner_queue import append
        action = f"fund-track: {candidate.family}"
        command = (
            f"IAS-C1 board review candidate -- corpus FROZEN at {candidate.frozen_at}. "
            f"Governs: {candidate.governs}. Does not govern: {candidate.does_not_govern}. "
            f"ACIS level: {candidate.acis_level}. {candidate.epistemic_caveat}"
        )
        return append(action, command, component=candidate.family,
                      source="dfp-transduction", state_dir=state_dir,
                      row_id=candidate.fingerprint)
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return None
