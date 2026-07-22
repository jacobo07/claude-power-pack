"""IAS-C2 -- Capability Demand Forecasting & Opportunity Cost (executable slice).

The full corpus (vault/knowledge_base/cpp_ias/03_CAPABILITY_ECONOMICS/
ias_c2_demand_forecasting.txt, SEALED, 18 Parts) specifies a four-subengine
forecasting engine over five signal classes. This package does not build that
engine -- Non-Duplication Ledger Candidate 24 (Opportunity Cost) is buildable
today against an EXISTING ranked-alternatives source, and building the full
forecasting apparatus first would be exactly the disproportionate, duplicative
build the CGF audit's "build only the confirmed gap, narrowly" verdict warns
against. This slice implements Part V (Opportunity Cost) and Part VI (the
Ledger) directly against `backlog_autopilot`'s real, already-ranked candidate
list -- the same real data `what_now()` already scores, reused rather than
re-derived, per Part V §5.3's ranking requirement.
"""
from .opportunity_cost import (
    OpportunityCostRecord,
    domain_aggregate,
    ledger_path,
    rank_and_forgo,
    record_opportunity_cost,
    settle_if_later_chosen,
)

__all__ = [
    "OpportunityCostRecord",
    "domain_aggregate",
    "ledger_path",
    "rank_and_forgo",
    "record_opportunity_cost",
    "settle_if_later_chosen",
]
