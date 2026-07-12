#!/usr/bin/env python3
"""necessity_record.py -- the DFP append-only necessity ledger.

Every necessity decision is recorded, and every record carries a PREDICTION written
before the outcome is knowable (INV-3, the falsifiability contract). A record without a
prediction is INADMISSIBLE as calibration evidence -- a protocol that records what it
decided but not what it expected that decision to produce cannot be proven wrong, and a
discipline that cannot be proven wrong is a belief.

An override is DATA, not a defeat (INV-8): when the Owner decides against the verdict,
that override is the highest-signal calibration event available, because it is the only
signal that comes from outside the protocol's own model of itself.

Append-only. Fail-open ABSOLUTE: an unwritable ledger degrades to silence, never a raise.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

LEDGER_REL = Path("vault") / "dataset_first" / "necessity_ledger.jsonl"


@dataclass
class Prediction:
    """What the protocol expects this decision to produce. Written BEFORE the outcome is
    knowable. `observable` is mandatory -- a prediction that names no observable is
    unfalsifiable and the record is inadmissible."""
    claim: str
    observable: str
    horizon: str = "next-implementation"


@dataclass
class Outcome:
    """Filled in later, BY MEASUREMENT, never by recollection."""
    observed: str
    paid_off: bool
    rework_events: int = 0
    citations: int = 0          # times the corpus was cited by the implementation


@dataclass
class Override:
    who: str
    why: str
    at: str


@dataclass
class DatasetNecessityRecord:
    id: str
    subject: str
    verdict: str                       # what the protocol said
    decided: str                       # what was actually done (may differ)
    score: int
    missing: list = field(default_factory=list)
    prediction: Prediction | None = None
    override: Override | None = None
    outcome: Outcome | None = None
    rationale: str = ""

    @property
    def was_overridden(self) -> bool:
        return self.decided != self.verdict

    @property
    def admissible(self) -> bool:
        """INV-3: no prediction -> inadmissible as calibration evidence."""
        return (self.prediction is not None
                and bool((self.prediction.observable or "").strip()))


def ledger_path(repo_root: Path | str | None = None) -> Path:
    return (Path(repo_root) if repo_root else _PP_ROOT) / LEDGER_REL


def _next_id(path: Path) -> str:
    n = 0
    try:
        if path.is_file():
            with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
                n = sum(1 for line in fh if line.strip())
    except OSError:
        n = 0
    return f"DFP-{n + 1:04d}"


def record(subject: str,
           verdict: str,
           decided: str,
           score: int,
           *,
           prediction: Prediction | None = None,
           override: Override | None = None,
           missing: list | None = None,
           rationale: str = "",
           repo_root: Path | str | None = None) -> DatasetNecessityRecord | None:
    """Append a necessity record. Returns the record, or None on a fail-open degradation.

    Refuses nothing and blocks nothing: a record WITHOUT a prediction is still written
    (the decision happened; hiding it would be worse), but it is marked inadmissible and
    the calibrator will drop it from the evidence set.
    """
    try:
        path = ledger_path(repo_root)
        rec = DatasetNecessityRecord(
            id=_next_id(path), subject=subject, verdict=verdict, decided=decided,
            score=int(score), missing=list(missing or []), prediction=prediction,
            override=override, rationale=rationale)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
        return rec
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE (INV-5)
        return None


def read_all(repo_root: Path | str | None = None) -> list:
    """Every record in the ledger. Fail-open -> []."""
    out: list = []
    try:
        path = ledger_path(repo_root)
        if not path.is_file():
            return []
        with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                pred = d.get("prediction")
                outc = d.get("outcome")
                over = d.get("override")
                out.append(DatasetNecessityRecord(
                    id=d.get("id", ""), subject=d.get("subject", ""),
                    verdict=d.get("verdict", ""), decided=d.get("decided", ""),
                    score=int(d.get("score", 0) or 0), missing=d.get("missing", []) or [],
                    prediction=Prediction(**pred) if pred else None,
                    override=Override(**over) if over else None,
                    outcome=Outcome(**outc) if outc else None,
                    rationale=d.get("rationale", "")))
    except Exception:  # noqa: BLE001 -- fail-open
        return out
    return out


def admissible(repo_root: Path | str | None = None) -> list:
    """The calibration evidence set: records that carry a falsifiable prediction."""
    return [r for r in read_all(repo_root) if r.admissible]
