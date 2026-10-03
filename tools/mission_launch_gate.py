"""The single pre-launch authority for a mission successor.

One effect, one authority, every entrance: launching a worker spends quota and acts in the env, and the
supervisor reaches it by four actions (fresh launch, replace, relay, same-session continue). The refusals
that depend on WHERE and WHETHER a launch may happen are decided here, once, and gsd_mission.supervise asks
at one place -- after the GSD check and before turn-end, stop_owner, continue_worker, align_cwd and
launch_worker -- so a refusal changes nothing: no epoch is spent and the predecessor is not stopped.

  Lineage hold (pillar C).  A PREPARED successor made by a budget renewal has no owner, so the relay-only
      provider hold never judges it. provider_breaker.lineage_hold lets it inherit its predecessor's hold:
      a renewal must not launder a quarantine. Always on (subject to CPP_LAUNCH_GATE and the breaker's own
      CPP_PROVIDER_BREAKER switch).
  Env preflight (pillar B).  tools/gex44_env_preflight.py judges the env the launch would happen in. It
      runs only on a DECLARED mission plane: CPP_ENV_PREFLIGHT=on, or CPP_MISSION_PLANE non-empty with
      CPP_ENV_PREFLIGHT not "off". The repeatable deploy writes CPP_MISSION_PLANE into the env's env.sh, so
      every env it reaches is gated and no undeclared host is: a laptop checkout or a dev clone must never
      be judged by GEX44 rules.

Fail directions (decided, not defaulted):
  * a MEASURED NOT_READY refuses, with the preflight's typed reasons;
  * UNMEASURABLE never reads as READY and never refuses: the launch proceeds and the ledger says
    launch_preflight_unmeasurable (a refusal on an instrument that could not answer would stop an
    estate for want of a measurement);
  * a raising preflight is UNMEASURABLE; an unknown verdict string is UNMEASURABLE (a closed vocabulary:
    an unknown answer is not READY);
  * a gate that cannot run at all is recorded by the caller as launch_gate_unavailable and the launch
    proceeds as it did before (the breaker stays the backstop on the relay path).
Kill switches: CPP_LAUNCH_GATE=off silences the whole gate; CPP_ENV_PREFLIGHT=off silences the preflight.

Named debt (shrink-only): `gsd_mission.py arm` launches its first worker directly and is not gated.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402


def enabled() -> bool:
    return os.environ.get("CPP_LAUNCH_GATE", "").lower() != "off"


def preflight_enabled() -> bool:
    flag = os.environ.get("CPP_ENV_PREFLIGHT", "").strip().lower()
    if flag == "off":
        return False
    if flag == "on":
        return True
    return bool(os.environ.get("CPP_MISSION_PLANE", "").strip())


def preflight(now: float) -> dict:
    """The env verdict for the process the launch would run in. The module attribute is the test boundary."""
    import gex44_env_preflight as ep
    return ep.run(ep.env_current(), now)


def _lineage(rec: dict, now: float) -> dict | None:
    import provider_breaker as pb
    hold = pb.lineage_hold(rec, now)
    if not hold:
        return None
    mid = rec.get("mission_id")
    src = hold.get("inherited_from")
    until = hold.get("until")
    cls = hold.get("class", "quota")
    when = "QUARANTINED" if hold.get("quarantine") else f"until {int(until)}" if until else "held"
    lr.ledger_append(mid, "provider_held", mission_id=mid, epoch=rec.get("epoch"), until=until,
                     reason=hold.get("reason"), provider_class=cls, streak=hold.get("streak"),
                     quarantine=bool(hold.get("quarantine")), inherited_from=src)
    return {"refuse": True, "kind": "lineage", "verdict": "PROVIDER_HELD",
            "reason": f"provider {cls} {when} inherited from {src}: {hold.get('reason')}"}


def _env(rec: dict, act: str, now: float) -> dict:
    """The env preflight's verdict as a launch decision. Closed vocabulary: only NOT_READY refuses."""
    mid = rec.get("mission_id")
    try:
        res = preflight(now)
        if not isinstance(res, dict):
            raise TypeError(f"preflight returned {type(res).__name__}")
    except Exception as exc:  # noqa: BLE001 -- an instrument that raises has not measured anything
        res = {"verdict": "UNMEASURABLE",
               "unmeasured": [{"check": "preflight", "why": f"{exc.__class__.__name__}: {exc}"[:160]}]}
    v = res.get("verdict")
    reasons = [str(r) for r in (res.get("reasons") or [])]
    unmeasured = res.get("unmeasured") or []
    if v == "NOT_READY":
        lr.ledger_append(mid, "launch_preflight_refused", mission_id=mid, epoch=rec.get("epoch"), act=act,
                         reasons=reasons, unmeasured=unmeasured)
        return {"refuse": True, "kind": "preflight", "verdict": "NOT_READY",
                "reason": f"env preflight NOT_READY: {', '.join(reasons) or 'no reason named'}"
                          " -- launch refused (owner bundle [B])"}
    if v == "READY":
        return {"refuse": False, "kind": "preflight", "verdict": "READY", "reason": "env preflight READY"}
    if not unmeasured:
        unmeasured = [{"check": "preflight", "why": f"unrecognised verdict {v!r}"}]
    first = unmeasured[0].get("why") if isinstance(unmeasured[0], dict) else str(unmeasured[0])
    lr.ledger_append(mid, "launch_preflight_unmeasurable", mission_id=mid, epoch=rec.get("epoch"), act=act,
                     unmeasured=unmeasured)
    return {"refuse": False, "kind": "preflight", "verdict": "UNMEASURABLE",
            "reason": f"env preflight UNMEASURABLE: {first}"}


def refusal(rec: dict, act: str, now: float) -> dict | None:
    """None when the gate is off or there is nothing to judge; otherwise
    {"refuse": bool, "kind": "lineage"|"preflight", "verdict": str, "reason": str}."""
    if not enabled():
        return None
    held = _lineage(rec, now)
    if held:
        return held
    if not preflight_enabled():
        return None
    return _env(rec, act, now)
