"""what_now_tracked -- what_now() plus IAS-C2 opportunity-cost recording.

`what_now()` in engine.py stays a pure function (untouched, zero regression
risk to its existing callers/contract). This wrapper is the real, live
consumer IAS-C2's Opportunity Cost Ledger needed (CGF Workstream E): every
time the backlog decision model picks a recommendation, the highest-ranked
alternative it did NOT pick is logged as a foregone demand (Part V §5.3), and
any previously-foregone item that gets picked on a later call settles
CONFIRMED (Part V §5.4) -- a real ROI decision (which backlog item to work on
now) now feeds a real ledger, not a dataset sitting idle next to its spec.
"""
from __future__ import annotations

from modules.ias_c2 import rank_and_forgo, record_opportunity_cost, settle_if_later_chosen

from .engine import BacklogItem, WhatNowResult, _score, what_now


def what_now_tracked(backlog: list[BacklogItem]) -> WhatNowResult:
    """Same recommendation as what_now(); additionally records/settles an
    IAS-C2 opportunity cost entry as a side effect. Fail-open: any ledger
    error never changes or blocks the recommendation itself."""
    result = what_now(backlog)
    if result.recommended is None:
        return result
    try:
        settle_if_later_chosen(result.recommended)
        candidates = [i for i in backlog if not i.done and not i.blockers]
        foregone = rank_and_forgo(candidates, result.recommended, _score)
        record_opportunity_cost(result.recommended, foregone)
    except Exception:  # noqa: BLE001 -- the ledger must never break the recommendation
        pass
    return result


__all__ = ["what_now_tracked"]
