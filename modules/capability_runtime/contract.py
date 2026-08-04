#!/usr/bin/env python3
"""contract.py -- the Capability Contract (CPP-APIR DS03).

The estate's registries are module-level (`liveness/reachability.py`),
skill-level (`skill_router`) or model-level (`cognitive_os/router`). None is
capability-level. This is that object.

A contract is the unit `applicability.py` ranks and `derivatives.py`
specializes. Validation is not decoration: four HR-APA rules are executable
here, and a contract that fails them is rejected rather than stored.

  HR-APA-006  no invisible activation  -> >=1 trigger AND >=1 consumer
  HR-APA-007  no unconsumed intelligence -> outputs require consumers
  HR-APA-009  activation must be reversible -> write surfaces require
              rollback AND kill_switch
  HR-APA-018  a capability must have an owner -> owner non-empty

Stdlib-only. Load is fail-open (a malformed file yields no contract, never a
crash); construction is fail-closed (an invalid contract raises).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = _PP_ROOT / "vault" / "capability_runtime" / "contracts"


class Cost(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Risk(str, Enum):
    REVERSIBLE = "reversible"
    LOCAL = "local"
    CROSS_CUTTING = "cross_cutting"
    ARCHITECTURE_CHANGING = "architecture_changing"
    PRODUCTION_CHANGING = "production_changing"
    SAFETY_CRITICAL = "safety_critical"


class Maturity(str, Enum):
    EXPERIMENTAL = "experimental"
    DEVELOPING = "developing"
    PROVEN = "proven"
    MATURE = "mature"


class FailureRisk(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Ordinal scales. Kept here so applicability.py never re-invents them.
COST_SCALE = {Cost.LOW: 1, Cost.MEDIUM: 2, Cost.HIGH: 3}
MATURITY_SCALE = {Maturity.EXPERIMENTAL: 1, Maturity.DEVELOPING: 2,
                  Maturity.PROVEN: 3, Maturity.MATURE: 4}
FAILURE_SCALE = {FailureRisk.NONE: 0, FailureRisk.LOW: 1, FailureRisk.MEDIUM: 2,
                 FailureRisk.HIGH: 3, FailureRisk.CRITICAL: 4}
# Risk classes that may never be activated without human escalation (HR-APA-010).
ESCALATING_RISK = frozenset({
    Risk.ARCHITECTURE_CHANGING, Risk.PRODUCTION_CHANGING, Risk.SAFETY_CRITICAL,
})


class ContractError(ValueError):
    """An invalid contract. Carries the violated rule id."""


@dataclass
class CapabilityContract:
    # identity
    id: str
    name: str
    owner: str
    sovereign_question: str = ""
    # boundary
    scope: list = field(default_factory=list)
    non_scope: list = field(default_factory=list)
    # activation
    triggers: list = field(default_factory=list)
    anti_triggers: list = field(default_factory=list)
    prerequisites: list = field(default_factory=list)
    required_evidence: list = field(default_factory=list)
    # flow
    inputs: list = field(default_factory=list)
    outputs: list = field(default_factory=list)
    consumers: list = field(default_factory=list)
    dependencies: list = field(default_factory=list)
    # authority
    permissions: list = field(default_factory=list)
    write_surfaces: list = field(default_factory=list)
    risk_class: Risk = Risk.REVERSIBLE
    # economics
    activation_cost: Cost = Cost.MEDIUM
    context_cost: Cost = Cost.MEDIUM
    operational_cost: Cost = Cost.LOW
    expected_leverage: Cost = Cost.MEDIUM
    failure_risk_if_omitted: FailureRisk = FailureRisk.MEDIUM
    # fitness
    maturity: Maturity = Maturity.DEVELOPING
    portable: bool = True
    compatible_runtimes: list = field(default_factory=list)
    # reversibility
    rollback: str = ""
    kill_switch: str = ""
    retirement_condition: str = ""
    # genealogy (set on derivatives; empty on a universal kernel)
    parent: str = ""
    version: str = "1.0.0"

    def __post_init__(self) -> None:
        self._coerce()
        self.validate()

    def _coerce(self) -> None:
        """Accept plain strings from JSON; normalize to enums."""
        for attr, enum_cls in (("risk_class", Risk), ("activation_cost", Cost),
                               ("context_cost", Cost), ("operational_cost", Cost),
                               ("expected_leverage", Cost),
                               ("failure_risk_if_omitted", FailureRisk),
                               ("maturity", Maturity)):
            val = getattr(self, attr)
            if not isinstance(val, enum_cls):
                try:
                    setattr(self, attr, enum_cls(str(val).lower()))
                except ValueError as exc:
                    raise ContractError(
                        f"{self.id}: {attr}={val!r} is not a valid "
                        f"{enum_cls.__name__}") from exc

    def validate(self) -> None:
        """Executable HR-APA rules. Raises ContractError naming the rule."""
        if not self.id or not self.name:
            raise ContractError("contract requires a non-empty id and name")
        if not str(self.owner).strip():
            raise ContractError(
                f"HR-APA-018 {self.id}: a capability must have an owner")
        if not self.triggers:
            raise ContractError(
                f"HR-APA-006 {self.id}: no trigger -- activation would be invisible")
        if not self.consumers:
            raise ContractError(
                f"HR-APA-006 {self.id}: no consumer -- activation would be invisible")
        if self.outputs and not self.consumers:
            raise ContractError(
                f"HR-APA-007 {self.id}: outputs with no consumer "
                "(unconsumed intelligence)")
        if self.write_surfaces and not (self.rollback and self.kill_switch):
            raise ContractError(
                f"HR-APA-009 {self.id}: write surfaces {self.write_surfaces} "
                "require both rollback and kill_switch")

    @property
    def escalates(self) -> bool:
        """HR-APA-010: automatic activation grants no authority to alter
        architecture or production. True => human escalation required."""
        return self.risk_class in ESCALATING_RISK

    def to_dict(self) -> dict:
        d = asdict(self)
        for k, v in d.items():
            if isinstance(v, Enum):
                d[k] = v.value
        return d


def from_dict(d: dict) -> CapabilityContract:
    known = {f for f in CapabilityContract.__dataclass_fields__}
    return CapabilityContract(**{k: v for k, v in d.items() if k in known})


def load_contracts(contracts_dir: Path | None = None) -> list:
    """Every valid contract on disk. Fail-open: an unreadable directory yields
    []; a malformed or invalid file is skipped, never fatal."""
    base = contracts_dir if contracts_dir is not None else CONTRACTS_DIR
    out: list = []
    try:
        paths = sorted(Path(base).glob("*.json"))
    except OSError:
        return out
    for p in paths:
        try:
            out.append(from_dict(json.loads(p.read_text(encoding="utf-8-sig"))))
        except (OSError, json.JSONDecodeError, ContractError, TypeError):
            continue
    return out


def save_contract(c: CapabilityContract, contracts_dir: Path | None = None) -> Path:
    """Atomically persist a validated contract."""
    base = Path(contracts_dir) if contracts_dir is not None else CONTRACTS_DIR
    base.mkdir(parents=True, exist_ok=True)
    p = base / f"{c.id}.json"
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(c.to_dict(), indent=2), encoding="utf-8")
    tmp.replace(p)
    return p


__all__ = [
    "CapabilityContract", "ContractError", "Cost", "Risk", "Maturity",
    "FailureRisk", "COST_SCALE", "MATURITY_SCALE", "FAILURE_SCALE",
    "ESCALATING_RISK", "CONTRACTS_DIR", "from_dict", "load_contracts",
    "save_contract",
]
