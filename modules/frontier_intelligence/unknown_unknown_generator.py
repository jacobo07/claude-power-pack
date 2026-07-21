#!/usr/bin/env python3
"""unknown_unknown_generator.py -- FIOS II-1 Unknown-Unknown Hunter (the generator).

Builds the II-1 engine the FIOS_INDEX carried as a thin-extend (🟡 EXTEND, "not built"):
FD-02 targets KNOWN weak spots; this is the unmapped-space complement, promoted from a
declaration seed to a live, tested engine.

question_harvester (FIOS I-4) mines the gaps the estate ALREADY RECORDED -- every
question it emits is grounded in an existing source_ref (a deposit, a trap, a
residual, an owner-queue row). But a recorded gap is a KNOWN unknown: the estate
already knows that it does not know. The harder frontier is the UNKNOWN unknown --
the gap no record contains, precisely because absence leaves no trace. A field
nobody wrote is in no ledger; a gate nobody built fails no test; a question nobody
posed is in no harvest.

This engine generates unknown-unknowns the only way a gap that left no record can be
seen: as a STRUCTURAL ASYMMETRY against a DISCOVERED peer cohort. If a feature is
present in the large majority of a cohort's peers and absent from one, that one
peer's absence is a question no source posed -- surfaced not from a record of the gap
but from the gap's shape against its own siblings. This is the estate's own
coverage-by-construction discipline (a peer set DISCOVERED from what exists, never
curated from what someone remembered) turned into a question generator: the single
point of failure nobody remembered is exactly the one the register cannot hold and
the harvester cannot mine, and it is found here by noticing it is the only sibling
missing what the rest of its cohort has.

Distinct object vs question_harvester (FIOS I-4): the harvester reads gaps the estate
WROTE DOWN; this engine finds gaps the estate's own structure IMPLIES but no record
names. Both only PROPOSE -- the output flows to the SAME FD-00 admission gate via the
session compiler (a proposed unknown-unknown the floor already covers is DECLINE'd
there, correctly). It emits the same question shape the harvester does, so it composes
the existing pipeline rather than forking one. Deterministic, zero-model, fail-open
ABSOLUTE: any error -> that cohort contributes nothing; generate() never raises.
"""
from __future__ import annotations

import hashlib
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

_MIN_COHORT = 3          # below this, "majority" is meaningless -> no asymmetry exists
_MAJORITY = 0.75         # a feature this fraction of peers have, and one lacks = asymmetry
_MAX_FINDINGS = 24       # bounded portfolio: quality over volume (FD-02)
_FP_HEX_LEN = 12
_MAX_FILE_BYTES = 400_000

# Default structural markers for a knowledge-base dataset cohort. Presence-only,
# deterministic; each is a feature a dataset either exhibits or does not.
_STRUCT_FEATURES = {
    "final_law": re.compile(r"(?i)FINAL LAW"),
    "decision_log": re.compile(r"(?im)^DECISION LOG\b"),
    "end_marker": re.compile(r"(?im)^END OF DATASET\b"),
    "epistemic_marking": re.compile(r"\b(?:DEFINED|OBSERVED|DERIVED|HYPOTHESIZED|NORMATIVE)\b"),
    "owner_queue_ref": re.compile(r"owner_queue"),
    "adversarial_section": re.compile(r"(?i)adversarial"),
    "boundary_statement": re.compile(r"(?i)\bboundary\b"),
}


@dataclass(frozen=True)
class Absence:
    """One peer lacking a feature its cohort's majority carries."""
    peer: str
    feature: str
    present: int         # how many peers in the cohort have the feature
    cohort_size: int
    cohort: str


@dataclass
class UnknownUnknown:
    """A generated question, shaped exactly like a HarvestedQuestion so it flows into
    the same session-compiler / FD-00 pipeline the harvester feeds."""
    text: str
    source: str = "structural_absence"
    source_ref: str = ""
    expected_asset: str = "asset"
    fingerprint: str = ""

    def __post_init__(self):
        if not self.fingerprint:
            norm = re.sub(r"\s+", " ", (self.text or "").strip().lower())
            self.fingerprint = "uu:" + hashlib.sha256(norm.encode("utf-8")).hexdigest()[:_FP_HEX_LEN]


def structural_features(text: str) -> set:
    """Default feature detector for a KB dataset: the set of structural markers present."""
    return {name for name, rx in _STRUCT_FEATURES.items() if rx.search(text or "")}


