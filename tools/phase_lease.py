#!/usr/bin/env python
"""Phase lease: a per-GSD-phase spend authority carried on the mission record (CCR v5 Stage A, A2).

Measured 2026-10-15 (plan vault/plans/ccr-v5-vehicle-repair-2026-10-15.md section 1-2): the phase stop-loss
was ROADMAP prose the model could read past (0 hits in gsd_mission / mission_spend / mission_recovery /
gsd_epoch); one gsd-planner spent 24.0M of an 80M incident. A phase lease is the deterministic version:

    {phase, forecast, warn, hard, reserve, base, state_file, set_by, set_at}

* Written only by `gsd_mission.set_envelope` (a CAS `transition`), never by the worker: the hook
  `mission_gate.js` denies a worker's call that names the mission record.
* Phase spend = mission processed tokens now - `base` (the processed total measured when the lease was
  set, i.e. at the phase's start). `warn`/`hard` are ratios of `forecast`.
* An unmeasurable spend, or a GSD phase (read from the workstream STATE.md) that is not the leased phase,
  is BLOCKED -- ambiguity is never permission. A phase moved on without a new lease is exactly the case
  where the old forecast no longer describes the spend.

Pure: the caller supplies the measurement and the current phase. No I/O except `current_phase`.
"""
from __future__ import annotations

import re
from pathlib import Path

WARN_RATIO = 1.2
HARD_RATIO = 1.5

OK, WARN, TRIP, BLOCKED = "OK", "WARN", "TRIP", "BLOCKED"

_PHASE_RE = re.compile(r"^current_phase:\s*[\"']?(\d+(?:\.\d+)?)", re.M)


class LeaseError(ValueError):
    pass


def make_lease(*, phase, forecast, base, state_file, reserve=0, warn=WARN_RATIO, hard=HARD_RATIO,
               set_at: float, max_calls=None, calls_base=None) -> dict:
    """Validate and build a lease. `base` is the mission's processed total at the phase start.
    `max_calls` (CCR v5 E2, boundary authority) caps the phase's model calls; `calls_base` is the
    mission's call count at the phase start, measured by the caller like `base`."""
    if max_calls is not None:
        if isinstance(max_calls, bool) or not isinstance(max_calls, int) or max_calls <= 0:
            raise LeaseError(f"max_calls must be a positive integer, not {max_calls!r}")
        if isinstance(calls_base, bool) or not isinstance(calls_base, int) or calls_base < 0:
            raise LeaseError(f"max_calls needs a measured calls_base (non-negative integer), not {calls_base!r}")
    phase = str(phase).strip()
    if not re.fullmatch(r"\d+(?:\.\d+)?", phase):
        raise LeaseError(f"phase must be a phase number like 1 or 2.1, not {phase!r}")
    for name, v in (("forecast", forecast), ("base", base), ("reserve", reserve)):
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise LeaseError(f"{name} must be a non-negative integer token count, not {v!r}")
    if forecast <= 0:
        raise LeaseError("forecast must be positive: a phase with no forecast has no authority to judge")
    if not (1.0 < float(warn) < float(hard)):
        raise LeaseError(f"need 1 < warn < hard, got warn={warn} hard={hard}")
    if not str(state_file or "").strip():
        raise LeaseError("state_file is required: the lease names where the current GSD phase is read")
    lease = {"phase": phase, "forecast": forecast, "warn": float(warn), "hard": float(hard), "reserve": reserve,
             "base": base, "state_file": str(state_file), "set_by": "envelope", "set_at": set_at}
    if max_calls is not None:
        lease.update(max_calls=max_calls, calls_base=calls_base)
    return lease


def current_phase(state_file: str | Path) -> str | None:
    """The GSD phase number in a workstream STATE.md front matter, or None when it cannot be read."""
    try:
        text = Path(state_file).read_text(encoding="utf-8-sig")
    except OSError:
        return None
    m = _PHASE_RE.search(text)
    return m.group(1) if m else None


def judge(lease: dict | None, spent: int | None, phase_now: str | None, calls: int | None = None) -> dict:
    """Token verdict (`_judge_tokens`) plus the boundary authority: a lease with `max_calls` also judges the
    phase's model calls (`calls` now - `calls_base`). A call count that is unmeasured or below its base is
    BLOCKED, never permission; more calls than `max_calls` is a TRIP whatever the tokens say, because a
    cheap-per-call phase can still rediscover the same code forever. A lease without `max_calls` is unchanged."""
    out = _judge_tokens(lease, spent, phase_now)
    if not lease or lease.get("max_calls") is None or out["verdict"] in (TRIP, BLOCKED):
        return out
    cap, base = int(lease["max_calls"]), int(lease.get("calls_base") or 0)
    if calls is None:
        return {**out, "verdict": BLOCKED, "calls": None, "max_calls": cap,
                "reason": f"phase {lease['phase']} call count is unmeasurable; unmeasured is not zero"}
    n = calls - base
    if n < 0:
        return {**out, "verdict": BLOCKED, "calls": n, "max_calls": cap,
                "reason": f"call count {calls:,} is below the lease base {base:,}: the baseline is not this lineage's"}
    out.update(calls=n, max_calls=cap)
    if n > cap:
        return {**out, "verdict": TRIP,
                "reason": f"boundary breaker: phase {lease['phase']} made {n:,} calls > max_calls {cap:,}; reforecast before release"}
    return out


def _judge_tokens(lease: dict | None, spent: int | None, phase_now: str | None) -> dict:
    """{verdict, spend, hard_at, warn_at, reason}. No lease -> OK with no reason (nothing to judge)."""
    if not lease:
        return {"verdict": OK, "reason": None}
    forecast, base = int(lease["forecast"]), int(lease["base"])
    warn_at, hard_at = int(forecast * float(lease["warn"])), int(forecast * float(lease["hard"]))
    out = {"phase": lease["phase"], "warn_at": warn_at, "hard_at": hard_at, "forecast": forecast}
    if spent is None:
        return {**out, "verdict": BLOCKED, "spend": None,
                "reason": f"phase {lease['phase']} spend is unmeasurable; unmeasured is not zero"}
    if phase_now is None:
        return {**out, "verdict": BLOCKED, "spend": None,
                "reason": f"the current GSD phase cannot be read from {lease['state_file']}"}
    if str(phase_now) != str(lease["phase"]):
        return {**out, "verdict": BLOCKED, "spend": None,
                "reason": (f"GSD is on phase {phase_now} but the lease is for phase {lease['phase']}: the prior phase's "
                           "accounting is ambiguous; a new lease needs a reforecast")}
    spend = spent - base
    if spend < 0:
        return {**out, "verdict": BLOCKED, "spend": spend,
                "reason": f"processed {spent:,} is below the lease base {base:,}: the baseline is not this lineage's"}
    out["spend"] = spend
    if spend > hard_at:
        return {**out, "verdict": TRIP,
                "reason": (f"phase breaker: phase {lease['phase']} spent {spend:,} > hard {hard_at:,} "
                           f"({lease['hard']:g} x forecast {forecast:,}); reforecast before release")}
    if spend > warn_at:
        return {**out, "verdict": WARN,
                "reason": f"phase {lease['phase']} spent {spend:,} > warn {warn_at:,} ({lease['warn']:g} x forecast {forecast:,})"}
    return {**out, "verdict": OK, "reason": None}
