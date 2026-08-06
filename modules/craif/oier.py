#!/usr/bin/env python3
"""oier.py -- the producer for Owner Intervention Escape Rate (CRAIF Part XIII).

`CRAIF_INDEX.md:93` names Part XIII "Owner Intervention Escape Rate & OIII" and
`craif_00_constitution_v1.txt` defines it as the constitutional metric: which
defects were Owner-surfaced versus system-surfaced. Measured 2026-08-06, the
identifiers OIER / owner_intervention / opportunity_miss / intervention_escape
appear in exactly one file in this repo -- a prose adversarial review. The
metric was specified at dataset tier and never written by anything.

That is the sealed `feedback_orphan_field_dead_recovery_path` shape: a field
with a consumer and no producer is dead by starvation, and the ledger lies by
reading healthy. This module is the missing producer.

Two design constraints carry sealed precedent and are not negotiable here:

1. An empty ledger reads UNMEASURED, never 0.0. `feedback_zero_cannot_fall`:
   a gate bounded by its own vocabulary reports zero for what it cannot see,
   and zero never falls. An OIER of 0.0 means "no defect ever escaped to the
   Owner" -- a perfect score. Producing that from an empty file would make the
   metric assert its best possible value precisely when it knows nothing.
   `rate` is None and `measurable` is False until the denominator is real.

2. AUTHORITY_BLOCK escapes are excluded from the numerator. An OWNER_QUEUE
   entry exists because HR-001 forbids the agent writing `~/.claude/hooks`,
   `settings.json` or commands -- a designed constitutional boundary, not a
   detector failure. Counting it as an escape would load the metric with a
   near-constant the system can never drive down, and
   `feedback_constant_factors_rank_nothing` records what a constant factor
   does to a score: it ranks nothing while looking like signal.

Append-only discipline mirrors `modules.craif.ledger.Ledger` exactly:
O_APPEND|O_BINARY with an explicit LF (Windows text-mode CRLF compounding,
`feedback_windows_text_mode_compounding`), utf-8-sig on read
(`feedback_python_utf8_bom`), fail-open on OSError, never raises.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OIER_LEDGER = PP_ROOT / "vault" / "craif_registry" / "oier.jsonl"
DEFAULT_OWNER_QUEUE = PP_ROOT / "vault" / "OWNER_QUEUE.md"


class SurfacedBy(str, Enum):
    """Who actually surfaced the defect."""

    OWNER = "OWNER"
    SYSTEM = "SYSTEM"


class EscapeClass(str, Enum):
    """Why it reached the Owner. Only DETECTOR_GAP counts as an escape.

    DETECTOR_GAP     -- no detector fired; the system could have caught it and
                        did not. This is the escape OIER exists to measure.
    AUTHORITY_BLOCK  -- a detector DID fire and correctly escalated, because a
                        Hard Rule forbids the agent from acting (HR-001).
                        Working as designed; excluded from the numerator.
    UNCLASSIFIED     -- recorded without a determination. Counted in the
                        denominator, never in the numerator: an unclassified
                        event must not be able to improve the rate.
    """

    DETECTOR_GAP = "DETECTOR_GAP"
    AUTHORITY_BLOCK = "AUTHORITY_BLOCK"
    UNCLASSIFIED = "UNCLASSIFIED"


@dataclass
class OierEvent:
    defect_id: str
    surfaced_by: str
    escape_class: str
    detector: str        # the system that caught it, "" when none did
    source: str          # the artifact this was harvested from
    note: str
    ts: str


@dataclass
class OierReading:
    """A reading that can say "I do not know" and is required to."""

    owner_surfaced: int
    system_surfaced: int
    denominator: int
    escapes: int                 # DETECTOR_GAP only
    excluded_authority_blocks: int
    unclassified: int
    rate: float | None           # None => unmeasured. Never 0.0 by default.
    measurable: bool
    note: str


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class OierLedger:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_OIER_LEDGER

    def append(self, event: OierEvent) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(asdict(event), ensure_ascii=False)
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0)
            fd = os.open(str(self.path), flags, 0o644)
            try:
                os.write(fd, (line + "\n").encode("utf-8"))
            finally:
                os.close(fd)
            return True
        except (OSError, TypeError, ValueError, AttributeError):
            return False

    def load(self) -> list[OierEvent]:
        out: list[OierEvent] = []
        try:
            if not self.path.exists():
                return out
            with self.path.open("r", encoding="utf-8-sig") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(row, dict):
                        continue
                    out.append(OierEvent(
                        defect_id=str(row.get("defect_id", "")),
                        surfaced_by=str(row.get("surfaced_by", "")),
                        escape_class=str(row.get("escape_class",
                                                 EscapeClass.UNCLASSIFIED.value)),
                        detector=str(row.get("detector", "")),
                        source=str(row.get("source", "")),
                        note=str(row.get("note", "")),
                        ts=str(row.get("ts", "")),
                    ))
        except OSError:
            return out
        return out

    def seen_ids(self) -> set[str]:
        return {e.defect_id for e in self.load() if e.defect_id}


def record(defect_id: str,
           surfaced_by: SurfacedBy | str,
           escape_class: EscapeClass | str = EscapeClass.UNCLASSIFIED,
           detector: str = "",
           source: str = "",
           note: str = "",
           path: Path | str | None = None) -> bool:
    """Write one observation. The producer this metric never had."""
    sb = surfaced_by.value if isinstance(surfaced_by, SurfacedBy) else str(surfaced_by)
    ec = escape_class.value if isinstance(escape_class, EscapeClass) else str(escape_class)
    return OierLedger(path).append(OierEvent(
        defect_id=str(defect_id), surfaced_by=sb, escape_class=ec,
        detector=detector, source=source, note=note, ts=_now()))


def read(path: Path | str | None = None) -> OierReading:
    """Compute OIER. Returns rate=None / measurable=False on an empty ledger."""
    events = OierLedger(path).load()
    owner = sum(1 for e in events if e.surfaced_by == SurfacedBy.OWNER.value)
    system = sum(1 for e in events if e.surfaced_by == SurfacedBy.SYSTEM.value)
    blocks = sum(1 for e in events
                 if e.escape_class == EscapeClass.AUTHORITY_BLOCK.value)
    unclassified = sum(1 for e in events
                       if e.escape_class == EscapeClass.UNCLASSIFIED.value)
    escapes = sum(1 for e in events
                  if e.surfaced_by == SurfacedBy.OWNER.value
                  and e.escape_class == EscapeClass.DETECTOR_GAP.value)
    # Authority blocks are a designed boundary, not a miss: out of both terms.
    denominator = len(events) - blocks

    if denominator <= 0:
        return OierReading(
            owner_surfaced=owner, system_surfaced=system, denominator=0,
            escapes=escapes, excluded_authority_blocks=blocks,
            unclassified=unclassified, rate=None, measurable=False,
            note=("UNMEASURED: no classifiable observation recorded. A rate of "
                  "0.0 here would assert the best possible score from an empty "
                  "ledger."))

    return OierReading(
        owner_surfaced=owner, system_surfaced=system, denominator=denominator,
        escapes=escapes, excluded_authority_blocks=blocks,
        unclassified=unclassified,
        rate=round(escapes / denominator, 4), measurable=True,
        note=(f"{escapes} detector-gap escape(s) over {denominator} "
              f"classifiable observation(s); {blocks} authority-block(s) "
              f"excluded by design."))


_QUEUE_HEADER = re.compile(r"^##\s+(?P<title>.+?)\s*\[(?P<state>[A-Z_]+)\]\s*$",
                           re.M)


def harvest_owner_queue(queue_path: Path | str | None = None,
                        path: Path | str | None = None) -> int:
    """Harvest OWNER_QUEUE.md entries as AUTHORITY_BLOCK observations.

    Every OWNER_QUEUE item is by construction work that reached the Owner: the
    file's own header says "items the agent prepared but cannot self-activate
    (HR-001)". They are real Owner interventions and belong in the record --
    but as AUTHORITY_BLOCK, so they populate the ledger without inflating the
    escape numerator. Idempotent: an id already present is not re-appended.
    """
    qp = Path(queue_path) if queue_path else DEFAULT_OWNER_QUEUE
    try:
        text = qp.read_text(encoding="utf-8-sig")
    except OSError:
        return 0

    ledger = OierLedger(path)
    seen = ledger.seen_ids()
    written = 0
    for m in _QUEUE_HEADER.finditer(text):
        title = m.group("title").strip()
        state = m.group("state").strip()
        defect_id = "OQ::" + re.sub(r"\s+", " ", title)[:120]
        if defect_id in seen:
            continue
        ok = ledger.append(OierEvent(
            defect_id=defect_id,
            surfaced_by=SurfacedBy.OWNER.value,
            escape_class=EscapeClass.AUTHORITY_BLOCK.value,
            detector="owner_queue",
            source=str(qp.name),
            note=f"OWNER_QUEUE state={state}",
            ts=_now()))
        if ok:
            seen.add(defect_id)
            written += 1
    return written


def format_reading(r: OierReading) -> str:
    rate = "UNMEASURED" if r.rate is None else f"{r.rate:.4f}"
    return (f"OIER={rate}  measurable={r.measurable}  "
            f"escapes={r.escapes}/{r.denominator}  "
            f"owner={r.owner_surfaced} system={r.system_surfaced}  "
            f"authority_blocks_excluded={r.excluded_authority_blocks}  "
            f"unclassified={r.unclassified}\n{r.note}")


if __name__ == "__main__":  # pragma: no cover - operator surface
    import sys
    if "--harvest" in sys.argv:
        n = harvest_owner_queue()
        print(f"harvested {n} new OWNER_QUEUE observation(s)")
    print(format_reading(read()))
