#!/usr/bin/env python3
"""prd_adapter.py -- a KARIMO PRD baseline, read as a SurfaceContext.

WHY THIS IS AN ADAPTER AND NOT A DECISION
-----------------------------------------
The capability is keyed to `SurfaceContext`: eighteen typed product constraints.
The estate's PRD stage produces a different shape -- must_have / must_not /
auth_required / integrations, extracted from prose. Nothing joined the two, so
the capability could not be reached from the one artifact that actually holds
product constraints.

This module is that join, and it is deliberately the dumbest thing that works.
It RESOLVES and TRANSLATES. It does not decide: no thresholds, no ranking, no
archetype ever named here. Every judgement stays in `resolver.py`, which is the
only place that owns it.

It lives under `verticals/` because it reads DOMAIN vocabulary -- the words for
accounts, trials and identity. The kernel is domain-blind by contract
(`V-SA-KERNEL-DOMAIN-BLIND`), so a module that must name those words belongs
here and nowhere else.

ABSENCE IS NOT A VALUE
----------------------
Every field of `SurfaceContext` defaults to None, meaning UNKNOWN, and that
three-valued design is the point. A PRD that never mentions payment tells us
NOTHING about whether payment precedes value; writing False there would convert
"nobody said" into "it was measured and it is false", and the resolver would
then answer a question it was never entitled to answer.

So this adapter only ever sets a field it has POSITIVE textual evidence for. A
silent PRD yields a context of all-unknowns, and the resolver correctly returns
UNDETERMINED rather than a confident topology.

MATCHING
--------
Phrases are multi-token and matched on word boundaries. A bare substring test is
how `"sign"` comes to match `"design"` and `"form"` matches `"information"` --
recorded as `T-SUBSTRING-DETECTOR-FLAGS-ITS-OWN-RULE-001` in the UACF
adjudication, from a detector in this same subsystem.
"""
from __future__ import annotations

from modules.surface_architecture.context import SurfaceContext
from modules.surface_architecture.verticals.surface_phrases import (
    apply_phrase_evidence, entry_surface_hits)

ARTIFACT_KIND = "prd_baseline"

# The phrase vocabulary moved to `surface_phrases.py` when `design_md` became a
# second artifact kind needing the SAME judgement about the SAME words. It was
# EXTRACTED rather than copied: a copy is correct on the day it is written and
# wrong on the day either side changes, with nothing to say which day that was.
# What stays here is the only thing that is genuinely PRD-shaped -- how to build
# a haystack out of this artifact, and the `auth_required` tri-state, which no
# other artifact has.


def _hay(baseline: dict) -> str:
    """One lowercased haystack of the PRD's own words.

    `sections` carries the raw prose; the buckets carry the extracted
    constraints. Both are searched, because a constraint can be stated in
    either and a miss here silently becomes an UNKNOWN field.
    """
    parts: list[str] = [str(baseline.get("title", ""))]
    for key in ("must_have", "must_not", "integrations", "perf_targets",
                "deadlines"):
        val = baseline.get(key) or []
        if isinstance(val, list):
            parts.extend(str(v) for v in val)
    for sec in baseline.get("sections") or []:
        if isinstance(sec, dict):
            parts.append(str(sec.get("heading", "")))
            parts.append(str(sec.get("body", "")))
        else:
            parts.append(str(sec))
    return " \n ".join(parts).lower()


def applies(baseline: dict) -> tuple[bool, str]:
    """Is a surface-architecture decision even relevant to this PRD?

    Applicability is FIRST-CLASS: a PRD for a batch job or a library must not be
    handed signup obligations. Returning False here is how a non-applicable
    project stays uncontaminated, which is a stated requirement and not a
    nicety.
    """
    hay = _hay(baseline)
    hit = entry_surface_hits(hay)
    if hit:
        return True, f"PRD names an entry surface: {hit[:4]}"
    if baseline.get("auth_required") is True:
        return True, "PRD declares auth_required"
    return False, "PRD names no entry surface and requires no auth"


def context_from_prd_baseline(baseline: dict) -> SurfaceContext:
    """Translate. Set a field ONLY on positive evidence; never guess."""
    if not isinstance(baseline, dict):
        raise TypeError("prd baseline must be a dict")

    hay = _hay(baseline)
    ctx = SurfaceContext(
        source=f"prd_baseline:{baseline.get('content_sha256', '')[:12] or 'unstamped'}")

    if baseline.get("title"):
        ctx.product_kind = str(baseline["title"])[:120]

    # auth_required is a real tri-state on the baseline: True, False, or absent.
    auth = baseline.get("auth_required")
    if auth is True:
        ctx.identity_driver = "account_required"
    # auth is False -> the PRD affirmatively said no auth, which IS evidence.
    elif auth is False:
        ctx.value_before_identity_possible = True

    # Every phrase-driven field, from the vocabulary both adapters share.
    apply_phrase_evidence(hay, ctx)

    integrations = baseline.get("integrations") or []
    if isinstance(integrations, list) and integrations:
        ctx.integrations_available = [str(i) for i in integrations]

    return ctx


def payload_for(baseline: dict):
    """The generic adapter protocol: (payload | None, reason).

    `None` means this capability does not apply to THIS artifact, and the reason
    travels with it so a non-applicable project can PROVE it was considered and
    deliberately left alone -- which is different evidence from never having
    been looked at.
    """
    try:
        ok, why = applies(baseline)
    except Exception as e:  # noqa: BLE001 -- a broken probe declines, loudly
        return None, f"applicability probe failed: {type(e).__name__}: {e}"
    if not ok:
        return None, why
    return context_from_prd_baseline(baseline), why


__all__ = ["ARTIFACT_KIND", "applies", "context_from_prd_baseline",
           "payload_for"]
