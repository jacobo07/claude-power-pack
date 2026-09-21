#!/usr/bin/env python3
"""archetypes.py -- the surface archetypes, as DATA, and a three-valued evaluator.

AN ARCHETYPE IS A TOPOLOGY AND A CONSTRAINT STRATEGY, NOT A TEMPLATE.

Each entry below declares what must hold for it to be justified, what disqualifies it,
what it must carry if chosen, and how it fails. Conditions are tuples rather than
lambdas so the registry can be read, diffed, and drift-checked against the dataset part
by a gate -- a predicate hidden in a closure is a rule nobody can audit.

THERE IS NO GLOBAL RANKING, deliberately. A weight would encode a preference the
evidence does not support, and "identity-first is worse" is exactly the kind of
universal claim LAW 10 refuses on one product's evidence. Selection is by context: an
archetype is justified, disqualified, or undecidable, and the resolver breaks a genuine
tie by refusing rather than by picking.

THE EVALUATOR IS THREE-VALUED, and that is the load-bearing part. A condition over a
fact nobody measured returns UNKNOWN, never False. Two-valued evaluation would silently
convert "we did not look" into "this archetype does not apply", which is the same
defect `context.py` exists to prevent, one layer up.

DOMAIN BLINDNESS: every id and every string here is a kernel noun. A vertical supplies
its own vocabulary through a DomainPack; naming one here would make that vertical's
derivative fail `contaminates_kernel`.

Stdlib-only.
"""
from __future__ import annotations

from dataclasses import dataclass

YES = "YES"
NO = "NO"
UNKNOWN = "UNKNOWN"

# Condition operators. Small on purpose: an operator set that can express anything can
# also express a rule nobody can read.
_OPS = ("is", "is_not", "truthy", "falsy", "present", "absent", "in", "not_in")


@dataclass(frozen=True)
class Archetype:
    """One topology. `requires` must all hold; any `disqualifiers` holding kills it."""
    id: str
    summary: str
    requires: tuple = ()
    disqualifiers: tuple = ()
    safeguards: tuple = ()
    failure_modes: tuple = ()
    fallback: str = ""


def _test(cond: tuple, ctx) -> str:
    """Evaluate one (field, op, value?) condition three-valued.

    An unmeasured field yields UNKNOWN for every operator EXCEPT `present`/`absent`,
    which are questions *about* measurement and are therefore always answerable.
    """
    field, op = cond[0], cond[1]
    expected = cond[2] if len(cond) > 2 else None
    val = getattr(ctx, field, None)

    if op == "present":
        return YES if val is not None else NO
    if op == "absent":
        return YES if val is None else NO
    if val is None:
        return UNKNOWN

    if op == "is":
        return YES if val == expected else NO
    if op == "is_not":
        return YES if val != expected else NO
    if op == "truthy":
        return YES if bool(val) else NO
    if op == "falsy":
        return YES if not bool(val) else NO
    if op == "in":
        return YES if val in (expected or ()) else NO
    if op == "not_in":
        return YES if val not in (expected or ()) else NO
    # An unrecognised operator is a registry defect, not a context defect. Fail
    # toward UNKNOWN so it surfaces as an unanswerable question rather than as a
    # confident NO that quietly disqualifies a valid archetype.
    return UNKNOWN


def _render(cond: tuple) -> str:
    if len(cond) > 2:
        return f"{cond[0]} {cond[1]} {cond[2]!r}"
    return f"{cond[0]} {cond[1]}"


def evaluate(arch: Archetype, ctx) -> tuple:
    """(verdict, reasons). YES = justified, NO = disqualified, UNKNOWN = cannot say."""
    reasons: list = []
    unknowns: list = []

    for cond in arch.disqualifiers:
        r = _test(cond, ctx)
        if r == YES:
            reasons.append(f"disqualified: {_render(cond)}")
            return NO, reasons
        if r == UNKNOWN:
            unknowns.append(f"unmeasured disqualifier: {_render(cond)}")

    for cond in arch.requires:
        r = _test(cond, ctx)
        if r == NO:
            reasons.append(f"requirement unmet: {_render(cond)}")
            return NO, reasons
        if r == UNKNOWN:
            unknowns.append(f"unmeasured requirement: {_render(cond)}")

    if unknowns:
        return UNKNOWN, unknowns
    return YES, [f"satisfied: {_render(c)}" for c in arch.requires] or ["no requirement"]


# --------------------------------------------------------------------- registry
#
# Ids are STABLE: the dataset part and the drift gate pin these strings, and the
# resolver may cite no id that is not here.

