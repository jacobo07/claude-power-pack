"""Auto-resume of stopped missions (spec vault/specs/mission-autoresume.md).

One more pass of the existing 5-minute sweep (`gsd_mission.supervise`). A mission HALTED for at least DELAY_S on a
plane mechanism (the iteration cap) is renewed under the Owner's unchanged ceilings; every other stop is ledgered and
notified, never resumed. Kill switch CPP_MISSION_AUTORESUME=off.

Measured origin (2026-11-10, GEX44 m-f27c61b9e75c): an iteration-cap halt was refused renewal against the AUTO envelope
(23.2M) while the Owner had granted 160M, the refusal reached no ledger and no person, and the mission sat 3 h 46 min.
"""
from __future__ import annotations

import os
import re
import time

DELAY_S = 300              # the Owner's "5 minutos"
MAX_AGE_S = 24 * 3600      # older halts are history, not stops to resume
MIN_WALL_LEFT_S = 15 * 60  # a successor with less wall than this cannot do a unit of work
_ITER_RE = re.compile(r"budget: iterations \d+ >= max \d+")
# refusals that say an instrument did not answer, not that the mission may not continue
_TRANSIENT_RE = re.compile(r"GSD answered (UNAVAILABLE|None)|goal check failed")


def enabled() -> bool:
    return (os.environ.get("CPP_MISSION_AUTORESUME") or "").strip().lower() != "off"


def classify(reason: str) -> str | None:
    """None when the halt is resumable by the plane; else why it belongs to the Owner."""
    r = reason or ""
    if r.startswith("owner:") or r.startswith("Owner"):
        return f"the Owner stopped it: {r[:200]}"
    if "owner BLOCKED" in r:
        return f"the worker was waiting on a human: {r[:200]}"
    if "older than" in r:
        return f"the wall clock is spent (Owner ceiling): {r[:200]}"
    if _ITER_RE.search(r):
        return None
    return f"not a plane-mechanism stop: {r[:200]}"


def _last_halt(events: list[dict]) -> dict | None:
    rows = [e for e in events if e.get("event") == "mission_halted"]
    return rows[-1] if rows else None


def _ts(row: dict) -> float | None:
    from datetime import datetime
    try:
        return datetime.fromisoformat(str(row["ts"]).replace("Z", "+00:00")).timestamp()
    except Exception:  # noqa: BLE001 -- an unreadable time is not "old enough"
        return None


def wall_left_s(rec: dict, now: float, default_hours: float) -> float:
    mh = float(rec.get("max_hours") or default_hours)
    used = now - float(rec.get("created_at") or now) - int(rec.get("waited_s") or 0)
    return mh * 3600 - used


def decide(rec: dict, halt: dict, now: float, *, why_not, default_hours: float, reserve) -> tuple[dict | None, str | None]:
    """(basis for renew_mission, None) to resume, or (None, refusal reason)."""
    why = classify(halt.get("reason") or "")
    if why:
        return None, why
    if rec.get("owner_hold"):
        return None, f"owner hold: {(rec['owner_hold'] or {}).get('reason')}"
    left = wall_left_s(rec, now, default_hours)
    if left < MIN_WALL_LEFT_S:
        return None, f"wall nearly spent: {max(0, int(left))} s of the Owner's {rec.get('max_hours')} h left"
    basis = dict(rec, max_hours=round(left / 3600, 2))
    auth = rec.get("lineage_authority_tokens") or rec.get("authority_tokens")
    if rec.get("token_estimate_src") == "auto" and auth:
        budget = int(auth) - int(reserve(rec))
        basis.update(token_estimate=budget, lineage_token_budget=budget, token_estimate_src="authority")
    refusal = why_not(basis, halt.get("reason") or "")
    if refusal:
        return None, refusal
    return basis, None


