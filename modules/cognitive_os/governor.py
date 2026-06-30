#!/usr/bin/env python3
"""governor.py -- CO-02: Economics Governor & Budget Violation Registry.

The enforcement arm of the economy. CO-01 prices and measures; CO-02 SETS budgets
and governs them across ALL sessions, and keeps the durable record of every breach
so the kernel never normalizes overspend. Where CO-00 governs the CONTEXT envelope,
CO-02 governs the COMPUTE envelope (tokens, weekly burn, model spend).

The governed envelope is nested (op/session/day/week), summed GLOBALLY across live
sessions -- the property the per-launch advisory lacks and the 48h burn needed (two
panes each "fine" can jointly blow the week). At each wrapper boundary the governor
returns ADMIT / ADMIT-DOWNGRADED / REFUSE. It PREFERS DOWNGRADE: rather than refuse,
force a cheaper model (CO-03), a lower iteration cap (CO-09), or sequential not
parallel (CO-08). REFUSE is reserved for the operation whose MINIMUM-VIABLE form
still breaches a hard budget -- and like CO-00, the refusal has no bypass flag; it
can only be satisfied by changing the operation's inputs.

Honest guarantee (CO-10): rung-3 launch-refusal/downgrade + rung-2 in-turn advisory;
it makes overspend EXPENSIVE TO IGNORE, not physically impossible mid-turn. The
Budget Violation Registry is the durable home the 49.2M/48h burn never had.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# Weekly compute envelope (output-token equivalent). Owner-derived estimate from
# cost_gate.WEEKLY_OUTPUT_LIMIT_EST (49.2M == 74% of the weekly limit).
WEEKLY_LIMIT = 66_000_000
AMBER_PCT = 0.70        # >=70% of the envelope -> tighten (bias cheaper)
RED_PCT = 0.90          # >=90% -> hard tighten
GREEN, AMBER, RED = "GREEN", "AMBER", "RED"

ADMIT, DOWNGRADED, REFUSE = "ADMIT", "ADMIT-DOWNGRADED", "REFUSE"

DEFAULT_VIOLATIONS = _PP_ROOT / "vault" / "cognitive_os" / "budget_violations.jsonl"


@dataclass
class GovernorVerdict:
    verdict: str                       # ADMIT | ADMIT-DOWNGRADED | REFUSE
    band: str                          # GREEN | AMBER | RED
    reason: str = ""
    satisfy: list = field(default_factory=list)
    new_total: int = 0
    limit: int = WEEKLY_LIMIT


def band_of(spent: int, limit: int = WEEKLY_LIMIT) -> str:
    if limit <= 0:
        return GREEN
    r = spent / limit
    if r >= RED_PCT:
        return RED
    if r >= AMBER_PCT:
        return AMBER
    return GREEN


def admit(projected: int, *, week_spent: int, week_limit: int = WEEKLY_LIMIT,
          can_downgrade: bool = True, min_viable: int = 0) -> GovernorVerdict:
    """Budget admission verdict. Prefers DOWNGRADE over REFUSE; REFUSE only when
    even the minimum-viable form breaches the hard envelope (no bypass)."""
    band = band_of(week_spent, week_limit)
    new_total = week_spent + max(0, projected)

    # Hard REFUSE: even the cheapest viable form does not fit.
    if week_spent + max(0, min_viable) > week_limit:
        return GovernorVerdict(
            REFUSE, band,
            f"even minimum-viable ({min_viable:,}) breaches the weekly envelope "
            f"({week_spent:,}/{week_limit:,})",
            ["reduce scope below the minimum, or wait for the weekly reset "
             "(no bypass -- the gate is satisfied, not silenced)"],
            week_spent + min_viable, week_limit)

    # Full op fits and we are GREEN: admit as-is.
    if new_total <= week_limit and band == GREEN:
        return GovernorVerdict(ADMIT, band, "under envelope, GREEN band",
                               [], new_total, week_limit)

    # Otherwise prefer DOWNGRADE: admit a cheaper form that fits.
    if can_downgrade:
        return GovernorVerdict(
            DOWNGRADED, band,
            f"{band} band / full op would reach {new_total:,} -- admit a cheaper "
            f"form (CO-03 cheaper model / CO-09 lower cap / CO-08 sequential)",
            ["route cheaper (CO-03)", "lower the loop iteration cap (CO-09)",
             "run sequentially not parallel (CO-08)"],
            new_total, week_limit)

    # Cannot downgrade and the full op breaches -> REFUSE.
    if new_total > week_limit:
        return GovernorVerdict(
            REFUSE, band,
            f"full op reaches {new_total:,} > {week_limit:,} and cannot downgrade",
            ["free envelope or reduce scope"], new_total, week_limit)

    return GovernorVerdict(ADMIT, band, "fits under envelope", [], new_total,
                           week_limit)


def record_violation(tier: str, *, op_class: str = "", model: str = "",
                     projected: int = 0, actual: int = 0, wu: int = 0,
                     disposition: str = "", un_gated: bool = False,
                     now: datetime | None = None, registry_path=None) -> dict:
    """Append a hard-budget breach to the durable Violation Registry (CO-02 II).
    Best-effort I/O. Captures the calibration miss (projected vs actual) and
    whether the spend escaped the wrapper (un_gated coverage gap)."""
    now = now or datetime.now(timezone.utc)
    rec = {"ts": now.isoformat(), "tier": tier, "op_class": op_class,
           "model": model, "projected": projected, "actual": actual, "wu": wu,
           "disposition": disposition, "un_gated": un_gated}
    try:
        p = Path(registry_path) if registry_path else DEFAULT_VIOLATIONS
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return rec


def read_violations(since: datetime | None = None, *, registry_path=None) -> list:
    p = Path(registry_path) if registry_path else DEFAULT_VIOLATIONS
    if not p.is_file():
        return []
    out = []
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if since is not None:
                try:
                    ts = datetime.fromisoformat(str(rec.get("ts")).replace("Z", "+00:00"))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts < since:
                        continue
                except (ValueError, TypeError):
                    continue
            out.append(rec)
    except OSError:
        return []
    return out


def weekly_envelope(proj_base=None, *, now: datetime | None = None,
                    window_fn=None) -> dict:
    """Real weekly compute spend vs the envelope (reader, not launch-critical).
    Sums 7d output via token_ground_truth.window_output. Fail-open -> unknown."""
    try:
        if window_fn is None:
            from tools.token_ground_truth import window_output as window_fn  # type: ignore
        spent = window_fn(24 * 7, proj_base, now)
        if not isinstance(spent, int):
            return {"spent": None, "limit": WEEKLY_LIMIT, "band": "unknown"}
        return {"spent": spent, "limit": WEEKLY_LIMIT,
                "band": band_of(spent, WEEKLY_LIMIT),
                "pct": round(100 * spent / WEEKLY_LIMIT, 1)}
    except Exception:  # noqa: BLE001
        return {"spent": None, "limit": WEEKLY_LIMIT, "band": "unknown"}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--proj-base", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    env = weekly_envelope(proj_base=args.proj_base)
    if args.json:
        print(json.dumps(env))
    else:
        sp = f"{env['spent']:,}" if env.get("spent") is not None else "unknown"
        print(f"weekly compute: {sp} / {env['limit']:,} "
              f"-> {env['band']}" + (f" ({env.get('pct')}%)" if env.get('pct') else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
