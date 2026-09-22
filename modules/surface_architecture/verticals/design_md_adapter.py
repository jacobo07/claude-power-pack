#!/usr/bin/env python3
"""design_md_adapter.py -- a DESIGN.md, read as a SurfaceContext.

THE SECOND ARTIFACT KIND
------------------------
`prd_adapter.py` proved a construction artifact could reach this capability
without the stage naming it. One subject proves an INTEGRATION. This module is
the second, differently-shaped subject that decides whether the inheritance
boundary is INFRASTRUCTURE -- and the generic layer
(`modules/capability_runtime/{enrichment,contract}.py`) was not edited to admit
it. That is the whole claim; if it had needed editing, the boundary was never
generic and the honest answer was to say so.

WHY A DESIGN.md IS NOT A PRD WEARING A HAT
------------------------------------------
The tempting cheap win is to point `prd_adapter._hay` at a different file and
call it a second artifact. That would prove nothing: it is the PRD path
duplicated, which is a predeclared falsifier of this mission. The two artifacts
genuinely differ:

    PRD baseline       typed buckets (must_have / integrations / auth_required),
                       a content_sha256, prose in `sections`
    DESIGN.md          front-matter (family, fonts, colors, ground), a CDIO-07
                       experience contract, declared WCAG / bundle context,
                       unresolved UX findings, and a body of markdown

So the CONTEXT THIS PRODUCES IS DELIBERATELY SPARSER. A DESIGN.md has no
`auth_required` tri-state, so `identity_driver` and
`value_before_identity_possible` stay UNKNOWN here where the PRD adapter can
set them, and it declares no integrations, so `integrations_available` stays
empty. Writing anything into those fields would be inventing product facts out
of a design document -- exactly the "absence is not a value" rule this
subsystem already states. The asymmetry is the evidence: two adapters reading
one vocabulary and reaching different conclusions is a shared mechanism, and
two adapters reaching identical conclusions would have been one adapter twice.

WHAT IS SHARED AND WHAT IS NOT
------------------------------
Shared, by import from `surface_phrases`: the domain WORDS and their
translation to context fields. Not shared: how to build a haystack out of a
DESIGN.md, which is the only genuinely design-shaped knowledge here, and which
is why this module lives under `verticals/` beside its PRD sibling. The kernel
stays domain-blind (`V-SA-KERNEL-DOMAIN-BLIND`).

It RESOLVES and TRANSLATES. It does not decide: no thresholds, no ranking, no
archetype is ever named here. Every judgement stays in `resolver.py`.

THE SUBSTRING TRAP, SHARPENED
-----------------------------
`T-SUBSTRING-DETECTOR-FLAGS-ITS-OWN-RULE-001` says a bare substring test is how
`"sign"` comes to match `"design"`. In a PRD that is a latent risk. In a file
literally called DESIGN.md, whose every other line says "design", it is a
certainty -- a bare-substring matcher would report that EVERY design document
in the estate describes a signup surface. The shared vocabulary matches on word
boundaries, and `V-INHERIT-DESIGN-SUBSTRING` drives that case directly rather
than trusting this paragraph.

THE PATH IS NOT EVIDENCE
------------------------
The document's own location is deliberately kept OUT of the haystack. A
DESIGN.md living in a folder called `signup/` would otherwise be read as
declaring an entry surface, which is an inference about a directory name rather
than a statement the author made. The path is used for provenance only.
"""
from __future__ import annotations

import re

from modules.surface_architecture.context import SurfaceContext
from modules.surface_architecture.verticals.surface_phrases import (
    apply_phrase_evidence, entry_surface_hits)

ARTIFACT_KIND = "design_md"

# The document's own statement of what it designs. First level-1 heading only:
# a DESIGN.md's H1 is its subject line, while lower headings are its sections.
_H1_RE = re.compile(r"^#[ \t]+(.+?)[ \t]*$", re.MULTILINE)


def _hay(artifact: dict) -> str:
    """One lowercased haystack of the DESIGN.md's OWN words.

    The full document text is the primary source, because a design document
    states what it is designing in prose rather than in typed fields. The
    unresolved UX findings are added explicitly: they are the one part of the
    front-matter that is free prose, and a finding such as "the sign up step
    loses people" is exactly the evidence this capability exists to notice.

    `family`, `fonts`, `colors` and the experience contract are NOT added. They
    are aesthetic and behavioural vocabulary with no product-topology meaning,
    and feeding enum values into a phrase matcher only invents coincidences.
    """
    parts: list[str] = [str(artifact.get("text") or "")]
    declared = artifact.get("declared_context") or {}
    if isinstance(declared, dict):
        findings = declared.get("unresolved_ux_findings") or []
        if isinstance(findings, list):
            parts.extend(str(f) for f in findings)
    return " \n ".join(parts).lower()


def applies(artifact: dict) -> tuple[bool, str]:
    """Is a surface-architecture decision even relevant to this DESIGN.md?

    Applicability is FIRST-CLASS. Most DESIGN.md files in this estate describe a
    dashboard, a document surface or a brand system, and handing any of them
    signup obligations would be exactly the contamination the enrichment
    boundary's NOT_CALLABLE record exists to prevent. A design document earns a
    surface-architecture opinion only by naming an entry surface in its own
    words.

    There is no `auth_required` fallback here, deliberately. The PRD adapter has
    one because a PRD baseline carries that field as a real tri-state; a
    DESIGN.md does not carry it at all, and inventing a substitute signal would
    make this adapter answer a question the artifact never addressed.
    """
    hay = _hay(artifact)
    hit = entry_surface_hits(hay)
    if hit:
        return True, f"DESIGN.md names an entry surface: {hit[:4]}"
    return False, "DESIGN.md names no entry surface"


def context_from_design_md(artifact: dict) -> SurfaceContext:
    """Translate. Set a field ONLY on positive evidence; never guess."""
    if not isinstance(artifact, dict):
        raise TypeError("design_md artifact must be a dict")

    hay = _hay(artifact)
    source = str(artifact.get("source") or "").strip()
    ctx = SurfaceContext(source=f"design_md:{source or 'unstamped'}")

    # The H1 is the document's own subject line. Absent H1 -> product_kind stays
    # None, because a filename is not a statement the author made.
    h1 = _H1_RE.search(str(artifact.get("text") or ""))
    if h1:
        ctx.product_kind = h1.group(1).strip()[:120]

    # Every phrase-driven field, from the vocabulary both adapters share.
    apply_phrase_evidence(hay, ctx)

    return ctx


def payload_for(artifact: dict):
    """The generic adapter protocol: (payload | None, reason).

    `None` means this capability does not apply to THIS artifact, and the reason
    travels with it so a non-applicable design document can PROVE it was
    considered and deliberately left alone -- which is different evidence from
    never having been looked at.
    """
    try:
        ok, why = applies(artifact)
    except Exception as e:  # noqa: BLE001 -- a broken probe declines, loudly
        return None, f"applicability probe failed: {type(e).__name__}: {e}"
    if not ok:
        return None, why
    return context_from_design_md(artifact), why


__all__ = ["ARTIFACT_KIND", "applies", "context_from_design_md", "payload_for"]
