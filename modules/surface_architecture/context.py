#!/usr/bin/env python3
"""context.py -- the measured facts a surface-architecture decision stands on.

EVERY FIELD IS OPTIONAL, AND THAT IS THE WHOLE DESIGN.

A record whose fields default to False, 0 or "" cannot distinguish "we measured this
and it is false" from "nobody looked". Those are different states of the world, and
collapsing them is how an absence of evidence becomes a confident answer: a rule
written `if cost > threshold and count > 0` silently cannot fire when `count` defaults
to zero, so the *missing* measurement is what makes the subject look healthy.

So a fact here is three-valued, exactly as `done_gate/strength_ladder` grades evidence
and `cdio/scorer` scores a review:

    True / a value   measured, and it is this
    False / a value  measured, and it is that
    None             nobody looked -- never a default, never a pass

`missing_material_facts()` names the second-kind absences. A caller that ignores it
gets UNDETERMINED from the resolver, not a guess.

DOMAIN BLINDNESS: no field here may be named for a domain. `identity_driver` is a
kernel noun; an equivalent named for one vertical would make that vertical's derivative
fail `contaminates_kernel`. See the package docstring.

Stdlib-only.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

# Closed vocabularies. A value outside these is a caller error, reported by
# `invalid_values()` rather than silently coerced -- an unrecognised string that
# resolves to the safest branch is indistinguishable from a measured one.
IDENTITY_DRIVERS = frozenset({
    "regulation",       # a rule outside the product requires a known party
    "abuse",            # anonymous use is economically or operationally unsafe
    "persistence",      # the work cannot survive without a durable owner
    "economics",        # the unit cost of anonymous use is not bearable
    "collaboration",    # more than one party must address the same work
    "external_effect",  # the product acts on the world on someone's behalf
    "none",             # measured: nothing requires a known party
})

RISK_LEVELS = frozenset({"low", "medium", "high"})
TENANCY = frozenset({"none", "individual", "organisation"})

# Facts without which no archetype can be justified. Deliberately SHORT: a long
# material list makes the resolver refuse everything, which is its own wrong answer.
# Each entry earns its place by being a fact that changes WHICH archetype wins, not
# merely one that is nice to know.
MATERIAL_FACTS: tuple[str, ...] = (
    "first_meaningful_value",
    "value_before_identity_possible",
    "identity_driver",
    "returning_parties_exist",
)


@dataclass
class SurfaceContext:
    """What is known about a product's entry surface. Absent facts stay absent."""

    # --- what the product is and what it is for
    product_kind: str | None = None
    primary_actor: str | None = None
    primary_intent: str | None = None

    # --- value
    first_meaningful_value: str | None = None
    value_before_identity_possible: bool | None = None
    value_requires_external_call: bool | None = None

    # --- identity and assurance
    identity_driver: str | None = None           # one of IDENTITY_DRIVERS
    assurance_required: bool | None = None        # a verified, not merely known, party
    regulated: bool | None = None
    sensitive_data: bool | None = None

    # --- work and persistence
    work_possible_before_identity: bool | None = None
    work_survives_interruption: bool | None = None

    # --- available shortcuts: each one can collapse many questions at once
    integrations_available: list | None = None
    artifacts_available: list | None = None       # documents the party already holds
    invitation_based: bool | None = None

    # --- population and shape
    returning_parties_exist: bool | None = None
    tenancy: str | None = None                    # one of TENANCY
    abuse_risk: str | None = None                 # one of RISK_LEVELS

    # --- commitment
    payment_before_value: bool | None = None
    external_consequences: bool | None = None

    # --- provenance of this record itself
    source: str = ""

    # ---------------------------------------------------------------- queries

    def missing_material_facts(self) -> list:
        """Material facts nobody measured. Sorted, so a diff is stable."""
        return sorted(n for n in MATERIAL_FACTS if getattr(self, n, None) is None)

    def invalid_values(self) -> list:
        """(field, value) pairs outside a closed vocabulary. Empty means clean.

        Reported rather than raised: a caller assembling a context incrementally is
        not yet wrong, and the resolver is the authority that refuses.
        """
        out = []
        for name, allowed in (("identity_driver", IDENTITY_DRIVERS),
                              ("tenancy", TENANCY),
                              ("abuse_risk", RISK_LEVELS)):
            val = getattr(self, name, None)
            if val is not None and str(val).strip().lower() not in allowed:
                out.append((name, val))
        return sorted(out)

    def measured(self) -> list:
        """Every field somebody actually looked at. The complement of absence."""
        return sorted(f.name for f in fields(self)
                      if f.name != "source" and getattr(self, f.name) is not None)

    @property
    def is_decidable(self) -> bool:
        return not self.missing_material_facts() and not self.invalid_values()

    def to_dict(self) -> dict:
        return asdict(self)


def from_dict(d: dict) -> SurfaceContext:
    """Build from JSON. Unknown keys are dropped rather than raising, so a fixture
    written against a later version still loads; missing keys stay None, which is the
    honest reading of a key nobody wrote."""
    known = {f.name for f in fields(SurfaceContext)}
    return SurfaceContext(**{k: v for k, v in (d or {}).items() if k in known})


def load(path: str | Path) -> SurfaceContext:
    """Read one context file. `utf-8-sig` because Windows tooling emits a BOM and
    `json.loads` throws on it -- a trap this estate has already paid for twice."""
    return from_dict(json.loads(Path(path).read_text(encoding="utf-8-sig")))


__all__ = [
    "SurfaceContext", "MATERIAL_FACTS", "IDENTITY_DRIVERS", "RISK_LEVELS",
    "TENANCY", "from_dict", "load",
]