REGISTRY: tuple = (
    Archetype(
        id="IDENTITY_FIRST",
        summary="A known party is established before anything else happens.",
        requires=(("identity_driver", "is_not", "none"),),
        disqualifiers=(("value_before_identity_possible", "truthy"),),
        safeguards=("state what identity buys before requesting it",
                    "offer the returning-party path at the same boundary"),
        failure_modes=("premature boundary: identity demanded before any justified need",
                       "abandonment concentrated at the first interaction"),
        fallback="INTENT_FIRST",
    ),
    Archetype(
        id="INTENT_FIRST",
        summary="What the party wants is captured before anything is asked of them.",
        requires=(("primary_intent", "present"),),
        disqualifiers=(("invitation_based", "truthy"),),
        safeguards=("intent must narrow later questions, or it is decoration",),
        failure_modes=("intent captured and then ignored by the next step",),
        fallback="STRUCTURED_CONFIGURATOR",
    ),
    Archetype(
        id="WORK_FIRST",
        summary="Useful work begins before a durable owner exists.",
        requires=(("work_possible_before_identity", "truthy"),
                  ("value_before_identity_possible", "truthy")),
        disqualifiers=(("regulated", "truthy"),
                       ("assurance_required", "truthy"),
                       ("abuse_risk", "is", "high")),
        safeguards=("work must survive the identity boundary in every branch",
                    "disclose any later gate before the work is invested"),
        failure_modes=("work lost at the identity boundary",
                       "a foreseeable gate revealed after substantial investment"),
        fallback="VALUE_FIRST",
    ),
    Archetype(
        id="VALUE_FIRST",
        summary="A result is demonstrated or delivered before anything is requested.",
        requires=(("first_meaningful_value", "present"),
                  ("value_before_identity_possible", "truthy")),
        disqualifiers=(("payment_before_value", "truthy"),
                       ("assurance_required", "truthy")),
        safeguards=("the demonstrated result must be the real one, not a mock",),
        failure_modes=("demonstrated value the product cannot actually deliver",),
        fallback="INTENT_FIRST",
    ),
    Archetype(
        id="ARTIFACT_FIRST",
        summary="An artifact the party already holds seeds the work and resolves facts.",
        requires=(("artifacts_available", "truthy"),),
        disqualifiers=(),
        safeguards=("every fact extracted from an artifact carries its provenance",
                    "extracted facts are correctable before they are consequential"),
        failure_modes=("invisible inference: an extracted fact used without review",
                       "two artifacts disagree and the conflict is hidden"),
        fallback="STRUCTURED_CONFIGURATOR",
    ),
    Archetype(
        id="INTEGRATION_FIRST",
        summary="An authorised external source is connected and resolves many facts at once.",
        requires=(("integrations_available", "truthy"),),
        disqualifiers=(),
        safeguards=("authorisation scope is stated before it is requested",
                    "retrieved facts are distinguishable from supplied ones"),
        failure_modes=("stale external data presented as current",
                       "an authorisation broader than the stated purpose"),
        fallback="ARTIFACT_FIRST",
    ),
    Archetype(
        id="INVITATION_FIRST",
        summary="Entry is predicated on an invitation that already carries context.",
        requires=(("invitation_based", "truthy"),),
        disqualifiers=(),
        safeguards=("an expired or reused invitation has a defined, non-dead-end state",),
        failure_modes=("invitation context discarded, so the party is asked what the "
                       "invitation already answered",),
        fallback="IDENTITY_FIRST",
    ),
    Archetype(
        id="NARRATIVE_BOOTSTRAP",
        summary="Free description bootstraps the work; structure is derived from it.",
        requires=(("primary_intent", "present"),),
        disqualifiers=(("external_consequences", "truthy"),
                       ("regulated", "truthy")),
        safeguards=("derived structure is shown and correctable before it is acted on",),
        failure_modes=("over-conversation where a structured control would be faster",
                       "ambiguity accepted where consequence requires precision"),
        fallback="STRUCTURED_CONFIGURATOR",
    ),
    Archetype(
        id="STRUCTURED_CONFIGURATOR",
        summary="Bounded choices assemble the work; every question justifies itself.",
        requires=(),
        disqualifiers=(),
        safeguards=("each question names what it unlocks",),
        failure_modes=("schema-driven friction: a question exists because a column does",
                       "wizard theater: one long form split across attractive pages"),
        fallback="",
    ),
    Archetype(
        id="RETURNING_PARTY_RESOLUTION",
        summary="An already-known party is recognised and routed, not re-enrolled.",
        requires=(("returning_parties_exist", "truthy"),),
        disqualifiers=(),
        safeguards=("the escape is reachable from the first surface, not a later one",),
        failure_modes=("a returning party driven through the new-party path",
                       "an existing-record collision presented as an error"),
        fallback="IDENTITY_FIRST",
    ),
    Archetype(
        id="EPHEMERAL_TO_DURABLE",
        summary="Work begins without a durable owner and is later bound to one.",
        requires=(("work_possible_before_identity", "truthy"),
                  ("work_survives_interruption", "truthy")),
        disqualifiers=(("regulated", "truthy"),),
        safeguards=("binding is defined for success, failure, cancellation, expiry, "
                    "collision, duplicate submission and cross-device resume",),
        failure_modes=("ephemeral work bound twice",
                       "work unrecoverable after an interruption"),
        fallback="WORK_FIRST",
    ),
)

BY_ID = {a.id: a for a in REGISTRY}
IDS = tuple(a.id for a in REGISTRY)


def classify(ctx) -> dict:
    """Every archetype against one context. {id: (verdict, reasons)}."""
    return {a.id: evaluate(a, ctx) for a in REGISTRY}


__all__ = ["Archetype", "REGISTRY", "BY_ID", "IDS", "evaluate", "classify",
           "YES", "NO", "UNKNOWN"]
