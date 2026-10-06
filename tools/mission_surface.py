"""The exception surface over mission attempts (GGMC C6, vault/specs/goal-governed-mission-control.md).

Pure and zero-model: each attempt is classed from its record, the plan `plan_next` gave it and the clock.
`plan_next` does not read `sleep`, so a sleeping attempt still plans relay/launch and supervise holds it --
the sleep is judged BEFORE the plan. Closed rules, first match wins:

  TERMINAL  state terminal
  COLD      owner-only: unreadable, owner_hold, sleep woken only by the Owner, plan surface_blocked
  WARM      wakes by itself or awaits an answer already asked: machine sleep, gsd_hold, capsule_hold,
            plan await / surface_unknown
  HOT       everything else: a due time wake, a live owner at work, a pass that will act
"""
from __future__ import annotations

from collections import Counter

HOT, WARM, COLD, TERMINAL = "HOT", "WARM", "COLD", "TERMINAL"


def classify(rec: dict | None, plan: dict | None, now: float, terminal_states) -> dict:
    """{"class", "owner_only", "why", "wake"} for one attempt. `rec` None = an unreadable record."""
    if rec is None:
        return {"class": COLD, "owner_only": True, "why": "record unreadable", "wake": None}
    action = (plan or {}).get("action")
    sleep = rec.get("sleep") if isinstance(rec.get("sleep"), dict) else None
    wake = (sleep or {}).get("wake") if isinstance((sleep or {}).get("wake"), dict) else None
    kind = (wake or {}).get("kind")

    def out(cls, why):
        return {"class": cls, "owner_only": cls == COLD, "why": why, "wake": wake}

    if rec.get("state") in terminal_states:
        return out(TERMINAL, f"terminal {rec.get('state')}")
    if rec.get("owner_hold"):
        return out(COLD, f"owner hold: {(rec['owner_hold'] or {}).get('reason')}")
    if kind == "owner":
        return out(COLD, f"asleep until an Owner release: {sleep.get('reason')}")
    if action == "surface_blocked":
        return out(COLD, f"a human is asked: {(plan or {}).get('reason')}")
    if kind == "time":
        at = wake.get("at")
        if at is None or float(at) > now:
            return out(WARM, f"asleep until {'an unknown time' if at is None else int(float(at))}: {sleep.get('reason')}")
        return out(HOT, f"time wake due ({int(float(at))}): the next pass re-judges it")
    if kind in ("env_ready", "cwd_aligned"):
        return out(WARM, f"asleep until {kind}: {sleep.get('reason')}")
    if rec.get("gsd_hold"):
        return out(WARM, f"waiting for GSD: {(rec['gsd_hold'] or {}).get('outcome')}")
    if rec.get("capsule_hold"):
        return out(WARM, f"capsule hold: {(rec['capsule_hold'] or {}).get('kind')}")
    if action in ("await", "surface_unknown"):
        return out(WARM, f"{action}: {(plan or {}).get('reason')}")
    return out(HOT, f"{action or 'none'}: {(plan or {}).get('reason')}")


def kpis(rows: list[dict]) -> dict:
    """Over non-terminal attempts. hot_ratio None when there are none: an empty estate is not 0% hot."""
    live = [r for r in rows if r.get("class") != TERMINAL]
    by = Counter(r.get("class") for r in live)
    causes = Counter(r["sleep_cause"] for r in live if r.get("sleep_cause"))
    return {"non_terminal": len(live), "by_class": {c: by.get(c, 0) for c in (HOT, WARM, COLD)},
            "hot_ratio": round(by.get(HOT, 0) / len(live), 3) if live else None,
            "owner_only": sum(1 for r in live if r.get("owner_only")),
            "holds_by_cause": dict(sorted(causes.items()))}
