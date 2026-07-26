"""reasoning_route.py -- CPCSC Tier-B B3: the reasoning-execution axis
(CO-03 x one_shot).

Two systems each decide part of "who executes this task's reasoning" and
neither reads the other. CO-03 (`modules/cost_collapse/router.py::route`)
keyword-matches a task description to a `RouteClass` (NANO/MICRO/MACRO/
ULTRA), a model, and a budget ceiling -- cheap, stateless, re-derivable
from the description alone. `one_shot.compiler.compile_contract` freezes
an Owner-declared `size` (S/M/L/XL) into a budget ceiling for the SAME
description, but the size is a caller-supplied literal, never checked
against what CO-03 would independently route -- so a MACRO-keyword
description ("architect...", "refactor across...") can be compiled at
size="S" with no signal, and `OneShotContract` carries no model field at
all. A third site, `one_shot.escalation.recommend_action`, names a model
by BARE STRING ("escalate-to-opus") with no tie to CO-03's actual model
IDs. Three places decide or imply a model/budget for one task; none of
them compose.

This module is the composition, decision-agnostic and additive -- it
reads both existing systems and surfaces a coherence signal; it changes
neither's authority. `compile_contract`'s Owner-declared size stays the
one source of truth for the frozen contract (composed, never overridden,
the same discipline DRK-03 already applies to ACIS: read, never set); CO-03
stays the one source of truth for model IDs and route classes.

  recommend_route(contract)   -- CO-03's route for the contract's own
                                  description, checked for coherence
                                  against the Owner-declared budget
                                  ceiling. Mirrors the established
                                  `decision_review/providers.py::route_for`
                                  adapter (same CO-03 call, same shape) for
                                  a distinct consumer: contract coherence
                                  at compile time, not a decision verdict.
  model_for_action(action)    -- resolves `escalation.recommend_action`'s
                                  bare "escalate-to-opus" string to CO-03's
                                  real model ID. Every other action (no
                                  escalation, or the Owner-decision STOP)
                                  resolves to None -- a model is recommended
                                  only for the one action that actually
                                  names one.

Fail-open ABSOLUTE: empty/unavailable input returns None -- an honest
absence (DAIF-01 2.6: unknown is a value, absent is a defect; this module
declares absence rather than fabricating an agreement or a guessed model).
"""
from __future__ import annotations

from dataclasses import dataclass

from .compiler import OneShotContract

# HR-COST-002 (sealed, ~/.claude/CLAUDE.md): "STOP if estimated cost > 2x
# task budget." Reused verbatim as the coherence threshold rather than a
# fresh number -- the estate already named the multiplier at which a cost
# divergence is dangerous; this composes that number, it does not re-derive it.
_DIVERGENCE_MULTIPLIER = 2.0

# The one escalation.py action that names a model at all (see module docstring).
_ESCALATE_ACTION = "escalate-to-opus"


@dataclass(frozen=True)
class RouteRecommendation:
    route_class: str
    model: str
    max_budget: float
    agrees_with_declared_size: bool
    note: str


def recommend_route(contract: OneShotContract):
    """CO-03's route for `contract.description`, checked against the
    Owner-declared `contract.budget_usd`.

    Returns None when the description is empty or CO-03 is unavailable --
    an honest absence, never a fabricated agreement.
    """
    try:
        desc = (contract.description or "").strip()
        if not desc:
            return None
        from modules.cost_collapse.router import route
        r = route(desc)
        declared = float(contract.budget_usd)
        derived = float(r.max_budget)
        agrees = derived <= declared * _DIVERGENCE_MULTIPLIER
        if agrees:
            note = "declared budget covers the CO-03-derived route"
        else:
            note = (
                f"CO-03 derives {r.route_class.name} (${derived:.2f}), more than "
                f"{_DIVERGENCE_MULTIPLIER:.0f}x the declared ${declared:.2f} -- "
                "the description may need a larger size or a narrower scope"
            )
        return RouteRecommendation(
            route_class=r.route_class.name,
            model=r.model,
            max_budget=derived,
            agrees_with_declared_size=agrees,
            note=note,
        )
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return None


def model_for_action(action: str):
    """Resolve an `escalation.recommend_action` result to a real CO-03
    model ID. Only "escalate-to-opus" names one; every other action
    (proceed, retry-same-model, stop-and-escalate-to-Owner) returns None --
    the STOP action is an Owner decision (HR-ONESHOT-003), not a model pick.
    """
    try:
        if (action or "").strip() != _ESCALATE_ACTION:
            return None
        from modules.cost_collapse.router import MODEL_MACRO
        return MODEL_MACRO
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return None
