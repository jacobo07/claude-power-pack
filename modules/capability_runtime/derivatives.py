#!/usr/bin/env python3
"""derivatives.py -- Governed Capability Derivatives (CPP-APIR DS07).

A project-specialized capability is a DERIVATIVE, not a copy: it keeps its
parent, its delta, and an upgrade path, so an improvement to the universal
kernel still reaches it.

This module is the enforcement surface for the two HR-APA rules that had none:

  HR-APA-016  no name-level specialization
              Renaming a capability is not specializing it. A derivative whose
              entire delta is naming is REJECTED. `universal-meta-systems`
              specializes by noun substitution and says so honestly -- that is
              the shape this rule exists to refuse as a *capability* delta.

  HR-APA-017  universal kernel integrity
              A derivative may not weaken an inherited boundary (non_scope,
              rollback, kill_switch) without an explicit, named, approved
              override.

Staleness is measured, not assumed: a derivative records the parent version it
was cut from, and goes stale when the parent moves past it.

Stdlib-only. Fail-open on load, fail-closed on derive.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.contract import (  # noqa: E402
    CapabilityContract, ContractError, from_dict,
)

DERIVATIVES_DIR = _PP_ROOT / "vault" / "capability_runtime" / "derivatives"

# Fields whose change is pure naming -- never, alone, a valid specialization.
NAMING_FIELDS = frozenset({
    "id", "name", "owner", "sovereign_question", "parent", "version",
})
# Inherited boundaries a derivative may not weaken unilaterally (HR-APA-017).
PROTECTED_FIELDS = ("non_scope", "rollback", "kill_switch")


@dataclass
class Derivative:
    """The genealogy record. Answers: from what, for whom, changed how,
    upgradeable how, and is it still current."""
    child_id: str
    parent_id: str
    parent_version: str
    project: str
    inherited: list = field(default_factory=list)
    overridden: list = field(default_factory=list)
    added: list = field(default_factory=list)
    approved_override: str = ""      # who approved a PROTECTED override
    upgrade_path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _substantive(delta: dict) -> dict:
    return {k: v for k, v in delta.items() if k not in NAMING_FIELDS}


def compute_delta(parent: CapabilityContract, child: CapabilityContract) -> dict:
    """Fields whose value differs. Order-insensitive for list fields, so a
    reordered list is not reported as a change."""
    out: dict = {}
    pd, cd = parent.to_dict(), child.to_dict()
    for k, pv in pd.items():
        cv = cd.get(k)
        if isinstance(pv, list) and isinstance(cv, list):
            if sorted(map(str, pv)) != sorted(map(str, cv)):
                out[k] = cv
        elif pv != cv:
            out[k] = cv
    return out


def derive(parent: CapabilityContract, project: str, overrides: dict,
           *, approved_override: str = "",
           upgrade_path: str = "") -> tuple:
    """Cut a project derivative from a universal parent.

    Returns (child_contract, derivative_record). Raises ContractError naming
    the violated rule. `overrides` carries the specialization -- the domain
    pack, runtime adapter, evidence adapter, quality and activation policy all
    land as field overrides here.
    """
    if not str(project).strip():
        raise ContractError("a derivative requires a project")

    base = parent.to_dict()
    base.update(overrides or {})
    base["parent"] = parent.id
    base["id"] = overrides.get("id") or f"{parent.id}@{project}"
    child = from_dict(base)          # re-validates every HR-APA contract rule

    delta = compute_delta(parent, child)
    subst = _substantive(delta)

    # HR-APA-016 -- naming is not specialization.
    if not subst:
        raise ContractError(
            f"HR-APA-016 {child.id}: delta is naming-only "
            f"({sorted(delta) or 'empty'}) -- renaming is not specialization")

    # HR-APA-017 -- an inherited boundary may not be weakened unilaterally.
    weakened = []
    for f_name in PROTECTED_FIELDS:
        if f_name not in delta:
            continue
        pv, cv = getattr(parent, f_name), getattr(child, f_name)
        if isinstance(pv, list):
            if set(map(str, pv)) - set(map(str, cv)):    # boundary removed
                weakened.append(f_name)
        elif pv and not cv:                              # guarantee dropped
            weakened.append(f_name)
    if weakened and not str(approved_override).strip():
        raise ContractError(
            f"HR-APA-017 {child.id}: weakens inherited {weakened} without an "
            "approved override -- name the approver in approved_override")

    rec = Derivative(
        child_id=child.id, parent_id=parent.id, parent_version=parent.version,
        project=str(project),
        inherited=sorted(k for k in parent.to_dict() if k not in delta),
        overridden=sorted(subst),
        added=sorted(k for k, v in subst.items()
                     if not getattr(parent, k, None) and v),
        approved_override=str(approved_override),
        upgrade_path=upgrade_path or f"re-derive from {parent.id} v{parent.version}",
    )
    return child, rec


def is_stale(rec: Derivative, parent: CapabilityContract) -> bool:
    """True when the parent has moved past the version this was cut from."""
    def parts(v):
        try:
            return tuple(int(x) for x in str(v).split("."))
        except ValueError:
            return (0,)
    return parts(parent.version) > parts(rec.parent_version)


def lineage(child_id: str, records=None, derivatives_dir=None) -> list:
    """Genealogy chain from a derivative up to its root. Cycle-safe."""
    recs = records if records is not None else load_derivatives(derivatives_dir)
    by_child = {r.child_id: r for r in recs}
    chain, seen, cur = [], set(), child_id
    while cur in by_child and cur not in seen:
        seen.add(cur)
        chain.append(cur)
        cur = by_child[cur].parent_id
    if cur and cur not in seen:
        chain.append(cur)
    return chain


def load_derivatives(derivatives_dir=None) -> list:
    base = Path(derivatives_dir) if derivatives_dir is not None else DERIVATIVES_DIR
    out: list = []
    try:
        paths = sorted(base.glob("*.json"))
    except OSError:
        return out
    known = set(Derivative.__dataclass_fields__)
    for p in paths:
        try:
            d = json.loads(p.read_text(encoding="utf-8-sig"))
            out.append(Derivative(**{k: v for k, v in d.items() if k in known}))
        except (OSError, json.JSONDecodeError, TypeError):
            continue
    return out


def save_derivative(rec: Derivative, derivatives_dir=None) -> Path:
    base = Path(derivatives_dir) if derivatives_dir is not None else DERIVATIVES_DIR
    base.mkdir(parents=True, exist_ok=True)
    p = base / f"{rec.child_id.replace('/', '_').replace('@', '_at_')}.json"
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rec.to_dict(), indent=2), encoding="utf-8")
    tmp.replace(p)
    return p


__all__ = [
    "Derivative", "DERIVATIVES_DIR", "NAMING_FIELDS", "PROTECTED_FIELDS",
    "compute_delta", "derive", "is_stale", "lineage", "load_derivatives",
    "save_derivative",
]