def autoresume_pass(now: float | None = None, *, gm=None, lr=None, gsd_status=None, notify=None) -> list[dict]:
    """Decide every recent HALTED mission once. Returns sweep rows. Never raises."""
    if not enabled():
        return []
    now = time.time() if now is None else now
    if gm is None:
        import gsd_mission as gm  # noqa: PLC0415
    if lr is None:
        import gsd_long_run as lr  # noqa: PLC0415
    import mission_spend as ms  # noqa: PLC0415
    if notify is None:
        import mission_remedies as mr  # noqa: PLC0415
        notify = mr.notify_incident
    rows: list[dict] = []
    try:
        missions = gm.all_missions()
    except Exception as exc:  # noqa: BLE001
        lr.ledger_append("autoresume", "autoresume_error", why=f"{type(exc).__name__}: {exc}"[:300])
        return [{"mission_id": "autoresume", "action": "autoresume", "status": "ERROR"}]
    succeeded = {m.get("renewed_from") for m in missions if m.get("renewed_from")}
    for rec in missions:
        mid = rec.get("mission_id")
        if rec.get("state") != gm.HALTED or mid in succeeded:
            continue
        try:
            events = lr.ledger_events(mid)
            halt = _last_halt(events)
            at = _ts(halt) if halt else None
            if at is None or not (DELAY_S <= now - at <= MAX_AGE_S):
                continue
            key = f"autoresume:{halt.get('seq')}"
            if any(e.get("event") in ("autoresume_renewed", "autoresume_refused") and e.get("key") == key
                   for e in events):
                # refused once: keep trying to deliver the notice (bounded inside notify_incident), decide nothing anew
                prior = next((e for e in events if e.get("event") == "autoresume_refused" and e.get("key") == key), None)
                if prior and prior.get("notified") is not False:
                    notify(mid, key, f"stopped and NOT auto-resumed: {prior.get('reason')}")
                continue
            wd = gm.live_root(rec)

            def why_not(basis, reason, _wd=wd, _rec=rec):
                st = (gsd_status or gm._supervise_gsd_status)(_wd, workstream=_rec.get("workstream"))
                return gm._renewal_why_not(basis, reason, st, _wd)

            basis, refusal = decide(rec, halt, now, why_not=why_not,
                                    default_hours=float(getattr(gm.lr, "DEFAULT_MAX_HOURS", 24)),
                                    reserve=ms.closeout_reserve)
            # capsule-v2: only the key the halt itself decided to hand on (continuity), never the record's own key,
            # which belongs to the predecessor and may be retired (review 2026-11-10, HIGH). Checked and used as one value.
            ck = (rec.get("continuity") or {}).get("capsule_key") if rec.get("rollover_protocol") else None
            if refusal is None and rec.get("rollover_protocol") and not ck:
                refusal = "capsule-v2 mission whose halt handed on no capsule: a renewal would be silently legacy"
            if refusal and _TRANSIENT_RE.search(refusal):
                # an instrument that did not answer decides nothing: re-decided on the next pass until MAX_AGE_S
                rows.append({"mission_id": mid, "action": "autoresume", "status": "retry", "why": refusal[:200]})
                continue
            if refusal and refusal.startswith("singleflight:"):
                # another live mission already carries this goal: the work is not stopped, so no notice (field dry
                # run 2026-11-10: m-9444639a3c78 was superseded by m-ea861dcb4d2e)
                lr.ledger_append(mid, "autoresume_refused", mission_id=mid, key=key, reason=refusal[:400],
                                 notified=False)
                rows.append({"mission_id": mid, "action": "autoresume", "status": "superseded"})
                continue
            if refusal:
                lr.ledger_append(mid, "autoresume_refused", mission_id=mid, key=key, reason=refusal[:400])
                notify(mid, key, f"stopped and NOT auto-resumed: {refusal[:400]}")
                rows.append({"mission_id": mid, "action": "autoresume", "status": "refused", "why": refusal[:200]})
                continue
            ck = (rec.get("continuity") or {}).get("capsule_key") if rec.get("rollover_protocol") else None
            new = gm.renew_mission(basis, now=now, capsule_key=ck,
                                   continuity_from={"mission_id": mid, "kind": "autoresume"})
            lr.ledger_append(mid, "autoresume_renewed", mission_id=mid, key=key, successor=new["mission_id"],
                             max_hours=basis.get("max_hours"), lineage_token_budget=new.get("lineage_token_budget"),
                             reason=(halt.get("reason") or "")[:200])
            rows.append({"mission_id": mid, "action": "autoresume", "status": "renewed",
                         "successor": new["mission_id"]})
            succeeded.add(mid)
        except Exception as exc:  # noqa: BLE001 -- one bad record never stops the pass
            lr.ledger_append(mid, "autoresume_error", mission_id=mid, why=f"{type(exc).__name__}: {exc}"[:300])
            rows.append({"mission_id": mid, "action": "autoresume", "status": "ERROR"})
    return rows
