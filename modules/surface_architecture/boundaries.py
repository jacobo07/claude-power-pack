#!/usr/bin/env python3
"""boundaries.py -- where the boundaries of an entry surface fall, and why.

A BOUNDARY IS A POSITION ON A PATH, NOT A STEP NUMBER.

Encoding "identity is step 3" bakes one product's topology into every product. What
transfers is the *reasoning*: there is a point before which a boundary cannot be
justified, and a point after which postponing it costs something. Those two are
computed from different facts, and the interesting result is when they cross -- a
product whose earliest justified position is LATER than its latest safe one has a
contradiction, and saying so is more useful than picking a number.

EVERY PLACEMENT CARRIES ITS BASIS. A position with no named fact behind it is an
opinion wearing a coordinate, so `basis` is populated from the context fields actually
read, and a placement that could not be computed is UNDETERMINED rather than a default.

Stdlib-only. Domain-blind: `PATH` names phases of any entry surface.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Ordered phases of an entry path. Index is position; later strictly follows earlier.
PATH: tuple = ("entry", "intent", "work", "value", "effect", "commitment")

PLACED = "PLACED"
UNDETERMINED = "UNDETERMINED"
CONFLICT = "CONFLICT"
NOT_APPLICABLE = "NOT_APPLICABLE"

# Which phase each identity driver first bites at. `none` is absent on purpose: a
# measured "nothing requires a known party" has no earliest justified position at all,
# which is a different statement from "it bites at the end".
_DRIVER_ONSET = {
    "regulation": "entry",
    "external_effect": "effect",
    "abuse": "work",
    "economics": "work",
    "collaboration": "work",
    "persistence": "value",
}


@dataclass
class Placement:
    """One boundary's position, or an honest refusal to place it."""
    boundary: str
    status: str
    position: str = ""
    basis: list = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {"boundary": self.boundary, "status": self.status,
                "position": self.position, "basis": list(self.basis),
                "note": self.note}


def _idx(phase: str) -> int:
    return PATH.index(phase) if phase in PATH else -1


def earliest_justified_identity(ctx) -> Placement:
    """The first phase at which requesting a known party is justified by a NEED.

    Not the first phase at which it is *possible* -- that is always `entry`, and a
    surface that treats possibility as justification is how identity becomes the
    default first step rather than a decision.
    """
    driver = ctx.identity_driver
    if driver is None:
        return Placement("identity.earliest_justified", UNDETERMINED,
                         note="identity_driver was never measured")
    driver = str(driver).strip().lower()
    if driver == "none":
        return Placement("identity.earliest_justified", NOT_APPLICABLE,
                         basis=["identity_driver=none"],
                         note="measured: no need justifies a known party at any phase")
    onset = _DRIVER_ONSET.get(driver)
    if onset is None:
        return Placement("identity.earliest_justified", UNDETERMINED,
                         basis=[f"identity_driver={driver}"],
                         note="driver outside the closed vocabulary; not placed")
    return Placement("identity.earliest_justified", PLACED, onset,
                     basis=[f"identity_driver={driver}"])


def latest_safe_identity(ctx) -> Placement:
    """The last phase after which postponing identity LOSES something.

    Driven by whether work can exist before a durable owner and whether it survives an
    interruption -- the two facts that decide whether postponement is free or costly.
    """
    can_work = ctx.work_possible_before_identity
    survives = ctx.work_survives_interruption
    if can_work is None:
        return Placement("identity.latest_safe", UNDETERMINED,
                         note="work_possible_before_identity was never measured")
    if not can_work:
        return Placement("identity.latest_safe", PLACED, "work",
                         basis=["work_possible_before_identity=False"],
                         note="no work exists before a durable owner, so postponing "
                              "past this phase postpones the product itself")
    if survives is None:
        return Placement("identity.latest_safe", UNDETERMINED,
                         basis=["work_possible_before_identity=True"],
                         note="work_survives_interruption was never measured, so the "
                              "cost of postponement cannot be established")
    if not survives:
        return Placement("identity.latest_safe", PLACED, "work",
                         basis=["work_possible_before_identity=True",
                                "work_survives_interruption=False"],
                         note="work does not survive an interruption, so postponing "
                              "past the work phase risks losing it")
    return Placement("identity.latest_safe", PLACED, "effect",
                     basis=["work_possible_before_identity=True",
                            "work_survives_interruption=True"],
                     note="work survives, so identity may be postponed until the "
                          "product acts on the world")


def value_boundary(ctx) -> Placement:
    if ctx.first_meaningful_value is None:
        return Placement("value", UNDETERMINED,
                         note="first_meaningful_value was never measured; a surface "
                              "whose value is unnamed cannot order anything against it")
    before = ctx.value_before_identity_possible
    if before is None:
        return Placement("value", UNDETERMINED,
                         basis=["first_meaningful_value present"],
                         note="value_before_identity_possible was never measured")
    return Placement("value", PLACED, "value" if before else "commitment",
                     basis=[f"value_before_identity_possible={before}"],
                     note="value precedes the identity boundary" if before
                          else "value is only reachable after commitment")