def detect_absences(cohort, *, cohort_name: str = "cohort",
                    threshold: float = _MAJORITY, min_cohort: int = _MIN_COHORT) -> list:
    """cohort: {peer_id -> iterable of feature tokens present in that peer}.

    Returns the Absences: a feature present in >= threshold of the peers AND absent
    from a given peer. A UNIVERSALLY-present feature yields none (no peer lacks it -- no
    asymmetry); a MINORITY feature yields none (its absence is the norm, not a gap).
    Fewer than min_cohort peers -> [] (a majority is undefined below three). Fail-open.
    """
    try:
        peers = {p: set(f or ()) for p, f in dict(cohort).items()}
        n = len(peers)
        if n < min_cohort:
            return []
        counts: dict[str, int] = {}
        for feats in peers.values():
            for f in feats:
                counts[f] = counts.get(f, 0) + 1
        out = []
        for f, c in counts.items():
            if c >= threshold * n and c < n:            # majority-present, not universal
                for p in sorted(peers):
                    if f not in peers[p]:
                        out.append(Absence(peer=p, feature=f, present=c,
                                           cohort_size=n, cohort=cohort_name))
        # Deterministic: strongest asymmetry (highest present count) first, then names.
        out.sort(key=lambda a: (-a.present, a.peer, a.feature))
        return out
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return []


def as_questions(absences, *, max_findings: int = _MAX_FINDINGS) -> list:
    """Turn Absences into pipeline-compatible questions. Bounded (FD-02)."""
    out = []
    for a in list(absences or [])[:max_findings]:
        text = (f"Every peer but '{a.peer}' in cohort '{a.cohort}' carries '{a.feature}' "
                f"({a.present}/{a.cohort_size}), and no record names why '{a.peer}' lacks "
                f"it. Is that absence a deliberate, defensible exception or an unposed gap "
                f"-- and if a gap, what always/never closes it for the whole cohort?")
        out.append(UnknownUnknown(
            text=text,
            source_ref=f"absence:{a.cohort}:{a.peer}:{a.feature}",
            expected_asset="asset"))
    return out


def cohort_from_paths(paths, feature_fn=structural_features, *, cohort_name: str = "paths"):
    """Build a DISCOVERED cohort: peers are the given file paths (found by the caller's
    own glob, never a hand-curated list), features extracted per file by
    feature_fn(text)->iterable[str]. A file that cannot be read contributes an EMPTY
    feature set and remains a peer -- its emptiness is itself a legitimate asymmetry
    signal, never a silent drop from the denominator. Returns (cohort, cohort_name).
    """
    cohort: dict[str, set] = {}
    for raw in paths or ():
        p = Path(raw)
        try:
            if p.is_file() and p.stat().st_size <= _MAX_FILE_BYTES:
                feats = set(feature_fn(p.read_text(encoding="utf-8-sig", errors="replace")) or ())
            else:
                feats = set()
        except Exception:  # noqa: BLE001 -- fail-open per peer
            feats = set()
        cohort[p.name] = feats
    return cohort, cohort_name


def generate(paths, *, feature_fn=structural_features, cohort_name: str = "datasets",
             threshold: float = _MAJORITY, max_findings: int = _MAX_FINDINGS) -> list:
    """Top-level: discover a cohort from paths, detect majority-absence asymmetries,
    and emit them as questions. Fail-open ABSOLUTE -> []."""
    try:
        cohort, name = cohort_from_paths(paths, feature_fn, cohort_name=cohort_name)
        absences = detect_absences(cohort, cohort_name=name, threshold=threshold)
        return as_questions(absences, max_findings=max_findings)
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return []


def as_declaration_questions(questions) -> list:
    """Dict form `SessionDeclaration.candidate_questions` accepts -- same contract as
    question_harvester.as_declaration_questions, so both feed one pipeline."""
    return [asdict(q) for q in (questions or [])]


def main(argv=None) -> int:
    import argparse
    import glob
    import json
    ap = argparse.ArgumentParser(
        description="FIOS unknown-unknown generator -- peer-cohort structural absence")
    ap.add_argument("--glob", default="vault/knowledge_base/d2a_fabric/daif_*.txt",
                    help="glob for the discovered peer cohort")
    ap.add_argument("--cohort", default="datasets")
    ap.add_argument("--threshold", type=float, default=_MAJORITY)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    paths = sorted(glob.glob(str(_PP_ROOT / args.glob))) or sorted(glob.glob(args.glob))
    qs = generate(paths, cohort_name=args.cohort, threshold=args.threshold)
    if args.json:
        print(json.dumps(as_declaration_questions(qs), ensure_ascii=False, indent=2))
    else:
        for q in qs:
            print(f"  [{q.source}] {q.fingerprint} ({q.expected_asset}) {q.text[:110]}")
        print(f"generated={len(qs)}  cohort={args.cohort}  peers={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
