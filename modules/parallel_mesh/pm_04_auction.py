#!/usr/bin/env python3
"""pm_04_auction.py -- PM-04: Parallel Budget Auction & Concurrency Modes.

Once N panes are allowed (PM-02) and not duplicating (PM-01/PM-03), the scarce
question is: under a shared burn envelope, who spends and how much? The default
today is arrival-order. PM-04 replaces it with ROI priority + concurrency modes
that scale every pane's allowed spend to the AGGREGATE real burn, plus an Opus
Singleton default. Every mechanism here is ADVISORY and FAIL-OPEN: it makes an
expensive choice visible and expensive-to-ignore, never physically blocked
(CO-10 rung-2). The gate order is scope (PM-02) -> budget (PM-04) -> the sealed
CO-00/CO-08 wrapper enforcement; all three are advisory.

Parents:
  CO-01 economics -- ROI / Cognitive Capital (the auction ranks by it).
  CO-02 governor  -- DOWNGRADE-over-REFUSE (a lost bid downgrades, never dies).
  CO-08 scheduler -- the same-repo discipline, applied to the model axis (Opus).
  W5  cost_gate.weekly_burn -- the REAL burn source. rate_factor = 24h output /
      the June daily average; None when unmeasured (-> Green, never a fake 0).

Honest (CO-10): the mode is derived from cost_gate's REAL per-turn transcript
burn, never an invented number. A missing measurement yields Green (silence), not
a fabricated factor.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

GREEN, YELLOW, RED, BLACK = "GREEN", "YELLOW", "RED", "BLACK"

# Mode thresholds on the burn rate factor (24h output / June daily avg). Boundaries
# per the PM-04 dataset: Green <=1.0, Yellow (1.0,1.5], Red (1.5,2.0], Black >2.0.
YELLOW_FACTOR = 1.0
RED_FACTOR = 1.5
BLACK_FACTOR = 2.0

# ROI a pane must declare to justify Opus in Yellow+ (a value-class floor; the
# auction is advisory so this is a recommendation, not a hard cut).
DEFAULT_ROI_THRESHOLD = 3.0


@dataclass
class ModeVerdict:
    mode: str
    factor: float | None = None
    source: str = ""          # real | failopen-green:<why>


@dataclass
class BudgetAdvisory:
    mode: str
    lines: list = field(default_factory=list)   # advisory strings (empty=silent)
    suggested_model: str = ""
    blocks: bool = False        # ALWAYS False -- PM-04 never hard-blocks (fail-open)


@dataclass
class Bid:
    sid: str
    roi: float = 0.0
    model: str = ""
    cost: int = 0


def _is_opus(model: str) -> bool:
    return "opus" in (model or "").lower()


def compute_mode(factor: float | None) -> str:
    """Pure: burn rate factor -> concurrency mode. None -> GREEN (fail-open)."""
    if factor is None:
        return GREEN
    if factor <= YELLOW_FACTOR:
        return GREEN
    if factor <= RED_FACTOR:
        return YELLOW
    if factor <= BLACK_FACTOR:
        return RED
    return BLACK


def current_mode(proj_base=None, now=None, *, burn_fn=None) -> ModeVerdict:
    """Read the REAL burn and derive the mode. `burn_fn` (injectable) returns a
    rate factor or None; the default reads cost_gate.weekly_burn().rate_factor.
    Fail-open ABSOLUTE: any error or missing measurement -> GREEN (never a fake
    factor, never a raise)."""
    try:
        if burn_fn is not None:
            factor = burn_fn()
        else:
            from modules.wrapper.cost_gate import weekly_burn  # type: ignore
            factor = weekly_burn(proj_base=proj_base, now=now).rate_factor
        if factor is None:
            return ModeVerdict(GREEN, None, "failopen-green:no-burn-data")
        return ModeVerdict(compute_mode(float(factor)), float(factor), "real")
    except Exception:  # noqa: BLE001 -- fail-open
        return ModeVerdict(GREEN, None, "failopen-green:error")


class BudgetAuction:
    """ROI-priority arbitration of a shared budget. In Yellow+ the mesh funds the
    highest-ROI bids first; lower-ROI bids are advised to defer or downgrade.
    Advisory only -- it ranks and recommends, never kills a pane."""

    @staticmethod
    def rank(bids) -> list:
        """Bids by descending ROI (arrival order is NOT the tiebreak beyond ROI)."""
        return sorted(list(bids or []), key=lambda b: b.roi, reverse=True)

    @classmethod
    def arbitrate(cls, bids, mode: str, *, roi_threshold: float = DEFAULT_ROI_THRESHOLD):
        """Return advisory lines for below-threshold bids in Yellow+. Green -> no
        friction. Never blocks."""
        if mode == GREEN:
            return []
        lines = []
        for b in cls.rank(bids):
            if b.roi < roi_threshold:
                lines.append(
                    f"PP PM-04 [{mode}]: bid {b.sid} ROI {b.roi:.1f} < "
                    f"{roi_threshold:.1f} -- defer or downgrade (higher-ROI work "
                    f"funded first).")
        return lines


def budget_gate(mode_verdict: ModeVerdict, *, model: str = "", roi: float | None = None,
                roi_threshold: float = DEFAULT_ROI_THRESHOLD,
                opus_incumbents: int = 0, roi_justified: bool = False,
                repo: str = "") -> BudgetAdvisory:
    """Gate 2 (after PM-02's scope-gate): concurrency-mode + Opus-Singleton
    advisories. ALWAYS advisory (blocks=False) -- the Owner may ignore every line
    and execution continues (fail-open)."""
    mode = mode_verdict.mode
    if mode == GREEN:
        return BudgetAdvisory(GREEN, [], model, False)   # no friction

    lines: list[str] = []
    suggested = model

    # Opus needs ROI justification in Yellow+.
    if _is_opus(model) and not roi_justified:
        lines.append(
            f"PP PM-04 [{mode}]: Opus requested without ROI justification -- "
            f"consider Sonnet, or declare ROI >= {roi_threshold:.1f}.")
        suggested = "sonnet"
        # Opus Singleton: a 2nd Opus-heavy pane on the same repo in Yellow+.
        if opus_incumbents >= 1:
            lines.append(
                f"PP PM-04 Opus Singleton: {opus_incumbents} Opus-heavy pane(s) "
                f"already on {repo or 'this repo'}; a 2nd needs explicit "
                f"ROI >= {roi_threshold:.1f}.")

    if mode == RED:
        lines.append(
            "PP PM-04 [RED]: one heavy task at a time -- other panes should be "
            "review / index / docs / low-cost.")
    if mode == BLACK:
        lines.append(
            "PP PM-04 [BLACK]: burn > 2x normal -- /compact or /kclear before a "
            "new heavy prompt.")

    return BudgetAdvisory(mode, lines, suggested, False)


def main(argv=None) -> int:
    import argparse
    import os
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--proj-base", default=None)
    ap.add_argument("--model", default="")
    ap.add_argument("--roi", type=float, default=None)
    ap.add_argument("--opus-incumbents", type=int, default=0)
    ap.add_argument("--roi-justified", action="store_true")
    ap.add_argument("--repo", default=None)
    args = ap.parse_args(argv)
    mv = current_mode(proj_base=args.proj_base)
    g = budget_gate(mv, model=args.model, roi=args.roi,
                    opus_incumbents=args.opus_incumbents,
                    roi_justified=args.roi_justified,
                    repo=args.repo or os.getcwd())
    print(f"# mode={mv.mode} (factor="
          f"{mv.factor if mv.factor is not None else 'n/a'}, {mv.source})")
    for ln in g.lines:
        print(ln)
    if not g.lines:
        print(f"# no budget advisory (suggested_model={g.suggested_model or 'any'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
