"""surface_architecture -- which surface architecture is justified, and where do its
boundaries fall?

The estate has eleven capability contracts. None of them answers this question, and
that is not an omission anyone has to infer: `architecture_reconstruction` puts
"deciding what to build" and "specifying the change" in its own `non_scope`
(`vault/capability_runtime/contracts/architecture_reconstruction.json:10-13`), and a
402-file sweep recorded in `commands/architecture-horizon.md:7-11` found nothing that
answered an architecture counterfactual. The boundary was drawn by the incumbents.

WHAT THIS OWNS
    Given a product's measured constraints, which surface archetype is justified, and
    where do the value / identity / persistence / assurance / consent / commitment /
    activation boundaries fall. It emits a decision and the alternatives it rejected.

WHAT THIS DOES NOT OWN, and must never grow
    visual quality, interaction behaviour  -> CDIO (evaluative; CDIO-00:22-24)
    which component realises a semantic    -> modules/cdicf
    whether a capability applies at all    -> modules/capability_runtime
    how strong a completion claim may be   -> modules/done_gate/strength_ladder
    provenance, failure taxonomy, ratchets -> DO-NOT-BUILD rows in the binding
                                              vault/audits/apir/NON_DUPLICATION_LEDGER.md

DOMAIN BLINDNESS IS STRUCTURAL, NOT STYLISTIC
    This package is the KERNEL. Every domain word lives in `verticals/`, never here.
    The reason is mechanical: `universal-meta-systems/runtime/specialization.py::
    contaminates_kernel` refuses a derivative whose domain vocabulary appears in a
    kernel field, and it matches by SUBSTRING with no word boundary -- so a domain
    noun anywhere in this package can make the first vertical uncompilable.

    This paragraph deliberately names none of those words. An earlier draft listed
    four of them as examples and `V-SA-KERNEL-DOMAIN-BLIND` failed on its own rule
    text, which is the correct behaviour: a substring detector cannot tell a
    prohibition from a violation. The gate has no exemption list, because an
    exemption written by the author of the rule is an exemption for everything.

Stdlib-only. Absence is never the ambient default: a fact nobody measured is None, and
a decision that depends on it is UNDETERMINED rather than a guess.
"""

__all__ = ["context", "archetypes", "boundaries", "resolver"]
