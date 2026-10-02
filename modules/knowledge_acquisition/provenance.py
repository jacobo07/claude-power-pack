"""What the source's OPERATOR has said about where its numbers come from.

WHY THIS EXISTS
---------------
`boundary.py` learns from the source's own words. On 2026-08-26 EVA said (SF30-022)
"no tenemos acceso a los datos financieros detallados de otros clientes", and
every cohort statistic after that was judged unsourced by its own admission.

On 2026-10-02 Consultoria.io's head of AI told the Owner directly how EVA's
figures are built: from anonymised metrics extracted from what users choose to
share in their conversations with EVA. Connecting client stores (Shopify, Meta
Ads, Klaviyo) at scale is a separate product, not live, expected around the end
of 2026 or early 2027.

Both statements are true together. The declared limit is about CONNECTED store
data; the cohort figures come from CHAT self-reports. So a cohort statistic is
not unsourced -- it has a source, and that source is weak in specific, nameable
ways: self-reported, opt-in (selection-biased towards whoever chose to share),
unverified, sample size and method unknown, and it may include the Owner's own
store.

WHAT AN ATTESTATION MAY AND MAY NOT DO
--------------------------------------
It renames the evidence; it never upgrades it. A claim covered by an
attestation stays capped at DERIVED and still gets the "how many cases?"
follow-up. It does NOT lift `route_to_expert`: questions that need first-hand
case outcomes still cannot be satisfied by this source until the connected-data
product exists.

An attestation is hearsay from the vendor about the vendor. It is recorded with
its date and who gave it (by role), so that a later contradicting statement can
supersede it explicitly rather than by silent edit.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProvenanceAttestation:
    """One operator statement about how an interface's figures are produced."""

    interface: str
    attested_by: str        # a role, never a personal name
    attested_on: str        # ISO date the statement was received
    cohort_figures_from: str
    not_available: str
    weaknesses: tuple[str, ...]

    def summary(self) -> str:
        return (
            f"per {self.attested_by} ({self.attested_on}): cohort figures come "
            f"from {self.cohort_figures_from}; {', '.join(self.weaknesses)}"
        )


ATTESTATIONS: dict[str, ProvenanceAttestation] = {
    "eva": ProvenanceAttestation(
        interface="eva",
        attested_by="Consultoria.io head of AI, message to the Owner",
        attested_on="2026-10-02",
        cohort_figures_from=(
            "anonymised metrics extracted from what users choose to share in "
            "EVA conversations"
        ),
        not_available=(
            "connected store data (Shopify, Meta Ads, Klaviyo) across clients; "
            "a separate product expected end 2026 / early 2027"
        ),
        weaknesses=(
            "self-reported",
            "opt-in and selection-biased",
            "unverified",
            "sample size and method unknown",
            "may include the Owner's own store",
        ),
    ),
}


def attestation_for(interface: str | None) -> ProvenanceAttestation | None:
    return ATTESTATIONS.get((interface or "").lower())


__all__ = ["ProvenanceAttestation", "ATTESTATIONS", "attestation_for"]