def assurance_boundary(ctx) -> Placement:
    if ctx.assurance_required is None:
        return Placement("assurance", UNDETERMINED,
                         note="assurance_required was never measured")
    if not ctx.assurance_required:
        return Placement("assurance", NOT_APPLICABLE,
                         basis=["assurance_required=False"],
                         note="a known party suffices; no verified party is required")
    return Placement("assurance", PLACED, "effect",
                     basis=["assurance_required=True"],
                     note="verification must complete before the product acts")


def consent_boundary(ctx) -> Placement:
    sensitive = ctx.sensitive_data
    external = ctx.external_consequences
    if sensitive is None and external is None:
        return Placement("consent", UNDETERMINED,
                         note="neither sensitive_data nor external_consequences "
                              "was measured")
    basis = [f"sensitive_data={sensitive}", f"external_consequences={external}"]
    if external:
        return Placement("consent", PLACED, "effect", basis=basis,
                         note="consent precedes any act with consequences outside "
                              "the product")
    if sensitive:
        return Placement("consent", PLACED, "work", basis=basis,
                         note="consent precedes the collection it authorises")
    return Placement("consent", NOT_APPLICABLE, basis=basis,
                     note="measured: nothing sensitive and no external consequence")


def commitment_boundary(ctx) -> Placement:
    pay = ctx.payment_before_value
    if pay is None:
        return Placement("commitment", UNDETERMINED,
                         note="payment_before_value was never measured")
    return Placement("commitment", PLACED, "value" if pay else "commitment",
                     basis=[f"payment_before_value={pay}"],
                     note="commitment is demanded before value is delivered -- this "
                          "is a disclosed wall, or it is a surprise one" if pay
                          else "commitment follows delivered value")


def persistence_boundary(ctx) -> Placement:
    can_work = ctx.work_possible_before_identity
    survives = ctx.work_survives_interruption
    if can_work is None or survives is None:
        return Placement("persistence", UNDETERMINED,
                         note="persistence follows from work_possible_before_identity "
                              "and work_survives_interruption; at least one is unmeasured")
    basis = [f"work_possible_before_identity={can_work}",
             f"work_survives_interruption={survives}"]
    if can_work and survives:
        return Placement("persistence", PLACED, "work", basis=basis,
                         note="durable storage is required before a durable owner "
                              "exists -- persistence is not identity")
    return Placement("persistence", PLACED, "value", basis=basis,
                     note="persistence coincides with a durable owner")


def activation_boundary(ctx) -> Placement:
    if ctx.first_meaningful_value is None:
        return Placement("activation", UNDETERMINED,
                         note="activation is defined relative to first_meaningful_value, "
                              "which was never measured")
    return Placement("activation", PLACED, "value",
                     basis=[f"first_meaningful_value={ctx.first_meaningful_value!r}"],
                     note="activation is the delivery of the named value, not the "
                          "creation of a record")


def identity_boundary(ctx) -> Placement:
    """Reconcile the earliest justified and latest safe positions.

    The valuable outcome is the CONFLICT: a product whose need bites later than its
    cost of postponement has no valid position, and naming that is worth more than
    choosing one of the two and hiding the tension.
    """
    early, late = earliest_justified_identity(ctx), latest_safe_identity(ctx)
    basis = list(early.basis) + list(late.basis)

    if early.status == NOT_APPLICABLE and late.status == PLACED:
        return Placement("identity", PLACED, late.position, basis=basis,
                         note="no need justifies identity; it is placed at the latest "
                              "safe position and is a convenience, not a gate")
    if early.status != PLACED or late.status != PLACED:
        unknown = [p.note for p in (early, late) if p.status == UNDETERMINED]
        return Placement("identity", UNDETERMINED, basis=basis,
                         note="; ".join(unknown) or "one side could not be placed")

    if _idx(early.position) > _idx(late.position):
        return Placement("identity", CONFLICT, basis=basis,
                         note=f"earliest justified ({early.position}) falls after "
                              f"latest safe ({late.position}): no position satisfies "
                              "both, so the product's constraints are contradictory")
    return Placement("identity", PLACED, early.position, basis=basis,
                     note=f"justified from {early.position}; postponement is safe "
                          f"until {late.position}")


PLANNERS = (
    ("value", value_boundary),
    ("identity", identity_boundary),
    ("persistence", persistence_boundary),
    ("assurance", assurance_boundary),
    ("consent", consent_boundary),
    ("commitment", commitment_boundary),
    ("activation", activation_boundary),
)

BOUNDARY_NAMES = tuple(n for n, _ in PLANNERS)


def plan(ctx) -> list:
    """Every boundary for one context, in path order."""
    return [fn(ctx) for _, fn in PLANNERS]


__all__ = ["Placement", "PATH", "PLANNERS", "BOUNDARY_NAMES", "plan",
           "identity_boundary", "earliest_justified_identity", "latest_safe_identity",
           "PLACED", "UNDETERMINED", "CONFLICT", "NOT_APPLICABLE"]
