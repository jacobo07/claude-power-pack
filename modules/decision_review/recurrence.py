"""Decision recurrence -- so a settled question stops being a question.

The registry was write-only for decision-making. `review_decision()`
appends and never reads back; three modules load the file, all of them for
offline reporting. `Registry.next_id()` derives a fresh `DEC-<n>` from the
line count, so re-submitting a byte-identical decision produced a NEW id
rather than a collision -- the system could not notice it had already
answered.

DEC's target is narrow and worth stating precisely: a decision whose
statement AND evidence are unchanged should be answerable from the prior
verdict instead of re-reasoned. Not all decisions -- a decision whose
evidence moved is a different decision wearing the same words, and that is
exactly the case this must not collapse.

WHAT THE FINGERPRINT COVERS is therefore the discriminator. It hashes the
statement, the chosen option, the option set, and every evidence claim with
its source. Change any of them and the fingerprint changes and the decision
is re-reasoned. It deliberately EXCLUDES ts, id, confidence and the derived
classification, because those are outputs of reasoning, not inputs to it --
including them would make every decision unique and the cache would never
hit, which is the same as not having one.
"""
from __future__ import annotations

import hashlib
import json

FINGERPRINT_VERSION = 1

# A cached verdict is a shortcut through judgement, so it is not allowed to
# outlive the conditions it was formed under indefinitely.
DEFAULT_MAX_AGE_S = 30 * 24 * 3600


def fingerprint(obj) -> str:
    """Stable digest of a decision's INPUTS."""
    ev = []
    for e in (getattr(obj, "evidence", None) or []):
        claim = getattr(e, "claim", None)
        source = getattr(e, "source", None)
        etype = getattr(e, "type", None)
        if claim is None and isinstance(e, dict):
            claim, source, etype = e.get("claim"), e.get("source"), e.get("type")
        ev.append([str(getattr(etype, "value", etype) or ""),
                   str(claim or "").strip(),
                   str(source or "").strip()])
    ev.sort()
    payload = {
        "v": FINGERPRINT_VERSION,
        "statement": str(getattr(obj, "statement", "") or "").strip(),
        "chosen": str(getattr(obj, "chosen", "") or "").strip(),
        "options": sorted(str(o).strip()
                          for o in (getattr(obj, "options", None) or [])),
        "evidence": ev,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def find_precedent(obj, registry, *, max_age_s: int = DEFAULT_MAX_AGE_S,
                   now_ts: float | None = None) -> dict | None:
    """The most recent recorded verdict for this exact decision, or None.

    Returns None on ANY doubt -- unreadable registry, absent fingerprint,
    missing verdict, aged-out record. A precedent lookup that guesses is
    worse than no precedent, because it would answer a live question with
    a decision nobody actually made.
    """
    import time

    try:
        rows = registry.load()
    except Exception:  # noqa: BLE001 -- never let a cache read break a decision
        return None
    if not rows:
        return None

    want = fingerprint(obj)
    now = time.time() if now_ts is None else now_ts
    best = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("fingerprint") != want:
            continue
        if not row.get("verdict"):
            continue
        # A superseded decision is precedent for nothing.
        if row.get("superseded_by"):
            continue
        ts = _epoch(row.get("ts"))
        if ts is None or (now - ts) > max_age_s:
            continue
        if best is None or ts > best[0]:
            best = (ts, row)
    if best is None:
        return None
    ts, row = best
    return {
        "id": row.get("id"),
        "verdict": row.get("verdict"),
        "tier": row.get("tier"),
        "ts": row.get("ts"),
        "age_days": round((now - ts) / 86400, 1),
        "fingerprint": want,
    }


def _epoch(ts) -> float | None:
    if isinstance(ts, (int, float)):
        return float(ts)
    if not isinstance(ts, str) or not ts:
        return None
    from datetime import datetime, timezone
    raw = ts.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()
