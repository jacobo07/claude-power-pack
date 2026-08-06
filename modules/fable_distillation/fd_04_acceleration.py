"""Epistemic acceleration over the FD-04 proof ledger (SEIP-EXT-M2).

FD-04 records, per claim, the CHEAPEST substrate on which that claim could be proven:
deterministic < small-model < mid-model. That ladder is the estate's cost-of-knowing.
Nothing ever read the ledger longitudinally, so the question the ladder exists to answer
-- *is this institution coming to know things more cheaply than it used to?* -- had never
been asked of the data.

This asks it. It is a READER over an existing ledger: no new record type, no second
authority, no writes.

WHAT ACCELERATION HONESTLY MEANS HERE
-------------------------------------
Two independent dimensions, and they fail independently:

  cadence      are proofs arriving closer together than they used to?
  cost descent is the SAME claim being re-proven on a cheaper substrate over time?

Cost descent is the stronger signal and the harder one to earn: it requires a fingerprint
to appear more than once. A ledger where every claim is proven exactly once cannot show a
claim getting cheaper, and saying otherwise would be reading a trend off a single point
per subject.

THE STALL GUARD
---------------
Measured 2026-08-06: 11 proofs across 11 distinct timestamps spanning 2026-07-10 to
2026-07-14, then nothing for 23 days. A cadence trend computed over that active window
alone would report a healthy rate for a loop that has not run in three weeks -- true
about the window, false about the institution, which is the worst kind of metric.

So staleness is checked FIRST and short-circuits the trend. A ledger silent for longer
than it was ever active is STALLED, and no arrangement of its interior points can
promote it to ACCELERATING. This is the same asymmetry the baseline guardian enforces:
the flattering reading has to clear the higher bar.

    python -m modules.fable_distillation.fd_04_acceleration

Fail-open: an absent or unreadable ledger is UNMEASURABLE, never a raise.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.fable_distillation.fd_04_prover import (  # noqa: E402
    _proofs_path, _read_jsonl)

# Cost of knowing, cheapest first. A claim proven deterministically can be re-verified
# for free; one needing a mid-model costs a call every time it is checked.
COST_LADDER = ("deterministic", "small-model", "mid-model")
COST_RANK = {name: i for i, name in enumerate(COST_LADDER)}

# Below this, an interval trend is noise dressed as a finding.
MIN_PROOFS_FOR_TREND = 6
# A ledger quiet this long is presumed stopped rather than slow.
STALE_DAYS = 14

ACCELERATING = "ACCELERATING"
DECELERATING = "DECELERATING"
FLAT = "FLAT"
STALLED = "STALLED"
UNMEASURABLE = "UNMEASURABLE"


def _parse_ts(raw):
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def load_proofs(repo: str, state_dir=None) -> list:
    """Well-formed proof records, oldest first. Never raises."""
    try:
        rows = _read_jsonl(_proofs_path(repo, state_dir))
    except Exception:                                    # noqa: BLE001
        return []
    out = []
    for r in rows:
        ts = _parse_ts(r.get("ts"))
        if ts is None or not r.get("fingerprint"):
            continue
        out.append({"ts": ts, "fingerprint": r["fingerprint"],
                    "verdict": r.get("verdict"),
                    "target": r.get("achieved_target")})
    out.sort(key=lambda r: r["ts"])
    return out


def cost_descent(proofs: list) -> dict:
    """Is the SAME claim being re-proven more cheaply? Needs a repeated fingerprint."""
    by_fp: dict = {}
    for p in proofs:
        by_fp.setdefault(p["fingerprint"], []).append(p)
    repeated = {fp: rs for fp, rs in by_fp.items() if len(rs) > 1}
    if not repeated:
        return {"verdict": UNMEASURABLE, "repeated_claims": 0,
                "descended": 0, "ascended": 0,
                "reason": f"{len(by_fp)} claim(s), none proven more than once. A claim "
                          "cannot be shown to get cheaper from a single observation of "
                          "it."}
    descended = ascended = 0
    for rs in repeated.values():
        first = COST_RANK.get(rs[0]["target"])
        last = COST_RANK.get(rs[-1]["target"])
        if first is None or last is None:
            continue
        if last < first:
            descended += 1
        elif last > first:
            ascended += 1
    if descended == 0 and ascended == 0:
        return {"verdict": FLAT, "repeated_claims": len(repeated),
                "descended": 0, "ascended": 0,
                "reason": "re-proven claims held their substrate"}
    return {"verdict": ACCELERATING if descended > ascended else DECELERATING,
            "repeated_claims": len(repeated),
            "descended": descended, "ascended": ascended,
            "reason": f"{descended} claim(s) moved to a cheaper substrate, "
                      f"{ascended} to a dearer one"}


def measure(repo: str = str(_PP_ROOT), state_dir=None, now=None) -> dict:
    """Cadence + cost descent over the FD-04 ledger. Absolute counts only."""
    proofs = load_proofs(repo, state_dir)
    base = {"proofs": len(proofs),
            "claims": len({p["fingerprint"] for p in proofs}),
            "proven": sum(1 for p in proofs if p["verdict"] == "PROVEN")}

    if not proofs:
        return {**base, "verdict": UNMEASURABLE, "span_days": 0.0,
                "days_since_last": None, "cost_descent": cost_descent([]),
                "reason": "no proof records; the ledger has never been written"}

    now = now or datetime.now(timezone.utc)
    span = (proofs[-1]["ts"] - proofs[0]["ts"]).total_seconds() / 86400.0
    quiet = (now - proofs[-1]["ts"]).total_seconds() / 86400.0
    descent = cost_descent(proofs)
    out = {**base, "span_days": round(span, 2), "days_since_last": round(quiet, 2),
           "cost_descent": descent}

    # Staleness short-circuits. A trend over the active window would describe the
    # window, not the institution.
    if quiet > STALE_DAYS and quiet > span:
        return {**out, "verdict": STALLED,
                "reason": f"silent {quiet:.1f} days after an active span of only "
                          f"{span:.1f} days. Whatever the interior points do, a loop "
                          "that has stopped is not accelerating."}

    if len(proofs) < MIN_PROOFS_FOR_TREND:
        return {**out, "verdict": UNMEASURABLE,
                "reason": f"{len(proofs)} proof(s); {MIN_PROOFS_FOR_TREND} is the "
                          "floor below which an interval trend is noise"}

    gaps = [(b["ts"] - a["ts"]).total_seconds()
            for a, b in zip(proofs, proofs[1:])]
    mid = len(gaps) // 2
    early, late = gaps[:mid], gaps[mid:]
    if not early or not late:
        return {**out, "verdict": UNMEASURABLE,
                "reason": "too few intervals to split into halves"}
    e, l = sum(early) / len(early), sum(late) / len(late)
    out["mean_gap_seconds_early"] = round(e, 1)
    out["mean_gap_seconds_late"] = round(l, 1)
    if l < e:
        verdict, why = ACCELERATING, "proofs are arriving closer together"
    elif l > e:
        verdict, why = DECELERATING, "proofs are arriving further apart"
    else:
        verdict, why = FLAT, "the interval between proofs is unchanged"
    return {**out, "verdict": verdict,
            "reason": f"{why} ({e:.0f}s -> {l:.0f}s mean interval)"}


def main(argv=None) -> int:
    print(json.dumps(measure(), ensure_ascii=False, indent=2, default=str))
    # Exit 0 on every verdict. A stalled proving loop is a fact to surface, not a
    # broken build, and failing here would pressure someone into writing proof
    # records to turn a gate green -- which is precisely the corruption FD-04 exists
    # to detect.
    return 0


if __name__ == "__main__":
    sys.exit(main())
