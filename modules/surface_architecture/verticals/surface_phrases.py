#!/usr/bin/env python3
"""surface_phrases.py -- the domain vocabulary two artifact kinds both read.

WHY THIS MODULE EXISTS
----------------------
`prd_adapter.py` owned this vocabulary alone while a PRD baseline was the only
artifact that could reach surface architecture. A second artifact kind
(`design_md`) needs the SAME judgement about the SAME words, and there are only
two ways to give it one:

  COPY the tuples into the new adapter  -- correct on the day it is written and
                                           wrong on the day either side changes,
                                           with nothing to say which day that was
  EXTRACT them here and import twice    -- one definition, one place to fix

The second is the only one that survives contact with a third artifact, so the
extraction happens now, while there are two callers and the diff is small.

WHAT BELONGS HERE AND WHAT DOES NOT
-----------------------------------
Here: the WORDS, and the translation from a word to a `SurfaceContext` field.
Not here: how to build a haystack out of a particular artifact. A PRD's prose
lives in `sections` and typed buckets; a DESIGN.md's lives in front-matter and
body. That shape knowledge stays in each adapter, which is the only party that
knows its own artifact.

Not here either: any judgement. No thresholds, no ranking, no archetype. Those
belong to `resolver.py` and nowhere else -- the same boundary `prd_adapter`
states in its own header, preserved by the extraction rather than diluted by it.

ABSENCE IS NOT A VALUE
----------------------
Every helper here only ever sets a field on POSITIVE textual evidence. A silent
document leaves the context all-unknown, and the resolver correctly answers
UNDETERMINED instead of inventing a topology. Writing `False` where nobody spoke
would convert "nobody said" into "it was measured and it is false".

MATCHING
--------
Multi-token phrases, matched on word boundaries, never a bare substring. A bare
substring test is how `"sign"` comes to match `"design"` and `"form"` matches
`"information"` -- recorded as T-SUBSTRING-DETECTOR-FLAGS-ITS-OWN-RULE-001 in the
UACF adjudication, from a detector in this same subsystem. The trap is sharper
here than it was in the PRD adapter: this vocabulary is now read by an adapter
whose artifact is a *design* document, in which the literal word "design" is
certain to appear.
"""
from __future__ import annotations

import re

# Multi-token phrases only. A single generic word is a false-positive engine.
INVITE = ("invite only", "invitation only", "invited by", "referral code",
          "waiting list", "waitlist")
PAYMENT_FIRST = ("payment before", "card required", "credit card up front",
                 "paid plan required", "pay before")
REGULATED = ("regulated", "kyc", "know your customer", "aml", "hipaa",
             "gdpr", "sox", "pci dss", "financial conduct")
SENSITIVE = ("personal data", "sensitive data", "medical record",
             "health record", "national id", "passport number")
ASSURANCE = ("identity verification", "verified identity", "proof of address",
             "document verification", "id check")
MULTI_TENANT = ("multi tenant", "multi-tenant", "organisation account",
                "organization account", "team workspace", "shared workspace")
SINGLE_TENANT = ("single tenant", "single-tenant", "personal account only")
EXTERNAL = ("sends email", "charges the customer", "places an order",
            "notifies third part", "publishes publicly")
RETURNING = ("returning user", "existing customer", "log back in",
             "sign back in", "repeat visit")

# The words that make surface architecture RELEVANT at all. Applicability is
# first-class: an artifact that names no entry surface must stay uncontaminated.
ENTRY_SURFACE = ("sign up", "signup", "sign-up", "onboarding",
                 "create an account", "account creation", "register",
                 "registration", "log in", "login", "trial", "free trial")


def matches(hay: str, phrases) -> bool:
    """Word-boundary match, never a bare substring."""
    for p in phrases:
        if re.search(r"\b" + re.escape(p) + r"\b", hay):
            return True
    return False


def entry_surface_hits(hay: str) -> list:
    """Every entry-surface phrase the text actually contains, sorted and unique.

    Returned rather than reduced to a bool so each adapter can put the words it
    matched into its own reason string. A reason naming the evidence is what lets
    a later reader falsify the applicability decision instead of trusting it.
    """
    hit = {s for s in ENTRY_SURFACE
           if re.search(r"\b" + re.escape(s) + r"\b", hay)}
    return sorted(hit)


def apply_phrase_evidence(hay: str, ctx) -> None:
    """Set every `SurfaceContext` field this vocabulary has evidence for.

    Mutates `ctx` in place and returns nothing, because the caller owns the
    context object and the fields this does NOT touch are exactly as meaningful
    as the ones it does: they stay None, which is UNKNOWN.

    Tenancy is the one exclusive pair -- a document declaring both is read as
    multi-tenant, which is the wider of the two and therefore the one that cannot
    silently narrow an obligation.
    """
    if matches(hay, INVITE):
        ctx.invitation_based = True
    if matches(hay, PAYMENT_FIRST):
        ctx.payment_before_value = True
    if matches(hay, REGULATED):
        ctx.regulated = True
    if matches(hay, SENSITIVE):
        ctx.sensitive_data = True
    if matches(hay, ASSURANCE):
        ctx.assurance_required = True
    if matches(hay, EXTERNAL):
        ctx.external_consequences = True
    if matches(hay, RETURNING):
        ctx.returning_parties_exist = True
    if matches(hay, MULTI_TENANT):
        ctx.tenancy = "multi_tenant"
    elif matches(hay, SINGLE_TENANT):
        ctx.tenancy = "single_tenant"


__all__ = ["ASSURANCE", "ENTRY_SURFACE", "EXTERNAL", "INVITE", "MULTI_TENANT",
           "PAYMENT_FIRST", "REGULATED", "RETURNING", "SENSITIVE",
           "SINGLE_TENANT", "apply_phrase_evidence", "entry_surface_hits",
           "matches"]
