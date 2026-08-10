#!/usr/bin/env python3
"""opportunity_cost.py -- IAS-C2 Part V (Opportunity Cost) + Part VI (the Ledger).

Implements the corpus's core defined objects against a REAL ranked-alternatives
source (backlog_autopilot's BacklogItem scoring), not a fabricated forecast:

  rank_and_forgo   -- Part V §5.3: opportunity cost is computed against the
                      HIGHEST-ranked live alternative NOT chosen, never an
                      arbitrarily selected one.
  OpportunityCostRecord -- Part V §5.6's two-phase (provisional/settled) record.
  record_opportunity_cost -- Part VI: append-only ledger, read-many/write-few
                      (§6.8) -- the only writer is the decision point itself.
  settle_if_later_chosen -- Part V §5.4's settlement mechanic, in its simplest
                      real form: a foregone item that gets chosen on a LATER
                      call settles CONFIRMED; nothing here fabricates a
                      forecast horizon this slice does not compute.
  domain_aggregate -- Part VI §6.2/§6.4: the ledger's primary consumer-facing
                      artifact is the per-domain pattern, never a false-
                      precision running total (magnitude stays ordinal).

Magnitude is read directly from the chosen/foregone item's own `impact` field
(Critical/High/Medium/Low) -- Part IV §4.3's ordinal-only discipline, reusing
the real category rather than inventing a parallel one.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

_PP_ROOT = Path(__file__).resolve().parents[2]


class Magnitude(str, Enum):
    """The ordinal magnitude of a foregone alternative (Part IV §4.3).

    UNDECLARED and UNRECOGNISED are STATES, never levels, and neither is on the
    ladder. They are kept apart on purpose, following the same reasoning
    `modules/rule_compiler/schema.py` gives for Binding: folding an unknown value
    into the absent one lets a typo read as "nobody has said yet".

    Before D-003 this vocabulary was an unguarded dict lookup defaulting to LOW.
    An impact of "Blocker" was therefore recorded as the LEAST urgent category,
    indistinguishable from a genuinely Low one -- a plausible value that does not
    reflect reality, which is worse than an absent one because nothing downstream
    can tell it was ever wrong.
    """
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNDECLARED = "UNDECLARED_IMPACT"        # no impact was given at all
    UNRECOGNISED = "UNRECOGNISED_IMPACT"    # a value was given, outside the vocabulary


#: Weakest first. The two states above are deliberately absent -- they are not levels.
MAGNITUDE_LADDER: tuple[Magnitude, ...] = (
    Magnitude.LOW, Magnitude.MODERATE, Magnitude.HIGH, Magnitude.CRITICAL,
)

#: The source vocabulary is BacklogItem.impact ("Critical" | "High" | "Medium" |
#: "Low"); MODERATE is this module's name for Medium. Both spellings resolve, so a
#: record round-trips through the ledger unchanged.
_MAGNITUDE_BY_NAME = {
    "CRITICAL": Magnitude.CRITICAL, "HIGH": Magnitude.HIGH,
    "MEDIUM": Magnitude.MODERATE, "MODERATE": Magnitude.MODERATE,
    "LOW": Magnitude.LOW,
}


def read_magnitude(raw) -> Magnitude:
    """Impact text -> Magnitude. Absent is UNDECLARED; present-but-unknown is
    UNRECOGNISED. Separators and emphasis are normalised -- but only those.
    Anything still unmatched is surfaced, never guessed into the ladder."""
    text = (raw or "").strip().strip("*_`").strip() if isinstance(raw, str) else ""
    if not text:
        return Magnitude.UNDECLARED
    key = re.sub(r"[\s\-]+", "_", text).upper()
    return _MAGNITUDE_BY_NAME.get(key, Magnitude.UNRECOGNISED)


def ledger_path(repo_root: Path | None = None) -> Path:
    return (Path(repo_root) if repo_root else _PP_ROOT) / "vault" / "ias" / "c2_opportunity_cost_ledger.jsonl"


@dataclass(frozen=True)
class OpportunityCostRecord:
    chosen_id: str
    chosen_domain: str
    foregone_id: str
    foregone_domain: str
    foregone_magnitude: str          # a Magnitude value: a ladder level, or a state
    decided_at: str                  # ISO-8601 UTC
    lifecycle: str = "PROJECTED"     # PROJECTED | CONFIRMED (Part V §5.4, simplified)
    settled_at: Optional[str] = None


def rank_and_forgo(candidates: list, chosen, score_fn: Callable[[object], int]):
    """The highest-ranked LIVE candidate that was NOT chosen (Part V §5.3).

    Ranks against ALL candidates still in the pool, never a single arbitrarily
    picked alternative. Returns None when `chosen` was the only candidate.
    """
    live = [c for c in candidates if c.id != chosen.id]
    if not live:
        return None
    return max(live, key=score_fn)


def _domain_of(item) -> str:
    """Coarse capability domain (Part VI §6.2). BacklogItem has no explicit
    domain field, so the id's prefix up to the first '-' stands in for it
    (matches this repo's own BacklogItem id convention, e.g. 'FIX-1', 'FEAT-2')."""
    return item.id.split("-", 1)[0] if "-" in item.id else item.id


def record_opportunity_cost(chosen, foregone, *, repo_root: Path | None = None,
                             now: datetime | None = None) -> OpportunityCostRecord | None:
    """Append one OpportunityCostRecord for this allocation decision. Fail-open:
    an IO error drops the record rather than breaking the caller's own decision
    (the ledger is an observability instrument, never load-bearing for the
    choice itself -- Part VI's read-many/write-few discipline never gates)."""
    if foregone is None:
        return None
    rec = OpportunityCostRecord(
        chosen_id=chosen.id,
        chosen_domain=_domain_of(chosen),
        foregone_id=foregone.id,
        foregone_domain=_domain_of(foregone),
        foregone_magnitude=read_magnitude(getattr(foregone, "impact", None)).value,
        decided_at=(now or datetime.now(timezone.utc)).isoformat(),
    )
    try:
        path = ledger_path(repo_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
    except OSError:
        pass
    return rec


def _read_ledger(repo_root: Path | None = None) -> list[dict]:
    path = ledger_path(repo_root)
    if not path.is_file():
        return []
    out = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return out


def settle_if_later_chosen(chosen, *, repo_root: Path | None = None,
                            now: datetime | None = None) -> int:
    """Part V §5.4's settlement, in its simplest real form: if the item chosen
    THIS time was foregone in an earlier still-PROJECTED record, that record
    settles CONFIRMED (the sacrificed value was eventually served after all).
    Returns the number of records settled. Fail-open -> 0."""
    try:
        rows = _read_ledger(repo_root)
        path = ledger_path(repo_root)
        if not rows or not path.is_file():
            return 0
        ts = (now or datetime.now(timezone.utc)).isoformat()
        settled = 0
        out_lines = []
        for row in rows:
            if row.get("lifecycle") == "PROJECTED" and row.get("foregone_id") == chosen.id:
                row["lifecycle"] = "CONFIRMED"
                row["settled_at"] = ts
                settled += 1
            out_lines.append(json.dumps(row, ensure_ascii=False))
        if settled:
            path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return settled
    except OSError:
        return 0


def domain_aggregate(repo_root: Path | None = None) -> dict[str, dict[str, int]]:
    """Part VI §6.2/§6.4: per-domain counts by lifecycle state -- the ledger's
    primary consumer-facing artifact. Never a pooled false-precision total."""
    agg: dict[str, dict[str, int]] = {}
    for row in _read_ledger(repo_root):
        d = row.get("foregone_domain", "unknown")
        bucket = agg.setdefault(d, {"PROJECTED": 0, "CONFIRMED": 0})
        state = row.get("lifecycle", "PROJECTED")
        bucket[state] = bucket.get(state, 0) + 1
    return agg


def magnitude_states(repo_root: Path | None = None) -> dict[str, list[str]]:
    """Records whose magnitude is a STATE rather than a ladder level, by named id.

    Recording UNRECOGNISED instead of collapsing to LOW only helps if something
    reads it back. Named id lists, never a ratio: a ratio is satisfied by adding
    well-formed records, a name has to be fixed at its source.
    """
    out: dict[str, list[str]] = {Magnitude.UNDECLARED.value: [],
                                 Magnitude.UNRECOGNISED.value: []}
    for row in _read_ledger(repo_root):
        m = row.get("foregone_magnitude", "")
        if m in out:
            out[m].append(row.get("foregone_id", "?"))
    return out


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="IAS-C2 Opportunity Cost Ledger")
    ap.add_argument("--report", action="store_true", help="print per-domain aggregate")
    args = ap.parse_args(argv)
    if args.report:
        agg = domain_aggregate()
        if not agg:
            print("(ledger empty -- no opportunity cost records yet)")
        for domain, counts in sorted(agg.items()):
            print(f"  {domain}: PROJECTED={counts.get('PROJECTED', 0)} "
                  f"CONFIRMED={counts.get('CONFIRMED', 0)}")
        for state, ids in magnitude_states().items():
            if ids:
                print(f"  {state}: {len(ids)} record(s) -- {', '.join(sorted(set(ids)))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
