"""capability_runtime -- the capability layer (CPP-APIR Option A).

Every other registry in this estate is module-level (`liveness`), skill-level
(`skill_router`) or model-level (`cognitive_os`). This is the capability-level
one: a contract object, an applicability computation over it, and a governed
derivative registry.

Scope is deliberately narrow. It does NOT activate anything (the hook
dispatcher does), does NOT select models (CO-03 does), does NOT propose new
systems (D2A does), and does NOT persist activation records (CDP owns
provenance -- see vault/audits/apir/NON_DUPLICATION_LEDGER.md sec. 3).
"""
from modules.capability_runtime.contract import (
    CapabilityContract, ContractError, Cost, FailureRisk, Maturity, Risk,
    from_dict, load_contracts, save_contract,
)
from modules.capability_runtime.applicability import (
    Applicability, MissionContext, Verdict, compile_stack, evaluate,
    evaluate_all,
)
from modules.capability_runtime.derivatives import (
    Derivative, compute_delta, derive, is_stale, lineage, load_derivatives,
    save_derivative,
)

__all__ = [
    "CapabilityContract", "ContractError", "Cost", "FailureRisk", "Maturity",
    "Risk", "from_dict", "load_contracts", "save_contract",
    "Applicability", "MissionContext", "Verdict", "compile_stack", "evaluate",
    "evaluate_all",
    "Derivative", "compute_delta", "derive", "is_stale", "lineage",
    "load_derivatives", "save_derivative",
]
