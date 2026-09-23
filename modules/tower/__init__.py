"""Universal Tower -- the persisted Mission Baseline Capsule.

Canonical semantic, recovered from the source corpus at B 102.293 and recorded
in vault/audits/ucr_cif/08_TOWER_SEMANTIC_RECOVERED.md:

    Baseline Tower Lift = verified capability delta, deduplicated against
    existing capability state.

This package owns the capsule: its states, its path, its production and its
reading. `tools/tower_capsule.py` is a CLI shim over it, and
`modules/gsd_x/tier.py` reads it on the prompt path. One effect, one owner.
"""

from .capsule import (  # noqa: F401
    AVAILABLE,
    EMPTY_BY_EVIDENCE,
    NOT_APPLICABLE,
    PRODUCER_FAILURE,
    STALE,
    UNKNOWN,
    capsule_path,
    evidence_tokens,
    produce,
    read,
)
