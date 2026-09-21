#!/usr/bin/env python3
"""signup.py -- the first vertical: the path from first contact to durable activation.

This is a `SpecializationSpec`, not a second engine. The kernel decides which surface
architecture is justified; this declares what that means HERE -- the vocabulary, what
counts as evidence, what makes an answer acceptable, when it may fire, and who consumes
it. The six components compile into contract-field overrides through
`universal-meta-systems/runtime/specialization.py`, and `capability_runtime/
derivatives.py` records the genealogy so a kernel improvement still reaches this.

WHY THE VOCABULARY VALUES ARE ALL MULTI-WORD
    `contaminates_kernel` matches by SUBSTRING with no word boundary
    (specialization.py:173-178) -- unlike `applicability._hits`, which anchors on \\b
    (applicability.py:104). A single-word value such as "form" would fire on the
    kernel's "information", and "sign" on "design". Every value below is at least two
    tokens and domain-anchored, so it cannot collide with ordinary kernel English.
    `V-SA-VERTICAL-NO-CONTAMINATION` asserts this against the real kernel contract,
    with a positive control, because a clean result from an unasked question is
    indistinguishable from a clean result.

WHY write_surfaces IS EMPTY
    `derive()` re-runs `validate()`, which raises HR-APA-009 when write_surfaces is
    non-empty and either rollback or kill_switch is falsy (contract.py:157-160). It is
    empty here because it is TRUE: this vertical persists nothing. The binding
    NON_DUPLICATION_LEDGER's DS13 ruling says applicability decisions are returned to
    the caller and not persisted until CDP exists, and an unconsumed store would be the
    Registry-Without-Runtime anti-pattern DS23 names.

WHAT THIS VERTICAL DOES NOT CLAIM
    Nothing dispatches it. The kernel contract's own non_scope says "dispatching its
    own decision", and that is inherited here rather than quietly dropped.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[3]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

PROJECT = "signup"

# Declared as plain data so the spec can be read, diffed and asserted on without
# importing the specialization machinery. `build_spec()` assembles the dataclasses.
NAMING = {
    "id": "",  # left to derive(): parent.id@project, so the id cannot drift
    "name": "Signup Surface Architecture",
    "owner": "modules/surface_architecture/verticals/signup.py",
    "sovereign_question": (
        "For this product, what is the lowest-work valid path from first contact to "
        "durable activation, and where does each boundary fall?"),
}

# Universal kernel noun -> what it is called here. VALUES are what
# `contaminates_kernel` tests, so every one is multi-token and domain-anchored.
VOCABULARY = {
    "entry surface": "signup surface",
    "known party": "account identity",
    "durable owner": "registered account",
    "returning party": "returning member",
    "activation moment": "activated account",
    "ephemeral work": "pre-account work",
}

DOMAIN = "signup surface"

TRIGGERS = [
    "signup", "sign-up", "sign up", "onboarding", "first-run experience",
    "account creation", "guest to account", "invitation acceptance",
    "trial start", "workspace creation", "returning user",
]

ANTI_TRIGGERS = [
    "password reset",          # credential recovery, not entry architecture
    "session expiry",          # a runtime concern
    "billing portal",
]

SCOPE = [
    "signup surface architecture",
    "activation boundary placement for a signup surface",
]

# ADDITIONS ONLY. The parent's non_scope is inherited VERBATIM and unioned in by
# `build_spec`, never restated here.
#
# HR-APA-017 refuses a derivative that weakens an inherited boundary, and it compares
# by value. An earlier draft of this list paraphrased two of the parent's entries --
# "which component renders a step" for "which component realises a semantic", and
# "visual and interaction quality" for "visual quality and interaction behaviour" --
# and `derive()` correctly rejected it: to the rule, a reworded boundary is a DROPPED
# boundary. Paraphrase is how a constraint quietly disappears, so the parent's strings
# are copied, not improved upon.
NON_SCOPE_ADDITIONS = [
    "credential storage",
    "which identity provider a product should use",
]

# What counts as evidence HERE. Not pushed into required_evidence on the contract --
# see the kernel seed tool: any name there is a hard gate compared as free text, and a
# name no caller supplies blocks the capability permanently and silently.
EVIDENCE_INPUTS = [
    "a measured SurfaceContext",
    "the product's stated first meaningful value",
    "whether useful work can precede a durable owner",
]

OUTPUTS = [
    "a justified signup archetype, or a named refusal",
    "value / identity / persistence / assurance / consent / commitment / activation "
    "boundary placements with their basis",
    "the archetypes rejected, and the measured fact that rejected each",
]

CONSUMERS = [
    "Owner",
    "Claude Code",
    "commands/surface-architecture.md",
]


def non_scope(parent_non_scope=()) -> list:
    """The parent's boundaries, verbatim and first, plus this vertical's additions.

    Order is parent-first and duplicates are dropped, so re-running against an updated
    kernel picks up a NEW parent boundary automatically instead of silently dropping it.
    """
    out = list(parent_non_scope)
    for item in NON_SCOPE_ADDITIONS:
        if item not in out:
            out.append(item)
    return out


def build_spec(parent_non_scope=()):
    """Assemble the six-component spec. The specialization machinery is loaded lazily
    so this module can be read for its data without it on the path.

    `parent_non_scope` is threaded rather than hardcoded: a derivative may not weaken
    an inherited boundary (HR-APA-017), and the only way to guarantee that as the
    kernel evolves is to read the parent's list at build time.
    """
    sp = _load_specialization()
    return sp.SpecializationSpec(
        project=PROJECT,
        naming={k: v for k, v in NAMING.items() if v},
        domain_pack=sp.DomainPack(
            domain=DOMAIN,
            triggers=list(TRIGGERS),
            anti_triggers=list(ANTI_TRIGGERS),
            scope=list(SCOPE),
            non_scope=non_scope(parent_non_scope),
            vocabulary=dict(VOCABULARY),
        ),
        runtime_adapter=sp.RuntimeAdapter(
            compatible_runtimes=[],      # portable: the decision needs no runtime
            dependencies=["modules/surface_architecture"],
        ),
        evidence_adapter=sp.EvidenceAdapter(
            required_evidence=[],        # see the comment above EVIDENCE_INPUTS
            inputs=list(EVIDENCE_INPUTS),
        ),
        quality_policy=sp.QualityPolicy(
            outputs=list(OUTPUTS),
            failure_risk_if_omitted="medium",
            maturity="experimental",
        ),
        activation_policy=sp.ActivationPolicy(
            activation_cost="low",
            context_cost="low",
            operational_cost="low",
            expected_leverage="high",
            risk_class="reversible",
            rollback="",                 # nothing is written; see the module docstring
            kill_switch="",
            retirement_condition=(
                "a signup surface decision is produced and consumed by a live "
                "dispatch path, making this derivative redundant"),
        ),
        project_contracts=sp.ProjectContracts(
            prerequisites=[],
            consumers=list(CONSUMERS),
            write_surfaces=[],           # HR-APA-009: empty because it is true
            permissions=[],
        ),
        benchmarks=[],
    )


def _load_specialization():
    """Import the specialization module from a package whose directory name contains a
    hyphen, which `import` cannot spell."""
    import importlib.util
    name = "_ums_specialization"
    if name in sys.modules:
        return sys.modules[name]
    path = (_PP_ROOT / "modules" / "universal-meta-systems" / "runtime"
            / "specialization.py")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load the specialization map from {path}")
    mod = importlib.util.module_from_spec(spec)
    # MUST be registered BEFORE exec_module. `@dataclass` resolves its own module via
    # `sys.modules.get(cls.__module__).__dict__` (dataclasses.py:749), so a module that
    # is executing but unregistered makes every dataclass in it raise
    # AttributeError: 'NoneType' object has no attribute '__dict__'.
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)   # never leave a half-executed module registered
        raise
    return mod


__all__ = ["PROJECT", "NAMING", "VOCABULARY", "DOMAIN", "TRIGGERS", "ANTI_TRIGGERS",
           "SCOPE", "NON_SCOPE_ADDITIONS", "OUTPUTS", "CONSUMERS", "non_scope",
           "build_spec"]
