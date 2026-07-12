#!/usr/bin/env python3
"""calibrator.py -- DFP-05: the protocol grading itself against reality.

Without this module the Dataset First Protocol is a dogma. It computes the two error
rates from the necessity ledger, recommends threshold movement, and -- the clause that
makes the family a science rather than a belief -- can emit `retirement_signal`, the
recommendation that the protocol itself be deleted.

INV-4 (the retirement clause): retirement_signal MUST be REACHABLE. If no possible
evidence could ever set it True, the protocol is unfalsifiable and must be deleted on
those grounds alone. `V-DFP-RETIREMENT-REACHABLE` proves reachability with a synthetic
evidence set.

INV-8: an override is DATA. A protocol overridden often AND CORRECTLY is a protocol that
is wrong, and it is required to notice this about itself.

Propose, never auto-apply: the calibrator RECOMMENDS a threshold delta. It never writes a
threshold. The Owner ratifies. (Mirrors the propose-never-build contract of D2A and the
evolution engines.)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.dataset_first.knowledge_sufficiency import (  # noqa: E402
    DATASET_FIRST_MANDATORY, DIRECT_IMPLEMENTATION, HYBRID,
    THRESHOLD_HYBRID, THRESHOLD_KNOWLEDGE_FIRST,
)
from modules.dataset_first.necessity_record import admissible  # noqa: E402

# A threshold unmoved after this many admissible records is UNMEASURED, never perfect
# (DFP-00 VI.4).
STALE_AFTER = 20

# The retirement condition (INV-4). All three must hold on a sufficient evidence base.
RETIREMENT_MIN_RECORDS = 10
RETIREMENT_FP_RATE = 0.50        # half the demanded corpora did not pay off
RETIREMENT_CITATION_RATE = 0.25  # and almost nothing cited them

# A hybrid rate above this is a GAMING signal, not nuance (DFP-00 IV.4): a classifier that
# has learned to avoid committing hides in HYBRID.
HYBRID_GAMING_RATE = 0.50


@dataclass
class ProtocolCalibrationRecord:
    window: str
    n_records: int = 0
    n_admissible: int = 0
    n_dataset_first: int = 0
    n_direct: int = 0
    n_hybrid: int = 0
    false_positive_rate: float = 0.0   # corpora demanded that did not pay off
    false_negative_rate: float = 0.0   # direct builds that needed the corpus they skipped
    override_rate: float = 0.0
    correct_override_rate: float = 0.0
    citation_rate: float = 0.0         # corpora actually cited by the implementation
    hybrid_rate: float = 0.0
    threshold_delta: dict = field(default_factory=dict)
    retirement_signal: bool = False
    findings: list = field(default_factory=list)


def _rate(n: int, d: int) -> float:
    return round(n / d, 3) if d else 0.0


def calibrate(repo_root: Path | str | None = None,
              window: str = "all") -> ProtocolCalibrationRecord:
    """Grade the protocol against its own ledger. Fail-open ABSOLUTE (INV-5)."""
    try:
        records = admissible(repo_root)
        rec = ProtocolCalibrationRecord(window=window, n_admissible=len(records))
        if not records:
            rec.findings.append(
                "no admissible records -- the protocol is UNMEASURED. Every claim in "
                "DFP-00 is a hypothesis until this ledger has evidence (DFP-00 X.6).")
            return rec

        scored = [r for r in records if r.outcome is not None]
        rec.n_records = len(records)
        rec.n_dataset_first = sum(1 for r in records
                                  if r.decided == DATASET_FIRST_MANDATORY)
        rec.n_direct = sum(1 for r in records if r.decided == DIRECT_IMPLEMENTATION)
        rec.n_hybrid = sum(1 for r in records if r.decided == HYBRID)
        rec.hybrid_rate = _rate(rec.n_hybrid, rec.n_records)

        # False positive: a corpus was DEMANDED and measurably did not pay off.
        df_scored = [r for r in scored if r.decided == DATASET_FIRST_MANDATORY]
        fp = sum(1 for r in df_scored if not r.outcome.paid_off)
        rec.false_positive_rate = _rate(fp, len(df_scored))

        # False negative: went DIRECT and the rework proves the corpus was owed.
        di_scored = [r for r in scored if r.decided == DIRECT_IMPLEMENTATION]
        fn = sum(1 for r in di_scored if r.outcome.rework_events >= 2)
        rec.false_negative_rate = _rate(fn, len(di_scored))

        # Citation rate: a corpus nothing cites was never owed (DFP-00 III.7).
        cited = sum(1 for r in df_scored if r.outcome.citations > 0)
        rec.citation_rate = _rate(cited, len(df_scored))

        # Overrides are DATA (INV-8).
        overridden = [r for r in records if r.was_overridden]
        rec.override_rate = _rate(len(overridden), rec.n_records)
        ov_scored = [r for r in overridden if r.outcome is not None]
        rec.correct_override_rate = _rate(
            sum(1 for r in ov_scored if r.outcome.paid_off), len(ov_scored))

        # --- threshold movement (PROPOSE, never auto-apply) --------------------------
        if rec.false_positive_rate > 0.30:
            rec.threshold_delta["THRESHOLD_KNOWLEDGE_FIRST"] = +5
            rec.findings.append(
                f"FP rate {rec.false_positive_rate:.0%}: the protocol is demanding "
                "corpora that do not pay off. RAISE the knowledge-first threshold "
                f"({THRESHOLD_KNOWLEDGE_FIRST} -> {THRESHOLD_KNOWLEDGE_FIRST + 5}). "
                "This protocol dies of false positives (DFP-00 III.1).")
        if rec.false_negative_rate > 0.30:
            rec.threshold_delta["THRESHOLD_KNOWLEDGE_FIRST"] = -5
            rec.findings.append(
                f"FN rate {rec.false_negative_rate:.0%}: direct builds are reworking. "
                f"LOWER the threshold ({THRESHOLD_KNOWLEDGE_FIRST} -> "
                f"{THRESHOLD_KNOWLEDGE_FIRST - 5}).")
        if rec.hybrid_rate > HYBRID_GAMING_RATE:
            rec.findings.append(
                f"hybrid rate {rec.hybrid_rate:.0%} > {HYBRID_GAMING_RATE:.0%}: a "
                "classifier that has learned to avoid committing hides in HYBRID. This "
                "is a GAMING signal, not nuance (DFP-00 IV.4).")
        if rec.correct_override_rate > 0.60 and len(ov_scored) >= 3:
            rec.findings.append(
                f"the Owner overrides this protocol and is RIGHT {rec.correct_override_rate:.0%} "
                "of the time. INV-8: a protocol overridden often and correctly is a "
                "protocol that is WRONG.")
        if rec.n_records >= STALE_AFTER and not rec.threshold_delta:
            rec.findings.append(
                f"{rec.n_records} records and the thresholds have never moved. They are "
                "either perfect or unmeasured, and they are never perfect (DFP-00 VI.4).")

        # --- the retirement clause (INV-4) -------------------------------------------
        if (len(df_scored) >= RETIREMENT_MIN_RECORDS
                and rec.false_positive_rate >= RETIREMENT_FP_RATE
                and rec.citation_rate <= RETIREMENT_CITATION_RATE):
            rec.retirement_signal = True
            rec.findings.append(
                "RETIREMENT SIGNAL: across "
                f"{len(df_scored)} scored knowledge-first decisions, "
                f"{rec.false_positive_rate:.0%} of the demanded corpora did not pay off "
                f"and only {rec.citation_rate:.0%} were ever cited by the implementation "
                "that followed. The discipline does not pay for itself. The honest "
                "response is NOT to adjust a threshold -- it is to RETIRE the protocol, "
                "delete the modules, keep the datasets as a well-conducted negative "
                "result, and seal the trap that stops the next agent proposing it "
                "(DFP-00 X.10).")
        return rec

    except Exception as e:  # noqa: BLE001 -- fail-open ABSOLUTE (INV-5)
        r = ProtocolCalibrationRecord(window=window)
        r.findings.append(f"fail-open: {type(e).__name__}")
        return r


def thresholds() -> dict:
    """The live thresholds. Read-only -- the calibrator PROPOSES deltas, the Owner
    ratifies. Nothing here writes a threshold."""
    return {"THRESHOLD_KNOWLEDGE_FIRST": THRESHOLD_KNOWLEDGE_FIRST,
            "THRESHOLD_HYBRID": THRESHOLD_HYBRID}
